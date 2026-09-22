"""
Tests for /concepts/activities/activity-sub-groups endpoints
"""

import json
import logging
from operator import itemgetter

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivitySubGroup,
    ActivitySubGroupCreateInput,
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

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
activity_subgroups_all: list[ActivitySubGroup]
archived_activity_subgroups: list[ActivitySubGroup]


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

    global activity_subgroups_all
    activity_subgroups_all = [
        TestUtils.create_activity_subgroup(name="name-AAA"),
        TestUtils.create_activity_subgroup(name="name-BBB"),
    ]

    for index in range(5):
        activity_subgroups_all.append(
            TestUtils.create_activity_subgroup(name=f"ActivityGroup-{index}")
        )

    global archived_activity_subgroups
    archived_activity_subgroups = [
        TestUtils.create_activity_subgroup(name="Archived SubGroup A"),
        TestUtils.create_activity_subgroup(name="Archived SubGroup B"),
    ]
    for asg in archived_activity_subgroups:
        TestUtils.archive_activity_subgroup(asg.uid)

    yield


ACTIVITY_SUBGROUP_FIELDS_ALL = [
    "uid",
    "name",
    "name_sentence_case",
    "nci_concept_id",
    "nci_concept_name",
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
]

ACTIVITY_SUBGROUP_FIELDS_NOT_NULL = ["uid", "name", "start_date"]


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, None, None, 7),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 0),
        pytest.param(10, 3, True, None, 0),  # Total number of activity sub groups is 7
    ],
)
def test_get_activity_subgroups(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    """
    SCENARIO: listing Activity Sub Groups with pagination and sorting
    GIVEN: multiple Activity Sub Groups in the database
    WHEN: GET /concepts/activities/activity-sub-groups with optional page_size, page_number,
          total_count and sort_by parameters
    THEN: should respond with 200 and a paginated payload with the expected number of items,
          correct page/size metadata, and all expected fields present and non-null.
    """
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
        result_vals_sorted_locally.sort(reverse=not sort_order_ascending)
        assert result_vals == result_vals_sorted_locally


def test_get_activity_subgroup(api_client):
    """
    SCENARIO: getting a single Activity Sub Group by uid
    GIVEN: an existing Activity Sub Group in the database
    WHEN: GET /concepts/activities/activity-sub-groups/{uid}
    THEN: should respond with 200, with all expected fields present, non-null fields non-null,
          and field values matching the created Activity Sub Group.
    """
    response = api_client.get(
        f"/concepts/activities/activity-sub-groups/{activity_subgroups_all[0].uid}"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(res.keys()) == set(ACTIVITY_SUBGROUP_FIELDS_ALL)
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
    """
    SCENARIO: getting all versions of all Activity Sub Groups
    GIVEN: multiple Activity Sub Groups in the database, one of which gets a new version created
    WHEN: GET /concepts/activities/activity-sub-groups/versions?page_size=100
    THEN: should respond with 200 and a paginated list containing all versions sorted by
          start_date descending, with all expected fields present and non-null fields non-null.
    """
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
    assert set(res.keys()) == set(["items", "total", "page", "size"])

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
    """
    SCENARIO: wildcard filtering of Activity Sub Group versions
    GIVEN: multiple existing Activity Sub Group versions in the database
    WHEN: GET /concepts/activities/activity-sub-groups/versions?filters={filter_by}
    THEN: should respond with 200; if a prefix is expected, every returned item's matched field
          starts with expected_result_prefix; if no prefix, zero items are returned.
    """
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
    """
    SCENARIO: exact field filtering of Activity Sub Group versions
    GIVEN: multiple existing Activity Sub Group versions in the database
    WHEN: GET /concepts/activities/activity-sub-groups/versions?filters={filter_by}
    THEN: should respond with 200; if a result is expected, every returned item's matched field
          equals expected_result; if no result, zero items are returned.
    """
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


def test_cascade_edit_activity_subgroups(api_client):
    """
    SCENARIO: cascade editing an Activity Sub Group propagates changes to linked Activities and Instances
    GIVEN: an Activity Sub Group linked to an Activity (with two groupings) and Activity Instance
    WHEN: PUT /concepts/activities/activity-sub-groups/{uid} + POST …/approvals?cascade_edit_and_approve=True
    THEN: the linked Activity and Activity Instance are both bumped to new Final versions
          with updated subgroup name across all groupings; no intermediate drafts persist.
    WHEN: PUT + POST …/approvals?cascade_edit_and_approve=False
    THEN: linked Activity and Activity Instance remain at their current versions unchanged.
    """
    # ==== Create activity and activity instance ====
    activity_group = TestUtils.create_activity_group(name="Cascade Group")
    second_activity_group = TestUtils.create_activity_group(name="Second Group")
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="Cascade SubGroup",
    )
    activity = TestUtils.create_activity(
        name="Cascade Activity",
        activity_subgroups=[activity_subgroup.uid, activity_subgroup.uid],
        activity_groups=[activity_group.uid, second_activity_group.uid],
        approve=True,
    )
    activity_instance_class = (
        TestUtils.create_activity_instance_class(
            name="Activity instance class",
            definition="def Activity instance class",
            is_domain_specific=True,
            level=1,
        ),
    )
    activity_instance = TestUtils.create_activity_instance(
        name="Cascade Activity Instance",
        activity_instance_class_uid=activity_instance_class[0].uid,
        name_sentence_case="cascade activity instance",
        nci_concept_id="C-1234",
        topic_code="cascade activity instance tc",
        activities=[activity.uid],
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        approve=True,
    )
    response = api_client.get(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup.uid}"
    )

    res = response.json()
    assert_response_status_code(response, 200)
    assert res["name"] == activity_subgroup.name
    assert res["version"] == "1.0"
    assert res["status"] == "Final"

    # ==== Update activity subgroup with cascade edit&approve, activity should be updated also ====

    # Create new version of activity
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup.uid}/versions",
        json={},
    )
    assert_response_status_code(response, 201)

    # Update the activity subgroup
    updated_activity_subgroup_name = "Edited Cascade Activity SubGroup"
    concept_id = "CONCEPT_ID"
    concept_name = "concept name"
    response = api_client.put(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup.uid}",
        json={
            "name": updated_activity_subgroup_name,
            "name_sentence_case": updated_activity_subgroup_name.lower(),
            "nci_concept_id": concept_id,
            "nci_concept_name": concept_name,
            "change_description": "test cascade edit",
            "library_name": activity_subgroup.library_name,
        },
    )
    assert_response_status_code(response, 200)

    # Approve the activity subgroup with cascade_edit_and_approve set to True
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup.uid}/approvals",
        params={"cascade_edit_and_approve": True},
    )
    assert_response_status_code(response, 201)

    # Assert Activity Subroup was updated
    response = api_client.get(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup.uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["name"] == updated_activity_subgroup_name
    assert res["name_sentence_case"] == updated_activity_subgroup_name.lower()
    assert res["nci_concept_id"] == concept_id
    assert res["nci_concept_name"] == concept_name
    assert res["status"] == "Final"
    assert res["version"] == "2.0"

    # Get the activity and assert that it was updated
    response = api_client.get(f"/concepts/activities/activities/{activity.uid}")
    assert_response_status_code(response, 200)
    res = response.json()

    # Assert that update Activity has the right groupings
    assert len(res["activity_groupings"]) == 2
    assert res["activity_groupings"][0]["activity_group_uid"] == activity_group.uid
    assert res["activity_groupings"][0]["activity_group_name"] == activity_group.name
    assert (
        res["activity_groupings"][0]["activity_subgroup_uid"] == activity_subgroup.uid
    )
    assert (
        res["activity_groupings"][0]["activity_subgroup_name"]
        == updated_activity_subgroup_name
    )
    assert (
        res["activity_groupings"][1]["activity_group_uid"] == second_activity_group.uid
    )
    assert (
        res["activity_groupings"][1]["activity_group_name"]
        == second_activity_group.name
    )
    assert (
        res["activity_groupings"][1]["activity_subgroup_uid"] == activity_subgroup.uid
    )
    assert (
        res["activity_groupings"][1]["activity_subgroup_name"]
        == updated_activity_subgroup_name
    )
    assert res["version"] == "2.0"
    assert res["status"] == "Final"

    # Get the activity instance and assert that it was updated
    response = api_client.get(
        f"/concepts/activities/activity-instances/{activity_instance.uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["activity_groupings"]) == 1
    assert res["activity_groupings"][0]["activity_group"]["uid"] == activity_group.uid
    assert res["activity_groupings"][0]["activity_group"]["name"] == activity_group.name
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["uid"]
        == activity_subgroup.uid
    )
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["name"]
        == updated_activity_subgroup_name
    )
    assert res["activity_groupings"][0]["activity"]["uid"] == activity.uid
    assert res["activity_groupings"][0]["activity"]["name"] == activity.name
    assert res["groupings_version"] == "2.0"
    assert res["groupings_status"] == "Final"

    # Get the activity subgroup versions and assert that two new versions were created.
    # There should be a draft version 1.1 that still links to activity group version 1.0 & 1.1,
    # a new draft version 1.2 that links to activity group version 2.0,
    # and a new final version 2.0 that links to activity group version 2.0
    response = api_client.get(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup.uid}/versions"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    unchanged_draft = TestUtils._get_version_from_list(res, "1.1")
    updated_draft = TestUtils._get_version_from_list(res, "1.2")
    new_final_subgroup = TestUtils._get_version_from_list(res, "2.0")
    assert updated_draft["name"] == updated_activity_subgroup_name
    assert new_final_subgroup["name"] == updated_activity_subgroup_name

    # Get the activity versions and assert that there is one new version created.
    # There should be a new final version 2.0 that links to activity subgroup version 2.0
    response = api_client.get(
        f"/concepts/activities/activities/{activity.uid}/versions"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    unchanged_draft = TestUtils._get_version_from_list(res, "1.1")
    updated_draft = TestUtils._get_version_from_list(res, "1.2")
    new_final = TestUtils._get_version_from_list(res, "2.0")

    assert unchanged_draft is None
    assert updated_draft is None
    assert len(new_final["activity_groupings"]) == 2
    assert (
        new_final["activity_groupings"][0]["activity_subgroup_name"]
        == updated_activity_subgroup_name
    )
    assert (
        new_final["activity_groupings"][0]["activity_group_name"] == activity_group.name
    )
    assert (
        new_final["activity_groupings"][1]["activity_subgroup_name"]
        == updated_activity_subgroup_name
    )
    assert (
        new_final["activity_groupings"][1]["activity_group_name"]
        == second_activity_group.name
    )

    # Get the activity instance versions and assert that there is one new version created.
    # There should be a new final version 2.0 that links to activity version 2.0
    response = api_client.get(
        f"/concepts/activities/activity-instances/{activity_instance.uid}/groupings/versions"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    unchanged_draft = TestUtils._get_version_from_list(res, "1.1")
    updated_draft = TestUtils._get_version_from_list(res, "1.2")
    new_final = TestUtils._get_version_from_list(res, "2.0")

    assert unchanged_draft is None
    assert updated_draft is None
    assert (
        new_final["activity_groupings"][0]["activity_subgroup"]["name"]
        == updated_activity_subgroup_name
    )
    assert len(new_final["activity_groupings"]) == 1

    # ==== Update activity subgroup without cascade edit&approve, activity activity should NOT be updated ====
    # Create new version of activity
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup.uid}/versions",
        json={},
    )
    assert_response_status_code(response, 201)

    # Put the activity subgroup
    second_updated_activity_subgroup_name = "Another update of activity subgroup name"
    response = api_client.put(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup.uid}",
        json={
            "name": second_updated_activity_subgroup_name,
            "name_sentence_case": second_updated_activity_subgroup_name.lower(),
            "activity_groups": [activity_group.uid, second_activity_group.uid],
            "change_description": "test cascade edit again",
            "library_name": activity_subgroup.library_name,
        },
    )
    assert_response_status_code(response, 200)

    # Approve the activity subgroup with cascade_edit_and_approve set to False
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup.uid}/approvals",
        params={"cascade_edit_and_approve": False},
    )
    assert_response_status_code(response, 201)

    # Get the activity and assert that it was not updated
    response = api_client.get(f"/concepts/activities/activities/{activity.uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["activity_groupings"]) == 2
    assert res["version"] == "2.0"
    assert res["status"] == "Final"
    assert (
        res["activity_groupings"][0]["activity_subgroup_name"]
        == updated_activity_subgroup_name
    )
    assert res["activity_groupings"][0]["activity_group_name"] == activity_group.name
    assert (
        res["activity_groupings"][1]["activity_subgroup_name"]
        == updated_activity_subgroup_name
    )
    assert (
        res["activity_groupings"][1]["activity_group_name"]
        == second_activity_group.name
    )

    # Get the activity instance and assert that it was not updated
    response = api_client.get(
        f"/concepts/activities/activity-instances/{activity_instance.uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["activity_groupings"]) == 1
    assert res["groupings_version"] == "2.0"
    assert res["groupings_status"] == "Final"
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["name"]
        == updated_activity_subgroup_name
    )


def test_get_activity_subgroups_excludes_archived(api_client):
    """
    SCENARIO: listing Activity Sub Groups excluding archived ones
    GIVEN: multiple Activity Sub Groups in the database, some archived
    WHEN: GET /concepts/activities/activity-sub-groups
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing all existing Activity Sub Groups, excluding archived Activity Sub Groups.
    """
    response = api_client.get(
        "/concepts/activities/activity-sub-groups", params={"page_size": 1000}
    )
    payload = parse_json_response(response, assert_status=200)

    items = payload["items"]
    assert len(items) > 0
    for item in items:
        assert item["library_name"] != settings.archived_library_name


def test_get_archived_activity_subgroups(api_client):
    """
    SCENARIO: getting archived Activity Sub Groups
    GIVEN: multiple Activity Sub Groups in the database, some archived
    WHEN: GET /concepts/activities/activity-sub-groups?library_name=Archived
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing only the archived Activity Sub Groups.
    """
    response = api_client.get(
        "/concepts/activities/activity-sub-groups",
        params={"library_name": settings.archived_library_name, "page_size": 1000},
    )
    payload = parse_json_response(response, assert_status=200)

    items = payload["items"]
    assert len(items) > 0
    for item in items:
        assert item["library_name"] == settings.archived_library_name
    for item in payload["items"]:
        assert item["library_name"] == settings.archived_library_name


def test_get_activity_subgroup_by_uid_returns_archived(api_client):
    """
    SCENARIO: getting a single archived Activity Sub Group by UID
    GIVEN: an archived Activity Sub Group in the database
    WHEN: GET /concepts/activities/activity-sub-groups/{uid}
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Activity Sub Group with library_name set to 'Archived'.
    """
    archived_asg = archived_activity_subgroups[0]
    response = api_client.get(
        f"/concepts/activities/activity-sub-groups/{archived_asg.uid}"
    )
    res = parse_json_response(response, assert_status=200)

    assert res["uid"] == archived_asg.uid
    assert res["library_name"] == settings.archived_library_name


def test_archived_activity_subgroup_excluded_from_headers(api_client):
    """
    SCENARIO: getting headers of Activity Sub Groups with archived Activity Sub Groups in the database
    GIVEN: an existing Activity Sub Group in the database, later archived
    WHEN: GET /concepts/activities/activity-sub-groups/headers?field_name=name
    THEN: should respond with 200 HTTP status code and JSON payload,
          with the archived Activity Sub Group excluded from the results.
    """
    # Create an Activity Sub Group
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="A Canary activity subgroup"
    )

    # Get headers — the new subgroup should appear
    response = api_client.get(
        "/concepts/activities/activity-sub-groups/headers",
        params={"field_name": "name", "search_string": "canary"},
    )
    payload = parse_json_response(response, assert_status=200)
    assert isinstance(payload, list)
    assert activity_subgroup.name in payload

    # Archive the Activity Sub Group
    TestUtils.archive_activity_subgroup(activity_subgroup.uid)

    # Get headers again — the archived subgroup should no longer appear
    response = api_client.get(
        "/concepts/activities/activity-sub-groups/headers",
        params={"field_name": "name", "search_string": "canary"},
    )
    payload = parse_json_response(response, assert_status=200)
    assert isinstance(payload, list)
    assert activity_subgroup.name not in payload


