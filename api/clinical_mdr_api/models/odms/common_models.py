from abc import ABC
from datetime import datetime
from typing import Annotated, Any, Callable, Self, overload

from pydantic import Field, StringConstraints, field_validator

from clinical_mdr_api.domains.enums import OdmTranslatedTextTypeEnum
from clinical_mdr_api.domains.odms.ar_base import OdmARBase
from clinical_mdr_api.domains.odms.vendor_attribute import OdmVendorAttributeAR
from clinical_mdr_api.models import _generic_descriptions
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel
from clinical_mdr_api.models.validators import is_language_supported
from common.config import settings


def deduplicate_and_keep_newest_version(data: list[dict[Any, Any]]):
    unique: dict[str, tuple[tuple[int, ...], dict[Any, Any]]] = {}

    for obj in data:
        version = tuple(map(int, obj["version"].split(".")))

        if obj["uid"] not in unique or version > unique[obj["uid"]][0]:
            unique[obj["uid"]] = (version, obj)

    return [obj for _, obj in unique.values()]


class OdmElementWithParentUid(BaseModel):
    uid: Annotated[str, Field()]
    name: Annotated[str, Field()]
    parent_uids: Annotated[list[str], Field()]


class OdmVendorRelationPostInput(PostInputModel):
    uid: Annotated[str, Field(min_length=1)]
    value: Annotated[str | None, Field(min_length=1)] = None


class OdmVendorElementRelationPostInput(PostInputModel):
    uid: Annotated[str, Field(min_length=1)]
    value: Annotated[str | None, Field(min_length=1)] = None


class OdmVendorsPostInput(PostInputModel):
    elements: Annotated[list[OdmVendorElementRelationPostInput], Field()]
    element_attributes: Annotated[list[OdmVendorRelationPostInput], Field()]
    attributes: Annotated[list[OdmVendorRelationPostInput], Field()]


class OdmRefVendorPostInput(PostInputModel):
    attributes: Annotated[list[OdmVendorRelationPostInput], Field()]


class OdmRefVendorAttributeModel(BaseModel):
    @overload
    @classmethod
    def from_uid(
        cls,
        uid: str,
        value: str,
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> Self: ...
    @overload
    @classmethod
    def from_uid(
        cls,
        uid: None,
        value: str,
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> None: ...
    @classmethod
    def from_uid(
        cls,
        uid: str | None,
        value: str,
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> Self | None:
        odm_vendor_element_ref_model = None

        if uid is not None:
            odm_vendor_attribute_ar = find_odm_vendor_attribute_by_uid(uid)
            if odm_vendor_attribute_ar is not None:
                odm_vendor_element_ref_model = cls(
                    uid=uid,
                    name=odm_vendor_attribute_ar.name,
                    data_type=odm_vendor_attribute_ar.odm_vo.data_type,
                    value_regex=odm_vendor_attribute_ar.odm_vo.value_regex,
                    value=value,
                    vendor_namespace_uid=odm_vendor_attribute_ar.odm_vo.vendor_namespace_uid,
                )
            else:
                odm_vendor_element_ref_model = cls(
                    uid=uid,
                    name=None,
                    data_type=None,
                    value_regex=None,
                    value=None,
                    vendor_namespace_uid=None,
                )
        return odm_vendor_element_ref_model

    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    data_type: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    value_regex: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    value: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    vendor_namespace_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class OdmRefVendor(BaseModel):
    attributes: Annotated[list[OdmRefVendorAttributeModel], Field()]


class OdmVendorNamespaceSimpleModel(BaseModel):
    @overload
    @classmethod
    def from_odm_vendor_namespace_uid(
        cls,
        uid: str,
        find_odm_vendor_namespace_by_uid: Callable[[str], OdmARBase | None],
    ) -> Self: ...
    @overload
    @classmethod
    def from_odm_vendor_namespace_uid(
        cls,
        uid: None,
        find_odm_vendor_namespace_by_uid: Callable[[str], OdmARBase | None],
    ) -> None: ...
    @classmethod
    def from_odm_vendor_namespace_uid(
        cls,
        uid: str | None,
        find_odm_vendor_namespace_by_uid: Callable[[str], OdmARBase | None],
    ) -> Self | None:
        simple_odm_vendor_namespace_model = None

        if uid is not None:
            odm_vendor_namespace = find_odm_vendor_namespace_by_uid(uid)

            if odm_vendor_namespace is not None:
                simple_odm_vendor_namespace_model = cls(
                    uid=uid,
                    name=odm_vendor_namespace.odm_vo.name,
                    prefix=odm_vendor_namespace.odm_vo.prefix,
                    url=odm_vendor_namespace.odm_vo.url,
                    status=odm_vendor_namespace.item_metadata.status.value,
                    version=odm_vendor_namespace.item_metadata.version,
                    possible_actions=sorted(
                        [_.value for _ in odm_vendor_namespace.get_possible_actions()]
                    ),
                )
            else:
                simple_odm_vendor_namespace_model = cls(
                    uid=uid,
                    name=None,
                    prefix=None,
                    url=None,
                    status=None,
                    version=None,
                    possible_actions=[],
                )
        return simple_odm_vendor_namespace_model

    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    prefix: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    url: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    status: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    possible_actions: Annotated[
        list[str] | None, Field(json_schema_extra={"nullable": True})
    ] = None


class OdmVendorAttributeSimpleModel(BaseModel):
    @overload
    @classmethod
    def from_odm_vendor_attribute_uid(
        cls,
        uid: str,
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmARBase | None],
    ) -> Self: ...
    @overload
    @classmethod
    def from_odm_vendor_attribute_uid(
        cls,
        uid: None,
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmARBase | None],
    ) -> None: ...
    @classmethod
    def from_odm_vendor_attribute_uid(
        cls,
        uid: str | None,
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmARBase | None],
    ) -> Self | None:
        simple_odm_vendor_attribute_model = None

        if uid is not None:
            odm_vendor_attribute = find_odm_vendor_attribute_by_uid(uid)

            if odm_vendor_attribute is not None:
                simple_odm_vendor_attribute_model = cls(
                    uid=uid,
                    name=odm_vendor_attribute.odm_vo.name,
                    data_type=odm_vendor_attribute.odm_vo.data_type,
                    compatible_types=odm_vendor_attribute.odm_vo.compatible_types,
                    status=odm_vendor_attribute.item_metadata.status.value,
                    version=odm_vendor_attribute.item_metadata.version,
                    possible_actions=sorted(
                        [_.value for _ in odm_vendor_attribute.get_possible_actions()]
                    ),
                )
            else:
                simple_odm_vendor_attribute_model = cls(
                    uid=uid,
                    name=None,
                    status=None,
                    version=None,
                    compatible_types=[],
                    possible_actions=[],
                )
        return simple_odm_vendor_attribute_model

    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    data_type: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    compatible_types: Annotated[list, Field()]
    status: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    possible_actions: Annotated[
        list[str] | None, Field(json_schema_extra={"nullable": True})
    ] = None


