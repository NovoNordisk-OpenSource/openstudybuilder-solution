# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_STUDY_ENDPOINT_CYPHER,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.selection.endpoint.negative")
    db.cypher_query(STARTUP_STUDY_ENDPOINT_CYPHER)

    yield

    drop_db("old.json.test.study.selection.endpoint.negative")


def test_adding_selection_endpoint_does_not_exists(api_client):
    data = {
        "endpoint_uid": "Endpoint_000001_does_not_exists",
        "endpoint_level": "Primary",
    }
    response = api_client.post("/studies/study_root/study-endpoints", json=data)

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "No EndpointRoot with UID 'Endpoint_000001_does_not_exists' found in given status, date and version."
    )


def test_adding_selection_study_objective_does_not_exists(api_client):
    data = {
        "study_objective_uid": "Study_Objective_000001_does_not_exists",
        "endpoint_level": "Primary",
    }
    response = api_client.post("/studies/study_root/study-endpoints", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "There is no selected Study Objective with UID 'Study_Objective_000001_does_not_exists'."
    )


def test_adding_selection_endpoint_units_are_missing_a_separator(api_client):
    data = {
        "endpoint_level": "Primary",
        "endpoint_units": {"units": ["unit 1", "unit 2"], "separator": None},
    }
    response = api_client.post("/studies/study_root/study-endpoints", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "In case of more than one endpoint units, a unit separator is required."
    )


def test_adding_selection_endpoint_units_having_a_separator_but_no_units(api_client):
    data = {
        "endpoint_level": "Primary",
        "endpoint_units": {"units": [], "separator": "and"},
    }
    response = api_client.post("/studies/study_root/study-endpoints", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "Separator should only be set if more than 1 units are selected '()'."
    )


def test_get_specific_selection_where_no_selection_exists(api_client):
    response = api_client.get("/studies/study_root/study-endpoints/study_endpoint_uid")

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "There is no selection between the Study Endpoint with UID 'study_endpoint_uid' and the study."
    )
