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
    inject_and_clear_db("old.json.test.time.point.negative")
    db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
    library_service.create(name="Sponsor", is_editable=True)
    db.cypher_query(STARTUP_TIME_POINTS)
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)

    yield

    drop_db("old.json.test.time.point.negative")


def test_post_time_point(api_client):
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


def test_post_non_existent_numeric_value(api_client):
    data = {
        "name_sentence_case": "time_point_name_sentence_case1",
        "definition": "time_point_definition1",
        "library_name": "Sponsor",
        "numeric_value_uid": "NumericValue_NON_EXISTENT",
        "unit_definition_uid": "UnitDefinition_000001",
        "time_reference_uid": "CTTermRoot_000001",
    }
    response = api_client.post("/concepts/time-points", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "TimePointVO tried to connect to non-existent Numeric Value with UID 'NumericValue_NON_EXISTENT'."
    )


def test_post_non_existent_unit_definition(api_client):
    data = {
        "name_sentence_case": "time_point_name_sentence_case1",
        "definition": "time_point_definition1",
        "library_name": "Sponsor",
        "numeric_value_uid": "NumericValue_000001",
        "unit_definition_uid": "UnitDefinition_NON_EXISTENT",
        "time_reference_uid": "CTTermRoot_000001",
    }
    response = api_client.post("/concepts/time-points", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "TimePointVO tried to connect to non-existent Unit Definition with UID 'UnitDefinition_NON_EXISTENT'."
    )


def test_post_non_existent_time_reference(api_client):
    data = {
        "name_sentence_case": "time_point_name_sentence_case1",
        "definition": "time_point_definition1",
        "library_name": "Sponsor",
        "numeric_value_uid": "NumericValue_000001",
        "unit_definition_uid": "UnitDefinition_000001",
        "time_reference_uid": "TimeReference_NON_EXISTENT",
    }
    response = api_client.post("/concepts/time-points", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "TimePointVO tried to connect to non-existent CT Term with UID 'TimeReference_NON_EXISTENT'."
    )
