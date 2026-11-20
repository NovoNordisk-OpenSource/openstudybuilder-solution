import starlette
from fastapi.routing import iter_route_contexts


def assert_route_registry_matches(main_app, all_routes_methods_roles, ignored_routes):
    """Check that an app's routes match its path, method, and role registry."""
    discovered_method_path_set = {
        (route.path, method)
        for route in iter_route_contexts(main_app.routes)
        if isinstance(route.original_route, starlette.routing.Route)
        and route.path is not None
        for method in route.methods or []
    }

    configured_method_path_set = {
        (path, method) for path, method, _ in all_routes_methods_roles
    }

    unconfigured_method_paths = sorted(
        discovered_method_path_set - configured_method_path_set - ignored_routes
    )
    if unconfigured_method_paths:
        unconfigured_route_summary = ", ".join(
            f"{method} {path}" for path, method in unconfigured_method_paths
        )
        recommended_entries = "\n".join(
            _recommend_path_method_roles_entry(path, method)
            for path, method in unconfigured_method_paths
        )
        raise AssertionError(
            "Unlisted route methods in ALL_ROUTES_METHODS_ROLES: "
            f"{unconfigured_route_summary}\n{recommended_entries}"
        )

    unknown_method_paths = sorted(
        configured_method_path_set - discovered_method_path_set
    )
    assert not unknown_method_paths, (
        "Remove obsolete routes from ALL_ROUTES_METHODS_ROLES: "
        f"{unknown_method_paths}"
    )


def _recommend_path_method_roles_entry(path: str, method: str) -> str:
    normalized_path = path
    path_parts = normalized_path.split("/")
    if (
        len(path_parts) > 2
        and path_parts[1].startswith("v")
        and path_parts[1][1:].isdigit()
    ):
        normalized_path = "/" + "/".join(path_parts[2:])

    if normalized_path.startswith("/stud"):
        role = "Study."
    elif normalized_path.startswith("/admin/"):
        role = "Admin."
    else:
        role = "Library."

    role += "Read" if method.upper() == "GET" else "Write"
    return f'    ("{path}", "{method}", {{"{role}"}}),'
