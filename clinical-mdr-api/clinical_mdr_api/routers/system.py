"""System router."""

import os

from fastapi import APIRouter
from fastapi.responses import FileResponse, PlainTextResponse

from clinical_mdr_api.models.feature_flag import FeatureFlag
from clinical_mdr_api.models.notification import Notification
from clinical_mdr_api.models.system import SystemInformation
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services import system as service
from clinical_mdr_api.services.feature_flags import FeatureFlagService
from clinical_mdr_api.services.notifications import NotificationService
from common import config

# Mounted under "/system" path as a sub-application, endpoints do not require authentication.
router = APIRouter()


@router.get(
    "/information",
    summary="Returns various information about this API (running version, etc.)",
    response_model=SystemInformation,
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
    filepath = os.path.join(config.APP_ROOT_DIR, filename)
    return FileResponse(path=filepath, media_type="text/markdown", filename=filename)


@router.get(
    "/information/license.md",
    summary="Returns license as markdown text",
    response_class=FileResponse,
    status_code=200,
)
def get_license_md() -> FileResponse:
    filename = "LICENSE.md"
    filepath = os.path.join(config.APP_ROOT_DIR, filename)
    return FileResponse(path=filepath, media_type="text/markdown", filename=filename)


@router.get(
    "/feature-flags",
    summary="Returns all feature flags.",
    response_model=list[FeatureFlag],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_feature_flags() -> list[FeatureFlag]:
    return FeatureFlagService().get_all_feature_flags()


@router.get(
    "/notifications",
    summary="Returns all notifications that are both published and in the specified time.",
    response_model=list[Notification],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_active_notifications() -> list[Notification]:
    return NotificationService().get_all_active_notifications()
