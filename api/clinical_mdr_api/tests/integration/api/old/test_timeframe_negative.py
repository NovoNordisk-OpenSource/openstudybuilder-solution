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
    template_data,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.timeframe.negative")
    db.cypher_query(STARTUP_PARAMETERS_CYPHER)

    library_service.create(name="Test library", is_editable=True)
    ttdata = template_data.copy()
    ttdata["name"] = "Test [Indication]"
    timeframe_template = tt_models.TimeframeTemplateCreateInput(**ttdata)
    timeframe_template = tt_service.TimeframeTemplateService().create(
        timeframe_template
    )
    tt_uid = (
        timeframe_template.uid
        if isinstance(timeframe_template, tt_models.TimeframeTemplate)
        else timeframe_template["uid"]
    )
    tt_service.TimeframeTemplateService().approve(tt_uid)
    ttdt = template_data.copy()
    ttdt["name"] = "Name not approved"
    timeframe_template = tt_models.TimeframeTemplateCreateInput(**ttdt)
    tt_service.TimeframeTemplateService().create(timeframe_template)

    yield

    drop_db("old.json.test.timeframe.negative")


def test_non_existent_library(api_client):
    data = {
        "library_name": "non-existent library",
        "name": "Test timeframe",
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
        "timeframe_template_uid": "TimeframeTemplate_000001",
    }
    response = api_client.post("/timeframes", json=data)

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert res["message"] == "Library with Name 'non-existent library' doesn't exist."


def test_wrong_template_uid(api_client):
    data = {
        "library_name": "Test library",
        "name": "Test timeframe",
        "parameter_terms": [],
        "timeframe_template_uid": "wrong-uid",
    }
    response = api_client.post("/timeframes", json=data)

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "No TimeframeTemplateRoot with UID 'wrong-uid' found in given status, date and version."
    )


def test_non_wront_tt(api_client):
    data = {
        "library_name": "Test library",
        "name": "Test timeframe",
        "parameter_terms": [],
        "timeframe_template_uid": "TimeframeTemplate_000002",
    }
    response = api_client.post("/timeframes", json=data)

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "No TimeframeTemplateRoot with UID 'TimeframeTemplate_000002' found in given status, date and version."
    )


def test_wrong_parameters(api_client):
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
                        "uid": "TemplateParameter_000001",
                        "value": "type 2 diabetes",
                    }
                ],
            }
        ],
        "timeframe_template_uid": "TimeframeTemplate_000001",
    }
    response = api_client.post("/timeframes", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "One or more of the specified template parameters can not be found."
    )
