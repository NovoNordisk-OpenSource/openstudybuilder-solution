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
    STARTUP_CT_TERM_NAME_CYPHER,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.ct.term.name")
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)

    yield

    drop_db("old.json.test.ct.term.name")


def test_reorder_term(api_client):
    data = {
        "codelist_uid": "editable_cr",
        "order": 5,
        "submission_value": "submission_value_2",
    }
    response = api_client.patch("/ct/terms/term_root_draft/codelists", json=data)

    assert_response_status_code(response, 200)
    res = response.json()

    assert res["codelist_uid"] == "editable_cr"
    assert res["order"] == 5
    assert res["submission_value"] == "submission_value_2"


def test_patch_term_names_draft_term(api_client):
    data = {
        "sponsor_preferred_name": "Sponsor_Preferred_Name",
        "sponsor_preferred_name_sentence_case": "sponsor_preferred_name",
        "change_description": "Term name update",
    }
    response = api_client.patch("/ct/terms/term_root_draft/names", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_names"] == ["SDTM CT"]
    assert res["sponsor_preferred_name"] == "Sponsor_Preferred_Name"
    assert res["sponsor_preferred_name_sentence_case"] == "sponsor_preferred_name"
    assert res["change_description"] == "Term name update"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["queried_effective_date"] is None
    assert res["date_conflict"] is False
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_post_names_approve_term(api_client):
    response = api_client.post("/ct/terms/term_root_draft/names/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_names"] == ["SDTM CT"]
    assert res["sponsor_preferred_name"] == "Sponsor_Preferred_Name"
    assert res["sponsor_preferred_name_sentence_case"] == "sponsor_preferred_name"
    assert res["change_description"] == "Approved version"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["queried_effective_date"] is None
    assert res["date_conflict"] is False
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_delete_names_activations_term(api_client):
    response = api_client.delete("/ct/terms/term_root_draft/names/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_names"] == ["SDTM CT"]
    assert res["sponsor_preferred_name"] == "Sponsor_Preferred_Name"
    assert res["sponsor_preferred_name_sentence_case"] == "sponsor_preferred_name"
    assert res["change_description"] == "Inactivated version"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Retired"
    assert res["version"] == "1.0"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["queried_effective_date"] is None
    assert res["date_conflict"] is False
    assert res["possible_actions"] == ["reactivate"]


def test_post_names_reactivate_term(api_client):
    response = api_client.post("/ct/terms/term_root_draft/names/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_names"] == ["SDTM CT"]
    assert res["sponsor_preferred_name"] == "Sponsor_Preferred_Name"
    assert res["sponsor_preferred_name_sentence_case"] == "sponsor_preferred_name"
    assert res["change_description"] == "Reactivated version"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["queried_effective_date"] is None
    assert res["date_conflict"] is False
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_post_names_versions(api_client):
    response = api_client.post("/ct/terms/term_root_draft/names/versions")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_names"] == ["SDTM CT"]
    assert res["sponsor_preferred_name"] == "Sponsor_Preferred_Name"
    assert res["sponsor_preferred_name_sentence_case"] == "sponsor_preferred_name"
    assert res["change_description"] == "New draft created"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["queried_effective_date"] is None
    assert res["date_conflict"] is False
    assert res["possible_actions"] == ["approve", "edit"]
