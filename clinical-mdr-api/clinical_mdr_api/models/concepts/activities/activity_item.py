from typing import Annotated

from pydantic import ConfigDict, Field

from clinical_mdr_api.models.utils import BaseModel, PostInputModel


class CompactActivityItemClass(BaseModel):
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
        Field(json_schema_extra={"source": "has_ct_term.uid", "nullable": True}),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_ct_term.has_name_root.has_latest_value.name",
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


class CompactOdmItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(json_schema_extra={"source": "has_odm_item.uid", "nullable": True}),
    ] = None
    oid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_odm_item.has_latest_value.oid",
                "nullable": True,
            },
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_odm_item.has_latest_value.name",
                "nullable": True,
            },
        ),
    ] = None


class ActivityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    activity_item_class: Annotated[CompactActivityItemClass, Field()]
    ct_terms: Annotated[list[CompactCTTerm], Field()] = []
    unit_definitions: Annotated[list[CompactUnitDefinition], Field()] = []
    is_adam_param_specific: bool
    odm_items: Annotated[list[CompactOdmItem], Field()] = []


class ActivityItemCreateInput(PostInputModel):
    activity_item_class_uid: Annotated[str, Field(min_length=1)]
    ct_term_uids: list[str]
    unit_definition_uids: list[str]
    is_adam_param_specific: bool
    odm_item_uids: list[str]
