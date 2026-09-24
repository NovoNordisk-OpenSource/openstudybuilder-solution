# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_ACTIVITIES,
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_ACTIVITY_SUB_GROUPS,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.activity")
    db.cypher_query(STARTUP_ACTIVITY_GROUPS)
    db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
    db.cypher_query(STARTUP_ACTIVITIES)

    yield

    drop_db("old.json.test.activity")


def test_post_create_activity(api_client):
    data = {
        "name": "new_name",
        "name_sentence_case": "new_name",
        "nci_concept_id": "C12345",
        "nci_concept_name": "NAME-C12345",
        "synonyms": ["NAME", "C12345"],
        "definition": "definition",
        "abbreviation": "abbv",
        "library_name": "Sponsor",
        "activity_groupings": [
            {
                "activity_subgroup_uid": "activity_subgroup_root1",
                "activity_group_uid": "activity_group_root1",
            },
            {
                "activity_subgroup_uid": "activity_subgroup_root3",
                "activity_group_uid": "activity_group_root3",
            },
        ],
        "is_data_collected": True,
        "is_multiple_selection_allowed": False,
    }
    response = api_client.post("/concepts/activities/activities", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Activity_000001"
    assert res["name"] == "new_name"
    assert res["name_sentence_case"] == "new_name"
    assert res["nci_concept_id"] == "C12345"
    assert res["nci_concept_name"] == "NAME-C12345"
    assert res["synonyms"] == ["NAME", "C12345"]
    assert res["definition"] == "definition"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["activity_groupings"] == [
        {
            "activity_subgroup_uid": "activity_subgroup_root1",
            "activity_subgroup_name": "name1",
            "activity_subgroup_version": None,
            "activity_group_uid": "activity_group_root1",
            "activity_group_name": "name1",
            "activity_group_version": None,
        },
        {
            "activity_subgroup_uid": "activity_subgroup_root3",
            "activity_subgroup_name": "name3",
            "activity_subgroup_version": None,
            "activity_group_uid": "activity_group_root3",
            "activity_group_name": "name3",
            "activity_group_version": None,
        },
    ]
    assert res["is_data_collected"] is True
    assert res["is_multiple_selection_allowed"] is False
    assert res["is_finalized"] is False
    assert res["is_used_by_legacy_instances"] is False
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["request_rationale"] is None
    assert res["is_request_final"] is False
    assert res["is_request_rejected"] is False
    assert res["contact_person"] is None
    assert res["reason_for_rejecting"] is None
    assert res["used_by_studies"] == []
    assert res["replaced_by_activity"] is None


def test_get_all_activities(api_client):
    response = api_client.get("/concepts/activities/activities?total_count=true")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "activity_root1"
    assert res["items"][0]["name"] == "name1"
    assert res["items"][0]["name_sentence_case"] == "name1"
    assert res["items"][0]["nci_concept_id"] is None
    assert res["items"][0]["nci_concept_name"] is None
    assert res["items"][0]["synonyms"] == []
    assert res["items"][0]["definition"] == "definition1"
    assert res["items"][0]["abbreviation"] == "abbv"
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["activity_groupings"] == [
        {
            "activity_subgroup_uid": "activity_subgroup_root1",
            "activity_subgroup_name": "name1",
            "activity_subgroup_version": "1.0",
            "activity_group_uid": "activity_group_root1",
            "activity_group_name": "name1",
            "activity_group_version": "1.0",
        }
    ]
    assert res["items"][0]["is_data_collected"] is False
    assert res["items"][0]["is_multiple_selection_allowed"] is True
    assert res["items"][0]["is_finalized"] is False
    assert res["items"][0]["is_used_by_legacy_instances"] is False
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] == "Final"
    assert res["items"][0]["version"] == "1.0"
    assert res["items"][0]["change_description"] == "Approved version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["possible_actions"] == ["inactivate", "new_version"]
    assert res["items"][0]["request_rationale"] is None
    assert res["items"][0]["is_request_final"] is False
    assert res["items"][0]["is_request_rejected"] is False
    assert res["items"][0]["contact_person"] is None
    assert res["items"][0]["reason_for_rejecting"] is None
    assert res["items"][0]["used_by_studies"] == []
    assert res["items"][0]["replaced_by_activity"] is None
    assert res["items"][1]["uid"] == "activity_root2"
    assert res["items"][1]["name"] == "name2"
    assert res["items"][1]["name_sentence_case"] == "name2"
    assert res["items"][1]["nci_concept_id"] is None
    assert res["items"][1]["nci_concept_name"] is None
    assert res["items"][1]["synonyms"] == []
    assert res["items"][1]["definition"] == "definition2"
    assert res["items"][1]["abbreviation"] == "abbv"
    assert res["items"][1]["library_name"] == "Sponsor"
    assert res["items"][1]["activity_groupings"] == [
        {
            "activity_subgroup_uid": "activity_subgroup_root2",
            "activity_subgroup_name": "name2",
            "activity_subgroup_version": "1.0",
            "activity_group_uid": "activity_group_root2",
            "activity_group_name": "name2",
            "activity_group_version": "1.0",
        }
    ]
    assert res["items"][1]["is_data_collected"] is False
    assert res["items"][1]["is_multiple_selection_allowed"] is True
    assert res["items"][1]["is_finalized"] is False
    assert res["items"][1]["is_used_by_legacy_instances"] is False
    assert res["items"][1]["end_date"] is None
    assert res["items"][1]["status"] == "Draft"
    assert res["items"][1]["version"] == "0.1"
    assert res["items"][1]["change_description"] == "New draft version"
    assert res["items"][1]["author_username"] == "unknown-user@example.com"
    assert res["items"][1]["possible_actions"] == ["approve", "delete", "edit"]
    assert res["items"][1]["request_rationale"] is None
    assert res["items"][1]["is_request_final"] is False
    assert res["items"][1]["is_request_rejected"] is False
    assert res["items"][1]["contact_person"] is None
    assert res["items"][1]["reason_for_rejecting"] is None
    assert res["items"][1]["used_by_studies"] == []
    assert res["items"][1]["replaced_by_activity"] is None
    assert res["items"][2]["uid"] == "activity_root3"
    assert res["items"][2]["name"] == "name3"
    assert res["items"][2]["name_sentence_case"] == "name3"
    assert res["items"][2]["nci_concept_id"] is None
    assert res["items"][2]["nci_concept_name"] is None
    assert res["items"][2]["synonyms"] == []
    assert res["items"][2]["definition"] == "definition3"
    assert res["items"][2]["abbreviation"] == "abbv"
    assert res["items"][2]["library_name"] == "Sponsor"
    assert res["items"][2]["activity_groupings"] == [
        {
            "activity_subgroup_uid": "activity_subgroup_root3",
            "activity_subgroup_name": "name3",
            "activity_subgroup_version": "1.0",
            "activity_group_uid": "activity_group_root3",
            "activity_group_name": "name3",
            "activity_group_version": "1.0",
        }
    ]
    assert res["items"][2]["is_data_collected"] is False
    assert res["items"][2]["is_multiple_selection_allowed"] is True
    assert res["items"][2]["is_finalized"] is False
    assert res["items"][2]["is_used_by_legacy_instances"] is False
    assert res["items"][2]["end_date"] is None
    assert res["items"][2]["status"] == "Final"
    assert res["items"][2]["version"] == "1.0"
    assert res["items"][2]["change_description"] == "Approved version"
    assert res["items"][2]["author_username"] == "unknown-user@example.com"
    assert res["items"][2]["possible_actions"] == ["inactivate", "new_version"]
    assert res["items"][2]["request_rationale"] is None
    assert res["items"][2]["is_request_final"] is False
    assert res["items"][2]["is_request_rejected"] is False
    assert res["items"][2]["contact_person"] is None
    assert res["items"][2]["reason_for_rejecting"] is None
    assert res["items"][2]["used_by_studies"] == []
    assert res["items"][2]["replaced_by_activity"] is None
    assert res["items"][3]["uid"] == "Activity_000001"
    assert res["items"][3]["name"] == "new_name"
    assert res["items"][3]["name_sentence_case"] == "new_name"
    assert res["items"][3]["nci_concept_id"] == "C12345"
    assert res["items"][3]["nci_concept_name"] == "NAME-C12345"
    assert res["items"][3]["synonyms"] == ["NAME", "C12345"]
    assert res["items"][3]["definition"] == "definition"
    assert res["items"][3]["abbreviation"] == "abbv"
    assert res["items"][3]["library_name"] == "Sponsor"
    assert res["items"][3]["activity_groupings"] == [
        {
            "activity_subgroup_uid": "activity_subgroup_root1",
            "activity_subgroup_name": "name1",
            "activity_subgroup_version": "1.0",
            "activity_group_uid": "activity_group_root1",
            "activity_group_name": "name1",
            "activity_group_version": "1.0",
        },
        {
            "activity_subgroup_uid": "activity_subgroup_root3",
            "activity_subgroup_name": "name3",
            "activity_subgroup_version": "1.0",
            "activity_group_uid": "activity_group_root3",
            "activity_group_name": "name3",
            "activity_group_version": "1.0",
        },
    ]
    assert res["items"][3]["is_data_collected"] is True
    assert res["items"][3]["is_multiple_selection_allowed"] is False
    assert res["items"][3]["is_finalized"] is False
    assert res["items"][3]["is_used_by_legacy_instances"] is False
    assert res["items"][3]["end_date"] is None
    assert res["items"][3]["status"] == "Draft"
    assert res["items"][3]["version"] == "0.1"
    assert res["items"][3]["change_description"] == "Initial version"
    assert res["items"][3]["author_username"] == "unknown-user@example.com"
    assert res["items"][3]["possible_actions"] == ["approve", "delete", "edit"]
    assert res["items"][3]["request_rationale"] is None
    assert res["items"][3]["is_request_final"] is False
    assert res["items"][3]["is_request_rejected"] is False
    assert res["items"][3]["contact_person"] is None
    assert res["items"][3]["reason_for_rejecting"] is None
    assert res["items"][3]["used_by_studies"] == []
    assert res["items"][3]["replaced_by_activity"] is None


