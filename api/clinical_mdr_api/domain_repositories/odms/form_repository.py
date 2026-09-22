from textwrap import dedent
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.odm import OdmFormRoot, OdmFormValue
from clinical_mdr_api.domain_repositories.odms.generic_repository import (
    OdmGenericRepository,
)
from clinical_mdr_api.domains.odms.form import OdmFormAR, OdmFormRefVO, OdmFormVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmTranslatedTextModel,
)
from clinical_mdr_api.models.odms.form import OdmForm
from clinical_mdr_api.services._utils import ensure_transaction
from common.utils import convert_to_datetime


class FormRepository(OdmGenericRepository[OdmFormAR]):
    root_class = OdmFormRoot
    value_class = OdmFormValue
    return_model = OdmForm

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> OdmFormAR:
        return OdmFormAR.from_repository_values(
            uid=root.uid,
            odm_vo=OdmFormVO.from_repository_values(
                oid=value.oid,
                name=value.name,
                sdtm_version=value.sdtm_version,
                repeating=value.repeating,
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
                item_group_uids=[
                    item_group_root.uid
                    for item_group_value in value.item_group_ref.all()
                    if (item_group_root := item_group_value.has_root.single())
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
    ) -> OdmFormAR:
        major, minor = input_dict["version"].split(".")
        odm_form_ar = OdmFormAR.from_repository_values(
            uid=input_dict["uid"],
            odm_vo=OdmFormVO.from_repository_values(
                oid=input_dict.get("oid"),
                name=input_dict["name"],
                sdtm_version=input_dict.get("sdtm_version"),
                repeating=input_dict.get("repeating"),
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
                item_group_uids=input_dict["item_group_uids"],
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

        return odm_form_ar

    def _get_specific_field_mapping(self) -> dict[str, str]:
        """Form specific field mappings - simple fields only."""
        return {
            "name": "odm_value.name AS name",
            "oid": "odm_value.oid AS oid",
            "repeating": "toString(odm_value.repeating) AS repeating",
            "sdtm_version": "odm_value.sdtm_version AS sdtm_version",
        }

    def _get_computed_field_expressions(self) -> dict[str, str]:
        """Form computed field expressions - requires list comprehensions."""
        # pylint: disable=line-too-long
        return {
            "translated_texts": "[(odm_value)-[:HAS_TRANSLATED_TEXT]->(dv:OdmTranslatedText) | {text_type: dv.text_type, language: dv.language, text: dv.text}] AS translated_texts",
            "aliases": "[(odm_value)-[:HAS_ALIAS]->(av:OdmAlias) | {name: av.name, context: av.context}] AS aliases",
            "item_groups": "[(odm_value)-[igref:ITEM_GROUP_REF]->(igv:OdmItemGroupValue)<-[hv:HAS_VERSION]-(igr:OdmItemGroupRoot) | {uid: igr.uid, oid: igv.oid, name: igv.name, order_number: igref.order_number, mandatory: igref.mandatory, collection_exception_condition_oid: igref.collection_exception_condition_oid, version: hv.version}] AS item_groups",
            "vendor_elements": "[(odm_value)-[hve:HAS_VENDOR_ELEMENT]->(vev:OdmVendorElementValue)<-[:HAS_VERSION]-(ver:OdmVendorElementRoot) | {uid: ver.uid, name: vev.name, compatible_types: vev.compatible_types, value: hve.value}] AS vendor_elements",
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
            apoc.coll.toSet([item_group in item_groups | item_group.uid]) AS item_group_uids,
            apoc.coll.toSet([vendor_element in vendor_elements | vendor_element.uid]) AS vendor_element_uids,
            apoc.coll.toSet([vendor_attribute in vendor_attributes | vendor_attribute.uid]) AS vendor_attribute_uids,
            apoc.coll.toSet([vendor_element_attribute in vendor_element_attributes | vendor_element_attribute.uid]) AS vendor_element_attribute_uids
            """
        )

    def _get_or_create_value(
        self,
        root: VersionRoot,
        ar: OdmFormAR,
        force_new_value_node: bool = False,
    ) -> VersionValue:
        current_latest = root.has_latest_value.single()
        old_item_group_ref_nodes = (
            current_latest.item_group_ref.all() if current_latest else []
        )
        new_item_group_ref_nodes = [
            old_item_group_root.has_latest_value.single()
            for old_item_group_ref_node in old_item_group_ref_nodes
            if (old_item_group_root := old_item_group_ref_node.has_root.single())
        ]

        new_value = super()._get_or_create_value(root, ar, force_new_value_node)

        for old_item_group_ref_node, new_item_group_ref_node in zip(
            old_item_group_ref_nodes, new_item_group_ref_nodes
        ):
            params = current_latest.item_group_ref.relationship(old_item_group_ref_node)
            new_value.item_group_ref.connect(
                new_item_group_ref_node,
                {
                    "order_number": params.order_number,
                    "mandatory": params.mandatory,
                    "collection_exception_condition_oid": params.collection_exception_condition_oid,
                    "vendor": params.vendor,
                },
            )

        if ar.should_disconnect_relationships:
            for old_item_group_ref_node in old_item_group_ref_nodes:
                current_latest.item_group_ref.disconnect(old_item_group_ref_node)

        self.manage_vendor_relationships(
            current_latest, new_value, ar.should_disconnect_relationships
        )
        self.connect_translated_texts(ar.odm_vo.translated_texts, new_value)
        self.connect_aliases(ar.odm_vo.aliases, new_value)

        return new_value

    def _create_new_value_node(self, ar: OdmFormAR) -> OdmFormValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.oid = ar.odm_vo.oid
        value_node.sdtm_version = ar.odm_vo.sdtm_version
        value_node.repeating = ar.odm_vo.repeating

        return value_node

    def _has_data_changed(self, ar: OdmFormAR, value: OdmFormValue) -> bool:
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

        are_rels_changed = (
            set(ar.odm_vo.translated_texts) != translated_text_nodes
            or set(ar.odm_vo.aliases) != alias_nodes
        )

        return (
            are_odm_properties_changed
            or are_rels_changed
            or ar.odm_vo.oid != value.oid
            or ar.odm_vo.sdtm_version != value.sdtm_version
            or ar.odm_vo.repeating != value.repeating
        )

    def find_by_uid_with_study_event_relation(
        self, uid: str, study_event_uid: str, study_event_version: str
    ) -> OdmFormRefVO:
        rs, _ = db.cypher_query(
            """
            MATCH (:OdmStudyEventRoot {uid: $study_event_uid})-[:HAS_VERSION {version: $study_event_version}]->(:OdmStudyEventValue)
            -[ref:FORM_REF]->(value:OdmFormValue)

            MATCH (value)<-[hv_rel:HAS_VERSION]-(:OdmFormRoot {uid: $uid})
            WITH value, ref, hv_rel
            ORDER BY hv_rel.start_date DESC
            WITH value, ref, collect(hv_rel) AS hv_rels

            RETURN
                value.oid AS oid,
                value.name AS name,
                hv_rels[0].version AS version,
                ref.order_number AS order_number,
                ref.mandatory AS mandatory,
                ref.locked AS locked,
                ref.collection_exception_condition_oid AS collection_exception_condition_oid
            """,
            params={
                "uid": uid,
                "study_event_uid": study_event_uid,
                "study_event_version": study_event_version,
            },
        )

        return OdmFormRefVO.from_repository_values(
            uid=uid,
            oid=rs[0][0],
            name=rs[0][1],
            study_event_uid=study_event_uid,
            version=rs[0][2],
            order_number=rs[0][3],
            mandatory=rs[0][4],
            locked=rs[0][5],
            collection_exception_condition_oid=rs[0][6],
        )

    @ensure_transaction(db)
    def _connect_relationships_to_new_value_node(
        self, root: VersionRoot, _: VersionValue
    ) -> None:
        """
        - Upgrades all incoming FORM_REF relationships to the second latest version to point
        to the latest version of OdmFormValue, preserving relationship properties.
        """
        db.cypher_query(
            f"""
            MATCH (root:{self.root_class.__name__} {{uid: $root_uid}})-[ver_rel:HAS_VERSION]->(value:{self.value_class.__name__})

            WITH root, ver_rel, value
            ORDER BY ver_rel.start_date DESC, ver_rel.end_date DESC
            LIMIT 2
            WITH root, collect(value) AS values
            WITH root, values[0] as latest_value, values[1] as second_latest_value

            MATCH (:OdmStudyEventRoot)-[p_ver_rel:HAS_VERSION]->(parent_value:OdmStudyEventValue)-[ref_rel:FORM_REF]->(second_latest_value)
            WHERE p_ver_rel.end_date IS NULL AND p_ver_rel.status = "Draft"

            WITH latest_value, ref_rel, parent_value,
                ref_rel.order_number AS order_number,
                ref_rel.mandatory AS mandatory,
                ref_rel.locked AS locked,
                ref_rel.collection_exception_condition_oid AS collection_exception_condition_oid

            CREATE (parent_value)-[new_ref_rel:FORM_REF]->(latest_value)

            SET new_ref_rel.order_number = order_number,
                new_ref_rel.mandatory = mandatory,
                new_ref_rel.locked = locked,
                new_ref_rel.collection_exception_condition_oid = collection_exception_condition_oid

            DELETE ref_rel
            """,
            {"root_uid": root.uid},
        )
