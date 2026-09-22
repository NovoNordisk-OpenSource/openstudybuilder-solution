import functools
import inspect
import logging
import re
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Callable, Generic

from cachetools import cached
from dateutil.parser import isoparse
from neo4j.exceptions import CypherSyntaxError
from neomodel import Q, db
from pydantic import BaseModel, Field, field_validator
from pydantic.types import T

from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    CompactActivityInstanceClassForActivityItemClass,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityGroupingHierarchySimpleModel,
)
from clinical_mdr_api.models.concepts.concept import VersionProperties
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleDictionaryTermModel,
    SimpleTermModel,
)
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmTranslatedTextModel,
)
from clinical_mdr_api.models.standard_data_models.sponsor_model import SponsorModelBase
from common.exceptions import ValidationException
from common.utils import (
    filter_sort_valid_keys_re,
    get_field_type,
    get_sub_fields,
    validate_max_skip_clause,
)

# Re-used regex
NESTED_REGEX = re.compile(r"\.")

log = logging.getLogger(__name__)

# Lucene special characters that need to be escaped: + - && || ! ( ) { } [ ] ^ " ~ * ? : \ /
LUCENE_SPECIAL_CHARS = r'+-&|!(){}[]^"~*?:\/'
LUCENE_ESCAPE_REGEX = re.compile(f"([{re.escape(LUCENE_SPECIAL_CHARS)}])")


def escape_lucene_special_chars(search_string: str) -> str:
    """
    Escape special characters in Lucene query syntax.

    Lucene special characters: + - && || ! ( ) { } [ ] ^ " ~ * ? : backslash /
    Lucene special characters are escaped with a backslash to be treated as literals.

    :param search_string: The raw search string from user input
    :return: Escaped search string safe for Lucene queries
    """
    # Use regex to escape all special characters in a single pass
    return LUCENE_ESCAPE_REGEX.sub(r"\\\1", search_string)


class ComparisonOperator(Enum):
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    CONTAINS = "co"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL_TO = "ge"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL_TO = "le"
    BETWEEN = "bw"
    IN = "in"


comparison_operator_to_neomodel = {
    ComparisonOperator.EQUALS: "",
    ComparisonOperator.NOT_EQUALS: "__ne",
    ComparisonOperator.CONTAINS: "__contains",
    ComparisonOperator.GREATER_THAN: "__gt",
    ComparisonOperator.GREATER_THAN_OR_EQUAL_TO: "__gte",
    ComparisonOperator.LESS_THAN: "__lt",
    ComparisonOperator.LESS_THAN_OR_EQUAL_TO: "__lte",
    ComparisonOperator.IN: "__in",
}


data_type_filters = {
    str: [
        ComparisonOperator.EQUALS,
        ComparisonOperator.NOT_EQUALS,
        ComparisonOperator.CONTAINS,
        ComparisonOperator.IN,
    ],
    int: [
        ComparisonOperator.EQUALS,
        ComparisonOperator.NOT_EQUALS,
        ComparisonOperator.GREATER_THAN,
        ComparisonOperator.GREATER_THAN_OR_EQUAL_TO,
        ComparisonOperator.LESS_THAN,
        ComparisonOperator.LESS_THAN_OR_EQUAL_TO,
        ComparisonOperator.BETWEEN,
        ComparisonOperator.IN,
    ],
    float: [
        ComparisonOperator.EQUALS,
        ComparisonOperator.NOT_EQUALS,
        ComparisonOperator.GREATER_THAN,
        ComparisonOperator.GREATER_THAN_OR_EQUAL_TO,
        ComparisonOperator.LESS_THAN,
        ComparisonOperator.LESS_THAN_OR_EQUAL_TO,
        ComparisonOperator.BETWEEN,
        ComparisonOperator.IN,
    ],
    datetime: [
        ComparisonOperator.EQUALS,
        ComparisonOperator.NOT_EQUALS,
        ComparisonOperator.GREATER_THAN,
        ComparisonOperator.GREATER_THAN_OR_EQUAL_TO,
        ComparisonOperator.LESS_THAN,
        ComparisonOperator.LESS_THAN_OR_EQUAL_TO,
        ComparisonOperator.BETWEEN,
        ComparisonOperator.IN,
    ],
    bool: [ComparisonOperator.EQUALS, ComparisonOperator.IN],
}


def get_wildcard_filter(filter_elem, model: type[BaseModel]):
    """
    Creates the wildcard filter for all string properties also nested one.
    The wildcard filter is a `contains` case insensitive filter that is combined by OR operator with other properties.

    Args:
        filter_elem: The filter element containing the search term.
        model (type[BaseModel]): The model to create the wildcard filter for.

    Returns:
        The created wildcard filter.
    """

    wildcard_filter = []
    for name, field in model.model_fields.items():
        field_source = get_field_path(prop=name, field=field)
        model_sources = get_version_properties_sources()
        jse = field.json_schema_extra or {}
        if not (
            field_source in model_sources
            and get_field_type(field.annotation) is str
            and not issubclass(model, SponsorModelBase)
        ) and not jse.get("remove_from_wildcard", False):
            if issubclass(get_field_type(field.annotation), BaseModel):
                q_obj = get_wildcard_filter(
                    filter_elem=filter_elem, model=get_field_type(field.annotation)
                )
                wildcard_filter.append(q_obj)
            elif (
                get_field_type(field.annotation) is str
                and get_sub_fields(field) is None
                and name not in ["possible_actions"]
            ):
                q_obj = Q(**{f"{field_source}__icontains": filter_elem.v[0]})
                wildcard_filter.append(q_obj)
    return functools.reduce(lambda filter1, filter2: filter1 | filter2, wildcard_filter)


