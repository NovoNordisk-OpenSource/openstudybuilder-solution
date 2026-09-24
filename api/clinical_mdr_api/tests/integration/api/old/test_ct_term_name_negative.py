# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM_NAME_CYPHER,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.ct.term.name.negative")
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)

    yield

    drop_db("old.json.test.ct.term.name.negative")


def test_get_all_terms_from_non_existent_codelist1(api_client):
    response = api_client.get("/ct/terms/names?codelist_uid=non_existent_codelist")

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"] == "CT Codelist with UID 'non_existent_codelist' doesn't exist."
    )


def test_patch_term_name_non_draft_term(api_client):
    data = {
        "sponsor_preferred_name": "Sponsor_preferred_name",
        "sponsor_preferred_name_sentence_case": "sponsor_preferred_name",
        "change_description": "term change",
    }
    response = api_client.patch("/ct/terms/term_root_final/names", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."


def test_patch_non_matching_sentence_case(api_client):
    data = {
        "sponsor_preferred_name": "wrong version of name",
        "definition": "definition",
        "change_description": "Changing sponsor preferred name",
    }
    response = api_client.patch("/ct/terms/term_root_draft/names", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "term_value_name_sentence_case isn't an independent case version of wrong version of name"
    )


def test_post_name_approve_non_draft_term(api_client):
    response = api_client.post("/ct/terms/term_root_final/names/approvals")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."


def test_delete_name_activations_non_final_term(api_client):
    response = api_client.delete("/ct/terms/term_root_draft/names/activations")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Cannot retire draft version."


def test_delete_name_delete_accepted_term(api_client):
    response = api_client.delete("/ct/terms/term_root_final/names")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Object has been accepted"


def test_patch_name_terms_name_already_exists(api_client):
    data = {
        "sponsor_preferred_name": "term_value_name1",
        "sponsor_preferred_name_sentence_case": "term_value_name1",
        "order": 1,
        "change_description": "changed",
    }
    response = api_client.patch("/ct/terms/term_root_draft/names", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == "CT Term Name with Name 'term_value_name1' already exists."
