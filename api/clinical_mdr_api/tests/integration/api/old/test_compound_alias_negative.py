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
    inject_and_clear_db("old.json.test.compound.alias.negative")
    db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
    db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
    db.cypher_query(STARTUP_ACTIVITY_GROUPS)
    db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
    db.cypher_query(STARTUP_ACTIVITIES)
    db.cypher_query(STARTUP_ACTIVITY_INSTANCES)
    db.cypher_query(STARTUP_NUMERIC_VALUES_WITH_UNITS)
    db.cypher_query(STARTUP_PROJECTS_CYPHER)

    yield

    drop_db("old.json.test.compound.alias.negative")


def test_post_create_compound2(api_client):
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


def test_post_approve_compound2(api_client):
    response = api_client.post("/concepts/compounds/Compound_000001/approvals")
    assert_response_status_code(response, 201)


def test_post_create_compound_alias_preferred_synonym(api_client):
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


def test_post_create_second_compound_alias_not_preferred_synonym(api_client):
    data = {
        "name": "compound_alias_name2",
        "name_sentence_case": "compound_alias_name_sentence_case2",
        "definition": "compound_alias_definition2",
        "abbreviation": "abbv2",
        "compound_uid": "Compound_000001",
        "is_preferred_synonym": False,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/compound-aliases", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "CompoundAlias_000002"
    assert res["name"] == "compound_alias_name2"
    assert res["name_sentence_case"] == "compound_alias_name_sentence_case2"
    assert res["definition"] == "compound_alias_definition2"
    assert res["abbreviation"] == "abbv2"
    assert res["compound"] == {"uid": "Compound_000001", "name": "compound_name1"}
    assert res["is_preferred_synonym"] is False
    assert res["library_name"] == "Sponsor"
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_post_compound_alias_as_second_preferred_synonym(api_client):
    data = {
        "name": "synonym_x",
        "name_sentence_case": "synonym_x",
        "definition": "synonym_x",
        "abbreviation": "abbv_XYZ",
        "compound_uid": "Compound_000001",
        "is_preferred_synonym": True,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/compound-aliases", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"] == "Another preferred synonym for compound is already defined."
    )


def test_patch_compound_alias_as_second_preferred_synonym(api_client):
    data = {
        "name": "synonym_x",
        "name_sentence_case": "synonym_x",
        "definition": "synonym_x",
        "abbreviation": "abbv2",
        "compound_uid": "Compound_000001",
        "is_preferred_synonym": True,
        "library_name": "Sponsor",
        "change_description": "patched",
    }
    response = api_client.patch(
        "/concepts/compound-aliases/CompoundAlias_000002", json=data
    )

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"] == "Another preferred synonym for compound is already defined."
    )


def test_get_all_compound_alias_non_existent_library_passed(api_client):
    response = api_client.get("/concepts/compound-aliases?library_name=non-existent")

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert res["message"] == "Library with Name 'non-existent' doesn't exist."


def test_delete_activations_non_final_compound_alias(api_client):
    response = api_client.delete(
        "/concepts/compound-aliases/CompoundAlias_000001/activations"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Cannot retire draft version."


def test_post_approve_compound_alias2(api_client):
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


def test_post_approve_non_draft_compound_alias(api_client):
    response = api_client.post(
        "/concepts/compound-aliases/CompoundAlias_000001/approvals"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."


def test_post_activations_non_retired_compound_alias(api_client):
    response = api_client.post(
        "/concepts/compound-aliases/CompoundAlias_000001/activations"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Only RETIRED version can be reactivated."


def test_delete_accepted_object3(api_client):
    response = api_client.delete("/concepts/compound-aliases/CompoundAlias_000001")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Object has been accepted"


def test_create_compound_alias_with_name_that_already_exists(api_client):
    data = {
        "name": "compound_alias_name1",
        "name_sentence_case": "compound_alias_name_sentence_case1_XYZ",
        "definition": "compound_alias_definition1_XYZ",
        "abbreviation": "abbv_XYZ",
        "compound_uid": "Compound_000001",
        "is_preferred_synonym": True,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/compound-aliases", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "Compound Alias with Name 'compound_alias_name1' already exists."
    )


def test_create_compound_alias_with_name_sentence_case_that_already_exists(api_client):
    data = {
        "name": "compound_alias_name1_XYZ",
        "name_sentence_case": "compound_alias_name_sentence_case1",
        "definition": "compound_alias_definition1_XYZ",
        "abbreviation": "abbv_XYZ",
        "compound_uid": "Compound_000001",
        "is_preferred_synonym": True,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/compound-aliases", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "Compound Alias with Name Sentence Case 'compound_alias_name_sentence_case1' already exists."
    )


def test_create_compound_alias_with_abbreviation_that_already_exists(api_client):
    data = {
        "name": "compound_alias_name1_XYZ",
        "name_sentence_case": "compound_alias_name_sentence_case1_XYZ",
        "definition": "compound_alias_definition1_XYZ",
        "abbreviation": "abbv",
        "compound_uid": "Compound_000001",
        "is_preferred_synonym": True,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/compound-aliases", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == "Compound Alias with Abbreviation 'abbv' already exists."


def test_create_compound_alias_with_non_existent_compound(api_client):
    data = {
        "name": "compound_alias_name3",
        "name_sentence_case": "compound_alias_name_sentence_case3",
        "definition": "compound_alias_definition3",
        "abbreviation": "abbv3",
        "compound_uid": "non-existent-uid",
        "is_preferred_synonym": True,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/compound-aliases", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "CompoundAliasVO tried to connect to non-existent Compound with UID 'non-existent-uid'."
    )
