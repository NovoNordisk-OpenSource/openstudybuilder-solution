"""
Tests for projects endpoints
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
from clinical_mdr_api.models.projects.project import Project
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import (
    assert_response_status_code,
    parse_json_response,
)

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
projects: list[Project]
clinical_programme: ClinicalProgramme

URL = "projects"


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

    global projects
    global clinical_programme

    # Create some projects
    projects = []

    clinical_programme = TestUtils.create_clinical_programme("CP")

    for _ in range(20):
        projects.append(
            TestUtils.create_project(
                name=f"Project Name {_}",
                project_number=f"Project Number {_}",
                description=f"Project Description {_}",
                clinical_programme_uid=clinical_programme.uid,
            )
        )

    yield


PROJECT_FIELDS_ALL = [
    "uid",
    "name",
    "project_number",
    "description",
    "clinical_programme",
]

PROJECT_FIELDS_NOT_NULL = [
    "uid",
    "name",
    "project_number",
    "clinical_programme",
]


def test_get_project(api_client):
    response = api_client.get(f"{URL}/{projects[0].uid}")
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["uid"] == projects[0].uid
    assert res["name"] == projects[0].name
    assert res["project_number"] == projects[0].project_number
    assert res["description"] == projects[0].description
    assert res["clinical_programme"]["uid"] == projects[0].clinical_programme.uid
    assert res["clinical_programme"]["name"] == projects[0].clinical_programme.name


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
    for project in projects:
        value = getattr(project, field_name)
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


def test_create_project(api_client):
    data = {
        "name": " Test Project ",
        "project_number": "Hello ",
        "description": "Desc",
        "clinical_programme_uid": clinical_programme.uid,
    }
    response = api_client.post(URL, json=data)
    res = response.json()
    log.info("Created Project: %s", res)

    assert_response_status_code(response, 201)
    assert res["uid"]
    assert res["name"] == data["name"].strip()
    assert res["project_number"] == data["project_number"].strip().upper()
    assert res["description"] == data["description"]
    assert res["clinical_programme"]["uid"] == clinical_programme.uid
    assert res["clinical_programme"]["name"] == clinical_programme.name


def test_update_project(api_client):
    _clinical_programme = TestUtils.create_clinical_programme("Test CP")

    data = {
        "name": "Updated Name",
        "description": "Updated Desc",
        "clinical_programme_uid": _clinical_programme.uid,
    }
    response = api_client.patch(f"{URL}/{projects[0].uid}", json=data)
    res = response.json()
    log.info("Updated Project: %s", res)

    assert_response_status_code(response, 200)
    assert res["uid"] == projects[0].uid
    assert res["name"] == data["name"]
    assert res["project_number"] == projects[0].project_number
    assert res["description"] == data["description"]
    assert res["clinical_programme"]["uid"] == _clinical_programme.uid
    assert res["clinical_programme"]["name"] == _clinical_programme.name


def test_delete_project(api_client):
    response = api_client.delete(f"{URL}/{projects[0].uid}")
    log.info("Deleted Project: %s", projects[0].uid)

    assert_response_status_code(response, 204)


def test_cannot_create_project_with_already_existing_project_number(api_client):
    data = {
        "name": "Test Project",
        "project_number": "Abc-123",
        "description": "Desc",
        "clinical_programme_uid": clinical_programme.uid,
    }
    response = api_client.post(URL, json=data)
    assert_response_status_code(response, 201)

    data["name"] = f" {data['name'].lower()}"

    response = api_client.post(URL, json=data)
    res = parse_json_response(response, assert_status=409)
    assert res["message"] == "Project with Project Number 'ABC-123' already exists."


def test_cannot_update_project_used_by_projects(api_client):
    TestUtils.create_study(project_number=projects[2].project_number)
    data = {
        "name": "Not updatable",
        "description": "Not updatable",
        "clinical_programme_uid": clinical_programme.uid,
    }
    response = api_client.patch(f"{URL}/{projects[2].uid}", json=data)
    res = response.json()
    log.info("Didn't update Project: %s", res)

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == f"Cannot update Project with UID '{projects[2].uid}' because it is used by studies."
    )


def test_cannot_delete_project_used_by_projects(api_client):
    response = api_client.delete(f"{URL}/{projects[2].uid}")
    res = response.json()
    log.info("Deleted Project: %s", projects[2].uid)

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == f"Cannot delete Project with UID '{projects[2].uid}' because it is used by studies."
    )
