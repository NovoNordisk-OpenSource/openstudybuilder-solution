"""ActivitySubGroup router."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query, Response, status
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivitySubGroup,
    ActivitySubGroupCreateInput,
    ActivitySubGroupEditInput,
    ActivitySubGroupOverview,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers.responses import YAMLResponse
from clinical_mdr_api.services.concepts.activities.activity_sub_group_service import (
    ActivitySubGroupService,
)
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/concepts/activities"
router = APIRouter()

ActivitySubGroupUID = Path(description="The unique id of the ActivitySubGroup")


@router.get(
    "/activity-sub-groups",
    dependencies=[rbac.LIBRARY_READ],
    summary="List all activity sub groups (for a given library)",
    description="""
State before:
 - The library must exist (if specified)

Business logic:
 - List all activities sub groups in their latest version, including properties derived from linked control terminology.

State after:
 - No change

Possible errors:
 - Invalid library name specified.""",
    response_model=CustomPage[ActivitySubGroup],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_activity_subgroups(
    library_name: Annotated[str | None, Query()] = None,
    activity_group_uid: Annotated[
        str | None, Query(description="The unique id of the activity group")
    ] = None,
    activity_group_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity group names to use as a specific filter",
            alias="activity_group_names[]",
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
            description=_generic_descriptions.FILTERS,
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
    activity_subgroup_service = ActivitySubGroupService()
    results = activity_subgroup_service.get_all_concepts(
        library=library_name,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        activity_group_uid=activity_group_uid,
        activity_group_names=activity_group_names,
    )
    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/activity-sub-groups/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List all versions of all activity subgroups (for a given library)",
    description="""
State before:
 - The library must exist (if specified)

Business logic:
 - List version history of all activity subgroups
 - The returned versions are ordered by version start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid library name specified.""",
    response_model=CustomPage[ActivitySubGroup],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_activity_subgroups_versions(
    library_name: Annotated[str | None, Query()] = None,
    activity_group_uid: Annotated[
        str | None, Query(description="The unique id of the activity group")
    ] = None,
    activity_group_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity group names to use as a specific filter",
            alias="activity_group_names[]",
        ),
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
            description=_generic_descriptions.FILTERS,
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
    activity_subgroup_service = ActivitySubGroupService()
    results = activity_subgroup_service.get_all_concept_versions(
        library=library_name,
        sort_by={"start_date": False},
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        activity_group_uid=activity_group_uid,
        activity_group_names=activity_group_names,
    )
    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/activity-sub-groups/headers",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns possible values from the database for a given header",
    description="Allowed parameters include : field name for which to get possible values, "
    "search string to provide filtering for the field name, additional filters to apply on other fields",
    response_model=list[Any],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
    },
)
def get_distinct_values_for_header(
    field_name: Annotated[
        str, Query(description=_generic_descriptions.HEADER_FIELD_NAME)
    ],
    library_name: Annotated[str | None, Query()] = None,
    search_string: Annotated[
        str | None, Query(description=_generic_descriptions.HEADER_SEARCH_STRING)
    ] = "",
    activity_group_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity group names to use as a specific filter",
            alias="activity_group_names[]",
        ),
    ] = None,
    activity_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity names to use as a specific filter",
            alias="activity_names[]",
        ),
    ] = None,
    filters: Annotated[
        Json | None,
        Query(
            description=_generic_descriptions.FILTERS,
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
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
        activity_group_names=activity_group_names,
        activity_names=activity_names,
    )


@router.get(
    "/activity-sub-groups/{activity_subgroup_uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get details on a specific activity sub group (in a specific version)",
    description="""
State before:
 - an activity sub group with uid must exist.

Business logic:
 - If parameter at_specified_date_time is specified then the latest/newest representation of the concept at this point in time is returned. The point in time needs to be specified in ISO 8601 format including the timezone, e.g.: '2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. If the timezone is ommitted, UTC�0 is assumed.
 - If parameter status is specified then the representation of the concept in that status is returned (if existent). This is useful if the concept has a status 'Draft' and a status 'Final'.
 - If parameter version is specified then the latest/newest representation of the concept in that version is returned. Only exact matches are considered. The version is specified in the following format: <major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0', ...