def test_get_all_activities_from_a_given_activity_sub_group(api_client):
    response = api_client.get(
        "/concepts/activities/activities?activity_subgroup_uid=activity_subgroup_root2&total_count=true"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "activity_root2"
    assert res["items"][0]["name"] == "name2"
    assert res["items"][0]["name_sentence_case"] == "name2"
    assert res["items"][0]["nci_concept_id"] is None
    assert res["items"][0]["nci_concept_name"] is None
    assert res["items"][0]["synonyms"] == []
    assert res["items"][0]["definition"] == "definition2"
    assert res["items"][0]["abbreviation"] == "abbv"
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["activity_groupings"] == [
        {
            "activity_subgroup_uid": "activity_subgroup_root2",
            "activity_subgroup_name": "name2",
            "activity_subgroup_version": "1.0",
            "activity_group_uid": "activity_group_root2",
            "activity_group_name": "name2",
            "activity_group_version": "1.0",
        }
    ]
    assert res["items"][0]["is_data_collected"] is False
    assert res["items"][0]["is_multiple_selection_allowed"] is True
    assert res["items"][0]["is_finalized"] is False
    assert res["items"][0]["is_used_by_legacy_instances"] is False
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] == "Draft"
    assert res["items"][0]["version"] == "0.1"
    assert res["items"][0]["change_description"] == "New draft version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["possible_actions"] == ["approve", "delete", "edit"]
    assert res["items"][0]["request_rationale"] is None
    assert res["items"][0]["is_request_final"] is False
    assert res["items"][0]["is_request_rejected"] is False
    assert res["items"][0]["contact_person"] is None
    assert res["items"][0]["reason_for_rejecting"] is None
    assert res["items"][0]["used_by_studies"] == []
    assert res["items"][0]["replaced_by_activity"] is None


