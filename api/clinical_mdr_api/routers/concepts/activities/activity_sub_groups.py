"""ActivitySubGroup router."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from starlette.requests import Request

from clinical_mdr_api.models.concepts.activities.activity import SimpleActivity
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivityGroupForActivitySubGroup,
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
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/concepts/activities"
router = APIRouter()

ActivitySubGroupUID = Path(description="The unique id of the ActivitySubGroup")


@router.get(
    "/activity-sub-groups",
    dependencies=[security, rbac.LIBRARY_READ],
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
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_activity_subgroups(
    library_name: Annotated[str | None, Query()] = None,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[ActivitySubGroup]:
    activity_subgroup_service = ActivitySubGroupService()
    results = activity_subgroup_service.get_all_concepts(
        library=library_name,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/activity-sub-groups/versions",
    dependencies=[security, rbac.LIBRARY_READ],
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
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_activity_subgroups_versions(
    library_name: Annotated[str | None, Query()] = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[ActivitySubGroup]:
    activity_subgroup_service = ActivitySubGroupService()
    results = activity_subgroup_service.get_all_concept_versions(
        library=library_name,
        sort_by={"start_date": False},
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/activity-sub-groups/headers",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns possible values from the database for a given header",
    description="Allowed parameters include : field name for which to get possible values, "
    "search string to provide filtering for the field name, additional filters to apply on other fields",
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
    field_name: _generic_descriptions.HEADER_FIELD_NAME_QUERY,
    library_name: Annotated[str | None, Query()] = None,
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/activity-sub-groups/{activity_subgroup_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific activity subgroup (in a specific version)",
    description="""
State before:
 - an activity subgroup with uid must exist.

Business logic:
 - If parameter at_specified_date_time is specified then the latest/newest representation of the concept at this point in time is returned. The point in time needs to be specified in ISO 8601 format including the timezone, e.g.: '2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. If the timezone is ommitted, UTC�0 is assumed.
 - If parameter status is specified then the representation of the concept in that status is returned (if existent). This is useful if the concept has a status 'Draft' and a status 'Final'.
 - If parameter version is specified then the latest/newest representation of the concept in that version is returned. Only exact matches are considered. The version is specified in the following format: <major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0', ...

State after:
 - No change

Possible errors:
 - Invalid uid, at_specified_date_time, status or version.
 """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_activity(
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
) -> ActivitySubGroup:
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.get_by_uid(uid=activity_subgroup_uid)


@router.get(
    "/activity-sub-groups/{activity_subgroup_uid}/versions",
    dependencies=[security, rbac.LIBRARY_READ],
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
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity subgroup with the specified 'activity_subgroup_uid' wasn't found.",
        },
    },
)
def get_versions(
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
) -> list[ActivitySubGroup]:
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.get_version_history(uid=activity_subgroup_uid)


@router.get(
    "/activity-sub-groups/{activity_subgroup_uid}/overview",
    dependencies=[security, rbac.LIBRARY_READ],
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
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid=activity_subgroup.activity_groups[].uid",
            "name=activity_subgroup.activity_groups[].name",
            "version=activity_subgroup.activity_groups[].version",
            "status=activity_subgroup.activity_groups[].status",
        ],
        "formats": [
            "application/x-yaml",
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ],
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
) -> ActivitySubGroupOverview:
    if version == "":
        version = None

    service = ActivitySubGroupService()
    return service.get_subgroup_overview(
        subgroup_uid=activity_subgroup_uid, version=version
    )


@router.get(
    "/activity-sub-groups/{activity_subgroup_uid}/activities",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get activities linked to a specific activity subgroup version",
    description="""
Returns a list of activities linked to the specified version of an activity subgroup.
If no version is provided, the latest version of the activity subgroup is used.
- Results are paginated based on provided parameters
- Setting page_size=0 will return all items without pagination

