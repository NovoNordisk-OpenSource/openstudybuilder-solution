import abc
from datetime import datetime
from typing import Any, Callable, TypeVar

from neomodel import db

from clinical_mdr_api.domain_repositories.study_selections.study_activity_base_repository import (
    StudySelectionActivityBaseRepository,
)
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
from common.telemetry import trace_calls

_AggregateRootType = TypeVar("_AggregateRootType")
_VOType = TypeVar("_VOType")  # pylint: disable=invalid-name


class StudyActivitySelectionBaseService(StudySelectionMixin):
    _repos: MetaRepository
    repository_interface: type
    selected_object_repository_interface: type

    _vo_to_ar_filter_map = {}

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    @property
    def repository(self) -> StudySelectionActivityBaseRepository[_AggregateRootType]:
        assert self._repos is not None
        return self.repository_interface()

    @property
    def selected_object_repository(self):
        assert self._repos is not None
        return self.selected_object_repository_interface()

    def _get_selected_object_exist_check(
        self,
    ) -> Callable[[str], bool]:
        return self.selected_object_repository.final_concept_exists

    @abc.abstractmethod
    def _transform_all_to_response_model(
        self,
        study_selection: _AggregateRootType,
        study_value_version: str | None = None,
    ) -> list[BaseModel]:
        raise NotImplementedError

    @abc.abstractmethod
    def _transform_from_vo_to_response_model(
        self,
        study_uid: str,
        specific_selection: _VOType,
        terms_at_specific_datetime: datetime | None,
        accepted_version: bool | None = None,
    ) -> BaseModel:
        raise NotImplementedError

    @abc.abstractmethod
    def _transform_history_to_response_model(
        self,
        study_selection_history: list[Any],
        study_uid: str,
        effective_dates: datetime | None = None,
    ) -> list[BaseModel]:
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
        study_selection: StudySelectionBaseVO,
        previous_study_selection: StudySelectionBaseVO,
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
    ) -> tuple[_AggregateRootType, _VOType]:
        raise NotImplementedError

    @abc.abstractmethod
    def _filter_ars_from_same_parent(
        self,
        selection_aggregate: StudySelectionBaseAR,
        selection_vo: StudySelectionBaseVO,
    ) -> StudySelectionBaseAR:
        raise NotImplementedError

    def get_default_sorting(
        self,
    ) -> dict | None:
        return None

    def get_all_selections_for_all_studies(
        self,
        project_name: str | None = None,
        project_number: str | None = None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        **kwargs,
    ) -> GenericFilteringReturn[BaseModel]:
        # Extract the study uids to use database level filtering for these
        # instead of service level filtering
        if filter_operator is None or filter_operator == FilterOperator.AND:
            study_uids = extract_filtering_values(filter_by, "study_uid")
        else:
            study_uids = None

        selection_ars = self.repository.find_all(
            project_name=project_name,
            project_number=project_number,
            study_uids=study_uids,
            **kwargs,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for selection_ar in selection_ars:
            parsed_selections = self._transform_all_to_response_model(selection_ar)
            for selection in parsed_selections:
                selections.append(selection)

        # Do filtering, sorting, pagination and count
        filtered_items = service_level_generic_filtering(
            items=selections,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        return filtered_items

    @trace_calls
    def get_all_selection(
        self,
        study_uid: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
        for_field_name: str | None = None,
        **kwargs,
    ) -> GenericFilteringReturn[BaseModel] | list[StudySelectionBaseAR]:
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
                        activity_selection_ar, study_value_version=study_value_version
                    )
                else:
                    return filtered_items
                filtered_items = GenericFilteringReturn.create(filtered_items, count)
            else:
                # Fall back to full generic filtering
                filtered_items = service_level_generic_filtering(
                    items=self._transform_all_to_response_model(
                        activity_selection_ar, study_value_version=study_value_version
                    ),
                    filter_by=filter_by,
                    filter_operator=filter_operator,
                    sort_by=sort_by,
                    total_count=total_count,
                    page_number=page_number,
                    page_size=page_size,
                )
            return filtered_items
        finally:
            repos.close()

    def get_all_selection_audit_trail(self, study_uid: str) -> list[BaseModel]:
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

    def get_specific_selection_audit_trail(
        self, study_uid: str, study_selection_uid: str
    ) -> list[BaseModel]:
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

    def get_specific_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        study_value_version: str | None = None,
    ) -> BaseModel:
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

    def _find_ar_to_patch(
        self, study_uid: str, study_selection_uid: str
    ) -> tuple[StudySelectionBaseAR, StudySelectionBaseVO]:
        # Load aggregate
        selection_aggregate = self.repository.find_by_study(
            study_uid=study_uid, for_update=True
        )

        assert selection_aggregate is not None

        # Load the current VO for updates
        current_vo, _ = selection_aggregate.get_specific_object_selection(
            study_selection_uid=study_selection_uid
        )
        selection_aggregate = self._filter_ars_from_same_parent(
            selection_aggregate=selection_aggregate, selection_vo=current_vo
        )
        return selection_aggregate, current_vo

    def _update_aggregate(
        self,
        selection_aggregate: _AggregateRootType,
        # pylint: disable=unused-argument
        previous_selection: _VOType,
        updated_selection: _VOType,
    ) -> bool:
        # let the aggregate update the value object
        selection_aggregate.update_selection(
            updated_study_object_selection=updated_selection,
            object_exist_callback=self._get_selected_object_exist_check(),
            ct_term_level_exist_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
        )
        selection_aggregate.validate()

        # sync with DB and save the update
        self.repository.save(selection_aggregate, self.author)

    @ensure_transaction(db)
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: BaseModel,
    ) -> BaseModel:
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

            self._update_aggregate(
                selection_aggregate=selection_aggregate,
                previous_selection=current_vo,
                updated_selection=updated_selection,
            )

            # # sync related nodes
            self.update_dependent_objects(
                study_selection=updated_selection, previous_study_selection=current_vo
            )

            selection_aggregate, updated_selection = self._find_ar_to_patch(
                study_uid=study_uid, study_selection_uid=study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )

            # add the activity and return
            return self._transform_from_vo_to_response_model(
                study_uid=selection_aggregate.study_uid,
                specific_selection=updated_selection,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    def get_distinct_values_for_header(
        self,
        field_name: str,
        study_uid: str | None = None,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        page_size: int = 10,
        study_value_version: str | None = None,
    ):
        all_items = self.get_all_selection(
            study_uid=study_uid,
            study_value_version=study_value_version,
            filter_by=filter_by,
            filter_operator=filter_operator,
            for_field_name=field_name,
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
    ) -> BaseModel:
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