def get_embedded_field(fields: list[Any], model: type[BaseModel]):
    """
    Returns the embedded field to filter by. For instance we can obtain 'flowchart_group.name' filter clause
    from the client which means that we want to filter by the name property in the flowchart_group nested model.

    Args:
        fields (list[Any]): A list of fields representing the nesting of the desired field.
        model (type[BaseModel]): The model to search for the nested field.

    Returns:
        ModelField | Any | None: The nested field to filter by.

    Raises:
        ValidationException: If the supplied value for 'field_name' is not valid.
    """
    if len(fields) == 1:
        return model.model_fields.get(fields[0])
    for field in fields:
        ValidationException.raise_if(
            len(field.strip()) == 0,
            msg="Supplied value for 'field_name' is not valid. Example valid value is: 'field.sub_field'.",
        )

    try:
        field_model = get_field_type(model.model_fields.get(fields[0]).annotation)
        return get_embedded_field(fields[1:], model=field_model)
    except AttributeError as _ex:
        raise ValidationException(
            msg=f"{fields[0]}.{fields[1]} is not a valid field"
        ) from _ex


def get_field(prop, model):
    # if property is a nested property, for instance flowchartGroup.name we have to get underlying
    # 'name' property to filter by.
    if "." in prop:
        field = get_embedded_field(fields=prop.split("."), model=model)
    else:
        field = model.model_fields.get(prop)

    ValidationException.raise_if_not(field, msg=f"Field '{prop}' is not supported")

    return field


def get_field_path(prop, field):
    jse = field.json_schema_extra or {}
    source = jse.get("source")
    if source is not None:
        if isinstance(source, dict):
            source = source["path"]
        if "." in source:
            field_name = source.replace(".", "__")
        else:
            field_name = source
    else:
        field_name = prop
    return field_name


def is_injected_field(field) -> bool:
    jse = field.json_schema_extra or {}
    source = jse.get("source")
    if source is None:
        return False
    if isinstance(source, dict):
        return source.get("injected", False)
    return False


def get_order_by_clause(
    sort_by: dict[str, bool] | None, model: type[BaseModel]
) -> list[str]:
    sort_paths = []
    if sort_by:
        for key, value in sort_by.items():
            path = get_field_path(prop=key, field=get_field(prop=key, model=model))
            if value is False:
                path = f"-{path}"
            sort_paths.append(path)
    return sort_paths


def merge_q_query_filters(*args, filter_operator: "FilterOperator"):
    if filter_operator == FilterOperator.AND and args:
        return functools.reduce(lambda filter1, filter2: filter1 & filter2, args)
    if filter_operator == FilterOperator.OR and args:
        return functools.reduce(lambda filter1, filter2: filter1 | filter2, args)
    return args


def get_versioning_q_filter(filter_elem, field: str, q_filters: list[Any]):
    neomodel_filter = comparison_operator_to_neomodel.get(filter_elem.op)
    if neomodel_filter is None:
        raise AttributeError(
            f"The following operator {filter_elem.op} is not mapped to the neomodel operators."
        )
    name = field.split("|")[1]
    q_filters.append(
        Q(**{f"has_version|{name}{neomodel_filter}": f"{filter_elem.v[0]}"})
    )


def get_version_properties_sources() -> list[Any]:
    result = []
    for field in VersionProperties.model_fields.values():
        if field.json_schema_extra:
            source = field.json_schema_extra.get("source")
            if source is not None:
                result.append(source["path"])  # type: ignore[call-overload,index]
    return result


def validate_sort_by_dict(sort_by: dict[str, bool] | None | str):
    # Accept an empty string as an empty dictionary
    if sort_by == "":
        sort_by = {}

    ValidationException.raise_if(
        sort_by is not None and not isinstance(sort_by, dict),
        msg=f"Invalid sort_by object provided: '{sort_by}', it must be a dict",
    )

    # Validate keys to prevent Cypher injection
    if sort_by:
        for key in sort_by:
            if key != "size(name)" and not filter_sort_valid_keys_re.fullmatch(key):
                raise ValidationException(msg=f"Invalid sorting key: {key}")

    return sort_by


def validate_filter_by_dict(filter_by: dict[str, Any] | str | None):
    # Accept an empty string as an empty dictionary
    if filter_by == "":
        filter_by = {}

    ValidationException.raise_if(
        filter_by is not None and not isinstance(filter_by, dict),
        msg=f"Invalid filter_by object provided: '{filter_by}', it must be a dict",
    )

    # Validate keys to prevent Cypher injection
    if filter_by:
        for key in filter_by:
            if key != "*" and not filter_sort_valid_keys_re.fullmatch(key):
                raise ValidationException(msg=f"Invalid filter key: {key}")

    return filter_by


def validate_filters_and_add_search_string(
    search_string: str, field_name: str, filter_by: dict[str, dict[str, Any]] | None
):
    filter_by = validate_filter_by_dict(filter_by)
    if search_string != "":
        if filter_by is None:
            filter_by = {}
        filter_by[field_name] = {
            "v": [search_string],
            "op": ComparisonOperator.CONTAINS,
        }
    return filter_by


