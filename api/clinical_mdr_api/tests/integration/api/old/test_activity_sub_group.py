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
    inject_and_clear_db("old.json.test.activity.sub.group")
    db.cypher_query(STARTUP_ACTIVITY_GROUPS)
    db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
    db.cypher_query(STARTUP_ACTIVITIES)

    yield

    drop_db("old.json.test.activity.sub.group")


def test_post_create_activity_sub_group(api_client):
    data = {
        "name": "new_name",
        "name_sentence_case": "new_name",
        "definition": "definition",
        "abbreviation": "abbv",
        "library_name": "Sponsor",
        "nci_concept_id": "CONCEPT_ID",
        "nci_concept_name": "CONCEPT_NAME",
    }
    response = api_client.post("/concepts/activities/activity-sub-groups", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "ActivitySubGroup_000001"
    assert res["name"] == "new_name"
    assert res["name_sentence_case"] == "new_name"
    assert res["definition"] == "definition"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["nci_concept_id"] == data["nci_concept_id"]
    assert res["nci_concept_name"] == data["nci_concept_name"]
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_get_all_activity_sub_groups(api_client):
    response = api_client.get(
        "/concepts/activities/activity-sub-groups?total_count=true"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "activity_subgroup_root1"
    assert res["items"][0]["name"] == "name1"
    assert res["items"][0]["name_sentence_case"] == "name1"
    assert res["items"][0]["definition"] == "definition1"
    assert res["items"][0]["abbreviation"] == "abbv"
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] == "Final"
    assert res["items"][0]["version"] == "1.0"
    assert res["items"][0]["change_description"] == "Approved version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["possible_actions"] == ["inactivate", "new_version"]
    assert res["items"][1]["uid"] == "activity_subgroup_root2"
    assert res["items"][1]["name"] == "name2"
    assert res["items"][1]["name_sentence_case"] == "name2"
    assert res["items"][1]["definition"] == "definition2"
    assert res["items"][1]["abbreviation"] == "abbv"
    assert res["items"][1]["library_name"] == "Sponsor"
    assert res["items"][1]["end_date"] is None
    assert res["items"][1]["status"] == "Final"
    assert res["items"][1]["version"] == "1.0"
    assert res["items"][1]["change_description"] == "Approved version"
    assert res["items"][1]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["possible_actions"] == ["inactivate", "new_version"]
    assert res["items"][2]["uid"] == "activity_subgroup_root3"
    assert res["items"][2]["name"] == "name3"
    assert res["items"][2]["name_sentence_case"] == "name3"
    assert res["items"][2]["definition"] == "definition3"
    assert res["items"][2]["abbreviation"] == "abbv"
    assert res["items"][2]["library_name"] == "Sponsor"
    assert res["items"][2]["end_date"] is None
    assert res["items"][2]["status"] == "Final"
    assert res["items"][2]["version"] == "1.0"
    assert res["items"][2]["change_description"] == "Approved version"
    assert res["items"][2]["author_username"] == "unknown-user@example.com"
    assert res["items"][2]["possible_actions"] == ["inactivate", "new_version"]
    assert res["items"][3]["uid"] == "ActivitySubGroup_000001"
    assert res["items"][3]["name"] == "new_name"
    assert res["items"][3]["name_sentence_case"] == "new_name"
    assert res["items"][3]["definition"] == "definition"
    assert res["items"][3]["abbreviation"] == "abbv"
    assert res["items"][3]["library_name"] == "Sponsor"
    assert res["items"][3]["end_date"] is None
    assert res["items"][3]["status"] == "Draft"
    assert res["items"][3]["version"] == "0.1"
    assert res["items"][3]["change_description"] == "Initial version"
    assert res["items"][3]["author_username"] == "unknown-user@example.com"
    assert res["items"][3]["possible_actions"] == ["approve", "delete", "edit"]


def test_post_approve_activity_sub_group(api_client):
    response = api_client.post(
        "/concepts/activities/activity-sub-groups/ActivitySubGroup_000001/approvals"
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "ActivitySubGroup_000001"
    assert res["name"] == "new_name"
    assert res["name_sentence_case"] == "new_name"
    assert res["definition"] == "definition"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_post_versions_activity_sub_group(api_client):
    response = api_client.post(
        "/concepts/activities/activity-sub-groups/ActivitySubGroup_000001/versions"
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "ActivitySubGroup_000001"
    assert res["name"] == "new_name"
    assert res["name_sentence_case"] == "new_name"
    assert res["definition"] == "definition"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["change_description"] == "New draft created"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "edit"]


def test_delete_activations_activity_sub_group(api_client):
    response = api_client.delete(
        "/concepts/activities/activity-sub-groups/activity_subgroup_root1/activations"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "activity_subgroup_root1"
    assert res["name"] == "name1"
    assert res["name_sentence_case"] == "name1"
    assert res["definition"] == "definition1"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Retired"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Inactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["reactivate"]


def test_post_activations_activity_sub_group(api_client):
    response = api_client.post(
        "/concepts/activities/activity-sub-groups/activity_subgroup_root1/activations"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "activity_subgroup_root1"
    assert res["name"] == "name1"
    assert res["name_sentence_case"] == "name1"
    assert res["definition"] == "definition1"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["inactivate", "new_version"]
