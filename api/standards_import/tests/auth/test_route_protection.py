"""Every route is behind a role, and behind the role it is meant to be."""

import pytest
from fastapi.routing import APIRoute

from common.auth.dependencies import RequiresAnyRole
from standards_import.main import app
from standards_import.tests.auth.routes import (
    ALL_ROUTES_METHODS_ROLES,
    PUBLIC_ROUTES,
    READ,
    WRITE,
)


def declared_roles(route: APIRoute) -> list[set[str]]:
    return [
        dependency.call.required_roles
        for dependency in route.dependant.dependencies
        if isinstance(getattr(dependency, "call", None), RequiresAnyRole)
    ]


def all_app_routes() -> dict[tuple[str, str], APIRoute]:
    return {
        (path, method): route
        for path, route in flatten(app.routes)
        for method in (route.methods or set()) - {"HEAD", "OPTIONS"}
    }


def app_routes() -> dict[tuple[str, str], APIRoute]:
    """The routes that must be behind a role, i.e. all but the declared public ones."""

    return {
        key: route
        for key, route in all_app_routes().items()
        if key not in PUBLIC_ROUTES
    }


def flatten(routes) -> list[tuple[str, APIRoute]]:
    """Every `APIRoute` the app serves, with the path it is actually reachable at.

    `app.routes` used to be a flat list of `APIRoute`. Newer FastAPI keeps each
    `include_router` call as one router object holding its own routes, so filtering
    the top level for `APIRoute` finds nothing at all — and a suite that finds no
    routes still passes every per-route assertion it makes, because there is no route
    left to fail one. Only the drift test notices, which is why it is here.

    The attributes below are private, so this may want revisiting on a FastAPI
    upgrade. There is no public equivalent: the OpenAPI document is the supported way
    to enumerate an app's routes, and it does not carry the dependencies, which are
    the whole point of these tests.
    """

    found = []
    for route in routes:
        if isinstance(route, APIRoute):
            found.append((route.path, route))
        elif hasattr(route, "effective_candidates"):
            found.extend(flatten(route.effective_candidates()))
        elif hasattr(route, "original_route"):
            found.append((route.path, route.original_route))
    return found


def test_rbac_is_actually_switched_on_for_these_tests():
    """The stub `RequiresAnyRole` silently drops roles, which would pass everything."""

    assert hasattr(RequiresAnyRole({"X"}), "required_roles")


@pytest.mark.parametrize("path, method, expected", ALL_ROUTES_METHODS_ROLES)
def test_each_route_requires_the_roles_it_should(path, method, expected):
    route = app_routes().get((path, method))

    assert route is not None, f"{method} {path} is not a route of this app"
    assert declared_roles(route) == [expected]


def test_no_route_is_left_unprotected():
    """A new route with no `rbac.` dependency would otherwise be open to any caller."""

    unprotected = [
        f"{method} {path}"
        for (path, method), route in app_routes().items()
        if not declared_roles(route)
    ]

    assert not unprotected


def test_the_route_table_has_not_drifted_from_the_app():
    """Catches a route added, removed or renamed without anyone updating this suite."""

    assert {(path, method) for path, method, _ in ALL_ROUTES_METHODS_ROLES} == set(
        app_routes()
    )
    assert set(all_app_routes()) >= PUBLIC_ROUTES


def test_public_routes_really_are_open():
    """An entry in `PUBLIC_ROUTES` that has since gained a role should leave the list."""

    for key in PUBLIC_ROUTES:
        assert not declared_roles(all_app_routes()[key]), key


def test_every_route_declares_exactly_one_role_requirement():
    """Two would mean a caller needs both, which is not how any of these are meant."""

    for (path, method), route in app_routes().items():
        assert len(declared_roles(route)) == 1, f"{method} {path}"


def test_reads_and_writes_use_the_known_role_sets_and_no_others():
    """A third, bespoke role set on one route would be easy to miss in review."""

    assert {frozenset(roles) for _, _, roles in ALL_ROUTES_METHODS_ROLES} <= {
        frozenset(READ),
        frozenset(WRITE),
    }


def test_no_route_admits_a_role_from_anywhere_else_in_osb():
    """`Library.Import` gates the whole app, reads included.

    Asserted against the app rather than against the route table, so a route wired to
    some other `rbac.` constant is caught even if the table was updated to match it.
    Reading here is the review queue and the contents of an unimported release, which is
    of no use to a general OSB reader — and the roles that would otherwise creep in are
    exactly the broadly granted ones.
    """

    for (path, method), route in app_routes().items():
        for required in declared_roles(route):
            assert required == {"Library.Import"}, f"{method} {path} admits {required}"
