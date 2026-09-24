from abc import ABC
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
from clinical_mdr_api.domain_repositories.models.dictionary import (
    DictionaryCodelistRoot,
    DictionaryTermRoot,
    DictionaryTermValue,
    MEDRTTermRoot,
    MEDRTTermValue,
    SnomedTermRoot,
    SnomedTermValue,
    UCUMTermRoot,
    UCUMTermValue,
    UNIITermRoot,
    UNIITermValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains.dictionaries.dictionary_term import (
    DictionaryTermAR,
    DictionaryTermVO,
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
from common.exceptions import ValidationException
from common.utils import convert_to_datetime


class DictionaryTermGenericRepository(
    LibraryItemRepositoryImplBase[DictionaryTermAR], ABC
):
    root_class = DictionaryTermRoot
    value_class = DictionaryTermValue
    specific_root_class_mapping = {
        "snomed": SnomedTermRoot,
        "med-rt": MEDRTTermRoot,
        "unii": UNIITermRoot,
        "ucum": UCUMTermRoot,
    }
    specific_value_class_mapping = {
        "snomed": SnomedTermValue,
        "med-rt": MEDRTTermValue,
        "unii": UNIITermValue,
        "ucum": UCUMTermValue,
    }

    def generate_uid(self) -> str:
        return DictionaryTermRoot.get_next_free_uid_and_increment_counter()

    def _create_aggregate_root_instance_from_cypher_result(
        self, term_dict: dict[str, Any]
    ) -> DictionaryTermAR:
        major, minor = term_dict.get("version").split(".")
        return DictionaryTermAR.from_repository_values(
            uid=term_dict["term_uid"],
            dictionary_term_vo=DictionaryTermVO.from_repository_values(
                codelist_uid=term_dict["codelist_uid"],
                dictionary_id=term_dict["dictionary_id"],
                name=term_dict["name"],
                name_sentence_case=term_dict["name_sentence_case"],
                abbreviation=term_dict.get("abbreviation"),
                definition=term_dict.get("definition"),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=term_dict["library_name"],
                is_library_editable_callback=(
                    lambda _: term_dict["is_library_editable"]
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=term_dict["change_description"],
                status=LibraryItemStatus(term_dict.get("status")),
                author_id=term_dict["author_id"],
                author_username=UserInfoService.get_author_username_from_id(
                    term_dict["author_id"]
                ),
                start_date=convert_to_datetime(value=term_dict["start_date"]),
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
    ) -> DictionaryTermAR:
        dictionary_codelist_root = root.has_term.single()
        library = dictionary_codelist_root.has_library.get_or_none()
        return DictionaryTermAR.from_repository_values(
            uid=root.uid,
            dictionary_term_vo=DictionaryTermVO.from_repository_values(
                codelist_uid=dictionary_codelist_root.uid,
                dictionary_id=value.dictionary_id,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                abbreviation=value.abbreviation,
                definition=value.definition,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def generic_match_clause(self):
        return """MATCH (dictionary_codelist_root:DictionaryCodelistRoot {uid: $codelist_uid})
            -[:HAS_TERM|HAD_TERM]->(dictionary_term_root:DictionaryTermRoot)-[:LATEST]->(dictionary_term_value)"""

    def generic_alias_clause(self):
        return """
            DISTINCT dictionary_codelist_root, dictionary_term_root, dictionary_term_value,
            head([(library:Library)-[:CONTAINS_DICTIONARY_CODELIST]->(dictionary_codelist_root) | library]) AS library
            WITH
                dictionary_term_root,
                dictionary_term_value,
                dictionary_codelist_root.uid as codelist_uid,
                dictionary_term_root.uid AS term_uid,
                dictionary_term_value.dictionary_id as dictionary_id,
                dictionary_term_value.name AS name,
                dictionary_term_value.name_sentence_case as name_sentence_case,
                dictionary_term_value.abbreviation as abbreviation,
                dictionary_term_value.definition AS definition,
                library.name AS library_name,
                library.is_editable AS is_library_editable
                CALL (dictionary_term_root, dictionary_term_value) {
                    MATCH (dictionary_term_root)-[hv:HAS_VERSION]-(dictionary_term_value)
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
                dictionary_term_value,
                codelist_uid,
                term_uid,
                dictionary_id,
                name,
                name_sentence_case,
                abbreviation,
                definition,
                library_name,
                is_library_editable,
                version_rel.start_date AS start_date,
                version_rel.end_date AS end_date,
                version_rel.status AS status,
                version_rel.version AS version,
                version_rel.change_description AS change_description,
                version_rel.author_id AS author_id,
                coalesce(author.username, version_rel.author_id) AS author_username
        """

    def specific_alias_clause(self) -> str:
        """
        Method should be overridden in subclass repository
        and it contains matches and traversals specific for domain object represented by subclass repository.
        :return str:
        """
        return ""

    def find_all(
        self,
        codelist_uid: str | None = None,
        sort_by: dict[str, bool] | None = None,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
        **_kwargs,
    ) -> tuple[list[DictionaryTermAR], int]:
        """
        Method runs a cypher query to fetch all needed data to create objects of type AggregateRootType.
        In the case of the following repository it will be some Terms aggregates.

        It uses cypher instead of neomodel as neomodel approach triggered some performance issues, because it is needed
        to traverse many relationships to fetch all needed data and each traversal is separate database call when using
        neomodel.
        :param codelist_uid:
        :param sort_by:
        :param page_number:
        :param page_size:
        :param filter_by:
        :param filter_operator:
        :param total_count:
        :return GenericFilteringReturn[_AggregateRootType]:
        """
        match_clause = self.generic_match_clause()

        alias_clause = self.generic_alias_clause() + self.specific_alias_clause()
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

        query.parameters.update({"codelist_uid": codelist_uid})
        result_array, attributes_names = query.execute()
        extracted_items = self._retrieve_terms_from_cypher_res(
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

    def _retrieve_terms_from_cypher_res(
        self, result_array, attribute_names
    ) -> list[DictionaryTermAR]:
        """
        Method maps the result of the cypher query into real aggregate objects.
        :param result_array:
        :param attribute_names:
        :return list[_AggregateRootType]:
        """
        term_ars = []
        for term in result_array:
            term_dictionary = {}
            for term_property, attribute_name in zip(term, attribute_names):
                term_dictionary[attribute_name] = term_property
            term_ars.append(
                self._create_aggregate_root_instance_from_cypher_result(term_dictionary)
            )

        return term_ars

    def get_distinct_headers(
        self,
        codelist_uid: str,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ) -> list[Any]:
        # Match clause
        match_clause = self.generic_match_clause()

        # Aliases clause
        alias_clause = self.generic_alias_clause() + self.specific_alias_clause()

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

        query.parameters.update({"codelist_uid": codelist_uid})
        query.full_query = query.build_header_query(
            header_alias=field_name, page_size=page_size
        )
        result_array, _ = query.execute()

        return (
            format_generic_header_values(result_array[0][0])
            if len(result_array) > 0
            else []
        )

    def find_by_uid(self, term_uid: str, for_update: bool = False) -> DictionaryTermAR:
        """
        This method returns the Dictionary Term with provided uid

        :param term_uid: UID of Dictionary Term to get
        :param for_update:
        :return DictionaryTermAR:
        """
        return self.find_by_uid_2(uid=term_uid, for_update=for_update)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def save(self, item: DictionaryTermAR) -> None:
        if item.uid is not None and item.repository_closure_data is None:
            self._create(item)
        elif item.uid is not None and not item.is_deleted:
            self._update(item)
        elif item.is_deleted:
            assert item.uid is not None
            self._soft_delete(item.uid)

    def _create(self, item: DictionaryTermAR) -> DictionaryTermAR:
        """
        Creates new DictionaryTerm versioned object, checks possibility based on library setting,
        then creates database representation.
        Creates DictionaryTermRoot and DictionaryTermValue database objects,
        recreates AR based on created database model and returns created AR.
        """
        relation_data: LibraryItemMetadataVO = item.item_metadata
        dictionary_codelist = DictionaryCodelistRoot.nodes.get_or_none(
            uid=item.dictionary_term_vo.codelist_uid
        )

        library = dictionary_codelist.has_library.get_or_none()
        library_name = library.name.lower()

        ValidationException.raise_if(
            library_name not in self.specific_root_class_mapping,
            msg=f"Unknown specific type '{library_name}' of dictionary term.",
        )

        root = self.specific_root_class_mapping[library_name](uid=item.uid)

        value = self._create_new_value_node(library_name=library_name, ar=item)

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

        dictionary_codelist.has_term.connect(
            root,
            {
                "start_date": datetime.now(timezone.utc),
                "end_date": None,
                "author_id": item.item_metadata.author_id,
            },
        )

        library = self._get_library(item.library.name)
        root.has_library.connect(library)

        self._maintain_parameters(item, root, value)

        return item

    def _get_or_create_value(
        self,
        root: DictionaryTermRoot,
        ar: DictionaryTermAR,
        force_new_value_node: bool = False,
    ) -> DictionaryTermValue:
        if not force_new_value_node:
            items = root.has_version.filter(
                name=ar.name,
                dictionary_id=ar.dictionary_term_vo.dictionary_id,
                name_sentence_case=ar.dictionary_term_vo.name_sentence_case,
                abbreviation=ar.dictionary_term_vo.abbreviation,
                definition=ar.dictionary_term_vo.definition,
            )
            for itm in items:
                return itm
            latest_draft = root.latest_draft.get_or_none()
            if latest_draft and not self._has_data_changed(ar, latest_draft):
                return latest_draft
            latest_final = root.latest_final.get_or_none()
            if latest_final and not self._has_data_changed(ar, latest_final):
                return latest_final
            latest_retired = root.latest_retired.get_or_none()
            if latest_retired and not self._has_data_changed(ar, latest_retired):
                return latest_retired

        library = root.has_library.get_or_none()
        library_name = library.name.lower()
        new_value = self._create_new_value_node(library_name=library_name, ar=ar)
        self._db_save_node(new_value)
        return new_value

    def _create_new_value_node(
        self, library_name: str, ar: _AggregateRootType
    ) -> VersionValue:
        return self.specific_value_class_mapping[library_name](
            name=ar.name,
            dictionary_id=ar.dictionary_term_vo.dictionary_id,
            name_sentence_case=ar.dictionary_term_vo.name_sentence_case,
            abbreviation=ar.dictionary_term_vo.abbreviation,
            definition=ar.dictionary_term_vo.definition,
        )

    def _has_data_changed(self, ar: DictionaryTermAR, value: VersionValue):
        return (
            ar.name != value.name
            or ar.dictionary_term_vo.dictionary_id != value.dictionary_id
            or ar.dictionary_term_vo.name_sentence_case != value.name_sentence_case
            or ar.dictionary_term_vo.abbreviation != value.abbreviation
            or ar.dictionary_term_vo.definition != value.definition
        )

    def _maintain_parameters(
        self, versioned_object: DictionaryTermAR, root: VersionRoot, value: VersionValue
    ) -> None:
        maintain_template_parameter_query = """
            MATCH (dictionary_codelist_root:DictionaryCodelistRoot {uid: $codelist_uid})-[:LATEST]->
                (dictionary_codelist_value:TemplateParameter)
            WITH dictionary_codelist_root, dictionary_codelist_value
            MATCH (dictionary_term_root:DictionaryTermRoot {uid: $term_uid})-[:LATEST]->(dictionary_term_value)
            MERGE (dictionary_codelist_value)-[hpt:HAS_PARAMETER_TERM]->(dictionary_term_root)
            SET dictionary_term_root:TemplateParameterTermRoot
            SET dictionary_term_value:TemplateParameterTermValue
        """
        db.cypher_query(
            maintain_template_parameter_query,
            {
                "codelist_uid": versioned_object.dictionary_term_vo.codelist_uid,
                "term_uid": versioned_object.uid,
            },
        )

    def term_exists(self, term_uid: str) -> bool:
        query = """
            MATCH (dictionary_term_root:DictionaryTermRoot {uid: $uid})-[:LATEST_FINAL]->(dictionary_term_value)
            RETURN dictionary_term_root
            """
        result, _ = db.cypher_query(query, {"uid": term_uid})
        return len(result) > 0 and len(result[0]) > 0

    def term_exists_by_name(self, term_name: str, codelist_uid: str) -> bool:
        query = """
            MATCH (dictionary_codelist_root:DictionaryCodelistRoot {uid:$codelist_uid})-[:HAS_TERM]->
            (dictionary_term_root)-[:LATEST_FINAL]->(dictionary_term_value:DictionaryTermValue {name: $term_name})
            RETURN dictionary_term_root
            """
        result, _ = db.cypher_query(
            query, {"term_name": term_name, "codelist_uid": codelist_uid}
        )
        return len(result) > 0 and len(result[0]) > 0
