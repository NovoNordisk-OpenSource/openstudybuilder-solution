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
    inject_and_clear_db("old.json.test.dictionary.codelists.negative")
    db.cypher_query(STARTUP_DICTIONARY_CODELISTS_CYPHER)
    db.cypher_query(STARTUP_DICTIONARY_TERMS_CYPHER)

    yield

    drop_db("old.json.test.dictionary.codelists.negative")


def test_patch_non_draft_codelist2(api_client):
    data = {
        "name": "codelist name",
        "template_parameter": True,
        "change_description": "Changing codelist",
    }
    response = api_client.patch("/dictionaries/codelists/codelist_root1_uid", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."


def test_patch_codelist_name_already_exists2(api_client):
    data = {
        "name": "name1",
        "template_parameter": True,
        "change_description": "Changing codelist",
    }
    response = api_client.patch("/dictionaries/codelists/codelist_root2_uid", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == "Dictionary Codelist with Name 'name1' already exists."


def test_post_approve_non_draft_codelist2(api_client):
    response = api_client.post("/dictionaries/codelists/codelist_root1_uid/approvals")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."


def test_post_add_term_that_already_is_added_to_given_codelist(api_client):
    data = {"term_uid": "term_root1_uid"}
    response = api_client.post(
        "/dictionaries/codelists/codelist_root1_uid/terms", json=data
    )

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "Codelist with UID 'codelist_root1_uid' already has a Term with UID 'term_root1_uid'."
    )


def test_delete_remove_term_that_is_not_assigned_to_given_codelist(api_client):
    response = api_client.delete(
        "/dictionaries/codelists/codelist_root1_uid/terms/term_root3_uid"
    )
    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Codelist with UID 'codelist_root1_uid' doesn't have a Term with UID 'term_root3_uid'."
    )
