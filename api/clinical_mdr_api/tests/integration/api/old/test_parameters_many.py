# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_PARAMETERS_CYPHER,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.parameters.many")
    db.cypher_query(STARTUP_PARAMETERS_CYPHER)
    db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)

    yield

    drop_db("old.json.test.parameters.many")


def test_random_test_name_52(api_client):
    response = api_client.get("/template-parameters")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["name"] == "Activity"
    assert res[0]["terms"] == []
    assert res[1]["name"] == "ActivityGroup"
    assert res[1]["terms"] == []
    assert res[2]["name"] == "ActivityInstance"
    assert res[2]["terms"] == [
        {"uid": "Intervention-99992", "name": "Metformin", "type": "Intervention"},
        {"uid": "Intervention-99991", "name": "human insulin", "type": "Intervention"},
    ]
    assert res[3]["name"] == "ActivitySubGroup"
    assert res[3]["terms"] == []
    assert res[4]["name"] == "CategoricFinding"
    assert res[4]["terms"] == []
    assert res[5]["name"] == "CompoundAlias"
    assert res[5]["terms"] == []
    assert res[6]["name"] == "CompoundDosing"
    assert res[6]["terms"] == []
    assert res[7]["name"] == "Event"
    assert res[7]["terms"] == []
    assert res[8]["name"] == "Finding"
    assert res[8]["terms"] == []
    assert res[9]["name"] == "Indication"
    assert res[9]["terms"] == [
        {"name": "breathing problems", "uid": "Indication-99993", "type": "Indication"},
        {
            "name": "coronary heart disease",
            "uid": "Indication-99992",
            "type": "Indication",
        },
        {"name": "type 2 diabetes", "uid": "Indication-99991", "type": "Indication"},
    ]
    assert res[10]["name"] == "Intervention"
    assert res[10]["terms"] == [
        {"uid": "Intervention-99992", "name": "Metformin", "type": "Intervention"},
        {"uid": "Intervention-99991", "name": "human insulin", "type": "Intervention"},
    ]
    assert res[11]["name"] == "LaboratoryActivity"
    assert res[11]["terms"] == []
    assert res[12]["name"] == "LagTime"
    assert res[12]["terms"] == []
    assert res[13]["name"] == "NumericFinding"
    assert res[13]["terms"] == []
    assert res[14]["name"] == "NumericValue"
    assert res[14]["terms"] == []
    assert res[15]["name"] == "NumericValueWithUnit"
    assert res[15]["terms"] == []
    assert res[16]["name"] == "RatingScale"
    assert res[16]["terms"] == []
    assert res[17]["name"] == "Reminder"
    assert res[17]["terms"] == []
    assert res[18]["name"] == "SimpleConcept"
    assert res[18]["terms"] == []
    assert res[19]["name"] == "SpecialPurpose"
    assert res[19]["terms"] == []
    assert res[20]["name"] == "StudyDay"
    assert res[20]["terms"] == []
    assert res[21]["name"] == "StudyDurationDays"
    assert res[21]["terms"] == []
    assert res[22]["name"] == "StudyDurationWeeks"
    assert res[22]["terms"] == []
    assert res[23]["name"] == "StudyEndpoint"
    assert res[23]["terms"] == []
    assert res[24]["name"] == "StudyWeek"
    assert res[24]["terms"] == []
    assert res[25]["name"] == "TextValue"
    assert res[25]["terms"] == []
    assert res[26]["name"] == "TextualFinding"
    assert res[26]["terms"] == []
    assert res[27]["name"] == "TimePoint"
    assert res[27]["terms"] == []
    assert res[28]["name"] == "VisitName"
    assert res[28]["terms"] == []
    assert res[29]["name"] == "WeekInStudy"
    assert res[29]["terms"] == []


def test_random_test_name_80(api_client):
    response = api_client.get("/template-parameters/ActivityInstance/terms")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["uid"] == "Intervention-99992"
    assert res[0]["name"] == "Metformin"
    assert res[0]["type"] == "Intervention"
    assert res[1]["uid"] == "Intervention-99991"
    assert res[1]["name"] == "human insulin"
    assert res[1]["type"] == "Intervention"
