import json
from typing import Annotated, Any, Callable, Self, overload

from pydantic import Field, field_validator, model_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.odms.utils import (
    RelationType,
    VendorAttributeCompatibleType,
)
from clinical_mdr_api.domains.odms.vendor_attribute import (
    OdmVendorAttributeAR,
    OdmVendorAttributeRelationVO,
    OdmVendorElementAttributeRelationVO,
)
from clinical_mdr_api.domains.odms.vendor_element import OdmVendorElementAR
from clinical_mdr_api.domains.odms.vendor_namespace import OdmVendorNamespaceAR
from clinical_mdr_api.models.odms.common_models import (
    OdmBaseModel,
    OdmPatchInput,
    OdmPostInput,
    OdmVendorElementSimpleModel,
    OdmVendorNamespaceSimpleModel,
)
from clinical_mdr_api.models.utils import BaseModel, make_optional
from clinical_mdr_api.models.validators import (
    validate_first_character_is_lowercase,
    validate_name_only_contains_letters,
    validate_regex,
)
from common.exceptions import ValidationException


class OdmVendorAttribute(OdmBaseModel):
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
    possible_actions: Annotated[list[str], Field()]

    @classmethod
    def from_odm_vendor_attribute_ar(
        cls,
        odm_vendor_attribute_ar: OdmVendorAttributeAR,
        find_odm_vendor_namespace_by_uid: Callable[[str], OdmVendorNamespaceAR | None],
        find_odm_vendor_element_by_uid: Callable[[str], OdmVendorElementAR | None],
    ) -> Self:
        return cls(
            uid=odm_vendor_attribute_ar._uid,
            name=odm_vendor_attribute_ar.name,
            compatible_types=odm_vendor_attribute_ar.odm_vo.compatible_types,
            data_type=odm_vendor_attribute_ar.odm_vo.data_type,
            value_regex=odm_vendor_attribute_ar.odm_vo.value_regex,
            library_name=odm_vendor_attribute_ar.library.name,
            start_date=odm_vendor_attribute_ar.item_metadata.start_date,
            end_date=odm_vendor_attribute_ar.item_metadata.end_date,
            status=odm_vendor_attribute_ar.item_metadata.status.value,
            version=odm_vendor_attribute_ar.item_metadata.version,
            change_description=odm_vendor_attribute_ar.item_metadata.change_description,
            author_username=odm_vendor_attribute_ar.item_metadata.author_username,
            vendor_namespace=OdmVendorNamespaceSimpleModel.from_odm_vendor_namespace_uid(
                uid=odm_vendor_attribute_ar.odm_vo.vendor_namespace_uid,
                find_odm_vendor_namespace_by_uid=find_odm_vendor_namespace_by_uid,
            ),
            vendor_element=OdmVendorElementSimpleModel.from_odm_vendor_element_uid(
                uid=odm_vendor_attribute_ar.odm_vo.vendor_element_uid,
                find_odm_vendor_element_by_uid=find_odm_vendor_element_by_uid,
            ),
            possible_actions=sorted(
                [_.value for _ in odm_vendor_attribute_ar.get_possible_actions()]
            ),
        )


