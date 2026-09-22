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
    inject_and_clear_db("old.json.test.dictionary.terms.substances.negative")
    db.cypher_query(STARTUP_DICTIONARY_CODELISTS_CYPHER)
    db.cypher_query(STARTUP_DICTIONARY_TERMS_CYPHER)

    yield

    drop_db("old.json.test.dictionary.terms.substances.negative")


def test_post_create_med_rt_dictionary_term_pharmacological_class1(api_client):
    data = {
        "dictionary_id": "dictionary_id_pharma_class",
        "name": "name_pharma_class",
        "name_sentence_case": "name_pharma_class",
        "abbreviation": "abbreviation_pharma_class",
        "definition": "definition_pharma_class",
        "codelist_uid": "codelist_pclass_uid",
        "library_name": "MED-RT",
    }
    response = api_client.post("/dictionaries/terms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "DictionaryTerm_000001"
    assert res["dictionary_id"] == "dictionary_id_pharma_class"
    assert res["name"] == "name_pharma_class"
    assert res["name_sentence_case"] == "name_pharma_class"
    assert res["abbreviation"] == "abbreviation_pharma_class"
    assert res["definition"] == "definition_pharma_class"
    assert res["library_name"] == "MED-RT"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_post_create_substance_dictionary_term1(api_client):
    data = {
        "dictionary_id": "dictionary_id_substance",
        "name": "name_substance",
        "name_sentence_case": "name_substance",
        "abbreviation": "abbreviation_substance",
        "definition": "definition_substance",
        "codelist_uid": "codelist_unii_uid",
        "library_name": "UNII",
        "pclass_uid": "DictionaryTerm_000001",
    }
    response = api_client.post("/dictionaries/substances", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "DictionaryTerm_000002"
    assert res["dictionary_id"] == "dictionary_id_substance"
    assert res["name"] == "name_substance"
    assert res["name_sentence_case"] == "name_substance"
    assert res["abbreviation"] == "abbreviation_substance"
    assert res["definition"] == "definition_substance"
    assert res["library_name"] == "UNII"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["pclass"] == {
        "term_uid": "DictionaryTerm_000001",
        "name": "name_pharma_class",
        "dictionary_id": "dictionary_id_pharma_class",
    }


def test_post_create_substance_dictionary_term_with_name_name_substance3(api_client):
    data = {
        "dictionary_id": "dictionary_id_substance",
        "name": "name_substance3",
        "name_sentence_case": "name_substance3",
        "abbreviation": "abbreviation_substance",
        "definition": "definition_substance",
        "codelist_uid": "codelist_unii_uid",
        "library_name": "UNII",
        "pclass_uid": "DictionaryTerm_000001",
    }
    response = api_client.post("/dictionaries/substances", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "DictionaryTerm_000003"
    assert res["dictionary_id"] == "dictionary_id_substance"
    assert res["name"] == "name_substance3"
    assert res["name_sentence_case"] == "name_substance3"
    assert res["abbreviation"] == "abbreviation_substance"
    assert res["definition"] == "definition_substance"
    assert res["library_name"] == "UNII"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["pclass"] == {
        "term_uid": "DictionaryTerm_000001",
        "name": "name_pharma_class",
        "dictionary_id": "dictionary_id_pharma_class",
    }


def test_post_approve_substance_term_with_name_name_substance3(api_client):
    response = api_client.post("/dictionaries/terms/DictionaryTerm_000003/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "DictionaryTerm_000003"
    assert res["dictionary_id"] == "dictionary_id_substance"
    assert res["name"] == "name_substance3"
    assert res["name_sentence_case"] == "name_substance3"
    assert res["abbreviation"] == "abbreviation_substance"
    assert res["definition"] == "definition_substance"
    assert res["library_name"] == "UNII"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_patch_non_matching_sentence_case1(api_client):
    data = {
        "name": "new sentence case name",
        "definition": "definition",
        "change_description": "Changing codelist",
    }
    response = api_client.patch(
        "/dictionaries/substances/DictionaryTerm_000002", json=data
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "name_substance isn't an independent case version of new sentence case name"
    )


def test_patch_term_name_already_exists1(api_client):
    data = {
        "name": "name_substance3",
        "name_sentence_case": "name_substance3",
        "definition": "definition",
        "change_description": "Changing term",
    }
    response = api_client.patch(
        "/dictionaries/substances/DictionaryTerm_000002", json=data
    )

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "Dictionary Term with Name 'name_substance3' already exists in Dictionary Codelist with UID 'codelist_unii_uid'."
    )


def test_post_term_name_already_exists(api_client):
    data = {
        "dictionary_id": "dictionary_id_substance",
        "name": "name_substance3",
        "name_sentence_case": "name_substance3",
        "abbreviation": "abbreviation_substance",
        "definition": "definition_substance",
        "codelist_uid": "codelist_unii_uid",
        "library_name": "UNII",
        "pclass_uid": "DictionaryTerm_000001",
    }
    response = api_client.post("/dictionaries/substances", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "Dictionary Term with Name 'name_substance3' already exists in Dictionary Codelist with UID 'codelist_unii_uid'."
    )