def test_get_all_activities_with_a_given_name(api_client):
    response = api_client.get(
        "/concepts/activities/activities?activity_names[]=name2&total_count=true"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "activity_root2"
    assert res["items"][0]["name"] == "name2"
    assert res["items"][0]["name_sentence_case"] == "name2"
    assert res["items"][0]["nci_concept_id"] is None
    assert res["items"][0]["nci_concept_name"] is None
    assert res["items"][0]["synonyms"] == []
    assert res["items"][0]["definition"] == "definition2"
    assert res["items"][0]["abbreviation"] == "abbv"
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["activity_groupings"] == [
        {
            "activity_subgroup_uid": "activity_subgroup_root2",
            "activity_subgroup_name": "name2",
            "activity_subgroup_version": "1.0",
            "activity_group_uid": "activity_group_root2",
            "activity_group_name": "name2",
            "activity_group_version": "1.0",
        }
    ]
    assert res["items"][0]["is_data_collected"] is False
    assert res["items"][0]["is_multiple_selection_allowed"] is True
    assert res["items"][0]["is_finalized"] is False
    assert res["items"][0]["is_used_by_legacy_instances"] is False
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] == "Draft"
    assert res["items"][0]["version"] == "0.1"
    assert res["items"][0]["change_description"] == "New draft version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["possible_actions"] == ["approve", "delete", "edit"]
    assert res["items"][0]["request_rationale"] is None
    assert res["items"][0]["is_request_final"] is False
    assert res["items"][0]["is_request_rejected"] is False
    assert res["items"][0]["contact_person"] is None
    assert res["items"][0]["reason_for_rejecting"] is None
    assert res["items"][0]["used_by_studies"] == []
    assert res["items"][0]["replaced_by_activity"] is None