def test_archiving_activity_subgroup_draft(api_client):
    """
    SCENARIO: archiving an Activity Sub Group in Draft status
    GIVEN: an Activity Sub Group in Draft status
    WHEN: POST /concepts/activities/activity-sub-groups/{uid}/archive
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Activity Sub Group with library_name set to the archived library.
    """
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="Draft SubGroup To Archive", approve=False
    )

    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup.uid}/archive"
    )
    res = parse_json_response(response, assert_status=200)

    assert res["library_name"] == settings.archived_library_name
    assert res["name"] == activity_subgroup.name


def test_archiving_activity_subgroup_final(api_client):
    """
    SCENARIO: archiving an Activity Sub Group in Final status
    GIVEN: an Activity Sub Group in Final (approved) status
    WHEN: POST /concepts/activities/activity-sub-groups/{uid}/archive
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Activity Sub Group with library_name set to the archived library.
    """
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="Final SubGroup To Archive"
    )

    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup.uid}/archive"
    )
    res = parse_json_response(response, assert_status=200)

    assert res["library_name"] == settings.archived_library_name


def test_can_not_archive_already_archived_activity_subgroup(api_client):
    """
    SCENARIO: attempting to archive an already-archived Activity Sub Group
    GIVEN: Activity Sub Groups that are already archived
    WHEN: POST /concepts/activities/activity-sub-groups/{uid}/archive for each archived subgroup
    THEN: should respond with 400 HTTP status code and an error message indicating the subgroup
          is already in the archived library.
    """
    for activity_subgroup in archived_activity_subgroups:
        uid = activity_subgroup.uid
        response = api_client.post(
            f"/concepts/activities/activity-sub-groups/{uid}/archive"
        )
        res = parse_json_response(response, assert_status=400)

        assert (
            res["message"]
            == f"Concept with UID '{uid}' is already in '{settings.archived_library_name}' library."
        )


