"""
Tests for /concepts/active-substances endpoints
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
from clinical_mdr_api.models.concepts.active_substance import (
    ActiveSubstance,
    ActiveSubstanceCreateInput,
)
from clinical_mdr_api.models.dictionaries.dictionary_codelist import DictionaryCodelist
from clinical_mdr_api.models.dictionaries.dictionary_term import DictionaryTerm
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

HEADERS = {"content-type": "application/json"}

# Global variables shared between fixtures and tests
active_substances_all: list[ActiveSubstance]
archived_active_substances: list[ActiveSubstance]
dictionary_term_unii: DictionaryTerm
unii_codelist: DictionaryCodelist


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "active-substances.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global active_substances_all
    global dictionary_term_unii
    global unii_codelist

    TestUtils.create_library("UNII")
    unii_codelist = TestUtils.create_dictionary_codelist(
        name="UNII", library_name="UNII"
    )
    dictionary_term_unii = TestUtils.create_dictionary_term(
        codelist_uid=unii_codelist.codelist_uid,
        library_name=unii_codelist.library_name,
        dictionary_id="P7YU3ED05N",
        name="INSULIN ICODEC",
    )

    # Create some active substances
    active_substances_all = []
    active_substances_all.append(
        TestUtils.create_active_substance(
            unii_term_uid=dictionary_term_unii.term_uid,
            external_id="external_id_a",
            analyte_number="analyte A",
            short_number="short number A",
            long_number="long number A",
            inn="inn A",
        )
    )

    active_substances_all.append(
        TestUtils.create_active_substance(analyte_number="analyte_number-AAA")
    )
    active_substances_all.append(
        TestUtils.create_active_substance(analyte_number="analyte_number-BBB")
    )
    active_substances_all.append(
        TestUtils.create_active_substance(short_number="short_number-XXX")
    )
    active_substances_all.append(
        TestUtils.create_active_substance(short_number="short_number-YYY")
    )

    for index in range(5):
        active_substance_a = TestUtils.create_active_substance(
            analyte_number=f"analyte_number-AAA-{index}"
        )
        active_substances_all.append(active_substance_a)

        active_substance_b = TestUtils.create_active_substance(
            analyte_number=f"analyte_number-BBB-{index}"
        )
        active_substances_all.append(active_substance_b)

        active_substance_c = TestUtils.create_active_substance(
            short_number=f"short_number-XXX-{index}"
        )
        active_substances_all.append(active_substance_c)

        active_substance_d = TestUtils.create_active_substance(
            short_number=f"short_number-YYY-{index}"
        )
        active_substances_all.append(active_substance_d)

    global archived_active_substances
    archived_active_substances = [
        TestUtils.create_active_substance(analyte_number="archived-analyte-A"),
        TestUtils.create_active_substance(analyte_number="archived-analyte-B"),
    ]
    for ast in archived_active_substances:
        TestUtils.archive_active_substance(ast.uid)

    yield


ACTIVE_SUBSTANCE_FIELDS_ALL = [
    "uid",
    "library_name",
    "start_date",
    "end_date",
    "status",
    "version",
    "change_description",
    "author_username",
    "possible_actions",
    "analyte_number",
    "short_number",
    "long_number",
    "inn",
    "external_id",
    "unii",
]

ACTIVE_SUBSTANCE_FIELDS_NOT_NULL = ["uid", "analyte_number", "start_date"]


def test_get_active_substance(api_client):
    """
    SCENARIO: Retrieve a single active substance by UID
    GIVEN an active substance with UNII term, analyte/short/long number, inn, and external_id exists
    WHEN GET /concepts/active-substances/{uid} is called
    THEN 200 is returned with all expected fields, correct values, version 0.1, status Draft, and a valid UTC start_date
    """
    response = api_client.get(
        f"/concepts/active-substances/{active_substances_all[0].uid}"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(res.keys()) == set(ACTIVE_SUBSTANCE_FIELDS_ALL)
    for key in ACTIVE_SUBSTANCE_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == active_substances_all[0].uid
    assert res["analyte_number"] == "analyte A"
    assert res["short_number"] == "short number A"
    assert res["long_number"] == "long number A"
    assert res["inn"] == "inn A"
    assert res["external_id"] == "external_id_a"
    assert res["unii"]["substance_term_uid"] == dictionary_term_unii.term_uid
    assert res["unii"]["substance_name"] == dictionary_term_unii.name
    assert res["unii"]["substance_unii"] == dictionary_term_unii.dictionary_id

    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)


def test_get_active_substances_versions(api_client):
    """
    SCENARIO: Retrieve all versions of active substances
    GIVEN active substances exist including archived ones
    WHEN GET /concepts/active-substances/versions?total_count=true is called
    THEN 200 is returned with 10 items per page, total count equals all + archived, and all required fields are non-null
    """
    response = api_client.get("/concepts/active-substances/versions?total_count=true")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res["items"]) == 10
    assert res["total"] == len(active_substances_all) + len(archived_active_substances)

    for item in res["items"]:
        assert set(list(item.keys())) == set(ACTIVE_SUBSTANCE_FIELDS_ALL)
        for key in ACTIVE_SUBSTANCE_FIELDS_NOT_NULL:
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
def test_get_active_substances_versions_csv_xml_excel(api_client, export_format):
    """
    SCENARIO: Export active substance versions in CSV, XML, and Excel formats
    GIVEN active substances exist
    WHEN GET /concepts/active-substances/versions is called with Accept header for csv/xml/excel
    THEN 200 is returned with data in the requested export format
    """
    url = "/concepts/active-substances/versions"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


def test_update_active_substance_property(api_client):
    """
    SCENARIO: Update active substance properties via PATCH
    GIVEN an active substance in Draft status exists
    WHEN PATCH /concepts/active-substances/{uid} is called with updated analyte_number, nullified inn, and unii changes
    THEN 200 is returned after each patch with updated values, correct version bump, and valid UTC start_date
    """
    payload: dict[Any, Any]
    # First try a dummy patch with no new property values in the payload
    payload = {
        "unii_term_uid": dictionary_term_unii.term_uid,
        "change_description": "dummy updated",
    }
    response = api_client.patch(
        f"/concepts/active-substances/{active_substances_all[0].uid}",
        data=json.dumps(payload),
        headers=HEADERS,
    )
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["uid"] == active_substances_all[0].uid
    assert res["analyte_number"] == active_substances_all[0].analyte_number
    assert res["short_number"] == active_substances_all[0].short_number
    assert res["long_number"] == active_substances_all[0].long_number
    assert res["inn"] == active_substances_all[0].inn
    assert res["external_id"] == active_substances_all[0].external_id
    assert res["unii"]["substance_term_uid"] == dictionary_term_unii.term_uid
    assert res["unii"]["substance_name"] == dictionary_term_unii.name
    assert res["unii"]["substance_unii"] == dictionary_term_unii.dictionary_id

    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    # Another dummy patch with no new property values in the payload
    payload = {
        "change_description": "dummy update",
    }
    response = api_client.patch(
        f"/concepts/active-substances/{active_substances_all[0].uid}",
        data=json.dumps(payload),
        headers=HEADERS,
    )
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["uid"] == active_substances_all[0].uid
    assert res["analyte_number"] == active_substances_all[0].analyte_number
    assert res["short_number"] == active_substances_all[0].short_number
    assert res["long_number"] == active_substances_all[0].long_number
    assert res["inn"] == active_substances_all[0].inn
    assert res["external_id"] == active_substances_all[0].external_id
    assert res["unii"]["substance_term_uid"] == dictionary_term_unii.term_uid
    assert res["unii"]["substance_name"] == dictionary_term_unii.name
    assert res["unii"]["substance_unii"] == dictionary_term_unii.dictionary_id

    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    # Update analyte number
    analyte_number_new = f"{active_substances_all[0].analyte_number}-updated"
    payload = {
        "analyte_number": analyte_number_new,
        "unii_term_uid": dictionary_term_unii.term_uid,
        "change_description": "analyte number updated",
    }
    response = api_client.patch(
        f"/concepts/active-substances/{active_substances_all[0].uid}",
        data=json.dumps(payload),
        headers=HEADERS,
    )
    res = response.json()

    assert_response_status_code(response, 200)

    assert res["uid"] == active_substances_all[0].uid
    assert res["analyte_number"] == analyte_number_new
    assert res["short_number"] == active_substances_all[0].short_number
    assert res["long_number"] == active_substances_all[0].long_number
    assert res["inn"] == active_substances_all[0].inn
    assert res["external_id"] == active_substances_all[0].external_id
    assert res["unii"]["substance_term_uid"] == dictionary_term_unii.term_uid
    assert res["unii"]["substance_name"] == dictionary_term_unii.name
    assert res["unii"]["substance_unii"] == dictionary_term_unii.dictionary_id

    assert res["version"] == "0.2"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)

    # Nullify inn
    payload = {
        "inn": None,
        "change_description": "inn set to null",
    }
    response = api_client.patch(
        f"/concepts/active-substances/{active_substances_all[0].uid}",
        data=json.dumps(payload),
        headers=HEADERS,
    )
    res = response.json()

    assert_response_status_code(response, 200)

    assert res["uid"] == active_substances_all[0].uid
    assert res["analyte_number"] == analyte_number_new
    assert res["short_number"] == active_substances_all[0].short_number
    assert res["long_number"] == active_substances_all[0].long_number
    assert res["inn"] is None
    assert res["external_id"] == active_substances_all[0].external_id
    assert res["unii"]["substance_term_uid"] == dictionary_term_unii.term_uid
    assert res["unii"]["substance_name"] == dictionary_term_unii.name
    assert res["unii"]["substance_unii"] == dictionary_term_unii.dictionary_id

    assert res["version"] == "0.3"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)


def test_update_active_substance_unii(api_client):
    """
    SCENARIO: Update and nullify UNII term on an active substance
    GIVEN an active substance in Draft status exists
    WHEN PATCH /concepts/active-substances/{uid} is called to change the UNII term, then to nullify it
    THEN 200 is returned each time with updated UNII data, then null UNII, and correct version bumps
    """
    unii_term_new = TestUtils.create_dictionary_term(
        codelist_uid=unii_codelist.codelist_uid,
        library_name=unii_codelist.library_name,
        dictionary_id="UNII123",
        name="Substance 123",
    )

    payload: dict[Any, Any]
    # Change unii value
    payload = {
        "unii_term_uid": unii_term_new.term_uid,
        "change_description": "unii updated",
    }
    response = api_client.patch(
        f"/concepts/active-substances/{active_substances_all[1].uid}",
        data=json.dumps(payload),
        headers=HEADERS,
    )
    res = response.json()

    assert_response_status_code(response, 200)

    assert res["uid"] == active_substances_all[1].uid
    assert res["short_number"] == active_substances_all[1].short_number
    assert res["long_number"] == active_substances_all[1].long_number
    assert res["inn"] == active_substances_all[1].inn
    assert res["external_id"] == active_substances_all[1].external_id
    assert res["unii"]["substance_term_uid"] == unii_term_new.term_uid
    assert res["unii"]["substance_name"] == unii_term_new.name
    assert res["unii"]["substance_unii"] == unii_term_new.dictionary_id

    assert res["version"] == "0.2"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)

    # Nullify unii value
    payload = {
        "unii_term_uid": None,
        "change_description": "unii updated",
    }
    response = api_client.patch(
        f"/concepts/active-substances/{active_substances_all[1].uid}",
        data=json.dumps(payload),
        headers=HEADERS,
    )
    res = response.json()

    assert_response_status_code(response, 200)

    assert res["uid"] == active_substances_all[1].uid
    assert res["unii"] is None

    assert res["version"] == "0.3"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]


def test_get_active_substance_versioning(api_client):
    """
    SCENARIO: Full lifecycle versioning of an active substance
    GIVEN an active substance in Draft status exists
    WHEN approve, new_version, approve, inactivate, reactivate, and get versions are called in sequence
    THEN each action returns the correct version number, status, and possible_actions; final version list is sorted newest first
    """
    uid = active_substances_all[3].uid

    response = api_client.get(f"/concepts/active-substances/{uid}/versions")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    for item in res:
        assert set(list(item.keys())) == set(ACTIVE_SUBSTANCE_FIELDS_ALL)
        for key in ACTIVE_SUBSTANCE_FIELDS_NOT_NULL:
            assert item[key] is not None

        assert item["uid"] == uid

    # Approve draft version
    response = api_client.post(f"/concepts/active-substances/{uid}/approvals")
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["version"] == "1.0"
    assert res["status"] == "Final"

    # Create new version
    response = api_client.post(f"/concepts/active-substances/{uid}/versions")
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["version"] == "1.1"
    assert res["status"] == "Draft"
    assert res["possible_actions"] == ["approve", "edit"]

    # Approve draft version
    response = api_client.post(f"/concepts/active-substances/{uid}/approvals")
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["version"] == "2.0"
    assert res["status"] == "Final"
    assert res["possible_actions"] == ["inactivate", "new_version"]

    # Inactivate final version
    response = api_client.delete(f"/concepts/active-substances/{uid}/activations")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["version"] == "2.0"
    assert res["status"] == "Retired"
    assert res["possible_actions"] == ["reactivate"]

    # Reactivate retired version
    response = api_client.post(f"/concepts/active-substances/{uid}/activations")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["version"] == "2.0"
    assert res["status"] == "Final"
    assert res["possible_actions"] == ["inactivate", "new_version"]

    # Get all versions, assert they are sorted by version number (newest on top)
    response = api_client.get(f"/concepts/active-substances/{uid}/versions")
    res = response.json()
    assert_response_status_code(response, 200)

    assert len(res) == 6

    assert res[0]["version"] == "2.0"
    assert res[0]["status"] == "Final"
    assert res[0]["possible_actions"] == ["inactivate", "new_version"]

    assert res[1]["version"] == "2.0"
    assert res[1]["status"] == "Retired"
    assert res[1]["possible_actions"] == ["reactivate"]

    assert res[2]["version"] == "2.0"
    assert res[2]["status"] == "Final"
    assert res[2]["possible_actions"] == ["inactivate", "new_version"]

    assert res[3]["version"] == "1.1"
    assert res[3]["status"] == "Draft"
    assert res[3]["possible_actions"] == ["approve", "edit"]

    assert res[4]["version"] == "1.0"
    assert res[4]["status"] == "Final"
    assert res[4]["possible_actions"] == ["inactivate", "new_version"]

    assert res[5]["version"] == "0.1"
    assert res[5]["status"] == "Draft"
    assert res[5]["possible_actions"] == ["approve", "delete", "edit"]


def test_get_active_substances_pagination(api_client):
    """
    SCENARIO: Paginated listing of active substances returns consistent results
    GIVEN multiple active substances exist
    WHEN the list endpoint is fetched across multiple pages (page_size=10) and in one large page (page_size=100)
    THEN the unique merged paginated results match the single-page result count and equal the fixture count
    """
    results_paginated: dict[Any, Any] = {}
    sort_by = '{"analyte_number": true}'
    for page_number in range(1, 4):
        url = f"/concepts/active-substances?page_number={page_number}&page_size=10&sort_by={sort_by}"
        response = api_client.get(url)
        res = response.json()
        res_analyte_numbers = [item["analyte_number"] for item in res["items"]]
        results_paginated[page_number] = res_analyte_numbers
        log.info("Page %s: %s", page_number, res_analyte_numbers)

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
        f"/concepts/active-substances?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["analyte_number"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(active_substances_all) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, None, None, 10),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 10),
        pytest.param(10, 3, True, None, 5),  # Total number of active substances is 25
        pytest.param(10, 1, True, '{"analyte_number": false}', 10),
        pytest.param(10, 2, True, '{"analyte_number": true}', 10),
    ],
)
def test_get_active_substances(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    """
    SCENARIO: List active substances with various pagination and sort parameters
    GIVEN active substances exist in the system
    WHEN GET /concepts/active-substances is called with parametrized page_size, page_number, total_count, sort_by
    THEN 200 is returned with the correct number of items, pagination metadata and all required fields; results are correctly sorted when sort_by is given
    """
    url = "/concepts/active-substances"
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
    assert res["total"] == (len(active_substances_all) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(ACTIVE_SUBSTANCE_FIELDS_ALL)
        for key in ACTIVE_SUBSTANCE_FIELDS_NOT_NULL:
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
        result_vals_sorted_locally = sorted(
            result_vals_sorted_locally,
            key=lambda x: (x is None, x),
            reverse=not sort_order_ascending,
        )
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
def test_get_active_substances_csv_xml_excel(api_client, export_format):
    """
    SCENARIO: Export active substances in CSV, XML, and Excel formats
    GIVEN active substances exist
    WHEN GET /concepts/active-substances is called with Accept header for csv/xml/excel
    THEN 200 is returned with data in the requested export format
    """
    url = "/concepts/active-substances"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["aaa"]}}', "analyte_number", "analyte_number-AAA"),
        pytest.param('{"*": {"v": ["bBb"]}}', "analyte_number", "analyte_number-BBB"),
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
    SCENARIO: Wildcard filter on active substances list
    GIVEN active substances with varied analyte numbers, statuses and versions exist
    WHEN GET /concepts/active-substances is called with a wildcard filter
    THEN 200 is returned and each result row contains a field starting with the filter prefix, or no results when no match
    """
    url = f"/concepts/active-substances?filters={filter_by}"
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
            '{"analyte_number": {"v": ["analyte_number-AAA"]}}',
            "analyte_number",
            "analyte_number-AAA",
        ),
        pytest.param(
            '{"analyte_number": {"v": ["analyte_number-BBB"]}}',
            "analyte_number",
            "analyte_number-BBB",
        ),
        pytest.param('{"analyte_number": {"v": ["cc"]}}', None, None),
        pytest.param(
            '{"short_number": {"v": ["short_number-XXX"]}}',
            "short_number",
            "short_number-XXX",
        ),
        pytest.param(
            '{"short_number": {"v": ["short_number-YYY"]}}',
            "short_number",
            "short_number-YYY",
        ),
        pytest.param('{"short_number": {"v": ["cc"]}}', None, None),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    """
    SCENARIO: Exact filter on active substances list
    GIVEN active substances with specific analyte and short numbers exist
    WHEN GET /concepts/active-substances is called with an exact-match filter
    THEN 200 is returned and each result row has the filtered field exactly equal to the expected value, or no results when no match
    """
    url = f"/concepts/active-substances?filters={filter_by}"
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