def test_get_all_activities_from_a_given_activity_sub_group_using_name(api_client):
    response = api_client.get(
        "/concepts/activities/activities?activity_subgroup_names[]=name2&total_count=true"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "activity_root2"
    assert res["items"][0]["name"] == "name2"
    assert res["items"][0]["name_sentence_case"] == "name2"
    assert res["items"][0]["nci_concept_id"] is None
    assert res["items"][0]["nci_concept_name"] is None
    assert res["items"][0]["synonyms"] == []
    assert res["items"][0]["definition"] == "definition2"
    assert res["items"][0]["abbreviation"] == "abbv"
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["activity_groupings"] == [
        {
            "activity_subgroup_uid": "activity_subgroup_root2",
            "activity_subgroup_name": "name2",
            "activity_subgroup_version": "1.0",
            "activity_group_uid": "activity_group_root2",
            "activity_group_name": "name2",
            "activity_group_version": "1.0",
        }
    ]
    assert res["items"][0]["is_data_collected"] is False
    assert res["items"][0]["is_multiple_selection_allowed"] is True
    assert res["items"][0]["is_finalized"] is False
    assert res["items"][0]["is_used_by_legacy_instances"] is False
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] == "Draft"
    assert res["items"][0]["version"] == "0.1"
    assert res["items"][0]["change_description"] == "New draft version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["possible_actions"] == ["approve", "delete", "edit"]
    assert res["items"][0]["request_rationale"] is None
    assert res["items"][0]["is_request_final"] is False
    assert res["items"][0]["is_request_rejected"] is False
    assert res["items"][0]["contact_person"] is None
    assert res["items"][0]["reason_for_rejecting"] is None
    assert res["items"][0]["used_by_studies"] == []
    assert res["items"][0]["replaced_by_activity"] is None


