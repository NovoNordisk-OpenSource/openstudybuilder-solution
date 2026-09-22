import random
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable, Mapping

from clinical_mdr_api.domains.study_definition_aggregates.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domains.study_definition_aggregates.root import (
    _DEF_INITIAL_HIGH_LEVEL_STUDY_DESIGN,
    _DEF_INITIAL_STUDY_INTERVENTION,
    _DEF_INITIAL_STUDY_POPULATION,
    StudyDefinitionAR,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    HighLevelStudyDesignVO,
    StudyDescriptionVO,
    StudyIdentificationMetadataVO,
    StudyInterventionVO,
    StudyMetadataVO,
    StudyPopulationVO,
    StudyStatus,
    StudyVersionMetadataVO,
)
from clinical_mdr_api.tests.unit.domain.study_definition_aggregate.test_study_metadata import (
    random_valid_high_level_study_design,
    random_valid_id_metadata,
    random_valid_study_intervention,
    random_valid_study_population,
)
from clinical_mdr_api.tests.unit.domain.utils import random_str
from common import exceptions


def _test_uid_generator() -> str:
    return random_str()


def _dict() -> Mapping[str, Any]:
    return {}


def create_random_study(
    generate_uid_callback: Callable[[], str],
    *,
    condition: Callable[[StudyDefinitionAR], bool] = lambda _: True,
    new_id_metadata_condition: Callable[
        [StudyIdentificationMetadataVO], bool
    ] = lambda _: True,
    new_id_metadata_fixed_values: Mapping[str, Any] | None = None,
    new_high_level_study_design_condition: Callable[
        [HighLevelStudyDesignVO], bool
    ] = lambda _: True,
    new_high_level_study_design_fixed_values: Mapping[str, Any] | None = None,
    new_study_population_condition: Callable[
        [StudyPopulationVO], bool
    ] = lambda _: True,
    new_study_intervention_condition: Callable[
        [StudyInterventionVO], bool
    ] = lambda _: True,
    max_tries: int = 100,
    is_study_after_create: bool = False,
    author_id: str = "unknown-user",
) -> StudyDefinitionAR:
    if new_id_metadata_fixed_values is None:
        new_id_metadata_fixed_values = _dict()
    if new_high_level_study_design_fixed_values is None:
        new_high_level_study_design_fixed_values = _dict()

    count: int = 0
    while True:
        initial_high_level_study_design = random_valid_high_level_study_design(
            condition=new_high_level_study_design_condition,
            fixed_values=new_high_level_study_design_fixed_values,
        )
        initial_id_metadata = random_valid_id_metadata(
            condition=new_id_metadata_condition,
            fixed_values=new_id_metadata_fixed_values,
        )
        initial_study_population = random_valid_study_population(
            condition=new_study_population_condition, max_tries=max_tries
        )
        initial_study_intervention = random_valid_study_intervention(
            condition=new_study_intervention_condition, max_tries=max_tries
        )
        result: StudyDefinitionAR = StudyDefinitionAR.from_initial_values(
            generate_uid_callback=generate_uid_callback,
            initial_id_metadata=initial_id_metadata,
            project_exists_callback=lambda _: True,
            study_number_exists_callback=lambda x, y: False,
            study_acronym_exists_callback=lambda x, y: False,
            initial_high_level_study_design=(
                initial_high_level_study_design
                if not is_study_after_create
                else _DEF_INITIAL_HIGH_LEVEL_STUDY_DESIGN
            ),
            study_type_exists_callback=lambda _: True,
            trial_type_exists_callback=lambda _: True,
            trial_intent_type_exists_callback=lambda _: True,
            trial_phase_exists_callback=lambda _: True,
            null_value_exists_callback=lambda _: True,
            initial_study_population=(
                initial_study_population
                if not is_study_after_create
                else _DEF_INITIAL_STUDY_POPULATION
            ),
            therapeutic_area_exists_callback=lambda _: True,
            disease_condition_or_indication_exists_callback=lambda _: True,
            diagnosis_group_exists_callback=lambda _: True,
            sex_of_participants_exists_callback=lambda _: True,
            initial_study_intervention=(
                initial_study_intervention
                if not is_study_after_create
                else _DEF_INITIAL_STUDY_INTERVENTION
            ),
            intervention_type_exists_callback=lambda _: True,
            control_type_exists_callback=lambda _: True,
            intervention_model_exists_callback=lambda _: True,
            trial_blinding_schema_exists_callback=lambda _: True,
            study_title_exists_callback=lambda _, study_number: False,
            study_short_title_exists_callback=lambda _, study_number: False,
            author_id=author_id,
        )

        if condition(result):
            return result
        count = count + 1
        if count >= max_tries:
            raise TimeoutError(
                f"Cannot find random data which satisfy given condition (after {count} tries)"
            )


def make_random_study_metadata_edit(
    study: StudyDefinitionAR,
    *,
    new_id_metadata_condition: Callable[[StudyIdentificationMetadataVO], bool] = (
        lambda _: True
    ),
    new_id_metadata_fixed_values: Mapping[str, Any] | None = None,
    new_high_level_study_design_condition: Callable[
        [HighLevelStudyDesignVO], bool
    ] = lambda _: True,
    new_high_level_study_design_fixed_values: Mapping[str, Any] | None = None,
    new_study_population_condition: Callable[
        [StudyPopulationVO], bool
    ] = lambda _: True,
    new_study_intervention_condition: Callable[
        [StudyInterventionVO], bool
    ] = lambda _: True,
    max_tries: int = 100,
    author_id: str,
):
    if new_id_metadata_fixed_values is None:
        new_id_metadata_fixed_values = _dict()
    if new_high_level_study_design_fixed_values is None:
        new_high_level_study_design_fixed_values = _dict()

    new_id_metadata = random_valid_id_metadata(
        max_tries=max_tries,
        condition=new_id_metadata_condition,
        fixed_values=new_id_metadata_fixed_values,
    )
    new_high_level_study_design = random_valid_high_level_study_design(
        max_tries=max_tries,
        condition=new_high_level_study_design_condition,
        fixed_values=new_high_level_study_design_fixed_values,
    )

    new_study_population = random_valid_study_population(
        condition=new_study_population_condition, max_tries=max_tries
    )

    new_study_intervention = random_valid_study_intervention(
        condition=new_study_intervention_condition, max_tries=max_tries
    )
    new_id_metadata = StudyIdentificationMetadataVO.from_input_values(
        study_number=(
            new_id_metadata.study_number
            if study.latest_locked_metadata is None
            else study.current_metadata.id_metadata.study_number
        ),
        subpart_id=None,
        study_acronym=new_id_metadata.study_acronym,
        project_number=new_id_metadata.project_number,
        description=new_id_metadata.description,
        registry_identifiers=RegistryIdentifiersVO(
            ct_gov_id=new_id_metadata.registry_identifiers.ct_gov_id,
            eudract_id=new_id_metadata.registry_identifiers.eudract_id,
            universal_trial_number_utn=new_id_metadata.registry_identifiers.universal_trial_number_utn,
            japanese_trial_registry_id_japic=new_id_metadata.registry_identifiers.japanese_trial_registry_id_japic,
            investigational_new_drug_application_number_ind=new_id_metadata.registry_identifiers.investigational_new_drug_application_number_ind,
            eu_trial_number=new_id_metadata.registry_identifiers.eu_trial_number,
            civ_id_sin_number=new_id_metadata.registry_identifiers.civ_id_sin_number,
            national_clinical_trial_number=new_id_metadata.registry_identifiers.national_clinical_trial_number,
            japanese_trial_registry_number_jrct=new_id_metadata.registry_identifiers.japanese_trial_registry_number_jrct,
            national_medical_products_administration_nmpa_number=(
                new_id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number
            ),
            eudamed_srn_number=new_id_metadata.registry_identifiers.eudamed_srn_number,
            investigational_device_exemption_ide_number=new_id_metadata.registry_identifiers.investigational_device_exemption_ide_number,
            eu_pas_number=new_id_metadata.registry_identifiers.eu_pas_number,
            ct_gov_id_null_value_code=new_id_metadata.registry_identifiers.ct_gov_id_null_value_code,
            eudract_id_null_value_code=new_id_metadata.registry_identifiers.eudract_id_null_value_code,
            universal_trial_number_utn_null_value_code=new_id_metadata.registry_identifiers.universal_trial_number_utn_null_value_code,
            japanese_trial_registry_id_japic_null_value_code=new_id_metadata.registry_identifiers.japanese_trial_registry_id_japic_null_value_code,
            investigational_new_drug_application_number_ind_null_value_code=(
                new_id_metadata.registry_identifiers.investigational_new_drug_application_number_ind_null_value_code
            ),
            eu_trial_number_null_value_code=new_id_metadata.registry_identifiers.eu_trial_number_null_value_code,
            civ_id_sin_number_null_value_code=new_id_metadata.registry_identifiers.civ_id_sin_number_null_value_code,
            national_clinical_trial_number_null_value_code=new_id_metadata.registry_identifiers.national_clinical_trial_number_null_value_code,
            japanese_trial_registry_number_jrct_null_value_code=(
                new_id_metadata.registry_identifiers.japanese_trial_registry_number_jrct_null_value_code
            ),
            national_medical_products_administration_nmpa_number_null_value_code=(
                new_id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number_null_value_code
            ),
            eudamed_srn_number_null_value_code=new_id_metadata.registry_identifiers.eudamed_srn_number_null_value_code,
            investigational_device_exemption_ide_number_null_value_code=(
                new_id_metadata.registry_identifiers.investigational_device_exemption_ide_number_null_value_code
            ),
            eu_pas_number_null_value_code=new_id_metadata.registry_identifiers.eu_pas_number_null_value_code,
        ),
    )

    study.edit_metadata(
        new_id_metadata=new_id_metadata,
        project_exists_callback=lambda _: True,
        new_high_level_study_design=new_high_level_study_design,
        study_type_exists_callback=lambda _: True,
        trial_type_exists_callback=lambda _: True,
        trial_intent_type_exists_callback=lambda _: True,
        trial_phase_exists_callback=lambda _: True,
        null_value_exists_callback=lambda _: True,
        new_study_population=new_study_population,
        therapeutic_area_exists_callback=lambda _: True,
        disease_condition_or_indication_exists_callback=lambda _: True,
        diagnosis_group_exists_callback=lambda _: True,
        sex_of_participants_exists_callback=lambda _: True,
        new_study_intervention=new_study_intervention,
        intervention_type_exists_callback=lambda _: True,
        control_type_exists_callback=lambda _: True,
        intervention_model_exists_callback=lambda _: True,
        trial_blinding_schema_exists_callback=lambda _: True,
        author_id=author_id,
    )


