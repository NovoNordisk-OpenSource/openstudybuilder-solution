from typing import Annotated, Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domains.concepts.odms.vendor_attribute import OdmVendorAttributeAR
from clinical_mdr_api.models.utils import BaseModel, PostInputModel


class OdmElementWithParentUid(BaseModel):
    uid: str
    name: str
    parent_uids: list[str]


class OdmVendorRelationPostInput(PostInputModel):
    uid: Annotated[str, Field(min_length=1)]
    value: Annotated[str, Field(min_length=1)]


class OdmVendorElementRelationPostInput(PostInputModel):
    uid: Annotated[str, Field(min_length=1)]
    value: Annotated[str | None, Field(min_length=1)]


class OdmVendorsPostInput(PostInputModel):
    elements: list[OdmVendorElementRelationPostInput]
    element_attributes: list[OdmVendorRelationPostInput]
    attributes: list[OdmVendorRelationPostInput]


class OdmRefVendorPostInput(PostInputModel):
    attributes: list[OdmVendorRelationPostInput]


class OdmRefVendorAttributeModel(BaseModel):
    @classmethod
    def from_uid(
        cls,
        uid: str,
        value: str,
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> Self | None:
        if uid is not None:
            odm_vendor_attribute_ar = find_odm_vendor_attribute_by_uid(uid)
            if odm_vendor_attribute_ar is not None:
                odm_vendor_element_ref_model = cls(
                    uid=uid,
                    name=odm_vendor_attribute_ar.name,
                    data_type=odm_vendor_attribute_ar.concept_vo.data_type,
                    value_regex=odm_vendor_attribute_ar.concept_vo.value_regex,
                    value=value,
                    vendor_namespace_uid=odm_vendor_attribute_ar.concept_vo.vendor_namespace_uid,
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
        else:
            odm_vendor_element_ref_model = None
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
    attributes: list[OdmRefVendorAttributeModel]


class OdmVendorNamespaceSimpleModel(BaseModel):
    @classmethod
    def from_odm_vendor_namespace_uid(
        cls,
        uid: str,
        find_odm_vendor_namespace_by_uid: Callable[[str], ConceptARBase | None],
    ) -> Self | None:
        if uid is not None:
            odm_vendor_namespace = find_odm_vendor_namespace_by_uid(uid)

            if odm_vendor_namespace is not None:
                simple_odm_vendor_namespace_model = cls(
                    uid=uid,
                    name=odm_vendor_namespace.concept_vo.name,
                    prefix=odm_vendor_namespace.concept_vo.prefix,
                    url=odm_vendor_namespace.concept_vo.url,
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
        else:
            simple_odm_vendor_namespace_model = None
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
    @classmethod
    def from_odm_vendor_attribute_uid(
        cls,
        uid: str,
        find_odm_vendor_attribute_by_uid: Callable[[str], ConceptARBase | None],
    ) -> Self | None:
        if uid is not None:
            odm_vendor_attribute = find_odm_vendor_attribute_by_uid(uid)

            if odm_vendor_attribute is not None:
                simple_odm_vendor_attribute_model = cls(
                    uid=uid,
                    name=odm_vendor_attribute.concept_vo.name,
                    data_type=odm_vendor_attribute.concept_vo.data_type,
                    compatible_types=odm_vendor_attribute.concept_vo.compatible_types,
                    status=odm_vendor_attribute.item_metadata.status.value,
                    version=odm_vendor_attribute.item_metadata.version,
                    possible_actions=sorted(
                        [_.value for _ in odm_vendor_attribute.get_possible_actions()]
                    ),
                )
            else:
                simple_odm_vendor_attribute_model = cls(
                    uid=uid, name=None, status=None, version=None, possible_actions=[]
                )
        else:
            simple_odm_vendor_attribute_model = None
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
    @classmethod
    def from_odm_vendor_element_uid(
        cls,
        uid: str,
        find_odm_vendor_element_by_uid: Callable[[str], ConceptARBase | None],
    ) -> Self | None:
        if uid is not None:
            odm_vendor_element = find_odm_vendor_element_by_uid(uid)

            if odm_vendor_element is not None:
                simple_odm_vendor_element_model = cls(
                    uid=uid,
                    name=odm_vendor_element.concept_vo.name,
                    compatible_types=odm_vendor_element.concept_vo.compatible_types,
                    status=odm_vendor_element.item_metadata.status.value,
                    version=odm_vendor_element.item_metadata.version,
                    possible_actions=sorted(
                        [_.value for _ in odm_vendor_element.get_possible_actions()]
                    ),
                )
            else:
                simple_odm_vendor_element_model = cls(
                    uid=uid, name=None, status=None, version=None, possible_actions=[]
                )
        else:
            simple_odm_vendor_element_model = None
        return simple_odm_vendor_element_model

    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    compatible_types: Annotated[list, Field()]
    status: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    possible_actions: Annotated[
        list[str] | None, Field(json_schema_extra={"nullable": True})
    ] = None
