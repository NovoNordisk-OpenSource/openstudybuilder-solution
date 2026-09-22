"""System router."""

import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse

from common import templating
from common.config import settings
from consumer_api.shared.common import get_api_version
from consumer_api.system import service

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def root(request: Request):
    root_path = os.environ.get("UVICORN_ROOT_PATH", "").strip("/")

    if str(request.base_url).endswith("/" + root_path):
        root_path = ""
    else:
        root_path = "/" + root_path

    return templating.templates.TemplateResponse(
        request,
        "pages/api-welcome.html",
        {
            "request": request,
            "data": {
                "app_name": "OpenStudyBuilder Consumer API",
                "version": get_api_version(),
                "root_path": root_path,
            },
        },
    )


@router.get(
    "/system/information",
    summary="Returns various information about this API (running version, etc.)",
    status_code=200,
)
def get_system_information() -> service.SystemInformation:
    return service.get_system_information()


@router.get(
    "/system/information/build-id",
    summary="Returns build id as plain text",
    status_code=200,
)
async def get_build_id() -> str:
    return service.get_build_id()


@router.get(
    "/system/healthcheck",
    summary="Returns 200 OK status if the system is ready to serve requests",
    status_code=200,
)
async def healthcheck() -> str:
    return "OK"


@router.get(
    "/system/information/sbom.md",
    summary="Returns SBOM as markdown text",
    response_class=FileResponse,
    status_code=200,
)
async def get_sbom_md() -> FileResponse:
    filename = "sbom.md"
    filepath = os.path.join(settings.app_root_dir, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail=f"file not found: {filename}")
    return FileResponse(path=filepath, media_type="text/markdown", filename=filename)


@router.get(
    "/system/information/license.md",
    summary="Returns license as markdown text",
    response_class=FileResponse,
    status_code=200,
)
async def get_license_md() -> FileResponse:
    filename = "LICENSE.md"
    filepath = os.path.join(settings.app_root_dir, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail=f"file not found: {filename}")
    return FileResponse(path=filepath, media_type="text/markdown", filename=filename)
