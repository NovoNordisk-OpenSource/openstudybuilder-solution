"""
Tests for /data-suppliers/rules endpoints
"""

import itertools
import json
import logging
from functools import reduce
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import CTCodelist
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.data_supplier_rules.data_supplier_rule import (
    DataSupplierRule,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
data_supplier_rules_all: list[DataSupplierRule]

# DataSupplierRule names must be unique, so tests generate a fresh one whenever
# they create a rule instead of reusing a single fixed literal.
_rule_name_counter = itertools.count(1)


def unique_rule_name(label: str = "Type") -> str:
    return f"{label} {next(_rule_name_counter)}"


DATA_SUPPLIER_RULE_NAME = unique_rule_name()
data_supplier_type_codelist: CTCodelist
data_supplier_type_term_1: CTTerm
data_supplier_type_term_2: CTTerm
data_supplier_type_term_edc_system: CTTerm
activity_grouping_data: dict[Any, Any]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    inject_and_clear_db("data-supplier-rule.api")
    inject_base_data()

    global data_supplier_rules_all
    global data_supplier_type_codelist
    global data_supplier_type_term_1
    global data_supplier_type_term_2
    global data_supplier_type_term_edc_system
    global activity_grouping_data

    data_supplier_type_codelist = TestUtils.create_ct_codelist(
        name="Data Supplier Type",
        sponsor_preferred_name="Data Supplier Type",
        extensible=True,
        approve=True,
        submission_value=settings.data_supplier_type_cl_submval,
        catalogue_name=settings.sdtm_ct_catalogue_name,
    )
    data_supplier_type_term_1 = TestUtils.create_ct_term(
        codelist_uid=data_supplier_type_codelist.codelist_uid,
        sponsor_preferred_name_sentence_case="type one",
        sponsor_preferred_name="Type One",
    )
    data_supplier_type_term_2 = TestUtils.create_ct_term(
        codelist_uid=data_supplier_type_codelist.codelist_uid,
        sponsor_preferred_name_sentence_case="type two",
        sponsor_preferred_name="Type Two",
    )
    data_supplier_type_term_edc_system = TestUtils.create_ct_term(
        codelist_uid=data_supplier_type_codelist.codelist_uid,
        submission_value=settings.edc_system_data_supplier_type_submval,
        sponsor_preferred_name_sentence_case="edc system",
        sponsor_preferred_name="EDC System",
    )

    activity_group = TestUtils.create_activity_group(
        name="Data Supplier Rule test group"
    )
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="Data Supplier Rule test subgroup"
    )
    activity = TestUtils.create_activity(
        name="Data Supplier Rule test activity",
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
    )
    activity_grouping_data = {
        "activity_uid": activity.uid,
        "activity_group_uid": activity_group.uid,
        "activity_subgroup_uid": activity_subgroup.uid,
    }

    # Create some data_supplier_rules
    data_supplier_rules_all = [
        TestUtils.create_data_supplier_rule(
            description="Description A",
            name=DATA_SUPPLIER_RULE_NAME,
            activity_groupings=[activity_grouping_data],
        ),
        TestUtils.create_data_supplier_rule(
            description="Description AAA",
            name=unique_rule_name(),
            activity_groupings=[activity_grouping_data],
        ),
        TestUtils.create_data_supplier_rule(
            description="Description BBB",
            name=unique_rule_name(),
            activity_groupings=[activity_grouping_data],
        ),
        TestUtils.create_data_supplier_rule(
            description="Description XXX",
            name=unique_rule_name(),
            activity_groupings=[activity_grouping_data],
        ),
        TestUtils.create_data_supplier_rule(
            description="Description YYY",
            name=unique_rule_name(),
            activity_groupings=[activity_grouping_data],
        ),
    ]

    for index in range(5):
        data_supplier_rules_all.append(
            TestUtils.create_data_supplier_rule(
                description=f"Description AAA {index}",
                name=unique_rule_name(),
                activity_groupings=[activity_grouping_data],
            )
        )


RULE_FIELDS_ALL = [
    "uid",
    "description",
    "name",
    "data_supplier_type",
    "activity_groupings",
    "library_name",
    "possible_actions",
    "version",
    "status",
    "start_date",
    "end_date",
    "change_description",
    "author_username",
]

RULE_FIELDS_NOT_NULL = [
    "uid",
    "name",
    "start_date",
]


