import logging
from textwrap import dedent
from typing import Any

from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.odm import (
    OdmVendorNamespaceRoot,
    OdmVendorNamespaceValue,
)
from clinical_mdr_api.domain_repositories.odms.generic_repository import (
    OdmGenericRepository,
)
from clinical_mdr_api.domains.odms.vendor_namespace import (
    OdmVendorNamespaceAR,
    OdmVendorNamespaceVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.odms.vendor_namespace import OdmVendorNamespace
from common.utils import convert_to_datetime

log = logging.getLogger(__name__)


class VendorNamespaceRepository(OdmGenericRepository[OdmVendorNamespaceAR]):
    root_class = OdmVendorNamespaceRoot
    value_class = OdmVendorNamespaceValue
    return_model = OdmVendorNamespace

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> OdmVendorNamespaceAR:
        log.debug(
            "Creating OdmVendorNamespaceAR from repository values for uid=%s", root.uid
        )
        return OdmVendorNamespaceAR.from_repository_values(
            uid=root.uid,
            odm_vo=OdmVendorNamespaceVO.from_repository_values(
                name=value.name,
                prefix=value.prefix,
                url=value.url,
                vendor_element_uids=list(
                    {
                        _root.uid
                        for vendor_element_value in value.has_vendor_element.all()
                        if (_root := vendor_element_value.has_root.single()) is not None
                    }
                ),
                vendor_attribute_uids=list(
                    {
                        _root.uid
                        for vendor_attribute_value in value.has_vendor_attribute.all()
                        if (_root := vendor_attribute_value.has_root.single())
                        is not None
                    }
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
    ) -> OdmVendorNamespaceAR:
        major, minor = input_dict["version"].split(".")
        log.debug(
            "Creating OdmVendorNamespaceAR from Cypher result for uid=%s",
            input_dict["uid"],
        )
        odm_vendor_namespace_ar = OdmVendorNamespaceAR.from_repository_values(
            uid=input_dict["uid"],
            odm_vo=OdmVendorNamespaceVO.from_repository_values(
                name=input_dict["name"],
                prefix=input_dict["prefix"],
                url=input_dict["url"],
                vendor_element_uids=input_dict["vendor_element_uids"],
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

        return odm_vendor_namespace_ar

    def _get_specific_field_mapping(self) -> dict[str, str]:
        """Field mappings for vendor namespace specific fields."""
        return {
            "name": "odm_value.name AS name",
            "prefix": "odm_value.prefix AS prefix",
            "url": "odm_value.url AS url",
        }

    def _get_computed_field_expressions(self) -> dict[str, str]:
        """Computed fields requiring complex Cypher expressions."""
        # pylint: disable=line-too-long
        return {
            "vendor_elements": "[(odm_value)-[hve:HAS_VENDOR_ELEMENT]->(vev:OdmVendorElementValue)<-[:HAS_VERSION]-(ver:OdmVendorElementRoot) | {uid: ver.uid, name: vev.name, compatible_types: vev.compatible_types, value: hve.value}] AS vendor_elements",
            "vendor_attributes": "[(odm_value)-[hva:HAS_VENDOR_ATTRIBUTE]->(vav:OdmVendorAttributeValue)<-[:HAS_VERSION]-(var:OdmVendorAttributeRoot) | {uid: var.uid, name: vav.name, compatible_types: vav.compatible_types, value: hva.value}] AS vendor_attributes",
        }

    def specific_alias_clause(self, **kwargs) -> str:
        return dedent(
            "WITH *,"
            + ", ".join(self._get_specific_field_mapping().values())
            + ","
            + ", ".join(self._get_computed_field_expressions().values())
            + """
            WITH *,
            apoc.coll.toSet([vendor_element in vendor_elements | vendor_element.uid]) AS vendor_element_uids,
            apoc.coll.toSet([vendor_attribute in vendor_attributes | vendor_attribute.uid]) AS vendor_attribute_uids
            """
        )

    def _get_or_create_value(
        self,
        root: VersionRoot,
        ar: OdmVendorNamespaceAR,
        force_new_value_node: bool = False,
    ) -> VersionValue:
        current_latest = root.has_latest_value.single()
        old_vendor_elements_nodes = (
            current_latest.has_vendor_element.all() if current_latest else []
        )
        new_vendor_elements_nodes = [
            old_vendor_elements_node.has_root.single().has_latest_value.single()
            for old_vendor_elements_node in old_vendor_elements_nodes
        ]
        old_vendor_attributes_nodes = (
            current_latest.has_vendor_attribute.all() if current_latest else []
        )
        new_vendor_attributes_nodes = [
            old_vendor_attributes_node.has_root.single().has_latest_value.single()
            for old_vendor_attributes_node in old_vendor_attributes_nodes
        ]

        new_value = super()._get_or_create_value(root, ar, force_new_value_node)

        for old_vendor_elements_node, new_vendor_elements_node in zip(
            old_vendor_elements_nodes, new_vendor_elements_nodes
        ):
            new_value.has_vendor_element.connect(new_vendor_elements_node)

        for old_vendor_attributes_node, new_vendor_attributes_node in zip(
            old_vendor_attributes_nodes, new_vendor_attributes_nodes
        ):
            new_value.has_vendor_attribute.connect(new_vendor_attributes_node)

        if ar.should_disconnect_relationships:
            for old_vendor_elements_node in old_vendor_elements_nodes:
                current_latest.has_vendor_element.disconnect(old_vendor_elements_node)
            for old_vendor_attributes_node in old_vendor_attributes_nodes:
                current_latest.has_vendor_attribute.disconnect(
                    old_vendor_attributes_node
                )

        return new_value

    def _create_new_value_node(
        self, ar: OdmVendorNamespaceAR
    ) -> OdmVendorNamespaceValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.prefix = ar.odm_vo.prefix
        value_node.url = ar.odm_vo.url

        log.debug("Created new VendorNamespaceValue node for name=%s", ar.name)
        return value_node

    def _has_data_changed(
        self, ar: OdmVendorNamespaceAR, value: OdmVendorNamespaceValue
    ) -> bool:
        are_odm_properties_changed = super()._has_data_changed(ar=ar, value=value)

        return (
            are_odm_properties_changed
            or ar.odm_vo.prefix != value.prefix
            or ar.odm_vo.url != value.url
        )
