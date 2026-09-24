# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_ACTIVITIES,
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_ACTIVITY_SUB_GROUPS,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.activity.group.negative")
    db.cypher_query(STARTUP_ACTIVITY_GROUPS)
    db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
    db.cypher_query(STARTUP_ACTIVITIES)

    yield

    drop_db("old.json.test.activity.group.negative")


def test_get_all_activity_sub_group_non_existent_library_passed(api_client):
    response = api_client.get(
        "/concepts/activities/activity-groups?library_name=non-existent"
    )

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert res["message"] == "Library with Name 'non-existent' doesn't exist."


def test_post_new_activity_group_name_already_exists(api_client):
    data = {
        "name": "name1",
        "name_sentence_case": "name1",
        "definition": "definition3",
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/activities/activity-groups", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == "Activity Group with Name 'name1' already exists."


def test_update_activity_group_name_already_exists(api_client):
    data = {
        "name": "name1",
        "name_sentence_case": "name1",
        "change_description": "Test change",
    }
    response = api_client.put(
        "/concepts/activities/activity-groups/activity_group_root2", json=data
    )

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == "Activity Group with Name 'name1' already exists."


def test_post_approve_non_draft_activity_group(api_client):
    response = api_client.post(
        "/concepts/activities/activity-groups/activity_group_root1/approvals"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."


def test_delete_accepted_object(api_client):
    response = api_client.delete(
        "/concepts/activities/activity-groups/activity_group_root1"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Object has been accepted"
