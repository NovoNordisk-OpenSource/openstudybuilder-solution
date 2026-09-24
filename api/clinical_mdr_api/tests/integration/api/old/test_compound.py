# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_ACTIVITIES,
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_ACTIVITY_INSTANCES,
    STARTUP_ACTIVITY_INSTANCES_CT_INIT,
    STARTUP_ACTIVITY_SUB_GROUPS,
    STARTUP_NUMERIC_VALUES_WITH_UNITS,
    STARTUP_PROJECTS_CYPHER,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.compound")
    db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
    db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
    db.cypher_query(STARTUP_ACTIVITY_GROUPS)
    db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
    db.cypher_query(STARTUP_ACTIVITIES)
    db.cypher_query(STARTUP_ACTIVITY_INSTANCES)
    db.cypher_query(STARTUP_NUMERIC_VALUES_WITH_UNITS)
    db.cypher_query(STARTUP_PROJECTS_CYPHER)

    yield

    drop_db("old.json.test.compound")


def test_post_create_compound(api_client):
    data = {
        "name": "compound_name1",
        "name_sentence_case": "compound_name_sentence_case1",
        "definition": "compound_definition1",
        "abbreviation": "abbv",
        "external_id": None,
        "library_name": "Sponsor",
        "status": None,
        "version": None,
        "change_description": None,
        "end_date": None,
    }
    response = api_client.post("/concepts/compounds", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Compound_000001"
    assert res["name"] == "compound_name1"
    assert res["name_sentence_case"] == "compound_name_sentence_case1"
    assert res["definition"] == "compound_definition1"
    assert res["abbreviation"] == "abbv"
    assert res["external_id"] is None
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_get_all_compounds(api_client):
    response = api_client.get("/concepts/compounds?total_count=true")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "Compound_000001"
    assert res["items"][0]["name"] == "compound_name1"
    assert res["items"][0]["name_sentence_case"] == "compound_name_sentence_case1"
    assert res["items"][0]["definition"] == "compound_definition1"
    assert res["items"][0]["abbreviation"] == "abbv"
    assert res["items"][0]["external_id"] is None
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["status"] == "Draft"
    assert res["items"][0]["version"] == "0.1"
    assert res["items"][0]["change_description"] == "Initial version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["possible_actions"] == ["approve", "delete", "edit"]


def test_get_all_simple_compounds(api_client):
    response = api_client.get("/concepts/compounds-simple?total_count=true")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "Compound_000001"
    assert res["items"][0]["name"] == "compound_name1"


def test_post_approve_compound(api_client):
    response = api_client.post("/concepts/compounds/Compound_000001/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Compound_000001"
    assert res["name"] == "compound_name1"
    assert res["name_sentence_case"] == "compound_name_sentence_case1"
    assert res["definition"] == "compound_definition1"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["inactivate", "new_version"]
    assert res["external_id"] is None


def test_post_versions_compound(api_client):
    response = api_client.post("/concepts/compounds/Compound_000001/versions")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Compound_000001"
    assert res["name"] == "compound_name1"
    assert res["name_sentence_case"] == "compound_name_sentence_case1"
    assert res["definition"] == "compound_definition1"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["change_description"] == "New draft created"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["approve", "edit"]
    assert res["external_id"] is None


def test_patch_draft_compound(api_client):
    data = {
        "name": "new_compound_name",
        "definition": "new_compound_definition",
        "external_id": None,
        "change_description": "compound_patch",
    }
    response = api_client.patch("/concepts/compounds/Compound_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "Compound_000001"
    assert res["name"] == "new_compound_name"
    assert res["name_sentence_case"] == "compound_name_sentence_case1"
    assert res["definition"] == "new_compound_definition"
    assert res["abbreviation"] == "abbv"
    assert res["external_id"] is None
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Draft"
    assert res["version"] == "1.2"
    assert res["change_description"] == "compound_patch"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["approve", "edit"]


def test_patch_draft_compound1(api_client):
    data = {
        "name": "new_compound_name",
        "definition": "new_compound_definition2",
        "external_id": None,
        "change_description": "compound_patch",
    }
    response = api_client.patch("/concepts/compounds/Compound_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "Compound_000001"
    assert res["name"] == "new_compound_name"
    assert res["name_sentence_case"] == "compound_name_sentence_case1"
    assert res["definition"] == "new_compound_definition2"
    assert res["abbreviation"] == "abbv"
    assert res["external_id"] is None
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Draft"
    assert res["version"] == "1.3"
    assert res["change_description"] == "compound_patch"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["approve", "edit"]


def test_post_approve_compound1(api_client):
    response = api_client.post("/concepts/compounds/Compound_000001/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Compound_000001"
    assert res["name"] == "new_compound_name"
    assert res["name_sentence_case"] == "compound_name_sentence_case1"
    assert res["definition"] == "new_compound_definition2"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Final"
    assert res["version"] == "2.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["inactivate", "new_version"]
    assert res["external_id"] is None


def test_delete_activations_compound(api_client):
    response = api_client.delete("/concepts/compounds/Compound_000001/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "Compound_000001"
    assert res["name"] == "new_compound_name"
    assert res["name_sentence_case"] == "compound_name_sentence_case1"
    assert res["definition"] == "new_compound_definition2"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Retired"
    assert res["version"] == "2.0"
    assert res["change_description"] == "Inactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["reactivate"]
    assert res["external_id"] is None


def test_post_activations_compound(api_client):
    response = api_client.post("/concepts/compounds/Compound_000001/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "Compound_000001"
    assert res["name"] == "new_compound_name"
    assert res["name_sentence_case"] == "compound_name_sentence_case1"
    assert res["definition"] == "new_compound_definition2"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Final"
    assert res["version"] == "2.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["inactivate", "new_version"]
    assert res["external_id"] is None


def test_post_create_compound_to_delete(api_client):
    data = {
        "name": "compound_name2",
        "name_sentence_case": "compound_name_sentence_case2",
        "definition": "compound_definition2",
        "abbreviation": "abbv",
        "external_id": None,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/compounds", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Compound_000002"
    assert res["name"] == "compound_name2"
    assert res["name_sentence_case"] == "compound_name_sentence_case2"
    assert res["definition"] == "compound_definition2"
    assert res["abbreviation"] == "abbv"
    assert res["external_id"] is None
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_delete_compound(api_client):
    response = api_client.delete("/concepts/compounds/Compound_000002")

    assert_response_status_code(response, 204)
