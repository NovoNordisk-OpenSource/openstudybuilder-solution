"""
Tests for /concepts/activities/activity-sub-groups/{uid}/overview endpoint
"""

import json
import logging
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.concepts.activities.activity import Activity
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

log = logging.getLogger(__name__)

ACTIVITY_SUBGROUP_BASE_URL = "/concepts/activities/activity-sub-groups"
ACTIVITIES_BASE_URL = "/concepts/activities/activities"

activity_groups_all: list[ActivityGroup] = []
activity_subgroups_all: list[ActivitySubGroup] = []
activities_all: list[Activity] = []


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client using the database name set in the test_data fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "activity-overview.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global activity_groups_all
    global activity_subgroups_all
    global activities_all

    log.info("\n=== Creating Test Data ===")

    # Creating activity group first
    group = TestUtils.create_activity_group(
        name="AE Requiring Additional Data",
        library_name="Sponsor",
        definition="Definition not provided",
    )
    log.info("Created Activity Group: %s", group)
    activity_groups_all.append(group)

    # Creating subgroup with link to activity group
    subgroup1 = TestUtils.create_activity_subgroup(
        name="Laboratory Assessment",
        library_name="Sponsor",
        activity_groups=[group.uid],
        definition="Laboratory Assessment Definition",
    )
    activity_subgroups_all.append(subgroup1)

    subgroup2 = TestUtils.create_activity_subgroup(
        name="Acute Kidney Injury",
        library_name="Sponsor",
        activity_groups=[group.uid],
        definition=None,
    )
    activity_subgroups_all.append(subgroup2)

    subgroup3 = TestUtils.create_activity_subgroup(
        name="Pancreatitis",
        library_name="Sponsor",
        activity_groups=[group.uid],
        definition=None,
    )
    activity_subgroups_all.append(subgroup3)

    test_activities = ["Albumin", "Renal Event", "Albumin/Creatinine"]

    client = TestClient(app)
    log.info("\n=== Creating Activities ===")

    for idx, activity_name in enumerate(test_activities, 1):
        log.info("Creating activity %s...", activity_name)
        activity_data = {
            "start_date": datetime.now(timezone.utc).isoformat(),
            "end_date": None,
            "status": "Draft",
            "version": "0.1",
            "change_description": "Initial version",
            "author_username": "unknown-user@example.com",
            "uid": f"Activity_{idx:06d}",
            "name": activity_name,
            "name_sentence_case": activity_name,
            "definition": None,
            "abbreviation": None,
            "library_name": "Sponsor",
            "possible_actions": ["approve", "delete", "edit"],
            "nci_concept_id": None,
            "nci_concept_name": None,
            "activity_groupings": [
                {
                    "activity_group_uid": group.uid,
                    "activity_group_name": group.name,
                    "activity_subgroup_uid": subgroup1.uid,
                    "activity_subgroup_name": subgroup1.name,
                }
            ],
            "synonyms": [],
            "request_rationale": None,
            "is_request_final": False,
            "is_request_rejected": False,
            "contact_person": None,
            "reason_for_rejecting": None,
            "requester_study_id": None,
            "replaced_by_activity": None,
            "is_data_collected": True,
            "is_multiple_selection_allowed": True,
            "is_finalized": False,
            "is_used_by_legacy_instances": False,
        }

        response = client.post(ACTIVITIES_BASE_URL, json=activity_data)
        assert (
            response.status_code == 201
        ), f"Failed to create activity {activity_name}: {response.text}"

        created_activity = response.json()
        log.info("Created Activity: %s", created_activity)
        activities_all.append(created_activity)

    log.info("\n=== Test Data Summary ===")
    log.info("Activity Groups created: %d", len(activity_groups_all))
    log.info("Activity Subgroups created: %d", len(activity_subgroups_all))
    log.info("Activities created: %d", len(activities_all))

    yield


def test_get_activity_subgroup_overview(api_client):
    """Test getting activity subgroup overview"""
    subgroup = activity_subgroups_all[0]

    log.info("\n=== Testing Activity Subgroup Overview ===")
    log.info("Getting overview for subgroup: %s", subgroup.uid)

    response = api_client.get(f"{ACTIVITY_SUBGROUP_BASE_URL}/{subgroup.uid}/overview")
    res = response.json()

    log.info("\n=== Response Data ===")
    log.info("Full API Response: %s", res)

    assert_response_status_code(response, 200)

    # Verifying structure and data
    assert "activity_subgroup" in res
    assert "activities" in res
    assert "all_versions" in res

    subgroup_data = res["activity_subgroup"]
    log.info("\n=== Validating Response ===")
    log.info("Subgroup Fields:")
    for field in [
        "name",
        "name_sentence_case",
        "library_name",
        "version",
        "status",
        "start_date",
    ]:
        log.info("  %s: %s", field, subgroup_data.get(field))

    assert subgroup_data["name"] == "Laboratory Assessment"
    assert subgroup_data["library_name"] == "Sponsor"
    assert "version" in subgroup_data
    assert "status" in subgroup_data
    assert "start_date" in subgroup_data
    assert "activity_groups" in subgroup_data

    activities = res["activities"]
    log.info("\nActivities in Response: %d", len(activities))
    for activity in activities:
        log.info("  Activity: %s (UID: %s)", activity["name"], activity["uid"])

    assert (
        len(activities) == 3
    ), f"Should have exactly 3 activities, got {len(activities)}"

    activity_names = sorted(activity["name"] for activity in activities)
    expected_names = sorted(["Albumin", "Renal Event", "Albumin/Creatinine"])
    assert (
        activity_names == expected_names
    ), f"Expected activities {expected_names}, got {activity_names}"


