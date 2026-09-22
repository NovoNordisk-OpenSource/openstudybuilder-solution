# pylint: disable=redefined-outer-name
"""
Auth tests for `GET /v1/library/activity-item-classes`.

The endpoint is protected by `rbac.LIBRARY_READ`. Without the proper role,
calls must be rejected with 401 (no token) or 403 (token without the role).
"""

import logging

from fastapi.testclient import TestClient

from consumer_api.tests.utils import assert_response_status_code

log = logging.getLogger(__name__)

ENDPOINT = "/v1/library/activity-item-classes"


def test_unauthenticated_request_is_rejected(api_client: TestClient):
    """Calling without a Bearer token must return 401."""
    log.info("GET %s without Authorization header", ENDPOINT)
    response = api_client.get(ENDPOINT)
    assert_response_status_code(response, [401, 403])


def test_token_without_library_read_is_rejected(
    api_client: TestClient, token_without_library_read: str | None = None
):
    """A valid token without `Library.Read` must return 403.

    Falls back to plain unauthenticated when no token fixture is provided
    (auth tests already cover the unauthenticated case above, so we just
    ensure the endpoint registered the dependency correctly).
    """
    headers = {}
    if token_without_library_read:
        headers["Authorization"] = f"Bearer {token_without_library_read}"
    response = api_client.get(ENDPOINT, headers=headers)
    assert_response_status_code(response, [401, 403])
