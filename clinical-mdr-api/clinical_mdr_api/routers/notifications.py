# pylint: disable=invalid-name
from typing import Annotated

from fastapi import APIRouter, Body, Path

from clinical_mdr_api.models.notification import (
    Notification,
    NotificationPatchInput,
    NotificationPostInput,
)
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.notifications import NotificationService
from common.auth import rbac

# Prefixed with "/notifications"
router = APIRouter()

SN = Path(title="Serial Number of the notification")

service = NotificationService()


@router.get(
    "",
    dependencies=[rbac.ADMIN_READ],
    summary="Returns all notifications.",
    response_model=list[Notification],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_notifications() -> list[Notification]:
    return service.get_all_notifications()


@router.get(
    "/{serial_number}",
    dependencies=[rbac.ADMIN_READ],
    summary="Returns the notification identified by the provided Serial Number.",
    response_model=Notification,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.validate_serial_number_against_neo4j_max_and_min_int()
def get_notification(serial_number: Annotated[int, SN]) -> Notification:
    return service.get_notification(serial_number)


@router.post(
    "",
    dependencies=[rbac.ADMIN_WRITE],
    summary="Creates a notification.",
    response_model=Notification,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def create_notification(
    notification_input: Annotated[NotificationPostInput, Body()],
) -> Notification:
    return service.create_notification(notification_input)


@router.patch(
    "/{serial_number}",
    dependencies=[rbac.ADMIN_WRITE],
    summary="Updates the notification identified by the provided Serial Number.",
    response_model=Notification,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.validate_serial_number_against_neo4j_max_and_min_int()
def update_notification(
    serial_number: Annotated[int, SN],
    notification_input: Annotated[NotificationPatchInput, Body()],
) -> Notification:
    return service.update_notification(serial_number, notification_input)


@router.delete(
    "/{serial_number}",
    dependencies=[rbac.ADMIN_WRITE],
    summary="Deletes the notification identified by the provided Serial Number.",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.validate_serial_number_against_neo4j_max_and_min_int()
def delete_notification(serial_number: Annotated[int, SN]) -> None:
    return service.delete_notification(serial_number)
