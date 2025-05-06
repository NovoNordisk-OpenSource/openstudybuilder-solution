"""Study model."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Callable, Collection, Iterable, Self

from pydantic import ConfigDict, Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domain_repositories.controlled_terminologies import (
    ct_term_generic_repository,
)
from clinical_mdr_api.domains.clinical_programmes.clinical_programme import (
    ClinicalProgrammeAR,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.domains.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domains.projects.project import ProjectAR
from clinical_mdr_api.domains.study_definition_aggregates.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domains.study_definition_aggregates.root import StudyDefinitionAR
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    HighLevelStudyDesignVO,
    StudyDescriptionVO,
    StudyFieldAuditTrailEntryAR,
    StudyIdentificationMetadataVO,
    StudyInterventionVO,
    StudyMetadataVO,
    StudyPopulationVO,
    StudyStatus,
    StudyVersionMetadataVO,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameWithConflictFlag,
    SimpleTermModel,
)
from clinical_mdr_api.models.study_selections.duration import DurationJsonModel
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel
from common import config
from common.exceptions import (
    BusinessLogicException,
    NotFoundException,
    ValidationException,
)


def update_study_subpart_properties(study: "Study | CompactStudy"):
    if study.study_parent_part and study.study_parent_part.study_id:
        study.current_metadata.identification_metadata.study_id = (
            study.study_parent_part.study_id
            + "-"
            + study.current_metadata.identification_metadata.subpart_id
        )


class StudyPreferredTimeUnit(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    study_uid: Annotated[
        str,
        Field(
            description="Uid of study",
            json_schema_extra={"source": "has_after.audit_trail.uid"},
        ),
    ]
    time_unit_uid: Annotated[
        str,
        Field(
            description="Uid of time unit",
            json_schema_extra={"source": "has_unit_definition.uid"},
        ),
    ]
    time_unit_name: Annotated[
        str,
        Field(
            description="Name of time unit",
            json_schema_extra={"source": "has_unit_definition.has_latest_value.name"},
        ),
    ]


class StudyPreferredTimeUnitInput(PatchInputModel):
    unit_definition_uid: Annotated[str, Field(description="Uid of preferred time unit")]


class StudySoaPreferencesInput(PatchInputModel):
    model_config = ConfigDict(
        populate_by_name=True, title="Study SoA Preferences input"
    )

    show_epochs: Annotated[
        bool,
        Field(
            description="Show study epochs in detailed SoA",
            alias=config.STUDY_FIELD_SOA_SHOW_EPOCHS,
        ),
    ] = True
    show_milestones: Annotated[
        bool,
        Field(
            description="Show study milestones in detailed SoA",
            alias=config.STUDY_FIELD_SOA_SHOW_MILESTONES,
        ),
    ] = False
    baseline_as_time_zero: Annotated[
        bool,
        Field(
            title="Baseline shown as time 0",
            description="Show the baseline visit as time 0 in all SoA layouts",
            alias=config.STUDY_FIELD_SOA_BASELINE_AS_TIME_ZERO,
        ),
    ] = False


class StudySoaPreferences(StudySoaPreferencesInput):
    model_config = ConfigDict(populate_by_name=True, title="Study SoA Preferences")

    study_uid: Annotated[str, Field(description="Uid of study")]


class RegistryIdentifiersJsonModel(BaseModel):
    model_config = ConfigDict(
        title="RegistryIdentifiersMetadata",
        description="RegistryIdentifiersMetadata metadata for study definition.",
    )

    ct_gov_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    ct_gov_id_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    eudract_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    eudract_id_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    universal_trial_number_utn: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    universal_trial_number_utn_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    japanese_trial_registry_id_japic: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    japanese_trial_registry_id_japic_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    investigational_new_drug_application_number_ind: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    investigational_new_drug_application_number_ind_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    eu_trial_number: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    eu_trial_number_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    civ_id_sin_number: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    civ_id_sin_number_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    national_clinical_trial_number: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    national_clinical_trial_number_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    japanese_trial_registry_number_jrct: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    japanese_trial_registry_number_jrct_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    national_medical_products_administration_nmpa_number: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    national_medical_products_administration_nmpa_number_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    eudamed_srn_number: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    eudamed_srn_number_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    investigational_device_exemption_ide_number: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    investigational_device_exemption_ide_number_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    @classmethod
    def from_study_registry_identifiers_vo(
        cls,
        registry_identifiers_vo: RegistryIdentifiersVO,
        find_term_by_uids: Callable[[str], CTTermNameAR | None],
        terms_at_specific_datetime: datetime | None = None,
    ) -> Self:
        c_codes = list(
            set(
                [
                    registry_identifiers_vo.ct_gov_id_null_value_code,
                    registry_identifiers_vo.eudract_id_null_value_code,
                    registry_identifiers_vo.universal_trial_number_utn_null_value_code,
                    registry_identifiers_vo.japanese_trial_registry_id_japic_null_value_code,
                    registry_identifiers_vo.investigational_new_drug_application_number_ind_null_value_code,
                    registry_identifiers_vo.eu_trial_number_null_value_code,
                    registry_identifiers_vo.civ_id_sin_number_null_value_code,
                    registry_identifiers_vo.national_clinical_trial_number_null_value_code,
                    registry_identifiers_vo.japanese_trial_registry_number_jrct_null_value_code,
                    registry_identifiers_vo.national_medical_products_administration_nmpa_number_null_value_code,
                    registry_identifiers_vo.eudamed_srn_number_null_value_code,
                    registry_identifiers_vo.investigational_device_exemption_ide_number_null_value_code,
                ]
            )
        )

        if None in c_codes:
            c_codes.remove(None)
        if ct_term_generic_repository.__name__ == find_term_by_uids.__module__:
            terms = {
                term.term_uid: term
                for term in SimpleCTTermNameWithConflictFlag.from_ct_codes(
                    c_codes=c_codes,
                    at_specific_date=terms_at_specific_datetime,
                    find_term_by_uids=find_term_by_uids,
                )
            }
        else:
            terms = {
                c_code: SimpleCTTermNameWithConflictFlag.from_ct_code(
                    c_code=c_code,
                    at_specific_date=terms_at_specific_datetime,
                    find_term_by_uid=find_term_by_uids,
                )
                for c_code in c_codes
            }
        return cls(
            ct_gov_id_null_value_code=(
                terms[registry_identifiers_vo.ct_gov_id_null_value_code]
                if registry_identifiers_vo.ct_gov_id_null_value_code
                else None
            ),
            eudract_id_null_value_code=(
                terms[registry_identifiers_vo.eudract_id_null_value_code]
                if registry_identifiers_vo.eudract_id_null_value_code
                else None
            ),
            universal_trial_number_utn_null_value_code=(
                terms[
                    registry_identifiers_vo.universal_trial_number_utn_null_value_code
                ]
                if registry_identifiers_vo.universal_trial_number_utn_null_value_code
                else None
            ),
            japanese_trial_registry_id_japic_null_value_code=(
                terms[
                    registry_identifiers_vo.japanese_trial_registry_id_japic_null_value_code
                ]
                if registry_identifiers_vo.japanese_trial_registry_id_japic_null_value_code
                else None
            ),
            investigational_new_drug_application_number_ind_null_value_code=(
                terms[
                    registry_identifiers_vo.investigational_new_drug_application_number_ind_null_value_code
                ]
                if registry_identifiers_vo.investigational_new_drug_application_number_ind_null_value_code
                else None
            ),
            eu_trial_number_null_value_code=(
                terms[registry_identifiers_vo.eu_trial_number_null_value_code]
                if registry_identifiers_vo.eu_trial_number_null_value_code
                else None
            ),
            civ_id_sin_number_null_value_code=(
                terms[registry_identifiers_vo.civ_id_sin_number_null_value_code]
                if registry_identifiers_vo.civ_id_sin_number_null_value_code
                else None
            ),
            national_clinical_trial_number_null_value_code=(
                terms[
                    registry_identifiers_vo.national_clinical_trial_number_null_value_code
                ]
                if registry_identifiers_vo.national_clinical_trial_number_null_value_code
                else None
            ),
            japanese_trial_registry_number_jrct_null_value_code=(
                terms[
                    registry_identifiers_vo.japanese_trial_registry_number_jrct_null_value_code
                ]
                if registry_identifiers_vo.japanese_trial_registry_number_jrct_null_value_code
                else None
            ),
            national_medical_products_administration_nmpa_number_null_value_code=(
                terms[
                    registry_identifiers_vo.national_medical_products_administration_nmpa_number_null_value_code
                ]
                if registry_identifiers_vo.national_medical_products_administration_nmpa_number_null_value_code
                else None
            ),
            eudamed_srn_number_null_value_code=(
                terms[registry_identifiers_vo.eudamed_srn_number_null_value_code]
                if registry_identifiers_vo.eudamed_srn_number_null_value_code
                else None
            ),
            investigational_device_exemption_ide_number_null_value_code=(
                terms[
                    registry_identifiers_vo.investigational_device_exemption_ide_number_null_value_code
                ]
                if registry_identifiers_vo.investigational_device_exemption_ide_number_null_value_code
                else None
            ),
            ct_gov_id=registry_identifiers_vo.ct_gov_id,
            eudract_id=registry_identifiers_vo.eudract_id,
            universal_trial_number_utn=registry_identifiers_vo.universal_trial_number_utn,
            japanese_trial_registry_id_japic=registry_identifiers_vo.japanese_trial_registry_id_japic,
            investigational_new_drug_application_number_ind=registry_identifiers_vo.investigational_new_drug_application_number_ind,
            eu_trial_number=registry_identifiers_vo.eu_trial_number,
            civ_id_sin_number=registry_identifiers_vo.civ_id_sin_number,
            national_clinical_trial_number=registry_identifiers_vo.national_clinical_trial_number,
            japanese_trial_registry_number_jrct=registry_identifiers_vo.japanese_trial_registry_number_jrct,
            national_medical_products_administration_nmpa_number=registry_identifiers_vo.national_medical_products_administration_nmpa_number,
            eudamed_srn_number=registry_identifiers_vo.eudamed_srn_number,
            investigational_device_exemption_ide_number=registry_identifiers_vo.investigational_device_exemption_ide_number,
        )


class StudyIdentificationMetadataJsonModel(BaseModel):
    model_config = ConfigDict(
        title="StudyIdentificationMetadata",
        description="Identification metadata for study definition.",
    )

    study_number: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    subpart_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    study_acronym: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_subpart_acronym: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    project_number: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    project_name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    clinical_programme_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    registry_identifiers: Annotated[
        RegistryIdentifiersJsonModel | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_study_identification_vo(
        cls,
        study_identification_o: StudyIdentificationMetadataVO | None,
        find_project_by_project_number: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
        find_term_by_uids: Callable[[str], CTTermNameAR | None],
        terms_at_specific_datetime: datetime | None = None,
    ) -> Self | None:
        if study_identification_o is None:
            return None
        project_ar = find_project_by_project_number(
            study_identification_o.project_number
        )
        BusinessLogicException.raise_if_not(
            project_ar,
            msg=f"There is no Project with Project Number '{study_identification_o.project_number}'.",
        )
        return cls(
            study_number=study_identification_o.study_number,
            subpart_id=study_identification_o.subpart_id,
            study_acronym=study_identification_o.study_acronym,
            study_subpart_acronym=study_identification_o.study_subpart_acronym,
            project_number=study_identification_o.project_number,
            project_name=project_ar.name,
            description=study_identification_o.description,
            clinical_programme_name=find_clinical_programme_by_uid(
                project_ar.clinical_programme_uid
            ).name,
            study_id=study_identification_o.study_id,
            registry_identifiers=RegistryIdentifiersJsonModel.from_study_registry_identifiers_vo(
                study_identification_o.registry_identifiers,
                find_term_by_uids=find_term_by_uids,
                terms_at_specific_datetime=terms_at_specific_datetime,
            ),
        )


class CompactStudyIdentificationMetadataJsonModel(BaseModel):
    model_config = ConfigDict(
        title="CompactStudyIdentificationMetadata",
        description="Identification metadata for study definition.",
    )

    study_number: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    subpart_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    study_acronym: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_subpart_acronym: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    project_number: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    project_name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    clinical_programme_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None

    @classmethod
    def from_study_identification_vo(
        cls,
        study_identification_o: StudyIdentificationMetadataVO | None,
        find_project_by_project_number: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
    ) -> Self | None:
        if study_identification_o is None:
            return None
        project_ar = find_project_by_project_number(
            study_identification_o.project_number
        )
        return cls(
            study_number=study_identification_o.study_number,
            subpart_id=study_identification_o.subpart_id,
            study_acronym=study_identification_o.study_acronym,
            study_subpart_acronym=study_identification_o.study_subpart_acronym,
            project_number=study_identification_o.project_number,
            project_name=project_ar.name if project_ar else None,
            description=study_identification_o.description,
            clinical_programme_name=(
                find_clinical_programme_by_uid(project_ar.clinical_programme_uid).name
                if project_ar
                else None
            ),
            study_id=study_identification_o.study_id,
        )


class StudyVersionMetadataJsonModel(BaseModel):
    model_config = ConfigDict(
        title="StudyVersionMetadata",
        description="Version metadata for study definition.",
    )

    study_status: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    version_number: Annotated[
        Decimal | None, Field(json_schema_extra={"nullable": True})
    ] = None
    version_timestamp: Annotated[
        datetime | None,
        Field(json_schema_extra={"remove_from_wildcard": True, "nullable": True}),
    ] = None
    version_author: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    version_description: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_study_version_metadata_vo(
        cls, study_version_metadata_vo: StudyVersionMetadataVO | None
    ) -> Self | None:
        if study_version_metadata_vo is None:
            return None
        return cls(
            study_status=study_version_metadata_vo.study_status.value,
            version_number=study_version_metadata_vo.version_number,
            version_timestamp=study_version_metadata_vo.version_timestamp,
            version_author=study_version_metadata_vo.version_author,
            version_description=study_version_metadata_vo.version_description,
        )


class HighLevelStudyDesignJsonModel(BaseModel):
    model_config = ConfigDict(
        title="high_level_study_design",
        description="High level study design parameters for study definition.",
    )

    study_type_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    study_type_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    trial_type_codes: Annotated[
        list[SimpleCTTermNameWithConflictFlag] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    trial_type_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    trial_phase_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    trial_phase_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    is_extension_trial: Annotated[
        bool | None, Field(json_schema_extra={"nullable": True})
    ] = None
    is_extension_trial_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    is_adaptive_design: Annotated[
        bool | None, Field(json_schema_extra={"nullable": True})
    ] = None
    is_adaptive_design_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    study_stop_rules: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_stop_rules_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    confirmed_response_minimum_duration: Annotated[
        DurationJsonModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    confirmed_response_minimum_duration_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    post_auth_indicator: Annotated[
        bool | None, Field(json_schema_extra={"nullable": True})
    ] = None
    post_auth_indicator_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    @classmethod
    def from_high_level_study_design_vo(
        cls,
        high_level_study_design_vo: HighLevelStudyDesignVO | None,
        find_term_by_uids: Callable[[str], CTTermNameAR | None],
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
        terms_at_specific_datetime: datetime | None = None,
    ) -> Self | None:
        if high_level_study_design_vo is None:
            return None

        c_codes = list(
            set(
                [
                    high_level_study_design_vo.study_type_code,
                    high_level_study_design_vo.study_type_null_value_code,
                    high_level_study_design_vo.trial_type_null_value_code,
                    high_level_study_design_vo.trial_phase_code,
                    high_level_study_design_vo.trial_phase_null_value_code,
                    high_level_study_design_vo.is_extension_trial_null_value_code,
                    high_level_study_design_vo.is_adaptive_design_null_value_code,
                    high_level_study_design_vo.study_stop_rules_null_value_code,
                    high_level_study_design_vo.confirmed_response_minimum_duration_null_value_code,
                    high_level_study_design_vo.post_auth_indicator_null_value_code,
                ]
                + high_level_study_design_vo.trial_type_codes
            )
        )

        if None in c_codes:
            c_codes.remove(None)
        if ct_term_generic_repository.__name__ == find_term_by_uids.__module__:
            terms = {
                term.term_uid: term
                for term in SimpleCTTermNameWithConflictFlag.from_ct_codes(
                    c_codes=c_codes,
                    at_specific_date=terms_at_specific_datetime,
                    find_term_by_uids=find_term_by_uids,
                )
            }
        else:
            terms = {
                c_code: SimpleCTTermNameWithConflictFlag.from_ct_code(
                    c_code=c_code,
                    at_specific_date=terms_at_specific_datetime,
                    find_term_by_uid=find_term_by_uids,
                )
                for c_code in c_codes
            }
        return cls(
            study_type_code=(
                terms[high_level_study_design_vo.study_type_code]
                if high_level_study_design_vo.study_type_code
                else None
            ),
            study_type_null_value_code=(
                terms[high_level_study_design_vo.study_type_null_value_code]
                if high_level_study_design_vo.study_type_null_value_code
                else None
            ),
            trial_type_codes=[
                terms[i_code] for i_code in high_level_study_design_vo.trial_type_codes
            ],
            trial_type_null_value_code=(
                terms[high_level_study_design_vo.trial_type_null_value_code]
                if high_level_study_design_vo.trial_type_null_value_code
                else None
            ),
            trial_phase_code=(
                terms[high_level_study_design_vo.trial_phase_code]
                if high_level_study_design_vo.trial_phase_code
                else None
            ),
            trial_phase_null_value_code=(
                terms[high_level_study_design_vo.trial_phase_null_value_code]
                if high_level_study_design_vo.trial_phase_null_value_code
                else None
            ),
            is_extension_trial_null_value_code=(
                terms[high_level_study_design_vo.is_extension_trial_null_value_code]
                if high_level_study_design_vo.is_extension_trial_null_value_code
                else None
            ),
            is_adaptive_design_null_value_code=(
                terms[high_level_study_design_vo.is_adaptive_design_null_value_code]
                if high_level_study_design_vo.is_adaptive_design_null_value_code
                else None
            ),
            study_stop_rules_null_value_code=(
                terms[high_level_study_design_vo.study_stop_rules_null_value_code]
                if high_level_study_design_vo.study_stop_rules_null_value_code
                else None
            ),
            confirmed_response_minimum_duration_null_value_code=(
                terms[
                    high_level_study_design_vo.confirmed_response_minimum_duration_null_value_code
                ]
                if high_level_study_design_vo.confirmed_response_minimum_duration_null_value_code
                else None
            ),
            post_auth_indicator_null_value_code=(
                terms[high_level_study_design_vo.post_auth_indicator_null_value_code]
                if high_level_study_design_vo.post_auth_indicator_null_value_code
                else None
            ),
            confirmed_response_minimum_duration=(
                DurationJsonModel.from_duration_object(
                    duration=high_level_study_design_vo.confirmed_response_minimum_duration,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if high_level_study_design_vo.confirmed_response_minimum_duration
                is not None
                else None
            ),
            is_extension_trial=high_level_study_design_vo.is_extension_trial,
            is_adaptive_design=high_level_study_design_vo.is_adaptive_design,
            study_stop_rules=high_level_study_design_vo.study_stop_rules,
            post_auth_indicator=high_level_study_design_vo.post_auth_indicator,
        )


class StudyPopulationJsonModel(BaseModel):
    model_config = ConfigDict(
        title="study_population",
        description="Study population parameters for study definition.",
    )

    therapeutic_area_codes: Annotated[
        list[SimpleTermModel] | None, Field(json_schema_extra={"nullable": True})
    ] = None
    therapeutic_area_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    disease_condition_or_indication_codes: Annotated[
        list[SimpleTermModel] | None, Field(json_schema_extra={"nullable": True})
    ] = None
    disease_condition_or_indication_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    diagnosis_group_codes: Annotated[
        list[SimpleTermModel] | None, Field(json_schema_extra={"nullable": True})
    ] = None
    diagnosis_group_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    sex_of_participants_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    sex_of_participants_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    rare_disease_indicator: Annotated[
        bool | None, Field(json_schema_extra={"nullable": True})
    ] = None
    rare_disease_indicator_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    healthy_subject_indicator: Annotated[
        bool | None, Field(json_schema_extra={"nullable": True})
    ] = None
    healthy_subject_indicator_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    planned_minimum_age_of_subjects: Annotated[
        DurationJsonModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    planned_minimum_age_of_subjects_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    planned_maximum_age_of_subjects: Annotated[
        DurationJsonModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    planned_maximum_age_of_subjects_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    stable_disease_minimum_duration: Annotated[
        DurationJsonModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    stable_disease_minimum_duration_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    pediatric_study_indicator: Annotated[
        bool | None, Field(json_schema_extra={"nullable": True})
    ] = None
    pediatric_study_indicator_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    pediatric_postmarket_study_indicator: Annotated[
        bool | None, Field(json_schema_extra={"nullable": True})
    ] = None
    pediatric_postmarket_study_indicator_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    pediatric_investigation_plan_indicator: Annotated[
        bool | None, Field(json_schema_extra={"nullable": True})
    ] = None
    pediatric_investigation_plan_indicator_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    relapse_criteria: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    relapse_criteria_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    number_of_expected_subjects: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    number_of_expected_subjects_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    @classmethod
    def from_study_population_vo(
        cls,
        study_population_vo: StudyPopulationVO | None,
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
        find_term_by_uids: Callable[[str], CTTermNameAR | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        terms_at_specific_datetime: datetime | None = None,
    ) -> Self | None:
        if study_population_vo is None:
            return None

        c_codes = list(
            set(
                [
                    study_population_vo.therapeutic_area_null_value_code,
                    study_population_vo.diagnosis_group_null_value_code,
                    study_population_vo.disease_condition_or_indication_null_value_code,
                    study_population_vo.sex_of_participants_code,
                    study_population_vo.sex_of_participants_null_value_code,
                    study_population_vo.rare_disease_indicator_null_value_code,
                    study_population_vo.healthy_subject_indicator_null_value_code,
                    study_population_vo.planned_minimum_age_of_subjects_null_value_code,
                    study_population_vo.planned_maximum_age_of_subjects_null_value_code,
                    study_population_vo.stable_disease_minimum_duration_null_value_code,
                    study_population_vo.pediatric_study_indicator_null_value_code,
                    study_population_vo.pediatric_postmarket_study_indicator_null_value_code,
                    study_population_vo.pediatric_investigation_plan_indicator_null_value_code,
                    study_population_vo.relapse_criteria_null_value_code,
                    study_population_vo.number_of_expected_subjects_null_value_code,
                ]
            )
        )

        if None in c_codes:
            c_codes.remove(None)
        if ct_term_generic_repository.__name__ == find_term_by_uids.__module__:
            terms = {
                term.term_uid: term
                for term in SimpleCTTermNameWithConflictFlag.from_ct_codes(
                    c_codes=c_codes,
                    at_specific_date=terms_at_specific_datetime,
                    find_term_by_uids=find_term_by_uids,
                )
            }
        else:
            terms = {
                c_code: SimpleCTTermNameWithConflictFlag.from_ct_code(
                    c_code=c_code,
                    at_specific_date=terms_at_specific_datetime,
                    find_term_by_uid=find_term_by_uids,
                )
                for c_code in c_codes
            }
        return cls(
            therapeutic_area_null_value_code=(
                terms[study_population_vo.therapeutic_area_null_value_code]
                if study_population_vo.therapeutic_area_null_value_code
                else None
            ),
            diagnosis_group_null_value_code=(
                terms[study_population_vo.diagnosis_group_null_value_code]
                if study_population_vo.diagnosis_group_null_value_code
                else None
            ),
            disease_condition_or_indication_null_value_code=(
                terms[
                    study_population_vo.disease_condition_or_indication_null_value_code
                ]
                if study_population_vo.disease_condition_or_indication_null_value_code
                else None
            ),
            sex_of_participants_code=(
                terms[study_population_vo.sex_of_participants_code]
                if study_population_vo.sex_of_participants_code
                else None
            ),
            sex_of_participants_null_value_code=(
                terms[study_population_vo.sex_of_participants_null_value_code]
                if study_population_vo.sex_of_participants_null_value_code
                else None
            ),
            rare_disease_indicator_null_value_code=(
                terms[study_population_vo.rare_disease_indicator_null_value_code]
                if study_population_vo.rare_disease_indicator_null_value_code
                else None
            ),
            healthy_subject_indicator_null_value_code=(
                terms[study_population_vo.healthy_subject_indicator_null_value_code]
                if study_population_vo.healthy_subject_indicator_null_value_code
                else None
            ),
            planned_minimum_age_of_subjects_null_value_code=(
                terms[
                    study_population_vo.planned_minimum_age_of_subjects_null_value_code
                ]
                if study_population_vo.planned_minimum_age_of_subjects_null_value_code
                else None
            ),
            planned_maximum_age_of_subjects_null_value_code=(
                terms[
                    study_population_vo.planned_maximum_age_of_subjects_null_value_code
                ]
                if study_population_vo.planned_maximum_age_of_subjects_null_value_code
                else None
            ),
            stable_disease_minimum_duration_null_value_code=(
                terms[
                    study_population_vo.stable_disease_minimum_duration_null_value_code
                ]
                if study_population_vo.stable_disease_minimum_duration_null_value_code
                else None
            ),
            pediatric_study_indicator_null_value_code=(
                terms[study_population_vo.pediatric_study_indicator_null_value_code]
                if study_population_vo.pediatric_study_indicator_null_value_code
                else None
            ),
            pediatric_postmarket_study_indicator_null_value_code=(
                terms[
                    study_population_vo.pediatric_postmarket_study_indicator_null_value_code
                ]
                if study_population_vo.pediatric_postmarket_study_indicator_null_value_code
                else None
            ),
            pediatric_investigation_plan_indicator_null_value_code=(
                terms[
                    study_population_vo.pediatric_investigation_plan_indicator_null_value_code
                ]
                if study_population_vo.pediatric_investigation_plan_indicator_null_value_code
                else None
            ),
            relapse_criteria_null_value_code=(
                terms[study_population_vo.relapse_criteria_null_value_code]
                if study_population_vo.relapse_criteria_null_value_code
                else None
            ),
            number_of_expected_subjects_null_value_code=(
                terms[study_population_vo.number_of_expected_subjects_null_value_code]
                if study_population_vo.number_of_expected_subjects_null_value_code
                else None
            ),
            therapeutic_area_codes=[
                SimpleTermModel.from_ct_code(
                    c_code=therapeutic_area_code,
                    find_term_by_uid=find_dictionary_term_by_uid,
                    at_specific_date=terms_at_specific_datetime,
                )
                for therapeutic_area_code in study_population_vo.therapeutic_area_codes
            ],
            disease_condition_or_indication_codes=[
                SimpleTermModel.from_ct_code(
                    c_code=disease_or_indication_code,
                    find_term_by_uid=find_dictionary_term_by_uid,
                    at_specific_date=terms_at_specific_datetime,
                )
                for disease_or_indication_code in study_population_vo.disease_condition_or_indication_codes
            ],
            diagnosis_group_codes=[
                SimpleTermModel.from_ct_code(
                    c_code=diagnosis_group_code,
                    find_term_by_uid=find_dictionary_term_by_uid,
                    at_specific_date=terms_at_specific_datetime,
                )
                for diagnosis_group_code in study_population_vo.diagnosis_group_codes
            ],
            planned_minimum_age_of_subjects=(
                DurationJsonModel.from_duration_object(
                    duration=study_population_vo.planned_minimum_age_of_subjects,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if study_population_vo.planned_minimum_age_of_subjects is not None
                else None
            ),
            planned_maximum_age_of_subjects=(
                DurationJsonModel.from_duration_object(
                    duration=study_population_vo.planned_maximum_age_of_subjects,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if study_population_vo.planned_maximum_age_of_subjects is not None
                else None
            ),
            stable_disease_minimum_duration=(
                DurationJsonModel.from_duration_object(
                    duration=study_population_vo.stable_disease_minimum_duration,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if study_population_vo.stable_disease_minimum_duration is not None
                else None
            ),
            rare_disease_indicator=study_population_vo.rare_disease_indicator,
            healthy_subject_indicator=study_population_vo.healthy_subject_indicator,
            pediatric_study_indicator=study_population_vo.pediatric_study_indicator,
            pediatric_postmarket_study_indicator=study_population_vo.pediatric_postmarket_study_indicator,
            pediatric_investigation_plan_indicator=study_population_vo.pediatric_investigation_plan_indicator,
            relapse_criteria=study_population_vo.relapse_criteria,
            number_of_expected_subjects=study_population_vo.number_of_expected_subjects,
        )


class StudyInterventionJsonModel(BaseModel):
    model_config = ConfigDict(
        title="study_intervention",
        description="Study interventions parameters for study definition.",
    )

    intervention_type_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    intervention_type_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    add_on_to_existing_treatments: Annotated[
        bool | None, Field(json_schema_extra={"nullable": True})
    ] = None
    add_on_to_existing_treatments_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    control_type_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    control_type_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    intervention_model_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    intervention_model_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    is_trial_randomised: Annotated[
        bool | None, Field(json_schema_extra={"nullable": True})
    ] = None
    is_trial_randomised_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    stratification_factor: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    stratification_factor_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    trial_blinding_schema_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    trial_blinding_schema_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    planned_study_length: Annotated[
        DurationJsonModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    planned_study_length_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    trial_intent_types_codes: Annotated[
        list[SimpleCTTermNameWithConflictFlag] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    trial_intent_types_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    @classmethod
    def from_study_intervention_vo(
        cls,
        study_intervention_vo: StudyInterventionVO | None,
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
        find_term_by_uids: Callable[[str], CTTermNameAR | None],
        terms_at_specific_datetime: datetime | None = None,
    ) -> Self | None:
        if study_intervention_vo is None:
            return None
        c_codes = list(
            set(
                [
                    study_intervention_vo.intervention_type_code,
                    study_intervention_vo.intervention_type_null_value_code,
                    study_intervention_vo.add_on_to_existing_treatments_null_value_code,
                    study_intervention_vo.control_type_code,
                    study_intervention_vo.control_type_null_value_code,
                    study_intervention_vo.intervention_model_code,
                    study_intervention_vo.intervention_model_null_value_code,
                    study_intervention_vo.is_trial_randomised_null_value_code,
                    study_intervention_vo.stratification_factor_null_value_code,
                    study_intervention_vo.trial_blinding_schema_code,
                    study_intervention_vo.trial_blinding_schema_null_value_code,
                    study_intervention_vo.planned_study_length_null_value_code,
                    study_intervention_vo.trial_intent_type_null_value_code,
                ]
                + study_intervention_vo.trial_intent_types_codes
            )
        )
        if None in c_codes:
            c_codes.remove(None)
        if ct_term_generic_repository.__name__ == find_term_by_uids.__module__:
            terms = {
                term.term_uid: term
                for term in SimpleCTTermNameWithConflictFlag.from_ct_codes(
                    c_codes=c_codes,
                    at_specific_date=terms_at_specific_datetime,
                    find_term_by_uids=find_term_by_uids,
                )
            }
        else:
            terms = {
                c_code: SimpleCTTermNameWithConflictFlag.from_ct_code(
                    c_code=c_code,
                    at_specific_date=terms_at_specific_datetime,
                    find_term_by_uid=find_term_by_uids,
                )
                for c_code in c_codes
            }
        return cls(
            intervention_type_code=(
                terms[study_intervention_vo.intervention_type_code]
                if study_intervention_vo.intervention_type_code
                else None
            ),
            intervention_type_null_value_code=(
                terms[study_intervention_vo.intervention_type_null_value_code]
                if study_intervention_vo.intervention_type_null_value_code
                else None
            ),
            add_on_to_existing_treatments=study_intervention_vo.add_on_to_existing_treatments,
            add_on_to_existing_treatments_null_value_code=(
                terms[
                    study_intervention_vo.add_on_to_existing_treatments_null_value_code
                ]
                if study_intervention_vo.add_on_to_existing_treatments_null_value_code
                else None
            ),
            control_type_code=(
                terms[study_intervention_vo.control_type_code]
                if study_intervention_vo.control_type_code
                else None
            ),
            control_type_null_value_code=(
                terms[study_intervention_vo.control_type_null_value_code]
                if study_intervention_vo.control_type_null_value_code
                else None
            ),
            intervention_model_code=(
                terms[study_intervention_vo.intervention_model_code]
                if study_intervention_vo.intervention_model_code
                else None
            ),
            intervention_model_null_value_code=(
                terms[study_intervention_vo.intervention_model_null_value_code]
                if study_intervention_vo.intervention_model_null_value_code
                else None
            ),
            is_trial_randomised=study_intervention_vo.is_trial_randomised,
            is_trial_randomised_null_value_code=(
                terms[study_intervention_vo.is_trial_randomised_null_value_code]
                if study_intervention_vo.is_trial_randomised_null_value_code
                else None
            ),
            stratification_factor=study_intervention_vo.stratification_factor,
            stratification_factor_null_value_code=(
                terms[study_intervention_vo.stratification_factor_null_value_code]
                if study_intervention_vo.stratification_factor_null_value_code
                else None
            ),
            trial_blinding_schema_code=(
                terms[study_intervention_vo.trial_blinding_schema_code]
                if study_intervention_vo.trial_blinding_schema_code
                else None
            ),
            trial_blinding_schema_null_value_code=(
                terms[study_intervention_vo.trial_blinding_schema_null_value_code]
                if study_intervention_vo.trial_blinding_schema_null_value_code
                else None
            ),
            planned_study_length_null_value_code=(
                terms[study_intervention_vo.planned_study_length_null_value_code]
                if study_intervention_vo.planned_study_length_null_value_code
                else None
            ),
            trial_intent_types_codes=[
                terms[i_code]
                for i_code in study_intervention_vo.trial_intent_types_codes
            ],
            trial_intent_types_null_value_code=(
                terms[study_intervention_vo.trial_intent_type_null_value_code]
                if study_intervention_vo.trial_intent_type_null_value_code
                else None
            ),
            planned_study_length=(
                DurationJsonModel.from_duration_object(
                    duration=study_intervention_vo.planned_study_length,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if study_intervention_vo.planned_study_length is not None
                else None
            ),
        )


class StudyDescriptionJsonModel(BaseModel):
    model_config = ConfigDict(
        title="study_description",
        description="Study description for the study definition.",
    )

    study_title: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    study_short_title: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_study_description_vo(
        cls, study_description_vo: StudyDescriptionVO | None
    ) -> Self | None:
        if study_description_vo is None:
            return None
        return cls(
            study_title=study_description_vo.study_title,
            study_short_title=study_description_vo.study_short_title,
        )


class CompactStudyMetadataJsonModel(BaseModel):
    model_config = ConfigDict(title="StudyMetadata", description="Study metadata")

    identification_metadata: Annotated[
        CompactStudyIdentificationMetadataJsonModel | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    version_metadata: Annotated[
        StudyVersionMetadataJsonModel | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    study_description: Annotated[
        StudyDescriptionJsonModel | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_study_metadata_vo(
        cls,
        study_metadata_vo: StudyMetadataVO,
        find_project_by_project_number: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
    ) -> Self:
        return cls(
            identification_metadata=CompactStudyIdentificationMetadataJsonModel.from_study_identification_vo(
                study_identification_o=study_metadata_vo.id_metadata,
                find_project_by_project_number=find_project_by_project_number,
                find_clinical_programme_by_uid=find_clinical_programme_by_uid,
            ),
            version_metadata=StudyVersionMetadataJsonModel.from_study_version_metadata_vo(
                study_version_metadata_vo=study_metadata_vo.ver_metadata
            ),
            study_description=StudyDescriptionJsonModel.from_study_description_vo(
                study_description_vo=study_metadata_vo.study_description
            ),
        )


class StudyMetadataJsonModel(BaseModel):
    model_config = ConfigDict(title="StudyMetadata", description="Study metadata")

    identification_metadata: Annotated[
        StudyIdentificationMetadataJsonModel | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    version_metadata: Annotated[
        StudyVersionMetadataJsonModel | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    high_level_study_design: Annotated[
        HighLevelStudyDesignJsonModel | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    study_population: Annotated[
        StudyPopulationJsonModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_intervention: Annotated[
        StudyInterventionJsonModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_description: Annotated[
        StudyDescriptionJsonModel | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_study_metadata_vo(
        cls,
        study_metadata_vo: StudyMetadataVO,
        find_project_by_project_number: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
        find_term_by_uids: Callable[[str], CTTermNameAR | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        terms_at_specific_datetime: datetime | None = None,
    ) -> Self:
        return cls(
            identification_metadata=StudyIdentificationMetadataJsonModel.from_study_identification_vo(
                study_identification_o=study_metadata_vo.id_metadata,
                find_project_by_project_number=find_project_by_project_number,
                find_clinical_programme_by_uid=find_clinical_programme_by_uid,
                find_term_by_uids=find_term_by_uids,
                terms_at_specific_datetime=terms_at_specific_datetime,
            ),
            version_metadata=StudyVersionMetadataJsonModel.from_study_version_metadata_vo(
                study_version_metadata_vo=study_metadata_vo.ver_metadata
            ),
            high_level_study_design=HighLevelStudyDesignJsonModel.from_high_level_study_design_vo(
                high_level_study_design_vo=study_metadata_vo.high_level_study_design,
                find_term_by_uids=find_term_by_uids,
                find_all_study_time_units=find_all_study_time_units,
                terms_at_specific_datetime=terms_at_specific_datetime,
            ),
            study_population=StudyPopulationJsonModel.from_study_population_vo(
                study_population_vo=study_metadata_vo.study_population,
                find_all_study_time_units=find_all_study_time_units,
                find_term_by_uids=find_term_by_uids,
                find_dictionary_term_by_uid=find_dictionary_term_by_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            ),
            study_intervention=StudyInterventionJsonModel.from_study_intervention_vo(
                study_intervention_vo=study_metadata_vo.study_intervention,
                find_all_study_time_units=find_all_study_time_units,
                terms_at_specific_datetime=terms_at_specific_datetime,
                find_term_by_uids=find_term_by_uids,
            ),
            study_description=StudyDescriptionJsonModel.from_study_description_vo(
                study_description_vo=study_metadata_vo.study_description
            ),
        )


class StudyPatchRequestJsonModel(PatchInputModel):
    model_config = ConfigDict(
        title="StudyPatchRequest",
        description="Identification metadata for study definition.",
    )

    study_parent_part_uid: Annotated[
        str | None, Field(description="UID of the Study Parent Part")
    ] = None
    current_metadata: Annotated[
        StudyMetadataJsonModel | None, Field(json_schema_extra={"nullable": True})
    ] = None


class StudyParentPart(BaseModel):
    uid: str
    study_number: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    study_acronym: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    project_number: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    study_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    study_title: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    registry_identifiers: RegistryIdentifiersJsonModel

    @classmethod
    def from_study_uid(
        cls,
        study_uid: str | None,
        find_study_parent_part_by_uid: Callable[[str], StudyDefinitionAR | None],
        find_term_by_uids: Callable[[str], CTTermNameAR | None],
    ) -> Self:
        if not study_uid:
            return None

        NotFoundException.raise_if_not(
            rs := find_study_parent_part_by_uid(study_uid),
            "Study Parent Part",
            study_uid,
        )

        return cls(
            uid=rs.uid,
            study_number=rs.current_metadata.id_metadata.study_number,
            study_acronym=rs.current_metadata.id_metadata.study_acronym,
            project_number=rs.current_metadata.id_metadata.project_number,
            description=rs.current_metadata.id_metadata.description,
            study_id=rs.current_metadata.id_metadata.study_id,
            study_title=rs.current_metadata.study_description.study_title,
            registry_identifiers=RegistryIdentifiersJsonModel.from_study_registry_identifiers_vo(
                rs.current_metadata.id_metadata.registry_identifiers,
                find_term_by_uids,
            ),
        )


class StudyStructureOverview(BaseModel):
    study_ids: list[str]
    arms: Annotated[int, Field(title="Number of Study Arms")]
    pre_treatment_epochs: Annotated[
        int, Field(title="Number of Study Pre Treatment Epochs")
    ]
    treatment_epochs: Annotated[int, Field(title="Number of Treatment Epochs")]
    no_treatment_epochs: Annotated[int, Field(title="Number of No Treatment Epochs")]
    post_treatment_epochs: Annotated[
        int, Field(title="Number of Post Treatment Epochs")
    ]
    treatment_elements: Annotated[int, Field(title="Number of Treatment Elements")]
    no_treatment_elements: Annotated[
        int, Field(title="Number of No Treatment Elements")
    ]
    cohorts_in_study: str


class CompactStudy(BaseModel):
    uid: Annotated[
        str,
        Field(
            description="The unique id of the study.",
            json_schema_extra={"remove_from_wildcard": True},
        ),
    ]
    study_parent_part: Annotated[
        StudyParentPart | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_subpart_uids: list[str]
    possible_actions: Annotated[
        list[str],
        Field(
            description=(
                "Holds those actions that can be performed on the ActivityInstances. "
                "Actions are: 'lock', 'release', 'unlock', 'delete'."
            )
        ),
    ]
    current_metadata: Annotated[
        CompactStudyMetadataJsonModel | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    @classmethod
    def from_study_definition_ar(
        cls,
        study_definition_ar: StudyDefinitionAR,
        find_project_by_project_number: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
        find_study_parent_part_by_uid: Callable[[str], StudyDefinitionAR | None],
        find_term_by_uids: Callable[[str], CTTermNameAR | None],
    ) -> Self:
        study = cls(
            uid=study_definition_ar.uid,
            study_parent_part=StudyParentPart.from_study_uid(
                study_definition_ar.study_parent_part_uid,
                find_study_parent_part_by_uid,
                find_term_by_uids,
            ),
            study_subpart_uids=sorted(study_definition_ar.study_subpart_uids),
            possible_actions=sorted(
                [_.value for _ in study_definition_ar.get_possible_actions()]
            ),
            current_metadata=CompactStudyMetadataJsonModel.from_study_metadata_vo(
                study_metadata_vo=study_definition_ar.current_metadata,
                find_project_by_project_number=find_project_by_project_number,
                find_clinical_programme_by_uid=find_clinical_programme_by_uid,
            ),
        )

        update_study_subpart_properties(study)

        return study


class Study(BaseModel):
    uid: Annotated[str, Field(description="The unique id of the study.")]
    study_parent_part: Annotated[
        StudyParentPart | None,
        Field(json_schema_extra={"nullable": True}),
    ]
    study_subpart_uids: list[str]
    possible_actions: Annotated[
        list[str],
        Field(
            description=(
                "Holds those actions that can be performed on the ActivityInstances. "
                "Actions are: 'lock', 'release', 'unlock', 'delete'."
            )
        ),
    ]
    current_metadata: Annotated[
        StudyMetadataJsonModel | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_study_definition_ar(
        cls,
        study_definition_ar: StudyDefinitionAR,
        find_project_by_project_number: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
        find_study_parent_part_by_uid: Callable[[str], StudyDefinitionAR | None],
        find_term_by_uids: Callable[[str], CTTermNameAR | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        # pylint: disable=unused-argument
        at_specified_date_time: datetime | None = None,
        study_value_version: str | None = None,
        status: StudyStatus | None = None,
        history_endpoint: bool = False,
        terms_at_specific_datetime: datetime | None = None,
    ) -> Self | None:
        current_metadata = None
        if status is not None:
            if status == StudyStatus.DRAFT:
                current_metadata = study_definition_ar.draft_metadata
            elif status == StudyStatus.RELEASED:
                current_metadata = study_definition_ar.released_metadata
            elif status == StudyStatus.LOCKED:
                current_metadata = study_definition_ar.latest_locked_metadata
        elif study_value_version is not None:
            current_metadata = study_definition_ar.version_specific_metadata
        else:
            current_metadata = study_definition_ar.current_metadata
        if current_metadata is None:
            ValidationException.raise_if_not(
                history_endpoint,
                msg=f"Study with UID '{study_definition_ar.uid}' doesn't have a version for status '{status}' and version '{study_value_version}'.",
            )
            return None
        is_metadata_the_last_one = bool(
            study_definition_ar.current_metadata == current_metadata
        )
        study = cls(
            uid=study_definition_ar.uid,
            study_parent_part=StudyParentPart.from_study_uid(
                study_definition_ar.study_parent_part_uid,
                find_study_parent_part_by_uid,
                find_term_by_uids,
            ),
            study_subpart_uids=sorted(study_definition_ar.study_subpart_uids),
            possible_actions=sorted(
                [_.value for _ in study_definition_ar.get_possible_actions()]
                if is_metadata_the_last_one
                else []
            ),
            current_metadata=StudyMetadataJsonModel.from_study_metadata_vo(
                study_metadata_vo=current_metadata,
                find_project_by_project_number=find_project_by_project_number,
                find_clinical_programme_by_uid=find_clinical_programme_by_uid,
                find_all_study_time_units=find_all_study_time_units,
                find_term_by_uids=find_term_by_uids,
                find_dictionary_term_by_uid=find_dictionary_term_by_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            ),
        )

        update_study_subpart_properties(study)

        return study


class StudyStructureStatistics(BaseModel):

    arm_count: Annotated[int, Field(description="Number of connected arms")]
    branch_count: Annotated[int, Field(description="Number of connected branches")]
    cohort_count: Annotated[int, Field(description="Number of connected cohorts")]
    element_count: Annotated[int, Field(description="Number of connected elements")]
    epoch_count: Annotated[int, Field(description="Number of connected epochs")]
    epoch_footnote_count: Annotated[
        int, Field(description="Number of connected footnotes (epoch level)")
    ]
    visit_count: Annotated[int, Field(description="Number of connected visits")]
    visit_footnote_count: Annotated[
        int, Field(description="Number of connected footnotes (visit level)")
    ]


class StudyCreateInput(PostInputModel):
    study_number: str | None = None

    study_acronym: str | None = None

    project_number: Annotated[str, Field(min_length=1)]

    description: str | None = None


class StudyCloneInput(StudyCreateInput):
    copy_study_arm: bool = False
    copy_study_branch_arm: bool = False
    copy_study_cohort: bool = False
    copy_study_element: bool = False
    copy_study_visit: bool = False
    copy_study_visits_study_footnote: bool = False
    copy_study_epoch: bool = False
    copy_study_epochs_study_footnote: bool = False
    copy_study_design_matrix: bool = False


class StudySubpartCreateInput(PostInputModel):
    study_subpart_acronym: Annotated[str, Field(min_length=1)]

    description: str | None = None

    study_parent_part_uid: Annotated[str, Field(min_length=1)]


class StatusChangeDescription(BaseModel):
    change_description: Annotated[
        str, Field(description="The description of the Study status change.")
    ]


class StudyFieldAuditTrailAction(BaseModel):
    section: Annotated[
        str, Field(description="The section that the modified study field is in.")
    ]

    field: Annotated[
        str, Field(description="The name of the study field that was changed.")
    ]

    before_value: Annotated[
        SimpleTermModel | None,
        Field(
            description="The value of the field before the edit.",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    after_value: Annotated[
        SimpleTermModel, Field(description="The value of the field after the edit.")
    ]

    action: Annotated[
        str,
        Field(
            description="The action taken on the study field. One of (Create, edit, delete...)"
        ),
    ]


class StudyFieldAuditTrailEntry(BaseModel):
    study_uid: Annotated[
        str | None,
        Field(
            description="The unique id of the study.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    date: Annotated[
        str | None,
        Field(
            description="The date that the edit was made.",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    actions: Annotated[
        list[StudyFieldAuditTrailAction] | None,
        Field(
            description="The actions that took place as part of this audit trial entry.",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_study_field_audit_trail_vo(
        cls,
        study_field_audit_trail_vo: StudyFieldAuditTrailEntryAR,
        sections_selected: Collection[str],
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
    ) -> Self:
        actions: list[StudyFieldAuditTrailAction] = [
            StudyFieldAuditTrailAction(
                section=action.section,
                field=action.field_name,
                action=action.action,
                before_value=SimpleTermModel.from_ct_code(
                    c_code=action.before_value, find_term_by_uid=find_term_by_uid
                ),
                after_value=SimpleTermModel.from_ct_code(
                    c_code=action.after_value, find_term_by_uid=find_term_by_uid
                ),
            )
            for action in study_field_audit_trail_vo.actions
            if action.section in sections_selected
        ]
        return cls(
            study_uid=study_field_audit_trail_vo.study_uid,
            actions=actions,
            author_username=study_field_audit_trail_vo.author_username,
            date=study_field_audit_trail_vo.date,
        )


class StudyProtocolTitle(BaseModel):
    study_uid: Annotated[
        str | None,
        Field(
            description="The unique id of the study.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    study_title: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    study_short_title: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    eudract_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    universal_trial_number_utn: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    trial_phase_code: Annotated[
        SimpleTermModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    ind_number: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    substance_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_study_definition_ar(
        cls,
        study_definition_ar: StudyDefinitionAR,
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
        study_value_version: str | None = None,
    ) -> Self:
        if study_value_version is not None:
            current_metadata = study_definition_ar.version_specific_metadata
        else:
            current_metadata = study_definition_ar.current_metadata
        return cls(
            study_uid=study_definition_ar.uid,
            study_title=current_metadata.study_description.study_title,
            study_short_title=current_metadata.study_description.study_short_title,
            eudract_id=current_metadata.id_metadata.registry_identifiers.eudract_id,
            universal_trial_number_utn=current_metadata.id_metadata.registry_identifiers.universal_trial_number_utn,
            trial_phase_code=SimpleTermModel.from_ct_code(
                c_code=current_metadata.high_level_study_design.trial_phase_code,
                find_term_by_uid=find_term_by_uid,
            ),
            ind_number=current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_ind,
        )


class StudySubpartReorderingInput(PatchInputModel):
    uid: Annotated[str, Field(description="UID of the Study Subpart.")]
    subpart_id: Annotated[
        str,
        Field(
            description="A single lowercase letter from 'a' to 'z' representing the Subpart ID.",
            max_length=1,
            pattern="[a-z]",
        ),
    ]


class StudySubpartAuditTrail(BaseModel):
    subpart_uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    subpart_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    study_acronym: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_subpart_acronym: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    start_date: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    end_date: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    change_type: str
    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []
