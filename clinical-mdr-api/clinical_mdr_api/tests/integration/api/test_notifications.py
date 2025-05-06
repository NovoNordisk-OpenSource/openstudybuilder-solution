"""
Tests for /notifications* endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments
# import json
import logging

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.notification import Notification
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
notifications: list[Notification]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "notifications.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global notifications

    notifications = []

    for index in range(10):
        notifications.append(
            TestUtils.create_notification(
                title=f"Notification {index}",
                description=f"Description {index}",
                published=index % 2 == 0,
            )
        )

    yield


NOTIFICATION_ALL = [
    "sn",
    "title",
    "notification_type",
    "description",
    "started_at",
    "ended_at",
    "published_at",
]
NOTIFICATION_NOT_NULL = [
    "sn",
    "title",
    "notification_type",
]


def test_get_all_notifications(api_client):
    response = api_client.get("/notifications")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) == 10

    for item in res:
        for x in NOTIFICATION_NOT_NULL:
            assert item[x] is not None


def test_get_all_active_notifications(api_client):
    response = api_client.get("system/notifications")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) == 5


def test_get_notification(api_client):
    response = api_client.get(f"/notifications/{notifications[0].sn}")

    assert_response_status_code(response, 200)


def test_create_notification(api_client):
    data = {
        "title": "Title",
        "notification_type": "warning",
        "description": "Description",
        "started_at": "2024-02-20T00:00:00Z",
        "ended_at": "2028-02-20T00:00:00Z",
        "published": True,
    }
    response = api_client.post("/notifications", json=data)

    assert_response_status_code(response, 201)
    res = response.json()
    assert res["sn"]
    assert res["title"] == data["title"]
    assert res["notification_type"] == data["notification_type"]
    assert res["description"] == data["description"]
    assert res["started_at"] == data["started_at"]
    assert res["ended_at"] == data["ended_at"]
    assert res["published_at"]


def test_update_notification(api_client):
    data = {
        "title": "updated Title",
        "notification_type": "warning",
        "description": "updated Description",
        "started_at": None,
        "ended_at": None,
        "published": False,
    }
    response = api_client.patch("/notifications/11", json=data)

    assert_response_status_code(response, 200)
    res = response.json()
    assert res["sn"] == 11
    assert res["title"] == data["title"]
    assert res["notification_type"] == data["notification_type"]
    assert res["description"] == data["description"]
    assert res["started_at"] == data["started_at"]
    assert res["ended_at"] == data["ended_at"]
    assert res["published_at"] is None


def test_delete_notification(api_client):
    response = api_client.delete(f"/notifications/{notifications[0].sn}")
    assert_response_status_code(response, 204)

    response = api_client.get(f"/notifications/{notifications[0].sn}")
    assert_response_status_code(response, 404)
    res = response.json()

    assert (
        res["message"]
        == f"Notification with Serial Number '{notifications[0].sn}' doesn't exist."
    )


def validate_serial_number_against_neo4j_max_and_min_int(api_client):
    serial_number = 9223372036854775808
    max_int = 9223372036854775807
    min_int = -9223372036854775807

    # Test positive integer
    response = api_client.get(f"/notifications/{serial_number}")
    assert_response_status_code(response, 400)
    assert (
        response.json()["message"]
        == f"Serial Number must not be greater than '{max_int}' and less than '{min_int}'."
    )

    response = api_client.patch(
        f"/notifications/{serial_number}",
        json={
            "title": "Title",
            "notification_type": "warning",
            "description": "Description",
            "started_at": None,
            "ended_at": None,
            "published": False,
        },
    )
    assert_response_status_code(response, 400)
    assert (
        response.json()["message"]
        == f"Serial Number must not be greater than '{max_int}' and less than '{min_int}'."
    )

    response = api_client.delete(f"/notifications/{serial_number}")
    assert_response_status_code(response, 400)
    assert (
        response.json()["message"]
        == f"Serial Number must not be greater than '{max_int}' and less than '{min_int}'."
    )

    # Test negative integer
    response = api_client.get(f"/notifications/-{serial_number}")
    assert_response_status_code(response, 400)
    assert (
        response.json()["message"]
        == f"Serial Number must not be greater than '{max_int}' and less than '{min_int}'."
    )

    response = api_client.patch(
        f"/notifications/-{serial_number}",
        json={
            "title": "Title",
            "notification_type": "warning",
            "description": "Description",
            "started_at": None,
            "ended_at": None,
            "published": False,
        },
    )
    assert_response_status_code(response, 400)
    assert (
        response.json()["message"]
        == f"Serial Number must not be greater than '{max_int}' and less than '{min_int}'."
    )

    response = api_client.delete(f"/notifications/-{serial_number}")
    assert_response_status_code(response, 400)
    assert (
        response.json()["message"]
        == f"Serial Number must not be greater than '{max_int}' and less than '{min_int}'."
    )
