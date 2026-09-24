import json
import typing
from datetime import datetime, timezone
from typing import Annotated, Any, cast

from fastapi import Query
from pydantic import AfterValidator, BeforeValidator

from clinical_mdr_api.models.validators import FLOAT_REGEX
from common.config import settings
from common.models.error import ErrorResponse


def study_section_description(desc: str):
    return f"""
    Optionally specify a list of sections to {desc} from the StudyDefinition.

    Valid values are:

    - identification_metadata
    - registry_identifiers
    - version_metadata
    - high_level_study_design
    - study_population
    - study_intervention
    - study_description

    If no filters are specified, the default sections are returned."""


def study_fields_audit_trail_section_description(desc: str):
    return f"""
    Optionally specify a list of sections to {desc} from the StudyDefinition.

    Valid values are:

    - identification_metadata
    - registry_identifiers
    - version_metadata
    - high_level_study_design
    - study_population
    - study_intervention
    - study_description

    If no sections are specified, the whole audit trail is returned."""


LIBRARY_NAME = "Library name"


def _parse_json_validator(value: typing.Any) -> typing.Any:
    """
    Validator function that automatically parses JSON string to dict.
    Used with BeforeValidator to parse query parameters (filters, sort_by, etc.).
    """
    if value is None:
        return None
    if isinstance(value, dict):
        return value  # Already parsed
    if isinstance(value, str):
        if not value.strip():
            return None
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON format: {value}") from exc
        # Treat non-dict JSON payloads (e.g. `false`, `null`, a bare number)
        # as "no filter/sort" — the API-level contract requires a JSON object.
        if not isinstance(parsed, dict):
            return None
        return parsed
    raise ValueError(f"Invalid type: {type(value)}")


SORT_BY = """
JSON dictionary of field names and boolean flags specifying the sort order. Supported values for sort order are:
- `true` - ascending order\n
- `false` - descending order\n

Default: `{}` (no sorting).

Format: `{"field_1": true, "field_2": false, ...}`.

Functionality: Sorts the results by `field_1` with sort order indicated by its boolean value, then by `field_2` etc.

Example: `{"topic_code": true, "name": false}` sorts the returned list by `topic_code ascending`, then by `name descending`.
"""

# Base Query definition for sort_by (for OpenAPI schema)
_SORT_BY_QUERY_BASE = Query(description=SORT_BY)

# Reusable Query parameter for sort_by - automatically parses JSON string to dict
# Usage: sort_by: SORT_BY_QUERY = None
# The validator automatically parses the JSON string to a dict
# Note: Using Any as the type to work with FastAPI query parameters, validator converts to dict | None
SORT_BY_QUERY = Annotated[
    Any,
    BeforeValidator(_parse_json_validator),
    _SORT_BY_QUERY_BASE,
]

PAGE_NUMBER = """
Page number of the returned list of entities.\n
Functionality : provided together with `page_size`, selects a page to retrieve for paginated results.\n
Errors: `page_size` not provided, `page_number` must be equal or greater than 1.
"""

# Reusable Query parameter for page_number with maximum constraint
PAGE_NUMBER_QUERY = Annotated[
    int, Query(ge=1, le=settings.max_page_number, description=PAGE_NUMBER)
]

PAGE_SIZE = f"""
Number of items to be returned per page.\n
Default: {settings.default_page_size}\n
Functionality: Provided together with `page_number`, selects the number of results per page.\n
In case the value is set to `0`, all rows will be returned.\n
Errors: `page_number` not provided.
"""

# Reusable Query parameter for page_size with maximum constraint (allows page_size=0 for "all rows")
PAGE_SIZE_QUERY = Annotated[
    int, Query(ge=0, le=settings.max_page_size, description=PAGE_SIZE)
]

# Reusable Query parameter for page_size with minimum constraint of 1 (does not allow page_size=0)
PAGE_SIZE_QUERY_MIN_1 = Annotated[
    int, Query(ge=1, le=settings.max_page_size, description=PAGE_SIZE)
]

FILTERS = """
JSON dictionary of field names and search strings, with a choice of operators for building complex filtering queries.

Default: `{}` (no filtering).

Functionality: filters the queried entities based on the provided search strings and operators.

Format:
`{"field_name":{"v":["search_str_1", "search_str_1"], "op":"comparison_operator"}, "other_field_name":{...}}`

- `v` specifies the list of values to match against the specified `field_name` field\n
    - If multiple values are provided in the `v` list, a logical OR filtering operation will be performed using these values.

- `op` specifies the type of string match/comparison operation to perform on the specified `field_name` field. Supported values are:\n
    - `eq` (default, equals)\n
    - `ne` (not equals)\n
    - `co` (string contains)\n
    - `ge` (greater or equal to)\n
    - `gt` (greater than)\n
    - `le` (less or equal to)\n
    - `lt` (less than)\n
    - `bw` (between - exactly two values are required)\n
    - `in` (value in list).\n

Note that filtering can also be performed on non-string field types. 
For example, this works as filter on a boolean field: `{"is_global_standard": {"v": [false]}}`.\n

Wildcard filtering is also supported. To do this, provide `*` value for `field_name`, for example: `{"*":{"v":["search_string"]}}`.

Wildcard only supports string search (with implicit `contains` operator) on fields of type string.\n

Finally, you can filter on items that have an empty value for a field. To achieve this, set the value of `v` list to an empty array - `[]`.\n

Complex filtering example:\n
`{"name":{"v": ["Jimbo", "Jumbo"], "op": "co"}, "start_date": {"v": ["2021-04-01T12:00:00+00.000"], "op": "ge"}, "*":{"v": ["wildcard_search"], "op": "co"}}`

"""

