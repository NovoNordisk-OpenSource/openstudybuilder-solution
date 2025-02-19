"""System router."""

import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse

from consumer_api.shared.common import APP_ROOT_DIR
from consumer_api.system import service

# Mounted under "/system" path as a sub-application, endpoints do not require authentication.
router = APIRouter()


@router.get(
    "/information",
    summary="Returns various information about this API (running version, etc.)",
    response_model=service.SystemInformation,
    status_code=200,
)
def get_system_information():
    return service.get_system_information()


@router.get(
    "/information/build-id",
    summary="Returns build id as plain text",
    response_class=PlainTextResponse,
    status_code=200,
)
def get_build_id() -> str:
    return service.get_build_id()


@router.get(
    "/healthcheck",
    summary="Returns 200 OK status if the system is ready to serve requests",
    response_class=PlainTextResponse,
    status_code=200,
)
def healthcheck():
    return "OK"


@router.get(
    "/information/sbom.md",
    summary="Returns SBOM as markdown text",
    response_class=FileResponse,
    status_code=200,
)
def get_sbom_md() -> FileResponse:
    filename = "sbom.md"
    filepath = os.path.join(APP_ROOT_DIR, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail=f"file not found: {filename}")
    return FileResponse(path=filepath, media_type="text/markdown", filename=filename)


@router.get(
    "/information/license.md",
    summary="Returns license as markdown text",
    response_class=FileResponse,
    status_code=200,
)
def get_license_md() -> FileResponse:
    filename = "LICENSE.md"
    filepath = os.path.join(APP_ROOT_DIR, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail=f"file not found: {filename}")
    return FileResponse(path=filepath, media_type="text/markdown", filename=filename)
