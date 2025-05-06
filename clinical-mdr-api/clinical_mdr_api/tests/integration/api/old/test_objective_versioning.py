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
from clinical_mdr_api.tests.integration.utils.data_library import (
    library_data,
    template_data,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.objective.versioning")

    library_service.create(**library_data)
    objective_template = ct_models.ObjectiveTemplateCreateInput(**template_data)
    objective_template = ObjectiveTemplateService().create(objective_template)
    if isinstance(objective_template, BaseModel):
        objective_template = objective_template.model_dump()
    ObjectiveTemplateService().approve(objective_template["uid"])

    yield

    drop_db("old.json.test.objective.versioning")


def test_if_zero_objectives(api_client):
    response = api_client.get("/objectives")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_if_adding_objective_works(api_client):
    data = {
        "library_name": "Test library",
        "name": "Test objective",
        "objective_template_uid": "ObjectiveTemplate_000001",
        "parameter_terms": [],
    }
    response = api_client.post("/objectives", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["change_description"] == "Initial version"
    assert res["end_date"] is None
    assert res["library"] == {"is_editable": True, "name": "Test library"}
    assert res["name"] == "Test_Name_Template"
    assert res["name_plain"] == "Test_Name_Template"
    assert res["template"] == {
        "name": "Test_Name_Template",
        "name_plain": "Test_Name_Template",
        "guidance_text": None,
        "uid": "ObjectiveTemplate_000001",
        "sequence_id": "O1",
        "library_name": "Test library",
    }
    assert res["parameter_terms"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["status"] == "Draft"
    assert res["study_count"] == 0
    assert res["uid"] == "Objective_000001"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["version"] == "0.1"


def test_if_approval_works1(api_client):
    response = api_client.post("/objectives/Objective_000001/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["change_description"] == "Approved version"
    assert res["end_date"] is None
    assert res["library"] == {"is_editable": True, "name": "Test library"}
    assert res["name"] == "Test_Name_Template"
    assert res["name_plain"] == "Test_Name_Template"
    assert res["template"] == {
        "name": "Test_Name_Template",
        "name_plain": "Test_Name_Template",
        "guidance_text": None,
        "uid": "ObjectiveTemplate_000001",
        "sequence_id": "O1",
        "library_name": "Test library",
    }
    assert res["parameter_terms"] == []
    assert res["possible_actions"] == ["inactivate"]
    assert res["status"] == "Final"
    assert res["study_count"] == 0
    assert res["uid"] == "Objective_000001"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["version"] == "1.0"


def test_if_second_approval_fails1(api_client):
    response = api_client.patch("/objectives/Objective_000001/approvals")

    assert_response_status_code(response, 405)

    res = response.json()

    assert res["detail"] == "Method Not Allowed"


def test_random_test_name_28(api_client):
    response = api_client.post("/objectives/Objective_000001/approvals")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."


def test_check_how_many_parameters_are_there_0(api_client):
    response = api_client.get("/objectives/Objective_000001/parameters")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == []


def test_version_display(api_client):
    response = api_client.get("/objectives/Objective_000001/versions")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["change_description"] == "Approved version"
    assert set(res[0]["changes"]) == set(
        [
            "change_description",
            "end_date",
            "possible_actions",
            "start_date",
            "status",
            "version",
        ]
    )
    assert res[0]["end_date"] is None
    assert res[0]["library"] == {"is_editable": True, "name": "Test library"}
    assert res[0]["name"] == "Test_Name_Template"
    assert res[0]["name_plain"] == "Test_Name_Template"
    assert res[0]["template"] == {
        "name": "Test_Name_Template",
        "name_plain": "Test_Name_Template",
        "guidance_text": None,
        "uid": "ObjectiveTemplate_000001",
        "sequence_id": "O1",
        "library_name": "Test library",
    }
    assert res[0]["parameter_terms"] == []
    assert res[0]["possible_actions"] == ["inactivate"]
    assert res[0]["status"] == "Final"
    assert res[0]["study_count"] == 0
    assert res[0]["uid"] == "Objective_000001"
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["version"] == "1.0"
    assert res[1]["change_description"] == "Initial version"
    assert res[1]["changes"] == []
    assert res[1]["end_date"]
    assert res[1]["library"] == {"is_editable": True, "name": "Test library"}
    assert res[1]["name"] == "Test_Name_Template"
    assert res[1]["name_plain"] == "Test_Name_Template"
    assert res[1]["template"] == {
        "name": "Test_Name_Template",
        "name_plain": "Test_Name_Template",
        "guidance_text": None,
        "uid": "ObjectiveTemplate_000001",
        "sequence_id": "O1",
        "library_name": "Test library",
    }
    assert res[1]["parameter_terms"] == []
    assert res[1]["possible_actions"] == ["approve", "delete", "edit"]
    assert res[1]["status"] == "Draft"
    assert res[1]["study_count"] == 0
    assert res[1]["uid"] == "Objective_000001"
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["version"] == "0.1"


def test_patching_aproved_objective_with_missing_field(api_client):
    data = {"name": "test{test-uid}", "parameter_terms": []}
    response = api_client.patch("/objectives/Objective_000001", json=data)

    assert_response_status_code(response, 422)

    res = response.json()

    assert res["detail"] == [
        {
            "type": "missing",
            "loc": ["body", "change_description"],
            "msg": "Field required",
            "input": {"name": "test{test-uid}", "parameter_terms": []},
        }
    ]


def test_patching_approved_objective1(api_client):
    data = {
        "change_description": "Change test",
        "name": "test{test-uid}",
        "parameter_terms": [],
    }
    response = api_client.patch("/objectives/Objective_000001", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."
