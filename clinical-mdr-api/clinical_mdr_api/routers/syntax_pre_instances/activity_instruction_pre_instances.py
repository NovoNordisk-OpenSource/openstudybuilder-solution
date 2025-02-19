from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query, Request, Response
from fastapi import status as fast_api_status
from pydantic.types import Json

from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.syntax_pre_instances.activity_instruction_pre_instance import (
    ActivityInstructionPreInstance,
    ActivityInstructionPreInstanceEditInput,
    ActivityInstructionPreInstanceIndexingsInput,
    ActivityInstructionPreInstanceVersion,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.syntax_pre_instances.activity_instruction_pre_instances import (
    ActivityInstructionPreInstanceService,
)
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

ActivityInstructionPreInstanceUID = Path(
    description="The unique id of the Activity Instruction Pre-Instance."
)

# Prefixed with "/activity-instruction-pre-instances"
router = APIRouter()

Service = ActivityInstructionPreInstanceService


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all syntax Pre-Instances in their latest/newest version.",
    description="Allowed parameters include : filter on fields, sort by field name with sort direction, pagination",
    response_model=CustomPage[ActivityInstructionPreInstance],
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "library=library.name",
            "uid",
            "sequence_id",
            "activity_instruction_template=template_name",
            "name",
            "indications",
            "activities",
            "activity_groups",
            "activity_subgroups",
            "start_date",
            "end_date",
            "status",
            "version",
            "change_description",
            "author_username",
        ],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def activity_instruction_pre_instances(
    request: Request,  # request is actually required by the allow_exports decorator
    status: Annotated[
        LibraryItemStatus | None,
        Query(
            description="If specified, only those Syntax Pre-Instances will be returned that are currently in the specified status. "
            "This may be particularly useful if the Activity Instruction Pre-Instance has "
            "a 'Draft' and a 'Final' status or and you are interested in the 'Final' status.\n"
            "Valid values are: 'Final' or 'Draft'.",
        ),
    ] = None,
    sort_by: Annotated[
        Json | None, Query(description=_generic_descriptions.SORT_BY)
    ] = None,
    page_number: Annotated[
        int | None, Query(ge=1, description=_generic_descriptions.PAGE_NUMBER)
    ] = config.DEFAULT_PAGE_NUMBER,
    page_size: Annotated[
        int | None,
        Query(
            ge=0,
            le=config.MAX_PAGE_SIZE,
            description=_generic_descriptions.PAGE_SIZE,
        ),
    ] = config.DEFAULT_PAGE_SIZE,
    filters: Annotated[
        Json | None,
        Query(
            description=_generic_descriptions.SYNTAX_FILTERS,
            openapi_examples=_generic_descriptions.FILTERS_EXAMPLE,
        ),
    ] = None,
    operator: Annotated[
        str | None, Query(description=_generic_descriptions.FILTER_OPERATOR)
    ] = config.DEFAULT_FILTER_OPERATOR,
    total_count: Annotated[
        bool | None, Query(description=_generic_descriptions.TOTAL_COUNT)
    ] = False,
):
    results = ActivityInstructionPreInstanceService().get_all(
        status=status,
        return_study_count=True,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
    )

    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/headers",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=list[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_values_for_header(
    field_name: Annotated[
        str, Query(description=_generic_descriptions.HEADER_FIELD_NAME)
    ],
    status: Annotated[
        LibraryItemStatus | None,
        Query(
            description="If specified, only those Syntax Pre-Instances will be returned that are currently in the specified status. "
            "This may be particularly useful if the Activity Instruction Pre-Instance has "
            "a 'Draft' and a 'Final' status or and you are interested in the 'Final' status.\n"
            "Valid values are: 'Final' or 'Draft'.",
        ),
    ] = None,
    search_string: Annotated[
        str | None, Query(description=_generic_descriptions.HEADER_SEARCH_STRING)
    ] = "",
    filters: Annotated[
        Json | None,
        Query(
            description=_generic_descriptions.SYNTAX_FILTERS,
            openapi_examples=_generic_descriptions.FILTERS_EXAMPLE,
        ),
    ] = None,
    operator: Annotated[
        str | None, Query(description=_generic_descriptions.FILTER_OPERATOR)
    ] = config.DEFAULT_FILTER_OPERATOR,
    page_size: Annotated[
        int | None, Query(description=_generic_descriptions.HEADER_PAGE_SIZE)
    ] = config.DEFAULT_HEADER_PAGE_SIZE,
):
    return Service().get_distinct_values_for_header(
        status=status,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/audit-trail",
    dependencies=[rbac.LIBRARY_READ],
    response_model=CustomPage[ActivityInstructionPreInstance],
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def retrieve_audit_trail(
    page_number: Annotated[
        int | None, Query(ge=1, description=_generic_descriptions.PAGE_NUMBER)
    ] = config.DEFAULT_PAGE_NUMBER,
    page_size: Annotated[
        int | None,
        Query(
            ge=0,
            le=config.MAX_PAGE_SIZE,
            description=_generic_descriptions.PAGE_SIZE,
        ),
    ] = config.DEFAULT_PAGE_SIZE,
    filters: Annotated[
        Json | None,
        Query(
            description=_generic_descriptions.SYNTAX_FILTERS,
            openapi_examples=_generic_descriptions.FILTERS_EXAMPLE,
        ),
    ] = None,
    operator: Annotated[
        str | None, Query(description=_generic_descriptions.FILTER_OPERATOR)
    ] = config.DEFAULT_FILTER_OPERATOR,
    total_count: Annotated[
        bool | None, Query(description=_generic_descriptions.TOTAL_COUNT)
    ] = False,
):
    results = Service().get_all(
        page_number=page_number,
        page_size=page_size,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        total_count=total_count,
        for_audit_trail=True,
    )

    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/{activity_instruction_pre_instance_uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the latest/newest version of a specific activity instruction pre-instance identified by 'activity_instruction_pre_instance_uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    response_model=ActivityInstructionPreInstance | None,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - "
            "The activity instruction pre-instance with the specified 'activity_instruction_pre_instance_uid' (and the specified date/time and/or status) wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get(
    activity_instruction_pre_instance_uid: Annotated[
        str, ActivityInstructionPreInstanceUID
    ],
):
    return ActivityInstructionPreInstanceService().get_by_uid(
        uid=activity_instruction_pre_instance_uid
    )


@router.patch(
    "/{activity_instruction_pre_instance_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Updates the Activity Instruction Pre-Instance identified by 'activity_instruction_pre_instance_uid'.",
    description="""This request is only valid if the Activity Instruction Pre-Instance
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.
* The link to the objective will remain as is.
""",
    response_model=ActivityInstructionPreInstance,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The Activity Instruction Pre-Instance is not in draft status.\n"
            "- The Activity Instruction Pre-Instance had been in 'Final' status before.\n"
            "- The provided list of parameters is invalid.\n"
            "- The library doesn't allow to edit draft versions.\n"
            "- The Activity Instruction Pre-Instance does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Activity Instruction Pre-Instance with the specified 'activity_instruction_pre_instance_uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit(
    activity_instruction_pre_instance_uid: Annotated[
        str, ActivityInstructionPreInstanceUID
    ],
    activity_instruction_pre_instance: Annotated[
        ActivityInstructionPreInstanceEditInput,
        Body(
            description="The new parameter terms for the Activity Instruction Pre-Instance, its indexings and the change description.",
        ),
    ] = None,
):
    return Service().edit_draft(
        uid=activity_instruction_pre_instance_uid,
        template=activity_instruction_pre_instance,
    )


@router.patch(
    "/{activity_instruction_pre_instance_uid}/indexings",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Updates the indexings of the Activity Instruction Pre-Instance identified by 'activity_instruction_pre_instance_uid'.",
    description="""This request is only valid if the Pre-Instance
    * belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).
    
    This is version independent : it won't trigger a status or a version change.
    """,
    response_model=ActivityInstructionPreInstance,
    status_code=200,
    responses={
        200: {
            "description": "No content - The indexings for this Pre-Instance were successfully updated."
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Pre-Instance with the specified 'activity_instruction_pre_instance_uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_indexings(
    activity_instruction_pre_instance_uid: Annotated[
        str, ActivityInstructionPreInstanceUID
    ],
    indexings: Annotated[
        ActivityInstructionPreInstanceIndexingsInput,
        Body(
            description="The lists of UIDs for the new indexings to be set, grouped by indexings to be updated.",
        ),
    ] = None,
) -> ActivityInstructionPreInstance:
    return Service().patch_indexings(
        uid=activity_instruction_pre_instance_uid, indexings=indexings
    )


@router.get(
    "/{activity_instruction_pre_instance_uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the version history of a specific Activity Instruction Pre-Instance identified by 'activity_instruction_pre_instance_uid'.",
    description=f"""
The returned versions are ordered by `start_date` descending (newest entries first).

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=list[ActivityInstructionPreInstanceVersion],
    status_code=200,
    responses={
        200: {"description": "OK."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Activity Instruction Pre-Instance with the specified 'activity_instruction_pre_instance_uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "text/csv": [
            "library=library.name",
            "activity_instruction_template=activity_instruction_template.uid",
            "uid",
            "name_plain",
            "name",
            "start_date",
            "end_date",
            "status",
            "version",
            "change_description",
            "author_username",
        ],
        "text/xml": [
            "library=library.name",
            "activity_instruction_template=activity_instruction_template.name",
            "objective=objective.name",
            "uid",
            "name_plain",
            "name",
            "start_date",
            "end_date",
            "status",
            "version",
            "change_description",
            "author_username",
        ],
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
            "library=library.name",
            "activity_instruction_template=activity_instruction_template.uid",
            "uid",
            "name_plain",
            "name",
            "start_date",
            "end_date",
            "status",
            "version",
            "change_description",
            "author_username",
        ],
    }
)
# pylint: disable=unused-argument
def get_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    activity_instruction_pre_instance_uid: Annotated[
        str, ActivityInstructionPreInstanceUID
    ],
):
    return Service().get_version_history(activity_instruction_pre_instance_uid)


@router.post(
    "/{activity_instruction_pre_instance_uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new version of the Activity Instruction Pre-Instance identified by 'activity_instruction_pre_instance_uid'.",
    description="""This request is only valid if the Activity Instruction Pre-Instance
* is in 'Final' or 'Retired' status only (so no latest 'Draft' status exists) and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The latest 'Final' or 'Retired' version will remain the same as before.
* The status of the new version will be automatically set to 'Draft'.
* The 'version' property of the new version will be automatically set to the version of the latest 'Final' or 'Retired' version increased by +0.1.

Parameters in the 'name' property cannot be changed with this request.
Only the surrounding text (excluding the parameters) can be changed.
""",
    response_model=ActivityInstructionPreInstance,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The Activity Instruction Pre-Instance is not in final or retired status or has a draft status.\n"
            "- The Activity Instruction Pre-Instance name is not valid.\n"
            "- The library doesn't allow to create a new version.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Activity Instruction Pre-Instance with the specified 'activity_instruction_pre_instance_uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_new_version(
    activity_instruction_pre_instance_uid: Annotated[
        str, ActivityInstructionPreInstanceUID
    ],
):
    return Service().create_new_version(uid=activity_instruction_pre_instance_uid)


@router.delete(
    "/{activity_instruction_pre_instance_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Inactivates/deactivates the activity instruction pre-instance identified by 'activity_instruction_pre_instance_uid'.",
    description="""This request is only valid if the activity instruction pre-instance
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=ActivityInstructionPreInstance,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity instruction pre-instance is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instruction pre-instance with the specified 'activity_instruction_pre_instance_uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def inactivate(
    activity_instruction_pre_instance_uid: Annotated[
        str, ActivityInstructionPreInstanceUID
    ],
):
    return ActivityInstructionPreInstanceService().inactivate_final(
        activity_instruction_pre_instance_uid
    )


@router.post(
    "/{activity_instruction_pre_instance_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivates the activity instruction pre-instance identified by 'activity_instruction_pre_instance_uid'.",
    description="""This request is only valid if the activity instruction pre-instance
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=ActivityInstructionPreInstance,
    status_code=200,
    responses={
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity instruction pre-instance is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instruction pre-instance with the specified 'activity_instruction_pre_instance_uid' wasn't found.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def reactivate(
    activity_instruction_pre_instance_uid: Annotated[
        str, ActivityInstructionPreInstanceUID
    ],
):
    return ActivityInstructionPreInstanceService().reactivate_retired(
        activity_instruction_pre_instance_uid
    )


@router.delete(
    "/{activity_instruction_pre_instance_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Deletes the Activity Instruction Pre-Instance identified by 'activity_instruction_pre_instance_uid'.",
    description="""This request is only valid if \n
* the Activity Instruction Pre-Instance is in 'Draft' status and
* the Activity Instruction Pre-Instance has never been in 'Final' status and
* the Activity Instruction Pre-Instance belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        204: {
            "description": "No Content - The Activity Instruction Pre-Instance was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The Activity Instruction Pre-Instance is not in draft status.\n"
            "- The Activity Instruction Pre-Instance was already in final state or is in use.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An Activity Instruction Pre-Instance with the specified uid could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete(
    activity_instruction_pre_instance_uid: Annotated[
        str, ActivityInstructionPreInstanceUID
    ],
):
    Service().soft_delete(activity_instruction_pre_instance_uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)


@router.post(
    "/{activity_instruction_pre_instance_uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approves the Activity Instruction Pre-Instance identified by 'activity_instruction_pre_instance_uid'.",
    description="""This request is only valid if the Activity Instruction Pre-Instance
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=ActivityInstructionPreInstance,
    status_code=201,
    responses={
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The Activity Instruction Pre-Instance is not in draft status.\n"
            "- The library doesn't allow to approve Activity Instruction Pre-Instances.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Activity Instruction Pre-Instance with the specified 'activity_instruction_pre_instance_uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve(
    activity_instruction_pre_instance_uid: Annotated[
        str, ActivityInstructionPreInstanceUID
    ],
):
    return Service().approve(activity_instruction_pre_instance_uid)
