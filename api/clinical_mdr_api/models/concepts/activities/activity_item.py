from typing import Annotated

from pydantic import ConfigDict, Field, model_validator

from clinical_mdr_api.models.utils import BaseModel, PostInputModel


class CompactActivityItemClassForActivityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str, Field(json_schema_extra={"source": "has_activity_item_class.uid"})
    ]
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_activity_item_class.has_latest_value.name",
                "nullable": True,
            },
        ),
    ] = None


class CompactCTTerm(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_ct_term.has_selected_term.uid",
                "nullable": True,
            }
        ),
    ] = None
    codelist_uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_ct_term.has_selected_codelist.uid",
                "nullable": True,
            }
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_ct_term.has_selected_term.has_name_root.has_latest_value.name",
                "nullable": True,
            },
        ),
    ] = None
    submission_value: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_ct_term.has_selected_term.has_term_root.submission_value",
                "nullable": True,
            },
        ),
    ] = None


class CompactCodelist(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "nullable": True,
            }
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "nullable": True,
            },
        ),
    ] = None


class CompactUnitDefinition(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(
            json_schema_extra={"source": "has_unit_definition.uid", "nullable": True}
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_unit_definition.has_latest_value.name",
                "nullable": True,
            },
        ),
    ] = None
    dimension_name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_unit_definition.has_latest_value.has_ct_dimension.has_name_root.has_latest_value.name",
                "nullable": True,
            },
        ),
    ] = None


class ActivityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    activity_item_class: Annotated[CompactActivityItemClassForActivityItem, Field()]
    ct_codelist: Annotated[CompactCodelist | None, Field()] = None
    ct_terms: list[CompactCTTerm] = Field(default_factory=list)
    unit_definitions: list[CompactUnitDefinition] = Field(default_factory=list)
    is_adam_param_specific: Annotated[bool, Field()]
    is_activity_instance_id_specific: Annotated[bool | None, Field()] = None
    text_value: Annotated[str | None, Field()] = None


class ActivityItemCreateInput(PostInputModel):
    class CTTermsInput(PostInputModel):
        term_uid: Annotated[str, Field(min_length=1)]
        codelist_uid: Annotated[str, Field(min_length=1)]

    activity_item_class_uid: Annotated[str, Field(min_length=1)]
    ct_codelist_uid: Annotated[str | None, Field()] = None
    ct_terms: Annotated[list[CTTermsInput], Field()]
    unit_definition_uids: Annotated[list[str], Field()]
    is_adam_param_specific: Annotated[bool, Field()]
    is_activity_instance_id_specific: Annotated[bool | None, Field()] = None
    text_value: Annotated[str | None, Field()] = None

    @model_validator(mode="after")
    def validate_codelist_and_terms(self):
        if self.ct_terms and self.ct_codelist_uid:
            raise ValueError(
                "Both ct_terms and ct_codelist cannot be provided at the same time for an ActivityItem."
            )
        if self.is_activity_instance_id_specific:
            if self.ct_codelist_uid:
                raise ValueError(
                    "An ActivityItem with 'is_activity_instance_id_specific' set to true must not have a ct_codelist_uid."
                )
            if len(self.ct_terms) > 1:
                raise ValueError(
                    "An ActivityItem with 'is_activity_instance_id_specific' set to true must not have more than one ct_term."
                )
            if len(self.unit_definition_uids) > 1:
                raise ValueError(
                    "An ActivityItem with 'is_activity_instance_id_specific' set to true must not have more than one unit_definition."
                )
        return self
