"""Minimal system router for the standards-import standalone app.

Serves `GET /system/healthcheck` so the Dockerfile HEALTHCHECK_PATH is reachable
when standards-import runs as its own process on port 8010.

The main clinical_mdr_api already provides a full system router (including
`/system/information`, SBOM endpoint, etc.) — those are not duplicated here; this
module only adds what is needed for the standalone deployment's liveness check.
"""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["System"])


@router.get(
    "/system/healthcheck",
    summary="Returns 200 OK if the standards-import service is ready to serve requests",
    response_class=PlainTextResponse,
    status_code=200,
)
async def healthcheck() -> str:
    return "OK"
