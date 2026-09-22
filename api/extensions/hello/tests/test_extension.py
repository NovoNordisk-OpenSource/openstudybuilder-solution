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


def test_get_nodes_count(api_client):
    res = api_client.get("/hello/nodes-count")
    assert res.status_code == 200
