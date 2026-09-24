# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.models.projects.project import Project
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from common.config import settings
from consumer_api.consumer_api import app
from consumer_api.tests.utils import assert_response_status_code, set_db

BASE_URL = "/v1"

PROJECT_FIELDS_ALL = [
    "uid",
    "id",
    "name",
    "description",
    "clinical_programme",
]

PROJECT_FIELDS_NOT_NULL = [
    "uid",
    "id",
    "name",
    "clinical_programme",
]

CLINICAL_PROGRAMME_FIELDS_ALL = ["uid", "name"]

CLINICAL_PROGRAMME_NAME = "CP"

# Enough projects to exercise pagination with the default page size of 10
TOTAL_PROJECTS = 15

projects: list[Project] = []
clinical_programme_uid: str = ""


@pytest.fixture(scope="module")
def projects_setup() -> dict[str, Any]:
    db_name = "consumer-api-v1-projects"
    set_db(db_name)

    global clinical_programme_uid  # pylint: disable=global-statement
    TestUtils.create_dummy_user()
    clinical_programme = TestUtils.create_clinical_programme(
        name=CLINICAL_PROGRAMME_NAME
    )
    clinical_programme_uid = clinical_programme.uid

    # Created in descending project ID order, so that a response which happens
    # to be in insertion order cannot pass the sort order assertions.
    for idx in reversed(range(TOTAL_PROJECTS)):
        projects.append(
            TestUtils.create_project(
                name=f"Project {idx:02d}",
                project_number=f"PRJ-{idx:02d}",
                description=f"Description of project {idx:02d}",
                clinical_programme_uid=clinical_programme.uid,
            )
        )

    return {"clinical_programme_uid": clinical_programme.uid}


@pytest.fixture(scope="module")
def api_client(projects_setup):
    yield TestClient(app)


def test_get_projects(api_client):
    response = api_client.get(f"{BASE_URL}/library/projects?page_size=100")
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res, False)
    assert len(res["items"]) == TOTAL_PROJECTS

    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, PROJECT_FIELDS_ALL, PROJECT_FIELDS_NOT_NULL
        )
        TestUtils.assert_response_shape_ok(
            item["clinical_programme"],
            CLINICAL_PROGRAMME_FIELDS_ALL,
            CLINICAL_PROGRAMME_FIELDS_ALL,
        )
        assert item["clinical_programme"]["uid"] == clinical_programme_uid
        assert item["clinical_programme"]["name"] == CLINICAL_PROGRAMME_NAME

    for project in projects:
        item = next((item for item in res["items"] if item["uid"] == project.uid), None)
        assert item is not None, f"Project {project.uid} not found in response"
        assert item["id"] == project.project_number
        assert item["name"] == project.name
        assert item["description"] == project.description


def test_get_projects_pagination(api_client):
    # Default page size is 100, so all projects fit on the first page
    response = api_client.get(f"{BASE_URL}/library/projects")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == TOTAL_PROJECTS
    TestUtils.assert_sort_order(res["items"], "id", False)

    # Non-default page size
    response = api_client.get(f"{BASE_URL}/library/projects?page_size=2")
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 2
    TestUtils.assert_sort_order(res["items"], "id", False)

    # Non-default page number and page size
    response = api_client.get(f"{BASE_URL}/library/projects?page_size=3&page_number=2")
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 3
    TestUtils.assert_sort_order(res["items"], "id", False)


@pytest.mark.parametrize("page_size", [4, 10, 100])
def test_get_projects_all(api_client, page_size):
    """Paging through the whole list must yield every project exactly once."""
    fetched_uids: list[str] = []
    page_number = 1

    while True:
        response = api_client.get(
            f"{BASE_URL}/library/projects?page_size={page_size}&page_number={page_number}"
        )
        assert_response_status_code(response, 200)
        items = response.json()["items"]
        if not items:
            break
        fetched_uids.extend(item["uid"] for item in items)
        page_number += 1

    assert len(fetched_uids) == TOTAL_PROJECTS
    assert len(set(fetched_uids)) == TOTAL_PROJECTS
    assert set(fetched_uids) == {project.uid for project in projects}


def test_get_projects_sorted_by_ascending_id(api_client):
    """Sort order is fixed: ascending by `id`, not client selectable."""
    response = api_client.get(f"{BASE_URL}/library/projects?page_size=100")
    assert_response_status_code(response, 200)
    res = response.json()

    ids = [item["id"] for item in res["items"]]
    assert ids == sorted(ids)


def test_get_projects_invalid_pagination_params(api_client):
    response = api_client.get(f"{BASE_URL}/library/projects?page_size=0")
    assert_response_status_code(response, 400)
    assert (
        response.json()["details"][0]["msg"]
        == "Input should be greater than or equal to 1"
    )

    response = api_client.get(
        f"{BASE_URL}/library/projects?page_size={settings.max_page_size + 1}"
    )
    assert_response_status_code(response, 400)
    assert (
        response.json()["details"][0]["msg"]
        == "Input should be less than or equal to 1000"
    )

    response = api_client.get(
        f"{BASE_URL}/library/projects?page_number={settings.max_int_neo4j + 1}&page_size=1"
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == "The request failed due to validation errors"
    assert res["details"][0]["error_code"] == "less_than_equal"
