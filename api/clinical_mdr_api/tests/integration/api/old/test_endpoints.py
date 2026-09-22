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
    library_data,
    template_data,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.endpoints")
    db.cypher_query(STARTUP_PARAMETERS_CYPHER)

    library_service.create(**library_data)
    epdata = template_data.copy()
    epdata["name"] = "Test [Indication]"
    endpoint_template = EndpointTemplateService().create(
        ep_models.EndpointTemplateCreateInput(**epdata)
    )
    assert isinstance(endpoint_template, ep_models.EndpointTemplate)
    EndpointTemplateService().approve(endpoint_template.uid)

    yield

    drop_db("old.json.test.endpoints")


def test_empty_list2(api_client):
    response = api_client.get("/endpoints")

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_adding_endpoint_wrong_parameter(api_client):
    data = {
        "endpoint_template_uid": "EndpointTemplate_000001",
        "library_name": "Test library",
        "name": "Test endpoint",
        "objective_uid": "",
        "parameter_terms": [
            {
                "conjunction": "and",
                "position": 1,
                "terms": [
                    {
                        "index": 1,
                        "name": "type 2 diabetes",
                        "type": "Indication",
                        "uid": "Indication_000001",
                    },
                    {
                        "index": 2,
                        "name": "coronary heart disease",
                        "type": "Indication",
                        "uid": "Indication-99992",
                    },
                ],
            }
        ],
    }
    response = api_client.post("/endpoints", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "One or more of the specified template parameters can not be found."
    )


def test_previewing_endpoint(api_client):
    data = {
        "endpoint_template_uid": "EndpointTemplate_000001",
        "library_name": "Test library",
        "name": "Test objective",
        "parameter_terms": [
            {
                "conjunction": "and",
                "position": 1,
                "terms": [
                    {
                        "index": 1,
                        "name": "type 2 diabetes",
                        "type": "Indication",
                        "uid": "Indication-99991",
                    }
                ],
            }
        ],
    }
    response = api_client.post("/endpoints/preview", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["change_description"] == "Initial version"
    assert res["end_date"] is None
    assert res["template"] == {
        "name": "Test [Indication]",
        "name_plain": "Test [Indication]",
        "guidance_text": None,
        "uid": "EndpointTemplate_000001",
        "sequence_id": "E1",
        "library_name": "Test library",
    }
    assert res["library"] == {"is_editable": True, "name": "Test library"}
    assert res["name"] == "Test [type 2 diabetes]"
    assert res["name_plain"] == "Test type 2 diabetes"
    assert res["parameter_terms"] == [
        {
            "conjunction": "and",
            "position": 1,
            "terms": [
                {
                    "index": 1,
                    "name": "type 2 diabetes",
                    "type": "Indication",
                    "uid": "Indication-99991",
                }
            ],
        }
    ]
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["status"] == "Draft"
    assert res["study_count"] == 0
    assert res["uid"] == "Endpoint_000001"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["version"] == "0.1"


def test_adding_endpoint(api_client):
    data = {
        "endpoint_template_uid": "EndpointTemplate_000001",
        "library_name": "Test library",
        "name": "Test objective",
        "parameter_terms": [
            {
                "conjunction": "and",
                "position": 1,
                "terms": [
                    {
                        "index": 1,
                        "name": "type 2 diabetes",
                        "type": "Indication",
                        "uid": "Indication-99991",
                    }
                ],
            }
        ],
    }
    response = api_client.post("/endpoints", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["change_description"] == "Initial version"
    assert res["end_date"] is None
    assert res["template"] == {
        "name": "Test [Indication]",
        "name_plain": "Test [Indication]",
        "guidance_text": None,
        "uid": "EndpointTemplate_000001",
        "sequence_id": "E1",
        "library_name": "Test library",
    }
    assert res["library"] == {"is_editable": True, "name": "Test library"}
    assert res["name"] == "Test [type 2 diabetes]"
    assert res["name_plain"] == "Test type 2 diabetes"
    assert res["parameter_terms"] == [
        {
            "conjunction": "and",
            "position": 1,
            "terms": [
                {
                    "index": 1,
                    "name": "type 2 diabetes",
                    "type": "Indication",
                    "uid": "Indication-99991",
                }
            ],
        }
    ]
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["status"] == "Draft"
    assert res["study_count"] == 0
    assert res["uid"] == "Endpoint_000002"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["version"] == "0.1"


def test_adding_the_same_endpoint_name(api_client):
    data = {
        "endpoint_template_uid": "EndpointTemplate_000001",
        "library_name": "Test library",
        "name": "Test objective",
        "parameter_terms": [
            {
                "conjunction": "and",
                "position": 1,
                "terms": [
                    {
                        "index": 1,
                        "name": "type 2 diabetes",
                        "type": "Indication",
                        "uid": "Indication-99991",
                    }
                ],
            }
        ],
    }
    response = api_client.post("/endpoints", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"] == "Resource with Name 'Test [type 2 diabetes]' already exists."
    )


def test_list_studies(api_client):
    response = api_client.get("/endpoints/Endpoint_000001/studies/")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == []


def test_delete1(api_client):
    response = api_client.delete("/endpoints/Endpoint_000002")

    assert_response_status_code(response, 204)
