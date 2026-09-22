"""
Tests for clinical_programmes endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.clinical_programmes.clinical_programme import (
    ClinicalProgramme,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
clinical_programmes: list[ClinicalProgramme]

URL = "clinical-programmes"


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    inject_and_clear_db(URL + ".api")
    inject_base_data()

    global clinical_programmes

    # Create some clinical programmes
    clinical_programmes = []

    for _ in range(20):
        clinical_programmes.append(TestUtils.create_clinical_programme(f"CP {_}"))

    yield


def test_get_clinical_programme(api_client):
    response = api_client.get(f"{URL}/{clinical_programmes[0].uid}")
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["uid"] == clinical_programmes[0].uid
    assert res["name"] == clinical_programmes[0].name


@pytest.mark.parametrize(
    "field_name",
    [
        pytest.param("name"),
    ],
)
def test_headers(api_client, field_name):
    response = api_client.get(f"{URL}/headers?field_name={field_name}&page_size=100")
    res = response.json()

    assert_response_status_code(response, 200)
    expected_result = []
    for clinical_programme in clinical_programmes:
        value = getattr(clinical_programme, field_name)
        if value:
            expected_result.append(value)
    log.info("Expected result is %s", expected_result)
    log.info("Returned %s", res)
    if expected_result:
        assert len(res) > 0
        assert len(set(expected_result)) + 1 == len(res)
        assert all(item in res for item in expected_result)
    else:
        assert len(res) == 0


def test_create_clinical_programme(api_client):
    data = {"name": "Test Clinical Programme"}
    response = api_client.post(URL, json=data)
    res = response.json()
    log.info("Created Clinical Programme: %s", res)

    assert_response_status_code(response, 201)
    assert res["uid"]
    assert res["name"] == data["name"]


def test_cannot_create_clinical_programme_with_case_insensitive_duplicate_name(
    api_client,
):
    response = api_client.post(URL, json={"name": "cp 0"})
    res = response.json()

    assert_response_status_code(response, 400)
    assert res["message"] == "Clinical Programme with name 'cp 0' already exists."


def test_cannot_update_clinical_programme_with_case_insensitive_duplicate_name(
    api_client,
):
    response = api_client.patch(
        f"{URL}/{clinical_programmes[1].uid}", json={"name": "cp 0"}
    )
    res = response.json()

    assert_response_status_code(response, 400)
    assert res["message"] == "Clinical Programme with name 'cp 0' already exists."


def test_update_clinical_programme(api_client):
    data = {"name": "Updated Name"}
    response = api_client.patch(f"{URL}/{clinical_programmes[0].uid}", json=data)
    res = response.json()
    log.info("Updated Clinical Programme: %s", res)

    assert_response_status_code(response, 200)
    assert res["uid"] == clinical_programmes[0].uid
    assert res["name"] == data["name"]


def test_delete_clinical_programme(api_client):
    response = api_client.delete(f"{URL}/{clinical_programmes[0].uid}")
    log.info("Deleted Clinical Programme: %s", clinical_programmes[0].uid)

    assert_response_status_code(response, 204)


def test_cannot_update_clinical_programme_used_by_projects(api_client):
    TestUtils.create_project(
        clinical_programme_uid=clinical_programmes[2].uid, project_number="321"
    )
    data = {"name": "Not updatable"}
    response = api_client.patch(f"{URL}/{clinical_programmes[2].uid}", json=data)
    res = response.json()
    log.info("Didn't update Clinical Programme: %s", res)

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == f"Cannot update Clinical Programme with UID '{clinical_programmes[2].uid}' because it is used by projects."
    )


def test_cannot_delete_clinical_programme_used_by_projects(api_client):
    response = api_client.delete(f"{URL}/{clinical_programmes[2].uid}")
    res = response.json()
    log.info("Deleted Clinical Programme: %s", clinical_programmes[2].uid)

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == f"Cannot delete Clinical Programme with UID '{clinical_programmes[2].uid}' because it is used by projects."
    )