class OdmVendorAttributeRelationModel(BaseModel):
    @overload
    @classmethod
    def from_uid(
        cls,
        uid: str,
        odm_element_uid: str,
        odm_element_version: str,
        odm_element_type: RelationType,
        find_by_uid_with_odm_element_relation: Callable[
            [str, str, str, RelationType, bool], OdmVendorAttributeRelationVO
        ],
        vendor_element_attribute: bool = True,
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
            [str, str, str, RelationType, bool], OdmVendorAttributeRelationVO
        ],
        vendor_element_attribute: bool = True,
    ) -> None: ...
    @classmethod
    def from_uid(
        cls,
        uid: str | None,
        odm_element_uid: str,
        odm_element_version: str,
        odm_element_type: RelationType,
        find_by_uid_with_odm_element_relation: Callable[
            [str, str, str, RelationType, bool], OdmVendorAttributeRelationVO
        ],
        vendor_element_attribute: bool = True,
    ) -> Self | None:
        odm_vendor_element_ref_model = None

        if uid is not None:
            odm_vendor_attribute_ref_vo = find_by_uid_with_odm_element_relation(
                uid,
                odm_element_uid,
                odm_element_version,
                odm_element_type,
                vendor_element_attribute,
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
    @overload
    @classmethod
    def from_uid(
        cls,
        uid: str,
        odm_element_uid: str,
        odm_element_version: str,
        odm_element_type: RelationType,
        find_by_uid_with_odm_element_relation: Callable[
            [str, str, str, RelationType, bool],
            OdmVendorElementAttributeRelationVO,
        ],
        vendor_element_attribute: bool = True,
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
            [str, str, str, RelationType, bool],
            OdmVendorElementAttributeRelationVO,
        ],
        vendor_element_attribute: bool = True,
    ) -> None: ...
    @classmethod
    def from_uid(
        cls,
        uid: str | None,
        odm_element_uid: str,
        odm_element_version: str,
        odm_element_type: RelationType,
        find_by_uid_with_odm_element_relation: Callable[
            [str, str, str, RelationType, bool],
            OdmVendorElementAttributeRelationVO,
        ],
        vendor_element_attribute: bool = True,
    ) -> Self | None:
        odm_vendor_element_ref_model = None

        if uid is not None:
            odm_vendor_element_attribute_ref_vo = find_by_uid_with_odm_element_relation(
                uid,
                odm_element_uid,
                odm_element_version,
                odm_element_type,
                vendor_element_attribute,
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


class OdmVendorAttributePostInput(OdmPostInput):
    compatible_types: list[VendorAttributeCompatibleType] = Field(default_factory=list)
    data_type: Annotated[str, Field(min_length=1)] = "string"
    value_regex: Annotated[str | None, Field(min_length=1)] = None
    vendor_namespace_uid: Annotated[str | None, Field(min_length=1)] = None
    vendor_element_uid: Annotated[str | None, Field(min_length=1)] = None

    _validate_regex = field_validator("value_regex", mode="before")(validate_regex)
    _validate_name_only_contains_letters = field_validator("name", mode="before")(
        validate_name_only_contains_letters
    )
    _validate_first_character_is_lowercase = field_validator("name", mode="after")(
        validate_first_character_is_lowercase
    )

    @model_validator(mode="before")
    @classmethod
    def one_and_only_one_of_the_two_uids_must_be_present(cls, values):
        # `values` can be something other than a dict when the request body is
        # malformed (e.g. a list/null/str). Skip validation here and let
        # pydantic's standard type coercion produce a proper 422.
        if not isinstance(values, dict):
            return values
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


@make_optional
class OdmVendorAttributeOptional(OdmVendorAttribute):
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        if data.get("compatible_types") is not None:
            data["compatible_types"] = json.loads(data["compatible_types"])

        if data.get("vendor_element") is not None:
            ve = data["vendor_element"]
            if ve.get("compatible_types") is not None and isinstance(
                ve["compatible_types"], str
            ):
                ve["compatible_types"] = json.loads(ve["compatible_types"])

        return cls(**data)


class OdmVendorAttributePatchInput(OdmPatchInput):
    name: Annotated[str, Field(min_length=1)]
    compatible_types: Annotated[list[VendorAttributeCompatibleType], Field()]
    data_type: Annotated[str | None, Field(min_length=1)]
    value_regex: Annotated[str | None, Field(min_length=1)]

    _validate_regex = field_validator("value_regex", mode="before")(validate_regex)
    _validate_name_only_contains_letters = field_validator("name", mode="before")(
        validate_name_only_contains_letters
    )
    _validate_first_character_is_lowercase = field_validator("name", mode="after")(
        validate_first_character_is_lowercase
    )


class OdmVendorAttributeVersion(OdmVendorAttribute):
    """
    Class for storing OdmVendorAttribute and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)
