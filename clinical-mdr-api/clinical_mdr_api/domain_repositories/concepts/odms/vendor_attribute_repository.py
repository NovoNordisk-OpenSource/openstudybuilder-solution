import json

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
    OdmFormRoot,
    OdmItemGroupRoot,
    OdmItemRoot,
    OdmVendorAttributeRoot,
    OdmVendorAttributeValue,
    OdmVendorElementRoot,
    OdmVendorNamespaceRoot,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domains.concepts.odms.vendor_attribute import (
    OdmVendorAttributeAR,
    OdmVendorAttributeRelationVO,
    OdmVendorAttributeVO,
    OdmVendorElementAttributeRelationVO,
)
from clinical_mdr_api.domains.concepts.utils import RelationType
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.odms.odm_vendor_attribute import (
    OdmVendorAttribute,
)
from common.exceptions import BusinessLogicException
from common.utils import convert_to_datetime


class VendorAttributeRepository(OdmGenericRepository[OdmVendorAttributeAR]):
    root_class = OdmVendorAttributeRoot
    value_class = OdmVendorAttributeValue
    return_model = OdmVendorAttribute

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> OdmVendorAttributeAR:
        vendor_namespace = root.belongs_to_vendor_namespace.get_or_none()
        vendor_element = root.belongs_to_vendor_element.get_or_none()
        return OdmVendorAttributeAR.from_repository_values(
            uid=root.uid,
            concept_vo=OdmVendorAttributeVO.from_repository_values(
                name=value.name,
                compatible_types=(
                    value.compatible_types if value.compatible_types else []
                ),
                data_type=value.data_type,
                value_regex=value.value_regex,
                vendor_namespace_uid=vendor_namespace.uid if vendor_namespace else None,
                vendor_element_uid=vendor_element.uid if vendor_element else None,
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
        odm_form_ar = OdmVendorAttributeAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=OdmVendorAttributeVO.from_repository_values(
                name=input_dict.get("name"),
                compatible_types=json.loads(input_dict.get("compatible_types") or "[]"),
                data_type=input_dict.get("data_type"),
                value_regex=input_dict.get("value_regex"),
                vendor_namespace_uid=input_dict.get("vendor_namespace_uid"),
                vendor_element_uid=input_dict.get("vendor_element_uid"),
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

        return odm_form_ar

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name, **kwargs
    ) -> str:
        return f"""
WITH *,
concept_value.compatible_types AS compatible_types,
concept_value.data_type AS data_type,
concept_value.value_regex AS value_regex,

head([(concept_value)<-[:{only_specific_status}]-(:OdmVendorAttributeRoot)<-[:HAS_VENDOR_ATTRIBUTE]-(vnr:OdmVendorNamespaceRoot)-[:LATEST]->(vnv:OdmVendorNamespaceValue) |
{{uid: vnr.uid, name: vnv.name, prefix: vnv.prefix, url: vnv.url}}]) AS vendor_namespace,

head([(concept_value)<-[:{only_specific_status}]-(:OdmVendorAttributeRoot)<-[:HAS_VENDOR_ATTRIBUTE]-(xtr:OdmVendorElementRoot)-[:LATEST]->(xtv:OdmVendorElementValue) |
{{uid: xtr.uid, name: xtv.name}}]) AS vendor_element


WITH *,
vendor_namespace.uid AS vendor_namespace_uid,
vendor_element.uid AS vendor_element_uid
"""

    def _get_or_create_value(
        self, root: VersionRoot, ar: ConceptARBase
    ) -> VersionValue:
        new_value = super()._get_or_create_value(root, ar)

        root.belongs_to_vendor_namespace.disconnect_all()
        root.belongs_to_vendor_element.disconnect_all()

        if ar.concept_vo.vendor_namespace_uid is not None:
            vendor_namespace = OdmVendorNamespaceRoot.nodes.get_or_none(
                uid=ar.concept_vo.vendor_namespace_uid
            )
            root.belongs_to_vendor_namespace.connect(vendor_namespace)

        if ar.concept_vo.vendor_element_uid is not None:
            vendor_element = OdmVendorElementRoot.nodes.get_or_none(
                uid=ar.concept_vo.vendor_element_uid
            )
            root.belongs_to_vendor_element.connect(vendor_element)

        return new_value

    def _create_new_value_node(
        self, ar: OdmVendorAttributeAR
    ) -> OdmVendorAttributeValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.compatible_types = ar.concept_vo.compatible_types
        value_node.data_type = ar.concept_vo.data_type
        value_node.value_regex = ar.concept_vo.value_regex

        return value_node

    def _has_data_changed(
        self, ar: OdmVendorAttributeAR, value: OdmVendorAttributeValue
    ) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        root = OdmVendorAttributeRoot.nodes.get_or_none(uid=ar.uid)

        vendor_namespace_uid = (
            vendor_namespace.uid
            if (vendor_namespace := root.belongs_to_vendor_namespace.get_or_none())
            else None
        )
        vendor_element_uid = (
            vendor_element.uid
            if (vendor_element := root.belongs_to_vendor_element.get_or_none())
            else None
        )

        are_rels_changed = (
            ar.concept_vo.vendor_namespace_uid != vendor_namespace_uid
            or ar.concept_vo.vendor_element_uid != vendor_element_uid
        )

        return (
            are_concept_properties_changed
            or are_rels_changed
            or ar.concept_vo.compatible_types != value.compatible_types
            or ar.concept_vo.data_type != value.data_type
            or ar.concept_vo.value_regex != value.value_regex
        )

    def find_by_uid_with_odm_element_relation(
        self,
        uid: str,
        odm_element_uid: str,
        odm_element_type: RelationType,
        vendor_element_attribute: bool = True,
    ):
        vendor_attribute_root = self.root_class.nodes.get_or_none(uid=uid)
        vendor_attribute_value = vendor_attribute_root.has_latest_value.get_or_none()

        if odm_element_type == RelationType.FORM:
            odm_element_root = OdmFormRoot.nodes.get_or_none(uid=odm_element_uid)
            if vendor_element_attribute:
                rel = vendor_attribute_root.belongs_to_element_form.relationship(
                    odm_element_root
                )
            else:
                rel = vendor_attribute_root.belongs_to_form.relationship(
                    odm_element_root
                )
        elif odm_element_type == RelationType.ITEM_GROUP:
            odm_element_root = OdmItemGroupRoot.nodes.get_or_none(uid=odm_element_uid)
            if vendor_element_attribute:
                rel = vendor_attribute_root.belongs_to_element_item_group.relationship(
                    odm_element_root
                )
            else:
                rel = vendor_attribute_root.belongs_to_item_group.relationship(
                    odm_element_root
                )
        elif odm_element_type == RelationType.ITEM:
            odm_element_root = OdmItemRoot.nodes.get_or_none(uid=odm_element_uid)
            if vendor_element_attribute:
                rel = vendor_attribute_root.belongs_to_element_item.relationship(
                    odm_element_root
                )
            else:
                rel = vendor_attribute_root.belongs_to_item.relationship(
                    odm_element_root
                )
        else:
            raise BusinessLogicException(msg="Invalid ODM element type.")

        if vendor_element_attribute:
            return OdmVendorElementAttributeRelationVO.from_repository_values(
                uid=uid,
                name=vendor_attribute_value.name,
                data_type=vendor_attribute_value.data_type,
                value_regex=vendor_attribute_value.value_regex,
                value=rel.value,
                vendor_element_uid=rel.end_node()
                .belongs_to_vendor_element.get_or_none()
                .uid,
            )

        return OdmVendorAttributeRelationVO.from_repository_values(
            uid=uid,
            name=vendor_attribute_value.name,
            compatible_types=vendor_attribute_value.compatible_types,
            data_type=vendor_attribute_value.data_type,
            value_regex=vendor_attribute_value.value_regex,
            value=rel.value,
            vendor_namespace_uid=rel.end_node()
            .belongs_to_vendor_namespace.get_or_none()
            .uid,
        )
