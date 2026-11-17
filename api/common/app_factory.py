"""Shared FastAPI application setup used by all four API apps.

All apps (clinical_mdr_api, standards_import, consumer_api, extensions) share the
same middleware stack, exception-handler set, and custom-openapi logic. This module
centralises that boilerplate so each main file becomes a thin, app-specific caller
rather than a copy-paste of 200 identical lines.

The factory is purely behaviour-preserving: every per-app difference (CORS presence,
TracingMiddleware's exclude_clients, separate_input_output_schemas, 422-removal in the
schema, app.openapi_version override, the StarletteHTTPException handler unique to the
main app) is expressed as an explicit parameter with the app's current default baked in,
so each app receives exactly the same observable behaviour as before the refactor.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.print_exporter import PrintExporter
from opencensus.trace.samplers import AlwaysOnSampler
from pydantic import ValidationError
from starlette_context.middleware import RawContextMiddleware

from common.auth.dependencies import security
from common.config import settings
from common.exceptions import MDRApiBaseException
from common.logger import log_exception
from common.models.error import ErrorResponse
from common.openapi import (
    strip_min_length_from_nullable_input_strings,
    strip_null_from_query_parameter_schemas,
)
from common.telemetry.request_metrics import patch_neomodel_database
from common.telemetry.traceback_middleware import ExceptionTracebackMiddleware
from common.telemetry.tracing_middleware import TracingMiddleware

log = logging.getLogger(__name__)


def build_middlewares(
    *,
    service_name: str,
    include_cors: bool = True,
    tracing_exclude_clients: set[str] | None = None,
) -> list[Middleware]:
    """Assembles the standard middleware stack.

    Parameters
    ----------
    service_name:
        Used as the service name in Zipkin traces (e.g. ``"clinical-mdr-api"``).
    include_cors:
        Whether to add ``CORSMiddleware``. ``consumer_api`` omits it.
    tracing_exclude_clients:
        IP addresses the tracing middleware should ignore. ``clinical_mdr_api`` passes
        ``None`` (no exclusions); the other three pass ``{"127.0.0.1", "::1"}``.
    """

    middlewares: list[Middleware] = []

    # GZip — compress large responses
    if settings.gzip_response_min_size:
        middlewares.append(
            Middleware(
                GZipMiddleware,
                minimum_size=settings.gzip_response_min_size,
                compresslevel=settings.gzip_level,
            )
        )

    # Context — must come before TracingMiddleware
    middlewares.append(Middleware(RawContextMiddleware))

    # Tracing
    if settings.tracing_enabled:
        if settings.appinsights_connection:
            tracing_exporter = AzureExporter(
                connection_string=settings.appinsights_connection,
                enable_local_storage=False,
            )
        elif settings.zipkin_host:
            # opencensus-ext-zipkin is a dev-only dependency
            from opencensus.ext.zipkin.trace_exporter import (  # pylint: disable=import-outside-toplevel
                ZipkinExporter,
            )

            tracing_exporter = ZipkinExporter(
                service_name=service_name,
                host_name=settings.zipkin_host,
                port=settings.zipkin_port,
                endpoint=settings.zipkin_endpoint,
                protocol=settings.zipkin_protocol,
            )
        else:
            tracing_exporter = PrintExporter()

        tracing_kwargs: dict[str, Any] = {
            "sampler": AlwaysOnSampler(),
            "exporter": tracing_exporter,
            "exclude_paths": {"*/system/healthcheck"},
        }
        if tracing_exclude_clients is not None:
            tracing_kwargs["exclude_clients"] = tracing_exclude_clients

        middlewares.append(Middleware(TracingMiddleware, **tracing_kwargs))
        patch_neomodel_database()

    # CORS
    if include_cors:
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

    # Exception traceback — convert uncaught exceptions before TracingMiddleware sees them
    middlewares.append(Middleware(ExceptionTracebackMiddleware))

    return middlewares


def build_openapi_func(
    app: FastAPI,
    *,
    remove_422: bool = True,
    separate_input_output_schemas: bool | None = None,
):
    """Returns a ``custom_openapi()`` function tailored to ``app``.

    The returned function is meant to be assigned via
    ``setattr(app, "openapi", build_openapi_func(app, ...))``.

    Parameters
    ----------
    app:
        The FastAPI application whose schema is to be customised.
    remove_422:
        Whether to strip the ``422 Unprocessable Entity`` response from every endpoint.
        ``True`` for ``clinical_mdr_api`` and ``consumer_api``; ``False`` for the other
        two apps.
    separate_input_output_schemas:
        Forwarded to ``get_openapi(separate_input_output_schemas=...)``.  Pass the value
        from ``app.separate_input_output_schemas`` for apps that set it (only
        ``clinical_mdr_api`` sets this attribute; others pass ``None`` and the kwarg is
        omitted entirely, preserving the old behaviour).
    """

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        get_openapi_kwargs: dict[str, Any] = {
            "title": app.title,
            "version": app.version,
            "openapi_version": app.openapi_version,
            "description": app.description,
            "routes": app.routes,
        }
        if separate_input_output_schemas is not None:
            get_openapi_kwargs["separate_input_output_schemas"] = (
                separate_input_output_schemas
            )

        openapi_schema = get_openapi(**get_openapi_kwargs)

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
                "bearerFormat": "JWT",
                "in": "header",
                "name": "Authorization",
                "description": (
                    "Access token that will be sent as `Authorization: Bearer {token}` "
                    "header in all requests"
                ),
            }
            openapi_schema["components"]["securitySchemes"][
                "OAuth2AuthorizationCodeBearer"
            ]["flows"]["authorizationCode"]["scopes"] = {
                "api:///API.call": "Make calls to the API"
            }

            # Stamp BearerJwtAuth onto routes protected by the security dependency
            api_routes = [route for route in app.routes if isinstance(route, APIRoute)]
            for route in api_routes:
                if not any(dep for dep in route.dependencies if dep == security):
                    continue
                path = getattr(route, "path")
                methods = [method.lower() for method in getattr(route, "methods")]
                for method in methods:
                    endpoint_security: list[Any] = openapi_schema["paths"][path][
                        method
                    ].get("security", [])
                    endpoint_security.append({"BearerJwtAuth": []})
                    openapi_schema["paths"][path][method][
                        "security"
                    ] = endpoint_security

        # Response cleanup: always add 400, optionally drop 422
        for path_item in openapi_schema["paths"].values():
            for operation in path_item.values():
                if "responses" not in operation:
                    operation["responses"] = {}
                if remove_422:
                    operation["responses"].pop("422", None)
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

    return custom_openapi


def register_exception_handlers(
    app: FastAPI,
    *,
    http_exception_class: type[Exception] | None = None,
    include_value_error: bool = True,
    validation_error_include_headers: bool = True,
) -> None:
    """Registers the standard exception handlers on ``app``.

    Parameters
    ----------
    http_exception_class:
        If provided, registers an HTTPException handler for this class.
        ``clinical_mdr_api`` passes ``StarletteHTTPException``; ``consumer_api`` passes
        ``fastapi.HTTPException``; ``standards_import`` and ``extensions`` pass ``None``
        (no HTTPException handler registered, matching current behaviour).
    include_value_error:
        Whether to register a ``ValueError → 400`` handler.  ``consumer_api`` does not
        have one; the other three do.
    validation_error_include_headers:
        Whether to pass ``headers={}`` in the ``ValidationError`` 400 response.
        ``clinical_mdr_api`` and ``consumer_api`` pass it; ``standards_import`` and
        ``extensions`` do not.
    """

    if http_exception_class is not None:

        @app.exception_handler(http_exception_class)
        async def http_exception_handler(request: Request, exception: http_exception_class):  # type: ignore[valid-type]
            """Returns an HTTP error code associated to given exception."""
            await log_exception(request, exception)
            ExceptionTracebackMiddleware.add_traceback_attributes(exception)
            return JSONResponse(
                status_code=exception.status_code,
                content=jsonable_encoder(ErrorResponse(request, exception)),
                headers=exception.headers,
            )

    @app.exception_handler(MDRApiBaseException)
    async def mdr_api_exception_handler(
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
    async def handle_validation_error(
        request: Request, exception: ValidationError
    ) -> JSONResponse:
        await log_exception(request, exception)
        ExceptionTracebackMiddleware.add_traceback_attributes(exception)
        response_kwargs: dict[str, Any] = {
            "status_code": status.HTTP_400_BAD_REQUEST,
            "content": jsonable_encoder(ErrorResponse(request, exception)),
        }
        if validation_error_include_headers:
            response_kwargs["headers"] = {}
        return JSONResponse(**response_kwargs)

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

    if include_value_error:

        @app.exception_handler(ValueError)
        async def value_error_handler(request: Request, exception: ValueError):
            """Returns ``400 Bad Request`` if a ``ValueError`` is raised."""
            await log_exception(request, exception)
            ExceptionTracebackMiddleware.add_traceback_attributes(exception)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=jsonable_encoder(ErrorResponse(request, exception)),
            )
