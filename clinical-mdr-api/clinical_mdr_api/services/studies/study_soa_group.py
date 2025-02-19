from copy import copy
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
from common.exceptions import ValidationException


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
        order: int | None = None,
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

    def update_dependent_objects(
        self,
        study_selection: StudySoAGroupVO,
        previous_study_selection: StudySoAGroupVO,
    ):
        study_activities = self._repos.study_activity_repository.get_all_study_activities_for_study_soa_group(
            study_soa_group_uid=study_selection.study_selection_uid
        )
        study_activity_aggregate = self._repos.study_activity_repository.find_by_study(
            study_selection.study_uid,
            for_update=True,
        )
        assert study_activity_aggregate is not None

        for study_activity in study_activities:
            selection, _ = study_activity_aggregate.get_specific_object_selection(
                study_activity.uid
            )
            updated_selection = copy(selection)
            study_activity_aggregate.update_selection(
                updated_study_object_selection=updated_selection,
                object_exist_callback=self._repos.activity_repository.final_or_replaced_retired_activity_exists,
                ct_term_level_exist_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
            )
        # sync with DB and save the update
        self._repos.study_activity_repository.save(
            study_activity_aggregate, self.author
        )

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
        )