{_generic_descriptions.DATA_EXPORTS_HEADER}
    """,
    status_code=200,
    response_model=CustomPage[SimpleActivity],
    responses={
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "name",
            "version",
            "status",
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
def get_activities_for_activity_subgroup(
    request: Request,  # request is actually required by the allow_exports decorator
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
    version: Annotated[
        str | None,
        Query(description="Select specific version, omit to view latest version"),
    ] = None,
    search_string: Annotated[
        str,
        Query(
            description="Search string to filter activities by name or other fields. Case-insensitive partial match."
        ),
    ] = "",
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: Annotated[
        int,
        Query(
            ge=0, le=settings.max_page_size, description=_generic_descriptions.PAGE_SIZE
        ),
    ] = settings.default_page_size,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[SimpleActivity]:
    if version == "":
        version = None

    service = ActivitySubGroupService()
    results = service.get_activities_for_subgroup(
        subgroup_uid=activity_subgroup_uid,
        version=version,
        search_string=search_string,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/activity-sub-groups/{activity_subgroup_uid}/activity-groups",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get activity groups for a specific activity subgroup",
    description="""
Returns activity groups linked to a specific activity subgroup.
Results are paginated and suitable for export with each group on a separate row.

{_generic_descriptions.DATA_EXPORTS_HEADER}
    """,
    status_code=200,
    response_model=CustomPage[ActivityGroupForActivitySubGroup],
    responses={
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": ["uid", "name", "version", "status"],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_activity_groups_for_subgroup(
    request: Request,  # request is actually required by the allow_exports decorator
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
    version: Annotated[
        str | None,
        Query(description="Select specific version, omit to view latest version"),
    ] = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: Annotated[
        int,
        Query(
            ge=0, le=settings.max_page_size, description=_generic_descriptions.PAGE_SIZE
        ),
    ] = settings.default_page_size,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[ActivityGroupForActivitySubGroup]:
    if version == "":
        version = None

    service = ActivitySubGroupService()
    return service.get_activity_groups_for_subgroup_paginated(
        subgroup_uid=activity_subgroup_uid,
        version=version,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
    )


@router.get(
    "/activity-sub-groups/{activity_subgroup_uid}/overview.cosmos",
    dependencies=[security, rbac.LIBRARY_READ],
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
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates new activity subgroup.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).
 - The specified CT term uids must exist, and the term names are in a final state.

Business logic:
 - New node is created for the activity subgroup with the set properties.
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
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The activity subgroup was successfully created."
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
) -> ActivitySubGroup:
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.create(concept_input=activity_create_input)


@router.put(
    "/activity-sub-groups/{activity_subgroup_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Update activity subgroup",
    description="""
State before:
 - uid must exist and activity subgroup must exist in status draft.
 - The activity subgroup must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - If activity subgroup exist in status draft then attributes are updated.
 - If links to CT are selected or updated then relationships are made to CTTermRoots.
- If the linked activity subgroup is updated, the relationships are updated to point to the activity subgroup value node.

State after:
 - attributes are updated for the activity subgroup.
 - Audit trail entry must be made with update of attributes.

Possible errors:
 - Invalid uid.

""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity subgroup is not in draft status.\n"
            "- The activity subgroup had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity subgroup with the specified 'activity_subgroup_uid' wasn't found.",
        },
    },
)
def edit(
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
    activity_edit_input: Annotated[ActivitySubGroupEditInput, Body()],
) -> ActivitySubGroup:
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.edit_draft(
        uid=activity_subgroup_uid,
        concept_edit_input=activity_edit_input,
        patch_mode=False,
    )


