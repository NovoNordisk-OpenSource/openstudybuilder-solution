from neomodel import db

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
    OdmAliasRoot,
    OdmConditionRoot,
    OdmConditionValue,
    OdmDescriptionRoot,
    OdmFormalExpressionRoot,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domains.concepts.odms.condition import (
    OdmConditionAR,
    OdmConditionVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.odms.odm_condition import OdmCondition
from common.utils import convert_to_datetime


class ConditionRepository(OdmGenericRepository[OdmConditionAR]):
    root_class = OdmConditionRoot
    value_class = OdmConditionValue
    return_model = OdmCondition

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> OdmConditionAR:
        return OdmConditionAR.from_repository_values(
            uid=root.uid,
            concept_vo=OdmConditionVO.from_repository_values(
                oid=value.oid,
                name=value.name,
                formal_expression_uids=[
                    formal_expression.uid
                    for formal_expression in root.has_formal_expression.all()
                ],
                description_uids=[
                    description.uid for description in root.has_description.all()
                ],
                alias_uids=[alias.uid for alias in root.has_alias.all()],
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
        odm_condition_ar = OdmConditionAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=OdmConditionVO.from_repository_values(
                oid=input_dict.get("oid"),
                name=input_dict.get("name"),
                formal_expression_uids=input_dict.get("formal_expression_uids"),
                description_uids=input_dict.get("description_uids"),
                alias_uids=input_dict.get("alias_uids"),
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

        return odm_condition_ar

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name, **kwargs
    ) -> str:
        return f"""
WITH *,
concept_value.oid AS oid,

[(concept_value)<-[:{only_specific_status}]-(:OdmConditionRoot)-[:HAS_FORMAL_EXPRESSION]->(fer:OdmFormalExpressionRoot)-[:LATEST]->(fev:OdmFormalExpressionValue) |
{{uid: fer.uid, context: fev.context, expression: fev.expression}}] AS formal_expressions,

[(concept_value)<-[:{only_specific_status}]-(:OdmConditionRoot)-[:HAS_DESCRIPTION]->(dr:OdmDescriptionRoot)-[:LATEST]->(dv:OdmDescriptionValue) |
{{uid: dr.uid, name: dv.name, language: dv.language, description: dv.description, instruction: dv.instruction}}] AS descriptions,

[(concept_value)<-[:{only_specific_status}]-(:OdmConditionRoot)-[:HAS_ALIAS]->(ar:OdmAliasRoot)-[:LATEST]->(av:OdmAliasValue) |
{{uid: ar.uid, name: av.name, context: av.context}}] AS aliases

WITH *,
apoc.coll.toSet([formal_expression in formal_expressions | formal_expression.uid]) AS formal_expression_uids,
apoc.coll.toSet([description in descriptions | description.uid]) AS description_uids,
apoc.coll.toSet([alias in aliases | alias.uid]) AS alias_uids
"""

    def _get_or_create_value(
        self, root: VersionRoot, ar: ConceptARBase
    ) -> VersionValue:
        new_value = super()._get_or_create_value(root, ar)

        root.has_formal_expression.disconnect_all()
        root.has_description.disconnect_all()
        root.has_alias.disconnect_all()

        if ar.concept_vo.formal_expression_uids is not None:
            for formal_expression_uid in ar.concept_vo.formal_expression_uids:
                formal_expression = OdmFormalExpressionRoot.nodes.get_or_none(
                    uid=formal_expression_uid
                )
                root.has_formal_expression.connect(formal_expression)

        if ar.concept_vo.description_uids is not None:
            for description_uid in ar.concept_vo.description_uids:
                description = OdmDescriptionRoot.nodes.get_or_none(uid=description_uid)
                root.has_description.connect(description)

        if ar.concept_vo.alias_uids is not None:
            for alias_uid in ar.concept_vo.alias_uids:
                alias = OdmAliasRoot.nodes.get_or_none(uid=alias_uid)
                root.has_alias.connect(alias)

        return new_value

    def _create_new_value_node(self, ar: OdmConditionAR) -> OdmConditionValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.oid = ar.concept_vo.oid

        return value_node

    def _has_data_changed(self, ar: OdmConditionAR, value: OdmConditionValue) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        root = OdmConditionRoot.nodes.get_or_none(uid=ar.uid)

        formal_expression_uids = {
            formal_expression.uid
            for formal_expression in root.has_formal_expression.all()
        }
        description_uids = {
            description.uid for description in root.has_description.all()
        }
        alias_uids = {alias.uid for alias in root.has_alias.all()}

        are_rels_changed = (
            set(ar.concept_vo.formal_expression_uids) != formal_expression_uids
            or set(ar.concept_vo.description_uids) != description_uids
            or set(ar.concept_vo.alias_uids) != alias_uids
        )

        return (
            are_concept_properties_changed
            or are_rels_changed
            or ar.concept_vo.oid != value.oid
        )

    def set_all_collection_exception_condition_oid_properties_to_null(self, oid):
        db.cypher_query(
            """MATCH ()-[r:ITEM_GROUP_REF|ITEM_REF {collection_exception_condition_oid: $oid}]-()
                SET r.collection_exception_condition_oid = null""",
            {"oid": oid},
        )
