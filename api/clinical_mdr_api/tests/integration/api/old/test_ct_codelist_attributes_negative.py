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
    STARTUP_CT_CODELISTS_ATTRIBUTES_CYPHER,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.ct.codelist.attributes.negative")
    db.cypher_query(STARTUP_CT_CODELISTS_ATTRIBUTES_CYPHER)

    yield

    drop_db("old.json.test.ct.codelist.attributes.negative")


def test_post_create_codelist_non_editable_library(api_client):
    data = {
        "catalogue_names": ["SDTM CT"],
        "name": "name",
        "submission_value": "Submission value",
        "nci_preferred_name": "Nci preferred name",
        "definition": "definition",
        "extensible": True,
        "is_ordinal": False,
        "sponsor_preferred_name": "Sponsor preferred name",
        "template_parameter": True,
        "library_name": "CDISC",
        "terms": [],
    }
    response = api_client.post("/ct/codelists", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"] == "Library with Name 'CDISC' doesn't allow creation of objects."
    )


def test_get_all_codelists_from_non_existent_catalogue(api_client):
    response = api_client.get("/ct/codelists/attributes?catalogue_name=SDTM%20CTM")

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert res["message"] == "Catalogue with Name 'SDTM CTM' doesn't exist."


def test_patch_non_draft_codelist(api_client):
    data = {
        "name": "codelist new name",
        "submission_value": "new codelist submission value",
        "nci_preferred_name": "new codelist preferred term",
        "definition": "new codelist definition",
        "extensible": True,
        "change_description": "changing codelist name",
    }
    response = api_client.patch("/ct/codelists/ct_codelist_root1/attributes", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."


def test_patch_codelist_in_non_editable_library(api_client):
    data = {
        "name": "codelist new name",
        "submission_value": "new codelist submission value",
        "nci_preferred_name": "new codelist preferred term",
        "definition": "new codelist definition",
        "extensible": True,
        "change_description": "changing codelist name",
    }
    response = api_client.patch("/ct/codelists/ct_codelist_root2/attributes", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Library isn't editable."


def test_patch_codelist_name_already_exists(api_client):
    data = {
        "name": "codelist attributes value1",
        "submission_value": "new codelist submission value",
        "nci_preferred_name": "new codelist preferred term",
        "definition": "new codelist definition",
        "extensible": True,
        "change_description": "changing codelist name",
    }
    response = api_client.patch("/ct/codelists/ct_codelist_root3/attributes", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "CT Codelist Attributes with Name 'codelist attributes value1' already exists."
    )


def test_patch_codelist_submission_value_already_exists(api_client):
    data = {
        "name": "new codelist name",
        "submission_value": "codelist submission value1",
        "nci_preferred_name": "new codelist preferred term",
        "definition": "new codelist definition",
        "extensible": True,
        "change_description": "changing codelist name",
    }
    response = api_client.patch("/ct/codelists/ct_codelist_root3/attributes", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "CT Codelist Attributes with Submission Value 'codelist submission value1' already exists."
    )


def test_post_versions_non_editable_library(api_client):
    response = api_client.post("/ct/codelists/ct_codelist_root2/attributes/versions")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Library isn't editable."


def test_post_approve_non_draft_codelist(api_client):
    response = api_client.post("/ct/codelists/ct_codelist_root1/attributes/approvals")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."


def test_post_approve_non_editable_library(api_client):
    response = api_client.post("/ct/codelists/ct_codelist_root2/attributes/approvals")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Library isn't editable."


def test_post_create_codelist_with_parent_codelist1(api_client):
    data = {
        "catalogue_names": ["SDTM CT"],
        "name": "name with parent",
        "parent_codelist_uid": "ct_codelist_root3",
        "submission_value": "Submission value with parent",
        "nci_preferred_name": "Nci preferred name with parent",
        "definition": "definition",
        "extensible": True,
        "is_ordinal": False,
        "sponsor_preferred_name": "Sponsor preferred name with parent",
        "template_parameter": True,
        "library_name": "Sponsor",
        "terms": [],
    }
    response = api_client.post("/ct/codelists", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["catalogue_names"] == ["SDTM CT"]
    assert res["codelist_uid"] == "CTCodelist_000001"
    assert res["parent_codelist_uid"] == "ct_codelist_root3"
    assert res["child_codelist_uids"] == []
    assert res["name"] == "name with parent"
    assert res["submission_value"] == "Submission value with parent"
    assert res["nci_preferred_name"] == "Nci preferred name with parent"
    assert res["definition"] == "definition"
    assert res["extensible"] is True
    assert res["is_ordinal"] is False
    assert res["sponsor_preferred_name"] == "Sponsor preferred name with parent"
    assert res["template_parameter"] is True
    assert res["library_name"] == "Sponsor"
    assert res["possible_actions"] == ["approve", "edit"]


def test_post_add_term_to_child_codelist1(api_client):
    data = {
        "term_uid": "term1",
        "submission_value": "Submission value with parent",
        "order": 999999,
    }
    response = api_client.post("/ct/codelists/CTCodelist_000001/terms", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "Term with UID 'term1' isn't in use by Parent Codelist with UID 'ct_codelist_root3'."
    )
