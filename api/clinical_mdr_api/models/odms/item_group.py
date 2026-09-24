from typing import Annotated, Any, Callable, Self, overload

from pydantic import Field, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_name_repository import (
    CTCodelistNameRepository,
)
from clinical_mdr_api.domains.odms.item import OdmItemRefVO
from clinical_mdr_api.domains.odms.item_group import OdmItemGroupAR, OdmItemGroupRefVO
from clinical_mdr_api.domains.odms.utils import RelationType
from clinical_mdr_api.domains.odms.vendor_attribute import (
    OdmVendorAttributeAR,
    OdmVendorAttributeRelationVO,
    OdmVendorElementAttributeRelationVO,
)
from clinical_mdr_api.domains.odms.vendor_element import OdmVendorElementRelationVO
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCodelistTermModel,
)
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmBaseModel,
    OdmPatchInput,
    OdmPostInput,
    OdmRefVendor,
    OdmRefVendorAttributeModel,
    OdmRefVendorPostInput,
    OdmTranslatedTextModel,
    OdmVendorElementRelationPostInput,
    OdmVendorRelationPostInput,
    deduplicate_and_keep_newest_version,
)
from clinical_mdr_api.models.odms.item import OdmItemRefModel
from clinical_mdr_api.models.odms.vendor_attribute import (
    OdmVendorAttributeRelationModel,
    OdmVendorElementAttributeRelationModel,
)
from clinical_mdr_api.models.odms.vendor_element import OdmVendorElementRelationModel
from clinical_mdr_api.models.utils import BaseModel, PostInputModel, make_optional
from clinical_mdr_api.models.validators import (
    BOOLEAN_STRING_PATTERN,
    has_english_description,
    translated_text_uniqueness_check,
    validate_string_represents_boolean,
)
from common.config import settings
from common.utils import booltostr


class OdmItemGroup(OdmBaseModel):
    oid: Annotated[str | None, Field()]
    repeating: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    is_reference_data: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    sas_dataset_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    origin: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    purpose: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    comment: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    translated_texts: Annotated[list[OdmTranslatedTextModel], Field()]
    aliases: Annotated[list[OdmAliasModel], Field()]
    sdtm_domains: Annotated[list[SimpleCodelistTermModel], Field()]
    items: Annotated[list[OdmItemRefModel], Field()]
    vendor_elements: Annotated[list[OdmVendorElementRelationModel], Field()]
    vendor_attributes: Annotated[list[OdmVendorAttributeRelationModel], Field()]
    vendor_element_attributes: Annotated[
        list[OdmVendorElementAttributeRelationModel], Field()
    ]
    possible_actions: Annotated[list[str], Field()]

    _validate_string_represents_boolean = field_validator(
        "repeating", "is_reference_data", mode="before"
    )(validate_string_represents_boolean)

    @classmethod
    def from_odm_item_group_ar(
        cls,
        odm_item_group_ar: OdmItemGroupAR,
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
        find_odm_item_by_uid_with_item_group_relation: Callable[
            [str, str, str], OdmItemRefVO
        ],
        find_odm_vendor_element_by_uid_with_odm_element_relation: Callable[
            [str, str, str, RelationType], OdmVendorElementRelationVO
        ],
        find_odm_vendor_attribute_by_uid_with_odm_element_relation: Callable[
            [str, str, str, RelationType, bool],
            OdmVendorAttributeRelationVO | OdmVendorElementAttributeRelationVO,
        ],
    ) -> Self:
        codelist_repo = CTCodelistNameRepository()
        domain_terms = []
        for sdtm_domain_uid in odm_item_group_ar.odm_vo.sdtm_domain_uids:
            term = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=sdtm_domain_uid,
                codelist_submission_value=settings.stdm_domain_cl_submval,
                find_codelist_term_by_uid_and_submission_value=codelist_repo.get_codelist_term_by_uid_and_submval,
            )
            if term is not None:
                domain_terms.append(term)

        return cls(
            uid=odm_item_group_ar._uid,
            oid=odm_item_group_ar.odm_vo.oid,
            name=odm_item_group_ar.name,
            repeating=booltostr(odm_item_group_ar.odm_vo.repeating),
            is_reference_data=booltostr(odm_item_group_ar.odm_vo.is_reference_data),
            sas_dataset_name=odm_item_group_ar.odm_vo.sas_dataset_name,
            origin=odm_item_group_ar.odm_vo.origin,
            purpose=odm_item_group_ar.odm_vo.purpose,
            comment=odm_item_group_ar.odm_vo.comment,
            library_name=odm_item_group_ar.library.name,
            start_date=odm_item_group_ar.item_metadata.start_date,
            end_date=odm_item_group_ar.item_metadata.end_date,
            status=odm_item_group_ar.item_metadata.status.value,
            version=odm_item_group_ar.item_metadata.version,
            change_description=odm_item_group_ar.item_metadata.change_description,
            author_username=odm_item_group_ar.item_metadata.author_username,
            translated_texts=sorted(
                odm_item_group_ar.odm_vo.translated_texts,
                key=lambda item: (item.text_type.value, item.text),
            ),
            aliases=sorted(
                odm_item_group_ar.odm_vo.aliases, key=lambda item: item.name
            ),
            sdtm_domains=sorted(
                domain_terms,
                key=lambda item: item.submission_value or "",
            ),
            items=sorted(
                [
                    OdmItemRefModel.from_odm_item_uid(
                        uid=item_uid,
                        item_group_uid=odm_item_group_ar._uid,
                        item_group_version=odm_item_group_ar.item_metadata.version,
                        find_odm_item_by_uid_with_item_group_relation=find_odm_item_by_uid_with_item_group_relation,
                        find_odm_vendor_attribute_by_uid=find_odm_vendor_attribute_by_uid,
                    )
                    for item_uid in odm_item_group_ar.odm_vo.item_uids
                ],
                key=lambda item: item.order_number,
            ),
            vendor_elements=sorted(
                [
                    OdmVendorElementRelationModel.from_uid(
                        uid=vendor_element_uid,
                        odm_element_uid=odm_item_group_ar._uid,
                        odm_element_version=odm_item_group_ar.item_metadata.version,
                        odm_element_type=RelationType.ITEM_GROUP,
                        find_by_uid_with_odm_element_relation=find_odm_vendor_element_by_uid_with_odm_element_relation,
                    )
                    for vendor_element_uid in odm_item_group_ar.odm_vo.vendor_element_uids
                ],
                key=lambda item: item.name or "",
            ),
            vendor_attributes=sorted(
                [
                    OdmVendorAttributeRelationModel.from_uid(
                        uid=vendor_attribute_uid,
                        odm_element_uid=odm_item_group_ar._uid,
                        odm_element_version=odm_item_group_ar.item_metadata.version,
                        odm_element_type=RelationType.ITEM_GROUP,
                        find_by_uid_with_odm_element_relation=find_odm_vendor_attribute_by_uid_with_odm_element_relation,  # type: ignore[arg-type]
                        vendor_element_attribute=False,
                    )
                    for vendor_attribute_uid in odm_item_group_ar.odm_vo.vendor_attribute_uids
                ],
                key=lambda item: item.name or "",
            ),
            vendor_element_attributes=sorted(
                [
                    OdmVendorElementAttributeRelationModel.from_uid(
                        uid=vendor_element_attribute_uid,
                        odm_element_uid=odm_item_group_ar._uid,
                        odm_element_version=odm_item_group_ar.item_metadata.version,
                        odm_element_type=RelationType.ITEM_GROUP,
                        find_by_uid_with_odm_element_relation=find_odm_vendor_attribute_by_uid_with_odm_element_relation,  # type: ignore[arg-type]
                    )
                    for vendor_element_attribute_uid in odm_item_group_ar.odm_vo.vendor_element_attribute_uids
                ],
                key=lambda item: item.name or "",
            ),
            possible_actions=sorted(
                [_.value for _ in odm_item_group_ar.get_possible_actions()]
            ),
        )


