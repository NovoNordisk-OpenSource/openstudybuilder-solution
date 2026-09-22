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
    inject_and_clear_db("old.json.test.dictionary.codelists")
    db.cypher_query(STARTUP_DICTIONARY_CODELISTS_CYPHER)
    db.cypher_query(STARTUP_DICTIONARY_TERMS_CYPHER)

    yield

    drop_db("old.json.test.dictionary.codelists")


def test_get_dictionary_codelists(api_client):
    response = api_client.get("/dictionaries/codelists?library_name=SNOMED")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["codelist_uid"] == "codelist_root1_uid"
    assert res["items"][0]["name"] == "name1"
    assert res["items"][0]["template_parameter"] is True
    assert res["items"][0]["library_name"] == "SNOMED"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] == "Final"
    assert res["items"][0]["version"] == "1.0"
    assert res["items"][0]["change_description"] == "Approved version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["possible_actions"] == ["new_version"]
    assert res["items"][1]["codelist_uid"] == "codelist_root2_uid"
    assert res["items"][1]["name"] == "name2"
    assert res["items"][1]["template_parameter"] is False
    assert res["items"][1]["library_name"] == "SNOMED"
    assert res["items"][1]["end_date"] is None
    assert res["items"][1]["status"] == "Draft"
    assert res["items"][1]["version"] == "0.1"
    assert res["items"][1]["change_description"] == "New draft version"
    assert res["items"][1]["author_username"] == "unknown-user@example.com"
    assert res["items"][1]["possible_actions"] == ["approve", "edit"]


def test_post_versions_codelist3(api_client):
    response = api_client.post("/dictionaries/codelists/codelist_root1_uid/versions")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["codelist_uid"] == "codelist_root1_uid"
    assert res["name"] == "name1"
    assert res["template_parameter"] is True
    assert res["library_name"] == "SNOMED"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["change_description"] == "New draft created"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "edit"]


def test_patch_draft_codelist_that_is_tp1(api_client):
    data = {
        "name": "codelist new name",
        "template_parameter": True,
        "change_description": "changing codelist name",
    }
    response = api_client.patch("/dictionaries/codelists/codelist_root1_uid", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["codelist_uid"] == "codelist_root1_uid"
    assert res["name"] == "codelist new name"
    assert res["template_parameter"] is True
    assert res["library_name"] == "SNOMED"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.2"
    assert res["change_description"] == "changing codelist name"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "edit"]


def test_patch_draft_codelist_that_is_not_tp2(api_client):
    data = {
        "name": "codelist patched name",
        "template_parameter": True,
        "change_description": "changing codelist name",
    }
    response = api_client.patch("/dictionaries/codelists/codelist_root2_uid", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["codelist_uid"] == "codelist_root2_uid"
    assert res["name"] == "codelist patched name"
    assert res["template_parameter"] is True
    assert res["library_name"] == "SNOMED"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["change_description"] == "changing codelist name"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "edit"]


def test_post_approve_codelist1(api_client):
    response = api_client.post("/dictionaries/codelists/codelist_root2_uid/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["codelist_uid"] == "codelist_root2_uid"
    assert res["name"] == "codelist patched name"
    assert res["template_parameter"] is True
    assert res["library_name"] == "SNOMED"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["new_version"]


def test_post_approve_codelist2(api_client):
    response = api_client.post("/dictionaries/codelists/codelist_root1_uid/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["codelist_uid"] == "codelist_root1_uid"
    assert res["name"] == "codelist new name"
    assert res["template_parameter"] is True
    assert res["library_name"] == "SNOMED"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "2.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["new_version"]


def test_post_add_term_that_is_not_assigned_to_given_codelist_yet(api_client):
    data = {"term_uid": "term_root3_uid"}
    response = api_client.post(
        "/dictionaries/codelists/codelist_root1_uid/terms", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["codelist_uid"] == "codelist_root1_uid"
    assert res["name"] == "codelist new name"
    assert res["template_parameter"] is True
    assert res["library_name"] == "SNOMED"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "2.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["new_version"]


def test_delete_remove_term_that_is_assigned_to_given_codelist(api_client):
    response = api_client.delete(
        "dictionaries/codelists/codelist_root1_uid/terms/term_root3_uid"
    )
    assert_response_status_code(response, 200)

    res = response.json()

    assert res["codelist_uid"] == "codelist_root1_uid"
    assert res["name"] == "codelist new name"
    assert res["template_parameter"] is True
    assert res["library_name"] == "SNOMED"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "2.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["new_version"]


def test_post_add_term_that_is_was_assigned_and_then_deleted(api_client):
    data = {"term_uid": "term_root3_uid"}
    response = api_client.post(
        "/dictionaries/codelists/codelist_root1_uid/terms", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["codelist_uid"] == "codelist_root1_uid"
    assert res["name"] == "codelist new name"
    assert res["template_parameter"] is True
    assert res["library_name"] == "SNOMED"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "2.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["new_version"]