def prepare_random_study(
    generate_uid_callback: Callable[[], str],
    *,
    max_count: int = 100,
    condition: Callable[[StudyDefinitionAR], bool] = lambda _: True,
) -> StudyDefinitionAR:
    """
    Function prepares random Study for testing having (on average) 5 locked versions.
    One third chance of being in LOCKED state.
    One third of being DRAFT without any RELEASED version.
    One third of being DRAFT and having RELEASED version.
    :return: StudyDefinitionAR
    """

    def is_lockable(_: StudyDefinitionAR) -> bool:
        return _.current_metadata.id_metadata.study_id is not None

    count = 0
    while count < max_count:
        study = create_random_study(
            condition=is_lockable, generate_uid_callback=generate_uid_callback
        )
        while random.random() > 0.2:
            study.edit_metadata(
                study_title_exists_callback=lambda _, study_number: False,
                study_short_title_exists_callback=lambda _, study_number: False,
                new_study_description=StudyDescriptionVO.from_input_values(
                    study_title="new_study_title", study_short_title="study_short_title"
                ),
                author_id=random_str(),
            )
            study.lock(
                version_description=random_str(),
                author_id=random_str(),
            )
            study.unlock(random_str())
            make_random_study_metadata_edit(
                study,
                new_id_metadata_fixed_values={
                    "study_number": study.current_metadata.id_metadata.study_number
                },
                author_id=random_str(),
            )
        if random.random() < 0.667:
            if random.random() < 0.5:
                study.release(
                    change_description="making a release",
                    author_id=random_str(),
                )
                make_random_study_metadata_edit(
                    study,
                    new_id_metadata_fixed_values={
                        "study_number": study.current_metadata.id_metadata.study_number
                    },
                    author_id=random_str(),
                )
            else:
                study.edit_metadata(
                    study_title_exists_callback=lambda _, study_number: False,
                    study_short_title_exists_callback=lambda _, study_number: False,
                    new_study_description=StudyDescriptionVO.from_input_values(
                        study_title="new_study_title",
                        study_short_title="study_short_title",
                    ),
                    author_id=random_str(),
                )
                study.lock(
                    version_description=random_str(),
                    author_id=random_str(),
                )
        if condition(study):
            return study
        count += 1
    raise TimeoutError(
        f"Cannot find random data which satisfy given condition (after {count} tries)"
    )


def prepare_random_study_sequence(
    *,
    count: int,
    generate_uid_callback: Callable[[], str],
    max_count: int = 100,
    condition: Callable[[StudyDefinitionAR], bool] = lambda _: True,
) -> list[StudyDefinitionAR]:
    return [
        prepare_random_study(
            generate_uid_callback=generate_uid_callback,
            condition=condition,
            max_count=max_count,
        )
        for _ in range(0, count)
    ]


def _random_study_number() -> str:
    choice = [str(_) for _ in range(0, 10)]
    return (
        random.choice(choice)
        + random.choice(choice)
        + random.choice(choice)
        + random.choice(choice)
    )


