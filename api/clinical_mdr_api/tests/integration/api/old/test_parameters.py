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
    inject_and_clear_db("old.json.test.parameters")

    yield

    drop_db("old.json.test.parameters")


def test_random_test_name_89(api_client):
    data = {"is_editable": True, "name": "Test library"}
    response = api_client.post("/libraries", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["is_editable"] is True
    assert res["name"] == "Test library"


def test_random_test_name_21(api_client):
    response = api_client.get("/libraries")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["is_editable"] is True
    assert res[0]["name"] == "Test library"


def test_random_test_name_66(api_client):
    data = {"is_editable": False, "name": "Test library1"}
    response = api_client.post("/libraries", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["is_editable"] is False
    assert res["name"] == "Test library1"


def test_random_test_name_3(api_client):
    response = api_client.get("/libraries")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["is_editable"] is True
    assert res[0]["name"] == "Test library"
    assert res[1]["is_editable"] is False
    assert res[1]["name"] == "Test library1"
