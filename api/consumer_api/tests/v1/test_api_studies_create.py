# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.tests.integration.utils.api import inject_base_data
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from consumer_api.consumer_api import app
from consumer_api.tests.utils import assert_response_status_code, set_db

BASE_URL = "/v1"

STUDY_CREATE_RESPONSE_FIELDS_ALL = [
    "uid",
    "id",
    "acronym",
    "description",
]

STUDY_CREATE_RESPONSE_FIELDS_NOT_NULL = STUDY_CREATE_RESPONSE_FIELDS_ALL

PROJECT_ID = "ABC-1"

# Study numbers used by the tests, kept apart so that they cannot collide with
# each other or with studies created by the fixtures.
_study_number_counter = 1000


def _next_study_number() -> str:
    global _study_number_counter  # pylint: disable=global-statement
    _study_number_counter += 1
    return str(_study_number_counter)


@pytest.fixture(scope="module")
def studies_create_setup() -> dict[str, Any]:
    db_name = "consumer-api-v1-studies-create"
    set_db(db_name)

    # Study creation needs the CTConfig nodes and the libraries/codelists that
    # the base data injection sets up, not just a project to hang the study off.
    study, test_data_dict = inject_base_data()

    project = TestUtils.create_project(
        name="Project ABC",
        project_number=PROJECT_ID,
        description="Base project",
        clinical_programme_uid=test_data_dict["clinical_programme"].uid,
    )

    return {
        "project_id": project.project_number,
        "base_study_uid": study.uid,
    }


@pytest.fixture(scope="module")
def api_client(studies_create_setup):
    yield TestClient(app)


def _build_study_payload(**overrides) -> dict[str, Any]:
    """Returns a valid `POST /v1/studies` payload, with `overrides` applied.

    A key mapped to `None` in `overrides` is sent as an explicit `null`; use
    `_without()` to leave a key out of the payload entirely.
    """
    payload: dict[str, Any] = {
        "study_number": _next_study_number(),
        "study_acronym": TestUtils.random_str(prefix="acronym-"),
        "project_id": PROJECT_ID,
        "description": "Study description",
    }
    payload.update(overrides)
    return payload


def _without(payload: dict[str, Any], *keys: str) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key not in keys}


def test_create_study(api_client):
    payload = _build_study_payload()

    response = api_client.post(f"{BASE_URL}/studies", json=payload)
    assert_response_status_code(response, 201)
    res = response.json()

    TestUtils.assert_response_shape_ok(
        res, STUDY_CREATE_RESPONSE_FIELDS_ALL, STUDY_CREATE_RESPONSE_FIELDS_NOT_NULL
    )

    assert res["acronym"] == payload["study_acronym"]
    assert res["description"] == payload["description"]
    # The study ID is derived by the server, it cannot be supplied by the caller
    assert res["id"] == f"{PROJECT_ID}-{payload['study_number']}"


def test_create_study_with_study_number_only(api_client):
    payload = _without(_build_study_payload(), "study_acronym", "description")

    response = api_client.post(f"{BASE_URL}/studies", json=payload)
    assert_response_status_code(response, 201)
    res = response.json()

    assert res["acronym"] is None
    assert res["id"] == f"{PROJECT_ID}-{payload['study_number']}"


def test_create_study_with_study_acronym_only(api_client):
    payload = _without(_build_study_payload(), "study_number", "description")

    response = api_client.post(f"{BASE_URL}/studies", json=payload)
    assert_response_status_code(response, 201)
    res = response.json()

    assert res["acronym"] == payload["study_acronym"]
    # Without a study number the ID is the project ID prefix and an empty
    # number part, which is what GET /studies returns for the same study
    assert res["id"] == f"{PROJECT_ID}-"


