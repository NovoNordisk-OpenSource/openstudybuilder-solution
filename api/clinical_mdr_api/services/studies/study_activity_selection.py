import dataclasses
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable, Mapping, Sequence

from fastapi import status
from neomodel import db

from clinical_mdr_api.domain_repositories._utils.helpers import (
    acquire_write_lock_study_value,
)
from clinical_mdr_api.domain_repositories.concepts.activities.activity_repository import (
    ActivityRepository,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityInstanceRoot,
    ActivityInstanceValue,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_repository import (
    SelectionHistory,
    StudySelectionActivityRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity import (
    ActivityAR,
    ActivityGroupingVO,
    ActivityVO,
)
from clinical_mdr_api.domains.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity import (
    StudySelectionActivityAR,
    StudySelectionActivityVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_group import (
    StudySelectionActivityGroupVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_instance import (
    StudySelectionActivityInstanceVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_subgroup import (
    StudySelectionActivitySubGroupVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_base import SoAItemType
from clinical_mdr_api.domains.study_selections.study_soa_group_selection import (
    StudySoAGroupVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityForStudyActivity,
    ActivityHierarchySimpleModel,
)
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.study_selections.study_selection import (
    DetailedSoAHistory,
    StudyActivityReplaceActivityInput,
    StudyActivitySchedule,
    StudyActivityScheduleCreateInput,
    StudyActivityScheduleDeleteInput,
    StudyActivitySyncLatestVersionInput,
    StudySelectionActivity,
    StudySelectionActivityBatchDeleteInput,
    StudySelectionActivityBatchInput,
    StudySelectionActivityBatchOutput,
    StudySelectionActivityBatchUpdateInput,
    StudySelectionActivityCore,
    StudySelectionActivityCreateInput,
    StudySelectionActivityInput,
    StudySelectionActivityInSoACreateInput,
    StudySelectionActivityRequestEditInput,
    StudySelectionActivityReviewBatchInput,
    StudySelectionReviewAction,
    StudySoAEditBatchInput,
    StudySoAEditBatchOutput,
    UpdateActivityPlaceholderToSponsorActivity,
)
from clinical_mdr_api.models.utils import BaseModel, GenericFilteringReturn
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    ensure_transaction,
    fill_missing_values_in_base_model_from_reference_base_model,
)
from clinical_mdr_api.services.concepts.activities.activity_group_service import (
    ActivityGroupService,
)
from clinical_mdr_api.services.concepts.activities.activity_sub_group_service import (
    ActivitySubGroupService,
)
from clinical_mdr_api.services.studies.study_activity_group import (
    StudyActivityGroupService,
)
from clinical_mdr_api.services.studies.study_activity_instruction import (
    StudyActivityInstructionService,
)
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.services.studies.study_activity_selection_base import (
    StudyActivitySelectionBaseService,
)
from clinical_mdr_api.services.studies.study_activity_subgroup import (
    StudyActivitySubGroupService,
)
from clinical_mdr_api.services.studies.study_soa_group import StudySoAGroupService
from common.auth.user import user
from common.config import settings
from common.exceptions import (
    AlreadyExistsException,
    BusinessLogicException,
    MDRApiBaseException,
    MethodNotAllowedException,
    NotFoundException,
    ValidationException,
)
from common.telemetry import trace_block, trace_calls


class StudyActivitySelectionService(
    StudyActivitySelectionBaseService[
        StudySelectionActivityAR, StudySelectionActivityVO, StudySelectionActivity
    ]
):
    _repos: MetaRepository
    repository_interface = StudySelectionActivityRepository
    selected_object_repository_interface = ActivityRepository

    _vo_to_ar_filter_map = {
        "order": "order",
        "activity.name": "activity_name",
        "study_activity_group.activity_group_name": "activity_group_name",
        "study_activity_subgroup.activity_subgroup_name": "activity_subgroup_name",
        "start_date": "start_date",
        "author_id": "author_id",
        "activity.library_name": "activity_library_name",
    }

    def _get_selected_object_exist_check(self) -> Callable[[str], bool]:
        return self.selected_object_repository.final_or_replaced_retired_activity_exists

    def _transform_from_vo_to_response_model(
        self,
        study_uid: str,
        specific_selection: StudySelectionActivityVO,
        terms_at_specific_datetime: datetime | None = None,
        accepted_version: bool = False,
        study_value_version: str | None = None,
        activity_versions_by_uid: (
            Mapping[str, Sequence[ActivityForStudyActivity]] | None
        ) = None,
    ) -> StudySelectionActivity:
        return StudySelectionActivity.from_study_selection_activity_vo_and_order(
            study_uid=study_uid,
            study_selection=specific_selection,
            accepted_version=accepted_version,
            get_activity_by_uid_callback=self._transform_latest_activity_model,
            get_activity_by_uid_version_callback=self._transform_activity_model,
            get_ct_term_flowchart_group=self._find_by_uid_or_raise_not_found,
            terms_at_specific_datetime=terms_at_specific_datetime,
            study_value_version=study_value_version,
            activity_versions_by_uid=activity_versions_by_uid,
        )

    @staticmethod
    def get_default_sorting() -> dict[str, bool] | None:
        return {
            "study_soa_group.order": True,
            "study_activity_group.order": True,
            "study_activity_subgroup.order": True,
            "order": True,
        }

    def _find_ar_and_validate_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> StudySelectionActivityAR:
        study_activity_to_reorder: StudySelectionActivityVO
        selection_aggregate, study_activity_to_reorder = self._find_ar_to_patch(
            study_uid=study_uid, study_selection_uid=study_selection_uid
        )

        BusinessLogicException.raise_if(
            new_order == study_activity_to_reorder.order,
            msg=f"The order ({new_order}) for study activity {study_activity_to_reorder.activity_name} was not changed",
        )
        if (
            study_activity_to_reorder.study_activity_subgroup_uid is None
            and study_activity_to_reorder.activity_library_name
            == settings.requested_library_name
        ):
            max_order = len(selection_aggregate.study_objects_selection)
            BusinessLogicException.raise_if(
                new_order > max_order,
                msg=f"""The maximum new order is ({max_order}) as there are {max_order} Study Activities for the same parents ({new_order}) was requested""",
            )
        else:
            study_activity_subgroup: StudySelectionActivitySubGroupVO
            _, study_activity_subgroup, _ = (
                self._get_specific_activity_subgroup_selection_by_uids(
                    study_uid=study_activity_to_reorder.study_uid,
                    study_selection_uid=study_activity_to_reorder.study_activity_subgroup_uid
                    or "",
                )
            )

            subgroup_size = len(study_activity_subgroup.study_activity_uids or [])
            subgroup_name = study_activity_subgroup.activity_subgroup_name
            BusinessLogicException.raise_if(
                new_order > subgroup_size,
                msg=f"""The maximum new order is ({subgroup_size}) as there are {subgroup_size} Study Activities in {subgroup_name} subgroup and order ({new_order}) was requested""",
            )

        return selection_aggregate

    def _filter_ars_from_same_parent(
        self,
        selection_aggregate: StudySelectionActivityAR,
        selection_vo: StudySelectionActivityVO,
    ) -> StudySelectionActivityAR:
        # If given SA is a Requested Activity without subgroup we should find all Requested Activities under the same SoAGroup that are having
        # (not selected) as Activity Subgroup
        if (
            selection_vo.study_activity_subgroup_uid is None
            and selection_vo.activity_library_name == settings.requested_library_name
        ):
            all_selections_from_same_subgroup = [
                selection
                for selection in selection_aggregate.study_objects_selection
                if selection.study_soa_group_uid == selection_vo.study_soa_group_uid
                and selection.activity_library_name == settings.requested_library_name
            ]
        else:
            all_selections_from_same_subgroup = [
                selection
                for selection in selection_aggregate.study_objects_selection
                if selection.study_activity_subgroup_uid
                == selection_vo.study_activity_subgroup_uid
            ]
        selection_ar_from_same_subgroup = (
            StudySelectionActivityAR.from_repository_values(
                study_uid=selection_aggregate.study_uid,
                study_objects_selection=all_selections_from_same_subgroup,
            )
        )
        selection_ar_from_same_subgroup.repository_closure_data = (
            all_selections_from_same_subgroup
        )
        return selection_ar_from_same_subgroup

    def _validate_no_study_wide_duplicate(
        self,
        study_uid: str,
        updated_selection: StudySelectionActivityVO,
    ) -> None:
        """Check that the updated selection doesn't duplicate an existing activity
        with the same name and groupings anywhere in the study.

        The AR-level validate() only sees a scoped subset (same study_activity_subgroup_uid),
        so duplicates across different subgroup scopes would slip through without this check.
        """
        AlreadyExistsException.raise_if(
            self.repository.activity_with_same_groupings_exists(
                study_uid=study_uid,
                activity_name=updated_selection.activity_name,
                activity_subgroup_uid=updated_selection.activity_subgroup_uid,
                activity_group_uid=updated_selection.activity_group_uid,
                exclude_study_selection_uid=updated_selection.study_selection_uid,
            ),
            msg=(
                f"There is already a Study Selection to the activity with Name "
                f"'{updated_selection.activity_name}' with the same groupings."
            ),
        )

    def _update_aggregate(
        self,
        selection_aggregate: StudySelectionActivityAR,
        updated_selection: StudySelectionActivityVO,
        previous_selection: StudySelectionActivityVO | None = None,
    ) -> StudySelectionActivityVO:
        updated_vo: StudySelectionActivityVO | None = None
        # Only re-validate uniqueness when fields that affect duplicate detection have actually changed
        if (
            previous_selection.activity_name != updated_selection.activity_name
            or previous_selection.activity_subgroup_uid
            != updated_selection.activity_subgroup_uid
            or previous_selection.activity_group_uid
            != updated_selection.activity_group_uid
        ):
            self._validate_no_study_wide_duplicate(
                study_uid=selection_aggregate.study_uid,
                updated_selection=updated_selection,
            )
        if (
            previous_selection.study_activity_subgroup_uid
            != updated_selection.study_activity_subgroup_uid
        ) or (
            updated_selection.activity_library_name == settings.requested_library_name
            and updated_selection.study_activity_subgroup_uid is None
            and previous_selection.study_soa_group_uid
            != updated_selection.study_soa_group_uid
        ):
            find_requested = (
                updated_selection.activity_library_name
                == settings.requested_library_name
            )
            activity_ar_cache_key = (
                updated_selection.study_activity_subgroup_uid,
                updated_selection.study_soa_group_uid,
                find_requested,
            )
            ar_cache_key = self._get_batch_ar_cache_key(*activity_ar_cache_key)
            if self._batch_cache is not None and ar_cache_key in self._batch_cache:
                new_selection_aggregate = self._batch_cache[ar_cache_key]
            else:
                new_selection_aggregate = self.repository.find_by_study(
                    study_uid=selection_aggregate.study_uid,
                    for_update=True,
                    study_activity_subgroup_uid=updated_selection.study_activity_subgroup_uid,
                    study_soa_group_uid=updated_selection.study_soa_group_uid,
                    find_requested_study_activities=find_requested,
                )
                if self._batch_cache is not None:
                    self._batch_cache[ar_cache_key] = new_selection_aggregate
            new_selection_aggregate.add_object_selection(
                updated_selection,
                object_exist_callback=self._get_selected_object_exist_check(),
                ct_term_level_exist_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
            )
            new_selection_aggregate.add_selection_to_closure_from_other_ar(
                updated_selection
            )
            new_selection_aggregate.validate()
            self.repository.save(new_selection_aggregate, author_id=self.author)
            # Invalidate Activity cache only when activity_uid changed (used_by_studies affected)
            if previous_selection.activity_uid != updated_selection.activity_uid:
                with self._repos.activity_repository.lock_store_item_by_uid:
                    self._repos.activity_repository.cache_store_item_by_uid.clear()
            # Grab the VO with the correct order written back by save()
            updated_vo = new_selection_aggregate.get_specific_object_selection(
                updated_selection.study_selection_uid
            )[
                0
            ]  # type: ignore[assignment]
            # Keep closure current so the next batch-mode PATCH with the same destination scope
            # sees the already-saved state and only diffs its own new selection.
            if self._batch_cache is not None:
                new_selection_aggregate.repository_closure_data = (
                    new_selection_aggregate.study_objects_selection
                )

            selection_aggregate.remove_object_selection(
                updated_selection.study_selection_uid
            )
            selection_aggregate.add_selection_to_closure_from_other_ar(
                updated_selection
            )
            # Evict the old-scope AR from the activity cache. The moved activity is no longer in
            # that scope on DB, but the cached AR's repository_closure_data still contains it.
            # A subsequent batch POST to the old scope would reuse the stale AR and the save diff
            # would try to issue a redundant Delete audit node for the already-moved activity.
            if self._batch_cache is not None:
                old_find_requested = (
                    previous_selection.activity_library_name
                    == settings.requested_library_name
                )
                old_scope_key = (
                    previous_selection.study_activity_subgroup_uid,
                    previous_selection.study_soa_group_uid,
                    old_find_requested,
                )
                old_cache_key = self._get_batch_ar_cache_key(*old_scope_key)
                self._batch_cache.pop(old_cache_key, None)
            # Recompact SoAGroup / ActivitySubGroup / ActivityGroup orders under the *old* parent
            # in case this SA was the last one there and the hierarchy node becomes invisible.
            # In batch mode, each unique old-parent scope is reordered at most once.
            soa_reorder_key = self._get_batch_reordered_key("soa")
            if self._batch_cache is None or soa_reorder_key not in self._batch_cache:
                study_soa_group_aggregate = (
                    self._repos.study_soa_group_repository.find_by_study(
                        study_uid=previous_selection.study_uid,
                        for_update=True,
                    )
                )
                is_soa_group_update_needed = False
                for new_order, study_soa_group_selection in enumerate(
                    study_soa_group_aggregate.study_objects_selection, start=1
                ):
                    if study_soa_group_selection.order != new_order:
                        is_soa_group_update_needed = True
                        reordered_study_soa_group_selection = dataclasses.replace(
                            study_soa_group_selection, order=new_order
                        )
                        study_soa_group_aggregate.update_selection(
                            updated_study_object_selection=reordered_study_soa_group_selection,
                        )
                if is_soa_group_update_needed:
                    study_soa_group_aggregate.validate()
                    self._repos.study_soa_group_repository.save(
                        study_soa_group_aggregate, self.author
                    )
                if self._batch_cache is not None:
                    self._batch_cache[soa_reorder_key] = True

            subgroup_reorder_key = self._get_batch_reordered_key(
                "subgroup", previous_selection.study_activity_group_uid
            )
            if previous_selection.study_activity_subgroup_uid and (
                self._batch_cache is None
                or subgroup_reorder_key not in self._batch_cache
            ):
                study_activity_subgroup_aggregate = self._repos.study_activity_subgroup_repository.find_by_study(
                    study_uid=previous_selection.study_uid,
                    for_update=True,
                    study_activity_group_uid=previous_selection.study_activity_group_uid,
                )
                is_study_activity_subgroup_update_needed = False
                for new_order, study_activity_subgroup_selection in enumerate(
                    study_activity_subgroup_aggregate.study_objects_selection, start=1
                ):
                    if study_activity_subgroup_selection.order != new_order:
                        is_study_activity_subgroup_update_needed = True
                        reordered_study_activity_subgroup_selection = (
                            dataclasses.replace(
                                study_activity_subgroup_selection, order=new_order
                            )
                        )
                        study_activity_subgroup_aggregate.update_selection(
                            updated_study_object_selection=reordered_study_activity_subgroup_selection,
                        )
                if is_study_activity_subgroup_update_needed:
                    study_activity_subgroup_aggregate.validate()
                    self._repos.study_activity_subgroup_repository.save(
                        study_activity_subgroup_aggregate, self.author
                    )
                if self._batch_cache is not None:
                    self._batch_cache[subgroup_reorder_key] = True

            group_reorder_key = self._get_batch_reordered_key(
                "group", previous_selection.study_soa_group_uid
            )
            if previous_selection.study_activity_group_uid and (
                self._batch_cache is None or group_reorder_key not in self._batch_cache
            ):
                study_activity_group_aggregate = (
                    self._repos.study_activity_group_repository.find_by_study(
                        study_uid=previous_selection.study_uid,
                        for_update=True,
                        study_soa_group_uid=previous_selection.study_soa_group_uid,
                    )
                )
                is_study_activity_group_update_needed = False
                for new_order, study_activity_group_selection in enumerate(
                    study_activity_group_aggregate.study_objects_selection, start=1
                ):
                    if study_activity_group_selection.order != new_order:
                        is_study_activity_group_update_needed = True
                        reordered_study_activity_group_selection = dataclasses.replace(
                            study_activity_group_selection, order=new_order
                        )
                        study_activity_group_aggregate.update_selection(
                            updated_study_object_selection=reordered_study_activity_group_selection,
                        )
                if is_study_activity_group_update_needed:
                    study_activity_group_aggregate.validate()
                    self._repos.study_activity_group_repository.save(
                        study_activity_group_aggregate, self.author
                    )
                if self._batch_cache is not None:
                    self._batch_cache[group_reorder_key] = True
        else:
            # let the aggregate update the value object
            selection_aggregate.update_selection(
                updated_study_object_selection=updated_selection,
                object_exist_callback=self._get_selected_object_exist_check(),
                ct_term_level_exist_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
            )
        selection_aggregate.validate()
        self.repository.save(selection_aggregate, self.author)
        # Invalidate Activity cache only when activity_uid changed (used_by_studies affected).
        if (
            previous_selection is not None
            and previous_selection.activity_uid != updated_selection.activity_uid
        ):
            with self._repos.activity_repository.lock_store_item_by_uid:
                self._repos.activity_repository.cache_store_item_by_uid.clear()
        # In the no-parent-change case the activity stayed in selection_aggregate;
        # grab the VO with the correct order written back by save().
        if updated_vo is None:
            updated_vo = selection_aggregate.get_specific_object_selection(
                updated_selection.study_selection_uid
            )[
                0
            ]  # type: ignore[assignment]
        return updated_vo

    def update_dependent_objects(
        self,
        study_selection: StudySelectionActivityVO,
        previous_study_selection: StudySelectionActivityVO,
    ):
        # If Activity selected by StudyActivity was changed we need to recreate StudyActivityInstances
        if (
            previous_study_selection is not None
            and study_selection.activity_uid != previous_study_selection.activity_uid
        ):
            self._recreate_study_activity_instances_after_activity_replacement(
                study_uid=study_selection.study_uid,
                study_activity_selection=study_selection,
            )

    def _replicate_schedules_to_study_activity(
        self,
        study_uid: str,
        target_study_activity_uid: str,
        schedules_to_replicate: list[StudyActivitySchedule],
    ) -> list[str]:
        """
        Replicates StudyActivitySchedules to target StudyActivity.
        Creates new schedule nodes for the target StudyActivity with the same study_visit_uid.

        Args:
            study_uid: Study UID
            target_study_activity_uid: Target StudyActivity UID to create schedules for
            schedules_to_replicate: List of StudyActivitySchedule objects to replicate

        Returns:
            List of newly created schedule UIDs
        """
        schedule_service = StudyActivityScheduleService()
        new_schedule_uids = []

        for schedule in schedules_to_replicate:
            # Create a new schedule for the target StudyActivity with the same visit
            new_schedule = schedule_service.create(
                study_uid=study_uid,
                schedule_input=StudyActivityScheduleCreateInput(
                    study_activity_uid=target_study_activity_uid,
                    study_visit_uid=schedule.study_visit_uid,
                ),
            )
            new_schedule_uids.append(new_schedule.study_activity_schedule_uid)

        return new_schedule_uids

    @ensure_transaction(db)
    def replace_study_activity_with_multiple_activities(
        self,
        study_uid: str,
        study_activity_uid: str,
        replacements: list[StudyActivityReplaceActivityInput],
    ) -> list[StudySelectionActivity]:
        """
        Replaces a StudyActivity with multiple activities.
        - Multiple replacements are only allowed when replacing a StudyActivity placeholder (activity in 'Requested' library).
        - First item in the list replaces the original StudyActivity
        - Remaining items create new StudyActivities
        - Schedules are preserved for the replaced StudyActivity and replicated to all new ones
        - StudyActivityInstances are recreated for the replaced StudyActivity and newly created StudyActivities
        """
        if not replacements:
            raise ValidationException(
                msg="At least one replacement must be provided in the replacements list."
            )

        # Get the original StudyActivity
        _, current_vo = self._find_ar_to_patch(
            study_uid=study_uid, study_selection_uid=study_activity_uid
        )
        NotFoundException.raise_if_not(
            current_vo,
            "Study Activity",
            study_activity_uid,
        )

        # Only allow multiple replacements if the original StudyActivity is a placeholder
        # (i.e., activity is in the "Requested" library)
        is_placeholder = (
            current_vo.activity_library_name == settings.requested_library_name
        )
        if not is_placeholder and len(replacements) > 1:
            raise BusinessLogicException(
                msg=(
                    "Multiple activity replacements are only allowed when replacing "
                    "a StudyActivity placeholder (activity in 'Requested' library). "
                    "For regular StudyActivities, only one replacement is allowed."
                )
            )

        # Get existing schedules for the original StudyActivity
        schedule_service = StudyActivityScheduleService()
        existing_schedules = schedule_service.get_all_schedules_for_specific_activity(
            study_uid=study_uid, study_activity_uid=study_activity_uid
        )
        results: list[StudySelectionActivity] = []
        replacement_target_uids: list[str] = []

        # Process first item: Replace the original StudyActivity
        first_replacement = replacements[0]
        replaced_study_activity = self.patch_selection(
            study_uid=study_uid,
            study_selection_uid=study_activity_uid,
            selection_update_input=first_replacement,
        )
        if replaced_study_activity.study_activity_uid is None:
            raise BusinessLogicException(
                msg="Failed to replace StudyActivity. Study Activity UID is missing."
            )
        replacement_target_uids.append(replaced_study_activity.study_activity_uid)
        results.append(replaced_study_activity)

        # Process remaining items: Create new StudyActivities
        for replacement in replacements[1:]:
            # Validate activity groupings using the same validation as patch_selection
            activity_ar = self._repos.activity_repository.find_by_uid(
                replacement.activity_uid
            )
            NotFoundException.raise_if_not(
                activity_ar, "Activity", replacement.activity_uid
            )

            # Create a minimal current_object for validation (only activity_uid is used in error messages)
            minimal_current_object = StudySelectionActivityVO.from_input_values(
                study_uid=study_uid,
                activity_uid=replacement.activity_uid,
                activity_version=activity_ar.item_metadata.version,
                study_soa_group_uid="",  # Not used in validation
                soa_group_term_uid="",  # Not used in validation
                author_id=self.author,
            )

            self._validate_new_activity_groupings(
                request_object=replacement,
                activity_ar=activity_ar,
                current_object=minimal_current_object,
            )

            # Validate soa_group_term_uid is provided (required for create)
            if not replacement.soa_group_term_uid:
                raise ValidationException(
                    msg="soa_group_term_uid is required when creating a new StudyActivity."
                )

            # Convert replacement to create input
            create_input = StudySelectionActivityCreateInput(
                activity_uid=replacement.activity_uid,
                activity_group_uid=replacement.activity_group_uid,
                activity_subgroup_uid=replacement.activity_subgroup_uid,
                soa_group_term_uid=replacement.soa_group_term_uid,
            )

            # Create new StudyActivity
            # Note: make_selection will automatically create StudyActivityInstances for non-placeholder activities
            new_study_activity = self.make_selection(
                study_uid=study_uid, selection_create_input=create_input
            )

            # Replicate schedules to the new StudyActivity
            # Use the schedules we fetched before replacement (they're still valid)
            assert (
                new_study_activity.study_activity_uid is not None
            ), "Newly created StudyActivity must have a study_activity_uid"
            self._replicate_schedules_to_study_activity(
                study_uid=study_uid,
                target_study_activity_uid=new_study_activity.study_activity_uid,
                schedules_to_replicate=existing_schedules,
            )

            replacement_target_uids.append(new_study_activity.study_activity_uid)
            results.append(new_study_activity)

        if is_placeholder:
            self._repos.study_activity_repository.create_replaced_by_links_from_previous_version(
                study_uid=study_uid,
                source_study_activity_uid=study_activity_uid,
                target_study_activity_uids=replacement_target_uids,
            )

        return results

    def _validate_activity(self, activity_uid: str) -> ActivityAR:
        activity_ar: ActivityAR | None = self._repos.activity_repository.find_by_uid(
            activity_uid
        )

        NotFoundException.raise_if_not(activity_ar, "Activity", activity_uid)

        BusinessLogicException.raise_if(
            activity_ar.item_metadata.status
            in [
                LibraryItemStatus.DRAFT,
                LibraryItemStatus.RETIRED,
            ],
            msg=f"There is no approved Activity with name '{activity_ar.name}'.",
        )
        return activity_ar

    def _create_value_object(
        self,
        study_uid: str,
        selection_create_input: StudySelectionActivityCreateInput,
        activity_ar: ActivityAR,
        **kwargs,
    ):
        # activity_ar: ActivityAR = kwargs.get("activity_ar")
        study_soa_group_selection_uid = kwargs["study_soa_group_selection_uid"]
        study_soa_group_order = kwargs.get("study_soa_group_order")
        study_activity_subgroup_selection_uid = kwargs.get(
            "study_activity_subgroup_selection_uid"
        )
        study_activity_subgroup_order = kwargs.get("study_activity_subgroup_order")
        study_activity_group_selection_uid = kwargs.get(
            "study_activity_group_selection_uid"
        )
        study_activity_group_order = kwargs.get("study_activity_group_order")
        activity_group_name = kwargs.get("activity_group_name")
        activity_subgroup_name = kwargs.get("activity_subgroup_name")
        show_soa_group_in_protocol_flowchart = kwargs.get(
            "show_soa_group_in_protocol_flowchart", False
        )
        show_activity_group_in_protocol_flowchart = kwargs.get(
            "show_activity_group_in_protocol_flowchart", True
        )
        show_activity_subgroup_in_protocol_flowchart = kwargs.get(
            "show_activity_subgroup_in_protocol_flowchart", True
        )

        BusinessLogicException.raise_if(
            activity_ar.library.name != settings.requested_library_name
            and (
                selection_create_input.activity_subgroup_uid is None
                or selection_create_input.activity_group_uid is None
            ),
            msg="Only StudyActivity placeholder can link to None ActivitySubGroup or None ActivityGroup",
        )
        BusinessLogicException.raise_if(
            selection_create_input.activity_subgroup_uid
            and selection_create_input.activity_subgroup_uid
            not in [
                grouping.activity_subgroup_uid
                for grouping in activity_ar.concept_vo.activity_groupings
            ],
            msg=f"The specified Subgroup with UID '{selection_create_input.activity_subgroup_uid}' is not linked with Activity with Name '{activity_ar.name}'.",
        )
        BusinessLogicException.raise_if(
            selection_create_input.activity_group_uid
            and selection_create_input.activity_group_uid
            not in [
                grouping.activity_group_uid
                for grouping in activity_ar.concept_vo.activity_groupings
            ],
            msg=f"The specified Group with UID '{selection_create_input.activity_group_uid}' is not linked with Activity with Name '{activity_ar.name}'.",
        )
        # create new VO to add
        new_selection = StudySelectionActivityVO.from_input_values(
            study_uid=study_uid,
            author_id=self.author,
            activity_uid=activity_ar.uid,
            activity_name=activity_ar.name,
            activity_version=activity_ar.item_metadata.version,
            activity_library_name=activity_ar.library.name,
            soa_group_term_uid=selection_create_input.soa_group_term_uid,
            study_soa_group_uid=study_soa_group_selection_uid,
            study_soa_group_order=study_soa_group_order,
            study_activity_subgroup_uid=study_activity_subgroup_selection_uid,
            study_activity_subgroup_order=study_activity_subgroup_order,
            study_activity_group_uid=study_activity_group_selection_uid,
            study_activity_group_order=study_activity_group_order,
            activity_group_name=activity_group_name,
            activity_subgroup_name=activity_subgroup_name,
            show_soa_group_in_protocol_flowchart=show_soa_group_in_protocol_flowchart,
            show_activity_group_in_protocol_flowchart=show_activity_group_in_protocol_flowchart,
            show_activity_subgroup_in_protocol_flowchart=show_activity_subgroup_in_protocol_flowchart,
            order=None,
            generate_uid_callback=self.repository.generate_uid,
            activity_subgroup_uid=selection_create_input.activity_subgroup_uid,
            activity_group_uid=selection_create_input.activity_group_uid,
            show_activity_in_protocol_flowchart=selection_create_input.show_activity_in_protocol_flowchart,
        )
        return new_selection

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionActivityAR | None,
        study_value_version: str | None = None,
        **kwargs,
    ) -> list[StudySelectionActivity]:
        if study_selection is None:
            return []

        activity_versions_by_uid: dict[str, list[ActivityForStudyActivity]] = (
            defaultdict(list)
        )
        filter_out_retired_groupings = kwargs.get("filter_out_retired_groupings", False)
        for activity in self._get_linked_activities(
            # filter_out_retired_groupings removes Activity Group/Subgroup pair if any of these is Retired
            study_selection.study_objects_selection,
            filter_out_retired_groupings=filter_out_retired_groupings,
        ):
            activity_versions_by_uid[activity.uid].append(
                ActivityForStudyActivity.from_activity_ar_objects(
                    activity,
                    activity_instance_ars=[
                        ActivityHierarchySimpleModel(**item)
                        for item in activity.concept_vo.activity_instances
                    ],
                )
            )

        return [
            self._transform_from_vo_to_response_model(
                study_uid=selection.study_uid,
                specific_selection=selection,
                accepted_version=selection.accepted_version,
                study_value_version=study_value_version,
                activity_versions_by_uid=activity_versions_by_uid,
            )
            for selection in study_selection.study_objects_selection
        ]

    def _transform_history_to_response_model(
        self,
        study_selection_history: list[SelectionHistory],
        study_uid: str,
        effective_dates: list[datetime | None] | None = None,
    ) -> list[StudySelectionActivityCore]:
        if effective_dates is None:
            effective_dates = []
        result = []
        for history, effective_date in zip(study_selection_history, effective_dates):
            result.append(
                StudySelectionActivityCore.from_study_selection_history(
                    study_selection_history=history,
                    study_uid=study_uid,
                    get_activity_by_uid_version_callback=self._transform_activity_model,
                    get_ct_term_flowchart_group=self._find_by_uid_or_raise_not_found,
                    effective_date=effective_date,
                )
            )
        return result

    def get_all_selection_audit_trail(self, study_uid: str) -> list[BaseModel]:
        repos = self._repos
        try:
            try:
                selection_history = self.repository.find_selection_history(study_uid)
            except ValueError as value_error:
                raise NotFoundException(msg=value_error.args[0]) from value_error
            # Extract start dates from the selection history
            start_dates = [history.start_date for history in selection_history]

            # Extract effective dates for each version based on the start dates
            effective_dates = (
                self._extract_multiple_version_study_standards_effective_date(
                    study_uid=study_uid, list_of_start_dates=start_dates
                )
            )
            return self._transform_history_to_response_model(
                selection_history,
                study_uid,
                effective_dates=effective_dates,
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
                raise NotFoundException(msg=value_error.args[0]) from value_error

            # Extract start dates from the selection history
            start_dates = [history.start_date for history in selection_history]

            # Extract effective dates for each version based on the start dates
            effective_dates = (
                self._extract_multiple_version_study_standards_effective_date(
                    study_uid=study_uid, list_of_start_dates=start_dates
                )
            )
            return self._transform_history_to_response_model(
                selection_history,
                study_uid,
                effective_dates=effective_dates,
            )
        finally:
            repos.close()

    def _create_activity_subgroup_selection_value_object(
        self,
        study_uid: str,
        activity_subgroup_uid: str,
        perform_subgroup_validation: bool = True,
        activity_subgroup_version: str | None = None,
        current_object: StudySelectionActivityVO | None = None,
    ):
        activity_subgroup_ar = self._validate_activity_subgroup(
            activity_subgroup_uid=activity_subgroup_uid,
            perform_subgroup_validation=perform_subgroup_validation,
            activity_subgroup_version=activity_subgroup_version,
        )

        # create new VO to add
        new_selection = StudySelectionActivitySubGroupVO.from_input_values(
            study_uid=study_uid,
            author_id=self.author,
            activity_subgroup_uid=activity_subgroup_uid,
            activity_subgroup_name=activity_subgroup_ar.concept_vo.name,
            activity_subgroup_version=activity_subgroup_ar.item_metadata.version,
            generate_uid_callback=self._repos.study_activity_subgroup_repository.generate_uid,
            show_activity_subgroup_in_protocol_flowchart=(
                current_object.show_activity_subgroup_in_protocol_flowchart
                if current_object
                else True
            ),
        )
        return new_selection

    @classmethod
    def _validate_activity_subgroup(
        cls,
        activity_subgroup_uid: str,
        perform_subgroup_validation: bool = True,
        activity_subgroup_version: str | None = None,
    ) -> ActivitySubGroupAR:
        activity_subgroup_service = ActivitySubGroupService()
        activity_subgroup_ar = activity_subgroup_service.repository.find_by_uid(
            activity_subgroup_uid, version=activity_subgroup_version
        )
        NotFoundException.raise_if_not(
            activity_subgroup_ar, "Activity Subgroup", activity_subgroup_uid
        )

        NotFoundException.raise_if(
            activity_subgroup_ar.item_metadata.status
            in [
                LibraryItemStatus.DRAFT,
                LibraryItemStatus.RETIRED,
            ]
            and perform_subgroup_validation,
            msg=f"Activity Subgroup '{activity_subgroup_ar.concept_vo.name}' with UID '{activity_subgroup_uid}' has status {activity_subgroup_ar.item_metadata.status.value}."
            " Only Final subgroups can be added to a study."
            " Contact OpenStudyBuilder library responsible for updates.",
        )
        return activity_subgroup_ar

    @classmethod
    def _validate_activity_group(
        cls,
        activity_group_uid: str,
        perform_group_validation: bool = True,
        activity_group_version: str | None = None,
    ) -> ActivityGroupAR:
        activity_group_service = ActivityGroupService()
        activity_group_ar = activity_group_service.repository.find_by_uid(
            activity_group_uid, version=activity_group_version
        )

        NotFoundException.raise_if_not(
            activity_group_ar, "Activity Group", activity_group_uid
        )

        NotFoundException.raise_if(
            activity_group_ar.item_metadata.status
            in [
                LibraryItemStatus.DRAFT,
                LibraryItemStatus.RETIRED,
            ]
            and perform_group_validation,
            msg=f"Activity Group '{activity_group_ar.concept_vo.name}' with UID '{activity_group_uid}' has status {activity_group_ar.item_metadata.status.value}."
            " Only Final groups can be added to a study."
            " Contact OpenStudyBuilder library responsible for updates.",
        )
        return activity_group_ar

    def _create_activity_group_selection_value_object(
        self,
        study_uid: str,
        activity_group_uid: str,
        perform_group_validation: bool = True,
        activity_group_version: str | None = None,
        current_object: StudySelectionActivityVO | None = None,
    ):
        activity_group_ar = self._validate_activity_group(
            activity_group_uid=activity_group_uid,
            perform_group_validation=perform_group_validation,
            activity_group_version=activity_group_version,
        )
        # create new VO to add
        new_selection = StudySelectionActivityGroupVO.from_input_values(
            study_uid=study_uid,
            author_id=self.author,
            activity_group_uid=activity_group_uid,
            activity_group_name=activity_group_ar.concept_vo.name,
            activity_group_version=activity_group_ar.item_metadata.version,
            generate_uid_callback=self._repos.study_activity_group_repository.generate_uid,
            show_activity_group_in_protocol_flowchart=(
                current_object.show_activity_group_in_protocol_flowchart
                if current_object
                else True
            ),
        )
        return new_selection

    def _patch_selected_activity(
        self,
        current_object: StudySelectionActivityVO,
        request_object: StudySelectionActivityRequestEditInput,
    ) -> ActivityAR:
        activity_ar = self._repos.activity_repository.find_by_uid_2(
            current_object.activity_uid, for_update=True
        )

        NotFoundException.raise_if_not(
            activity_ar, "Activity", current_object.activity_uid
        )

        BusinessLogicException.raise_if(
            activity_ar.item_metadata.status
            not in [
                LibraryItemStatus.FINAL,
                LibraryItemStatus.DRAFT,
            ],
            msg=f"The underlying Activity with UID '{current_object.activity_uid}' must be in Draft or Final status.",
        )
        if activity_ar.item_metadata.status == LibraryItemStatus.FINAL:
            activity_ar.create_new_version(author_id=self.author)
            self._repos.activity_repository.save(activity_ar)
        if request_object.activity_name:
            activity_name = request_object.activity_name
        else:
            activity_name = current_object.activity_name or ""
        # This method is called only in scope for the ActivityRequest edition.
        # It means that we are sure that we have just one grouping linked to the ActivityRequest.
        activity_groupings = []
        if request_object.activity_subgroup_uid or request_object.activity_group_uid:
            activity_subgroup_uid = None
            activity_group_uid = None
            if activity_ar.concept_vo.activity_groupings:
                activity_grouping = activity_ar.concept_vo.activity_groupings[0]
                activity_subgroup_uid = activity_grouping.activity_subgroup_uid
                activity_group_uid = activity_grouping.activity_group_uid
            activity_subgroup_uid = (
                request_object.activity_subgroup_uid
                if request_object.activity_subgroup_uid
                else activity_subgroup_uid
            )
            activity_group_uid = (
                request_object.activity_group_uid
                if request_object.activity_group_uid
                else activity_group_uid
            )
            activity_grouping = ActivityGroupingVO(
                activity_subgroup_uid=activity_subgroup_uid or "",
                activity_group_uid=activity_group_uid or "",
            )
            activity_groupings.append(activity_grouping)
        activity_ar.edit_draft(
            author_id=self.author,
            change_description=None,
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=activity_ar.concept_vo.nci_concept_id,
                nci_concept_name=activity_ar.concept_vo.nci_concept_name,
                name=activity_name,
                name_sentence_case=activity_name.lower(),
                synonyms=activity_ar.concept_vo.synonyms,
                definition=activity_ar.concept_vo.definition,
                abbreviation=activity_ar.concept_vo.abbreviation,
                activity_groupings=activity_groupings,
                activity_instances=[],
                request_rationale=(
                    request_object.request_rationale
                    if request_object.request_rationale is not None
                    else activity_ar.concept_vo.request_rationale
                ),
                is_request_final=(
                    request_object.is_request_final
                    if request_object.is_request_final is not None
                    else activity_ar.concept_vo.is_request_final
                ),
                is_data_collected=(
                    request_object.is_data_collected
                    if request_object.is_data_collected is not None
                    else activity_ar.concept_vo.is_data_collected
                ),
                is_multiple_selection_allowed=activity_ar.concept_vo.is_multiple_selection_allowed,
            ),
            concept_exists_by_library_and_name_callback=self._repos.activity_repository.latest_concept_in_library_exists_by_name,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
        )
        self._repos.activity_repository.save(activity_ar)
        activity_ar.approve(
            author_id=self.author,
            change_description="Created new version from the StudyActivityRequest Edit",
        )
        self._repos.activity_repository.save(activity_ar)
        return activity_ar

    def _patch_soa_group_selection_value_object(
        self,
        study_uid: str,
        current_study_activity: StudySelectionActivityVO,
        selection_create_input: StudySelectionActivityInput,
        is_soa_group_changed: bool,
    ):
        soa_group_term_uid = str(selection_create_input.soa_group_term_uid)
        if not is_soa_group_changed:
            # SoA group unchanged — build a lightweight VO from known values; avoids find_by_study round-trip
            return StudySoAGroupVO.from_input_values(
                study_uid=study_uid,
                author_id=self.author,
                soa_group_term_uid=current_study_activity.soa_group_term_uid,
                study_selection_uid=current_study_activity.study_soa_group_uid,
                order=current_study_activity.study_soa_group_order,
                show_soa_group_in_protocol_flowchart=current_study_activity.show_soa_group_in_protocol_flowchart,
            )

        ct_term_ar = self._repos.ct_term_name_repository.find_by_uid(soa_group_term_uid)

        NotFoundException.raise_if_not(
            ct_term_ar, "SoA Group CT Term", soa_group_term_uid
        )

        NotFoundException.raise_if(
            ct_term_ar.item_metadata.status
            in [
                LibraryItemStatus.DRAFT,
                LibraryItemStatus.RETIRED,
            ],
            msg=f"There is no approved SoAGroup CTTerm with UID '{soa_group_term_uid}'.",
        )
        # get VO if possible or create it
        return self._get_or_create_study_soa_group(
            study_uid=study_uid, soa_group_term_uid=soa_group_term_uid
        )

    def _create_soa_group_selection_value_object(
        self, study_uid: str, soa_group_term_uid: str
    ):
        ct_term_ar = self._repos.ct_term_name_repository.find_by_uid(soa_group_term_uid)

        NotFoundException.raise_if_not(
            ct_term_ar, "SoA Group CT Term", soa_group_term_uid
        )

        NotFoundException.raise_if(
            ct_term_ar.item_metadata.status
            in [
                LibraryItemStatus.DRAFT,
                LibraryItemStatus.RETIRED,
            ],
            msg=f"There is no approved SoAGroup CTTerm with UID '{soa_group_term_uid}'.",
        )

        # create new VO to add
        new_selection = StudySoAGroupVO.from_input_values(
            study_uid=study_uid,
            author_id=self.author,
            soa_group_term_uid=soa_group_term_uid,
            generate_uid_callback=self._repos.study_soa_group_repository.generate_uid,
        )
        return new_selection

    def _get_or_create_study_soa_group(
        self, study_uid: str, soa_group_term_uid: str
    ) -> StudySoAGroupVO:
        cache_key = self._get_batch_vo_cache_key("soa", study_uid, soa_group_term_uid)
        if self._batch_cache is not None and cache_key in self._batch_cache:
            return self._batch_cache[cache_key]

        study_soa_group_node = (
            self._repos.study_soa_group_repository.find_study_soa_group_in_a_study(
                study_uid=study_uid,
                soa_group_term_uid=soa_group_term_uid,
            )
        )
        if study_soa_group_node:
            # Node already found — construct a lightweight VO directly; avoids a second find_by_study.
            # Pass the node's order and show_* flag so the VO carries them without a reload.
            study_soa_group_selection = StudySoAGroupVO.from_input_values(
                study_uid=study_uid,
                author_id=self.author,
                soa_group_term_uid=soa_group_term_uid,
                study_selection_uid=study_soa_group_node.uid,
                order=study_soa_group_node.order,
                show_soa_group_in_protocol_flowchart=study_soa_group_node.show_soa_group_in_protocol_flowchart,
            )
        else:
            study_soa_group_selection = self._create_soa_group_selection_value_object(
                study_uid=study_uid,
                soa_group_term_uid=soa_group_term_uid,
            )
            # add VO to aggregate
            study_soa_group_aggregate = (
                self._repos.study_soa_group_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )
            assert study_soa_group_aggregate is not None
            study_soa_group_aggregate.add_object_selection(
                study_soa_group_selection,
            )
            # sync with DB and save the update
            self._repos.study_soa_group_repository.save(
                study_soa_group_aggregate, self.author
            )
            # save() writes the DB-assigned order back into the aggregate; read the updated VO.
            study_soa_group_selection, _ = (
                study_soa_group_aggregate.get_specific_object_selection(
                    study_soa_group_selection.study_selection_uid
                )
            )
        if self._batch_cache is not None:
            self._batch_cache[cache_key] = study_soa_group_selection
        return study_soa_group_selection

    def _get_or_create_study_activity_subgroup(
        self,
        study_uid: str,
        activity_subgroup_uid: str | None,
        activity_group_uid: str | None,
        study_activity_group_uid: str | None,
        soa_group_term_uid: str | None,
        perform_subgroup_validation: bool = True,
        activity_subgroup_version: str | None = None,
        sync_latest_version: bool = False,
        current_object: StudySelectionActivityVO | None = None,
    ) -> StudySelectionActivitySubGroupVO:
        study_activity_subgroup_selection: StudySelectionActivitySubGroupVO | None = (
            None
        )

        if activity_subgroup_uid and activity_group_uid and soa_group_term_uid:
            cache_key = self._get_batch_vo_cache_key(
                "subgroup",
                study_uid,
                activity_subgroup_uid,
                activity_group_uid,
                soa_group_term_uid,
                sync_latest_version,
            )
            if self._batch_cache is not None and cache_key in self._batch_cache:
                return self._batch_cache[cache_key]

            study_activity_subgroup_selection = self._repos.study_activity_subgroup_repository.find_study_activity_subgroup_vo_with_same_groupings(
                study_uid=study_uid,
                activity_subgroup_uid=activity_subgroup_uid,
                activity_group_uid=activity_group_uid,
                soa_group_term_uid=soa_group_term_uid,
                sync_latest_version=sync_latest_version,
            )
            if study_activity_subgroup_selection is None:
                # create new VO to add
                study_activity_subgroup_selection = (
                    self._create_activity_subgroup_selection_value_object(
                        study_uid=study_uid,
                        activity_subgroup_uid=activity_subgroup_uid,
                        perform_subgroup_validation=perform_subgroup_validation,
                        activity_subgroup_version=activity_subgroup_version,
                        current_object=current_object,
                    )
                )
                # add VO to aggregate
                study_activity_subgroup_aggregate = (
                    self._repos.study_activity_subgroup_repository.find_by_study(
                        study_uid=study_uid,
                        for_update=True,
                        study_activity_group_uid=study_activity_group_uid,
                    )
                )
                assert study_activity_subgroup_aggregate is not None
                study_activity_subgroup_aggregate.add_object_selection(
                    study_activity_subgroup_selection,
                    self._repos.activity_subgroup_repository.check_exists_final_version,
                )
                # sync with DB and save the update
                self._repos.study_activity_subgroup_repository.save(
                    study_activity_subgroup_aggregate, self.author
                )
                # save() writes the DB-assigned order back into the aggregate; read the updated VO.
                study_activity_subgroup_selection, _ = (
                    study_activity_subgroup_aggregate.get_specific_object_selection(
                        study_activity_subgroup_selection.study_selection_uid
                    )
                )
            if self._batch_cache is not None:
                self._batch_cache[cache_key] = study_activity_subgroup_selection
        return study_activity_subgroup_selection

    def _get_or_create_study_activity_group(
        self,
        study_uid: str,
        activity_subgroup_uid: str | None,
        activity_group_uid: str | None,
        soa_group_term_uid: str | None,
        study_soa_group_uid: str | None,
        perform_group_validation: bool = True,
        activity_group_version: str | None = None,
        sync_latest_version: bool = False,
        current_object: StudySelectionActivityVO | None = None,
    ) -> StudySelectionActivityGroupVO:
        study_activity_group_selection: StudySelectionActivityGroupVO | None = None
        if (
            activity_subgroup_uid
            and activity_group_uid
            and soa_group_term_uid
            and study_soa_group_uid
        ):
            cache_key = self._get_batch_vo_cache_key(
                "group",
                study_uid,
                activity_group_uid,
                soa_group_term_uid,
                sync_latest_version,
            )
            if self._batch_cache is not None and cache_key in self._batch_cache:
                return self._batch_cache[cache_key]

            study_activity_group_selection = self._repos.study_activity_group_repository.find_study_activity_group_vo_with_same_groupings(
                study_uid=study_uid,
                activity_group_uid=activity_group_uid,
                soa_group_term_uid=soa_group_term_uid,
                sync_latest_version=sync_latest_version,
            )
            if study_activity_group_selection is None:
                # create new VO to add
                study_activity_group_selection = (
                    self._create_activity_group_selection_value_object(
                        study_uid=study_uid,
                        activity_group_uid=activity_group_uid,
                        perform_group_validation=perform_group_validation,
                        activity_group_version=activity_group_version,
                        current_object=current_object,
                    )
                )
                # add VO to aggregate
                study_activity_group_aggregate = (
                    self._repos.study_activity_group_repository.find_by_study(
                        study_uid=study_uid,
                        for_update=True,
                        study_soa_group_uid=study_soa_group_uid,
                    )
                )
                assert study_activity_group_aggregate is not None
                study_activity_group_aggregate.add_object_selection(
                    study_activity_group_selection,
                    self._repos.activity_group_repository.check_exists_final_version,
                )
                # sync with DB and save the update
                self._repos.study_activity_group_repository.save(
                    study_activity_group_aggregate, self.author
                )
                # save() writes the DB-assigned order back into the aggregate; read the updated VO.
                study_activity_group_selection, _ = (
                    study_activity_group_aggregate.get_specific_object_selection(
                        study_activity_group_selection.study_selection_uid
                    )
                )
            if self._batch_cache is not None:
                self._batch_cache[cache_key] = study_activity_group_selection
        return study_activity_group_selection

    def _create_study_activity_instances(
        self, study_uid: str, study_activity_selection: StudySelectionActivityVO
    ):
        # Find ActivityInstances linked to the ActivityGroupings referenced by StudyActivity
        related_activity_instances: list[
            tuple[ActivityInstanceRoot, ActivityInstanceValue]
        ] = self._repos.activity_instance_repository.get_all_activity_instances_for_activity_grouping(
            activity_uid=study_activity_selection.activity_uid,
            activity_subgroup_uid=study_activity_selection.activity_subgroup_uid or "",
            activity_group_uid=study_activity_selection.activity_group_uid or "",
            filter_by_boolean_flags=True,
        )

        linked_activity_instances: dict[str | None, bool] = {}
        for (
            activity_instance_root,
            activity_instance_value,
        ) in related_activity_instances:
            linked_activity_instances.setdefault(
                activity_instance_root.uid,
                activity_instance_value.is_required_for_activity,
            )

        # If there is no ActivityInstances linked to selected Activity
        # we create a 'placeholder' StudyActivityInstance that can link to ActivityInstance later
        if len(linked_activity_instances) == 0:
            linked_activity_instances[None] = False

        # In batch mode reuse the cached AR so all POSTs share one find_by_study + one save;
        # in non-batch mode load fresh and save immediately as before.
        if self._batch_instance_ar is not None:
            study_activity_instance_aggregate = self._batch_instance_ar
        else:
            study_activity_instance_aggregate = (
                self._repos.study_activity_instance_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )
            assert study_activity_instance_aggregate is not None
            if self._batch_cache is not None:
                # Batch mode — cache for reuse by subsequent POST operations
                self._batch_instance_ar = study_activity_instance_aggregate
        for (
            activity_instance_uid,
            is_required_for_activity,
        ) in linked_activity_instances.items():
            activity_instance_selection = StudySelectionActivityInstanceVO.from_input_values(
                study_uid=study_uid,
                author_id=self.author,
                study_activity_uid=study_activity_selection.study_selection_uid,
                activity_instance_uid=activity_instance_uid,
                activity_uid=study_activity_selection.activity_uid,
                activity_subgroup_uid=study_activity_selection.activity_subgroup_uid,
                activity_group_uid=study_activity_selection.activity_group_uid,
                generate_uid_callback=self._repos.study_activity_instance_repository.generate_uid,
                is_reviewed=is_required_for_activity,
            )  # add VO to aggregate
            study_activity_instance_aggregate.add_object_selection(
                activity_instance_selection,
                self._repos.activity_instance_repository.check_exists_final_version,
            )
        study_activity_instance_aggregate.validate()
        if self._batch_instance_ar is None:
            # Non-batch mode — save immediately
            self._repos.study_activity_instance_repository.save(
                study_activity_instance_aggregate, self.author
            )
        # Batch mode: AR is already cached; the batch finally block flushes once at the end

    def _recreate_study_activity_instances_after_activity_replacement(
        self, study_uid: str, study_activity_selection: StudySelectionActivityVO
    ):
        # Flush any deferred batch-mode instance saves so the DB query below sees current state
        if self._batch_instance_ar is not None:
            self._repos.study_activity_instance_repository.save(
                self._batch_instance_ar, self.author
            )
            self._batch_instance_ar = None
        # Remove related Study activity instances — load aggregate once, remove all, save once
        study_activity_instances = self._repos.study_activity_instance_repository.get_all_study_activity_instances_for_study_activity(
            study_uid=study_uid,
            study_activity_uid=study_activity_selection.study_selection_uid,
        )
        if study_activity_instances:
            study_activity_instance_ar = (
                self._repos.study_activity_instance_repository.find_by_study(
                    study_uid, for_update=True
                )
            )
            assert study_activity_instance_ar is not None
            for study_activity_instance in study_activity_instances:
                study_activity_instance_ar.remove_object_selection(
                    study_activity_instance.uid
                )
            self._repos.study_activity_instance_repository.save(
                study_activity_instance_ar, self.author
            )
        self._create_study_activity_instances(
            study_uid=study_uid, study_activity_selection=study_activity_selection
        )

    def _get_activity_group_subgroup_version_from_activity_ar(
        self,
        activity_ar: ActivityAR,
        activity_group_uid: str | None,
        activity_subgroup_uid: str | None,
    ) -> tuple[str | None, str | None]:
        activity_group_version: str | None = None
        activity_subgroup_version: str | None = None
        for activity_grouping in activity_ar.concept_vo.activity_groupings:
            if activity_grouping.activity_group_uid == activity_group_uid:
                activity_group_version = activity_grouping.activity_group_version
            if activity_grouping.activity_subgroup_uid == activity_subgroup_uid:
                activity_subgroup_version = activity_grouping.activity_subgroup_version
        return activity_group_version, activity_subgroup_version

    @ensure_transaction(db)
    def make_selection(
        self,
        study_uid: str,
        selection_create_input: StudySelectionActivityCreateInput,
    ) -> StudySelectionActivity:
        repos = self._repos
        try:
            study_soa_group_selection = self._get_or_create_study_soa_group(
                study_uid=study_uid,
                soa_group_term_uid=selection_create_input.soa_group_term_uid,
            )
            study_soa_group_selection_uid = (
                study_soa_group_selection.study_selection_uid
            )

            activity_ar = self._validate_activity(selection_create_input.activity_uid)

            activity_group_version, activity_subgroup_version = (
                self._get_activity_group_subgroup_version_from_activity_ar(
                    activity_ar=activity_ar,
                    activity_group_uid=selection_create_input.activity_group_uid,
                    activity_subgroup_uid=selection_create_input.activity_subgroup_uid,
                )
            )

            study_activity_group_selection = self._get_or_create_study_activity_group(
                study_uid=study_uid,
                soa_group_term_uid=selection_create_input.soa_group_term_uid,
                study_soa_group_uid=study_soa_group_selection_uid,
                activity_group_uid=selection_create_input.activity_group_uid,
                activity_subgroup_uid=selection_create_input.activity_subgroup_uid,
                activity_group_version=activity_group_version,
            )
            study_activity_group_selection_uid = (
                study_activity_group_selection.study_selection_uid
                if study_activity_group_selection
                else None
            )

            study_activity_subgroup_selection = (
                self._get_or_create_study_activity_subgroup(
                    study_uid=study_uid,
                    soa_group_term_uid=selection_create_input.soa_group_term_uid,
                    activity_group_uid=selection_create_input.activity_group_uid,
                    study_activity_group_uid=study_activity_group_selection_uid,
                    activity_subgroup_uid=selection_create_input.activity_subgroup_uid,
                    activity_subgroup_version=activity_subgroup_version,
                )
            )
            study_activity_subgroup_selection_uid = (
                study_activity_subgroup_selection.study_selection_uid
                if study_activity_subgroup_selection
                else None
            )

            # StudyActivitySelection
            # create new VO to add
            study_activity_selection = self._create_value_object(
                study_uid=study_uid,
                selection_create_input=selection_create_input,
                activity_ar=activity_ar,
                study_soa_group_selection_uid=study_soa_group_selection_uid,
                study_soa_group_order=study_soa_group_selection.order,
                study_activity_subgroup_selection_uid=study_activity_subgroup_selection_uid,
                study_activity_subgroup_order=(
                    study_activity_subgroup_selection.order
                    if study_activity_subgroup_selection
                    else None
                ),
                study_activity_group_selection_uid=study_activity_group_selection_uid,
                study_activity_group_order=(
                    study_activity_group_selection.order
                    if study_activity_group_selection
                    else None
                ),
                activity_group_name=(
                    study_activity_group_selection.activity_group_name
                    if study_activity_group_selection
                    else None
                ),
                activity_subgroup_name=(
                    study_activity_subgroup_selection.activity_subgroup_name
                    if study_activity_subgroup_selection
                    else None
                ),
                show_soa_group_in_protocol_flowchart=study_soa_group_selection.show_soa_group_in_protocol_flowchart,
                show_activity_group_in_protocol_flowchart=(
                    study_activity_group_selection.show_activity_group_in_protocol_flowchart
                    if study_activity_group_selection
                    else True
                ),
                show_activity_subgroup_in_protocol_flowchart=(
                    study_activity_subgroup_selection.show_activity_subgroup_in_protocol_flowchart
                    if study_activity_subgroup_selection
                    else True
                ),
            )
            # add VO to aggregate
            # In batch mode reuse the cached AR so all POSTs with the same (subgroup, soa) grouping
            # share one find_by_study(for_update) + acquire._write_lock; the AR is saved per-POST
            # but closure_data is updated after each save so the diff stays correct.
            find_requested = (
                study_activity_selection.activity_library_name
                == settings.requested_library_name
            )
            activity_ar_cache_key = (
                study_activity_subgroup_selection_uid,
                study_soa_group_selection_uid,
                find_requested,
            )
            ar_cache_key = self._get_batch_ar_cache_key(*activity_ar_cache_key)
            if self._batch_cache is not None and ar_cache_key in self._batch_cache:
                study_activity_aggregate = self._batch_cache[ar_cache_key]
            else:
                study_activity_aggregate = self.repository.find_by_study(
                    study_uid=study_uid,
                    for_update=True,
                    study_activity_subgroup_uid=study_activity_subgroup_selection_uid,
                    study_soa_group_uid=study_soa_group_selection_uid,
                    find_requested_study_activities=find_requested,
                )
                if self._batch_cache is not None:
                    self._batch_cache[ar_cache_key] = study_activity_aggregate
            assert study_activity_aggregate is not None
            study_activity_aggregate.add_object_selection(
                study_activity_selection,
                self.selected_object_repository.check_exists_final_version,
                self._repos.ct_term_name_repository.term_specific_exists_by_uid,
            )
            self._validate_no_study_wide_duplicate(
                study_uid=study_uid,
                updated_selection=study_activity_selection,
            )
            study_activity_aggregate.validate()
            self.repository.save(study_activity_aggregate, self.author)
            # Invalidate Activity cache so GET /concepts/activities/... will recalculate used_by_studies
            with repos.activity_repository.lock_store_item_by_uid:
                repos.activity_repository.cache_store_item_by_uid.clear()
            # Update closure so the cached AR reflects the just-saved state; the next POST
            # in the same batch will then only diff its own new selection.
            if self._batch_cache is not None:
                study_activity_aggregate.repository_closure_data = (
                    study_activity_aggregate.study_objects_selection
                )

            # create StudyActivityInstance selection
            if (
                # We are not creating a StudyActivityInstance selection for Activity placeholders
                study_activity_selection.activity_library_name
                != settings.requested_library_name
            ):
                self._create_study_activity_instances(
                    study_uid=study_uid,
                    study_activity_selection=study_activity_selection,
                )

            # save() writes the computed order back into the in-memory aggregate,
            # so we can read the fully-populated VO directly without a DB round-trip.
            new_selection, _ = study_activity_aggregate.get_specific_object_selection(
                study_activity_selection.study_selection_uid
            )

            # In batch mode, update the patch AR selections cache with the new VO
            # so subsequent PATCHes see the newly created entity without a DB reload.
            if self._batch_cache is not None:
                self._append_to_patch_ar_selections_cache(new_selection)

            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            # add the activity and return
            return self._transform_from_vo_to_response_model(
                study_uid=study_activity_aggregate.study_uid,
                specific_selection=new_selection,  # type: ignore[arg-type]
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    @ensure_transaction(db)
    @trace_calls(args=[1, 2], kwargs=["study_uid", "study_selection_uid"])
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        # StudyActivitySchedule and StudyActivityInstruction Services for cascade delete if any
        study_activity_instructions_service = StudyActivityInstructionService()
        study_activity_group_service = StudyActivityGroupService()
        study_activity_subgroup_service = StudyActivitySubGroupService()
        study_soa_group_service = StudySoAGroupService()

        repos = self._repos
        try:
            acquire_write_lock_study_value(study_uid)

            # Load aggregate and capture the VO being deleted (needed for cache updates)
            selection_aggregate, deleted_vo = self._find_ar_to_patch(
                study_uid=study_uid, study_selection_uid=study_selection_uid
            )

            # Remove related Study activity schedules
            with trace_block("Removing related study activity schedules"):
                repos.study_activity_repository.delete_related_study_activity_schedules(
                    study_uid=study_uid,
                    study_activity_uid=study_selection_uid,
                    author_id=self.author,
                )

            # Remove related Study activity instructions
            with trace_block("Removing related study activity instructions"):
                study_activity_instructions = study_activity_instructions_service.get_all_study_instructions_for_specific_study_activity(
                    study_uid=study_uid, study_activity_uid=study_selection_uid
                )
                for study_activity_instruction in study_activity_instructions:
                    if (
                        study_activity_instruction.study_activity_instruction_uid
                        is None
                    ):
                        raise BusinessLogicException(
                            msg="Study Activity Instruction UID is must be provided."
                        )

                    self._repos.study_activity_instruction_repository.delete(
                        study_uid,
                        study_activity_instruction.study_activity_instruction_uid,
                        self.author,
                    )

            # Remove related Study activity subgroups
            with trace_block("Removing related study activity subgroups"):
                study_activity_subgroups = repos.study_activity_subgroup_repository.get_all_study_activity_subgroups_for_study_activity(
                    study_uid=study_uid, study_activity_uid=study_selection_uid
                )
                for study_activity_subgroup in study_activity_subgroups:
                    # delete study activity subgroup
                    study_activity_subgroup_ar, _ = (
                        study_activity_subgroup_service._find_ar_to_patch(
                            study_uid=study_uid,
                            study_selection_uid=study_activity_subgroup.uid,
                        )
                    )
                    study_activity_subgroup_ar.remove_object_selection(
                        study_activity_subgroup.uid
                    )
                    repos.study_activity_subgroup_repository.save(
                        study_activity_subgroup_ar, self.author
                    )

            # Remove related Study activity groups
            with trace_block("Removing related study activity groups"):
                study_activity_groups = repos.study_activity_group_repository.get_all_study_activity_groups_for_study_activity(
                    study_uid=study_uid, study_activity_uid=study_selection_uid
                )
                for study_activity_group in study_activity_groups:
                    # delete study activity group
                    study_activity_group_ar, _ = (
                        study_activity_group_service._find_ar_to_patch(
                            study_uid=study_uid,
                            study_selection_uid=study_activity_group.uid,
                        )
                    )
                    study_activity_group_ar.remove_object_selection(
                        study_activity_group.uid
                    )
                    repos.study_activity_group_repository.save(
                        study_activity_group_ar, self.author
                    )

            # Remove related Study soa groups
            with trace_block("Removing related study soa-groups"):
                study_soa_groups = repos.study_soa_group_repository.get_all_study_soa_groups_for_study_activity(
                    study_uid=study_uid, study_activity_uid=study_selection_uid
                )
                for study_soa_group in study_soa_groups:
                    # delete study soa group
                    study_soa_group_ar, _ = study_soa_group_service._find_ar_to_patch(
                        study_uid=study_uid, study_selection_uid=study_soa_group.uid
                    )
                    study_soa_group_ar.remove_object_selection(study_soa_group.uid)
                    repos.study_soa_group_repository.save(
                        study_soa_group_ar, self.author
                    )

            # Remove related Study activity instances
            with trace_block("Removing related study activity instances"):
                # Flush any deferred batch-mode instance saves so the DB query below sees current state
                if self._batch_instance_ar is not None:
                    repos.study_activity_instance_repository.save(
                        self._batch_instance_ar, self.author
                    )
                    self._batch_instance_ar = None
                study_activity_instances = repos.study_activity_instance_repository.get_all_study_activity_instances_for_study_activity(
                    study_uid=study_uid, study_activity_uid=study_selection_uid
                )
                non_placeholder_instances = [
                    inst for inst in study_activity_instances if inst.uid is not None
                ]
                if non_placeholder_instances:
                    study_activity_instance_ar = (
                        repos.study_activity_instance_repository.find_by_study(
                            study_uid, for_update=True
                        )
                    )
                    assert study_activity_instance_ar is not None
                    for study_activity_instance in non_placeholder_instances:
                        study_activity_instance_ar.remove_object_selection(
                            study_activity_instance.uid
                        )
                    repos.study_activity_instance_repository.save(
                        study_activity_instance_ar, self.author
                    )

            # remove the connection
            assert selection_aggregate is not None
            selection_aggregate.remove_object_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_activity_repository.save(selection_aggregate, self.author)
            # Invalidate Activity cache so GET /concepts/activities/... will recalculate used_by_studies
            with repos.activity_repository.lock_store_item_by_uid:
                repos.activity_repository.cache_store_item_by_uid.clear()

            # In batch mode, update caches with targeted eviction instead of blanket invalidation.
            if self._batch_cache is not None:
                self._remove_from_patch_ar_selections_cache(study_selection_uid)
                self._evict_ar_cache_for_scope(
                    study_activity_subgroup_uid=deleted_vo.study_activity_subgroup_uid,
                    study_soa_group_uid=deleted_vo.study_soa_group_uid,
                    activity_library_name=deleted_vo.activity_library_name,
                )
        finally:
            repos.close()

    def _update_underlying_activity_if_needed(
        self,
        current_object: StudySelectionActivityVO,
        request_object: (
            StudyActivityReplaceActivityInput
            | StudySelectionActivityInput
            | StudySelectionActivityRequestEditInput
            | UpdateActivityPlaceholderToSponsorActivity
        ),
    ):
        activity_ar: ActivityAR | None
        # update underlying Activity
        if isinstance(request_object, StudySelectionActivityRequestEditInput):
            activity_ar = self._patch_selected_activity(
                current_object=current_object,
                request_object=request_object,
            )
        elif (
            isinstance(
                request_object,
                (
                    UpdateActivityPlaceholderToSponsorActivity,
                    StudyActivityReplaceActivityInput,
                ),
            )
            and request_object.activity_uid
        ):
            activity_ar = self._repos.activity_repository.find_by_uid(
                request_object.activity_uid
            )
            ValidationException.raise_if_not(
                activity_ar,
                msg=f"The Activity with UID '{current_object.activity_uid}' doesn't exist.",
            )
        else:
            # Skip fetching activity AR when no grouping-related fields are changing;
            # _patch_prepare_new_value_object falls back to current_object values in that case
            if (
                request_object.activity_group_uid is None
                and request_object.activity_subgroup_uid is None
            ):
                return None
            activity_ar = self._repos.activity_repository.find_by_uid(
                current_object.activity_uid,
                version=current_object.activity_version,
            )
        return activity_ar

    def _validate_new_activity_groupings(
        self,
        request_object: (
            StudyActivityReplaceActivityInput
            | StudySelectionActivityInput
            | StudySelectionActivityRequestEditInput
            | UpdateActivityPlaceholderToSponsorActivity
        ),
        activity_ar: ActivityAR | None,
        current_object: StudySelectionActivityVO,
    ):
        if activity_ar is None:
            return
        ValidationException.raise_if(
            request_object.activity_group_uid is None
            and request_object.activity_subgroup_uid is not None
            and activity_ar.library.name != "Requested",
            msg="An activity group is required for the selection",
        )
        ValidationException.raise_if(
            request_object.activity_subgroup_uid is None
            and request_object.activity_group_uid is not None
            and activity_ar.library.name != "Requested",
            msg="An activity subgroup is required for the selection",
        )
        self.validate_activity_groupings(
            activity_group_uid=request_object.activity_group_uid,
            activity_subgroup_uid=request_object.activity_subgroup_uid,
            activity_ar=activity_ar,
            current_object=current_object,
        )

    def validate_activity_groupings(
        self,
        activity_subgroup_uid: str | None,
        activity_group_uid: str | None,
        activity_ar: ActivityAR,
        current_object: StudySelectionActivityVO,
    ) -> None:
        ValidationException.raise_if(
            activity_group_uid
            and activity_group_uid
            not in [
                activity_grouping.activity_group_uid
                for activity_grouping in activity_ar.concept_vo.activity_groupings
            ],
            msg=f"Provided Activity Group is not included in '{current_object.activity_uid}' Activity Groupings.",
        )
        ValidationException.raise_if(
            activity_subgroup_uid
            and not any(
                activity_grouping.activity_subgroup_uid == activity_subgroup_uid
                and activity_grouping.activity_group_uid == activity_group_uid
                for activity_grouping in activity_ar.concept_vo.activity_groupings
            ),
            msg=f"Provided Activity Subgroup is not part of a Grouping with UID '{activity_group_uid}' Group in the '{current_object.activity_uid}' Activity Groupings.",
        )

    def _patch_or_get_study_activity_group(
        self,
        request_object: (
            StudyActivityReplaceActivityInput
            | StudySelectionActivityInput
            | StudySelectionActivityRequestEditInput
            | UpdateActivityPlaceholderToSponsorActivity
            | StudyActivitySyncLatestVersionInput
        ),
        current_object: StudySelectionActivityVO,
        is_soa_group_changed: bool,
        study_soa_group_uid: str,
        sync_latest_version: bool = False,
    ) -> StudySelectionActivityGroupVO:
        soa_group_term_uid = (
            request_object.soa_group_term_uid
            if not isinstance(request_object, StudyActivitySyncLatestVersionInput)
            else current_object.soa_group_term_uid
        )
        if (
            request_object.activity_group_uid
            and current_object.activity_group_uid != request_object.activity_group_uid
        ) or sync_latest_version:
            return self._get_or_create_study_activity_group(
                study_uid=current_object.study_uid,
                activity_subgroup_uid=request_object.activity_subgroup_uid,
                activity_group_uid=request_object.activity_group_uid,
                soa_group_term_uid=soa_group_term_uid,
                study_soa_group_uid=study_soa_group_uid,
                sync_latest_version=sync_latest_version,
                current_object=current_object,
            )
        # When SoAGroup is changed we need to update StudyActivityGroup for other shared nodes if given StudyActivity contains StudyActivityGroup
        if is_soa_group_changed and current_object.activity_group_uid:
            return self._get_or_create_study_activity_group(
                study_uid=current_object.study_uid,
                activity_subgroup_uid=current_object.activity_subgroup_uid,
                activity_group_uid=current_object.activity_group_uid,
                soa_group_term_uid=soa_group_term_uid,
                study_soa_group_uid=study_soa_group_uid,
                perform_group_validation=False,
                sync_latest_version=sync_latest_version,
                current_object=current_object,
            )
        # Unchanged — build lightweight VO from current_object
        return StudySelectionActivityGroupVO.from_input_values(
            study_uid=current_object.study_uid,
            author_id=self.author,
            activity_group_uid=current_object.activity_group_uid,  # type: ignore[arg-type]
            activity_group_name=current_object.activity_group_name,
            activity_group_version=None,
            study_selection_uid=current_object.study_activity_group_uid,
            order=current_object.study_activity_group_order,
            show_activity_group_in_protocol_flowchart=current_object.show_activity_group_in_protocol_flowchart,
        )

    def _patch_or_get_study_activity_subgroup(
        self,
        request_object: (
            StudyActivityReplaceActivityInput
            | StudySelectionActivityInput
            | StudySelectionActivityRequestEditInput
            | UpdateActivityPlaceholderToSponsorActivity
            | StudyActivitySyncLatestVersionInput
        ),
        current_object: StudySelectionActivityVO,
        is_soa_group_changed: bool,
        is_study_activity_group_changed: bool,
        study_activity_group_uid: str | None,
        sync_latest_version: bool = False,
    ) -> StudySelectionActivitySubGroupVO:
        soa_group_term_uid = (
            request_object.soa_group_term_uid
            if not isinstance(request_object, StudyActivitySyncLatestVersionInput)
            else current_object.soa_group_term_uid
        )
        if (
            request_object.activity_subgroup_uid
            and current_object.activity_subgroup_uid
            != request_object.activity_subgroup_uid
        ) or sync_latest_version:
            return self._get_or_create_study_activity_subgroup(
                study_uid=current_object.study_uid,
                activity_subgroup_uid=request_object.activity_subgroup_uid,
                activity_group_uid=request_object.activity_group_uid
                or current_object.activity_group_uid,
                soa_group_term_uid=soa_group_term_uid,
                study_activity_group_uid=study_activity_group_uid,
                sync_latest_version=sync_latest_version,
                current_object=current_object,
            )
        # When SoAGroup or StudyActivityGroup is changed we need to update StudyActivitySubGroup for other shared nodes if given StudyActivity contains StudyActivitySubGroup
        if (
            is_soa_group_changed or is_study_activity_group_changed
        ) and current_object.activity_subgroup_uid:
            return self._get_or_create_study_activity_subgroup(
                study_uid=current_object.study_uid,
                activity_subgroup_uid=current_object.activity_subgroup_uid,
                activity_group_uid=current_object.activity_group_uid,
                soa_group_term_uid=soa_group_term_uid,
                perform_subgroup_validation=False,
                study_activity_group_uid=study_activity_group_uid,
                sync_latest_version=sync_latest_version,
                current_object=current_object,
            )
        # Unchanged — build lightweight VO from current_object
        return StudySelectionActivitySubGroupVO.from_input_values(
            study_uid=current_object.study_uid,
            author_id=self.author,
            activity_subgroup_uid=current_object.activity_subgroup_uid,  # type: ignore[arg-type]
            activity_subgroup_name=current_object.activity_subgroup_name,
            activity_subgroup_version=None,
            study_selection_uid=current_object.study_activity_subgroup_uid,
            order=current_object.study_activity_subgroup_order,
            show_activity_subgroup_in_protocol_flowchart=current_object.show_activity_subgroup_in_protocol_flowchart,
        )

    def _patch_prepare_new_value_object(
        self,
        request_object: (
            StudyActivityReplaceActivityInput
            | StudySelectionActivityInput
            | StudySelectionActivityRequestEditInput
            | UpdateActivityPlaceholderToSponsorActivity
        ),
        current_object: StudySelectionActivityVO,
    ) -> StudySelectionActivityVO:
        # transform current to input model
        transformed_current = StudySelectionActivityInput(
            show_activity_in_protocol_flowchart=current_object.show_activity_in_protocol_flowchart,
            soa_group_term_uid=current_object.soa_group_term_uid,
            keep_old_version=current_object.keep_old_version,
            activity_group_uid=None,
            activity_subgroup_uid=None,
        )
        keep_old_version_date = None
        if request_object.keep_old_version is True:
            keep_old_version_date = datetime.now(timezone.utc)
        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_object,
            reference_base_model=transformed_current,
        )

        # update underlying Activity
        activity_ar = self._update_underlying_activity_if_needed(
            request_object=request_object, current_object=current_object
        )

        is_soa_group_changed = (
            current_object.soa_group_term_uid != request_object.soa_group_term_uid
        )
        # update StudySoAGroup selection
        updated_soa_selection = self._patch_soa_group_selection_value_object(
            study_uid=current_object.study_uid,
            current_study_activity=current_object,
            selection_create_input=request_object,
            is_soa_group_changed=is_soa_group_changed,
        )

        # make validation of the new activity grouping properties if passed
        self._validate_new_activity_groupings(
            request_object=request_object,
            activity_ar=activity_ar,
            current_object=current_object,
        )

        # update StudyActivityGroup
        updated_group = self._patch_or_get_study_activity_group(
            request_object=request_object,
            current_object=current_object,
            is_soa_group_changed=is_soa_group_changed,
            study_soa_group_uid=updated_soa_selection.study_selection_uid,
        )

        is_study_activity_group_changed = (
            updated_group.study_selection_uid != current_object.study_activity_group_uid
        )
        # update StudyActivitySubGroup
        updated_subgroup = self._patch_or_get_study_activity_subgroup(
            request_object=request_object,
            current_object=current_object,
            is_soa_group_changed=is_soa_group_changed,
            is_study_activity_group_changed=is_study_activity_group_changed,
            study_activity_group_uid=updated_group.study_selection_uid,
        )
        updated_study_activity_vo = StudySelectionActivityVO.from_input_values(
            study_uid=current_object.study_uid,
            activity_uid=(
                activity_ar.uid if activity_ar else current_object.activity_uid
            ),
            activity_version=(
                activity_ar.item_metadata.version
                if activity_ar
                else current_object.activity_version  # type: ignore[arg-type]
            ),
            activity_name=(
                activity_ar.name if activity_ar else current_object.activity_name
            ),
            soa_group_term_uid=updated_soa_selection.soa_group_term_uid,
            study_soa_group_uid=updated_soa_selection.study_selection_uid,
            study_soa_group_order=updated_soa_selection.order,
            study_selection_uid=current_object.study_selection_uid,
            study_activity_subgroup_uid=updated_subgroup.study_selection_uid,
            study_activity_subgroup_order=updated_subgroup.order,
            activity_subgroup_uid=updated_subgroup.activity_subgroup_uid,
            activity_subgroup_name=updated_subgroup.activity_subgroup_name,
            study_activity_group_uid=updated_group.study_selection_uid,
            study_activity_group_order=updated_group.order,
            activity_group_uid=updated_group.activity_group_uid,
            activity_group_name=updated_group.activity_group_name,
            show_soa_group_in_protocol_flowchart=updated_soa_selection.show_soa_group_in_protocol_flowchart,
            show_activity_group_in_protocol_flowchart=updated_group.show_activity_group_in_protocol_flowchart,
            show_activity_subgroup_in_protocol_flowchart=updated_subgroup.show_activity_subgroup_in_protocol_flowchart,
            show_activity_in_protocol_flowchart=request_object.show_activity_in_protocol_flowchart,
            keep_old_version=request_object.keep_old_version,
            keep_old_version_date=keep_old_version_date,
            author_id=user().id(),
            author_username=user().username,
            activity_library_name=current_object.activity_library_name,
        )

        return updated_study_activity_vo

    @ensure_transaction(db)
    def handle_batch_operations(
        self,
        study_uid: str,
        operations: list[StudySelectionActivityBatchInput],
    ) -> list[StudySelectionActivityBatchOutput]:
        """Handle a batch of study activity selection operations with proper cache management.

        This method processes POST, PATCH, and DELETE operations in sequence while
        maintaining cache consistency. Each operation may invalidate caches that
        affect subsequent operations in the batch.

        Cache Lifecycle:
        1. Initialize all caches at batch start
        2. Each operation may invalidate related cache entries
        3. Cache state is preserved between operations for performance
        4. All caches are cleared in finally block

        Args:
            study_uid: Study identifier for all operations
            operations: List of batch operations to execute

        Returns:
            List of batch operation results with status codes and content
        """
        results = []

        # Initialize all batch caches and tracking
        self._initialize_batch_caches()

        try:
            for operation in operations:
                item = None
                try:
                    if operation.method == "PATCH":
                        if isinstance(
                            operation.content, StudySelectionActivityBatchUpdateInput
                        ):
                            item = self.patch_selection(
                                study_uid,
                                operation.content.study_activity_uid,
                                operation.content.content,
                            )
                            response_code = status.HTTP_200_OK
                        else:
                            raise ValidationException(
                                msg="PATCH operation requires StudySelectionActivityBatchUpdateInput as request payload."
                            )

                    elif operation.method == "DELETE":
                        if isinstance(
                            operation.content, StudySelectionActivityBatchDeleteInput
                        ):
                            self.delete_selection(
                                study_uid, operation.content.study_activity_uid
                            )
                            response_code = status.HTTP_204_NO_CONTENT
                        else:
                            raise ValidationException(
                                msg="DELETE operation requires StudySelectionActivityBatchDeleteInput as request payload."
                            )

                    elif operation.method == "POST":
                        if isinstance(
                            operation.content, StudySelectionActivityCreateInput
                        ):
                            item = self.make_selection(study_uid, operation.content)
                            response_code = status.HTTP_201_CREATED
                        else:
                            raise ValidationException(
                                msg="POST operation requires StudySelectionActivityCreateInput as request payload."
                            )
                    else:
                        raise MethodNotAllowedException(method=operation.method)

                    results.append(
                        StudySelectionActivityBatchOutput.model_construct(
                            response_code=response_code,
                            content=item,
                        )
                    )

                except MDRApiBaseException as error:
                    results.append(
                        StudySelectionActivityBatchOutput.model_construct(
                            response_code=error.status_code,
                            content=BatchErrorResponse(message=str(error)),
                        )
                    )
                    raise error

        finally:
            # Save any pending batch instance AR before clearing caches
            if self._batch_instance_ar is not None:
                self._repos.study_activity_instance_repository.save(
                    self._batch_instance_ar, self.author
                )

            # Clear all caches and tracking state
            self._clear_all_batch_caches()

        return results

    @ensure_transaction(db)
    def handle_review_changes(
        self,
        study_uid: str,
        operations: list[StudySelectionActivityReviewBatchInput],
    ) -> list[StudySelectionActivityBatchOutput]:
        """Handle a batch of review changes with proper cache management.

        Review operations are simpler than full batch operations but still
        require cache management for consistency between operations.
        """
        results = []

        # Initialize all batch caches for review operations
        self._initialize_batch_caches()

        try:
            for operation in operations:
                item = None
                try:
                    if operation.action == StudySelectionReviewAction.ACCEPT:
                        item = self.update_selection_to_latest_version(
                            study_uid=study_uid,
                            study_selection_uid=operation.uid,
                            sync_latest_version_input=StudyActivitySyncLatestVersionInput(
                                activity_group_uid=operation.content.activity_group_uid,
                                activity_subgroup_uid=operation.content.activity_subgroup_uid,
                            ),
                        )
                        response_code = status.HTTP_200_OK
                    elif operation.action == StudySelectionReviewAction.DECLINE:
                        self.patch_selection(
                            study_uid=study_uid,
                            study_selection_uid=operation.uid,
                            selection_update_input=operation.content,
                        )
                        response_code = status.HTTP_204_NO_CONTENT
                    else:
                        raise MethodNotAllowedException(method=operation.action)
                    results.append(
                        StudySelectionActivityBatchOutput(
                            response_code=response_code,
                            content=item,
                        )
                    )
                except MDRApiBaseException as error:
                    results.append(
                        StudySelectionActivityBatchOutput.model_construct(
                            response_code=error.status_code,
                            content=BatchErrorResponse(message=str(error)),
                        )
                    )
                    raise error
        finally:
            # Save any pending batch instance AR before clearing caches
            if self._batch_instance_ar is not None:
                self._repos.study_activity_instance_repository.save(
                    self._batch_instance_ar, self.author
                )

            # Clear all caches and tracking state
            self._clear_all_batch_caches()

        return results

    @ensure_transaction(db)
    def handle_soa_edit_batch_operations(
        self,
        study_uid: str,
        operations: list[StudySoAEditBatchInput],
    ) -> list[StudySoAEditBatchOutput]:
        """Handle a batch of SoA edit operations with proper cache management.

        SoA edit operations can modify study activities and schedules, requiring
        comprehensive cache invalidation to maintain consistency.
        """
        study_activity_schedules_service = StudyActivityScheduleService()
        results = []

        # Initialize all batch caches and tracking
        self._initialize_batch_caches()
        try:
            for operation in operations:
                item = None
                try:
                    if (
                        operation.method == "PATCH"
                        and operation.object == SoAItemType.STUDY_ACTIVITY.value
                    ):
                        if isinstance(
                            operation.content, StudySelectionActivityBatchUpdateInput
                        ):
                            item = self.patch_selection(
                                study_uid,
                                operation.content.study_activity_uid,
                                operation.content.content,
                            )
                            response_code = status.HTTP_200_OK
                        else:
                            raise ValidationException(
                                msg="PATCH operation requires StudySelectionActivityBatchUpdateInput as request payload."
                            )
                    elif operation.method == "POST":
                        if operation.object == SoAItemType.STUDY_ACTIVITY.value:
                            if isinstance(
                                operation.content, StudySelectionActivityCreateInput
                            ):
                                item = self.make_selection(study_uid, operation.content)
                            else:
                                raise ValidationException(
                                    msg="POST operation requires StudySelectionActivityCreateInput as request payload."
                                )
                        elif (
                            operation.object
                            == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value
                        ):
                            if isinstance(
                                operation.content, StudyActivityScheduleCreateInput
                            ):
                                item = study_activity_schedules_service.create(
                                    study_uid, operation.content
                                )
                            else:
                                raise ValidationException(
                                    msg="POST operation requires StudyActivityScheduleCreateInput as request payload."
                                )

                        response_code = status.HTTP_201_CREATED
                    elif operation.method == "DELETE":
                        if operation.object == SoAItemType.STUDY_ACTIVITY.value:
                            if isinstance(
                                operation.content,
                                StudySelectionActivityBatchDeleteInput,
                            ):
                                self.delete_selection(
                                    study_uid, operation.content.study_activity_uid
                                )
                            else:
                                raise ValidationException(
                                    msg="DELETE operation requires StudySelectionActivityBatchDeleteInput as request payload."
                                )
                        elif (
                            operation.object
                            == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value
                        ):
                            if isinstance(
                                operation.content, StudyActivityScheduleDeleteInput
                            ):
                                item = study_activity_schedules_service.delete(
                                    study_uid, operation.content.uid
                                )
                            else:
                                raise ValidationException(
                                    msg="DELETE operation requires StudyActivityScheduleDeleteInput as request payload."
                                )
                        response_code = status.HTTP_204_NO_CONTENT
                    else:
                        raise MethodNotAllowedException(method=operation.method)
                    results.append(
                        StudySoAEditBatchOutput(
                            response_code=response_code, content=item
                        )
                    )
                except MDRApiBaseException as error:
                    results.append(
                        StudySoAEditBatchOutput.model_construct(
                            response_code=error.status_code,
                            content=BatchErrorResponse(message=str(error)),
                        )
                    )
        finally:
            # Save any pending batch instance AR before clearing caches
            if self._batch_instance_ar is not None:
                self._repos.study_activity_instance_repository.save(
                    self._batch_instance_ar, self.author
                )

            # Clear all caches and tracking state
            self._clear_all_batch_caches()

        return results

    @ensure_transaction(db)
    def update_activity_request_with_sponsor_activity(
        self,
        study_uid: str,
        study_selection_uid: str,
    ) -> StudySelectionActivity:
        selection_aggregate, current_vo = self._find_ar_to_patch(
            study_uid=study_uid, study_selection_uid=study_selection_uid
        )

        assert selection_aggregate is not None

        # Load the current VO for updates
        activity_ar = self._repos.activity_repository.find_by_uid(
            current_vo.activity_uid
        )
        NotFoundException.raise_if_not(activity_ar, "Activity", current_vo.activity_uid)
        replaced_activity_ar = self._repos.activity_repository.find_by_uid(
            activity_ar.concept_vo.replaced_by_activity  # type: ignore[arg-type]
        )
        NotFoundException.raise_if_not(
            replaced_activity_ar,
            "Activity",
            activity_ar.concept_vo.replaced_by_activity,
        )
        updated_study_activity = self.patch_selection(
            study_uid=study_uid,
            study_selection_uid=study_selection_uid,
            selection_update_input=UpdateActivityPlaceholderToSponsorActivity(
                activity_uid=replaced_activity_ar.uid,
                # It is safe to access activity_groupings by [0] as it's a required to pass just exactly one
                # set of groupings when creating a Sponsor activity out of Activity Request
                activity_subgroup_uid=replaced_activity_ar.concept_vo.activity_groupings[
                    0
                ].activity_subgroup_uid,
                activity_group_uid=replaced_activity_ar.concept_vo.activity_groupings[
                    0
                ].activity_group_uid,
            ),
        )
        if updated_study_activity.study_activity_uid is None:
            raise BusinessLogicException(
                msg="Failed to update StudyActivity. Study Activity UID is missing."
            )
        self._repos.study_activity_repository.create_replaced_by_links_from_previous_version(
            study_uid=study_uid,
            source_study_activity_uid=study_selection_uid,
            target_study_activity_uids=[updated_study_activity.study_activity_uid],
        )
        return updated_study_activity

    def get_detailed_soa_history(
        self, study_uid: str, page_number: int, page_size: int, total_count: bool
    ) -> GenericFilteringReturn[DetailedSoAHistory]:
        NotFoundException.raise_if_not(
            self._repos.study_definition_repository.study_exists_by_uid(
                study_uid=study_uid
            ),
            "Study",
            study_uid,
        )

        (
            detailed_soa_history,
            amount_of_history_items,
        ) = self.repository.get_detailed_soa_history(
            study_uid=study_uid,
            page_size=page_size,
            page_number=page_number,
            total_count=total_count,
        )
        all_detailed_history = GenericFilteringReturn(
            items=detailed_soa_history, total=amount_of_history_items
        )
        all_detailed_history.items = [
            DetailedSoAHistory.from_history(detailed_soa_history_item=item)
            for item in all_detailed_history.items
        ]
        return all_detailed_history

    @ensure_transaction(db)
    def update_selection_to_latest_version(
        self,
        study_uid: str,
        study_selection_uid: str,
        sync_latest_version_input: StudyActivitySyncLatestVersionInput | None,
    ):
        selection_ar: StudySelectionActivityAR
        current_selection: StudySelectionActivityVO
        selection_ar, current_selection = self._find_ar_to_patch(
            study_uid=study_uid, study_selection_uid=study_selection_uid
        )
        activity_uid = current_selection.activity_uid
        activity_ar = self._repos.activity_repository.find_by_uid_2(
            activity_uid, for_update=True
        )
        if activity_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            activity_ar.approve(self.author)
            self._repos.activity_repository.save(activity_ar)
        elif activity_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise BusinessLogicException(
                msg="Cannot add retired activity as selection. Please reactivate."
            )
        selection: StudySelectionActivityVO = current_selection.update_version(
            activity_version=activity_ar.item_metadata.version
        )
        activity_group_uid_to_validate: str | None = None
        if sync_latest_version_input and sync_latest_version_input.activity_group_uid:
            activity_group_uid_to_validate = (
                sync_latest_version_input.activity_group_uid
            )
        else:
            activity_group_uid_to_validate = current_selection.activity_group_uid
        activity_subgroup_uid_to_validate: str | None = None
        if (
            sync_latest_version_input
            and sync_latest_version_input.activity_subgroup_uid
        ):
            activity_subgroup_uid_to_validate = (
                sync_latest_version_input.activity_subgroup_uid
            )
        else:
            activity_subgroup_uid_to_validate = current_selection.activity_subgroup_uid
        self.validate_activity_groupings(
            activity_group_uid=activity_group_uid_to_validate,
            activity_subgroup_uid=activity_subgroup_uid_to_validate,
            activity_ar=activity_ar,
            current_object=current_selection,
        )
        # When we sync to latest version it means we clear keep_old_version flag as user
        # decided to update to latest version
        selection = selection.update_keep_old_version(
            keep_old_version=False, keep_old_version_date=None
        )

        # update StudyActivityGroup
        is_study_activity_group_changed: bool = False
        sync_activity_group_version: bool = False
        if sync_latest_version_input and sync_latest_version_input.activity_group_uid:
            latest_activity_group_name = (
                self._repos.activity_group_repository.get_latest_concept_name(
                    uid=sync_latest_version_input.activity_group_uid
                )
            )
            if latest_activity_group_name != current_selection.activity_group_name:
                sync_activity_group_version = True
        if sync_latest_version_input and sync_latest_version_input.activity_group_uid:
            updated_group = self._patch_or_get_study_activity_group(
                request_object=sync_latest_version_input,
                current_object=selection,
                is_soa_group_changed=False,
                study_soa_group_uid=selection.study_soa_group_uid,
                sync_latest_version=sync_activity_group_version,
            )
            is_study_activity_group_changed = (
                selection.study_activity_group_uid != updated_group.study_selection_uid
            )

            if not updated_group.study_selection_uid:
                raise BusinessLogicException(
                    msg="Study Activity Group UID cannot be None when syncing to latest version."
                )

            selection = selection.update_activity_group(
                activity_group_uid=updated_group.activity_group_uid,
                study_activity_group_uid=updated_group.study_selection_uid,
            )

        sync_activity_subgroup_version: bool = False
        if (
            sync_latest_version_input
            and sync_latest_version_input.activity_subgroup_uid
        ):
            latest_activity_subgroup_name = (
                self._repos.activity_subgroup_repository.get_latest_concept_name(
                    uid=sync_latest_version_input.activity_subgroup_uid
                )
            )
            if (
                latest_activity_subgroup_name
                != current_selection.activity_subgroup_name
            ):
                sync_activity_subgroup_version = True
        # update StudyActivitySubGroup
        if (
            sync_latest_version_input
            and sync_latest_version_input.activity_subgroup_uid
        ) or is_study_activity_group_changed:
            if sync_latest_version_input is None:
                raise ValidationException(
                    msg="Sync latest version input can't be None at this point"
                )
            updated_subgroup = self._patch_or_get_study_activity_subgroup(
                request_object=sync_latest_version_input,
                current_object=selection,
                is_soa_group_changed=False,
                is_study_activity_group_changed=is_study_activity_group_changed,
                study_activity_group_uid=updated_group.study_selection_uid,
                sync_latest_version=sync_activity_subgroup_version
                or is_study_activity_group_changed,
            )
            selection = selection.update_activity_subgroup(
                activity_subgroup_uid=updated_subgroup.activity_subgroup_uid,
                study_activity_subgroup_uid=updated_subgroup.study_selection_uid,
            )
        self._update_aggregate(
            selection_aggregate=selection_ar,
            previous_selection=current_selection,
            updated_selection=selection,
        )
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_uid
        )
        selection_aggregate = self.repository.find_by_study(
            study_uid=study_uid,
        )
        # Fetch the new selection which was just updated
        (
            new_selection,
            _,
        ) = selection_aggregate.get_specific_object_selection(study_selection_uid)

        # Keep _batch_patch_ar_selections current for subsequent operations in the same batch.
        # patch_selection does this in the base class; update_selection_to_latest_version
        # calls _update_aggregate directly so we mirror the same update here using the
        # fully-populated VO from the reload above. Uses immutable update to prevent cache coherence issues.
        if self._batch_patch_ar_selections is not None:
            self._batch_patch_ar_selections = [
                new_selection if vo.study_selection_uid == study_selection_uid else vo
                for vo in self._batch_patch_ar_selections
            ]

        return self._transform_from_vo_to_response_model(
            study_uid=study_uid,
            specific_selection=new_selection,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    @ensure_transaction(db)
    def create_study_activity_directly_in_soa(
        self,
        study_uid: str,
        selection_create_input: StudySelectionActivityInSoACreateInput,
    ):
        new_study_activity = self.make_selection(
            study_uid=study_uid,
            selection_create_input=StudySelectionActivityCreateInput(
                soa_group_term_uid=selection_create_input.soa_group_term_uid,
                activity_uid=selection_create_input.activity_uid,
                activity_subgroup_uid=selection_create_input.activity_subgroup_uid,
                activity_group_uid=selection_create_input.activity_group_uid,
                activity_instance_uid=selection_create_input.activity_instance_uid,
            ),
        )
        if new_study_activity.study_activity_uid is None:
            raise BusinessLogicException(
                msg="Failed to create Study Activity in SoA. Study Activity UID is missing."
            )

        return self.set_new_order(
            study_uid=study_uid,
            study_selection_uid=new_study_activity.study_activity_uid,
            new_order=selection_create_input.order,
        )