@router.post(
    "/activity-sub-groups/{activity_subgroup_uid}/versions",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Create a new version of activity subgroup",
    description="""
State before:
 - uid must exist and the activity subgroup must be in status Final.

Business logic:
- The activity subgroup is changed to a draft state.

State after:
 - ActivitySubGroup changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
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
            "- The activity subgroup is not in final status.\n"
            "- The activity subgroup with the specified 'activity_subgroup_uid' could not be found.",
        },
    },
)
def new_version(
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
) -> ActivitySubGroup:
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.create_new_version(uid=activity_subgroup_uid)


@router.post(
    "/activity-sub-groups/{activity_subgroup_uid}/approvals",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Approve draft version of activity subgroup",
    description="""
State before:
 - uid must exist and activity subgroup must be in status Draft.

Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically 'Approved version'.
 - If cascade_edit_and_approve is set to True, all activities that are linked to the latest 'Final' version of this activity subgroup
   are updated to link to the newly approved activity subgroup, and then approved.

State after:
 - Activity subgroup changed status to Final and assigned a new major version number.
 - Audit trail entry must be made with action of approving to new Final version.

Possible errors:
 - Invalid uid or status not Draft.
    """,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity subgroup is not in draft status.\n"
            "- The library doesn't allow to approve activity subgroup.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity subgroup with the specified 'activity_subgroup_uid' wasn't found.",
        },
    },
)
def approve(
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
    cascade_edit_and_approve: Annotated[
        bool, Query(description="Approve all linked activities")
    ] = False,
) -> ActivitySubGroup:
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.approve(
        uid=activity_subgroup_uid, cascade_edit_and_approve=cascade_edit_and_approve
    )


@router.delete(
    "/activity-sub-groups/{activity_subgroup_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of activity subgroup",
    description="""
State before:
 - uid must exist and activity subgroup must be in status Final.

Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status will be automatically set to 'Retired'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - Activity subgroup changed status to Retired.
 - Audit trail entry must be made with action of inactivating to retired version.

Possible errors:
 - Invalid uid or status not Final.
    """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity subgroup is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity subgroup with the specified 'activity_subgroup_uid' could not be found.",
        },
    },
)
def inactivate(
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
) -> ActivitySubGroup:
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.inactivate_final(uid=activity_subgroup_uid)


@router.post(
    "/activity-sub-groups/{activity_subgroup_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a activity subgroup",
    description="""
State before:
 - uid must exist and activity subgroup must be in status Retired.

Business logic:
 - The latest 'Retired' version will remain the same as before.
 - The status will be automatically set to 'Final'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - Activity subgroup changed status to Final.
 - An audit trail entry must be made with action of reactivating to final version.

Possible errors:
 - Invalid uid or status not Retired.
    """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity subgroup is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity subgroup with the specified 'activity_subgroup_uid' could not be found.",
        },
    },
)
def reactivate(
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
) -> ActivitySubGroup:
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.reactivate_retired(uid=activity_subgroup_uid)


@router.delete(
    "/activity-sub-groups/{activity_subgroup_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Delete draft version of activity subgroup",
    description="""
State before:
 - uid must exist
 - The concept must be in status Draft in a version less then 1.0 (never been approved).
 - The concept must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - The draft concept is deleted.

State after:
 - Activity subgroup is successfully deleted.

Possible errors:
 - Invalid uid or status not Draft or exist in version 1.0 or above (previously been approved) or not in an editable library.
    """,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The activity subgroup was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity subgroup is not in draft status.\n"
            "- The activity subgroup was already in final state or is in use.\n"
            "- The library doesn't allow to delete activity subgroup.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An activity subgroup with the specified 'activity_subgroup_uid' could not be found.",
        },
    },
)
def delete_activity_subgroup(
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
):
    activity_subgroup_service = ActivitySubGroupService()
    activity_subgroup_service.soft_delete(uid=activity_subgroup_uid)


@router.post(
    "/activity-sub-groups/{activity_subgroup_uid}/archive",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=f"Move activity subgroup to {settings.archived_library_name} library",
    description="Moves an existing activity subgroup to the target library if not yet in it. Returns new state of ActivitySubGroup.",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: _generic_descriptions.ERROR_400,
        404: _generic_descriptions.ERROR_404,
    },
)
def archive(
    activity_subgroup_uid: Annotated[str, ActivitySubGroupUID],
) -> ActivitySubGroup:
    activity_subgroup_service = ActivitySubGroupService()
    return activity_subgroup_service.archive(uid=activity_subgroup_uid)