@pytest.mark.parametrize(
    "field_name, expected_returned_values",
    [
        pytest.param("analyte_number", ["analyte_number-AAA", "analyte_number-BBB"]),
        pytest.param("short_number", ["short_number-XXX", "short_number-YYY"]),
        pytest.param("long_number", ["long number A"]),
    ],
)
def test_get_active_substances_headers(
    api_client, field_name, expected_returned_values
):
    """
    SCENARIO: Retrieve distinct header values for a given active substance field
    GIVEN active substances with varied analyte_number, short_number, and long_number values exist
    WHEN GET /concepts/active-substances/headers?field_name={field_name} is called
    THEN 200 is returned with a list containing at least the expected values
    """
    url = f"/concepts/active-substances/headers?field_name={field_name}&page_size=100"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) >= len(expected_returned_values)
    for val in expected_returned_values:
        assert val in res


def test_create_and_delete_active_substance(api_client):
    """
    SCENARIO: Create a new active substance then delete it
    GIVEN no active substance with the new analyte_number exists
    WHEN POST /concepts/active-substances is called with full payload, then DELETE is called on the returned uid
    THEN 201 is returned with correct field values on create; 204 on delete; 404 on subsequent GET
    """
    # Create new active substance
    payload = {
        "library_name": "Sponsor",
        "analyte_number": "analyte_number-NEW",
        "short_number": "short_number-NEW",
        "long_number": "long_number-NEW",
        "inn": "inn-NEW",
        "external_id": "external_id-NEW",
        "unii_term_uid": dictionary_term_unii.term_uid,
    }
    response = api_client.post(
        "/concepts/active-substances", data=json.dumps(payload), headers=HEADERS
    )
    res = response.json()

    assert_response_status_code(response, 201)
    assert res["analyte_number"] == "analyte_number-NEW"
    assert res["short_number"] == "short_number-NEW"
    assert res["long_number"] == "long_number-NEW"
    assert res["inn"] == "inn-NEW"
    assert res["external_id"] == "external_id-NEW"
    assert res["unii"]["substance_term_uid"] == dictionary_term_unii.term_uid
    assert res["unii"]["substance_name"] == dictionary_term_unii.name
    assert res["unii"]["substance_unii"] == dictionary_term_unii.dictionary_id

    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)

    # Delete active substance
    response = api_client.delete(f"/concepts/active-substances/{res['uid']}")
    assert_response_status_code(response, 204)

    # Check that the active substance is deleted
    response = api_client.get(f"/concepts/active-substances/{res['uid']}")
    assert_response_status_code(response, 404)


