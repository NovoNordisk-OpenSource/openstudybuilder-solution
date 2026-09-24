import starlette

from consumer_api.tests.auth.integration.routes import ALL_ROUTES_METHODS_ROLES

IGNORE_ROUTES_METHODS = {
    ("/", "GET"),
    ("/system/information/license.md", "GET"),
    ("/system/information/sbom.md", "GET"),
    ("/system/information/build-id", "GET"),
    ("/system/information", "GET"),
    ("/system/healthcheck", "GET"),
    ("/docs", "HEAD"),
    ("/redoc", "HEAD"),
    ("/docs/oauth2-redirect", "HEAD"),
    ("/openapi.json", "HEAD"),
    ("/docs", "GET"),
    ("/redoc", "GET"),
    ("/docs/oauth2-redirect", "GET"),
    ("/openapi.json", "GET"),
}


def test_oauth_integration_test_routes(main_app):
    """Assures ALL_ROUTES_METHODS_ROLES includes all routes (paths & methods) except IGNORE_ROUTES_METHODS"""

    discovered_method_path_set = {
        (route.path, method)
        for route in main_app.routes
        if isinstance(route, starlette.routing.Route)
        for method in route.methods
    }

    configured_method_path_set = {
        (path, method) for path, method, _ in ALL_ROUTES_METHODS_ROLES
    }

    unconfigured_method_path_set = (
        discovered_method_path_set - configured_method_path_set - IGNORE_ROUTES_METHODS
    )

    assert (
        not unconfigured_method_path_set
    ), "Some routes are not listed in ALL_ROUTES_METHODS_ROLES:\n%s" % "\n".join(
        _recommend_path_method_roles_entry(path, method)
        for path, method in unconfigured_method_path_set
    )

    unknown_method_path_set = configured_method_path_set - discovered_method_path_set

    assert (
        not unknown_method_path_set
    ), "Remove obsolete routes from ALL_ROUTES_METHODS_ROLES: \n%s" % "\n".join(
        map(str, unknown_method_path_set)
    )


def _recommend_path_method_roles_entry(path: str, method: str) -> str:
    if path.startswith("/stud"):
        role = "Study."
    elif path.startswith("/admin/"):
        role = "Admin."
    else:
        role = "Library."

    if method.upper() == "GET":
        role += "Read"
    else:
        role += "Write"

    return f"""    ("{path}", "{method}", {{"{role}"}}),"""
