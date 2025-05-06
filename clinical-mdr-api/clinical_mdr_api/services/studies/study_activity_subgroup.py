from datetime import datetime
from typing import Any

from clinical_mdr_api.domain_repositories.concepts.activities.activity_sub_group_repository import (
    ActivitySubGroupRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_subgroup_repository import (
    StudySelectionActivitySubGroupRepository,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_group import (
    StudySelectionActivityGroupVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_subgroup import (
    StudySelectionActivitySubGroupAR,
    StudySelectionActivitySubGroupVO,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyActivitySubGroup,
    StudyActivitySubGroupEditInput,
)
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.studies.study_activity_selection_base import (
    StudyActivitySelectionBaseService,
    _VOType,
)
from common.exceptions import BusinessLogicException


class StudyActivitySubGroupService(StudyActivitySelectionBaseService):
    _repos: MetaRepository
    repository_interface = StudySelectionActivitySubGroupRepository
    selected_object_repository_interface = ActivitySubGroupRepository

    def _create_value_object(
        self,
        study_uid: str,
        selection_create_input: BaseModel,
        **kwargs,
    ):
        pass

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionActivitySubGroupAR,
        study_value_version: str | None = None,
    ) -> list[StudyActivitySubGroup]:
        result = []
        for selection in study_selection.study_objects_selection:
            result.append(
                self._transform_from_vo_to_response_model(
                    study_uid=study_selection.study_uid,
                    specific_selection=selection,
                )
            )
        return result

    def _transform_from_vo_to_response_model(
        self,
        study_uid: str,
        specific_selection: _VOType,
        terms_at_specific_datetime: datetime | None = None,
        accepted_version: bool | None = None,
    ) -> BaseModel:
        return StudyActivitySubGroup.from_study_selection_activity_vo(
            study_uid=study_uid, specific_selection=specific_selection
        )

    def _transform_history_to_response_model(
        self, study_selection_history: list[Any], study_uid: str
    ) -> list[BaseModel]:
        pass

    def _filter_ars_from_same_parent(
        self,
        selection_aggregate: StudySelectionActivitySubGroupAR,
        selection_vo: StudySelectionActivitySubGroupVO,
    ) -> StudySelectionActivitySubGroupAR:
        all_selections_from_same_parent = [
            selection
            for selection in selection_aggregate.study_objects_selection
            if selection.study_activity_group_uid
            == selection_vo.study_activity_group_uid
        ]
        selection_ar_from_same_parent = (
            StudySelectionActivitySubGroupAR.from_repository_values(
                study_uid=selection_aggregate.study_uid,
                study_objects_selection=all_selections_from_same_parent,
            )
        )
        selection_ar_from_same_parent.repository_closure_data = (
            all_selections_from_same_parent
        )
        return selection_ar_from_same_parent

    def _find_ar_and_validate_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> StudySelectionActivitySubGroupAR:
        selection_aggregate, study_activity_subgroup_to_reorder = (
            self._find_ar_to_patch(
                study_uid=study_uid, study_selection_uid=study_selection_uid
            )
        )

        BusinessLogicException.raise_if(
            new_order == study_activity_subgroup_to_reorder.order,
            msg=f"The order ({new_order}) for study activity subgroup {study_activity_subgroup_to_reorder.activity_subgroup_name} was not changed",
        )
        study_activity_group: StudySelectionActivityGroupVO
        _, study_activity_group, _ = (
            self._get_specific_activity_group_selection_by_uids(
                study_uid=study_uid,
                study_selection_uid=study_activity_subgroup_to_reorder.study_activity_group_uid,
            )
        )

        group_size = len(study_activity_group.study_activity_subgroup_uids)
        group_name = study_activity_group.activity_group_name
        BusinessLogicException.raise_if(
            new_order > group_size,
            msg=f"The maximum new order is ({group_size}) as there are {group_size} StudyActivitySubGroups in {group_name} group and order ({new_order}) was requested",
        )

        return selection_aggregate

    def update_dependent_objects(
        self,
        study_selection: StudySelectionActivitySubGroupVO,
        previous_study_selection: StudySelectionActivitySubGroupVO,
    ):
        pass

    def _patch_prepare_new_value_object(
        self,
        request_object: StudyActivitySubGroupEditInput,
        current_object: StudySelectionActivitySubGroupVO,
    ) -> StudySelectionActivitySubGroupVO:
        BusinessLogicException.raise_if(
            request_object.show_activity_subgroup_in_protocol_flowchart
            == current_object.show_activity_subgroup_in_protocol_flowchart,
            msg=f"The StudyActivitySubGroup is already set to be "
            f"{'visible' if request_object.show_activity_subgroup_in_protocol_flowchart else 'not visible'}' in the protocol flowchart",
        )

        return StudySelectionActivitySubGroupVO.from_input_values(
            study_uid=current_object.study_uid,
            activity_subgroup_uid=current_object.activity_subgroup_uid,
            activity_subgroup_version=current_object.activity_subgroup_version,
            study_selection_uid=current_object.study_selection_uid,
            show_activity_subgroup_in_protocol_flowchart=request_object.show_activity_subgroup_in_protocol_flowchart,
            author_id=self.author,
            order=current_object.order,
        )
