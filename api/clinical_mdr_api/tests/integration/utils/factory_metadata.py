from clinical_mdr_api.domains.study_definition_aggregates.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    HighLevelStudyDesignVO,
    StudyInterventionVO,
    StudyPopulationVO,
    StudyStatus,
    StudyVersionMetadataVO,
)
from clinical_mdr_api.models.study_selections.study import (
    HighLevelStudyDesignJsonModel,
    RegistryIdentifiersJsonModel,
    StudyDescriptionJsonModel,
    StudyIdentificationMetadataJsonModel,
    StudyInterventionJsonModel,
    StudyMetadataJsonModel,
    StudyPatchRequestJsonModel,
    StudyPopulationJsonModel,
    StudyVersionMetadataJsonModel,
)
from clinical_mdr_api.services.studies.study import StudyService


def input_metadata_in_study(study_uid):
    study_service = StudyService()
    study_service.patch(
        uid=study_uid,
        dry=False,
        study_patch_request=generate_study_patch_request(),
    )


def generate_description_json_model() -> StudyDescriptionJsonModel:
    return StudyDescriptionJsonModel(
        study_title="Some Study Title for Testing",
        study_short_title="Some Study Short Title for Testing",
    )


def generate_registry_identifiers_json_model() -> RegistryIdentifiersJsonModel:
    return RegistryIdentifiersJsonModel(
        ct_gov_id="some ct gov id",
        ct_gov_id_null_value_code=None,
        eudract_id="some eudtact id",
        eudract_id_null_value_code=None,
        universal_trial_number_utn="some utn id",
        universal_trial_number_utn_null_value_code=None,
        japanese_trial_registry_id_japic="some japic id",
        japanese_trial_registry_id_japic_null_value_code=None,
        investigational_new_drug_application_number_ind="some ind id",
        investigational_new_drug_application_number_ind_null_value_code=None,
        eu_trial_number="some etn",
        eu_trial_number_null_value_code=None,
        civ_id_sin_number="some cisn",
        civ_id_sin_number_null_value_code=None,
        national_clinical_trial_number="some nctn",
        national_clinical_trial_number_null_value_code=None,
        japanese_trial_registry_number_jrct="some jrct",
        japanese_trial_registry_number_jrct_null_value_code=None,
        national_medical_products_administration_nmpa_number="some nmpa",
        national_medical_products_administration_nmpa_number_null_value_code=None,
        eudamed_srn_number="some esn",
        eudamed_srn_number_null_value_code=None,
        investigational_device_exemption_ide_number="some ide",
        investigational_device_exemption_ide_number_null_value_code=None,
        eu_pas_number="some eupn",
        eu_pas_number_null_value_code=None,
    )


def generate_identification_metadata_json_model() -> (
    StudyIdentificationMetadataJsonModel
):
    return StudyIdentificationMetadataJsonModel(
        registry_identifiers=generate_registry_identifiers_json_model()
    )


def generate_ver_metadata_json_model() -> StudyVersionMetadataJsonModel:
    result = StudyVersionMetadataVO(study_status=StudyStatus.DRAFT)
    return StudyVersionMetadataJsonModel.from_study_version_metadata_vo(result)


def generate_high_level_study_design_json_model() -> HighLevelStudyDesignJsonModel:
    return HighLevelStudyDesignJsonModel(
        study_type_code=None,
        study_type_null_value_code=None,
        trial_type_codes=None,
        trial_type_null_value_code=None,
        trial_phase_code=None,
        trial_phase_null_value_code=None,
        development_stage_code=None,
        is_extension_trial=False,
        is_extension_trial_null_value_code=None,
        is_adaptive_design=False,
        is_adaptive_design_null_value_code=None,
        study_stop_rules="some stop rule",
        study_stop_rules_null_value_code=None,
        confirmed_response_minimum_duration=None,
        confirmed_response_minimum_duration_null_value_code=None,
        post_auth_indicator=True,
        post_auth_indicator_null_value_code=None,
    )