def test_can_not_create_new_version_of_archived_activity_subgroup(api_client):
    """
    SCENARIO: attempting to create a new version of an archived Activity Sub Group
    GIVEN: Activity Sub Groups that are already archived
    WHEN: POST /concepts/activities/activity-sub-groups/{uid}/versions for each archived subgroup
    THEN: should respond with 400 HTTP status code and an error message indicating the library
          is not editable.
    """
    for activity_subgroup in archived_activity_subgroups:
        response = api_client.post(
            f"/concepts/activities/activity-sub-groups/{activity_subgroup.uid}/versions"
        )
        res = parse_json_response(response, assert_status=400)

        assert res["message"] == "Library isn't editable."


def test_can_not_edit_archived_activity_subgroup(api_client):
    """
    SCENARIO: attempting to edit an archived Activity Sub Group
    GIVEN: Activity Sub Groups that are already archived
    WHEN: PUT /concepts/activities/activity-sub-groups/{uid} for each archived subgroup
    THEN: should respond with 400 HTTP status code and an error message indicating the library
          is not editable.
    """
    for activity_subgroup in archived_activity_subgroups:
        response = api_client.put(
            f"/concepts/activities/activity-sub-groups/{activity_subgroup.uid}",
            json={
                "name": "Edited Archived Subgroup",
                "name_sentence_case": "edited archived subgroup",
                "change_description": "edit attempt on archived",
                "library_name": settings.sponsor_library_name,
            },
        )
        res = parse_json_response(response, assert_status=400)

        assert res["message"] == "Library isn't editable."


