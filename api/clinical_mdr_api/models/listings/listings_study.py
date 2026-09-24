from datetime import datetime, timezone
from typing import Annotated, Any, Callable, Self, overload

from pydantic import ConfigDict, Field

from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domains.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domains.study_definition_aggregates.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    HighLevelStudyDesignVO,
    StudyInterventionVO,
    StudyMetadataVO,
    StudyPopulationVO,
)
from clinical_mdr_api.domains.study_selections.study_design_cell import (
    StudyDesignCellVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_arm import (
    StudySelectionArmAR,
    StudySelectionArmVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_branch_arm import (
    StudySelectionBranchArmAR,
    StudySelectionBranchArmVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_cohort import (
    StudySelectionCohortAR,
    StudySelectionCohortVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_criteria import (
    StudySelectionCriteriaAR,
    StudySelectionCriteriaVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_element import (
    StudySelectionElementAR,
    StudySelectionElementVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_endpoint import (
    StudySelectionEndpointsAR,
    StudySelectionEndpointVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_objective import (
    StudySelectionObjectivesAR,
    StudySelectionObjectiveVO,
)
from clinical_mdr_api.domains.study_selections.study_visit import StudyVisitVO
from clinical_mdr_api.domains.syntax_instances.criteria import CriteriaAR
from clinical_mdr_api.domains.syntax_instances.endpoint import EndpointAR
from clinical_mdr_api.domains.syntax_instances.objective import ObjectiveAR
from clinical_mdr_api.domains.syntax_instances.timeframe import TimeframeAR
from clinical_mdr_api.models.study_selections.study import StudyDescriptionJsonModel
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpoch
from clinical_mdr_api.models.syntax_instances.criteria import Criteria
from clinical_mdr_api.models.syntax_instances.endpoint import Endpoint
from clinical_mdr_api.models.syntax_instances.objective import Objective
from clinical_mdr_api.models.syntax_instances.timeframe import Timeframe
from clinical_mdr_api.models.utils import BaseModel
from common.exceptions import BusinessLogicException


class SimpleListingCTModel(BaseModel):
    @overload
    @classmethod
    def from_ct_code(
        cls, ct_uid: str, find_term_by_uid: Callable[[str], Any | None]
    ) -> Self: ...
    @overload
    @classmethod
    def from_ct_code(
        cls, ct_uid: None, find_term_by_uid: Callable[[str], Any | None]
    ) -> None: ...
    @classmethod
    def from_ct_code(
        cls, ct_uid: str | None, find_term_by_uid: Callable[[str], Any | None]
    ) -> Self | None:
        simple_listing_ct_model = None
        if ct_uid is not None:
            term = find_term_by_uid(ct_uid)

            if term is not None:
                if hasattr(term, "ct_term_vo"):
                    simple_listing_ct_model = cls(
                        id=getattr(term.ct_term_vo, "concept_id"),
                        name=getattr(term.ct_term_vo, "code_submission_value"),
                    )
                elif hasattr(term, "dictionary_term_vo"):
                    simple_listing_ct_model = cls(
                        id=getattr(term.dictionary_term_vo, "dictionary_id"),
                        name=getattr(term.dictionary_term_vo, "name"),
                    )
            else:
                simple_listing_ct_model = cls(id=ct_uid, name=None)
        return simple_listing_ct_model

    id: Annotated[
        str | None,
        Field(
            description="concept id: c code for CDISC CT, dictionary id for dictionary codes",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    name: Annotated[
        str | None,
        Field(
            description="name: submission name for CDISC CT, name for dictionary codes",
            json_schema_extra={"nullable": True},
        ),
    ] = None


# TODO this function needs to know what codelist to get submission value from.
# Note, this is currently not used by the UI.
def ct_term_uid_to_str(
    ct_uid: str | None, find_term_by_uid: Callable[[str], Any | None]
):
    if ct_uid is not None:
        term = find_term_by_uid(ct_uid)
        if term is not None:
            if hasattr(term, "ct_term_vo"):
                # return getattr(term.ct_term_vo, "code_submission_value")
                return getattr(term.ct_term_vo, "preferred_term")
        else:
            return f"uid: {ct_uid} not found"
    return ""


def boolean_to_ny(response: bool | None):
    if response:
        return "Y"
    return "N"


def none_to_empty_str(obj):
    if obj is None:
        return ""
    return obj


class RegistryIdentifiersListingModel(BaseModel):
    model_config = ConfigDict(
        title="Registry identifiers model for listing supplying SDTM generation framework"
    )

    ct_gov: Annotated[str, Field()]
    eudract: Annotated[str, Field()]
    utn: Annotated[str, Field()]
    japic: Annotated[str, Field()]
    ind: Annotated[str, Field()]
    eutn: Annotated[str, Field()]
    civ: Annotated[str, Field()]
    nctn: Annotated[str, Field()]
    jrct: Annotated[str, Field()]
    nmpa: Annotated[str, Field()]
    esn: Annotated[str, Field()]
    ide: Annotated[str, Field()]
    eupn: Annotated[str, Field()]

    @classmethod
    def from_study_registry_identifiers_vo(
        cls,
        registry_identifiers_vo: RegistryIdentifiersVO,
    ) -> Self | None:
        if registry_identifiers_vo is None:
            return None
        return cls(
            ct_gov=none_to_empty_str(registry_identifiers_vo.ct_gov_id),
            eudract=none_to_empty_str(registry_identifiers_vo.eudract_id),
            utn=none_to_empty_str(registry_identifiers_vo.universal_trial_number_utn),
            japic=none_to_empty_str(
                registry_identifiers_vo.japanese_trial_registry_id_japic
            ),
            ind=none_to_empty_str(
                registry_identifiers_vo.investigational_new_drug_application_number_ind
            ),
            eutn=none_to_empty_str(registry_identifiers_vo.eu_trial_number),
            civ=none_to_empty_str(registry_identifiers_vo.civ_id_sin_number),
            nctn=none_to_empty_str(
                registry_identifiers_vo.national_clinical_trial_number
            ),
            jrct=none_to_empty_str(
                registry_identifiers_vo.japanese_trial_registry_number_jrct
            ),
            nmpa=none_to_empty_str(
                registry_identifiers_vo.national_medical_products_administration_nmpa_number
            ),
            esn=none_to_empty_str(registry_identifiers_vo.eudamed_srn_number),
            ide=none_to_empty_str(
                registry_identifiers_vo.investigational_device_exemption_ide_number
            ),
            eupn=none_to_empty_str(registry_identifiers_vo.eu_pas_number),
        )


class StudyTypeListingModel(BaseModel):
    model_config = ConfigDict(
        title="Study type model for listing supplying SDTM generation framework"
    )

    stype: Annotated[str, Field()]
    stype_nf: Annotated[str, Field()]

    trial_type: Annotated[list[SimpleListingCTModel], Field()]
    trial_type_nf: Annotated[str, Field()]

    phase: Annotated[str, Field()]
    phase_nf: Annotated[str, Field()]

    extension: Annotated[str, Field()]
    extension_nf: Annotated[str, Field()]

    adaptive: Annotated[str, Field()]
    adaptive_nf: Annotated[str, Field()]

    stop_rule: Annotated[str, Field()]
    stop_rule_nf: Annotated[str, Field()]

    confirmed_res_min_dur: Annotated[str, Field()]
    confirmed_res_min_dur_nf: Annotated[str, Field()]

    post_auth: Annotated[str, Field()]
    post_auth_nf: Annotated[str, Field()]

    @classmethod
    def from_high_level_study_design_vo(
        cls,
        high_level_study_design_vo: HighLevelStudyDesignVO | None,
        find_term_by_uid: Callable[[str], CTTermAttributesAR | None],
    ) -> Self | None:
        if high_level_study_design_vo is None:
            return None
        return cls(
            stype=ct_term_uid_to_str(
                ct_uid=high_level_study_design_vo.study_type_code,
                find_term_by_uid=find_term_by_uid,
            ),
            stype_nf=ct_term_uid_to_str(
                ct_uid=high_level_study_design_vo.study_type_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            trial_type=[
                SimpleListingCTModel.from_ct_code(
                    ct_uid=trial_type_code, find_term_by_uid=find_term_by_uid
                )
                for trial_type_code in high_level_study_design_vo.trial_type_codes
                if high_level_study_design_vo.trial_type_codes
            ],
            trial_type_nf=ct_term_uid_to_str(
                ct_uid=high_level_study_design_vo.trial_type_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            phase=ct_term_uid_to_str(
                ct_uid=high_level_study_design_vo.trial_phase_code,
                find_term_by_uid=find_term_by_uid,
            ),
            phase_nf=ct_term_uid_to_str(
                ct_uid=high_level_study_design_vo.trial_phase_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            extension=none_to_empty_str(
                boolean_to_ny(high_level_study_design_vo.is_extension_trial)
            ),
            extension_nf=ct_term_uid_to_str(
                ct_uid=high_level_study_design_vo.is_extension_trial_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            adaptive=none_to_empty_str(
                boolean_to_ny(high_level_study_design_vo.is_adaptive_design)
            ),
            adaptive_nf=ct_term_uid_to_str(
                ct_uid=high_level_study_design_vo.is_adaptive_design_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            stop_rule=none_to_empty_str(high_level_study_design_vo.study_stop_rules),
            stop_rule_nf=ct_term_uid_to_str(
                ct_uid=high_level_study_design_vo.study_stop_rules_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            confirmed_res_min_dur=none_to_empty_str(
                high_level_study_design_vo.confirmed_response_minimum_duration
            ),
            confirmed_res_min_dur_nf=ct_term_uid_to_str(
                ct_uid=high_level_study_design_vo.confirmed_response_minimum_duration_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            post_auth=none_to_empty_str(
                boolean_to_ny(high_level_study_design_vo.post_auth_indicator)
            ),
            post_auth_nf=ct_term_uid_to_str(
                ct_uid=high_level_study_design_vo.post_auth_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
        )


class StudyPopulationListingModel(BaseModel):
    model_config = ConfigDict(
        title="Study population model for listing supplying SDTM generation framework"
    )

    therapy_area: Annotated[list[SimpleListingCTModel], Field()]
    therapy_area_nf: Annotated[str, Field()]

    indication: Annotated[list[SimpleListingCTModel], Field()]
    indication_nf: Annotated[str, Field()]

    diag_grp: Annotated[list[SimpleListingCTModel], Field()]
    diag_grp_nf: Annotated[str, Field()]

    sex: Annotated[str, Field()]
    sex_nf: Annotated[str, Field()]

    rare_dis: Annotated[str, Field()]
    rare_dis_nf: Annotated[str, Field()]

    healthy_subj: Annotated[str, Field()]
    healthy_subj_nf: Annotated[str, Field()]

    min_age: Annotated[str, Field()]
    min_age_nf: Annotated[str, Field()]

    max_age: Annotated[str, Field()]
    max_age_nf: Annotated[str, Field()]

    stable_dis_min_dur: Annotated[str, Field()]
    stable_dis_min_dur_nf: Annotated[str, Field()]

    pediatric: Annotated[str, Field()]
    pediatric_nf: Annotated[str, Field()]

    pediatric_postmarket: Annotated[str, Field()]
    pediatric_postmarket_nf: Annotated[str, Field()]

    pediatric_inv: Annotated[str, Field()]
    pediatric_inv_nf: Annotated[str, Field()]

    relapse_criteria: Annotated[str, Field()]
    relapse_criteria_nf: Annotated[str, Field()]

    plan_no_subject: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    plan_no_subject_nf: Annotated[str, Field()]

    @classmethod
    def from_study_population_vo(
        cls,
        study_population_vo: StudyPopulationVO | None,
        find_term_by_uid: Callable[[str], CTTermAttributesAR | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
    ) -> Self | None:
        if study_population_vo is None:
            return None
        return cls(
            therapy_area=[
                SimpleListingCTModel.from_ct_code(
                    ct_uid=therapeutic_area_code,
                    find_term_by_uid=find_dictionary_term_by_uid,
                )
                for therapeutic_area_code in study_population_vo.therapeutic_area_codes
                if study_population_vo.therapeutic_area_codes
            ],
            therapy_area_nf=ct_term_uid_to_str(
                ct_uid=study_population_vo.therapeutic_area_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            indication=[
                SimpleListingCTModel.from_ct_code(
                    ct_uid=disease_or_indication_code,
                    find_term_by_uid=find_dictionary_term_by_uid,
                )
                for disease_or_indication_code in study_population_vo.disease_condition_or_indication_codes
                if study_population_vo.disease_condition_or_indication_codes
            ],
            indication_nf=(
                ct_term_uid_to_str(
                    ct_uid=study_population_vo.disease_condition_or_indication_null_value_code,
                    find_term_by_uid=find_term_by_uid,
                )
            ),
            diag_grp=[
                SimpleListingCTModel.from_ct_code(
                    ct_uid=diagnosis_group_code,
                    find_term_by_uid=find_dictionary_term_by_uid,
                )
                for diagnosis_group_code in study_population_vo.diagnosis_group_codes
                if study_population_vo.diagnosis_group_codes
            ],
            diag_grp_nf=ct_term_uid_to_str(
                ct_uid=study_population_vo.diagnosis_group_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            sex=ct_term_uid_to_str(
                ct_uid=study_population_vo.sex_of_participants_code,
                find_term_by_uid=find_term_by_uid,
            ),
            sex_nf=ct_term_uid_to_str(
                ct_uid=study_population_vo.sex_of_participants_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            rare_dis=none_to_empty_str(
                boolean_to_ny(study_population_vo.rare_disease_indicator)
            ),
            rare_dis_nf=ct_term_uid_to_str(
                ct_uid=study_population_vo.rare_disease_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            healthy_subj=none_to_empty_str(
                boolean_to_ny(study_population_vo.healthy_subject_indicator)
            ),
            healthy_subj_nf=ct_term_uid_to_str(
                ct_uid=study_population_vo.healthy_subject_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            min_age=none_to_empty_str(
                study_population_vo.planned_minimum_age_of_subjects
            ),
            min_age_nf=ct_term_uid_to_str(
                ct_uid=study_population_vo.planned_minimum_age_of_subjects_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            max_age=none_to_empty_str(
                study_population_vo.planned_maximum_age_of_subjects
            ),
            max_age_nf=ct_term_uid_to_str(
                ct_uid=study_population_vo.planned_maximum_age_of_subjects_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            stable_dis_min_dur=none_to_empty_str(
                study_population_vo.stable_disease_minimum_duration
            ),
            stable_dis_min_dur_nf=ct_term_uid_to_str(
                ct_uid=study_population_vo.stable_disease_minimum_duration_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            pediatric=none_to_empty_str(
                boolean_to_ny(study_population_vo.pediatric_study_indicator)
            ),
            pediatric_nf=ct_term_uid_to_str(
                ct_uid=study_population_vo.pediatric_study_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            pediatric_postmarket=none_to_empty_str(
                boolean_to_ny(study_population_vo.pediatric_postmarket_study_indicator)
            ),
            pediatric_postmarket_nf=ct_term_uid_to_str(
                ct_uid=study_population_vo.pediatric_postmarket_study_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            pediatric_inv=none_to_empty_str(
                boolean_to_ny(
                    study_population_vo.pediatric_investigation_plan_indicator
                )
            ),
            pediatric_inv_nf=ct_term_uid_to_str(
                ct_uid=study_population_vo.pediatric_investigation_plan_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            relapse_criteria=none_to_empty_str(study_population_vo.relapse_criteria),
            relapse_criteria_nf=ct_term_uid_to_str(
                ct_uid=study_population_vo.relapse_criteria_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            plan_no_subject=study_population_vo.number_of_expected_subjects,
            plan_no_subject_nf=ct_term_uid_to_str(
                ct_uid=study_population_vo.number_of_expected_subjects_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
        )


class StudyAttributesListingModel(BaseModel):
    model_config = ConfigDict(
        title="Study attributes model for listing supplying SDTM generation framework"
    )

    intv_type: Annotated[str, Field()]
    intv_type_nf: Annotated[str, Field()]

    add_on: Annotated[str, Field()]
    add_on_nf: Annotated[str, Field()]

    control_type: Annotated[str, Field()]
    control_type_nf: Annotated[str, Field()]

    intv_model: Annotated[str, Field()]
    intv_model_nf: Annotated[str, Field()]

    randomised: Annotated[str, Field()]
    randomised_nf: Annotated[str, Field()]

    strata: Annotated[str, Field()]
    strata_nf: Annotated[str, Field()]

    blinding: Annotated[str, Field()]
    blinding_nf: Annotated[str, Field()]

    planned_length: Annotated[str, Field()]
    planned_length_nf: Annotated[str, Field()]

    study_intent: Annotated[list[SimpleListingCTModel], Field()]
    study_intent_nf: Annotated[str, Field()]

    @classmethod
    def from_study_intervention_vo(
        cls,
        study_intervention_vo: StudyInterventionVO | None,
        find_term_by_uid: Callable[[str], CTTermAttributesAR | None],
    ) -> Self | None:
        if study_intervention_vo is None:
            return None
        return cls(
            intv_type=ct_term_uid_to_str(
                ct_uid=study_intervention_vo.intervention_type_code,
                find_term_by_uid=find_term_by_uid,
            ),
            intv_type_nf=ct_term_uid_to_str(
                ct_uid=study_intervention_vo.intervention_type_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            add_on=none_to_empty_str(
                boolean_to_ny(study_intervention_vo.add_on_to_existing_treatments)
            ),
            add_on_nf=ct_term_uid_to_str(
                ct_uid=study_intervention_vo.add_on_to_existing_treatments_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            control_type=ct_term_uid_to_str(
                ct_uid=study_intervention_vo.control_type_code,
                find_term_by_uid=find_term_by_uid,
            ),
            control_type_nf=ct_term_uid_to_str(
                ct_uid=study_intervention_vo.control_type_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            intv_model=ct_term_uid_to_str(
                ct_uid=study_intervention_vo.intervention_model_code,
                find_term_by_uid=find_term_by_uid,
            ),
            intv_model_nf=ct_term_uid_to_str(
                ct_uid=study_intervention_vo.intervention_model_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            randomised=none_to_empty_str(
                boolean_to_ny(study_intervention_vo.is_trial_randomised)
            ),
            randomised_nf=ct_term_uid_to_str(
                ct_uid=study_intervention_vo.is_trial_randomised_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            strata=none_to_empty_str(study_intervention_vo.stratification_factor),
            strata_nf=ct_term_uid_to_str(
                ct_uid=study_intervention_vo.stratification_factor_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            blinding=ct_term_uid_to_str(
                ct_uid=study_intervention_vo.trial_blinding_schema_code,
                find_term_by_uid=find_term_by_uid,
            ),
            blinding_nf=ct_term_uid_to_str(
                ct_uid=study_intervention_vo.trial_blinding_schema_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            planned_length=none_to_empty_str(
                study_intervention_vo.planned_study_length
            ),
            planned_length_nf=ct_term_uid_to_str(
                ct_uid=study_intervention_vo.planned_study_length_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            study_intent=[
                SimpleListingCTModel.from_ct_code(
                    ct_uid=trial_intent_type_code, find_term_by_uid=find_term_by_uid
                )
                for trial_intent_type_code in study_intervention_vo.trial_intent_types_codes
                if study_intervention_vo.trial_intent_types_codes
            ],
            study_intent_nf=ct_term_uid_to_str(
                ct_uid=study_intervention_vo.trial_intent_type_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
        )


class StudySelctionListingModel(BaseModel):
    uid: Annotated[str, Field()]
    name: Annotated[str, Field()]
    short_name: Annotated[str, Field()]
    code: Annotated[str, Field()]
    no_subject: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    desc: Annotated[str, Field()]


class StudyBranchArmListingModel(StudySelctionListingModel):
    model_config = ConfigDict(title="Study Branch Arm model for listing")

    order: Annotated[int, Field()]
    arm_uid: Annotated[str, Field()]
    rand_grp: Annotated[str, Field()]

    @classmethod
    def from_study_selection_branch_arm_vo(
        cls,
        study_selection_branch_arm_vo: StudySelectionBranchArmVO,
        order: int,
    ) -> Self | None:
        return cls(
            uid=study_selection_branch_arm_vo.study_selection_uid,
            arm_uid=study_selection_branch_arm_vo.arm_root_uid,
            order=order,
            name=none_to_empty_str(study_selection_branch_arm_vo.name),
            short_name=none_to_empty_str(study_selection_branch_arm_vo.short_name),
            rand_grp=none_to_empty_str(
                study_selection_branch_arm_vo.randomization_group
            ),
            code=none_to_empty_str(study_selection_branch_arm_vo.code),
            no_subject=study_selection_branch_arm_vo.number_of_subjects,
            desc=none_to_empty_str(study_selection_branch_arm_vo.description),
        )

    @staticmethod
    def from_study_selection_branch_arm_ar(
        study_selection_branch_arm_ar: StudySelectionBranchArmAR,
    ) -> list["StudyBranchArmListingModel"]:
        branch_arms = []
        for selection in study_selection_branch_arm_ar.study_branch_arms_selection:
            selection_and_order = (
                study_selection_branch_arm_ar.get_specific_object_selection(
                    selection.study_selection_uid
                )
            )
            branch_arms.append(
                StudyBranchArmListingModel.from_study_selection_branch_arm_vo(
                    study_selection_branch_arm_vo=selection_and_order[0],
                    order=selection_and_order[1],
                )
            )
        return branch_arms


class StudyArmListingModel(StudySelctionListingModel):
    model_config = ConfigDict(title="Study Arm model for listing")

    order: Annotated[int, Field()]
    rand_grp: Annotated[str, Field()]
    type: Annotated[str, Field()]

    @classmethod
    def from_study_selection_arm_vo(
        cls,
        study_selection_arm_vo: StudySelectionArmVO,
        order: int,
        find_simple_term_arm_type_by_term_uid: Callable,
    ) -> Self | None:
        return cls(
            uid=study_selection_arm_vo.study_selection_uid,
            type=ct_term_uid_to_str(
                ct_uid=study_selection_arm_vo.arm_type_uid,
                find_term_by_uid=find_simple_term_arm_type_by_term_uid,
            ),
            order=order,
            name=none_to_empty_str(study_selection_arm_vo.name),
            short_name=none_to_empty_str(study_selection_arm_vo.short_name),
            rand_grp=none_to_empty_str(study_selection_arm_vo.randomization_group),
            code=none_to_empty_str(study_selection_arm_vo.code),
            no_subject=study_selection_arm_vo.number_of_subjects,
            desc=none_to_empty_str(study_selection_arm_vo.description),
        )

    @staticmethod
    def from_study_selection_arm_ar(
        study_selection_arm_ar: StudySelectionArmAR,
        find_simple_term_arm_type_by_term_uid: Callable,
    ) -> list["StudyArmListingModel"]:
        arms = []
        for selection in study_selection_arm_ar.study_arms_selection:
            selection_and_order = study_selection_arm_ar.get_specific_object_selection(
                selection.study_selection_uid
            )
            arms.append(
                StudyArmListingModel.from_study_selection_arm_vo(
                    study_selection_arm_vo=selection_and_order[0],
                    order=selection_and_order[1],
                    find_simple_term_arm_type_by_term_uid=find_simple_term_arm_type_by_term_uid,
                )
            )
        return arms


class StudyCohortListingModel(StudySelctionListingModel):
    model_config = ConfigDict(title="study attributes model for listing")

    arm_uid: Annotated[list[str], Field()]
    branch_uid: Annotated[list[str], Field()]

    @classmethod
    def from_study_selection_cohort_vo(
        cls,
        study_selection_cohort_vo: StudySelectionCohortVO,
    ) -> Self | None:
        return cls(
            uid=study_selection_cohort_vo.study_selection_uid,
            name=none_to_empty_str(study_selection_cohort_vo.name),
            short_name=none_to_empty_str(study_selection_cohort_vo.short_name),
            code=none_to_empty_str(study_selection_cohort_vo.code),
            no_subject=study_selection_cohort_vo.number_of_subjects,
            desc=none_to_empty_str(study_selection_cohort_vo.description),
            arm_uid=(
                study_selection_cohort_vo.arm_root_uids
                if study_selection_cohort_vo.arm_root_uids
                else []
            ),
            branch_uid=(
                study_selection_cohort_vo.branch_arm_root_uids
                if study_selection_cohort_vo.branch_arm_root_uids
                else []
            ),
        )

    @staticmethod
    def from_study_selection_cohort_ar(
        study_selection_cohort_ar: StudySelectionCohortAR,
    ) -> list["StudyCohortListingModel"]:
        cohorts = []
        for selection in study_selection_cohort_ar.study_cohorts_selection:
            cohorts.append(
                StudyCohortListingModel.from_study_selection_cohort_vo(
                    study_selection_cohort_vo=selection,
                )
            )
        return cohorts


class StudyEpochListingModel(BaseModel):
    uid: Annotated[str, Field()]
    order: Annotated[int | None, Field(json_schema_extra={"nullable": True})]
    name: Annotated[str, Field()]
    type: Annotated[str, Field()]
    subtype: Annotated[str, Field()]
    start_rule: Annotated[str, Field()]
    end_rule: Annotated[str, Field()]
    description: Annotated[str, Field()]

    @classmethod
    def from_study_epoch(
        cls,
        study_epoch: StudyEpoch,
        find_term_by_uid: Callable,
    ) -> Self | None:
        return cls(
            uid=study_epoch.uid,
            order=study_epoch.order,
            name=none_to_empty_str(study_epoch.epoch_ctterm.sponsor_preferred_name),
            type=ct_term_uid_to_str(
                study_epoch.epoch_type_ctterm.term_uid,
                find_term_by_uid=find_term_by_uid,
            ),
            subtype=ct_term_uid_to_str(
                study_epoch.epoch_subtype_ctterm.term_uid,
                find_term_by_uid=find_term_by_uid,
            ),
            start_rule=none_to_empty_str(study_epoch.start_rule),
            end_rule=none_to_empty_str(study_epoch.end_rule),
            description=none_to_empty_str(study_epoch.description),
        )

    @staticmethod
    def from_all_study_epochs(
        all_study_epochs: list[StudyEpoch],
        find_term_by_uid: Callable,
    ) -> list["StudyEpochListingModel"]:
        epochs = []
        for epoch in all_study_epochs:
            epochs.append(
                StudyEpochListingModel.from_study_epoch(
                    study_epoch=epoch,
                    find_term_by_uid=find_term_by_uid,
                )
            )
        return epochs


class StudyElementListingModel(BaseModel):
    uid: Annotated[str, Field()]
    order: Annotated[int, Field()]
    name: Annotated[str, Field()]
    short_name: Annotated[str, Field()]
    type: Annotated[str, Field()]
    subtype: Annotated[str, Field()]
    start_rule: Annotated[str, Field()]
    end_rule: Annotated[str, Field()]
    dur: Annotated[str, Field()]
    desc: Annotated[str, Field()]

    @classmethod
    def from_study_element_vo(
        cls,
        study_element_vo: StudySelectionElementVO,
        order: int,
        find_term_by_uid: Callable,
    ) -> Self | None:
        return cls(
            uid=study_element_vo.study_selection_uid,
            order=order,
            name=none_to_empty_str(study_element_vo.name),
            short_name=none_to_empty_str(study_element_vo.short_name),
            type=ct_term_uid_to_str(
                study_element_vo.code, find_term_by_uid=find_term_by_uid
            ),
            subtype=ct_term_uid_to_str(
                study_element_vo.element_subtype_uid, find_term_by_uid=find_term_by_uid
            ),
            start_rule=none_to_empty_str(study_element_vo.start_rule),
            end_rule=none_to_empty_str(study_element_vo.end_rule),
            dur=none_to_empty_str(study_element_vo.planned_duration),
            desc=none_to_empty_str(study_element_vo.description),
        )

    @staticmethod
    def from_study_element_ar(
        study_element_ar: StudySelectionElementAR,
        find_term_by_uid: Callable,
    ) -> list["StudyElementListingModel"]:
        elements = []
        for selection in study_element_ar.study_elements_selection:
            selection_and_order = study_element_ar.get_specific_object_selection(
                selection.study_selection_uid
            )
            elements.append(
                StudyElementListingModel.from_study_element_vo(
                    study_element_vo=selection_and_order[0],
                    order=selection_and_order[1],
                    find_term_by_uid=find_term_by_uid,
                )
            )
        return elements


class StudyDesignMatrixListingModel(BaseModel):
    arm_uid: Annotated[str, Field()]
    branch_uid: Annotated[str, Field()]
    epoch_uid: Annotated[str, Field()]
    element_uid: Annotated[str, Field()]

    @classmethod
    def from_study_design_cell_vo(
        cls,
        design_cell_vo: StudyDesignCellVO,
    ) -> Self:
        return cls(
            arm_uid=none_to_empty_str(design_cell_vo.study_arm_uid),
            branch_uid=none_to_empty_str(design_cell_vo.study_branch_arm_uid),
            epoch_uid=design_cell_vo.study_epoch_uid,
            element_uid=none_to_empty_str(design_cell_vo.study_element_uid),
        )

    @staticmethod
    def from_all_study_design_cells(
        all_design_cells: list[StudyDesignCellVO],
    ) -> list["StudyDesignMatrixListingModel"]:
        design_cells = []
        for design_cell in all_design_cells:
            design_cells.append(
                StudyDesignMatrixListingModel.from_study_design_cell_vo(
                    design_cell_vo=design_cell,
                )
            )
        return design_cells


class StudyVisitListingModel(BaseModel):
    epoch_uid: Annotated[str, Field()]
    epoch_name: Annotated[str, Field()]
    visit_type: Annotated[str | None, Field(json_schema_extra={"nullable": True})]
    contact_model: Annotated[str | None, Field(json_schema_extra={"nullable": True})]
    visit_no: Annotated[str, Field()]
    name: Annotated[str, Field()]
    short_name: Annotated[str, Field()]
    study_day: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    window_min: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    window_max: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    window_unit: Annotated[str, Field()]
    desc: Annotated[str, Field()]
    epoch_alloc: Annotated[str, Field()]
    start_rule: Annotated[str, Field()]
    end_rule: Annotated[str, Field()]

    @classmethod
    def from_study_visit_vo(
        cls,
        study_visit_vo: StudyVisitVO,
    ) -> Self:
        return cls(
            epoch_uid=study_visit_vo.epoch_uid,
            epoch_name=study_visit_vo.epoch.epoch.sponsor_preferred_name,
            visit_type=study_visit_vo.visit_type.sponsor_preferred_name,
            contact_model=study_visit_vo.visit_contact_mode.sponsor_preferred_name,
            visit_no=str(study_visit_vo.unique_visit_number),
            name=study_visit_vo.derive_visit_name(),
            short_name=study_visit_vo.visit_short_name,
            study_day=(
                study_visit_vo.study_day_number if study_visit_vo.study_day else None
            ),
            window_min=study_visit_vo.visit_window_min,
            window_max=study_visit_vo.visit_window_max,
            window_unit=none_to_empty_str(
                study_visit_vo.window_unit_object.name
                if study_visit_vo.window_unit_object
                else None
            ),
            desc=none_to_empty_str(study_visit_vo.description),
            epoch_alloc=none_to_empty_str(
                study_visit_vo.epoch_allocation.sponsor_preferred_name
                if study_visit_vo.epoch_allocation
                else None
            ),
            start_rule=none_to_empty_str(study_visit_vo.start_rule),
            end_rule=none_to_empty_str(study_visit_vo.end_rule),
        )

    @staticmethod
    def from_all_study_visits(
        all_study_visits: list[StudyVisitVO],
    ) -> list["StudyVisitListingModel"]:
        study_visits = []
        for study_visit in all_study_visits:
            study_visits.append(
                StudyVisitListingModel.from_study_visit_vo(
                    study_visit_vo=study_visit,
                )
            )
        return study_visits


class StudyCriteriaListingModel(BaseModel):
    type: Annotated[str, Field()]
    text: Annotated[str, Field()]

    @classmethod
    def from_study_criteria_vo(
        cls,
        study_criteria_vo: StudySelectionCriteriaVO,
        find_term_by_uid: Callable[[str], CTTermAttributesAR | None],
        find_criteria_by_uid: Callable[[str], CriteriaAR | None],
    ) -> Self:
        criteria_ar = find_criteria_by_uid(study_criteria_vo.syntax_object_uid)
        if criteria_ar is None:
            raise BusinessLogicException(
                msg=f"Criteria with UID {study_criteria_vo.syntax_object_uid} not found."
            )
        return cls(
            type=ct_term_uid_to_str(
                ct_uid=study_criteria_vo.criteria_type_uid,
                find_term_by_uid=find_term_by_uid,
            ),
            text=none_to_empty_str(Criteria.from_criteria_ar(criteria_ar).name_plain),
        )

    @staticmethod
    def from_study_criteria_ar(
        study_criteria_ar: StudySelectionCriteriaAR,
        find_term_by_uid: Callable[[str], CTTermAttributesAR | None],
        find_criteria_by_uid: Callable[[str], CriteriaAR | None],
    ) -> list["StudyCriteriaListingModel"]:
        study_criterias = []
        for study_criteria in study_criteria_ar.study_criteria_selection:
            if study_criteria.is_instance:
                study_criterias.append(
                    StudyCriteriaListingModel.from_study_criteria_vo(
                        study_criteria,
                        find_term_by_uid,
                        find_criteria_by_uid=find_criteria_by_uid,
                    )
                )
        return study_criterias


class StudyObjectiveListingModel(BaseModel):
    uid: Annotated[str, Field()]
    type: Annotated[str, Field()]
    text: Annotated[str, Field()]

    @classmethod
    def from_study_objective_vo(
        cls,
        study_objective_vo: StudySelectionObjectiveVO,
        find_term_by_uid: Callable[[str], CTTermAttributesAR | None],
        find_objective_by_uid: Callable[[str], ObjectiveAR | None],
    ) -> Self:
        objective_ar = (
            find_objective_by_uid(study_objective_vo.objective_uid)
            if study_objective_vo.objective_uid is not None
            else None
        )
        if objective_ar is None:
            raise BusinessLogicException(
                msg=f"Objective with UID {study_objective_vo.objective_uid} not found."
            )
        return cls(
            uid=study_objective_vo.study_selection_uid,
            type=ct_term_uid_to_str(
                ct_uid=study_objective_vo.objective_level_uid,
                find_term_by_uid=find_term_by_uid,
            ),
            text=none_to_empty_str(
                Objective.from_objective_ar(objective_ar).name_plain
            ),
        )

    @staticmethod
    def from_study_objective_ar(
        study_objective_ar: StudySelectionObjectivesAR,
        find_term_by_uid: Callable[[str], CTTermAttributesAR | None],
        find_objective_by_uid: Callable[[str], ObjectiveAR | None],
    ) -> list["StudyObjectiveListingModel"]:
        study_objectives = []
        for study_objective in study_objective_ar.study_objectives_selection:
            study_objectives.append(
                StudyObjectiveListingModel.from_study_objective_vo(
                    study_objective,
                    find_term_by_uid,
                    find_objective_by_uid=find_objective_by_uid,
                )
            )
        return study_objectives


class StudyEndpointListingModel(BaseModel):
    uid: Annotated[str, Field()]
    type: Annotated[str, Field()]
    subtype: Annotated[str, Field()]
    text: Annotated[str, Field()]
    objective_uid: Annotated[str, Field()]
    timeframe: Annotated[str, Field()]
    endpoint_unit: Annotated[str, Field()]

    @classmethod
    def from_study_endpoint_vo(
        cls,
        study_endpoint_vo: StudySelectionEndpointVO,
        find_term_by_uid: Callable[[str], CTTermAttributesAR | None],
        find_endpoint_by_uid: Callable[[str], EndpointAR | None],
        find_timeframe_by_uid: Callable[[str], TimeframeAR | None],
    ) -> Self:
        units = (
            [u["name"] for u in study_endpoint_vo.endpoint_units]
            if study_endpoint_vo.endpoint_units
            else None
        )
        if units is None:
            ep_unit = ""
        elif len(units) == 1:
            ep_unit = units[0]
        else:
            ep_unit = f" {study_endpoint_vo.unit_separator} ".join(units)

        endpoint_ar = (
            find_endpoint_by_uid(study_endpoint_vo.endpoint_uid)
            if study_endpoint_vo.endpoint_uid is not None
            else None
        )
        if endpoint_ar is None:
            raise BusinessLogicException(
                msg=f"Endpoint with UID {study_endpoint_vo.endpoint_uid} not found."
            )
        timeframe_ar = (
            find_timeframe_by_uid(study_endpoint_vo.timeframe_uid)
            if study_endpoint_vo.timeframe_uid is not None
            else None
        )
        if timeframe_ar is None:
            raise BusinessLogicException(
                msg=f"Timeframe with UID {study_endpoint_vo.timeframe_uid} not found."
            )

        return cls(
            uid=study_endpoint_vo.study_selection_uid,
            type=ct_term_uid_to_str(
                ct_uid=study_endpoint_vo.endpoint_level_uid,
                find_term_by_uid=find_term_by_uid,
            ),
            subtype=ct_term_uid_to_str(
                ct_uid=study_endpoint_vo.endpoint_sublevel_uid,
                find_term_by_uid=find_term_by_uid,
            ),
            text=none_to_empty_str(Endpoint.from_endpoint_ar(endpoint_ar).name_plain),
            objective_uid=none_to_empty_str(study_endpoint_vo.study_objective_uid),
            timeframe=none_to_empty_str(
                Timeframe.from_timeframe_ar(timeframe_ar).name_plain
                if study_endpoint_vo.timeframe_uid
                else None
            ),
            endpoint_unit=ep_unit,
        )

    @staticmethod
    def from_study_endpoint_ar(
        study_endpoint_ar: StudySelectionEndpointsAR,
        find_term_by_uid: Callable[[str], CTTermAttributesAR | None],
        find_endpoint_by_uid: Callable[[str], EndpointAR | None],
        find_timeframe_by_uid: Callable[[str], TimeframeAR | None],
    ) -> list["StudyEndpointListingModel"]:
        study_endpoints = []
        for study_endpoint in study_endpoint_ar.study_endpoints_selection:
            study_endpoints.append(
                StudyEndpointListingModel.from_study_endpoint_vo(
                    study_endpoint,
                    find_term_by_uid,
                    find_endpoint_by_uid=find_endpoint_by_uid,
                    find_timeframe_by_uid=find_timeframe_by_uid,
                )
            )
        return study_endpoints


class StudyMetadataListingModel(BaseModel):
    model_config = ConfigDict(title="Study Metadata model for listing")

    api_ver: Annotated[str, Field()]
    study_id: Annotated[str, Field()]
    study_ver: Annotated[float, Field()]
    specified_dt: Annotated[str, Field()]
    request_dt: Annotated[str, Field()]
    title: Annotated[str | None, Field(json_schema_extra={"nullable": True})]
    reg_id: Annotated[
        RegistryIdentifiersListingModel | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    study_type: Annotated[
        StudyTypeListingModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_attributes: Annotated[
        StudyAttributesListingModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_population: Annotated[
        StudyPopulationListingModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    arms: Annotated[
        list[StudyArmListingModel] | None, Field(json_schema_extra={"nullable": True})
    ] = None
    branches: Annotated[
        list[StudyBranchArmListingModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    cohorts: Annotated[
        list[StudyCohortListingModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    epochs: Annotated[
        list[StudyEpochListingModel] | None, Field(json_schema_extra={"nullable": True})
    ] = None
    elements: Annotated[
        list[StudyElementListingModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    design_matrix: Annotated[
        list[StudyDesignMatrixListingModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    visits: Annotated[
        list[StudyVisitListingModel] | None, Field(json_schema_extra={"nullable": True})
    ] = None
    criteria: Annotated[
        list[StudyCriteriaListingModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    objectives: Annotated[
        list[StudyObjectiveListingModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    endpoints: Annotated[
        list[StudyEndpointListingModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    @classmethod
    def from_study_metadata_vo(
        cls,
        api_ver: str,
        study_id: str,
        study_ver: str,
        specified_dt: str | None,
        study_metadata_vo: StudyMetadataVO,
        study_selection_arm_ar: StudySelectionArmAR,
        study_selection_branch_arm_ar: StudySelectionBranchArmAR,
        study_selection_cohort_ar: StudySelectionCohortAR,
        study_epochs: list[StudyEpoch],
        study_element_ar: StudySelectionElementAR,
        study_design_cells: list[StudyDesignCellVO],
        study_visits: list[StudyVisitVO],
        study_criteria_ar: StudySelectionCriteriaAR,
        study_objective_ar: StudySelectionObjectivesAR,
        study_endpoint_ar: StudySelectionEndpointsAR,
        find_term_by_uid: Callable[[str], CTTermAttributesAR | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_criteria_by_uid: Callable[[str], CriteriaAR | None],
        find_objective_by_uid: Callable[[str], ObjectiveAR | None],
        find_endpoint_by_uid: Callable[[str], EndpointAR | None],
        find_timeframe_by_uid: Callable[[str], TimeframeAR | None],
    ) -> Self | None:
        if study_metadata_vo is None:
            return None
        return cls(
            api_ver=api_ver,
            study_id=study_id,
            study_ver=float(study_ver),
            specified_dt=none_to_empty_str(specified_dt),
            request_dt=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            title=StudyDescriptionJsonModel.from_study_description_vo(
                study_description_vo=study_metadata_vo.study_description
            ).study_title,
            reg_id=RegistryIdentifiersListingModel.from_study_registry_identifiers_vo(
                registry_identifiers_vo=study_metadata_vo.id_metadata.registry_identifiers,
            ),
            study_type=StudyTypeListingModel.from_high_level_study_design_vo(
                high_level_study_design_vo=study_metadata_vo.high_level_study_design,
                find_term_by_uid=find_term_by_uid,
            ),
            study_attributes=StudyAttributesListingModel.from_study_intervention_vo(
                study_intervention_vo=study_metadata_vo.study_intervention,
                find_term_by_uid=find_term_by_uid,
            ),
            study_population=StudyPopulationListingModel.from_study_population_vo(
                study_population_vo=study_metadata_vo.study_population,
                find_term_by_uid=find_term_by_uid,
                find_dictionary_term_by_uid=find_dictionary_term_by_uid,
            ),
            arms=StudyArmListingModel.from_study_selection_arm_ar(
                study_selection_arm_ar=study_selection_arm_ar,
                find_simple_term_arm_type_by_term_uid=find_term_by_uid,
            ),
            branches=StudyBranchArmListingModel.from_study_selection_branch_arm_ar(
                study_selection_branch_arm_ar=study_selection_branch_arm_ar,
            ),
            cohorts=StudyCohortListingModel.from_study_selection_cohort_ar(
                study_selection_cohort_ar=study_selection_cohort_ar,
            ),
            epochs=StudyEpochListingModel.from_all_study_epochs(
                all_study_epochs=study_epochs,
                find_term_by_uid=find_term_by_uid,
            ),
            elements=StudyElementListingModel.from_study_element_ar(
                study_element_ar=study_element_ar,
                find_term_by_uid=find_term_by_uid,
            ),
            design_matrix=StudyDesignMatrixListingModel.from_all_study_design_cells(
                all_design_cells=study_design_cells,
            ),
            visits=StudyVisitListingModel.from_all_study_visits(
                all_study_visits=study_visits,
            ),
            criteria=StudyCriteriaListingModel.from_study_criteria_ar(
                study_criteria_ar=study_criteria_ar,
                find_term_by_uid=find_term_by_uid,
                find_criteria_by_uid=find_criteria_by_uid,
            ),
            objectives=StudyObjectiveListingModel.from_study_objective_ar(
                study_objective_ar=study_objective_ar,
                find_term_by_uid=find_term_by_uid,
                find_objective_by_uid=find_objective_by_uid,
            ),
            endpoints=StudyEndpointListingModel.from_study_endpoint_ar(
                study_endpoint_ar=study_endpoint_ar,
                find_term_by_uid=find_term_by_uid,
                find_endpoint_by_uid=find_endpoint_by_uid,
                find_timeframe_by_uid=find_timeframe_by_uid,
            ),
        )
