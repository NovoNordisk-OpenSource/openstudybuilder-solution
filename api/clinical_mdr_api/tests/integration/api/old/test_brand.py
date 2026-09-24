# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.brand")

    yield

    drop_db("old.json.test.brand")


def test_post_brand(api_client):
    data = {"name": "Brand A"}
    response = api_client.post("/brands", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Brand_000001"
    assert res["name"] == "Brand A"


def test_post_brand1(api_client):
    data = {"name": "Brand B"}
    response = api_client.post("/brands", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Brand_000002"
    assert res["name"] == "Brand B"


def test_post_brand_with_existing_name(api_client):
    data = {"name": "Brand A"}
    response = api_client.post("/brands", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Brand_000001"
    assert res["name"] == "Brand A"


def test_get_single_brand(api_client):
    response = api_client.get("/brands/Brand_000001")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "Brand_000001"
    assert res["name"] == "Brand A"


def test_get_all_brands(api_client):
    response = api_client.get("/brands")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["uid"] == "Brand_000001"
    assert res[0]["name"] == "Brand A"
    assert res[1]["uid"] == "Brand_000002"
    assert res[1]["name"] == "Brand B"


def test_delete_brand(api_client):
    response = api_client.delete("/brands/Brand_000002")

    assert_response_status_code(response, 204)


def test_get_just_deleted_brand(api_client):
    response = api_client.get("/brands/Brand_000002")

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert res["message"] == "Brand with UID 'Brand_000002' doesn't exist."
