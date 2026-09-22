"""
Tests for /admin/global-preferences and /user-preferences endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name

import logging

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.domain_repositories.preferences_registry import (
    PREFERENCE_DEFINITIONS,
    PREFERENCE_KEYS,
    to_metadata_dict,
)
from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Expected defaults derived from registry
EXPECTED_DEFAULTS = {d.key: d.default for d in PREFERENCE_DEFINITIONS}


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "preferences.api"
    inject_and_clear_db(db_name)
    inject_base_data()


# ─── Global preferences ───────────────────────────────────────────────


def test_get_global_preferences_returns_defaults(api_client):
    """GET /admin/global-preferences returns all defaults on first access."""
    response = api_client.get("/admin/global-preferences")
    assert_response_status_code(response, 200)
    body = response.json()

    assert "preferences" in body
    assert "metadata" in body

    prefs = body["preferences"]
    for key in PREFERENCE_KEYS:
        assert key in prefs, f"Missing preference key: {key}"
        assert (
            prefs[key] == EXPECTED_DEFAULTS[key]
        ), f"Default mismatch for '{key}': expected {EXPECTED_DEFAULTS[key]}, got {prefs[key]}"


def test_get_global_preferences_metadata_shape(api_client):
    """Metadata for each key matches the registry definition."""
    response = api_client.get("/admin/global-preferences")
    assert_response_status_code(response, 200)
    metadata = response.json()["metadata"]

    for defn in PREFERENCE_DEFINITIONS:
        assert defn.key in metadata, f"Metadata missing key: {defn.key}"
        expected = to_metadata_dict(defn)
        actual = metadata[defn.key]
        for field, value in expected.items():
            assert actual[field] == value, (
                f"Metadata field '{field}' mismatch for '{defn.key}': "
                f"expected {value}, got {actual.get(field)}"
            )


def test_patch_global_preferences_integer(api_client):
    """PATCH /admin/global-preferences updates rows_per_page."""
    response = api_client.patch("/admin/global-preferences", json={"rows_per_page": 25})
    assert_response_status_code(response, 200)
    assert response.json()["preferences"]["rows_per_page"] == 25

    # Verify via GET
    response = api_client.get("/admin/global-preferences")
    assert_response_status_code(response, 200)
    assert response.json()["preferences"]["rows_per_page"] == 25


def test_patch_global_preferences_boolean(api_client):
    """PATCH /admin/global-preferences updates sidebar_visible."""
    response = api_client.patch(
        "/admin/global-preferences", json={"sidebar_visible": False}
    )
    assert_response_status_code(response, 200)
    assert response.json()["preferences"]["sidebar_visible"] is False


def test_patch_global_preferences_enum(api_client):
    """PATCH /admin/global-preferences updates language."""
    response = api_client.patch("/admin/global-preferences", json={"language": "en"})
    assert_response_status_code(response, 200)
    assert response.json()["preferences"]["language"] == "en"


def test_patch_global_preferences_theme(api_client):
    """PATCH /admin/global-preferences updates theme."""
    response = api_client.patch(
        "/admin/global-preferences", json={"theme": "NNOceanTheme"}
    )
    assert_response_status_code(response, 200)
    assert response.json()["preferences"]["theme"] == "NNOceanTheme"


def test_patch_global_preferences_multiple_fields(api_client):
    """PATCH /admin/global-preferences updates multiple fields at once."""
    payload = {
        "rows_per_page": 50,
        "sidebar_auto_minimize": True,
    }
    response = api_client.patch("/admin/global-preferences", json=payload)
    assert_response_status_code(response, 200)
    prefs = response.json()["preferences"]
    assert prefs["rows_per_page"] == 50
    assert prefs["sidebar_auto_minimize"] is True


def test_patch_global_preferences_invalid_rows_per_page_too_low(api_client):
    """PATCH with rows_per_page < 5 returns 400 (Pydantic validation)."""
    response = api_client.patch("/admin/global-preferences", json={"rows_per_page": 2})
    assert_response_status_code(response, 400)


def test_patch_global_preferences_invalid_rows_per_page_too_high(api_client):
    """PATCH with rows_per_page > 100 returns 400 (Pydantic validation)."""
    response = api_client.patch(
        "/admin/global-preferences", json={"rows_per_page": 999}
    )
    assert_response_status_code(response, 400)


def test_patch_global_preferences_invalid_language(api_client):
    """PATCH with invalid language value returns 400 (Pydantic Literal validation)."""
    response = api_client.patch("/admin/global-preferences", json={"language": "xx"})
    assert_response_status_code(response, 400)


def test_patch_global_preferences_theme_accepts_arbitrary_string(api_client):
    """PATCH accepts any string for theme - it's an unvalidated frontend palette name."""
    response = api_client.patch("/admin/global-preferences", json={"theme": "unknown"})
    assert_response_status_code(response, 200)
    assert response.json()["preferences"]["theme"] == "unknown"