def test_allow_recreating_archived_activity_subgroup(api_client):
    """
    SCENARIO: re-creating an Activity Sub Group with the same name as an archived one
    GIVEN: Activity Sub Groups that are already archived
    WHEN: POST /concepts/activities/activity-sub-groups with the same name as the archived subgroup
    THEN: should respond with 201 HTTP status code and JSON payload,
          containing the newly created Activity Sub Group with the same name.
    """
    for activity_subgroup in archived_activity_subgroups:
        subgroup_dict = activity_subgroup.model_dump()
        subgroup_dict["library_name"] = settings.sponsor_library_name
        input_model = ActivitySubGroupCreateInput(**subgroup_dict)

        response = api_client.post(
            "/concepts/activities/activity-sub-groups",
            json=input_model.model_dump(),
        )
        res = parse_json_response(response, assert_status=201)

        assert res["name"] == activity_subgroup.name


def test_delete_draft_activity_subgroup(api_client):
    """
    SCENARIO: deleting a draft Activity Sub Group
    GIVEN: an existing draft Activity Sub Group
    WHEN: DELETE /concepts/activities/activity-sub-groups/{uid}
    THEN: should respond with 204 HTTP status code
    """

    activity_subgroup = TestUtils.create_activity_subgroup(
        name="Activity Sub Group to delete", approve=False
    )

    response = api_client.delete(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup.uid}"
    )
    assert_response_status_code(response, 204)


def test_delete_archived_activity_subgroup_fails(api_client):
    """
    SCENARIO: deleting an archived Activity Sub Group
    GIVEN: an existing archived Activity Sub Group
    WHEN: DELETE /concepts/activities/activity-sub-groups/{uid}
    THEN: should respond with 400 HTTP status code and JSON payload,
          with an error message that archived concepts cannot be deleted.
    """

    activity_subgroup = TestUtils.create_activity_subgroup(
        name="Archived Activity Sub Group to delete", approve=False
    )
    TestUtils.archive_activity_subgroup(activity_subgroup.uid)

    response = api_client.delete(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup.uid}"
    )
    resp = parse_json_response(response, assert_status=400)
    assert "Can't delete Concept" in resp["message"]
