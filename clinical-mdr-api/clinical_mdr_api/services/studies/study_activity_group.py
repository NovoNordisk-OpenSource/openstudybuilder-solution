from datetime import datetime
from typing import Any

from clinical_mdr_api.domain_repositories.concepts.activities.activity_group_repository import (
    ActivityGroupRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_group_repository import (
    StudySelectionActivityGroupRepository,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_group import (
    StudySelectionActivityGroupAR,
    StudySelectionActivityGroupVO,
)
from clinical_mdr_api.domains.study_selections.study_soa_group_selection import (
    StudySoAGroupVO,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyActivityGroup,
    StudyActivityGroupEditInput,
)
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.studies.study_activity_selection_base import (
    StudyActivitySelectionBaseService,
    _VOType,
)
from common.exceptions import BusinessLogicException, ValidationException


class StudyActivityGroupService(StudyActivitySelectionBaseService):
    _repos: MetaRepository
    repository_interface = StudySelectionActivityGroupRepository
    selected_object_repository_interface = ActivityGroupRepository

    def _create_value_object(
        self,
        study_uid: str,
        selection_create_input: BaseModel,
        **kwargs,
    ):
        pass

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionActivityGroupAR,
        study_value_version: str | None = None,
    ) -> list[StudyActivityGroup]:
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
        return StudyActivityGroup.from_study_selection_activity_vo(
            study_uid=study_uid, specific_selection=specific_selection
        )

    def _transform_history_to_response_model(
        self, study_selection_history: list[Any], study_uid: str
    ) -> list[BaseModel]:
        pass

    def _filter_ars_from_same_parent(
        self,
        selection_aggregate: StudySelectionActivityGroupAR,
        selection_vo: StudySelectionActivityGroupVO,
    ) -> StudySelectionActivityGroupAR:
        all_selections_from_same_parent = [
            selection
            for selection in selection_aggregate.study_objects_selection
            if selection.study_soa_group_uid == selection_vo.study_soa_group_uid
        ]
        selection_ar_from_same_parent = (
            StudySelectionActivityGroupAR.from_repository_values(
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
    ) -> StudySelectionActivityGroupAR:
        study_activity_group_to_reorder: StudySelectionActivityGroupVO
        selection_aggregate, study_activity_group_to_reorder = self._find_ar_to_patch(
            study_uid=study_uid, study_selection_uid=study_selection_uid
        )

        BusinessLogicException.raise_if(
            new_order == study_activity_group_to_reorder.order,
            msg=f"The order ({new_order}) for study activity group {study_activity_group_to_reorder.activity_group_name} was not changed",
        )
        study_soa_group: StudySoAGroupVO
        _, study_soa_group, _ = self._get_specific_soa_group_selection_by_uids(
            study_uid=study_uid,
            study_selection_uid=study_activity_group_to_reorder.study_soa_group_uid,
        )

        soa_group_size = len(study_soa_group.study_activity_group_uids)
        soa_group_name = study_soa_group.soa_group_term_name
        BusinessLogicException.raise_if(
            new_order > soa_group_size,
            msg=f"""The maximum new order is ({soa_group_size}) as there are {soa_group_size} StudyActivityGroups in {soa_group_name} soa group and order ({new_order}) was requested""",
        )

        return selection_aggregate

    def update_dependent_objects(
        self,
        study_selection: StudySelectionActivityGroupVO,
        previous_study_selection: StudySelectionActivityGroupVO,
    ):
        pass

    def _patch_prepare_new_value_object(
        self,
        request_object: StudyActivityGroupEditInput,
        current_object: StudySelectionActivityGroupVO,
    ) -> StudySelectionActivityGroupVO:
        ValidationException.raise_if(
            request_object.show_activity_group_in_protocol_flowchart
            == current_object.show_activity_group_in_protocol_flowchart,
            msg=f"The StudyActivityGroup is already set to be "
            f"{'visible' if request_object.show_activity_group_in_protocol_flowchart else 'not visible'}' in the protocol flowchart",
        )

        return StudySelectionActivityGroupVO.from_input_values(
            study_uid=current_object.study_uid,
            activity_group_uid=current_object.activity_group_uid,
            activity_group_version=current_object.activity_group_version,
            study_selection_uid=current_object.study_selection_uid,
            show_activity_group_in_protocol_flowchart=request_object.show_activity_group_in_protocol_flowchart,
            author_id=self.author,
            order=current_object.order,
        )
