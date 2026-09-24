from abc import ABC, abstractmethod
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.utils import (
    list_concept_wildcard_properties,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    format_generic_header_values,
)
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    calculate_total_count_from_query_result,
    validate_filters_and_add_search_string,
)
from common.exceptions import NotFoundException, ValidationException


class StandardDataModelRepository(ABC):
    root_class = type
    value_class = type
    return_model: type

    def _create_base_model_from_cypher_result(self, input_dict: dict[str, Any]):
        return self.return_model.from_repository_output(input_dict)

    def specific_header_match_clause(self) -> str | None:
        return None

    def sort_by(self) -> dict[str, bool] | None:
        return None

    @abstractmethod
    def specific_alias_clause(self) -> str:
        """
        Methods is overridden in the ConceptGenericRepository subclasses
        and it contains matches and traversals specific for domain object represented by subclass repository.
        :return str:
        """

    # pylint: disable=unused-argument
    def union_match_clause(self, _: dict[Any, Any]) -> str | None:
        return None

    def find_by_uid(
        self,
        uid: str,
        **kwargs,
    ) -> BaseModel | None:
        if not uid:
            return None

        match_clause = self.generic_match_clause(versioning_relationship="LATEST")

        filter_statements, filter_query_parameters = self.create_query_filter_statement(
            uid=uid, find_by_uid=True, **kwargs
        )
        match_clause += filter_statements
        alias_clause = self.specific_alias_clause()
        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            return_model=self.return_model,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()

        extracted_items = self._retrieve_items_from_cypher_res(
            result_array, attributes_names
        )

        NotFoundException.raise_if(
            len(extracted_items) == 0, str(self.return_model.__class__), uid
        )
        ValidationException.raise_if(
            len(extracted_items) > 1,
            msg=f"Returned more than one '{self.return_model.__class__}' with UID '{uid}'",
        )

        return extracted_items[0]

    def generic_match_clause(self, versioning_relationship: str):
        standard_data_model_label = self.root_class.__label__
        standard_data_model_value_label = self.value_class.__label__
        return f"""MATCH (standard_root:{standard_data_model_label})-[:{versioning_relationship}]->
                (standard_value:{standard_data_model_value_label})"""

    def _retrieve_items_from_cypher_res(
        self, result_array, attribute_names
    ) -> list[BaseModel]:
        """
        Method maps the result of the cypher query into real aggregate objects.
        :param result_array:
        :param attribute_names:
        :return Iterable[BaseModel]:
        """
        items = []
        for item in result_array:
            concept_dictionary = {}
            for concept_property, attribute_name in zip(item, attribute_names):
                concept_dictionary[attribute_name] = concept_property
            items.append(self._create_base_model_from_cypher_result(concept_dictionary))
        return items

    def create_query_filter_statement(
        self, uid: str | None = None, **kwargs
    ) -> tuple[str, dict[Any, Any]]:
        filter_parameters: list[Any] = []
        filter_query_parameters: dict[Any, Any] = {}
        if uid:
            filter_parameters.append("standard_root.uid=$uid")
            filter_query_parameters["uid"] = uid
        filter_statements = " AND ".join(filter_parameters)
        filter_statements = (
            "WHERE " + filter_statements if len(filter_statements) > 0 else ""
        )
        return filter_statements, filter_query_parameters

    def find_all(
        self,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        **kwargs,
    ) -> tuple[list[BaseModel], int]:
        """
        Method runs a cypher query to fetch all needed data to create objects of type AggregateRootType.
        In the case of the following repository it will be some Concept aggregates.

        It uses cypher instead of neomodel as neomodel approach triggered some performance issues, because it is needed
        to traverse many relationships to fetch all needed data and each traversal is separate database call when using
        neomodel.
        :param sort_by:
        :param page_number:
        :param page_size:
        :param filter_by:
        :param filter_operator:
        :param total_count:
        :return GenericFilteringReturn[_AggregateRootType]:
        """
        match_clause = self.generic_match_clause(versioning_relationship="HAS_VERSION")

        filter_statements, filter_query_parameters = self.create_query_filter_statement(
            **kwargs
        )
        match_clause += filter_statements

        alias_clause = self.specific_alias_clause()
        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            union_match_clause=(
                _union_match_clause + filter_statements
                if (
                    _union_match_clause := self.union_match_clause(
                        filter_query_parameters
                    )
                )
                else None
            ),
            sort_by=self.sort_by() if self.sort_by() else sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
            return_model=self.return_model,
        )
        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()

        extracted_items = self._retrieve_items_from_cypher_res(
            result_array, attributes_names
        )

        total_amount = calculate_total_count_from_query_result(
            len(extracted_items), page_number, page_size, total_count
        )
        if total_amount is None:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0 and total_count:
                if query.union_match_clause:
                    total_amount = count_result[0][0] + count_result[1][0]
                else:
                    total_amount = count_result[0][0]
            else:
                total_amount = 0

        return extracted_items, total_amount

    def get_distinct_headers(
        self,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
        **kwargs,
    ) -> list[Any]:
        # pylint: disable=unused-argument
        """
        Method runs a cypher query to fetch possible values for a given field_name, with a limit of page_size.
        It uses generic filtering capability, on top of filtering the field_name with provided search_string.

        :param field_name: Field name for which to return possible values
        :param search_string
        :param filter_by:
        :param filter_operator: Same as for generic filtering
        :param page_size: Max number of values to return. Default 10
        :return list[Any]:
        """
        # Match clause
        match_clause = self.generic_match_clause(versioning_relationship="HAS_VERSION")
        if self.specific_header_match_clause():
            match_clause += self.specific_header_match_clause()

        filter_statements, filter_query_parameters = self.create_query_filter_statement(
            **kwargs
        )
        match_clause += filter_statements
        # Aliases clause
        alias_clause = self.specific_alias_clause()

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
            return_model=self.return_model,
            wildcard_properties_list=list_concept_wildcard_properties(
                self.return_model
            ),
        )

        query.parameters.update(filter_query_parameters)
        query.full_query = query.build_header_query(
            header_alias=field_name, page_size=page_size
        )
        result_array, _ = query.execute()

        return (
            format_generic_header_values(result_array[0][0])
            if len(result_array) > 0
            else []
        )
