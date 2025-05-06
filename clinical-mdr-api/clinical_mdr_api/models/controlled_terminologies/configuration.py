from enum import Enum
from typing import Annotated, Self

from pydantic import ConfigDict, Field, field_validator

from clinical_mdr_api.domains.controlled_terminologies.configurations import CTConfigAR
from clinical_mdr_api.models.concepts.concept import (
    NoLibraryConceptModelNoName,
    VersionProperties,
)
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel


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


class CTConfigBaseModel(BaseModel):
    study_field_name: str
    study_field_data_type: StudyFieldType
    study_field_null_value_code: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    configured_codelist_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    configured_term_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    study_field_grouping: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_field_name_api: str
    is_dictionary_term: bool


class CTConfigOGM(VersionProperties):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[str, Field(json_schema_extra={"source": "uid"})]
    study_field_name: Annotated[
        str, Field(json_schema_extra={"source": "has_latest_value.study_field_name"})
    ]
    study_field_data_type: Annotated[
        StudyFieldType | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.study_field_data_type",
                "nullable": True,
            },
        ),
    ] = None
    study_field_null_value_code: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.study_field_null_value_code",
                "nullable": True,
            },
        ),
    ] = None

    configured_codelist_uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_configured_codelist.uid",
                "nullable": True,
            },
        ),
    ] = None
    configured_term_uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_configured_term.uid",
                "nullable": True,
            },
        ),
    ] = None

    study_field_grouping: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.study_field_grouping",
                "nullable": True,
            },
        ),
    ] = None
    study_field_name_api: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.study_field_name_api",
                "nullable": True,
            },
        ),
    ] = None
    is_dictionary_term: Annotated[
        bool, Field(json_schema_extra={"source": "has_latest_value.is_dictionary_term"})
    ]


class CTConfigModel(CTConfigBaseModel, NoLibraryConceptModelNoName):
    @classmethod
    def from_ct_config_ar(cls, ct_config_definition_ar: CTConfigAR) -> Self:
        return CTConfigModel(
            uid=ct_config_definition_ar.uid,
            study_field_name=ct_config_definition_ar.value.study_field_name,
            study_field_data_type=ct_config_definition_ar.value.study_field_data_type,
            study_field_null_value_code=ct_config_definition_ar.value.study_field_null_value_code,
            configured_codelist_uid=ct_config_definition_ar.value.configured_codelist_uid,
            configured_term_uid=ct_config_definition_ar.value.configured_term_uid,
            study_field_grouping=ct_config_definition_ar.value.study_field_grouping,
            study_field_name_api=ct_config_definition_ar.value.study_field_name_api,
            is_dictionary_term=ct_config_definition_ar.value.is_dictionary_term,
            start_date=ct_config_definition_ar.item_metadata.start_date,
            status=ct_config_definition_ar.item_metadata.status.value,
            version=ct_config_definition_ar.item_metadata.version,
            author_username=ct_config_definition_ar.item_metadata.author_username,
            change_description=ct_config_definition_ar.item_metadata.change_description,
        )


class CTConfigPostInput(PostInputModel):
    study_field_name: Annotated[str, Field(min_length=1)]
    study_field_data_type: StudyFieldType
    study_field_null_value_code: Annotated[str | None, Field(min_length=1)] = None

    configured_codelist_uid: Annotated[str | None, Field(min_length=1)] = None
    configured_term_uid: Annotated[str | None, Field(min_length=1)] = None

    study_field_grouping: Annotated[str | None, Field(min_length=1)] = None
    study_field_name_api: Annotated[str, Field(min_length=1)]
    is_dictionary_term: bool
    # field used to create a configuration based on codelist name
    configured_codelist_name: Annotated[str | None, Field(min_length=1)] = None

    @field_validator("*")
    @classmethod
    def replace_empty_string_with_none(cls, field):
        if field == "":
            return None
        return field


class CTConfigPatchInput(PatchInputModel):
    study_field_name: Annotated[str, Field(min_length=1)]
    study_field_data_type: StudyFieldType
    study_field_null_value_code: Annotated[str | None, Field(min_length=1)] = None

    configured_codelist_uid: Annotated[str | None, Field(min_length=1)] = None
    configured_term_uid: Annotated[str | None, Field(min_length=1)] = None

    study_field_grouping: Annotated[str | None, Field(min_length=1)] = None
    study_field_name_api: Annotated[str, Field(min_length=1)]
    is_dictionary_term: bool
    change_description: Annotated[str, Field(min_length=1)]
