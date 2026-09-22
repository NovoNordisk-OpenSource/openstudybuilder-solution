"""
Tests for /feature-flags* endpoints (Final-only Root/Value)
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

import logging

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.feature_flag import FeatureFlag
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

feature_flags: list[FeatureFlag] = []


@pytest.fixture(scope="module")
def api_client(test_data):
    """Provide a test client with feature-flag test data loaded."""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Seed the database with feature flags used by this module's tests."""
    db_name = "featureflags.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    feature_flags.clear()

    for index in range(10):
        feature_flags.append(
            TestUtils.create_feature_flag(
                name=f"Feature Flag {index}",
                enabled=index % 2 == 0,
                description=f"Description {index}",
            )
        )

    yield


FEATURE_FLAG_NOT_NULL = [
    "uid",
    "name",
    "enabled",
    "status",
    "version",
]


def test_get_all_feature_flags(api_client):
    """List endpoint returns all current Final feature flags by default."""
    response = api_client.get("/feature-flags")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) == 10

    for item in res:
        for x in FEATURE_FLAG_NOT_NULL:
            assert item[x] is not None
        assert item["status"] == "Final"


def test_get_feature_flag(api_client):
    """Single-item endpoint returns the current feature flag state."""
    response = api_client.get(f"/feature-flags/{feature_flags[0].uid}")

    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == feature_flags[0].uid
    assert res["status"] == "Final"
    assert res["version"] == "1.0"


def test_create_feature_flag(api_client):
    """Create endpoint persists a new Final feature flag."""
    data = {
        "section": "admin",
        "feature": "Feature",
        "name": "Name",
        "enabled": False,
        "description": "Description",
    }
    response = api_client.post("/feature-flags", json=data)

    assert_response_status_code(response, 201)
    res = response.json()
    assert res["uid"].startswith("FeatureFlag_")
    assert res["name"] == data["name"]
    assert res["enabled"] == data["enabled"]
    assert res["description"] == data["description"]
    assert res["status"] == "Final"
    assert res["version"] == "1.0"


def test_update_feature_flag_creates_new_final_version(api_client):
    """Patch endpoint creates a new Final version when fields change."""
    uid = feature_flags[1].uid
    data = {"section": "studies", "feature": "Feature XX", "enabled": True}
    response = api_client.patch(f"/feature-flags/{uid}", json=data)

    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == uid
    assert res["status"] == "Final"
    assert res["version"] == "1.1"
    for field, value in data.items():
        assert res[field] == value


def test_patch_feature_flag_only_section(api_client):
    """Patching only section preserves the remaining current values."""
    original = api_client.get(f"/feature-flags/{feature_flags[2].uid}").json()

    data = {"section": "library"}
    response = api_client.patch(f"/feature-flags/{feature_flags[2].uid}", json=data)

    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == feature_flags[2].uid
    assert res["section"] == "library"
    assert res["feature"] == original["feature"]
    assert res["name"] == original["name"]
    assert res["enabled"] == original["enabled"]
    assert res["description"] == original["description"]
    assert res["version"] != original["version"]
    assert res["status"] == "Final"


def test_patch_feature_flag_only_feature(api_client):
    """Patching only feature preserves the remaining current values."""
    original = api_client.get(f"/feature-flags/{feature_flags[3].uid}").json()

    data = {"feature": "Updated Feature Name"}
    response = api_client.patch(f"/feature-flags/{feature_flags[3].uid}", json=data)

    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == feature_flags[3].uid
    assert res["feature"] == "Updated Feature Name"
    assert res["section"] == original["section"]
    assert res["name"] == original["name"]
    assert res["enabled"] == original["enabled"]
    assert res["description"] == original["description"]


def test_patch_feature_flag_only_enabled(api_client):
    """Patching only enabled flips the boolean and preserves other fields."""
    original = api_client.get(f"/feature-flags/{feature_flags[4].uid}").json()
    original_enabled_state = original["enabled"]

    data = {"enabled": not original_enabled_state}
    response = api_client.patch(f"/feature-flags/{feature_flags[4].uid}", json=data)

    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == feature_flags[4].uid
    assert res["enabled"] == (not original_enabled_state)
    assert res["section"] == original["section"]
    assert res["feature"] == original["feature"]
    assert res["name"] == original["name"]
    assert res["description"] == original["description"]


