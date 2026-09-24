"""
Tests for /data-completeness-tags* and /studies/{study_uid}/data-completeness-tags* endpoints
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
from clinical_mdr_api.models.data_completeness_tag import DataCompletenessTag
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
data_completeness_tags: list[DataCompletenessTag]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "datacompletenesstags.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global data_completeness_tags

    data_completeness_tags = []
    for index in range(10):
        data_completeness_tags.append(
            TestUtils.create_data_completeness_tag(
                name=f"Data Completeness Tag {index}",
            )
        )

    yield


DATA_COMPLETENESS_TAG_FIELDS = [
    "uid",
    "name",
]


def test_get_all_data_completeness_tags(api_client):
    response = api_client.get("/data-completeness-tags")
    assert_response_status_code(response, 200)
    res = response.json()

    assert len(res) >= 10
    uids = [item["uid"] for item in res]
    for tag in data_completeness_tags:
        assert tag.uid in uids

    for item in res:
        for field in DATA_COMPLETENESS_TAG_FIELDS:
            assert item[field] is not None


def test_create_data_completeness_tag(api_client):
    data = {"name": "Create Test Tag"}
    response = api_client.post("/data-completeness-tags", json=data)

    assert_response_status_code(response, 201)
    res = response.json()
    assert res["uid"]
    assert res["name"] == data["name"]

    # Cleanup
    api_client.delete(f"/data-completeness-tags/{res['uid']}")


def test_update_data_completeness_tag(api_client):
    tag = data_completeness_tags[1]
    original_name = tag.name
    data = {"name": "Updated Tag Name"}
    response = api_client.put(f"/data-completeness-tags/{tag.uid}", json=data)

    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == tag.uid
    assert res["name"] == data["name"]

    # Restore original name
    api_client.put(f"/data-completeness-tags/{tag.uid}", json={"name": original_name})


def test_delete_data_completeness_tag(api_client):
    # Setup: create a dedicated tag for deletion
    tag = TestUtils.create_data_completeness_tag(name="To Be Deleted")

    response = api_client.delete(f"/data-completeness-tags/{tag.uid}")
    assert_response_status_code(response, 204)

    # Verify it was deleted
    response = api_client.get("/data-completeness-tags")
    assert_response_status_code(response, 200)
    uids = [item["uid"] for item in response.json()]
    assert tag.uid not in uids


def test_cannot_create_data_completeness_tag_with_existing_name(api_client):
    response = api_client.post(
        "/data-completeness-tags",
        json={"name": data_completeness_tags[0].name},
    )

    assert_response_status_code(response, 409)
    res = response.json()
    assert (
        res["message"]
        == f"Data Completeness Tag with Name '{data_completeness_tags[0].name}' already exists."
    )


def test_update_nonexistent_data_completeness_tag(api_client):
    data = {"name": "Does Not Matter"}
    response = api_client.put("/data-completeness-tags/nonexistent-uid", json=data)

    assert_response_status_code(response, 404)
    res = response.json()
    assert (
        res["message"]
        == "Data Completeness Tag with UID 'nonexistent-uid' doesn't exist."
    )


# --- Study-level data completeness tag tests ---


def test_get_study_data_completeness_tags_empty(api_client):
    study = TestUtils.create_study()
    response = api_client.get(f"/studies/{study.uid}/data-completeness-tags")

    assert_response_status_code(response, 200)
    res = response.json()
    assert res == []


def test_assign_data_completeness_tag_to_study(api_client):
    study = TestUtils.create_study()
    tag = data_completeness_tags[2]

    response = api_client.post(
        f"/studies/{study.uid}/data-completeness-tags",
        json={"uid": tag.uid},
    )

    assert_response_status_code(response, 201)
    res = response.json()
    assert res["uid"] == tag.uid
    assert res["name"] == tag.name


def test_assign_multiple_tags_and_list(api_client):
    study = TestUtils.create_study()
    tag1 = data_completeness_tags[4]
    tag2 = data_completeness_tags[5]

    api_client.post(
        f"/studies/{study.uid}/data-completeness-tags", json={"uid": tag1.uid}
    )
    api_client.post(
        f"/studies/{study.uid}/data-completeness-tags", json={"uid": tag2.uid}
    )

    # Verify both tags are returned
    response = api_client.get(f"/studies/{study.uid}/data-completeness-tags")
    assert_response_status_code(response, 200)
    res = response.json()
    uids = {item["uid"] for item in res}
    assert tag1.uid in uids
    assert tag2.uid in uids


def test_remove_data_completeness_tag_from_study(api_client):
    study = TestUtils.create_study()
    tag1 = data_completeness_tags[6]
    tag2 = data_completeness_tags[7]

    api_client.post(
        f"/studies/{study.uid}/data-completeness-tags", json={"uid": tag1.uid}
    )
    api_client.post(
        f"/studies/{study.uid}/data-completeness-tags", json={"uid": tag2.uid}
    )

    # Remove tag2
    response = api_client.delete(
        f"/studies/{study.uid}/data-completeness-tags/{tag2.uid}"
    )
    assert_response_status_code(response, 204)

    # Verify only tag1 remains
    response = api_client.get(f"/studies/{study.uid}/data-completeness-tags")
    assert_response_status_code(response, 200)
    uids = {item["uid"] for item in response.json()}
    assert tag1.uid in uids
    assert tag2.uid not in uids


def test_studies_list_returns_data_completeness_tags(api_client):
    """Verify that /studies/list returns data_completeness_tags for each study."""
    study = TestUtils.create_study()
    tag = data_completeness_tags[8]
    api_client.post(
        f"/studies/{study.uid}/data-completeness-tags", json={"uid": tag.uid}
    )

    response = api_client.get("/studies/list?minimal_response=false")
    assert_response_status_code(response, 200)
    res = response.json()

    # Find our study in the list
    study_item = next((s for s in res if s["uid"] == study.uid), None)
    assert study_item is not None, f"Study {study.uid} not found in /studies/list"

    assert "data_completeness_tags" in study_item
    assert isinstance(study_item["data_completeness_tags"], list)
    assert tag.name in study_item["data_completeness_tags"]
