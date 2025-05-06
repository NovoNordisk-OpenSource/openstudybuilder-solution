from typing import Annotated, Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.domains.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domains.study_definition_aggregates.root import StudyDefinitionAR
from clinical_mdr_api.domains.study_selections.study_selection_arm import (
    StudySelectionArmAR,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudySelectionCriteria,
    StudySelectionEndpoint,
)
from clinical_mdr_api.models.utils import (
    BaseModel,
    from_duration_object_to_value_and_unit,
)
from clinical_mdr_api.services._utils import get_name_or_none


class CompactStudyArm(BaseModel):
    arm_type: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    arm_title: Annotated[str, Field()]
    arm_description: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class CompactOutcomeMeasure(BaseModel):
    title: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    timeframe: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )


class CompactRegistryIdentifier(BaseModel):
    secondary_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    id_type: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )


class StudyPharmaCM(BaseModel):
    unique_protocol_identification_number: Annotated[str, Field()]
    brief_title: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    official_title: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    acronym: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    study_type: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    secondary_ids: Annotated[
        list[CompactRegistryIdentifier], Field(json_schema_extra={"nullable": True})
    ] = []

    responsible_party: Annotated[str, Field()] = "Sponsor"
    primary_disease_or_condition_being_studied: Annotated[list[str], Field()] = []
    primary_purpose: Annotated[list[str], Field()] = []
    study_phase: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    interventional_study_model: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    number_of_arms: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    allocation: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    number_of_subjects: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_arms: Annotated[list[CompactStudyArm], Field()] = []
    intervention_type: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    outcome_measures: Annotated[list[CompactOutcomeMeasure], Field()] = []
    minimum_age: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    maximum_age: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    accepts_healthy_volunteers: Annotated[
        bool | None, Field(json_schema_extra={"nullable": True})
    ] = None
    inclusion_criteria: Annotated[list[str], Field()] = []
    exclusion_criteria: Annotated[list[str], Field()] = []

    @classmethod
    def from_various_data(
        cls,
        study: StudyDefinitionAR,
        study_arms: list[StudySelectionArmAR],
        study_endpoints: list[StudySelectionEndpoint],
        inclusion_criterias: list[StudySelectionCriteria],
        exclusion_criterias: list[StudySelectionCriteria],
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_all_units: Callable[[], UnitDefinitionAR],
    ) -> Self:
        study_type = get_name_or_none(
            find_term_by_uid(
                term_uid=study.current_metadata.high_level_study_design.study_type_code
            )
        )
        is_trial_randomized = (
            study.current_metadata.study_intervention.is_trial_randomised
        )
        allocation_text = "randomized" if is_trial_randomized else "not randomized"
        planned_minimum_age = (
            study.current_metadata.study_population.planned_minimum_age_of_subjects
        )
        minimum_age, minimum_age_unit = (
            from_duration_object_to_value_and_unit(
                duration=planned_minimum_age,
                find_all_study_time_units=find_all_units,
            )
            if planned_minimum_age
            else (None, None)
        )
        minimum_age_str = (
            f"{minimum_age} {minimum_age_unit.name}" if minimum_age_unit else None
        )
        planned_maximum_age = (
            study.current_metadata.study_population.planned_maximum_age_of_subjects
        )
        maximum_age, maximum_age_unit = (
            from_duration_object_to_value_and_unit(
                duration=planned_maximum_age,
                find_all_study_time_units=find_all_units,
            )
            if planned_maximum_age
            else (None, None)
        )
        maximum_age_str = (
            f"{maximum_age} {maximum_age_unit.name}" if maximum_age_unit else None
        )
        number_of_arms = len(study_arms.study_arms_selection)
        secondary_ids = []
        registry_identifier = "Registry Identifier"
        other_identifier = "Other Identifier"
        eudract_number_identifier = "EudraCT Number"
        if study.current_metadata.id_metadata.registry_identifiers.eudract_id:
            secondary_ids.append(
                CompactRegistryIdentifier(
                    secondary_id=study.current_metadata.id_metadata.registry_identifiers.eudract_id,
                    id_type=eudract_number_identifier,
                    description="EUDRACT ID",
                )
            )
        if study.current_metadata.id_metadata.registry_identifiers.ct_gov_id:
            secondary_ids.append(
                CompactRegistryIdentifier(
                    secondary_id=study.current_metadata.id_metadata.registry_identifiers.ct_gov_id,
                    id_type=registry_identifier,
                    description="ClinicalTrials.gov ID",
                )
            )
        if (
            study.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn
        ):
            secondary_ids.append(
                CompactRegistryIdentifier(
                    secondary_id=study.current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn,
                    id_type=other_identifier,
                    description="Universal Trial Number (UTN)",
                )
            )
        if (
            study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic
        ):
            secondary_ids.append(
                CompactRegistryIdentifier(
                    secondary_id=study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_japic,
                    id_type=registry_identifier,
                    description="Japanese Trial Registry ID (JAPIC)",
                )
            )
        if (
            study.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind
        ):
            secondary_ids.append(
                CompactRegistryIdentifier(
                    secondary_id=study.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind,
                    id_type=registry_identifier,
                    description="Investigational New Drug Application (IND) Number",
                )
            )
        if (
            study.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number
        ):
            secondary_ids.append(
                CompactRegistryIdentifier(
                    secondary_id=study.current_metadata.id_metadata.registry_identifiers.national_clinical_trial_number,
                    id_type=other_identifier,
                    description="National Clinical Trial Number",
                )
            )
        if (
            study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct
        ):
            secondary_ids.append(
                CompactRegistryIdentifier(
                    secondary_id=study.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_number_jrct,
                    id_type=registry_identifier,
                    description="Japanese Trial Registry Number",
                )
            )
        if (
            study.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number
        ):
            secondary_ids.append(
                CompactRegistryIdentifier(
                    secondary_id=study.current_metadata.id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number,
                    id_type=other_identifier,
                    description="NMPA Number",
                )
            )
        if study.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number:
            secondary_ids.append(
                CompactRegistryIdentifier(
                    secondary_id=study.current_metadata.id_metadata.registry_identifiers.eudamed_srn_number,
                    id_type=other_identifier,
                    description="EUDAMED number",
                )
            )
        if (
            study.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number
        ):
            secondary_ids.append(
                CompactRegistryIdentifier(
                    secondary_id=study.current_metadata.id_metadata.registry_identifiers.investigational_device_exemption_ide_number,
                    id_type=registry_identifier,
                )
            )
        return cls(
            unique_protocol_identification_number=f"{study.current_metadata.id_metadata.study_id_prefix}-{study.current_metadata.id_metadata.study_number}",
            brief_title=study.current_metadata.study_description.study_short_title,
            official_title=study.current_metadata.study_description.study_title,
            acronym=study.current_metadata.id_metadata.study_acronym,
            study_type=study_type,
            secondary_ids=secondary_ids,
            primary_disease_or_condition_being_studied=[
                find_dictionary_term_by_uid(term_uid=code).name
                for code in study.current_metadata.study_population.disease_condition_or_indication_codes
            ],
            primary_purpose=[
                find_term_by_uid(term_uid=code).name
                for code in study.current_metadata.study_intervention.trial_intent_types_codes
            ],
            study_phase=get_name_or_none(
                find_term_by_uid(
                    term_uid=study.current_metadata.high_level_study_design.trial_phase_code
                )
            ),
            interventional_study_model=get_name_or_none(
                find_term_by_uid(
                    term_uid=study.current_metadata.study_intervention.intervention_model_code
                )
            ),
            number_of_arms=number_of_arms,
            allocation="N/A" if study_type != "Interventional" else allocation_text,
            number_of_subjects=sum(
                study_arm.number_of_subjects
                for study_arm in study_arms.study_arms_selection
                if study_arm.number_of_subjects
            ),
            study_arms=[
                CompactStudyArm(
                    arm_type=get_name_or_none(
                        find_term_by_uid(term_uid=study_arm.arm_type_uid)
                    ),
                    arm_title=study_arm.name,
                    arm_description=study_arm.description,
                )
                for study_arm in study_arms.study_arms_selection
            ],
            intervention_type=get_name_or_none(
                find_term_by_uid(
                    term_uid=study.current_metadata.study_intervention.intervention_type_code
                )
            ),
            outcome_measures=[
                CompactOutcomeMeasure(
                    title=(
                        study_endpoint.study_objective.objective.name_plain
                        if study_endpoint.study_objective
                        else None
                    ),
                    timeframe=(
                        study_endpoint.timeframe.name_plain
                        if study_endpoint.timeframe
                        else None
                    ),
                    description=(
                        f" {study_endpoint.endpoint_units.separator} ".join(
                            [unit.name for unit in study_endpoint.endpoint_units.units]
                        )
                        if len(study_endpoint.endpoint_units.units) > 1
                        else "".join(
                            [unit.name for unit in study_endpoint.endpoint_units.units]
                        )
                    ),
                )
                for study_endpoint in study_endpoints
            ],
            minimum_age=minimum_age_str,
            maximum_age=maximum_age_str,
            accepts_healthy_volunteers=study.current_metadata.study_population.healthy_subject_indicator,
            inclusion_criteria=[
                inclusion_criteria.criteria.name_plain
                for inclusion_criteria in inclusion_criterias
            ],
            exclusion_criteria=[
                exclusion_criteria.criteria.name_plain
                for exclusion_criteria in exclusion_criterias
            ],
        )


