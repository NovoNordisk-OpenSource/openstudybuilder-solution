# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import STARTUP_ODM_FORMS
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.odm.study.events.negative")
    db.cypher_query(STARTUP_ODM_FORMS)

    yield

    drop_db("old.json.test.odm.study.events.negative")


def test_create_a_new_odm_study_event(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "effective_date": "2022-04-21",
        "retired_date": "2022-04-21",
        "description": "description1",
    }
    response = api_client.post("odms/study-events", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["effective_date"] == "2022-04-21"
    assert res["retired_date"] == "2022-04-21"
    assert res["description"] == "description1"
    assert res["display_in_tree"] is True
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["forms"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_cannot_create_a_new_odm_study_event_with_same_properties(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "effective_date": "2022-04-21",
        "retired_date": "2022-04-21",
        "description": "description1",
    }
    response = api_client.post("odms/study-events", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "ODM Study Event already exists with UID (OdmStudyEvent_000001) and data {'name': 'name1', 'oid': 'oid1', 'effective_date': '2022-04-21', 'retired_date': '2022-04-21', 'description': 'description1', 'display_in_tree': True}"
    )


def test_getting_error_for_retrieving_non_existent_odm_study_event(api_client):
    response = api_client.get("odms/study-events/OdmStudyEvent_000002")

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "OdmStudyEventAR with UID 'OdmStudyEvent_000002' doesn't exist or there's no version with requested status or version number."
    )


def test_cannot_inactivate_an_odm_study_event_that_is_in_draft_status(api_client):
    response = api_client.delete("odms/study-events/OdmStudyEvent_000001/activations")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Cannot retire draft version."


def test_cannot_reactivate_an_odm_study_event_that_is_not_retired(api_client):
    response = api_client.post("odms/study-events/OdmStudyEvent_000001/activations")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Only RETIRED version can be reactivated."


def test_approve_odm_study_event(api_client):
    response = api_client.post("odms/study-events/OdmStudyEvent_000001/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["change_description"] == "Approved version"
    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["effective_date"] == "2022-04-21"
    assert res["retired_date"] == "2022-04-21"
    assert res["description"] == "description1"
    assert res["display_in_tree"] is True
    assert res["forms"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_inactivate_odm_study_event(api_client):
    response = api_client.delete("odms/study-events/OdmStudyEvent_000001/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["end_date"] is None
    assert res["status"] == "Retired"
    assert res["version"] == "2.0"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["change_description"] == "Inactivated version"
    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["name"] == "name1"
    assert res["library_name"] == "Sponsor"
    assert res["oid"] == "oid1"
    assert res["effective_date"] == "2022-04-21"
    assert res["retired_date"] == "2022-04-21"
    assert res["description"] == "description1"
    assert res["display_in_tree"] is True
    assert res["forms"] == []
    assert res["possible_actions"] == ["delete", "reactivate"]


def test_cannot_add_odm_forms_to_an_odm_study_event_that_is_in_retired_status(
    api_client,
):
    data = [
        {
            "uid": "odm_form1",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "No",
            "collection_exception_condition_oid": "None",
        }
    ]
    response = api_client.post(
        "odms/study-events/OdmStudyEvent_000001/forms", json=data
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "ODM element is not in Draft."
