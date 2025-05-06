from abc import abstractmethod
from typing import Any, TypeVar

from neomodel import NodeSet
from neomodel.sync_.match import NodeNameResolver

from clinical_mdr_api.repositories._utils import (
    FilterOperator,
    get_field,
    get_field_path,
    get_order_by_clause,
    merge_q_query_filters,
    transform_filters_into_neomodel,
    validate_filter_by_is_dict,
    validate_filters_and_add_search_string,
    validate_sort_by_is_dict,
)
from common.utils import validate_page_number_and_page_size

# pylint: disable=invalid-name
_StandardsReturnType = TypeVar("_StandardsReturnType")


class NeomodelExtBaseRepository:
    root_class = type
    return_model = type

    @abstractmethod
    def get_neomodel_extension_query(self) -> NodeSet:
        """
        Method creates a specific neomodel extension query that
        fetches all required relationships to build an object of type
        return_model.

        :return NodeSet:
        """

        raise NotImplementedError

    def find_all(
        self,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> tuple[list[_StandardsReturnType], int]:
        # Validate params
        filter_by = validate_filter_by_is_dict(filter_by=filter_by)
        sort_by = validate_sort_by_is_dict(sort_by=sort_by)
        validate_page_number_and_page_size(page_number=page_number, page_size=page_size)

        q_filters = transform_filters_into_neomodel(
            filter_by=filter_by, model=self.return_model
        )
        q_filters = merge_q_query_filters(q_filters, filter_operator=filter_operator)
        sort_paths = get_order_by_clause(sort_by=sort_by, model=self.return_model)
        start: int = (page_number - 1) * page_size
        end: int = start + page_size
        nodes = self.get_neomodel_extension_query()
        nodes = nodes.order_by(sort_paths[0] if len(sort_paths) > 0 else "uid")
        nodes = nodes.filter(*q_filters)[start:end]
        nodes = nodes.resolve_subgraph()

        all_data_model = [
            self.return_model.model_validate(activity_node) for activity_node in nodes
        ]
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
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
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
        nodeset = self.root_class.nodes
        if "__" in field_path:
            path, prop = field_path.rsplit("__", 1)
            source = NodeNameResolver(path)
            nodeset = nodeset.fetch_relations(path)
        else:
            # FIXME: we need a proper way to resolve the variable name (NodeNameResolver
            # does not support 'self'...)
            source = self.root_class.__name__.lower()
            prop = field_path
        values = (
            nodeset.filter(*q_filters)[:page_size]
            .intermediate_transform(
                {
                    field_path: {
                        "source": source,
                        "source_prop": prop,
                        "include_in_return": True,
                    }
                },
                distinct=True,
            )
            .all()
        )
        return values


def _get_author_id(node) -> str:
    author_id = node._relations.get("latest_version_relationship").author_id
    return author_id if author_id else "?"
