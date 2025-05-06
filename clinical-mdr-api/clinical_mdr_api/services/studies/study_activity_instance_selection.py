from collections import defaultdict
from datetime import datetime
from typing import Callable

from fastapi import status
from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.activities.activity_instance_repository import (
    ActivityInstanceRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_instance_repository import (
    SelectionHistory,
    StudySelectionActivityInstanceRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity import ActivityAR
from clinical_mdr_api.domains.study_selections.study_selection_activity_instance import (
    StudySelectionActivityInstanceAR,
    StudySelectionActivityInstanceVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityForStudyActivity,
    ActivityHierarchySimpleModel,
)
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term_name import CTTermName
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.study_selections.study_selection import (
    StudySelectionActivityInstance,
    StudySelectionActivityInstanceBatchCreate,
    StudySelectionActivityInstanceBatchOutput,
    StudySelectionActivityInstanceCreateInput,
    StudySelectionActivityInstanceEditInput,
)
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    ensure_transaction,
    fill_missing_values_in_base_model_from_reference_base_model,
)
from clinical_mdr_api.services.concepts.activities.activity_instance_service import (
    ActivityInstanceService,
)
from clinical_mdr_api.services.studies.study_activity_selection_base import (
    StudyActivitySelectionBaseService,
)
from common import exceptions


class StudyActivityInstanceSelectionService(StudyActivitySelectionBaseService):
    _repos: MetaRepository
    repository_interface = StudySelectionActivityInstanceRepository
    selected_object_repository_interface = ActivityInstanceRepository

    def update_dependent_objects(
        self,
        study_selection: StudySelectionActivityInstanceVO,
        previous_study_selection: StudySelectionActivityInstanceVO,
    ):
        pass

    def _find_ar_and_validate_new_order(
        self,
        study_uid: str,
        study_selection_uid: str,
        new_order: int,
    ) -> tuple[StudySelectionActivityInstanceAR, StudySelectionActivityInstanceVO]:
        pass

    def _filter_ars_from_same_parent(
        self,
        selection_aggregate: StudySelectionActivityInstanceAR,
        selection_vo: StudySelectionActivityInstanceVO,
    ) -> StudySelectionActivityInstanceAR:
        return selection_aggregate

    _vo_to_ar_filter_map = {
        "order": "order",
        "start_date": "start_date",
        "author_id": "author_id",
        "activity.name": "activity_name",
        "activity_instance.name": "activity_instance_name",
        "study_soa_group.soa_group_term_name": "soa_group_term_name",
        "study_activity_subgroup.activity_subgroup_name": "activity_subgroup_name",
        "study_activity_group.activity_group_name": "activity_group_name",
    }

    def _get_selected_object_exist_check(self) -> Callable[[str], bool]:
        return self.selected_object_repository.final_concept_exists

    def _transform_from_vo_to_response_model(
        self,
        study_uid: str,
        specific_selection: StudySelectionActivityInstanceVO,
        terms_at_specific_datetime: datetime | None = None,
        accepted_version: bool = False,
        activity_for_study_activity_instances: (
            list[ActivityForStudyActivity] | None
        ) = None,
        activity_instances_for_study_activity_instances: (
            list[ActivityInstance] | None
        ) = None,
    ) -> StudySelectionActivityInstance:
        return StudySelectionActivityInstance.from_study_selection_activity_instance_vo_and_order(
            study_uid=study_uid,
            specific_selection=specific_selection,
            get_activity_by_uid_callback=self._transform_latest_activity_model,
            get_activity_by_uid_version_callback=self._transform_activity_model,
            get_activity_instance_by_uid_callback=self._transform_latest_activity_instance_model,
            get_activity_instance_by_uid_version_callback=self._transform_activity_instance_model,
            activity_for_study_activity_instances=activity_for_study_activity_instances,
            activity_instances_for_study_activity_instances=activity_instances_for_study_activity_instances,
        )

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionActivityInstanceAR,
        study_value_version: str | None = None,
    ) -> list[StudySelectionActivityInstance]:
        result = []

        # ACTIVITIES
        activities = []
        activities = self._get_objects(
            study_selection=study_selection, att_name="activity_uid"
        )

        activity_groups_uids = set()
        activity_subgroups_uids = set()
        for activity in activities:
            for activity_grouping in activity.concept_vo.activity_groupings:
                activity_subgroups_uids.add(activity_grouping.activity_subgroup_uid)
                activity_groups_uids.add(activity_grouping.activity_group_uid)

        activity_subgroups = [
            ActivityHierarchySimpleModel.from_activity_ar_object(
                activity_ar=activity_subgroup,
            )
            for activity_subgroup in (
                self._repos.activity_subgroup_repository.get_all_optimized(
                    filter_by={"uid": {"v": activity_subgroups_uids, "op": "eq"}},
                    filter_operator=FilterOperator.OR,
                )[0]
                if activity_subgroups_uids
                else []
            )
        ]

        activity_groups = [
            ActivityHierarchySimpleModel.from_activity_ar_object(
                activity_ar=activity_group,
            )
            for activity_group in (
                self._repos.activity_group_repository.get_all_optimized(
                    filter_by={"uid": {"v": activity_groups_uids, "op": "eq"}},
                    filter_operator=FilterOperator.OR,
                )[0]
                if activity_groups_uids
                else []
            )
        ]

        activity_for_study_activities: list[ActivityForStudyActivity] = []
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

        # ACTIVITY INSTANCES
        activity_instances = []
        activity_instances = self._get_objects(
            study_selection=study_selection, att_name="activity_instance_uid"
        )

        activity_instance_subgroups_uids = set()
        activity_instance_groups_uids = set()
        for activity_instance in activity_instances:
            for (
                activity_instance_grouping
            ) in activity_instance.concept_vo.activity_groupings:
                activity_instance_subgroups_uids.add(
                    activity_instance_grouping.activity_subgroup_uid
                )
                activity_instance_groups_uids.add(
                    activity_instance_grouping.activity_group_uid
                )

        activity_instance_grouping_activity_subgroups = [
            ActivityHierarchySimpleModel.from_activity_ar_object(
                activity_ar=activity_instance_subgroup,
            )
            for activity_instance_subgroup in (
                self._repos.activity_subgroup_repository.get_all_optimized(
                    filter_by={
                        "uid": {"v": activity_instance_subgroups_uids, "op": "eq"}
                    },
                    filter_operator=FilterOperator.OR,
                )[0]
                if activity_instance_subgroups_uids
                else []
            )
        ]

        activity_instance_grouping_activity_groups = [
            ActivityHierarchySimpleModel.from_activity_ar_object(
                activity_ar=activity_instance_group,
            )
            for activity_instance_group in (
                self._repos.activity_group_repository.get_all_optimized(
                    filter_by={"uid": {"v": activity_instance_groups_uids, "op": "eq"}},
                    filter_operator=FilterOperator.OR,
                )[0]
                if activity_instance_groups_uids
                else []
            )
        ]

        activity_instances_for_study_activity_instances = []
        for activity_instance in activity_instances:
            activity_instance_grouping_uids = set()
            for (
                activity_instance_grouping
            ) in activity_instance.concept_vo.activity_groupings:
                activity_instance_grouping_uids.add(
                    activity_instance_grouping.activity_subgroup_uid
                )
                activity_instance_grouping_uids.add(
                    activity_instance_grouping.activity_group_uid
                )
                activity_instance_grouping_uids.add(
                    activity_instance_grouping.activity_uid
                )
            activity_instances_for_study_activity_instances.append(
                ActivityInstance.from_activity_instance_ar_objects(
                    activity_instance_ar=activity_instance,
                    activity_ars=[
                        activity_instance_grouping_activity
                        for activity_instance_grouping_activity in activity_for_study_activities
                        if activity_instance_grouping_activity.uid
                        in activity_instance_grouping_uids
                    ],
                    activity_instance_subgroup_ars=[
                        activity_instance_grouping_activity_subgroup
                        for activity_instance_grouping_activity_subgroup in activity_instance_grouping_activity_subgroups
                        if activity_instance_grouping_activity_subgroup.uid
                        in activity_instance_grouping_uids
                    ],
                    activity_instance_group_ars=[
                        activity_instance_grouping_activity_group
                        for activity_instance_grouping_activity_group in activity_instance_grouping_activity_groups
                        if activity_instance_grouping_activity_group.uid
                        in activity_instance_grouping_uids
                    ],
                )
            )
        for specific_selection in study_selection.study_objects_selection:
            result.append(
                self._transform_from_vo_to_response_model(
                    study_uid=study_selection.study_uid,
                    specific_selection=specific_selection,
                    activity_for_study_activity_instances=activity_for_study_activities,
                    activity_instances_for_study_activity_instances=activity_instances_for_study_activity_instances,
                )
            )
        return result

    def _get_objects(
        self, study_selection: StudySelectionActivityInstanceAR, att_name: str
    ) -> CTTermName | ActivityAR | None:
        if att_name == "activity_uid":
            version_specific_uids = defaultdict(set)
            for selection in study_selection.study_objects_selection:
                version_specific_uids[getattr(selection, att_name)].add(
                    selection.activity_version
                )
                version_specific_uids[getattr(selection, att_name)].add("LATEST")
            return self._repos.activity_repository.get_all_optimized(
                version_specific_uids=version_specific_uids
            )[0]
        if att_name == "activity_instance_uid":
            version_specific_uids = defaultdict(set)
            for selection in study_selection.study_objects_selection:
                if selection.activity_instance_uid:
                    version_specific_uids[getattr(selection, att_name)].add(
                        selection.activity_instance_version
                    )
                    version_specific_uids[getattr(selection, att_name)].add("LATEST")
            return self._repos.activity_instance_repository.get_all_optimized(
                version_specific_uids=version_specific_uids
            )[0]
        return None

    def _transform_history_to_response_model(
        self, study_selection_history: list[SelectionHistory], study_uid: str
    ) -> list[StudySelectionActivityInstance]:
        result = []
        for history in study_selection_history:
            result.append(
                StudySelectionActivityInstance.from_study_selection_history(
                    study_selection_history=history,
                    study_uid=study_uid,
                    get_activity_by_uid_version_callback=self._transform_activity_model,
                    get_activity_instance_by_uid_version_callback=self._transform_activity_instance_model,
                )
            )
        return result

    def activity_instance_validation(
        self,
        activity_instance_uid: str,
        study_activity_selection: StudySelectionActivityInstanceVO,
    ):
        activity_instance_service = ActivityInstanceService()
        activity_instance_ar = activity_instance_service.repository.find_by_uid_2(
            activity_instance_uid, for_update=True
        )
        exceptions.NotFoundException.raise_if_not(
            activity_instance_uid, "Activity Instance", activity_instance_uid
        )

        exceptions.NotFoundException.raise_if(
            activity_instance_ar.item_metadata.status
            in [
                LibraryItemStatus.DRAFT,
                LibraryItemStatus.RETIRED,
            ],
            msg=f"There is no approved Activity Instance with UID '{activity_instance_uid}'.",
        )

        related_activity_instances = self._repos.activity_instance_repository.get_all_activity_instances_for_activity_grouping(
            activity_uid=study_activity_selection.activity_uid,
            activity_subgroup_uid=study_activity_selection.activity_subgroup_uid,
            activity_group_uid=study_activity_selection.activity_group_uid,
        )
        linked_activity_instances = []
        for activity_instance in related_activity_instances:
            if activity_instance.uid not in linked_activity_instances:
                linked_activity_instances.append(activity_instance.uid)
        exceptions.BusinessLogicException.raise_if(
            activity_instance_uid not in linked_activity_instances,
            msg=f"Activity Instance with Name '{activity_instance_ar.name}' isn't linked with the Activity with Name '{study_activity_selection.activity_name}'.",
        )

        return activity_instance_ar

    def _create_value_object(
        self,
        study_uid: str,
        selection_create_input: StudySelectionActivityInstanceCreateInput,
        **kwargs,
    ):
        _, study_activity_selection, _ = self._get_specific_activity_selection_by_uids(
            study_uid=study_uid,
            study_selection_uid=selection_create_input.study_activity_uid,
        )
        if selection_create_input.activity_instance_uid:
            activity_instance_ar = self.activity_instance_validation(
                activity_instance_uid=selection_create_input.activity_instance_uid,
                study_activity_selection=study_activity_selection,
            )
        else:
            activity_instance_ar = None

        # create new VO to add
        new_selection = StudySelectionActivityInstanceVO.from_input_values(
            study_uid=study_uid,
            author_id=self.author,
            activity_instance_uid=(
                activity_instance_ar.uid if activity_instance_ar else None
            ),
            activity_instance_version=(
                activity_instance_ar.item_metadata.version
                if activity_instance_ar
                else None
            ),
            study_activity_uid=selection_create_input.study_activity_uid,
            activity_uid=study_activity_selection.activity_uid,
            activity_subgroup_uid=study_activity_selection.activity_subgroup_uid,
            activity_group_uid=study_activity_selection.activity_group_uid,
            generate_uid_callback=self.repository.generate_uid,
        )
        return new_selection

    @db.transaction
    def make_selection(
        self,
        study_uid: str,
        selection_create_input: StudySelectionActivityInstanceCreateInput,
    ) -> StudySelectionActivityInstance:
        return self.non_transactional_make_selection(
            study_uid=study_uid, selection_create_input=selection_create_input
        )

    def non_transactional_make_selection(
        self,
        study_uid: str,
        selection_create_input: StudySelectionActivityInstanceCreateInput,
    ) -> StudySelectionActivityInstance:
        repos = self._repos
        try:
            # create new VO to add
            study_activity_instance_selection = self._create_value_object(
                study_uid=study_uid,
                selection_create_input=selection_create_input,
            )
            # add VO to aggregate
            study_activity_instance_aggregate = self.repository.find_by_study(
                study_uid=study_uid, for_update=True
            )
            assert study_activity_instance_aggregate is not None
            study_activity_instance_aggregate.add_object_selection(
                study_activity_instance_selection,
                self.selected_object_repository.check_exists_final_version,
                self._repos.ct_term_name_repository.term_specific_exists_by_uid,
            )
            study_activity_instance_aggregate.validate()
            # sync with DB and save the update
            self.repository.save(study_activity_instance_aggregate, self.author)

            study_activity_instance_aggregate = self.repository.find_by_study(
                study_uid=study_uid, for_update=True
            )
            # Fetch the new selection which was just added
            (
                specific_selection,
                _,
            ) = study_activity_instance_aggregate.get_specific_object_selection(
                study_activity_instance_selection.study_selection_uid
            )

            # add the activity and return
            return self._transform_from_vo_to_response_model(
                study_uid=study_activity_instance_aggregate.study_uid,
                specific_selection=specific_selection,
            )
        finally:
            repos.close()

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_activity_instance_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # remove the connection
            assert selection_aggregate is not None
            selection_aggregate.remove_object_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_activity_instance_repository.save(
                selection_aggregate, self.author
            )
        finally:
            repos.close()

    def _patch_prepare_new_value_object(
        self,
        request_object: StudySelectionActivityInstanceEditInput,
        current_object: StudySelectionActivityInstanceVO,
    ) -> StudySelectionActivityInstanceVO:
        # transform current to input model
        transformed_current = StudySelectionActivityInstanceEditInput(
            show_activity_instance_in_protocol_flowchart=current_object.show_activity_instance_in_protocol_flowchart,
            activity_instance_uid=current_object.activity_instance_uid,
            study_activity_uid=current_object.study_activity_uid,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_object,
            reference_base_model=transformed_current,
        )

        _, study_activity_selection, _ = self._get_specific_activity_selection_by_uids(
            study_uid=current_object.study_uid,
            study_selection_uid=current_object.study_activity_uid,
        )
        if request_object.activity_instance_uid:
            activity_instance_ar = self.activity_instance_validation(
                activity_instance_uid=request_object.activity_instance_uid,
                study_activity_selection=study_activity_selection,
            )
        else:
            activity_instance_ar = None

        return StudySelectionActivityInstanceVO.from_input_values(
            study_uid=current_object.study_uid,
            study_selection_uid=current_object.study_selection_uid,
            author_id=self.author,
            activity_instance_uid=(
                activity_instance_ar.uid if activity_instance_ar else None
            ),
            activity_instance_version=(
                activity_instance_ar.item_metadata.version
                if activity_instance_ar
                else None
            ),
            activity_uid=current_object.activity_uid,
            activity_subgroup_uid=current_object.activity_subgroup_uid,
            activity_group_uid=current_object.activity_group_uid,
            activity_version=current_object.activity_version,
            study_activity_uid=current_object.study_activity_uid,
            show_activity_instance_in_protocol_flowchart=request_object.show_activity_instance_in_protocol_flowchart,
        )

    def get_specific_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        study_value_version: str | None = None,
    ) -> StudySelectionActivityInstance:
        (
            _,
            specific_selection,
            _,
        ) = self._get_specific_activity_instance_selection_by_uids(
            study_uid, study_selection_uid, study_value_version=study_value_version
        )
        return self._transform_from_vo_to_response_model(
            study_uid=study_uid,
            specific_selection=specific_selection,
        )

    @db.transaction
    def update_selection_to_latest_version(
        self, study_uid: str, study_selection_uid: str
    ):
        (
            selection_ar,
            selection,
            _,
        ) = self._get_specific_activity_instance_selection_by_uids(
            study_uid=study_uid,
            study_selection_uid=study_selection_uid,
            for_update=True,
        )
        activity_instance_uid = selection.activity_instance_uid
        activity_instance_ar = self._repos.activity_instance_repository.find_by_uid_2(
            activity_instance_uid, for_update=True
        )
        if activity_instance_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            activity_instance_ar.approve(self.author)
            self._repos.activity_instance_repository.save(activity_instance_ar)
        elif activity_instance_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                msg="Cannot add retired activity instances as selection. Please reactivate."
            )
        new_selection: StudySelectionActivityInstanceVO = selection.update_version(
            activity_instance_version=activity_instance_ar.item_metadata.version
        )
        selection_ar.update_selection(new_selection)
        self._repos.study_activity_instance_repository.save(selection_ar, self.author)

        return self._transform_from_vo_to_response_model(
            study_uid=study_uid,
            specific_selection=new_selection,
        )

    @ensure_transaction(db)
    def batch_create(
        self,
        study_uid: str,
        create_payload: StudySelectionActivityInstanceBatchCreate,
    ) -> list[StudySelectionActivityInstanceBatchOutput]:
        results = []
        study_activity_instance_aggregate = self.repository.find_by_study(
            study_uid=study_uid, for_update=True
        )
        selected_instances = {
            study_activity_instance.activity_instance_uid: study_activity_instance.study_selection_uid
            for study_activity_instance in study_activity_instance_aggregate.study_objects_selection
        }

        for activity_instance_uid in create_payload.activity_instance_uids:
            result = {}
            try:
                if activity_instance_uid not in selected_instances:
                    item = self.non_transactional_make_selection(
                        study_uid=study_uid,
                        selection_create_input=StudySelectionActivityInstanceCreateInput(
                            activity_instance_uid=activity_instance_uid,
                            study_activity_uid=create_payload.study_activity_uid,
                        ),
                    )
                    response_code = status.HTTP_201_CREATED
                else:
                    item = self.get_specific_selection(
                        study_uid=study_uid,
                        study_selection_uid=selected_instances[activity_instance_uid],
                    )
                    response_code = status.HTTP_200_OK
                result["response_code"] = response_code
                if item:
                    result["content"] = item.model_dump()
                results.append(StudySelectionActivityInstanceBatchOutput(**result))
            except exceptions.MDRApiBaseException as error:
                results.append(
                    StudySelectionActivityInstanceBatchOutput.model_construct(
                        response_code=error.status_code,
                        content=BatchErrorResponse(message=str(error)),
                    )
                )
        return results
