"""
Tests for /concepts/activities/activity-groups endpoints
"""

import logging
from operator import itemgetter

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.concepts.activities.activity_group import (
    ActivityGroup,
    ActivityGroupCreateInput,
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
activity_groups_all: list[ActivityGroup]
archived_activity_groups: list[ActivityGroup]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "activitiesgroups.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global activity_groups_all
    activity_groups_all = [
        TestUtils.create_activity_group(name="name-AAA"),
        TestUtils.create_activity_group(
            name="name-BBB",
        ),
    ]

    for index in range(5):
        activity_groups_all.append(
            TestUtils.create_activity_group(
                name=f"ActivityGroup-{index}",
            )
        )

    global archived_activity_groups
    archived_activity_groups = [
        TestUtils.create_activity_group(name="Archived Group A"),
        TestUtils.create_activity_group(name="Archived Group B"),
    ]
    for ag in archived_activity_groups:
        TestUtils.archive_activity_group(ag.uid)

    yield


ACTIVITY_GROUP_FIELDS_ALL = [
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
    "author_username",
    "possible_actions",
]

ACTIVITY_GROUP_FIELDS_NOT_NULL = ["uid", "name", "start_date"]


def test_get_activity_group(api_client):
    """
    SCENARIO: getting a single Activity Group by uid
    GIVEN: an existing Activity Group in the database
    WHEN: GET /concepts/activities/activity-groups/{uid}
    THEN: should respond with 200, with all expected fields present, non-null fields non-null,
          and field values matching the created Activity Group.
    """
    response = api_client.get(
        f"/concepts/activities/activity-groups/{activity_groups_all[0].uid}"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(res.keys()) == set(ACTIVITY_GROUP_FIELDS_ALL)
    for key in ACTIVITY_GROUP_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == activity_groups_all[0].uid
    assert res["name"] == "name-AAA"
    assert res["name_sentence_case"] == "name-AAA"
    assert res["library_name"] == "Sponsor"
    assert res["definition"] is None
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_get_activity_group_version(api_client):
    """
    SCENARIO: getting all versions of a single Activity Group
    GIVEN: an existing Activity Group in the database (has Draft 0.1 and Final 1.0)
    WHEN: GET /concepts/activities/activity-groups/{uid}/versions
    THEN: should respond with 200 and a list of 2 version objects with correct version/status values.
    """
    response = api_client.get(
        f"/concepts/activities/activity-groups/{activity_groups_all[0].uid}/versions"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    assert len(res) == 2

    # Check fields included in the response
    for item in res:
        assert set(list(item.keys())) == set(ACTIVITY_GROUP_FIELDS_ALL)
        for key in ACTIVITY_GROUP_FIELDS_NOT_NULL:
            assert item[key] is not None

    assert res[0]["uid"] == activity_groups_all[0].uid
    assert res[0]["name"] == "name-AAA"
    assert res[0]["name_sentence_case"] == "name-AAA"
    assert res[0]["library_name"] == "Sponsor"
    assert res[0]["definition"] is None
    assert res[0]["version"] == "1.0"
    assert res[0]["status"] == "Final"
    assert res[0]["possible_actions"] == ["inactivate", "new_version"]

    assert res[1]["uid"] == activity_groups_all[0].uid
    assert res[1]["name"] == "name-AAA"
    assert res[1]["name_sentence_case"] == "name-AAA"
    assert res[1]["library_name"] == "Sponsor"
    assert res[1]["definition"] is None
    assert res[1]["version"] == "0.1"
    assert res[1]["status"] == "Draft"
    assert res[1]["possible_actions"] == ["approve", "delete", "edit"]


def test_get_activity_groups_versions(api_client):
    """
    SCENARIO: getting all versions of all Activity Groups
    GIVEN: multiple Activity Groups in the database, one of which gets a new version created
    WHEN: GET /concepts/activities/activity-groups/versions?page_size=100
    THEN: should respond with 200 and a paginated list containing all versions sorted by
          start_date descending, with all expected fields present and non-null fields non-null.
    """
    # Create a new version of an activity group
    response = api_client.post(
        f"/concepts/activities/activity-groups/{activity_groups_all[0].uid}/versions"
    )
    assert_response_status_code(response, 201)

    # Get all versions of all activities
    response = api_client.get(
        "/concepts/activities/activity-groups/versions?page_size=100"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(res.keys()) == set(["items", "total", "page", "size"])

    assert len(res["items"]) == len(activity_groups_all) * 2 + 1
    for item in res["items"]:
        assert set(list(item.keys())) == set(ACTIVITY_GROUP_FIELDS_ALL)
        for key in ACTIVITY_GROUP_FIELDS_NOT_NULL:
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
    SCENARIO: wildcard filtering of Activity Group versions
    GIVEN: multiple existing Activity Group versions in the database
    WHEN: GET /concepts/activities/activity-groups/versions?filters={filter_by}
    THEN: should respond with 200; if a prefix is expected, every returned item's matched field
          starts with expected_result_prefix; if no prefix, zero items are returned.
    """
    url = f"/concepts/activities/activity-groups/versions?filters={filter_by}"
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
    SCENARIO: exact field filtering of Activity Group versions
    GIVEN: multiple existing Activity Group versions in the database
    WHEN: GET /concepts/activities/activity-groups/versions?filters={filter_by}
    THEN: should respond with 200; if a result is expected, every returned item's matched field
          equals expected_result; if no result, zero items are returned.
    """
    url = f"/concepts/activities/activity-groups/versions?filters={filter_by}"
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


def test_cascade_edit_activity_groups(api_client):
    """
    SCENARIO: cascade editing an Activity Group propagates changes to linked Activities and Instances
    GIVEN: an Activity Group linked to an Activity and Activity Instance
    WHEN: PUT /concepts/activities/activity-groups/{uid} + POST …/approvals?cascade_edit_and_approve=True
    THEN: the linked Activity and Activity Instance are both bumped to new Final versions
          reflecting the updated Activity Group name, with no intermediate drafts persisting.
    WHEN: PUT + POST …/approvals?cascade_edit_and_approve=False
    THEN: linked Activity and Activity Instance remain at their current versions unchanged.
    """
    # ==== Create activity and activity instance ====
    activity_group = TestUtils.create_activity_group(name="Cascade Group")
    _second_activity_group = TestUtils.create_activity_group(name="Second Group")
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="Cascade SubGroup",
    )
    activity = TestUtils.create_activity(
        name="Cascade Activity",
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
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

    # ==== Update activity group with cascade edit&approve, activity and instance should be updated also ====

    # Create new version of activity
    response = api_client.post(
        f"/concepts/activities/activity-groups/{activity_group.uid}/versions",
        json={},
    )
    assert_response_status_code(response, 201)

    # Update the activity group
    updated_activity_group_name = "Edited Cascade Activity Group"
    concept_id = "CONCEPT_ID"
    concept_name = "concept name"
    response = api_client.put(
        f"/concepts/activities/activity-groups/{activity_group.uid}",
        json={
            "name": updated_activity_group_name,
            "name_sentence_case": updated_activity_group_name.lower(),
            "nci_concept_id": concept_id,
            "nci_concept_name": concept_name,
            "change_description": "test cascade edit",
            "library_name": activity_group.library_name,
        },
    )
    assert_response_status_code(response, 200)

    # Approve the activity group with cascade_edit_and_approve set to True
    response = api_client.post(
        f"/concepts/activities/activity-groups/{activity_group.uid}/approvals",
        params={"cascade_edit_and_approve": True},
    )
    assert_response_status_code(response, 201)

    # Assert Activity Group was updated
    response = api_client.get(
        f"/concepts/activities/activity-groups/{activity_group.uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["name"] == updated_activity_group_name
    assert res["name_sentence_case"] == updated_activity_group_name.lower()
    assert res["nci_concept_id"] == concept_id
    assert res["nci_concept_name"] == concept_name
    assert res["status"] == "Final"
    assert res["version"] == "2.0"

    # Get the activity and assert that it was updated
    response = api_client.get(f"/concepts/activities/activities/{activity.uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["version"] == "2.0"
    assert res["status"] == "Final"
    assert len(res["activity_groupings"]) == 1
    assert res["activity_groupings"][0]["activity_group_uid"] == activity_group.uid
    assert (
        res["activity_groupings"][0]["activity_group_name"]
        == updated_activity_group_name
    )
    assert (
        res["activity_groupings"][0]["activity_subgroup_uid"] == activity_subgroup.uid
    )
    assert (
        res["activity_groupings"][0]["activity_subgroup_name"] == activity_subgroup.name
    )

    # Get the activity instance and assert that it was updated
    response = api_client.get(
        f"/concepts/activities/activity-instances/{activity_instance.uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["groupings_version"] == "2.0"
    assert res["groupings_status"] == "Final"
    assert len(res["activity_groupings"]) == 1
    assert res["activity_groupings"][0]["activity_group"]["uid"] == activity_group.uid
    assert (
        res["activity_groupings"][0]["activity_group"]["name"]
        == updated_activity_group_name
    )
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["uid"]
        == activity_subgroup.uid
    )
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["name"]
        == activity_subgroup.name
    )
    assert res["activity_groupings"][0]["activity"]["uid"] == activity.uid
    assert res["activity_groupings"][0]["activity"]["name"] == activity.name

    # Get the activity versions and assert that one new version was created.
    # There should be a new final version 2.0 that links to activity group version 2.0
    # and activity subgroup version 1.0
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
    assert (
        new_final["activity_groupings"][0]["activity_group_name"]
        == updated_activity_group_name
    )

    # Get the activity instance versions and assert that one new version was created.
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
        new_final["activity_groupings"][0]["activity_group"]["name"]
        == updated_activity_group_name
    )

    # ==== Update activity group without cascade edit&approve, activity and instance should NOT be updated ====
    # Create new version of activity
    response = api_client.post(
        f"/concepts/activities/activity-groups/{activity_group.uid}/versions",
        json={},
    )
    assert_response_status_code(response, 201)

    # Put the activity group
    second_updated_activity_group_name = "Another update of activity group name"
    response = api_client.put(
        f"/concepts/activities/activity-groups/{activity_group.uid}",
        json={
            "name": second_updated_activity_group_name,
            "name_sentence_case": second_updated_activity_group_name.lower(),
            "change_description": "test cascade edit again",
            "library_name": activity.library_name,
        },
    )
    assert_response_status_code(response, 200)

    # Approve the activity group with cascade_edit_and_approve set to False
    response = api_client.post(
        f"/concepts/activities/activity-groups/{activity_group.uid}/approvals",
        params={"cascade_edit_and_approve": False},
    )
    assert_response_status_code(response, 201)

    # Get the activity and assert that it was not updated
    response = api_client.get(f"/concepts/activities/activities/{activity.uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["version"] == "2.0"
    assert res["status"] == "Final"
    assert len(res["activity_groupings"]) == 1
    assert (
        res["activity_groupings"][0]["activity_subgroup_uid"] == activity_subgroup.uid
    )
    assert res["activity_groupings"][0]["activity_group_uid"] == activity_group.uid
    assert (
        res["activity_groupings"][0]["activity_group_name"]
        == updated_activity_group_name
    )

    # Get the activity instance and assert that it was not updated
    response = api_client.get(
        f"/concepts/activities/activity-instances/{activity_instance.uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["groupings_version"] == "2.0"
    assert res["groupings_status"] == "Final"
    assert len(res["activity_groupings"]) == 1
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["uid"]
        == activity_subgroup.uid
    )
    assert res["activity_groupings"][0]["activity_group"]["uid"] == activity_group.uid
    assert (
        res["activity_groupings"][0]["activity_group"]["name"]
        == updated_activity_group_name
    )


def test_get_activity_groups_excludes_archived(api_client):
    """
    SCENARIO: listing Activity Groups excluding archived ones
    GIVEN: multiple Activity Groups in the database, some archived
    WHEN: GET /concepts/activities/activity-groups
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing all existing Activity Groups, excluding archived Activity Groups.
    """
    response = api_client.get(
        "/concepts/activities/activity-groups", params={"page_size": 1000}
    )
    payload = parse_json_response(response, assert_status=200)

    items = payload["items"]
    assert len(items) > 0
    for item in items:
        assert item["library_name"] != settings.archived_library_name


def test_get_archived_activity_groups(api_client):
    """
    SCENARIO: getting archived Activity Groups
    GIVEN: multiple Activity Groups in the database, some archived
    WHEN: GET /concepts/activities/activity-groups?library_name=Archived
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing only the archived Activity Groups.
    """
    response = api_client.get(
        "/concepts/activities/activity-groups",
        params={"library_name": settings.archived_library_name, "page_size": 1000},
    )
    payload = parse_json_response(response, assert_status=200)

    items = payload["items"]
    assert len(items) > 0
    for item in items:
        assert item["library_name"] == settings.archived_library_name
    for item in payload["items"]:
        assert item["library_name"] == settings.archived_library_name


def test_get_activity_group_by_uid_returns_archived(api_client):
    """
    SCENARIO: getting a single archived Activity Group by UID
    GIVEN: an archived Activity Group in the database
    WHEN: GET /concepts/activities/activity-groups/{uid}
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Activity Group with library_name set to 'Archived'.
    """
    archived_ag = archived_activity_groups[0]
    response = api_client.get(f"/concepts/activities/activity-groups/{archived_ag.uid}")
    res = parse_json_response(response, assert_status=200)

    assert res["uid"] == archived_ag.uid
    assert res["library_name"] == settings.archived_library_name


def test_archived_activity_group_excluded_from_headers(api_client):
    """
    SCENARIO: getting headers of Activity Groups with archived Activity Groups in the database
    GIVEN: an existing Activity Group in the database, later archived
    WHEN: GET /concepts/activities/activity-groups/headers?field_name=name
    THEN: should respond with 200 HTTP status code and JSON payload,
          with the archived Activity Group excluded from the results.
    """
    # Create an Activity Group
    activity_group = TestUtils.create_activity_group(name="A Canary activity group")

    # Get headers — the new group should appear
    response = api_client.get(
        "/concepts/activities/activity-groups/headers",
        params={"field_name": "name", "search_string": "canary"},
    )
    payload = parse_json_response(response, assert_status=200)
    assert isinstance(payload, list)
    assert activity_group.name in payload

    # Archive the Activity Group
    TestUtils.archive_activity_group(activity_group.uid)

    # Get headers again — the archived group should no longer appear
    response = api_client.get(
        "/concepts/activities/activity-groups/headers",
        params={"field_name": "name", "search_string": "canary"},
    )
    payload = parse_json_response(response, assert_status=200)
    assert isinstance(payload, list)
    assert activity_group.name not in payload


def test_archiving_activity_group_draft(api_client):
    """
    SCENARIO: archiving an Activity Group in Draft status
    GIVEN: an Activity Group in Draft status
    WHEN: POST /concepts/activities/activity-groups/{uid}/archive
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Activity Group with library_name set to the archived library.
    """
    activity_group = TestUtils.create_activity_group(
        name="Draft Group To Archive", approve=False
    )

    response = api_client.post(
        f"/concepts/activities/activity-groups/{activity_group.uid}/archive"
    )
    res = parse_json_response(response, assert_status=200)

    assert res["library_name"] == settings.archived_library_name
    assert res["name"] == activity_group.name


def test_archiving_activity_group_final(api_client):
    """
    SCENARIO: archiving an Activity Group in Final status
    GIVEN: an Activity Group in Final (approved) status
    WHEN: POST /concepts/activities/activity-groups/{uid}/archive
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Activity Group with library_name set to the archived library.
    """
    activity_group = TestUtils.create_activity_group(name="Final Group To Archive")

    response = api_client.post(
        f"/concepts/activities/activity-groups/{activity_group.uid}/archive"
    )
    res = parse_json_response(response, assert_status=200)

    assert res["library_name"] == settings.archived_library_name


def test_can_not_archive_already_archived_activity_group(api_client):
    """
    SCENARIO: attempting to archive an already-archived Activity Group
    GIVEN: Activity Groups that are already archived
    WHEN: POST /concepts/activities/activity-groups/{uid}/archive for each archived group
    THEN: should respond with 400 HTTP status code and an error message indicating the group
          is already in the archived library.
    """
    for activity_group in archived_activity_groups:
        uid = activity_group.uid
        response = api_client.post(
            f"/concepts/activities/activity-groups/{uid}/archive"
        )
        res = parse_json_response(response, assert_status=400)

        assert (
            res["message"]
            == f"Concept with UID '{uid}' is already in '{settings.archived_library_name}' library."
        )


def test_can_not_create_new_version_of_archived_activity_group(api_client):
    """
    SCENARIO: attempting to create a new version of an archived Activity Group
    GIVEN: Activity Groups that are already archived
    WHEN: POST /concepts/activities/activity-groups/{uid}/versions for each archived group
    THEN: should respond with 400 HTTP status code and an error message indicating the library
          is not editable.
    """
    for activity_group in archived_activity_groups:
        response = api_client.post(
            f"/concepts/activities/activity-groups/{activity_group.uid}/versions"
        )
        res = parse_json_response(response, assert_status=400)

        assert res["message"] == "Library isn't editable."


def test_can_not_edit_archived_activity_group(api_client):
    """
    SCENARIO: attempting to edit an archived Activity Group
    GIVEN: Activity Groups that are already archived
    WHEN: PUT /concepts/activities/activity-groups/{uid} for each archived group
    THEN: should respond with 400 HTTP status code and an error message indicating the library
          is not editable.
    """
    for activity_group in archived_activity_groups:
        response = api_client.put(
            f"/concepts/activities/activity-groups/{activity_group.uid}",
            json={
                "name": "Edited Archived Group",
                "name_sentence_case": "edited archived group",
                "change_description": "edit attempt on archived",
                "library_name": settings.sponsor_library_name,
            },
        )
        res = parse_json_response(response, assert_status=400)

        assert res["message"] == "Library isn't editable."


def test_allow_recreating_archived_activity_group(api_client):
    """
    SCENARIO: re-creating an Activity Group with the same name as an archived one
    GIVEN: Activity Groups that are already archived
    WHEN: POST /concepts/activities/activity-groups with the same name as the archived group
    THEN: should respond with 201 HTTP status code and JSON payload,
          containing the newly created Activity Group with the same name.
    """
    for activity_group in archived_activity_groups:
        group_dict = activity_group.model_dump()
        group_dict["library_name"] = settings.sponsor_library_name
        input_model = ActivityGroupCreateInput(**group_dict)

        response = api_client.post(
            "/concepts/activities/activity-groups",
            json=input_model.model_dump(),
        )
        res = parse_json_response(response, assert_status=201)

        assert res["name"] == activity_group.name


def test_delete_draft_activity_group(api_client):
    """
    SCENARIO: deleting a draft Activity Group
    GIVEN: an existing draft Activity Group
    WHEN: DELETE /concepts/activities/activity-groups/{uid}
    THEN: should respond with 204 HTTP status code
    """

    activity_group = TestUtils.create_activity_group(
        name="Activity Group to delete", approve=False
    )

    response = api_client.delete(
        f"/concepts/activities/activity-groups/{activity_group.uid}"
    )
    assert_response_status_code(response, 204)


def test_delete_archived_activity_group_fails(api_client):
    """
    SCENARIO: deleting an archived Activity Group
    GIVEN: an existing archived Activity Group
    WHEN: DELETE /concepts/activities/activity-groups/{uid}
    THEN: should respond with 400 HTTP status code and JSON payload,
          with an error message that archived concepts cannot be deleted.
    """

    activity_group = TestUtils.create_activity_group(
        name="Archived Activity Group to delete", approve=False
    )
    TestUtils.archive_activity_group(activity_group.uid)

    response = api_client.delete(
        f"/concepts/activities/activity-groups/{activity_group.uid}"
    )
    resp = parse_json_response(response, assert_status=400)
    assert "Can't delete Concept" in resp["message"]