FILTER_OPERATOR = (
    "Specifies which logical operation - `and` or `or` - should be used in case filtering is done on several fields.\n\n"
    "Default: `and` (all fields have to match their filter).\n\n"
    "Functionality: `and` will return entities having all filters matching, `or` will return entities with any matches.\n\n"
)

# Reusable Query parameter for operator
FILTER_OPERATOR_QUERY = Annotated[
    str, Query(description=FILTER_OPERATOR, pattern="^(and|or)$")
]

FILTERS_EXAMPLE = {
    "none": {
        "summary": "No Filters",
        "description": "No filters are applied.",
        "value": "{}",
    },
    "wildcard": {
        "summary": "Wildcard Filter",
        "description": "Apply a wildcard filter.",
        "value": """{"*":{ "v": [""], "op": "co"}}""",
    },
    "uid__contains": {
        "summary": "Partial Match on UID",
        "description": "Apply a filter to display records **containing** specified UIDs.",
        "value": """{"uid":{ "v": [""], "op": "co"}}""",
    },
    "uid": {
        "summary": "Exact Match on UID",
        "description": "Apply a filter to display only those records with **exact** matching UIDs.",
        "value": """{"uid":{ "v": [""], "op": "eq"}}""",
    },
    "name__contains": {
        "summary": "Partial Match on Name",
        "description": "Apply a filter to display records **containing** specified names.",
        "value": """{"name":{ "v": [""], "op": "co"}}""",
    },
    "name": {
        "summary": "Exact Match on Name",
        "description": "Apply a filter to display only those records with **exact** matching names.",
        "value": """{"name":{ "v": [""], "op": "eq"}}""",
    },
}

TOTAL_COUNT = (
    "Boolean flag to include the total count of entities in the response.\n\n"
    "Default: `false`\n\n"
    "Functionality: When set to `true`, returns the total number of entities that match the query.\n\n"
    "When combined with filters, the count reflects only the entities matching those filters.\n\n"
    "Note: This operation can be expensive for large datasets.\n\n"
    "Special case: A value of `-1` indicates that the exact count is unavailable due to performance constraints, "
    "but confirms that at least one more entity exists beyond the current page."
)


def _strict_bool_validator(value: Any) -> Any:
    """
    Validator that rejects integer-like boolean query parameters (e.g. `0`, `1`).

    FastAPI/Starlette coerce these into `bool`, which silently accepts values
    that are schema-violations for an OpenAPI `boolean`. This validator enforces
    the stricter, schema-accurate behavior: only `true`/`false` (case-insensitive)
    and the native Python `bool` are allowed.

    Used with ``BeforeValidator`` to harden boolean query parameters.
    """
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "false"):
            return lowered == "true"
    raise ValueError(
        "Invalid boolean value: must be 'true' or 'false' (case-insensitive)."
    )


# Reusable marker applying strict boolean validation to a query/path parameter.
# Include this alongside a ``fastapi.Query(...)`` inside an ``Annotated`` spec
# whenever the endpoint accepts a ``bool`` value from the URL, e.g.
#
#     flag: Annotated[bool, STRICT_BOOL_VALIDATOR, Query(description="...")] = False
#
# It rejects integer-like values such as ``?flag=0`` or ``?flag=1`` that
# FastAPI/Starlette would otherwise silently coerce into ``False``/``True``.
STRICT_BOOL_VALIDATOR = BeforeValidator(_strict_bool_validator)

# Reusable Query parameter for total_count
TOTAL_COUNT_QUERY = Annotated[
    bool, STRICT_BOOL_VALIDATOR, Query(description=TOTAL_COUNT)
]

INCLUDE_TS_PARAMETERS = (
    "If true, response includes Trial Summary parameter fields "
    "(reference, required_level, cardinality, notes, osb_field_name, "
    "semantic_data_type, response_codelist, response_dictionary_uids, "
    "valid_null_flavor_terms, osb_page_reference). Default is false to "
    "skip extra graph traversals and reduce payload size."
)
INCLUDE_TS_PARAMETERS_QUERY = Annotated[bool, Query(description=INCLUDE_TS_PARAMETERS)]

SELECTED_FIELDS = Annotated[
    str | None,
    Query(
        description="Return only the specified field(s) along with uid. "
        "Accepts a single field name or comma-separated field names (e.g., 'name' or 'name,status,version'). "
        "When provided, only uid and the specified fields will be returned in each item."
    ),
]
HEADER_FIELD_NAME = (
    "The field name for which to lookup possible values in the database.\n\n"
    "Functionality: searches for possible values (aka 'headers') of this field in the database."
    "Errors: invalid field name specified"
)
HEADER_FIELD_NAME_QUERY = Annotated[
    str, Query(description=HEADER_FIELD_NAME, min_length=1)
]