def test_patch_feature_flag_only_description(api_client):
    """Patching only description preserves the remaining current values."""
    original = api_client.get(f"/feature-flags/{feature_flags[5].uid}").json()

    data = {"description": "Updated description only"}
    response = api_client.patch(f"/feature-flags/{feature_flags[5].uid}", json=data)

    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == feature_flags[5].uid
    assert res["description"] == "Updated description only"
    assert res["section"] == original["section"]
    assert res["feature"] == original["feature"]
    assert res["name"] == original["name"]
    assert res["enabled"] == original["enabled"]
    assert res["version"] != original["version"]
    assert res["status"] == "Final"


def test_patch_feature_flag_multiple_fields(api_client):
    """Patching multiple fields updates only the supplied values."""
    original = api_client.get(f"/feature-flags/{feature_flags[5].uid}").json()

    data = {"section": "studies", "enabled": True}
    response = api_client.patch(f"/feature-flags/{feature_flags[5].uid}", json=data)

    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == feature_flags[5].uid
    assert res["section"] == "studies"
    assert res["enabled"] is True
    assert res["feature"] == original["feature"]
    assert res["name"] == original["name"]
    assert res["description"] == original["description"]


def test_patch_feature_flag_empty_body(api_client):
    """Empty patch body leaves the current feature flag version unchanged."""
    original = api_client.get(f"/feature-flags/{feature_flags[6].uid}").json()

    response = api_client.patch(f"/feature-flags/{feature_flags[6].uid}", json={})

    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == original["uid"]
    assert res["version"] == original["version"]
    assert res["enabled"] == original["enabled"]
    assert res["section"] == original["section"]


def test_patch_feature_flag_enabled_false(api_client):
    """Patching enabled to false persists the disabled state."""
    api_client.patch(f"/feature-flags/{feature_flags[7].uid}", json={"enabled": True})

    current = api_client.get(f"/feature-flags/{feature_flags[7].uid}").json()
    assert current["enabled"] is True

    response = api_client.patch(
        f"/feature-flags/{feature_flags[7].uid}", json={"enabled": False}
    )

    assert_response_status_code(response, 200)
    res = response.json()
    assert res["enabled"] is False


def test_get_feature_flag_versions(api_client):
    """Version history includes diff content for successive Final versions."""
    uid = feature_flags[8].uid
    api_client.patch(f"/feature-flags/{uid}", json={"enabled": True})
    api_client.patch(f"/feature-flags/{uid}", json={"enabled": False})

    response = api_client.get(f"/feature-flags/{uid}/versions")
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) >= 3
    assert all(item["uid"] == uid for item in res)
    assert all(item["status"] == "Final" for item in res)
    assert res[0]["changes"] is not None

    # Newest first. calculate_diffs() diffs each entry against the following
    # one, so the order decides which version a change is credited to: fed
    # oldest-first it blames the version below the one that changed and leaves
    # the newest with an empty diff.
    start_dates = [item["start_date"] for item in res]
    assert start_dates == sorted(start_dates, reverse=True)

    # res[0] is therefore the current version -- the second patch above -- and
    # it is the entry that has to report `enabled` as changed.
    assert res[0]["end_date"] is None
    assert res[0]["enabled"] is False
    assert "enabled" in res[0]["changes"]
    # The initial version has nothing to diff against.
    assert res[-1]["changes"] == []


def test_inactivate_and_list_excludes_deprecated_by_default(api_client):
    """Retired flags stay addressable by uid and are excluded from default list."""
    uid = feature_flags[0].uid
    enabled_before = api_client.get(f"/feature-flags/{uid}").json()["enabled"]

    response = api_client.delete(f"/feature-flags/{uid}/activations")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == uid
    assert res["status"] == "Retired"
    assert res["enabled"] == enabled_before

    # Still retrievable by uid; enabled unchanged by lifecycle
    response = api_client.get(f"/feature-flags/{uid}")
    assert_response_status_code(response, 200)
    assert response.json()["status"] == "Retired"
    assert response.json()["enabled"] == enabled_before

    # Default list excludes retired
    response = api_client.get("/feature-flags")
    assert_response_status_code(response, 200)
    assert all(item["uid"] != uid for item in response.json())

    # include_retired=true includes retired
    response = api_client.get("/feature-flags", params={"include_retired": True})
    assert_response_status_code(response, 200)
    assert any(
        item["uid"] == uid and item["status"] == "Retired" for item in response.json()
    )

    # include_deprecated=true remains supported as a compatibility alias
    response = api_client.get("/feature-flags", params={"include_deprecated": True})
    assert_response_status_code(response, 200)
    assert any(
        item["uid"] == uid and item["status"] == "Retired" for item in response.json()
    )