State after:
 - No change

Possible errors:
 - Invalid uid, at_specified_date_time, status or version.
 """,
    response_model=ActivitySubGroup,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_activity(
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
):
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.get_by_uid(uid=activity_subgroup_uid)


@router.get(
    "/activity-sub-groups/{activity_subgroup_uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List version history for activity sub groups",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for activity sub groups.
 - The returned versions are ordered by start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=list[ActivitySubGroup],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity sub group with the specified 'activity_subgroup_uid' wasn't found.",
        },
    },
)
def get_versions(
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
):
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.get_version_history(uid=activity_subgroup_uid)


@router.get(
    "/activity-sub-groups/{activity_subgroup_uid}/overview",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get detailed overview of a specific activity subgroup",
    description="""
Returns detailed description about activity subgroup including:
- Activity Subgroup details
- Linked Activities
- Version history

State before:
- UID must exist

State after:
- No change

Possible errors:
- Invalid uid
    """,
    response_model=ActivitySubGroupOverview,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": ["activity_subgroup", "activities", "all_versions"],
        "formats": ["application/x-yaml"],
    }
)
# pylint: disable=unused-argument
def get_activity_subgroup_overview(
    request: Request,
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
    version: Annotated[
        str | None,
        Query(description="Select specific version, omit to view latest version"),
    ] = None,
):
    if version == "":
        version = None

    service = ActivitySubGroupService()
    return service.get_subgroup_overview(
        subgroup_uid=activity_subgroup_uid, version=version
    )


@router.get(
    "/activity-sub-groups/{activity_subgroup_uid}/overview.cosmos",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get a COSMoS compatible representation of a specific activity subgroup",
    description="""
Returns detailed description about activity subgroup, including information about:
 - Activity Subgroup details
 - Linked activity groups
 - Linked activities

State before:
 - An activity subgroup with uid must exist.

State after:
 - No change

Possible errors:
 - Invalid uid.
 """,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"content": {"application/x-yaml": {}}},
        404: _generic_descriptions.ERROR_404,
    },
)
# pylint: disable=unused-argument
def get_cosmos_activity_subgroup_overview(
    request: Request,  # request is actually required by the YAMLResponse
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
):
    activity_subgroup_service = ActivitySubGroupService()
    return YAMLResponse(
        activity_subgroup_service.get_cosmos_subgroup_overview(
            subgroup_uid=activity_subgroup_uid
        )
    )


@router.post(
    "/activity-sub-groups",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates new activity sub group.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).
 - The specified CT term uids must exist, and the term names are in a final state.

Business logic:
 - New node is created for the activity sub group with the set properties.
 - relationships to specified control terminology are created (as in the model).
 - relationships to specified activity parent are created (as in the model)
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'change_description' property will be set automatically to 'Initial version'.

State after:
 - ActivitySubGroup is created in status Draft and assigned an initial minor version number as 0.1.
 - Audit trail entry must be made with action of creating new Draft version.

Possible errors:
 - Invalid library or control terminology uid's specified.
""",
    response_model=ActivitySubGroup,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The activity sub group was successfully created."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
    },
)
def create(
    activity_create_input: Annotated[ActivitySubGroupCreateInput, Body()],
):
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.create(concept_input=activity_create_input)


@router.patch(
    "/activity-sub-groups/{activity_subgroup_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Update activity sub group",
    description="""
State before:
 - uid must exist and activity sub group must exist in status draft.
 - The activity sub group must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - If activity sub group exist in status draft then attributes are updated.
 - If links to CT are selected or updated then relationships are made to CTTermRoots.
- If the linked activity sub group is updated, the relationships are updated to point to the activity sub group value node.

State after:
 - attributes are updated for the activity sub group.
 - Audit trail entry must be made with update of attributes.

Possible errors:
 - Invalid uid.

""",
    response_model=ActivitySubGroup,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity sub group is not in draft status.\n"
            "- The activity sub group had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity sub group with the specified 'activity_subgroup_uid' wasn't found.",
        },
    },
)
def edit(
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
    activity_edit_input: Annotated[ActivitySubGroupEditInput, Body()],
):
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.edit_draft(
        uid=activity_subgroup_uid, concept_edit_input=activity_edit_input
    )


