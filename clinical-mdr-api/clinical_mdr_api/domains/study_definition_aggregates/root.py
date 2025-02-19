from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable, MutableSequence, Self

from clinical_mdr_api.domains.study_definition_aggregates._utils import (
    default_failure_callback_for_variable,
)
from clinical_mdr_api.domains.study_definition_aggregates.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_configuration import (
    FieldConfiguration,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    HighLevelStudyDesignVO,
    StudyAction,
    StudyDescriptionVO,
    StudyIdentificationMetadataVO,
    StudyInterventionVO,
    StudyMetadataVO,
    StudyPopulationVO,
    StudyStatus,
    StudyVersionMetadataVO,
)
from clinical_mdr_api.services.user_info import UserInfoService
from common.exceptions import BusinessLogicException, ValidationException


@dataclass
class StudyDefinitionSnapshot:
    """
    Memento object representing StudyDefinition state passed to/from repository.

    *Attributes*:
        * uid - unique id (mandatory)
        * draft_metadata - if provided also implies Study is in DRAFT state (otherwise Study is considered LOCKED)
        * released_metadata - only valid if draft_metadata provided
        * locked_metadata_versions - sequence of locked versions in order of version increasing version numbers
            (version 1 goes first)
    """

    # pylint: disable=too-many-instance-attributes
    @dataclass
    class StudyMetadataSnapshot:
        """
        Class for representing values of Study metadata in some particular version (DRAFT, RELEASED or LOCKED).
        """

        study_number: str | None = None
        subpart_id: str | None = None
        study_acronym: str | None = None
        study_subpart_acronym: str | None = None
        study_id_prefix: str | None = None
        project_number: str | None = None
        description: str | None = None
        ct_gov_id: str | None = None
        ct_gov_id_null_value_code: str | None = None
        eudract_id: str | None = None
        eudract_id_null_value_code: str | None = None
        universal_trial_number_utn: str | None = None
        universal_trial_number_utn_null_value_code: str | None = None
        japanese_trial_registry_id_japic: str | None = None
        japanese_trial_registry_id_japic_null_value_code: str | None = None
        investigational_new_drug_application_number_ind: str | None = None
        investigational_new_drug_application_number_ind_null_value_code: str | None = (
            None
        )
        eu_trial_number: str | None = None
        eu_trial_number_null_value_code: str | None = None
        civ_id_sin_number: str | None = None
        civ_id_sin_number_null_value_code: str | None = None
        national_clinical_trial_number: str | None = None
        national_clinical_trial_number_null_value_code: str | None = None
        japanese_trial_registry_number_jrct: str | None = None
        japanese_trial_registry_number_jrct_null_value_code: str | None = None
        national_medical_products_administration_nmpa_number: str | None = None
        national_medical_products_administration_nmpa_number_null_value_code: (
            str | None
        ) = None
        eudamed_srn_number: str | None = None
        eudamed_srn_number_null_value_code: str | None = None
        investigational_device_exemption_ide_number: str | None = None
        investigational_device_exemption_ide_number_null_value_code: str | None = None
        version_timestamp: datetime | None = None
        version_author: str | None = None
        version_description: str | None = None
        version_number: Decimal | None = None
        study_type_code: str | None = None
        study_type_null_value_code: str | None = None
        trial_intent_types_codes: tuple[str] = ()
        trial_intent_type_null_value_code: str | None = None
        trial_type_codes: tuple[str] = ()
        trial_type_null_value_code: str | None = None
        trial_phase_code: str | None = None
        trial_phase_null_value_code: str | None = None
        is_extension_trial: bool | None = None
        is_extension_trial_null_value_code: str | None = None
        is_adaptive_design: bool | None = None
        is_adaptive_design_null_value_code: str | None = None
        post_auth_indicator: bool | None = None
        post_auth_indicator_null_value_code: str | None = None
        study_stop_rules: str | None = None
        study_stop_rules_null_value_code: str | None = None

        therapeutic_area_codes: tuple[str] = ()
        therapeutic_area_null_value_code: str | None = None

        disease_condition_or_indication_codes: tuple[str] = ()
        disease_condition_or_indication_null_value_code: str | None = None

        diagnosis_group_codes: tuple[str] = ()
        diagnosis_group_null_value_code: str | None = None

        sex_of_participants_code: str | None = None
        sex_of_participants_null_value_code: str | None = None

        rare_disease_indicator: bool | None = None
        rare_disease_indicator_null_value_code: str | None = None

        healthy_subject_indicator: bool | None = None
        healthy_subject_indicator_null_value_code: str | None = None

        planned_minimum_age_of_subjects: str | None = None
        planned_minimum_age_of_subjects_null_value_code: str | None = None

        planned_maximum_age_of_subjects: str | None = None
        planned_maximum_age_of_subjects_null_value_code: str | None = None

        stable_disease_minimum_duration: str | None = None
        stable_disease_minimum_duration_null_value_code: str | None = None

        pediatric_study_indicator: bool | None = None
        pediatric_study_indicator_null_value_code: str | None = None

        pediatric_postmarket_study_indicator: bool | None = None
        pediatric_postmarket_study_indicator_null_value_code: str | None = None

        pediatric_investigation_plan_indicator: bool | None = None
        pediatric_investigation_plan_indicator_null_value_code: str | None = None

        relapse_criteria: str | None = None
        relapse_criteria_null_value_code: str | None = None

        number_of_expected_subjects: int | None = None
        number_of_expected_subjects_null_value_code: str | None = None

        intervention_type_code: str | None = None
        intervention_type_null_value_code: str | None = None

        add_on_to_existing_treatments: bool | None = None
        add_on_to_existing_treatments_null_value_code: str | None = None

        control_type_code: str | None = None
        control_type_null_value_code: str | None = None

        intervention_model_code: str | None = None
        intervention_model_null_value_code: str | None = None

        is_trial_randomised: bool | None = None
        is_trial_randomised_null_value_code: str | None = None

        stratification_factor: str | None = None
        stratification_factor_null_value_code: str | None = None

        trial_blinding_schema_code: str | None = None
        trial_blinding_schema_null_value_code: str | None = None

        planned_study_length: str | None = None
        planned_study_length_null_value_code: str | None = None

        confirmed_response_minimum_duration: str | None = None
        confirmed_response_minimum_duration_null_value_code: str | None = None

        study_title: str | None = None
        study_short_title: str | None = None

    uid: str | None  # = None
    study_parent_part_uid: str | None
    study_subpart_uids: list[str]
    current_metadata: StudyMetadataSnapshot | None  # = None
    draft_metadata: StudyMetadataSnapshot | None  # = None
    released_metadata: StudyMetadataSnapshot | None  # = None
    locked_metadata_versions: MutableSequence[
        StudyMetadataSnapshot
    ]  # = field(default_factory=list)
    study_status: str | None
    deleted: bool  # = False
    specific_metadata: StudyMetadataSnapshot | None = None


