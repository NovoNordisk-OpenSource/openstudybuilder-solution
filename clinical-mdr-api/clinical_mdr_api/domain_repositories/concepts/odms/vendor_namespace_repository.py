from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.concepts.odms.odm_generic_repository import (
    OdmGenericRepository,
)
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
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.odms.vendor_namespace import (
    OdmVendorNamespaceAR,
    OdmVendorNamespaceVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.odms.odm_vendor_namespace import (
    OdmVendorNamespace,
)
from common.utils import convert_to_datetime


class VendorNamespaceRepository(OdmGenericRepository[OdmVendorNamespaceAR]):
    root_class = OdmVendorNamespaceRoot
    value_class = OdmVendorNamespaceValue
    return_model = OdmVendorNamespace

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> OdmVendorNamespaceAR:
        return OdmVendorNamespaceAR.from_repository_values(
            uid=root.uid,
            concept_vo=OdmVendorNamespaceVO.from_repository_values(
                name=value.name,
                prefix=value.prefix,
                url=value.url,
                vendor_element_uids=[
                    vendor_element.uid
                    for vendor_element in root.has_vendor_element.all()
                ],
                vendor_attribute_uids=[
                    vendor_attribute.uid
                    for vendor_attribute in root.has_vendor_attribute.all()
                ],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> _AggregateRootType:
        major, minor = input_dict.get("version").split(".")
        odm_vendor_namespace_ar = OdmVendorNamespaceAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=OdmVendorNamespaceVO.from_repository_values(
                name=input_dict.get("name"),
                prefix=input_dict.get("prefix"),
                url=input_dict.get("url"),
                vendor_element_uids=input_dict.get("vendor_element_uids"),
                vendor_attribute_uids=input_dict.get("vendor_attribute_uids"),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict.get("library_name"),
                is_library_editable_callback=(
                    lambda _: input_dict.get("is_library_editable")
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict.get("change_description"),
                status=LibraryItemStatus(input_dict.get("status")),
                author_id=input_dict.get("author_id"),
                author_username=input_dict.get("author_username"),
                start_date=convert_to_datetime(value=input_dict.get("start_date")),
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

        return odm_vendor_namespace_ar

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name, **kwargs
    ) -> str:
        return f"""
WITH *,
concept_value.prefix AS prefix,
concept_value.url AS url,

[(concept_value)<-[:{only_specific_status}]-(:OdmVendorNamespaceRoot)-[hve:HAS_VENDOR_ELEMENT]->(ver:OdmVendorElementRoot)-[:LATEST]->(vev:OdmVendorElementValue) |
{{uid: ver.uid, name: vev.name, value: hve.value}}] AS vendor_elements,

[(concept_value)<-[:{only_specific_status}]-(:OdmVendorNamespaceRoot)-[hva:HAS_VENDOR_ATTRIBUTE]->(var:OdmVendorAttributeRoot)-[:LATEST]->(vav:OdmVendorAttributeValue) |
{{uid: var.uid, name: vav.name, value: hva.value}}] AS vendor_attributes

WITH *,
apoc.coll.toSet([vendor_element in vendor_elements | vendor_element.uid]) AS vendor_element_uids,
apoc.coll.toSet([vendor_attribute in vendor_attributes | vendor_attribute.uid]) AS vendor_attribute_uids
"""

    def _create_new_value_node(
        self, ar: OdmVendorNamespaceAR
    ) -> OdmVendorNamespaceValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.prefix = ar.concept_vo.prefix
        value_node.url = ar.concept_vo.url

        return value_node

    def _has_data_changed(
        self, ar: OdmVendorNamespaceAR, value: OdmVendorNamespaceValue
    ) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        return (
            are_concept_properties_changed
            or ar.concept_vo.prefix != value.prefix
            or ar.concept_vo.url != value.url
        )