def test_negative_delete_approved_active_substance(api_client):
    """
    SCENARIO: Attempt to delete an approved active substance
    GIVEN an active substance in Final (approved) status exists
    WHEN DELETE /concepts/active-substances/{uid} is called
    THEN 400 is returned with message "Object has been accepted" and the substance is still retrievable
    """
    item = TestUtils.create_active_substance(approve=True)

    # Try to delete approved active substance
    response = api_client.delete(f"/concepts/active-substances/{item.uid}")
    assert_response_status_code(response, 400)
    assert response.json()["message"] == "Object has been accepted"

    # Check that the active substance is not deleted
    response = api_client.get(f"/concepts/active-substances/{item.uid}")
    assert_response_status_code(response, 200)


def test_negative_create_active_substance_wrong_links(api_client):
    """
    SCENARIO: Attempt to create an active substance with a non-existing UNII UID
    GIVEN no UNII term with UID 'NON_EXISTING_UID' exists
    WHEN POST /concepts/active-substances is called with unii_term_uid set to 'NON_EXISTING_UID'
    THEN 400 is returned with a message indicating the UNII term does not exist
    """
    # Try to create new active substance with non-existing UNII uid
    payload = {
        "analyte_number": "analyte_number_new",
        "unii_term_uid": "NON_EXISTING_UID",
        "library_name": "Sponsor",
    }
    response = api_client.post(
        "/concepts/active-substances", data=json.dumps(payload), headers=HEADERS
    )
    res = response.json()

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "ActiveSubstanceVO tried to connect to non existing UNII Term with UID 'NON_EXISTING_UID'."
    )


