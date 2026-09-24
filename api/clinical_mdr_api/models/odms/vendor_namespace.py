import json
import re
from typing import Annotated, Any, Callable, Self

from pydantic import Field, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.odms.vendor_attribute import OdmVendorAttributeAR
from clinical_mdr_api.domains.odms.vendor_element import OdmVendorElementAR
from clinical_mdr_api.domains.odms.vendor_namespace import OdmVendorNamespaceAR
from clinical_mdr_api.models.odms.common_models import (
    OdmBaseModel,
    OdmPatchInput,
    OdmPostInput,
    OdmVendorAttributeSimpleModel,
    OdmVendorElementSimpleModel,
)
from clinical_mdr_api.models.utils import make_optional


class OdmVendorNamespace(OdmBaseModel):
    prefix: Annotated[str | None, Field()]
    url: Annotated[str | None, Field()]
    vendor_elements: Annotated[list[OdmVendorElementSimpleModel], Field()]
    vendor_attributes: Annotated[list[OdmVendorAttributeSimpleModel], Field()]
    possible_actions: Annotated[list[str], Field()]

    @classmethod
    def from_odm_vendor_namespace_ar(
        cls,
        odm_vendor_namespace_ar: OdmVendorNamespaceAR,
        find_odm_vendor_element_by_uid: Callable[[str], OdmVendorElementAR | None],
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> Self:
        return cls(
            uid=odm_vendor_namespace_ar._uid,
            name=odm_vendor_namespace_ar.name,
            prefix=odm_vendor_namespace_ar.odm_vo.prefix,
            url=odm_vendor_namespace_ar.odm_vo.url,
            library_name=odm_vendor_namespace_ar.library.name,
            start_date=odm_vendor_namespace_ar.item_metadata.start_date,
            end_date=odm_vendor_namespace_ar.item_metadata.end_date,
            status=odm_vendor_namespace_ar.item_metadata.status.value,
            version=odm_vendor_namespace_ar.item_metadata.version,
            change_description=odm_vendor_namespace_ar.item_metadata.change_description,
            author_username=odm_vendor_namespace_ar.item_metadata.author_username,
            vendor_elements=sorted(
                [
                    OdmVendorElementSimpleModel.from_odm_vendor_element_uid(
                        uid=vendor_element_uid,
                        find_odm_vendor_element_by_uid=find_odm_vendor_element_by_uid,
                    )
                    for vendor_element_uid in odm_vendor_namespace_ar.odm_vo.vendor_element_uids
                ],
                key=lambda item: item.name or "",
            ),
            vendor_attributes=sorted(
                [
                    OdmVendorAttributeSimpleModel.from_odm_vendor_attribute_uid(
                        uid=vendor_attribute_uid,
                        find_odm_vendor_attribute_by_uid=find_odm_vendor_attribute_by_uid,
                    )
                    for vendor_attribute_uid in odm_vendor_namespace_ar.odm_vo.vendor_attribute_uids
                ],
                key=lambda item: item.name or "",
            ),
            possible_actions=sorted(
                [_.value for _ in odm_vendor_namespace_ar.get_possible_actions()]
            ),
        )


class OdmVendorNamespacePostInput(OdmPostInput):
    prefix: Annotated[str, Field(min_length=1)]
    url: Annotated[str, Field(min_length=1)]

    @field_validator("prefix")
    @classmethod
    def prefix_may_only_contain_letters(cls, value):
        if re.search("[^a-zA-Z]", value):
            raise ValueError("may only contain letters")
        return value


@make_optional
class OdmVendorNamespaceOptional(OdmVendorNamespace):
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        if data.get("vendor_elements") is not None:
            for vendor_element in data["vendor_elements"]:
                if vendor_element.get("compatible_types") is not None:
                    vendor_element["compatible_types"] = json.loads(
                        vendor_element["compatible_types"]
                    )
        if data.get("vendor_attributes") is not None:
            for vendor_attribute in data["vendor_attributes"]:
                if vendor_attribute.get("compatible_types") is not None:
                    vendor_attribute["compatible_types"] = json.loads(
                        vendor_attribute["compatible_types"]
                    )

        return cls(**data)


class OdmVendorNamespacePatchInput(OdmPatchInput):
    name: Annotated[str, Field(min_length=1)]
    prefix: Annotated[str, Field(min_length=1)]
    url: Annotated[str, Field(min_length=1)]


class OdmVendorNamespaceVersion(OdmVendorNamespace):
    """
    Class for storing OdmVendorNamespace and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)