def test_get_all_activities_from_a_given_activity_group_using_name(api_client):
    response = api_client.get(
        "/concepts/activities/activities?activity_group_names[]=name2&total_count=true"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "activity_root2"
    assert res["items"][0]["name"] == "name2"
    assert res["items"][0]["name_sentence_case"] == "name2"
    assert res["items"][0]["nci_concept_id"] is None
    assert res["items"][0]["nci_concept_name"] is None
    assert res["items"][0]["synonyms"] == []
    assert res["items"][0]["definition"] == "definition2"
    assert res["items"][0]["abbreviation"] == "abbv"
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["activity_groupings"] == [
        {
            "activity_subgroup_uid": "activity_subgroup_root2",
            "activity_subgroup_name": "name2",
            "activity_subgroup_version": "1.0",
            "activity_group_uid": "activity_group_root2",
            "activity_group_name": "name2",
            "activity_group_version": "1.0",
        }
    ]
    assert res["items"][0]["is_data_collected"] is False
    assert res["items"][0]["is_multiple_selection_allowed"] is True
    assert res["items"][0]["is_finalized"] is False
    assert res["items"][0]["is_used_by_legacy_instances"] is False
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] == "Draft"
    assert res["items"][0]["version"] == "0.1"
    assert res["items"][0]["change_description"] == "New draft version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["possible_actions"] == ["approve", "delete", "edit"]
    assert res["items"][0]["request_rationale"] is None
    assert res["items"][0]["is_request_final"] is False
    assert res["items"][0]["is_request_rejected"] is False
    assert res["items"][0]["contact_person"] is None
    assert res["items"][0]["reason_for_rejecting"] is None
    assert res["items"][0]["used_by_studies"] == []
    assert res["items"][0]["replaced_by_activity"] is None