def test_get_active_substances_excludes_archived(api_client):
    """
    SCENARIO: listing Active Substances excluding archived ones
    GIVEN: multiple Active Substances in the database, some archived
    WHEN: GET /concepts/active-substances
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing all existing Active Substances, excluding archived Active Substances.
    """

    response = api_client.get("/concepts/active-substances", params={"page_size": 1000})
    payload = parse_json_response(response, assert_status=200)

    items = payload["items"]
    assert len(items) > 0
    for item in items:
        assert item["library_name"] != settings.archived_library_name


def test_get_archived_active_substances(api_client):
    """
    SCENARIO: getting archived Active Substances
    GIVEN: multiple Active Substances in the database, some archived
    WHEN: GET /concepts/active-substances?library_name=Archived
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing only the archived Active Substances.
    """
    response = api_client.get(
        "/concepts/active-substances",
        params={"library_name": settings.archived_library_name, "page_size": 1000},
    )
    payload = parse_json_response(response, assert_status=200)

    items = payload["items"]
    assert len(items) > 0
    for item in items:
        assert item["library_name"] == settings.archived_library_name


def test_get_active_substance_by_uid_returns_archived(api_client):
    """
    SCENARIO: getting a single archived Active Substance by UID
    GIVEN: an archived Active Substance in the database
    WHEN: GET /concepts/active-substances/{uid}
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Active Substance with library_name set to 'Archived'.
    """
    archived_ast = archived_active_substances[0]
    response = api_client.get(f"/concepts/active-substances/{archived_ast.uid}")
    res = parse_json_response(response, assert_status=200)

    assert res["uid"] == archived_ast.uid
    assert res["library_name"] == settings.archived_library_name