def test_patch_global_preferences_preserves_unset_fields(api_client):
    """PATCH only updates provided fields, leaves others unchanged."""
    # Reset to known state
    api_client.patch(
        "/admin/global-preferences",
        json={"rows_per_page": 10, "sidebar_visible": True},
    )

    # Patch only rows_per_page
    api_client.patch("/admin/global-preferences", json={"rows_per_page": 30})

    response = api_client.get("/admin/global-preferences")
    assert_response_status_code(response, 200)
    prefs = response.json()["preferences"]
    assert prefs["rows_per_page"] == 30
    assert prefs["sidebar_visible"] is True  # unchanged


# ─── User preferences ─────────────────────────────────────────────────


def test_get_user_preferences_returns_globals_when_no_overrides(api_client):
    """GET /user-preferences returns global defaults with all overrides=False."""
    # Reset global prefs to defaults first
    api_client.patch("/admin/global-preferences", json=EXPECTED_DEFAULTS)

    response = api_client.get("/user-preferences")
    assert_response_status_code(response, 200)
    body = response.json()

    assert "preferences" in body
    assert "overrides" in body
    assert "metadata" in body

    for key in PREFERENCE_KEYS:
        assert key in body["preferences"]
        assert key not in body["overrides"]


def test_patch_user_preferences(api_client):
    """PATCH /user-preferences sets a user override."""
    response = api_client.patch("/user-preferences", json={"rows_per_page": 42})
    assert_response_status_code(response, 200)
    body = response.json()
    assert body["preferences"]["rows_per_page"] == 42
    assert body["overrides"]["rows_per_page"] == 10


def test_patch_user_preferences_multiple_fields(api_client):
    """PATCH /user-preferences updates multiple fields."""
    payload = {
        "sidebar_visible": False,
        "sidebar_auto_minimize": True,
    }
    response = api_client.patch("/user-preferences", json=payload)
    assert_response_status_code(response, 200)
    body = response.json()
    assert body["preferences"]["sidebar_visible"] is False
    assert body["preferences"]["sidebar_auto_minimize"] is True
    assert body["overrides"]["sidebar_visible"] is True
    assert body["overrides"]["sidebar_auto_minimize"] is False


def test_patch_user_preferences_theme(api_client):
    """PATCH /user-preferences sets a theme override."""
    response = api_client.patch(
        "/user-preferences", json={"theme": "HighContrastTheme"}
    )
    assert_response_status_code(response, 200)
    body = response.json()
    assert body["preferences"]["theme"] == "HighContrastTheme"
    assert body["overrides"]["theme"] == "NNCustomLightTheme"


def test_get_user_preferences_shows_overrides(api_client):
    """GET /user-preferences reflects previously set overrides."""
    response = api_client.get("/user-preferences")
    assert_response_status_code(response, 200)
    body = response.json()
    # rows_per_page was set to 42 in earlier test
    assert body["preferences"]["rows_per_page"] == 42
    assert body["overrides"]["rows_per_page"] == 10


def test_delete_user_preference_resets_to_global(api_client):
    """DELETE /user-preferences/{key} resets that key to global default."""
    response = api_client.delete("/user-preferences/rows_per_page")
    assert_response_status_code(response, 200)
    body = response.json()
    assert "rows_per_page" not in body["overrides"]
    # Should now reflect the global value
    global_resp = api_client.get("/admin/global-preferences")
    global_rows = global_resp.json()["preferences"]["rows_per_page"]
    assert body["preferences"]["rows_per_page"] == global_rows


def test_delete_user_theme_preference_resets_to_global(api_client):
    """DELETE /user-preferences/theme resets theme to global default."""
    response = api_client.delete("/user-preferences/theme")
    assert_response_status_code(response, 200)
    body = response.json()
    assert "theme" not in body["overrides"]
    global_resp = api_client.get("/admin/global-preferences")
    global_theme = global_resp.json()["preferences"]["theme"]
    assert body["preferences"]["theme"] == global_theme


def test_delete_user_preference_invalid_key(api_client):
    """DELETE /user-preferences/{invalid_key} returns 400."""
    response = api_client.delete("/user-preferences/nonexistent_key")
    assert_response_status_code(response, 400)


def test_patch_user_preferences_invalid_rows_per_page(api_client):
    """PATCH /user-preferences with invalid rows_per_page returns 400."""
    response = api_client.patch("/user-preferences", json={"rows_per_page": 1})
    assert_response_status_code(response, 400)


def test_patch_user_preferences_invalid_language(api_client):
    """PATCH /user-preferences with invalid language returns 400."""
    response = api_client.patch("/user-preferences", json={"language": "fr"})
    assert_response_status_code(response, 400)


def test_patch_user_preferences_theme_accepts_arbitrary_string(api_client):
    """PATCH /user-preferences accepts any string for theme - it's an unvalidated frontend palette name."""
    response = api_client.patch("/user-preferences", json={"theme": "unknown"})
    assert_response_status_code(response, 200)
    assert response.json()["preferences"]["theme"] == "unknown"


def test_user_preferences_metadata_matches_global(api_client):
    """User preferences metadata matches global preferences metadata."""
    global_resp = api_client.get("/admin/global-preferences")
    user_resp = api_client.get("/user-preferences")
    assert_response_status_code(global_resp, 200)
    assert_response_status_code(user_resp, 200)
    assert global_resp.json()["metadata"] == user_resp.json()["metadata"]
