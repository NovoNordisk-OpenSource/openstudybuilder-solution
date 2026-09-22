from neomodel import db

from clinical_mdr_api.domain_repositories.odms.form_repository import FormRepository
from clinical_mdr_api.domains.odms.form import OdmFormAR, OdmFormVO
from clinical_mdr_api.domains.odms.utils import (
    RelationType,
    VendorAttributeCompatibleType,
    VendorElementCompatibleType,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.odms.form import (
    OdmForm,
    OdmFormItemGroupPostInput,
    OdmFormOptional,
    OdmFormPatchInput,
    OdmFormPostInput,
    OdmFormVersion,
)
from clinical_mdr_api.services._utils import ensure_transaction, get_input_or_new_value
from clinical_mdr_api.services.odms.generic_service import OdmGenericService
from clinical_mdr_api.utils import normalize_string, to_dict
from common.exceptions import BusinessLogicException, NotFoundException
from common.utils import strtobool


class OdmFormService(OdmGenericService[OdmFormAR]):
    aggregate_class = OdmFormAR
    version_class = OdmFormVersion
    repository_interface = FormRepository
    optional_model_class = OdmFormOptional

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmFormAR
    ) -> OdmForm:
        return OdmForm.from_odm_form_ar(
            odm_form_ar=item_ar,
            find_odm_vendor_attribute_by_uid=self._repos.odm_vendor_attribute_repository.find_by_uid_2,
            find_odm_item_group_by_uid_with_form_relation=self._repos.odm_item_group_repository.find_by_uid_with_form_relation,
            find_odm_vendor_element_by_uid_with_odm_element_relation=(
                self._repos.odm_vendor_element_repository.find_by_uid_with_odm_element_relation
            ),
            find_odm_vendor_attribute_by_uid_with_odm_element_relation=(
                self._repos.odm_vendor_attribute_repository.find_by_uid_with_odm_element_relation
            ),
        )

    def _create_aggregate_root(self, odm_input: OdmFormPostInput, library) -> OdmFormAR:
        return OdmFormAR.from_input_values(
            author_id=self.author_id,
            odm_vo=OdmFormVO.from_repository_values(
                oid=get_input_or_new_value(odm_input.oid, "F.", odm_input.name),
                name=odm_input.name,
                sdtm_version=odm_input.sdtm_version,
                repeating=strtobool(odm_input.repeating),
                translated_texts=odm_input.translated_texts,
                aliases=odm_input.aliases,
                item_group_uids=[],
                vendor_element_uids=[],
                vendor_attribute_uids=[],
                vendor_element_attribute_uids=[],
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            odm_object_exists_callback=self._repos.odm_form_repository.odm_object_exists,
        )

    def _edit_aggregate(
        self, item: OdmFormAR, odm_edit_input: OdmFormPatchInput
    ) -> OdmFormAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=odm_edit_input.change_description,
            odm_vo=OdmFormVO.from_repository_values(
                oid=odm_edit_input.oid,
                name=odm_edit_input.name,
                sdtm_version=odm_edit_input.sdtm_version,
                repeating=strtobool(odm_edit_input.repeating),
                translated_texts=odm_edit_input.translated_texts,
                aliases=odm_edit_input.aliases,
                item_group_uids=item.odm_vo.item_group_uids,
                vendor_element_uids=item.odm_vo.vendor_element_uids,
                vendor_attribute_uids=item.odm_vo.vendor_attribute_uids,
                vendor_element_attribute_uids=item.odm_vo.vendor_element_attribute_uids,
            ),
            odm_object_exists_callback=self._repos.odm_form_repository.odm_object_exists,
        )
        return item

    @db.transaction
    def create(self, odm_input: OdmFormPostInput) -> OdmForm:
        item = super().create(odm_input)

        super().manage_vendors(
            item.uid,
            VendorElementCompatibleType.FORM_DEF,
            VendorAttributeCompatibleType.FORM_DEF,
            odm_input.vendor_elements,
            odm_input.vendor_element_attributes,
            odm_input.vendor_attributes,
            self._repos.odm_form_repository,
        )

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_form_repository.find_by_uid_2(item.uid)
        )

    @db.transaction
    def edit_draft(self, uid: str, odm_edit_input: OdmFormPatchInput) -> OdmForm:
        super().edit_draft(uid, odm_edit_input)

        super().manage_vendors(
            uid,
            VendorElementCompatibleType.FORM_DEF,
            VendorAttributeCompatibleType.FORM_DEF,
            odm_edit_input.vendor_elements,
            odm_edit_input.vendor_element_attributes,
            odm_edit_input.vendor_attributes,
            self._repos.odm_form_repository,
        )

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_form_repository.find_by_uid_2(uid)
        )

    @ensure_transaction(db)
    def add_item_groups(
        self,
        uid: str,
        odm_form_item_group_post_input: list[OdmFormItemGroupPostInput],
        override: bool = False,
    ) -> OdmForm:
        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        renumbering_start = len(odm_form_ar.odm_vo.item_group_uids) + 1

        BusinessLogicException.raise_if(
            odm_form_ar.item_metadata.status != LibraryItemStatus.DRAFT,
            msg=self.OBJECT_NOT_IN_DRAFT,
        )

        if override:
            self._repos.odm_form_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.ITEM_GROUP,
                disconnect_all=True,
            )
            renumbering_start = 1

        vendor_attribute_patterns = self.get_regex_patterns_of_attributes(
            [
                attribute.uid
                for input_attribute in odm_form_item_group_post_input
                if input_attribute.vendor
                for attribute in input_attribute.vendor.attributes
            ]
        )
        self.are_attributes_vendor_compatible(
            [
                vendor_attribute
                for item_group in odm_form_item_group_post_input
                for vendor_attribute in item_group.vendor.attributes
            ],
            VendorAttributeCompatibleType.ITEM_GROUP_REF,
        )

        post_input = self.renumber_items_sequentially(
            odm_form_item_group_post_input, "order_number", renumbering_start
        )

        for item_group in post_input:
            if item_group.vendor:
                self.can_connect_vendor_attributes(item_group.vendor.attributes)
                self.attribute_values_matches_their_regex(
                    item_group.vendor.attributes,
                    vendor_attribute_patterns,
                )

            self._repos.odm_form_repository.add_relation(
                uid=uid,
                relation_uid=item_group.uid,
                relationship_type=RelationType.ITEM_GROUP,
                parameters={
                    "order_number": item_group.order_number,
                    "mandatory": strtobool(item_group.mandatory),
                    "collection_exception_condition_oid": item_group.collection_exception_condition_oid,
                    "vendor": to_dict(item_group.vendor),
                },
            )

        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_form_ar)

    @db.transaction
    def get_active_relationships(self, uid: str):
        NotFoundException.raise_if_not(
            self._repos.odm_form_repository.exists_by("uid", uid, True),
            "ODM Form",
            uid,
        )

        return self._repos.odm_form_repository.get_active_relationships(
            uid, ["form_ref"]
        )

    @db.transaction
    def get_forms_that_belongs_to_study_event(self):
        return self._repos.odm_form_repository.get_if_has_relationship("form_ref")