def test_get_activity_subgroup_overview_not_found(api_client):
    """Test getting overview for non-existent activity subgroup"""
    response = api_client.get(f"{ACTIVITY_SUBGROUP_BASE_URL}/non_existent_uid/overview")
    assert_response_status_code(response, 404)


def test_get_activity_subgroup_overview_with_version(api_client):
    """Test getting activity subgroup overview with specific version"""
    subgroup = activity_subgroups_all[0]

    log.info("\n=== Testing Activity Subgroup Overview With Version ===")
    log.info("Getting version 0.1 overview for subgroup: %s", subgroup.uid)

    response = api_client.get(
        f"{ACTIVITY_SUBGROUP_BASE_URL}/{subgroup.uid}/overview?version=0.1"
    )
    res = response.json()

    log.info("\n=== Response Data ===")
    log.info("Full API Response: %s", res)

    assert_response_status_code(response, 200)

    activities = res["activities"]
    log.info("\nActivities in Version 0.1: %d", len(activities))
    for activity in activities:
        log.info("  Activity: %s (UID: %s)", activity["name"], activity["uid"])

    assert (
        len(activities) == 3
    ), f"Should have 3 activities in version 0.1, got {len(activities)}"


def test_get_activity_group_overview(api_client):
    """Test getting activity group overview"""
    group = activity_groups_all[0]

    log.info("\n=== Testing Activity Group Overview ===")
    log.info("Getting overview for group: %s", group.uid)

    response = api_client.get(
        f"/concepts/activities/activity-groups/{group.uid}/overview"
    )
    res = response.json()

    log.info("\n=== Response Data ===")
    log.info("Full API Response: %s", res)

    assert_response_status_code(response, 200)

    # Verifying structure and data
    assert "group" in res
    assert "subgroups" in res
    assert "all_versions" in res

    # Verifying group details
    group_data = res["group"]
    log.info("\n=== Validating Group Response ===")
    expected_group_fields = [
        "name",
        "name_sentence_case",
        "library_name",
        "start_date",
        "end_date",
        "status",
        "version",
        "possible_actions",
        "change_description",
        "author_username",
        "definition",
        "abbreviation",
    ]
    for field in expected_group_fields:
        log.info("  %s: %s", field, group_data.get(field))
        assert field in group_data

    assert group_data["name"] == "AE Requiring Additional Data"
    assert group_data["name_sentence_case"] == "AE Requiring Additional Data"
    assert group_data["library_name"] == "Sponsor"
    assert group_data["status"] == "Final"
    assert group_data["version"] == "1.0"
    assert group_data["author_username"] == "unknown-user@example.com"
    assert group_data["definition"] == "Definition not provided"
    assert group_data["abbreviation"] is None
    assert "possible_actions" in group_data
    assert isinstance(group_data["possible_actions"], list)

    # Verifying subgroups
    subgroups = res["subgroups"]
    log.info("\nSubgroups in Response: %d", len(subgroups))
    for subgroup in subgroups:
        log.info(
            "  Subgroup: %s (Status: %s, Version: %s)",
            subgroup["name"],
            subgroup["status"],
            subgroup["version"],
        )

        # Verifying subgroup structure
        assert all(
            field in subgroup
            for field in ["uid", "name", "version", "status", "definition"]
        )

    # Verifying we have all expected subgroups
    assert len(subgroups) == 3

    # Sort subgroups by uid for consistent testing
    sorted_subgroups = sorted(subgroups, key=lambda x: x["uid"])

    # Verifying specific subgroups
    assert sorted_subgroups[0]["name"] == "Laboratory Assessment"
    assert sorted_subgroups[0]["version"] == "1.0"
    assert sorted_subgroups[0]["status"] == "Final"

    assert sorted_subgroups[1]["name"] == "Acute Kidney Injury"
    assert sorted_subgroups[1]["version"] == "1.0"
    assert sorted_subgroups[1]["status"] == "Final"

    assert sorted_subgroups[2]["name"] == "Pancreatitis"
    assert sorted_subgroups[2]["version"] == "1.0"
    assert sorted_subgroups[2]["status"] == "Final"

    # Verifyin versions
    versions = res["all_versions"]
    assert len(versions) == 2
    assert versions == ["1.0", "0.1"]


def test_get_activity_group_overview_not_found(api_client):
    """Test getting overview for non-existent activity group"""
    response = api_client.get(
        "/concepts/activities/activity-groups/non_existent_uid/overview"
    )
    assert_response_status_code(response, 404)


def test_get_activity_group_overview_with_version(api_client):
    """Test getting activity group overview with specific version"""
    group = activity_groups_all[0]

    log.info("\n=== Testing Activity Group Overview With Version ===")
    log.info("Getting version 0.1 overview for group: %s", group.uid)

    response = api_client.get(
        f"/concepts/activities/activity-groups/{group.uid}/overview?version=0.1"
    )
    res = response.json()

    log.info("\n=== Response Data ===")
    log.info("Full API Response: %s", res)

    assert_response_status_code(response, 200)

    # Verifying group details in specific version
    group_data = res["group"]
    assert group_data["version"] == "0.1"
    assert group_data["status"] == "Draft"

    # Verifying subgroups in this version context
    subgroups = res["subgroups"]
    log.info("\nSubgroups in Version 0.1: %d", len(subgroups))
    for subgroup in subgroups:
        log.info(
            "  Subgroup: %s (Status: %s, Version: %s)",
            subgroup["name"],
            subgroup["status"],
            subgroup["version"],
        )
