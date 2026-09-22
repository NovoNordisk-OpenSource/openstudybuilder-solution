from datetime import datetime, timezone
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    format_generic_header_values,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CodelistTermRelationship,
)
from clinical_mdr_api.domain_repositories.models.dictionary import (
    DictionaryCodelistRoot,
    DictionaryCodelistValue,
    DictionaryTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameterTermRoot,
)
from clinical_mdr_api.domains.dictionaries.dictionary_codelist import (
    DictionaryCodelistAR,
    DictionaryCodelistVO,
    DictionaryType,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.dictionaries.dictionary_codelist import DictionaryCodelist
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    calculate_total_count_from_query_result,
    sb_clear_cache,
    validate_filters_and_add_search_string,
)
from clinical_mdr_api.services.user_info import UserInfoService
from common.utils import convert_to_datetime


class DictionaryCodelistGenericRepository(
    LibraryItemRepositoryImplBase[DictionaryCodelistAR]
):
    root_class = DictionaryCodelistRoot
    value_class = DictionaryCodelistValue

    def generate_uid(self) -> str:
        return DictionaryCodelistRoot.get_next_free_uid_and_increment_counter()

    @classmethod
    def is_ct_node_a_tp(cls, dictionary_value_node: VersionValue) -> bool:
        return "TemplateParameter" in dictionary_value_node.labels()

    def _create_aggregate_root_instance_from_cypher_result(
        self, codelist_dict: dict[str, Any]
    ) -> DictionaryCodelistAR:
        major, minor = codelist_dict.get("version").split(".")

        return DictionaryCodelistAR.from_repository_values(
            uid=codelist_dict["codelist_uid"],
            dictionary_codelist_vo=DictionaryCodelistVO.from_repository_values(
                name=codelist_dict["name"],
                is_template_parameter=codelist_dict["template_parameter"],
                current_terms=[
                    (term["term_uid"], term["author"])
                    for term in codelist_dict.get("current_terms")
                ],
                previous_terms=[
                    (term["term_uid"], term["author"])
                    for term in codelist_dict.get("previous_terms")
                ],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=codelist_dict["library_name"],
                is_library_editable_callback=(
                    lambda _: codelist_dict["is_library_editable"]
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=codelist_dict["change_description"],
                status=LibraryItemStatus(codelist_dict.get("status")),
                author_id=codelist_dict["author_id"],
                author_username=UserInfoService.get_author_username_from_id(
                    codelist_dict["author_id"]
                ),
                start_date=convert_to_datetime(value=codelist_dict["start_date"]),
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> DictionaryCodelistAR:
        current_terms = []
        previous_terms = []
        for dictionary_term in root.has_term.all():
            has_term_relationship: CodelistTermRelationship = (
                root.has_term.relationship(dictionary_term)
            )
            current_terms.append((dictionary_term.uid, has_term_relationship.author_id))
        for dictionary_term in root.had_term.all():
            had_term_relationship: CodelistTermRelationship = (
                root.had_term.relationship(dictionary_term)
            )
            previous_terms.append(
                (dictionary_term.uid, had_term_relationship.author_id)
            )

        return DictionaryCodelistAR.from_repository_values(
            uid=root.uid,
            dictionary_codelist_vo=DictionaryCodelistVO.from_repository_values(
                name=value.name,
                is_template_parameter=self.is_ct_node_a_tp(value),
                current_terms=current_terms,
                previous_terms=previous_terms,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def generic_match_clause(self, dictionary_type: DictionaryType):
        return f"""MATCH (library:Library {{name:"{dictionary_type.value}"}})-[:CONTAINS_DICTIONARY_CODELIST]->
                (dictionary_codelist_root:DictionaryCodelistRoot)-[:LATEST]-(dictionary_codelist_value)"""

    def generic_alias_clause(self):
        return """
            DISTINCT dictionary_codelist_root, dictionary_codelist_value, library,
            [(dictionary_codelist_root)-[has_term:HAS_TERM]->(dictionary_term_root) | {
                term_uid: dictionary_term_root.uid,
                author: has_term.author
            }] as has_terms,
            [(dictionary_codelist_root)-[had_term:HAD_TERM]->(dictionary_term_root) | {
                term_uid: dictionary_term_root.uid,
                author: had_term.author
            }] as had_terms
            WITH
                dictionary_codelist_root, dictionary_codelist_value,
                dictionary_codelist_root.uid AS codelist_uid,
                dictionary_codelist_value.name AS name,
                "TemplateParameter" IN labels(dictionary_codelist_value) AS template_parameter,
                library.name AS library_name,
                library.is_editable AS is_library_editable,
                has_terms,
                had_terms
                CALL (dictionary_codelist_root, dictionary_codelist_value) {
                    MATCH (dictionary_codelist_root)-[hv:HAS_VERSION]-(dictionary_codelist_value)
                    WITH hv
                    ORDER BY
                        toInteger(split(hv.version, '.')[0]) ASC,
                        toInteger(split(hv.version, '.')[1]) ASC,
                        hv.end_date ASC,
                        hv.start_date ASC
                    WITH collect(hv) as hvs
                    RETURN last(hvs) AS version_rel
                }
            WITH *
                CALL (version_rel) {
                    OPTIONAL MATCH (author: User)
                    WHERE author.user_id = version_rel.author_id
                    RETURN author
                }
            WITH
                codelist_uid,
                name,
                template_parameter,
                library_name,
                is_library_editable,
                version_rel.start_date AS start_date,
                version_rel.end_date AS end_date,
                version_rel.status AS status,
                version_rel.version AS version,
                version_rel.change_description AS change_description,
                version_rel.author_id AS author_id,
                coalesce(author.username, version_rel.author_id) AS author_username,
                has_terms AS current_terms,
                had_terms AS previous_terms
        """

    def find_all(
        self,
        library_name: DictionaryType,
        sort_by: dict[str, bool] | None = None,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
        **_kwargs,
    ) -> tuple[list[DictionaryCodelistAR], int]:
        """
        Method runs a cypher query to fetch all needed data to create objects of type AggregateRootType.
        In the case of the following repository it will be some Codelists aggregates.

        It uses cypher instead of neomodel as neomodel approach triggered some performance issues, because it is needed
        to traverse many relationships to fetch all needed data and each traversal is separate database call when using
        neomodel.
        :param library_name:
        :param sort_by:
        :param page_number:
        :param page_size:
        :param filter_by:
        :param filter_operator:
        :param total_count:
        :return GenericFilteringReturn[DictionaryCodelistAR]:
        """
        match_clause = self.generic_match_clause(dictionary_type=library_name)

        alias_clause = self.generic_alias_clause()
        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
            return_model=DictionaryCodelist,
        )
        result_array, attributes_names = query.execute()
        extracted_items = self._retrieve_codelists_from_cypher_res(
            result_array, attributes_names
        )

        total_amount = calculate_total_count_from_query_result(
            len(extracted_items), page_number, page_size, total_count
        )
        if total_amount is None:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            total_amount = count_result[0][0] if len(count_result) > 0 else 0

        return extracted_items, total_amount

    def _retrieve_codelists_from_cypher_res(
        self, result_array, attribute_names
    ) -> list[DictionaryCodelistAR]:
        """
        Method maps the result of the cypher query into real aggregate objects.
        :param result_array:
        :param attribute_names:
        :return list[DictionaryCodelistAR]:
        """
        codelist_ars = []
        for codelist in result_array:
            codelist_dictionary = {}
            for codelist_property, attribute_name in zip(codelist, attribute_names):
                codelist_dictionary[attribute_name] = codelist_property
            codelist_ars.append(
                self._create_aggregate_root_instance_from_cypher_result(
                    codelist_dictionary
                )
            )

        return codelist_ars

    def get_distinct_headers(
        self,
        library: DictionaryType,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ) -> list[str]:
        # Match clause
        match_clause = self.generic_match_clause(dictionary_type=library)

        # Aliases clause
        alias_clause = self.generic_alias_clause()

        # Add header field name to filter_by, to filter with a CONTAINS pattern
        filter_by = validate_filters_and_add_search_string(
            search_string, field_name, filter_by
        )

        # Use Cypher query class to use reusable helper methods
        query = CypherQueryBuilder(
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            match_clause=match_clause,
            alias_clause=alias_clause,
        )

        query.full_query = query.build_header_query(
            header_alias=field_name, page_size=page_size
        )
        result_array, _ = query.execute()

        return (
            format_generic_header_values(result_array[0][0])
            if len(result_array) > 0
            else []
        )

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def save(self, item: DictionaryCodelistAR) -> None:
        if item.uid is not None and item.repository_closure_data is None:
            self._create(item)
        elif item.uid is not None and not item.is_deleted:
            self._update(item)
        elif item.is_deleted:
            assert item.uid is not None
            self._soft_delete(item.uid)

    def _create(self, item: DictionaryCodelistAR) -> DictionaryCodelistAR:
        """
        Creates new DictionaryCodelist versioned object, checks possibility based on library setting,
        then creates database representation.
        Creates DictionaryCodelistRoot and DictionaryCodelistValue database objects,
        recreates AR based on created database model and returns created AR.
        """
        relation_data: LibraryItemMetadataVO = item.item_metadata
        root = self.root_class(uid=item.uid)
        value = self.value_class(name=item.name)
        self._db_save_node(root)

        (
            root,
            value,
            _,
            _,
            _,
        ) = self._db_create_and_link_nodes(
            root, value, self._library_item_metadata_vo_to_datadict(relation_data)
        )

        library = self._get_library(item.library.name)
        root.has_library.connect(library)

        self._maintain_parameters(item, root, value)

        return item

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: VersionRoot,
        value: VersionValue,
    ) -> None:
        """
        Method maintains HAS_TERM relationship and HAD_TERM relationship if some DictionaryTerm was added or deleted
        from the DictionaryCodelist identified by versioned_object.uid
        It also maintains TemplateParameter label if it was modified.
        :param versioned_object:
        :param root:
        :param value:
        :return None:
        """
        # only when performing an update of a codelist
        if versioned_object.repository_closure_data is not None:
            (
                _,
                _,
                _,
                previous_versioned_object,
            ) = versioned_object.repository_closure_data
            added_terms = list(
                set(versioned_object.dictionary_codelist_vo.current_terms)
                - set(previous_versioned_object.dictionary_codelist_vo.current_terms)
            )
            removed_terms = list(
                set(previous_versioned_object.dictionary_codelist_vo.current_terms)
                - set(versioned_object.dictionary_codelist_vo.current_terms)
            )

            for added_term in added_terms:
                dictionary_codelist_node = DictionaryCodelistRoot.nodes.get_or_none(
                    uid=versioned_object.uid
                )
                dictionary_term_node = DictionaryTermRoot.nodes.get_or_none(
                    uid=added_term[0]
                )
                # adding HAS_TERM relationship as term was added to the codelist
                dictionary_codelist_node.has_term.connect(
                    dictionary_term_node,
                    {
                        "start_date": datetime.now(timezone.utc),
                        "end_date": None,
                        "author_id": added_term[1],
                    },
                )

            for removed_term in removed_terms:
                dictionary_codelist_node = DictionaryCodelistRoot.nodes.get_or_none(
                    uid=versioned_object.uid
                )
                dictionary_term_node = DictionaryTermRoot.nodes.get_or_none(
                    uid=removed_term[0]
                )
                has_term_relationship: CodelistTermRelationship = (
                    dictionary_codelist_node.has_term.relationship(dictionary_term_node)
                )
                # adding HAD_TERM relationship as term was removed from codelist
                dictionary_codelist_node.had_term.connect(
                    dictionary_term_node,
                    {
                        "start_date": has_term_relationship.start_date,
                        "end_date": datetime.now(timezone.utc),
                        "author_id": removed_term[1],
                    },
                )
                # removing HAS_TERM relationship as term was removed from codelist
                dictionary_codelist_node.has_term.disconnect(dictionary_term_node)

        if versioned_object.dictionary_codelist_vo.is_template_parameter:
            query = """
                MATCH (dictionary_codelist_root:DictionaryCodelistRoot {uid: $codelist_uid})-[:LATEST]->(dictionary_codelist_value)
                SET dictionary_codelist_value:TemplateParameter
                WITH dictionary_codelist_root, dictionary_codelist_value

                MATCH (dictionary_codelist_root)-[:HAS_TERM]->(dictionary_term_root:DictionaryTermRoot)-[:LATEST]->(dictionary_term_value)
                MERGE (dictionary_codelist_value)-[hpt:HAS_PARAMETER_TERM]->(dictionary_term_root)
                SET dictionary_term_root:TemplateParameterTermRoot
                SET dictionary_term_value:TemplateParameterTermValue
            """
            db.cypher_query(query, {"codelist_uid": versioned_object.uid})
            TemplateParameterTermRoot.generate_node_uids_if_not_present()
        else:
            query = """
                MATCH (dictionary_codelist_root:DictionaryCodelistRoot {uid: $codelist_uid})-[:LATEST]->(dictionary_codelist_value)
                REMOVE dictionary_codelist_value:TemplateParameter
                WITH dictionary_codelist_root, dictionary_codelist_value

                MATCH (dictionary_codelist_root)-[:HAS_TERM]->(dictionary_term_root:DictionaryTermRoot)-[:LATEST]->(dictionary_term_value)
                MATCH (dictionary_codelist_value)-[hpt:HAS_PARAMETER_TERM]->(dictionary_term_root)
                DELETE hpt
                REMOVE dictionary_term_root:TemplateParameterTermRoot
                REMOVE dictionary_term_value:TemplateParameterTermValue
            """
            db.cypher_query(query, {"codelist_uid": versioned_object.uid})

    def codelist_exists(self, codelist_uid: str) -> bool:
        query = """
            MATCH (dictionary_codelist_root:DictionaryCodelistRoot {uid: $uid})-[:LATEST_FINAL]->(dictionary_codelist_value)
            RETURN dictionary_codelist_root
            """
        result, _ = db.cypher_query(query, {"uid": codelist_uid})
        return len(result) > 0 and len(result[0]) > 0

    def codelist_exists_by_name(self, codelist_name: str) -> bool:
        query = """
            MATCH (dictionary_codelist_root)-[:LATEST]->(dictionary_codelist_value:DictionaryCodelistValue
             {name: $codelist_name})
            RETURN dictionary_codelist_root
            """
        result, _ = db.cypher_query(query, {"codelist_name": codelist_name})
        return len(result) > 0 and len(result[0]) > 0