def transform_filters_into_neomodel(
    filter_by: dict[str, dict[str, Any]] | None, model: type[BaseModel]
):
    q_filters = []
    filters = FilterDict.model_validate({"elements": filter_by})
    for prop, filter_elem in filters.elements.items():
        if prop == "*":
            q_filters.append(get_wildcard_filter(filter_elem=filter_elem, model=model))
        else:
            field = get_field(prop=prop, model=model)
            if field is not None:
                field_name = get_field_path(prop=prop, field=field)
                model_sources = get_version_properties_sources()
                if field_name in model_sources:
                    get_versioning_q_filter(
                        filter_elem=filter_elem, field=field_name, q_filters=q_filters
                    )
                    continue

                # get the list of possible filters for a given field type
                possible_filters = data_type_filters.get(
                    get_field_type(field.annotation)
                )

                # if possible filter list is None it means that data type of the filter field is not listed
                # in the data_type_filters configuration
                if possible_filters is None:
                    raise AttributeError(
                        f"Passed not supported data type {get_field_type(field.annotation)}"
                    )
                if filter_elem.op not in possible_filters:
                    raise AttributeError(
                        f"The following filtering type {filter_elem.op.name} is not supported for the following data type {get_field_type(field.annotation)}."
                    )
                if len(filter_elem.v) == 1:
                    neomodel_filter = comparison_operator_to_neomodel.get(
                        filter_elem.op
                    )
                    if neomodel_filter is None:
                        raise AttributeError(
                            f"The following operator {filter_elem.op} is not mapped to the neomodel operators."
                        )
                    filter_name = f"{field_name}{neomodel_filter}"
                    filter_value = filter_elem.v[0]
                    if isinstance(filter_value, str) and is_date(filter_value):
                        filter_value = f"datetime({filter_value})"
                    q_filters.append(Q(**{filter_name: filter_value}))
                else:
                    if filter_elem.op == ComparisonOperator.BETWEEN:
                        filter_elem.v.sort()
                        filter_values = filter_elem.v
                        min_bound = f"{field_name}__gt"
                        max_bound = f"{field_name}__lt"
                        min_bound_value = filter_values[0]
                        max_bound_value = filter_values[1]
                        if isinstance(min_bound_value, str) and is_date(
                            min_bound_value
                        ):
                            min_bound_value = f"datetime({min_bound_value})"
                        q_filters.append(Q(**{min_bound: min_bound_value}))
                        if isinstance(max_bound_value, str) and is_date(
                            max_bound_value
                        ):
                            max_bound_value = f"datetime({max_bound_value})"
                        q_filters.append(Q(**{max_bound: max_bound_value}))
                    elif filter_elem.op == ComparisonOperator.EQUALS:
                        neomodel_filter = comparison_operator_to_neomodel.get(
                            ComparisonOperator.IN
                        )
                        filter_name = f"{field_name}{neomodel_filter}"
                        filter_value = filter_elem.v
                        q_filters.append(Q(**{filter_name: filter_value}))
                    elif filter_elem.op == ComparisonOperator.NOT_EQUALS:
                        neomodel_filter = comparison_operator_to_neomodel.get(
                            ComparisonOperator.NOT_EQUALS
                        )
                        filter_name = f"{field_name}{neomodel_filter}"
                        filter_value = filter_elem.v
                        for f_val in filter_value:
                            q_filters.append(Q(**{filter_name: f_val}))
                    else:
                        raise AttributeError(
                            f"Not valid operator {filter_elem.op.value} for the following property {prop} of type"
                            f"{type(prop)}"
                        )
            else:
                raise AttributeError("Passed wrong filter field name")
    return q_filters


def is_date(string):
    try:
        # changing into isoparse instead of parse as
        # parse was interpreting for instance '1.0' as date
        # and '1.0' is commonly used value in version filtering
        isoparse(string)
        return True
    except ValueError:
        return False


class GenericFilteringReturn:
    def __init__(self, items: list[Any], total: int):
        self.items = items
        self.total = total


class FilterOperator(Enum):
    AND = "and"
    OR = "or"

    @staticmethod
    def from_str(label):
        if label in ("or", "OR"):
            return FilterOperator.OR
        if label in ("and", "AND"):
            return FilterOperator.AND
        raise ValidationException(
            msg="Filter operator only accepts values of 'and' and 'or'."
        )


class FilterDictElement(BaseModel, Generic[T]):
    v: Annotated[
        list[T],
        Field(
            description="List of values to use as search values. Can be of any type.",
        ),
    ]
    op: Annotated[
        ComparisonOperator | None,
        Field(
            description="Comparison operator from enum, for operations like =, >=, or <"
        ),
    ] = ComparisonOperator.EQUALS

    @field_validator("op", mode="before")
    @classmethod
    def _is_op_supported(cls, val):
        try:
            return ComparisonOperator(val)
        except Exception as exc:
            raise ValidationException(
                msg=f"Unsupported comparison operator: '{val}'"
            ) from exc


class FilterDict(BaseModel):
    elements: Annotated[
        dict[str, FilterDictElement],
        Field(
            description="Filters description, with key being the alias to filter against, and value is a description object with search values and comparison operator"
        ),
    ]

    @field_validator("elements", mode="before")
    @classmethod
    def _none_as_empty_dict(cls, val):
        if val is None:
            return {}
        return val

    @field_validator("elements")
    @classmethod
    def _validate_keys(cls, val: dict[str, FilterDictElement]):
        """Restricts the characters allowed in filter keys to prevent Cypher query injection"""

        for key in val:
            if key != "*" and not filter_sort_valid_keys_re.fullmatch(key):
                raise ValidationException(msg=f"Invalid filter key: {key}")
        return val


