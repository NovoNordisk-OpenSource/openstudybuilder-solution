"""
Tests for the bidirectional relationship between activity subgroups and groups
- Tests activity subgroups showing their related groups
"""

import logging

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

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
activity_group_1: ActivityGroup
activity_group_2: ActivityGroup
activity_subgroup_1: ActivitySubGroup
activity_subgroup_2: ActivitySubGroup


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data with linked activity groups and subgroups"""
    db_name = "activities-subgroup-group-relationships-api"
    inject_and_clear_db(db_name)
    inject_base_data()

    # Create activity groups
    global activity_group_1, activity_group_2
    activity_group_1 = TestUtils.create_activity_group(
        name="Test Group 1",
        definition="Definition for group 1",
    )
    activity_group_2 = TestUtils.create_activity_group(
        name="Test Group 2",
        definition="Definition for group 2",
    )

    # Create activity subgroups
    global activity_subgroup_1, activity_subgroup_2
    activity_subgroup_1 = TestUtils.create_activity_subgroup(name="Test Subgroup 1")
    activity_subgroup_2 = TestUtils.create_activity_subgroup(
        name="Test Subgroup 2",
    )

    # Create an activity that links subgroup 2 with both groups 1 and 2
    TestUtils.create_activity(
        name="Activity 1",
        activity_groups=[activity_group_1.uid, activity_group_2.uid],
        activity_subgroups=[activity_subgroup_2.uid, activity_subgroup_2.uid],
    )
    yield


def test_activity_subgroup_groups_listing(api_client):
    """Test that activity subgroup group listing includes detailed information about linked groups"""
    # Request the activity subgroup group listing
    response = api_client.get(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup_2.uid}/activity-groups"
    )
    assert_response_status_code(response, 200)

    groups_json = response.json()
    groups = groups_json["items"]

    # Check that the response contains the expected activity groups

    # Subgroup 2 should be linked to both groups
    assert len(groups) == 2, f"Expected 2 linked groups in overview, got {len(groups)}"

    # Verify group details include all expected fields
    for group in groups:
        assert "uid" in group, "Group should include uid field"
        assert "name" in group, "Group should include name field"
        assert "version" in group, "Group should include version field"
        assert "status" in group, "Group should include status field"
        assert group["status"] == "Final", "Only Final status groups should be linked"

    # Find both groups and verify their details
    group_1 = next((g for g in groups if g["uid"] == activity_group_1.uid), None)
    assert (
        group_1 is not None
    ), f"Group 1 ({activity_group_1.uid}) not found in groups listing"
    assert (
        group_1["name"] == "Test Group 1"
    ), "Group 1 name does not match expected value"

    group_2 = next((g for g in groups if g["uid"] == activity_group_2.uid), None)
    assert (
        group_2 is not None
    ), f"Group 2 ({activity_group_2.uid}) not found in groups listing"
    assert (
        group_2["name"] == "Test Group 2"
    ), "Group 2 name does not match expected value"


def test_draft_status_groups_are_included(api_client):
    """Test that Draft status groups ARE included in linked groups (per user requirement)"""
    # Create a new draft group
    draft_group = TestUtils.create_activity_group(
        name="Draft Group", definition="Definition for draft group"
    )

    # Create a new subgroup linked to the draft group and an existing Final group
    test_subgroup = TestUtils.create_activity_subgroup(
        name="Test Subgroup for Draft Group",
    )
    TestUtils.create_activity(
        name="Activity linking Draft Group",
        activity_groups=[draft_group.uid, activity_group_1.uid],
        activity_subgroups=[test_subgroup.uid, test_subgroup.uid],
    )

    # Update the group status after creation
    TestUtils.update_entity_status(draft_group.uid, "Draft", "ActivityGroup")

    # Request the groups linked to the activity subgroup
    response = api_client.get(
        f"/concepts/activities/activity-sub-groups/{test_subgroup.uid}/activity-groups"
    )
    assert_response_status_code(response, 200)

    subgroup_data = response.json()

    # Check the response contains both the Draft and Final status groups
    groups = subgroup_data["items"]

    # Both Draft and Final status groups should be included (per user requirement)
    group_uids = [g["uid"] for g in groups]
    # Both groups should be present
    assert (
        activity_group_1.uid in group_uids
    ), "Final group should be included in linked groups"
    assert (
        draft_group.uid in group_uids
    ), "Draft group should be included in linked groups (per user requirement)"


def test_specific_activity_subgroup_version_shows_correct_groups(api_client):
    """Test that requesting a specific version of an activity subgroup shows the correct linked groups"""

    # Create new version of the activity subgroup
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup_2.uid}/versions",
        json={},
    )
    assert_response_status_code(response, 201)

    # Update the new version - use exact same name but with different definition
    response = api_client.get(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup_2.uid}"
    )
    current_data = response.json()

    response = api_client.put(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup_2.uid}",
        json={
            "name": current_data[
                "name"
            ],  # Use exactly the same name to avoid case sensitivity validation
            "name_sentence_case": current_data["name_sentence_case"],
            "library_name": current_data["library_name"],
            "definition": "Updated definition for subgroup 2",
            "change_description": "Updated subgroup definition",
        },
    )
    assert_response_status_code(response, 200)

    # Approve the new version
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup_2.uid}/approvals"
    )
    assert_response_status_code(response, 201)

    # First, get the available versions to confirm they exist
    response = api_client.get(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup_2.uid}/versions"
    )
    assert_response_status_code(response, 200)
    versions_data = response.json()

    # Handle different possible response formats for versions
    versions_list = []
    if isinstance(versions_data, dict) and "versions" in versions_data:
        versions_list = versions_data["versions"]
    elif isinstance(versions_data, list):
        versions_list = versions_data

    # Extract version numbers safely
    version_numbers = []
    for v in versions_list:
        if isinstance(v, dict) and "version" in v:
            version_numbers.append(v["version"])

    # Request version 1.0 of the activity subgroup (use the correct endpoint format)
    response = api_client.get(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup_2.uid}/activity-groups?version=1.0"
    )
    assert_response_status_code(response, 200)
    version_v1 = response.json()["items"]

    # Request version 2.0 of the activity subgroup
    response = api_client.get(
        f"/concepts/activities/activity-sub-groups/{activity_subgroup_2.uid}/activity-groups?version=2.0"
    )
    assert_response_status_code(response, 200)
    version_v2 = response.json()["items"]

    # Extract group uids from both versions
    group_uids_v1 = [g["uid"] for g in version_v1]
    group_uids_v2 = [g["uid"] for g in version_v2]

    assert len(group_uids_v1) == 2, "Version 1.0 should have 2 linked groups"
    assert len(group_uids_v2) == 0, "Version 2.0 should have no linked groups"
    assert set(group_uids_v1) == {
        activity_group_1.uid,
        activity_group_2.uid,
    }, "Version 1.0 linked groups do not match expected groups"
