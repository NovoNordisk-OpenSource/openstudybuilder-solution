from typing import Annotated, Callable, Self

from pydantic import Field, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.odms.vendor_attribute import OdmVendorAttributeAR
from clinical_mdr_api.domains.concepts.odms.vendor_element import (
    OdmVendorElementAR,
    OdmVendorElementRelationVO,
)
from clinical_mdr_api.domains.concepts.odms.vendor_namespace import OdmVendorNamespaceAR
from clinical_mdr_api.domains.concepts.utils import (
    RelationType,
    VendorElementCompatibleType,
)
from clinical_mdr_api.models.concepts.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_common_models import (
    OdmVendorAttributeSimpleModel,
    OdmVendorNamespaceSimpleModel,
)
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.models.validators import validate_name_only_contains_letters


class OdmVendorElement(ConceptModel):
    compatible_types: Annotated[list[str], Field(json_schema_extra={"is_json": True})]
    vendor_namespace: OdmVendorNamespaceSimpleModel
    vendor_attributes: list[OdmVendorAttributeSimpleModel]
    possible_actions: list[str]

    @classmethod
    def from_odm_vendor_element_ar(
        cls,
        odm_vendor_element_ar: OdmVendorElementAR,
        find_odm_vendor_namespace_by_uid: Callable[[str], OdmVendorNamespaceAR | None],
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> Self:
        return cls(
            uid=odm_vendor_element_ar._uid,
            compatible_types=odm_vendor_element_ar.concept_vo.compatible_types,
            name=odm_vendor_element_ar.concept_vo.name,
            library_name=odm_vendor_element_ar.library.name,
            start_date=odm_vendor_element_ar.item_metadata.start_date,
            end_date=odm_vendor_element_ar.item_metadata.end_date,
            status=odm_vendor_element_ar.item_metadata.status.value,
            version=odm_vendor_element_ar.item_metadata.version,
            change_description=odm_vendor_element_ar.item_metadata.change_description,
            author_username=odm_vendor_element_ar.item_metadata.author_username,
            vendor_namespace=OdmVendorNamespaceSimpleModel.from_odm_vendor_namespace_uid(
                uid=odm_vendor_element_ar.concept_vo.vendor_namespace_uid,
                find_odm_vendor_namespace_by_uid=find_odm_vendor_namespace_by_uid,
            ),
            vendor_attributes=sorted(
                [
                    OdmVendorAttributeSimpleModel.from_odm_vendor_attribute_uid(
                        uid=vendor_attribute_uid,
                        find_odm_vendor_attribute_by_uid=find_odm_vendor_attribute_by_uid,
                    )
                    for vendor_attribute_uid in odm_vendor_element_ar.concept_vo.vendor_attribute_uids
                ],
                key=lambda item: item.name,
            ),
            possible_actions=sorted(
                [_.value for _ in odm_vendor_element_ar.get_possible_actions()]
            ),
        )


class OdmVendorElementRelationModel(BaseModel):
    @classmethod
    def from_uid(
        cls,
        uid: str,
        odm_element_uid: str,
        odm_element_type: RelationType,
        find_by_uid_with_odm_element_relation: Callable[
            [str, str, RelationType], OdmVendorElementRelationVO | None
        ],
    ) -> Self | None:
        if uid is not None:
            odm_vendor_element_ref_vo = find_by_uid_with_odm_element_relation(
                uid, odm_element_uid, odm_element_type
            )
            if odm_vendor_element_ref_vo is not None:
                odm_vendor_element_ref_model = cls(
                    uid=uid,
                    name=odm_vendor_element_ref_vo.name,
                    value=odm_vendor_element_ref_vo.value,
                )
            else:
                odm_vendor_element_ref_model = cls(
                    uid=uid,
                    name=None,
                    value=None,
                )
        else:
            odm_vendor_element_ref_model = None
        return odm_vendor_element_ref_model

    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    value: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None


class OdmVendorElementPostInput(ConceptPostInput):
    compatible_types: Annotated[list[VendorElementCompatibleType], Field(min_length=1)]
    vendor_namespace_uid: Annotated[str, Field(min_length=1)]

    _validate_name_only_contains_letters = field_validator("name", mode="before")(
        validate_name_only_contains_letters
    )


class OdmVendorElementPatchInput(ConceptPatchInput):
    compatible_types: Annotated[list[VendorElementCompatibleType], Field(min_length=1)]


class OdmVendorElementVersion(OdmVendorElement):
    """
    Class for storing OdmVendorElement and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []
