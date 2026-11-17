"""RESTful API endpoints used by consumers that want to extract data from OpenStudyBuilder"""

# Placed at the top to ensure logging is configured before anything else is loaded
from common.config import settings
from common.database import configure_app_database
from common.logger import default_logging_config

default_logging_config()

configure_app_database(settings.neo4j_dsn)


import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.exceptions import HTTPException as StarletteHTTPException

from common.app_factory import (
    build_middlewares,
    build_openapi_func,
    register_exception_handlers,
)
from common.auth.discovery import reconfigure_with_openid_discovery
from consumer_api.shared.common import get_api_version
from consumer_api.system.routes import router as system_router
from consumer_api.v1.main import router as v1_router

# from consumer_api.v2.main import router as v2_router

log = logging.getLogger(__name__)

middlewares = build_middlewares(
    service_name="consumer-api",
    include_cors=False,  # consumer_api does not include CORSMiddleware
    tracing_exclude_clients={"127.0.0.1", "::1"},
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.oauth_enabled:
        # Reconfiguring Swagger UI settings with OpenID Connect discovery
        await reconfigure_with_openid_discovery()
    yield


app = FastAPI(
    title="OpenStudyBuilder Consumer API",
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

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Licenses and Acknowledgements for Incorporated Software

This component contains software licensed under different licenses when compiled, please refer to the third-party-licenses.md file for further information and full license texts.

## Authentication

Supports OAuth2 [Authorization Code Flow](https://datatracker.ietf.org/doc/html/rfc6749#section-4.1),
at paths described in the OpenID Connect Discovery metadata document (whose URL is defined by the `OAUTH_METADATA_URL` environment variable).

Microsoft Identity Platform documentation can be read 
([here](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow)).
""",
)


register_exception_handlers(
    app,
    # Starlette's HTTPException (parent of fastapi.HTTPException) also covers errors
    # raised inside FastAPI's request-body parsing machinery
    http_exception_class=StarletteHTTPException,
    include_value_error=False,  # consumer_api has no ValueError handler
    validation_error_include_headers=True,
)


app.include_router(system_router, tags=["System"])

app.include_router(v1_router, prefix="/v1")
# app.include_router(v2_router, prefix="/v2")


setattr(app, "openapi", build_openapi_func(app, remove_422=True))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "consumer_api.consumer_api:app",
        host=os.getenv("UVICORN_HOST", "127.0.0.1"),
        port=int(os.getenv("UVICORN_PORT", "8008")),
        reload=True,
    )
