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
    inject_and_clear_db("old.json.test.compound.alias")
    db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
    db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
    db.cypher_query(STARTUP_ACTIVITY_GROUPS)
    db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
    db.cypher_query(STARTUP_ACTIVITIES)
    db.cypher_query(STARTUP_ACTIVITY_INSTANCES)
    db.cypher_query(STARTUP_NUMERIC_VALUES_WITH_UNITS)
    db.cypher_query(STARTUP_PROJECTS_CYPHER)

    yield

    drop_db("old.json.test.compound.alias")


def test_post_create_compound1(api_client):
    data = {
        "name": "compound_name1",
        "name_sentence_case": "compound_name_sentence_case1",
        "definition": "compound_definition1",
        "abbreviation": "abbv",
        "external_id": None,
        "is_name_inn": True,
        "library_name": "Sponsor",
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


def test_post_approve_compound1(api_client):
    response = api_client.post("/concepts/compounds/Compound_000001/approvals")
    assert_response_status_code(response, 201)


def test_post_create_compound_alias(api_client):
    data = {
        "name": "compound_alias_name1",
        "name_sentence_case": "compound_alias_name_sentence_case1",
        "definition": "compound_alias_definition1",
        "abbreviation": "abbv",
        "compound_uid": "Compound_000001",
        "is_preferred_synonym": True,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/compound-aliases", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "CompoundAlias_000001"
    assert res["name"] == "compound_alias_name1"
    assert res["name_sentence_case"] == "compound_alias_name_sentence_case1"
    assert res["definition"] == "compound_alias_definition1"
    assert res["abbreviation"] == "abbv"
    assert res["compound"] == {"uid": "Compound_000001", "name": "compound_name1"}
    assert res["is_preferred_synonym"] is True
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_patch_draft_compound_alias(api_client):
    data = {
        "name": "compound_alias_name1_updated",
        "compound_uid": "Compound_000001",
        "name_sentence_case": "compound_alias_name_sentence_case1_updated",
        "definition": "compound_alias_definition1_updated",
        "abbreviation": "abbv_updated",
        "is_preferred_synonym": False,
        "library_name": "Sponsor",
        "change_description": "patched",
    }
    response = api_client.patch(
        "/concepts/compound-aliases/CompoundAlias_000001", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "CompoundAlias_000001"
    assert res["name"] == "compound_alias_name1_updated"
    assert res["name_sentence_case"] == "compound_alias_name_sentence_case1_updated"
    assert res["definition"] == "compound_alias_definition1_updated"
    assert res["abbreviation"] == "abbv_updated"
    assert res["compound"] == {"uid": "Compound_000001", "name": "compound_name1"}
    assert res["is_preferred_synonym"] is False
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["change_description"] == "patched"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_patch_draft_compound_alias_pt_2(api_client):
    data = {
        "name": "compound_alias_name1",
        "compound_uid": "Compound_000001",
        "name_sentence_case": "compound_alias_name_sentence_case1",
        "definition": "compound_alias_definition1",
        "abbreviation": "abbv",
        "is_preferred_synonym": True,
        "library_name": "Sponsor",
        "change_description": "patched",
    }
    response = api_client.patch(
        "/concepts/compound-aliases/CompoundAlias_000001", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "CompoundAlias_000001"
    assert res["name"] == "compound_alias_name1"
    assert res["name_sentence_case"] == "compound_alias_name_sentence_case1"
    assert res["definition"] == "compound_alias_definition1"
    assert res["abbreviation"] == "abbv"
    assert res["compound"] == {"uid": "Compound_000001", "name": "compound_name1"}
    assert res["is_preferred_synonym"] is True
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Draft"
    assert res["version"] == "0.3"
    assert res["change_description"] == "patched"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_get_all_compound_aliases_from_given_library(api_client):
    response = api_client.get(
        "/concepts/compound-aliases?library_name=Sponsor&total_count=true"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "CompoundAlias_000001"
    assert res["items"][0]["name"] == "compound_alias_name1"
    assert res["items"][0]["name_sentence_case"] == "compound_alias_name_sentence_case1"
    assert res["items"][0]["definition"] == "compound_alias_definition1"
    assert res["items"][0]["abbreviation"] == "abbv"
    assert res["items"][0]["compound"] == {
        "uid": "Compound_000001",
        "name": "compound_name1",
    }
    assert res["items"][0]["is_preferred_synonym"] is True
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["status"] == "Draft"
    assert res["items"][0]["version"] == "0.3"
    assert res["items"][0]["change_description"] == "patched"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["possible_actions"] == ["approve", "delete", "edit"]


def test_post_approve_compound_alias(api_client):
    response = api_client.post(
        "concepts/compound-aliases/CompoundAlias_000001/approvals"
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "CompoundAlias_000001"
    assert res["compound"] == {"uid": "Compound_000001", "name": "compound_name1"}
    assert res["is_preferred_synonym"] is True
    assert res["name"] == "compound_alias_name1"
    assert res["name_sentence_case"] == "compound_alias_name_sentence_case1"
    assert res["definition"] == "compound_alias_definition1"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_post_versions_compound_alias(api_client):
    response = api_client.post(
        "/concepts/compound-aliases/CompoundAlias_000001/versions"
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "CompoundAlias_000001"
    assert res["compound"] == {"uid": "Compound_000001", "name": "compound_name1"}
    assert res["is_preferred_synonym"] is True
    assert res["name"] == "compound_alias_name1"
    assert res["name_sentence_case"] == "compound_alias_name_sentence_case1"
    assert res["definition"] == "compound_alias_definition1"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["change_description"] == "New draft created"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["approve", "edit"]


def test_post_approve_compound_alias1(api_client):
    response = api_client.post(
        "concepts/compound-aliases/CompoundAlias_000001/approvals"
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "CompoundAlias_000001"
    assert res["compound"] == {"uid": "Compound_000001", "name": "compound_name1"}
    assert res["is_preferred_synonym"] is True
    assert res["name"] == "compound_alias_name1"
    assert res["name_sentence_case"] == "compound_alias_name_sentence_case1"
    assert res["definition"] == "compound_alias_definition1"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Final"
    assert res["version"] == "2.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_delete_activations_compound_alias(api_client):
    response = api_client.delete(
        "concepts/compound-aliases/CompoundAlias_000001/activations"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "CompoundAlias_000001"
    assert res["compound"] == {"uid": "Compound_000001", "name": "compound_name1"}
    assert res["is_preferred_synonym"] is True
    assert res["name"] == "compound_alias_name1"
    assert res["name_sentence_case"] == "compound_alias_name_sentence_case1"
    assert res["definition"] == "compound_alias_definition1"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Retired"
    assert res["version"] == "2.0"
    assert res["change_description"] == "Inactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["reactivate"]


def test_post_activations_compound_alias(api_client):
    response = api_client.post(
        "concepts/compound-aliases/CompoundAlias_000001/activations"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "CompoundAlias_000001"
    assert res["compound"] == {"uid": "Compound_000001", "name": "compound_name1"}
    assert res["is_preferred_synonym"] is True
    assert res["name"] == "compound_alias_name1"
    assert res["name_sentence_case"] == "compound_alias_name_sentence_case1"
    assert res["definition"] == "compound_alias_definition1"
    assert res["abbreviation"] == "abbv"
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Final"
    assert res["version"] == "2.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_getting_possible_header_values(api_client):
    response = api_client.get("concepts/compound-aliases/headers?field_name=name")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == ["compound_alias_name1"]
