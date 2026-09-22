import json
from textwrap import dedent
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.odm import (
    OdmItemGroupRoot,
    OdmItemGroupValue,
)
from clinical_mdr_api.domain_repositories.odms.generic_repository import (
    OdmGenericRepository,
)
from clinical_mdr_api.domains.odms.item_group import (
    OdmItemGroupAR,
    OdmItemGroupRefVO,
    OdmItemGroupVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmTranslatedTextModel,
)
from clinical_mdr_api.models.odms.item_group import OdmItemGroup
from clinical_mdr_api.services._utils import ensure_transaction
from common.config import settings
from common.utils import convert_to_datetime


class ItemGroupRepository(OdmGenericRepository[OdmItemGroupAR]):
    root_class = OdmItemGroupRoot
    value_class = OdmItemGroupValue
    return_model = OdmItemGroup

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> OdmItemGroupAR:
        sdtm_domains = []
        if sdtm_domain_contexts := value.has_sdtm_domain.all():
            for sdtm_domain in sdtm_domain_contexts:
                if selected_term := sdtm_domain.has_selected_term.get_or_none():
                    sdtm_domains.append(selected_term)

        return OdmItemGroupAR.from_repository_values(
            uid=root.uid,
            odm_vo=OdmItemGroupVO.from_repository_values(
                oid=value.oid,
                name=value.name,
                repeating=value.repeating,
                is_reference_data=value.is_reference_data,
                sas_dataset_name=value.sas_dataset_name,
                origin=value.origin,
                purpose=value.purpose,
                comment=value.comment,
                translated_texts=[
                    OdmTranslatedTextModel(
                        text_type=translated_text_value.text_type,
                        language=translated_text_value.language,
                        text=translated_text_value.text,
                    )
                    for translated_text_value in value.has_translated_text.all()
                ],
                aliases=[
                    OdmAliasModel(name=alias_value.name, context=alias_value.context)
                    for alias_value in value.has_alias.all()
                ],
                sdtm_domain_uids=[sdtm_domain.uid for sdtm_domain in sdtm_domains],
                item_uids=[
                    item_root.uid
                    for item_value in value.item_ref.all()
                    if (item_root := item_value.has_root.single())
                ],
                vendor_element_uids=[
                    vendor_element_root.uid
                    for vendor_element_value in value.has_vendor_element.all()
                    if (vendor_element_root := vendor_element_value.has_root.single())
                ],
                vendor_attribute_uids=[
                    vendor_attribute_root.uid
                    for vendor_attribute_value in value.has_vendor_attribute.all()
                    if (
                        vendor_attribute_root := vendor_attribute_value.has_root.single()
                    )
                ],
                vendor_element_attribute_uids=[
                    vendor_element_attribute_root.uid
                    for vendor_element_attribute_value in value.has_vendor_element_attribute.all()
                    if (
                        vendor_element_attribute_root := vendor_element_attribute_value.has_root.single()
                    )
                ],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict[str, Any]
    ) -> OdmItemGroupAR:
        major, minor = input_dict["version"].split(".")
        odm_item_group_ar = OdmItemGroupAR.from_repository_values(
            uid=input_dict["uid"],
            odm_vo=OdmItemGroupVO.from_repository_values(
                oid=input_dict.get("oid"),
                name=input_dict["name"],
                repeating=input_dict.get("repeating"),
                is_reference_data=input_dict.get("is_reference_data"),
                sas_dataset_name=input_dict.get("sas_dataset_name"),
                origin=input_dict.get("origin"),
                purpose=input_dict.get("purpose"),
                comment=input_dict.get("comment"),
                translated_texts=[
                    OdmTranslatedTextModel(
                        text_type=translated_text["text_type"],
                        language=translated_text["language"],
                        text=translated_text["text"],
                    )
                    for translated_text in input_dict["translated_texts"]
                ],
                aliases=[
                    OdmAliasModel(name=alias["name"], context=alias["context"])
                    for alias in input_dict["aliases"]
                ],
                sdtm_domain_uids=input_dict["sdtm_domain_uids"],
                item_uids=input_dict["item_uids"],
                vendor_element_uids=input_dict["vendor_element_uids"],
                vendor_attribute_uids=input_dict["vendor_attribute_uids"],
                vendor_element_attribute_uids=input_dict[
                    "vendor_element_attribute_uids"
                ],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict["library_name"],
                is_library_editable_callback=(
                    lambda _: input_dict["is_library_editable"]
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict["change_description"],
                status=LibraryItemStatus(input_dict.get("status")),
                author_id=input_dict["author_id"],
                author_username=input_dict.get("author_username"),
                start_date=convert_to_datetime(value=input_dict["start_date"]),
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

        return odm_item_group_ar

    def _get_specific_field_mapping(self) -> dict[str, str]:
        """Item Group specific field mappings - simple fields only."""
        return {
            "name": "odm_value.name AS name",
            "oid": "odm_value.oid AS oid",
            "repeating": "toString(odm_value.repeating) AS repeating",
            "is_reference_data": "toString(odm_value.is_reference_data) AS is_reference_data",
            "sas_dataset_name": "odm_value.sas_dataset_name AS sas_dataset_name",
            "origin": "odm_value.origin AS origin",
            "purpose": "odm_value.purpose AS purpose",
            "comment": "odm_value.comment AS comment",
        }

    def _get_computed_field_expressions(self) -> dict[str, str]:
        """Item Group computed field expressions."""
        # pylint: disable=line-too-long
        return {
            "translated_texts": "[(odm_value)-[:HAS_TRANSLATED_TEXT]->(dv:OdmTranslatedText) | {text_type: dv.text_type, language: dv.language, text: dv.text}] AS translated_texts",
            "aliases": "[(odm_value)-[:HAS_ALIAS]->(av:OdmAlias) | {name: av.name, context: av.context}] AS aliases",
            "sdtm_domains": f"""[(odm_value)-[:HAS_SDTM_DOMAIN]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(tr:CTTermRoot) |
            {{
                term_uid: tr.uid,
                term_name: head([(tr)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(tnv:CTTermNameValue) | tnv.name]),
                submission_value: head(
                    [(tr)<-[:HAS_TERM_ROOT]->(cct:CTCodelistTerm)<-[:HAS_TERM]-(:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(ctcav:CTCodelistAttributesValue {{submission_value: "{settings.stdm_domain_cl_submval}"}}) | cct.submission_value]
                ),
                preferred_term: head([(tr)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(tav2:CTTermAttributesValue) | tav2.preferred_term])
            }}] AS sdtm_domains""",
            "items": "[(odm_value)-[iref:ITEM_REF]->(iv:OdmItemValue)<-[hv:HAS_VERSION]-(ir:OdmItemRoot) | {uid: ir.uid, oid: iv.oid, name: iv.name, order_number: iref.order_number, mandatory: iref.mandatory, key_sequence: iref.key_sequence, method_oid: iref.method_oid, imputation_method_oid: iref.imputation_method_oid, role: iref.role, role_codelist_oid: iref.role_codelist_oid, collection_exception_condition_oid: iref.collection_exception_condition_oid, version: hv.version}] AS items",
            "vendor_elements": "[(odm_value)-[hve:HAS_VENDOR_ELEMENT]->(vev:OdmVendorElementValue)<-[:HAS_VERSION]-(ver:OdmVendorElementRoot) | {uid: ver.uid, name: vev.name, value: hve.value}] AS vendor_elements",
            "vendor_attributes": "[(odm_value)-[hva:HAS_VENDOR_ATTRIBUTE]->(vav:OdmVendorAttributeValue)<-[:HAS_VERSION]-(var:OdmVendorAttributeRoot) | {uid: var.uid, name: vav.name, data_type: vav.data_type, value_regex: vav.value_regex, compatible_types: vav.compatible_types, value: hva.value}] AS vendor_attributes",
            "vendor_element_attributes": "[(odm_value)-[hvea:HAS_VENDOR_ELEMENT_ATTRIBUTE]->(vav:OdmVendorAttributeValue)<-[:HAS_VERSION]-(var:OdmVendorAttributeRoot) | {uid: var.uid, name: vav.name, data_type: vav.data_type, value_regex: vav.value_regex, compatible_types: vav.compatible_types, value: hvea.value}] AS vendor_element_attributes",
        }

    def specific_alias_clause(self, **kwargs) -> str:
        return dedent(
            "WITH *,"
            + ", ".join(self._get_specific_field_mapping().values())
            + ","
            + ", ".join(self._get_computed_field_expressions().values())
            + """
            WITH *,
            apoc.coll.toSet([sdtm_domain in sdtm_domains | sdtm_domain.term_uid]) AS sdtm_domain_uids,
            apoc.coll.toSet([item in items | item.uid]) AS item_uids,
            apoc.coll.toSet([vendor_element in vendor_elements | vendor_element.uid]) AS vendor_element_uids,
            apoc.coll.toSet([vendor_attribute in vendor_attributes | vendor_attribute.uid]) AS vendor_attribute_uids,
            apoc.coll.toSet([vendor_element_attribute in vendor_element_attributes | vendor_element_attribute.uid]) AS vendor_element_attribute_uids
            """
        )

    def _get_or_create_value(
        self, root: VersionRoot, ar: OdmItemGroupAR, force_new_value_node: bool = False
    ) -> VersionValue:
        current_latest = root.has_latest_value.single()
        old_item_ref_nodes = current_latest.item_ref.all() if current_latest else []
        new_item_ref_nodes = [
            old_item_root.has_latest_value.single()
            for old_item_ref_node in old_item_ref_nodes
            if (old_item_root := old_item_ref_node.has_root.single())
        ]
        new_value = super()._get_or_create_value(root, ar, force_new_value_node)

        for old_item_ref_node, new_item_ref_node in zip(
            old_item_ref_nodes,
            new_item_ref_nodes,
        ):
            params = current_latest.item_ref.relationship(old_item_ref_node)
            new_value.item_ref.connect(
                new_item_ref_node,
                {
                    "order_number": params.order_number,
                    "mandatory": params.mandatory,
                    "key_sequence": params.key_sequence,
                    "method_oid": params.method_oid,
                    "imputation_method_oid": params.imputation_method_oid,
                    "role": params.role,
                    "role_codelist_oid": params.role_codelist_oid,
                    "collection_exception_condition_oid": params.collection_exception_condition_oid,
                    "vendor": params.vendor,
                },
            )

        if ar.should_disconnect_relationships:
            for item_ref_node in old_item_ref_nodes:
                current_latest.item_ref.disconnect(item_ref_node)

        new_value.has_sdtm_domain.disconnect_all()

        self.manage_vendor_relationships(
            current_latest, new_value, ar.should_disconnect_relationships
        )
        self.connect_translated_texts(ar.odm_vo.translated_texts, new_value)
        self.connect_aliases(ar.odm_vo.aliases, new_value)

        for sdtm_domain_uid in ar.odm_vo.sdtm_domain_uids:
            sdtm_domain_node = CTTermRoot.nodes.get(uid=sdtm_domain_uid)
            selected_term_node = (
                CTCodelistAttributesRepository().get_or_create_selected_term(
                    sdtm_domain_node,
                    codelist_submission_value=settings.stdm_domain_cl_submval,
                    catalogue_name=settings.sdtm_ct_catalogue_name,
                )
            )
            new_value.has_sdtm_domain.connect(selected_term_node)

        return new_value

    def _create_new_value_node(self, ar: OdmItemGroupAR) -> OdmItemGroupValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.oid = ar.odm_vo.oid
        value_node.repeating = ar.odm_vo.repeating
        value_node.is_reference_data = ar.odm_vo.is_reference_data
        value_node.sas_dataset_name = ar.odm_vo.sas_dataset_name
        value_node.origin = ar.odm_vo.origin
        value_node.purpose = ar.odm_vo.purpose
        value_node.comment = ar.odm_vo.comment

        return value_node

    def _has_data_changed(self, ar: OdmItemGroupAR, value: OdmItemGroupValue) -> bool:
        are_odm_properties_changed = super()._has_data_changed(ar=ar, value=value)

        translated_text_nodes = {
            OdmTranslatedTextModel(
                text_type=translated_text_node.text_type,
                language=translated_text_node.language,
                text=translated_text_node.text,
            )
            for translated_text_node in value.has_translated_text.all()
        }
        alias_nodes = {
            OdmAliasModel(name=alias_node.name, context=alias_node.context)
            for alias_node in value.has_alias.all()
        }
        sdtm_domain_uids = {
            sdtm_domain.uid
            for sdtm_domain_context in value.has_sdtm_domain.all()
            if (sdtm_domain := sdtm_domain_context.has_selected_term.get_or_none())
        }

        are_rels_changed = (
            set(ar.odm_vo.translated_texts) != translated_text_nodes
            or set(ar.odm_vo.aliases) != alias_nodes
            or set(ar.odm_vo.sdtm_domain_uids) != sdtm_domain_uids
        )

        return (
            are_odm_properties_changed
            or are_rels_changed
            or ar.odm_vo.oid != value.oid
            or ar.odm_vo.repeating != value.repeating
            or ar.odm_vo.is_reference_data != value.is_reference_data
            or ar.odm_vo.sas_dataset_name != value.sas_dataset_name
            or ar.odm_vo.origin != value.origin
            or ar.odm_vo.purpose != value.purpose
            or ar.odm_vo.comment != value.comment
        )

    def find_by_uid_with_form_relation(
        self, uid: str, form_uid: str, form_version: str
    ):
        rs, _ = db.cypher_query(
            """
            MATCH (:OdmFormRoot {uid: $form_uid})-[:HAS_VERSION {version: $form_version}]->(:OdmFormValue)
            -[ref:ITEM_GROUP_REF]->(value:OdmItemGroupValue)

            MATCH (value)<-[hv_rel:HAS_VERSION]-(:OdmItemGroupRoot {uid: $uid})
            WITH value, ref, hv_rel
            ORDER BY hv_rel.start_date DESC
            WITH value, ref, collect(hv_rel) AS hv_rels

            RETURN
                value.oid AS oid,
                value.name AS name,
                hv_rels[0].version AS version,
                ref.order_number AS order_number,
                ref.mandatory AS mandatory,
                ref.collection_exception_condition_oid AS collection_exception_condition_oid,
                ref.vendor AS vendor
            """,
            params={"uid": uid, "form_uid": form_uid, "form_version": form_version},
            resolve_objects=True,
        )

        return OdmItemGroupRefVO.from_repository_values(
            uid=uid,
            oid=rs[0][0],
            name=rs[0][1],
            version=rs[0][2],
            form_uid=form_uid,
            order_number=rs[0][3],
            mandatory=rs[0][4],
            collection_exception_condition_oid=rs[0][5],
            vendor=json.loads(rs[0][6]) if rs[0][6] else {},
        )

    @ensure_transaction(db)
    def _connect_relationships_to_new_value_node(
        self, root: VersionRoot, _: VersionValue
    ) -> None:
        """
        - Upgrades all incoming ITEM_GROUP_REF relationships to the second latest version to
        point to the latest version of OdmItemGroupValue, preserving relationship properties.
        of its child OdmItemValue nodes are connected to.
        """
        db.cypher_query(
            f"""
            MATCH (root:{self.root_class.__name__} {{uid: $root_uid}})-[ver_rel:HAS_VERSION]->(value:{self.value_class.__name__})

            WITH root, ver_rel, value
            ORDER BY ver_rel.start_date DESC, ver_rel.end_date DESC
            LIMIT 2
            WITH root, collect(value) AS values
            WITH root, values[0] as latest_value, values[1] as second_latest_value

            MATCH (:OdmFormRoot)-[p_ver_rel:HAS_VERSION]->(parent_value:OdmFormValue)-[ref_rel:ITEM_GROUP_REF]->(second_latest_value)
            WHERE p_ver_rel.end_date IS NULL AND p_ver_rel.status = "Draft"

            WITH latest_value, ref_rel, parent_value,
                ref_rel.order_number AS order_number,
                ref_rel.mandatory AS mandatory,
                ref_rel.collection_exception_condition_oid AS collection_exception_condition_oid,
                ref_rel.vendor AS vendor

            CREATE (parent_value)-[new_ref_rel:ITEM_GROUP_REF]->(latest_value)

            SET new_ref_rel.order_number = order_number,
                new_ref_rel.mandatory = mandatory,
                new_ref_rel.collection_exception_condition_oid = collection_exception_condition_oid,
                new_ref_rel.vendor = vendor

            DELETE ref_rel
            """,
            {"root_uid": root.uid},
        )
