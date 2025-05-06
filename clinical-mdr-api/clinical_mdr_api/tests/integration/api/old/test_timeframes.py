# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db
from pydantic import BaseModel

import clinical_mdr_api.models.syntax_templates.timeframe_template as tt_models
import clinical_mdr_api.services.libraries.libraries as library_service
import clinical_mdr_api.services.syntax_templates.timeframe_templates as tt_service
from clinical_mdr_api.main import app
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
    inject_and_clear_db("old.json.test.timeframes")
    db.cypher_query(STARTUP_PARAMETERS_CYPHER)

    library_service.create(**library_data)
    ttdata = template_data.copy()
    ttdata["name"] = "Test [Indication]"
    timeframe_template = tt_models.TimeframeTemplateCreateInput(**ttdata)
    timeframe_template = tt_service.TimeframeTemplateService().create(
        timeframe_template
    )
    if isinstance(timeframe_template, BaseModel):
        timeframe_template = timeframe_template.model_dump()
    tt_service.TimeframeTemplateService().approve(timeframe_template["uid"])
    ttdata = template_data.copy()
    ttdata["name"] = "Test [Indication] and [Intervention]"
    timeframe_template = tt_models.TimeframeTemplateCreateInput(**ttdata)
    tt2 = tt_service.TimeframeTemplateService().create(timeframe_template)
    if isinstance(tt2, BaseModel):
        tt2 = tt2.model_dump()
    tt_service.TimeframeTemplateService().approve(tt2["uid"])

    yield

    drop_db("old.json.test.timeframes")


def test_empty_list4(api_client):
    response = api_client.get("/timeframes")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_adding_timeframe_wrong_parameter(api_client):
    data = {
        "library_name": "Test library",
        "parameter_terms": [
            {
                "conjunction": ",",
                "name": "Intervention",
                "terms": [
                    {
                        "index": 1,
                        "name": "Intervention",
                        "type": "Intervention",
                        "uid": "Indication-99991",
                        "value": "diabetes",
                    }
                ],
            }
        ],
        "timeframe_template_uid": "TimeframeTemplate_000001",
    }
    response = api_client.post("/timeframes", json=data)

    assert_response_status_code(response, 422)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "Parameter term Indication-99991 ('type 2 diabetes') not valid for parameter 'Intervention'"
    )


