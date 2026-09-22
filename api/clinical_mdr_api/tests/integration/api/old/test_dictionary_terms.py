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
    inject_and_clear_db("old.json.test.dictionary.terms")
    db.cypher_query(STARTUP_DICTIONARY_CODELISTS_CYPHER)
    db.cypher_query(STARTUP_DICTIONARY_TERMS_CYPHER)

    yield

    drop_db("old.json.test.dictionary.terms")


def test_post_create_dictionary_term(api_client):
    data = {
        "dictionary_id": "dictionary_id5",
        "name": "name5",
        "name_sentence_case": "Name5",
        "abbreviation": "abbreviation5",
        "definition": "definition5",
        "codelist_uid": "codelist_root1_uid",
        "library_name": "SNOMED",
    }
    response = api_client.post("/dictionaries/terms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "DictionaryTerm_000001"
    assert res["dictionary_id"] == "dictionary_id5"
    assert res["name"] == "name5"
    assert res["name_sentence_case"] == "Name5"
    assert res["abbreviation"] == "abbreviation5"
    assert res["definition"] == "definition5"
    assert res["library_name"] == "SNOMED"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_get_all_dictionaries_terms_from_given_codelist(api_client):
    sort_by = '{"term_uid": true}'
    response = api_client.get(
        f"/dictionaries/terms?codelist_uid=codelist_root1_uid&total_count=true&sort_by={sort_by}"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["term_uid"] == "DictionaryTerm_000001"
    assert res["items"][0]["dictionary_id"] == "dictionary_id5"
    assert res["items"][0]["name"] == "name5"
    assert res["items"][0]["name_sentence_case"] == "Name5"
    assert res["items"][0]["abbreviation"] == "abbreviation5"
    assert res["items"][0]["definition"] == "definition5"
    assert res["items"][0]["library_name"] == "SNOMED"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] == "Draft"
    assert res["items"][0]["version"] == "0.1"
    assert res["items"][0]["change_description"] == "Initial version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["possible_actions"] == ["approve", "delete", "edit"]

    assert res["items"][1]["term_uid"] == "term_root1_uid"
    assert res["items"][1]["dictionary_id"] == "dictionary_id1"
    assert res["items"][1]["name"] == "name1"
    assert res["items"][1]["name_sentence_case"] == "Name1"
    assert res["items"][1]["abbreviation"] == "abbreviation1"
    assert res["items"][1]["definition"] == "definition1"
    assert res["items"][1]["library_name"] == "SNOMED"
    assert res["items"][1]["end_date"] is None
    assert res["items"][1]["status"] == "Final"
    assert res["items"][1]["version"] == "1.0"
    assert res["items"][1]["change_description"] == "Approved version"
    assert res["items"][1]["author_username"] == "unknown-user@example.com"
    assert res["items"][1]["possible_actions"] == ["inactivate", "new_version"]

    assert res["items"][2]["term_uid"] == "term_root4_uid"
    assert res["items"][2]["dictionary_id"] == "dictionary_id4"
    assert res["items"][2]["name"] == "name4"
    assert res["items"][2]["name_sentence_case"] == "Name4"
    assert res["items"][2]["abbreviation"] == "abbreviation4"
    assert res["items"][2]["definition"] == "definition4"
    assert res["items"][2]["library_name"] == "SNOMED"
    assert res["items"][2]["end_date"] is None
    assert res["items"][2]["status"] == "Final"
    assert res["items"][2]["version"] == "1.0"
    assert res["items"][2]["change_description"] == "Approved version"
    assert res["items"][2]["author_username"] == "unknown-user@example.com"
    assert res["items"][2]["possible_actions"] == ["inactivate", "new_version"]


def test_post_versions_term(api_client):
    response = api_client.post("/dictionaries/terms/term_root1_uid/versions")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "term_root1_uid"
    assert res["dictionary_id"] == "dictionary_id1"
    assert res["name"] == "name1"
    assert res["name_sentence_case"] == "Name1"
    assert res["abbreviation"] == "abbreviation1"
    assert res["definition"] == "definition1"
    assert res["library_name"] == "SNOMED"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["change_description"] == "New draft created"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "edit"]


def test_patch_draft_term(api_client):
    data = {
        "name": "term new name",
        "name_sentence_case": "Term new name",
        "definition": "new_definition",
        "change_description": "term patch",
    }
    response = api_client.patch("/dictionaries/terms/term_root1_uid", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root1_uid"
    assert res["dictionary_id"] == "dictionary_id1"
    assert res["name"] == "term new name"
    assert res["name_sentence_case"] == "Term new name"
    assert res["abbreviation"] == "abbreviation1"
    assert res["definition"] == "new_definition"
    assert res["library_name"] == "SNOMED"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.2"
    assert res["change_description"] == "term patch"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "edit"]


def test_post_approve_term(api_client):
    response = api_client.post("/dictionaries/terms/term_root2_uid/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "term_root2_uid"
    assert res["dictionary_id"] == "dictionary_id2"
    assert res["name"] == "name2"
    assert res["name_sentence_case"] == "Name2"
    assert res["abbreviation"] == "abbreviation2"
    assert res["definition"] == "definition2"
    assert res["library_name"] == "SNOMED"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_delete_activations_term(api_client):
    response = api_client.delete("/dictionaries/terms/term_root2_uid/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root2_uid"
    assert res["dictionary_id"] == "dictionary_id2"
    assert res["name"] == "name2"
    assert res["name_sentence_case"] == "Name2"
    assert res["abbreviation"] == "abbreviation2"
    assert res["definition"] == "definition2"
    assert res["library_name"] == "SNOMED"
    assert res["end_date"] is None
    assert res["status"] == "Retired"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Inactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["reactivate"]


def test_post_activations_term(api_client):
    response = api_client.post("/dictionaries/terms/term_root2_uid/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root2_uid"
    assert res["dictionary_id"] == "dictionary_id2"
    assert res["name"] == "name2"
    assert res["name_sentence_case"] == "Name2"
    assert res["abbreviation"] == "abbreviation2"
    assert res["definition"] == "definition2"
    assert res["library_name"] == "SNOMED"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_delete_term(api_client):
    response = api_client.delete("/dictionaries/terms/term_root5_uid")

    assert_response_status_code(response, 204)
