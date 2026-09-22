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
    inject_and_clear_db("old.json.test.study.week.negative")
    library_service.create(name="Sponsor", is_editable=True)
    db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)

    yield

    drop_db("old.json.test.study.week.negative")


def test_post_study_week(api_client):
    data = {
        "value": 1.23,
        "definition": "study_week_definition1",
        "abbreviation": "abbv",
        "library_name": "Sponsor",
        "template_parameter": True,
    }
    response = api_client.post("/concepts/study-weeks", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "StudyWeek_000001"
    assert res["name"] == "Week 1.23"
    assert res["value"] == 1.23
    assert res["name_sentence_case"] == "week 1.23"
    assert res["definition"] == "study_week_definition1"
    assert res["abbreviation"] == "abbv"
    assert res["template_parameter"] is True
    assert res["library_name"] == "Sponsor"
