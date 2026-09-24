# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM_ATTRIBUTES_CYPHER,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.ct.term.attributes")
    db.cypher_query(STARTUP_CT_TERM_ATTRIBUTES_CYPHER)

    yield

    drop_db("old.json.test.ct.term.attributes")


def test_post_create_term(api_client):
    data = {
        "catalogue_names": ["SDTM CT"],
        "nci_preferred_name": "nci_preferred_name",
        "definition": "definition",
        "sponsor_preferred_name": "string",
        "sponsor_preferred_name_sentence_case": "string",
        "library_name": "Sponsor",
        "codelists": [
            {
                "codelist_uid": "editable_cr",
                "order": 7,
                "submission_value": "term_submission_value",
            }
        ],
    }
    response = api_client.post("/ct/terms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()
    term_uid = res["term_uid"]

    assert res["term_uid"] == term_uid
    assert res["catalogue_names"] == ["SDTM CT"]
    assert res["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["codelists"][0]["codelist_name"] == "Objective Level"
    assert (
        res["codelists"][0]["codelist_submission_value"] == "codelist submission value1"
    )
    assert res["codelists"][0]["codelist_concept_id"] == "editable_cr"
    assert res["codelists"][0]["submission_value"] == "term_submission_value"
    assert res["codelists"][0]["order"] == 7
    assert res["codelists"][0]["library_name"] == "Sponsor"
    assert res["codelists"][0]["start_date"] is not None
    assert res["concept_id"] is None
    assert res["nci_preferred_name"] == "nci_preferred_name"
    assert res["definition"] == "definition"
    assert res["sponsor_preferred_name"] == "string"
    assert res["sponsor_preferred_name_sentence_case"] == "string"
    assert res["library_name"] == "Sponsor"
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_patch_term_attributes_draft_term(api_client):
    data = {
        "nci_preferred_name": "nci_preferred_name",
        "definition": "definitionPATCHED",
        "change_description": "change_description",
    }
    response = api_client.patch("/ct/terms/term_root_draft/attributes", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_names"] == ["SDTM CT"]
    assert res["concept_id"] is None
    assert res["nci_preferred_name"] == "nci_preferred_name"
    assert res["definition"] == "definitionPATCHED"
    assert res["change_description"] == "change_description"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_post_attributes_approve_term(api_client):
    response = api_client.post("/ct/terms/term_root_draft/attributes/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_names"] == ["SDTM CT"]
    assert res["concept_id"] is None
    assert res["nci_preferred_name"] == "nci_preferred_name"
    assert res["definition"] == "definitionPATCHED"
    assert res["change_description"] == "Approved version"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_delete_attributes_activations_term(api_client):
    response = api_client.delete("/ct/terms/term_root_draft/attributes/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_names"] == ["SDTM CT"]
    assert res["concept_id"] is None
    assert res["nci_preferred_name"] == "nci_preferred_name"
    assert res["definition"] == "definitionPATCHED"
    assert res["change_description"] == "Inactivated version"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Retired"
    assert res["version"] == "1.0"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["reactivate"]


def test_post_attributes_reactivate_term(api_client):
    response = api_client.post("/ct/terms/term_root_draft/attributes/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_names"] == ["SDTM CT"]
    assert res["concept_id"] is None
    assert res["nci_preferred_name"] == "nci_preferred_name"
    assert res["definition"] == "definitionPATCHED"
    assert res["change_description"] == "Reactivated version"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_post_attributes_versions_term(api_client):
    response = api_client.post("/ct/terms/term_root_draft/attributes/versions")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_names"] == ["SDTM CT"]
    assert res["concept_id"] is None
    assert res["nci_preferred_name"] == "nci_preferred_name"
    assert res["definition"] == "definitionPATCHED"
    assert res["change_description"] == "New draft created"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "edit"]


def test_add_term_node_parent(api_client):
    response = api_client.post(
        "/ct/terms/term_root_final/parents?parent_uid=term_root_final&relationship_type=type"
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "term_root_final"
    assert res["catalogue_names"] == ["SDTM CT"]
    assert len(res["codelists"]) == 1
    assert res["concept_id"] == "concept_id1"
    assert res["nci_preferred_name"] == "preferred_term1"
    assert res["definition"] == "definition"
    assert res["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["sponsor_preferred_name_sentence_case"] == "term_value_name_sentence_case"
    )
    assert res["library_name"] == "Sponsor"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_remove_term_node_parent(api_client):
    response = api_client.delete(
        "/ct/terms/term_root_final/parents?parent_uid=term_root_final&relationship_type=type"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root_final"
    assert res["catalogue_names"] == ["SDTM CT"]
    assert len(res["codelists"]) == 1
    assert res["concept_id"] == "concept_id1"
    assert res["nci_preferred_name"] == "preferred_term1"
    assert res["definition"] == "definition"
    assert res["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["sponsor_preferred_name_sentence_case"] == "term_value_name_sentence_case"
    )
    assert res["library_name"] == "Sponsor"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_add_term_node_parent_after_deleting(api_client):
    response = api_client.post(
        "/ct/terms/term_root_final/parents?parent_uid=term_root_final&relationship_type=type"
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "term_root_final"
    assert res["catalogue_names"] == ["SDTM CT"]
    assert len(res["codelists"]) == 1
    assert res["concept_id"] == "concept_id1"
    assert res["nci_preferred_name"] == "preferred_term1"
    assert res["definition"] == "definition"
    assert res["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["sponsor_preferred_name_sentence_case"] == "term_value_name_sentence_case"
    )
    assert res["library_name"] == "Sponsor"
    assert res["possible_actions"] == ["inactivate", "new_version"]
