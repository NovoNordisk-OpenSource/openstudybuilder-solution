from datetime import datetime
from typing import Any

from clinical_mdr_api.domain_repositories.study_selections.study_soa_group_repository import (
    StudySoAGroupRepository,
)
from clinical_mdr_api.domains.study_selections.study_soa_group_selection import (
    StudySoAGroupAR,
    StudySoAGroupVO,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudySoAGroup,
    StudySoAGroupEditInput,
)
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.studies.study_activity_selection_base import (
    StudyActivitySelectionBaseService,
    _VOType,
)
from common.exceptions import BusinessLogicException, ValidationException


class StudySoAGroupService(StudyActivitySelectionBaseService):
    _repos: MetaRepository
    repository_interface = StudySoAGroupRepository
    selected_object_repository_interface = None

    def _create_value_object(
        self,
        study_uid: str,
        selection_create_input: BaseModel,
        **kwargs,
    ):
        pass

    def _get_selected_object_exist_check(self):
        return True

    def _transform_all_to_response_model(
        self,
        study_selection: StudySoAGroupAR,
        study_value_version: str | None = None,
    ) -> list[StudySoAGroup]:
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
        return StudySoAGroup.from_study_selection_activity_vo(
            study_uid=study_uid,
            specific_selection=specific_selection,
        )

    def _transform_history_to_response_model(
        self, study_selection_history: list[Any], study_uid: str
    ) -> list[BaseModel]:
        pass

    def _filter_ars_from_same_parent(
        self,
        selection_aggregate: StudySoAGroupAR,
        selection_vo: StudySoAGroupVO,
    ) -> StudySoAGroupAR:
        return selection_aggregate

    def _find_ar_and_validate_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> StudySoAGroupAR:
        study_soa_group_to_reorder: StudySoAGroupVO
        selection_aggregate, study_soa_group_to_reorder = self._find_ar_to_patch(
            study_uid=study_uid, study_selection_uid=study_selection_uid
        )

        BusinessLogicException.raise_if(
            new_order == study_soa_group_to_reorder.order,
            msg=f"The order ({new_order}) for study soa group {study_soa_group_to_reorder.soa_group_term_name} was not changed",
        )

        soa_group_size = len(selection_aggregate.study_objects_selection)

        BusinessLogicException.raise_if(
            new_order > soa_group_size,
            msg=f"The maximum new order is ({soa_group_size}) as there are {soa_group_size} StudySoAGroups and order ({new_order}) was requested",
        )

        return selection_aggregate

    def update_dependent_objects(
        self,
        study_selection: StudySoAGroupVO,
        previous_study_selection: StudySoAGroupVO,
    ):
        pass

    def _patch_prepare_new_value_object(
        self,
        request_object: StudySoAGroupEditInput,
        current_object: StudySoAGroupVO,
    ) -> StudySoAGroupVO:
        ValidationException.raise_if(
            request_object.show_soa_group_in_protocol_flowchart
            == current_object.show_soa_group_in_protocol_flowchart,
            msg=f"The StudySoAGroup is already set to be "
            f"{'visible' if request_object.show_soa_group_in_protocol_flowchart else 'not visible'}' in the protocol flowchart",
        )

        return StudySoAGroupVO.from_input_values(
            study_uid=current_object.study_uid,
            soa_group_term_uid=current_object.soa_group_term_uid,
            study_selection_uid=current_object.study_selection_uid,
            show_soa_group_in_protocol_flowchart=request_object.show_soa_group_in_protocol_flowchart,
            author_id=self.author,
            order=current_object.order,
        )
