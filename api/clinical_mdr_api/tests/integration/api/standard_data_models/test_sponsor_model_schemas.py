"""
Tests for /standards/sponsor-models/schema endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name

import logging

import pytest
import yaml
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.standard_data_models.data_model import DataModel
from clinical_mdr_api.models.standard_data_models.data_model_ig import DataModelIG
from clinical_mdr_api.services.standard_data_models.sponsor_model_schema import (
    _SCHEMA_CACHE,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import (
    CDISC_LIBRARY_NAME,
    SPONSOR_LIBRARY_NAME,
    TestUtils,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

SCHEMA_URL = "/standards/sponsor-models/schema"

# A representative schema blob; the API treats it as an opaque string.
SCHEMA_V1 = "fields:\n  - name: STUDYID\n    transformer: identity\n"
SCHEMA_V1_DIFFERENT = "fields:\n  - name: STUDYID\n    transformer: uppercase\n"

data_model: DataModel
data_model_ig: DataModelIG


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client using the database set up in `test_data`."""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    inject_and_clear_db("sponsor-model-schemas.api")
    inject_base_data()

    global data_model
    global data_model_ig

    # The in-process schema cache is module-global; clear it so a previous
    # module's entries can't leak into this freshly-injected database.
    _SCHEMA_CACHE.clear()

    TestUtils.create_data_model_catalogue(name="DataModelCatalogueA")
    data_model = TestUtils.create_data_model(name="DataModelA")
    data_model_ig = TestUtils.create_data_model_ig(
        name="DataModelIGA", version_number="1", implemented_data_model=data_model.uid
    )
    yield


def test_publish_new_version_then_get(api_client):
    response = api_client.post(
        SCHEMA_URL, json={"schema_version": 1, "schema": SCHEMA_V1}
    )
    assert_response_status_code(response, 201)
    created = response.json()
    assert created["schema_version"] == 1
    # Stored as YAML, returned as parsed JSON.
    assert created["schema"] == yaml.safe_load(SCHEMA_V1)
    assert created["library_name"] == SPONSOR_LIBRARY_NAME
    assert created["content_hash"]

    # Retrievable via GET, returning the same immutable content.
    response = api_client.get(f"{SCHEMA_URL}/1")
    assert_response_status_code(response, 200)
    fetched = response.json()
    assert fetched["schema"] == yaml.safe_load(SCHEMA_V1)
    assert fetched["content_hash"] == created["content_hash"]


def test_republish_identical_is_noop(api_client):
    # One version exists before.
    before = api_client.get(SCHEMA_URL).json()
    assert len([s for s in before if s["schema_version"] == 1]) == 1

    response = api_client.post(
        SCHEMA_URL, json={"schema_version": 1, "schema": SCHEMA_V1}
    )
    # Identical re-publish is a 200 no-op, not a 201.
    assert_response_status_code(response, 200)

    # Still exactly one node for version 1 (no duplicate created).
    after = api_client.get(SCHEMA_URL).json()
    assert len([s for s in after if s["schema_version"] == 1]) == 1


def test_republish_different_content_conflicts(api_client):
    response = api_client.post(
        SCHEMA_URL, json={"schema_version": 1, "schema": SCHEMA_V1_DIFFERENT}
    )
    assert_response_status_code(response, 409)

    # The stored version is unchanged.
    fetched = api_client.get(f"{SCHEMA_URL}/1").json()
    assert fetched["schema"] == yaml.safe_load(SCHEMA_V1)


def test_get_nonexistent_version_returns_404(api_client):
    response = api_client.get(f"{SCHEMA_URL}/999")
    assert_response_status_code(response, 404)


def test_publish_invalid_yaml_returns_400(api_client):
    response = api_client.post(
        SCHEMA_URL,
        json={"schema_version": 2, "schema": "key: [unbalanced\n  nested: value"},
    )
    assert_response_status_code(response, 400)