def test_get_data_supplier_rule(api_client):
    response = api_client.get(f"/data-suppliers/rules/{data_supplier_rules_all[0].uid}")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(res.keys()) == set(RULE_FIELDS_ALL)
    for key in RULE_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == data_supplier_rules_all[0].uid
    assert res["description"] == "Description A"
    assert res["name"] == DATA_SUPPLIER_RULE_NAME
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert res["library_name"] == "Sponsor"
    assert res["possible_actions"] == ["edit", "inactivate"]


def test_get_data_supplier_rule_pagination(api_client):
    results_paginated: dict[Any, Any] = {}
    sort_by = '{"description": true}'
    for page_number in range(1, 4):
        url = f"/data-suppliers/rules?page_number={page_number}&page_size=10&sort_by={sort_by}"
        response = api_client.get(url)
        res = response.json()
        res_descriptions = [item["description"] for item in res["items"]]
        results_paginated[page_number] = res_descriptions
        log.info("Page %s: %s", page_number, res_descriptions)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        reduce(lambda a, b: list(a) + list(b), list(results_paginated.values()))
    )
    log.info("All rows returned by pagination: %s", results_paginated_merged)

    res_all = api_client.get(
        f"/data-suppliers/rules?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = [x["description"] for x in res_all["items"]]
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(data_supplier_rules_all) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, None, None, 10),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 1, True, None, 10),
        pytest.param(10, 1, True, '{"description": false}', 10),
    ],
)
def test_get_data_supplier_rules(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    url = "/data-suppliers/rules"
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
    assert res["total"] == (len(data_supplier_rules_all) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(item.keys()) == set(RULE_FIELDS_ALL)
        for key in RULE_FIELDS_NOT_NULL:
            assert item[key] is not None

    if sort_by:
        # sort_by is JSON string in the form: {"sort_field_name": is_ascending_order}
        sort_by_dict = json.loads(sort_by)
        sort_field: str = next(iter(sort_by_dict.keys()))
        sort_order_ascending: bool = next(iter(sort_by_dict.values()))

        # extract list of values of 'sort_field_name' field from the returned result
        result_vals = [x[sort_field] for x in res["items"]]
        result_vals_sorted_locally = result_vals.copy()
        result_vals_sorted_locally.sort(reverse=not sort_order_ascending)
        assert result_vals == result_vals_sorted_locally


def test_get_data_supplier_rule_versions(api_client):
    response = api_client.get(
        f"/data-suppliers/rules/{data_supplier_rules_all[0].uid}/versions"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    assert len(res) == 2
    assert res[0]["uid"] == data_supplier_rules_all[0].uid
    assert res[0]["status"] == "Final"
    assert res[0]["version"] == "1.0"

    assert res[1]["uid"] == data_supplier_rules_all[0].uid
    assert res[1]["status"] == "Draft"
    assert res[1]["version"] == "0.1"


@pytest.mark.parametrize(
    "field_name",
    [
        pytest.param("uid"),
        pytest.param("description"),
    ],
)
def test_headers(api_client, field_name):
    response = api_client.get(
        f"/data-suppliers/rules/headers?field_name={field_name}&page_size=100"
    )
    res = response.json()

    assert_response_status_code(response, 200)
    expected_result = []
    for data_supplier_rule in data_supplier_rules_all:
        value = getattr(data_supplier_rule, field_name)
        if value:
            expected_result.append(value)
    log.info("Expected result is %s", expected_result)
    log.info("Returned %s", res)
    if expected_result:
        assert len(res) > 0
        assert len(set(expected_result)) == len(res)
        assert all(item in res for item in expected_result)
    else:
        assert len(res) == 0


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
def test_get_data_supplier_rules_csv_xml_excel(api_client, export_format):
    url = "data-suppliers/rules"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["aaa"]}}', "description", "Description AAA"),
        pytest.param('{"*": {"v": ["bBb"]}}', "description", "Description BBB"),
        pytest.param('{"*": {"v": ["zzz"]}}', None, None),
    ],
)
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    url = f"/data-suppliers/rules?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    if expected_result_prefix:
        assert len(res["items"]) > 0
        for row in res["items"]:
            assert row[expected_matched_field].startswith(expected_result_prefix)
    else:
        assert len(res["items"]) == 0


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result",
    [
        pytest.param(
            '{"description": {"v": ["Description AAA"]}}',
            "description",
            "Description AAA",
        ),
        pytest.param('{"description": {"v": ["nope"]}}', None, None),
        pytest.param(
            f'{{"name": {{"v": ["{DATA_SUPPLIER_RULE_NAME}"]}}}}',
            "name",
            DATA_SUPPLIER_RULE_NAME,
        ),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    url = f"/data-suppliers/rules?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    if expected_result:
        assert len(res["items"]) > 0

        nested_path = None
        if isinstance(expected_matched_field, str) and "." in expected_matched_field:
            nested_path = expected_matched_field.split(".")
            expected_matched_field = nested_path[-1]
            nested_path = nested_path[:-1]

        for row in res["items"]:
            current_row = row
            if nested_path:
                for prop in nested_path:
                    current_row = current_row[prop]
            assert current_row[expected_matched_field] == expected_result
    else:
        assert len(res["items"]) == 0


def test_filtering_wildcard_no_duplicates_with_activity_groupings(api_client):
    """Regression: a data_supplier_rule with activity groupings (a to-many relationship) must not
    be returned multiple times when a wildcard filter traverses that relationship."""
    data_supplier_rule = TestUtils.create_data_supplier_rule(
        description="Description WILDCARD_DEDUP",
        name=unique_rule_name(),
        activity_groupings=[activity_grouping_data],
    )

    url = '/data-suppliers/rules?filters={"*": {"v": ["WILDCARD_DEDUP"]}}&total_count=true'
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    matching_uids = [
        item["uid"] for item in res["items"] if item["uid"] == data_supplier_rule.uid
    ]
    assert len(matching_uids) == 1
    assert res["total"] == 1


def test_edit_data_supplier_rule(api_client):
    data_supplier_rule = TestUtils.create_data_supplier_rule(
        description="Data Supplier Rule to edit",
        name=unique_rule_name(),
        activity_groupings=[activity_grouping_data],
    )

    new_name = unique_rule_name()

    response = api_client.patch(
        f"/data-suppliers/rules/{data_supplier_rule.uid}",
        json={
            "description": "new description for data_supplier_rule",
            "name": new_name,
            "change_description": "Updated via API",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["description"] == "new description for data_supplier_rule"
    assert res["name"] == new_name
    assert res["version"] == "2.0"
    assert res["status"] == "Final"
    assert res["possible_actions"] == ["edit", "inactivate"]
    assert res["library_name"] == "Sponsor"
    # activity_groupings was omitted from the PATCH payload, so it must be left unchanged
    assert len(res["activity_groupings"]) == 1
    assert (
        res["activity_groupings"][0]["activity_uid"]
        == activity_grouping_data["activity_uid"]
    )

    response = api_client.get(f"/data-suppliers/rules/{data_supplier_rule.uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["description"] == "new description for data_supplier_rule"
    assert res["name"] == new_name
    assert res["version"] == "2.0"
    assert res["status"] == "Final"
    assert res["possible_actions"] == ["edit", "inactivate"]
    assert res["library_name"] == "Sponsor"
    assert len(res["activity_groupings"]) == 1
    assert (
        res["activity_groupings"][0]["activity_uid"]
        == activity_grouping_data["activity_uid"]
    )


def test_edit_data_supplier_rule_activity_groupings(api_client):
    data_supplier_rule = TestUtils.create_data_supplier_rule(
        description="Data Supplier Rule to edit - activity groupings",
        name=unique_rule_name(),
        activity_groupings=[activity_grouping_data],
    )

    response = api_client.get(f"/data-suppliers/rules/{data_supplier_rule.uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert len(res["activity_groupings"]) == 1
    assert (
        res["activity_groupings"][0]["activity_uid"]
        == activity_grouping_data["activity_uid"]
    )

    response = api_client.patch(
        f"/data-suppliers/rules/{data_supplier_rule.uid}",
        json={
            "activity_groupings": None,
            "change_description": "Updated activity groupings via API",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert len(res["activity_groupings"]) == 1
    assert (
        res["activity_groupings"][0]["activity_uid"]
        == activity_grouping_data["activity_uid"]
    )

    response = api_client.get(f"/data-suppliers/rules/{data_supplier_rule.uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert len(res["activity_groupings"]) == 1
    assert (
        res["activity_groupings"][0]["activity_uid"]
        == activity_grouping_data["activity_uid"]
    )


def test_post_data_supplier_rule(api_client):
    rule_name = unique_rule_name()
    response = api_client.post(
        "/data-suppliers/rules",
        json={
            "description": "New Data Supplier Rule Desc",
            "name": rule_name,
            "activity_groupings": [activity_grouping_data],
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["description"] == "New Data Supplier Rule Desc"
    assert res["name"] == rule_name
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert res["possible_actions"] == ["edit", "inactivate"]
    assert res["library_name"] == "Sponsor"


def test_post_data_supplier_rule_duplicate_name(api_client):
    rule_name = unique_rule_name()
    response = api_client.post(
        "/data-suppliers/rules",
        json={
            "description": "First rule with this name",
            "name": rule_name,
            "activity_groupings": [activity_grouping_data],
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.post(
        "/data-suppliers/rules",
        json={
            "description": "Second rule reusing the same name",
            "name": rule_name,
            "activity_groupings": [activity_grouping_data],
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 400)


def test_patch_data_supplier_rule_duplicate_name(api_client):
    rule_a = TestUtils.create_data_supplier_rule(
        description="Rule A",
        name=unique_rule_name(),
        activity_groupings=[activity_grouping_data],
    )
    rule_b = TestUtils.create_data_supplier_rule(
        description="Rule B",
        name=unique_rule_name(),
        activity_groupings=[activity_grouping_data],
    )

    # Renaming rule_b to rule_a's name is rejected
    response = api_client.patch(
        f"/data-suppliers/rules/{rule_b.uid}",
        json={
            "name": rule_a.name,
            "change_description": "Attempt to reuse another rule's name",
        },
    )
    assert_response_status_code(response, 400)

    # Keeping rule_b's own name unchanged (e.g. while patching another field) is allowed
    response = api_client.patch(
        f"/data-suppliers/rules/{rule_b.uid}",
        json={
            "name": rule_b.name,
            "description": "Updated description, same name",
            "change_description": "Update description only",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["name"] == rule_b.name
    assert res["description"] == "Updated description, same name"
    # activity_groupings was omitted from the PATCH payload, so it must be left unchanged
    assert len(res["activity_groupings"]) == 1
    assert (
        res["activity_groupings"][0]["activity_uid"]
        == activity_grouping_data["activity_uid"]
    )


def test_post_data_supplier_rule_missing_name(api_client):
    response = api_client.post(
        "/data-suppliers/rules",
        json={
            "description": "Bad Data Supplier Rule",
            "activity_groupings": [activity_grouping_data],
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 400)


def test_post_data_supplier_rule_with_activity_groupings(api_client):
    response = api_client.post(
        "/data-suppliers/rules",
        json={
            "description": "Data Supplier Rule with groupings",
            "name": unique_rule_name(),
            "activity_groupings": [activity_grouping_data],
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert len(res["activity_groupings"]) == 1
    grouping = res["activity_groupings"][0]
    assert grouping["activity_uid"] == activity_grouping_data["activity_uid"]
    assert (
        grouping["activity_group_uid"] == activity_grouping_data["activity_group_uid"]
    )
    assert (
        grouping["activity_subgroup_uid"]
        == activity_grouping_data["activity_subgroup_uid"]
    )

    # Verify the groupings are returned on GET as well
    get_response = api_client.get(f"/data-suppliers/rules/{res['uid']}")
    assert_response_status_code(get_response, 200)
    get_res = get_response.json()
    assert len(get_res["activity_groupings"]) == 1
    assert (
        get_res["activity_groupings"][0]["activity_uid"]
        == activity_grouping_data["activity_uid"]
    )


def test_post_data_supplier_rule_non_existent_activity_grouping(api_client):
    response = api_client.post(
        "/data-suppliers/rules",
        json={
            "description": "Data Supplier Rule with bad grouping",
            "name": unique_rule_name(),
            "activity_groupings": [
                {
                    "activity_uid": "NonExistent",
                    "activity_group_uid": "NonExistent",
                    "activity_subgroup_uid": "NonExistent",
                }
            ],
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 400)


def test_data_supplier_rule_versioning(api_client):
    data_supplier_rule = TestUtils.create_data_supplier_rule(
        description="Data Supplier Rule for versioning",
        name=unique_rule_name(),
        activity_groupings=[activity_grouping_data],
    )

    # not successful reactivate
    response = api_client.post(
        f"/data-suppliers/rules/{data_supplier_rule.uid}/activations"
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == "Only RETIRED version can be reactivated."

    # successful inactivate
    response = api_client.delete(
        f"/data-suppliers/rules/{data_supplier_rule.uid}/activations"
    )
    assert_response_status_code(response, 200)

    # successful reactivate
    response = api_client.post(
        f"/data-suppliers/rules/{data_supplier_rule.uid}/activations"
    )
    assert_response_status_code(response, 200)


def test_post_data_supplier_rule_with_data_supplier_type(api_client):
    response = api_client.post(
        "/data-suppliers/rules",
        json={
            "description": "Data Supplier Rule with type",
            "name": unique_rule_name(),
            "activity_groupings": [activity_grouping_data],
            "data_supplier_type_uid": data_supplier_type_term_1.term_uid,
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["data_supplier_type"]["uid"] == data_supplier_type_term_1.term_uid
    assert res["data_supplier_type"]["name"] is not None

    # Verify type is returned on GET single as well
    get_response = api_client.get(f"/data-suppliers/rules/{res['uid']}")
    assert_response_status_code(get_response, 200)
    get_res = get_response.json()
    assert get_res["data_supplier_type"]["uid"] == data_supplier_type_term_1.term_uid

    # Verify type is returned on GET list as well
    list_response = api_client.get(
        f'/data-suppliers/rules?filters={{"uid": {{"v": ["{res["uid"]}"]}}}}'
    )
    assert_response_status_code(list_response, 200)
    list_res = list_response.json()
    listed_item = next(item for item in list_res["items"] if item["uid"] == res["uid"])
    assert (
        listed_item["data_supplier_type"]["uid"] == data_supplier_type_term_1.term_uid
    )


def test_post_data_supplier_rule_non_existent_data_supplier_type(api_client):
    response = api_client.post(
        "/data-suppliers/rules",
        json={
            "description": "Data Supplier Rule with bad type",
            "name": unique_rule_name(),
            "data_supplier_type_uid": "NonExistentType",
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 400)


def test_patch_data_supplier_rule_data_supplier_type(api_client):
    data_supplier_rule = TestUtils.create_data_supplier_rule(
        description="Data Supplier Rule to edit type",
        name=unique_rule_name(),
        activity_groupings=[activity_grouping_data],
        data_supplier_type_uid=data_supplier_type_term_1.term_uid,
    )
    assert (
        data_supplier_rule.data_supplier_type.uid == data_supplier_type_term_1.term_uid
    )

    # Update to a different type
    response = api_client.patch(
        f"/data-suppliers/rules/{data_supplier_rule.uid}",
        json={
            "data_supplier_type_uid": data_supplier_type_term_2.term_uid,
            "change_description": "Update data supplier type",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["data_supplier_type"]["uid"] == data_supplier_type_term_2.term_uid
    # activity_groupings was omitted from the PATCH payload, so it must be left unchanged
    assert len(res["activity_groupings"]) == 1
    assert (
        res["activity_groupings"][0]["activity_uid"]
        == activity_grouping_data["activity_uid"]
    )

    # Explicitly disconnect the data supplier type
    response = api_client.patch(
        f"/data-suppliers/rules/{data_supplier_rule.uid}",
        json={
            "data_supplier_type_uid": "",
            "change_description": "Remove data supplier type",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["data_supplier_type"] is None
    # activity_groupings was again omitted from the PATCH payload, so it must still be unchanged
    assert len(res["activity_groupings"]) == 1
    assert (
        res["activity_groupings"][0]["activity_uid"]
        == activity_grouping_data["activity_uid"]
    )


def test_post_data_supplier_rule_rejects_edc_system_data_supplier_type(api_client):
    response = api_client.post(
        "/data-suppliers/rules",
        json={
            "description": "Data Supplier Rule with EDC System type",
            "name": unique_rule_name(),
            "activity_groupings": [activity_grouping_data],
            "data_supplier_type_uid": data_supplier_type_term_edc_system.term_uid,
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 400)


def test_patch_data_supplier_rule_rejects_edc_system_data_supplier_type(api_client):
    data_supplier_rule = TestUtils.create_data_supplier_rule(
        description="Data Supplier Rule to attempt attaching EDC System type",
        name=unique_rule_name(),
        activity_groupings=[activity_grouping_data],
        data_supplier_type_uid=data_supplier_type_term_1.term_uid,
    )

    response = api_client.patch(
        f"/data-suppliers/rules/{data_supplier_rule.uid}",
        json={
            "data_supplier_type_uid": data_supplier_type_term_edc_system.term_uid,
            "change_description": "Attempt to move rule to EDC System type",
        },
    )
    assert_response_status_code(response, 400)


def test_post_data_supplier_rule_rejects_multiple_data_supplier_types(api_client):
    # The API only accepts a single data supplier type uid per rule; sending a
    # list is rejected by request validation.
    response = api_client.post(
        "/data-suppliers/rules",
        json={
            "description": "Data Supplier Rule with multiple types",
            "name": unique_rule_name(),
            "activity_groupings": [activity_grouping_data],
            "data_supplier_type_uid": [
                data_supplier_type_term_1.term_uid,
                data_supplier_type_term_2.term_uid,
            ],
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 400)