class CypherQueryBuilder:
    """
    This class builds two queries : items and total_count with filtering and pagination capabilities.
    Important note : To provide the filtering and sorting capabilities, this class
    relies on the use of Cypher aliases. Please read the 'Mandatory inputs' section carefully.

    Mandatory inputs :
        match_clause : Basically everything a Cypher query needs to do before a
            RETURN statement : MATCH a pattern, CALL a procedure/subquery, do a WITH processing...
            Note, though, filtering, sorting and pagination will be added
            automatically by the class methods.
        alias_clause : Cypher aliases definition clause ; Similar to what you would
            write in your RETURN statement, but without the RETURN keyword.
            This is processed to set variables on which to apply filtering and sorting.

    Optional inputs :
        sort_by: dictionary of Cypher aliases on which to apply sorting as keys, and
            boolean to define sort direction (true=ascending) as values.
        implicit_sort_by: an alias on which to apply sorting, after the aliases given in
            sort_by are applied. Used to ensure a stable order when just sort_by is not sufficient.
        page_number : int, number of the page to return. 1-based (will be converted
            to 0-based for Cypher by class methods).
        page_size : int, number of results per page
        filter_by : dict, keys are field names for filter_variable and values are
            objects describing the filtering to execute
            * v = list of values to filter against
            * op = filter operator. Expected values : eq, co (contains), ge, gt, le, lt
            Example : { "name" : { "v": ["Jimbo"], "op": "co" }}
        return_model : (class) / wildcard_properties_list (list of strings).
            When a wildcard filtering is requested, we need to extract the list of
            known properties on which to apply filter. This can be done automatically
            from the return model definition ; in some more complex cases
            (e.g. aggregated object with many nested objects), the list cannot be
            extracted directly from the model definition, and has to be provided to this method.
        format_filter_sort_keys: Callable. In some cases, the returned model property
            keys differ from the property keys defined in the database.
            To cover these cases, a conversion function can be provided.

    Output properties :
        full_query : Complete cypher query with all clauses. See build_full_query
            method definition for more details.
        count_query : Cypher query with match, filter clauses, and results count. See
            build_count_query method definition for more details.
        parameters : Parameters object to pass along with the cypher query.

    Internal properties :
        filter_clause : str - Generated on class init ; adds filtering on aliases as
            defined in the filter_by dictionary.
        sort_clause : str - Generated on class init ; adds sorting on aliases as
            defined in the sort_by dictionary.
        pagination_clause : str - Generated on class init ; adds pagination.
    """

    def __init__(
        self,
        match_clause: str,
        alias_clause: str,
        page_number: int = 1,
        page_size: int = 0,
        sort_by: dict[str, bool] | None = None,
        implicit_sort_by: str | None = None,
        filter_by: FilterDict | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        return_model: type | None = None,
        wildcard_properties_list: list[str] | None = None,
        format_filter_sort_keys: Callable | None = None,
        union_match_clause: str | None = None,
        one_element_extra: bool = False,
    ):
        if wildcard_properties_list is None:
            wildcard_properties_list = []

        self.match_clause = match_clause
        self.alias_clause = alias_clause
        self.union_match_clause = union_match_clause
        self.sort_by = sort_by if sort_by is not None else {}
        self.implicit_sort_by = implicit_sort_by
        self.page_number = page_number
        self.page_size = page_size
        self.one_element_extra = one_element_extra
        self.filter_by = filter_by
        self.filter_operator = filter_operator
        self.total_count = total_count
        self.return_model = return_model
        self.wildcard_properties_list = wildcard_properties_list
        self.format_filter_sort_keys = format_filter_sort_keys
        self.filter_clause = ""
        self.sort_clause = ""
        self.pagination_clause = ""
        self.parameters: dict[Any, Any] = {}

        # Auto-generate internal clauses
        if filter_by is not None:
            filter_by.elements = validate_filter_by_dict(filter_by=filter_by.elements)

        if filter_by and len(self.filter_by.elements) > 0:
            self.build_filter_clause()
        if self.page_size > 0:
            self.build_pagination_clause()
        if self.sort_by:
            self.sort_by = validate_sort_by_dict(sort_by=self.sort_by)
            self.build_sort_clause()

        # Auto-generate final queries
        self.build_full_query()
        self.build_count_query()

    def _handle_nested_base_model_filtering(
        self,
        _predicates: list[str],
        _alias: str,
        _parsed_operator: str,
        _query_param_name: str,
        elm: Any,
    ):
        if elm is not None:
            if isinstance(elm, str):
                elm = elm.lower()
            self.parameters[f"{_query_param_name}"] = elm

        if "." in _alias:
            nested_path = _alias.split(".")
            attr_desc = self.return_model.model_fields.get(nested_path[0])
            path = nested_path[0]
            _alias = nested_path[-1]
            nested_path = nested_path[1:-1]
            # Each returned row has a field that starts with the specified filter value
            for traversal in nested_path:
                attr_desc = get_field_type(attr_desc.annotation).model_fields.get(
                    traversal
                )
                path = traversal

            if get_sub_fields(attr_desc) is None:
                # Need to get the nested field descriptor to check its type
                # attr_desc at this point refers to the parent list field (e.g., activity_instance_classes)
                # We need to get the field descriptor for the actual field we're filtering on
                parent_field_type = get_field_type(attr_desc.annotation)
                if hasattr(parent_field_type, "model_fields"):
                    nested_field_desc = parent_field_type.model_fields.get(_alias)
                    field_type = (
                        get_field_type(nested_field_desc.annotation)
                        if nested_field_desc
                        else None
                    )

                    # Check if field is a string type - if so, apply toLower()
                    if field_type is str:
                        _predicates.append(
                            f"toLower({path}.{_alias}){_parsed_operator}${_query_param_name}"
                        )
                    else:
                        # For non-string types (bool, int, etc.), don't use toLower()
                        _predicates.append(
                            f"{path}.{_alias}{_parsed_operator}${_query_param_name}"
                        )
                else:
                    # Fallback to original behavior if we can't determine the type
                    _predicates.append(
                        f"toLower({path}.{_alias}){_parsed_operator}${_query_param_name}"
                    )
            else:
                # Special handling for activity_groupings fields that map to nested structure
                # activity_group_name -> activity_group.name
                # activity_subgroup_name -> activity_subgroup.name
                if elm is None:
                    _predicates.append(f"size({path}) = 0 ")
                elif path == "activity_groupings" and _alias == "activity_group_name":
                    _predicates.append(
                        f"any(attr in {path} WHERE toLower(attr.activity_group.name) {_parsed_operator} ${_query_param_name})"
                    )
                elif (
                    path == "activity_groupings" and _alias == "activity_subgroup_name"
                ):
                    _predicates.append(
                        f"any(attr in {path} WHERE toLower(attr.activity_subgroup.name) {_parsed_operator} ${_query_param_name})"
                    )
                else:
                    # Default behavior for other array fields - check field type first
                    # Get the element type of the list
                    list_element_type = get_field_type(attr_desc.annotation)
                    if hasattr(list_element_type, "model_fields"):
                        nested_field_desc = list_element_type.model_fields.get(_alias)
                        field_type = (
                            get_field_type(nested_field_desc.annotation)
                            if nested_field_desc
                            else None
                        )

                        if field_type is str:
                            _predicates.append(
                                f"any(attr in {path} WHERE toLower(attr.{_alias}) {_parsed_operator} ${_query_param_name})"
                            )
                        else:
                            # For non-string types, don't use toLower()
                            _predicates.append(
                                f"any(attr in {path} WHERE attr.{_alias} {_parsed_operator} ${_query_param_name})"
                            )
                    else:
                        # Fallback to original behavior
                        _predicates.append(
                            f"any(attr in {path} WHERE toLower(attr.{_alias}) {_parsed_operator} ${_query_param_name})"
                        )
        else:
            attr_desc = self.return_model.model_fields.get(_alias)
            if get_sub_fields(attr_desc) is None:
                _predicates.append(
                    f"toLower({_alias}.name){_parsed_operator}${_query_param_name}"
                )
            else:
                if elm is None:
                    _predicates.append(f"size({_alias}) = 0 ")
                else:
                    _predicates.append(
                        f"any(attr in {_alias} WHERE toLower(attr.name) {_parsed_operator} ${_query_param_name})"
                    )

    # pylint: disable=too-many-statements
    def build_filter_clause(self) -> None:
        _filter_clause = "WHERE "
        filter_predicates = []

        for key in self.filter_by.elements:
            _alias = key
            if key != "*" and not filter_sort_valid_keys_re.fullmatch(key):
                raise ValueError(f"Invalid filter key: {key}")
            _values = self.filter_by.elements[key].v
            _operator = self.filter_by.elements[key].op
            _predicates = []
            _predicate_operator = " OR "
            _parsed_operator = "="

            if _alias == "*":
                # Parse operator to use in filter for wildcard
                _parsed_operator = " CONTAINS "
                # Only accept requests with default operator (set to equal by FilterDict class) or specified contains operator
                ValidationException.raise_if(
                    ComparisonOperator(_operator) != ComparisonOperator.EQUALS
                    and ComparisonOperator(_operator) != ComparisonOperator.CONTAINS,
                    msg="Only the default 'contains' operator is supported for wildcard filtering.",
                )
            else:
                # Parse operator to use in filter for the current label
                if ComparisonOperator(_operator) == ComparisonOperator.CONTAINS:
                    _parsed_operator = " CONTAINS "
                elif ComparisonOperator(_operator) == ComparisonOperator.NOT_EQUALS:
                    _predicate_operator = " AND "
                    _parsed_operator = "<>"
                elif ComparisonOperator(_operator) == ComparisonOperator.GREATER_THAN:
                    _parsed_operator = ">"
                elif (
                    ComparisonOperator(_operator)
                    == ComparisonOperator.GREATER_THAN_OR_EQUAL_TO
                ):
                    _parsed_operator = ">="
                elif ComparisonOperator(_operator) == ComparisonOperator.LESS_THAN:
                    _parsed_operator = "<"
                elif (
                    ComparisonOperator(_operator)
                    == ComparisonOperator.LESS_THAN_OR_EQUAL_TO
                ):
                    _parsed_operator = "<="

            # Parse filter clauses for the current label
            # 'Between' operator works differently from the others
            if ComparisonOperator(_operator) == ComparisonOperator.BETWEEN:
                ValidationException.raise_if(
                    len(_values) != 2,
                    msg="For between operator to work, exactly 2 values must be provided",
                )

                ValidationException.raise_if(
                    _alias == "*",
                    msg="Between operator not supported with wildcard filtering",
                )

                # If necessary, replace key using return-model-to-cypher fieldname mapping
                if self.format_filter_sort_keys:
                    _alias = self.format_filter_sort_keys(_alias)
                    if not filter_sort_valid_keys_re.fullmatch(key):
                        raise ValueError(f"Invalid filter key: {key}")
                _values.sort()
                _query_param_prefix = f"{self.escape_alias(_alias)}"
                _predicate = (
                    f"${_query_param_prefix}_0<={_alias}<=${_query_param_prefix}_1"
                )
                # If the provided value can be parsed as a date, also add a predicate with a datetime casting on the Neo4j side
                if is_date(_values[0]) and is_date(_values[1]):
                    _date_predicate = f"datetime(${_query_param_prefix}_0)<={_alias}<=datetime(${_query_param_prefix}_1)"
                    _predicate += f" OR {_date_predicate}"
                filter_predicates.append(_predicate)
                self.parameters[f"{_query_param_prefix}_0"] = _values[0]
                self.parameters[f"{_query_param_prefix}_1"] = _values[1]
            else:
                # If necessary, replace key using return-model-to-cypher fieldname mapping
                if self.format_filter_sort_keys and _alias != "*":
                    _alias = self.format_filter_sort_keys(_alias)
                    if not filter_sort_valid_keys_re.fullmatch(key):
                        raise ValueError(f"Invalid filter key: {key}")
                # An empty _values list means that the returned item's property value should be null
                if len(_values) == 0:
                    ValidationException.raise_if(
                        _alias == "*",
                        msg="Wildcard filtering not supported with null values",
                    )
                    _predicates.append(f"{_alias} IS NULL")
                else:
                    for index, elm in enumerate(_values):
                        # If filter is a wildcard
                        if _alias == "*":
                            # Wildcard filtering only accepts a search value of type string

                            ValidationException.raise_if_not(
                                isinstance(elm, str),
                                msg="Wildcard filtering only supports a search value of type string",
                            )

                            # If a list of wildcard properties is provided, use it
                            if len(self.wildcard_properties_list) > 0:
                                for db_property in self.wildcard_properties_list:
                                    _predicates.append(
                                        f"toLower({db_property}){_parsed_operator}$wildcard_{index}"
                                    )
                            # If not, then extract list of properties from return model
                            elif self.return_model:
                                for (
                                    attribute,
                                    attr_desc,
                                ) in self.return_model.model_fields.items():
                                    # Skip fields explicitly excluded from wildcard filtering
                                    jse = attr_desc.json_schema_extra or {}
                                    if jse.get("remove_from_wildcard", False):
                                        continue
                                    # Wildcard filtering only searches in properties of type string
                                    if (
                                        get_field_type(attr_desc.annotation) is str
                                        # and field is not a list [str]
                                        and get_sub_fields(attr_desc) is None
                                    ):
                                        # name=$name_0 with name_0 defined in parameter objects
                                        if self.format_filter_sort_keys:
                                            attribute = self.format_filter_sort_keys(
                                                attribute
                                            )
                                        _predicates.append(
                                            f"toLower({attribute}){_parsed_operator}$wildcard_{index}"
                                        )
                                    # if field is list[str]: case-insensitive substring match on each element
                                    elif (
                                        get_sub_fields(attr_desc) is not None
                                        and get_field_type(attr_desc.annotation) is str
                                        and attribute not in ["possible_actions"]
                                    ):
                                        _predicates.append(
                                            f"ANY(x IN {attribute} WHERE toLower(x){_parsed_operator}$wildcard_{index})"
                                        )
                                    # Wildcard filtering for SimpleTermModel
                                    elif (
                                        get_field_type(attr_desc.annotation)
                                        is SimpleTermModel
                                    ):
                                        # name=$name_0 with name_0 defined in parameter objects
                                        if self.format_filter_sort_keys:
                                            attribute = self.format_filter_sort_keys(
                                                attribute
                                            )
                                        if get_sub_fields(attr_desc) is None:
                                            # if field is just SimpleTermModel compare wildcard filter
                                            # with name property of SimpleTermModel
                                            _predicates.append(
                                                f"toLower({attribute}.name){_parsed_operator}$wildcard_{index}"
                                            )
                                        else:
                                            # if field is an array of SimpleTermModels
                                            _predicates.append(
                                                f"$wildcard_{index} IN [attr in {attribute} | toLower(attr.name)]"
                                            )
                                    # Wildcard filtering for SimpleDictionaryTermModel
                                    elif (
                                        get_field_type(attr_desc.annotation)
                                        is SimpleDictionaryTermModel
                                    ):
                                        # name=$name_0 with name_0 defined in parameter objects
                                        if self.format_filter_sort_keys:
                                            attribute = self.format_filter_sort_keys(
                                                attribute
                                            )
                                        if get_sub_fields(attr_desc) is None:
                                            # if field is just SimpleDictionaryTermModel compare wildcard filter
                                            # with `name` or `dictionary_id` property of SimpleDictionaryTermModel
                                            _predicates.append(
                                                f"toLower({attribute}.name){_parsed_operator}$wildcard_{index}"
                                            )
                                            _predicates.append(
                                                f"toLower({attribute}.dictionary_id){_parsed_operator}$wildcard_{index}"
                                            )
                                        else:
                                            # if field is an array of SimpleDictionaryTermModel
                                            _predicates.append(
                                                f"$wildcard_{index} IN [attr in {attribute} | toLower(attr.name)]"
                                            )
                                            _predicates.append(
                                                f"$wildcard_{index} IN [attr in {attribute} | toLower(attr.dictionary_id)]"
                                            )
                                    elif (
                                        get_field_type(attr_desc.annotation)
                                        is ActivityGroupingHierarchySimpleModel
                                    ):
                                        _predicates.append(
                                            f"any(attr in {attribute} WHERE toLower(attr.activity_group.name) {_parsed_operator} $wildcard_{index})"
                                        )
                                        _predicates.append(
                                            f"any(attr in {attribute} WHERE toLower(attr.activity_subgroup.name) {_parsed_operator} $wildcard_{index})"
                                        )
                                    elif (
                                        get_field_type(attr_desc.annotation)
                                        is CompactActivityInstanceClassForActivityItemClass
                                    ):
                                        # Wildcard filtering for activity_instance_classes
                                        # Search in the name field of each activity instance class
                                        _predicates.append(
                                            f"any(attr in {attribute} WHERE toLower(attr.name) {_parsed_operator} $wildcard_{index})"
                                        )
                                    elif (
                                        get_field_type(attr_desc.annotation)
                                        is OdmTranslatedTextModel
                                    ):
                                        _predicates.append(
                                            f"any(attr in {attribute} WHERE toLower(attr.name) {_parsed_operator} $wildcard_{index})"
                                        )
                                        _predicates.append(
                                            f"any(attr in {attribute} WHERE toLower(attr.description) {_parsed_operator} $wildcard_{index})"
                                        )
                                        _predicates.append(
                                            f"any(attr in {attribute} WHERE toLower(attr.instruction) {_parsed_operator} $wildcard_{index})"
                                        )
                                        _predicates.append(
                                            f"any(attr in {attribute} WHERE toLower(attr.sponsor_instruction) {_parsed_operator} $wildcard_{index})"
                                        )
                                    elif (
                                        get_field_type(attr_desc.annotation)
                                        is OdmAliasModel
                                    ):
                                        _predicates.append(
                                            f"any(attr in {attribute} WHERE toLower(attr.name) {_parsed_operator} $wildcard_{index})"
                                        )
                                        _predicates.append(
                                            f"any(attr in {attribute} WHERE toLower(attr.context) {_parsed_operator} $wildcard_{index})"
                                        )
                            # If none are provided, raise an exception
                            else:
                                raise ValidationException(
                                    msg="Wildcard filtering not properly covered for this object"
                                )
                            self.parameters[f"wildcard_{index}"] = elm.lower()
                        else:
                            # name=$name_0 with name_0 defined in parameter objects
                            # . for nested properties will be replaced by _
                            _query_param_name = f"{self.escape_alias(_alias)}_{index}"
                            if "." in _alias:
                                real_alias = _alias.split(".")[0]
                            else:
                                real_alias = _alias
                            jse = (
                                self.return_model.model_fields.get(
                                    _alias
                                ).json_schema_extra
                                or {}
                                if self.return_model
                                and hasattr(self.return_model, "model_fields")
                                and self.return_model.model_fields.get(_alias)
                                else {}
                            )
                            if (
                                self.return_model
                                and issubclass(self.return_model, BaseModel)
                                and self.return_model.model_fields.get(real_alias)
                                and issubclass(
                                    get_field_type(
                                        self.return_model.model_fields.get(
                                            real_alias
                                        ).annotation
                                    ),
                                    BaseModel,
                                )
                            ):
                                self._handle_nested_base_model_filtering(
                                    _predicates=_predicates,
                                    _alias=_alias,
                                    _parsed_operator=_parsed_operator,
                                    _query_param_name=_query_param_name,
                                    elm=elm,
                                )
                            elif (
                                # pylint: disable=too-many-boolean-expressions
                                self.return_model
                                and issubclass(self.return_model, BaseModel)
                                and self.return_model.model_fields.get(_alias)
                                and get_sub_fields(
                                    self.return_model.model_fields[_alias]
                                )
                                is not None
                                and get_field_type(
                                    self.return_model.model_fields.get(
                                        _alias
                                    ).annotation
                                )
                                is str
                                and not jse.get("is_json", False)
                            ):
                                _predicates.append(f"${_query_param_name} IN {_alias}")
                                self.parameters[_query_param_name] = elm
                            elif (
                                isinstance(elm, str)
                                and ComparisonOperator(_operator)
                                == ComparisonOperator.CONTAINS
                            ):
                                _predicates.append(
                                    f"toLower(toString({_alias})){_parsed_operator}${_query_param_name}"
                                )
                                self.parameters[f"{_query_param_name}"] = elm.lower()
                            else:
                                _predicates.append(
                                    f"{_alias}{_parsed_operator}${_query_param_name}"
                                )
                                # If the provided value is a string that can be parsed as a date,
                                # also add a predicate with a datetime casting on the Neo4j side
                                # It is necessary to check if it is a string because the value could also be a boolean here
                                if isinstance(elm, str) and is_date(elm):
                                    _predicates.append(
                                        f"{_alias}{_parsed_operator}datetime(${_query_param_name})"
                                    )
                                self.parameters[_query_param_name] = elm

                # If multiple values, will create a clause with OR or AND, between ()
                _predicate = _predicate_operator.join(_predicates)
                if len(_values) > 1 or _alias == "*":
                    _predicate = f"({_predicate})"

                # Add to list of predicates
                filter_predicates.append(_predicate)

        # Set clause
        self.filter_clause = (
            _filter_clause
            + f" {self.filter_operator.value.upper()} ".join(list(filter_predicates))
        )

    def build_pagination_clause(self) -> None:
        validate_max_skip_clause(page_number=self.page_number, page_size=self.page_size)

        # Set clause
        self.pagination_clause = "SKIP $skip_number LIMIT $limit_number"

        # Add corresponding parameters
        self.parameters["skip_number"] = (self.page_number - 1) * self.page_size
        self.parameters["limit_number"] = (
            self.page_size + 1 if self.one_element_extra else self.page_size
        )

    def build_sort_clause(self) -> None:
        _sort_clause = "ORDER BY "
        # Add list of order by statements parsed from dict
        # If necessary, replace key using return-model-to-cypher fieldname mapping
        sort_by_statements = []
        for key, value in self.sort_by.items():
            if value:
                sort_order = " ASC"
            else:
                sort_order = " DESC"
            if self.format_filter_sort_keys:
                key = self.format_filter_sort_keys(key)
            if self.return_model and issubclass(self.return_model, BaseModel):
                attr_desc = self.return_model.model_fields.get(key)
                # if property is of string type we should apply toLower() to sort
                if (
                    attr_desc
                    and get_field_type(attr_desc.annotation) is str
                    and get_sub_fields(attr_desc) is None
                ):
                    key = f"toLower({key})"
            sort_by_statements.append(key + sort_order)

        if (
            self.implicit_sort_by is not None
            and self.implicit_sort_by not in self.sort_by
        ):
            sort_by_statements.append(
                self.format_filter_sort_keys(self.implicit_sort_by)
                if self.format_filter_sort_keys
                else self.implicit_sort_by
            )
        # Set clause
        self.sort_clause = _sort_clause + ",".join(sort_by_statements)

    def build_full_query(self) -> None:
        """
        The generated query will have the following pattern :
            MATCH caller-provided (and WITH, CALL, ... any custom pattern matching necessary)
            > WITH alias_clause caller-provided
            > WHERE filter_clause using aliases
            > RETURN * to return results as is
            > ORDER BY to sort results using aliases
            > SKIP * LIMIT * to paginate results
        """
        _with_alias_clause = f"WITH {self.alias_clause}"
        _return_clause = "RETURN *"

        # Set clause
        self.full_query = " ".join(
            [
                self.match_clause,
                _with_alias_clause,
                self.filter_clause,
                _return_clause,
                self.sort_clause,
                self.pagination_clause,
            ]
        )
        if self.union_match_clause:
            self.full_query += " UNION "
            self.full_query += " ".join(
                [
                    self.union_match_clause,
                    _with_alias_clause,
                    self.filter_clause,
                    _return_clause,
                    self.sort_clause,
                    self.pagination_clause,
                ]
            )

    def build_count_query(self) -> None:
        """
        The generated query will have the following pattern :
            MATCH caller-provided (and WITH, CALL, ... any custom pattern matching necessary)
            > WITH alias_clause caller-provided
            > WHERE filter_clause using aliases
            > RETURN results count
        """
        _with_alias_clause = f"WITH {self.alias_clause}"
        _return_count_clause = "RETURN count(*) AS total_count"

        # Set clause
        if not self.union_match_clause:
            self.count_query = " ".join(
                [
                    self.match_clause,
                    _with_alias_clause,
                    self.filter_clause,
                    _return_count_clause,
                ]
            )
        else:
            self.count_query = " ".join(
                [
                    self.match_clause,
                    _with_alias_clause,
                    self.filter_clause,
                    _return_count_clause,
                    "UNION",
                    self.union_match_clause,
                    _with_alias_clause,
                    self.filter_clause,
                    _return_count_clause,
                ]
            )

    def build_header_query(self, header_alias: str, page_size: int) -> str:
        """
        Mandatory inputs :
            * header_alias - Alias of the header for which to get possible values, as defined in the alias clause
            * page_size - Number of results to return
        The generated query will have the following pattern :
            MATCH caller-provided (and WITH, CALL, ... any custom pattern matching necessary)
            > WITH alias_clause caller-provided
            > WHERE filter_clause using aliases
            > RETURN list of possible headers for given alias, ordered, with a limit
        """
        if not filter_sort_valid_keys_re.fullmatch(header_alias):
            raise ValidationException(msg=f"Invalid header: {header_alias}")

        _with_alias_clause = f"WITH {self.alias_clause}"

        # support header clause for nested properties
        _escaped_header_alias = self.escape_alias(header_alias)
        alias_clause = None
        if "." in header_alias:
            split = header_alias.split(".")
            first_property = split[0]
            last_property = split[-1]
            ValidationException.raise_if(
                first_property == "" or last_property == "",
                msg=f"Invalid field name: {header_alias}",
            )
            paths = split[1:-1]
            if self.return_model:
                attr_desc = self.return_model.model_fields.get(first_property)
                if attr_desc is not None:
                    attr_desc_name = first_property
                    for path in paths:
                        attr_desc = get_field_type(
                            attr_desc.annotation
                        ).model_fields.get(path)
                        attr_desc_name = path

                        ValidationException.raise_if_not(
                            attr_desc, msg=f"Invalid field name: {header_alias}"
                        )

                    if get_sub_fields(attr_desc) is not None:
                        if self.format_filter_sort_keys:
                            last_property = self.format_filter_sort_keys(last_property)

                        alias_clause = (
                            f"[attr in {attr_desc_name} | attr.{last_property}]"
                        )

        if not alias_clause:
            alias_clause = header_alias
        _return_header_clause = f"""WITH DISTINCT {alias_clause} AS
        {_escaped_header_alias} ORDER BY {_escaped_header_alias} LIMIT {page_size}
        RETURN apoc.coll.toSet(apoc.coll.flatten(collect(DISTINCT {_escaped_header_alias}))) AS values"""

        return " ".join(
            [
                self.match_clause,
                _with_alias_clause,
                self.filter_clause,
                _return_header_clause,
            ]
        )

    def escape_alias(self, alias: str) -> str:
        """
        Escapes alias to prevent Cypher failures.
            * Replaces . for nested properties by _
        """
        return re.sub(NESTED_REGEX, "_", alias)

    def execute(self) -> tuple[Any, Any]:
        try:
            result_array, attributes_names = db.cypher_query(
                query=self.full_query,
                params=self.parameters,
            )
        except CypherSyntaxError as ex:
            log.error("%s: %s", ex.code, ex.message)
            raise ValidationException(
                msg="Unsupported filters, sort_by or fields parameters or other syntax error in Cypher query"
            ) from ex
        return result_array, attributes_names