def generate_study_intervention_json_model() -> StudyInterventionJsonModel:
    return StudyInterventionJsonModel(
        intervention_type_code=None,
        intervention_type_null_value_code=None,
        add_on_to_existing_treatments=False,
        add_on_to_existing_treatments_null_value_code=None,
        control_type_code=None,
        control_type_null_value_code=None,
        intervention_model_code=None,
        intervention_model_null_value_code=None,
        is_trial_randomised=True,
        is_trial_randomised_null_value_code=None,
        stratification_factor="Some stratification factors",
        stratification_factor_null_value_code=None,
        trial_blinding_schema_code=None,
        trial_blinding_schema_null_value_code=None,
        planned_study_length=None,
        planned_study_length_null_value_code=None,
        trial_intent_types_codes=None,
        trial_intent_types_null_value_code=None,
    )


def generate_study_population_json_model() -> StudyPopulationJsonModel:
    return StudyPopulationJsonModel(
        therapeutic_area_codes=None,
        therapeutic_area_null_value_code=None,
        disease_condition_or_indication_codes=None,
        disease_condition_or_indication_null_value_code=None,
        diagnosis_group_codes=None,
        diagnosis_group_null_value_code=None,
        sex_of_participants_code=None,
        sex_of_participants_null_value_code=None,
        rare_disease_indicator=None,
        rare_disease_indicator_null_value_code=None,
        healthy_subject_indicator=None,
        healthy_subject_indicator_null_value_code=None,
        planned_minimum_age_of_subjects=None,
        planned_minimum_age_of_subjects_null_value_code=None,
        planned_maximum_age_of_subjects=None,
        planned_maximum_age_of_subjects_null_value_code=None,
        stable_disease_minimum_duration=None,
        stable_disease_minimum_duration_null_value_code=None,
        pediatric_study_indicator=None,
        pediatric_study_indicator_null_value_code=None,
        pediatric_postmarket_study_indicator=False,
        pediatric_postmarket_study_indicator_null_value_code=None,
        pediatric_investigation_plan_indicator=True,
        pediatric_investigation_plan_indicator_null_value_code=None,
        relapse_criteria="some criteria",
        relapse_criteria_null_value_code=None,
    )


def generate_study_metadata() -> StudyMetadataJsonModel:
    return StudyMetadataJsonModel(
        study_description=generate_description_json_model(),
        identification_metadata=generate_identification_metadata_json_model(),
        version_metadata=generate_ver_metadata_json_model(),
        high_level_study_design=generate_high_level_study_design_json_model(),
        study_intervention=generate_study_intervention_json_model(),
        study_population=generate_study_population_json_model(),
    )


def generate_study_patch_request() -> StudyPatchRequestJsonModel:
    return StudyPatchRequestJsonModel(current_metadata=generate_study_metadata())


def registry_identifiers_json_model_to_vo(
    json_model: (
        RegistryIdentifiersJsonModel | None
    ) = generate_registry_identifiers_json_model(),
):
    return RegistryIdentifiersVO.from_input_values(
        ct_gov_id=json_model.ct_gov_id,
        ct_gov_id_null_value_code=json_model.ct_gov_id_null_value_code,  # type: ignore[arg-type]
        eudract_id=json_model.eudract_id,
        eudract_id_null_value_code=json_model.eudract_id_null_value_code,  # type: ignore[arg-type]
        universal_trial_number_utn=json_model.universal_trial_number_utn,
        universal_trial_number_utn_null_value_code=json_model.universal_trial_number_utn_null_value_code,  # type: ignore[arg-type]
        japanese_trial_registry_id_japic=json_model.japanese_trial_registry_id_japic,
        japanese_trial_registry_id_japic_null_value_code=json_model.japanese_trial_registry_id_japic_null_value_code,  # type: ignore[arg-type]
        investigational_new_drug_application_number_ind=json_model.investigational_new_drug_application_number_ind,
        investigational_new_drug_application_number_ind_null_value_code=json_model.investigational_new_drug_application_number_ind_null_value_code,  # type: ignore[arg-type]
        eu_trial_number=json_model.eu_trial_number,
        eu_trial_number_null_value_code=json_model.eu_trial_number_null_value_code,  # type: ignore[arg-type]
        civ_id_sin_number=json_model.civ_id_sin_number,
        civ_id_sin_number_null_value_code=json_model.civ_id_sin_number_null_value_code,  # type: ignore[arg-type]
        national_clinical_trial_number=json_model.national_clinical_trial_number,
        national_clinical_trial_number_null_value_code=json_model.national_clinical_trial_number_null_value_code,  # type: ignore[arg-type]
        japanese_trial_registry_number_jrct=json_model.japanese_trial_registry_number_jrct,
        japanese_trial_registry_number_jrct_null_value_code=json_model.japanese_trial_registry_number_jrct_null_value_code,  # type: ignore[arg-type]
        national_medical_products_administration_nmpa_number=json_model.national_medical_products_administration_nmpa_number,
        national_medical_products_administration_nmpa_number_null_value_code=(
            json_model.national_medical_products_administration_nmpa_number_null_value_code  # type: ignore[arg-type]
        ),
        eudamed_srn_number=json_model.eudamed_srn_number,
        eudamed_srn_number_null_value_code=json_model.eudamed_srn_number_null_value_code,  # type: ignore[arg-type]
        investigational_device_exemption_ide_number=json_model.investigational_device_exemption_ide_number,
        investigational_device_exemption_ide_number_null_value_code=json_model.investigational_device_exemption_ide_number_null_value_code,  # type: ignore[arg-type]
        eu_pas_number=json_model.eu_pas_number,
        eu_pas_number_null_value_code=json_model.eu_pas_number_null_value_code,  # type: ignore[arg-type]
    )


