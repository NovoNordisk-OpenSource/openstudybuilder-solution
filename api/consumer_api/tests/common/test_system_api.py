# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
import pytest
from fastapi.testclient import TestClient

from consumer_api.consumer_api import app
from consumer_api.tests.utils import assert_response_status_code


@pytest.fixture(scope="module")
def api_client():
    """Create FastAPI test client"""
    yield TestClient(app)


@pytest.mark.parametrize(
    "path",
    [
        "/system/information",
        "/system/information/build-id",
        "/system/healthcheck",
    ],
)
def test_system_api_endpoints(api_client, path):
    response = api_client.get(path)
    assert_response_status_code(response, 200)
