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
    STARTUP_CT_CODELISTS_NAME_CYPHER,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.ct.codelist.name")
    db.cypher_query(STARTUP_CT_CODELISTS_NAME_CYPHER)

    yield

    drop_db("old.json.test.ct.codelist.name")


def test_patch_draft_codelist_that_is_tp(api_client):
    data = {
        "name": "codelist new name",
        "template_parameter": True,
        "change_description": "changing codelist name",
    }
    response = api_client.patch("/ct/codelists/ct_codelist_root3/names", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["catalogue_names"] == ["SDTM CT"]
    assert res["codelist_uid"] == "ct_codelist_root3"
    assert res["name"] == "codelist new name"
    assert res["template_parameter"] is True
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["change_description"] == "changing codelist name"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "edit"]


def test_patch_draft_codelist_that_is_not_tp(api_client):
    data = {
        "name": "codelist new name",
        "template_parameter": False,
        "change_description": "changing codelist name",
    }
    response = api_client.patch("/ct/codelists/ct_codelist_root3/names", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["catalogue_names"] == ["SDTM CT"]
    assert res["codelist_uid"] == "ct_codelist_root3"
    assert res["name"] == "codelist new name"
    assert res["template_parameter"] is False
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.3"
    assert res["change_description"] == "changing codelist name"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "edit"]


def test_post_versions_codelist(api_client):
    response = api_client.post("/ct/codelists/ct_codelist_root1/names/versions")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["catalogue_names"] == ["SDTM CT"]
    assert res["codelist_uid"] == "ct_codelist_root1"
    assert res["name"] == "tp_codelist_name_value"
    assert res["template_parameter"] is True
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["change_description"] == "New draft created"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "edit"]


def test_post_versions_codelist1(api_client):
    response = api_client.post("/ct/codelists/ct_codelist_root3/names/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["catalogue_names"] == ["SDTM CT"]
    assert res["codelist_uid"] == "ct_codelist_root3"
    assert res["name"] == "codelist new name"
    assert res["template_parameter"] is False
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["new_version"]
