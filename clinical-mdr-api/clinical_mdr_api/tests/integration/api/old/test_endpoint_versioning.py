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
    inject_and_clear_db("old.json.test.endpoint.versioning")
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

    drop_db("old.json.test.endpoint.versioning")


def test_if_zero_endpoints(api_client):
    response = api_client.get("/endpoints")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_if_adding_endpoint_works(api_client):
    data = {
        "endpoint_template_uid": "EndpointTemplate_000001",
        "library_name": "Test library",
        "name": "Test objective",
        "parameter_terms": [
            {
                "conjunction": ",",
                "name": "Indication",
                "terms": [
                    {
                        "index": 1,
                        "name": "Indication",
                        "type": "Indication",
                        "uid": "Indication-99991",
                        "value": "type 2 diabetes",
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
            "conjunction": ",",
            "position": 1,
            "terms": [
                {
                    "index": 1,
                    "type": "Indication",
                    "uid": "Indication-99991",
                    "name": "type 2 diabetes",
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


def test_if_approval_works(api_client):
    response = api_client.post("/endpoints/Endpoint_000001/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["change_description"] == "Approved version"
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
            "conjunction": ",",
            "position": 1,
            "terms": [
                {
                    "index": 1,
                    "type": "Indication",
                    "uid": "Indication-99991",
                    "name": "type 2 diabetes",
                }
            ],
        }
    ]
    assert res["possible_actions"] == ["inactivate"]
    assert res["status"] == "Final"
    assert res["study_count"] == 0
    assert res["uid"] == "Endpoint_000001"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["version"] == "1.0"


def test_if_second_approval_fails(api_client):
    response = api_client.patch("/endpoints/Endpoint_000001/approvals")

    assert_response_status_code(response, 405)

    res = response.json()

    assert res["detail"] == "Method Not Allowed"


def test_random_test_name_34(api_client):
    response = api_client.post("/endpoints/Endpoint_000001/approvals")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."


def test_check_how_many_parameters_are_there_1(api_client):
    response = api_client.get("/endpoints/Endpoint_000001/parameters")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["name"] == "Indication"
    assert res[0]["terms"] == [
        {"name": "breathing problems", "uid": "Indication-99993", "type": "Indication"},
        {
            "name": "coronary heart disease",
            "uid": "Indication-99992",
            "type": "Indication",
        },
        {"name": "type 2 diabetes", "uid": "Indication-99991", "type": "Indication"},
    ]


def test_patching_aproved_endpoint_with_missing_field(api_client):
    data = {
        "name": "test{test-uid}",
        "parameter_terms": [
            {
                "conjunction": ",",
                "position": 1,
                "terms": [
                    {
                        "index": 1,
                        "type": "Indication",
                        "uid": "Indication-99991",
                        "name": "type 2 diabetes",
                    }
                ],
            }
        ],
    }
    response = api_client.patch("/endpoints/Endpoint_000001", json=data)

    assert_response_status_code(response, 422)

    res = response.json()

    assert res["detail"] == [
        {
            "type": "missing",
            "loc": ["body", "change_description"],
            "msg": "Field required",
            "input": {
                "name": "test{test-uid}",
                "parameter_terms": [
                    {
                        "conjunction": ",",
                        "position": 1,
                        "terms": [
                            {
                                "index": 1,
                                "type": "Indication",
                                "uid": "Indication-99991",
                                "name": "type 2 diabetes",
                            }
                        ],
                    }
                ],
            },
        }
    ]


def test_patching_approved_objective(api_client):
    data = {
        "change_description": "Change test",
        "name": "test{test-uid}",
        "parameter_terms": [
            {
                "conjunction": ",",
                "name": "Indication",
                "terms": [
                    {
                        "index": 1,
                        "type": "Indication",
                        "uid": "Indication-99991",
                        "name": "type 2 diabetes",
                    }
                ],
            }
        ],
    }
    response = api_client.patch("/endpoints/Endpoint_000001", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."