def test_previewing_timeframe_single_parameter(api_client):
    data = {
        "library_name": "Test library",
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
                    },
                    {
                        "index": 2,
                        "name": "Indication",
                        "type": "Indication",
                        "uid": "Indication-99992",
                        "value": "coronary heart disease",
                    },
                ],
            }
        ],
        "timeframe_template_uid": "TimeframeTemplate_000001",
    }
    response = api_client.post("/timeframes/preview", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_count"] == 0
    assert res["change_description"] == "Initial version"
    assert res["end_date"] is None
    assert res["library"] == {"is_editable": True, "name": "Test library"}
    assert res["name"] == "Test [type 2 diabetes , coronary heart disease]"
    assert res["name_plain"] == "Test type 2 diabetes , coronary heart disease"
    assert res["parameter_terms"] == [
        {
            "conjunction": ",",
            "position": 1,
            "terms": [
                {
                    "index": 1,
                    "name": "type 2 diabetes",
                    "type": "Indication",
                    "uid": "Indication-99991",
                },
                {
                    "index": 2,
                    "name": "coronary heart disease",
                    "type": "Indication",
                    "uid": "Indication-99992",
                },
            ],
        }
    ]
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["status"] == "Draft"
    assert res["template"] == {
        "name": "Test [Indication]",
        "name_plain": "Test [Indication]",
        "guidance_text": None,
        "uid": "TimeframeTemplate_000001",
        "sequence_id": "T1",
        "library_name": "Test library",
    }
    assert res["uid"] == "Timeframe_000001"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["version"] == "0.1"


def test_adding_timeframe_single_parameter(api_client):
    data = {
        "library_name": "Test library",
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
                    },
                    {
                        "index": 2,
                        "name": "Indication",
                        "type": "Indication",
                        "uid": "Indication-99992",
                        "value": "coronary heart disease",
                    },
                ],
            }
        ],
        "timeframe_template_uid": "TimeframeTemplate_000001",
    }
    response = api_client.post("/timeframes", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_count"] == 0
    assert res["change_description"] == "Initial version"
    assert res["end_date"] is None
    assert res["library"] == {"is_editable": True, "name": "Test library"}
    assert res["name"] == "Test [type 2 diabetes , coronary heart disease]"
    assert res["name_plain"] == "Test type 2 diabetes , coronary heart disease"
    assert res["parameter_terms"] == [
        {
            "conjunction": ",",
            "position": 1,
            "terms": [
                {
                    "index": 1,
                    "name": "type 2 diabetes",
                    "type": "Indication",
                    "uid": "Indication-99991",
                },
                {
                    "index": 2,
                    "name": "coronary heart disease",
                    "type": "Indication",
                    "uid": "Indication-99992",
                },
            ],
        }
    ]
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["status"] == "Draft"
    assert res["template"] == {
        "name": "Test [Indication]",
        "name_plain": "Test [Indication]",
        "guidance_text": None,
        "uid": "TimeframeTemplate_000001",
        "sequence_id": "T1",
        "library_name": "Test library",
    }
    assert res["uid"] == "Timeframe_000002"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["version"] == "0.1"


def test_adding_timeframe_multiple_parameters(api_client):
    data = {
        "library_name": "Test library",
        "parameter_terms": [
            {
                "conjunction": ",",
                "name": "Indication",
                "terms": [
                    {
                        "index": 1,
                        "name": "type 2 diabetes",
                        "type": "Indication",
                        "uid": "Indication-99991",
                    },
                    {
                        "index": 2,
                        "name": "coronary heart disease",
                        "type": "Indication",
                        "uid": "Indication-99992",
                    },
                ],
            },
            {
                "conjunction": "and",
                "name": "Intervention",
                "terms": [
                    {
                        "index": 1,
                        "name": "Metformin",
                        "type": "Intervention",
                        "uid": "Intervention-99991",
                    },
                    {
                        "index": 2,
                        "name": "human insulin",
                        "type": "Intervention",
                        "uid": "Intervention-99992",
                    },
                ],
            },
        ],
        "timeframe_template_uid": "TimeframeTemplate_000002",
    }
    response = api_client.post("/timeframes", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_count"] == 0
    assert res["change_description"] == "Initial version"
    assert res["end_date"] is None
    assert res["library"] == {"is_editable": True, "name": "Test library"}
    assert (
        res["name"]
        == "Test [type 2 diabetes , coronary heart disease] and [human insulin and Metformin]"
    )
    assert (
        res["name_plain"]
        == "Test type 2 diabetes , coronary heart disease and human insulin and Metformin"
    )
    assert res["parameter_terms"] == [
        {
            "conjunction": ",",
            "position": 1,
            "terms": [
                {
                    "index": 1,
                    "name": "type 2 diabetes",
                    "type": "Indication",
                    "uid": "Indication-99991",
                },
                {
                    "index": 2,
                    "name": "coronary heart disease",
                    "type": "Indication",
                    "uid": "Indication-99992",
                },
            ],
        },
        {
            "conjunction": "and",
            "position": 2,
            "terms": [
                {
                    "index": 1,
                    "name": "human insulin",
                    "type": "Intervention",
                    "uid": "Intervention-99991",
                },
                {
                    "index": 2,
                    "name": "Metformin",
                    "type": "Intervention",
                    "uid": "Intervention-99992",
                },
            ],
        },
    ]
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["status"] == "Draft"
    assert res["template"] == {
        "name": "Test [Indication] and [Intervention]",
        "name_plain": "Test [Indication] and [Intervention]",
        "guidance_text": None,
        "uid": "TimeframeTemplate_000002",
        "sequence_id": "T2",
        "library_name": "Test library",
    }
    assert res["uid"] == "Timeframe_000003"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["version"] == "0.1"


def test_adding_the_same_timeframe_name(api_client):
    data = {
        "library_name": "Test library",
        "parameter_terms": [
            {
                "conjunction": ",",
                "position": 1,
                "terms": [
                    {
                        "index": 1,
                        "name": "type 2 diabetes",
                        "type": "Indication",
                        "uid": "Indication-99991",
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
        "timeframe_template_uid": "TimeframeTemplate_000001",
    }
    response = api_client.post("/timeframes", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "Resource with Name 'Test [type 2 diabetes , coronary heart disease]' already exists."
    )


def test_delete7(api_client):
    response = api_client.delete("/timeframes/Timeframe_000002")

    assert_response_status_code(response, 204)
