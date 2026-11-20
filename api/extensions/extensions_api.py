"""RESTful API endpoints that extend the main API functionality"""

# Placed at the top to ensure logging is configured before anything else is loaded
import importlib
import sys

from common.config import settings
from common.logger import default_logging_config
from extensions.common import get_api_version

default_logging_config()


import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from common.app_factory import (
    build_middlewares,
    build_openapi_func,
    register_exception_handlers,
)
from common.auth.discovery import reconfigure_with_openid_discovery
from common.database import configure_app_database

log = logging.getLogger(__name__)

# Configure Neo4J connection on startup
configure_app_database(settings.neo4j_dsn)

middlewares = build_middlewares(
    service_name="extension-api",
    tracing_exclude_clients={"127.0.0.1", "::1"},
)


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

app.openapi_version = "3.1.0"


register_exception_handlers(
    app,
    http_exception_class=None,  # extensions has no HTTPException handler
    include_value_error=True,
    validation_error_include_headers=False,  # extensions omits headers={} on ValidationError
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
                    log.exception(
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


load_extensions()

# `custom_openapi` is kept as a module-level name for backwards compatibility — tests
# import it by name (`from extensions.extensions_api import custom_openapi`).
custom_openapi = build_openapi_func(app, remove_422=False)
setattr(app, "openapi", custom_openapi)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "extensions.extensions_api:app",
        host=os.getenv("UVICORN_HOST", "127.0.0.1"),
        port=int(os.getenv("UVICORN_PORT", "8009")),
        reload=True,
    )
