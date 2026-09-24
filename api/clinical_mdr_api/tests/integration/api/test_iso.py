"""
Tests for /admin/* endpoints
"""

import logging

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def api_client():
    """Create FastAPI test client"""
    yield TestClient(app)


def test_get_iso_languages(api_client):
    response = api_client.get("/iso/639")
    assert_response_status_code(response, 200)

    rs = response.json()

    assert len(rs) == 181, f"Expected 181 languages, but got {len(rs)}"

    for lang in rs:
        assert (
            len(lang["_1"]) == 2
        ), f"Key '{lang["_1"]}' must be 2 characters long for 639-1"
        assert (
            len(lang["_2T"]) == 3
        ), f"Key '{lang["_2T"]}' must be 3 characters long for 639-2T"
