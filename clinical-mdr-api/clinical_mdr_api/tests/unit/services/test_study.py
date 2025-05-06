import random
import sys
import unittest
from dataclasses import dataclass
from typing import Iterable
from unittest.mock import PropertyMock, patch

from clinical_mdr_api.domain_repositories.controlled_terminologies import (
    ct_term_generic_repository,
)
from clinical_mdr_api.domains.study_definition_aggregates import study_configuration
from clinical_mdr_api.domains.study_definition_aggregates.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domains.study_definition_aggregates.root import StudyDefinitionAR
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    HighLevelStudyDesignVO,
    StudyComponentEnum,
    StudyIdentificationMetadataVO,
    StudyStatus,
)
from clinical_mdr_api.models.study_selections.study import (
    DurationJsonModel,
    HighLevelStudyDesignJsonModel,
    RegistryIdentifiersJsonModel,
    StudyCreateInput,
    StudyDescriptionJsonModel,
    StudyIdentificationMetadataJsonModel,
    StudyInterventionJsonModel,
    StudyMetadataJsonModel,
    StudyPatchRequestJsonModel,
    StudyPopulationJsonModel,
    StudyPreferredTimeUnit,
)
from clinical_mdr_api.models.utils import from_duration_object_to_value_and_unit
from clinical_mdr_api.services._utils import create_duration_object_from_api_input
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.tests.unit.domain.clinical_programme_aggregate.test_clinical_programme import (
    create_random_clinical_programme,
)
from clinical_mdr_api.tests.unit.domain.controlled_terminology_aggregates.test_ct_term_names import (
    create_random_ct_term_name_ar,
    create_random_ct_term_name_ars,
)
from clinical_mdr_api.tests.unit.domain.project_aggregate.test_project import (
    create_random_project,
)
from clinical_mdr_api.tests.unit.domain.study_definition_aggregate.test_root import (
    create_random_study,
)
from clinical_mdr_api.tests.unit.domain.utils import random_str
from clinical_mdr_api.tests.unit.domain_repositories.test_study_definition_repository_base import (
    StudyDefinitionRepositoryFake,
    StudyDefinitionsDBFake,
)
from clinical_mdr_api.tests.unit.services.test_study_description import (
    StudyTitleRepositoryForTestImpl,
)
from common.config import DEFAULT_STUDY_FIELD_CONFIG_FILE


class UnitDefinitionRepositoryForTestImpl:
    @dataclass(frozen=True)
    class UnitDefinition:
        uid: str
        name: str
        definition: str

    _repo_content = frozenset(
        {
            UnitDefinition("UnitDefinition_000001", "Day", "def1"),
            UnitDefinition("UnitDefinition_000002", "Days", "def2"),
            UnitDefinition("UnitDefinition_000003", "Hour", "def3"),
            UnitDefinition("UnitDefinition_000004", "Hours", "def4"),
            UnitDefinition("UnitDefinition_000005", "Month", "def5"),
            UnitDefinition("UnitDefinition_000006", "Months", "def6"),
            UnitDefinition("UnitDefinition_000007", "Week", "def7"),
            UnitDefinition("UnitDefinition_000008", "Weeks", "def8"),
            UnitDefinition("UnitDefinition_000009", "Year", "def9"),
            UnitDefinition("UnitDefinition_000010", "Years", "def10"),
        }
    )

    def find_by_uid_2(self, code: str) -> UnitDefinition | None:
        results = [_ for _ in self._repo_content if _.uid == code]
        return None if len(results) == 0 else results[0]

    def find_all(self) -> Iterable[UnitDefinition]:
        return self._repo_content, len(self._repo_content)

    def term_exists(self, code: str) -> bool:
        for age_unit in self._repo_content:
            if age_unit.uid == code:
                return True
        return False


