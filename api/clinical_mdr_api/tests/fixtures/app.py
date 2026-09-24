# pylint: disable=redefined-outer-name

import logging
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from starlette.testclient import TestClient

__all__ = ["api_client", "main_app", "openapi_schema"]

log = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def main_app(request) -> FastAPI:
    """Fixture to load the API application

    Intention to move this to a fixture is to increase the initial startup time,
    save on loading and initializing the whole app (which does tons of DB queries) if only a unit test is requested,
    and to isolate where the startup time is spent.
    """
    log.info("%s fixture: loading FastAPI application", request.fixturename)
    from clinical_mdr_api.main import app

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
