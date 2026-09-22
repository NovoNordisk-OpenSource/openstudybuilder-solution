import json
from typing import Annotated, Any, Callable, Self, overload

from pydantic import Field, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.odms.utils import (
    RelationType,
    VendorElementCompatibleType,
)
from clinical_mdr_api.domains.odms.vendor_attribute import OdmVendorAttributeAR
from clinical_mdr_api.domains.odms.vendor_element import (
    OdmVendorElementAR,
    OdmVendorElementRelationVO,
)
from clinical_mdr_api.domains.odms.vendor_namespace import OdmVendorNamespaceAR
from clinical_mdr_api.models.odms.common_models import (
    OdmBaseModel,
    OdmPatchInput,
    OdmPostInput,
    OdmVendorAttributeSimpleModel,
    OdmVendorNamespaceSimpleModel,
)
from clinical_mdr_api.models.utils import BaseModel, make_optional
from clinical_mdr_api.models.validators import (
    validate_first_character_is_uppercase,
    validate_name_only_contains_letters,
)


class OdmVendorElement(OdmBaseModel):
    compatible_types: Annotated[list[str], Field(json_schema_extra={"is_json": True})]
    vendor_namespace: Annotated[OdmVendorNamespaceSimpleModel, Field()]
    vendor_attributes: Annotated[list[OdmVendorAttributeSimpleModel], Field()]
    possible_actions: Annotated[list[str], Field()]

    @classmethod
    def from_odm_vendor_element_ar(
        cls,
        odm_vendor_element_ar: OdmVendorElementAR,
        find_odm_vendor_namespace_by_uid: Callable[[str], OdmVendorNamespaceAR | None],
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> Self:
        return cls(
            uid=odm_vendor_element_ar._uid,
            compatible_types=odm_vendor_element_ar.odm_vo.compatible_types,
            name=odm_vendor_element_ar.name,
            library_name=odm_vendor_element_ar.library.name,
            start_date=odm_vendor_element_ar.item_metadata.start_date,
            end_date=odm_vendor_element_ar.item_metadata.end_date,
            status=odm_vendor_element_ar.item_metadata.status.value,
            version=odm_vendor_element_ar.item_metadata.version,
            change_description=odm_vendor_element_ar.item_metadata.change_description,
            author_username=odm_vendor_element_ar.item_metadata.author_username,
            vendor_namespace=OdmVendorNamespaceSimpleModel.from_odm_vendor_namespace_uid(
                uid=odm_vendor_element_ar.odm_vo.vendor_namespace_uid,
                find_odm_vendor_namespace_by_uid=find_odm_vendor_namespace_by_uid,
            ),
            vendor_attributes=sorted(
                [
                    OdmVendorAttributeSimpleModel.from_odm_vendor_attribute_uid(
                        uid=vendor_attribute_uid,
                        find_odm_vendor_attribute_by_uid=find_odm_vendor_attribute_by_uid,
                    )
                    for vendor_attribute_uid in set(
                        odm_vendor_element_ar.odm_vo.vendor_attribute_uids
                    )
                ],
                key=lambda item: item.name or "",
            ),
            possible_actions=sorted(
                [_.value for _ in odm_vendor_element_ar.get_possible_actions()]
            ),
        )


class OdmVendorElementRelationModel(BaseModel):
    @overload
    @classmethod
    def from_uid(
        cls,
        uid: str,
        odm_element_uid: str,
        odm_element_version: str,
        odm_element_type: RelationType,
        find_by_uid_with_odm_element_relation: Callable[
            [str, str, str, RelationType], OdmVendorElementRelationVO
        ],
    ) -> Self: ...
    @overload
    @classmethod
    def from_uid(
        cls,
        uid: None,
        odm_element_uid: str,
        odm_element_version: str,
        odm_element_type: RelationType,
        find_by_uid_with_odm_element_relation: Callable[
            [str, str, str, RelationType], OdmVendorElementRelationVO
        ],
    ) -> None: ...
    @classmethod
    def from_uid(
        cls,
        uid: str | None,
        odm_element_uid: str,
        odm_element_version: str,
        odm_element_type: RelationType,
        find_by_uid_with_odm_element_relation: Callable[
            [str, str, str, RelationType], OdmVendorElementRelationVO
        ],
    ) -> Self | None:
        odm_vendor_element_ref_model = None

        if uid is not None:
            odm_vendor_element_ref_vo = find_by_uid_with_odm_element_relation(
                uid, odm_element_uid, odm_element_version, odm_element_type
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
        return odm_vendor_element_ref_model

    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    value: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None


class OdmVendorElementPostInput(OdmPostInput):
    compatible_types: Annotated[list[VendorElementCompatibleType], Field(min_length=1)]
    vendor_namespace_uid: Annotated[str, Field(min_length=1)]

    _validate_name_only_contains_letters = field_validator("name", mode="before")(
        validate_name_only_contains_letters
    )
    _validate_first_character_is_uppercase = field_validator("name", mode="after")(
        validate_first_character_is_uppercase
    )


@make_optional
class OdmVendorElementOptional(OdmVendorElement):
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        if data.get("compatible_types") is not None:
            data["compatible_types"] = json.loads(data["compatible_types"])

        if data.get("vendor_attributes") is not None:
            for vendor_attribute in data["vendor_attributes"]:
                vendor_attribute["compatible_types"] = json.loads(
                    vendor_attribute["compatible_types"] or "[]"
                )

        return cls(**data)


class OdmVendorElementPatchInput(OdmPatchInput):
    name: Annotated[str, Field(min_length=1)]
    compatible_types: Annotated[list[VendorElementCompatibleType], Field(min_length=1)]

    _validate_name_only_contains_letters = field_validator("name", mode="before")(
        validate_name_only_contains_letters
    )
    _validate_first_character_is_uppercase = field_validator("name", mode="after")(
        validate_first_character_is_uppercase
    )


class OdmVendorElementVersion(OdmVendorElement):
    """
    Class for storing OdmVendorElement and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)
