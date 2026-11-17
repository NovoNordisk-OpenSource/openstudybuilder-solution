"""Standards import API application."""

# Placed at the top to ensure logging is configured before anything else is loaded
from common.config import settings
from common.database import configure_database
from common.logger import default_logging_config

default_logging_config()

configure_database(
    settings.neo4j_dsn,
    soft_cardinality_check=settings.soft_cardinality_check,
    max_connection_lifetime=settings.neo4j_connection_lifetime,
    liveness_check_timeout=settings.neo4j_liveness_check_timeout,
)

# pylint: disable=wrong-import-position,wrong-import-order,ungrouped-imports
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool

from common.app_factory import (
    build_middlewares,
    build_openapi_func,
    register_exception_handlers,
)
from common.auth.discovery import reconfigure_with_openid_discovery
from common.database import log_rbac_guard_result
from standards_import.common import get_api_version
from standards_import.repositories import staging_db
from standards_import.routers import (
    codelists,
    effective_dates,
    imports,
    inconsistencies,
    jobs,
    package_files,
    resolution_rules,
    sponsor_impact,
    system as system_router_module,
    type_descriptions,
)
from standards_import.services import job_service

log = logging.getLogger(__name__)

middlewares = build_middlewares(
    service_name="standards-import-api",
    tracing_exclude_clients={"127.0.0.1", "::1"},
)


def _staging_connection_sees_only_cdiscstaging() -> bool:
    with staging_db.staging_session() as session:
        rows = staging_db.run_query(
            session, "MATCH (n) WHERE NOT n:CDISCStaging RETURN count(n) AS count"
        )
    return rows[0]["count"] == 0


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.oauth_enabled:
        # Reconfiguring Swagger UI settings with OpenID Connect discovery
        await reconfigure_with_openid_discovery()

    # Every job kind runs in a background task and so cannot outlive its process.
    # Anything still RUNNING from a previous life will never finish or record its own
    # failure, and would hold its release busy forever — a job kind's own status blocks
    # almost everything else about the release. Runs in a worker thread: the driver is
    # blocking, and this must not stall startup.
    try:
        await run_in_threadpool(job_service.fail_abandoned_jobs)
    except Exception:  # pylint: disable=broad-except
        # A staging database that is unreachable at boot must not stop the app coming
        # up; every endpoint that needs it reports the failure on its own.
        log.exception("Could not check for abandoned jobs at startup")

    try:
        # If the `staging` role from db/init_neo4j.py is active, this connection can
        # see :CDISCStaging nodes and nothing else. A non-zero count means either
        # Community edition or the roles are not provisioned yet, and the app must
        # keep working either way (this is defence in depth, not the isolation
        # mechanism). Runs in a worker thread: the raw driver is blocking.
        isolated = await run_in_threadpool(_staging_connection_sees_only_cdiscstaging)
        log_rbac_guard_result("staging connection sees only :CDISCStaging", isolated)
    except Exception:  # pylint: disable=broad-except
        log.exception("Could not check the RBAC guard status at startup")

    yield


app = FastAPI(
    title="OpenStudyBuilder Standards Import API",
    version=get_api_version(),
    middleware=middlewares,
    lifespan=lifespan,
    swagger_ui_init_oauth=settings.swagger_ui_init_oauth,
    swagger_ui_parameters={"docExpansion": "none"},
    description="""
## Purpose

Ingests CDISC controlled terminology packages into the OpenStudyBuilder MDR database.

A CDISC quarterly release is a set of catalogue files sharing one effective date.
Files are uploaded one at a time, but grouping and inconsistency detection run across
all catalogues of the same effective date — so the effective date, not the file, is
the unit of work.

Uploaded files land in a staging database where they are grouped by concept id and
checked for inconsistencies between catalogues. Nothing reaches the MDR database until
the effective date has been analysed and any open review items resolved.

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

app.include_router(system_router_module.router)
app.include_router(package_files.router)
app.include_router(package_files.discovery_router)
app.include_router(package_files.pairings_router)
app.include_router(package_files.changelog_router)
app.include_router(effective_dates.router)
app.include_router(sponsor_impact.router)
app.include_router(imports.router)
app.include_router(inconsistencies.router)
app.include_router(inconsistencies.options_router)
app.include_router(resolution_rules.router)
app.include_router(jobs.router)
app.include_router(type_descriptions.router)
app.include_router(codelists.router)


register_exception_handlers(
    app,
    http_exception_class=None,  # SI has no HTTPException handler
    include_value_error=True,
    validation_error_include_headers=False,  # SI's ValidationError handler omits headers={}
)

setattr(app, "openapi", build_openapi_func(app, remove_422=False))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "standards_import.main:app",
        host=os.getenv("UVICORN_HOST", "127.0.0.1"),
        port=int(os.getenv("UVICORN_PORT", "8010")),
        reload=True,
    )