def test_archived_active_substance_excluded_from_headers(api_client):
    """
    SCENARIO: getting headers of Active Substances with archived Active Substances in the database
    GIVEN: an existing Active Substance in the database, later archived
    WHEN: GET /concepts/active-substances/headers?field_name=analyte_number
    THEN: should respond with 200 HTTP status code and JSON payload,
          with the archived Active Substance excluded from the results.
    """
    # Create an Active Substance
    active_substance = TestUtils.create_active_substance(
        analyte_number="canary-analyte-number"
    )

    # Get headers — the new substance should appear
    response = api_client.get(
        "/concepts/active-substances/headers",
        params={"field_name": "analyte_number", "search_string": "canary"},
    )
    payload = parse_json_response(response, assert_status=200)
    assert isinstance(payload, list)
    assert active_substance.analyte_number in payload

    # Archive the Active Substance
    TestUtils.archive_active_substance(active_substance.uid)

    # Get headers again — the archived substance should no longer appear
    response = api_client.get(
        "/concepts/active-substances/headers",
        params={"field_name": "analyte_number", "search_string": "canary"},
    )
    payload = parse_json_response(response, assert_status=200)
    assert isinstance(payload, list)
    assert active_substance.analyte_number not in payload


def test_archiving_active_substance_draft(api_client):
    """
    SCENARIO: archiving an Active Substance in Draft status
    GIVEN: an Active Substance in Draft status
    WHEN: POST /concepts/active-substances/{uid}/archive
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Active Substance with library_name set to the archived library.
    """
    active_substance = TestUtils.create_active_substance(
        analyte_number="Draft Substance To Archive", approve=False
    )

    response = api_client.post(
        f"/concepts/active-substances/{active_substance.uid}/archive"
    )
    res = parse_json_response(response, assert_status=200)

    assert res["library_name"] == settings.archived_library_name
    assert res["analyte_number"] == active_substance.analyte_number