def high_level_study_design_json_model_to_vo(
    json_model: (
        HighLevelStudyDesignJsonModel | None
    ) = generate_high_level_study_design_json_model(),
):
    return HighLevelStudyDesignVO.from_input_values(
        study_type_code=json_model.study_type_code,  # type: ignore[arg-type]
        study_type_null_value_code=json_model.study_type_null_value_code,  # type: ignore[arg-type]
        trial_type_codes=json_model.trial_type_codes,  # type: ignore[arg-type]
        trial_type_null_value_code=json_model.trial_type_null_value_code,  # type: ignore[arg-type]
        trial_phase_code=json_model.trial_phase_code,  # type: ignore[arg-type]
        trial_phase_null_value_code=json_model.trial_phase_null_value_code,  # type: ignore[arg-type]
        development_stage_code=json_model.development_stage_code,  # type: ignore[arg-type]
        is_extension_trial=json_model.is_extension_trial,
        is_extension_trial_null_value_code=json_model.is_extension_trial_null_value_code,  # type: ignore[arg-type]
        is_adaptive_design=json_model.is_adaptive_design,
        is_adaptive_design_null_value_code=json_model.is_adaptive_design_null_value_code,  # type: ignore[arg-type]
        study_stop_rules=json_model.study_stop_rules,
        study_stop_rules_null_value_code=json_model.study_stop_rules_null_value_code,  # type: ignore[arg-type]
        confirmed_response_minimum_duration=json_model.confirmed_response_minimum_duration,  # type: ignore[arg-type]
        confirmed_response_minimum_duration_null_value_code=json_model.confirmed_response_minimum_duration_null_value_code,  # type: ignore[arg-type]
        post_auth_indicator=json_model.post_auth_indicator,
        post_auth_indicator_null_value_code=json_model.post_auth_indicator_null_value_code,  # type: ignore[arg-type]
    )


