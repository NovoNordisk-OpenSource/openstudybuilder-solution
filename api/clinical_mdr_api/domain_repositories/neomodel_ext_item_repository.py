from abc import abstractmethod
from typing import Any, TypeVar, cast

from neo4j.time import DateTime
from neomodel import NodeSet
from neomodel.sync_.match import NodeNameResolver, RelationNameResolver
from pydantic import BaseModel

from clinical_mdr_api.repositories._utils import (
    FilterOperator,
    get_field,
    get_field_path,
    get_order_by_clause,
    is_injected_field,
    merge_q_query_filters,
    transform_filters_into_neomodel,
    validate_filter_by_dict,
    validate_filters_and_add_search_string,
    validate_sort_by_dict,
)
from common.utils import convert_to_datetime, validate_page_number_and_page_size

# pylint: disable=invalid-name
_StandardsReturnType = TypeVar("_StandardsReturnType", bound=BaseModel)


class NeomodelExtBaseRepository:
    root_class: type
    return_model: type[BaseModel]

    @abstractmethod
    def get_neomodel_extension_query(self) -> NodeSet:
        """
        Method creates a specific neomodel extension query that
        fetches all required relationships to build an object of type
        return_model.

        :return NodeSet:
        """

        raise NotImplementedError

    def extend_distinct_headers_query(
        self,
        nodeset: NodeSet,
        field_name: str,  # pylint: disable=unused-argument
        filter_by: (  # pylint: disable=unused-argument
            dict[str, dict[str, Any]] | None
        ) = None,
    ) -> NodeSet:
        """
        Method to extend the query built for distinct header retrieval.
        """
        return nodeset

    def check_for_incorrect_optional_markers(
        self, nodes: NodeSet, q_filters: list[Any]
    ) -> None:
        """
        Make sure that traversal used in filters are included in the cypher query
        using a MATCH and not an OPTIONAL MATCH statement.
        """
        for qfilter in q_filters:
            path = qfilter.children[0][0]
            if "__" not in path and "|" not in path:
                continue
            parts = path.split("__")
            path = "__".join(parts[:-1])
            if "|" in parts[-1]:
                path += "__" + parts[-1].split("|")[0]
            for relation in nodes.relations_to_fetch:
                if relation.value == path and relation.optional:
                    relation.optional = False

    def _get_subgraph_and_filters(
        self,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        **_kwargs,
    ) -> tuple[list[Any], list[Any]]:
        """
        Build and execute the neomodel extension query, returning subgraph and filters.
        Can be used by subclasses that need to process the subgraph before model building.

        Args:
            **_kwargs: Additional arguments for subclass-specific filtering

        Returns:
            tuple: (subgraph, q_filters)
        """
        # Validate params
        filter_by = validate_filter_by_dict(filter_by=filter_by)
        sort_by = validate_sort_by_dict(sort_by=sort_by)
        validate_page_number_and_page_size(page_number=page_number, page_size=page_size)

        q_filters = transform_filters_into_neomodel(
            filter_by=filter_by, model=self.return_model
        )
        q_filters = merge_q_query_filters(q_filters, filter_operator=filter_operator)
        sort_paths = get_order_by_clause(sort_by=sort_by, model=self.return_model)
        start: int = (page_number - 1) * page_size
        end: int = start + page_size
        nodes = self.get_neomodel_extension_query()
        self.check_for_incorrect_optional_markers(nodes, q_filters)
        nodes = nodes.order_by(sort_paths[0] if len(sort_paths) > 0 else "uid")
        nodes = nodes.filter(*q_filters)[start:end]
        subgraph = nodes.resolve_subgraph()

        return subgraph, q_filters

    def _build_models_from_subgraph(
        self, subgraph: list[Any]
    ) -> list[_StandardsReturnType]:
        """
        Build Pydantic models from subgraph nodes.
        Can be overridden by subclasses to add custom processing.

        Args:
            subgraph: List of nodes from resolve_subgraph()

        Returns:
            List of validated Pydantic models
        """
        return cast(
            list[_StandardsReturnType],
            [self.return_model.model_validate(node) for node in subgraph],
        )

    def find_all(
        self,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        **kwargs,
    ) -> tuple[list[_StandardsReturnType], int]:
        subgraph, q_filters = self._get_subgraph_and_filters(
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=filter_by,
            filter_operator=filter_operator,
            **kwargs,
        )

        all_data_model: list[_StandardsReturnType] = self._build_models_from_subgraph(
            subgraph
        )

        if total_count:
            len_query = self.root_class.nodes.filter(*q_filters)
            all_nodes = len(len_query)

        # pylint: disable=possibly-used-before-assignment
        return all_data_model, all_nodes if total_count else 0

    def find_by_uid(self, uid: str) -> _StandardsReturnType | None:
        return self.get_neomodel_extension_query().filter(uid=uid).resolve_subgraph()

    def get_distinct_headers(
        self,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ) -> list[Any]:
        """
        Fetches possible values for a given field_name, with a limit of page_size.
        It uses generic filtering capability, on top of filtering the field_name with provided search_string.

        Args:
            field_name (str): The name of the field for which to return possible values.
            search_string (str | None, optional): A string to filter the field with. Defaults to "".
            filter_by (dict | None, optional): A dictionary of filters. Defaults to None.
            filter_operator (FilterOperator | None, optional): The operator to use for the filters. Defaults to FilterOperator.AND.
            page_size (int, optional): The maximum number of values to return. Defaults to 10.

        Returns:
        A `sequence` of possible values for the given field_name.
        """
        # Add header field name to filter_by, to filter with a CONTAINS pattern
        filter_by = validate_filters_and_add_search_string(
            search_string, field_name, filter_by
        )
        q_filters = transform_filters_into_neomodel(
            filter_by=filter_by, model=self.return_model
        )
        q_filters = merge_q_query_filters(q_filters, filter_operator=filter_operator)
        field = get_field(prop=field_name, model=self.return_model)
        field_path = get_field_path(prop=field_name, field=field)

        field_name_alias = field_name.replace(".", "_")

        nodeset = self.root_class.nodes
        if "|" in field_path:
            path, prop = field_path.rsplit("|", 1)
            if is_injected_field(field):
                # We don't want to add a traversal in this case
                source = path
            else:
                source = RelationNameResolver(path)
                nodeset = nodeset.traverse(path)
        elif "__" in field_path:
            path, prop = field_path.rsplit("__", 1)
            source = NodeNameResolver(path)
            nodeset = nodeset.traverse(path)
        else:
            # FIXME: we need a proper way to resolve the variable name (NodeNameResolver
            # does not support 'self'...)
            source = self.root_class.__name__.lower()
            prop = field_path
        nodeset = nodeset.filter(*q_filters)[:page_size].intermediate_transform(
            {
                field_name_alias: {
                    "source": source,
                    "source_prop": prop,
                    "include_in_return": True,
                }
            },
            distinct=True,
        )
        nodeset = self.extend_distinct_headers_query(
            nodeset, field_name=field_name, filter_by=filter_by
        )

        rs = nodeset.all()

        for idx, node in enumerate(rs):
            if isinstance(node, DateTime):
                rs[idx] = convert_to_datetime(node)

        return rs


def _get_author_id(node) -> str:
    author_id = node._relations.get("latest_version_relationship").author_id
    return author_id if author_id else "?"
