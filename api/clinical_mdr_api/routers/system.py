"""System router."""

import os

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse

from clinical_mdr_api.models.system import SystemInformation
from clinical_mdr_api.services import system as service
from clinical_mdr_api.utils.api_version import get_api_version
from common import templating
from common.config import settings

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
                "app_name": settings.app_name,
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
def get_system_information() -> SystemInformation:
    return service.get_system_information()


@router.get(
    "/system/information/build-id",
    summary="Returns build id as plain text",
    response_class=PlainTextResponse,
    status_code=200,
)
async def get_build_id() -> str:
    return service.get_build_id()


@router.get(
    "/system/healthcheck",
    summary="Returns 200 OK status if the system is ready to serve requests",
    response_class=PlainTextResponse,
    status_code=200,
)
async def healthcheck():
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
    return FileResponse(path=filepath, media_type="text/markdown", filename=filename)
