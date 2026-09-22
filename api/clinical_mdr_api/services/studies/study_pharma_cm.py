from typing import Any

from clinical_mdr_api.models.study_selections.study_pharma_cm import (
    StudyPharmaCM,
    StudyPharmaCMXML,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.studies.study_criteria_selection import (
    StudyCriteriaSelectionService,
)
from clinical_mdr_api.services.studies.study_endpoint_selection import (
    StudyEndpointSelectionService,
)
from common import exceptions
from common.auth.user import user


class StudyPharmaCMService:
    _repos: MetaRepository

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    def get_pharma_cm_representation(
        self, study_uid: str, study_value_version: str | None
    ) -> StudyPharmaCM:
        study = self._repos.study_definition_repository.find_by_uid(
            uid=study_uid, study_value_version=study_value_version
        )
        if study is None:
            raise exceptions.NotFoundException("Study", study_uid)

        study_arms = self._repos.study_arm_repository.find_by_study(
            study_uid=study_uid, study_value_version=study_value_version
        )
        study_endpoint_service = StudyEndpointSelectionService()
        study_endpoints = study_endpoint_service.get_all_selection(
            study_uid=study_uid,
            study_value_version=study_value_version,
            no_brackets=True,
        )
        study_criteria_service = StudyCriteriaSelectionService()
        study_inclusion_criterias = study_criteria_service.get_all_selection(
            study_uid=study_uid,
            study_value_version=study_value_version,
            filter_by={
                "criteria_type.sponsor_preferred_name_sentence_case": {
                    "v": ["inclusion criteria"],
                    "op": "eq",
                },
                "key_criteria": {"v": [True], "op": "eq"},
            },
            no_brackets=True,
        )
        study_exclusion_criterias = study_criteria_service.get_all_selection(
            study_uid=study_uid,
            study_value_version=study_value_version,
            filter_by={
                "criteria_type.sponsor_preferred_name_sentence_case": {
                    "v": ["exclusion criteria"],
                    "op": "eq",
                },
                "key_criteria": {"v": [True], "op": "eq"},
            },
            no_brackets=True,
        )
        return StudyPharmaCM.from_various_data(
            study=study,
            study_arms=study_arms,
            study_endpoints=study_endpoints.items,
            inclusion_criterias=study_inclusion_criterias.items,
            exclusion_criterias=study_exclusion_criterias.items,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
            find_all_units=self._repos.unit_definition_repository.find_all,
        )

    def get_pharma_cm_xml(
        self, study_uid: str, study_value_version: str | None
    ) -> dict[str, Any]:
        study_pharma_cm: StudyPharmaCM = self.get_pharma_cm_representation(
            study_uid=study_uid, study_value_version=study_value_version
        )
        return StudyPharmaCMXML.from_pharma_cm_data(study_pharma_cm=study_pharma_cm)
