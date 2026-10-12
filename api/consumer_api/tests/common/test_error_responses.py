import pytest
from fastapi.testclient import TestClient

from consumer_api.consumer_api import app
from consumer_api.tests.utils import assert_response_status_code

ERROR_RESPONSE_REQUIRED_FIELDS = {"time", "path", "method", "type", "message"}


@pytest.fixture(scope="module")
def api_client():
    """Create FastAPI test client"""
    yield TestClient(app)


def test_unparsable_body_uses_documented_error_response(api_client):
    """A body the parser cannot read must still return the documented shape.

    FastAPI raises Starlette's `HTTPException` from its body-parsing machinery,
    so the handler has to be registered on that base class. Registered on
    `fastapi.HTTPException` instead, the response falls through to Starlette's
    default `{"detail": ...}`, which does not match the `ErrorResponse` schema
    the endpoint documents for 400.
    """
    response = api_client.post(
        "/v1/studies",
        content=b"\xff\x6e\x8f",
        headers={"Content-Type": "application/json"},
    )

    assert_response_status_code(response, 400)
    assert ERROR_RESPONSE_REQUIRED_FIELDS <= set(response.json())
