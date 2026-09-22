"""Study model."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Callable, Collection, Self, overload

from pydantic import ConfigDict, Field, model_validator

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
from clinical_mdr_api.domains.enums import LibraryItemStatus, ValidationMode
from clinical_mdr_api.domains.projects.project import ProjectAR
from clinical_mdr_api.domains.study_definition_aggregates.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domains.study_definition_aggregates.root import StudyDefinitionAR
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    HighLevelStudyDesignVO,
    StudyComponentEnum,
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
from clinical_mdr_api.models.controlled_terminologies.ct_term_name import (
    TSParameterRequiredLevel,
)
from clinical_mdr_api.models.study_selections.duration import DurationJsonModel
from clinical_mdr_api.models.utils import (
    BaseModel,
    BatchInputModel,
    EditInputModel,
    PatchInputModel,
    PostInputModel,
)
from common.config import settings
from common.exceptions import (
    BusinessLogicException,
    NotFoundException,
    ValidationException,
)
from common.utils import convert_to_datetime


def update_study_subpart_properties(study: "Study | CompactStudy"):
    if (
        study.study_parent_part
        and study.study_parent_part.study_id
        and study.current_metadata.identification_metadata.study_subpart_acronym
        is not None
    ):
        study.current_metadata.identification_metadata.study_id = (
            study.study_parent_part.study_id
            + "-"
            + study.current_metadata.identification_metadata.study_subpart_acronym
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

    show_epochs: bool = Field(  # type: ignore[literal-required]
        True,
        description="Show study epochs in detailed SoA",
        alias=settings.study_field_soa_show_epochs,
    )
    show_milestones: bool = Field(  # type: ignore[literal-required]
        False,
        description="Show study milestones in detailed SoA",
        alias=settings.study_field_soa_show_milestones,
    )
    baseline_as_time_zero: bool = Field(  # type: ignore[literal-required]
        False,
        description="Show the baseline visit as time 0 in all SoA layouts",
        alias=settings.study_field_soa_baseline_as_time_zero,
    )
    show_all_visits_lab_table: bool = Field(  # type: ignore[literal-required]
        False,
        description="Show all visits in protocol lab table SoA (incl. those without lab assessments)",
        alias=settings.study_field_soa_show_all_visits_lab_table,
    )


class StudySoaPreferences(StudySoaPreferencesInput):
    model_config = ConfigDict(populate_by_name=True, title="Study SoA Preferences")

    study_uid: Annotated[str, Field(description="Uid of study")]


class StudySoaSplitInput(PatchInputModel):
    model_config = ConfigDict(title="SoA Split uid input")
    uid: Annotated[str, Field(description="Uid of a StudyVisit")]


class StudySoaSplit(StudySoaSplitInput):
    model_config = ConfigDict(title="SoA Split uid")
    study_uid: Annotated[str, Field(description="Uid of study")]


class StudyOtherAttributeInput(PostInputModel):
    """Input payload for create/update of a Study Other Attribute selection.

    Exactly one of ``parameter_value`` or ``null_flavor_term_uid`` should be
    provided. All other columns shown in the UI table are derived from the
    referenced TS-parameter CT term (codelists `C66738` / `C67152`).
    """

    model_config = ConfigDict(title="Study Other Attribute input")

    ts_parameter_term_uid: Annotated[
        str,
        Field(
            min_length=1,
            description="UID of the Trial Summary parameter CTTermRoot "
            "(member of codelist `C66738` or `C67152`).",
        ),
    ]
    parameter_value: Annotated[
        str | bool | None,
        Field(
            description="Value for the parameter. Send a JSON boolean for Boolean "
            "attributes, an ISO 8601 string for Date/DateTime/Time attributes, "
            "or a plain string for text attributes.",
        ),
    ] = None
    null_flavor_term_uid: Annotated[
        str | None,
        Field(
            description="UID of the CTTermRoot used as Null Flavor "
            "(from the `NULLFLVR` codelist).",
        ),
    ] = None

    @model_validator(mode="after")
    def check_xor(self) -> Self:
        if self.parameter_value is not None and self.null_flavor_term_uid is not None:
            raise ValueError(
                "Provide either 'parameter_value' or 'null_flavor_term_uid', not both."
            )
        if self.parameter_value is None and self.null_flavor_term_uid is None:
            raise ValueError(
                "Provide either 'parameter_value' or 'null_flavor_term_uid'; both cannot be empty."
            )
        return self


class StudyOtherAttributePatchInput(PatchInputModel):
    """PATCH payload for an existing Study Other Attribute selection."""

    model_config = ConfigDict(title="Study Other Attribute patch input")

    parameter_value: Annotated[
        str | bool | None,
        Field(
            description="Value for the parameter. Send a JSON boolean for Boolean "
            "attributes, an ISO 8601 string for Date/DateTime/Time attributes, "
            "or a plain string for text attributes.",
        ),
    ] = None
    null_flavor_term_uid: Annotated[str | None, Field()] = None

    @model_validator(mode="after")
    def check_xor(self) -> Self:
        if self.parameter_value is not None and self.null_flavor_term_uid is not None:
            raise ValueError(
                "Provide either 'parameter_value' or 'null_flavor_term_uid', not both."
            )
        if self.parameter_value is None and self.null_flavor_term_uid is None:
            raise ValueError(
                "Provide either 'parameter_value' or 'null_flavor_term_uid'; both cannot be empty."
            )
        return self


class OtherAttributeResponseCodelist(BaseModel):
    """Reference to a CT codelist (response codelist) for an Other Attribute."""

    model_config = ConfigDict(title="Other Attribute Response Codelist")

    uid: Annotated[str, Field(description="UID of the response CTCodelistRoot.")]
    sponsor_preferred_name: Annotated[
        str | None,
        Field(
            description="Sponsor preferred name of the response codelist.",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class OtherAttributeNullFlavor(BaseModel):
    """Reference to the selected Null Flavor CT term for an Other Attribute."""

    model_config = ConfigDict(title="Other Attribute Null Flavor")

    uid: Annotated[str, Field(description="UID of the Null Flavor CTTermRoot.")]
    sponsor_preferred_name: Annotated[
        str | None,
        Field(
            description="Sponsor preferred name of the Null Flavor CT term.",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class StudyOtherAttributeColumns(BaseModel):
    """Flat projection of one DB row for Other Study Attributes.

    Field names match the Cypher RETURN aliases so that
    ``CypherQueryBuilder`` can validate filter/sort keys against this model.
    """

    ts_parameter_term_uid: Annotated[str, Field()] = ""
    code: Annotated[str | None, Field()] = None
    parameter: Annotated[str | None, Field()] = None
    reference: Annotated[str | None, Field()] = None
    required_level: Annotated[TSParameterRequiredLevel | None, Field()] = None
    semantic_data_type: Annotated[str | None, Field()] = None
    response_codelist_uid: Annotated[str | None, Field()] = None
    response_codelist_name: Annotated[str | None, Field()] = None
    notes: Annotated[str | None, Field()] = None
    parameter_value: Annotated[str | None, Field()] = None
    null_flavor_term_uid: Annotated[str | None, Field()] = None
    null_flavor_term_name: Annotated[str | None, Field()] = None
    start_date: Annotated[datetime | None, Field()] = None
    author_username: Annotated[str | None, Field()] = None


class StudyOtherAttribute(BaseModel):
    """One row of the Study Other Attributes table.

    Columns marked as *derived* are read-only and come from the linked CT term
    in the TS-parameter codelists (C66738 / C67152) and its
    `RELATED_STUDY_FIELD_SELECTION` MetaStudyField.
    """

    model_config = ConfigDict(title="Study Other Attribute")

    study_uid: Annotated[str, Field(description="UID of the study.")]
    ts_parameter_term_uid: Annotated[
        str, Field(description="UID of the TS parameter CTTermRoot.")
    ]
    code: Annotated[
        str | None,
        Field(description="Submission value of the CT term (derived)."),
    ] = None
    parameter: Annotated[
        str | None,
        Field(description="Name of the CT term (derived)."),
    ] = None
    reference: Annotated[str | None, Field()] = None
    required_level: Annotated[
        TSParameterRequiredLevel | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    semantic_data_type: Annotated[str | None, Field()] = None
    response_codelist: Annotated[
        OtherAttributeResponseCodelist | None,
        Field(
            description="Response codelist referenced by the CT term (derived).",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    notes: Annotated[str | None, Field()] = None
    parameter_value: Annotated[
        str | bool | None,
        Field(
            description="Value selected by the study. Returns a JSON boolean for "
            "Boolean attributes, an ISO 8601 string for Date/DateTime/Time "
            "attributes, or a plain string for text attributes (None if not set).",
        ),
    ] = None
    null_flavor: Annotated[
        OtherAttributeNullFlavor | None,
        Field(
            description="Selected Null Flavor CT term (None if not set).",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    start_date: Annotated[
        datetime | None,
        Field(
            description="The most recent point in time when the attribute was edited.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    author_username: Annotated[
        str | None,
        Field(
            description="Version author.",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class StudyOtherAttributeDeleteInput(BaseModel):
    """DELETE payload for a batch operation on a Study Other Attribute."""

    model_config = ConfigDict(extra="forbid")

    ts_parameter_term_uid: Annotated[
        str,
        Field(
            min_length=1,
            description="UID of the TS parameter CTTermRoot to delete.",
        ),
    ]


class StudyOtherAttributeBatchInput(BatchInputModel):
    """Single operation in a batch request for Study Other Attributes.

    For POST: content must be a StudyOtherAttributeInput (ts_parameter_term_uid + value/null_flavor).
    For PATCH: content must be a StudyOtherAttributeInput (ts_parameter_term_uid identifies the target).
    For DELETE: content must be a StudyOtherAttributeDeleteInput (ts_parameter_term_uid only).
    """

    method: Annotated[
        str,
        Field(
            description="HTTP method corresponding to operation type",
            pattern="^(POST|PATCH|DELETE)$",
        ),
    ]
    content: Annotated[
        StudyOtherAttributeInput | StudyOtherAttributeDeleteInput,
        Field(description="Payload matching the method type."),
    ]


class StudyOtherAttributeBatchOutput(BaseModel):
    """Result of one operation in a batch request for Study Other Attributes."""

    response_code: Annotated[
        int, Field(description="The HTTP response code related to input operation")
    ]
    content: Annotated[
        StudyOtherAttribute | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None


class StudyTemplateInput(PostInputModel):
    study_uid: Annotated[str, Field(min_length=1, description="Uid of template study")]
    study_value_version: Annotated[
        str,
        Field(
            min_length=1,
            description="Study value version of template study, e.g. '1.0'",
        ),
    ]


class StudyTemplatePatchInput(EditInputModel):
    study_uid: Annotated[
        str,
        Field(
            description="Uid of template study; empty string clears the configured target",
        ),
    ]
    study_value_version: Annotated[
        str,
        Field(
            description="Released study value version; required when study_uid is non-empty",
        ),
    ]

    @model_validator(mode="after")
    def _study_version_required_when_study_uid_set(self) -> Self:
        if self.study_uid.strip() and not self.study_value_version.strip():
            raise ValueError(
                "study_value_version is required when study_uid is non-empty"
            )
        return self


class StudyTemplate(BaseModel):
    uid: Annotated[str, Field(description="Uid of study template root")]
    study_uid: Annotated[str, Field(description="Uid of template study")]
    study_value_version: Annotated[str, Field(description="Study value version")]
    status: Annotated[LibraryItemStatus, Field(description="Template item status")]
    version: Annotated[str, Field(description="Template item version")]
    change_description: Annotated[str, Field(description="Version change description")]


class RegistryIdentifiersJsonModel(BaseModel):

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
    eu_pas_number: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    eu_pas_number_null_value_code: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    @classmethod
    def from_study_registry_identifiers_vo(
        cls,
        registry_identifiers_vo: RegistryIdentifiersVO,
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
        terms_at_specific_datetime: datetime | None = None,
    ) -> Self:
        c_codes = [
            code
            for code in list(
                {
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
                    registry_identifiers_vo.eu_pas_number_null_value_code,
                }
            )
            if code is not None
        ]

        terms: dict[str, SimpleCTTermNameWithConflictFlag]

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
                    c_code=c_code or "",
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
            eu_pas_number_null_value_code=(
                terms[registry_identifiers_vo.eu_pas_number_null_value_code]
                if registry_identifiers_vo.eu_pas_number_null_value_code
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
            eu_pas_number=registry_identifiers_vo.eu_pas_number,
        )


class StudyIdentificationMetadataJsonModel(BaseModel):

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
        str | None,
        Field(
            json_schema_extra={"nullable": True},
        ),
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

    @overload
    @classmethod
    def from_study_identification_vo(
        cls,
        study_identification_o: StudyIdentificationMetadataVO,
        find_project_by_project_number: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
        terms_at_specific_datetime: datetime | None = None,
    ) -> Self: ...
    @overload
    @classmethod
    def from_study_identification_vo(
        cls,
        study_identification_o: None,
        find_project_by_project_number: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
        terms_at_specific_datetime: datetime | None = None,
    ) -> None: ...
    @classmethod
    def from_study_identification_vo(
        cls,
        study_identification_o: StudyIdentificationMetadataVO | None,
        find_project_by_project_number: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
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

    development_stage_code: Annotated[
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

    @overload
    @classmethod
    def from_high_level_study_design_vo(
        cls,
        high_level_study_design_vo: HighLevelStudyDesignVO,
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
        find_all_study_time_units: Callable[[str], tuple[list[UnitDefinitionAR], int]],
        terms_at_specific_datetime: datetime | None = None,
    ) -> Self: ...
    @overload
    @classmethod
    def from_high_level_study_design_vo(
        cls,
        high_level_study_design_vo: None,
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
        find_all_study_time_units: Callable[[str], tuple[list[UnitDefinitionAR], int]],
        terms_at_specific_datetime: datetime | None = None,
    ) -> None: ...
    @classmethod
    def from_high_level_study_design_vo(
        cls,
        high_level_study_design_vo: HighLevelStudyDesignVO | None,
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
        find_all_study_time_units: Callable[[str], tuple[list[UnitDefinitionAR], int]],
        terms_at_specific_datetime: datetime | None = None,
    ) -> Self | None:
        if high_level_study_design_vo is None:
            return None

        _c_codes = list(
            {
                high_level_study_design_vo.study_type_code,
                high_level_study_design_vo.study_type_null_value_code,
                high_level_study_design_vo.trial_type_null_value_code,
                high_level_study_design_vo.trial_phase_code,
                high_level_study_design_vo.trial_phase_null_value_code,
                high_level_study_design_vo.development_stage_code,
                high_level_study_design_vo.is_extension_trial_null_value_code,
                high_level_study_design_vo.is_adaptive_design_null_value_code,
                high_level_study_design_vo.study_stop_rules_null_value_code,
                high_level_study_design_vo.confirmed_response_minimum_duration_null_value_code,
                high_level_study_design_vo.post_auth_indicator_null_value_code,
            }
        )

        for trial_type_code in high_level_study_design_vo.trial_type_codes:
            if trial_type_code is not None:
                _c_codes.append(trial_type_code)

        c_codes = [code for code in _c_codes if code is not None]

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
                    c_code=c_code or "",
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
            development_stage_code=(
                terms[high_level_study_design_vo.development_stage_code]
                if high_level_study_design_vo.development_stage_code
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

    @overload
    @classmethod
    def from_study_population_vo(
        cls,
        study_population_vo: StudyPopulationVO,
        find_all_study_time_units: Callable[[str], tuple[list[UnitDefinitionAR], int]],
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        terms_at_specific_datetime: datetime | None = None,
    ) -> Self: ...
    @overload
    @classmethod
    def from_study_population_vo(
        cls,
        study_population_vo: None,
        find_all_study_time_units: Callable[[str], tuple[list[UnitDefinitionAR], int]],
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        terms_at_specific_datetime: datetime | None = None,
    ) -> None: ...
    @classmethod
    def from_study_population_vo(
        cls,
        study_population_vo: StudyPopulationVO | None,
        find_all_study_time_units: Callable[[str], tuple[list[UnitDefinitionAR], int]],
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        terms_at_specific_datetime: datetime | None = None,
    ) -> Self | None:
        if study_population_vo is None:
            return None

        c_codes = [
            code
            for code in list(
                {
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
                }
            )
            if code is not None
        ]

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
                    c_code=c_code or "",
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

    @overload
    @classmethod
    def from_study_intervention_vo(
        cls,
        study_intervention_vo: StudyInterventionVO,
        find_all_study_time_units: Callable[[str], tuple[list[UnitDefinitionAR], int]],
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
        terms_at_specific_datetime: datetime | None = None,
    ) -> Self: ...
    @overload
    @classmethod
    def from_study_intervention_vo(
        cls,
        study_intervention_vo: None,
        find_all_study_time_units: Callable[[str], tuple[list[UnitDefinitionAR], int]],
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
        terms_at_specific_datetime: datetime | None = None,
    ) -> None: ...
    @classmethod
    def from_study_intervention_vo(
        cls,
        study_intervention_vo: StudyInterventionVO | None,
        find_all_study_time_units: Callable[[str], tuple[list[UnitDefinitionAR], int]],
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
        terms_at_specific_datetime: datetime | None = None,
    ) -> Self | None:
        if study_intervention_vo is None:
            return None

        _c_codes = list(
            {
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
            }
        )

        for trial_intent_types_code in study_intervention_vo.trial_intent_types_codes:
            if trial_intent_types_code is not None:
                _c_codes.append(trial_intent_types_code)

        c_codes = [code for code in _c_codes if code is not None]

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
                    c_code=c_code or "",
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

    study_title: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    study_short_title: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @overload
    @classmethod
    def from_study_description_vo(
        cls, study_description_vo: StudyDescriptionVO
    ) -> Self: ...
    @overload
    @classmethod
    def from_study_description_vo(cls, study_description_vo: None) -> None: ...
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
        find_all_study_time_units: Callable[[str], tuple[list[UnitDefinitionAR], int]],
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        terms_at_specific_datetime: datetime | None = None,
        needed_sections: set[str] | None = None,
    ) -> Self:
        def _should_build(section: str) -> bool:
            return needed_sections is None or section in needed_sections

        return cls(
            identification_metadata=(
                StudyIdentificationMetadataJsonModel.from_study_identification_vo(
                    study_identification_o=study_metadata_vo.id_metadata,
                    find_project_by_project_number=find_project_by_project_number,
                    find_clinical_programme_by_uid=find_clinical_programme_by_uid,
                    find_term_by_uids=find_term_by_uids,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
                if _should_build(StudyComponentEnum.IDENTIFICATION_METADATA.value)
                else None
            ),
            version_metadata=(
                StudyVersionMetadataJsonModel.from_study_version_metadata_vo(
                    study_version_metadata_vo=study_metadata_vo.ver_metadata
                )
                if _should_build(StudyComponentEnum.VERSION_METADATA.value)
                else None
            ),
            high_level_study_design=(
                HighLevelStudyDesignJsonModel.from_high_level_study_design_vo(
                    high_level_study_design_vo=study_metadata_vo.high_level_study_design,
                    find_term_by_uids=find_term_by_uids,
                    find_all_study_time_units=find_all_study_time_units,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
                if _should_build(StudyComponentEnum.STUDY_DESIGN.value)
                else None
            ),
            study_population=(
                StudyPopulationJsonModel.from_study_population_vo(
                    study_population_vo=study_metadata_vo.study_population,
                    find_all_study_time_units=find_all_study_time_units,
                    find_term_by_uids=find_term_by_uids,
                    find_dictionary_term_by_uid=find_dictionary_term_by_uid,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
                if _should_build(StudyComponentEnum.STUDY_POPULATION.value)
                else None
            ),
            study_intervention=(
                StudyInterventionJsonModel.from_study_intervention_vo(
                    study_intervention_vo=study_metadata_vo.study_intervention,
                    find_all_study_time_units=find_all_study_time_units,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                    find_term_by_uids=find_term_by_uids,
                )
                if _should_build(StudyComponentEnum.STUDY_INTERVENTION.value)
                else None
            ),
            study_description=(
                StudyDescriptionJsonModel.from_study_description_vo(
                    study_description_vo=study_metadata_vo.study_description
                )
                if _should_build(StudyComponentEnum.STUDY_DESCRIPTION.value)
                else None
            ),
        )


class StudyPatchRequestJsonModel(PatchInputModel):

    study_parent_part_uid: Annotated[
        str | None, Field(description="UID of the Study Parent Part")
    ] = None
    current_metadata: Annotated[
        StudyMetadataJsonModel | None, Field(json_schema_extra={"nullable": True})
    ] = None


class StudyParentPart(BaseModel):
    uid: Annotated[str, Field()]
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
    registry_identifiers: Annotated[RegistryIdentifiersJsonModel, Field()]

    @classmethod
    def from_study_uid(
        cls,
        study_uid: str | None,
        find_study_parent_part_by_uid: Callable[[str], StudyDefinitionAR | None],
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
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
    study_ids: Annotated[list[str], Field()]
    arms: Annotated[int, Field(description="Number of Study Arms")]
    pre_treatment_epochs: Annotated[
        int, Field(description="Number of Study Pre Treatment Epochs")
    ]
    treatment_epochs: Annotated[int, Field(description="Number of Treatment Epochs")]
    no_treatment_epochs: Annotated[
        int, Field(description="Number of No Treatment Epochs")
    ]
    post_treatment_epochs: Annotated[
        int, Field(description="Number of Post Treatment Epochs")
    ]
    treatment_elements: Annotated[
        int, Field(description="Number of Treatment Elements")
    ]
    no_treatment_elements: Annotated[
        int, Field(description="Number of No Treatment Elements")
    ]
    cohorts_in_study: Annotated[str, Field()]


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
    study_subpart_uids: Annotated[list[str], Field()]
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
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
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


class StudyVersionHistory(BaseModel):
    study_status: Annotated[
        list[StudyStatus],
        Field(description="List of StudyStatuses for specific study version"),
    ]
    reason_for_lock_name: Annotated[
        str | None,
        Field(
            description="Name of the selected Reason For Lock Sponsor CTTerm",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    reason_for_unlock_name: Annotated[
        str | None,
        Field(
            description="Name of the selected Reason For Unlock Sponsor CTTerm",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    metadata_version: Annotated[
        str | None,
        Field(
            description="Metadata version associated with a given Study version",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    original_metadata_version: Annotated[
        str | None,
        Field(
            description="Metadata version of the first occurrence for the same protocol header version",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    protocol_header_major_version: Annotated[
        int | None,
        Field(
            description="Major protocol header version associated with a given Study version",
            json_schema_extra={"nullable": True},
            ge=0,
            lt=settings.max_int_neo4j,
        ),
    ] = None
    protocol_header_minor_version: Annotated[
        int | None,
        Field(
            description="Minor protocol header version associated with a given Study version",
            json_schema_extra={"nullable": True},
            ge=0,
            lt=settings.max_int_neo4j,
        ),
    ] = None
    description: Annotated[
        str | None,
        Field(
            description="Description of the released/locked version",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    other_reason_for_unlocking: Annotated[
        str | None,
        Field(
            description="Other description for unlocking",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    other_reason_for_locking_releasing: Annotated[
        str | None,
        Field(
            description="Other description for locking&releasing",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    modified_date: Annotated[
        datetime, Field(description="Datetime when the Study version was modified")
    ]
    modified_by: Annotated[
        str,
        Field(description="Initials of the person who made given Study version change"),
    ]

    @classmethod
    def from_repository_output(
        cls,
        val: dict[str, Any],
    ) -> Self:
        return cls(
            study_status=[StudyStatus(status) for status in val["statuses"]],
            reason_for_lock_name=val.get("reason_for_lock"),
            reason_for_unlock_name=val.get("reason_for_unlock"),
            metadata_version=val.get("metadata_version"),
            original_metadata_version=val.get("original_metadata_version"),
            protocol_header_major_version=val.get("protocol_header_major_version"),
            protocol_header_minor_version=val.get("protocol_header_minor_version"),
            description=val.get("description"),
            other_reason_for_unlocking=val.get("other_reason_for_unlocking"),
            other_reason_for_locking_releasing=val.get("other_reason_for_lock_release"),
            modified_date=convert_to_datetime(value=val["date"]),
            modified_by=val["modified_by"],
        )


class StudyMinimal(BaseModel):
    uid: Annotated[str, Field(description="UID of the study, e.g. 'Study_000001'")]
    id: Annotated[
        str | None,
        Field(
            description="ID of the study, e.g. 'XX1234-56789'",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    acronym: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    subpart_acronym: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_input(
        cls,
        val: dict[str, Any],
    ) -> Self:
        return cls(
            uid=val["uid"],
            acronym=val["acronym"],
            subpart_acronym=val["subpart_acronym"],
            id=val["id"],
        )


class StudySimple(StudyMinimal):
    class VersionInfo(BaseModel):
        version_number: Annotated[
            str | None, Field(json_schema_extra={"nullable": True})
        ] = None
        change_description: Annotated[
            str | None, Field(json_schema_extra={"nullable": True})
        ] = None

    main_id: Annotated[
        str | None,
        Field(
            description="Main ID of the study, e.g. 'XX1234-56789'",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    number: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    title: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    subpart_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    subpart_acronym: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    clinical_programme_name: Annotated[str, Field()]
    project_number: Annotated[str, Field()]
    project_name: Annotated[str, Field()]
    version_author: Annotated[str, Field()]
    version_status: Annotated[StudyStatus, Field()]
    version_start_date: Annotated[datetime, Field()]
    version_number: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    latest_locked_version: Annotated[
        VersionInfo | None, Field(json_schema_extra={"nullable": True})
    ] = None
    latest_released_version: Annotated[
        VersionInfo | None, Field(json_schema_extra={"nullable": True})
    ] = None
    data_completeness_tags: list[str] = Field(
        description="List of data completeness tag names assigned to the study.",
        default_factory=list,
    )

    @classmethod
    def from_input(
        cls,
        val: dict[str, Any],
        deleted: bool = False,
    ) -> Self:
        return cls(
            uid=val["uid"],
            acronym=val.get("acronym"),
            number=val.get("study_number"),
            id=val["id"],
            main_id=val["main_id"],
            title=val.get("title"),
            description=val.get("description"),
            subpart_id=val.get("subpart_id"),
            subpart_acronym=val.get("subpart_acronym"),
            clinical_programme_name=val["clinical_programme_name"],
            project_number=val["project_number"],
            project_name=val["project_name"],
            version_author=val["version_author"],
            version_status=(
                StudyStatus.DELETED if deleted else StudyStatus(val["version_status"])
            ),
            version_start_date=val["version_start_date"],
            version_number=val["version_number"],
            latest_locked_version=(
                cls.VersionInfo(**val["latest_locked_version"])
                if val.get("latest_locked_version") is not None
                else None
            ),
            latest_released_version=(
                cls.VersionInfo(**val["latest_released_version"])
                if val.get("latest_released_version") is not None
                else None
            ),
            data_completeness_tags=val.get("data_completeness_tags", []),
        )


class Study(BaseModel):
    uid: Annotated[str, Field(description="The unique id of the study.")]
    study_parent_part: Annotated[
        StudyParentPart | None,
        Field(json_schema_extra={"nullable": True}),
    ]
    study_subpart_uids: Annotated[list[str], Field()]
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
        find_all_study_time_units: Callable[[str], tuple[list[UnitDefinitionAR], int]],
        find_study_parent_part_by_uid: Callable[[str], StudyDefinitionAR | None],
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        # pylint: disable=unused-argument
        at_specified_date_time: datetime | None = None,
        study_value_version: str | None = None,
        status: StudyStatus | None = None,
        history_endpoint: bool = False,
        terms_at_specific_datetime: datetime | None = None,
        needed_sections: set[str] | None = None,
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
                needed_sections=needed_sections,
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
    study_activity_count: Annotated[
        int, Field(description="Number of connected study activities")
    ]
    study_activity_schedule_count: Annotated[
        int, Field(description="Number of connected study activity schedules")
    ]


class StudySelectionContainmentLabelRow(BaseModel):
    """Per-label comparison when checking if target is contained in source."""

    label: Annotated[str, Field(description="Concrete study selection label")]
    target_selection_count: Annotated[int, Field(description="Selections on target")]
    source_selection_count: Annotated[int, Field(description="Selections on source")]
    target_distinct_ct_term_root_count: Annotated[
        int,
        Field(
            description="Distinct CT term roots on target (via CTTermContext on selections)"
        ),
    ]
    source_distinct_ct_term_root_count: Annotated[
        int,
        Field(
            description="Distinct CT term roots on source (via CTTermContext on selections)"
        ),
    ]
    label_contained: Annotated[
        bool,
        Field(
            description="True if target selection and term counts are <= source for this label"
        ),
    ]


class StudySelectionContainmentResult(BaseModel):
    """
    Whether the **target** study's selection statistics are contained in the **source**.

    Only labels that appear on the **target** study are considered (except
    ``StudySoAFootnote``, which is skipped because SoA footnotes are copied
    conditionally). Containment means for each such label, target counts are less
    than or equal to source counts (selection nodes and distinct CT term roots via
    CTTermContext).
    """

    target_contained_in_source: Annotated[
        bool,
        Field(
            description="True if containment holds for every compared label present on target"
        ),
    ]
    labels_from_target: Annotated[
        list[str],
        Field(
            description=(
                "Concrete selection labels on the target used in the comparison "
                "(excludes StudySoAFootnote)"
            )
        ),
    ]
    per_label: Annotated[
        list[StudySelectionContainmentLabelRow],
        Field(description="Breakdown per label"),
    ]


class StudyCreateInput(PostInputModel):
    study_number: Annotated[str | None, Field()] = None

    study_acronym: Annotated[str | None, Field()] = None

    project_number: Annotated[str, Field(min_length=1)]

    description: Annotated[str | None, Field()] = None


class StudyCloneInput(StudyCreateInput):
    copy_study_arm: Annotated[bool, Field()] = False
    copy_study_branch_arm: Annotated[bool, Field()] = False
    copy_study_cohort: Annotated[bool, Field()] = False
    copy_study_element: Annotated[bool, Field()] = False
    copy_study_visit: Annotated[bool, Field()] = False
    copy_study_visits_study_footnote: Annotated[bool, Field()] = False
    copy_study_epoch: Annotated[bool, Field()] = False
    copy_study_epochs_study_footnote: Annotated[bool, Field()] = False
    copy_study_design_matrix: Annotated[bool, Field()] = False
    copy_study_soa_group: Annotated[bool, Field()] = False
    copy_study_activity: Annotated[bool, Field()] = False
    copy_study_activity_instance: Annotated[bool, Field()] = False
    copy_study_activity_group: Annotated[bool, Field()] = False
    copy_study_activity_subgroup: Annotated[bool, Field()] = False
    copy_study_activity_schedule: Annotated[bool, Field()] = False
    validation_mode: Annotated[ValidationMode, Field()] = ValidationMode.STRICT


class StudySubpartCreateInput(PostInputModel):
    study_subpart_acronym: Annotated[
        str, Field(min_length=1, max_length=10, pattern=r"^[A-Za-z0-9]+$")
    ]

    description: Annotated[str | None, Field()] = None

    study_parent_part_uid: Annotated[str, Field(min_length=1)]


class LockReleaseInput(BaseModel):
    reason_for_change_uid: Annotated[str, Field(min_length=1)]
    change_description: Annotated[
        str | None, Field(description="The description of the Study status change.")
    ] = None
    other_reason_for_locking_releasing: Annotated[str | None, Field()] = None
    protocol_header_major_version: Annotated[
        int | None, Field(description="The major version of protocol header.")
    ] = None
    protocol_header_minor_version: Annotated[
        int | None, Field(description="The minor version of protocol header.")
    ] = None


class UnlockInput(BaseModel):
    reason_for_change_uid: Annotated[str, Field(min_length=1)]
    other_reason_for_unlocking: Annotated[str | None, Field()] = None


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
                    c_code=action.after_value or "", find_term_by_uid=find_term_by_uid
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


class StudyProtocolHeaderVersion(BaseModel):
    protocol_header_version: Annotated[
        str | None,
        Field(
            description="The latest available protocol header version.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    has_final_protocol_locked_version: Annotated[
        bool,
        Field(
            description="Indicates whether the study contains a locked version with 'Final Protocol' as the reason for lock.",
        ),
    ] = False


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
    development_stage_code: Annotated[
        SimpleTermModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    protocol_header_version: Annotated[
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
            development_stage_code=SimpleTermModel.from_ct_code(
                c_code=current_metadata.high_level_study_design.development_stage_code,
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
    change_type: Annotated[str, Field()]
    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)


# Integrity Check Response Models
class IntegrityCheckResult(BaseModel):
    """Result of a single integrity check for a study."""

    check_id: str
    description: str
    passed: bool
    noncompliant_count: int
    noncompliant_labels: list[list[str]]
    noncompliant_node_ids: list[int | str]
    root_uids: list[str] | None = None
    error: str | None = None


class StudyIntegrityCheckResponse(BaseModel):
    """Integrity check results for a single study."""

    study_uid: str
    study_number: str | None = None
    study_acronym: str | None = None
    all_passed: bool
    checks: list[IntegrityCheckResult]
    error: str | None = None
