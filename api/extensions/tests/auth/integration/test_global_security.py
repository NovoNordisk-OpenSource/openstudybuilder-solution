from common.tests.auth.global_security import (
    assert_global_security_rejects_expired_token,
    assert_global_security_requires_auth,
)
from extensions.tests.auth.markers import if_oauth_enabled

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


def test_global_security_dependency(main_app_all_route_paths, api_client):
    """Test that global Security dependency is in effect, and mandates an access token on (nearly) all paths"""
    assert_global_security_requires_auth(
        main_app_all_route_paths, api_client, SKIP_PATHS
    )


def test_global_security_dependency_with_invalid_token(
    main_app_all_route_paths, api_client, monkeypatch
):
    """Test that global Security dependency is in effect, and refuses an expired access token on (nearly) all paths"""
    assert_global_security_rejects_expired_token(
        main_app_all_route_paths, api_client, SKIP_PATHS, monkeypatch
    )
