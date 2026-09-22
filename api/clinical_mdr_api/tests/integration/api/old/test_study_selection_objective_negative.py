# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_STUDY_OBJECTIVE_CYPHER,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.selection.objective.negative")
    db.cypher_query(STARTUP_STUDY_OBJECTIVE_CYPHER)

    yield

    drop_db("old.json.test.study.selection.objective.negative")


def test_adding_selection_objective_does_not_exists(api_client):
    data = {
        "objective_uid": "Objective_000001_does_not_exists",
        "objective_level": "Primary",
    }
    response = api_client.post("/studies/study_root/study-objectives", json=data)

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "No ObjectiveRoot with UID 'Objective_000001_does_not_exists' found in given status, date and version."
    )


def test_selection_objective_is_retired(api_client):
    data = {"objective_uid": "Objective_000005", "objective_level": "Primary"}
    response = api_client.post("/studies/study_root/study-objectives", json=data)

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "No ObjectiveRoot with UID 'Objective_000005' found in given status, date and version."
    )


def test_get_specific_selection_where_no_selection_exists1(api_client):
    response = api_client.get(
        "/studies/study_root/study-objectives/study_objective_uid"
    )

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "Study Objective with UID 'study_objective_uid' doesn't exist."
    )
