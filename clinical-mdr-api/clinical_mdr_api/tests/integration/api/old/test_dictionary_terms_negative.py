# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_DICTIONARY_CODELISTS_CYPHER,
    STARTUP_DICTIONARY_TERMS_CYPHER,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.dictionary.terms.negative")
    db.cypher_query(STARTUP_DICTIONARY_CODELISTS_CYPHER)
    db.cypher_query(STARTUP_DICTIONARY_TERMS_CYPHER)

    yield

    drop_db("old.json.test.dictionary.terms.negative")


def test_patch_non_matching_sentence_case(api_client):
    data = {
        "name": "new sentence case name",
        "definition": "definition",
        "change_description": "Changing codelist",
    }
    response = api_client.patch("/dictionaries/terms/term_root1_uid", json=data)

    assert_response_status_code(response, 422)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "Name1 isn't an independent case version of new sentence case name"
    )


def test_patch_non_draft_term(api_client):
    data = {"definition": "definition", "change_description": "Changing codelist"}
    response = api_client.patch("/dictionaries/terms/term_root1_uid", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."


def test_patch_term_name_already_exists(api_client):
    data = {
        "name": "name1",
        "name_sentence_case": "Name1",
        "definition": "definition",
        "change_description": "Changing term",
    }
    response = api_client.patch("/dictionaries/terms/term_root4_uid", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "Dictionary Term with Name 'name1' already exists in Dictionary Codelist with UID 'codelist_root1_uid'."
    )


def test_post_approve_non_draft_term(api_client):
    response = api_client.post("/dictionaries/terms/term_root1_uid/approvals")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."


def test_delete_activations_non_final_term(api_client):
    response = api_client.delete("/dictionaries/terms/term_root2_uid/activations")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Cannot retire draft version."


def test_post_activations_non_retired_term(api_client):
    response = api_client.post("/dictionaries/terms/term_root2_uid/activations")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Only RETIRED version can be reactivated."


def test_delete_accepted_object4(api_client):
    response = api_client.delete("/dictionaries/terms/term_root1_uid")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Object has been accepted"
