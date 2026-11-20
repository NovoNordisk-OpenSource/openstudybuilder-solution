from clinical_mdr_api.tests.auth.integration.routes import ALL_ROUTES_METHODS_ROLES
from common.tests.auth.route_coverage import assert_route_registry_matches

IGNORE_ROUTES_METHODS = {
    ("/", "GET"),
    ("/system/information/license.md", "GET"),
    ("/system/information/sbom.md", "GET"),
    ("/system/information/build-id", "GET"),
    ("/system/information", "GET"),
    ("/system/healthcheck", "GET"),
    ("/notifications/actives", "GET"),
    ("/docs", "HEAD"),
    ("/redoc", "HEAD"),
    ("/docs/oauth2-redirect", "HEAD"),
    ("/openapi.json", "HEAD"),
    ("/docs", "GET"),
    ("/redoc", "GET"),
    ("/docs/oauth2-redirect", "GET"),
    ("/openapi.json", "GET"),
    (
        "/concepts/activities/activity-sub-groups/{activity_subgroup_uid}/activities",
        "GET",
    ),
}


def test_oauth_integration_test_routes(main_app):
    """Assures ALL_ROUTES_METHODS_ROLES includes all routes (paths & methods) except IGNORE_ROUTES_METHODS"""
    assert_route_registry_matches(
        main_app, ALL_ROUTES_METHODS_ROLES, IGNORE_ROUTES_METHODS
    )
