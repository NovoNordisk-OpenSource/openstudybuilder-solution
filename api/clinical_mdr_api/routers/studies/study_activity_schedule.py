from typing import Annotated

from fastapi import Body, Query

from clinical_mdr_api.models.study_selections.study_selection import (
    StudyActivitySchedule,
    StudyActivityScheduleBatchInput,
    StudyActivityScheduleBatchOutput,
    StudyActivityScheduleCreateInput,
    StudyActivityScheduleHistory,
)
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.routers import study_router as router
from clinical_mdr_api.routers.studies import utils
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.models.error import ErrorResponse


@router.get(
    "/studies/{study_uid}/study-activity-schedules",
    dependencies=[security, rbac.STUDY_READ],
    summary="List all study activity schedules currently defined for the study",
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there is no study with the given uid.",
        },
    },
)
def get_all_selected_activities(
    study_uid: Annotated[str, utils.studyUID],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
    operational: Annotated[
        bool | None,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="List scheduled study activity instances instead of study activities",
        ),
    ] = False,
) -> list[StudyActivitySchedule]:
    service = StudyActivityScheduleService()
    return service.get_all_schedules(
        study_uid=study_uid,
        study_value_version=study_value_version,
        operational=operational,
    )


@router.post(
    "/studies/{study_uid}/study-activity-schedules",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Add a study activity schedule to a study",
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - A study activity schedule already exists for selected study activity and visit",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study, study activity or study visit is not found with the passed 'study_uid'.",
        },
    },
)
def post_new_activity_schedule_create(
    study_uid: Annotated[str, utils.studyUID],
    selection: Annotated[
        StudyActivityScheduleCreateInput,
        Body(description="Related parameters of the schedule that shall be created."),
    ],
) -> StudyActivitySchedule:
    service = StudyActivityScheduleService()
    return service.create(study_uid=study_uid, schedule_input=selection)


@router.delete(
    "/studies/{study_uid}/study-activity-schedules/{study_activity_schedule_uid}",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Delete a study activity schedule",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity schedule and the study provided.",
        },
    },
)
def delete_activity_schedule(
    study_uid: Annotated[str, utils.studyUID],
    study_activity_schedule_uid: Annotated[str, utils.study_activity_schedule_uid],
):
    service = StudyActivityScheduleService()
    service.delete(study_uid=study_uid, schedule_uid=study_activity_schedule_uid)


@router.get(
    "/studies/{study_uid}/study-activity-schedules/audit-trail/",
    dependencies=[security, rbac.STUDY_READ],
    summary="List full audit trail related to definition of all study activity schedules.",
    description="""
The following values should be returned for all study activities:
- date_time
- author_username
- action
- activity
- order
    """,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_schedules_audit_trail(
    study_uid: Annotated[str, utils.studyUID],
) -> list[StudyActivityScheduleHistory]:
    service = StudyActivityScheduleService()
    return service.get_all_schedules_audit_trail(study_uid=study_uid)


@router.post(
    "/studies/{study_uid}/study-activity-schedules/batch",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Batch operations (create, delete) for study activity schedules",
    status_code=207,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def activity_schedule_batch_operations(
    study_uid: Annotated[str, utils.studyUID],
    operations: Annotated[
        list[StudyActivityScheduleBatchInput],
        Body(description="List of operation to perform"),
    ],
) -> list[StudyActivityScheduleBatchOutput]:
    service = StudyActivityScheduleService()
    return service.handle_batch_operations(study_uid, operations)
