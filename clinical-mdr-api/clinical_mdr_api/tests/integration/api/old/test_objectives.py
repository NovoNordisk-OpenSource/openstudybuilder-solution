# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db
from pydantic import BaseModel

import clinical_mdr_api.models.syntax_templates.objective_template as ct_models
import clinical_mdr_api.services.libraries.libraries as library_service
from clinical_mdr_api.main import app
from clinical_mdr_api.services.syntax_templates.objective_templates import (
    ObjectiveTemplateService,
)
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_PARAMETERS_CYPHER,
    library_data,
    template_data,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.objectives")
    db.cypher_query(STARTUP_PARAMETERS_CYPHER)
    db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)

    library_service.create(**library_data)
    otdata = template_data.copy()
    otdata["name"] = "Test [Indication]"
    objective_template = ct_models.ObjectiveTemplateCreateInput(**otdata)
    objective_template = ObjectiveTemplateService().create(objective_template)
    if isinstance(objective_template, BaseModel):
        objective_template = objective_template.model_dump()
    ObjectiveTemplateService().approve(objective_template["uid"])

    yield

    drop_db("old.json.test.objectives")


def test_empty_list3(api_client):
    response = api_client.get("/objectives")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_adding_objective_wrong_parameter(api_client):
    data = {
        "library_name": "Test library",
        "name": "Test objective",
        "objective_template_uid": "ObjectiveTemplate_000001",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "and",
                "terms": [
                    {
                        "index": 1,
                        "type": "ActivityInstance",
                        "name": "type 2 diabetes",
                        "uid": "Indication-99991",
                    },
                    {
                        "index": 2,
                        "type": "ActivityInstance",
                        "name": "coronary heart disease",
                        "uid": "Indication-99992",
                    },
                ],
            }
        ],
    }
    response = api_client.post("/objectives", json=data)

    assert_response_status_code(response, 422)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "Parameter term Indication-99991 ('type 2 diabetes') not valid for parameter 'ActivityInstance'"
    )


def test_previewing_objective(api_client):
    data = {
        "library_name": "Test library",
        "name": "Test objective",
        "objective_template_uid": "ObjectiveTemplate_000001",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "and",
                "terms": [
                    {
                        "index": 1,
                        "type": "Indication",
                        "name": "type 2 diabetes",
                        "uid": "Indication-99991",
                    },
                    {
                        "index": 2,
                        "type": "Indication",
                        "name": "coronary heart disease",
                        "uid": "Indication-99992",
                    },
                ],
            }
        ],
    }
    response = api_client.post("/objectives/preview", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "Objective_000001"
    assert res["name"] == "Test [type 2 diabetes and coronary heart disease]"
    assert res["name_plain"] == "Test type 2 diabetes and coronary heart disease"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["study_count"] == 0
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["template"] == {
        "name": "Test [Indication]",
        "name_plain": "Test [Indication]",
        "guidance_text": None,
        "uid": "ObjectiveTemplate_000001",
        "sequence_id": "O1",
        "library_name": "Test library",
    }
    assert res["parameter_terms"] == [
        {
            "position": 1,
            "conjunction": "and",
            "terms": [
                {
                    "index": 1,
                    "type": "Indication",
                    "name": "type 2 diabetes",
                    "uid": "Indication-99991",
                },
                {
                    "index": 2,
                    "type": "Indication",
                    "name": "coronary heart disease",
                    "uid": "Indication-99992",
                },
            ],
        }
    ]
    assert res["library"] == {"name": "Test library", "is_editable": True}


def test_adding_objective(api_client):
    data = {
        "library_name": "Test library",
        "name": "Test objective",
        "objective_template_uid": "ObjectiveTemplate_000001",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "and",
                "terms": [
                    {
                        "index": 1,
                        "type": "Indication",
                        "name": "type 2 diabetes",
                        "uid": "Indication-99991",
                    },
                    {
                        "index": 2,
                        "type": "Indication",
                        "name": "coronary heart disease",
                        "uid": "Indication-99992",
                    },
                ],
            }
        ],
    }
    response = api_client.post("/objectives", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Objective_000002"
    assert res["name"] == "Test [type 2 diabetes and coronary heart disease]"
    assert res["name_plain"] == "Test type 2 diabetes and coronary heart disease"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["study_count"] == 0
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["template"] == {
        "name": "Test [Indication]",
        "name_plain": "Test [Indication]",
        "guidance_text": None,
        "uid": "ObjectiveTemplate_000001",
        "sequence_id": "O1",
        "library_name": "Test library",
    }
    assert res["parameter_terms"] == [
        {
            "position": 1,
            "conjunction": "and",
            "terms": [
                {
                    "index": 1,
                    "type": "Indication",
                    "name": "type 2 diabetes",
                    "uid": "Indication-99991",
                },
                {
                    "index": 2,
                    "type": "Indication",
                    "name": "coronary heart disease",
                    "uid": "Indication-99992",
                },
            ],
        }
    ]
    assert res["library"] == {"name": "Test library", "is_editable": True}


def test_adding_the_same_objective_name(api_client):
    data = {
        "library_name": "Test library",
        "name": "Test objective",
        "objective_template_uid": "ObjectiveTemplate_000001",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "and",
                "terms": [
                    {
                        "index": 1,
                        "type": "Indication",
                        "name": "type 2 diabetes",
                        "uid": "Indication-99991",
                    },
                    {
                        "index": 2,
                        "type": "Indication",
                        "name": "coronary heart disease",
                        "uid": "Indication-99992",
                    },
                ],
            }
        ],
    }
    response = api_client.post("/objectives", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "Resource with Name 'Test [type 2 diabetes and coronary heart disease]' already exists."
    )


def test_list_studies1(api_client):
    response = api_client.get("/objectives/Objective_000001/studies/")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == []


def test_delete2(api_client):
    response = api_client.delete("/objectives/Objective_000002")

    assert_response_status_code(response, 204)