def test_archiving_active_substance_final(api_client):
    """
    SCENARIO: archiving an Active Substance in Final status
    GIVEN: an Active Substance in Final (approved) status
    WHEN: POST /concepts/active-substances/{uid}/archive
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Active Substance with library_name set to the archived library.
    """
    active_substance = TestUtils.create_active_substance(
        analyte_number="Final Substance To Archive"
    )

    response = api_client.post(
        f"/concepts/active-substances/{active_substance.uid}/archive"
    )
    res = parse_json_response(response, assert_status=200)

    assert res["library_name"] == settings.archived_library_name


def test_can_not_archive_already_archived_active_substance(api_client):
    """
    SCENARIO: attempting to archive an already-archived Active Substance
    GIVEN: Active Substances that are already archived
    WHEN: POST /concepts/active-substances/{uid}/archive for each archived substance
    THEN: should respond with 400 HTTP status code and an error message indicating the substance
          is already in the archived library.
    """
    for active_substance in archived_active_substances:
        uid = active_substance.uid
        response = api_client.post(f"/concepts/active-substances/{uid}/archive")
        res = parse_json_response(response, assert_status=400)

        assert (
            res["message"]
            == f"Concept with UID '{uid}' is already in '{settings.archived_library_name}' library."
        )


def test_can_not_create_new_version_of_archived_active_substance(api_client):
    """
    SCENARIO: attempting to create a new version of an archived Active Substance
    GIVEN: Active Substances that are already archived
    WHEN: POST /concepts/active-substances/{uid}/versions for each archived substance
    THEN: should respond with 400 HTTP status code and an error message indicating the library
          is not editable.
    """
    for active_substance in archived_active_substances:
        response = api_client.post(
            f"/concepts/active-substances/{active_substance.uid}/versions"
        )
        res = parse_json_response(response, assert_status=400)

        assert res["message"] == "Library isn't editable."


