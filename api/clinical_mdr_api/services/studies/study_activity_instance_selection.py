import dataclasses
from collections import defaultdict
from datetime import datetime, timezone
from typing import Callable, Iterable

from fastapi import status
from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.activities.activity_instance_repository import (
    ActivityInstanceRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_instance_repository import (
    SelectionHistory,
    StudySelectionActivityInstanceRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity_instance import (
    ActivityInstanceAR,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity import (
    StudySelectionActivityVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_instance import (
    StudySelectionActivityInstanceAR,
    StudySelectionActivityInstanceVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.study_selections.study_selection import (
    StudySelectionActivityInstance,
    StudySelectionActivityInstanceBatchInput,
    StudySelectionActivityInstanceBatchOutput,
    StudySelectionActivityInstanceCreateInput,
    StudySelectionActivityInstanceEditInput,
    StudySelectionActivityInstanceReviewBatchInput,
    StudySelectionReviewAction,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    ensure_transaction,
    fill_missing_values_in_base_model_from_reference_base_model,
)
from clinical_mdr_api.services.studies.study_activity_selection_base import (
    StudyActivitySelectionBaseService,
)
from clinical_mdr_api.utils import db_result_to_list
from common import exceptions
from common.auth.user import user


class StudyActivityInstanceSelectionService(
    StudyActivitySelectionBaseService[
        StudySelectionActivityInstanceAR,
        StudySelectionActivityInstanceVO,
        StudySelectionActivityInstance,
    ]
):
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
    ):
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
    ) -> StudySelectionActivityInstance:
        return StudySelectionActivityInstance.from_study_selection_activity_instance_vo_and_order(
            study_uid=study_uid,
            study_selection=specific_selection,
        )

    # pylint: disable=unused-argument
    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionActivityInstanceAR | None,
        study_value_version: str | None = None,
        **kwargs,
    ) -> list[StudySelectionActivityInstance]:
        if study_selection is None:
            return []

        return [
            self._transform_from_vo_to_response_model(
                study_uid=specific_selection.study_uid,
                specific_selection=specific_selection,
            )
            for specific_selection in study_selection.study_objects_selection
        ]

    def _get_linked_activity_instances(
        self,
        selection_vos: Iterable[StudySelectionActivityInstanceVO],
    ) -> list[ActivityInstanceAR]:
        version_specific_uids = defaultdict(set)

        for selection_vo in selection_vos:
            if selection_vo.activity_instance_uid:
                version_specific_uids[selection_vo.activity_instance_uid].add(
                    selection_vo.activity_instance_version
                )
                version_specific_uids[selection_vo.activity_instance_uid].add("LATEST")

        if not version_specific_uids:
            return []

        return self._repos.activity_instance_repository.get_all_optimized(
            version_specific_uids=version_specific_uids
        )[0]

    def _transform_history_to_response_model(
        self, study_selection_history: list[SelectionHistory], study_uid: str
    ) -> list[StudySelectionActivityInstance]:
        result = []
        for history in study_selection_history:
            result.append(
                StudySelectionActivityInstance.from_study_selection_history(
                    study_selection_history=history,
                    study_uid=study_uid,
                )
            )
        return result

    def activity_instance_validation(
        self,
        activity_instance_uid: str,
        study_activity_selection: StudySelectionActivityVO,
        current_activity_instance_uid: str | None = None,
        current_activity_instance_version: str | None = None,
    ) -> ActivityInstanceAR:
        is_validation_needed: bool = True
        activity_instance_ar: ActivityInstanceAR
        # If ActivityInstance wasn't changed we should fetch it in the version it was selected by previous StudyActivityInstance
        if activity_instance_uid == current_activity_instance_uid:
            activity_instance_ar = (
                self._repos.activity_instance_repository.find_by_uid_2(
                    activity_instance_uid,
                    version=current_activity_instance_version,
                )
            )
            # If the previous version of ActivityInstance is selected we don't need to validate it
            is_validation_needed = False
        else:
            activity_instance_ar = (
                self._repos.activity_instance_repository.find_by_uid_2(
                    activity_instance_uid
                )
            )

        exceptions.NotFoundException.raise_if_not(
            activity_instance_ar, "Activity Instance", activity_instance_uid
        )

        exceptions.NotFoundException.raise_if(
            activity_instance_ar.item_metadata.status
            in [
                LibraryItemStatus.DRAFT,
                LibraryItemStatus.RETIRED,
            ]
            and is_validation_needed,
            msg=f"There is no approved Activity Instance with name '{activity_instance_ar.name}'.",
        )

        if (
            study_activity_selection.activity_subgroup_uid is None
            or study_activity_selection.activity_group_uid is None
        ):
            raise exceptions.BusinessLogicException(
                msg="Activity Subgroup UID and Activity Group UID must be provided for new selections."
            )

        related_activity_instances = self._repos.activity_instance_repository.get_all_activity_instances_for_activity_grouping(
            activity_uid=study_activity_selection.activity_uid,
            activity_subgroup_uid=study_activity_selection.activity_subgroup_uid,
            activity_group_uid=study_activity_selection.activity_group_uid,
        )
        linked_activity_instances = []
        for activity_instance_root, _ in related_activity_instances:
            if activity_instance_root.uid not in linked_activity_instances:
                linked_activity_instances.append(activity_instance_root.uid)
        exceptions.BusinessLogicException.raise_if(
            activity_instance_uid not in linked_activity_instances
            and is_validation_needed,
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
            study_activity_uid=selection_create_input.study_activity_uid,
            study_activity_instance_baseline_visits=[
                {
                    "uid": uid,
                }
                for uid in selection_create_input.baseline_visit_uids or []
            ],
            show_activity_instance_in_protocol_flowchart=selection_create_input.show_activity_instance_in_protocol_flowchart,
            is_important=selection_create_input.is_important,
            activity_instance_uid=(
                activity_instance_ar.uid if activity_instance_ar else None
            ),
            activity_instance_version=(
                activity_instance_ar.item_metadata.version
                if activity_instance_ar
                else None
            ),
            activity_uid=study_activity_selection.activity_uid,
            activity_subgroup_uid=study_activity_selection.activity_subgroup_uid,
            activity_group_uid=study_activity_selection.activity_group_uid,
            generate_uid_callback=self.repository.generate_uid,
            is_reviewed=activity_instance_ar.concept_vo.activity_instance_attributes.is_required_for_activity
            or selection_create_input.is_reviewed,
            study_data_supplier_uid=selection_create_input.study_data_supplier_uid,
            origin_type_uid=selection_create_input.origin_type_uid,
            origin_source_uid=selection_create_input.origin_source_uid,
        )
        return new_selection

    ensure_transaction(db)

    def make_selection(
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

    @ensure_transaction(db)
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            selection_aggregate = (
                repos.study_activity_instance_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            selection_to_delete, _ = selection_aggregate.get_specific_object_selection(
                study_selection_uid=study_selection_uid
            )
            other_selections_referencing_same_activity = [
                selection
                for selection in selection_aggregate.study_objects_selection
                if selection.activity_uid == selection_to_delete.activity_uid
                and selection.study_selection_uid != study_selection_uid
            ]

            if other_selections_referencing_same_activity:
                selection_aggregate.remove_object_selection(study_selection_uid)
            elif (
                not other_selections_referencing_same_activity
                and selection_to_delete.activity_instance_uid
            ):
                selection_aggregate.update_selection(
                    updated_study_object_selection=dataclasses.replace(
                        selection_to_delete,
                        activity_instance_uid=None,
                        is_reviewed=False,
                    ),
                    object_exist_callback=self._get_selected_object_exist_check(),
                    ct_term_level_exist_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                )
            else:
                exceptions.BusinessLogicException.raise_if(
                    True, msg="Activity cannot be deleted"
                )
            selection_aggregate.validate()
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
            keep_old_version=current_object.keep_old_version,
            is_reviewed=current_object.is_reviewed,
            is_important=current_object.is_important,
            baseline_visit_uids=request_object.baseline_visit_uids
            or [
                baseline_visit["uid"]
                for baseline_visit in current_object.study_activity_instance_baseline_visits
            ],
            study_data_supplier_uid=current_object.study_data_supplier_uid,
            origin_type_uid=current_object.origin_type_uid,
            origin_source_uid=current_object.origin_source_uid,
        )
        keep_old_version_date = None
        if request_object.keep_old_version is True:
            keep_old_version_date = datetime.now(timezone.utc)
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
                current_activity_instance_uid=current_object.activity_instance_uid,
                current_activity_instance_version=current_object.activity_instance_version,
            )
        else:
            activity_instance_ar = None

        return StudySelectionActivityInstanceVO.from_input_values(
            study_uid=current_object.study_uid,
            study_selection_uid=current_object.study_selection_uid,
            author_id=user().id(),
            author_username=user().username,
            study_activity_uid=current_object.study_activity_uid,
            study_activity_instance_baseline_visits=[
                {
                    "uid": uid,
                }
                for uid in request_object.baseline_visit_uids or []
            ],
            show_activity_instance_in_protocol_flowchart=request_object.show_activity_instance_in_protocol_flowchart,
            keep_old_version=request_object.keep_old_version,
            keep_old_version_date=keep_old_version_date,
            is_reviewed=request_object.is_reviewed,
            is_important=request_object.is_important,
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
            study_data_supplier_uid=request_object.study_data_supplier_uid,
            origin_type_uid=request_object.origin_type_uid,
            origin_source_uid=request_object.origin_source_uid,
        )

    @ensure_transaction(db)
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: StudySelectionActivityInstanceEditInput,
    ):
        super().patch_selection(
            study_uid=study_uid,
            study_selection_uid=study_selection_uid,
            selection_update_input=selection_update_input,
        )
        # Fetch the single updated VO directly (avoids loading the full aggregate).
        return self._get_specific_selection_vo_as_response(
            study_uid=study_uid,
            study_selection_uid=study_selection_uid,
        )

    def _get_specific_selection_vo_as_response(
        self,
        study_uid: str,
        study_selection_uid: str,
    ) -> StudySelectionActivityInstance:
        """Fetch a single fully-resolved VO and convert to response model."""
        vo = self._repos.study_activity_instance_repository.find_selection_vo_by_uid(
            study_uid=study_uid,
            study_selection_uid=study_selection_uid,
        )
        if vo is None:
            raise exceptions.NotFoundException(
                msg=f"Study activity instance selection with UID '{study_selection_uid}' not found."
            )
        return self._transform_from_vo_to_response_model(
            study_uid=study_uid,
            specific_selection=vo,
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

    @ensure_transaction(db)
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

        # When we sync to latest version it means we clear keep_old_version flag and set is_reviewed flag
        # as user explicitly decided to update to latest version which also reviews given Study activity instance
        new_selection = new_selection.update_keep_old_version_and_is_reviewed(
            keep_old_version=False, is_reviewed=True, keep_old_version_date=None
        )

        selection_ar.update_selection(new_selection)
        self._repos.study_activity_instance_repository.save(selection_ar, self.author)

        return self._transform_from_vo_to_response_model(
            study_uid=study_uid,
            specific_selection=new_selection,
        )

    @ensure_transaction(db)
    def handle_batch_operations(
        self,
        study_uid: str,
        operations: list[StudySelectionActivityInstanceBatchInput],
    ) -> list[StudySelectionActivityInstanceBatchOutput]:
        results = []
        for operation in operations:
            item = None
            try:
                if operation.method == "PATCH":
                    item = self.patch_selection(
                        study_uid=study_uid,
                        study_selection_uid=operation.content.study_activity_instance_uid,
                        selection_update_input=StudySelectionActivityInstanceEditInput(
                            activity_instance_uid=operation.content.activity_instance_uid,
                            study_activity_uid=operation.content.study_activity_uid,
                            is_reviewed=operation.content.is_reviewed,
                            is_important=operation.content.is_important,
                            baseline_visit_uids=operation.content.baseline_visit_uids,
                            study_data_supplier_uid=operation.content.study_data_supplier_uid,
                            origin_type_uid=operation.content.origin_type_uid,
                            origin_source_uid=operation.content.origin_source_uid,
                        ),
                    )
                    response_code = status.HTTP_200_OK
                elif operation.method == "POST":
                    item = self.make_selection(
                        study_uid=study_uid,
                        selection_create_input=StudySelectionActivityInstanceCreateInput(
                            activity_instance_uid=operation.content.activity_instance_uid,
                            study_activity_uid=operation.content.study_activity_uid,
                            is_reviewed=operation.content.is_reviewed,
                            is_important=operation.content.is_important,
                            baseline_visit_uids=operation.content.baseline_visit_uids,
                            study_data_supplier_uid=operation.content.study_data_supplier_uid,
                            origin_type_uid=operation.content.origin_type_uid,
                            origin_source_uid=operation.content.origin_source_uid,
                        ),
                    )
                    response_code = status.HTTP_201_CREATED
                else:
                    raise exceptions.MethodNotAllowedException(method=operation.method)
                results.append(
                    StudySelectionActivityInstanceBatchOutput(
                        response_code=response_code,
                        content=item,
                    )
                )
            except exceptions.MDRApiBaseException as error:
                results.append(
                    StudySelectionActivityInstanceBatchOutput.model_construct(
                        response_code=error.status_code,
                        content=BatchErrorResponse(message=str(error)),
                    )
                )
                raise error
        return results

    @ensure_transaction(db)
    def handle_review_changes(
        self,
        study_uid: str,
        operations: list[StudySelectionActivityInstanceReviewBatchInput],
    ) -> list[StudySelectionActivityInstanceBatchOutput]:
        results = []
        for operation in operations:
            item = None
            try:
                if operation.action == StudySelectionReviewAction.ACCEPT:
                    item = self.update_selection_to_latest_version(
                        study_uid=study_uid,
                        study_selection_uid=operation.uid,
                    )
                    response_code = status.HTTP_200_OK
                elif operation.action == StudySelectionReviewAction.DECLINE:
                    exceptions.ValidationException.raise_if(
                        not isinstance(
                            operation.content, StudySelectionActivityInstanceEditInput
                        ),
                        msg="Decline action requires StudySelectionActivityInstanceEditInput as request payload.",
                    )
                    self.patch_selection(
                        study_uid=study_uid,
                        study_selection_uid=operation.uid,
                        selection_update_input=StudySelectionActivityInstanceEditInput(
                            keep_old_version=operation.content.keep_old_version,
                            is_reviewed=True,
                        ),
                    )
                    response_code = status.HTTP_204_NO_CONTENT
                else:
                    raise exceptions.MethodNotAllowedException(
                        method=operation.action.value
                    )
                results.append(
                    StudySelectionActivityInstanceBatchOutput(
                        response_code=response_code,
                        content=item,
                    )
                )
            except exceptions.MDRApiBaseException as error:
                results.append(
                    StudySelectionActivityInstanceBatchOutput.model_construct(
                        response_code=error.status_code,
                        content=BatchErrorResponse(message=str(error)),
                    )
                )
        return results

    def get_crfs(self, study_uid: str):
        query = """
        MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(:StudyValue)
            -[:HAS_STUDY_ACTIVITY_INSTANCE]->(:StudyActivityInstance)
            -[:HAS_SELECTED_ACTIVITY_INSTANCE]->(:ActivityInstanceValue)
            -[:CONTAINS_ACTIVITY_ITEM]->(:ActivityItem)
            <-[:LINKS_TO_ACTIVITY_ITEM]-(oiv:OdmItemValue)
            <-[:ITEM_REF]-(oigv:OdmItemGroupValue)
            <-[:ITEM_GROUP_REF]-(ofv:OdmFormValue)
            <-[hv:HAS_VERSION]-(ofr:OdmFormRoot)
        
        WITH ofr, ofv, hv ORDER BY hv.end_date DESC
        
        WITH ofr, COLLECT({ofv: ofv, hv: hv})[0] AS latest
        
        RETURN DISTINCT
            ofr.uid AS uid,
            latest.ofv.name AS name,
            latest.hv.version AS version
        """

        results = db.cypher_query(query, params={"study_uid": study_uid})

        return db_result_to_list(results)
