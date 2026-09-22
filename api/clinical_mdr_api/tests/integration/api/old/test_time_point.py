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
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_TIME_POINTS,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.time.point")
    db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
    library_service.create(name="Sponsor", is_editable=True)
    db.cypher_query(STARTUP_TIME_POINTS)
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)

    yield

    drop_db("old.json.test.time.point")


def test_post_time_point_which_is_a_tp(api_client):
    data = {
        "name_sentence_case": "time_point_name_sentence_case1",
        "definition": "time_point_definition1",
        "abbreviation": "abbv",
        "template_parameter": True,
        "library_name": "Sponsor",
        "numeric_value_uid": "NumericValue_000001",
        "unit_definition_uid": "UnitDefinition_000001",
        "time_reference_uid": "CTTermRoot_000001",
    }
    response = api_client.post("/concepts/time-points", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "TimePoint_000001"
    assert res["name"] == "1.23 name_1 after term_value_name1"
    assert res["name_sentence_case"] == "time_point_name_sentence_case1"
    assert res["definition"] == "time_point_definition1"
    assert res["abbreviation"] == "abbv"
    assert res["template_parameter"] is True
    assert res["library_name"] == "Sponsor"
    assert res["status"] is None
    assert res["version"] is None
    assert res["change_description"] is None
    assert res["author_username"] is None
    assert res["start_date"] is None
    assert res["end_date"] is None
    assert res["numeric_value_uid"] == "NumericValue_000001"
    assert res["unit_definition_uid"] == "UnitDefinition_000001"
    assert res["time_reference_uid"] == "CTTermRoot_000001"


def test_post_time_point_which_is_a_tp_existing_time_point_is_returned(api_client):
    data = {
        "name_sentence_case": "time_point_name_sentence_case1",
        "definition": "time_point_definition1",
        "abbreviation": "abbv",
        "template_parameter": True,
        "library_name": "Sponsor",
        "numeric_value_uid": "NumericValue_000001",
        "unit_definition_uid": "UnitDefinition_000001",
        "time_reference_uid": "CTTermRoot_000001",
    }
    response = api_client.post("/concepts/time-points", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "TimePoint_000001"
    assert res["name"] == "1.23 name_1 after term_value_name1"
    assert res["name_sentence_case"] == "time_point_name_sentence_case1"
    assert res["definition"] == "time_point_definition1"
    assert res["abbreviation"] == "abbv"
    assert res["template_parameter"] is True
    assert res["library_name"] == "Sponsor"
    assert res["status"] is None
    assert res["version"] is None
    assert res["change_description"] is None
    assert res["author_username"] is None
    assert res["start_date"] is None
    assert res["end_date"] is None
    assert res["numeric_value_uid"] == "NumericValue_000001"
    assert res["unit_definition_uid"] == "UnitDefinition_000001"
    assert res["time_reference_uid"] == "CTTermRoot_000001"


def test_post_time_point_which_is_not_tp(api_client):
    data = {
        "name_sentence_case": "time_point_name_sentence_case2",
        "definition": "time_point_definition2",
        "abbreviation": "abbv",
        "template_parameter": False,
        "library_name": "Sponsor",
        "numeric_value_uid": "NumericValue_000002",
        "unit_definition_uid": "UnitDefinition_000001",
        "time_reference_uid": "CTTermRoot_000001",
    }
    response = api_client.post("/concepts/time-points", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "TimePoint_000002"
    assert res["name"] == "3.21 name_1 after term_value_name1"
    assert res["name_sentence_case"] == "time_point_name_sentence_case2"
    assert res["definition"] == "time_point_definition2"
    assert res["abbreviation"] == "abbv"
    assert res["template_parameter"] is False
    assert res["library_name"] == "Sponsor"
    assert res["status"] is None
    assert res["version"] is None
    assert res["change_description"] is None
    assert res["author_username"] is None
    assert res["start_date"] is None
    assert res["end_date"] is None
    assert res["numeric_value_uid"] == "NumericValue_000002"
    assert res["unit_definition_uid"] == "UnitDefinition_000001"
    assert res["time_reference_uid"] == "CTTermRoot_000001"


def test_get_all_time_points(api_client):
    response = api_client.get("/concepts/time-points?total_count=true")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "TimePoint_000001"
    assert res["items"][0]["name"] == "1.23 name_1 after term_value_name1"
    assert res["items"][0]["name_sentence_case"] == "time_point_name_sentence_case1"
    assert res["items"][0]["definition"] == "time_point_definition1"
    assert res["items"][0]["abbreviation"] == "abbv"
    assert res["items"][0]["template_parameter"] is True
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["status"] is None
    assert res["items"][0]["version"] is None
    assert res["items"][0]["change_description"] is None
    assert res["items"][0]["author_username"] is None
    assert res["items"][0]["start_date"] is None
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["numeric_value_uid"] == "NumericValue_000001"
    assert res["items"][0]["unit_definition_uid"] == "UnitDefinition_000001"
    assert res["items"][0]["time_reference_uid"] == "CTTermRoot_000001"
    assert res["items"][1]["uid"] == "TimePoint_000002"
    assert res["items"][1]["name"] == "3.21 name_1 after term_value_name1"
    assert res["items"][1]["name_sentence_case"] == "time_point_name_sentence_case2"
    assert res["items"][1]["definition"] == "time_point_definition2"
    assert res["items"][1]["abbreviation"] == "abbv"
    assert res["items"][1]["template_parameter"] is False
    assert res["items"][1]["library_name"] == "Sponsor"
    assert res["items"][1]["status"] is None
    assert res["items"][1]["version"] is None
    assert res["items"][1]["change_description"] is None
    assert res["items"][1]["author_username"] is None
    assert res["items"][1]["start_date"] is None
    assert res["items"][1]["end_date"] is None
    assert res["items"][1]["numeric_value_uid"] == "NumericValue_000002"
    assert res["items"][1]["unit_definition_uid"] == "UnitDefinition_000001"
    assert res["items"][1]["time_reference_uid"] == "CTTermRoot_000001"
