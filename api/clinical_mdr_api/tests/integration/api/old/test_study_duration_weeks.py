# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

import clinical_mdr_api.services.libraries.libraries as library_service
from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.duration.weeks")
    library_service.create(name="Sponsor", is_editable=True)
    db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)

    yield

    drop_db("old.json.test.study.duration.weeks")


def test_post_study_duration_weeks_which_is_a_tp(api_client):
    data = {
        "value": 1.23,
        "definition": "study_duration_weeks_definition1",
        "abbreviation": "abbv",
        "template_parameter": True,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/study-duration-weeks", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "StudyDurationWeeks_000001"
    assert res["name"] == "1.23 weeks"
    assert res["value"] == 1.23
    assert res["name_sentence_case"] == "1.23 weeks"
    assert res["definition"] == "study_duration_weeks_definition1"
    assert res["abbreviation"] == "abbv"
    assert res["template_parameter"] is True
    assert res["library_name"] == "Sponsor"
    assert res["status"] is None
    assert res["version"] is None
    assert res["change_description"] is None
    assert res["author_username"] is None
    assert res["end_date"] is None


def test_post_study_duration_weeks_which_is_a_tp_existing_study_duration_weeks_is_returned(
    api_client,
):
    data = {
        "value": 1.23,
        "definition": "study_duration_weeks_definition1",
        "abbreviation": "abbv",
        "template_parameter": True,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/study-duration-weeks", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "StudyDurationWeeks_000001"
    assert res["name"] == "1.23 weeks"
    assert res["value"] == 1.23
    assert res["name_sentence_case"] == "1.23 weeks"
    assert res["definition"] == "study_duration_weeks_definition1"
    assert res["abbreviation"] == "abbv"
    assert res["template_parameter"] is True
    assert res["library_name"] == "Sponsor"
    assert res["status"] is None
    assert res["version"] is None
    assert res["change_description"] is None
    assert res["author_username"] is None
    assert res["end_date"] is None


def test_post_study_duration_weeks_which_is_not_tp(api_client):
    data = {
        "value": 1.234,
        "definition": "study_duration_weeks_definition2",
        "abbreviation": "abbv",
        "template_parameter": False,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/study-duration-weeks", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "StudyDurationWeeks_000002"
    assert res["name"] == "1.234 weeks"
    assert res["value"] == 1.234
    assert res["name_sentence_case"] == "1.234 weeks"
    assert res["definition"] == "study_duration_weeks_definition2"
    assert res["abbreviation"] == "abbv"
    assert res["template_parameter"] is False
    assert res["library_name"] == "Sponsor"
    assert res["status"] is None
    assert res["version"] is None
    assert res["change_description"] is None
    assert res["author_username"] is None
    assert res["end_date"] is None


def test_get_all_study_duration_weeks(api_client):
    response = api_client.get("/concepts/study-duration-weeks?total_count=true")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "StudyDurationWeeks_000001"
    assert res["items"][0]["name"] == "1.23 weeks"
    assert res["items"][0]["value"] == 1.23
    assert res["items"][0]["name_sentence_case"] == "1.23 weeks"
    assert res["items"][0]["definition"] == "study_duration_weeks_definition1"
    assert res["items"][0]["abbreviation"] == "abbv"
    assert res["items"][0]["template_parameter"] is True
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["status"] is None
    assert res["items"][0]["version"] is None
    assert res["items"][0]["change_description"] is None
    assert res["items"][0]["author_username"] is None
    assert res["items"][0]["end_date"] is None
    assert res["items"][1]["uid"] == "StudyDurationWeeks_000002"
    assert res["items"][1]["name"] == "1.234 weeks"
    assert res["items"][1]["value"] == 1.234
    assert res["items"][1]["name_sentence_case"] == "1.234 weeks"
    assert res["items"][1]["definition"] == "study_duration_weeks_definition2"
    assert res["items"][1]["abbreviation"] == "abbv"
    assert res["items"][1]["template_parameter"] is False
    assert res["items"][1]["library_name"] == "Sponsor"
    assert res["items"][1]["status"] is None
    assert res["items"][1]["version"] is None
    assert res["items"][1]["change_description"] is None
    assert res["items"][1]["author_username"] is None
    assert res["items"][1]["end_date"] is None