# a global helper variables used as a default for some methods arguments in the StudyDefinitionAR class
_DEF_INITIAL_HIGH_LEVEL_STUDY_DESIGN = HighLevelStudyDesignVO(
    study_type_code=None,
    study_stop_rules=None,
    is_adaptive_design=None,
    trial_type_codes=[],
    trial_phase_code=None,
    is_extension_trial=None,
    is_adaptive_design_null_value_code=None,
    study_stop_rules_null_value_code=None,
    study_type_null_value_code=None,
    trial_type_null_value_code=None,
    is_extension_trial_null_value_code=None,
    trial_phase_null_value_code=None,
    confirmed_response_minimum_duration=None,
    confirmed_response_minimum_duration_null_value_code=None,
)

_DEF_INITIAL_STUDY_POPULATION = StudyPopulationVO(
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
)

_DEF_INITIAL_STUDY_INTERVENTION = StudyInterventionVO(
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
)

_DEF_INITIAL_STUDY_DESCRIPTION = StudyDescriptionVO(
    study_title=None, study_short_title=None
)


@dataclass
class StudyDefinitionAR:
    _uid: str
    study_parent_part_uid: str | None
    study_subpart_uids: list[str]
    _draft_metadata: StudyMetadataVO | None
    _released_metadata: StudyMetadataVO | None

    # index on list corresponds to locked version number (so earliest goes first)
    _locked_metadata_versions: list[StudyMetadataVO]
    _deleted: bool
    _specific_metadata: StudyMetadataVO | None = None

    @property
    def uid(self) -> str:
        return self._uid

    def get_possible_actions(self):
        """
        Returns set of possible actions
        """
        if self.study_status == StudyStatus.DRAFT and not self.latest_locked_metadata:
            if self.study_parent_part_uid:
                return {StudyAction.DELETE}
            return {StudyAction.LOCK, StudyAction.RELEASE, StudyAction.DELETE}
        if (
            self.study_status in [StudyStatus.DRAFT, StudyStatus.RELEASED]
            and not self.study_parent_part_uid
        ):
            return {StudyAction.LOCK, StudyAction.RELEASE}
        if self.study_status == StudyStatus.LOCKED and not self.study_parent_part_uid:
            return {StudyAction.UNLOCK}
        if self.study_status == StudyStatus.DELETED:
            return set()
        return frozenset()

    @property
    def current_metadata(self) -> StudyMetadataVO:
        latest_locked_metadata = self.latest_locked_metadata
        if latest_locked_metadata:
            if (
                self.draft_metadata
                and self._draft_metadata.ver_metadata.version_timestamp
                > latest_locked_metadata.ver_metadata.version_timestamp
            ):
                return self._draft_metadata
            return latest_locked_metadata
        if self.draft_metadata:
            return self._draft_metadata
        return self.released_metadata

    @property
    def version_specific_metadata(self):
        return self._specific_metadata

    @property
    def study_status(self):
        return self.current_metadata.ver_metadata.study_status

    @property
    def released_metadata(self) -> StudyMetadataVO:
        return self._released_metadata

    @property
    def draft_metadata(self) -> StudyMetadataVO:
        return self._draft_metadata

    def _can_edit_metadata(self, raise_error: bool = False) -> bool:
        if self.current_metadata.ver_metadata.study_status != StudyStatus.DRAFT:
            BusinessLogicException.raise_if(
                raise_error, msg=f"Study with UID '{self.uid}' isn't in DRAFT state."
            )
            return False
        return True

    def edit_metadata(
        self,
        *,
        new_id_metadata: StudyIdentificationMetadataVO | None = None,
        new_high_level_study_design: HighLevelStudyDesignVO | None = None,
        new_study_population: StudyPopulationVO | None = None,
        new_study_intervention: StudyInterventionVO | None = None,
        new_study_description: StudyDescriptionVO | None = None,
        therapeutic_area_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("therapeutic_area"),
        disease_condition_or_indication_exists_callback: Callable[[str], bool] = (
            default_failure_callback_for_variable("disease_condition_or_indication")
        ),
        diagnosis_group_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("diagnosis_group"),
        sex_of_participants_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("sex_of_participants"),
        study_number_exists_callback: Callable[[str, str], bool] = (lambda x, y: False),
        project_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("project_number"),
        study_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("study_type"),
        trial_intent_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("trial_intent_type"),
        trial_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("trial_type"),
        trial_phase_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("trial_phase"),
        null_value_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("null_value_code"),
        intervention_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("intervention_type_code"),
        control_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("control_type_code"),
        intervention_model_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("intervention_model_code"),
        trial_blinding_schema_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("trial_blinding_schema_code"),
        study_title_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("study_title"),
        study_short_title_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("study_short_title"),
        author_id: str | None = None,
        is_subpart: bool = False,
        previous_is_subpart: bool = False,
        updatable_subpart: bool = False,
    ) -> None:
        self._can_edit_metadata(raise_error=True)

        new_ver_metadata = StudyVersionMetadataVO(
            study_status=StudyStatus.DRAFT,
            version_number=None,
            version_timestamp=datetime.now(timezone.utc),
            version_author=UserInfoService.get_author_username_from_id(author_id),
        )

        # If nothing is set, we return an error.
        ValidationException.raise_if(
            new_id_metadata is None
            and new_high_level_study_design is None
            and new_study_population is None
            and new_study_intervention is None
            and new_study_description is None,
            msg="No data to patch was provided.",
        )

        # otherwise the call is pointless
        if new_id_metadata is not None:
            if self.latest_locked_metadata is None:
                # if the study has no locked versions study_id_prefix is set after project_number
                new_id_metadata = StudyIdentificationMetadataVO(
                    _study_id_prefix=new_id_metadata.project_number,  # here comes the substitution
                    project_number=new_id_metadata.project_number,
                    study_number=new_id_metadata.study_number,
                    subpart_id=new_id_metadata.subpart_id,
                    study_acronym=new_id_metadata.study_acronym,
                    study_subpart_acronym=new_id_metadata.study_subpart_acronym,
                    description=new_id_metadata.description,
                    registry_identifiers=RegistryIdentifiersVO(
                        ct_gov_id=new_id_metadata.registry_identifiers.ct_gov_id,
                        ct_gov_id_null_value_code=new_id_metadata.registry_identifiers.ct_gov_id_null_value_code,
                        eudract_id=new_id_metadata.registry_identifiers.eudract_id,
                        eudract_id_null_value_code=new_id_metadata.registry_identifiers.eudract_id_null_value_code,
                        universal_trial_number_utn=new_id_metadata.registry_identifiers.universal_trial_number_utn,
                        universal_trial_number_utn_null_value_code=new_id_metadata.registry_identifiers.universal_trial_number_utn_null_value_code,
                        japanese_trial_registry_id_japic=new_id_metadata.registry_identifiers.japanese_trial_registry_id_japic,
                        japanese_trial_registry_id_japic_null_value_code=(
                            new_id_metadata.registry_identifiers.japanese_trial_registry_id_japic_null_value_code
                        ),
                        investigational_new_drug_application_number_ind=(
                            new_id_metadata.registry_identifiers.investigational_new_drug_application_number_ind
                        ),
                        investigational_new_drug_application_number_ind_null_value_code=(
                            new_id_metadata.registry_identifiers.investigational_new_drug_application_number_ind_null_value_code
                        ),
                        eu_trial_number=new_id_metadata.registry_identifiers.eu_trial_number,
                        eu_trial_number_null_value_code=new_id_metadata.registry_identifiers.eu_trial_number_null_value_code,
                        civ_id_sin_number=new_id_metadata.registry_identifiers.civ_id_sin_number,
                        civ_id_sin_number_null_value_code=new_id_metadata.registry_identifiers.civ_id_sin_number_null_value_code,
                        national_clinical_trial_number=new_id_metadata.registry_identifiers.national_clinical_trial_number,
                        national_clinical_trial_number_null_value_code=(
                            new_id_metadata.registry_identifiers.national_clinical_trial_number_null_value_code
                        ),
                        japanese_trial_registry_number_jrct=new_id_metadata.registry_identifiers.japanese_trial_registry_number_jrct,
                        japanese_trial_registry_number_jrct_null_value_code=(
                            new_id_metadata.registry_identifiers.japanese_trial_registry_number_jrct_null_value_code
                        ),
                        national_medical_products_administration_nmpa_number=(
                            new_id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number
                        ),
                        national_medical_products_administration_nmpa_number_null_value_code=(
                            new_id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number_null_value_code
                        ),
                        eudamed_srn_number=new_id_metadata.registry_identifiers.eudamed_srn_number,
                        eudamed_srn_number_null_value_code=new_id_metadata.registry_identifiers.eudamed_srn_number_null_value_code,
                        investigational_device_exemption_ide_number=new_id_metadata.registry_identifiers.investigational_device_exemption_ide_number,
                        investigational_device_exemption_ide_number_null_value_code=(
                            new_id_metadata.registry_identifiers.investigational_device_exemption_ide_number_null_value_code
                        ),
                    ),
                )
            else:
                # if the study has locked versions study_id_prefix stays the same
                new_id_metadata = StudyIdentificationMetadataVO(
                    _study_id_prefix=self.current_metadata.id_metadata.study_id_prefix,  # here comes the substitution
                    project_number=new_id_metadata.project_number,
                    study_number=(
                        new_id_metadata.study_number
                        if is_subpart or previous_is_subpart
                        else self.current_metadata.id_metadata.study_number
                    ),
                    subpart_id=new_id_metadata.subpart_id,
                    study_acronym=new_id_metadata.study_acronym,
                    study_subpart_acronym=new_id_metadata.study_subpart_acronym,
                    description=new_id_metadata.description,
                    registry_identifiers=RegistryIdentifiersVO(
                        ct_gov_id=new_id_metadata.registry_identifiers.ct_gov_id,
                        ct_gov_id_null_value_code=new_id_metadata.registry_identifiers.ct_gov_id_null_value_code,
                        eudract_id=new_id_metadata.registry_identifiers.eudract_id,
                        eudract_id_null_value_code=new_id_metadata.registry_identifiers.eudract_id_null_value_code,
                        universal_trial_number_utn=new_id_metadata.registry_identifiers.universal_trial_number_utn,
                        universal_trial_number_utn_null_value_code=new_id_metadata.registry_identifiers.universal_trial_number_utn_null_value_code,
                        japanese_trial_registry_id_japic=new_id_metadata.registry_identifiers.japanese_trial_registry_id_japic,
                        japanese_trial_registry_id_japic_null_value_code=(
                            new_id_metadata.registry_identifiers.japanese_trial_registry_id_japic_null_value_code
                        ),
                        investigational_new_drug_application_number_ind=(
                            new_id_metadata.registry_identifiers.investigational_new_drug_application_number_ind
                        ),
                        investigational_new_drug_application_number_ind_null_value_code=(
                            new_id_metadata.registry_identifiers.investigational_new_drug_application_number_ind_null_value_code
                        ),
                        eu_trial_number=new_id_metadata.registry_identifiers.eu_trial_number,
                        eu_trial_number_null_value_code=new_id_metadata.registry_identifiers.eu_trial_number_null_value_code,
                        civ_id_sin_number=new_id_metadata.registry_identifiers.civ_id_sin_number,
                        civ_id_sin_number_null_value_code=new_id_metadata.registry_identifiers.civ_id_sin_number_null_value_code,
                        national_clinical_trial_number=new_id_metadata.registry_identifiers.national_clinical_trial_number,
                        national_clinical_trial_number_null_value_code=(
                            new_id_metadata.registry_identifiers.national_clinical_trial_number_null_value_code
                        ),
                        japanese_trial_registry_number_jrct=new_id_metadata.registry_identifiers.japanese_trial_registry_number_jrct,
                        japanese_trial_registry_number_jrct_null_value_code=(
                            new_id_metadata.registry_identifiers.japanese_trial_registry_number_jrct_null_value_code
                        ),
                        national_medical_products_administration_nmpa_number=(
                            new_id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number
                        ),
                        national_medical_products_administration_nmpa_number_null_value_code=(
                            new_id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number_null_value_code
                        ),
                        eudamed_srn_number=new_id_metadata.registry_identifiers.eudamed_srn_number,
                        eudamed_srn_number_null_value_code=new_id_metadata.registry_identifiers.eudamed_srn_number_null_value_code,
                        investigational_device_exemption_ide_number=new_id_metadata.registry_identifiers.investigational_device_exemption_ide_number,
                        investigational_device_exemption_ide_number_null_value_code=(
                            new_id_metadata.registry_identifiers.investigational_device_exemption_ide_number_null_value_code
                        ),
                    ),
                )

            assert new_id_metadata is not None  # making linter happy
            if new_id_metadata != self.current_metadata.id_metadata:
                new_id_metadata.validate(
                    uid=self.uid,
                    project_exists_callback=project_exists_callback,
                    study_number_exists_callback=study_number_exists_callback,
                    is_subpart=is_subpart,
                    previous_is_subpart=previous_is_subpart,
                    updatable_subpart=updatable_subpart,
                    previous_project_number=self.current_metadata.id_metadata.project_number,
                )
                self._draft_metadata = StudyMetadataVO(
                    id_metadata=new_id_metadata,
                    high_level_study_design=self.current_metadata.high_level_study_design,
                    ver_metadata=new_ver_metadata,
                    study_population=self.current_metadata.study_population,
                    study_intervention=self.current_metadata.study_intervention,
                    study_description=self.current_metadata.study_description,
                )

        if (
            new_high_level_study_design is not None
            and new_high_level_study_design
            != self.current_metadata.high_level_study_design
        ):
            new_high_level_study_design.validate(
                study_type_exists_callback=study_type_exists_callback,
                trial_phase_exists_callback=trial_phase_exists_callback,
                trial_type_exists_callback=trial_type_exists_callback,
                trial_intent_type_exists_callback=trial_intent_type_exists_callback,
                null_value_exists_callback=null_value_exists_callback,
            )

            self._draft_metadata = StudyMetadataVO(
                id_metadata=self.current_metadata.id_metadata,
                high_level_study_design=new_high_level_study_design,
                ver_metadata=new_ver_metadata,
                study_population=self.current_metadata.study_population,
                study_intervention=self.current_metadata.study_intervention,
                study_description=self.current_metadata.study_description,
            )

        if (
            new_study_population is not None
            and new_study_population != self.current_metadata.study_population
        ):
            new_study_population.validate(
                null_value_exists_callback=null_value_exists_callback,
                therapeutic_area_exists_callback=therapeutic_area_exists_callback,
                disease_condition_or_indication_exists_callback=disease_condition_or_indication_exists_callback,
                diagnosis_group_exists_callback=diagnosis_group_exists_callback,
                sex_of_participants_exists_callback=sex_of_participants_exists_callback,
            )

            self._draft_metadata = StudyMetadataVO(
                ver_metadata=new_ver_metadata,
                id_metadata=self.current_metadata.id_metadata,
                high_level_study_design=self.current_metadata.high_level_study_design,
                study_population=new_study_population,
                study_intervention=self.current_metadata.study_intervention,
                study_description=self.current_metadata.study_description,
            )

        if (
            new_study_intervention is not None
            and new_study_intervention != self.current_metadata.study_intervention
        ):
            new_study_intervention.validate(
                null_value_exists_callback=null_value_exists_callback,
                intervention_type_exists_callback=intervention_type_exists_callback,
                control_type_exists_callback=control_type_exists_callback,
                intervention_model_exists_callback=intervention_model_exists_callback,
                trial_blinding_schema_exists_callback=trial_blinding_schema_exists_callback,
            )

            self._draft_metadata = StudyMetadataVO(
                ver_metadata=new_ver_metadata,
                id_metadata=self.current_metadata.id_metadata,
                high_level_study_design=self.current_metadata.high_level_study_design,
                study_population=self.current_metadata.study_population,
                study_intervention=new_study_intervention,
                study_description=self.current_metadata.study_description,
            )

        if (
            new_study_description is not None
            and new_study_description != self.current_metadata.study_description
        ):
            new_study_description.validate(
                study_title_exists_callback=study_title_exists_callback,
                study_short_title_exists_callback=study_short_title_exists_callback,
                study_number=self.current_metadata.id_metadata.study_number,
            )

            self._draft_metadata = StudyMetadataVO(
                ver_metadata=new_ver_metadata,
                id_metadata=self.current_metadata.id_metadata,
                high_level_study_design=self.current_metadata.high_level_study_design,
                study_population=self.current_metadata.study_population,
                study_intervention=self.current_metadata.study_intervention,
                study_description=new_study_description,
            )

    def release(
        self, change_description: str | None, author_id: str | None = None
    ) -> None:
        """
        Creates new RELEASED version of study metadata (replacing previous one if exists).
        Only allowed if current state of Study is DRAFT. Current state of the study remains DRAFT.
        """
        current_metadata = self.current_metadata
        BusinessLogicException.raise_if(
            current_metadata.ver_metadata.study_status != StudyStatus.DRAFT,
            msg=f"Study with UID '{self.uid}' isn't in DRAFT state.",
        )

        # we update timestamp on draft metadata (to avoid having draft older then release)
        self._draft_metadata = StudyMetadataVO(
            id_metadata=current_metadata.id_metadata,
            high_level_study_design=current_metadata.high_level_study_design,
            study_population=current_metadata.study_population,
            ver_metadata=StudyVersionMetadataVO(
                study_status=StudyStatus.DRAFT,
                version_timestamp=datetime.now(timezone.utc),
                version_number=None,
                version_author=UserInfoService.get_author_username_from_id(author_id),
            ),
            study_intervention=current_metadata.study_intervention,
            study_description=current_metadata.study_description,
        )
        version_number = (
            Decimal(self.released_metadata.ver_metadata.version_number)
            if self.released_metadata
            else None
        )
        # and replace released metadata
        self._released_metadata = StudyMetadataVO(
            id_metadata=current_metadata.id_metadata,
            high_level_study_design=current_metadata.high_level_study_design,
            study_population=current_metadata.study_population,
            ver_metadata=StudyVersionMetadataVO(
                study_status=StudyStatus.RELEASED,
                version_description=change_description,
                version_number=(
                    Decimal("0.1")
                    if not version_number
                    else version_number + Decimal("0.1")
                ),
                version_timestamp=self.current_metadata.ver_metadata.version_timestamp,
                version_author=UserInfoService.get_author_username_from_id(author_id),
            ),
            study_intervention=current_metadata.study_intervention,
            study_description=current_metadata.study_description,
        )

    def lock(self, version_description: str, author_id: str) -> None:
        current_metadata = self.current_metadata
        ValidationException.raise_if(
            current_metadata.ver_metadata.study_status != StudyStatus.DRAFT,
            msg=f"Study with UID '{self.uid}' isn't in DRAFT state.",
        )

        BusinessLogicException.raise_if(
            not self.study_parent_part_uid
            and (
                current_metadata.id_metadata.study_number is None
                or current_metadata.study_description.study_title is None
            ),
            msg="Both study number and study title must be set before locking.",
        )
        version_number = Decimal(len(self._locked_metadata_versions) + 1)
        # and replace released metadata
        self._released_metadata = StudyMetadataVO(
            id_metadata=current_metadata.id_metadata,
            high_level_study_design=current_metadata.high_level_study_design,
            study_population=current_metadata.study_population,
            ver_metadata=StudyVersionMetadataVO(
                study_status=StudyStatus.RELEASED,
                version_number=version_number,
                version_timestamp=datetime.now(timezone.utc),
                version_description=version_description,
                version_author=UserInfoService.get_author_username_from_id(author_id),
            ),
            study_intervention=current_metadata.study_intervention,
            study_description=current_metadata.study_description,
        )

        # first we create a new locked version
        locked_metadata = StudyMetadataVO(
            id_metadata=current_metadata.id_metadata,
            high_level_study_design=current_metadata.high_level_study_design,
            study_population=current_metadata.study_population,
            ver_metadata=StudyVersionMetadataVO(
                study_status=StudyStatus.LOCKED,
                version_number=version_number,
                version_timestamp=datetime.now(timezone.utc),
                version_description=version_description,
                version_author=UserInfoService.get_author_username_from_id(author_id),
            ),
            study_intervention=current_metadata.study_intervention,
            study_description=current_metadata.study_description,
        )

        # append that version to the list
        self._locked_metadata_versions.append(locked_metadata)

    def unlock(self, author_id: str | None = None) -> None:
        current_metadata = self.current_metadata
        BusinessLogicException.raise_if(
            current_metadata.ver_metadata.study_status != StudyStatus.LOCKED,
            msg=f"Study with UID '{self.uid}' isn't in LOCKED state.",
        )

        # it just takes to create a draft version
        self._draft_metadata = StudyMetadataVO(
            id_metadata=current_metadata.id_metadata,
            high_level_study_design=current_metadata.high_level_study_design,
            study_population=current_metadata.study_population,
            ver_metadata=StudyVersionMetadataVO(
                study_status=StudyStatus.DRAFT,
                version_timestamp=datetime.now(timezone.utc),
                version_author=UserInfoService.get_author_username_from_id(author_id),
            ),
            study_intervention=current_metadata.study_intervention,
            study_description=current_metadata.study_description,
        )

    def mark_deleted(self) -> None:
        BusinessLogicException.raise_if(
            self.latest_locked_metadata is not None,
            msg=f"Study {self.uid}: cannot delete a StudyDefinition having some locked versions.",
        )
        BusinessLogicException.raise_if(
            self.study_subpart_uids,
            msg=f"Study {self.uid}: cannot delete a Study having Study Subparts: {self.study_subpart_uids}.",
        )
        self._deleted = True

    @property
    def latest_locked_metadata(self) -> StudyMetadataVO | None:
        if len(self._locked_metadata_versions) > 0:
            return self._locked_metadata_versions[
                len(self._locked_metadata_versions) - 1
            ]
        return None

    @property
    def latest_released_or_locked_metadata(self) -> StudyMetadataVO | None:
        if self._released_metadata is not None:
            release_timestamp = self._released_metadata.ver_metadata.version_timestamp
        else:
            release_timestamp = None

        if self.latest_locked_metadata is not None:
            locked_timestamp = (
                self.latest_locked_metadata.ver_metadata.version_timestamp
            )
        else:
            locked_timestamp = None
        if release_timestamp is None:
            metadata_to_return = self.latest_locked_metadata
        elif locked_timestamp is None:
            metadata_to_return = self._released_metadata
        elif locked_timestamp >= release_timestamp:
            metadata_to_return = self.latest_locked_metadata
        else:
            metadata_to_return = self._released_metadata
        return metadata_to_return

    def get_all_locked_versions(self) -> list[StudyMetadataVO]:
        # we do copy to assure immutability of list stored inside our instance
        return list(self._locked_metadata_versions)

    def get_specific_locked_metadata_version(
        self, version_number: int
    ) -> StudyMetadataVO:
        ValidationException.raise_if(
            version_number > len(self._locked_metadata_versions),
            msg=f"Study with UID '{self.uid}' has no locked version with number '{version_number}'.",
        )
        return self._locked_metadata_versions[version_number - 1]

    # it would be nice to factor it out to a super class (since we consider each aggregate having this closure)
    # to avoid repeating this lines in every aggregate
    # they are excluded from the constructor and from comparisons either
    # however they are included in repr (so they can be conveniently inspected on console log or what so ever)
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    def get_snapshot(self) -> StudyDefinitionSnapshot:
        """
        :return: a memento (StudyDefinitionSnapshot) object representing a current state of the whole aggregate
            (see Memento design pattern)
        """

        # helper function for creating StudyMetadataSnapshots
        def snapshot_from_study_metadata(
            study_metadata: StudyMetadataVO,
        ) -> StudyDefinitionSnapshot.StudyMetadataSnapshot:
            snapshot_dict = {}
            for config_item in FieldConfiguration.default_field_config():
                if "." in config_item.study_field_grouping:
                    accessors = config_item.study_field_grouping.split(".")
                    value_object = study_metadata
                    for accessor in accessors:
                        value_object = getattr(value_object, accessor)
                else:
                    value_object = getattr(
                        study_metadata, config_item.study_field_grouping
                    )
                value = getattr(value_object, config_item.study_field_name)
                snapshot_dict[config_item.study_field_name] = value
            result = StudyDefinitionSnapshot.StudyMetadataSnapshot(**snapshot_dict)
            return result

        # initiating snapshot
        released_metadata = None
        draft_metadata = None
        locked_metadata_versions = []
        current_metadata = None
        study_status = None
        if self._deleted:
            # short path for deletion
            deleted = True
        else:
            deleted = False

            if self._released_metadata is not None:
                released_metadata = snapshot_from_study_metadata(
                    self._released_metadata
                )
            draft_metadata = snapshot_from_study_metadata(self._draft_metadata)
            # and whatever state there always is a list of locked metadata versions (perhaps empty one)
            locked_metadata_versions = [
                snapshot_from_study_metadata(sm)
                for sm in self._locked_metadata_versions
            ]
            if self.latest_locked_metadata:
                if (
                    locked_metadata_versions[-1].version_timestamp
                    > draft_metadata.version_timestamp
                ):
                    current_metadata = locked_metadata_versions[-1]
                else:
                    current_metadata = draft_metadata
            else:
                current_metadata = draft_metadata
            study_status = self.current_metadata.ver_metadata.study_status.value
        return StudyDefinitionSnapshot(
            uid=self._uid,
            study_parent_part_uid=self.study_parent_part_uid,
            study_subpart_uids=self.study_subpart_uids,
            deleted=deleted,
            released_metadata=released_metadata,
            locked_metadata_versions=locked_metadata_versions,
            current_metadata=current_metadata,
            draft_metadata=draft_metadata,
            study_status=study_status,
        )

    @staticmethod
    def from_snapshot(study_snapshot: StudyDefinitionSnapshot) -> "StudyDefinitionAR":
        """
        A factory static method for rehydrating persisted instance of aggregate.
        Assumes that data are consistent with relevant business rules (does little or no validation).

        :param study_snapshot: a memento (Snapshot) object containing a representation of the Study aggregate

        :return: and instance of StudyDefinitionAR created from above data
        """

        def study_metadata_values_from_snapshot(
            study_metadata_snapshot: StudyDefinitionSnapshot.StudyMetadataSnapshot,
            study_state: StudyStatus,
        ) -> StudyMetadataVO:
            study_metadata_dict = {}
            meta_classes = {}
            for config_item in FieldConfiguration.default_field_config():
                if config_item.study_field_grouping not in study_metadata_dict:
                    study_metadata_dict[config_item.study_field_grouping] = {}
                    meta_classes[config_item.study_field_grouping] = (
                        config_item.study_value_object_class
                    )
                study_metadata_dict[config_item.study_field_grouping][
                    config_item.study_field_name
                ] = getattr(study_metadata_snapshot, config_item.study_field_name)
            study_creation_dict = {}
            for value_object_name, value_object_class in meta_classes.items():
                if value_object_name == "id_metadata":
                    id_metadata = StudyIdentificationMetadataVO(
                        study_number=study_metadata_snapshot.study_number,
                        subpart_id=study_metadata_snapshot.subpart_id,
                        project_number=study_metadata_snapshot.project_number,
                        study_acronym=study_metadata_snapshot.study_acronym,
                        study_subpart_acronym=study_metadata_snapshot.study_subpart_acronym,
                        description=study_metadata_snapshot.description,
                        _study_id_prefix=study_metadata_snapshot.study_id_prefix,
                        registry_identifiers=RegistryIdentifiersVO(
                            ct_gov_id=study_metadata_snapshot.ct_gov_id,
                            ct_gov_id_null_value_code=study_metadata_snapshot.ct_gov_id_null_value_code,
                            eudract_id=study_metadata_snapshot.eudract_id,
                            eudract_id_null_value_code=study_metadata_snapshot.eudract_id_null_value_code,
                            universal_trial_number_utn=study_metadata_snapshot.universal_trial_number_utn,
                            universal_trial_number_utn_null_value_code=study_metadata_snapshot.universal_trial_number_utn_null_value_code,
                            japanese_trial_registry_id_japic=study_metadata_snapshot.japanese_trial_registry_id_japic,
                            japanese_trial_registry_id_japic_null_value_code=(
                                study_metadata_snapshot.japanese_trial_registry_id_japic_null_value_code
                            ),
                            investigational_new_drug_application_number_ind=study_metadata_snapshot.investigational_new_drug_application_number_ind,
                            investigational_new_drug_application_number_ind_null_value_code=(
                                study_metadata_snapshot.investigational_new_drug_application_number_ind_null_value_code
                            ),
                            eu_trial_number=study_metadata_snapshot.eu_trial_number,
                            eu_trial_number_null_value_code=study_metadata_snapshot.eu_trial_number_null_value_code,
                            civ_id_sin_number=study_metadata_snapshot.civ_id_sin_number,
                            civ_id_sin_number_null_value_code=study_metadata_snapshot.civ_id_sin_number_null_value_code,
                            national_clinical_trial_number=study_metadata_snapshot.national_clinical_trial_number,
                            national_clinical_trial_number_null_value_code=(
                                study_metadata_snapshot.national_clinical_trial_number_null_value_code
                            ),
                            japanese_trial_registry_number_jrct=study_metadata_snapshot.japanese_trial_registry_number_jrct,
                            japanese_trial_registry_number_jrct_null_value_code=(
                                study_metadata_snapshot.japanese_trial_registry_number_jrct_null_value_code
                            ),
                            national_medical_products_administration_nmpa_number=(
                                study_metadata_snapshot.national_medical_products_administration_nmpa_number
                            ),
                            national_medical_products_administration_nmpa_number_null_value_code=(
                                study_metadata_snapshot.national_medical_products_administration_nmpa_number_null_value_code
                            ),
                            eudamed_srn_number=study_metadata_snapshot.eudamed_srn_number,
                            eudamed_srn_number_null_value_code=study_metadata_snapshot.eudamed_srn_number_null_value_code,
                            investigational_device_exemption_ide_number=study_metadata_snapshot.investigational_device_exemption_ide_number,
                            investigational_device_exemption_ide_number_null_value_code=(
                                study_metadata_snapshot.investigational_device_exemption_ide_number_null_value_code
                            ),
                        ),
                    )
                    study_creation_dict[value_object_name] = id_metadata
                elif value_object_name == "ver_metadata":
                    ver_metadata = StudyVersionMetadataVO(
                        study_status=study_state,
                        version_number=study_metadata_snapshot.version_number,
                        version_timestamp=study_metadata_snapshot.version_timestamp,
                        version_author=study_metadata_snapshot.version_author,
                        version_description=study_metadata_snapshot.version_description,
                    )
                    study_creation_dict[value_object_name] = ver_metadata
                elif value_object_name != "id_metadata.registry_identifiers":
                    vo_object = value_object_class(
                        **(study_metadata_dict[value_object_name])
                    )
                    study_creation_dict[value_object_name] = vo_object
            return StudyMetadataVO(**study_creation_dict)

        if not study_snapshot.deleted:
            assert study_snapshot.current_metadata is not None
            assert study_snapshot.study_status in (
                StudyStatus.DRAFT.value,
                StudyStatus.RELEASED.value,
            ) or (
                study_snapshot.locked_metadata_versions[
                    len(study_snapshot.locked_metadata_versions) - 1
                ]
                == study_snapshot.current_metadata
            )
            assert study_snapshot.uid is not None

        draft_metadata: StudyMetadataVO | None = None
        released_metadata: StudyMetadataVO | None = None
        specific_metadata: StudyMetadataVO | None = None
        uid = study_snapshot.uid

        if study_snapshot.draft_metadata is not None:
            if study_snapshot.deleted:
                draft_metadata = study_metadata_values_from_snapshot(
                    study_snapshot.draft_metadata, StudyStatus.DELETED
                )
            else:
                draft_metadata = study_metadata_values_from_snapshot(
                    study_snapshot.draft_metadata, StudyStatus.DRAFT
                )
        if study_snapshot.released_metadata is not None:
            released_metadata = study_metadata_values_from_snapshot(
                study_snapshot.released_metadata, StudyStatus.RELEASED
            )

        if study_snapshot.specific_metadata is not None:
            specific_metadata = study_metadata_values_from_snapshot(
                study_snapshot.specific_metadata, StudyStatus.RELEASED
            )

        locked_metadata_versions = [
            study_metadata_values_from_snapshot(
                study_snapshot.locked_metadata_versions[i], StudyStatus.LOCKED
            )
            for i in range(0, len(study_snapshot.locked_metadata_versions))
        ]

        return StudyDefinitionAR(
            _uid=uid,
            study_parent_part_uid=study_snapshot.study_parent_part_uid,
            study_subpart_uids=study_snapshot.study_subpart_uids,
            _draft_metadata=draft_metadata,
            _released_metadata=released_metadata,
            _locked_metadata_versions=locked_metadata_versions,
            _deleted=study_snapshot.deleted,
            _specific_metadata=specific_metadata,
        )

    @staticmethod
    def from_initial_values(
        *,
        generate_uid_callback: Callable[[], str],
        initial_id_metadata: StudyIdentificationMetadataVO,
        project_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("project_number"),
        study_number_exists_callback: Callable[[str, str], bool] = (lambda x, y: False),
        initial_high_level_study_design: HighLevelStudyDesignVO = _DEF_INITIAL_HIGH_LEVEL_STUDY_DESIGN,
        initial_study_population: StudyPopulationVO = _DEF_INITIAL_STUDY_POPULATION,
        initial_study_intervention: StudyInterventionVO = _DEF_INITIAL_STUDY_INTERVENTION,
        initial_study_description: StudyDescriptionVO = _DEF_INITIAL_STUDY_DESCRIPTION,
        therapeutic_area_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("therapeutic_area"),
        disease_condition_or_indication_exists_callback: Callable[[str], bool] = (
            default_failure_callback_for_variable("disease_condition_or_indication")
        ),
        diagnosis_group_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("diagnosis_group"),
        sex_of_participants_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("sex_of_participants"),
        study_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("study_type_code"),
        trial_intent_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("trial_intent_type_code"),
        trial_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("trial_type_code"),
        trial_phase_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("trial_phase_code"),
        null_value_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("null_value_code"),
        intervention_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("intervention_type_code"),
        control_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("control_type_code"),
        intervention_model_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("intervention_model_code"),
        trial_blinding_schema_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("trial_blinding_schema_code"),
        study_title_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("study_title"),
        study_short_title_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("study_short_title"),
        author_id: str | None = None,
        is_subpart: bool = False,
    ) -> Self:
        """
        A factory supporting user story concerned with brand new study creation with some initial information
        provided by the user.

        :param initial_id_metadata: initial identification values for newly created study metadata

        :param project_exists_callback: a callback function for checking of existence of project by given project_number
            initial_id_metadata

        :param study_number_exists_callback: a callback function for checking of existence of study_number in the database

        :param initial_high_level_study_design: stored as current_metadata.high_level_study_design in created object
            (if not provided default value with empty parameters is assumed)

        :param initial_study_population: stored as current_metadata.study_population in created object (if not provided
            default value with empty parameters is assumed)

        :param initial_study_intervention: stored as current_metadata.study_intervention in created object
            (if not provided default value with empty parameters is assumed)

        :param initial_study_description: stored as current_metadata.study_title in created object
            (if not provided default value with empty parameters is assumed)

        :param generate_uid_callback: optional, repository callback to generate unique id (since generating id may
            involve some repository capabilities). If None provided, the instance will be created with None as uid.
            The uid property then can be set later (but only once).

        :param study_type_exists_callback: (optional) callback for checking study_type_codes

        :param trial_intent_type_exists_callback: (optional) callback for checking intent_type_codes

        :param trial_type_exists_callback: (optional) callback for checking trail_type_codes

        :param trial_phase_exists_callback: (optional) callback for checking trial_phase_codes

        :param null_value_exists_callback: (optional) callback for checking null_value_codes

        :param therapeutic_area_exists_callback: (optional) callback for checking therapeutic_area_codes

        :param disease_condition_or_indication_exists_callback: (optional) callback for checking relevant codes

        :param diagnosis_group_exists_callback:  (optional) callback for checking relevant codes

        :param sex_of_participants_exists_callback:  (optional) callback for checking relevant codes

        :param intervention_type_exists_callback:  (optional) callback for checking intervention_type_code

        :param control_type_exists_callback:  (optional) callback for checking control_type_code

        :param intervention_model_exists_callback:  (optional) callback for checking intervention_model_code

        :param trial_blinding_schema_exists_callback:  (optional) callback for checking trial_blinding_schema_code

        :param study_title_exists_callback:  (optional) callback for checking study_title

        :param study_short_title_exists_callback:  (optional) callback for checking study_short_title

        :raises: exceptions.ValidationException -- when passed arguments do not comply with business rules relevant to Study creation

        :return: instance of new StudyDefinitionAR (aggregate root) created from provided initial values
        """

        # when we create a new study we assume study_id_prefix is taken from project_number (aby value provided is lost)
        initial_id_metadata = StudyIdentificationMetadataVO(
            project_number=initial_id_metadata.project_number,
            study_number=initial_id_metadata.study_number,
            subpart_id=initial_id_metadata.subpart_id,
            study_acronym=initial_id_metadata.study_acronym,
            study_subpart_acronym=initial_id_metadata.study_subpart_acronym,
            description=initial_id_metadata.description,
            registry_identifiers=RegistryIdentifiersVO(
                ct_gov_id=initial_id_metadata.registry_identifiers.ct_gov_id,
                ct_gov_id_null_value_code=initial_id_metadata.registry_identifiers.ct_gov_id_null_value_code,
                eudract_id=initial_id_metadata.registry_identifiers.eudract_id,
                eudract_id_null_value_code=initial_id_metadata.registry_identifiers.eudract_id_null_value_code,
                universal_trial_number_utn=initial_id_metadata.registry_identifiers.universal_trial_number_utn,
                universal_trial_number_utn_null_value_code=initial_id_metadata.registry_identifiers.universal_trial_number_utn_null_value_code,
                japanese_trial_registry_id_japic=initial_id_metadata.registry_identifiers.japanese_trial_registry_id_japic,
                japanese_trial_registry_id_japic_null_value_code=(
                    initial_id_metadata.registry_identifiers.japanese_trial_registry_id_japic_null_value_code
                ),
                investigational_new_drug_application_number_ind=(
                    initial_id_metadata.registry_identifiers.investigational_new_drug_application_number_ind
                ),
                investigational_new_drug_application_number_ind_null_value_code=(
                    initial_id_metadata.registry_identifiers.investigational_new_drug_application_number_ind_null_value_code
                ),
                eu_trial_number=initial_id_metadata.registry_identifiers.eu_trial_number,
                eu_trial_number_null_value_code=initial_id_metadata.registry_identifiers.eu_trial_number_null_value_code,
                civ_id_sin_number=initial_id_metadata.registry_identifiers.civ_id_sin_number,
                civ_id_sin_number_null_value_code=initial_id_metadata.registry_identifiers.civ_id_sin_number_null_value_code,
                national_clinical_trial_number=initial_id_metadata.registry_identifiers.national_clinical_trial_number,
                national_clinical_trial_number_null_value_code=(
                    initial_id_metadata.registry_identifiers.national_clinical_trial_number_null_value_code
                ),
                japanese_trial_registry_number_jrct=initial_id_metadata.registry_identifiers.japanese_trial_registry_number_jrct,
                japanese_trial_registry_number_jrct_null_value_code=(
                    initial_id_metadata.registry_identifiers.japanese_trial_registry_number_jrct_null_value_code
                ),
                national_medical_products_administration_nmpa_number=(
                    initial_id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number
                ),
                national_medical_products_administration_nmpa_number_null_value_code=(
                    initial_id_metadata.registry_identifiers.national_medical_products_administration_nmpa_number_null_value_code
                ),
                eudamed_srn_number=initial_id_metadata.registry_identifiers.eudamed_srn_number,
                eudamed_srn_number_null_value_code=initial_id_metadata.registry_identifiers.eudamed_srn_number_null_value_code,
                investigational_device_exemption_ide_number=initial_id_metadata.registry_identifiers.investigational_device_exemption_ide_number,
                investigational_device_exemption_ide_number_null_value_code=(
                    initial_id_metadata.registry_identifiers.investigational_device_exemption_ide_number_null_value_code
                ),
            ),
            _study_id_prefix=initial_id_metadata.project_number,
        )

        initial_study_metadata = StudyMetadataVO(
            id_metadata=initial_id_metadata,
            high_level_study_design=initial_high_level_study_design,
            study_population=initial_study_population,
            study_intervention=initial_study_intervention,
            ver_metadata=StudyVersionMetadataVO(
                study_status=StudyStatus.DRAFT,
                version_number=None,
                version_timestamp=datetime.now(timezone.utc),
                version_author=UserInfoService.get_author_username_from_id(author_id),
            ),
            study_description=initial_study_description,
        )

        initial_study_metadata.validate(
            study_type_exists_callback=study_type_exists_callback,
            trial_phase_exists_callback=trial_phase_exists_callback,
            trial_type_exists_callback=trial_type_exists_callback,
            trial_intent_type_exists_callback=trial_intent_type_exists_callback,
            project_exists_callback=project_exists_callback,
            study_number_exists_callback=study_number_exists_callback,
            null_value_exists_callback=null_value_exists_callback,
            diagnosis_group_exists_callback=diagnosis_group_exists_callback,
            disease_condition_or_indication_exists_callback=disease_condition_or_indication_exists_callback,
            sex_of_participants_exists_callback=sex_of_participants_exists_callback,
            therapeutic_area_exists_callback=therapeutic_area_exists_callback,
            intervention_type_exists_callback=intervention_type_exists_callback,
            control_type_exists_callback=control_type_exists_callback,
            intervention_model_exists_callback=intervention_model_exists_callback,
            trial_blinding_schema_exists_callback=trial_blinding_schema_exists_callback,
            study_title_exists_callback=study_title_exists_callback,
            study_short_title_exists_callback=study_short_title_exists_callback,
            is_subpart=is_subpart,
        )

        # seems all relevant business rules are ok. Now get the uid (using callback)
        # or set to None if no callback provided
        uid = generate_uid_callback()

        # and lets return an instance
        return StudyDefinitionAR(
            _uid=uid,
            study_parent_part_uid=None,
            study_subpart_uids=[],
            _draft_metadata=initial_study_metadata,
            _released_metadata=None,
            _locked_metadata_versions=[],
            _deleted=False,
        )
