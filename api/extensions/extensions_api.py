"""RESTful API endpoints that extend the main API functionality"""

# Placed at the top to ensure logging is configured before anything else is loaded
import importlib
import sys
from typing import Any

from fastapi.exceptions import RequestValidationError
from opencensus.trace.print_exporter import PrintExporter

from common.logger import default_logging_config, log_exception
from common.telemetry.request_metrics import patch_neomodel_database
from common.telemetry.tracing_middleware import TracingMiddleware
from extensions.common import get_api_version

default_logging_config()

# pylint: disable=wrong-import-position,wrong-import-order,ungrouped-imports
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from neomodel import config as neomodel_config
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import AlwaysOnSampler
from pydantic import ValidationError
from starlette_context.middleware import RawContextMiddleware

from common.auth.dependencies import security
from common.auth.discovery import reconfigure_with_openid_discovery
from common.config import settings
from common.exceptions import MDRApiBaseException
from common.models.error import ErrorResponse
from common.openapi import (
    strip_min_length_from_nullable_input_strings,
    strip_null_from_query_parameter_schemas,
)
from common.telemetry.traceback_middleware import ExceptionTracebackMiddleware

log = logging.getLogger(__name__)

# Configure Neo4J connection on startup
neo4j_dsn = os.getenv("NEO4J_DSN")
if neo4j_dsn:
    neomodel_config.DATABASE_URL = neo4j_dsn
    log.info("Neo4j DSN set to: %s", neo4j_dsn.split("@")[-1])


# Middlewares - please don't use app.add_middleware() as that inserts them to the beginning of the list
middlewares = []

# gzip compress responses
if settings.gzip_response_min_size:
    middlewares.append(
        Middleware(
            GZipMiddleware,
            minimum_size=settings.gzip_response_min_size,
            compresslevel=settings.gzip_level,
        )
    )

# Context middleware - must come before TracingMiddleware
middlewares.append(Middleware(RawContextMiddleware))

# Tracing middleware
if settings.tracing_enabled:

    # Azure Application Insights integration for tracing
    if settings.appinsights_connection:
        tracing_exporter = AzureExporter(
            connection_string=settings.appinsights_connection,
            enable_local_storage=False,
        )

    elif settings.zipkin_host:
        # opencensus-ext-zipkin is a dev-only package dependency
        from opencensus.ext.zipkin.trace_exporter import ZipkinExporter

        tracing_exporter = ZipkinExporter(
            service_name="extension-api",
            host_name=settings.zipkin_host,
            port=settings.zipkin_port,
            endpoint=settings.zipkin_endpoint,
            protocol=settings.zipkin_protocol,
        )

    else:
        tracing_exporter = PrintExporter()

    middlewares.append(
        Middleware(
            TracingMiddleware,
            sampler=AlwaysOnSampler(),
            exporter=tracing_exporter,
            exclude_paths={"*/system/healthcheck"},
            exclude_clients={"127.0.0.1", "::1"},
        )
    )

    patch_neomodel_database()

middlewares.append(
    Middleware(
        CORSMiddleware,
        allow_origin_regex=settings.allow_origin_regex,
        allow_credentials=settings.allow_credentials,
        allow_methods=settings.allow_methods,
        allow_headers=settings.allow_headers,
        expose_headers=["traceresponse"],
    )
)

# Convert all uncaught exceptions to response before returning to TracingMiddleware
middlewares.append(Middleware(ExceptionTracebackMiddleware))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.oauth_enabled:
        # Reconfiguring Swagger UI settings with OpenID Connect discovery
        await reconfigure_with_openid_discovery()
    yield


app = FastAPI(
    title="OpenStudyBuilder API Extensions",
    version=get_api_version(),
    middleware=middlewares,
    lifespan=lifespan,
    swagger_ui_init_oauth=settings.swagger_ui_init_oauth,
    swagger_ui_parameters={"docExpansion": "none"},
    description="""
## NOTICE

This license information is applicable to the swagger documentation of the clinical-mdr-api, that is the openapi.json.

## License Terms (MIT)

Copyright (C) 2025 Novo Nordisk A/S, Danish company registration no. 24256790

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Licenses and Acknowledgements for Incorporated Software

This component contains software licensed under different licenses when compiled, please refer to the third-party-licenses.md file for further information and full license texts.

## Authentication

Supports OAuth2 [Authorization Code Flow](https://datatracker.ietf.org/doc/html/rfc6749#section-4.1),
at paths described in the OpenID Connect Discovery metadata document (whose URL is defined by the `OAUTH_METADATA_URL` environment variable).

Microsoft Identity Platform documentation can be read 
([here](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow)).
""",
)

app.openapi_version = "3.1.0"


