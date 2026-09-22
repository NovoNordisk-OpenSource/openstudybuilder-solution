import os

import pytest

from consumer_api.tests.auth.markers import if_oauth_enabled

# Skip all tests in this module if OAuth is not enabled
pytestmark = if_oauth_enabled

SKIP_PATHS = {
    "/openapi.json",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
    "/",
    "/system/information/license.md",
    "/system/information/sbom.md",
    "/system/information/build-id",
    "/system/information",
    "/system/healthcheck",
}
EXPIRED_ACCESS_TOKEN = os.environ.get("EXPIRED_ACCESS_TOKEN")


def test_global_security_dependency(main_app_all_route_paths, api_client):
    """Test that global Security dependency is in effect, and mandates an access token on (nearly) all paths"""

    for path, methods in main_app_all_route_paths:
        if path in SKIP_PATHS:
            continue

        for method in methods:
            response = api_client.request(method, path)
            assert response.status_code == 401, f"Bad status code for {method} {path}"


# This is redundant with test_jwk_service() which also tests with expired token
@pytest.mark.skipif(
    not EXPIRED_ACCESS_TOKEN,
    reason="EXPIRED_ACCESS_TOKEN is not set",
)
def test_global_security_dependency_with_invalid_token(
    main_app_all_route_paths, api_client
):
    """Test that global Security dependency is in effect, and refuses an expired access token on (nearly) all paths"""

    for path, methods in main_app_all_route_paths:
        if path in SKIP_PATHS:
            continue

        for method in methods:
            response = api_client.request(
                method,
                path,
                headers={"Authorization": f"Bearer {EXPIRED_ACCESS_TOKEN}"},
            )
            assert response.status_code == 401, (
                f"Bad status code {response.status_code} for {method} {path}"
                f" \n{response.text[:1024]}"
            )
