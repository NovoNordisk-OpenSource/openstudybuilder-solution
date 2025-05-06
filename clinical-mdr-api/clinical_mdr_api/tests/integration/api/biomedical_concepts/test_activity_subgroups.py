"""
Tests for /concepts/activities/activity-sub-groups endpoints
"""

import json
import logging
from operator import itemgetter

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.concepts.activities.activity_group import ActivityGroup
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivitySubGroup,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
activity_group_1: ActivityGroup
activity_group_2: ActivityGroup
activity_group_3: ActivityGroup
activity_subgroups_all: list[ActivitySubGroup]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "activitiessubgroups.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global activity_group_1
    activity_group_1 = TestUtils.create_activity_group(name="A activity_group")
    global activity_group_2
    activity_group_2 = TestUtils.create_activity_group(name="B activity_group")
    global activity_group_3
    activity_group_3 = TestUtils.create_activity_group(name="C activity_group")

    global activity_subgroups_all
    activity_subgroups_all = [
        TestUtils.create_activity_subgroup(
            name="name-AAA", activity_groups=[activity_group_1.uid]
        ),
        TestUtils.create_activity_subgroup(
            name="name-BBB", activity_groups=[activity_group_2.uid]
        ),
    ]

    for index in range(5):
        activity_subgroups_all.append(
            TestUtils.create_activity_subgroup(
                name=f"ActivityGroup-{index}", activity_groups=[activity_group_3.uid]
            )
        )

    yield


ACTIVITY_SUBGROUP_FIELDS_ALL = [
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
    "possible_actions",
    "author_username",
    "activity_groups",
]

ACTIVITY_SUBGROUP_FIELDS_NOT_NULL = ["uid", "name", "start_date", "activity_groups"]


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, None, None, 7),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 0),
        pytest.param(10, 3, True, None, 0),  # Total number of activity sub groups is 7
        pytest.param(10, 1, True, '{"activity_groups": false}', 7),
        pytest.param(10, 1, True, '{"activity_groups": true}', 7),
    ],
)
def test_get_activity_subgroups(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    url = "/concepts/activities/activity-sub-groups"
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
    assert res["total"] == (len(activity_subgroups_all) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(ACTIVITY_SUBGROUP_FIELDS_ALL)
        for key in ACTIVITY_SUBGROUP_FIELDS_NOT_NULL:
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
        if sort_field == "activity_groups":
            result_vals_sorted_locally.sort(
                reverse=not sort_order_ascending, key=lambda group: group[0]["name"]
            )
        else:
            result_vals_sorted_locally.sort(reverse=not sort_order_ascending)
        assert result_vals == result_vals_sorted_locally


def test_get_activity_subgroup(api_client):
    response = api_client.get(
        f"/concepts/activities/activity-sub-groups/{activity_subgroups_all[0].uid}"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(list(res.keys())) == set(ACTIVITY_SUBGROUP_FIELDS_ALL)
    for key in ACTIVITY_SUBGROUP_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == activity_subgroups_all[0].uid
    assert res["name"] == "name-AAA"
    assert res["name_sentence_case"] == "name-AAA"
    assert res["library_name"] == "Sponsor"
    assert res["definition"] is None
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_get_activity_subgroups_versions(api_client):
    # Create a new version of an activity group
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{activity_subgroups_all[0].uid}/versions"
    )
    assert_response_status_code(response, 201)

    # Get all versions of all activities
    response = api_client.get(
        "/concepts/activities/activity-sub-groups/versions?page_size=100"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(list(res.keys())) == set(["items", "total", "page", "size"])

    assert len(res["items"]) == len(activity_subgroups_all) * 2 + 1
    for item in res["items"]:
        assert set(list(item.keys())) == set(ACTIVITY_SUBGROUP_FIELDS_ALL)
        for key in ACTIVITY_SUBGROUP_FIELDS_NOT_NULL:
            assert item[key] is not None

    # Check that the items are sorted by start_date descending
    sorted_items = sorted(res["items"], key=itemgetter("start_date"), reverse=True)
    assert sorted_items == res["items"]


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["aaa"]}}', "name", "name-AAA"),
        pytest.param('{"*": {"v": ["bBb"]}}', "name", "name-BBB"),
        pytest.param('{"*": {"v": ["ccc"]}}', None, None),
        pytest.param('{"*": {"v": ["Final"]}}', "status", "Final"),
        pytest.param('{"*": {"v": ["1.0"]}}', "version", "1.0"),
    ],
)
def test_filtering_versions_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    url = f"/concepts/activities/activity-sub-groups/versions?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    if expected_result_prefix:
        assert len(res["items"]) > 0
        nested_path = None

        # if we expect a nested property to be equal to specified value
        if isinstance(expected_matched_field, str) and "." in expected_matched_field:
            nested_path = expected_matched_field.split(".")
            expected_matched_field = nested_path[-1]
            nested_path = nested_path[:-1]

        # Each returned row has a field that starts with the specified filter value
        for row in res["items"]:
            if nested_path:
                for prop in nested_path:
                    row = row[prop]
            if isinstance(row, list):
                any(
                    item[expected_matched_field].startswith(expected_result_prefix)
                    for item in row
                )
            else:
                assert row[expected_matched_field].startswith(expected_result_prefix)
    else:
        assert len(res["items"]) == 0


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result",
    [
        pytest.param('{"name": {"v": ["name-AAA"]}}', "name", "name-AAA"),
        pytest.param('{"name": {"v": ["name-BBB"]}}', "name", "name-BBB"),
        pytest.param('{"name": {"v": ["cc"]}}', None, None),
        pytest.param(
            '{"name_sentence_case": {"v": ["name-AAA"]}}',
            "name_sentence_case",
            "name-AAA",
        ),
        pytest.param(
            '{"name_sentence_case": {"v": ["name-BBB"]}}',
            "name_sentence_case",
            "name-BBB",
        ),
        pytest.param('{"name_sentence_case": {"v": ["cc"]}}', None, None),
    ],
)
def test_filtering_versions_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    url = f"/concepts/activities/activity-sub-groups/versions?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    if expected_result:
        assert len(res["items"]) > 0

        # if we expect a nested property to be equal to specified value
        nested_path = None
        if isinstance(expected_matched_field, str) and "." in expected_matched_field:
            nested_path = expected_matched_field.split(".")
            expected_matched_field = nested_path[-1]
            nested_path = nested_path[:-1]

        # Each returned row has a field whose value is equal to the specified filter value
        for row in res["items"]:
            if nested_path:
                for prop in nested_path:
                    row = row[prop]
            if isinstance(expected_result, list):
                assert all(
                    item in row[expected_matched_field] for item in expected_result
                )
            else:
                if isinstance(row, list):
                    all(item[expected_matched_field] == expected_result for item in row)
                else:
                    assert row[expected_matched_field] == expected_result
    else:
        assert len(res["items"]) == 0


