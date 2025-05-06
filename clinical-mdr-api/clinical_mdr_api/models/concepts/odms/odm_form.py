from typing import Annotated, Callable, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domains.concepts.odms.alias import OdmAliasAR
from clinical_mdr_api.domains.concepts.odms.description import OdmDescriptionAR
from clinical_mdr_api.domains.concepts.odms.form import OdmFormAR, OdmFormRefVO
from clinical_mdr_api.domains.concepts.odms.item_group import OdmItemGroupRefVO
from clinical_mdr_api.domains.concepts.odms.vendor_attribute import (
    OdmVendorAttributeAR,
    OdmVendorAttributeRelationVO,
    OdmVendorElementAttributeRelationVO,
)
from clinical_mdr_api.domains.concepts.odms.vendor_element import (
    OdmVendorElementRelationVO,
)
from clinical_mdr_api.domains.concepts.utils import RelationType
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityHierarchySimpleModel,
)
from clinical_mdr_api.models.concepts.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_alias import OdmAliasSimpleModel
from clinical_mdr_api.models.concepts.odms.odm_common_models import (
    OdmRefVendorPostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_description import (
    OdmDescriptionBatchPatchInput,
    OdmDescriptionPostInput,
    OdmDescriptionSimpleModel,
)
from clinical_mdr_api.models.concepts.odms.odm_item_group import OdmItemGroupRefModel
from clinical_mdr_api.models.concepts.odms.odm_vendor_attribute import (
    OdmVendorAttributeRelationModel,
    OdmVendorElementAttributeRelationModel,
)
from clinical_mdr_api.models.concepts.odms.odm_vendor_element import (
    OdmVendorElementRelationModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermAttributes,
)
from clinical_mdr_api.models.utils import BaseModel, PostInputModel
from common import config
from common.utils import booltostr


class OdmForm(ConceptModel):
    oid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    repeating: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    sdtm_version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    scope: Annotated[
        SimpleCTTermAttributes | None, Field(json_schema_extra={"nullable": True})
    ] = None
    descriptions: Annotated[
        list[OdmDescriptionSimpleModel] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    aliases: list[OdmAliasSimpleModel]
    activity_groups: list[ActivityHierarchySimpleModel]
    item_groups: list[OdmItemGroupRefModel]
    vendor_elements: list[OdmVendorElementRelationModel]
    vendor_attributes: list[OdmVendorAttributeRelationModel]
    vendor_element_attributes: list[OdmVendorElementAttributeRelationModel]
    possible_actions: list[str]

    @classmethod
    def from_odm_form_ar(
        cls,
        odm_form_ar: OdmFormAR,
        find_term_callback: Callable[[str], CTTermAttributesAR | None],
        find_odm_description_by_uid: Callable[[str], OdmDescriptionAR | None],
        find_odm_alias_by_uid: Callable[[str], OdmAliasAR | None],
        find_activity_group_by_uid: Callable[[str], ActivityGroupAR | None],
        find_odm_item_group_by_uid_with_form_relation: Callable[
            [str, str], OdmItemGroupRefVO | None
        ],
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
        find_odm_vendor_element_by_uid_with_odm_element_relation: Callable[
            [str, str, RelationType], OdmVendorElementRelationVO | None
        ],
        find_odm_vendor_attribute_by_uid_with_odm_element_relation: Callable[
            [str, str, RelationType, bool],
            OdmVendorAttributeRelationVO | OdmVendorElementAttributeRelationVO | None,
        ],
    ) -> Self:
        return cls(
            uid=odm_form_ar._uid,
            oid=odm_form_ar.concept_vo.oid,
            name=odm_form_ar.concept_vo.name,
            sdtm_version=odm_form_ar.concept_vo.sdtm_version,
            repeating=booltostr(odm_form_ar.concept_vo.repeating),
            library_name=odm_form_ar.library.name,
            start_date=odm_form_ar.item_metadata.start_date,
            end_date=odm_form_ar.item_metadata.end_date,
            status=odm_form_ar.item_metadata.status.value,
            version=odm_form_ar.item_metadata.version,
            change_description=odm_form_ar.item_metadata.change_description,
            author_username=odm_form_ar.item_metadata.author_username,
            scope=SimpleCTTermAttributes.from_term_uid(
                uid=odm_form_ar.concept_vo.scope_uid,
                find_term_by_uid=find_term_callback,
            ),
            descriptions=sorted(
                [
                    OdmDescriptionSimpleModel.from_odm_description_uid(
                        uid=description_uid,
                        find_odm_description_by_uid=find_odm_description_by_uid,
                    )
                    for description_uid in odm_form_ar.concept_vo.description_uids
                ],
                key=lambda item: item.name,
            ),
            aliases=sorted(
                [
                    OdmAliasSimpleModel.from_odm_alias_uid(
                        uid=alias_uid,
                        find_odm_alias_by_uid=find_odm_alias_by_uid,
                    )
                    for alias_uid in odm_form_ar.concept_vo.alias_uids
                ],
                key=lambda item: item.name,
            ),
            activity_groups=sorted(
                [
                    ActivityHierarchySimpleModel.from_activity_uid(
                        uid=activity_group_uid,
                        find_activity_by_uid=find_activity_group_by_uid,
                    )
                    for activity_group_uid in odm_form_ar.concept_vo.activity_group_uids
                ],
                key=lambda item: item.name,
            ),
            item_groups=sorted(
                [
                    OdmItemGroupRefModel.from_odm_item_group_uid(
                        uid=item_group_uid,
                        form_uid=odm_form_ar._uid,
                        find_odm_item_group_by_uid_with_form_relation=find_odm_item_group_by_uid_with_form_relation,
                        find_odm_vendor_attribute_by_uid=find_odm_vendor_attribute_by_uid,
                    )
                    for item_group_uid in odm_form_ar.concept_vo.item_group_uids
                ],
                key=lambda item: item.order_number,
            ),
            vendor_elements=sorted(
                [
                    OdmVendorElementRelationModel.from_uid(
                        uid=vendor_element_uid,
                        odm_element_uid=odm_form_ar._uid,
                        odm_element_type=RelationType.FORM,
                        find_by_uid_with_odm_element_relation=find_odm_vendor_element_by_uid_with_odm_element_relation,
                    )
                    for vendor_element_uid in odm_form_ar.concept_vo.vendor_element_uids
                ],
                key=lambda item: item.name,
            ),
            vendor_attributes=sorted(
                [
                    OdmVendorAttributeRelationModel.from_uid(
                        uid=vendor_attribute_uid,
                        odm_element_uid=odm_form_ar._uid,
                        odm_element_type=RelationType.FORM,
                        find_by_uid_with_odm_element_relation=find_odm_vendor_attribute_by_uid_with_odm_element_relation,
                        vendor_element_attribute=False,
                    )
                    for vendor_attribute_uid in odm_form_ar.concept_vo.vendor_attribute_uids
                ],
                key=lambda item: item.name,
            ),
            vendor_element_attributes=sorted(
                [
                    OdmVendorElementAttributeRelationModel.from_uid(
                        uid=vendor_element_attribute_uid,
                        odm_element_uid=odm_form_ar._uid,
                        odm_element_type=RelationType.FORM,
                        find_by_uid_with_odm_element_relation=find_odm_vendor_attribute_by_uid_with_odm_element_relation,
                    )
                    for vendor_element_attribute_uid in odm_form_ar.concept_vo.vendor_element_attribute_uids
                ],
                key=lambda item: item.name,
            ),
            possible_actions=sorted(
                [_.value for _ in odm_form_ar.get_possible_actions()]
            ),
        )


class OdmFormRefModel(BaseModel):
    @classmethod
    def from_odm_form_uid(
        cls,
        uid: str,
        study_event_uid: str,
        find_odm_form_by_uid_with_study_event_relation: Callable[
            [str, str], OdmFormRefVO | None
        ],
    ) -> Self | None:
        if uid is not None:
            odm_form_ref_vo = find_odm_form_by_uid_with_study_event_relation(
                uid, study_event_uid
            )
            if odm_form_ref_vo is not None:
                odm_form_ref_model = cls(
                    uid=uid,
                    name=odm_form_ref_vo.name,
                    order_number=odm_form_ref_vo.order_number,
                    mandatory=odm_form_ref_vo.mandatory,
                    locked=odm_form_ref_vo.locked,
                    collection_exception_condition_oid=odm_form_ref_vo.collection_exception_condition_oid,
                )
            else:
                odm_form_ref_model = cls(
                    uid=uid,
                    name=None,
                    order_number=None,
                    mandatory=None,
                    locked=None,
                    collection_exception_condition_oid=None,
                )
        else:
            odm_form_ref_model = None
        return odm_form_ref_model

    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    order_number: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    mandatory: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    locked: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    collection_exception_condition_oid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class OdmFormPostInput(ConceptPostInput):
    oid: Annotated[str | None, Field(min_length=1)] = None
    sdtm_version: str | None = None
    repeating: Annotated[str, Field(min_length=1)]
    scope_uid: str | None = None
    descriptions: list[OdmDescriptionPostInput | str]
    alias_uids: list[str]


class OdmFormPatchInput(ConceptPatchInput):
    oid: Annotated[str | None, Field(min_length=1)]
    sdtm_version: str | None
    repeating: str | None
    scope_uid: str | None
    descriptions: list[OdmDescriptionBatchPatchInput | OdmDescriptionPostInput | str]
    alias_uids: list[str]


class OdmFormItemGroupPostInput(PostInputModel):
    uid: Annotated[str, Field(min_length=1)]
    order_number: Annotated[int, Field(lt=config.MAX_INT_NEO4J)]
    mandatory: Annotated[str, Field(min_length=1)]
    collection_exception_condition_oid: str | None = None
    vendor: OdmRefVendorPostInput


class OdmFormActivityGroupPostInput(PostInputModel):
    uid: Annotated[str, Field(min_length=1)]


class OdmFormVersion(OdmForm):
    """
    Class for storing OdmForm and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []
