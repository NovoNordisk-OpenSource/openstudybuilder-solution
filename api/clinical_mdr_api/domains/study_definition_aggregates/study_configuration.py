from dataclasses import dataclass
from enum import Enum

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    HighLevelStudyDesignVO,
    RegistryIdentifiersVO,
    StudyDescriptionVO,
    StudyIdentificationMetadataVO,
    StudyInterventionVO,
    StudyPopulationVO,
    StudyVersionMetadataVO,
)


class StudyFieldType(Enum):
    INT = "int"
    TEXT = "text"
    CODELIST_SELECT = "codelist_select"
    CODELIST_MULTISELECT = "multiselect"
    TIME = "time"
    DATE = "date"
    BOOL = "bool"
    REGISTRY = "registry"
    PROJECT = "project"


@dataclass
class StudyFieldConfigurationEntry:
    study_field_data_type: StudyFieldType
    study_field_name: str
    study_field_null_value_code: str | None
    configured_codelist_uid: str | None
    configured_term_uid: str | None
    study_field_grouping: str
    study_value_object_class: type
    study_field_name_api: str
    is_dictionary_term: bool
    ts_vcdref: str | None


def _e(
    data_type: StudyFieldType,
    name: str,
    grouping: str,
    vo_class: type,
    *,
    null_value_code: str | None = None,
    codelist_uid: str | None = None,
    term_uid: str | None = None,
    api_name: str | None = None,
    is_dictionary_term: bool = False,
    ts_vcdref: str | None = None,
) -> StudyFieldConfigurationEntry:
    return StudyFieldConfigurationEntry(
        study_field_data_type=data_type,
        study_field_name=name,
        study_field_null_value_code=null_value_code,
        configured_codelist_uid=codelist_uid,
        configured_term_uid=term_uid,
        study_field_grouping=grouping,
        study_value_object_class=vo_class,
        study_field_name_api=api_name or name,
        is_dictionary_term=is_dictionary_term,
        ts_vcdref=ts_vcdref,
    )


_T = StudyFieldType.TEXT
_B = StudyFieldType.BOOL
_I = StudyFieldType.INT
_TIME = StudyFieldType.TIME
_DATE = StudyFieldType.DATE
_MS = StudyFieldType.CODELIST_MULTISELECT
_REG = StudyFieldType.REGISTRY
_PROJ = StudyFieldType.PROJECT

_ID = "id_metadata"
_REG_ID = "id_metadata.registry_identifiers"
_VER = "ver_metadata"
_HLD = "high_level_study_design"
_POP = "study_population"
_INT = "study_intervention"
_DESC = "study_description"

_IdVO = StudyIdentificationMetadataVO
_RegVO = RegistryIdentifiersVO
_VerVO = StudyVersionMetadataVO
_HldVO = HighLevelStudyDesignVO
_PopVO = StudyPopulationVO
_IntVO = StudyInterventionVO
_DescVO = StudyDescriptionVO