class OdmItemGroupRefModel(BaseModel):
    @overload
    @classmethod
    def from_odm_item_group_uid(
        cls,
        uid: str,
        form_uid: str,
        form_version: str,
        find_odm_item_group_by_uid_with_form_relation: Callable[
            [str, str, str], OdmItemGroupRefVO
        ],
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> Self: ...
    @overload
    @classmethod
    def from_odm_item_group_uid(
        cls,
        uid: None,
        form_uid: str,
        form_version: str,
        find_odm_item_group_by_uid_with_form_relation: Callable[
            [str, str, str], OdmItemGroupRefVO
        ],
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> None: ...
    @classmethod
    def from_odm_item_group_uid(
        cls,
        uid: str | None,
        form_uid: str,
        form_version: str,
        find_odm_item_group_by_uid_with_form_relation: Callable[
            [str, str, str], OdmItemGroupRefVO
        ],
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> Self | None:
        odm_item_group_ref_model = None

        if uid is not None:
            odm_item_group_ref_vo = find_odm_item_group_by_uid_with_form_relation(
                uid, form_uid, form_version
            )
            if odm_item_group_ref_vo is not None:
                odm_item_group_ref_model = cls(
                    uid=uid,
                    oid=odm_item_group_ref_vo.oid,
                    name=odm_item_group_ref_vo.name,
                    version=odm_item_group_ref_vo.version,
                    order_number=odm_item_group_ref_vo.order_number,
                    mandatory=odm_item_group_ref_vo.mandatory,
                    collection_exception_condition_oid=odm_item_group_ref_vo.collection_exception_condition_oid,
                    vendor=OdmRefVendor(
                        attributes=(
                            [
                                OdmRefVendorAttributeModel.from_uid(
                                    uid=attribute["uid"],
                                    value=attribute["value"],
                                    find_odm_vendor_attribute_by_uid=find_odm_vendor_attribute_by_uid,
                                )
                                for attribute in odm_item_group_ref_vo.vendor[
                                    "attributes"
                                ]
                            ]
                            if odm_item_group_ref_vo.vendor
                            else []
                        ),
                    ),
                )
            else:
                odm_item_group_ref_model = cls(
                    uid=uid,
                    oid=None,
                    name=None,
                    version=None,
                    order_number=None,
                    mandatory=None,
                    collection_exception_condition_oid=None,
                    vendor=OdmRefVendor(attributes=[]),
                )
        return odm_item_group_ref_model

    uid: Annotated[str, Field()]
    oid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    order_number: Annotated[int, Field()] = 999999
    mandatory: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    collection_exception_condition_oid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    vendor: Annotated[OdmRefVendor, Field()]


class OdmItemGroupPostInput(OdmPostInput):
    oid: Annotated[str | None, Field(min_length=1)] = None
    repeating: Annotated[str, Field(pattern=BOOLEAN_STRING_PATTERN)]
    is_reference_data: Annotated[str | None, Field(pattern=BOOLEAN_STRING_PATTERN)] = (
        None
    )
    sas_dataset_name: Annotated[str | None, Field()] = None
    origin: Annotated[str | None, Field()] = None
    purpose: Annotated[str | None, Field()] = None
    comment: Annotated[str | None, Field()] = None
    translated_texts: Annotated[list[OdmTranslatedTextModel], Field()]
    aliases: list[OdmAliasModel] = Field(default_factory=list)
    sdtm_domain_uids: Annotated[list[str], Field()]
    vendor_elements: list[OdmVendorElementRelationPostInput] = Field(
        default_factory=list
    )
    vendor_element_attributes: list[OdmVendorRelationPostInput] = Field(
        default_factory=list
    )
    vendor_attributes: list[OdmVendorRelationPostInput] = Field(default_factory=list)

    _validate_string_represents_boolean = field_validator(
        "repeating", "is_reference_data", mode="before"
    )(validate_string_represents_boolean)
    _translated_text_uniqueness_check = field_validator("translated_texts")(
        translated_text_uniqueness_check
    )
    _english_description_validator = field_validator("translated_texts")(
        has_english_description
    )


class OdmItemGroupPatchInput(OdmPatchInput):
    name: Annotated[str, Field(min_length=1)]
    oid: Annotated[str | None, Field(min_length=1)]
    repeating: Annotated[str | None, Field(pattern=BOOLEAN_STRING_PATTERN)]
    is_reference_data: Annotated[str | None, Field(pattern=BOOLEAN_STRING_PATTERN)]
    sas_dataset_name: Annotated[str | None, Field()]
    origin: Annotated[str | None, Field()]
    purpose: Annotated[str | None, Field()]
    comment: Annotated[str | None, Field()]
    translated_texts: Annotated[list[OdmTranslatedTextModel], Field()]
    aliases: list[OdmAliasModel] = Field(default_factory=list)
    sdtm_domain_uids: Annotated[list[str], Field()]
    vendor_elements: Annotated[list[OdmVendorElementRelationPostInput], Field()]
    vendor_element_attributes: Annotated[list[OdmVendorRelationPostInput], Field()]
    vendor_attributes: Annotated[list[OdmVendorRelationPostInput], Field()]

    _validate_string_represents_boolean = field_validator(
        "repeating", "is_reference_data", mode="before"
    )(validate_string_represents_boolean)
    _translated_text_uniqueness_check = field_validator("translated_texts")(
        translated_text_uniqueness_check
    )
    _english_description_validator = field_validator("translated_texts")(
        has_english_description
    )


@make_optional
class OdmItemGroupOptional(OdmItemGroup):
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        if data.get("repeating") is not None:
            data["repeating"] = booltostr(data["repeating"])
        if data.get("is_reference_data") is not None:
            data["is_reference_data"] = booltostr(data["is_reference_data"])

        if data.get("items") is not None:
            data["items"] = deduplicate_and_keep_newest_version(data.get("items", []))

            for item in data["items"]:
                if item.get("order_number") is not None:
                    item["order_number"] = item.pop("order_number")
                if item.get("mandatory") is not None and isinstance(
                    item["mandatory"], bool
                ):
                    item["mandatory"] = booltostr(item["mandatory"])
                item.setdefault("vendor", {"attributes": []})

        return cls(**data)


class OdmItemGroupItemPostInput(PostInputModel):
    uid: Annotated[str, Field(min_length=1)]
    order_number: Annotated[int, Field(lt=settings.max_int_neo4j)]
    mandatory: Annotated[str, Field()]
    key_sequence: Annotated[str | None, Field()] = None
    method_oid: Annotated[str | None, Field()] = None
    imputation_method_oid: Annotated[str | None, Field()] = None
    role: Annotated[str | None, Field()] = None
    role_codelist_oid: Annotated[str | None, Field()] = None
    collection_exception_condition_oid: Annotated[str | None, Field()] = None
    vendor: OdmRefVendorPostInput


class OdmItemGroupVersion(OdmItemGroup):
    """
    Class for storing OdmItemGroup and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)
