from fastapi import Query

from clinical_mdr_api.models.validators import FLOAT_REGEX
from common import config
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

SORT_BY = """
JSON dictionary of field names and boolean flags specifying the sort order. Supported values for sort order are:
- `true` - ascending order\n
- `false` - descending order\n

Default: `{}` (no sorting).

Format: `{"field_1": true, "field_2": false, ...}`.

Functionality: Sorts the results by `field_1` with sort order indicated by its boolean value, then by `field_2` etc.

Example: `{"topic_code": true, "name": false}` sorts the returned list by `topic_code ascending`, then by `name descending`.
"""

PAGE_NUMBER = """
Page number of the returned list of entities.\n
Functionality : provided together with `page_size`, selects a page to retrieve for paginated results.\n
Errors: `page_size` not provided, `page_number` must be equal or greater than 1.
"""

PAGE_SIZE = f"""
Number of items to be returned per page.\n
Default: {config.DEFAULT_PAGE_SIZE}\n
Functionality: Provided together with `page_number`, selects the number of results per page.\n
In case the value is set to `0`, all rows will be returned.\n
Errors: `page_number` not provided.
"""

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

FILTERS_EXAMPLE = {
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
    "none": {
        "summary": "No Filters",
        "description": "No filters are applied.",
        "value": {},
    },
}

TOTAL_COUNT = (
    "Boolean value specifying whether total count of entities should be included in the response.\n\n"
    "Functionality: retrieve total count of queried entities.\n\n"
)

HEADER_FIELD_NAME = (
    "The field name for which to lookup possible values in the database.\n\n"
    "Functionality: searches for possible values (aka 'headers') of this field in the database."
    "Errors: invalid field name specified"
)

HEADER_SEARCH_STRING = """Optionally, a (part of the) text for a given field.
The query result will be values of the field that contain the provided search string."""

HEADER_PAGE_SIZE = "Optionally, the number of results to return. Default = 10."

DATA_EXPORTS_HEADER = """\n
Response format:\n
- In addition to retrieving data in JSON format (default behaviour), 
it is possible to request data to be returned in CSV, XML or Excel formats 
by sending the `Accept` http request header with one of the following values:
  - `text/csv`\n
  - `text/xml`\n
  - `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`\n
"""

STUDY_VALUE_VERSION_QUERY = Query(
    description="""If specified, study data with specified version is returned.

    Only exact matches are considered. 

    E.g. 1, 2, 2.1, ...""",
    pattern=FLOAT_REGEX,
)

ERROR_400 = {"model": ErrorResponse, "description": "Error"}
ERROR_403 = {"model": ErrorResponse, "description": "Forbidden"}
ERROR_404 = {"model": ErrorResponse, "description": "Entity not found"}
ERROR_409 = {
    "model": ErrorResponse,
    "description": "The request could not be completed due to a conflict with the current state of the target resource. "
    "This typically occurs when attempting to create or modify a resource that already exists or violates a uniqueness constraint.",
}
ERROR_422 = {"model": ErrorResponse, "description": "Unprocessable Content"}


SYNTAX_FILTERS = (
    FILTERS
    + """
If any provided search term for a given field name is other than a string type, then equal operator will automatically be applied overriding any provided operator.
"""
)