def test_update_subgroup_to_new_group(api_client):
    original_group_name = "original group name"
    subgroup_name = "original subgroup name"
    edited_group_name = "edited group name"

    # ==== Create group and subgroup ====
    group = TestUtils.create_activity_group(name=original_group_name)

    subgroup = TestUtils.create_activity_subgroup(
        name=subgroup_name, activity_groups=[group.uid]
    )

    # ==== Update group ====
    # Create new version of subgroup
    response = api_client.post(
        f"/concepts/activities/activity-groups/{group.uid}/versions",
        json={},
    )
    assert_response_status_code(response, 201)

    # Patch the group
    response = api_client.patch(
        f"/concepts/activities/activity-groups/{group.uid}",
        json={
            "name": edited_group_name,
            "name_sentence_case": edited_group_name,
            "change_description": "patch group",
        },
    )
    assert_response_status_code(response, 200)

    # Approve the group
    response = api_client.post(
        f"/concepts/activities/activity-groups/{group.uid}/approvals"
    )

    # === Assert that the group was updated as expected ===
    response = api_client.get(f"/concepts/activities/activity-groups/{group.uid}")

    assert_response_status_code(response, 200)
    res = response.json()

    assert res["name"] == edited_group_name
    assert res["version"] == "2.0"
    assert res["status"] == "Final"

    # ==== Update subgroup ====

    # Create new version of subgroup
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{subgroup.uid}/versions",
        json={},
    )
    assert_response_status_code(response, 201)

    # Patch the subgroup, no changes
    response = api_client.patch(
        f"/concepts/activities/activity-sub-groups/{subgroup.uid}",
        json={
            "change_description": "patch subgroup",
        },
    )
    assert_response_status_code(response, 200)

    # Approve the subgroup
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{subgroup.uid}/approvals"
    )
    assert_response_status_code(response, 201)

    # Get the activity by uid and assert that it was updated to the new group version
    response = api_client.get(
        f"/concepts/activities/activity-sub-groups/{subgroup.uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["version"] == "2.0"
    assert res["status"] == "Final"

    assert res["name"] == subgroup_name
    assert len(res["activity_groups"]) == 1

    assert res["activity_groups"][0]["uid"] == group.uid
    assert res["activity_groups"][0]["name"] == edited_group_name
