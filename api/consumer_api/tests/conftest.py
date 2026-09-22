# pylint: disable=redefined-outer-name

import logging
from collections import defaultdict
from typing import Any

import pytest
import starlette.routing
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.testclient import TestClient

from common.auth.dependencies import dummy_access_token_claims, dummy_auth_object
from common.config import settings

log = logging.getLogger(__name__)

PARAMETER_DEFAULTS = defaultdict(
    lambda: "MISSING",
    **{
        "codelist_uid": "98765432101",
        "catalogue_name": "98765432102",
        "study_number": "98765432103",
        "term_uid": "98765432104",
        "uid": "98765432105",
        "study_uid": "98765432106",
        "version": "0.98765432107",
        "field_name": "uid",
        "repeating": "false",
    },
)


@pytest.fixture(scope="session")
def main_app(request) -> FastAPI:
    """Fixture to load the API application

    Intention to move this to a fixture is to increase the initial startup time,
    save on loading and initializing the whole app (which does tons of DB queries) if only a unit test is requested,
    and to isolate where the startup time is spent.
    """
    log.info("%s fixture: loading FastAPI application", request.fixturename)
    from consumer_api.consumer_api import app

    log.info("%s fixture: application loading completed", request.fixturename)
    return app


@pytest.fixture(scope="session")
def api_client(main_app, request) -> TestClient:
    log.debug("%s fixture: creating shared TestClient", request.fixturename)
    return TestClient(main_app)


@pytest.fixture(scope="session")
def openapi_schema(main_app) -> dict[str, Any]:
    schema = get_openapi(title="test", version="test", routes=main_app.routes)
    return schema


@pytest.fixture(scope="session")
def main_app_all_route_paths(main_app) -> tuple[tuple[str, tuple[str, ...]], ...]:
    log.debug("Compiling a list of all route paths")

    paths = []
    for route in main_app.routes:
        if isinstance(route, starlette.routing.Route):
            path = route.path.format_map(PARAMETER_DEFAULTS)
            paths.append((path, tuple(route.methods or [])))

    return tuple(paths)


@pytest.fixture(scope="session", autouse=not settings.oauth_enabled)
def mock_auth_context(request):
    """Mock starlette context with dummy user data"""

    from starlette_context import context, request_cycle_context

    mocked_store = {"auth": dummy_auth_object(dummy_access_token_claims())}

    log.info(
        "%s fixture: mocking context with dummy auth user",
        request.fixturename,
    )

    with request_cycle_context(mocked_store):
        yield context
