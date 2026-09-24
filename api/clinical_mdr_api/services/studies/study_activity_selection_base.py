import abc
import threading
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Generic, Iterable, TypeVar

from cachetools import TTLCache
from neomodel import db

from clinical_mdr_api.domain_repositories.study_selections.study_activity_base_repository import (
    StudySelectionActivityBaseRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity import ActivityAR
from clinical_mdr_api.domains.study_selections.study_selection_base import (
    StudySelectionBaseAR,
    StudySelectionBaseVO,
)
from clinical_mdr_api.models.utils import BaseModel, GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    build_simple_filters,
    ensure_transaction,
    extract_filtering_values,
    generic_item_filtering,
    generic_pagination,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
    validate_is_dict,
)
from clinical_mdr_api.services.studies.study_selection_base import StudySelectionMixin
from common import exceptions
from common.auth.user import user
from common.config import settings
from common.telemetry import trace_calls

_AggregateRootType = TypeVar("_AggregateRootType", bound=StudySelectionBaseAR)
_VOType = TypeVar("_VOType")  # pylint: disable=invalid-name
OutputModel = TypeVar("OutputModel")


class StudyActivitySelectionBaseService(
    StudySelectionMixin, Generic[_AggregateRootType, _VOType, OutputModel]
):
    _repos: MetaRepository
    repository_interface: type
    selected_object_repository_interface: type | None

    _vo_to_ar_filter_map: dict[Any, Any] = {}

    # Shared class-level cache for study standards effective dates across all service instances
    # Uses config values for consistent cache behavior across the application
    _shared_terms_date_cache: TTLCache = TTLCache(
        maxsize=settings.cache_max_size, ttl=settings.cache_ttl
    )
    # Thread lock for safe concurrent access to the shared cache
    _shared_terms_date_cache_lock: threading.RLock = threading.RLock()

    def __init__(self):
        self._repos = MetaRepository()

        # Unified batch cache - single TTLCache with namespaced keys for all batch operations.
        # Uses dedicated batch_cache_* settings (NOT the cross-request cache_ttl which may be 0).
        # Batch caches are instance-scoped and explicitly cleared in _clear_all_batch_caches.
        self._batch_cache: TTLCache | None = None

        # Single cached instance AR to avoid repeated find_by_study/save per POST
        # Flushed to DB in the batch finally block (or on first PATCH/DELETE that needs DB state)
        self._batch_instance_ar: Any | None = (
            None  # Keep as single value - no TTL needed
        )

        # Cached selection list for _find_ar_to_patch operations
        # Avoids repeated find_by_study(for_update=True) calls during batch PATCH
        self._batch_patch_ar_selections: list | None = (
            None  # Keep as list - single value per batch
        )

    @property
    def author(self):
        return user().id()

    @property
    def repository(self) -> StudySelectionActivityBaseRepository[_AggregateRootType]:
        assert self._repos is not None
        return self.repository_interface()

    @property
    def selected_object_repository(self):
        assert self._repos is not None
        if self.selected_object_repository_interface is None:
            return None
        return self.selected_object_repository_interface()

    def _get_selected_object_exist_check(
        self,
    ) -> Callable[[str], bool]:
        return self.selected_object_repository.final_concept_exists

    def _initialize_batch_caches(self) -> None:
        """Initialize all batch-related caches and tracking sets for a new batch operation.

        Cache Lifecycle Management:
        - Called at the start of handle_batch_operations
        - Caches persist throughout the entire batch for performance
        - Individual operations may invalidate specific cache entries
        - All caches are cleared in the finally block
        """

        self._batch_cache = TTLCache(
            maxsize=settings.cache_max_size, ttl=settings.cache_ttl
        )
        self._batch_patch_ar_selections = []  # Keep as list - single value per batch

    def _clear_all_batch_caches(self) -> None:
        """Clear all batch-related caches and reset tracking state.

        This method ensures a clean state after batch processing and prevents
        memory leaks from retained cache references.
        """
        if self._batch_cache is not None:
            try:
                # Explicitly clear all entries to trigger internal cleanup
                self._batch_cache.clear()
                # Force garbage collection of expired entries
                # TTLCache may have internal timers that need explicit cleanup
                if hasattr(self._batch_cache, "expire"):
                    self._batch_cache.expire()
            except Exception as e:  # pylint: disable=broad-exception-caught
                # Log but don't fail - cleanup is best-effort
                import logging

                logging.warning("Error during batch cache cleanup: %s", e)
            finally:
                self._batch_cache = None

        self._batch_instance_ar = None
        self._batch_patch_ar_selections = None

    # Unified Cache Access Helpers
    def _get_batch_vo_cache_key(self, *args) -> tuple[str, ...]:
        """Generate namespaced key for VO cache entries."""
        return ("vo", *args)

    def _get_batch_ar_cache_key(self, *args) -> tuple[str, ...]:
        """Generate namespaced key for AR cache entries."""
        return ("ar", *args)

    def _get_batch_reordered_key(self, *args) -> tuple[str, ...]:
        """Generate namespaced key for reordered parent tracking."""
        return ("reordered", *args)

    def _append_to_patch_ar_selections_cache(self, new_vo: _VOType) -> None:
        """Append a newly created VO to the patch AR selections cache.

        Called after POST so subsequent PATCHes see the new entity without
        a DB reload. Uses immutable update to prevent cache coherence issues.
        """
        if self._batch_patch_ar_selections is None:
            return
        self._batch_patch_ar_selections = [*self._batch_patch_ar_selections, new_vo]

    def _remove_from_patch_ar_selections_cache(self, study_selection_uid: str) -> None:
        """Remove a deleted VO from the patch AR selections cache.

        Called after DELETE so subsequent PATCHes no longer see the removed entity
        without a DB reload.
        """
        if self._batch_patch_ar_selections is None:
            return
        self._batch_patch_ar_selections = [
            vo
            for vo in self._batch_patch_ar_selections
            if vo.study_selection_uid != study_selection_uid
        ]

    def _clear_batch_caches(self) -> None:
        """Clear unified batch cache for data consistency."""
        if self._batch_cache is not None:
            self._batch_cache.clear()

    @classmethod
    def clear_study_standards_cache_for_study(cls, study_uid: str) -> None:
        """Clear cached study standards effective dates for a specific study.

        Call this when study standards are modified (create/edit/delete operations)
        to ensure subsequent queries see updated effective dates.

        Args:
            study_uid: The study whose standards cache entries should be cleared
        """
        with cls._shared_terms_date_cache_lock:
            if not cls._shared_terms_date_cache:
                return

            # Remove all cache entries for this study (across all versions)
            keys_to_remove = [
                key
                for key in cls._shared_terms_date_cache.keys()
                if key[0]
                == study_uid  # Cache key format: (study_uid, study_value_version)
            ]
            for key in keys_to_remove:
                del cls._shared_terms_date_cache[key]

    def _evict_ar_cache_for_scope(
        self,
        study_activity_subgroup_uid: str | None,
        study_soa_group_uid: str,
        activity_library_name: str,
    ) -> None:
        """Evict the specific scope's AR cache entry after DELETE.

        Only the deleted entity's scope becomes stale. Other scopes remain valid.
        Also clears reordered-parent tracking since the hierarchy may need re-compaction.
        """
        if self._batch_cache is None:
            return
        find_requested = activity_library_name == settings.requested_library_name
        scope_key = self._get_batch_ar_cache_key(
            study_activity_subgroup_uid, study_soa_group_uid, find_requested
        )
        self._batch_cache.pop(scope_key, None)

        # Parent hierarchy may need re-compaction after deletion
        reordered_keys = [k for k in self._batch_cache.keys() if k[0] == "reordered"]
        for key in reordered_keys:
            del self._batch_cache[key]

    @abc.abstractmethod
    def _transform_all_to_response_model(
        self,
        study_selection: _AggregateRootType | None,
        study_value_version: str | None = None,
    ) -> list[OutputModel]:
        raise NotImplementedError

    @abc.abstractmethod
    def _transform_from_vo_to_response_model(
        self,
        study_uid: str,
        specific_selection: _VOType,
        terms_at_specific_datetime: datetime | None,
        accepted_version: bool | None = None,
    ) -> OutputModel:
        raise NotImplementedError

    @abc.abstractmethod
    def _transform_history_to_response_model(
        self,
        study_selection_history: list[Any],
        study_uid: str,
        effective_dates: list[datetime | None] | None = None,
    ) -> list[OutputModel]:
        raise NotImplementedError

    @abc.abstractmethod
    def _create_value_object(
        self,
        study_uid: str,
        selection_create_input: BaseModel,
        **kwargs,
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def update_dependent_objects(
        self,
        study_selection: _VOType,
        previous_study_selection: _VOType,
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def _patch_prepare_new_value_object(
        self,
        request_object: BaseModel,
        current_object: _VOType,
    ) -> _VOType:
        raise NotImplementedError

    @abc.abstractmethod
    def _find_ar_and_validate_new_order(
        self,
        study_uid: str,
        study_selection_uid: str,
        new_order: int,
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def _filter_ars_from_same_parent(
        self,
        selection_aggregate: _AggregateRootType,
        selection_vo: _VOType,
    ) -> _AggregateRootType:
        raise NotImplementedError

    @staticmethod
    def get_default_sorting() -> dict[str, bool] | None:
        return None

    def get_all_selections_for_all_studies(
        self,
        project_name: str | None = None,
        project_number: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        **kwargs,
    ) -> GenericFilteringReturn[OutputModel]:
        # Extract the study uids to use database level filtering for these
        # instead of service level filtering
        if filter_operator is None or filter_operator == FilterOperator.AND:
            study_uids = extract_filtering_values(filter_by, "study_uid")
        else:
            study_uids = None

        # selection_ars = self.repository.find_all(
        selection_ar = self.repository.find_all(
            project_name=project_name,
            project_number=project_number,
            study_uids=study_uids,
            **kwargs,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = self._transform_all_to_response_model(selection_ar)

        # Do filtering, sorting, pagination and count
        return service_level_generic_filtering(
            items=selections,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

    @trace_calls
    def get_all_selection(
        self,
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
        for_field_name: str | None = None,
        **kwargs,
    ) -> GenericFilteringReturn[OutputModel] | list[_AggregateRootType]:
        repos = self._repos
        try:
            activity_selection_ar = self.repository.find_by_study(
                study_uid, study_value_version=study_value_version, **kwargs
            )
            assert activity_selection_ar is not None
            if filter_by is not None:
                validate_is_dict("filter_by", filter_by)
            if sort_by is not None:
                validate_is_dict("sort_by", sort_by)
            else:
                if (sort_by := self.get_default_sorting()) is not None:
                    validate_is_dict("sort_by", sort_by)

            simple_filters = build_simple_filters(
                self._vo_to_ar_filter_map, filter_by, sort_by
            )
            if simple_filters:
                # Filtering only needs data that is already available in the AR
                items = list(activity_selection_ar.study_objects_selection)
                filtered_items = generic_item_filtering(
                    items=items,
                    filter_by=simple_filters["filter_by"],
                    filter_operator=filter_operator,
                    sort_by=simple_filters["sort_by"],
                )

                # Do count
                count = len(filtered_items) if total_count else 0

                # Do pagination
                filtered_items = generic_pagination(
                    items=filtered_items,
                    page_number=page_number,
                    page_size=page_size,
                )
                # Put the sorted and filtered items back into the AR and transform them to the response model
                if (
                    for_field_name is None
                    or for_field_name not in self._vo_to_ar_filter_map
                ):
                    activity_selection_ar.study_objects_selection = filtered_items
                    filtered_items = self._transform_all_to_response_model(
                        activity_selection_ar,
                        study_value_version=study_value_version,
                        **kwargs,
                    )
                else:
                    return filtered_items
                return GenericFilteringReturn(items=filtered_items, total=count)

            # Fall back to full generic filtering
            return service_level_generic_filtering(
                items=self._transform_all_to_response_model(
                    activity_selection_ar,
                    study_value_version=study_value_version,
                    **kwargs,
                ),
                filter_by=filter_by,
                filter_operator=filter_operator,
                sort_by=sort_by,
                total_count=total_count,
                page_number=page_number,
                page_size=page_size,
            )
        finally:
            repos.close()

    @trace_calls
    def get_all_selection_audit_trail(self, study_uid: str) -> list[OutputModel]:
        repos = self._repos
        try:
            try:
                selection_history = self.repository.find_selection_history(study_uid)
            except ValueError as value_error:
                raise exceptions.NotFoundException(msg=value_error.args[0])

            return self._transform_history_to_response_model(
                selection_history, study_uid
            )
        finally:
            repos.close()

    @trace_calls
    def get_specific_selection_audit_trail(
        self, study_uid: str, study_selection_uid: str
    ) -> list[OutputModel]:
        repos = self._repos
        try:
            try:
                selection_history = self.repository.find_selection_history(
                    study_uid, study_selection_uid
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(msg=value_error.args[0])

            return self._transform_history_to_response_model(
                selection_history, study_uid
            )
        finally:
            repos.close()

    @trace_calls
    def get_specific_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        study_value_version: str | None = None,
    ) -> OutputModel:
        (
            _,
            new_selection,
            _,
        ) = self._get_specific_activity_selection_by_uids(
            study_uid, study_selection_uid, study_value_version=study_value_version
        )
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_uid,
            study_value_version=study_value_version,
        )
        return self._transform_from_vo_to_response_model(
            study_uid=study_uid,
            specific_selection=new_selection,
            accepted_version=new_selection.accepted_version,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    @trace_calls(args=[1, 2], kwargs=["study_uid", "study_selection_uid"])
    def _find_ar_to_patch(
        self, study_uid: str, study_selection_uid: str, for_update: bool = True
    ) -> tuple[_AggregateRootType, _VOType]:
        """Find aggregate root and value object for patching operations.

        In batch mode, this method uses cached selection lists to avoid repeated
        database queries. The cache is automatically invalidated when POST/DELETE
        operations modify the entity set that PATCH operations need to see.

        Args:
            study_uid: Study identifier
            study_selection_uid: Selection identifier to patch
            for_update: Whether to acquire update locks

        Returns:
            Tuple of (selection_aggregate, current_vo) for the patch operation
        """
        # In batch mode, use cached selections if available and not invalidated.
        # Three states for _batch_patch_ar_selections:
        #   non-empty list → cache populated, use it
        #   []             → batch initialised but not yet seeded → load from DB and store
        #   None           → non-batch mode or cache was invalidated → load from DB without storing
        if for_update and self._batch_patch_ar_selections:
            # Build AR from cached selections — avoids DB round-trip
            selections = self._batch_patch_ar_selections
            selection_aggregate = (
                self.repository._aggregate_root_type.from_repository_values(
                    study_uid=study_uid, study_objects_selection=selections
                )
            )
            selection_aggregate.repository_closure_data = selections
        elif for_update and self._batch_patch_ar_selections is not None:
            # Empty list [] — batch mode started, seed the cache from DB
            selection_aggregate = self.repository.find_by_study(
                study_uid=study_uid, for_update=for_update
            )
            self._batch_patch_ar_selections = list(
                selection_aggregate.study_objects_selection
            )
        else:
            # None — non-batch mode or cache was invalidated — load from database
            selection_aggregate = self.repository.find_by_study(
                study_uid=study_uid, for_update=for_update
            )

        assert selection_aggregate is not None

        # Load the current VO for updates
        current_vo, _ = selection_aggregate.get_specific_object_selection(
            study_selection_uid=study_selection_uid
        )
        selection_aggregate = self._filter_ars_from_same_parent(
            selection_aggregate=selection_aggregate, selection_vo=current_vo  # type: ignore[arg-type]
        )
        return selection_aggregate, current_vo

    def _update_aggregate(
        self,
        selection_aggregate: _AggregateRootType,
        updated_selection: _VOType,
        # pylint: disable=unused-argument
        previous_selection: _VOType | None = None,
    ) -> _VOType:
        # let the aggregate update the value object
        selection_aggregate.update_selection(
            updated_study_object_selection=updated_selection,
            object_exist_callback=self._get_selected_object_exist_check(),
            ct_term_level_exist_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
        )
        selection_aggregate.validate()

        # sync with DB and save the update
        self.repository.save(selection_aggregate, self.author)
        # After save(), the repository writeback has updated the in-memory VO with the correct order.
        updated_vo, _ = selection_aggregate.get_specific_object_selection(
            updated_selection.study_selection_uid
        )
        return updated_vo

    @ensure_transaction(db)
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: BaseModel,
    ):
        repos = self._repos
        try:
            selection_aggregate, current_vo = self._find_ar_to_patch(
                study_uid=study_uid, study_selection_uid=study_selection_uid
            )

            # merge current with updates

            updated_selection = self._patch_prepare_new_value_object(
                request_object=selection_update_input,
                current_object=current_vo,
            )

            updated_selection = self._update_aggregate(
                selection_aggregate=selection_aggregate,
                updated_selection=updated_selection,
                previous_selection=current_vo,
            )

            # # sync related nodes
            self.update_dependent_objects(
                study_selection=updated_selection, previous_study_selection=current_vo
            )

            # Keep the batch AR-selection cache current after each PATCH save.
            # This ensures subsequent PATCH operations in the same batch see the updated state.
            # Uses immutable update to prevent cache coherence issues.
            if self._batch_patch_ar_selections is not None:
                self._batch_patch_ar_selections = [
                    (
                        updated_selection
                        if vo.study_selection_uid == study_selection_uid
                        else vo
                    )
                    for vo in self._batch_patch_ar_selections
                ]

            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )

            # add the activity and return
            return self._transform_from_vo_to_response_model(
                study_uid=study_uid,
                specific_selection=updated_selection,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    def get_distinct_values_for_header(
        self,
        field_name: str,
        study_uid: str | None = None,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
        study_value_version: str | None = None,
        include_placeholders: bool = False,
    ):
        all_items = self.get_all_selection(
            study_uid=study_uid,
            study_value_version=study_value_version,
            filter_by=filter_by,
            filter_operator=filter_operator,
            for_field_name=field_name,
            include_placeholders=include_placeholders,
        )
        if isinstance(all_items, list):
            # We got a list of StudySelectionBaseAR,
            # this means we look up the values in the AR under a modified field name
            field_name = self._vo_to_ar_filter_map[field_name]
        else:
            all_items = all_items.items

        header_values = service_level_generic_header_filtering(
            items=all_items,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )

        return header_values

    @ensure_transaction(db)
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> OutputModel:
        repos = self._repos
        try:
            selection_aggregate = self._find_ar_and_validate_new_order(
                study_uid=study_uid,
                study_selection_uid=study_selection_uid,
                new_order=new_order,
            )

            assert selection_aggregate is not None
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order, self.author
            )

            # sync with DB and save the update
            self.repository.save(selection_aggregate, self.author)

            selection_aggregate = self.repository.find_by_study(
                study_uid=study_uid, for_update=True
            )
            # Fetch the new selection which was just added
            (
                specific_selection,
                _,
            ) = selection_aggregate.get_specific_object_selection(study_selection_uid)
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )

            # add the activity and return
            reordered_item = self._transform_from_vo_to_response_model(
                study_uid=study_uid,
                specific_selection=specific_selection,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
            return reordered_item
        finally:
            repos.close()

    def _get_linked_activities(
        self,
        selection_vos: Iterable[StudySelectionBaseVO],
        filter_out_retired_groupings: bool = False,
    ) -> list[ActivityAR]:
        version_specific_uids: dict[str, set[str]] = defaultdict(set)
        latest_uids: dict[str, set[str]] = defaultdict(set)

        for selection_vo in selection_vos:
            version_specific_uids[selection_vo.activity_uid].add(
                selection_vo.activity_version
            )
            latest_uids[selection_vo.activity_uid].add("LATEST")

        if not version_specific_uids:
            return []

        if not filter_out_retired_groupings:
            for uid, versions in latest_uids.items():
                version_specific_uids[uid].update(versions)
            return self._repos.activity_repository.get_all_optimized(
                version_specific_uids=version_specific_uids,
                include_retired_versions=True,
            )[0]

        # When filtering retired groupings, fetch pinned versions unfiltered (so the study's
        # pinned `activity` always shows all its original groupings) and fetch the LATEST
        # versions with the filter applied (so `latest_activity` only shows active groupings).
        # Combining both allows _find_versions to resolve each field independently.
        pinned_results: list[ActivityAR] = (
            self._repos.activity_repository.get_all_optimized(
                version_specific_uids=version_specific_uids,
                include_retired_versions=True,
            )[0]
        )
        latest_results: list[ActivityAR] = (
            self._repos.activity_repository.get_all_optimized(
                version_specific_uids=latest_uids,
                include_retired_versions=True,
                filter_out_retired_groupings=True,
            )[0]
        )
        return pinned_results + latest_results
