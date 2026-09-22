# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

import clinical_mdr_api.models.syntax_templates.objective_template as ct_models
import clinical_mdr_api.services.libraries.libraries as library_service
from clinical_mdr_api.main import app
from clinical_mdr_api.services.syntax_templates.objective_templates import (
    ObjectiveTemplateService,
)
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import template_data
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.objective.negative")

    library_service.create(name="Test library", is_editable=True)
    otdata = template_data.copy()
    objective_template = ct_models.ObjectiveTemplateCreateInput(**otdata)
    objective_template = ObjectiveTemplateService().create(objective_template)
    if isinstance(objective_template, BaseModel):
        objective_template = objective_template.model_dump()
    ObjectiveTemplateService().approve(objective_template["uid"])
    otdt = template_data.copy()
    otdt["name"] = "Name not approved"
    objective_template = ct_models.ObjectiveTemplateCreateInput(**otdt)
    not_approved_ot = ObjectiveTemplateService().create(objective_template)
    if isinstance(not_approved_ot, BaseModel):
        not_approved_ot = not_approved_ot.model_dump()

    yield

    drop_db("old.json.test.objective.negative")


def test_random_test_name_30(api_client):
    data = {
        "library_name": "non-existent library",
        "name": "Test objective",
        "objective_template_uid": "ObjectiveTemplate_000001",
        "parameter_terms": [],
    }
    response = api_client.post("/objectives", json=data)

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert res["message"] == "Library with Name 'non-existent library' doesn't exist."


def test_random_test_name_31(api_client):
    data = {
        "library_name": "Test library",
        "name": "Test objective",
        "objective_template_uid": "wrong-uid",
        "parameter_terms": [],
    }
    response = api_client.post("/objectives", json=data)

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "No ObjectiveTemplateRoot with UID 'wrong-uid' found in given status, date and version."
    )


def test_random_test_name_14(api_client):
    data = {
        "library_name": "Test library",
        "name": "Test objective",
        "objective_template_uid": "not_approved_ot",
        "parameter_terms": [],
    }
    response = api_client.post("/objectives", json=data)

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "No ObjectiveTemplateRoot with UID 'not_approved_ot' found in given status, date and version."
    )