def study_population_json_model_to_vo(
    json_model: (
        StudyPopulationJsonModel | None
    ) = generate_study_population_json_model(),
):
    return StudyPopulationVO.from_input_values(
        therapeutic_area_codes=json_model.therapeutic_area_codes,  # type: ignore[arg-type]
        therapeutic_area_null_value_code=json_model.therapeutic_area_null_value_code,  # type: ignore[arg-type]
        disease_condition_or_indication_codes=json_model.disease_condition_or_indication_codes,  # type: ignore[arg-type]
        disease_condition_or_indication_null_value_code=json_model.disease_condition_or_indication_null_value_code,  # type: ignore[arg-type]
        diagnosis_group_codes=json_model.diagnosis_group_codes,  # type: ignore[arg-type]
        diagnosis_group_null_value_code=json_model.diagnosis_group_null_value_code,  # type: ignore[arg-type]
        sex_of_participants_code=json_model.sex_of_participants_code,  # type: ignore[arg-type]
        sex_of_participants_null_value_code=json_model.sex_of_participants_null_value_code,  # type: ignore[arg-type]
        rare_disease_indicator=json_model.rare_disease_indicator,
        rare_disease_indicator_null_value_code=json_model.rare_disease_indicator_null_value_code,  # type: ignore[arg-type]
        healthy_subject_indicator=json_model.healthy_subject_indicator,
        healthy_subject_indicator_null_value_code=json_model.healthy_subject_indicator_null_value_code,  # type: ignore[arg-type]
        planned_minimum_age_of_subjects=json_model.planned_minimum_age_of_subjects,  # type: ignore[arg-type]
        planned_minimum_age_of_subjects_null_value_code=json_model.planned_minimum_age_of_subjects_null_value_code,  # type: ignore[arg-type]
        planned_maximum_age_of_subjects=json_model.planned_maximum_age_of_subjects,  # type: ignore[arg-type]
        planned_maximum_age_of_subjects_null_value_code=json_model.planned_maximum_age_of_subjects_null_value_code,  # type: ignore[arg-type]
        stable_disease_minimum_duration=json_model.stable_disease_minimum_duration,  # type: ignore[arg-type]
        stable_disease_minimum_duration_null_value_code=json_model.stable_disease_minimum_duration_null_value_code,  # type: ignore[arg-type]
        pediatric_study_indicator=json_model.pediatric_study_indicator,
        pediatric_study_indicator_null_value_code=json_model.pediatric_study_indicator_null_value_code,  # type: ignore[arg-type]
        pediatric_postmarket_study_indicator=json_model.pediatric_postmarket_study_indicator,
        pediatric_postmarket_study_indicator_null_value_code=json_model.pediatric_postmarket_study_indicator_null_value_code,  # type: ignore[arg-type]
        pediatric_investigation_plan_indicator=json_model.pediatric_investigation_plan_indicator,
        pediatric_investigation_plan_indicator_null_value_code=json_model.pediatric_investigation_plan_indicator_null_value_code,  # type: ignore[arg-type]
        relapse_criteria=json_model.relapse_criteria,
        relapse_criteria_null_value_code=json_model.relapse_criteria_null_value_code,  # type: ignore[arg-type]
        number_of_expected_subjects=json_model.number_of_expected_subjects,
        number_of_expected_subjects_null_value_code=json_model.number_of_expected_subjects_null_value_code,  # type: ignore[arg-type]
    )


def study_intervention_json_model_to_vo(
    json_model: (
        StudyInterventionJsonModel | None
    ) = generate_study_intervention_json_model(),
):
    return StudyInterventionVO.from_input_values(
        intervention_type_code=json_model.intervention_type_code,  # type: ignore[arg-type]
        intervention_type_null_value_code=json_model.intervention_type_null_value_code,  # type: ignore[arg-type]
        add_on_to_existing_treatments=json_model.add_on_to_existing_treatments,
        add_on_to_existing_treatments_null_value_code=json_model.add_on_to_existing_treatments_null_value_code,  # type: ignore[arg-type]
        control_type_code=json_model.control_type_code,  # type: ignore[arg-type]
        control_type_null_value_code=json_model.control_type_null_value_code,  # type: ignore[arg-type]
        intervention_model_code=json_model.intervention_model_code,  # type: ignore[arg-type]
        intervention_model_null_value_code=json_model.intervention_model_null_value_code,  # type: ignore[arg-type]
        trial_intent_types_codes=json_model.trial_intent_types_codes,  # type: ignore[arg-type]
        trial_intent_type_null_value_code=json_model.trial_intent_types_null_value_code,  # type: ignore[arg-type]
        is_trial_randomised=json_model.is_trial_randomised,
        is_trial_randomised_null_value_code=json_model.is_trial_randomised_null_value_code,  # type: ignore[arg-type]
        stratification_factor=json_model.stratification_factor,
        stratification_factor_null_value_code=json_model.stratification_factor_null_value_code,  # type: ignore[arg-type]
        trial_blinding_schema_code=json_model.trial_blinding_schema_code,  # type: ignore[arg-type]
        trial_blinding_schema_null_value_code=json_model.trial_blinding_schema_null_value_code,  # type: ignore[arg-type]
        planned_study_length=json_model.planned_study_length,  # type: ignore[arg-type]
        planned_study_length_null_value_code=json_model.planned_study_length_null_value_code,  # type: ignore[arg-type]
    )
