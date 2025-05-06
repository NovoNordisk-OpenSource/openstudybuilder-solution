"""
Tests for /admin/* endpoints
"""

import logging

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


log = logging.getLogger(__name__)


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
    user_id = "unknown-user"
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