HEADER_SEARCH_STRING = """Optionally, a (part of the) text for a given field.
The query result will be values of the field that contain the provided search string."""
HEADER_SEARCH_STRING_QUERY = Annotated[str, Query(description=HEADER_SEARCH_STRING)]

HEADER_PAGE_SIZE = "Optionally, the number of results to return. Default = 10."
HEADER_PAGE_SIZE_QUERY = Annotated[int, Query(description=HEADER_PAGE_SIZE)]

HEADERS_QUERY_LITE = "Whether to use the lightweight implementation of this endpoint, which doesn't support `filters` and `operator` parameters."

EXPORT_FIELDS = """Comma-separated list of field names to include in the export.

When exporting to CSV, XML, or Excel formats, this parameter allows you to specify which fields to include in the export.
Supports nested fields using dot notation (e.g., 'dataset.uid', 'parent.name').

If not provided, default fields will be used as defined by the endpoint.

Example: 'uid,name,status,version' or 'uid,dataset.uid,dataset.name'
"""

EXPORT_FIELDS_QUERY = Annotated[
    str | None,
    Query(description=EXPORT_FIELDS),
]

DATA_EXPORTS_HEADER = """\n
Response format:\n
- In addition to retrieving data in JSON format (default behaviour), 
it is possible to request data to be returned in CSV, XML or Excel formats 
by sending the `Accept` http request header with one of the following values:
  - `text/csv`\n
  - `text/xml`\n
  - `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`\n
- To customize which fields are included in the export, use the `export_fields` query parameter 
with a comma-separated list of field names (e.g., `?export_fields=uid,name,status,version`).
Supports nested fields using dot notation (e.g., `dataset.uid`).
"""

STUDY_VALUE_VERSION_QUERY: Any = Query(
    description="""If specified, study data with specified version is returned.

    Only exact matches are considered. 

    E.g. 1, 2, 2.1, ...""",
    pattern=FLOAT_REGEX,
)

ERROR_400 = {
    "model": ErrorResponse,
    "description": "Bad Request",
}
ERROR_401 = {"model": ErrorResponse, "description": "Unauthorized"}
ERROR_403 = {"model": ErrorResponse, "description": "Forbidden"}
ERROR_404 = {"model": ErrorResponse, "description": "Entity not found"}
ERROR_409 = {
    "model": ErrorResponse,
    "description": "The request could not be completed due to a conflict with the current state of the target resource. "
    "This typically occurs when attempting to create or modify a resource that already exists or violates a uniqueness constraint.",
}


SYNTAX_FILTERS = FILTERS + """
If any provided search term for a given field name is other than a string type, then equal operator will automatically be applied overriding any provided operator.
"""


# Alias for backward compatibility - use _parse_json_validator instead
_parse_filters_validator = _parse_json_validator


# Base Query definitions (for OpenAPI schema)
_FILTERS_QUERY_BASE = Query(
    description=FILTERS,
    openapi_examples=cast("dict[str, Any]", FILTERS_EXAMPLE),
)

_SYNTAX_FILTERS_QUERY_BASE = Query(
    description=SYNTAX_FILTERS,
    openapi_examples=cast("dict[str, Any]", FILTERS_EXAMPLE),
)

# Reusable Query parameter for filters - automatically parses JSON string to dict
# Usage: filters: FILTERS_QUERY = None
# The validator automatically parses the JSON string to a dict
# Note: Using Any as the type to work with FastAPI query parameters, validator converts to dict | None
FILTERS_QUERY = Annotated[
    Any,
    BeforeValidator(_parse_filters_validator),
    _FILTERS_QUERY_BASE,
]

# Reusable Query parameter for syntax filters - automatically parses JSON string to dict
# Usage: filters: SYNTAX_FILTERS_QUERY = None
# The validator automatically parses the JSON string to a dict
# Note: Using Any as the type to work with FastAPI query parameters, validator converts to dict | None
SYNTAX_FILTERS_QUERY = Annotated[
    Any,
    BeforeValidator(_parse_filters_validator),
    _SYNTAX_FILTERS_QUERY_BASE,
]


def _normalize_datetime_to_utc(value: datetime | None) -> datetime | None:
    """Normalize a timezone-aware datetime to UTC.

    The Neo4j bolt driver rejects datetimes whose (epoch_seconds, nanos, offset)
    combination overflows int64 math — e.g. extreme years combined with large
    timezone offsets. Converting to UTC before the parameter reaches the driver
    is semantically lossless (Cypher's `datetime()` treats the value as an
    instant) and avoids the overflow.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        # Per existing router docs, tz-naive values are treated as UTC.
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


# Reusable Query parameter for `at_specified_date_time` / `at_specific_date_time`.
# Usage: at_specified_date_time: AT_SPECIFIC_DATE_TIME_QUERY = None
AT_SPECIFIC_DATE_TIME_QUERY = Annotated[
    datetime | None,
    AfterValidator(_normalize_datetime_to_utc),
]
