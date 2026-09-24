import json
import logging
from textwrap import dedent
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.odm import (
    OdmVendorElementRoot,
    OdmVendorElementValue,
    OdmVendorNamespaceRoot,
)
from clinical_mdr_api.domain_repositories.odms.generic_repository import (
    OdmGenericRepository,
)
from clinical_mdr_api.domains.odms.utils import RelationType
from clinical_mdr_api.domains.odms.vendor_element import (
    OdmVendorElementAR,
    OdmVendorElementRelationVO,
    OdmVendorElementVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.odms.vendor_element import OdmVendorElement
from clinical_mdr_api.services._utils import ensure_transaction
from common.exceptions import BusinessLogicException
from common.utils import convert_to_datetime

log = logging.getLogger(__name__)


class VendorElementRepository(OdmGenericRepository[OdmVendorElementAR]):
    root_class = OdmVendorElementRoot
    value_class = OdmVendorElementValue
    return_model = OdmVendorElement

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> OdmVendorElementAR:
        vendor_namespace_value = value.belongs_to_vendor_namespace.get_or_none()
        log.debug(
            "Creating OdmVendorElementAR from repository values for uid=%s", root.uid
        )
        return OdmVendorElementAR.from_repository_values(
            uid=root.uid,
            odm_vo=OdmVendorElementVO.from_repository_values(
                name=value.name,
                compatible_types=value.compatible_types,
                vendor_namespace_uid=vendor_namespace_value.has_root.single().uid,
                vendor_attribute_uids=[
                    _root.uid
                    for vendor_attribute_value in value.has_vendor_attribute.all()
                    if (_root := vendor_attribute_value.has_root.single()) is not None
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
    ) -> OdmVendorElementAR:
        major, minor = input_dict["version"].split(".")
        log.debug(
            "Creating OdmVendorElementAR from Cypher result for uid=%s",
            input_dict["uid"],
        )
        odm_vendor_element_ar = OdmVendorElementAR.from_repository_values(
            uid=input_dict["uid"],
            odm_vo=OdmVendorElementVO.from_repository_values(
                name=input_dict["name"],
                compatible_types=json.loads(input_dict.get("compatible_types") or "[]"),
                vendor_namespace_uid=input_dict["vendor_namespace_uid"],
                vendor_attribute_uids=input_dict["vendor_attribute_uids"],
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

        return odm_vendor_element_ar

    def _get_specific_field_mapping(self) -> dict[str, str]:
        """Field mappings for vendor element specific fields."""
        return {
            "name": "odm_value.name AS name",
            "compatible_types": "odm_value.compatible_types AS compatible_types",
        }

    def _get_computed_field_expressions(self) -> dict[str, str]:
        """Computed fields requiring complex Cypher expressions."""
        # pylint: disable=line-too-long
        return {
            "vendor_namespace": "head([(odm_value)<-[:HAS_VENDOR_ELEMENT]-(vnv:OdmVendorNamespaceValue)<-[:HAS_VERSION]-(vnr:OdmVendorNamespaceRoot) | {uid: vnr.uid, name: vnv.name, prefix: vnv.prefix, url: vnv.url}]) AS vendor_namespace",
            "vendor_attributes": "[(odm_value)-[:HAS_VENDOR_ATTRIBUTE]->(vav:OdmVendorAttributeValue)<-[:HAS_VERSION]-(var:OdmVendorAttributeRoot) | {uid: var.uid, name: vav.name, compatible_types: vav.compatible_types}] AS vendor_attributes",
        }

    def specific_alias_clause(self, **kwargs) -> str:
        return dedent(
            "WITH *,"
            + ", ".join(self._get_specific_field_mapping().values())
            + ","
            + ", ".join(self._get_computed_field_expressions().values())
            + """
            WITH *,
            vendor_namespace.uid AS vendor_namespace_uid,
            apoc.coll.toSet([vendor_attribute in vendor_attributes | vendor_attribute.uid]) AS vendor_attribute_uids
            """
        )

    def _get_or_create_value(
        self,
        root: VersionRoot,
        ar: OdmVendorElementAR,
        force_new_value_node: bool = False,
    ) -> VersionValue:
        current_latest = root.has_latest_value.single()
        old_has_vendor_attribute_nodes = (
            current_latest.has_vendor_attribute.all() if current_latest else []
        )
        new_has_vendor_attribute_nodes = [
            old_vendor_attribute_root.has_latest_value.single()
            for old_has_vendor_attribute_node in old_has_vendor_attribute_nodes
            if (
                old_vendor_attribute_root := old_has_vendor_attribute_node.has_root.single()
            )
        ]

        new_value = super()._get_or_create_value(root, ar, force_new_value_node)

        new_value.belongs_to_vendor_namespace.disconnect_all()

        if ar.odm_vo.vendor_namespace_uid is not None:
            vendor_namespace_root = OdmVendorNamespaceRoot.nodes.get_or_none(
                uid=ar.odm_vo.vendor_namespace_uid
            )
            vendor_namespace_value = (
                vendor_namespace_root.has_latest_value.get_or_none()
            )
            if vendor_namespace_value:
                new_value.belongs_to_vendor_namespace.connect(vendor_namespace_value)

        for new_has_vendor_attribute_node in new_has_vendor_attribute_nodes:
            new_value.has_vendor_attribute.connect(new_has_vendor_attribute_node)

        if ar.should_disconnect_relationships:
            for old_has_vendor_attribute_node in old_has_vendor_attribute_nodes:
                current_latest.has_vendor_attribute.disconnect(
                    old_has_vendor_attribute_node
                )

        return new_value

    def _create_new_value_node(self, ar: OdmVendorElementAR) -> OdmVendorElementValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.compatible_types = ar.odm_vo.compatible_types

        log.debug("Created new VendorElementValue node for name=%s", ar.name)
        return value_node

    def _has_data_changed(
        self, ar: OdmVendorElementAR, value: OdmVendorElementValue
    ) -> bool:
        are_odm_properties_changed = super()._has_data_changed(ar=ar, value=value)

        vendor_namespace_uid = (
            vendor_namespace_value.has_root.single().uid
            if (
                vendor_namespace_value := value.belongs_to_vendor_namespace.get_or_none()
            )
            else None
        )

        are_rels_changed = ar.odm_vo.vendor_namespace_uid != vendor_namespace_uid

        return (
            are_odm_properties_changed
            or are_rels_changed
            or ar.odm_vo.compatible_types != value.compatible_types
        )

    def find_by_uid_with_odm_element_relation(
        self,
        uid: str,
        odm_element_uid: str,
        odm_element_version: str,
        odm_element_type: RelationType,
    ):
        log.info(
            "Finding VendorElement with uid=%s for ODM element uid=%s, version=%s",
            uid,
            odm_element_uid,
            odm_element_version,
        )
        if odm_element_type == RelationType.FORM:
            odm_element_root = "OdmFormRoot"
            odm_element_value = "OdmFormValue"
        elif odm_element_type == RelationType.ITEM_GROUP:
            odm_element_root = "OdmItemGroupRoot"
            odm_element_value = "OdmItemGroupValue"
        elif odm_element_type == RelationType.ITEM:
            odm_element_root = "OdmItemRoot"
            odm_element_value = "OdmItemValue"
        else:
            raise BusinessLogicException(msg="Invalid ODM element type.")

        rs, _ = db.cypher_query(
            f"""
            MATCH (:{odm_element_root} {{uid: $odm_element_uid}})-[:HAS_VERSION {{version: $odm_element_version}}]->(:{odm_element_value})
            -[ref:HAS_VENDOR_ELEMENT]->(value:OdmVendorElementValue)<-[:HAS_VERSION]-(:OdmVendorElementRoot {{uid: $uid}})
            RETURN
                value.name AS name,
                value.compatible_types AS compatible_types,
                ref.value AS value
            """,
            params={
                "uid": uid,
                "odm_element_uid": odm_element_uid,
                "odm_element_version": odm_element_version,
            },
        )

        return OdmVendorElementRelationVO.from_repository_values(
            uid=uid,
            name=rs[0][0],
            compatible_types=rs[0][1],
            value=rs[0][2],
        )

    @ensure_transaction(db)
    def _connect_relationships_to_new_value_node(
        self, root: VersionRoot, _: VersionValue
    ) -> None:
        """
        Upgrades all incoming HAS_VENDOR_ELEMENT relationships to the second latest version to point
        to the latest version of OdmVendorElementValue, preserving relationship properties.
        """
        log.info("Upgrading vendor element relationships for root uid=%s", root.uid)
        query = f"""
        MATCH (root:{self.root_class.__name__} {{uid: $root_uid}})-[ver_rel:HAS_VERSION]->(value:{self.value_class.__name__})

        WITH root, ver_rel, value
        ORDER BY ver_rel.start_date DESC, ver_rel.end_date DESC
        LIMIT 2
        WITH root, collect(value) AS values
        WITH root, values[0] as latest_value, values[1] as second_latest_value

        MATCH (:OdmFormRoot|OdmItemGroupRoot|OdmItemRoot)-[p_ver_rel:HAS_VERSION]->
        (parent_value:OdmFormValue|OdmItemGroupValue|OdmItemValue)-[has_vendor_element:HAS_VENDOR_ELEMENT]->(second_latest_value)
        WHERE p_ver_rel.end_date IS NULL AND p_ver_rel.status = "Draft"

        WITH latest_value, has_vendor_element, parent_value,
            has_vendor_element.value AS value

        CREATE (parent_value)-[new_has_vendor_element:HAS_VENDOR_ELEMENT]->(latest_value)

        SET new_has_vendor_element.value = value

        DELETE has_vendor_element
        """
        db.cypher_query(query, {"root_uid": root.uid})