class OdmVendorElementSimpleModel(BaseModel):
    @overload
    @classmethod
    def from_odm_vendor_element_uid(
        cls,
        uid: str,
        find_odm_vendor_element_by_uid: Callable[[str], OdmARBase | None],
    ) -> Self: ...
    @overload
    @classmethod
    def from_odm_vendor_element_uid(
        cls,
        uid: None,
        find_odm_vendor_element_by_uid: Callable[[str], OdmARBase | None],
    ) -> None: ...
    @classmethod
    def from_odm_vendor_element_uid(
        cls,
        uid: str | None,
        find_odm_vendor_element_by_uid: Callable[[str], OdmARBase | None],
    ) -> Self | None:
        simple_odm_vendor_element_model = None

        if uid is not None:
            odm_vendor_element = find_odm_vendor_element_by_uid(uid)

            if odm_vendor_element is not None:
                simple_odm_vendor_element_model = cls(
                    uid=uid,
                    name=odm_vendor_element.odm_vo.name,
                    compatible_types=odm_vendor_element.odm_vo.compatible_types,
                    status=odm_vendor_element.item_metadata.status.value,
                    version=odm_vendor_element.item_metadata.version,
                    possible_actions=sorted(
                        [_.value for _ in odm_vendor_element.get_possible_actions()]
                    ),
                )
            else:
                simple_odm_vendor_element_model = cls(
                    uid=uid,
                    name=None,
                    status=None,
                    version=None,
                    compatible_types=[],
                    possible_actions=[],
                )
        return simple_odm_vendor_element_model

    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    compatible_types: Annotated[list, Field()]
    status: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    possible_actions: Annotated[
        list[str] | None, Field(json_schema_extra={"nullable": True})
    ] = None


class OdmAliasModel(BaseModel, frozen=True):  # type: ignore[misc]
    name: Annotated[str, Field(min_length=1)]
    context: Annotated[str, Field(min_length=1)]


class OdmTranslatedTextModel(BaseModel, frozen=True):  # type: ignore[misc]
    text_type: Annotated[OdmTranslatedTextTypeEnum, Field()]
    language: Annotated[
        str, StringConstraints(to_lower=True, strip_whitespace=True, min_length=1)
    ]
    text: Annotated[str, Field(json_schema_extra={"format": "html"})]

    _language_validator = field_validator("language")(is_language_supported)


class OdmFormalExpressionModel(BaseModel, frozen=True):  # type: ignore[misc]
    context: Annotated[str, Field(min_length=1)]
    expression: Annotated[str, Field(min_length=1)]


# ODM-specific base models to replace Concept* classes
class OdmBaseModel(BaseModel, ABC):
    """Base model for all ODM entities, providing versioning and metadata fields."""

    uid: Annotated[str, Field()]
    name: Annotated[str, Field()]
    library_name: Annotated[str, Field()]
    start_date: Annotated[
        datetime,
        Field(
            description=_generic_descriptions.START_DATE,
            json_schema_extra={"source": "latest_version|start_date"},
        ),
    ]
    end_date: Annotated[
        datetime | None,
        Field(
            description=_generic_descriptions.END_DATE,
            json_schema_extra={"source": "latest_version|end_date", "nullable": True},
        ),
    ] = None
    status: Annotated[str, Field()]
    version: Annotated[str, Field()]
    author_username: Annotated[
        str | None,
        Field(
            json_schema_extra={"nullable": True},
        ),
    ] = None
    change_description: Annotated[str, Field()]


class OdmPostInput(PostInputModel, ABC):
    """Base input model for creating new ODM entities."""

    name: Annotated[str, Field(min_length=1)]
    library_name: Annotated[str, Field(min_length=1)] = settings.sponsor_library_name


class OdmPatchInput(PatchInputModel, ABC):
    """Base input model for partially updating existing ODM entities."""

    change_description: Annotated[str, Field(min_length=1)]
    name: Annotated[str | None, Field(min_length=1)] = None