def test_reactivate_retired_feature_flag(api_client):
    """Reactivating a retired flag returns it to the default Final list."""
    uid = feature_flags[9].uid
    enabled_before = api_client.get(f"/feature-flags/{uid}").json()["enabled"]
    api_client.delete(f"/feature-flags/{uid}/activations")
    assert api_client.get(f"/feature-flags/{uid}").json()["enabled"] == enabled_before

    response = api_client.post(f"/feature-flags/{uid}/activations")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["uid"] == uid
    assert res["status"] == "Final"
    assert res["enabled"] == enabled_before

    response = api_client.get("/feature-flags")
    assert_response_status_code(response, 200)
    assert any(
        item["uid"] == uid and item["status"] == "Final" for item in response.json()
    )


def test_cannot_create_feature_flag_with_existing_name(api_client):
    """Creating a duplicate feature flag name returns a conflict."""
    response = api_client.post(
        "/feature-flags",
        json={
            "section": "admin",
            "feature": "Feature",
            "name": "Name",
            "enabled": False,
            "description": "Description",
        },
    )

    assert_response_status_code(response, 409)
    res = response.json()
    assert res["message"] == "Feature Flag with Name 'Name' already exists."


def test_cannot_update_retired_feature_flag(api_client):
    """Retired feature flags cannot be updated."""
    uid = feature_flags[0].uid
    # Ensure retired (may already be retired from earlier tests in module)
    current = api_client.get(f"/feature-flags/{uid}").json()
    if current["status"] != "Retired":
        assert_response_status_code(
            api_client.delete(f"/feature-flags/{uid}/activations"), 200
        )

    response = api_client.patch(f"/feature-flags/{uid}", json={"enabled": True})
    assert_response_status_code(response, 400)
    assert "Only Final" in response.json()["message"]


def test_cannot_inactivate_already_retired_feature_flag(api_client):
    """Retired feature flags cannot be inactivated again."""
    uid = feature_flags[0].uid
    current = api_client.get(f"/feature-flags/{uid}").json()
    if current["status"] != "Retired":
        assert_response_status_code(
            api_client.delete(f"/feature-flags/{uid}/activations"), 200
        )

    response = api_client.delete(f"/feature-flags/{uid}/activations")
    assert_response_status_code(response, 400)
    assert "Only Final" in response.json()["message"]


def test_cannot_reactivate_final_feature_flag(api_client):
    """Final feature flags cannot be reactivated."""
    # feature_flags[1] should still be Final (not used by inactivate tests)
    uid = feature_flags[1].uid
    current = api_client.get(f"/feature-flags/{uid}").json()
    assert current["status"] == "Final"

    response = api_client.post(f"/feature-flags/{uid}/activations")
    assert_response_status_code(response, 400)
    assert "Only Retired" in response.json()["message"]


def test_versions_include_retired_after_inactivate(api_client):
    """Version history includes both Final and Retired entries after inactivation."""
    # Use a fresh flag so history is controlled
    created = api_client.post(
        "/feature-flags",
        json={
            "section": "admin",
            "feature": "Lifecycle Feature",
            "name": "Lifecycle Version History Flag",
            "enabled": False,
            "description": "For version history with Retired",
        },
    )
    assert_response_status_code(created, 201)
    uid = created.json()["uid"]

    assert_response_status_code(
        api_client.patch(f"/feature-flags/{uid}", json={"enabled": True}), 200
    )
    assert_response_status_code(
        api_client.delete(f"/feature-flags/{uid}/activations"), 200
    )

    response = api_client.get(f"/feature-flags/{uid}/versions")
    assert_response_status_code(response, 200)
    res = response.json()
    statuses = {item["status"] for item in res}
    assert "Final" in statuses
    assert "Retired" in statuses
    assert all("changes" in item for item in res)
    assert all(item["uid"] == uid for item in res)