def cached_skip_on(skip_param: str, *, cache, key, lock=None):
    """
    Decorator equivalent to :func:`cachetools.cached`, but bypasses the cache
    (no read, no write) when the given parameter is truthy in the call.

    Used for repository methods like ``find_by_uid_2`` where a ``for_update=True``
    call must always execute the method body so that Neo4j write locks are
    actually taken in the current transaction. A cached result from a prior
    (already-committed) transaction would otherwise be returned without any
    lock being held.

    ``skip_param`` is matched against both keyword and positional arguments,
    resolved via ``inspect.signature.bind_partial``.
    """

    def decorator(function):
        sig = inspect.signature(function)
        cached_function = cached(cache=cache, key=key, lock=lock)(function)

        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            try:
                skip = sig.bind_partial(*args, **kwargs).arguments.get(skip_param)
            except TypeError:
                skip = False
            if skip:
                return function(*args, **kwargs)
            return cached_function(*args, **kwargs)

        return wrapper

    return decorator


def sb_clear_cache(caches: list[str] | None = None):
    """
    Decorator that will clear the specified caches after the wrapped function execution.
    """
    if caches is None:
        caches = []

    def decorator(function):
        @functools.wraps(function)
        def wrapper(self, *args, **kwargs):
            try:
                result = function(self, *args, **kwargs)
                return result
            finally:
                for cache_name in caches:
                    cache = getattr(self, cache_name, None)
                    if cache:
                        log.info(
                            "Clear cache '%s.%s' of size: %s",
                            type(self).__name__,
                            cache_name,
                            cache.currsize,
                        )
                        cache.clear()

        return wrapper

    return decorator


def calculate_total_count_from_query_result(
    result_count: int,
    page_number: int,
    page_size: int,
    total_count: bool,
    extra_requested: bool = False,
) -> int | None:
    """
    Given the number of results returned from a paginated query,
    calculate the total count of items if possible.
    """
    if not total_count:
        # Total count not requested, return 0
        return 0
    if page_size == 0 and page_number == 1:
        # All results requested in a single page
        return result_count
    if result_count == 0 and page_number > 1:
        # No results on a page beyond the first means there may be more results
        # but we cannot know how many
        return None
    if result_count < page_size:
        # Fewer results than page size implies this is the last page
        return (page_number - 1) * page_size + result_count
    if extra_requested and result_count == page_size:
        # We got a full page and no extra item, so we can assume this is the last page
        return page_number * page_size
    if extra_requested and result_count == page_size + 1:
        # More results than page size implies we requested one extra item to check for more
        return -1
    # Otherwise, we cannot determine the total count
    return None
