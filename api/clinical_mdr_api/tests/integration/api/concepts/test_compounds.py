"""
Tests for /concepts/compounds endpoints
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
from clinical_mdr_api.models.concepts.compound import Compound, CompoundCreateInput
from clinical_mdr_api.models.concepts.compound_alias import (
    CompoundAlias,
    CompoundAliasCreateInput,
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
rand: str
compounds_all: list[Compound]
compound_aliases_all: list[CompoundAlias]
archived_compounds: list[Compound]
archived_compound_aliases: list[CompoundAlias]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "compounds.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global rand
    global compounds_all
    global compound_aliases_all

    rand = TestUtils.random_str(10)

    # Create some compounds
    compounds_all = []
    compound_aliases_all = []
    compounds_all.append(TestUtils.create_compound(name=f"Compound A {rand}"))

    compounds_all.append(TestUtils.create_compound(name=f"name-AAA-{rand}"))
    compounds_all.append(TestUtils.create_compound(name=f"name-BBB-{rand}"))
    compounds_all.append(TestUtils.create_compound(definition=f"def-XXX-{rand}"))
    compounds_all.append(TestUtils.create_compound(definition=f"def-YYY-{rand}"))

    for index in range(5):
        compound_a = TestUtils.create_compound(
            name=f"name-AAA-{rand}-{index}", approve=True
        )
        compounds_all.append(compound_a)
        compound_aliases_all.append(
            TestUtils.create_compound_alias(
                name=f"compAlias-AAA-{rand}-{index}", compound_uid=compound_a.uid
            )
        )

        compound_b = TestUtils.create_compound(name=f"name-BBB-{rand}-{index}")
        compounds_all.append(compound_b)
        compound_aliases_all.append(
            TestUtils.create_compound_alias(
                name=f"compAlias-BBB-{rand}-{index}", compound_uid=compound_b.uid
            )
        )

        compound_c = TestUtils.create_compound(definition=f"def-XXX-{rand}-{index}")
        compounds_all.append(compound_c)
        compound_aliases_all.append(
            TestUtils.create_compound_alias(
                definition=f"def-XXX-{rand}-{index}", compound_uid=compound_c.uid
            )
        )

        compound_d = TestUtils.create_compound(definition=f"def-YYY-{rand}-{index}")
        compounds_all.append(compound_d)
        compound_aliases_all.append(
            TestUtils.create_compound_alias(
                definition=f"def-YYY-{rand}-{index}", compound_uid=compound_d.uid
            )
        )

    global archived_compounds
    global archived_compound_aliases
    archived_compounds = [
        TestUtils.create_compound(name=f"Archived Compound A {rand}"),
        TestUtils.create_compound(name=f"Archived Compound B {rand}"),
    ]
    for comp in archived_compounds:
        TestUtils.archive_compound(comp.uid)

    archived_compound_aliases = [
        TestUtils.create_compound_alias(
            name=f"Archived Alias A {rand}", compound_uid=compounds_all[0].uid
        ),
        TestUtils.create_compound_alias(
            name=f"Archived Alias B {rand}", compound_uid=compounds_all[0].uid
        ),
    ]
    for alias in archived_compound_aliases:
        TestUtils.archive_compound_alias(alias.uid)


COMPOUND_FIELDS_ALL = [
    "uid",
    "name",
    "name_sentence_case",
    "definition",
    "abbreviation",
    "library_name",
    "start_date",
    "end_date",
    "status",
    "version",
    "change_description",
    "author_username",
    "possible_actions",
    "external_id",
]

COMPOUND_FIELDS_NOT_NULL = ["uid", "name", "start_date"]

COMPOUND_ALIASES_FIELDS_ALL = [
    "uid",
    "name",
    "name_sentence_case",
    "definition",
    "abbreviation",
    "library_name",
    "start_date",
    "end_date",
    "status",
    "version",
    "change_description",
    "author_username",
    "possible_actions",
    "compound",
    "is_preferred_synonym",
]

COMPOUND_ALIASES_FIELDS_NOT_NULL = ["uid", "name", "start_date"]


def test_get_compound(api_client):
    """
    SCENARIO: Retrieve a single compound by UID
    GIVEN a compound in Draft status exists
    WHEN GET /concepts/compounds/{uid} is called
    THEN 200 is returned with all expected fields, correct name, version 0.1, status Draft, and a valid UTC start_date
    """
    response = api_client.get(f"/concepts/compounds/{compounds_all[0].uid}")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(res.keys()) == set(COMPOUND_FIELDS_ALL)
    for key in COMPOUND_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == compounds_all[0].uid
    assert res["name"] == f"Compound A {rand}"
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)


def test_get_compounds_versions(api_client):
    """
    SCENARIO: Retrieve all compound versions
    GIVEN compounds exist including approved and archived ones
    WHEN GET /concepts/compounds/versions?total_count=true is called
    THEN 200 is returned with 10 items per page, total count accounts for approved duplicates and archived, and all required fields are present
    """
    response = api_client.get("/concepts/compounds/versions?total_count=true")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res["items"]) == 10
    assert res["total"] == len(compounds_all) + 5 + len(
        archived_compounds
    )  # +5 because 5 compound was approved, so they have 2 versions

    for item in res["items"]:
        assert set(list(item.keys())) == set(COMPOUND_FIELDS_ALL)
        for key in COMPOUND_FIELDS_NOT_NULL:
            assert item[key] is not None
        TestUtils.assert_timestamp_is_in_utc_zone(item["start_date"])
        TestUtils.assert_timestamp_is_newer_than(item["start_date"], 60)


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
def test_get_compounds_versions_csv_xml_excel(api_client, export_format):
    """
    SCENARIO: Export compound versions in CSV, XML, and Excel formats
    GIVEN compounds exist
    WHEN GET /concepts/compounds/versions is called with Accept header for csv/xml/excel
    THEN 200 is returned with data in the requested export format
    """
    url = "/concepts/compounds/versions"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


def test_get_compound_versions(api_client):
    """
    SCENARIO: Full lifecycle versioning of a compound
    GIVEN a compound in Draft status exists
    WHEN approve, new_version, and get versions are called in sequence
    THEN each action returns the correct version number, status, and possible_actions; version list grows accordingly
    """
    response = api_client.get(f"/concepts/compounds/{compounds_all[0].uid}/versions")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) == 1

    assert res[0]["version"] == "0.1"
    assert res[0]["status"] == "Draft"
    assert list(res[0]["possible_actions"]) == ["approve", "delete", "edit"]

    for item in res:
        assert set(list(item.keys())) == set(COMPOUND_FIELDS_ALL)
        for key in COMPOUND_FIELDS_NOT_NULL:
            assert item[key] is not None
        TestUtils.assert_timestamp_is_in_utc_zone(item["start_date"])
        TestUtils.assert_timestamp_is_newer_than(item["start_date"], 60)

    # Approve compound. Assert that 2 versions exist in total.
    api_client.post(f"/concepts/compounds/{compounds_all[0].uid}/approvals")
    response = api_client.get(f"/concepts/compounds/{compounds_all[0].uid}/versions")
    res = response.json()
    assert len(res) == 2

    assert res[0]["version"] == "1.0"
    assert res[0]["status"] == "Final"
    assert list(res[0]["possible_actions"]) == ["inactivate", "new_version"]

    assert res[1]["version"] == "0.1"
    assert res[1]["status"] == "Draft"
    assert list(res[1]["possible_actions"]) == ["approve", "delete", "edit"]

    # Create new version of the compound. Assert that 3 versions exist in total.
    api_client.post(f"/concepts/compounds/{compounds_all[0].uid}/versions")
    response = api_client.get(f"/concepts/compounds/{compounds_all[0].uid}/versions")
    res = response.json()
    assert len(res) == 3

    assert res[0]["version"] == "1.1"
    assert res[0]["status"] == "Draft"
    assert list(res[0]["possible_actions"]) == ["approve", "edit"]

    assert res[1]["version"] == "1.0"
    assert res[1]["status"] == "Final"
    assert list(res[1]["possible_actions"]) == ["inactivate", "new_version"]

    assert res[2]["version"] == "0.1"
    assert res[2]["status"] == "Draft"
    assert list(res[2]["possible_actions"]) == ["approve", "delete", "edit"]


def test_update_compound(api_client):
    """
    SCENARIO: Update a compound's name via PATCH
    GIVEN a compound in Draft status exists
    WHEN PATCH /concepts/compounds/{uid} is called with an updated name
    THEN 200 is returned with a valid UTC start_date
    """
    payload = {
        "name": f"{compounds_all[0].name}-updated",
        "change_description": "name updated",
    }
    response = api_client.patch(
        f"/concepts/compounds/{compounds_all[0].uid}",
        data=json.dumps(payload),
        headers={"content-type": "application/json"},
    )
    res = response.json()

    assert_response_status_code(response, 200)

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)


def test_get_compounds_pagination(api_client):
    """
    SCENARIO: Paginated listing of compounds returns consistent results
    GIVEN multiple compounds exist
    WHEN the list endpoint is fetched across multiple pages (page_size=10) and in one large page (page_size=100)
    THEN the unique merged paginated results match the single-page result count and equal the fixture count
    """
    results_paginated: dict[Any, Any] = {}
    sort_by = '{"name": true}'
    for page_number in range(1, 4):
        url = f"/concepts/compounds?page_number={page_number}&page_size=10&sort_by={sort_by}"
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
        f"/concepts/compounds?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["name"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(compounds_all) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, None, None, 10),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 10),
        pytest.param(10, 3, True, None, 5),  # Total number of compounds is 25
        pytest.param(10, 1, True, '{"name": false}', 10),
        pytest.param(10, 2, True, '{"name": true}', 10),
    ],
)
def test_get_compounds(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    """
    SCENARIO: List compounds with various pagination and sort parameters
    GIVEN compounds exist in the system
    WHEN GET /concepts/compounds is called with parametrized page_size, page_number, total_count, sort_by
    THEN 200 is returned with the correct number of items, pagination metadata and all required fields; results are correctly sorted when sort_by is given
    """
    url = "/concepts/compounds"
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
    assert res["total"] == (len(compounds_all) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(COMPOUND_FIELDS_ALL)
        for key in COMPOUND_FIELDS_NOT_NULL:
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
def test_get_compounds_csv_xml_excel(api_client, export_format):
    """
    SCENARIO: Export compounds in CSV, XML, and Excel formats
    GIVEN compounds exist
    WHEN GET /concepts/compounds is called with Accept header for csv/xml/excel
    THEN 200 is returned with data in the requested export format
    """
    url = "/concepts/compounds"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["aaa"]}}', "name", "name-AAA"),
        pytest.param('{"*": {"v": ["bBb"]}}', "name", "name-BBB"),
        pytest.param(
            '{"*": {"v": ["unknown-user"], "op": "co"}}',
            "author_username",
            "unknown-user@example.com",
        ),
        pytest.param('{"*": {"v": ["Draft"]}}', "status", "Draft"),
        pytest.param('{"*": {"v": ["0.1"]}}', "version", "0.1"),
        pytest.param('{"*": {"v": ["ccc"]}}', None, None),
    ],
)
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    """
    SCENARIO: Wildcard filter on compounds list
    GIVEN compounds with varied names, statuses and versions exist
    WHEN GET /concepts/compounds is called with a wildcard filter
    THEN 200 is returned and each result row contains a field starting with the filter prefix, or no results when no match
    """
    url = f"/concepts/compounds?filters={filter_by}"
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
        pytest.param('{"name": {"v": ["name-AAA-{rand}"]}}', "name", "name-AAA-{rand}"),
        pytest.param('{"name": {"v": ["name-BBB-{rand}"]}}', "name", "name-BBB-{rand}"),
        pytest.param('{"name": {"v": ["cc"]}}', None, None),
        pytest.param(
            '{"definition": {"v": ["def-XXX-{rand}"]}}', "definition", "def-XXX-{rand}"
        ),
        pytest.param(
            '{"definition": {"v": ["def-YYY-{rand}"]}}', "definition", "def-YYY-{rand}"
        ),
        pytest.param('{"definition": {"v": ["cc"]}}', None, None),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    """
    SCENARIO: Exact filter on compounds list
    GIVEN compounds with specific names and definitions exist
    WHEN GET /concepts/compounds is called with an exact-match filter
    THEN 200 is returned and each result row has the filtered field exactly equal to the expected value, or no results when no match
    """
    filter_by = filter_by.replace("{rand}", rand)
    url = f"/concepts/compounds?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    if expected_result:
        assert len(res["items"]) > 0
        # Each returned row has a field whose value is equal to the specified filter value
        for row in res["items"]:
            assert row[expected_matched_field] == expected_result.replace(
                "{rand}", rand
            )
    else:
        assert len(res["items"]) == 0


# Compound Aliases


def test_get_compound_aliases_versions(api_client):
    """
    SCENARIO: Retrieve all compound alias versions
    GIVEN compound aliases exist including archived ones
    WHEN GET /concepts/compound-aliases/versions?total_count=true is called
    THEN 200 is returned with 10 items per page, total count equals all + archived, and all required fields are present
    """
    response = api_client.get("/concepts/compound-aliases/versions?total_count=true")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res["items"]) == 10
    assert res["total"] == len(compound_aliases_all) + len(archived_compound_aliases)

    for item in res["items"]:
        assert set(list(item.keys())) == set(COMPOUND_ALIASES_FIELDS_ALL)
        for key in COMPOUND_ALIASES_FIELDS_NOT_NULL:
            assert item[key] is not None
        TestUtils.assert_timestamp_is_in_utc_zone(item["start_date"])
        TestUtils.assert_timestamp_is_newer_than(item["start_date"], 60)


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
def test_get_compound_aliases_versions_csv_xml_excel(api_client, export_format):
    """
    SCENARIO: Export compound alias versions in CSV, XML, and Excel formats
    GIVEN compound aliases exist
    WHEN GET /concepts/compound-aliases/versions is called with Accept header for csv/xml/excel
    THEN 200 is returned with data in the requested export format
    """
    url = "/concepts/compound-aliases/versions"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


def test_get_compound_alias_versions(api_client):
    """
    SCENARIO: Full lifecycle versioning of a compound alias
    GIVEN a compound alias in Draft status exists
    WHEN approve, new_version, and get versions are called in sequence
    THEN each action returns the correct version number, status, and possible_actions; version list grows accordingly
    """
    response = api_client.get(
        f"/concepts/compound-aliases/{compound_aliases_all[0].uid}/versions"
    )
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) == 1

    assert res[0]["version"] == "0.1"
    assert res[0]["status"] == "Draft"
    assert list(res[0]["possible_actions"]) == ["approve", "delete", "edit"]

    for item in res:
        assert set(list(item.keys())) == set(COMPOUND_ALIASES_FIELDS_ALL)
        for key in COMPOUND_ALIASES_FIELDS_NOT_NULL:
            assert item[key] is not None
        TestUtils.assert_timestamp_is_in_utc_zone(item["start_date"])
        TestUtils.assert_timestamp_is_newer_than(item["start_date"], 60)

    # Approve compound alias. Assert that 2 versions exist in total.
    api_client.post(
        f"/concepts/compound-aliases/{compound_aliases_all[0].uid}/approvals"
    )
    response = api_client.get(
        f"/concepts/compound-aliases/{compound_aliases_all[0].uid}/versions"
    )
    res = response.json()
    assert len(res) == 2

    assert res[0]["version"] == "1.0"
    assert res[0]["status"] == "Final"
    assert list(res[0]["possible_actions"]) == ["inactivate", "new_version"]

    assert res[1]["version"] == "0.1"
    assert res[1]["status"] == "Draft"
    assert list(res[1]["possible_actions"]) == ["approve", "delete", "edit"]

    # Create new version of the compound alias. Assert that 3 versions exist in total.
    api_client.post(
        f"/concepts/compound-aliases/{compound_aliases_all[0].uid}/versions"
    )
    response = api_client.get(
        f"/concepts/compound-aliases/{compound_aliases_all[0].uid}/versions"
    )
    res = response.json()
    assert len(res) == 3

    assert res[0]["version"] == "1.1"
    assert res[0]["status"] == "Draft"
    assert list(res[0]["possible_actions"]) == ["approve", "edit"]

    assert res[1]["version"] == "1.0"
    assert res[1]["status"] == "Final"
    assert list(res[1]["possible_actions"]) == ["inactivate", "new_version"]

    assert res[2]["version"] == "0.1"
    assert res[2]["status"] == "Draft"
    assert list(res[2]["possible_actions"]) == ["approve", "delete", "edit"]


def test_get_compound_aliases_pagination(api_client):
    """
    SCENARIO: Paginated listing of compound aliases returns consistent results
    GIVEN multiple compound aliases exist
    WHEN the list endpoint is fetched across multiple pages (page_size=10) and in one large page (page_size=100)
    THEN the unique merged paginated results match the single-page result count and equal the fixture count
    """
    results_paginated: dict[Any, Any] = {}
    sort_by = '{"name": true}'
    for page_number in range(1, 4):
        url = f"/concepts/compound-aliases?page_number={page_number}&page_size=10&sort_by={sort_by}"
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
        f"/concepts/compound-aliases?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["name"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(compound_aliases_all) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, None, None, 10),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 10),
        pytest.param(10, 1, True, '{"name": false}', 10),
        pytest.param(10, 2, True, '{"name": true}', 10),
    ],
)
def test_get_compound_aliases(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    """
    SCENARIO: List compound aliases with various pagination and sort parameters
    GIVEN compound aliases exist in the system
    WHEN GET /concepts/compound-aliases is called with parametrized page_size, page_number, total_count, sort_by
    THEN 200 is returned with the correct number of items, pagination metadata; results are correctly sorted when sort_by is given
    """
    url = "/concepts/compound-aliases"
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
    assert res["total"] == (len(compound_aliases_all) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

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
def test_get_compound_aliases_csv_xml_excel(api_client, export_format):
    """
    SCENARIO: Export compound aliases in CSV, XML, and Excel formats
    GIVEN compound aliases exist
    WHEN GET /concepts/compound-aliases is called with Accept header for csv/xml/excel
    THEN 200 is returned with data in the requested export format
    """
    url = "/concepts/compound-aliases"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["aaa"]}}', "name", "compAlias-AAA"),
        pytest.param('{"*": {"v": ["bBb"]}}', "name", "compAlias-BBB"),
        pytest.param(
            '{"*": {"v": ["unknown-user"], "op": "co"}}',
            "author_username",
            "unknown-user@example.com",
        ),
        pytest.param('{"*": {"v": ["Draft"]}}', "status", "Draft"),
        pytest.param('{"*": {"v": ["0.1"]}}', "version", "0.1"),
        pytest.param('{"*": {"v": ["ccc"]}}', None, None),
    ],
)
def test_compound_aliases_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    """
    SCENARIO: Wildcard filter on compound aliases list
    GIVEN compound aliases with varied names, statuses and versions exist
    WHEN GET /concepts/compound-aliases is called with a wildcard filter
    THEN 200 is returned and each result row contains a field starting with the filter prefix, or no results when no match
    """
    url = f"/concepts/compound-aliases?filters={filter_by}"
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
        pytest.param(
            '{"name": {"v": ["compAlias-AAA-{rand}-1"]}}',
            "name",
            "compAlias-AAA-{rand}-1",
        ),
        pytest.param(
            '{"name": {"v": ["compAlias-BBB-{rand}-1"]}}',
            "name",
            "compAlias-BBB-{rand}-1",
        ),
        pytest.param('{"name": {"v": ["cc"]}}', None, None),
        pytest.param(
            '{"definition": {"v": ["def-XXX-{rand}-1"]}}',
            "definition",
            "def-XXX-{rand}-1",
        ),
        pytest.param(
            '{"definition": {"v": ["def-YYY-{rand}-1"]}}',
            "definition",
            "def-YYY-{rand}-1",
        ),
        pytest.param('{"definition": {"v": ["cc"]}}', None, None),
    ],
)
def test_compound_aliases_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    """
    SCENARIO: Exact filter on compound aliases list
    GIVEN compound aliases with specific names and definitions exist
    WHEN GET /concepts/compound-aliases is called with an exact-match filter
    THEN 200 is returned and each result row has the filtered field exactly equal to the expected value, or no results when no match
    """
    filter_by = filter_by.replace("{rand}", rand)
    url = f"/concepts/compound-aliases?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    if expected_result:
        assert len(res["items"]) > 0
        # Each returned row has a field whose value is equal to the specified filter value
        for row in res["items"]:
            assert row[expected_matched_field] == expected_result.replace(
                "{rand}", rand
            )
    else:
        assert len(res["items"]) == 0


def test_get_compounds_excludes_archived(api_client):
    """
    SCENARIO: listing Compounds excluding archived ones
    GIVEN: multiple Compounds in the database, some archived
    WHEN: GET /concepts/compounds
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing all existing Compounds, excluding archived Compounds.
    """
    response = api_client.get("/concepts/compounds", params={"page_size": 1000})
    payload = parse_json_response(response, assert_status=200)

    items = payload["items"]
    assert len(items) > 0
    for item in items:
        assert item["library_name"] != settings.archived_library_name


def test_get_archived_compounds(api_client):
    """
    SCENARIO: getting archived Compounds
    GIVEN: multiple Compounds in the database, some archived
    WHEN: GET /concepts/compounds?library_name=Archived
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing only the archived Compounds.
    """
    response = api_client.get(
        "/concepts/compounds",
        params={"library_name": settings.archived_library_name, "page_size": 1000},
    )
    payload = parse_json_response(response, assert_status=200)

    items = payload["items"]
    assert len(items) > 0
    for item in items:
        assert item["library_name"] == settings.archived_library_name


def test_get_compound_by_uid_returns_archived(api_client):
    """
    SCENARIO: getting a single archived Compound by UID
    GIVEN: an archived Compound in the database
    WHEN: GET /concepts/compounds/{uid}
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Compound with library_name set to 'Archived'.
    """
    archived_comp = archived_compounds[0]
    response = api_client.get(f"/concepts/compounds/{archived_comp.uid}")
    res = parse_json_response(response, assert_status=200)

    assert res["uid"] == archived_comp.uid
    assert res["library_name"] == settings.archived_library_name


def test_archived_compound_excluded_from_headers(api_client):
    """
    SCENARIO: getting headers of Compounds with archived Compounds in the database
    GIVEN: an existing Compound in the database, later archived
    WHEN: GET /concepts/compounds/headers?field_name=name
    THEN: should respond with 200 HTTP status code and JSON payload,
          with the archived Compound excluded from the results.
    """
    # Create a Compound
    compound = TestUtils.create_compound(name=f"A Canary compound {rand}")

    # Get headers — the new compound should appear
    response = api_client.get(
        "/concepts/compounds/headers",
        params={"field_name": "name", "search_string": "Canary"},
    )
    payload = parse_json_response(response, assert_status=200)
    assert isinstance(payload, list)
    assert compound.name in payload

    # Archive the Compound
    TestUtils.archive_compound(compound.uid)

    # Get headers again — the archived compound should no longer appear
    response = api_client.get(
        "/concepts/compounds/headers",
        params={"field_name": "name", "search_string": "Canary"},
    )
    payload = parse_json_response(response, assert_status=200)
    assert isinstance(payload, list)
    assert compound.name not in payload


def test_get_compound_aliases_excludes_archived(api_client):
    """
    SCENARIO: listing Compound Aliases excluding archived ones
    GIVEN: multiple Compound Aliases in the database, some archived
    WHEN: GET /concepts/compound-aliases
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing all existing Compound Aliases, excluding archived Compound Aliases.
    """
    response = api_client.get("/concepts/compound-aliases", params={"page_size": 1000})
    payload = parse_json_response(response, assert_status=200)

    items = payload["items"]
    assert len(items) > 0
    for item in items:
        assert item["library_name"] != settings.archived_library_name


def test_get_archived_compound_aliases(api_client):
    """
    SCENARIO: getting archived Compound Aliases
    GIVEN: multiple Compound Aliases in the database, some archived
    WHEN: GET /concepts/compound-aliases?library_name=Archived
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing only the archived Compound Aliases.
    """
    response = api_client.get(
        "/concepts/compound-aliases",
        params={"library_name": settings.archived_library_name, "page_size": 1000},
    )
    payload = parse_json_response(response, assert_status=200)

    items = payload["items"]
    assert len(items) > 0
    for item in items:
        assert item["library_name"] == settings.archived_library_name


# ===========================================================================
# Compound core archival tests
# ===========================================================================


def test_archiving_compound_draft(api_client):
    """
    SCENARIO: archiving a Compound in Draft status
    GIVEN: a Compound in Draft status
    WHEN: POST /concepts/compounds/{uid}/archive
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Compound with library_name set to the archived library.
    """
    compound = TestUtils.create_compound(
        name=f"Draft Compound To Archive {rand}", approve=False
    )

    response = api_client.post(f"/concepts/compounds/{compound.uid}/archive")
    res = parse_json_response(response, assert_status=200)

    assert res["library_name"] == settings.archived_library_name
    assert res["name"] == compound.name


def test_archiving_compound_final(api_client):
    """
    SCENARIO: archiving a Compound in Final status
    GIVEN: a Compound in Final (approved) status
    WHEN: POST /concepts/compounds/{uid}/archive
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Compound with library_name set to the archived library.
    """
    compound = TestUtils.create_compound(
        name=f"Final Compound To Archive {rand}", approve=True
    )

    response = api_client.post(f"/concepts/compounds/{compound.uid}/archive")
    res = parse_json_response(response, assert_status=200)

    assert res["library_name"] == settings.archived_library_name


def test_can_not_archive_already_archived_compound(api_client):
    """
    SCENARIO: attempting to archive an already-archived Compound
    GIVEN: Compounds that are already archived
    WHEN: POST /concepts/compounds/{uid}/archive for each archived Compound
    THEN: should respond with 400 HTTP status code and an error message indicating the Compound
          is already in the archived library.
    """
    for compound in archived_compounds:
        uid = compound.uid
        response = api_client.post(f"/concepts/compounds/{uid}/archive")
        res = parse_json_response(response, assert_status=400)

        assert (
            res["message"]
            == f"Concept with UID '{uid}' is already in '{settings.archived_library_name}' library."
        )


def test_can_not_create_new_version_of_archived_compound(api_client):
    """
    SCENARIO: attempting to create a new version of an archived Compound
    GIVEN: Compounds that are already archived
    WHEN: POST /concepts/compounds/{uid}/versions for each archived Compound
    THEN: should respond with 400 HTTP status code and an error message indicating the library
          is not editable.
    """
    for compound in archived_compounds:
        response = api_client.post(f"/concepts/compounds/{compound.uid}/versions")
        res = parse_json_response(response, assert_status=400)

        assert res["message"] == "Library isn't editable."


def test_can_not_edit_archived_compound(api_client):
    """
    SCENARIO: attempting to edit an archived Compound
    GIVEN: Compounds that are already archived
    WHEN: PATCH /concepts/compounds/{uid} for each archived Compound
    THEN: should respond with 400 HTTP status code and an error message indicating the library
          is not editable.
    """
    for compound in archived_compounds:
        response = api_client.patch(
            f"/concepts/compounds/{compound.uid}",
            json={
                "name": "Edited Archived Compound",
                "change_description": "edit attempt on archived",
            },
        )
        res = parse_json_response(response, assert_status=400)

        assert res["message"] == "Library isn't editable."


@pytest.mark.xfail(
    reason="Backend issue: Uniqueness checks do not exclude Archived library"
)
def test_allow_recreating_archived_compound(api_client):
    """
    SCENARIO: re-creating a Compound with the same name as an archived one
    GIVEN: Compounds that are already archived
    WHEN: POST /concepts/compounds with the same name as the archived Compound
    THEN: should respond with 201 HTTP status code and JSON payload,
          containing the newly created Compound with the same name.
    """
    for compound in archived_compounds:
        compound_dict = compound.model_dump()
        compound_dict["library_name"] = settings.sponsor_library_name
        input_model = CompoundCreateInput(**compound_dict)

        response = api_client.post(
            "/concepts/compounds",
            json=input_model.model_dump(),
        )
        res = parse_json_response(response, assert_status=201)

        assert res["name"] == compound.name


# ===========================================================================
# CompoundAlias listing tests (A3 and A4)
# ===========================================================================


def test_get_compound_alias_by_uid_returns_archived(api_client):
    """
    SCENARIO: getting a single archived Compound Alias by UID
    GIVEN: an archived Compound Alias in the database
    WHEN: GET /concepts/compound-aliases/{uid}
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Compound Alias with library_name set to 'Archived'.
    """
    archived_alias = archived_compound_aliases[0]
    response = api_client.get(f"/concepts/compound-aliases/{archived_alias.uid}")
    res = parse_json_response(response, assert_status=200)

    assert res["uid"] == archived_alias.uid
    assert res["library_name"] == settings.archived_library_name


def test_archived_compound_alias_excluded_from_headers(api_client):
    """
    SCENARIO: getting headers of Compound Aliases with archived Compound Aliases in the database
    GIVEN: an existing Compound Alias in the database, later archived
    WHEN: GET /concepts/compound-aliases/headers?field_name=name
    THEN: should respond with 200 HTTP status code and JSON payload,
          with the archived Compound Alias excluded from the results.
    """
    # Create a CompoundAlias with a canary name
    alias = TestUtils.create_compound_alias(
        name=f"A Canary Alias {rand}", compound_uid=compounds_all[0].uid
    )

    # Get headers — the new alias should appear
    response = api_client.get(
        "/concepts/compound-aliases/headers",
        params={"field_name": "name", "search_string": "Canary Alias"},
    )
    payload = parse_json_response(response, assert_status=200)
    assert isinstance(payload, list)
    assert alias.name in payload

    # Archive the CompoundAlias
    TestUtils.archive_compound_alias(alias.uid)

    # Get headers again — the archived alias should no longer appear
    response = api_client.get(
        "/concepts/compound-aliases/headers",
        params={"field_name": "name", "search_string": "Canary Alias"},
    )
    payload = parse_json_response(response, assert_status=200)
    assert isinstance(payload, list)
    assert alias.name not in payload


# ===========================================================================
# CompoundAlias core archival tests
# ===========================================================================


def test_archiving_compound_alias_draft(api_client):
    """
    SCENARIO: archiving a Compound Alias in Draft status
    GIVEN: a Compound Alias in Draft status
    WHEN: POST /concepts/compound-aliases/{uid}/archive
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Compound Alias with library_name set to the archived library.
    """
    alias = TestUtils.create_compound_alias(
        name=f"Draft Alias To Archive {rand}",
        compound_uid=compounds_all[0].uid,
        approve=False,
    )

    response = api_client.post(f"/concepts/compound-aliases/{alias.uid}/archive")
    res = parse_json_response(response, assert_status=200)

    assert res["library_name"] == settings.archived_library_name
    assert res["name"] == alias.name


def test_archiving_compound_alias_final(api_client):
    """
    SCENARIO: archiving a Compound Alias in Final status
    GIVEN: a Compound Alias in Final (approved) status
    WHEN: POST /concepts/compound-aliases/{uid}/archive
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Compound Alias with library_name set to the archived library.
    """
    # Use an approved compound so the alias can also be approved
    approved_compound = compounds_all[5]  # index 5 is the first approve=True compound
    alias = TestUtils.create_compound_alias(
        name=f"Final Alias To Archive {rand}",
        compound_uid=approved_compound.uid,
        approve=True,
    )

    response = api_client.post(f"/concepts/compound-aliases/{alias.uid}/archive")
    res = parse_json_response(response, assert_status=200)

    assert res["library_name"] == settings.archived_library_name


def test_can_not_archive_already_archived_compound_alias(api_client):
    """
    SCENARIO: attempting to archive an already-archived Compound Alias
    GIVEN: Compound Aliases that are already archived
    WHEN: POST /concepts/compound-aliases/{uid}/archive for each archived Compound Alias
    THEN: should respond with 400 HTTP status code and an error message indicating the Compound Alias
          is already in the archived library.
    """
    for alias in archived_compound_aliases:
        uid = alias.uid
        response = api_client.post(f"/concepts/compound-aliases/{uid}/archive")
        res = parse_json_response(response, assert_status=400)

        assert (
            res["message"]
            == f"Concept with UID '{uid}' is already in '{settings.archived_library_name}' library."
        )


def test_can_not_create_new_version_of_archived_compound_alias(api_client):
    """
    SCENARIO: attempting to create a new version of an archived Compound Alias
    GIVEN: Compound Aliases that are already archived
    WHEN: POST /concepts/compound-aliases/{uid}/versions for each archived Compound Alias
    THEN: should respond with 400 HTTP status code and an error message indicating the library
          is not editable.
    """
    for alias in archived_compound_aliases:
        response = api_client.post(f"/concepts/compound-aliases/{alias.uid}/versions")
        res = parse_json_response(response, assert_status=400)

        assert res["message"] == "Library isn't editable."


def test_can_not_edit_archived_compound_alias(api_client):
    """
    SCENARIO: attempting to edit an archived Compound Alias
    GIVEN: Compound Aliases that are already archived
    WHEN: PATCH /concepts/compound-aliases/{uid} for each archived Compound Alias
    THEN: should respond with 400 HTTP status code and an error message indicating the library
          is not editable.
    """
    for alias in archived_compound_aliases:
        response = api_client.patch(
            f"/concepts/compound-aliases/{alias.uid}",
            json={
                "name": "Edited Archived Alias",
                "compound_uid": compounds_all[0].uid,
                "change_description": "edit attempt on archived",
            },
        )
        res = parse_json_response(response, assert_status=400)

        assert res["message"] == "Library isn't editable."


@pytest.mark.xfail(
    reason="Backend issue: Uniqueness checks do not exclude Archived library"
)
def test_allow_recreating_archived_compound_alias(api_client):
    """
    SCENARIO: re-creating a Compound Alias with the same name as an archived one
    GIVEN: Compound Aliases that are already archived
    WHEN: POST /concepts/compound-aliases with the same name and compound_uid as the archived Compound Alias
    THEN: should respond with 201 HTTP status code and JSON payload,
          containing the newly created Compound Alias with the same name.
    """
    for alias in archived_compound_aliases:
        alias_dict = alias.model_dump()
        alias_dict["library_name"] = settings.sponsor_library_name
        alias_dict["compound_uid"] = compounds_all[0].uid
        input_model = CompoundAliasCreateInput(**alias_dict)

        response = api_client.post(
            "/concepts/compound-aliases",
            json=input_model.model_dump(),
        )
        res = parse_json_response(response, assert_status=201)

        assert res["name"] == alias.name


# ===========================================================================
# CompoundAlias linking to archived Compound tests
# ===========================================================================


def test_forbid_creating_compound_alias_for_archived_compound(api_client):
    """
    SCENARIO: creating a Compound Alias linked to an archived Compound
    GIVEN: an archived Compound in the database
    WHEN: POST /concepts/compound-aliases with compound_uid pointing to the archived Compound
    THEN: should respond with 400 HTTP status code and JSON payload, with an error message.
    """
    archived_compound = archived_compounds[0]

    response = api_client.post(
        "/concepts/compound-aliases",
        json={
            "name": f"Alias for archived compound {rand}",
            "compound_uid": archived_compound.uid,
            "library_name": settings.sponsor_library_name,
        },
    )
    parse_json_response(response, assert_status=400)


def test_forbid_linking_compound_alias_to_archived_compound(api_client):
    """
    SCENARIO: updating an existing Compound Alias to link to an archived Compound
    GIVEN: an existing Compound Alias in the database, and an archived Compound in the database
    WHEN: PATCH /concepts/compound-aliases/{uid} with compound_uid pointing to the archived Compound
    THEN: should respond with 400 HTTP status code and JSON payload, with an error message.
    """
    alias = TestUtils.create_compound_alias(
        name=f"Alias to relink to archived {rand}", compound_uid=compounds_all[0].uid
    )
    archived_compound = archived_compounds[0]

    response = api_client.patch(
        f"/concepts/compound-aliases/{alias.uid}",
        json={
            "name": alias.name,
            "compound_uid": archived_compound.uid,
            "change_description": "attempting to link to archived compound",
        },
    )
    parse_json_response(response, assert_status=400)


def test_delete_draft_compound(api_client):
    """
    SCENARIO: deleting a draft Compound
    GIVEN: an existing draft Compound
    WHEN: DELETE /concepts/compounds/{uid}
    THEN: should respond with 204 HTTP status code
    """

    compound = TestUtils.create_compound(approve=False)

    response = api_client.delete(f"/concepts/compounds/{compound.uid}")
    assert_response_status_code(response, 204)


def test_delete_archived_compound_fails(api_client):
    """
    SCENARIO: deleting an archived Compound
    GIVEN: an existing archived Compound
    WHEN: DELETE /concepts/compounds/{uid}
    THEN: should respond with 400 HTTP status code and JSON payload,
          with an error message that archived concepts cannot be deleted.
    """

    compound = TestUtils.create_compound(approve=False)
    TestUtils.archive_compound(compound.uid)

    response = api_client.delete(f"/concepts/compounds/{compound.uid}")
    resp = parse_json_response(response, assert_status=400)
    assert "Can't delete Compound" in resp["message"]


def test_delete_draft_compound_alias(api_client):
    """
    SCENARIO: deleting a draft Compound Alias
    GIVEN: an existing draft Compound Alias
    WHEN: DELETE /concepts/compound-aliases/{uid}
    THEN: should respond with 204 HTTP status code
    """

    alias = TestUtils.create_compound_alias(
        compound_uid=compounds_all[0].uid, approve=False
    )

    response = api_client.delete(f"/concepts/compound-aliases/{alias.uid}")
    assert_response_status_code(response, 204)


def test_delete_archived_compound_alias_fails(api_client):
    """
    SCENARIO: deleting an archived Compound Alias
    GIVEN: an existing archived Compound Alias
    WHEN: DELETE /concepts/compound-aliases/{uid}
    THEN: should respond with 400 HTTP status code and JSON payload,
          with an error message that archived concepts cannot be deleted.
    """

    alias = TestUtils.create_compound_alias(
        compound_uid=compounds_all[0].uid, approve=False
    )
    TestUtils.archive_compound_alias(alias.uid)

    response = api_client.delete(f"/concepts/compound-aliases/{alias.uid}")
    resp = parse_json_response(response, assert_status=400)
    assert "Can't delete Concept" in resp["message"]