class TestStudyService(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.patcher = patch(
            target=study_configuration.__name__ + ".from_database",
            new=lambda: study_configuration.from_file(DEFAULT_STUDY_FIELD_CONFIG_FILE),
        )
        cls.patcher.start()

    @classmethod
    def tear_down_class(cls) -> None:
        cls.patcher.stop()

    @staticmethod
    def get_field_or_simple_term_uid(field):
        return field if field is None else field.term_uid

    @staticmethod
    def get_field_or_unit_def_uid(field):
        return field if field is None else field.uid

    @patch(StudyService.__module__ + ".MetaRepository.unit_definition_repository")
    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    @patch(StudyService.__module__ + ".MetaRepository.ct_term_name_repository")
    def test__get_by_uid__plus_study_population__result(
        self,
        ct_term_name_repository_property_mock: PropertyMock,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
        unit_definition_repository_property_mock: PropertyMock,
    ):
        unit_definition_test_repo = UnitDefinitionRepositoryForTestImpl()
        ct_term_name_repository_property_mock.find_by_uid.return_value = (
            create_random_ct_term_name_ar()
        )
        ct_term_name_repository_property_mock.find_by_uids.side_effect = (
            lambda term_uids, at_specific_date: (
                create_random_ct_term_name_ars(term_uids=term_uids)
            )
        )
        # Change the __module__ attribute to simulate the module change
        ct_term_name_repository_property_mock.find_by_uids.__module__ = (
            ct_term_generic_repository.__name__
        )
        unit_definition_repository_property_mock.find_all.return_value = (
            unit_definition_test_repo.find_all()
        )
        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint: disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint: disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )

        for _ in range(0, 100):
            with self.subTest():
                # given
                test_db = StudyDefinitionsDBFake()

                prepare_repo = StudyDefinitionRepositoryFake(test_db)
                sample_study_definition = create_random_study(
                    generate_uid_callback=prepare_repo.generate_uid
                )
                prepare_repo.save(sample_study_definition)
                prepare_repo.close()

                test_repo = StudyDefinitionRepositoryFake(test_db)
                study_definition_repository_property_mock.return_value = test_repo

                # when
                study_service = StudyService()
                service_response = study_service.get_by_uid(
                    uid=sample_study_definition.uid,
                    include_sections=[StudyComponentEnum.STUDY_POPULATION],
                )

                # then
                # correct values of high level study design
                _ref_study_population = (
                    sample_study_definition.current_metadata.study_population
                )
                _res_study_population = (
                    service_response.current_metadata.study_population
                )

                self.assertEqual(
                    list(_ref_study_population.therapeutic_area_codes),
                    [
                        self.get_field_or_simple_term_uid(therapeutic_area_code)
                        for therapeutic_area_code in _res_study_population.therapeutic_area_codes
                    ],
                )
                self.assertEqual(
                    _ref_study_population.therapeutic_area_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.therapeutic_area_null_value_code
                    ),
                )
                self.assertEqual(
                    list(_ref_study_population.disease_condition_or_indication_codes),
                    [
                        self.get_field_or_simple_term_uid(disease_or_indication_code)
                        for disease_or_indication_code in _res_study_population.disease_condition_or_indication_codes
                    ],
                )
                self.assertEqual(
                    _ref_study_population.disease_condition_or_indication_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.disease_condition_or_indication_null_value_code
                    ),
                )
                self.assertEqual(
                    list(_ref_study_population.diagnosis_group_codes),
                    [
                        self.get_field_or_simple_term_uid(diagnosis_group_code)
                        for diagnosis_group_code in _res_study_population.diagnosis_group_codes
                    ],
                )
                self.assertEqual(
                    _ref_study_population.diagnosis_group_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.diagnosis_group_null_value_code
                    ),
                )
                self.assertEqual(
                    _ref_study_population.sex_of_participants_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.sex_of_participants_code
                    ),
                )
                self.assertEqual(
                    _ref_study_population.sex_of_participants_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.sex_of_participants_null_value_code
                    ),
                )
                self.assertEqual(
                    _ref_study_population.rare_disease_indicator,
                    _res_study_population.rare_disease_indicator,
                )
                self.assertEqual(
                    _ref_study_population.rare_disease_indicator_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.rare_disease_indicator_null_value_code
                    ),
                )
                self.assertEqual(
                    _ref_study_population.healthy_subject_indicator,
                    _res_study_population.healthy_subject_indicator,
                )
                self.assertEqual(
                    _ref_study_population.healthy_subject_indicator_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.healthy_subject_indicator_null_value_code
                    ),
                )
                self.assertEqual(
                    _ref_study_population.planned_minimum_age_of_subjects_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.planned_minimum_age_of_subjects_null_value_code
                    ),
                )
                self.assertEqual(
                    _ref_study_population.planned_maximum_age_of_subjects_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.planned_maximum_age_of_subjects_null_value_code
                    ),
                )
                self.assertEqual(
                    _ref_study_population.pediatric_study_indicator,
                    _res_study_population.pediatric_study_indicator,
                )
                self.assertEqual(
                    _ref_study_population.pediatric_study_indicator_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.pediatric_study_indicator_null_value_code
                    ),
                )
                self.assertEqual(
                    _ref_study_population.pediatric_postmarket_study_indicator,
                    _res_study_population.pediatric_postmarket_study_indicator,
                )
                self.assertEqual(
                    _ref_study_population.pediatric_postmarket_study_indicator_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.pediatric_postmarket_study_indicator_null_value_code
                    ),
                )
                self.assertEqual(
                    _ref_study_population.pediatric_investigation_plan_indicator,
                    _res_study_population.pediatric_investigation_plan_indicator,
                )
                self.assertEqual(
                    _ref_study_population.pediatric_investigation_plan_indicator_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.pediatric_investigation_plan_indicator_null_value_code
                    ),
                )
                self.assertEqual(
                    _ref_study_population.number_of_expected_subjects_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.number_of_expected_subjects_null_value_code
                    ),
                )

                if _ref_study_population.planned_minimum_age_of_subjects is None:
                    self.assertIsNone(
                        _res_study_population.planned_minimum_age_of_subjects
                    )
                else:
                    self.assertIsNotNone(
                        _res_study_population.planned_minimum_age_of_subjects
                    )
                    value, unit = from_duration_object_to_value_and_unit(
                        _ref_study_population.planned_minimum_age_of_subjects,
                        unit_definition_repository_property_mock.find_all,
                    )
                    print("unit", unit)
                    print(
                        "durationunitcode",
                        _res_study_population.planned_minimum_age_of_subjects.duration_unit_code,
                    )
                    self.assertEqual(
                        value,
                        _res_study_population.planned_minimum_age_of_subjects.duration_value,
                    )
                    self.assertEqual(
                        unit.uid,
                        self.get_field_or_unit_def_uid(
                            _res_study_population.planned_minimum_age_of_subjects.duration_unit_code
                        ),
                    )

                if _ref_study_population.planned_maximum_age_of_subjects is None:
                    self.assertIsNone(
                        _res_study_population.planned_maximum_age_of_subjects
                    )
                else:
                    self.assertIsNotNone(
                        _res_study_population.planned_maximum_age_of_subjects
                    )
                    value, unit = from_duration_object_to_value_and_unit(
                        _ref_study_population.planned_maximum_age_of_subjects,
                        unit_definition_repository_property_mock.find_all,
                    )
                    print("ref_study_population", _ref_study_population)
                    print("unit", unit)
                    print(
                        "durationunitcode",
                        _res_study_population.planned_maximum_age_of_subjects.duration_unit_code,
                    )
                    self.assertEqual(
                        value,
                        _res_study_population.planned_maximum_age_of_subjects.duration_value,
                    )
                    self.assertEqual(
                        unit.uid,
                        self.get_field_or_unit_def_uid(
                            _res_study_population.planned_maximum_age_of_subjects.duration_unit_code
                        ),
                    )

    @patch(StudyService.__module__ + ".MetaRepository.ct_term_name_repository")
    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__get_by_uid__minus_identification_plus_high_level_study_design__result(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
        ct_term_name_repository_property_mock: PropertyMock,
    ):
        # given
        test_db = StudyDefinitionsDBFake()

        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = create_random_study(
            generate_uid_callback=prepare_repo.generate_uid
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()

        test_repo = StudyDefinitionRepositoryFake(test_db)
        study_definition_repository_property_mock.return_value = test_repo

        # when
        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint: disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint: disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )
        ct_term_name_repository_property_mock.find_by_uid.return_value = (
            create_random_ct_term_name_ar()
        )
        ct_term_name_repository_property_mock.find_by_uids.side_effect = (
            lambda term_uids, at_specific_date: (
                create_random_ct_term_name_ars(term_uids=term_uids)
            )
        )
        # Change the __module__ attribute to simulate the module change
        ct_term_name_repository_property_mock.find_by_uids.__module__ = (
            ct_term_generic_repository.__name__
        )
        study_service = StudyService()
        service_response = study_service.get_by_uid(
            uid=sample_study_definition.uid,
            include_sections=[StudyComponentEnum.STUDY_DESIGN],
            exclude_sections=[StudyComponentEnum.IDENTIFICATION_METADATA],
        )

        # then

        # no id metadata in response
        self.assertIsNone(service_response.current_metadata.identification_metadata)
        self.assertNotIn(
            "identification_metadata",
            service_response.current_metadata.model_fields_set,
        )

        # correct values of ver metadata
        self.assertEqual(
            sample_study_definition.current_metadata.ver_metadata.study_status.value,
            service_response.current_metadata.version_metadata.study_status,
        )
        self.assertEqual(
            sample_study_definition.current_metadata.ver_metadata.version_number,
            service_response.current_metadata.version_metadata.version_number,
        )
        self.assertEqual(
            sample_study_definition.current_metadata.ver_metadata.version_description,
            service_response.current_metadata.version_metadata.version_description,
        )
        self.assertEqual(
            sample_study_definition.current_metadata.ver_metadata.version_author,
            service_response.current_metadata.version_metadata.version_author,
        )
        self.assertEqual(
            sample_study_definition.current_metadata.ver_metadata.version_timestamp,
            service_response.current_metadata.version_metadata.version_timestamp,
        )

        # correct values of high level study design
        _ref_high_level_study_design = (
            sample_study_definition.current_metadata.high_level_study_design
        )
        _res_high_level_study_design = (
            service_response.current_metadata.high_level_study_design
        )

        self.assertEqual(
            self.get_field_or_simple_term_uid(
                _res_high_level_study_design.study_type_null_value_code
            ),
            _ref_high_level_study_design.study_type_null_value_code,
        )
        self.assertEqual(
            self.get_field_or_simple_term_uid(
                _res_high_level_study_design.study_type_code
            ),
            _ref_high_level_study_design.study_type_code,
        )
        self.assertEqual(
            self.get_field_or_simple_term_uid(
                _res_high_level_study_design.is_extension_trial_null_value_code
            ),
            _ref_high_level_study_design.is_extension_trial_null_value_code,
        )
        self.assertEqual(
            _res_high_level_study_design.is_extension_trial,
            _ref_high_level_study_design.is_extension_trial,
        )
        self.assertEqual(
            _res_high_level_study_design.is_adaptive_design,
            _ref_high_level_study_design.is_adaptive_design,
        )
        self.assertEqual(
            self.get_field_or_simple_term_uid(
                _res_high_level_study_design.is_adaptive_design_null_value_code
            ),
            _ref_high_level_study_design.is_adaptive_design_null_value_code,
        )
        self.assertEqual(
            _res_high_level_study_design.study_stop_rules,
            _ref_high_level_study_design.study_stop_rules,
        )
        self.assertEqual(
            self.get_field_or_simple_term_uid(
                _res_high_level_study_design.study_stop_rules_null_value_code
            ),
            _ref_high_level_study_design.study_stop_rules_null_value_code,
        )
        self.assertEqual(
            self.get_field_or_simple_term_uid(
                _res_high_level_study_design.trial_phase_code
            ),
            _ref_high_level_study_design.trial_phase_code,
        )
        self.assertEqual(
            self.get_field_or_simple_term_uid(
                _res_high_level_study_design.trial_phase_null_value_code
            ),
            _ref_high_level_study_design.trial_phase_null_value_code,
        )
        self.assertEqual(
            [
                self.get_field_or_simple_term_uid(trial_type_code)
                for trial_type_code in _res_high_level_study_design.trial_type_codes
            ],
            list(_ref_high_level_study_design.trial_type_codes),
        )
        self.assertEqual(
            self.get_field_or_simple_term_uid(
                _res_high_level_study_design.trial_type_null_value_code
            ),
            _ref_high_level_study_design.trial_type_null_value_code,
        )

    @patch(StudyService.__module__ + ".MetaRepository.unit_definition_repository")
    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__study_service__create__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
        unit_definition_repository_property_mock: PropertyMock,
    ):
        # given
        test_db = StudyDefinitionsDBFake()
        test_repo = StudyDefinitionRepositoryFake(test_db)
        study_definition_repository_property_mock.return_value = test_repo
        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint: disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint: disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )
        unit_definition_repository_property_mock.final_concept_exists.return_value = (
            True
        )
        study_create_input = StudyCreateInput(
            study_acronym="ACRONYM", project_number="something"
        )
        study_service = StudyService()
        study_service.post_study_preferred_time_unit = lambda study_uid, unit_definition_uid, for_protocol_soa=False: StudyPreferredTimeUnit(
            study_uid=study_uid,
            time_unit_uid="time_unit_uid",
            time_unit_name="time_unit_name",
        )

        # when
        study_service.create(study_create_input=study_create_input)

        # then
        another_repo_instance = StudyDefinitionRepositoryFake(test_db)
        db_content = another_repo_instance.find_all(
            page_number=1, page_size=sys.maxsize
        ).items
        self.assertEqual(len(db_content), 1)
        for study_definition_ar in db_content:
            self.assertEqual(
                study_definition_ar.current_metadata.ver_metadata.study_status,
                StudyStatus.DRAFT,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.study_acronym,
                study_create_input.study_acronym,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.study_number,
                study_create_input.study_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.project_number,
                study_create_input.project_number,
            )

    @patch(StudyService.__module__ + ".MetaRepository.ct_term_name_repository")
    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__study_service__get_by_uid__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
        ct_term_name_repository_property_mock: PropertyMock,
    ):
        # given
        test_db = StudyDefinitionsDBFake()

        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = create_random_study(
            generate_uid_callback=prepare_repo.generate_uid
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()

        test_repo = StudyDefinitionRepositoryFake(test_db)
        study_definition_repository_property_mock.return_value = test_repo

        ct_term_name_repository_property_mock.find_by_uid.return_value = (
            create_random_ct_term_name_ar()
        )
        ct_term_name_repository_property_mock.find_by_uids.side_effect = (
            lambda term_uids, at_specific_date: (
                create_random_ct_term_name_ars(term_uids=term_uids)
            )
        )
        # Change the __module__ attribute to simulate the module change
        ct_term_name_repository_property_mock.find_by_uids.__module__ = (
            ct_term_generic_repository.__name__
        )
        # when
        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint: disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint: disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )
        study_service = StudyService()
        service_response = study_service.get_by_uid(sample_study_definition.uid)

        # then
        self.assertEqual(
            sample_study_definition.current_metadata.ver_metadata.study_status,
            StudyStatus.DRAFT,
        )
        self.assertEqual(
            sample_study_definition.current_metadata.id_metadata.study_acronym,
            service_response.current_metadata.identification_metadata.study_acronym,
        )
        self.assertEqual(
            sample_study_definition.current_metadata.id_metadata.study_number,
            service_response.current_metadata.identification_metadata.study_number,
        )
        self.assertEqual(
            sample_study_definition.current_metadata.id_metadata.project_number,
            service_response.current_metadata.identification_metadata.project_number,
        )
        self.assertEqual(sample_study_definition.uid, service_response.uid)

    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__study_service__get_all__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
    ):
        # given
        test_db = StudyDefinitionsDBFake()

        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definitions = [
            StudyDefinitionAR.from_initial_values(
                generate_uid_callback=prepare_repo.generate_uid,
                initial_id_metadata=StudyIdentificationMetadataVO.from_input_values(
                    project_number=None,
                    study_acronym=f"ACRONYM-{num}",
                    study_number=None,
                    subpart_id=None,
                    description=None,
                    registry_identifiers=RegistryIdentifiersVO.from_input_values(
                        ct_gov_id=None,
                        eudract_id=None,
                        universal_trial_number_utn=None,
                        japanese_trial_registry_id_japic=None,
                        investigational_new_drug_application_number_ind=None,
                        ct_gov_id_null_value_code=None,
                        eudract_id_null_value_code=None,
                        eu_trial_number=None,
                        civ_id_sin_number=None,
                        national_clinical_trial_number=None,
                        japanese_trial_registry_number_jrct=None,
                        national_medical_products_administration_nmpa_number=None,
                        eudamed_srn_number=None,
                        investigational_device_exemption_ide_number=None,
                        universal_trial_number_utn_null_value_code=None,
                        japanese_trial_registry_id_japic_null_value_code=None,
                        investigational_new_drug_application_number_ind_null_value_code=None,
                        eu_trial_number_null_value_code=None,
                        civ_id_sin_number_null_value_code=None,
                        national_clinical_trial_number_null_value_code=None,
                        japanese_trial_registry_number_jrct_null_value_code=None,
                        national_medical_products_administration_nmpa_number_null_value_code=None,
                        eudamed_srn_number_null_value_code=None,
                        investigational_device_exemption_ide_number_null_value_code=None,
                    ),
                ),
                study_title_exists_callback=(lambda _, study_number: False),
                study_short_title_exists_callback=(lambda _, study_number: False),
            )
            for num in range(0, 2)
        ]
        for _study_definition in sample_study_definitions:
            prepare_repo.save(_study_definition)
        prepare_repo.close()

        test_repo = StudyDefinitionRepositoryFake(test_db)
        study_definition_repository_property_mock.return_value = test_repo

        # when
        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint: disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint: disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )
        study_service = StudyService()
        service_response = study_service.get_all().items

        # then
        self.assertEqual(len(service_response), len(sample_study_definitions))

        self.assertEqual(
            {_.uid for _ in service_response}, {_.uid for _ in sample_study_definitions}
        )

        for sample_study_definition in sample_study_definitions:
            service_response_item = [
                _ for _ in service_response if _.uid == sample_study_definition.uid
            ][0]
            self.assertEqual(
                sample_study_definition.current_metadata.ver_metadata.study_status.value,
                service_response_item.current_metadata.version_metadata.study_status,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.id_metadata.study_acronym,
                service_response_item.current_metadata.identification_metadata.study_acronym,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.id_metadata.study_number,
                service_response_item.current_metadata.identification_metadata.study_number,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.id_metadata.project_number,
                service_response_item.current_metadata.identification_metadata.project_number,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.ver_metadata.version_number,
                service_response_item.current_metadata.version_metadata.version_number,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.ver_metadata.version_description,
                service_response_item.current_metadata.version_metadata.version_description,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.ver_metadata.version_author,
                service_response_item.current_metadata.version_metadata.version_author,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.ver_metadata.version_timestamp,
                service_response_item.current_metadata.version_metadata.version_timestamp,
            )

    @patch(f"{StudyService.__module__}.MetaRepository.ct_term_name_repository")
    @patch(
        f"{StudyService.__module__}.MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__get_protocol_title__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        ct_term_name_repository_property_mock: PropertyMock,
    ):
        # given
        test_db = StudyDefinitionsDBFake()
        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = create_random_study(
            generate_uid_callback=prepare_repo.generate_uid
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()

        test_repo = StudyDefinitionRepositoryFake(test_db)
        study_definition_repository_property_mock.return_value = test_repo
        ct_term_name_repository_property_mock.find_by_uid.return_value = (
            create_random_ct_term_name_ar()
        )
        ct_term_name_repository_property_mock.find_by_uids.side_effect = (
            lambda term_uids, at_specific_date: (
                create_random_ct_term_name_ars(term_uids=term_uids)
            )
        )
        # Change the __module__ attribute to simulate the module change
        ct_term_name_repository_property_mock.find_by_uids.__module__ = (
            ct_term_generic_repository.__name__
        )

        # When
        study_service = StudyService()
        result = study_service.get_protocol_title(sample_study_definition.uid)

        # Then
        self.assertEqual(
            sample_study_definition.current_metadata.id_metadata.registry_identifiers.eudract_id,
            result.eudract_id,
        )

    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__patch__high_level_study_design__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
    ):
        # given
        test_db = StudyDefinitionsDBFake()

        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint: disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint: disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )

        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = StudyDefinitionAR.from_initial_values(
            generate_uid_callback=prepare_repo.generate_uid,
            initial_id_metadata=StudyIdentificationMetadataVO.from_input_values(
                project_number=None,
                study_acronym="ACRONYM",
                study_number=None,
                subpart_id=None,
                description=None,
                registry_identifiers=RegistryIdentifiersVO.from_input_values(
                    ct_gov_id=None,
                    eudract_id=None,
                    universal_trial_number_utn=None,
                    japanese_trial_registry_id_japic=None,
                    investigational_new_drug_application_number_ind=None,
                    eu_trial_number=None,
                    civ_id_sin_number=None,
                    national_clinical_trial_number=None,
                    japanese_trial_registry_number_jrct=None,
                    national_medical_products_administration_nmpa_number=None,
                    eudamed_srn_number=None,
                    investigational_device_exemption_ide_number=None,
                    ct_gov_id_null_value_code=None,
                    eudract_id_null_value_code=None,
                    universal_trial_number_utn_null_value_code=None,
                    japanese_trial_registry_id_japic_null_value_code=None,
                    investigational_new_drug_application_number_ind_null_value_code=None,
                    eu_trial_number_null_value_code=None,
                    civ_id_sin_number_null_value_code=None,
                    national_clinical_trial_number_null_value_code=None,
                    japanese_trial_registry_number_jrct_null_value_code=None,
                    national_medical_products_administration_nmpa_number_null_value_code=None,
                    eudamed_srn_number_null_value_code=None,
                    investigational_device_exemption_ide_number_null_value_code=None,
                ),
            ),
            initial_high_level_study_design=HighLevelStudyDesignVO.from_input_values(
                study_type_code=None,
                study_stop_rules_null_value_code=None,
                trial_type_codes=[],
                trial_type_null_value_code=None,
                trial_phase_code=None,
                trial_phase_null_value_code=None,
                is_adaptive_design=False,
                is_adaptive_design_null_value_code=None,
                is_extension_trial=False,
                is_extension_trial_null_value_code=None,
                study_stop_rules="Some important study stop rules.",
                study_type_null_value_code=None,
                confirmed_response_minimum_duration=None,
                confirmed_response_minimum_duration_null_value_code=None,
                post_auth_indicator=None,
                post_auth_indicator_null_value_code=None,
            ),
            study_title_exists_callback=(lambda _, study_number: False),
            study_short_title_exists_callback=(lambda _, study_number: False),
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()

        high_level_study_design = HighLevelStudyDesignJsonModel(
            study_stop_rules="Other study stop rules."
        )
        current_metadata = StudyMetadataJsonModel(
            high_level_study_design=high_level_study_design
        )
        study_patch_request = StudyPatchRequestJsonModel(
            current_metadata=current_metadata
        )

        assert study_patch_request.current_metadata is not None
        assert study_patch_request.current_metadata.high_level_study_design is not None

        test_repo = StudyDefinitionRepositoryFake(test_db)
        study_definition_repository_property_mock.return_value = test_repo

        # when
        study_service = StudyService()
        study_service.patch(
            uid=sample_study_definition.uid,
            dry=False,
            study_patch_request=study_patch_request,
        )

        # then
        another_repo_instance = StudyDefinitionRepositoryFake(test_db)
        db_content = another_repo_instance.find_all(
            page_number=1, page_size=sys.maxsize
        ).items

        self.assertEqual(len(db_content), 1)
        for study_definition_ar in db_content:
            self.assertEqual(
                study_definition_ar.current_metadata.ver_metadata.study_status,
                StudyStatus.DRAFT,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata,
                sample_study_definition.current_metadata.id_metadata,
            )

            # we check whether new high_level_study_design is as expected

            self.assertEqual(
                study_definition_ar.current_metadata.high_level_study_design,
                sample_study_definition.current_metadata.high_level_study_design.fix_some_values(
                    study_stop_rules=(
                        study_patch_request.current_metadata.high_level_study_design.study_stop_rules
                    )
                ),
            )

    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__patch__id_metadata__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
    ):
        # given
        test_db = StudyDefinitionsDBFake()

        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint: disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint: disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )

        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = StudyDefinitionAR.from_initial_values(
            generate_uid_callback=prepare_repo.generate_uid,
            initial_id_metadata=StudyIdentificationMetadataVO.from_input_values(
                project_number=None,
                study_acronym="ACRONYM",
                study_number=None,
                subpart_id=None,
                description=None,
                registry_identifiers=RegistryIdentifiersVO.from_input_values(
                    ct_gov_id=None,
                    eudract_id=None,
                    universal_trial_number_utn=None,
                    japanese_trial_registry_id_japic=None,
                    investigational_new_drug_application_number_ind=None,
                    eu_trial_number=None,
                    civ_id_sin_number=None,
                    national_clinical_trial_number=None,
                    japanese_trial_registry_number_jrct=None,
                    national_medical_products_administration_nmpa_number=None,
                    eudamed_srn_number=None,
                    investigational_device_exemption_ide_number=None,
                    ct_gov_id_null_value_code=None,
                    eudract_id_null_value_code=None,
                    universal_trial_number_utn_null_value_code=None,
                    japanese_trial_registry_id_japic_null_value_code=None,
                    investigational_new_drug_application_number_ind_null_value_code=None,
                    eu_trial_number_null_value_code=None,
                    civ_id_sin_number_null_value_code=None,
                    national_clinical_trial_number_null_value_code=None,
                    japanese_trial_registry_number_jrct_null_value_code=None,
                    national_medical_products_administration_nmpa_number_null_value_code=None,
                    eudamed_srn_number_null_value_code=None,
                    investigational_device_exemption_ide_number_null_value_code=None,
                ),
            ),
            study_title_exists_callback=(lambda _, study_number: False),
            study_short_title_exists_callback=(lambda _, study_number: False),
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()

        # patching without registry_identifiers
        identification_metadata = StudyIdentificationMetadataJsonModel()
        identification_metadata.study_acronym = "OTHER_ACRONYM"
        current_metadata = StudyMetadataJsonModel(
            identification_metadata=identification_metadata
        )
        study_patch_request = StudyPatchRequestJsonModel(
            current_metadata=current_metadata
        )

        assert study_patch_request.current_metadata is not None
        assert study_patch_request.current_metadata.identification_metadata is not None

        test_repo = StudyDefinitionRepositoryFake(test_db)
        study_definition_repository_property_mock.return_value = test_repo
        project_repository_property_mock.project_number_exists.return_value = True

        # when
        study_service = StudyService()
        study_service.patch(
            uid=sample_study_definition.uid,
            dry=False,
            study_patch_request=study_patch_request,
        )

        # then
        another_repo_instance = StudyDefinitionRepositoryFake(test_db)
        db_content = another_repo_instance.find_all(
            page_number=1, page_size=sys.maxsize
        ).items

        self.assertEqual(len(db_content), 1)
        for study_definition_ar in db_content:
            self.assertEqual(
                study_definition_ar.current_metadata.ver_metadata.study_status,
                StudyStatus.DRAFT,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.study_acronym,
                study_patch_request.current_metadata.identification_metadata.study_acronym,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.study_number,
                sample_study_definition.current_metadata.id_metadata.study_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.eudract_id,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.eudract_id,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.ct_gov_id,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.ct_gov_id,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.eudract_id_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.eudract_id_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.ct_gov_id_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.ct_gov_id_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn_null_value_code,
            )
            self.assertEqual(
                # pylint: disable=line-too-long
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind_null_value_code,
                # pylint: disable=line-too-long
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.eu_trial_number,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.eu_trial_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.civ_id_sin_number,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.civ_id_sin_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.eu_trial_number_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.eu_trial_number_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.civ_id_sin_number_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.civ_id_sin_number_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct_null_value_code,
            )
            self.assertEqual(
                # pylint: disable=line-too-long
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.project_number,
                sample_study_definition.current_metadata.id_metadata.project_number,
            )

    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__patch__id_metadata_registry_identifiers__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
    ):
        # given
        test_db = StudyDefinitionsDBFake()

        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint: disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint: disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )

        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = StudyDefinitionAR.from_initial_values(
            generate_uid_callback=prepare_repo.generate_uid,
            initial_id_metadata=StudyIdentificationMetadataVO.from_input_values(
                project_number=None,
                study_acronym="ACRONYM",
                study_number=None,
                subpart_id=None,
                description=None,
                registry_identifiers=RegistryIdentifiersVO.from_input_values(
                    ct_gov_id=None,
                    eudract_id=None,
                    universal_trial_number_utn=None,
                    japanese_trial_registry_id_japic=None,
                    investigational_new_drug_application_number_ind=None,
                    eu_trial_number=None,
                    civ_id_sin_number=None,
                    national_clinical_trial_number=None,
                    japanese_trial_registry_number_jrct=None,
                    national_medical_products_administration_nmpa_number=None,
                    eudamed_srn_number=None,
                    investigational_device_exemption_ide_number=None,
                    ct_gov_id_null_value_code=None,
                    eudract_id_null_value_code=None,
                    universal_trial_number_utn_null_value_code=None,
                    japanese_trial_registry_id_japic_null_value_code=None,
                    investigational_new_drug_application_number_ind_null_value_code=None,
                    eu_trial_number_null_value_code=None,
                    civ_id_sin_number_null_value_code=None,
                    national_clinical_trial_number_null_value_code=None,
                    japanese_trial_registry_number_jrct_null_value_code=None,
                    national_medical_products_administration_nmpa_number_null_value_code=None,
                    eudamed_srn_number_null_value_code=None,
                    investigational_device_exemption_ide_number_null_value_code=None,
                ),
            ),
            study_title_exists_callback=(lambda _, study_number: False),
            study_short_title_exists_callback=(lambda _, study_number: False),
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()

        ri_metadata = RegistryIdentifiersJsonModel()
        ri_metadata.ct_gov_id = "ct_gov_has_value"
        # removing part data model to ensure we can patch without complete model being submitted
        del ri_metadata.eudract_id
        identification_metadata = StudyIdentificationMetadataJsonModel(
            registry_identifiers=ri_metadata
        )
        current_metadata = StudyMetadataJsonModel(
            identification_metadata=identification_metadata
        )
        study_patch_request = StudyPatchRequestJsonModel(
            current_metadata=current_metadata
        )

        assert study_patch_request.current_metadata is not None
        assert study_patch_request.current_metadata.identification_metadata is not None
        assert (
            study_patch_request.current_metadata.identification_metadata.registry_identifiers
            is not None
        )

        test_repo = StudyDefinitionRepositoryFake(test_db)
        study_definition_repository_property_mock.return_value = test_repo
        project_repository_property_mock.project_number_exists.return_value = True

        # when
        study_service = StudyService()
        study_service.patch(
            uid=sample_study_definition.uid,
            dry=False,
            study_patch_request=study_patch_request,
        )

        # then
        another_repo_instance = StudyDefinitionRepositoryFake(test_db)
        db_content = another_repo_instance.find_all(
            page_number=1, page_size=sys.maxsize
        ).items

        self.assertEqual(len(db_content), 1)
        for study_definition_ar in db_content:
            self.assertEqual(
                study_definition_ar.current_metadata.ver_metadata.study_status,
                StudyStatus.DRAFT,
            )

            # we check if other parts stay intact
            print("STUDY POP", study_definition_ar.current_metadata.study_population)
            print("MODIFIED", sample_study_definition.current_metadata.study_population)
            self.assertEqual(
                study_definition_ar.current_metadata.study_population,
                sample_study_definition.current_metadata.study_population,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.high_level_study_design,
                sample_study_definition.current_metadata.high_level_study_design,
            )

            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.study_acronym,
                study_patch_request.current_metadata.identification_metadata.study_acronym,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.study_number,
                sample_study_definition.current_metadata.id_metadata.study_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.eudract_id,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.eudract_id,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.study_acronym,
                sample_study_definition.current_metadata.id_metadata.study_acronym,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.eudract_id_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.eudract_id_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn_null_value_code,
            )
            self.assertEqual(
                # pylint: disable=line-too-long
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind_null_value_code,
                # pylint: disable=line-too-long
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.eu_trial_number,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.eu_trial_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.civ_id_sin_number,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.civ_id_sin_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.eu_trial_number_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.eu_trial_number_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.civ_id_sin_number_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.civ_id_sin_number_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct_null_value_code,
            )
            self.assertEqual(
                # pylint: disable=line-too-long
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.project_number,
                sample_study_definition.current_metadata.id_metadata.project_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.project_number,
                sample_study_definition.current_metadata.id_metadata.project_number,
            )

    @patch(StudyService.__module__ + ".MetaRepository.unit_definition_repository")
    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__patch__study_population__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
        unit_definition_repository_property_mock: PropertyMock,
        ct_gov_id=None,
    ):
        # given
        unit_definition_test_repo = UnitDefinitionRepositoryForTestImpl()
        test_db = StudyDefinitionsDBFake()
        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = StudyDefinitionAR.from_initial_values(
            generate_uid_callback=prepare_repo.generate_uid,
            initial_id_metadata=StudyIdentificationMetadataVO.from_input_values(
                project_number=None,
                study_acronym="ACRONYM",
                study_number=None,
                subpart_id=None,
                description=None,
                registry_identifiers=RegistryIdentifiersVO.from_input_values(
                    ct_gov_id=ct_gov_id,
                    eudract_id=None,
                    universal_trial_number_utn=None,
                    japanese_trial_registry_id_japic=None,
                    investigational_new_drug_application_number_ind=None,
                    eu_trial_number=None,
                    civ_id_sin_number=None,
                    national_clinical_trial_number=None,
                    japanese_trial_registry_number_jrct=None,
                    national_medical_products_administration_nmpa_number=None,
                    eudamed_srn_number=None,
                    investigational_device_exemption_ide_number=None,
                    ct_gov_id_null_value_code=None,
                    eudract_id_null_value_code=None,
                    universal_trial_number_utn_null_value_code=None,
                    japanese_trial_registry_id_japic_null_value_code=None,
                    investigational_new_drug_application_number_ind_null_value_code=None,
                    eu_trial_number_null_value_code=None,
                    civ_id_sin_number_null_value_code=None,
                    national_clinical_trial_number_null_value_code=None,
                    japanese_trial_registry_number_jrct_null_value_code=None,
                    national_medical_products_administration_nmpa_number_null_value_code=None,
                    eudamed_srn_number_null_value_code=None,
                    investigational_device_exemption_ide_number_null_value_code=None,
                ),
            ),
            study_title_exists_callback=(lambda _, study_number: False),
            study_short_title_exists_callback=(lambda _, study_number: False),
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()

        unit_definitions, _ = unit_definition_test_repo.find_all()
        study_population = StudyPopulationJsonModel(
            planned_minimum_age_of_subjects=DurationJsonModel(
                # some positive number
                duration_value=random.randint(0, 100),
                # one of the values in age unit test repo
                duration_unit_code={
                    "uid": random.choice([_.uid for _ in unit_definitions])
                },
            ),
            rare_disease_indicator=random.choice([True, False]),
        )
        current_metadata = StudyMetadataJsonModel(study_population=study_population)
        study_patch_request = StudyPatchRequestJsonModel(
            current_metadata=current_metadata
        )

        assert study_patch_request.current_metadata is not None
        assert study_patch_request.current_metadata.study_population is not None
        assert (
            study_patch_request.current_metadata.study_population.planned_minimum_age_of_subjects
            is not None
        )

        test_repo = StudyDefinitionRepositoryFake(test_db)

        # mocking repos
        unit_definition_repository_property_mock.find_all.return_value = (
            unit_definition_test_repo.find_all()
        )
        unit_definition_repository_property_mock.find_by_uid_2 = (
            unit_definition_test_repo.find_by_uid_2
        )

        study_definition_repository_property_mock.return_value = test_repo
        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint: disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint: disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )

        # when
        study_service = StudyService()
        study_service.patch(
            uid=sample_study_definition.uid,
            dry=False,
            study_patch_request=study_patch_request,
        )

        # then
        another_repo_instance = StudyDefinitionRepositoryFake(test_db)
        db_content = another_repo_instance.find_all(
            page_number=1, page_size=sys.maxsize
        ).items

        self.assertEqual(len(db_content), 1)
        for study_definition_ar in db_content:
            self.assertEqual(
                study_definition_ar.current_metadata.ver_metadata.study_status,
                StudyStatus.DRAFT,
            )

            # we check if other parts stay intact
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata,
                sample_study_definition.current_metadata.id_metadata,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.high_level_study_design,
                sample_study_definition.current_metadata.high_level_study_design,
            )

            # we check whether new high_level_study_design is as expected
            assert (
                study_population.planned_minimum_age_of_subjects is not None
            )  # for linter to be happy
            self.assertEqual(
                study_definition_ar.current_metadata.study_population,
                sample_study_definition.current_metadata.study_population.fix_some_values(
                    planned_minimum_age_of_subjects=create_duration_object_from_api_input(
                        value=study_population.planned_minimum_age_of_subjects.duration_value,
                        unit=(
                            study_population.planned_minimum_age_of_subjects.duration_unit_code.uid
                        ),
                        find_duration_name_by_code=lambda _: unit_definition_test_repo.find_by_uid_2(
                            study_population.planned_minimum_age_of_subjects.duration_unit_code.uid
                        ),
                    ),
                    rare_disease_indicator=study_population.rare_disease_indicator,
                ),
            )

    @patch(StudyService.__module__ + ".MetaRepository.unit_definition_repository")
    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__patch__study_intervention__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
        unit_definition_repository_property_mock: PropertyMock,
        ct_gov_id=None,
    ):
        # given
        unit_definition_test_repo = UnitDefinitionRepositoryForTestImpl()
        test_db = StudyDefinitionsDBFake()
        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = StudyDefinitionAR.from_initial_values(
            generate_uid_callback=prepare_repo.generate_uid,
            initial_id_metadata=StudyIdentificationMetadataVO.from_input_values(
                project_number=None,
                study_acronym="ACRONYM",
                study_number=None,
                subpart_id=None,
                description=None,
                registry_identifiers=RegistryIdentifiersVO.from_input_values(
                    ct_gov_id=ct_gov_id,
                    eudract_id=None,
                    universal_trial_number_utn=None,
                    japanese_trial_registry_id_japic=None,
                    investigational_new_drug_application_number_ind=None,
                    eu_trial_number=None,
                    civ_id_sin_number=None,
                    national_clinical_trial_number=None,
                    japanese_trial_registry_number_jrct=None,
                    national_medical_products_administration_nmpa_number=None,
                    eudamed_srn_number=None,
                    investigational_device_exemption_ide_number=None,
                    ct_gov_id_null_value_code=None,
                    eudract_id_null_value_code=None,
                    universal_trial_number_utn_null_value_code=None,
                    japanese_trial_registry_id_japic_null_value_code=None,
                    investigational_new_drug_application_number_ind_null_value_code=None,
                    eu_trial_number_null_value_code=None,
                    civ_id_sin_number_null_value_code=None,
                    national_clinical_trial_number_null_value_code=None,
                    japanese_trial_registry_number_jrct_null_value_code=None,
                    national_medical_products_administration_nmpa_number_null_value_code=None,
                    eudamed_srn_number_null_value_code=None,
                    investigational_device_exemption_ide_number_null_value_code=None,
                ),
            ),
            study_title_exists_callback=(lambda _, study_number: False),
            study_short_title_exists_callback=(lambda _, study_number: False),
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()
        unit_definitions, _ = unit_definition_test_repo.find_all()
        study_intervention = StudyInterventionJsonModel(
            planned_study_length=DurationJsonModel(
                # some positive number
                duration_value=random.randint(0, 100),
                # one of the values in age unit test repo
                duration_unit_code={
                    "uid": random.choice([_.uid for _ in unit_definitions])
                },
            ),
            is_trial_randomised=random.choice([True, False]),
        )
        current_metadata = StudyMetadataJsonModel(study_intervention=study_intervention)
        study_patch_request = StudyPatchRequestJsonModel(
            current_metadata=current_metadata
        )

        assert study_patch_request.current_metadata is not None
        assert study_patch_request.current_metadata.study_intervention is not None
        assert (
            study_patch_request.current_metadata.study_intervention.planned_study_length
            is not None
        )

        test_repo = StudyDefinitionRepositoryFake(test_db)

        # mocking repos
        unit_definition_repository_property_mock.find_all.return_value = (
            unit_definition_test_repo.find_all()
        )
        unit_definition_repository_property_mock.find_by_uid_2 = (
            unit_definition_test_repo.find_by_uid_2
        )
        study_definition_repository_property_mock.return_value = test_repo
        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint: disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint: disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )

        # when
        study_service = StudyService()
        study_service.patch(
            uid=sample_study_definition.uid,
            dry=False,
            study_patch_request=study_patch_request,
        )

        # then
        another_repo_instance = StudyDefinitionRepositoryFake(test_db)
        db_content = another_repo_instance.find_all(
            page_number=1, page_size=sys.maxsize
        ).items

        self.assertEqual(len(db_content), 1)
        for study_definition_ar in db_content:
            self.assertEqual(
                study_definition_ar.current_metadata.ver_metadata.study_status,
                StudyStatus.DRAFT,
            )

            # we check if other parts stay intact
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata,
                sample_study_definition.current_metadata.id_metadata,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.high_level_study_design,
                sample_study_definition.current_metadata.high_level_study_design,
            )

            # we check whether new high_level_study_design is as expected
            assert (
                study_intervention.planned_study_length is not None
            )  # for linter to be happy
            self.assertEqual(
                study_definition_ar.current_metadata.study_intervention,
                sample_study_definition.current_metadata.study_intervention.fix_some_values(
                    planned_study_length=create_duration_object_from_api_input(
                        value=study_intervention.planned_study_length.duration_value,
                        unit=(
                            study_intervention.planned_study_length.duration_unit_code.uid
                        ),
                        find_duration_name_by_code=lambda _: unit_definition_test_repo.find_by_uid_2(
                            study_intervention.planned_study_length.duration_unit_code.uid
                        ),
                    ),
                    is_trial_randomised=study_intervention.is_trial_randomised,
                ),
            )

    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    @patch(
        StudyService.__module__ + ".MetaRepository.study_title_repository",
        new_callable=PropertyMock,
    )
    def test__patch__study_description__success(
        self,
        study_title_repository_mock: PropertyMock,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
    ):
        # given
        study_title_test_repo = StudyTitleRepositoryForTestImpl()
        test_db = StudyDefinitionsDBFake()
        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = StudyDefinitionAR.from_initial_values(
            generate_uid_callback=prepare_repo.generate_uid,
            initial_id_metadata=StudyIdentificationMetadataVO.from_input_values(
                project_number=None,
                study_acronym="ACRONYM",
                study_number=None,
                subpart_id=None,
                description=None,
                registry_identifiers=RegistryIdentifiersVO.from_input_values(
                    ct_gov_id=None,
                    eudract_id=None,
                    universal_trial_number_utn=None,
                    japanese_trial_registry_id_japic=None,
                    investigational_new_drug_application_number_ind=None,
                    eu_trial_number=None,
                    civ_id_sin_number=None,
                    national_clinical_trial_number=None,
                    japanese_trial_registry_number_jrct=None,
                    national_medical_products_administration_nmpa_number=None,
                    eudamed_srn_number=None,
                    investigational_device_exemption_ide_number=None,
                    ct_gov_id_null_value_code=None,
                    eudract_id_null_value_code=None,
                    universal_trial_number_utn_null_value_code=None,
                    japanese_trial_registry_id_japic_null_value_code=None,
                    investigational_new_drug_application_number_ind_null_value_code=None,
                    eu_trial_number_null_value_code=None,
                    civ_id_sin_number_null_value_code=None,
                    national_clinical_trial_number_null_value_code=None,
                    japanese_trial_registry_number_jrct_null_value_code=None,
                    national_medical_products_administration_nmpa_number_null_value_code=None,
                    eudamed_srn_number_null_value_code=None,
                    investigational_device_exemption_ide_number_null_value_code=None,
                ),
            ),
            study_title_exists_callback=(lambda _, study_number: False),
            study_short_title_exists_callback=(lambda _, study_number: False),
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()

        study_title = random_str()
        study_short_title = random_str()
        study_description = StudyDescriptionJsonModel(
            study_title=str(study_title), study_short_title=str(study_short_title)
        )
        current_metadata = StudyMetadataJsonModel(study_description=study_description)
        study_patch_request = StudyPatchRequestJsonModel(
            current_metadata=current_metadata
        )

        assert study_patch_request.current_metadata is not None
        assert study_patch_request.current_metadata.study_description is not None
        assert (
            study_patch_request.current_metadata.study_description.study_title
            is not None
        )

        test_repo = StudyDefinitionRepositoryFake(test_db)

        # mocking repos
        study_definition_repository_property_mock.return_value = test_repo
        study_title_repository_mock.return_value = study_title_test_repo
        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint: disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint: disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )

        # when
        study_service = StudyService()
        study_service.patch(
            uid=sample_study_definition.uid,
            dry=False,
            study_patch_request=study_patch_request,
        )

        # then
        another_repo_instance = StudyDefinitionRepositoryFake(test_db)
        db_content = another_repo_instance.find_all(
            page_number=1, page_size=sys.maxsize
        ).items

        self.assertEqual(len(db_content), 1)
        for study_definition_ar in db_content:
            self.assertEqual(
                study_definition_ar.current_metadata.ver_metadata.study_status,
                StudyStatus.DRAFT,
            )

            # we check if other parts stay intact
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata,
                sample_study_definition.current_metadata.id_metadata,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.high_level_study_design,
                sample_study_definition.current_metadata.high_level_study_design,
            )

            # we check whether new study_description is as expected
            assert study_description.study_title is not None  # for linter to be happy
            self.assertEqual(
                study_definition_ar.current_metadata.study_description,
                sample_study_definition.current_metadata.study_description.fix_some_values(
                    study_title=study_description.study_title,
                    study_short_title=study_description.study_short_title,
                ),
            )