def test_post_approve_activity(api_client):
    response = api_client.post(
        "/concepts/activities/activities/Activity_000001/approvals"
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Activity_000001"
    assert res["name"] == "new_name"
    assert res["name_sentence_case"] == "new_name"
    assert res["nci_concept_id"] == "C12345"
    assert res["nci_concept_name"] == "NAME-C12345"
    assert res["synonyms"] == ["NAME", "C12345"]
    assert res["definition"] == "definition"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["activity_groupings"] == [
        {
            "activity_subgroup_uid": "activity_subgroup_root1",
            "activity_subgroup_name": "name1",
            "activity_subgroup_version": "1.0",
            "activity_group_uid": "activity_group_root1",
            "activity_group_name": "name1",
            "activity_group_version": "1.0",
        },
        {
            "activity_subgroup_uid": "activity_subgroup_root3",
            "activity_subgroup_name": "name3",
            "activity_subgroup_version": "1.0",
            "activity_group_uid": "activity_group_root3",
            "activity_group_name": "name3",
            "activity_group_version": "1.0",
        },
    ]
    assert res["is_data_collected"] is True
    assert res["is_multiple_selection_allowed"] is False
    assert res["is_finalized"] is False
    assert res["is_used_by_legacy_instances"] is False
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["inactivate", "new_version"]
    assert res["request_rationale"] is None
    assert res["is_request_final"] is False
    assert res["is_request_rejected"] is False
    assert res["contact_person"] is None
    assert res["reason_for_rejecting"] is None
    assert res["used_by_studies"] == []
    assert res["replaced_by_activity"] is None


def test_post_versions_activity(api_client):
    response = api_client.post(
        "/concepts/activities/activities/Activity_000001/versions"
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Activity_000001"
    assert res["name"] == "new_name"
    assert res["name_sentence_case"] == "new_name"
    assert res["nci_concept_id"] == "C12345"
    assert res["nci_concept_name"] == "NAME-C12345"
    assert res["synonyms"] == ["NAME", "C12345"]
    assert res["definition"] == "definition"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["activity_groupings"] == [
        {
            "activity_subgroup_uid": "activity_subgroup_root1",
            "activity_subgroup_name": "name1",
            "activity_subgroup_version": "1.0",
            "activity_group_uid": "activity_group_root1",
            "activity_group_name": "name1",
            "activity_group_version": "1.0",
        },
        {
            "activity_subgroup_uid": "activity_subgroup_root3",
            "activity_subgroup_name": "name3",
            "activity_subgroup_version": "1.0",
            "activity_group_uid": "activity_group_root3",
            "activity_group_name": "name3",
            "activity_group_version": "1.0",
        },
    ]
    assert res["is_data_collected"] is True
    assert res["is_multiple_selection_allowed"] is False
    assert res["is_finalized"] is False
    assert res["is_used_by_legacy_instances"] is False
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["change_description"] == "New draft created"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "edit"]
    assert res["request_rationale"] is None
    assert res["is_request_final"] is False
    assert res["is_request_rejected"] is False
    assert res["contact_person"] is None
    assert res["reason_for_rejecting"] is None
    assert res["used_by_studies"] == []
    assert res["replaced_by_activity"] is None


def test_delete_activations_activity(api_client):
    response = api_client.delete(
        "/concepts/activities/activities/activity_root1/activations"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "activity_root1"
    assert res["name"] == "name1"
    assert res["name_sentence_case"] == "name1"
    assert res["nci_concept_id"] is None
    assert res["nci_concept_name"] is None
    assert res["synonyms"] == []
    assert res["definition"] == "definition1"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["activity_groupings"] == [
        {
            "activity_subgroup_uid": "activity_subgroup_root1",
            "activity_subgroup_name": "name1",
            "activity_subgroup_version": "1.0",
            "activity_group_uid": "activity_group_root1",
            "activity_group_name": "name1",
            "activity_group_version": "1.0",
        }
    ]
    assert res["is_data_collected"] is False
    assert res["is_multiple_selection_allowed"] is True
    assert res["is_finalized"] is False
    assert res["is_used_by_legacy_instances"] is False
    assert res["end_date"] is None
    assert res["status"] == "Retired"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Inactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["reactivate"]
    assert res["request_rationale"] is None
    assert res["is_request_final"] is False
    assert res["is_request_rejected"] is False
    assert res["contact_person"] is None
    assert res["reason_for_rejecting"] is None
    assert res["used_by_studies"] == []
    assert res["replaced_by_activity"] is None


def test_post_activations_activity(api_client):
    response = api_client.post(
        "/concepts/activities/activities/activity_root1/activations"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "activity_root1"
    assert res["name"] == "name1"
    assert res["name_sentence_case"] == "name1"
    assert res["nci_concept_id"] is None
    assert res["nci_concept_name"] is None
    assert res["synonyms"] == []
    assert res["definition"] == "definition1"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["activity_groupings"] == [
        {
            "activity_subgroup_uid": "activity_subgroup_root1",
            "activity_subgroup_name": "name1",
            "activity_subgroup_version": "1.0",
            "activity_group_uid": "activity_group_root1",
            "activity_group_name": "name1",
            "activity_group_version": "1.0",
        }
    ]
    assert res["is_data_collected"] is False
    assert res["is_multiple_selection_allowed"] is True
    assert res["is_finalized"] is False
    assert res["is_used_by_legacy_instances"] is False
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["inactivate", "new_version"]
    assert res["request_rationale"] is None
    assert res["is_request_final"] is False
    assert res["is_request_rejected"] is False
    assert res["contact_person"] is None
    assert res["reason_for_rejecting"] is None
    assert res["used_by_studies"] == []
    assert res["replaced_by_activity"] is None


def test_delete_activity(api_client):
    response = api_client.delete("/concepts/activities/activities/activity_root2")

    assert_response_status_code(response, 204)