@app.exception_handler(MDRApiBaseException)
async def extension_api_exception_handler(
    request: Request, exception: MDRApiBaseException
):
    """Returns an HTTP error code associated to given exception."""

    await log_exception(request, exception)

    ExceptionTracebackMiddleware.add_traceback_attributes(exception)

    return JSONResponse(
        status_code=exception.status_code,
        content=jsonable_encoder(ErrorResponse(request, exception)),
        headers=exception.headers,
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_error_handler(
    request: Request, exception: ValidationError
):
    """Returns `400 Bad Request` http error status code in case Pydantic detects validation issues
    with supplied payloads or parameters."""

    await log_exception(request, exception)

    ExceptionTracebackMiddleware.add_traceback_attributes(exception)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(ErrorResponse(request, exception)),
    )


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(
    request: Request, exception: RequestValidationError
) -> JSONResponse:
    await log_exception(request, exception)

    ExceptionTracebackMiddleware.add_traceback_attributes(exception)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(ErrorResponse(request, exception)),
        headers={},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exception: ValueError):
    """Returns `400 Bad Request` http error status code in case ValueError is raised"""

    await log_exception(request, exception)

    ExceptionTracebackMiddleware.add_traceback_attributes(exception)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(ErrorResponse(request, exception)),
    )


class PathContext:

    def __init__(self, path, orig_path=None):
        self.path = path
        self.orig_path = orig_path

    def __enter__(self):
        self.orig_path = list(sys.path)
        if self.path is not None:
            sys.path = self.path + sys.path

    def __exit__(self, etype, evalue, etraceback):
        sys.path = self.orig_path


def load_extensions():
    """Function to load extensions when this module is imported."""
    # Loop through all subfolders of the 'extensions' folder dynamically
    # and load their '{extension}_main.py' API router files if they exist
    extensions_folder = os.path.dirname(__file__)
    # Sort to ensure deterministic load order: os.listdir() is filesystem-dependent,
    # which would cause the generated OpenAPI spec to differ between machines.
    for extension_name in sorted(os.listdir(extensions_folder)):
        extension_path = os.path.join(extensions_folder, extension_name)
        extension_main_module = f"{extension_name}_main"
        extension_main_file = os.path.join(
            extension_path, extension_main_module + ".py"
        )
        if os.path.isdir(extension_path) and os.path.exists(extension_main_file):
            log.info(
                "Loading extension '%s' from '%s'",
                extension_main_module,
                extension_path,
            )
            with PathContext([extension_path]):
                try:
                    module = importlib.import_module(extension_main_module)
                    router = module.router
                except Exception as e:
                    log.error(
                        "Error loading extension '%s' from '%s'",
                        extension_main_module,
                        extension_path,
                    )
                    log.debug("Details:", exc_info=e)
                    raise
            app.include_router(
                router,
                prefix="/" + extension_name.replace("_", "-"),
            )


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["servers"] = [{"url": settings.openapi_schema_api_root_path}]

    if settings.oauth_enabled:
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}

        if "securitySchemes" not in openapi_schema["components"]:
            openapi_schema["components"]["securitySchemes"] = {}

        # Add 'BearerJwtAuth' security schema globally
        openapi_schema["components"]["securitySchemes"]["BearerJwtAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",  # optional, arbitrary value for documentation purposes
            "in": "header",
            "name": "Authorization",
            "description": "Access token that will be sent as `Authorization: Bearer {token}` header in all requests",
        }

        openapi_schema["components"]["securitySchemes"][
            "OAuth2AuthorizationCodeBearer"
        ]["flows"]["authorizationCode"]["scopes"] = {
            "api:///API.call": "Make calls to the API"
        }

        # Add 'BearerJwtAuth' security method to all endpoints
        api_router = [route for route in app.routes if isinstance(route, APIRoute)]
        for route in api_router:
            if not any(
                dependency
                for dependency in route.dependencies
                if dependency == security
            ):
                continue
            path = getattr(route, "path")
            methods = [method.lower() for method in getattr(route, "methods")]

            for method in methods:
                endpoint_security: list[Any] = openapi_schema["paths"][path][
                    method
                ].get("security", [])
                endpoint_security.append({"BearerJwtAuth": []})
                openapi_schema["paths"][path][method]["security"] = endpoint_security

    # Add `400 Bad Request` error response to all endpoints
    for path, path_item in openapi_schema["paths"].items():
        for method, operation in path_item.items():
            if "responses" not in operation:
                operation["responses"] = {}
            if "400" not in operation["responses"]:
                operation["responses"]["400"] = {
                    "description": "Bad Request",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                        }
                    },
                }

    strip_null_from_query_parameter_schemas(openapi_schema)
    strip_min_length_from_nullable_input_strings(openapi_schema)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


load_extensions()

setattr(app, "openapi", custom_openapi)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "extensions.extensions_api:app",
        host=os.getenv("UVICORN_HOST", "127.0.0.1"),
        port=int(os.getenv("UVICORN_PORT", "8009")),
        reload=True,
    )