# fmt: off
_STATIC_FIELD_CONFIG: list[StudyFieldConfigurationEntry] = [
    # ── Identification Metadata ──
    _e(_T,    "study_number",                    _ID,     _IdVO),
    _e(_T,    "subpart_id",                      _ID,     _IdVO),
    _e(_T,    "study_id_prefix",                 _ID,     _IdVO),
    _e(_T,    "study_acronym",                   _ID,     _IdVO),
    _e(_T,    "study_subpart_acronym",           _ID,     _IdVO),
    _e(_T,    "description",                     _ID,     _IdVO),
    _e(_PROJ, "project_number",                  _ID,     _IdVO),

    # ── Registry Identifiers ──
    _e(_REG,  "ct_gov_id",                                                          _REG_ID, _RegVO, null_value_code="ct_gov_id_null_value_code", ts_vcdref="ClinicalTrials.gov"),
    _e(_T,    "ct_gov_id_null_value_code",                                          _REG_ID, _RegVO),
    _e(_REG,  "eudract_id",                                                         _REG_ID, _RegVO, null_value_code="eudract_id_null_value_code", ts_vcdref="EUDRACT"),
    _e(_T,    "eudract_id_null_value_code",                                         _REG_ID, _RegVO),
    _e(_REG,  "universal_trial_number_utn",                                         _REG_ID, _RegVO, null_value_code="universal_trial_number_utn_null_value_code", ts_vcdref="UTN"),
    _e(_T,    "universal_trial_number_utn_null_value_code",                         _REG_ID, _RegVO),
    _e(_REG,  "japanese_trial_registry_id_japic",                                   _REG_ID, _RegVO, null_value_code="japanese_trial_registry_id_japic_null_value_code", ts_vcdref="JAPIC"),
    _e(_T,    "japanese_trial_registry_id_japic_null_value_code",                   _REG_ID, _RegVO),
    _e(_REG,  "investigational_new_drug_application_number_ind",                    _REG_ID, _RegVO,
       null_value_code="investigational_new_drug_application_number_ind_null_value_code", ts_vcdref="IND"),
    _e(_T,    "investigational_new_drug_application_number_ind_null_value_code",    _REG_ID, _RegVO),
    _e(_REG,  "eu_trial_number",                                                    _REG_ID, _RegVO, null_value_code="eu_trial_number_null_value_code", ts_vcdref="ETN"),
    _e(_T,    "eu_trial_number_null_value_code",                                    _REG_ID, _RegVO),
    _e(_REG,  "civ_id_sin_number",                                                  _REG_ID, _RegVO, null_value_code="civ_id_sin_number_null_value_code", ts_vcdref="CISN"),
    _e(_T,    "civ_id_sin_number_null_value_code",                                  _REG_ID, _RegVO),
    _e(_REG,  "national_clinical_trial_number",                                     _REG_ID, _RegVO, null_value_code="national_clinical_trial_number_null_value_code", ts_vcdref="NCTN"),
    _e(_T,    "national_clinical_trial_number_null_value_code",                     _REG_ID, _RegVO),
    _e(_REG,  "japanese_trial_registry_number_jrct",                                _REG_ID, _RegVO, null_value_code="japanese_trial_registry_number_jrct_null_value_code", ts_vcdref="JRCT"),
    _e(_T,    "japanese_trial_registry_number_jrct_null_value_code",                _REG_ID, _RegVO),
    _e(_REG,  "national_medical_products_administration_nmpa_number",               _REG_ID, _RegVO,
       null_value_code="national_medical_products_administration_nmpa_number_null_value_code", ts_vcdref="NMPA"),
    _e(_T,    "national_medical_products_administration_nmpa_number_null_value_code", _REG_ID, _RegVO),
    _e(_REG,  "eudamed_srn_number",                                                 _REG_ID, _RegVO, null_value_code="eudamed_srn_number_null_value_code", ts_vcdref="ESN"),
    _e(_T,    "eudamed_srn_number_null_value_code",                                 _REG_ID, _RegVO),
    _e(_REG,  "investigational_device_exemption_ide_number",                        _REG_ID, _RegVO, null_value_code="investigational_device_exemption_ide_number_null_value_code", ts_vcdref="IDE"),
    _e(_T,    "investigational_device_exemption_ide_number_null_value_code",        _REG_ID, _RegVO),
    _e(_REG,  "eu_pas_number",                                                      _REG_ID, _RegVO, null_value_code="eu_pas_number_null_value_code", ts_vcdref="EPN"),
    _e(_T,    "eu_pas_number_null_value_code",                                      _REG_ID, _RegVO),

    # ── Version Metadata ──
    _e(_DATE, "version_timestamp",               _VER,    _VerVO),
    _e(_T,    "version_description",             _VER,    _VerVO),
    _e(_T,    "version_author",                  _VER,    _VerVO),
    _e(_T,    "version_number",                  _VER,    _VerVO),

    # ── High Level Study Design ──
    _e(_T,    "study_type_code",                 _HLD,    _HldVO, null_value_code="study_type_null_value_code", codelist_uid="C99077"),
    _e(_T,    "study_type_null_value_code",      _HLD,    _HldVO),
    _e(_T,    "trial_phase_code",                _HLD,    _HldVO, null_value_code="trial_phase_null_value_code", codelist_uid="C66737"),
    _e(_T,    "trial_phase_null_value_code",     _HLD,    _HldVO),
    _e(_T,    "development_stage_code",          _HLD,    _HldVO),
    _e(_MS,   "trial_type_codes",                _HLD,    _HldVO, null_value_code="trial_type_null_value_code", codelist_uid="C66739"),
    _e(_T,    "trial_type_null_value_code",      _HLD,    _HldVO),
    _e(_B,    "is_extension_trial",              _HLD,    _HldVO, null_value_code="is_extension_trial_null_value_code", term_uid="C139274"),
    _e(_T,    "is_extension_trial_null_value_code", _HLD, _HldVO),
    _e(_T,    "study_stop_rules",                _HLD,    _HldVO, null_value_code="study_stop_rules_null_value_code"),
    _e(_T,    "study_stop_rules_null_value_code", _HLD,   _HldVO),
    _e(_B,    "is_adaptive_design",              _HLD,    _HldVO, null_value_code="is_adaptive_design_null_value_code", term_uid="C146995"),
    _e(_T,    "is_adaptive_design_null_value_code", _HLD, _HldVO),
    _e(_B,    "post_auth_indicator",             _HLD,    _HldVO, null_value_code="post_auth_indicator_null_value_code", term_uid="C139275"),
    _e(_T,    "post_auth_indicator_null_value_code", _HLD, _HldVO),
    _e(_TIME, "confirmed_response_minimum_duration", _HLD, _HldVO, null_value_code="confirmed_response_minimum_duration_null_value_code"),
    _e(_T,    "confirmed_response_minimum_duration_null_value_code", _HLD, _HldVO),

    # ── Study Population ──
    _e(_MS,   "therapeutic_area_codes",          _POP,    _PopVO, null_value_code="therapeutic_area_null_value_code", is_dictionary_term=True),
    _e(_T,    "therapeutic_area_null_value_code", _POP,   _PopVO),
    _e(_MS,   "disease_condition_or_indication_codes", _POP, _PopVO, null_value_code="disease_condition_or_indication_null_value_code", is_dictionary_term=True),
    _e(_T,    "disease_condition_or_indication_null_value_code", _POP, _PopVO),
    _e(_MS,   "diagnosis_group_codes",           _POP,    _PopVO, null_value_code="diagnosis_group_null_value_code", is_dictionary_term=True),
    _e(_T,    "diagnosis_group_null_value_code", _POP,    _PopVO),
    _e(_T,    "sex_of_participants_code",        _POP,    _PopVO, null_value_code="sex_of_participants_null_value_code", codelist_uid="C66732"),
    _e(_T,    "sex_of_participants_null_value_code", _POP, _PopVO),
    _e(_B,    "rare_disease_indicator",          _POP,    _PopVO, null_value_code="rare_disease_indicator_null_value_code", term_uid="C126070"),
    _e(_T,    "rare_disease_indicator_null_value_code", _POP, _PopVO),
    _e(_B,    "healthy_subject_indicator",       _POP,    _PopVO, null_value_code="healthy_subject_indicator_null_value_code", term_uid="C98737"),
    _e(_T,    "healthy_subject_indicator_null_value_code", _POP, _PopVO),
    _e(_TIME, "planned_maximum_age_of_subjects", _POP,    _PopVO, null_value_code="planned_maximum_age_of_subjects_null_value_code"),
    _e(_T,    "planned_maximum_age_of_subjects_null_value_code", _POP, _PopVO),
    _e(_TIME, "planned_minimum_age_of_subjects", _POP,    _PopVO, null_value_code="planned_minimum_age_of_subjects_null_value_code"),
    _e(_T,    "planned_minimum_age_of_subjects_null_value_code", _POP, _PopVO),
    _e(_TIME, "stable_disease_minimum_duration", _POP,    _PopVO, null_value_code="stable_disease_minimum_duration_null_value_code"),
    _e(_T,    "stable_disease_minimum_duration_null_value_code", _POP, _PopVO),
    _e(_B,    "pediatric_study_indicator",       _POP,    _PopVO, null_value_code="pediatric_study_indicator_null_value_code", term_uid="C123632"),
    _e(_T,    "pediatric_study_indicator_null_value_code", _POP, _PopVO),
    _e(_B,    "pediatric_postmarket_study_indicator", _POP, _PopVO, null_value_code="pediatric_postmarket_study_indicator_null_value_code", term_uid="C123631"),
    _e(_T,    "pediatric_postmarket_study_indicator_null_value_code", _POP, _PopVO),
    _e(_B,    "pediatric_investigation_plan_indicator", _POP, _PopVO, null_value_code="pediatric_investigation_plan_indicator_null_value_code", term_uid="C126069"),
    _e(_T,    "pediatric_investigation_plan_indicator_null_value_code", _POP, _PopVO),
    _e(_T,    "relapse_criteria",                _POP,    _PopVO, null_value_code="relapse_criteria_null_value_code"),
    _e(_T,    "relapse_criteria_null_value_code", _POP,   _PopVO),
    _e(_I,    "number_of_expected_subjects",     _POP,    _PopVO, null_value_code="number_of_expected_subjects_null_value_code"),
    _e(_T,    "number_of_expected_subjects_null_value_code", _POP, _PopVO),

    # ── Study Intervention ──
    _e(_MS,   "trial_intent_types_codes",        _INT,    _IntVO, null_value_code="trial_intent_type_null_value_code", codelist_uid="C66736"),
    _e(_T,    "trial_intent_type_null_value_code", _INT,  _IntVO),
    _e(_T,    "intervention_type_code",          _INT,    _IntVO, null_value_code="intervention_type_null_value_code", codelist_uid="C99078"),
    _e(_T,    "intervention_type_null_value_code", _INT,  _IntVO),
    _e(_B,    "add_on_to_existing_treatments",   _INT,    _IntVO, null_value_code="add_on_to_existing_treatments_null_value_code", term_uid="C49703"),
    _e(_T,    "add_on_to_existing_treatments_null_value_code", _INT, _IntVO),
    _e(_T,    "control_type_code",               _INT,    _IntVO, null_value_code="control_type_null_value_code", codelist_uid="C66785"),
    _e(_T,    "control_type_null_value_code",    _INT,    _IntVO),
    _e(_T,    "intervention_model_code",         _INT,    _IntVO, null_value_code="intervention_model_null_value_code", codelist_uid="C99076"),
    _e(_T,    "intervention_model_null_value_code", _INT, _IntVO),
    _e(_B,    "is_trial_randomised",             _INT,    _IntVO, null_value_code="is_trial_randomised_null_value_code", term_uid="C25196"),
    _e(_T,    "is_trial_randomised_null_value_code", _INT, _IntVO),
    _e(_T,    "stratification_factor",           _INT,    _IntVO, null_value_code="stratification_factor_null_value_code"),
    _e(_T,    "stratification_factor_null_value_code", _INT, _IntVO),
    _e(_T,    "trial_blinding_schema_code",      _INT,    _IntVO, null_value_code="trial_blinding_schema_null_value_code", codelist_uid="C66735"),
    _e(_T,    "trial_blinding_schema_null_value_code", _INT, _IntVO),
    _e(_TIME, "planned_study_length",            _INT,    _IntVO, null_value_code="planned_study_length_null_value_code"),
    _e(_T,    "planned_study_length_null_value_code", _INT, _IntVO),

    # ── Study Description ──
    _e(_T,    "study_title",                     _DESC,   _DescVO),
    _e(_T,    "study_short_title",               _DESC,   _DescVO),
]
# fmt: on


class FieldConfiguration:
    _field_config: list[StudyFieldConfigurationEntry] | None = None

    @classmethod
    def default_field_config(cls) -> list[StudyFieldConfigurationEntry]:
        if cls._field_config is None:
            cls._field_config = list(_STATIC_FIELD_CONFIG)
        return cls._field_config

    @classmethod
    def registry_identifier_vcdref_map(cls) -> dict[str, str]:
        """Return {field_name: ts_vcdref} for all REGISTRY-type fields that have a ts_vcdref."""
        configs: list[StudyFieldConfigurationEntry] = cls.default_field_config()
        return {
            e.study_field_name: e.ts_vcdref
            for e in configs  # pylint: disable=not-an-iterable
            if e.study_field_data_type == StudyFieldType.REGISTRY and e.ts_vcdref
        }
