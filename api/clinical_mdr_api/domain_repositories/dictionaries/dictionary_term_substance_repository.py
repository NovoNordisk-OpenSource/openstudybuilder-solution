from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.dictionaries.dictionary_term_repository import (
    DictionaryTermGenericRepository,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    format_generic_header_values,
)
from clinical_mdr_api.domain_repositories.models.dictionary import DictionaryTermRoot
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains.dictionaries.dictionary_term_substance import (
    DictionaryTermSubstanceAR,
    DictionaryTermSubstanceVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.dictionaries.dictionary_term import DictionaryTermSubstance
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    calculate_total_count_from_query_result,
    validate_filters_and_add_search_string,
)
from clinical_mdr_api.services.user_info import UserInfoService
from common.config import settings
from common.utils import convert_to_datetime


class DictionaryTermSubstanceRepository(DictionaryTermGenericRepository):
    def _create_new_value_node(
        self, library_name: str, ar: _AggregateRootType
    ) -> VersionValue:
        value_node = super()._create_new_value_node(library_name=library_name, ar=ar)

        value_node.save()

        if ar.dictionary_term_vo.pclass_uid is not None:
            value_node.has_pclass.connect(
                DictionaryTermRoot.nodes.get(uid=ar.dictionary_term_vo.pclass_uid)
            )

        return value_node

    def _create_aggregate_root_instance_from_cypher_result(
        self, term_dict: dict[str, Any]
    ) -> DictionaryTermSubstanceAR:
        major, minor = term_dict.get("version").split(".")
        return DictionaryTermSubstanceAR.from_repository_values(
            uid=term_dict["term_uid"],
            dictionary_term_vo=DictionaryTermSubstanceVO.from_repository_values(
                codelist_uid=term_dict["codelist_uid"],
                dictionary_id=term_dict["dictionary_id"],
                name=term_dict["name"],
                name_sentence_case=term_dict["name_sentence_case"],
                abbreviation=term_dict.get("abbreviation"),
                definition=term_dict.get("definition"),
                pclass_uid=(
                    term_dict.get("pclass").get("uid")
                    if term_dict.get("pclass")
                    else None
                ),
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
    ) -> DictionaryTermSubstanceAR:
        dictionary_codelist_root = root.has_term.single()
        library = dictionary_codelist_root.has_library.get_or_none()
        return DictionaryTermSubstanceAR.from_repository_values(
            uid=root.uid,
            dictionary_term_vo=DictionaryTermSubstanceVO.from_repository_values(
                codelist_uid=dictionary_codelist_root.uid,
                dictionary_id=value.dictionary_id,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                abbreviation=value.abbreviation,
                definition=value.definition,
                pclass_uid=self._get_uid_or_none(value.has_pclass.get_or_none()),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def generic_match_clause(self):
        return """
            MATCH (dictionary_codelist_root:DictionaryCodelistRoot)
            -[:HAS_TERM|HAD_TERM]->(dictionary_term_root:DictionaryTermRoot)-[:LATEST]->(dictionary_term_value)
            
            WHERE EXISTS {
            (dictionary_codelist_root)-[:LATEST_FINAL]->(DictionaryCodelistValue {name: $codelist_name})
            }   
            """

    def specific_alias_clause(self) -> str:
        return """
            WITH *,
                head([(dictionary_term_value)-[:HAS_PCLASS]->(pclass_dict_term_root:DictionaryTermRoot)-[:LATEST]->(pclass_dict_term_value) | {uid: pclass_dict_term_root.uid, dictionary_id: pclass_dict_term_value.dictionary_id, name: pclass_dict_term_value.name}]) AS pclass
            """

    def find_all(
        self,
        codelist_uid: str | None = None,
        sort_by: dict[str, bool] | None = None,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
        codelist_name: str | None = None,
    ) -> tuple[list[DictionaryTermSubstanceAR], int]:
        """
        Method runs a cypher query to fetch all needed data to create objects of type AggregateRootType.
        In the case of the following repository it will be some Terms aggregates.

        It uses cypher instead of neomodel as neomodel approach triggered some performance issues, because it is needed
        to traverse many relationships to fetch all needed data and each traversal is separate database call when using
        neomodel.
        :param codelist_name:
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
            return_model=DictionaryTermSubstance,
        )

        query.parameters.update({"codelist_name": codelist_name})
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

    def get_distinct_headers(
        self,
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

        query.parameters.update(
            {"codelist_name": settings.library_substances_codelist_name}
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

    def _has_data_changed(self, ar: DictionaryTermSubstanceAR, value: VersionValue):
        parent_data_modified = super()._has_data_changed(ar=ar, value=value)

        relation_changed = ar.dictionary_term_vo.pclass_uid != self._get_uid_or_none(
            value.has_pclass.get_or_none()
        )

        return parent_data_modified or relation_changed
