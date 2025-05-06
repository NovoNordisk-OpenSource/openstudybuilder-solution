from typing import Annotated, Callable, Self

from pydantic import Field, field_validator, model_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.odms.vendor_attribute import (
    OdmVendorAttributeAR,
    OdmVendorAttributeRelationVO,
    OdmVendorElementAttributeRelationVO,
)
from clinical_mdr_api.domains.concepts.odms.vendor_element import OdmVendorElementAR
from clinical_mdr_api.domains.concepts.odms.vendor_namespace import OdmVendorNamespaceAR
from clinical_mdr_api.domains.concepts.utils import (
    RelationType,
    VendorAttributeCompatibleType,
)
from clinical_mdr_api.models.concepts.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_common_models import (
    OdmVendorElementSimpleModel,
    OdmVendorNamespaceSimpleModel,
)
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.models.validators import (
    validate_name_only_contains_letters,
    validate_regex,
)
from common.exceptions import ValidationException


class OdmVendorAttribute(ConceptModel):
    compatible_types: Annotated[list[str], Field(json_schema_extra={"is_json": True})]
    data_type: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    value_regex: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    vendor_namespace: Annotated[
        OdmVendorNamespaceSimpleModel | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    vendor_element: Annotated[
        OdmVendorElementSimpleModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    possible_actions: list[str]

    @classmethod
    def from_odm_vendor_attribute_ar(
        cls,
        odm_vendor_attribute_ar: OdmVendorAttributeAR,
        find_odm_vendor_namespace_by_uid: Callable[[str], OdmVendorNamespaceAR | None],
        find_odm_vendor_element_by_uid: Callable[[str], OdmVendorElementAR | None],
    ) -> Self:
        return cls(
            uid=odm_vendor_attribute_ar._uid,
            name=odm_vendor_attribute_ar.concept_vo.name,
            compatible_types=odm_vendor_attribute_ar.concept_vo.compatible_types,
            data_type=odm_vendor_attribute_ar.concept_vo.data_type,
            value_regex=odm_vendor_attribute_ar.concept_vo.value_regex,
            library_name=odm_vendor_attribute_ar.library.name,
            start_date=odm_vendor_attribute_ar.item_metadata.start_date,
            end_date=odm_vendor_attribute_ar.item_metadata.end_date,
            status=odm_vendor_attribute_ar.item_metadata.status.value,
            version=odm_vendor_attribute_ar.item_metadata.version,
            change_description=odm_vendor_attribute_ar.item_metadata.change_description,
            author_username=odm_vendor_attribute_ar.item_metadata.author_username,
            vendor_namespace=OdmVendorNamespaceSimpleModel.from_odm_vendor_namespace_uid(
                uid=odm_vendor_attribute_ar.concept_vo.vendor_namespace_uid,
                find_odm_vendor_namespace_by_uid=find_odm_vendor_namespace_by_uid,
            ),
            vendor_element=OdmVendorElementSimpleModel.from_odm_vendor_element_uid(
                uid=odm_vendor_attribute_ar.concept_vo.vendor_element_uid,
                find_odm_vendor_element_by_uid=find_odm_vendor_element_by_uid,
            ),
            possible_actions=sorted(
                [_.value for _ in odm_vendor_attribute_ar.get_possible_actions()]
            ),
        )


class OdmVendorAttributeRelationModel(BaseModel):
    @classmethod
    def from_uid(
        cls,
        uid: str,
        odm_element_uid: str,
        odm_element_type: RelationType,
        find_by_uid_with_odm_element_relation: Callable[
            [str, str, RelationType, bool], OdmVendorAttributeRelationVO | None
        ],
        vendor_element_attribute: bool = True,
    ) -> Self | None:
        if uid is not None:
            odm_vendor_attribute_ref_vo = find_by_uid_with_odm_element_relation(
                uid, odm_element_uid, odm_element_type, vendor_element_attribute
            )
            if odm_vendor_attribute_ref_vo is not None:
                odm_vendor_element_ref_model = cls(
                    uid=uid,
                    name=odm_vendor_attribute_ref_vo.name,
                    data_type=odm_vendor_attribute_ref_vo.data_type,
                    value_regex=odm_vendor_attribute_ref_vo.value_regex,
                    value=odm_vendor_attribute_ref_vo.value,
                    vendor_namespace_uid=odm_vendor_attribute_ref_vo.vendor_namespace_uid,
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


class OdmVendorElementAttributeRelationModel(BaseModel):
    @classmethod
    def from_uid(
        cls,
        uid: str,
        odm_element_uid: str,
        odm_element_type: RelationType,
        find_by_uid_with_odm_element_relation: Callable[
            [str, str, RelationType, bool],
            OdmVendorElementAttributeRelationVO | None,
        ],
        vendor_element_attribute: bool = True,
    ) -> Self | None:
        if uid is not None:
            odm_vendor_element_attribute_ref_vo = find_by_uid_with_odm_element_relation(
                uid, odm_element_uid, odm_element_type, vendor_element_attribute
            )
            if odm_vendor_element_attribute_ref_vo is not None:
                odm_vendor_element_ref_model = cls(
                    uid=uid,
                    name=odm_vendor_element_attribute_ref_vo.name,
                    data_type=odm_vendor_element_attribute_ref_vo.data_type,
                    value_regex=odm_vendor_element_attribute_ref_vo.value_regex,
                    value=odm_vendor_element_attribute_ref_vo.value,
                    vendor_element_uid=odm_vendor_element_attribute_ref_vo.vendor_element_uid,
                )
            else:
                odm_vendor_element_ref_model = cls(
                    uid=uid,
                    name=None,
                    data_type=None,
                    value_regex=None,
                    value=None,
                    vendor_element_uid=None,
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
    vendor_element_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class OdmVendorAttributePostInput(ConceptPostInput):
    compatible_types: list[VendorAttributeCompatibleType] = []
    data_type: Annotated[str, Field(min_length=1)] = "string"
    value_regex: Annotated[str | None, Field(min_length=1)] = None
    vendor_namespace_uid: Annotated[str | None, Field(min_length=1)] = None
    vendor_element_uid: Annotated[str | None, Field(min_length=1)] = None

    _validate_regex = field_validator("value_regex", mode="before")(validate_regex)
    _validate_name_only_contains_letters = field_validator("name", mode="before")(
        validate_name_only_contains_letters
    )

    @model_validator(mode="before")
    @classmethod
    def one_and_only_one_of_the_two_uids_must_be_present(cls, values):
        ValidationException.raise_if(
            (
                not values.get("vendor_element_uid")
                and not values.get("vendor_namespace_uid")
            )
            or (
                values.get("vendor_element_uid") and values.get("vendor_namespace_uid")
            ),
            msg="Either vendor_namespace_uid or vendor_element_uid must be provided",
        )

        return values


class OdmVendorAttributePatchInput(ConceptPatchInput):
    compatible_types: list[VendorAttributeCompatibleType]
    data_type: Annotated[str | None, Field(min_length=1)]
    value_regex: Annotated[str | None, Field(min_length=1)]

    _validate_regex = field_validator("value_regex", mode="before")(validate_regex)


class OdmVendorAttributeVersion(OdmVendorAttribute):
    """
    Class for storing OdmVendorAttribute and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []
