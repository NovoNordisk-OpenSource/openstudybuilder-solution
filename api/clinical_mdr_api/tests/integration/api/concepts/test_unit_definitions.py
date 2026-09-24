"""
Tests for /concepts/unit-definitions endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments
import json
import logging
from functools import reduce
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
    UnitDefinitionPostInput,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import (
    assert_response_status_code,
    parse_json_response,
)
from common.config import settings

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
unit_definitions: list[UnitDefinitionModel]
archived_unit_definitions: list[UnitDefinitionModel]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "unitdefs.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global unit_definitions

    unit_definitions = []

    for index in range(25):
        unit_definitions.append(
            TestUtils.create_unit_definition(name=f"Unit def {index}")
        )

    global archived_unit_definitions
    archived_unit_definitions = [
        TestUtils.create_unit_definition(name="Archived Unit A"),
        TestUtils.create_unit_definition(name="Archived Unit B"),
    ]
    for ud in archived_unit_definitions:
        TestUtils.archive_unit_definition(ud.uid)

    yield


UNIT_DEF_FIELDS_ALL = [
    "comment",
    "library_name",
    "uid",
    "author_username",
    "template_parameter",
    "display_unit",
    "us_conventional_unit",
    "use_complex_unit_conversion",
    "conversion_factor_to_master",
    "unit_dimension",
    "ucum",
    "legacy_code",
    "master_unit",
    "version",
    "start_date",
    "convertible_unit",
    "status",
    "end_date",
    "definition",
    "unit_subsets",
    "use_molecular_weight",
    "change_description",
    "si_unit",
    "name",
    "order",
    "ct_units",
]
UNIT_DEF_FIELDS_NOT_NULL = ["uid", "name", "start_date"]


def test_get_unit_definition(api_client):
    """
    SCENARIO: Retrieve a single unit definition by UID
    GIVEN an approved unit definition exists
    WHEN GET /concepts/unit-definitions/{uid} is called
    THEN 200 is returned with all expected fields, correct name, version, status and a valid UTC start_date
    """
    response = api_client.get(f"/concepts/unit-definitions/{unit_definitions[0].uid}")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(res.keys()) == set(UNIT_DEF_FIELDS_ALL)
    for key in UNIT_DEF_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == unit_definitions[0].uid
    assert res["name"] == "Unit def 0"
    assert res["version"] == "1.0"
    assert res["status"] == "Final"

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)


def test_get_unit_definitions_pagination(api_client):
    """
    SCENARIO: Paginated listing of unit definitions returns consistent results
    GIVEN multiple unit definitions exist
    WHEN the list endpoint is fetched across multiple pages (page_size=10) and in one large page (page_size=100)
    THEN the unique merged paginated results match the single-page result count and are at least as many as the fixture count
    """
    results_paginated: dict[Any, Any] = {}
    sort_by = '{"name": true}'
    for page_number in range(1, 4):
        url = f"/concepts/unit-definitions?page_number={page_number}&page_size=10&sort_by={sort_by}"
        response = api_client.get(url)
        res = response.json()
        res_names = [item["name"] for item in res["items"]]
        results_paginated[page_number] = res_names
        log.info("Page %s: %s", page_number, res_names)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        set(
            list(
                reduce(lambda a, b: list(a) + list(b), list(results_paginated.values()))
            )
        )
    )
    log.info("All unique rows returned by pagination: %s", results_paginated_merged)

    res_all = api_client.get(
        f"/concepts/unit-definitions?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["name"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(unit_definitions) <= len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, None, None, 10),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 10),
        pytest.param(10, 3, True, None, 8),  # Total number is 28
        pytest.param(10, 1, True, '{"name": false}', 10),
        pytest.param(10, 2, True, '{"name": true}', 10),
    ],
)
def test_get_unit_definitions(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    """
    SCENARIO: List unit definitions with various pagination and sort parameters
    GIVEN unit definitions exist in the system
    WHEN GET /concepts/unit-definitions is called with parametrized page_size, page_number, total_count, sort_by
    THEN 200 is returned with the correct number of items, pagination metadata and all required fields; results are correctly sorted when sort_by is given
    """
    url = "/concepts/unit-definitions"
    query_params = []
    if page_size:
        query_params.append(f"page_size={page_size}")
    if page_number:
        query_params.append(f"page_number={page_number}")
    if total_count:
        query_params.append(f"total_count={total_count}")
    if sort_by:
        query_params.append(f"sort_by={sort_by}")

    if query_params:
        url = f"{url}?{'&'.join(query_params)}"

    log.info("GET %s", url)
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert list(res.keys()) == ["items", "total", "page", "size"]
    assert len(res["items"]) == expected_result_len
    # Adding +3 for UnitDefinitions that are created in scope of inject_base_data
    assert res["total"] == (len(unit_definitions) + 3 if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(UNIT_DEF_FIELDS_ALL)
        for key in UNIT_DEF_FIELDS_NOT_NULL:
            assert item[key] is not None
        TestUtils.assert_timestamp_is_in_utc_zone(item["start_date"])
        TestUtils.assert_timestamp_is_newer_than(item["start_date"], 60)

    if sort_by:
        # sort_by is JSON string in the form: {"sort_field_name": is_ascending_order}
        sort_by_dict = json.loads(sort_by)
        sort_field: str = list(sort_by_dict.keys())[0]
        sort_order_ascending: bool = list(sort_by_dict.values())[0]

        # extract list of values of 'sort_field_name' field from the returned result
        result_vals = list(map(lambda x: x[sort_field], res["items"]))
        result_vals_sorted_locally = result_vals.copy()
        result_vals_sorted_locally.sort(reverse=not sort_order_ascending)
        assert result_vals == result_vals_sorted_locally


@pytest.mark.parametrize(
    "export_format",
    [
        pytest.param("text/csv"),
        pytest.param("text/xml"),
        pytest.param(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    ],
)
def test_get_unit_definitions_csv_xml_excel(api_client, export_format):
    """
    SCENARIO: Export unit definitions in CSV, XML, and Excel formats
    GIVEN unit definitions exist
    WHEN GET /concepts/unit-definitions is called with Accept header for csv/xml/excel
    THEN 200 is returned with data in the requested export format
    """
    url = "/concepts/unit-definitions"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["Unit def"]}}', "name", "Unit def"),
        pytest.param('{"*": {"v": ["Unit def 2"]}}', "name", "Unit def 2"),
        pytest.param('{"*": {"v": ["Final"]}}', "status", "Final"),
        pytest.param('{"*": {"v": ["1.0"]}}', "version", "1.0"),
        pytest.param('{"*": {"v": ["ccc"]}}', None, None),
    ],
)
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    """
    SCENARIO: Wildcard filter on unit definitions list
    GIVEN unit definitions with varied names, statuses and versions exist
    WHEN GET /concepts/unit-definitions is called with a wildcard filter
    THEN 200 is returned and each result row contains a field starting with the filter prefix, or no results when no match
    """
    url = f"/concepts/unit-definitions?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    if expected_result_prefix:
        assert len(res["items"]) > 0
        # Each returned row has a field that starts with the specified filter value
        for row in res["items"]:
            assert row[expected_matched_field].startswith(expected_result_prefix)
    else:
        assert len(res["items"]) == 0


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result",
    [
        pytest.param('{"name": {"v": ["Unit def 0"]}}', "name", "Unit def 0"),
        pytest.param('{"name": {"v": ["Unit def 3"]}}', "name", "Unit def 3"),
        pytest.param('{"name": {"v": ["cc"]}}', None, None),
        pytest.param('{"definition": {"v": ["cc"]}}', None, None),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    """
    SCENARIO: Exact filter on unit definitions list
    GIVEN unit definitions with specific names and definitions exist
    WHEN GET /concepts/unit-definitions is called with an exact-match filter
    THEN 200 is returned and each result row has the filtered field exactly equal to the expected value, or no results when no match
    """
    url = f"/concepts/unit-definitions?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    if expected_result:
        assert len(res["items"]) > 0
        # Each returned row has a field whose value is equal to the specified filter value
        for row in res["items"]:
            assert row[expected_matched_field] == expected_result
    else:
        assert len(res["items"]) == 0


def test_get_unit_definitions_excludes_archived(api_client):
    """
    SCENARIO: listing Unit Definitions excluding archived ones
    GIVEN: multiple Unit Definitions in the database, some archived
    WHEN: GET /concepts/unit-definitions
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing all existing Unit Definitions, excluding archived Unit Definitions.
    """
    response = api_client.get("/concepts/unit-definitions", params={"page_size": 1000})
    payload = parse_json_response(response, assert_status=200)

    items = payload["items"]
    assert len(items) > 0
    for item in items:
        assert item["library_name"] != settings.archived_library_name


def test_get_archived_unit_definitions(api_client):
    """
    SCENARIO: getting archived Unit Definitions
    GIVEN: multiple Unit Definitions in the database, some archived
    WHEN: GET /concepts/unit-definitions?library_name=Archived
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing only the archived Unit Definitions.
    """
    response = api_client.get(
        "/concepts/unit-definitions",
        params={"library_name": settings.archived_library_name, "page_size": 1000},
    )
    payload = parse_json_response(response, assert_status=200)

    items = payload["items"]
    assert len(items) > 0
    for item in items:
        assert item["library_name"] == settings.archived_library_name


def test_get_unit_definition_by_uid_returns_archived(api_client):
    """
    SCENARIO: getting a single archived Unit Definition by UID
    GIVEN: an archived Unit Definition in the database
    WHEN: GET /concepts/unit-definitions/{uid}
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Unit Definition with library_name set to 'Archived'.
    """
    archived_ud = archived_unit_definitions[0]
    response = api_client.get(f"/concepts/unit-definitions/{archived_ud.uid}")
    res = parse_json_response(response, assert_status=200)

    assert res["uid"] == archived_ud.uid
    assert res["library_name"] == settings.archived_library_name


def test_archived_unit_definition_excluded_from_headers(api_client):
    """
    SCENARIO: getting headers of Unit Definitions with archived Unit Definitions in the database
    GIVEN: an existing Unit Definition in the database, later archived
    WHEN: GET /concepts/unit-definitions/headers?field_name=name
    THEN: should respond with 200 HTTP status code and JSON payload,
          with the archived Unit Definition excluded from the results.
    """
    # Create a Unit Definition
    unit_definition = TestUtils.create_unit_definition(name="A Canary unit definition")

    # Get headers — the new unit definition should appear
    response = api_client.get(
        "/concepts/unit-definitions/headers",
        params={"field_name": "name", "search_string": "canary"},
    )
    payload = parse_json_response(response, assert_status=200)
    assert isinstance(payload, list)
    assert unit_definition.name in payload

    # Archive the Unit Definition
    TestUtils.archive_unit_definition(unit_definition.uid)

    # Get headers again — the archived unit definition should no longer appear
    response = api_client.get(
        "/concepts/unit-definitions/headers",
        params={"field_name": "name", "search_string": "canary"},
    )
    payload = parse_json_response(response, assert_status=200)
    assert isinstance(payload, list)
    assert unit_definition.name not in payload


def test_archiving_unit_definition_draft(api_client):
    """
    SCENARIO: archiving a Unit Definition in Draft status
    GIVEN: a Unit Definition in Draft status
    WHEN: POST /concepts/unit-definitions/{uid}/archive
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Unit Definition with library_name set to the archived library.
    """
    unit_definition = TestUtils.create_unit_definition(
        name="Draft Unit Def To Archive", approve=False
    )

    response = api_client.post(
        f"/concepts/unit-definitions/{unit_definition.uid}/archive"
    )
    res = parse_json_response(response, assert_status=200)

    assert res["library_name"] == settings.archived_library_name
    assert res["name"] == unit_definition.name


def test_archiving_unit_definition_final(api_client):
    """
    SCENARIO: archiving a Unit Definition in Final status
    GIVEN: a Unit Definition in Final (approved) status
    WHEN: POST /concepts/unit-definitions/{uid}/archive
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Unit Definition with library_name set to the archived library.
    """
    unit_definition = TestUtils.create_unit_definition(name="Final Unit Def To Archive")

    response = api_client.post(
        f"/concepts/unit-definitions/{unit_definition.uid}/archive"
    )
    res = parse_json_response(response, assert_status=200)

    assert res["library_name"] == settings.archived_library_name


def test_can_not_archive_already_archived_unit_definition(api_client):
    """
    SCENARIO: attempting to archive an already-archived Unit Definition
    GIVEN: Unit Definitions that are already archived
    WHEN: POST /concepts/unit-definitions/{uid}/archive for each archived unit definition
    THEN: should respond with 400 HTTP status code and an error message indicating the unit definition
          is already in the archived library.
    """
    for unit_definition in archived_unit_definitions:
        uid = unit_definition.uid
        response = api_client.post(f"/concepts/unit-definitions/{uid}/archive")
        res = parse_json_response(response, assert_status=400)

        assert (
            res["message"]
            == f"Concept with UID '{uid}' is already in '{settings.archived_library_name}' library."
        )


def test_can_not_create_new_version_of_archived_unit_definition(api_client):
    """
    SCENARIO: attempting to create a new version of an archived Unit Definition
    GIVEN: Unit Definitions that are already archived
    WHEN: POST /concepts/unit-definitions/{uid}/versions for each archived unit definition
    THEN: should respond with 400 HTTP status code and an error message indicating the library
          is not editable.
    """
    for unit_definition in archived_unit_definitions:
        response = api_client.post(
            f"/concepts/unit-definitions/{unit_definition.uid}/versions"
        )
        res = parse_json_response(response, assert_status=400)

        assert res["message"] == "Library isn't editable."


def test_can_not_edit_archived_unit_definition(api_client):
    """
    SCENARIO: attempting to edit an archived Unit Definition
    GIVEN: Unit Definitions that are already archived
    WHEN: PATCH /concepts/unit-definitions/{uid} for each archived unit definition
    THEN: should respond with 400 HTTP status code and an error message indicating the library
          is not editable.
    """
    for unit_definition in archived_unit_definitions:
        response = api_client.patch(
            f"/concepts/unit-definitions/{unit_definition.uid}",
            json={
                "name": "Edited Archived Unit Definition",
                "change_description": "edit attempt on archived",
            },
        )
        res = parse_json_response(response, assert_status=400)

        assert res["message"] == "Library isn't editable."


def test_allow_recreating_archived_unit_definition(api_client):
    """
    SCENARIO: re-creating a Unit Definition with the same name as an archived one
    GIVEN: Unit Definitions that are already archived
    WHEN: POST /concepts/unit-definitions with the same name as the archived unit definition
    THEN: should respond with 201 HTTP status code and JSON payload,
          containing the newly created Unit Definition with the same name.
    """
    for unit_definition in archived_unit_definitions:
        ud_dict = unit_definition.model_dump()
        ud_dict["library_name"] = settings.sponsor_library_name
        post_input_fields = UnitDefinitionPostInput.model_fields.keys()
        input_model = UnitDefinitionPostInput(
            **{k: v for k, v in ud_dict.items() if k in post_input_fields}
        )

        response = api_client.post(
            "/concepts/unit-definitions",
            json=input_model.model_dump(),
        )
        res = parse_json_response(response, assert_status=201)
        assert res["name"] == unit_definition.name


def test_delete_draft_unit_definition(api_client):
    """
    SCENARIO: deleting a draft Unit Definition
    GIVEN: an existing draft Unit Definition
    WHEN: DELETE /concepts/unit-definitions/{uid}
    THEN: should respond with 204 HTTP status code
    """

    unit_definition = TestUtils.create_unit_definition(
        name="Unit Definition to delete", approve=False
    )

    response = api_client.delete(f"/concepts/unit-definitions/{unit_definition.uid}")
    assert_response_status_code(response, 204)


def test_delete_archived_unit_definition_fails(api_client):
    """
    SCENARIO: deleting an archived Unit Definition
    GIVEN: an existing archived Unit Definition
    WHEN: DELETE /concepts/unit-definitions/{uid}
    THEN: should respond with 400 HTTP status code and JSON payload,
          with an error message that archived concepts cannot be deleted.
    """

    unit_definition = TestUtils.create_unit_definition(
        name="Archived Unit Definition to delete", approve=False
    )
    TestUtils.archive_unit_definition(unit_definition.uid)

    response = api_client.delete(f"/concepts/unit-definitions/{unit_definition.uid}")
    resp = parse_json_response(response, assert_status=400)
    assert "Can't delete Concept" in resp["message"]
