"""
Tests for /admin/* endpoints
"""

import logging
import random

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


log = logging.getLogger(__name__)

COMPLEXITY_BURDEN_FIELDS = [
    "burden_id",
    "name",
    "description",
    "site_burden",
    "patient_burden",
    "median_cost_usd",
]
COMPLEXITY_BURDEN_FIELDS_NOT_NULL = [
    "burden_id",
    "name",
    "description",
    "site_burden",
    "patient_burden",
]

COMPLEXITY_ACTIVITY_BURDEN_FIELDS = [
    "activity_subgroup_uid",
    "activity_subgroup_name",
    "burden_id",
    "site_burden",
    "patient_burden",
    "median_cost_usd",
]
COMPLEXITY_ACTIVITY_BURDEN_FIELDS_NOT_NULL = [
    "activity_subgroup_uid",
    "activity_subgroup_name",
]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "admin.api"
    inject_and_clear_db(db_name)
    inject_base_data()


def test_get_caches(api_client):
    """Test GET /admin/caches"""

    # Make a request that will populate one cache
    api_client.get("/clinical-programmes/ClinicalProgramme_000001")

    response = api_client.get("/admin/caches?show_items=true")
    assert_response_status_code(response, 200)
    assert len(response.json()) > 1

    all_store_classes = [item["class"] for item in response.json()]
    assert (
        "<class 'clinical_mdr_api.domain_repositories.clinical_programmes.clinical_programme_repository.ClinicalProgrammeRepository'>"
        in all_store_classes
    )

    # Assert that the cache store 'cache_store_item_by_uid' is not empty
    for item in response.json():
        if "clinical_programme_repository.ClinicalProgrammeRepository" in item["class"]:
            all_cache_stores = [store["store_name"] for store in item["cache_stores"]]
            assert "cache_store_item_by_uid" in all_cache_stores

            for cache_store in item["cache_stores"]:
                if cache_store["store_name"] == "cache_store_item_by_uid":
                    assert cache_store["size"] == 1
                    break


def test_clear_caches(api_client):
    """Test DELETE /admin/caches"""
    response = api_client.delete("/admin/caches")
    assert_response_status_code(response, 200)
    assert len(response.json()) > 1

    response = api_client.get("/admin/caches?show_items=true")
    assert_response_status_code(response, 200)
    assert len(response.json()) > 1

    # Assert that the cache store 'cache_store_item_by_uid' is empty
    for item in response.json():
        if "clinical_programme_repository.ClinicalProgrammeRepository" in item["class"]:
            for cache_store in item["cache_stores"]:
                if cache_store["store_name"] == "cache_store_item_by_uid":
                    assert cache_store["size"] == 0
                    break


def test_get_users(api_client):
    """Test GET /admin/users"""
    response = api_client.get("/admin/users")
    assert_response_status_code(response, 200)
    assert len(response.json()) > 0
    assert response.json()[0]["user_id"] == "unknown-user"
    assert response.json()[0]["username"] == "unknown-user@example.com"


def test_patch_user(api_client):
    """Test PATCH /admin/users/{user_id}"""
    user_id = "test-user-" + str(random.randint(1000, 9999))
    TestUtils.create_dummy_user(user_id=user_id)
    new_username = "new_username"

    response = api_client.patch(
        f"/admin/users/{user_id}", json={"username": new_username}
    )
    assert_response_status_code(response, 200)
    assert response.json()["username"] == new_username

    response = api_client.get("/admin/users")
    assert_response_status_code(response, 200)
    for item in response.json():
        if item["user_id"] == user_id:
            assert item["username"] == new_username
            break

    # Revert username change - we have mysterious test isolation issues
    response = api_client.patch(
        f"/admin/users/{user_id}", json={"username": "unknown-user@example.com"}
    )
    assert_response_status_code(response, 200)
    assert response.json()["username"] == "unknown-user@example.com"


def test_complexity_score_post_burdens(api_client):
    """Test POST /admin/complexity-scores/burdens"""
    payload = {
        "burden_id": "B001",
        "name": "Test Burden",
        "description": "This is a test burden",
        "site_burden": 10.0,
        "patient_burden": 5.0,
        "median_cost_usd": 100.0,
    }
    response = api_client.post("/admin/complexity-scores/burdens", json=payload)
    assert_response_status_code(response, 201)
    assert response.json()["name"] == payload["name"]
    assert response.json()["description"] == payload["description"]
    assert response.json()["site_burden"] == payload["site_burden"]
    assert response.json()["patient_burden"] == payload["patient_burden"]
    assert response.json()["median_cost_usd"] == payload["median_cost_usd"]


def test_complexity_score_put_activity_burdens(api_client):
    """Test PUT /admin/complexity-scores/burdens/activity-burdens/{activity_subgroup_id}"""
    _activity_group = TestUtils.create_activity_group(
        name="Test Activity Group",
    )

    activity_subgroup = TestUtils.create_activity_subgroup(
        name="Test Activity Subgroup",
    )

    # Create a burden to be used in the activity burden mapping
    burden_payload = {
        "burden_id": f"B00-{random.randint(10,99999999)}",
        "name": "Test Burden",
        "description": "This is a test burden",
        "site_burden": 3.4,
        "patient_burden": 1.4,
        "median_cost_usd": 134.0,
    }
    response = api_client.post("/admin/complexity-scores/burdens", json=burden_payload)
    assert_response_status_code(response, 201)

    # Map the activity subgroup to the created burden
    payload = {
        "burden_id": burden_payload["burden_id"],
    }
    response = api_client.put(
        f"/admin/complexity-scores/burdens/activity-burdens/{activity_subgroup.uid}",
        json=payload,
    )
    assert_response_status_code(response, 200)
    assert response.json()["burden_id"] == payload["burden_id"]
    assert response.json()["site_burden"] == burden_payload["site_burden"]
    assert response.json()["patient_burden"] == burden_payload["patient_burden"]
    assert response.json()["median_cost_usd"] == burden_payload["median_cost_usd"]


def test_complexity_score_get_burdens(api_client):
    """Test GET /admin/complexity-scores/burdens"""

    response = api_client.get("/admin/complexity-scores/burdens")
    assert_response_status_code(response, 200)
    assert isinstance(response.json(), list)
    for item in response.json():
        TestUtils.assert_response_shape_ok(
            item,
            COMPLEXITY_BURDEN_FIELDS,
            COMPLEXITY_BURDEN_FIELDS_NOT_NULL,
        )


def test_complexity_score_get_activity_burdens(api_client):
    """Test GET /admin/complexity-scores/activity-burdens"""

    response = api_client.get("/admin/complexity-scores/activity-burdens")
    assert_response_status_code(response, 200)
    assert isinstance(response.json(), list)
    for item in response.json():
        TestUtils.assert_response_shape_ok(
            item,
            COMPLEXITY_ACTIVITY_BURDEN_FIELDS,
            COMPLEXITY_ACTIVITY_BURDEN_FIELDS_NOT_NULL,
        )
