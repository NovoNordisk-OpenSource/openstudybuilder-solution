from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.compounds import (
    CompoundAliasRoot,
    CompoundAliasValue,
    CompoundRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.compound_alias import (
    CompoundAliasAR,
    CompoundAliasVO,
)
from clinical_mdr_api.domains.concepts.concept_base import _AggregateRootType
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.compound_alias import CompoundAlias
from common.utils import convert_to_datetime


class CompoundAliasRepository(ConceptGenericRepository):
    root_class = CompoundAliasRoot
    value_class = CompoundAliasValue
    return_model = CompoundAlias

    def _create_new_value_node(self, ar: _AggregateRootType) -> VersionValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.is_preferred_synonym = ar.concept_vo.is_preferred_synonym
        value_node.save()

        value_node.is_compound.connect(
            CompoundRoot.nodes.get(uid=ar.concept_vo.compound_uid)
        )

        return value_node

    def _has_data_changed(self, ar: _AggregateRootType, value: VersionValue) -> bool:
        was_parent_data_modified = super()._has_data_changed(ar=ar, value=value)

        are_props_changed = (
            ar.concept_vo.is_preferred_synonym != value.is_preferred_synonym
        )

        are_rels_changed = ar.concept_vo.compound_uid != self._get_uid_or_none(
            value.is_compound.get_or_none()
        )

        return was_parent_data_modified or are_props_changed or are_rels_changed

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> CompoundAliasAR:
        major, minor = input_dict.get("version").split(".")
        return CompoundAliasAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=CompoundAliasVO.from_repository_values(
                name=input_dict.get("name"),
                name_sentence_case=input_dict.get("name_sentence_case"),
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
                is_preferred_synonym=input_dict.get("is_preferred_synonym"),
                compound_uid=input_dict.get("compound_uid"),
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

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> CompoundAliasAR:
        return CompoundAliasAR.from_repository_values(
            uid=root.uid,
            concept_vo=CompoundAliasVO.from_repository_values(
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                definition=value.definition,
                abbreviation=value.abbreviation,
                compound_uid=self._get_uid_or_none(value.is_compound.get_or_none()),
                is_preferred_synonym=value.is_preferred_synonym,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name, **kwargs
    ) -> str:
        return """
            WITH *,            
                head([(concept_value)-[:IS_COMPOUND]->(compound_root:CompoundRoot) | compound_root.uid]) AS compound_uid,
                head([(concept_value)-[:IS_COMPOUND]->(compound_root:CompoundRoot)-[:LATEST]->(compound_value:CompoundValue) | compound_value]) AS compound,
                concept_value.is_preferred_synonym AS is_preferred_synonym
            """

    def get_compound_preferred_synonyms(self, compound_uid: str) -> list[str]:
        query = f"""
            MATCH (concept_root:{self.root_class.__label__})-[:LATEST]->
                (concept_value {{is_preferred_synonym:True}})-[IS_COMPOUND]->
                (compound_root:CompoundRoot {{uid:$compound_uid}})
            RETURN concept_root.uid as synonyms
            """
        result, _ = db.cypher_query(query, {"compound_uid": compound_uid})
        return result[0] if len(result) else []

    def get_compound_uid_by_alias_uid(self, compound_alias_uid: str) -> str | None:
        query = """
            MATCH (concept_root:CompoundAliasRoot {uid:$compound_alias_uid})-[:LATEST]->
                (concept_value:CompoundAliasValue)-[IS_COMPOUND]->
                (compound_root:CompoundRoot)
            RETURN compound_root.uid as compound_uid
            """
        result, _ = db.cypher_query(query, {"compound_alias_uid": compound_alias_uid})
        if len(result) and len(result[0]):
            return result[0][0]
        return None

    def get_aliases_by_compound_uid(self, compound_uid: str) -> list[str]:
        query = """
            MATCH (concept_root:CompoundAliasRoot)-[:LATEST]->
                (concept_value:CompoundAliasValue)-[IS_COMPOUND]->
                (compound_root:CompoundRoot {uid:$compound_uid})
            RETURN concept_root.uid as compound_uid
            """
        result, _ = db.cypher_query(query, {"compound_uid": compound_uid})
        if len(result):
            return list(map(lambda x: x[0], result))
        return []