def test_can_not_edit_archived_active_substance(api_client):
    """
    SCENARIO: attempting to edit an archived Active Substance
    GIVEN: Active Substances that are already archived
    WHEN: PATCH /concepts/active-substances/{uid} for each archived substance
    THEN: should respond with 400 HTTP status code and an error message indicating the library
          is not editable.
    """
    for active_substance in archived_active_substances:
        response = api_client.patch(
            f"/concepts/active-substances/{active_substance.uid}",
            json={
                "short_number": TestUtils.random_str(prefix="short-number-"),
                "change_description": "edit attempt on archived",
            },
        )
        res = parse_json_response(response, assert_status=400)

        assert res["message"] == "Library isn't editable."


@pytest.mark.xfail(
    reason="Backend issue: Uniqueness checks do not exclude Archived library"
)
def test_allow_recreating_archived_active_substance(api_client):
    """
    SCENARIO: re-creating an Active Substance with the same name as an archived one
    GIVEN: Active Substances that are already archived
    WHEN: POST /concepts/active-substances with the same analyte_number as the archived substance
    THEN: should respond with 201 HTTP status code and JSON payload,
          containing the newly created Active Substance with the same analyte_number.
    """
    for active_substance in archived_active_substances:
        substance_dict = active_substance.model_dump()
        substance_dict["library_name"] = settings.sponsor_library_name

        # the model has "unii", input expects "unii_term_uid"
        if active_substance.unii:
            substance_dict["unii_term_uid"] = active_substance.unii.substance_term_uid

        input_model = ActiveSubstanceCreateInput(**substance_dict)

        response = api_client.post(
            "/concepts/active-substances",
            json=input_model.model_dump(),
        )
        res = parse_json_response(response, assert_status=201)

        assert res["analyte_number"] == active_substance.analyte_number


def test_delete_draft_active_substance(api_client):
    """
    SCENARIO: deleting a draft Active Substance
    GIVEN: an existing draft Active Substance
    WHEN: DELETE /concepts/active-substances/{uid}
    THEN: should respond with 204 HTTP status code
    """

    active_substance = TestUtils.create_active_substance(approve=False)

    response = api_client.delete(f"/concepts/active-substances/{active_substance.uid}")
    assert_response_status_code(response, 204)


def test_delete_archived_active_substance_fails(api_client):
    """
    SCENARIO: deleting an archived Active Substance
    GIVEN: an existing archived Active Substance
    WHEN: DELETE /concepts/active-substances/{uid}
    THEN: should respond with 400 HTTP status code and JSON payload,
          with an error message that archived concepts cannot be deleted.
    """

    active_substance = TestUtils.create_active_substance(approve=False)
    TestUtils.archive_active_substance(active_substance.uid)

    response = api_client.delete(f"/concepts/active-substances/{active_substance.uid}")
    resp = parse_json_response(response, assert_status=400)
    assert "Can't delete Concept" in resp["message"]
