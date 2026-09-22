from neomodel import db

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
    CTCodelistGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.odm import OdmItemRoot
from clinical_mdr_api.domain_repositories.odms.item_repository import ItemRepository
from clinical_mdr_api.domains.odms.item import CTTermItem, OdmItemAR, OdmItemVO
from clinical_mdr_api.domains.odms.utils import (
    RelationType,
    VendorAttributeCompatibleType,
    VendorElementCompatibleType,
)
from clinical_mdr_api.models.odms.item import (
    OdmItem,
    OdmItemOptional,
    OdmItemPatchInput,
    OdmItemPostInput,
    OdmItemTermRelationshipInput,
    OdmItemUnitDefinitionRelationshipInput,
    OdmItemVersion,
)
from clinical_mdr_api.services._utils import ensure_transaction, get_input_or_new_value
from clinical_mdr_api.services.odms.generic_service import OdmGenericService
from common.exceptions import NotFoundException


class OdmItemService(OdmGenericService[OdmItemAR]):
    aggregate_class = OdmItemAR
    version_class = OdmItemVersion
    repository_interface = ItemRepository
    optional_model_class = OdmItemOptional

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmItemAR
    ) -> OdmItem:
        return OdmItem.from_odm_item_ar(
            odm_item_ar=item_ar,
            find_unit_definition_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
            find_unit_definition_with_item_relation_by_item_uid=self._repos.odm_item_repository.find_unit_definition_with_item_relation_by_item_uid,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_codelist_attribute_by_codelist_uid=self._repos.ct_codelist_attribute_repository.find_by_uid,
            find_term_with_item_relation_by_item_uid=self._repos.odm_item_repository.find_term_with_item_relation_by_item_uid,
            find_odm_vendor_element_by_uid_with_odm_element_relation=(
                self._repos.odm_vendor_element_repository.find_by_uid_with_odm_element_relation
            ),
            find_odm_vendor_attribute_by_uid_with_odm_element_relation=(
                self._repos.odm_vendor_attribute_repository.find_by_uid_with_odm_element_relation
            ),
        )

    def _create_aggregate_root(self, odm_input: OdmItemPostInput, library) -> OdmItemAR:
        return OdmItemAR.from_input_values(
            author_id=self.author_id,
            odm_vo=OdmItemVO.from_repository_values(
                oid=get_input_or_new_value(odm_input.oid, "I.", odm_input.name),
                name=odm_input.name,
                prompt=odm_input.prompt,
                datatype=(
                    self._get_datatype_ct_term_item(odm_input.datatype_uid)
                    if odm_input.datatype_uid
                    else None
                ),
                length=odm_input.length,
                significant_digits=odm_input.significant_digits,
                sas_field_name=odm_input.sas_field_name,
                sds_var_name=odm_input.sds_var_name,
                origin=odm_input.origin,
                comment=odm_input.comment,
                odm_item_group=None,
                translated_texts=odm_input.translated_texts,
                aliases=odm_input.aliases,
                unit_definition_uids=[
                    unit_definition.uid
                    for unit_definition in odm_input.unit_definitions
                ],
                external_question=(
                    CTTermItem(
                        uid=odm_input.external_question.term_uid,
                        codelist_uid=odm_input.external_question.codelist_uid,
                    )
                    if odm_input.external_question
                    else None
                ),
                codelist=odm_input.codelist,
                term_uids=[term.uid for term in odm_input.terms],
                activity_instances=[],
                vendor_element_uids=[],
                vendor_attribute_uids=[],
                vendor_element_attribute_uids=[],
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            odm_object_exists_callback=self._repos.odm_item_repository.odm_object_exists,
            unit_definition_exists_by_callback=self._repos.unit_definition_repository.exists_by,
            find_codelist_attribute_callback=self._repos.ct_codelist_attribute_repository.find_by_uid,
            find_all_terms_callback=self._repos.ct_term_name_repository.find_all,
            term_exists_by_uid_callback=self._repos.ct_term_name_repository.term_exists,
        )

    def _edit_aggregate(
        self, item: OdmItemAR, odm_edit_input: OdmItemPatchInput
    ) -> OdmItemAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=odm_edit_input.change_description,
            odm_vo=OdmItemVO.from_repository_values(
                oid=odm_edit_input.oid,
                name=odm_edit_input.name,
                prompt=odm_edit_input.prompt,
                datatype=(
                    self._get_datatype_ct_term_item(odm_edit_input.datatype_uid)
                    if odm_edit_input.datatype_uid
                    else None
                ),
                length=odm_edit_input.length,
                significant_digits=odm_edit_input.significant_digits,
                sas_field_name=odm_edit_input.sas_field_name,
                sds_var_name=odm_edit_input.sds_var_name,
                origin=odm_edit_input.origin,
                odm_item_group=None,
                comment=odm_edit_input.comment,
                translated_texts=odm_edit_input.translated_texts,
                aliases=odm_edit_input.aliases,
                unit_definition_uids=[
                    unit_definition.uid
                    for unit_definition in odm_edit_input.unit_definitions
                ],
                external_question=(
                    CTTermItem(
                        uid=odm_edit_input.external_question.term_uid,
                        codelist_uid=odm_edit_input.external_question.codelist_uid,
                    )
                    if odm_edit_input.external_question
                    else None
                ),
                codelist=odm_edit_input.codelist,
                term_uids=[term.uid for term in odm_edit_input.terms],
                activity_instances=[
                    model.model_dump() for model in odm_edit_input.activity_instances
                ],
                vendor_element_uids=item.odm_vo.vendor_element_uids,
                vendor_attribute_uids=item.odm_vo.vendor_attribute_uids,
                vendor_element_attribute_uids=item.odm_vo.vendor_element_attribute_uids,
            ),
            odm_object_exists_callback=self._repos.odm_item_repository.odm_object_exists,
            unit_definition_exists_by_callback=self._repos.unit_definition_repository.exists_by,
            find_codelist_attribute_callback=self._repos.ct_codelist_attribute_repository.find_by_uid,
            find_all_terms_callback=self._repos.ct_term_name_repository.find_all,
            term_exists_by_uid_callback=self._repos.ct_term_name_repository.term_exists,
            find_activity_instance_callback=self._repos.activity_instance_repository.find_by_uid_2,
        )
        return item

    @db.transaction
    def create(self, odm_input: OdmItemPostInput) -> OdmItem:
        item = super().create(odm_input)

        self._manage_terms(
            item.uid, getattr(odm_input.codelist, "uid", None), odm_input.terms
        )
        self._manage_unit_definitions(item.uid, odm_input.unit_definitions)
        super().manage_vendors(
            item.uid,
            VendorElementCompatibleType.ITEM_DEF,
            VendorAttributeCompatibleType.ITEM_DEF,
            odm_input.vendor_elements,
            odm_input.vendor_element_attributes,
            odm_input.vendor_attributes,
            self._repos.odm_item_repository,
        )

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_item_repository.find_by_uid_2(item.uid)
        )

    @db.transaction
    def edit_draft(self, uid: str, odm_edit_input: OdmItemPatchInput) -> OdmItem:
        super().edit_draft(uid, odm_edit_input)

        self._manage_terms(
            uid,
            getattr(odm_edit_input.codelist, "uid", None),
            odm_edit_input.terms,
            True,
        )
        self._manage_unit_definitions(uid, odm_edit_input.unit_definitions, True)
        super().manage_vendors(
            uid,
            VendorElementCompatibleType.ITEM_DEF,
            VendorAttributeCompatibleType.ITEM_DEF,
            odm_edit_input.vendor_elements,
            odm_edit_input.vendor_element_attributes,
            odm_edit_input.vendor_attributes,
            self._repos.odm_item_repository,
        )

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_item_repository.find_by_uid_2(uid)
        )

    @ensure_transaction(db)
    def inactivate_final(
        self,
        uid: str,
        cascade_inactivate: bool = False,
        force_new_value_node: bool = False,
    ) -> OdmItem:
        old_item = self._find_by_uid_or_raise_not_found(uid, for_update=True)

        unit_definitions = [
            self._repos.odm_item_repository.find_unit_definition_with_item_relation_by_item_uid(
                uid, unit_definition_uid
            )
            for unit_definition_uid in old_item.odm_vo.unit_definition_uids
        ]
        unit_definitions = [
            OdmItemUnitDefinitionRelationshipInput(
                uid=unit_definition_uid,
                mandatory=unit_definition.mandatory,
                order=unit_definition.order,
            )
            for unit_definition, unit_definition_uid in zip(
                unit_definitions, old_item.odm_vo.unit_definition_uids
            )
            if unit_definition is not None
        ]

        terms = [
            self._repos.odm_item_repository.find_term_with_item_relation_by_item_uid(
                uid, term_uid
            )
            for term_uid in old_item.odm_vo.term_uids
        ]
        terms = [
            OdmItemTermRelationshipInput(
                uid=term_uid,
                mandatory=term.mandatory,
                order=term.order,
                display_text=term.display_text,
            )
            for term, term_uid in zip(terms, old_item.odm_vo.term_uids)
            if term is not None
        ]

        super().inactivate_final(uid, cascade_inactivate, force_new_value_node)

        self._manage_terms(
            uid, getattr(old_item.odm_vo.codelist, "uid", None), terms, True
        )
        self._manage_unit_definitions(uid, unit_definitions, True)

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_item_repository.find_by_uid_2(uid)
        )

    @ensure_transaction(db)
    def reactivate_retired(
        self,
        uid: str,
        cascade_reactivate: bool = False,
        force_new_value_node: bool = False,
    ) -> OdmItem:
        old_item = self._find_by_uid_or_raise_not_found(uid, for_update=True)

        unit_definitions = [
            self._repos.odm_item_repository.find_unit_definition_with_item_relation_by_item_uid(
                uid, unit_definition_uid
            )
            for unit_definition_uid in old_item.odm_vo.unit_definition_uids
        ]
        unit_definitions = [
            OdmItemUnitDefinitionRelationshipInput(
                uid=unit_definition_uid,
                mandatory=unit_definition.mandatory,
                order=unit_definition.order,
            )
            for unit_definition, unit_definition_uid in zip(
                unit_definitions, old_item.odm_vo.unit_definition_uids
            )
            if unit_definition is not None
        ]

        terms = [
            self._repos.odm_item_repository.find_term_with_item_relation_by_item_uid(
                uid, term_uid
            )
            for term_uid in old_item.odm_vo.term_uids
        ]
        terms = [
            OdmItemTermRelationshipInput(
                uid=term_uid,
                mandatory=term.mandatory,
                order=term.order,
                display_text=term.display_text,
            )
            for term, term_uid in zip(terms, old_item.odm_vo.term_uids)
            if term is not None
        ]

        super().reactivate_retired(uid, cascade_reactivate, force_new_value_node)

        self._manage_terms(
            uid, getattr(old_item.odm_vo.codelist, "uid", None), terms, True
        )
        self._manage_unit_definitions(uid, unit_definitions, True)

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_item_repository.find_by_uid_2(uid)
        )

    @ensure_transaction(db)
    def create_new_version(
        self,
        uid: str,
        cascade_new_version: bool = False,
        force_new_value_node: bool = False,
        ignore_exc: bool = False,
    ) -> OdmItem:
        old_item = self._find_by_uid_or_raise_not_found(uid, for_update=True)

        unit_definitions = [
            self._repos.odm_item_repository.find_unit_definition_with_item_relation_by_item_uid(
                uid, unit_definition_uid
            )
            for unit_definition_uid in old_item.odm_vo.unit_definition_uids
        ]
        unit_definitions = [
            OdmItemUnitDefinitionRelationshipInput(
                uid=unit_definition_uid,
                mandatory=unit_definition.mandatory,
                order=unit_definition.order,
            )
            for unit_definition, unit_definition_uid in zip(
                unit_definitions, old_item.odm_vo.unit_definition_uids
            )
            if unit_definition is not None
        ]

        terms = [
            self._repos.odm_item_repository.find_term_with_item_relation_by_item_uid(
                uid, term_uid
            )
            for term_uid in old_item.odm_vo.term_uids
        ]
        terms = [
            OdmItemTermRelationshipInput(
                uid=term_uid,
                mandatory=term.mandatory,
                order=term.order,
                display_text=term.display_text,
            )
            for term, term_uid in zip(terms, old_item.odm_vo.term_uids)
            if term is not None
        ]

        super().create_new_version(
            uid, cascade_new_version, force_new_value_node, ignore_exc
        )

        self._manage_terms(
            uid, getattr(old_item.odm_vo.codelist, "uid", None), terms, True
        )
        self._manage_unit_definitions(uid, unit_definitions, True)

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_item_repository.find_by_uid_2(uid)
        )

    def _manage_terms(
        self,
        item_uid: str,
        codelist_uid: str | None,
        input_terms: list[OdmItemTermRelationshipInput],
        for_update: bool = False,
    ):
        if for_update:
            self._repos.odm_item_repository.remove_all_codelist_terms_from_item(
                item_uid
            )

        (
            items,
            prop_names,
        ) = self._repos.ct_term_attributes_repository.get_term_attributes_by_term_uids(
            [input_term.uid for input_term in input_terms]
        )

        terms = [dict(zip(prop_names, item)) for item in items]

        if input_terms and codelist_uid:
            submission_value = CTCodelistGenericRepository.get_codelist_submval_by_uid(
                codelist_uid
            )
            value = OdmItemRoot.nodes.get(uid=item_uid).has_latest_value.single()

            for input_term in input_terms:
                ct_term = CTTermRoot.nodes.get(uid=input_term.uid)
                selected_term_node = (
                    CTCodelistAttributesRepository().get_or_create_selected_term(
                        ct_term, codelist_submission_value=submission_value
                    )
                )
                props = self._repos.ct_term_attributes_repository.get_codelist_to_term_properties(
                    input_term.uid, codelist_uid
                )

                value.has_codelist_term.connect(
                    selected_term_node,
                    {
                        "mandatory": input_term.mandatory,
                        "order": (
                            input_term.order
                            if input_term.order is not None
                            else props.get("order", 999999) or 999999
                        ),
                        "display_text": (
                            input_term.display_text
                            if not any(
                                input_term.uid == term["term_uid"]
                                and input_term.display_text
                                == term["nci_preferred_name"]
                                for term in terms
                            )
                            else None
                        ),
                    },
                )

    def _manage_unit_definitions(
        self,
        item_uid: str,
        unit_definitions: list[OdmItemUnitDefinitionRelationshipInput],
        for_update: bool = False,
    ):
        if for_update:
            self._repos.odm_item_repository.remove_relation(
                uid=item_uid,
                relation_uid=None,
                relationship_type=RelationType.UNIT_DEFINITION,
                disconnect_all=True,
            )

        for unit_definition in unit_definitions:
            self._repos.odm_item_repository.add_relation(
                uid=item_uid,
                relation_uid=unit_definition.uid,
                relationship_type=RelationType.UNIT_DEFINITION,
                parameters={
                    "mandatory": unit_definition.mandatory,
                    "order": unit_definition.order,
                },
            )

    def calculate_item_length_value(
        self,
        length: int | None,
        codelist_uid: str | None,
        input_terms: list[OdmItemTermRelationshipInput],
    ):
        if length:
            return length

        if not codelist_uid or not input_terms:
            return None

        (
            items,
            prop_names,
        ) = self._repos.ct_term_attributes_repository.get_term_name_and_attributes_by_codelist_uids(
            [codelist_uid]
        )

        terms = sorted(
            [dict(zip(prop_names, item)) for item in items],
            key=lambda elm: len(elm["submission_value"]),
            reverse=True,
        )

        input_term_uids = [input_term.uid for input_term in input_terms]

        return next(
            (
                len(term["submission_value"])
                for term in terms
                if term["term_uid"] in input_term_uids
            ),
            None,
        )

    @ensure_transaction(db)
    def get_active_relationships(self, uid: str):
        NotFoundException.raise_if_not(
            self._repos.odm_item_repository.exists_by("uid", uid, True),
            "ODM Item",
            uid,
        )

        return self._repos.odm_item_repository.get_active_relationships(
            uid, ["item_ref"]
        )

    @ensure_transaction(db)
    def get_items_that_belongs_to_item_groups(self):
        return self._repos.odm_item_repository.get_if_has_relationship("item_ref")

    def _get_datatype_ct_term_item(self, datatype_uid: str) -> CTTermItem:
        """
        Fetch CTTermItem with submission_value for the given datatype UID.
        This is needed for domain validation to work properly.
        """
        term_ar = self._repos.ct_term_name_repository.find_by_uid(datatype_uid)
        if not term_ar:
            return CTTermItem(
                uid=datatype_uid, name=None, codelist_uid=None, submission_value=None
            )

        # Get the submission value from the CTCodelistTerm
        submission_value = None
        term_root = CTTermRoot.nodes.get_or_none(uid=datatype_uid)
        if term_root:
            codelist_term = term_root.has_term_root.get_or_none()
            if codelist_term:
                submission_value = codelist_term.submission_value

        return CTTermItem(
            uid=datatype_uid,
            name=term_ar.name,
            codelist_uid=None,  # We don't need this for validation
            submission_value=submission_value,
        )
