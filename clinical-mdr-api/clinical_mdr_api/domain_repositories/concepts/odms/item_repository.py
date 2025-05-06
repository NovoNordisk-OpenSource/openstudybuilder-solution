from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.concepts.odms.odm_generic_repository import (
    OdmGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.concepts import UnitDefinitionRoot
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCodelistRoot,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.odm import (
    OdmAliasRoot,
    OdmDescriptionRoot,
    OdmItemGroupRoot,
    OdmItemRoot,
    OdmItemValue,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domains.concepts.odms.item import (
    OdmItemAR,
    OdmItemRefVO,
    OdmItemTermVO,
    OdmItemUnitDefinitionVO,
    OdmItemVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.odms.odm_item import OdmItem
from common.exceptions import NotFoundException
from common.utils import convert_to_datetime, version_string_to_tuple


class ItemRepository(OdmGenericRepository[OdmItemAR]):
    root_class = OdmItemRoot
    value_class = OdmItemValue
    return_model = OdmItem

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> OdmItemAR:
        codelist = root.has_codelist.get_or_none()
        activity = root.has_activity.get_or_none()
        return OdmItemAR.from_repository_values(
            uid=root.uid,
            concept_vo=OdmItemVO.from_repository_values(
                oid=value.oid,
                name=value.name,
                prompt=value.prompt,
                datatype=value.datatype,
                length=value.length,
                significant_digits=value.significant_digits,
                sas_field_name=value.sas_field_name,
                sds_var_name=value.sds_var_name,
                origin=value.origin,
                comment=value.comment,
                description_uids=[
                    description.uid for description in root.has_description.all()
                ],
                alias_uids=[alias.uid for alias in root.has_alias.all()],
                unit_definition_uids=[
                    unit_definition.uid
                    for unit_definition in root.has_unit_definition.all()
                ],
                codelist_uid=codelist.uid if codelist else None,
                term_uids=[term.uid for term in root.has_codelist_term.all()],
                activity_uid=activity.uid if activity else None,
                vendor_element_uids=[
                    vendor_element.uid
                    for vendor_element in root.has_vendor_element.all()
                ],
                vendor_attribute_uids=[
                    vendor_attribute.uid
                    for vendor_attribute in root.has_vendor_attribute.all()
                ],
                vendor_element_attribute_uids=[
                    vendor_element_attribute.uid
                    for vendor_element_attribute in root.has_vendor_element_attribute.all()
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
        odm_item_ar = OdmItemAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=OdmItemVO.from_repository_values(
                oid=input_dict.get("oid"),
                name=input_dict.get("name"),
                prompt=input_dict.get("prompt"),
                datatype=input_dict.get("datatype"),
                length=input_dict.get("length"),
                significant_digits=input_dict.get("significant_digits"),
                sas_field_name=input_dict.get("sas_field_name"),
                sds_var_name=input_dict.get("sds_var_name"),
                origin=input_dict.get("origin"),
                comment=input_dict.get("comment"),
                description_uids=input_dict.get("description_uids"),
                alias_uids=input_dict.get("alias_uids"),
                unit_definition_uids=input_dict.get("unit_definition_uids"),
                codelist_uid=input_dict.get("codelist_uid"),
                term_uids=input_dict.get("term_uids"),
                activity_uid=input_dict.get("activity_uid"),
                vendor_element_uids=input_dict.get("vendor_element_uids"),
                vendor_attribute_uids=input_dict.get("vendor_attribute_uids"),
                vendor_element_attribute_uids=input_dict.get(
                    "vendor_element_attribute_uids"
                ),
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

        return odm_item_ar

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name, **kwargs
    ) -> str:
        return f"""
WITH *,
concept_value.oid as oid,
concept_value.prompt as prompt,
concept_value.datatype as datatype,
concept_value.length as length,
concept_value.significant_digits as significant_digits,
concept_value.sas_field_name as sas_field_name,
concept_value.sds_var_name as sds_var_name,
concept_value.origin as origin,
concept_value.comment as comment,

[(concept_value)<-[:{only_specific_status}]-(:OdmItemRoot)-[:HAS_DESCRIPTION]->(dr:OdmDescriptionRoot)-[:LATEST]->(dv:OdmDescriptionValue) |
{{uid: dr.uid, name: dv.name, language: dv.language, description: dv.description, instruction: dv.instruction}}] AS descriptions,

[(concept_value)<-[:{only_specific_status}]-(:OdmItemRoot)-[:HAS_ALIAS]->(ar:OdmAliasRoot)-[:LATEST]->(av:OdmAliasValue) |
{{uid: ar.uid, name: av.name, context: av.context}}] AS aliases,

[(concept_value)<-[:{only_specific_status}]-(:OdmItemRoot)-[hud:HAS_UNIT_DEFINITION]->(udr:UnitDefinitionRoot)-[:LATEST]->(udv:UnitDefinitionValue) |
{{uid: udr.uid, name: udv.name, mandatory: hud.mandatory, order: hud.order}}] AS unit_definitions,

head([(concept_value)<-[:{only_specific_status}]-(:OdmItemRoot)-[:HAS_CODELIST]->(ctcr:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->
(:CTCodelistAttributesRoot)-[:LATEST]->(ctcav:CTCodelistAttributesValue) | ctcr.uid]) AS codelist_uid,

[(concept_value)<-[:{only_specific_status}]-(:OdmItemRoot)-[hct:HAS_CODELIST_TERM]->(cttr:CTTermRoot)-[:HAS_NAME_ROOT]->(cttnr:CTTermNameRoot)-[:LATEST]->(cttnv:CTTermNameValue) |
{{uid: cttr.uid, name: cttnv.name, mandatory: hct.mandatory, order: hct.order}}] AS terms,

head([(concept_value)<-[:{only_specific_status}]-(:OdmItemRoot)-[:HAS_ACTIVITY]->(ar:ActivityRoot)-[:LATEST]->(av:ActivityValue) |
{{uid: ar.uid, name: av.name}}]) AS activity,

[(concept_value)<-[:{only_specific_status}]-(:OdmItemRoot)-[hve:HAS_VENDOR_ELEMENT]->(ver:OdmVendorElementRoot)-[:LATEST]->(vev:OdmVendorElementValue) |
{{uid: ver.uid, name: vev.name, value: hve.value}}] AS vendor_elements,

[(concept_value)<-[:{only_specific_status}]-(:OdmItemRoot)-[hva:HAS_VENDOR_ATTRIBUTE]->(var:OdmVendorAttributeRoot)-[:LATEST]->(vav:OdmVendorAttributeValue) |
{{uid: var.uid, name: vav.name, value: hva.value}}] AS vendor_attributes,

[(concept_value)<-[:{only_specific_status}]-(:OdmItemRoot)-[hvea:HAS_VENDOR_ELEMENT_ATTRIBUTE]->(var:OdmVendorAttributeRoot)-[:LATEST]->(vav:OdmVendorAttributeValue) |
{{uid: var.uid, name: vav.name, value: hvea.value}}] AS vendor_element_attributes

WITH *,
activity.uid AS activity_uid,
apoc.coll.toSet([description in descriptions | description.uid]) AS description_uids,
apoc.coll.toSet([alias in aliases | alias.uid]) AS alias_uids,
apoc.coll.toSet([unit_definition in unit_definitions | unit_definition.uid]) AS unit_definition_uids,
apoc.coll.toSet([term in terms | term.uid]) AS term_uids,
apoc.coll.toSet([vendor_element in vendor_elements | vendor_element.uid]) AS vendor_element_uids,
apoc.coll.toSet([vendor_attribute in vendor_attributes | vendor_attribute.uid]) AS vendor_attribute_uids,
apoc.coll.toSet([vendor_element_attribute in vendor_element_attributes | vendor_element_attribute.uid]) AS vendor_element_attribute_uids
"""

    def _get_or_create_value(
        self, root: VersionRoot, ar: ConceptARBase
    ) -> VersionValue:
        new_value = super()._get_or_create_value(root, ar)

        root.has_description.disconnect_all()
        root.has_alias.disconnect_all()
        root.has_codelist.disconnect_all()

        if ar.concept_vo.description_uids is not None:
            for description_uid in ar.concept_vo.description_uids:
                description = OdmDescriptionRoot.nodes.get_or_none(uid=description_uid)
                root.has_description.connect(description)

        if ar.concept_vo.alias_uids is not None:
            for alias_uid in ar.concept_vo.alias_uids:
                alias = OdmAliasRoot.nodes.get_or_none(uid=alias_uid)
                root.has_alias.connect(alias)

        if ar.concept_vo.codelist_uid is not None:
            codelist = CTCodelistRoot.nodes.get_or_none(uid=ar.concept_vo.codelist_uid)
            root.has_codelist.connect(codelist)

        return new_value

    def _create_new_value_node(self, ar: OdmItemAR) -> OdmItemValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.oid = ar.concept_vo.oid
        value_node.prompt = ar.concept_vo.prompt
        value_node.datatype = ar.concept_vo.datatype
        value_node.length = ar.concept_vo.length
        value_node.significant_digits = ar.concept_vo.significant_digits
        value_node.sas_field_name = ar.concept_vo.sas_field_name
        value_node.sds_var_name = ar.concept_vo.sds_var_name
        value_node.origin = ar.concept_vo.origin
        value_node.comment = ar.concept_vo.comment

        return value_node

    def _has_data_changed(self, ar: OdmItemAR, value: OdmItemValue) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        root = OdmItemRoot.nodes.get_or_none(uid=ar.uid)

        description_uids = {
            description.uid for description in root.has_description.all()
        }
        alias_uids = {alias.uid for alias in root.has_alias.all()}
        unit_definition_uids = {
            unit_definition.uid for unit_definition in root.has_unit_definition.all()
        }
        codelist_uid = (
            codelist.uid if (codelist := root.has_codelist.get_or_none()) else None
        )
        term_uids = {term.uid for term in root.has_codelist_term.all()}

        are_rels_changed = (
            set(ar.concept_vo.description_uids) != description_uids
            or set(ar.concept_vo.alias_uids) != alias_uids
            or set(ar.concept_vo.unit_definition_uids) != unit_definition_uids
            or ar.concept_vo.codelist_uid != codelist_uid
            or set(ar.concept_vo.term_uids) != term_uids
        )

        return (
            are_concept_properties_changed
            or are_rels_changed
            or ar.concept_vo.oid != value.oid
            or ar.concept_vo.prompt != value.prompt
            or ar.concept_vo.datatype != value.datatype
            or ar.concept_vo.length != value.length
            or ar.concept_vo.significant_digits != value.significant_digits
            or ar.concept_vo.sas_field_name != value.sas_field_name
            or ar.concept_vo.sds_var_name != value.sds_var_name
            or ar.concept_vo.origin != value.origin
            or ar.concept_vo.comment != value.comment
        )

    def find_by_uid_with_item_group_relation(self, uid: str, item_group_uid: str):
        item_root = self.root_class.nodes.get_or_none(uid=uid)
        item_value = item_root.has_latest_value.get_or_none()

        item_group_root = OdmItemGroupRoot.nodes.get_or_none(uid=item_group_uid)

        rel = item_root.item_ref.relationship(item_group_root)

        return OdmItemRefVO.from_repository_values(
            uid=uid,
            oid=item_value.oid,
            name=item_value.name,
            item_group_uid=item_group_uid,
            order_number=rel.order_number,
            mandatory=rel.mandatory,
            key_sequence=rel.key_sequence,
            method_oid=rel.method_oid,
            imputation_method_oid=rel.imputation_method_oid,
            role=rel.role,
            role_codelist_oid=rel.role_codelist_oid,
            collection_exception_condition_oid=rel.collection_exception_condition_oid,
            vendor=rel.vendor,
        )

    def _get_latest_version_for_status(
        self, root: VersionRoot, value: VersionValue, status: LibraryItemStatus
    ) -> VersionRelationship:
        all_rels = root.has_version.all_relationships(value)
        rels = [rel for rel in all_rels if rel.status == status.value]
        if len(rels) == 0:
            raise RuntimeError(f"No HAS_VERSION was found with status {status}")
        latest = max(rels, key=lambda r: version_string_to_tuple(r.version))
        return latest

    def find_term_with_item_relation_by_item_uid(self, uid: str, term_uid: str):
        def _get_relationship():
            if ct_term_attributes_value_draft:
                rel_data = self._get_latest_version_for_status(
                    ct_term_attributes_root,
                    ct_term_attributes_value,
                    LibraryItemStatus.DRAFT,
                )
                if rel_data and not rel_data.end_date:
                    return rel_data

            if ct_term_attributes_value_final:
                rel_data = self._get_latest_version_for_status(
                    ct_term_attributes_root,
                    ct_term_attributes_value,
                    LibraryItemStatus.FINAL,
                )
                if not rel_data.end_date:
                    return rel_data

            raise NotFoundException(
                msg=f"No DRAFT or FINAL found for CT Term with UID '{ct_term_root.uid}'."
            )

        item_root = self.root_class.nodes.get_or_none(uid=uid)

        ct_term_root = CTTermRoot.nodes.get_or_none(uid=term_uid)
        ct_term_name_root = ct_term_root.has_name_root.get_or_none()
        ct_term_name_value = ct_term_name_root.has_latest_value.get_or_none()
        ct_term_attributes_root = ct_term_root.has_attributes_root.get_or_none()
        ct_term_attributes_value = (
            ct_term_attributes_root.has_latest_value.get_or_none()
        )
        ct_term_attributes_value_draft = (
            ct_term_attributes_root.latest_draft.get_or_none()
        )
        ct_term_attributes_value_final = (
            ct_term_attributes_root.latest_final.get_or_none()
        )

        rel = item_root.has_codelist_term.relationship(ct_term_root)

        if rel:
            return OdmItemTermVO.from_repository_values(
                uid=uid,
                name=ct_term_name_value.name,
                mandatory=rel.mandatory,
                order=rel.order,
                display_text=rel.display_text,
                version=_get_relationship().version,
            )
        return None

    def find_unit_definition_with_item_relation_by_item_uid(
        self, uid: str, unit_definition_uid: str
    ):
        item_root = self.root_class.nodes.get_or_none(uid=uid)

        unit_definition_root = UnitDefinitionRoot.nodes.get_or_none(
            uid=unit_definition_uid
        )
        unit_definition_value = unit_definition_root.has_latest_value.get_or_none()

        rel = item_root.has_unit_definition.relationship(unit_definition_root)

        if rel:
            return OdmItemUnitDefinitionVO.from_repository_values(
                uid=uid,
                name=unit_definition_value.name,
                mandatory=rel.mandatory,
                order=rel.order,
            )
        return None
