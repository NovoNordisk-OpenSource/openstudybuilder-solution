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
    OdmVendorAttributeRoot,
    OdmVendorAttributeValue,
    OdmVendorElementRoot,
    OdmVendorNamespaceRoot,
)
from clinical_mdr_api.domain_repositories.odms.generic_repository import (
    OdmGenericRepository,
)
from clinical_mdr_api.domains.odms.utils import RelationType
from clinical_mdr_api.domains.odms.vendor_attribute import (
    OdmVendorAttributeAR,
    OdmVendorAttributeRelationVO,
    OdmVendorAttributeVO,
    OdmVendorElementAttributeRelationVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.odms.vendor_attribute import OdmVendorAttribute
from clinical_mdr_api.services._utils import ensure_transaction
from common.exceptions import BusinessLogicException
from common.utils import convert_to_datetime

log = logging.getLogger(__name__)


class VendorAttributeRepository(OdmGenericRepository[OdmVendorAttributeAR]):
    root_class = OdmVendorAttributeRoot
    value_class = OdmVendorAttributeValue
    return_model = OdmVendorAttribute

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> OdmVendorAttributeAR:
        vendor_namespace_value = value.belongs_to_vendor_namespace.get_or_none()
        vendor_element_value = value.belongs_to_vendor_element.get_or_none()
        log.debug(
            "Creating OdmVendorAttributeAR from repository values for uid=%s", root.uid
        )
        return OdmVendorAttributeAR.from_repository_values(
            uid=root.uid,
            odm_vo=OdmVendorAttributeVO.from_repository_values(
                name=value.name,
                compatible_types=(
                    value.compatible_types if value.compatible_types else []
                ),
                data_type=value.data_type,
                value_regex=value.value_regex,
                vendor_namespace_uid=(
                    vendor_namespace_value.has_root.single().uid
                    if vendor_namespace_value
                    else None
                ),
                vendor_element_uid=(
                    vendor_element_value.has_root.single().uid
                    if vendor_element_value
                    else None
                ),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict[str, Any]
    ) -> OdmVendorAttributeAR:
        major, minor = input_dict["version"].split(".")
        log.debug(
            "Creating OdmVendorAttributeAR from Cypher result for uid=%s",
            input_dict["uid"],
        )
        odm_form_ar = OdmVendorAttributeAR.from_repository_values(
            uid=input_dict["uid"],
            odm_vo=OdmVendorAttributeVO.from_repository_values(
                name=input_dict["name"],
                compatible_types=json.loads(input_dict.get("compatible_types") or "[]"),
                data_type=input_dict.get("data_type"),
                value_regex=input_dict.get("value_regex"),
                vendor_namespace_uid=input_dict.get("vendor_namespace_uid"),
                vendor_element_uid=input_dict.get("vendor_element_uid"),
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
        """Field mappings for vendor attribute specific fields."""
        return {
            "name": "odm_value.name AS name",
            "compatible_types": "odm_value.compatible_types AS compatible_types",
            "data_type": "odm_value.data_type AS data_type",
            "value_regex": "odm_value.value_regex AS value_regex",
        }

    def _get_computed_field_expressions(self) -> dict[str, str]:
        """Computed fields requiring complex Cypher expressions."""
        # pylint: disable=line-too-long
        return {
            "vendor_namespace": "head([(odm_value)<-[:HAS_VENDOR_ATTRIBUTE]-(vnv:OdmVendorNamespaceValue)<-[:HAS_VERSION]-(vnr:OdmVendorNamespaceRoot) | {uid: vnr.uid, name: vnv.name, prefix: vnv.prefix, url: vnv.url}]) AS vendor_namespace",
            "vendor_element": "head([(odm_value)<-[:HAS_VENDOR_ATTRIBUTE]-(xtv:OdmVendorElementValue)<-[:HAS_VERSION]-(xtr:OdmVendorElementRoot) | {uid: xtr.uid, name: xtv.name, compatible_types: xtv.compatible_types}]) AS vendor_element",
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
            vendor_element.uid AS vendor_element_uid
            """
        )

    def _get_or_create_value(
        self,
        root: VersionRoot,
        ar: OdmVendorAttributeAR,
        force_new_value_node: bool = False,
    ) -> VersionValue:
        new_value = super()._get_or_create_value(root, ar, force_new_value_node)

        new_value.belongs_to_vendor_namespace.disconnect_all()
        new_value.belongs_to_vendor_element.disconnect_all()

        if ar.odm_vo.vendor_namespace_uid is not None:
            vendor_namespace_root = OdmVendorNamespaceRoot.nodes.get_or_none(
                uid=ar.odm_vo.vendor_namespace_uid
            )
            vendor_namespace_value = (
                vendor_namespace_root.has_latest_value.get_or_none()
                if vendor_namespace_root
                else None
            )
            if vendor_namespace_value:
                new_value.belongs_to_vendor_namespace.connect(vendor_namespace_value)

        if ar.odm_vo.vendor_element_uid is not None:
            vendor_element_root = OdmVendorElementRoot.nodes.get_or_none(
                uid=ar.odm_vo.vendor_element_uid
            )
            vendor_element_value = (
                vendor_element_root.has_latest_value.get_or_none()
                if vendor_element_root
                else None
            )
            if vendor_element_value:
                new_value.belongs_to_vendor_element.connect(vendor_element_value)

        return new_value

    def _create_new_value_node(
        self, ar: OdmVendorAttributeAR
    ) -> OdmVendorAttributeValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.compatible_types = ar.odm_vo.compatible_types
        value_node.data_type = ar.odm_vo.data_type
        value_node.value_regex = ar.odm_vo.value_regex

        log.debug("Created new VendorAttributeValue node for name=%s", ar.name)
        return value_node

    def _has_data_changed(
        self, ar: OdmVendorAttributeAR, value: OdmVendorAttributeValue
    ) -> bool:
        are_odm_properties_changed = super()._has_data_changed(ar=ar, value=value)

        vendor_namespace_uid = (
            vendor_namespace_value.has_root.single().uid
            if (
                vendor_namespace_value := value.belongs_to_vendor_namespace.get_or_none()
            )
            else None
        )
        vendor_element_uid = (
            vendor_element_value.has_root.single().uid
            if (vendor_element_value := value.belongs_to_vendor_element.get_or_none())
            else None
        )

        are_rels_changed = (
            ar.odm_vo.vendor_namespace_uid != vendor_namespace_uid
            or ar.odm_vo.vendor_element_uid != vendor_element_uid
        )

        return (
            are_odm_properties_changed
            or are_rels_changed
            or ar.odm_vo.compatible_types != value.compatible_types
            or ar.odm_vo.data_type != value.data_type
            or ar.odm_vo.value_regex != value.value_regex
        )

    def find_by_uid_with_odm_element_relation(
        self,
        uid: str,
        odm_element_uid: str,
        odm_element_version: str,
        odm_element_type: RelationType,
        vendor_element_attribute: bool = True,
    ):
        log.info(
            "Finding VendorAttribute with uid=%s for ODM element uid=%s, version=%s",
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

        if vendor_element_attribute:
            rs, _ = db.cypher_query(
                f"""
                MATCH (:{odm_element_root} {{uid: $odm_element_uid}})-[:HAS_VERSION {{version: $odm_element_version}}]->(:{odm_element_value})
                -[ref:HAS_VENDOR_ELEMENT_ATTRIBUTE]->(value:OdmVendorAttributeValue)<-[:HAS_VERSION]-(:OdmVendorAttributeRoot {{uid: $uid}})
                MATCH (value)<-[:HAS_VENDOR_ATTRIBUTE]-(:OdmVendorElementValue)<-[:HAS_VERSION]-(vendor_element_root:OdmVendorElementRoot)
                RETURN
                    value.name AS name,
                    value.data_type AS data_type,
                    value.value_regex AS value_regex,
                    ref.value AS value,
                    vendor_element_root.uid AS vendor_element_uid
                """,
                params={
                    "uid": uid,
                    "odm_element_uid": odm_element_uid,
                    "odm_element_version": odm_element_version,
                },
            )
            return OdmVendorElementAttributeRelationVO.from_repository_values(
                uid=uid,
                name=rs[0][0],
                data_type=rs[0][1],
                value_regex=rs[0][2],
                value=rs[0][3],
                vendor_element_uid=rs[0][4],
            )

        rs, _ = db.cypher_query(
            f"""
                MATCH (:{odm_element_root} {{uid: $odm_element_uid}})-[:HAS_VERSION {{version: $odm_element_version}}]->(:{odm_element_value})
                -[ref:HAS_VENDOR_ATTRIBUTE]->(value:OdmVendorAttributeValue)<-[:HAS_VERSION]-(:OdmVendorAttributeRoot {{uid: $uid}})
                MATCH (value)<-[:HAS_VENDOR_ATTRIBUTE]-(:OdmVendorNamespaceValue)<-[:HAS_VERSION]-(vendor_namespace_root:OdmVendorNamespaceRoot)
                RETURN
                    value.name AS name,
                    value.compatible_types AS compatible_types,
                    value.data_type AS data_type,
                    value.value_regex AS value_regex,
                    ref.value AS value,
                    vendor_namespace_root.uid AS vendor_namespace_uid
                """,
            params={
                "uid": uid,
                "odm_element_uid": odm_element_uid,
                "odm_element_version": odm_element_version,
            },
        )

        return OdmVendorAttributeRelationVO.from_repository_values(
            uid=uid,
            name=rs[0][0],
            compatible_types=json.loads(rs[0][1]),
            data_type=rs[0][2],
            value_regex=rs[0][3],
            value=rs[0][4],
            vendor_namespace_uid=rs[0][5],
        )

    @ensure_transaction(db)
    def _connect_relationships_to_new_value_node(
        self, root: VersionRoot, _: VersionValue
    ) -> None:
        """
        - Upgrades all incoming HAS_VENDOR_ELEMENT_ATTRIBUTE relationships to the second latest version to point
        to the latest version of OdmVendorAttributeValue, preserving relationship properties.
        - Upgrades all incoming HAS_VENDOR_ATTRIBUTE relationships to the second latest version to point
        to the latest version of OdmVendorAttributeValue, preserving relationship properties.
        """
        log.info(
            "Upgrading vendor element attribute relationships for root uid=%s", root.uid
        )
        query = f"""
        MATCH (root:{self.root_class.__name__} {{uid: $root_uid}})-[ver_rel:HAS_VERSION]->(value:{self.value_class.__name__})

        WITH root, ver_rel, value
        ORDER BY ver_rel.start_date DESC, ver_rel.end_date DESC
        LIMIT 2
        WITH root, collect(value) AS values
        WITH root, values[0] as latest_value, values[1] as second_latest_value

        MATCH (:OdmFormRoot|OdmItemGroupRoot|OdmItemRoot)-[p_ver_rel:HAS_VERSION]->
        (parent_value:OdmFormValue|OdmItemGroupValue|OdmItemValue)-[has_vendor_element_attribute:HAS_VENDOR_ELEMENT_ATTRIBUTE]->(second_latest_value)
        WHERE p_ver_rel.end_date IS NULL AND p_ver_rel.status = "Draft"

        WITH latest_value, has_vendor_element_attribute, parent_value,
            has_vendor_element_attribute.value AS value

        CREATE (parent_value)-[new_has_vendor_element_attribute:HAS_VENDOR_ELEMENT_ATTRIBUTE]->(latest_value)

        SET new_has_vendor_element_attribute.value = value

        DELETE has_vendor_element_attribute
        """
        db.cypher_query(query, {"root_uid": root.uid})

        log.info("Upgrading vendor attribute relationships for root uid=%s", root.uid)
        query = f"""
        MATCH (root:{self.root_class.__name__} {{uid: $root_uid}})-[ver_rel:HAS_VERSION]->(value:{self.value_class.__name__})

        WITH root, ver_rel, value
        ORDER BY ver_rel.start_date DESC, ver_rel.end_date DESC
        LIMIT 2
        WITH root, collect(value) AS values
        WITH root, values[0] as latest_value, values[1] as second_latest_value

        MATCH (:OdmFormRoot|OdmItemGroupRoot|OdmItemRoot)-[p_ver_rel:HAS_VERSION]->
        (parent_value:OdmFormValue|OdmItemGroupValue|OdmItemValue)-[has_vendor_attribute:HAS_VENDOR_ATTRIBUTE]->(second_latest_value)
        WHERE p_ver_rel.end_date IS NULL AND p_ver_rel.status = "Draft"

        WITH latest_value, has_vendor_attribute, parent_value,
            has_vendor_attribute.value AS value

        CREATE (parent_value)-[new_has_vendor_attribute:HAS_VENDOR_ATTRIBUTE]->(latest_value)

        SET new_has_vendor_attribute.value = value

        DELETE has_vendor_attribute
        """
        db.cypher_query(query, {"root_uid": root.uid})
