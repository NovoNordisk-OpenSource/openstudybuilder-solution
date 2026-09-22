# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

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
    inject_and_clear_db("old.json.test.ct.codelist.name.negative")
    db.cypher_query(STARTUP_CT_CODELISTS_NAME_CYPHER)

    yield

    drop_db("old.json.test.ct.codelist.name.negative")


def test_get_all_codelists_from_non_existent_catalogue1(api_client):
    response = api_client.get("/ct/codelists/names?catalogue_name=SDTM%20CTM")

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert res["message"] == "Catalogue with Name 'SDTM CTM' doesn't exist."


def test_patch_non_draft_codelist1(api_client):
    data = {
        "name": "codelist name",
        "template_parameter": True,
        "change_description": "Changing codelist",
    }
    response = api_client.patch("/ct/codelists/ct_codelist_root1/names", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."


def test_patch_codelist_name_already_exists1(api_client):
    data = {
        "name": "not_tp_codelist_name_value",
        "template_parameter": True,
        "change_description": "Changing codelist",
    }
    response = api_client.patch("/ct/codelists/ct_codelist_root3/names", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "CT Codelist Name with Name 'not_tp_codelist_name_value' already exists."
    )


def test_post_approve_non_draft_codelist1(api_client):
    response = api_client.post("/ct/codelists/ct_codelist_root1/names/approvals")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."