def test_list_returns_metadata_without_blob(api_client):
    response = api_client.get(SCHEMA_URL)
    assert_response_status_code(response, 200)
    items = response.json()
    versions = {item["schema_version"] for item in items}
    assert 1 in versions
    for item in items:
        # The list is metadata-only; the blob is never included.
        assert "schema" not in item
        assert item["content_hash"]


@pytest.mark.parametrize("bad_version", [0, -1])
def test_publish_rejects_non_positive_version(api_client, bad_version):
    # schema_version has a ge=1 constraint. This app maps request-validation
    # failures to 400 (it strips 422 from the spec), so a non-positive version is 400.
    response = api_client.post(
        SCHEMA_URL, json={"schema_version": bad_version, "schema": SCHEMA_V1}
    )
    assert_response_status_code(response, 400)


def test_get_rejects_non_positive_version(api_client):
    # The path parameter carries the same ge=1 constraint.
    response = api_client.get(f"{SCHEMA_URL}/0")
    assert_response_status_code(response, 400)


def test_schema_versions_are_namespaced_per_library(api_client):
    # Version 1 already exists for the Sponsor library (published above). Publishing
    # version 1 to a DIFFERENT library with DIFFERENT content must succeed and stay
    # isolated: the key is (library_name, schema_version), not the version alone.
    response = api_client.post(
        SCHEMA_URL,
        json={
            "schema_version": 1,
            "schema": SCHEMA_V1_DIFFERENT,
            "library_name": CDISC_LIBRARY_NAME,
        },
    )
    assert_response_status_code(response, 201)
    assert response.json()["library_name"] == CDISC_LIBRARY_NAME

    # Each library returns its own content for version 1.
    cdisc = api_client.get(
        f"{SCHEMA_URL}/1", params={"library_name": CDISC_LIBRARY_NAME}
    ).json()
    sponsor = api_client.get(f"{SCHEMA_URL}/1").json()
    assert cdisc["schema"] == yaml.safe_load(SCHEMA_V1_DIFFERENT)
    assert sponsor["schema"] == yaml.safe_load(SCHEMA_V1)
    assert cdisc["content_hash"] != sponsor["content_hash"]

    # The listing is scoped to the requested library.
    cdisc_list = api_client.get(SCHEMA_URL, params={"library_name": CDISC_LIBRARY_NAME})
    assert_response_status_code(cdisc_list, 200)
    assert all(item["library_name"] == CDISC_LIBRARY_NAME for item in cdisc_list.json())


def test_sponsor_model_follows_published_schema(api_client):
    # Sponsor model referencing the published schema version 1.
    response = api_client.post(
        "/standards/sponsor-models/models",
        json={
            "ig_uid": data_model_ig.uid,
            "ig_version_number": data_model_ig.version_number,
            "version_number": "1",
            # The sponsor model must live in the same library as the schema it
            # follows for the FOLLOWS_SCHEMA link to resolve.
            "library_name": SPONSOR_LIBRARY_NAME,
            "schema_version": 1,
        },
    )
    assert_response_status_code(response, 201)
    assert response.json()["schema_version"] == 1

    # And it is surfaced on the list/get read path too.
    listed = api_client.get("/standards/sponsor-models/models").json()["items"]
    assert any(sm["schema_version"] == 1 for sm in listed)


def test_sponsor_model_without_schema_version_defaults_to_one(api_client):
    response = api_client.post(
        "/standards/sponsor-models/models",
        json={
            "ig_uid": data_model_ig.uid,
            "ig_version_number": data_model_ig.version_number,
            "version_number": "2",
            "library_name": SPONSOR_LIBRARY_NAME,
        },
    )
    assert_response_status_code(response, 201)
    # Missing link is treated as schema version 1 at read time.
    assert response.json()["schema_version"] == 1


def test_sponsor_model_with_unpublished_schema_version_is_rejected(api_client):
    response = api_client.post(
        "/standards/sponsor-models/models",
        json={
            "ig_uid": data_model_ig.uid,
            "ig_version_number": data_model_ig.version_number,
            "version_number": "3",
            "library_name": SPONSOR_LIBRARY_NAME,
            "schema_version": 42,
        },
    )
    assert_response_status_code(response, 400)