class TestStudyDefinitionAR(unittest.TestCase):
    def test__study_ar_from_initial_values__success(self):
        counter = 0

        def generate_uid_callback() -> str:
            nonlocal counter
            counter = counter + 1
            return str(counter)

        # test data in form of tuples
        # (study_number, study_acronym, study_id_prefix, ct_gov_id, eudract_id, project_number)

        test_tuples = [
            ("0000", "study-acronym", "study-id", "proj_num", "desc1"),
            ("0000", None, None, None, None),
            (None, "study-acronym", None, "proj-num-2", "desc2"),
        ]

        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                # given
                study_id_metadata = StudyIdentificationMetadataVO.from_input_values(
                    study_number=test_tuple[0],
                    subpart_id=None,
                    study_acronym=test_tuple[1],
                    project_number=test_tuple[2],
                    description=test_tuple[4],
                    registry_identifiers=RegistryIdentifiersVO(
                        ct_gov_id=None,
                        eudract_id=None,
                        universal_trial_number_utn=None,
                        japanese_trial_registry_id_japic=None,
                        investigational_new_drug_application_number_ind=None,
                        ct_gov_id_null_value_code=None,
                        eudract_id_null_value_code=None,
                        universal_trial_number_utn_null_value_code=None,
                        japanese_trial_registry_id_japic_null_value_code=None,
                        investigational_new_drug_application_number_ind_null_value_code=None,
                        eu_trial_number=None,
                        eu_trial_number_null_value_code=None,
                        civ_id_sin_number=None,
                        civ_id_sin_number_null_value_code=None,
                        national_clinical_trial_number=None,
                        national_clinical_trial_number_null_value_code=None,
                        japanese_trial_registry_number_jrct=None,
                        japanese_trial_registry_number_jrct_null_value_code=None,
                        national_medical_products_administration_nmpa_number=None,
                        national_medical_products_administration_nmpa_number_null_value_code=None,
                        eudamed_srn_number=None,
                        eudamed_srn_number_null_value_code=None,
                        investigational_device_exemption_ide_number=None,
                        investigational_device_exemption_ide_number_null_value_code=None,
                        eu_pas_number=None,
                        eu_pas_number_null_value_code=None,
                    ),
                )
                start_timestamp = datetime.now(timezone.utc)

                # when
                author = random_str()
                study: StudyDefinitionAR = StudyDefinitionAR.from_initial_values(
                    generate_uid_callback=generate_uid_callback,
                    initial_id_metadata=study_id_metadata,
                    project_exists_callback=lambda _: True,
                    study_title_exists_callback=lambda _, study_number: False,
                    study_short_title_exists_callback=lambda _, study_number: False,
                    study_number_exists_callback=lambda x, y: False,
                    study_acronym_exists_callback=lambda x, y: False,
                    author_id=author,
                )

                # then
                end_timestamp = datetime.now(timezone.utc)
                self.assertGreaterEqual(
                    study.current_metadata.ver_metadata.version_timestamp,
                    start_timestamp,
                )
                self.assertLessEqual(
                    study.current_metadata.ver_metadata.version_timestamp, end_timestamp
                )

                # so timestamp is as expected
                expected_timestamp = (
                    study.current_metadata.ver_metadata.version_timestamp
                )
                expected_current_metadata = StudyMetadataVO(
                    id_metadata=StudyIdentificationMetadataVO(
                        _study_id_prefix=study_id_metadata.project_number,  # NOTE: not study_id_prefix
                        subpart_id=None,
                        project_number=study_id_metadata.project_number,
                        study_number=study_id_metadata.study_number,
                        study_acronym=study_id_metadata.study_acronym,
                        description=study_id_metadata.description,
                        registry_identifiers=RegistryIdentifiersVO(
                            ct_gov_id=study_id_metadata.registry_identifiers.ct_gov_id,
                            eudract_id=study_id_metadata.registry_identifiers.eudract_id,
                            universal_trial_number_utn=study_id_metadata.registry_identifiers.universal_trial_number_utn,
                            japanese_trial_registry_id_japic=study_id_metadata.registry_identifiers.japanese_trial_registry_id_japic,
                            investigational_new_drug_application_number_ind=(
                                study_id_metadata.registry_identifiers.investigational_new_drug_application_number_ind
                            ),
                            ct_gov_id_null_value_code=study_id_metadata.registry_identifiers.ct_gov_id_null_value_code,
                            eudract_id_null_value_code=study_id_metadata.registry_identifiers.eudract_id_null_value_code,
                            universal_trial_number_utn_null_value_code=(
                                study_id_metadata.registry_identifiers.universal_trial_number_utn_null_value_code
                            ),
                            japanese_trial_registry_id_japic_null_value_code=(
                                study_id_metadata.registry_identifiers.japanese_trial_registry_id_japic_null_value_code
                            ),
                            investigational_new_drug_application_number_ind_null_value_code=(
                                study_id_metadata.registry_identifiers.investigational_new_drug_application_number_ind_null_value_code
                            ),
                            eu_trial_number=study_id_metadata.registry_identifiers.eu_trial_number,
                            eu_trial_number_null_value_code=study_id_metadata.registry_identifiers.eu_trial_number_null_value_code,
                            civ_id_sin_number=study_id_metadata.registry_identifiers.civ_id_sin_number,
                            civ_id_sin_number_null_value_code=study_id_metadata.registry_identifiers.civ_id_sin_number_null_value_code,
                            national_clinical_trial_number=study_id_metadata.registry_identifiers.national_clinical_trial_number,
                            national_clinical_trial_number_null_value_code=(
                                study_id_metadata.registry_identifiers.national_clinical_trial_number_null_value_code
                            ),
                            japanese_trial_registry_number_jrct=study_id_metadata.registry_identifiers.japanese_trial_registry_number_jrct,
                            japanese_trial_registry_number_jrct_null_value_code=(
                                study_id_metadata.registry_identifiers.japanese_trial_registry_number_jrct_null_value_code
                            ),
                            national_medical_products_administration_nmpa_number=(
                                study_id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number
                            ),
                            national_medical_products_administration_nmpa_number_null_value_code=(
                                study_id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number_null_value_code
                            ),
                            eudamed_srn_number=study_id_metadata.registry_identifiers.eudamed_srn_number,
                            eudamed_srn_number_null_value_code=study_id_metadata.registry_identifiers.eudamed_srn_number_null_value_code,
                            investigational_device_exemption_ide_number=(
                                study_id_metadata.registry_identifiers.investigational_device_exemption_ide_number
                            ),
                            investigational_device_exemption_ide_number_null_value_code=(
                                study_id_metadata.registry_identifiers.investigational_device_exemption_ide_number_null_value_code
                            ),
                            eu_pas_number=study_id_metadata.registry_identifiers.eu_pas_number,
                            eu_pas_number_null_value_code=study_id_metadata.registry_identifiers.eu_pas_number_null_value_code,
                        ),
                    ),
                    high_level_study_design=HighLevelStudyDesignVO(
                        study_type_code=None,
                        study_stop_rules=None,
                        trial_type_codes=[],
                        is_adaptive_design=None,
                        trial_phase_code=None,
                        development_stage_code=None,
                        is_extension_trial=None,
                        study_type_null_value_code=None,
                        trial_type_null_value_code=None,
                        is_extension_trial_null_value_code=None,
                        trial_phase_null_value_code=None,
                        is_adaptive_design_null_value_code=None,
                        study_stop_rules_null_value_code=None,
                        confirmed_response_minimum_duration=None,
                        confirmed_response_minimum_duration_null_value_code=None,
                    ),
                    study_population=StudyPopulationVO(
                        therapeutic_area_codes=[],
                        therapeutic_area_null_value_code=None,
                        disease_condition_or_indication_codes=[],
                        disease_condition_or_indication_null_value_code=None,
                        diagnosis_group_codes=[],
                        diagnosis_group_null_value_code=None,
                        sex_of_participants_code=None,
                        sex_of_participants_null_value_code=None,
                        healthy_subject_indicator=None,
                        healthy_subject_indicator_null_value_code=None,
                        rare_disease_indicator=None,
                        rare_disease_indicator_null_value_code=None,
                        planned_minimum_age_of_subjects=None,
                        planned_minimum_age_of_subjects_null_value_code=None,
                        planned_maximum_age_of_subjects=None,
                        planned_maximum_age_of_subjects_null_value_code=None,
                        stable_disease_minimum_duration=None,
                        stable_disease_minimum_duration_null_value_code=None,
                        pediatric_study_indicator=None,
                        pediatric_study_indicator_null_value_code=None,
                        pediatric_postmarket_study_indicator=None,
                        pediatric_postmarket_study_indicator_null_value_code=None,
                        pediatric_investigation_plan_indicator=None,
                        pediatric_investigation_plan_indicator_null_value_code=None,
                        relapse_criteria=None,
                        relapse_criteria_null_value_code=None,
                        number_of_expected_subjects=None,
                        number_of_expected_subjects_null_value_code=None,
                    ),
                    study_intervention=StudyInterventionVO(
                        intervention_type_code=None,
                        intervention_type_null_value_code=None,
                        add_on_to_existing_treatments=None,
                        add_on_to_existing_treatments_null_value_code=None,
                        control_type_code=None,
                        control_type_null_value_code=None,
                        intervention_model_code=None,
                        intervention_model_null_value_code=None,
                        is_trial_randomised=None,
                        is_trial_randomised_null_value_code=None,
                        stratification_factor=None,
                        stratification_factor_null_value_code=None,
                        trial_blinding_schema_code=None,
                        trial_blinding_schema_null_value_code=None,
                        planned_study_length=None,
                        planned_study_length_null_value_code=None,
                        trial_intent_types_codes=[],
                        trial_intent_type_null_value_code=None,
                    ),
                    ver_metadata=StudyVersionMetadataVO(
                        study_status=StudyStatus.DRAFT,
                        version_number=None,
                        version_author=author,
                        version_timestamp=expected_timestamp,
                    ),
                    study_description=StudyDescriptionVO(
                        study_title=None, study_short_title=None
                    ),
                )

                self.assertIsInstance(study, StudyDefinitionAR)
                self.assertEqual(study.current_metadata, expected_current_metadata)
                self.assertEqual(study.uid, str(counter))
                self.assertIsNone(study.latest_locked_metadata)
                self.assertIsNone(study.latest_released_or_locked_metadata)

    def test__get_snapshot__results(self):
        for _ in range(0, 10):
            with self.subTest():
                # given
                study = prepare_random_study(generate_uid_callback=_test_uid_generator)

                # when
                study_snapshot = study.get_snapshot()

                # then
                # check id
                self.assertEqual(study_snapshot.uid, study.uid)

                self.assertEqual(
                    study_snapshot.study_status,
                    study.current_metadata.ver_metadata.study_status.value,
                )

                # check if study_snapshot.locked_metadata_versions corresponds to given study
                self.assertEqual(
                    len(study_snapshot.locked_metadata_versions),
                    len(study.get_all_locked_versions()),
                )
                for v_num in range(1, len(study_snapshot.locked_metadata_versions) + 1):
                    self.assertEqual(
                        study_snapshot.locked_metadata_versions[
                            v_num - 1
                        ].id_metadata.study_id_prefix,
                        study.get_specific_locked_metadata_version(
                            v_num
                        ).id_metadata.study_id_prefix,
                    )
                    self.assertEqual(
                        study_snapshot.locked_metadata_versions[
                            v_num - 1
                        ].id_metadata.study_number,
                        study.get_specific_locked_metadata_version(
                            v_num
                        ).id_metadata.study_number,
                    )
                    self.assertEqual(
                        study_snapshot.locked_metadata_versions[
                            v_num - 1
                        ].id_metadata.study_acronym,
                        study.get_specific_locked_metadata_version(
                            v_num
                        ).id_metadata.study_acronym,
                    )
                    self.assertEqual(
                        study_snapshot.locked_metadata_versions[
                            v_num - 1
                        ].id_metadata.project_number,
                        study.get_specific_locked_metadata_version(
                            v_num
                        ).id_metadata.project_number,
                    )

                if (
                    study.current_metadata.ver_metadata.study_status
                    == StudyStatus.DRAFT
                ):
                    # if given study in DRAFT state, check current metadata in snapshot
                    self.assertEqual(
                        study_snapshot.current_metadata.id_metadata.study_id_prefix,
                        study.current_metadata.id_metadata.study_id_prefix,
                    )
                    self.assertEqual(
                        study_snapshot.current_metadata.id_metadata.study_number,
                        study.current_metadata.id_metadata.study_number,
                    )
                    self.assertEqual(
                        study_snapshot.current_metadata.id_metadata.study_acronym,
                        study.current_metadata.id_metadata.study_acronym,
                    )
                    self.assertEqual(
                        study_snapshot.current_metadata.id_metadata.project_number,
                        study.current_metadata.id_metadata.project_number,
                    )

                    if study.latest_released_or_locked_metadata is None:
                        # there are no RELEASED nor LOCKED versions check if that properly reflected in snapshot
                        self.assertIsNone(study_snapshot.released_metadata)
                        self.assertEqual(
                            len(study_snapshot.locked_metadata_versions), 0
                        )
                    elif (
                        study.latest_released_or_locked_metadata.ver_metadata.study_status
                        == StudyStatus.RELEASED
                    ):
                        # if there is RELEASED version check if it's properly reflected in snapshot
                        self.assertEqual(
                            study_snapshot.released_metadata.id_metadata.study_id_prefix,
                            study.latest_released_or_locked_metadata.id_metadata.study_id_prefix,
                        )
                        self.assertEqual(
                            study_snapshot.released_metadata.id_metadata.study_number,
                            study.latest_released_or_locked_metadata.id_metadata.study_number,
                        )
                        self.assertEqual(
                            study_snapshot.released_metadata.id_metadata.study_acronym,
                            study.latest_released_or_locked_metadata.id_metadata.study_acronym,
                        )
                        self.assertEqual(
                            study_snapshot.released_metadata.id_metadata.project_number,
                            study.latest_released_or_locked_metadata.id_metadata.project_number,
                        )

    def test__study_ar_from_snapshot__results(self):
        for _ in range(0, 10):
            with self.subTest():
                # given
                original_study = prepare_random_study(
                    generate_uid_callback=_test_uid_generator
                )
                print(original_study)
                study_snapshot = original_study.get_snapshot()

                # when
                restored_study = StudyDefinitionAR.from_snapshot(study_snapshot)
                print(restored_study)
                # then
                self.assertEqual(restored_study, original_study)

    def test__release__result(self):
        for study in prepare_random_study_sequence(
            count=10,
            generate_uid_callback=_test_uid_generator,
            condition=lambda s: s.current_metadata.ver_metadata.study_status
            == StudyStatus.DRAFT,
        ):
            with self.subTest():
                # given
                given_study_metadata = study.current_metadata
                given_study_released_metadata = study.released_metadata
                given_study_latest_locked_metadata = study.latest_locked_metadata
                start_timestamp = datetime.now(timezone.utc)

                # when
                study.release(
                    change_description="making a release", author_id=random_str()
                )
                study_title = study.current_metadata.study_description.study_title
                study_short_title = (
                    study.current_metadata.study_description.study_short_title
                )

                # then
                end_timestamp = datetime.now(timezone.utc)
                self.assertGreaterEqual(
                    study.latest_released_or_locked_metadata.ver_metadata.version_timestamp,
                    start_timestamp,
                )
                self.assertLessEqual(
                    study.latest_released_or_locked_metadata.ver_metadata.version_timestamp,
                    end_timestamp,
                )

                # so the timestamp is as expected
                expected_released_timestamp = (
                    study.latest_released_or_locked_metadata.ver_metadata.version_timestamp
                )
                expected_released_description = (
                    study.latest_released_or_locked_metadata.ver_metadata.version_description
                )
                exp_released_ver_number: Decimal = (
                    given_study_released_metadata.ver_metadata.version_number
                    if given_study_released_metadata
                    else Decimal("0")
                )
                expected_released_metadata = StudyMetadataVO(
                    id_metadata=given_study_metadata.id_metadata,
                    high_level_study_design=given_study_metadata.high_level_study_design,
                    study_population=given_study_metadata.study_population,
                    study_intervention=given_study_metadata.study_intervention,
                    ver_metadata=StudyVersionMetadataVO(
                        study_status=StudyStatus.RELEASED,
                        version_timestamp=expected_released_timestamp,
                        version_description=expected_released_description,
                        version_author=study.released_metadata.ver_metadata.version_author,
                        version_number=exp_released_ver_number + Decimal("0.1"),
                    ),
                    study_description=StudyDescriptionVO(
                        study_title=study_title, study_short_title=study_short_title
                    ),
                )

                expected_current_metadata = StudyMetadataVO(
                    id_metadata=given_study_metadata.id_metadata,
                    high_level_study_design=given_study_metadata.high_level_study_design,
                    study_population=given_study_metadata.study_population,
                    study_intervention=given_study_metadata.study_intervention,
                    ver_metadata=StudyVersionMetadataVO(
                        study_status=StudyStatus.DRAFT,
                        version_timestamp=expected_released_timestamp,
                        version_author=study.current_metadata.ver_metadata.version_author,
                        version_number=given_study_metadata.ver_metadata.version_number,
                    ),
                    study_description=StudyDescriptionVO(
                        study_title=study_title, study_short_title=study_short_title
                    ),
                )
                self.assertEqual(
                    study.latest_released_or_locked_metadata, expected_released_metadata
                )
                self.assertEqual(study.current_metadata, expected_current_metadata)
                self.assertEqual(
                    study.latest_locked_metadata, given_study_latest_locked_metadata
                )

    def test__release__failure(self):
        for study in prepare_random_study_sequence(
            count=10,
            generate_uid_callback=_test_uid_generator,
            condition=lambda s: s.current_metadata.ver_metadata.study_status
            != StudyStatus.DRAFT,
        ):
            with self.subTest():
                # given
                assert (
                    study.current_metadata.ver_metadata.study_status
                    != StudyStatus.DRAFT
                )

                # then
                with self.assertRaises(exceptions.BusinessLogicException):
                    # when
                    study.release(
                        change_description="making a release", author_id=random_str()
                    )

    def test__lock__result(self):
        tested = False
        for study in prepare_random_study_sequence(
            count=10,
            generate_uid_callback=_test_uid_generator,
            condition=(
                lambda s: s.current_metadata.ver_metadata.study_status
                == StudyStatus.DRAFT
                and s.current_metadata.id_metadata.study_id is not None
            ),
        ):
            tested = True
            with self.subTest():
                # given
                given_study_metadata = study.current_metadata
                given_latest_locked_metadata = study.latest_locked_metadata
                start_timestamp = datetime.now(timezone.utc)
                version_author = random_str()
                version_info = random_str()
                study_title = "new_study_title"
                study_short_title = "study_short_title"
                # when
                study.edit_metadata(
                    study_title_exists_callback=lambda _, study_number: False,
                    study_short_title_exists_callback=lambda _, study_number: False,
                    new_study_description=StudyDescriptionVO.from_input_values(
                        study_title=study_title, study_short_title=study_short_title
                    ),
                    author_id=random_str(),
                )
                study.lock(
                    author_id=version_author,
                    version_description=version_info,
                )

                # then
                end_timestamp = datetime.now(timezone.utc)
                expected_version_number = (
                    given_latest_locked_metadata.ver_metadata.version_number + 1
                    if given_latest_locked_metadata is not None
                    and given_latest_locked_metadata.ver_metadata.version_number
                    is not None
                    else 1
                )

                self.assertGreaterEqual(
                    study.latest_released_or_locked_metadata.ver_metadata.version_timestamp,
                    start_timestamp,
                )
                self.assertLessEqual(
                    study.latest_released_or_locked_metadata.ver_metadata.version_timestamp,
                    end_timestamp,
                )

                expected_locked_metadata = StudyMetadataVO(
                    id_metadata=given_study_metadata.id_metadata,
                    high_level_study_design=given_study_metadata.high_level_study_design,
                    study_population=given_study_metadata.study_population,
                    study_intervention=given_study_metadata.study_intervention,
                    ver_metadata=StudyVersionMetadataVO(
                        study_status=StudyStatus.LOCKED,
                        version_number=expected_version_number,
                        version_timestamp=study.latest_released_or_locked_metadata.ver_metadata.version_timestamp,
                        version_author=version_author,
                        version_description=version_info,
                    ),
                    study_description=StudyDescriptionVO(
                        study_title=study_title, study_short_title=study_short_title
                    ),
                )

                self.assertEqual(
                    study.latest_released_or_locked_metadata, expected_locked_metadata
                )
                self.assertEqual(study.latest_locked_metadata, expected_locked_metadata)
                self.assertEqual(study.current_metadata, expected_locked_metadata)
        self.assertTrue(tested)

    def test__lock__failure(self):
        for study in prepare_random_study_sequence(
            count=10,
            generate_uid_callback=_test_uid_generator,
            condition=lambda s: s.current_metadata.ver_metadata.study_status
            != StudyStatus.DRAFT,
        ):
            with self.subTest():
                # given
                assert (
                    study.current_metadata.ver_metadata.study_status
                    != StudyStatus.DRAFT
                )

                # then
                with self.assertRaises(exceptions.BusinessLogicException):
                    # when
                    study.edit_metadata(
                        study_title_exists_callback=lambda _, study_number: False,
                        study_short_title_exists_callback=(
                            lambda _, study_number: False
                        ),
                        new_study_description=StudyDescriptionVO.from_input_values(
                            study_title="new_study_title",
                            study_short_title="study_short_title",
                        ),
                        author_id=random_str(),
                    )
                    study.lock(
                        version_description=random_str(),
                        author_id=random_str(),
                    )

    def test__unlock__result(self):
        for study in prepare_random_study_sequence(
            count=10,
            generate_uid_callback=_test_uid_generator,
            condition=lambda s: s.current_metadata.ver_metadata.study_status
            == StudyStatus.LOCKED,
        ):
            with self.subTest():
                author = random_str()
                # given
                given_study_metadata = study.current_metadata
                given_study_latest_locked_metadata = (
                    study.latest_released_or_locked_metadata
                )
                start_timestamp = datetime.now(timezone.utc)
                study_title = "new_study_title"
                study_short_title = "study_short_title"
                # when
                study.unlock(author)

                # then
                end_timestamp = datetime.now(timezone.utc)
                self.assertGreaterEqual(
                    study.current_metadata.ver_metadata.version_timestamp,
                    start_timestamp,
                )
                self.assertLessEqual(
                    study.current_metadata.ver_metadata.version_timestamp, end_timestamp
                )

                expected_current_metadata = StudyMetadataVO(
                    id_metadata=given_study_metadata.id_metadata,
                    high_level_study_design=given_study_metadata.high_level_study_design,
                    study_population=given_study_metadata.study_population,
                    study_intervention=given_study_metadata.study_intervention,
                    ver_metadata=StudyVersionMetadataVO(
                        study_status=StudyStatus.DRAFT,
                        version_number=None,
                        version_author=author,
                        # the last one is checked before so we assume it's the right one
                        version_timestamp=study.current_metadata.ver_metadata.version_timestamp,
                    ),
                    study_description=StudyDescriptionVO(
                        study_title=study_title, study_short_title=study_short_title
                    ),
                )
                self.assertEqual(study.current_metadata, expected_current_metadata)
                self.assertEqual(
                    study.latest_released_or_locked_metadata,
                    given_study_latest_locked_metadata,
                )
                self.assertEqual(
                    study.latest_locked_metadata, given_study_latest_locked_metadata
                )

    def test__unlock__failure(self):
        for study in prepare_random_study_sequence(
            count=10,
            generate_uid_callback=_test_uid_generator,
            condition=lambda s: s.current_metadata.ver_metadata.study_status
            != StudyStatus.LOCKED,
        ):
            with self.subTest():
                # given
                assert (
                    study.current_metadata.ver_metadata.study_status
                    != StudyStatus.LOCKED
                )

                # then
                with self.assertRaises(exceptions.BusinessLogicException):
                    # when
                    study.unlock(random_str())

    def test__edit_metadata__result(self):
        for study in prepare_random_study_sequence(
            count=10,
            generate_uid_callback=_test_uid_generator,
            condition=lambda s: s.current_metadata.ver_metadata.study_status
            == StudyStatus.DRAFT,
        ):
            with self.subTest():
                # given
                given_study_latest_released_or_locked_metadata = (
                    study.latest_released_or_locked_metadata
                )
                given_study_latest_locked_metadata = study.latest_locked_metadata
                new_id_metadata = StudyIdentificationMetadataVO.from_input_values(
                    study_number=study.current_metadata.id_metadata.study_number,
                    subpart_id=None,
                    study_acronym=random_str(),
                    description=random_str(),
                    registry_identifiers=RegistryIdentifiersVO(
                        ct_gov_id=random_str(),
                        eudract_id=random_str(),
                        universal_trial_number_utn=random_str(),
                        japanese_trial_registry_id_japic=random_str(),
                        investigational_new_drug_application_number_ind=random_str(),
                        eu_trial_number=random_str(),
                        civ_id_sin_number=random_str(),
                        national_clinical_trial_number=random_str(),
                        japanese_trial_registry_number_jrct=random_str(),
                        national_medical_products_administration_nmpa_number=random_str(),
                        eudamed_srn_number=random_str(),
                        investigational_device_exemption_ide_number=random_str(),
                        eu_pas_number=random_str(),
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
                        eu_pas_number_null_value_code=None,
                    ),
                    project_number=random_str(),
                )
                start_timestamp = datetime.now(timezone.utc)

                # when
                study.edit_metadata(
                    new_id_metadata=new_id_metadata,
                    project_exists_callback=lambda _: True,
                    author_id=random_str(),
                )

                # then
                end_timestamp = datetime.now(timezone.utc)
                expected_current_id_prefix = (
                    new_id_metadata.project_number
                    if study.latest_locked_metadata is None
                    else study.latest_locked_metadata.id_metadata.study_id_prefix
                )

                expected_current_id_metadata = StudyIdentificationMetadataVO(
                    project_number=new_id_metadata.project_number,
                    study_number=new_id_metadata.study_number,
                    subpart_id=None,
                    study_acronym=new_id_metadata.study_acronym,
                    description=new_id_metadata.description,
                    _study_id_prefix=expected_current_id_prefix,
                    registry_identifiers=RegistryIdentifiersVO(
                        ct_gov_id=new_id_metadata.registry_identifiers.ct_gov_id,
                        eudract_id=new_id_metadata.registry_identifiers.eudract_id,
                        universal_trial_number_utn=new_id_metadata.registry_identifiers.universal_trial_number_utn,
                        japanese_trial_registry_id_japic=new_id_metadata.registry_identifiers.japanese_trial_registry_id_japic,
                        investigational_new_drug_application_number_ind=(
                            new_id_metadata.registry_identifiers.investigational_new_drug_application_number_ind
                        ),
                        eu_trial_number=new_id_metadata.registry_identifiers.eu_trial_number,
                        civ_id_sin_number=new_id_metadata.registry_identifiers.civ_id_sin_number,
                        national_clinical_trial_number=new_id_metadata.registry_identifiers.national_clinical_trial_number,
                        japanese_trial_registry_number_jrct=new_id_metadata.registry_identifiers.japanese_trial_registry_number_jrct,
                        national_medical_products_administration_nmpa_number=(
                            new_id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number
                        ),
                        eudamed_srn_number=new_id_metadata.registry_identifiers.eudamed_srn_number,
                        investigational_device_exemption_ide_number=new_id_metadata.registry_identifiers.investigational_device_exemption_ide_number,
                        eu_pas_number=new_id_metadata.registry_identifiers.eu_pas_number,
                        ct_gov_id_null_value_code=new_id_metadata.registry_identifiers.ct_gov_id_null_value_code,
                        eudract_id_null_value_code=new_id_metadata.registry_identifiers.eudract_id_null_value_code,
                        universal_trial_number_utn_null_value_code=new_id_metadata.registry_identifiers.universal_trial_number_utn_null_value_code,
                        japanese_trial_registry_id_japic_null_value_code=(
                            new_id_metadata.registry_identifiers.japanese_trial_registry_id_japic_null_value_code
                        ),
                        investigational_new_drug_application_number_ind_null_value_code=(
                            new_id_metadata.registry_identifiers.investigational_new_drug_application_number_ind_null_value_code
                        ),
                        eu_trial_number_null_value_code=new_id_metadata.registry_identifiers.eu_trial_number_null_value_code,
                        civ_id_sin_number_null_value_code=new_id_metadata.registry_identifiers.civ_id_sin_number_null_value_code,
                        national_clinical_trial_number_null_value_code=(
                            new_id_metadata.registry_identifiers.national_clinical_trial_number_null_value_code
                        ),
                        japanese_trial_registry_number_jrct_null_value_code=(
                            new_id_metadata.registry_identifiers.japanese_trial_registry_number_jrct_null_value_code
                        ),
                        national_medical_products_administration_nmpa_number_null_value_code=(
                            new_id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number_null_value_code
                        ),
                        eudamed_srn_number_null_value_code=new_id_metadata.registry_identifiers.eudamed_srn_number_null_value_code,
                        investigational_device_exemption_ide_number_null_value_code=(
                            new_id_metadata.registry_identifiers.investigational_device_exemption_ide_number_null_value_code
                        ),
                        eu_pas_number_null_value_code=new_id_metadata.registry_identifiers.eu_pas_number_null_value_code,
                    ),
                )

                self.assertEqual(
                    study.current_metadata.id_metadata, expected_current_id_metadata
                )
                self.assertEqual(
                    study.current_metadata.ver_metadata.study_status, StudyStatus.DRAFT
                )
                self.assertGreaterEqual(
                    study.current_metadata.ver_metadata.version_timestamp,
                    start_timestamp,
                )
                self.assertLessEqual(
                    study.current_metadata.ver_metadata.version_timestamp, end_timestamp
                )
                self.assertEqual(
                    study.latest_released_or_locked_metadata,
                    given_study_latest_released_or_locked_metadata,
                )
                self.assertEqual(
                    study.latest_locked_metadata, given_study_latest_locked_metadata
                )

    def test__edit_metadata__non_draft_status__failure(self):
        for study in prepare_random_study_sequence(
            count=10,
            generate_uid_callback=_test_uid_generator,
            condition=lambda s: s.current_metadata.ver_metadata.study_status
            != StudyStatus.DRAFT,
        ):
            with self.subTest():
                # given
                new_id_metadata = StudyIdentificationMetadataVO.from_input_values(
                    study_number=study.current_metadata.id_metadata.study_number,
                    subpart_id=None,
                    study_acronym=random_str(),
                    project_number=study.current_metadata.id_metadata.project_number,
                    description=random_str(),
                    registry_identifiers=RegistryIdentifiersVO(
                        ct_gov_id=study.current_metadata.id_metadata.registry_identifiers.ct_gov_id,
                        eudract_id=study.current_metadata.id_metadata.registry_identifiers.eudract_id,
                        universal_trial_number_utn=study.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn,
                        japanese_trial_registry_id_japic=study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic,
                        investigational_new_drug_application_number_ind=(
                            study.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind
                        ),
                        eu_trial_number=study.current_metadata.id_metadata.registry_identifiers.eu_trial_number,
                        civ_id_sin_number=study.current_metadata.id_metadata.registry_identifiers.civ_id_sin_number,
                        national_clinical_trial_number=study.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number,
                        japanese_trial_registry_number_jrct=(
                            study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct
                        ),
                        national_medical_products_administration_nmpa_number=(
                            study.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number
                        ),
                        eudamed_srn_number=study.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number,
                        investigational_device_exemption_ide_number=(
                            study.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number
                        ),
                        eu_pas_number=study.current_metadata.id_metadata.registry_identifiers.eu_pas_number,
                        ct_gov_id_null_value_code=study.current_metadata.id_metadata.registry_identifiers.ct_gov_id_null_value_code,
                        eudract_id_null_value_code=study.current_metadata.id_metadata.registry_identifiers.eudract_id_null_value_code,
                        universal_trial_number_utn_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn_null_value_code
                        ),
                        japanese_trial_registry_id_japic_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic_null_value_code
                        ),
                        investigational_new_drug_application_number_ind_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind_null_value_code
                        ),
                        eu_trial_number_null_value_code=study.current_metadata.id_metadata.registry_identifiers.eu_trial_number_null_value_code,
                        civ_id_sin_number_null_value_code=study.current_metadata.id_metadata.registry_identifiers.civ_id_sin_number_null_value_code,
                        national_clinical_trial_number_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number_null_value_code
                        ),
                        japanese_trial_registry_number_jrct_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct_null_value_code
                        ),
                        national_medical_products_administration_nmpa_number_null_value_code=(
                            # pylint: disable=line-too-long
                            study.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number_null_value_code
                        ),
                        eudamed_srn_number_null_value_code=study.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number_null_value_code,
                        investigational_device_exemption_ide_number_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number_null_value_code
                        ),
                        eu_pas_number_null_value_code=study.current_metadata.id_metadata.registry_identifiers.eu_pas_number_null_value_code,
                    ),
                )

                # then
                with self.assertRaises(exceptions.BusinessLogicException):
                    # when
                    study.edit_metadata(
                        new_id_metadata=new_id_metadata,
                        project_exists_callback=lambda _: True,
                        author_id=random_str(),
                    )

    def test__edit_metadata__non_existent_project_num__failure(self):
        for study in prepare_random_study_sequence(
            count=10,
            generate_uid_callback=_test_uid_generator,
            condition=lambda s: s.current_metadata.ver_metadata.study_status
            == StudyStatus.DRAFT,
        ):
            with self.subTest():
                # given
                new_id_metadata = StudyIdentificationMetadataVO.from_input_values(
                    study_number=study.current_metadata.id_metadata.study_number,
                    subpart_id=None,
                    study_acronym=study.current_metadata.id_metadata.study_acronym,
                    description=study.current_metadata.id_metadata.description,
                    registry_identifiers=RegistryIdentifiersVO(
                        ct_gov_id=study.current_metadata.id_metadata.registry_identifiers.ct_gov_id,
                        eudract_id=study.current_metadata.id_metadata.registry_identifiers.eudract_id,
                        universal_trial_number_utn=study.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn,
                        japanese_trial_registry_id_japic=study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic,
                        investigational_new_drug_application_number_ind=(
                            study.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind
                        ),
                        eu_trial_number=study.current_metadata.id_metadata.registry_identifiers.eu_trial_number,
                        civ_id_sin_number=study.current_metadata.id_metadata.registry_identifiers.civ_id_sin_number,
                        national_clinical_trial_number=study.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number,
                        japanese_trial_registry_number_jrct=(
                            study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct
                        ),
                        national_medical_products_administration_nmpa_number=(
                            study.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number
                        ),
                        eudamed_srn_number=study.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number,
                        investigational_device_exemption_ide_number=(
                            study.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number
                        ),
                        eu_pas_number=study.current_metadata.id_metadata.registry_identifiers.eu_pas_number,
                        ct_gov_id_null_value_code=study.current_metadata.id_metadata.registry_identifiers.ct_gov_id_null_value_code,
                        eudract_id_null_value_code=study.current_metadata.id_metadata.registry_identifiers.eudract_id_null_value_code,
                        universal_trial_number_utn_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn_null_value_code
                        ),
                        japanese_trial_registry_id_japic_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic_null_value_code
                        ),
                        investigational_new_drug_application_number_ind_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind_null_value_code
                        ),
                        eu_trial_number_null_value_code=study.current_metadata.id_metadata.registry_identifiers.eu_trial_number_null_value_code,
                        civ_id_sin_number_null_value_code=study.current_metadata.id_metadata.registry_identifiers.civ_id_sin_number_null_value_code,
                        national_clinical_trial_number_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number_null_value_code
                        ),
                        japanese_trial_registry_number_jrct_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct_null_value_code
                        ),
                        national_medical_products_administration_nmpa_number_null_value_code=(
                            # pylint: disable=line-too-long
                            study.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number_null_value_code
                        ),
                        eudamed_srn_number_null_value_code=study.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number_null_value_code,
                        investigational_device_exemption_ide_number_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number_null_value_code
                        ),
                        eu_pas_number_null_value_code=study.current_metadata.id_metadata.registry_identifiers.eu_pas_number_null_value_code,
                    ),
                    project_number=random_str(),
                )

                # then
                with self.assertRaises(exceptions.BusinessLogicException):
                    # when
                    study.edit_metadata(
                        new_id_metadata=new_id_metadata,
                        project_exists_callback=lambda _: False,
                        author_id=random_str(),
                    )

    def test__mark_deleted__deleting_once_locked__failure(self):
        for study in prepare_random_study_sequence(
            count=10,
            generate_uid_callback=_test_uid_generator,
            condition=lambda s: s.latest_locked_metadata is not None,
        ):
            with self.subTest():
                # given
                assert study.latest_locked_metadata is not None

                # then
                with self.assertRaises(exceptions.BusinessLogicException):
                    # when
                    study.mark_deleted()

    def test__edit_id_metadata__changing_project_for_never_locked_study__results(self):
        for study in prepare_random_study_sequence(
            count=10,
            generate_uid_callback=_test_uid_generator,
            condition=(
                lambda s: s.latest_locked_metadata is None
                and s.current_metadata.ver_metadata.study_status == StudyStatus.DRAFT
            ),
        ):
            with self.subTest():
                # given
                new_id_metadata = StudyIdentificationMetadataVO.from_input_values(
                    study_number=study.current_metadata.id_metadata.study_number,
                    subpart_id=None,
                    study_acronym=study.current_metadata.id_metadata.study_acronym,
                    description=study.current_metadata.id_metadata.description,
                    registry_identifiers=RegistryIdentifiersVO(
                        ct_gov_id=study.current_metadata.id_metadata.registry_identifiers.ct_gov_id,
                        eudract_id=study.current_metadata.id_metadata.registry_identifiers.eudract_id,
                        universal_trial_number_utn=study.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn,
                        japanese_trial_registry_id_japic=study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic,
                        investigational_new_drug_application_number_ind=(
                            study.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind
                        ),
                        eu_trial_number=study.current_metadata.id_metadata.registry_identifiers.eu_trial_number,
                        civ_id_sin_number=study.current_metadata.id_metadata.registry_identifiers.civ_id_sin_number,
                        national_clinical_trial_number=study.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number,
                        japanese_trial_registry_number_jrct=(
                            study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct
                        ),
                        national_medical_products_administration_nmpa_number=(
                            study.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number
                        ),
                        eudamed_srn_number=study.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number,
                        investigational_device_exemption_ide_number=(
                            study.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number
                        ),
                        eu_pas_number=study.current_metadata.id_metadata.registry_identifiers.eu_pas_number,
                        ct_gov_id_null_value_code=study.current_metadata.id_metadata.registry_identifiers.ct_gov_id_null_value_code,
                        eudract_id_null_value_code=study.current_metadata.id_metadata.registry_identifiers.eudract_id_null_value_code,
                        universal_trial_number_utn_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn_null_value_code
                        ),
                        japanese_trial_registry_id_japic_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic_null_value_code
                        ),
                        investigational_new_drug_application_number_ind_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind_null_value_code
                        ),
                        eu_trial_number_null_value_code=study.current_metadata.id_metadata.registry_identifiers.eu_trial_number_null_value_code,
                        civ_id_sin_number_null_value_code=study.current_metadata.id_metadata.registry_identifiers.civ_id_sin_number_null_value_code,
                        national_clinical_trial_number_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number_null_value_code
                        ),
                        japanese_trial_registry_number_jrct_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct_null_value_code
                        ),
                        national_medical_products_administration_nmpa_number_null_value_code=(
                            # pylint: disable=line-too-long
                            study.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number_null_value_code
                        ),
                        eudamed_srn_number_null_value_code=study.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number_null_value_code,
                        investigational_device_exemption_ide_number_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number_null_value_code
                        ),
                        eu_pas_number_null_value_code=study.current_metadata.id_metadata.registry_identifiers.eu_pas_number_null_value_code,
                    ),
                    project_number=random_str(),
                )

                # when
                study.edit_metadata(
                    new_id_metadata=new_id_metadata,
                    project_exists_callback=lambda _: True,
                    author_id=random_str(),
                )

                # then
                expected_current_id_metadata = StudyIdentificationMetadataVO(
                    study_number=new_id_metadata.study_number,
                    subpart_id=None,
                    study_acronym=new_id_metadata.study_acronym,
                    _study_id_prefix=new_id_metadata.project_number,  # same as project number
                    description=new_id_metadata.description,
                    registry_identifiers=RegistryIdentifiersVO(
                        ct_gov_id=new_id_metadata.registry_identifiers.ct_gov_id,
                        eudract_id=new_id_metadata.registry_identifiers.eudract_id,
                        universal_trial_number_utn=new_id_metadata.registry_identifiers.universal_trial_number_utn,
                        japanese_trial_registry_id_japic=new_id_metadata.registry_identifiers.japanese_trial_registry_id_japic,
                        investigational_new_drug_application_number_ind=(
                            new_id_metadata.registry_identifiers.investigational_new_drug_application_number_ind
                        ),
                        eu_trial_number=new_id_metadata.registry_identifiers.eu_trial_number,
                        civ_id_sin_number=new_id_metadata.registry_identifiers.civ_id_sin_number,
                        national_clinical_trial_number=new_id_metadata.registry_identifiers.national_clinical_trial_number,
                        japanese_trial_registry_number_jrct=(
                            new_id_metadata.registry_identifiers.japanese_trial_registry_number_jrct
                        ),
                        national_medical_products_administration_nmpa_number=(
                            new_id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number
                        ),
                        eudamed_srn_number=new_id_metadata.registry_identifiers.eudamed_srn_number,
                        investigational_device_exemption_ide_number=(
                            new_id_metadata.registry_identifiers.investigational_device_exemption_ide_number
                        ),
                        eu_pas_number=new_id_metadata.registry_identifiers.eu_pas_number,
                        ct_gov_id_null_value_code=new_id_metadata.registry_identifiers.ct_gov_id_null_value_code,
                        eudract_id_null_value_code=new_id_metadata.registry_identifiers.eudract_id_null_value_code,
                        universal_trial_number_utn_null_value_code=(
                            new_id_metadata.registry_identifiers.universal_trial_number_utn_null_value_code
                        ),
                        japanese_trial_registry_id_japic_null_value_code=(
                            new_id_metadata.registry_identifiers.japanese_trial_registry_id_japic_null_value_code
                        ),
                        investigational_new_drug_application_number_ind_null_value_code=(
                            new_id_metadata.registry_identifiers.investigational_new_drug_application_number_ind_null_value_code
                        ),
                        eu_trial_number_null_value_code=new_id_metadata.registry_identifiers.eu_trial_number_null_value_code,
                        civ_id_sin_number_null_value_code=new_id_metadata.registry_identifiers.civ_id_sin_number_null_value_code,
                        national_clinical_trial_number_null_value_code=(
                            new_id_metadata.registry_identifiers.national_clinical_trial_number_null_value_code
                        ),
                        japanese_trial_registry_number_jrct_null_value_code=(
                            new_id_metadata.registry_identifiers.japanese_trial_registry_number_jrct_null_value_code
                        ),
                        national_medical_products_administration_nmpa_number_null_value_code=(
                            new_id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number_null_value_code
                        ),
                        eudamed_srn_number_null_value_code=new_id_metadata.registry_identifiers.eudamed_srn_number_null_value_code,
                        investigational_device_exemption_ide_number_null_value_code=(
                            new_id_metadata.registry_identifiers.investigational_device_exemption_ide_number_null_value_code
                        ),
                        eu_pas_number_null_value_code=new_id_metadata.registry_identifiers.eu_pas_number_null_value_code,
                    ),
                    project_number=new_id_metadata.project_number,
                )

                self.assertEqual(
                    study.current_metadata.id_metadata, expected_current_id_metadata
                )

    def test__edit_id_metadata__changing_project_for_once_locked_study__results(self):
        for study in prepare_random_study_sequence(
            count=10,
            generate_uid_callback=_test_uid_generator,
            condition=(
                lambda s: s.latest_locked_metadata is not None
                and s.current_metadata.ver_metadata.study_status == StudyStatus.DRAFT
            ),
        ):
            with self.subTest():
                # given
                new_id_metadata = StudyIdentificationMetadataVO.from_input_values(
                    study_number=study.current_metadata.id_metadata.study_number,
                    subpart_id=None,
                    study_acronym=study.current_metadata.id_metadata.study_acronym,
                    description=study.current_metadata.id_metadata.description,
                    registry_identifiers=RegistryIdentifiersVO(
                        ct_gov_id=study.current_metadata.id_metadata.registry_identifiers.ct_gov_id,
                        eudract_id=study.current_metadata.id_metadata.registry_identifiers.eudract_id,
                        universal_trial_number_utn=study.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn,
                        japanese_trial_registry_id_japic=study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic,
                        investigational_new_drug_application_number_ind=(
                            study.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind
                        ),
                        eu_trial_number=study.current_metadata.id_metadata.registry_identifiers.eu_trial_number,
                        civ_id_sin_number=study.current_metadata.id_metadata.registry_identifiers.civ_id_sin_number,
                        national_clinical_trial_number=study.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number,
                        japanese_trial_registry_number_jrct=(
                            study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct
                        ),
                        national_medical_products_administration_nmpa_number=(
                            study.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number
                        ),
                        eudamed_srn_number=study.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number,
                        investigational_device_exemption_ide_number=(
                            study.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number
                        ),
                        eu_pas_number=study.current_metadata.id_metadata.registry_identifiers.eu_pas_number,
                        ct_gov_id_null_value_code=study.current_metadata.id_metadata.registry_identifiers.ct_gov_id_null_value_code,
                        eudract_id_null_value_code=study.current_metadata.id_metadata.registry_identifiers.eudract_id_null_value_code,
                        universal_trial_number_utn_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn_null_value_code
                        ),
                        japanese_trial_registry_id_japic_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic_null_value_code
                        ),
                        investigational_new_drug_application_number_ind_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind_null_value_code
                        ),
                        eu_trial_number_null_value_code=study.current_metadata.id_metadata.registry_identifiers.eu_trial_number_null_value_code,
                        civ_id_sin_number_null_value_code=study.current_metadata.id_metadata.registry_identifiers.civ_id_sin_number_null_value_code,
                        national_clinical_trial_number_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number_null_value_code
                        ),
                        japanese_trial_registry_number_jrct_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct_null_value_code
                        ),
                        national_medical_products_administration_nmpa_number_null_value_code=(
                            # pylint: disable=line-too-long
                            study.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number_null_value_code
                        ),
                        eudamed_srn_number_null_value_code=study.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number_null_value_code,
                        investigational_device_exemption_ide_number_null_value_code=(
                            study.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number_null_value_code
                        ),
                        eu_pas_number_null_value_code=study.current_metadata.id_metadata.registry_identifiers.eu_pas_number_null_value_code,
                    ),
                    project_number=random_str(),
                )

                # when
                study.edit_metadata(
                    new_id_metadata=new_id_metadata,
                    project_exists_callback=lambda _: True,
                    author_id=random_str(),
                )

                # then
                expected_current_id_metadata = StudyIdentificationMetadataVO(
                    study_number=new_id_metadata.study_number,
                    subpart_id=None,
                    study_acronym=new_id_metadata.study_acronym,
                    _study_id_prefix=study.latest_locked_metadata.id_metadata.study_id_prefix,  # as in latest locked
                    description=new_id_metadata.description,
                    registry_identifiers=RegistryIdentifiersVO(
                        ct_gov_id=study.latest_locked_metadata.id_metadata.registry_identifiers.ct_gov_id,
                        eudract_id=study.latest_locked_metadata.id_metadata.registry_identifiers.eudract_id,
                        universal_trial_number_utn=study.latest_locked_metadata.id_metadata.registry_identifiers.universal_trial_number_utn,
                        japanese_trial_registry_id_japic=(
                            study.latest_locked_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic
                        ),
                        investigational_new_drug_application_number_ind=(
                            study.latest_locked_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind
                        ),
                        eu_trial_number=study.latest_locked_metadata.id_metadata.registry_identifiers.eu_trial_number,
                        civ_id_sin_number=study.latest_locked_metadata.id_metadata.registry_identifiers.civ_id_sin_number,
                        national_clinical_trial_number=study.latest_locked_metadata.id_metadata.registry_identifiers.national_clinical_trial_number,
                        japanese_trial_registry_number_jrct=(
                            study.latest_locked_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct
                        ),
                        national_medical_products_administration_nmpa_number=(
                            study.latest_locked_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number
                        ),
                        eudamed_srn_number=study.latest_locked_metadata.id_metadata.registry_identifiers.eudamed_srn_number,
                        investigational_device_exemption_ide_number=(
                            study.latest_locked_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number
                        ),
                        eu_pas_number=study.latest_locked_metadata.id_metadata.registry_identifiers.eu_pas_number,
                        ct_gov_id_null_value_code=study.latest_locked_metadata.id_metadata.registry_identifiers.ct_gov_id_null_value_code,
                        eudract_id_null_value_code=study.latest_locked_metadata.id_metadata.registry_identifiers.eudract_id_null_value_code,
                        universal_trial_number_utn_null_value_code=(
                            study.latest_locked_metadata.id_metadata.registry_identifiers.universal_trial_number_utn_null_value_code
                        ),
                        japanese_trial_registry_id_japic_null_value_code=(
                            study.latest_locked_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic_null_value_code
                        ),
                        investigational_new_drug_application_number_ind_null_value_code=(
                            # pylint: disable=line-too-long
                            study.latest_locked_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind_null_value_code
                        ),
                        eu_trial_number_null_value_code=study.latest_locked_metadata.id_metadata.registry_identifiers.eu_trial_number_null_value_code,
                        civ_id_sin_number_null_value_code=(
                            study.latest_locked_metadata.id_metadata.registry_identifiers.civ_id_sin_number_null_value_code
                        ),
                        national_clinical_trial_number_null_value_code=(
                            study.latest_locked_metadata.id_metadata.registry_identifiers.national_clinical_trial_number_null_value_code
                        ),
                        japanese_trial_registry_number_jrct_null_value_code=(
                            study.latest_locked_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct_null_value_code
                        ),
                        national_medical_products_administration_nmpa_number_null_value_code=(
                            # pylint: disable=line-too-long
                            study.latest_locked_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number_null_value_code
                        ),
                        eudamed_srn_number_null_value_code=(
                            study.latest_locked_metadata.id_metadata.registry_identifiers.eudamed_srn_number_null_value_code
                        ),
                        investigational_device_exemption_ide_number_null_value_code=(
                            study.latest_locked_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number_null_value_code
                        ),
                        eu_pas_number_null_value_code=study.latest_locked_metadata.id_metadata.registry_identifiers.eu_pas_number_null_value_code,
                    ),
                    project_number=new_id_metadata.project_number,
                )

                self.assertEqual(
                    study.current_metadata.id_metadata, expected_current_id_metadata
                )

    def test__study_ar_from_initial_values__failure(self):
        counter = 0

        def generate_uid_callback() -> str:
            nonlocal counter
            counter = counter + 1
            return str(counter)

        # test data in form of tuples
        # (study_number, study_acronym, ct_gov_id, eudract_id, project_number)

        test_tuples = [
            (None, None, "existing-proj-num", "desc1"),
            (None, None, "existing-proj-num", "desc1"),
            ("study-number", "study-acronym", "non-existent-proj-num", "desc3"),
        ]

        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                # given
                study_id_metadata = StudyIdentificationMetadataVO.from_input_values(
                    study_number=test_tuple[0],
                    subpart_id=None,
                    study_acronym=test_tuple[1],
                    description=test_tuple[3],
                    registry_identifiers=RegistryIdentifiersVO(
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
                        eu_pas_number=None,
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
                        eu_pas_number_null_value_code=None,
                    ),
                    project_number=test_tuple[2],
                )

                # then
                with self.assertRaises(exceptions.ValidationException):
                    # when
                    StudyDefinitionAR.from_initial_values(
                        generate_uid_callback=generate_uid_callback,
                        initial_id_metadata=study_id_metadata,
                        project_exists_callback=(
                            lambda proj_num: proj_num == "existing-proj-num"
                        ),
                        author_id=random_str(),
                    )