def test_create_study_with_lowercase_project_id(api_client):
    """`project_id` is matched exactly, so casing must match the stored project."""
    payload = _build_study_payload(project_id=PROJECT_ID.lower())

    response = api_client.post(f"{BASE_URL}/studies", json=payload)
    assert_response_status_code(response, 400)
    message = response.json()["message"]
    assert PROJECT_ID.lower() in message
    # The error must point the caller at where valid values can be found
    assert "GET /v1/library/projects" in message


def test_create_study_without_study_number_and_study_acronym(api_client):
    payload = _without(_build_study_payload(), "study_number", "study_acronym")

    response = api_client.post(f"{BASE_URL}/studies", json=payload)
    assert_response_status_code(response, 400)
    assert (
        "At least one of 'study_number' and 'study_acronym' must be provided"
        in response.json()["details"][0]["msg"]
    )


@pytest.mark.parametrize(
    "study_number",
    ["12345", "abc", "12a", "", " 123", "-1"],
)
def test_create_study_with_invalid_study_number(api_client, study_number):
    payload = _build_study_payload(study_number=study_number)

    response = api_client.post(f"{BASE_URL}/studies", json=payload)
    assert_response_status_code(response, 400)
    assert response.json()["details"][0]["error_code"] == "string_pattern_mismatch"


def test_create_study_with_unknown_project_id(api_client):
    payload = _build_study_payload(project_id="NON-EXISTENT")

    response = api_client.post(f"{BASE_URL}/studies", json=payload)
    assert_response_status_code(response, 400)
    message = response.json()["message"]
    assert "NON-EXISTENT" in message
    # The error must point the caller at where valid values can be found
    assert "GET /v1/library/projects" in message


def test_create_study_without_project_id(api_client):
    payload = _without(_build_study_payload(), "project_id")

    response = api_client.post(f"{BASE_URL}/studies", json=payload)
    assert_response_status_code(response, 400)
    assert response.json()["details"][0]["error_code"] == "missing"


def test_create_study_with_unknown_field(api_client):
    """Unknown fields are rejected rather than silently ignored.

    A typo in a field name would otherwise create a study missing the value the
    caller believed they had sent.
    """
    payload = _build_study_payload(study_acronyms="typo")

    response = api_client.post(f"{BASE_URL}/studies", json=payload)
    assert_response_status_code(response, 400)
    assert response.json()["details"][0]["error_code"] == "extra_forbidden"


def test_create_study_with_duplicate_study_number(api_client):
    payload = _build_study_payload()

    response = api_client.post(f"{BASE_URL}/studies", json=payload)
    assert_response_status_code(response, 201)

    duplicate = _build_study_payload(study_number=payload["study_number"])
    response = api_client.post(f"{BASE_URL}/studies", json=duplicate)
    assert_response_status_code(response, 409)
    assert payload["study_number"] in response.json()["message"]


def test_create_study_with_duplicate_study_acronym(api_client):
    payload = _build_study_payload()

    response = api_client.post(f"{BASE_URL}/studies", json=payload)
    assert_response_status_code(response, 201)

    duplicate = _build_study_payload(study_acronym=payload["study_acronym"])
    response = api_client.post(f"{BASE_URL}/studies", json=duplicate)
    assert_response_status_code(response, 409)
    assert payload["study_acronym"] in response.json()["message"]


def test_created_study_is_returned_by_get_studies(api_client):
    payload = _build_study_payload()

    response = api_client.post(f"{BASE_URL}/studies", json=payload)
    assert_response_status_code(response, 201)
    created = response.json()
    study_uid = created["uid"]

    response = api_client.get(f"{BASE_URL}/studies?page_size=100")
    assert_response_status_code(response, 200)
    res = response.json()

    study = next((item for item in res["items"] if item["uid"] == study_uid), None)
    assert study is not None, f"Study {study_uid} not found in GET /studies response"
    assert study["number"] == payload["study_number"]
    assert study["acronym"] == payload["study_acronym"]
    # A study must be identified the same way regardless of which endpoint
    # returned it
    assert study["id"] == created["id"]
