# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
import pytest
from fastapi.testclient import TestClient

from extensions.extensions_api import app


@pytest.fixture(scope="module")
def api_client():
    """Create FastAPI test client"""
    yield TestClient(app)


def test_healthcheck_endpoint(api_client):
    res = api_client.get("/system/healthcheck")
    assert res.text == '"OK"'
    assert res.status_code == 200