@router.post(
    "/activity-sub-groups/{activity_subgroup_uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Create a new version of activity sub group",
    description="""
State before:
 - uid must exist and the activity sub group must be in status Final.

Business logic:
- The activity sub group is changed to a draft state.

State after:
 - ActivitySubGroup changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=ActivitySubGroup,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't allow to create activity sub groups.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The activity sub group is not in final status.\n"
            "- The activity sub group with the specified 'activity_subgroup_uid' could not be found.",
        },
    },
)
def new_version(
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
):
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.create_new_version(uid=activity_subgroup_uid)


@router.post(
    "/activity-sub-groups/{activity_subgroup_uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approve draft version of activity sub group",
    description="""
State before:
 - uid must exist and activity sub group must be in status Draft.

Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically 'Approved version'.

State after:
 - Activity sub group changed status to Final and assigned a new major version number.
 - Audit trail entry must be made with action of approving to new Final version.

Possible errors:
 - Invalid uid or status not Draft.
    """,
    response_model=ActivitySubGroup,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity sub group is not in draft status.\n"
            "- The library doesn't allow to approve activity sub group.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity sub group with the specified 'activity_subgroup_uid' wasn't found.",
        },
    },
)
def approve(
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
):
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.approve(uid=activity_subgroup_uid)


@router.delete(
    "/activity-sub-groups/{activity_subgroup_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of activity sub group",
    description="""
State before:
 - uid must exist and activity sub group must be in status Final.

Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status will be automatically set to 'Retired'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - Activity sub group changed status to Retired.
 - Audit trail entry must be made with action of inactivating to retired version.

Possible errors:
 - Invalid uid or status not Final.
    """,
    response_model=ActivitySubGroup,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity sub group is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity sub group with the specified 'activity_subgroup_uid' could not be found.",
        },
    },
)
def inactivate(
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
):
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.inactivate_final(uid=activity_subgroup_uid)


@router.post(
    "/activity-sub-groups/{activity_subgroup_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a activity sub group",
    description="""
State before:
 - uid must exist and activity sub group must be in status Retired.

Business logic:
 - The latest 'Retired' version will remain the same as before.
 - The status will be automatically set to 'Final'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - Activity sub group changed status to Final.
 - An audit trail entry must be made with action of reactivating to final version.

Possible errors:
 - Invalid uid or status not Retired.
    """,
    response_model=ActivitySubGroup,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity sub group is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity sub group with the specified 'activity_subgroup_uid' could not be found.",
        },
    },
)
def reactivate(
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
):
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.reactivate_retired(uid=activity_subgroup_uid)


@router.delete(
    "/activity-sub-groups/{activity_subgroup_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Delete draft version of activity sub group",
    description="""
State before:
 - uid must exist
 - The concept must be in status Draft in a version less then 1.0 (never been approved).
 - The concept must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - The draft concept is deleted.

State after:
 - Activity sub group is successfully deleted.

Possible errors:
 - Invalid uid or status not Draft or exist in version 1.0 or above (previously been approved) or not in an editable library.
    """,
    response_model=None,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The activity sub group was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity sub group is not in draft status.\n"
            "- The activity sub group was already in final state or is in use.\n"
            "- The library doesn't allow to delete activity sub group.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An activity sub group with the specified 'activity_subgroup_uid' could not be found.",
        },
    },
)
def delete_activity_subgroup(
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
):
    activity_subgroup_service = ActivitySubGroupService()
    activity_subgroup_service.soft_delete(uid=activity_subgroup_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
