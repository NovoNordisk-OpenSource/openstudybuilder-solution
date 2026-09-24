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
    inject_and_clear_db("old.json.test.compound.negative")
    db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
    db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
    db.cypher_query(STARTUP_ACTIVITY_GROUPS)
    db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
    db.cypher_query(STARTUP_ACTIVITIES)
    db.cypher_query(STARTUP_ACTIVITY_INSTANCES)
    db.cypher_query(STARTUP_NUMERIC_VALUES_WITH_UNITS)
    db.cypher_query(STARTUP_PROJECTS_CYPHER)

    yield

    drop_db("old.json.test.compound.negative")


def test_post_create_compound3(api_client):
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


def test_post_name_already_exists(api_client):
    data = {
        "name": "compound_name1",
        "name_sentence_case": "compound_name_sentence_case1",
        "definition": "compound_definition1",
        "external_id": None,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/compounds", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == "Compound with Name 'compound_name1' already exists."


def test_post_name_sentence_case_already_exists(api_client):
    data = {
        "name": "compound_name1xyz",
        "name_sentence_case": "compound_name_sentence_case1",
        "definition": "compound_definition1",
        "external_id": None,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/compounds", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "Compound with Name Sentence Case 'compound_name_sentence_case1' already exists."
    )
