# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

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
    inject_and_clear_db("old.json.test.timeframe.versioning")
    db.cypher_query(STARTUP_PARAMETERS_CYPHER)

    library_service.create(**library_data)
    timeframe_template = tt_models.TimeframeTemplateCreateInput(**template_data)
    timeframe_template = tt_service.TimeframeTemplateService().create(
        timeframe_template
    )
    tt_uid = (
        timeframe_template.uid
        if isinstance(timeframe_template, tt_models.TimeframeTemplate)
        else timeframe_template["uid"]
    )
    tt_service.TimeframeTemplateService().approve(tt_uid)

    yield

    drop_db("old.json.test.timeframe.versioning")


def test_if_zero_timeframes(api_client):
    response = api_client.get("/timeframes")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_if_adding_timeframe_works(api_client):
    data = {
        "library_name": "Test library",
        "name": "Test timeframe",
        "timeframe_template_uid": "TimeframeTemplate_000001",
        "parameter_terms": [],
    }
    response = api_client.post("/timeframes", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_count"] == 0
    assert res["change_description"] == "Initial version"
    assert res["end_date"] is None
    assert res["library"] == {"is_editable": True, "name": "Test library"}
    assert res["name"] == "Test_Name_Template"
    assert res["name_plain"] == "Test_Name_Template"
    assert res["template"] == {
        "name": "Test_Name_Template",
        "name_plain": "Test_Name_Template",
        "guidance_text": None,
        "uid": "TimeframeTemplate_000001",
        "sequence_id": "T1",
        "library_name": "Test library",
    }
    assert res["parameter_terms"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["status"] == "Draft"
    assert res["uid"] == "Timeframe_000001"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["version"] == "0.1"


def test_if_approval_works2(api_client):
    response = api_client.post("/timeframes/Timeframe_000001/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_count"] == 0
    assert res["change_description"] == "Approved version"
    assert res["end_date"] is None
    assert res["library"] == {"is_editable": True, "name": "Test library"}
    assert res["name"] == "Test_Name_Template"
    assert res["name_plain"] == "Test_Name_Template"
    assert res["parameter_terms"] == []
    assert res["possible_actions"] == ["inactivate"]
    assert res["template"] == {
        "name": "Test_Name_Template",
        "name_plain": "Test_Name_Template",
        "guidance_text": None,
        "uid": "TimeframeTemplate_000001",
        "sequence_id": "T1",
        "library_name": "Test library",
    }
    assert res["status"] == "Final"
    assert res["uid"] == "Timeframe_000001"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["version"] == "1.0"


def test_if_second_approval_fails2(api_client):
    response = api_client.patch("/timeframes/Timeframe_000001/approvals")

    assert_response_status_code(response, 405)

    res = response.json()

    assert res["detail"] == "Method Not Allowed"


def test_random_test_name_33(api_client):
    response = api_client.post("/timeframes/Timeframe_000001/approvals")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."


def test_check_how_many_parameters_are_there_2(api_client):
    response = api_client.get("/timeframes/Timeframe_000001/parameters")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == []


def test_version_display1(api_client):
    response = api_client.get("/timeframes/Timeframe_000001/versions")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["uid"] == "Timeframe_000001"
    assert res[0]["name"] == "Test_Name_Template"
    assert res[0]["name_plain"] == "Test_Name_Template"
    assert res[0]["end_date"] is None
    assert res[0]["status"] == "Final"
    assert res[0]["version"] == "1.0"
    assert res[0]["change_description"] == "Approved version"
    assert res[0]["study_count"] == 0
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["possible_actions"] == ["inactivate"]
    assert res[0]["template"] == {
        "name": "Test_Name_Template",
        "name_plain": "Test_Name_Template",
        "guidance_text": None,
        "uid": "TimeframeTemplate_000001",
        "sequence_id": "T1",
        "library_name": "Test library",
    }
    assert res[0]["parameter_terms"] == []
    assert res[0]["library"] == {"name": "Test library", "is_editable": True}
    assert set(res[0]["changes"]) == set(
        [
            "start_date",
            "end_date",
            "status",
            "version",
            "change_description",
            "possible_actions",
        ]
    )
    assert res[1]["uid"] == "Timeframe_000001"
    assert res[1]["name"] == "Test_Name_Template"
    assert res[1]["name_plain"] == "Test_Name_Template"
    assert res[1]["end_date"]
    assert res[1]["status"] == "Draft"
    assert res[1]["version"] == "0.1"
    assert res[1]["change_description"] == "Initial version"
    assert res[1]["study_count"] == 0
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["possible_actions"] == ["approve", "delete", "edit"]
    assert res[1]["template"] == {
        "name": "Test_Name_Template",
        "name_plain": "Test_Name_Template",
        "guidance_text": None,
        "uid": "TimeframeTemplate_000001",
        "sequence_id": "T1",
        "library_name": "Test library",
    }
    assert res[1]["parameter_terms"] == []
    assert res[1]["library"] == {"name": "Test library", "is_editable": True}
    assert res[1]["changes"] == []


def test_patching_aproved_timeframe_with_missing_field(api_client):
    data = {
        "name": "test{test-uid}",
        "parameter_terms": [
            {
                "name": "Intervention",
                "terms": [
                    {
                        "uid": "TemplateParameter_000003",
                        "type": "Intervention",
                        "name": "Intervention",
                        "value": "diabetes",
                        "index": 1,
                    }
                ],
                "conjunction": "",
            }
        ],
    }
    response = api_client.patch("/timeframes/Timeframe_000001", json=data)

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
                        "name": "Intervention",
                        "terms": [
                            {
                                "uid": "TemplateParameter_000003",
                                "type": "Intervention",
                                "name": "Intervention",
                                "value": "diabetes",
                                "index": 1,
                            }
                        ],
                        "conjunction": "",
                    }
                ],
            },
        }
    ]


def test_patching_approved_timeframe(api_client):
    data = {
        "change_description": "Change test",
        "name": "test{test-uid}",
        "parameter_terms": [],
    }
    response = api_client.patch("/timeframes/Timeframe_000001", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."
