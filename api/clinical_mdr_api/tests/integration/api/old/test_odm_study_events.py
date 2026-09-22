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
    inject_and_clear_db("old.json.test.odm.study.events")
    db.cypher_query(STARTUP_ODM_FORMS)

    yield

    drop_db("old.json.test.odm.study.events")


def test_getting_empty_list_of_odm_study_events(api_client):
    response = api_client.get("odms/study-events")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_creating_a_new_odm_study_event(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "oid1",
        "effective_date": "2022-04-21",
        "retired_date": "2022-04-21",
        "description": "description1",
        "display_in_tree": False,
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
    assert res["display_in_tree"] is False
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["forms"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_non_empty_list_of_odm_study_events(api_client):
    response = api_client.get("odms/study-events")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "OdmStudyEvent_000001"
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["name"] == "name1"
    assert res["items"][0]["oid"] == "oid1"
    assert res["items"][0]["effective_date"] == "2022-04-21"
    assert res["items"][0]["retired_date"] == "2022-04-21"
    assert res["items"][0]["description"] == "description1"
    assert res["items"][0]["display_in_tree"] is False
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] == "Draft"
    assert res["items"][0]["version"] == "0.1"
    assert res["items"][0]["change_description"] == "Initial version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["forms"] == []
    assert res["items"][0]["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_possible_header_values_of_odm_study_events(api_client):
    response = api_client.get("odms/study-events/headers?field_name=name")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == ["name1"]


def test_getting_a_specific_odm_study_event(api_client):
    response = api_client.get("odms/study-events/OdmStudyEvent_000001")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["effective_date"] == "2022-04-21"
    assert res["retired_date"] == "2022-04-21"
    assert res["description"] == "description1"
    assert res["display_in_tree"] is False
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["forms"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_versions_of_a_specific_odm_study_event(api_client):
    response = api_client.get("odms/study-events/OdmStudyEvent_000001/versions")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["uid"] == "OdmStudyEvent_000001"
    assert res[0]["library_name"] == "Sponsor"
    assert res[0]["name"] == "name1"
    assert res[0]["oid"] == "oid1"
    assert res[0]["effective_date"] == "2022-04-21"
    assert res[0]["retired_date"] == "2022-04-21"
    assert res[0]["description"] == "description1"
    assert res[0]["display_in_tree"] is False
    assert res[0]["end_date"] is None
    assert res[0]["status"] == "Draft"
    assert res[0]["version"] == "0.1"
    assert res[0]["change_description"] == "Initial version"
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["forms"] == []
    assert res[0]["possible_actions"] == ["approve", "delete", "edit"]


def test_updating_an_existing_odm_study_event(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1",
        "oid": "new oid1",
        "effective_date": "2022-04-21",
        "retired_date": "2022-04-21",
        "display_in_tree": True,
        "change_description": "oid and display_in_tree changed",
    }
    response = api_client.patch("odms/study-events/OdmStudyEvent_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "new oid1"
    assert res["effective_date"] == "2022-04-21"
    assert res["retired_date"] == "2022-04-21"
    assert res["description"] == "description1"
    assert res["display_in_tree"] is True
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["change_description"] == "oid and display_in_tree changed"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["forms"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_getting_a_specific_odm_study_event_in_specific_version(api_client):
    response = api_client.get("odms/study-events/OdmStudyEvent_000001?version=0.1")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "oid1"
    assert res["effective_date"] == "2022-04-21"
    assert res["retired_date"] == "2022-04-21"
    assert res["description"] == "description1"
    assert res["display_in_tree"] is False
    assert res["end_date"]
    assert res["status"] == "Draft"
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["forms"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_adding_odm_forms_to_a_specific_odm_study_event(api_client):
    data = [
        {
            "uid": "odm_form1",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "Yes",
            "collection_exception_condition_oid": "None",
        }
    ]
    response = api_client.post(
        "odms/study-events/OdmStudyEvent_000001/forms", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "new oid1"
    assert res["effective_date"] == "2022-04-21"
    assert res["retired_date"] == "2022-04-21"
    assert res["description"] == "description1"
    assert res["display_in_tree"] is True
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["change_description"] == "oid and display_in_tree changed"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["forms"] == [
        {
            "uid": "odm_form1",
            "oid": "oid1",
            "name": "name1",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "Yes",
            "collection_exception_condition_oid": "None",
        }
    ]
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_overriding_odm_forms_from_a_specific_odm_study_event(api_client):
    data = [
        {
            "uid": "odm_form2",
            "order_number": 2,  # this order number should be overridden by the API to 1, since it's the only form in the request
            "mandatory": "Yes",
            "locked": "Yes",
            "collection_exception_condition_oid": "None",
        },
    ]
    response = api_client.post(
        "odms/study-events/OdmStudyEvent_000001/forms?override=true", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "new oid1"
    assert res["effective_date"] == "2022-04-21"
    assert res["retired_date"] == "2022-04-21"
    assert res["description"] == "description1"
    assert res["display_in_tree"] is True
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["change_description"] == "oid and display_in_tree changed"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["forms"] == [
        {
            "uid": "odm_form2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "Yes",
            "collection_exception_condition_oid": "None",
        }
    ]
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_approving_an_odm_study_event(api_client):
    response = api_client.post("odms/study-events/OdmStudyEvent_000001/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "new oid1"
    assert res["effective_date"] == "2022-04-21"
    assert res["retired_date"] == "2022-04-21"
    assert res["description"] == "description1"
    assert res["display_in_tree"] is True
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["forms"] == [
        {
            "uid": "odm_form2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "Yes",
            "collection_exception_condition_oid": "None",
        }
    ]
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_inactivating_a_specific_odm_study_event(api_client):
    response = api_client.delete("odms/study-events/OdmStudyEvent_000001/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "new oid1"
    assert res["effective_date"] == "2022-04-21"
    assert res["retired_date"] == "2022-04-21"
    assert res["description"] == "description1"
    assert res["display_in_tree"] is True
    assert res["end_date"] is None
    assert res["status"] == "Retired"
    assert res["version"] == "2.0"
    assert res["change_description"] == "Inactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["forms"] == [
        {
            "uid": "odm_form2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "Yes",
            "collection_exception_condition_oid": "None",
        }
    ]
    assert res["possible_actions"] == ["delete", "reactivate"]


def test_reactivating_a_specific_odm_study_event(api_client):
    response = api_client.post("odms/study-events/OdmStudyEvent_000001/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "new oid1"
    assert res["effective_date"] == "2022-04-21"
    assert res["retired_date"] == "2022-04-21"
    assert res["description"] == "description1"
    assert res["display_in_tree"] is True
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "3.0"
    assert res["change_description"] == "Reactivated version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["forms"] == [
        {
            "uid": "odm_form2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "Yes",
            "collection_exception_condition_oid": "None",
        }
    ]
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_getting_minimal_response_for_study_event(api_client):
    response = api_client.get(
        "odms/study-events/OdmStudyEvent_000001?fields=oid,name,effective_date,retired_date,description,display_in_tree,forms"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["name"] == "name1"
    assert res["oid"] == "new oid1"
    assert res["effective_date"] == "2022-04-21"
    assert res["retired_date"] == "2022-04-21"
    assert res["description"] == "description1"
    assert res["display_in_tree"] is True
    assert res["forms"] == [
        {
            "uid": "odm_form2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "Yes",
            "collection_exception_condition_oid": "None",
        }
    ]


def test_creating_a_new_odm_study_event_version(api_client):
    response = api_client.post("odms/study-events/OdmStudyEvent_000001/versions")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmStudyEvent_000001"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1"
    assert res["oid"] == "new oid1"
    assert res["effective_date"] == "2022-04-21"
    assert res["retired_date"] == "2022-04-21"
    assert res["description"] == "description1"
    assert res["display_in_tree"] is True
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "3.1"
    assert res["change_description"] == "New draft created"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["forms"] == [
        {
            "uid": "odm_form2",
            "oid": "oid2",
            "name": "name2",
            "version": "1.0",
            "order_number": 1,
            "mandatory": "Yes",
            "locked": "Yes",
            "collection_exception_condition_oid": "None",
        }
    ]
    assert res["possible_actions"] == ["approve", "edit"]


def test_create_a_new_odm_study_event_for_deleting_it(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "name1 - delete",
        "oid": "oid1",
        "effective_date": "2022-04-21",
        "retired_date": "2022-04-21",
        "description": "description1",
    }
    response = api_client.post("odms/study-events", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "OdmStudyEvent_000002"
    assert res["library_name"] == "Sponsor"
    assert res["name"] == "name1 - delete"
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


def test_deleting_a_specific_odm_study_event(api_client):
    response = api_client.delete("odms/study-events/OdmStudyEvent_000002")

    assert_response_status_code(response, 204)


def test_getting_uids_of_a_specific_odm_study_events_active_relationships(api_client):
    response = api_client.get("odms/study-events/OdmStudyEvent_000001/relationships")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {}
