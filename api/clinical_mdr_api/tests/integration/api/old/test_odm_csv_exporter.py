# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments
import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CODMDT_CODELIST,
    STARTUP_CT_TERM,
    STARTUP_ODM_CONDITIONS,
    STARTUP_ODM_FORMS,
    STARTUP_ODM_ITEM_GROUPS,
    STARTUP_ODM_ITEMS,
    STARTUP_ODM_METHODS,
    STARTUP_ODM_STUDY_EVENTS,
    STARTUP_ODM_VENDOR_ELEMENTS,
    STARTUP_ODM_VENDOR_NAMESPACES,
    STARTUP_ODM_XML_EXPORTER,
    STARTUP_UNIT_DEFINITIONS,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

HEADERS = {"content-type": "text/csv"}


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.odm.csv.exporter")
    db.cypher_query(STARTUP_CODMDT_CODELIST)
    db.cypher_query(STARTUP_ODM_CONDITIONS)
    db.cypher_query(STARTUP_ODM_METHODS)
    db.cypher_query(STARTUP_CT_TERM)
    db.cypher_query(STARTUP_UNIT_DEFINITIONS)
    db.cypher_query(STARTUP_ODM_ITEMS)
    db.cypher_query(STARTUP_ODM_ITEM_GROUPS)
    db.cypher_query(STARTUP_ODM_FORMS)
    db.cypher_query(STARTUP_ODM_STUDY_EVENTS)
    db.cypher_query(STARTUP_ODM_VENDOR_NAMESPACES)
    db.cypher_query(STARTUP_ODM_VENDOR_ELEMENTS)
    db.cypher_query(STARTUP_ODM_XML_EXPORTER)

    yield

    drop_db("old.json.test.odm.csv.exporter")


def test_get_odm_study_event(api_client):
    response = api_client.post(
        "odms/metadata/csvs/export?target_uid=odm_study_event1&target_type=study_event",
        headers=HEADERS,
    )

    assert_response_status_code(response, 200)
    assert (
        response.text
        # pylint: disable=line-too-long
        == '"StudyEvent_Name","StudyEvent_Version","Form_Name","Form_Repeating","Form_Version","ItemGroup_Name","ItemGroup_Version","Item_Name","Item_Datatype","Item_Version","Item_Units","Item_Codelist","Item_Terms"\n"name1","1.0","name1","yes","1.0","name1","1.0","name1","string","1.0","name1","name1","submission_value1"\n'
    )


def test_get_odm_form(api_client):
    response = api_client.post(
        "odms/metadata/csvs/export?target_uid=odm_form1&target_type=form",
        headers=HEADERS,
    )

    assert_response_status_code(response, 200)
    assert (
        response.text
        # pylint: disable=line-too-long
        == '"Form_Name","Form_Repeating","Form_Version","ItemGroup_Name","ItemGroup_Version","Item_Name","Item_Datatype","Item_Version","Item_Units","Item_Codelist","Item_Terms"\n"name1","yes","1.0","name1","1.0","name1","string","1.0","name1","name1","submission_value1"\n'
    )


def test_get_odm_item_group(api_client):
    response = api_client.post(
        "odms/metadata/csvs/export?target_uid=odm_item_group1&target_type=item_group",
        headers=HEADERS,
    )

    assert_response_status_code(response, 200)
    assert (
        response.text
        # pylint: disable=line-too-long
        == '"ItemGroup_Name","ItemGroup_Version","Item_Name","Item_Datatype","Item_Version","Item_Units","Item_Codelist","Item_Terms"\n"name1","1.0","name1","string","1.0","name1","name1","submission_value1"\n'
    )


def test_get_odm_item(api_client):
    response = api_client.post(
        "odms/metadata/csvs/export?target_uid=odm_item1&target_type=item",
        headers=HEADERS,
    )

    assert_response_status_code(response, 200)
    assert (
        response.text
        # pylint: disable=line-too-long
        == '"Item_Name","Item_Datatype","Item_Version","Item_Units","Item_Codelist","Item_Terms"\n"name1","string","1.0","name1","name1","submission_value1"\n'
    )


def test_odm_not_supported_target_type(api_client):
    response = api_client.post(
        "odms/metadata/csvs/export?target_uid=wrong&target_type=study",
        headers=HEADERS,
    )

    assert_response_status_code(response, 400)
    res = response.json()
    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Requested target type not supported."


def test_odm_study_event_not_found(api_client):
    response = api_client.post(
        "odms/metadata/csvs/export?target_uid=wrong&target_type=study_event",
        headers=HEADERS,
    )

    assert_response_status_code(response, 404)


def test_odm_form_not_found(api_client):
    response = api_client.post(
        "odms/metadata/csvs/export?target_uid=wrong&target_type=form",
        headers=HEADERS,
    )

    assert_response_status_code(response, 404)


def test_odm_item_group_not_found(api_client):
    response = api_client.post(
        "odms/metadata/csvs/export?target_uid=wrong&target_type=item_group",
        headers=HEADERS,
    )

    assert_response_status_code(response, 404)


def test_odm_item_not_found(api_client):
    response = api_client.post(
        "odms/metadata/csvs/export?target_uid=wrong&target_type=item",
        headers=HEADERS,
    )

    assert_response_status_code(response, 404)
