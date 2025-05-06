import re
from typing import Annotated, Callable, Self

from pydantic import Field, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.odms.vendor_attribute import OdmVendorAttributeAR
from clinical_mdr_api.domains.concepts.odms.vendor_element import OdmVendorElementAR
from clinical_mdr_api.domains.concepts.odms.vendor_namespace import OdmVendorNamespaceAR
from clinical_mdr_api.models.concepts.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_common_models import (
    OdmVendorAttributeSimpleModel,
    OdmVendorElementSimpleModel,
)


class OdmVendorNamespace(ConceptModel):
    prefix: str | None
    url: str | None
    vendor_elements: list[OdmVendorElementSimpleModel]
    vendor_attributes: list[OdmVendorAttributeSimpleModel]
    possible_actions: list[str]

    @classmethod
    def from_odm_vendor_namespace_ar(
        cls,
        odm_vendor_namespace_ar: OdmVendorNamespaceAR,
        find_odm_vendor_element_by_uid: Callable[[str], OdmVendorElementAR | None],
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> Self:
        return cls(
            uid=odm_vendor_namespace_ar._uid,
            name=odm_vendor_namespace_ar.concept_vo.name,
            prefix=odm_vendor_namespace_ar.concept_vo.prefix,
            url=odm_vendor_namespace_ar.concept_vo.url,
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
                    for vendor_element_uid in odm_vendor_namespace_ar.concept_vo.vendor_element_uids
                ],
                key=lambda item: item.name,
            ),
            vendor_attributes=sorted(
                [
                    OdmVendorAttributeSimpleModel.from_odm_vendor_attribute_uid(
                        uid=vendor_attribute_uid,
                        find_odm_vendor_attribute_by_uid=find_odm_vendor_attribute_by_uid,
                    )
                    for vendor_attribute_uid in odm_vendor_namespace_ar.concept_vo.vendor_attribute_uids
                ],
                key=lambda item: item.name,
            ),
            possible_actions=sorted(
                [_.value for _ in odm_vendor_namespace_ar.get_possible_actions()]
            ),
        )


class OdmVendorNamespacePostInput(ConceptPostInput):
    prefix: Annotated[str, Field(min_length=1)]
    url: Annotated[str, Field(min_length=1)]

    @field_validator("prefix")
    @classmethod
    def prefix_may_only_contain_letters(cls, value):
        if re.search("[^a-zA-Z]", value):
            raise ValueError("may only contain letters")
        return value


class OdmVendorNamespacePatchInput(ConceptPatchInput):
    prefix: Annotated[str, Field(min_length=1)]
    url: Annotated[str, Field(min_length=1)]


class OdmVendorNamespaceVersion(OdmVendorNamespace):
    """
    Class for storing OdmVendorNamespace and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []
