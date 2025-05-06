import dataclasses
from collections import defaultdict
from datetime import datetime
from typing import Callable

from fastapi import status
from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.activities.activity_repository import (
    ActivityRepository,
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
from clinical_mdr_api.models.controlled_terminologies.ct_term_name import CTTermName
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.study_selections.study_selection import (
    DetailedSoAHistory,
    StudyActivityReplaceActivityInput,
    StudySelectionActivity,
    StudySelectionActivityBatchInput,
    StudySelectionActivityBatchOutput,
    StudySelectionActivityCore,
    StudySelectionActivityCreateInput,
    StudySelectionActivityInput,
    StudySelectionActivityInSoACreateInput,
    StudySelectionActivityRequestEditInput,
    StudySoAEditBatchInput,
    StudySoAEditBatchOutput,
    UpdateActivityPlaceholderToSponsorActivity,
)
from clinical_mdr_api.models.utils import BaseModel, GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    ensure_transaction,
    fill_missing_values_in_base_model_from_reference_base_model,
)
from clinical_mdr_api.services.concepts.activities.activity_group_service import (
    ActivityGroupService,
)
from clinical_mdr_api.services.concepts.activities.activity_service import (
    ActivityService,
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
from clinical_mdr_api.services.studies.study_soa_footnote import StudySoAFootnoteService
from clinical_mdr_api.services.studies.study_soa_group import StudySoAGroupService
from common.config import REQUESTED_LIBRARY_NAME
from common.exceptions import (
    BusinessLogicException,
    MDRApiBaseException,
    MethodNotAllowedException,
    NotFoundException,
    ValidationException,
)


class StudyActivitySelectionService(StudyActivitySelectionBaseService):
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
        terms_at_specific_datetime: datetime | None,
        accepted_version: bool = False,
        study_value_version: str | None = None,
        soa_groups: list[CTTermName] | None = None,
        activity_for_study_activities: list[ActivityForStudyActivity] | None = None,
    ) -> StudySelectionActivity:
        return StudySelectionActivity.from_study_selection_activity_vo_and_order(
            study_uid=study_uid,
            specific_selection=specific_selection,
            accepted_version=accepted_version,
            get_activity_by_uid_callback=self._transform_latest_activity_model,
            get_activity_by_uid_version_callback=self._transform_activity_model,
            get_ct_term_flowchart_group=self._find_by_uid_or_raise_not_found,
            study_value_version=study_value_version,
            terms_at_specific_datetime=terms_at_specific_datetime,
            soa_groups=soa_groups,
            activity_for_study_activities=activity_for_study_activities,
        )

    def get_default_sorting(
        self,
    ) -> dict | None:
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
            == REQUESTED_LIBRARY_NAME
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
                    study_selection_uid=study_activity_to_reorder.study_activity_subgroup_uid,
                )
            )

            subgroup_size = len(study_activity_subgroup.study_activity_uids)
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
            and selection_vo.activity_library_name == REQUESTED_LIBRARY_NAME
        ):
            all_selections_from_same_subgroup = [
                selection
                for selection in selection_aggregate.study_objects_selection
                if selection.study_soa_group_uid == selection_vo.study_soa_group_uid
                and selection.activity_library_name == REQUESTED_LIBRARY_NAME
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

    def _update_aggregate(
        self,
        selection_aggregate: StudySelectionActivityAR,
        previous_selection: StudySelectionActivityVO,
        updated_selection: StudySelectionActivityVO,
    ) -> bool:
        if (
            previous_selection.study_activity_subgroup_uid
            != updated_selection.study_activity_subgroup_uid
        ) or (
            updated_selection.activity_library_name == REQUESTED_LIBRARY_NAME
            and updated_selection.study_activity_subgroup_uid is None
            and previous_selection.study_soa_group_uid
            != updated_selection.study_soa_group_uid
        ):
            new_selection_aggregate = self.repository.find_by_study(
                study_uid=selection_aggregate.study_uid,
                for_update=True,
                study_activity_subgroup_uid=updated_selection.study_activity_subgroup_uid,
                study_soa_group_uid=updated_selection.study_soa_group_uid,
                find_requested_study_activities=updated_selection.activity_library_name
                == REQUESTED_LIBRARY_NAME,
            )
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

            selection_aggregate.remove_object_selection(
                updated_selection.study_selection_uid
            )
            selection_aggregate.add_selection_to_closure_from_other_ar(
                updated_selection
            )
            # If previous StudyActivity was assigned with some StudyActivitySubGroup
            # The past StudyActivitySubGroup orders should be updated
            if previous_selection.study_activity_subgroup_uid:
                study_activity_subgroup_aggregate = self._repos.study_activity_subgroup_repository.find_by_study(
                    study_uid=previous_selection.study_uid,
                    for_update=True,
                    study_activity_group_uid=previous_selection.study_activity_group_uid,
                )
                for new_order, study_activity_subgroup_selection in enumerate(
                    study_activity_subgroup_aggregate.study_objects_selection, start=1
                ):
                    reordered_study_activity_subgroup_selection = dataclasses.replace(
                        study_activity_subgroup_selection, order=new_order
                    )
                    study_activity_subgroup_aggregate.update_selection(
                        updated_study_object_selection=reordered_study_activity_subgroup_selection,
                        object_exist_callback=self._repos.activity_subgroup_repository.final_concept_exists,
                        ct_term_level_exist_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                    )
                assert study_activity_subgroup_aggregate is not None

                study_activity_subgroup_aggregate.validate()
                # sync with DB and save the update
                self._repos.study_activity_subgroup_repository.save(
                    study_activity_subgroup_aggregate, self.author
                )
            # If previous StudyActivitySelection was assigned with some StudyActivityGroup
            # The past StudyActivityGroup orders should be updated
            if previous_selection.study_activity_group_uid:
                study_activity_group_aggregate = (
                    self._repos.study_activity_group_repository.find_by_study(
                        study_uid=previous_selection.study_uid,
                        for_update=True,
                        study_soa_group_uid=previous_selection.study_soa_group_uid,
                    )
                )
                for new_order, study_activity_group_selection in enumerate(
                    study_activity_group_aggregate.study_objects_selection, start=1
                ):
                    reordered_study_activity_group_selection = dataclasses.replace(
                        study_activity_group_selection, order=new_order
                    )
                    study_activity_group_aggregate.update_selection(
                        updated_study_object_selection=reordered_study_activity_group_selection,
                        object_exist_callback=self._repos.activity_group_repository.final_concept_exists,
                        ct_term_level_exist_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                    )
                assert study_activity_group_aggregate is not None

                study_activity_group_aggregate.validate()
                # sync with DB and save the update
                self._repos.study_activity_group_repository.save(
                    study_activity_group_aggregate, self.author
                )
        else:
            # let the aggregate update the value object
            selection_aggregate.update_selection(
                updated_study_object_selection=updated_selection,
                object_exist_callback=self._get_selected_object_exist_check(),
                ct_term_level_exist_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
            )
        selection_aggregate.validate()
        self.repository.save(selection_aggregate, self.author)

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

    def _create_value_object(
        self,
        study_uid: str,
        selection_create_input: StudySelectionActivityCreateInput,
        **kwargs,
    ):
        study_soa_group_selection_uid = kwargs.get("study_soa_group_selection_uid")
        study_activity_subgroup_selection_uid = kwargs.get(
            "study_activity_subgroup_selection_uid"
        )
        study_activity_group_selection_uid = kwargs.get(
            "study_activity_group_selection_uid"
        )

        activity_service = ActivityService()
        activity_uid = selection_create_input.activity_uid
        activity_ar = activity_service.repository.find_by_uid_2(
            activity_uid, for_update=True
        )

        NotFoundException.raise_if_not(activity_ar, "Activity", activity_uid)

        BusinessLogicException.raise_if(
            activity_ar.library.name != REQUESTED_LIBRARY_NAME
            and (
                selection_create_input.activity_subgroup_uid is None
                or selection_create_input.activity_group_uid is None
            ),
            msg="Only StudyActivity placeholder can link to None ActivitySubGroup or None ActivityGroup",
        )
        BusinessLogicException.raise_if(
            activity_ar.item_metadata.status
            in [
                LibraryItemStatus.DRAFT,
                LibraryItemStatus.RETIRED,
            ],
            msg=f"There is no approved Activity with UID '{activity_uid}'.",
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
            activity_uid=activity_uid,
            activity_name=activity_ar.name,
            activity_version=activity_ar.item_metadata.version,
            activity_library_name=activity_ar.library.name,
            soa_group_term_uid=selection_create_input.soa_group_term_uid,
            study_soa_group_uid=study_soa_group_selection_uid,
            study_activity_subgroup_uid=study_activity_subgroup_selection_uid,
            study_activity_group_uid=study_activity_group_selection_uid,
            order=None,
            generate_uid_callback=self.repository.generate_uid,
            activity_subgroup_uid=selection_create_input.activity_subgroup_uid,
            activity_group_uid=selection_create_input.activity_group_uid,
        )
        return new_selection

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionActivityAR,
        study_value_version: str | None = None,
    ) -> list[StudySelectionActivity]:
        result = []
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_selection.study_uid,
            study_value_version=study_value_version,
        )
        soa_groups = self._get_objects(
            study_selection=study_selection,
            att_name="soa_group_term_uid",
            terms_at_specific_datetime=terms_at_specific_datetime,
            include_retired_versions=True,
        )

        activities = []
        activities = self._get_objects(
            study_selection=study_selection, att_name="activity_uid"
        )

        activity_subgroups_uids = set()
        for activity in activities:
            for activity_grouping in activity.concept_vo.activity_groupings:
                activity_subgroups_uids.add(activity_grouping.activity_subgroup_uid)

        activity_subgroups = [
            ActivityHierarchySimpleModel.from_activity_ar_object(
                activity_ar=activity_subgroup,
            )
            for activity_subgroup in (
                self._repos.activity_subgroup_repository.get_all_optimized(
                    filter_by={"uid": {"v": activity_subgroups_uids, "op": "eq"}},
                    filter_operator=FilterOperator.OR,
                    include_retired_versions=True,
                )[0]
                if activity_subgroups_uids
                else []
            )
        ]

        activity_groups_uids = set()
        for activity in activities:
            for activity_grouping in activity.concept_vo.activity_groupings:
                activity_groups_uids.add(activity_grouping.activity_group_uid)

        activity_groups = [
            ActivityHierarchySimpleModel.from_activity_ar_object(
                activity_ar=activity_group,
            )
            for activity_group in (
                self._repos.activity_group_repository.get_all_optimized(
                    filter_by={"uid": {"v": activity_groups_uids, "op": "eq"}},
                    filter_operator=FilterOperator.OR,
                    include_retired_versions=True,
                )[0]
                if activity_groups_uids
                else []
            )
        ]

        activity_for_study_activities = []
        for activity in activities:
            activity_grouping_uids = set()
            for activity_grouping in activity.concept_vo.activity_groupings:
                activity_grouping_uids.add(activity_grouping.activity_subgroup_uid)
                activity_grouping_uids.add(activity_grouping.activity_group_uid)
            activity_for_study_activities.append(
                ActivityForStudyActivity.from_activity_ar_objects(
                    activity,
                    activity_subgroup_ars=[
                        activity_subgroup
                        for activity_subgroup in activity_subgroups
                        if activity_subgroup.uid in activity_grouping_uids
                    ],
                    activity_group_ars=[
                        activity_group
                        for activity_group in activity_groups
                        if activity_group.uid in activity_grouping_uids
                    ],
                )
            )

        for _, selection in enumerate(study_selection.study_objects_selection, start=1):
            result.append(
                self._transform_from_vo_to_response_model(
                    study_uid=study_selection.study_uid,
                    specific_selection=selection,
                    accepted_version=selection.accepted_version,
                    study_value_version=study_value_version,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                    soa_groups=soa_groups,
                    activity_for_study_activities=activity_for_study_activities,
                )
            )
        return result

    def _get_objects(
        self,
        study_selection: StudySelectionActivityAR,
        att_name: str,
        terms_at_specific_datetime: datetime | None = None,
        include_retired_versions: bool = True,
    ) -> CTTermName | ActivityAR | None:
        if att_name == "activity_uid":
            version_specific_uids = defaultdict(set)
            for selection in study_selection.study_objects_selection:
                version_specific_uids[getattr(selection, att_name)].add(
                    selection.activity_version
                )
                version_specific_uids[getattr(selection, att_name)].add("LATEST")
            return self._repos.activity_repository.get_all_optimized(
                version_specific_uids=version_specific_uids,
            )[0]
        if att_name == "soa_group_term_uid":
            return self._find_terms_by_uids(
                term_uids=[
                    getattr(selection, att_name)
                    for selection in study_selection.study_objects_selection
                ],
                at_specific_date=terms_at_specific_datetime,
                include_retired_versions=include_retired_versions,
            )
        return None

    def _transform_history_to_response_model(
        self,
        study_selection_history: list[SelectionHistory],
        study_uid: str,
        effective_dates: datetime | None = None,
    ) -> list[StudySelectionActivityCore]:
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

    @db.transaction
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
    ):
        activity_subgroup_ar = self._validate_activity_subgroup(
            activity_subgroup_uid=activity_subgroup_uid,
            perform_subgroup_validation=perform_subgroup_validation,
        )

        # create new VO to add
        new_selection = StudySelectionActivitySubGroupVO.from_input_values(
            study_uid=study_uid,
            author_id=self.author,
            activity_subgroup_uid=activity_subgroup_uid,
            activity_subgroup_name=activity_subgroup_ar.concept_vo.name,
            activity_subgroup_version=activity_subgroup_ar.item_metadata.version,
            generate_uid_callback=self._repos.study_activity_subgroup_repository.generate_uid,
        )
        return new_selection

    @classmethod
    def _validate_activity_subgroup(
        cls, activity_subgroup_uid: str, perform_subgroup_validation: bool = True
    ) -> ActivitySubGroupAR:
        activity_subgroup_service = ActivitySubGroupService()
        activity_subgroup_ar = activity_subgroup_service.repository.find_by_uid_2(
            activity_subgroup_uid, for_update=True
        )
        NotFoundException.raise_if_not(
            activity_subgroup_uid, "Activity Subgroup", activity_subgroup_uid
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
            " Contact StudyBuilder library responsible for updates.",
        )
        return activity_subgroup_ar

    def _patch_study_activity_subgroup_selection_value_object(
        self,
        study_uid: str,
        current_study_activity: StudySelectionActivityVO,
        selection_create_input: (
            StudySelectionActivityInput
            | StudySelectionActivityRequestEditInput
            | UpdateActivityPlaceholderToSponsorActivity
        ),
        study_activity_group_uid: str,
    ):
        activity_subgroup_uid = selection_create_input.activity_subgroup_uid
        activity_group_uid = selection_create_input.activity_group_uid
        soa_group_term_uid = selection_create_input.soa_group_term_uid

        if current_study_activity.study_activity_subgroup_uid is None:
            new_selection = self._get_or_create_study_activity_subgroup(
                study_uid=study_uid,
                activity_subgroup_uid=activity_subgroup_uid,
                activity_group_uid=activity_group_uid,
                soa_group_term_uid=soa_group_term_uid,
                study_activity_group_uid=study_activity_group_uid,
            )
        else:
            self._validate_activity_subgroup(
                activity_subgroup_uid=activity_subgroup_uid
            )
            # create new VO to add
            new_selection = self._get_or_create_study_activity_subgroup(
                study_uid=study_uid,
                activity_subgroup_uid=activity_subgroup_uid,
                activity_group_uid=activity_group_uid,
                soa_group_term_uid=soa_group_term_uid,
                study_activity_group_uid=study_activity_group_uid,
            )

        return new_selection

    @classmethod
    def _validate_activity_group(
        cls, activity_group_uid: str, perform_group_validation: bool = True
    ) -> ActivityGroupAR:
        activity_group_service = ActivityGroupService()
        activity_group_ar = activity_group_service.repository.find_by_uid_2(
            activity_group_uid, for_update=True
        )

        NotFoundException.raise_if_not(
            activity_group_uid, "Activity Group", activity_group_uid
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
            " Contact StudyBuilder library responsible for updates.",
        )
        return activity_group_ar

    def _create_activity_group_selection_value_object(
        self,
        study_uid: str,
        activity_group_uid: str,
        perform_group_validation: bool = True,
    ):
        activity_group_ar = self._validate_activity_group(
            activity_group_uid=activity_group_uid,
            perform_group_validation=perform_group_validation,
        )
        # create new VO to add
        new_selection = StudySelectionActivityGroupVO.from_input_values(
            study_uid=study_uid,
            author_id=self.author,
            activity_group_uid=activity_group_uid,
            activity_group_name=activity_group_ar.concept_vo.name,
            activity_group_version=activity_group_ar.item_metadata.version,
            generate_uid_callback=self._repos.study_activity_group_repository.generate_uid,
        )
        return new_selection

    def _patch_study_activity_group_selection_value_object(
        self,
        study_uid: str,
        current_study_activity: StudySelectionActivityVO,
        selection_create_input: (
            StudySelectionActivityInput
            | StudySelectionActivityRequestEditInput
            | UpdateActivityPlaceholderToSponsorActivity
        ),
        study_soa_group_uid: str,
    ):
        activity_subgroup_uid = selection_create_input.activity_subgroup_uid
        activity_group_uid = selection_create_input.activity_group_uid
        soa_group_term_uid = selection_create_input.soa_group_term_uid

        if current_study_activity.study_activity_group_uid is None:
            new_selection = self._get_or_create_study_activity_group(
                study_uid=study_uid,
                activity_subgroup_uid=activity_subgroup_uid,
                activity_group_uid=activity_group_uid,
                soa_group_term_uid=soa_group_term_uid,
                study_soa_group_uid=study_soa_group_uid,
            )
        else:
            self._validate_activity_group(activity_group_uid=activity_group_uid)
            # create new VO to add
            new_selection = self._get_or_create_study_activity_group(
                study_uid=study_uid,
                activity_subgroup_uid=activity_subgroup_uid,
                activity_group_uid=activity_group_uid,
                soa_group_term_uid=soa_group_term_uid,
                study_soa_group_uid=study_soa_group_uid,
            )

        return new_selection

    def _patch_selected_activity(
        self,
        current_object: StudySelectionActivityVO,
        request_object: StudySelectionActivityRequestEditInput,
    ) -> ActivityAR:
        activity_service = ActivityService()
        activity_ar = activity_service.repository.find_by_uid_2(
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
            activity_name = current_object.activity_name
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
                activity_subgroup_uid=activity_subgroup_uid,
                activity_group_uid=activity_group_uid,
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
        soa_group_term_uid = selection_create_input.soa_group_term_uid
        selection_aggregate = self._repos.study_soa_group_repository.find_by_study(
            study_uid=study_uid
        )
        assert selection_aggregate is not None
        new_selection, _ = selection_aggregate.get_specific_object_selection(
            study_selection_uid=current_study_activity.study_soa_group_uid
        )
        if is_soa_group_changed:
            ct_term_ar = self._repos.ct_term_name_repository.find_by_uid(
                soa_group_term_uid
            )

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
            new_selection = self._get_or_create_study_soa_group(
                study_uid=study_uid, soa_group_term_uid=soa_group_term_uid
            )

        return new_selection

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
        study_soa_group_node = (
            self._repos.study_soa_group_repository.find_study_soa_group_in_a_study(
                study_uid=study_uid,
                soa_group_term_uid=soa_group_term_uid,
            )
        )
        if study_soa_group_node:
            (
                _,
                study_soa_group_selection,
                _,
            ) = self._get_specific_soa_group_selection_by_uids(
                study_uid=study_uid, study_selection_uid=study_soa_group_node.uid
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
        return study_soa_group_selection

    def _get_or_create_study_activity_subgroup(
        self,
        study_uid: str,
        activity_subgroup_uid: str,
        activity_group_uid: str,
        study_activity_group_uid: str,
        soa_group_term_uid: str,
        perform_subgroup_validation: bool = True,
    ) -> StudySelectionActivitySubGroupVO:
        study_activity_subgroup_selection: StudySelectionActivitySubGroupVO | None = (
            None
        )

        if activity_subgroup_uid:
            study_activity_subgroup_node = self._repos.study_activity_subgroup_repository.find_study_activity_subgroup_with_same_groupings(
                study_uid=study_uid,
                activity_subgroup_uid=activity_subgroup_uid,
                activity_group_uid=activity_group_uid,
                soa_group_term_uid=soa_group_term_uid,
            )
            if study_activity_subgroup_node:
                (
                    _,
                    study_activity_subgroup_selection,
                    _,
                ) = self._get_specific_activity_subgroup_selection_by_uids(
                    study_uid=study_uid,
                    study_selection_uid=study_activity_subgroup_node.uid,
                )
            else:
                # create new VO to add
                study_activity_subgroup_selection = (
                    self._create_activity_subgroup_selection_value_object(
                        study_uid=study_uid,
                        activity_subgroup_uid=activity_subgroup_uid,
                        perform_subgroup_validation=perform_subgroup_validation,
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
        return study_activity_subgroup_selection

    def _get_or_create_study_activity_group(
        self,
        study_uid: str,
        activity_subgroup_uid: str,
        activity_group_uid: str,
        soa_group_term_uid: str,
        study_soa_group_uid: str,
        perform_group_validation: bool = True,
    ) -> StudySelectionActivityGroupVO:
        study_activity_group_selection: StudySelectionActivityGroupVO | None = None

        if activity_subgroup_uid and activity_group_uid:
            study_activity_group_node = self._repos.study_activity_group_repository.find_study_activity_group_with_same_groupings(
                study_uid=study_uid,
                activity_group_uid=activity_group_uid,
                soa_group_term_uid=soa_group_term_uid,
            )
            if study_activity_group_node:
                (
                    _,
                    study_activity_group_selection,
                    _,
                ) = self._get_specific_activity_group_selection_by_uids(
                    study_uid=study_uid,
                    study_selection_uid=study_activity_group_node.uid,
                )
            else:
                # create new VO to add
                study_activity_group_selection = (
                    self._create_activity_group_selection_value_object(
                        study_uid=study_uid,
                        activity_group_uid=activity_group_uid,
                        perform_group_validation=perform_group_validation,
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
        return study_activity_group_selection

    def _create_study_activity_instances(
        self, study_uid: str, study_activity_selection: StudySelectionActivityVO
    ):
        # Find ActivityInstances linked to the ActivityGroupings referenced by StudyActivity
        related_activity_instances = self._repos.activity_instance_repository.get_all_activity_instances_for_activity_grouping(
            activity_uid=study_activity_selection.activity_uid,
            activity_subgroup_uid=study_activity_selection.activity_subgroup_uid,
            activity_group_uid=study_activity_selection.activity_group_uid,
            filter_by_boolean_flags=True,
        )
        linked_activity_instances = []
        for activity_instance in related_activity_instances:
            if activity_instance.uid not in linked_activity_instances:
                linked_activity_instances.append(activity_instance.uid)

        # If there is no ActivityInstances linked to selected Activity
        # we create a 'placeholder' StudyActivityInstance that can link to ActivityInstance later
        if len(linked_activity_instances) == 0:
            linked_activity_instances.append(None)
        for activity_instance_uid in linked_activity_instances:
            activity_instance_selection = StudySelectionActivityInstanceVO.from_input_values(
                study_uid=study_uid,
                author_id=self.author,
                activity_instance_uid=activity_instance_uid,
                activity_uid=study_activity_selection.activity_uid,
                activity_subgroup_uid=study_activity_selection.activity_subgroup_uid,
                activity_group_uid=study_activity_selection.activity_group_uid,
                study_activity_uid=study_activity_selection.study_selection_uid,
                generate_uid_callback=self._repos.study_activity_instance_repository.generate_uid,
            )  # add VO to aggregate

            study_activity_instance_aggregate = (
                self._repos.study_activity_instance_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )
            assert study_activity_instance_aggregate is not None
            study_activity_instance_aggregate.add_object_selection(
                activity_instance_selection,
                self._repos.activity_instance_repository.check_exists_final_version,
            )
            study_activity_instance_aggregate.validate()
            # sync with DB and save the update
            self._repos.study_activity_instance_repository.save(
                study_activity_instance_aggregate, self.author
            )

    def _recreate_study_activity_instances_after_activity_replacement(
        self, study_uid: str, study_activity_selection: StudySelectionActivityVO
    ):
        # Remove related Study activity instances
        study_activity_instances = self._repos.study_activity_instance_repository.get_all_study_activity_instances_for_study_activity(
            study_uid=study_uid,
            study_activity_uid=study_activity_selection.study_selection_uid,
        )
        for study_activity_instance in study_activity_instances:
            # delete study activity instance
            (
                study_activity_instance_ar,
                _,
                _,
            ) = self._get_specific_activity_instance_selection_by_uids(
                study_uid=study_uid,
                study_selection_uid=study_activity_instance.uid,
                for_update=True,
            )
            study_activity_instance_ar.remove_object_selection(
                study_activity_instance.uid
            )
            self._repos.study_activity_instance_repository.save(
                study_activity_instance_ar, self.author
            )
        self._create_study_activity_instances(
            study_uid=study_uid, study_activity_selection=study_activity_selection
        )

    @ensure_transaction(db)
    def make_selection(
        self,
        study_uid: str,
        selection_create_input: StudySelectionActivityCreateInput,
    ) -> StudySelectionActivity:
        repos = self._repos
        try:
            study_soa_group_selection_uid = self._get_or_create_study_soa_group(
                study_uid=study_uid,
                soa_group_term_uid=selection_create_input.soa_group_term_uid,
            ).study_selection_uid

            study_activity_group_selection = self._get_or_create_study_activity_group(
                study_uid=study_uid,
                soa_group_term_uid=selection_create_input.soa_group_term_uid,
                study_soa_group_uid=study_soa_group_selection_uid,
                activity_group_uid=selection_create_input.activity_group_uid,
                activity_subgroup_uid=selection_create_input.activity_subgroup_uid,
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
                study_soa_group_selection_uid=study_soa_group_selection_uid,
                study_activity_subgroup_selection_uid=study_activity_subgroup_selection_uid,
                study_activity_group_selection_uid=study_activity_group_selection_uid,
            )
            # add VO to aggregate
            study_activity_aggregate = self.repository.find_by_study(
                study_uid=study_uid,
                for_update=True,
                study_activity_subgroup_uid=study_activity_subgroup_selection_uid,
                study_soa_group_uid=study_soa_group_selection_uid,
                find_requested_study_activities=study_activity_selection.activity_library_name
                == REQUESTED_LIBRARY_NAME,
            )
            assert study_activity_aggregate is not None
            study_activity_aggregate.add_object_selection(
                study_activity_selection,
                self.selected_object_repository.check_exists_final_version,
                self._repos.ct_term_name_repository.term_specific_exists_by_uid,
            )
            study_activity_aggregate.validate()
            # sync with DB and save the update
            self.repository.save(study_activity_aggregate, self.author)

            # create StudyActivityInstance selection
            if (
                # We are not creating a StudyActivityInstance selection for Activity placeholders
                study_activity_selection.activity_library_name
                != REQUESTED_LIBRARY_NAME
            ):
                self._create_study_activity_instances(
                    study_uid=study_uid,
                    study_activity_selection=study_activity_selection,
                )

            study_activity_aggregate = self.repository.find_by_study(
                study_uid=study_uid,
            )
            # Fetch the new selection which was just added
            (
                new_selection,
                _,
            ) = study_activity_aggregate.get_specific_object_selection(
                study_activity_selection.study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            # add the activity and return
            return self._transform_from_vo_to_response_model(
                study_uid=study_activity_aggregate.study_uid,
                specific_selection=new_selection,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    @ensure_transaction(db)
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        # StudyActivitySchedule and StudyActivityInstruction Services for cascade delete if any
        study_activity_schedules_service = StudyActivityScheduleService()
        study_activity_instructions_service = StudyActivityInstructionService()
        study_activity_group_service = StudyActivityGroupService()
        study_activity_subgroup_service = StudyActivitySubGroupService()
        study_soa_group_service = StudySoAGroupService()

        repos = self._repos
        try:
            # Load aggregate
            study_activity_selection: StudySelectionActivityVO
            selection_aggregate, study_activity_selection = self._find_ar_to_patch(
                study_uid=study_uid, study_selection_uid=study_selection_uid
            )

            activity_ar = repos.activity_repository.find_by_uid_2(
                study_activity_selection.activity_uid, for_update=True
            )
            # We should retire ActivityRequest if it's not finalized
            if (
                activity_ar.library.name == REQUESTED_LIBRARY_NAME
                and not activity_ar.concept_vo.is_finalized
                and activity_ar.concept_vo.is_request_final
            ):
                ValidationException.raise_if_not(
                    activity_ar,
                    msg=f"The Activity with UID '{study_activity_selection.activity_uid}' doesn't exist.",
                )
                if activity_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                    activity_ar.approve(author_id=self.author)
                    activity_ar.inactivate(author_id=self.author)
                if activity_ar.item_metadata.status == LibraryItemStatus.FINAL:
                    activity_ar.inactivate(author_id=self.author)
                repos.activity_repository.save(activity_ar)

            # Remove related Study activity schedules
            study_activity_schedules = study_activity_schedules_service.get_all_schedules_for_specific_activity(
                study_uid=study_uid, study_activity_uid=study_selection_uid
            )
            for study_activity_schedule in study_activity_schedules:
                self._repos.study_activity_schedule_repository.delete(
                    study_uid,
                    study_activity_schedule.study_activity_schedule_uid,
                    self.author,
                )

            # Remove related Study activity instructions
            study_activity_instructions = study_activity_instructions_service.get_all_study_instructions_for_specific_study_activity(
                study_uid=study_uid, study_activity_uid=study_selection_uid
            )
            for study_activity_instruction in study_activity_instructions:
                self._repos.study_activity_instruction_repository.delete(
                    study_uid,
                    study_activity_instruction.study_activity_instruction_uid,
                    self.author,
                )

            # Remove related Study activity subgroups
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
            study_soa_groups = repos.study_soa_group_repository.get_all_study_soa_groups_for_study_activity(
                study_uid=study_uid, study_activity_uid=study_selection_uid
            )
            for study_soa_group in study_soa_groups:
                # delete study soa group
                study_soa_group_ar, _ = study_soa_group_service._find_ar_to_patch(
                    study_uid=study_uid, study_selection_uid=study_soa_group.uid
                )
                study_soa_group_ar.remove_object_selection(study_soa_group.uid)
                repos.study_soa_group_repository.save(study_soa_group_ar, self.author)

            # Remove related Study activity instances
            study_activity_instances = repos.study_activity_instance_repository.get_all_study_activity_instances_for_study_activity(
                study_uid=study_uid, study_activity_uid=study_selection_uid
            )
            for study_activity_instance in study_activity_instances:
                # delete study activity instance
                (
                    study_activity_instance_ar,
                    _,
                    _,
                ) = self._get_specific_activity_instance_selection_by_uids(
                    study_uid=study_uid,
                    study_selection_uid=study_activity_instance.uid,
                    for_update=True,
                )
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
        # update underlying Activity
        activity_service = ActivityService()

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
            activity_ar = activity_service.repository.find_by_uid_2(
                request_object.activity_uid
            )
            ValidationException.raise_if_not(
                activity_ar,
                msg=f"The Activity with UID '{current_object.activity_uid}' doesn't exist.",
            )
        else:
            activity_ar = activity_service.repository.find_by_uid_2(
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
        activity_ar: ActivityAR,
        current_object: StudySelectionActivityVO,
    ):
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
        ValidationException.raise_if(
            request_object.activity_group_uid
            and request_object.activity_group_uid
            not in [
                activity_grouping.activity_group_uid
                for activity_grouping in activity_ar.concept_vo.activity_groupings
            ],
            msg=f"Provided Activity Group is not included in '{current_object.activity_uid}' Activity Groupings.",
        )
        ValidationException.raise_if(
            request_object.activity_subgroup_uid
            and not any(
                activity_grouping.activity_subgroup_uid
                == request_object.activity_subgroup_uid
                and activity_grouping.activity_group_uid
                == request_object.activity_group_uid
                for activity_grouping in activity_ar.concept_vo.activity_groupings
            ),
            msg=f"Provided Activity Subgroup is not part of a Grouping with UID '{request_object.activity_group_uid}' Group in the '{current_object.activity_uid}' Activity Groupings.",
        )

    def _patch_or_get_study_activity_group(
        self,
        request_object: (
            StudyActivityReplaceActivityInput
            | StudySelectionActivityInput
            | StudySelectionActivityRequestEditInput
            | UpdateActivityPlaceholderToSponsorActivity
        ),
        current_object: StudySelectionActivityVO,
        is_soa_group_changed: bool,
        study_soa_group_uid: str,
    ):

        activity_group_uid = current_object.activity_group_uid
        activity_group_name = current_object.activity_group_name
        study_activity_group_uid = current_object.study_activity_group_uid
        if (
            request_object.activity_group_uid
            and current_object.activity_group_uid != request_object.activity_group_uid
        ):
            activity_group_uid = request_object.activity_group_uid
            study_activity_group = (
                self._patch_study_activity_group_selection_value_object(
                    study_uid=current_object.study_uid,
                    current_study_activity=current_object,
                    selection_create_input=request_object,
                    study_soa_group_uid=study_soa_group_uid,
                )
            )
            study_activity_group_uid = study_activity_group.study_selection_uid
            activity_group_name = study_activity_group.activity_group_name
        # When SoAGroup is changed we need to update StudyActivityGroup for other shared nodes if given StudyActivity contains StudyActivityGroup
        elif is_soa_group_changed and activity_group_uid:
            activity_group_selection = self._get_or_create_study_activity_group(
                study_uid=current_object.study_uid,
                activity_subgroup_uid=current_object.activity_subgroup_uid,
                activity_group_uid=activity_group_uid,
                soa_group_term_uid=request_object.soa_group_term_uid,
                study_soa_group_uid=study_soa_group_uid,
                perform_group_validation=False,
            )
            (
                activity_group_uid,
                activity_group_name,
                study_activity_group_uid,
            ) = (
                activity_group_selection.activity_group_uid,
                None,
                activity_group_selection.study_selection_uid,
            )
        return activity_group_uid, activity_group_name, study_activity_group_uid

    def _patch_or_get_study_activity_subgroup(
        self,
        request_object: (
            StudyActivityReplaceActivityInput
            | StudySelectionActivityInput
            | StudySelectionActivityRequestEditInput
            | UpdateActivityPlaceholderToSponsorActivity
        ),
        current_object: StudySelectionActivityVO,
        is_soa_group_changed: bool,
        is_study_activity_group_changed: bool,
        study_activity_group_uid: str,
    ):
        activity_subgroup_uid = current_object.activity_subgroup_uid
        activity_subgroup_name = current_object.activity_subgroup_name
        study_activity_subgroup_uid = current_object.study_activity_subgroup_uid
        if (
            request_object.activity_subgroup_uid
            and current_object.activity_subgroup_uid
            != request_object.activity_subgroup_uid
        ):
            activity_subgroup_uid = request_object.activity_subgroup_uid
            study_activity_subgroup = (
                self._patch_study_activity_subgroup_selection_value_object(
                    study_uid=current_object.study_uid,
                    current_study_activity=current_object,
                    selection_create_input=request_object,
                    study_activity_group_uid=study_activity_group_uid,
                )
            )
            study_activity_subgroup_uid = study_activity_subgroup.study_selection_uid
            activity_subgroup_name = study_activity_subgroup.activity_subgroup_name
        # When SoAGroup or StudyActivityGroup is changed we need to update StudyActivitySubGroup for other shared nodes if given StudyActivity contains StudyActivitySubGroup
        elif (
            is_soa_group_changed or is_study_activity_group_changed
        ) and activity_subgroup_uid:
            activity_subgroup_selection = self._get_or_create_study_activity_subgroup(
                study_uid=current_object.study_uid,
                activity_subgroup_uid=activity_subgroup_uid,
                activity_group_uid=current_object.activity_group_uid,
                soa_group_term_uid=request_object.soa_group_term_uid,
                perform_subgroup_validation=False,
                study_activity_group_uid=study_activity_group_uid,
            )
            (
                activity_subgroup_uid,
                activity_subgroup_name,
                study_activity_subgroup_uid,
            ) = (
                activity_subgroup_selection.activity_subgroup_uid,
                None,
                activity_subgroup_selection.study_selection_uid,
            )

        return (
            activity_subgroup_uid,
            activity_subgroup_name,
            study_activity_subgroup_uid,
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
            activity_group_uid=None,
            activity_subgroup_uid=None,
        )

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
        (
            activity_group_uid,
            activity_group_name,
            study_activity_group_uid,
        ) = self._patch_or_get_study_activity_group(
            request_object=request_object,
            current_object=current_object,
            is_soa_group_changed=is_soa_group_changed,
            study_soa_group_uid=updated_soa_selection.study_selection_uid,
        )

        is_study_activity_group_changed = (
            study_activity_group_uid != current_object.study_activity_group_uid
        )
        # update StudyActivitySubGroup
        (
            activity_subgroup_uid,
            activity_subgroup_name,
            study_activity_subgroup_uid,
        ) = self._patch_or_get_study_activity_subgroup(
            request_object=request_object,
            current_object=current_object,
            is_soa_group_changed=is_soa_group_changed,
            is_study_activity_group_changed=is_study_activity_group_changed,
            study_activity_group_uid=study_activity_group_uid,
        )
        updated_study_activity_vo = StudySelectionActivityVO.from_input_values(
            study_uid=current_object.study_uid,
            activity_uid=activity_ar.uid,
            activity_version=activity_ar.item_metadata.version,
            activity_name=activity_ar.name,
            soa_group_term_uid=updated_soa_selection.soa_group_term_uid,
            study_soa_group_uid=updated_soa_selection.study_selection_uid,
            study_selection_uid=current_object.study_selection_uid,
            study_activity_subgroup_uid=study_activity_subgroup_uid,
            activity_subgroup_uid=activity_subgroup_uid,
            activity_subgroup_name=activity_subgroup_name,
            study_activity_group_uid=study_activity_group_uid,
            activity_group_uid=activity_group_uid,
            activity_group_name=activity_group_name,
            show_activity_in_protocol_flowchart=request_object.show_activity_in_protocol_flowchart,
            author_id=self.author,
            activity_library_name=current_object.activity_library_name,
        )

        return updated_study_activity_vo

    @ensure_transaction(db)
    def handle_batch_operations(
        self,
        study_uid: str,
        operations: list[StudySelectionActivityBatchInput],
    ) -> list[StudySelectionActivityBatchOutput]:
        results = []
        for operation in operations:
            result = {}
            item = None
            try:
                if operation.method == "PATCH":
                    item = self.patch_selection(
                        study_uid,
                        operation.content.study_activity_uid,
                        operation.content.content,
                    )
                    response_code = status.HTTP_200_OK
                elif operation.method == "DELETE":
                    self.delete_selection(
                        study_uid, operation.content.study_activity_uid
                    )
                    response_code = status.HTTP_204_NO_CONTENT
                elif operation.method == "POST":
                    item = self.make_selection(study_uid, operation.content)
                    response_code = status.HTTP_201_CREATED
                else:
                    raise MethodNotAllowedException(method=operation.method)
                result["response_code"] = response_code
                result["content"] = item
                results.append(StudySelectionActivityBatchOutput(**result))
            except MDRApiBaseException as error:
                results.append(
                    StudySelectionActivityBatchOutput.model_construct(
                        response_code=error.status_code,
                        content=BatchErrorResponse(message=str(error)),
                    )
                )
        all_soa_footnotes = (
            self._repos.study_soa_footnote_repository.find_all_footnotes(
                study_uids=study_uid
            )
        )
        StudySoAFootnoteService().synchronize_footnotes(
            study_uid=study_uid, all_soa_footnotes=all_soa_footnotes
        )
        return results

    @ensure_transaction(db)
    def handle_soa_edit_batch_operations(
        self,
        study_uid: str,
        operations: list[StudySoAEditBatchInput],
    ) -> list[StudySoAEditBatchOutput]:
        study_activity_schedules_service = StudyActivityScheduleService()
        results = []
        for operation in operations:
            result = {}
            item = None
            try:
                if (
                    operation.method == "PATCH"
                    and operation.object == SoAItemType.STUDY_ACTIVITY.value
                ):
                    item = self.patch_selection(
                        study_uid,
                        operation.content.study_activity_uid,
                        operation.content.content,
                    )
                    response_code = status.HTTP_200_OK
                elif operation.method == "POST":
                    if operation.object == SoAItemType.STUDY_ACTIVITY.value:
                        item = self.make_selection(study_uid, operation.content)
                    elif operation.object == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value:
                        item = study_activity_schedules_service.create(
                            study_uid, operation.content
                        )
                    response_code = status.HTTP_201_CREATED
                elif operation.method == "DELETE":
                    if operation.object == SoAItemType.STUDY_ACTIVITY.value:
                        self.delete_selection(
                            study_uid, operation.content.study_activity_uid
                        )
                    elif operation.object == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value:
                        item = study_activity_schedules_service.delete(
                            study_uid, operation.content.uid
                        )
                    response_code = status.HTTP_204_NO_CONTENT
                else:
                    raise MethodNotAllowedException(method=operation.method)
                result["response_code"] = response_code
                result["content"] = item
                results.append(StudySoAEditBatchOutput(**result))
            except MDRApiBaseException as error:
                results.append(
                    StudySoAEditBatchOutput.model_construct(
                        response_code=error.status_code,
                        content=BatchErrorResponse(message=str(error)),
                    )
                )
        all_soa_footnotes = (
            self._repos.study_soa_footnote_repository.find_all_footnotes(
                study_uids=study_uid
            )
        )
        StudySoAFootnoteService().synchronize_footnotes(
            study_uid=study_uid, all_soa_footnotes=all_soa_footnotes
        )
        return results

    @db.transaction
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
        activity_ar = self._repos.activity_repository.find_by_uid_2(
            current_vo.activity_uid
        )
        replaced_activity_ar = self._repos.activity_repository.find_by_uid_2(
            activity_ar.concept_vo.replaced_by_activity
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
        all_detailed_history = GenericFilteringReturn.create(
            items=detailed_soa_history, total=amount_of_history_items
        )
        all_detailed_history.items = [
            DetailedSoAHistory.from_history(detailed_soa_history_item=item)
            for item in all_detailed_history.items
        ]
        return all_detailed_history

    @db.transaction
    def update_selection_to_latest_version(
        self, study_uid: str, study_selection_uid: str
    ):
        selection_ar, selection = self._find_ar_to_patch(
            study_uid=study_uid, study_selection_uid=study_selection_uid
        )
        activity_uid = selection.activity_uid
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
        new_selection: StudySelectionActivityVO = selection.update_version(
            activity_version=activity_ar.item_metadata.version
        )
        selection_ar.update_selection(new_selection)
        self._repos.study_activity_repository.save(selection_ar, self.author)
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_uid
        )
        selection_aggregate = self.repository.find_by_study(
            study_uid=study_uid,
        )
        # Fetch the new selection which was just added
        (
            new_selection,
            _,
        ) = selection_aggregate.get_specific_object_selection(study_selection_uid)

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
        return self.set_new_order(
            study_uid=study_uid,
            study_selection_uid=new_study_activity.study_activity_uid,
            new_order=selection_create_input.order,
        )