class StudyPharmaCMXML(BaseModel):

    @classmethod
    def from_pharma_cm_data(cls, study_pharma_cm: StudyPharmaCM) -> Self:
        return {
            "study_collection": {
                "clinical_study": {
                    "id_info": {
                        "provider_name": None,
                        "provider_study_id": None,
                        "org_name": None,
                        "org_study_id": study_pharma_cm.unique_protocol_identification_number,
                        "secondary_id": [
                            {
                                "id": secondary_id.secondary_id,
                                "id_type": secondary_id.id_type,
                                "id_domain": secondary_id.description,
                            }
                            for secondary_id in study_pharma_cm.secondary_ids
                        ],
                    },
                    "is_fda_regulated": None,
                    "is_section_801": None,
                    "delayed_posting": None,
                    "is_ind_study": None,
                    "ind_info": {
                        "ind_grantor": None,
                        "ind_number": None,
                        "ind_serial_number": None,
                        "has_expanded_access": None,
                        "expanded_access_nct_id": None,
                    },
                    "brief_titile": study_pharma_cm.brief_title,
                    "acronym": study_pharma_cm.acronym,
                    "official_title": study_pharma_cm.official_title,
                    "sponsors": {
                        "lead_sponsor": None,
                        "collaborator": None,
                        "resp_party": {
                            "resp_party_type": "Sponsor",
                            "investigator_username": None,
                            "investigator_title": None,
                            "investigator_affiliation": None,
                        },
                    },
                    "oversight_info": {
                        "regulatory_authority": None,
                        "irb_info": {
                            "approval_status": None,
                            "approval_number": None,
                            "name": None,
                            "affiliation": None,
                            "phone": None,
                            "phone_ext": None,
                            "email": None,
                            "full_address": None,
                        },
                        "has_dmc": None,
                        "fda_regulated_drug": None,
                        "exported_from_us": None,
                        "fda_regulated_device": None,
                        "post_prior_to_approval": None,
                        "ped_postmarket_surv": None,
                    },
                    "ipd_sharing_statement": {
                        "sharing_ipd": None,
                        "ipd_description": {"textblock": None},
                        "ipd_info_type_protocol": None,
                        "ipd_info_type_sap": None,
                        "ipd_info_type_icf": None,
                        "ipd_info_type_csr": None,
                        "ipd_info_type_analytic_code": None,
                        "ipd_time_frame": {"textblock": None},
                        "ipd_access_criteria": {"textblock": None},
                        "ipd_url": None,
                    },
                    "brief_summary": {"textblock": None},
                    "detailed_description": {"textblock": None},
                    "why_stopped": None,
                    "expanded_access_status": None,
                    "verification_date": None,
                    "overall_status": None,
                    "start_date": None,
                    "start_date_type": None,
                    "last_follow_up_date": None,
                    "last_follow_up_date_type": None,
                    "primary_compl_date": None,
                    "primary_compl_date_type": None,
                    "study_design": {
                        "study_type": study_pharma_cm.study_type,
                        "no_exp_acc_type": None,
                        "exp_acc_type_individual": None,
                        "exp_acc_type_intermediate": None,
                        "exp_acc_type_treatment": None,
                        "interventional_design": {
                            "interventional_subtype": study_pharma_cm.primary_purpose,
                            "phase": study_pharma_cm.study_phase,
                            "assignment": study_pharma_cm.interventional_study_model,
                            "allocation": study_pharma_cm.allocation,
                            "masking": None,
                            "masked_subject": None,
                            "masked_caregiver": None,
                            "masked_investigator": None,
                            "masked_assessor": None,
                            "no_masking": None,
                            "control": None,
                            "endpoint": None,
                            "number_of_arms": study_pharma_cm.number_of_arms,
                            "model_description": {"textblock": None},
                            "masking_description": {"textblock": None},
                        },
                        "observational_design": {
                            "observational_study_design": None,
                            "biospecimen_retention": None,
                            "biospecimen_description": {"textblock": None},
                            "timing": None,
                            "number_of_groups": None,
                            "patient_registry": None,
                            "target_duration_quantity": None,
                            "target_duration_units": None,
                        },
                    },
                    "primary_outcome": [
                        {
                            "outcome_measure": outcome_measure.title,
                            "outcome_time_frame": outcome_measure.timeframe,
                            "outcome_description": {
                                "description": outcome_measure.description
                            },
                        }
                        for outcome_measure in study_pharma_cm.outcome_measures
                    ],
                    "secondary_outcome": None,
                    "other_outcome": None,
                    "enrollment": None,
                    "enrollment_type": None,
                    "condition": study_pharma_cm.primary_disease_or_condition_being_studied,
                    "arm_group": [
                        {
                            "arm_group_label": study_arm.arm_title,
                            "arm_type": study_arm.arm_type,
                            "arm_group_description": {
                                "textblock": study_arm.arm_description
                            },
                        }
                        for study_arm in study_pharma_cm.study_arms
                    ],
                    "intervention": {
                        "intervention_type": study_pharma_cm.intervention_type,
                        "intervention_name": None,
                        "intervention_description": {"textblock": None},
                        "arm_group_label": None,
                    },
                    "eligibility": {
                        "study_population": {"textblock": None},
                        "sampling_method": None,
                        "criteria": {
                            "textblock": f""" Inclusion Criteria:
                                {"".join(["-" + inclusion_criteria+"\n" for inclusion_criteria in study_pharma_cm.inclusion_criteria])}
                                Exclusion Criteria:
                                {"".join(["-" + exclusion_criteria+"\n" for exclusion_criteria in study_pharma_cm.exclusion_criteria])}
                                """
                        },
                        "healthy_volunteers": study_pharma_cm.accepts_healthy_volunteers,
                        "gender": None,
                        "gender_based": None,
                        "gender_description": {"textblock"},
                        "minimum_age": study_pharma_cm.minimum_age,
                        "maximum_age": study_pharma_cm.maximum_age,
                    },
                    "overall_official": {
                        "first_name": None,
                        "middle_name": None,
                        "last_name": None,
                        "degrees": None,
                        "role": None,
                        "affiliation": None,
                    },
                    "overall_contact": {
                        "first_name": None,
                        "middle_name": None,
                        "last_name": None,
                        "degrees": None,
                        "phone": None,
                        "phone_ext": None,
                        "email": None,
                    },
                    "overall_contact_backup": {
                        "first_name": None,
                        "middle_name": None,
                        "last_name": None,
                        "degrees": None,
                        "phone": None,
                        "phone_ext": None,
                        "email": None,
                    },
                    "location": {
                        "facility": {
                            "name": None,
                            "address": {
                                "city": None,
                                "state": None,
                                "country": None,
                                "zip": None,
                            },
                        },
                        "status": None,
                        "contact": {
                            "first_name": None,
                            "middle_name": None,
                            "last_name": None,
                            "degrees": None,
                            "phone": None,
                            "phone_ext": None,
                            "email": None,
                        },
                        "contact_backup": {
                            "first_name": None,
                            "middle_name": None,
                            "last_name": None,
                            "degrees": None,
                            "phone": None,
                            "phone_ext": None,
                            "email": None,
                        },
                        "investigator": {
                            "first_name": None,
                            "middle_name": None,
                            "last_name": None,
                            "degrees": None,
                            "role": None,
                        },
                    },
                }
            }
        }
