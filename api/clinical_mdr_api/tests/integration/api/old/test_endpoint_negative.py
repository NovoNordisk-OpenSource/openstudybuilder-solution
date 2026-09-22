# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

import clinical_mdr_api.models.syntax_templates.endpoint_template as ep_models
import clinical_mdr_api.services.libraries.libraries as library_service
from clinical_mdr_api.main import app
from clinical_mdr_api.services.syntax_templates.endpoint_templates import (
    EndpointTemplateService,
)
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_PARAMETERS_CYPHER,
    template_data,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.endpoint.negative")
    db.cypher_query(STARTUP_PARAMETERS_CYPHER)

    library_service.create(name="Test library", is_editable=True)
    etdata = template_data.copy()
    endpoint_template = EndpointTemplateService().create(
        ep_models.EndpointTemplateCreateInput(**etdata)
    )
    assert isinstance(endpoint_template, ep_models.EndpointTemplate)
    EndpointTemplateService().approve(endpoint_template.uid)
    etdt = template_data.copy()
    etdt["name"] = "Name not approved"
    endpoint_template = ep_models.EndpointTemplateCreateInput(**etdt)
    not_approved_et = EndpointTemplateService().create(endpoint_template)
    assert isinstance(not_approved_et, ep_models.EndpointTemplate)

    yield

    drop_db("old.json.test.endpoint.negative")


def test_check_add_endpoint(api_client):
    data = {
        "endpoint_template_uid": "EndpointTemplate_000001",
        "library_name": "non-existent library",
        "name": "Test objective",
        "parameter_terms": [],
    }
    response = api_client.post("/endpoints", json=data)

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert res["message"] == "Library with Name 'non-existent library' doesn't exist."


def test_check_missing_endpoint_temlpate(api_client):
    data = {
        "endpoint_template_uid": "wrong-uid",
        "library_name": "Test library",
        "name": "Test objective",
        "parameter_terms": [],
    }
    response = api_client.post("/endpoints", json=data)

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "No EndpointTemplateRoot with UID 'wrong-uid' found in given status, date and version."
    )


def test_check_endpoint_template_not_in_final_version(api_client):
    data = {
        "endpoint_template_uid": "wrong_uid",
        "library_name": "Test library",
        "name": "Test objective",
        "parameter_terms": [],
    }
    response = api_client.post("/endpoints", json=data)

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "No EndpointTemplateRoot with UID 'wrong_uid' found in given status, date and version."
    )
