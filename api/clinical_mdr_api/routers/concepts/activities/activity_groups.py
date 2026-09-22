"""ActivityGroup router."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from starlette.requests import Request

from clinical_mdr_api.models.concepts.activities.activity_group import (
    ActivityGroup,
    ActivityGroupCreateInput,
    ActivityGroupDetail,
    ActivityGroupEditInput,
    ActivityGroupOverview,
    SimpleSubGroup,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers.responses import YAMLResponse
from clinical_mdr_api.services.concepts.activities.activity_group_service import (
    ActivityGroupService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/concepts/activities"
router = APIRouter()

ActivityGroupUID = Path(description="The unique id of the ActivityGroup")


@router.get(
    "/activity-groups",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all activity groups (for a given library)",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List all activities groups in their latest version, including properties derived from linked control terminology.

State after:
 - No change

Possible errors:
 - Invalid library name specified.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": ["uid", "name", "start_date", "status", "version"],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_activity_groups(
    request: Request,
    library_name: Annotated[str | None, Query()] = None,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[ActivityGroup]:
    activity_group_service = ActivityGroupService()
    results = activity_group_service.get_all_concepts(
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
    "/activity-groups/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all versions of all activity groups (for a given library)",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List version history of all activity groups
 - The returned versions are ordered by version start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid library name specified.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": ["uid", "name", "start_date", "status", "version"],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_activity_groups_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    library_name: Annotated[str | None, Query()] = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[ActivityGroup]:
    activity_group_service = ActivityGroupService()
    results = activity_group_service.get_all_concept_versions(
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
    "/activity-groups/headers",
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
    activity_subgroup_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity subgroup names to use as a specific filter",
            alias="activity_subgroup_names[]",
        ),
    ] = None,
    activity_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity names to use as a specific filter",
            alias="activity_names[]",
        ),
    ] = None,
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
    activity_group_service = ActivityGroupService()
    return activity_group_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
        activity_names=activity_names,
        activity_subgroup_names=activity_subgroup_names,
    )


@router.get(
    "/activity-groups/{activity_group_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific activity group (in a specific version)",
    description="""
State before:
 - an activity group with uid must exist.

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
def get_activity(activity_group_uid: Annotated[str, ActivityGroupUID]) -> ActivityGroup:
    activity_group_service = ActivityGroupService()
    return activity_group_service.get_by_uid(uid=activity_group_uid)


@router.get(
    "/activity-groups/{activity_group_uid}/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List version history for activity groups",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for activity groups.
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
            "description": "Not Found - The activity group with the specified 'activity_group_uid' wasn't found.",
        },
    },
)
def get_versions(
    activity_group_uid: Annotated[str, ActivityGroupUID],
) -> list[ActivityGroup]:
    activity_group_service = ActivityGroupService()
    return activity_group_service.get_version_history(uid=activity_group_uid)


@router.get(
    "/activity-groups/{activity_group_uid}/details",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get only the details of a specific activity group",
    description="""
Returns only the activity group details without linked subgroups:
- Activity group metadata (name, library, dates, status, etc.)
- Definition information

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
def get_activity_group_details(
    activity_group_uid: Annotated[str, ActivityGroupUID],
    version: Annotated[
        str | None,
        Query(description="Select specific version, omit to view latest version"),
    ] = None,
) -> ActivityGroupDetail:
    if version == "":
        version = None

    service = ActivityGroupService()
    return service.get_group_details(group_uid=activity_group_uid, version=version)


@router.get(
    "/activity-groups/{activity_group_uid}/subgroups",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get only the subgroups linked to a specific activity group",
    description=f"""
Returns only the activity subgroups linked to a specific activity group:
- List of subgroups with their uid, name, version, and status
- Results are paginated based on provided parameters
- Setting page_size=0 will return all items without pagination

State before:
- UID must exist

State after:
- No change

Possible errors:
- Invalid uid
{_generic_descriptions.DATA_EXPORTS_HEADER}
    """,
    status_code=200,
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
            "definition",
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
def get_activity_group_subgroups(
    request: Request,  # request is actually required by the allow_exports decorator
    activity_group_uid: Annotated[str, ActivityGroupUID],
    version: Annotated[
        str | None,
        Query(description="Select specific version, omit to view latest version"),
    ] = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[SimpleSubGroup]:
    if version == "":
        version = None

    service = ActivityGroupService()
    # Get paginated results from service layer
    results = service.get_group_subgroups(
        group_uid=activity_group_uid,
        version=version,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
    )

    # Convert GenericFilteringReturn to CustomPage for API response
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/activity-groups/{activity_group_uid}/overview",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get detailed overview of a specific activity group",
    description="""
Returns detailed description about activity group including:
- Activity Group details
- Linked Subgroups
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
        "defaults": ["group", "subgroups", "all_versions"],
        "formats": ["application/x-yaml"],
    }
)
def get_activity_group_overview(
    # pylint: disable=unused-argument
    request: Request,  # request is actually required by the allow_exports decorator
    activity_group_uid: Annotated[str, ActivityGroupUID],
    version: Annotated[
        str | None,
        Query(description="Select specific version, omit to view latest version"),
    ] = None,
) -> ActivityGroupOverview:
    if version == "":
        version = None

    service = ActivityGroupService()
    return service.get_group_overview(group_uid=activity_group_uid, version=version)


@router.get(
    "/activity-groups/{activity_group_uid}/overview.cosmos",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get a COSMoS compatible representation of a specific activity group",
    description="""
Returns detailed description about activity group, including information about:
 - Activity Group details
 - Linked activity subgroups
 - Linked activities

State before:
 - An activity group with uid must exist.

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
def get_cosmos_activity_group_overview(
    request: Request,
    activity_group_uid: Annotated[str, ActivityGroupUID],
):
    activity_group_service = ActivityGroupService()
    return YAMLResponse(
        activity_group_service.get_cosmos_group_overview(group_uid=activity_group_uid)
    )


@router.post(
    "/activity-groups",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates new activity group.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).
 - The specified CT term uids must exist, and the term names are in a final state.

Business logic:
 - New node is created for the activity group with the set properties.
 - relationships to specified control terminology are created (as in the model).
 - relationships to specified activity parent are created (as in the model)
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'change_description' property will be set automatically to 'Initial version'.

State after:
 - ActivityGroup is created in status Draft and assigned an initial minor version number as 0.1.
 - Audit trail entry must be made with action of creating new Draft version.

Possible errors:
 - Invalid library or control terminology uid's specified.
""",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The activity group was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
        404: _generic_descriptions.ERROR_404,
    },
)
def create(
    activity_create_input: Annotated[ActivityGroupCreateInput, Body()],
) -> ActivityGroup:
    activity_group_service = ActivityGroupService()
    return activity_group_service.create(concept_input=activity_create_input)


@router.put(
    "/activity-groups/{activity_group_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Update activity group",
    description="""
State before:
 - uid must exist and activity group must exist in status draft.
 - The activity group must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - If activity group exist in status draft then attributes are updated.
 - If links to CT are selected or updated then relationships are made to CTTermRoots.
- If the linked activity group is updated, the relationships are updated to point to the activity group value node.

State after:
 - attributes are updated for the activity group.
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
            "- The activity group is not in draft status.\n"
            "- The activity group had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity group with the specified 'activity_group_uid' wasn't found.",
        },
    },
)
def edit(
    activity_group_uid: Annotated[str, ActivityGroupUID],
    activity_edit_input: Annotated[ActivityGroupEditInput, Body()],
) -> ActivityGroup:
    activity_group_service = ActivityGroupService()
    return activity_group_service.edit_draft(
        uid=activity_group_uid, concept_edit_input=activity_edit_input, patch_mode=False
    )


@router.post(
    "/activity-groups/{activity_group_uid}/versions",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Create a new version of activity group",
    description="""
State before:
 - uid must exist and the activity group must be in status Final.

Business logic:
- The activity group is changed to a draft state.

State after:
 - ActivityGroup changed status to Draft and assigned a new minor version number.
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
            "- The activity group is not in final status.\n"
            "- The activity group with the specified 'activity_group_uid' could not be found.",
        },
    },
)
def create_new_version(
    activity_group_uid: Annotated[str, ActivityGroupUID],
) -> ActivityGroup:
    activity_group_service = ActivityGroupService()
    return activity_group_service.create_new_version(uid=activity_group_uid)


@router.post(
    "/activity-groups/{activity_group_uid}/approvals",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Approve draft version of activity group",
    description="""
State before:
 - uid must exist and activity group must be in status Draft.

Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically 'Approved version'.
 - If cascade_edit_and_approve is set to True, all activity subgroups that are linked to the latest 'Final' version of this activity group
   are updated to link to the newly approved activity group, and then approved.

State after:
 - Activity group changed status to Final and assigned a new major version number.
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
            "- The activity group is not in draft status.\n"
            "- The library doesn't allow to approve activity group.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity group with the specified 'activity_group_uid' wasn't found.",
        },
    },
)
def approve(
    activity_group_uid: Annotated[str, ActivityGroupUID],
    cascade_edit_and_approve: Annotated[
        bool, Query(description="Approve all linked activity subgroups")
    ] = False,
) -> ActivityGroup:
    activity_group_service = ActivityGroupService()
    return activity_group_service.approve(
        uid=activity_group_uid, cascade_edit_and_approve=cascade_edit_and_approve
    )


@router.delete(
    "/activity-groups/{activity_group_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of activity group",
    description="""
State before:
 - uid must exist and activity group must be in status Final.

Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status will be automatically set to 'Retired'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - Activity group changed status to Retired.
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
            "- The activity group is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity group with the specified 'activity_group_uid' could not be found.",
        },
    },
)
def inactivate(activity_group_uid: Annotated[str, ActivityGroupUID]) -> ActivityGroup:
    activity_group_service = ActivityGroupService()
    return activity_group_service.inactivate_final(uid=activity_group_uid)


@router.post(
    "/activity-groups/{activity_group_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a activity group",
    description="""
State before:
 - uid must exist and activity group must be in status Retired.

Business logic:
 - The latest 'Retired' version will remain the same as before.
 - The status will be automatically set to 'Final'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - Activity group changed status to Final.
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
            "- The activity group is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity group with the specified 'activity_group_uid' could not be found.",
        },
    },
)
def reactivate(activity_group_uid: Annotated[str, ActivityGroupUID]) -> ActivityGroup:
    activity_group_service = ActivityGroupService()
    return activity_group_service.reactivate_retired(uid=activity_group_uid)


@router.delete(
    "/activity-groups/{activity_group_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Delete draft version of activity group",
    description="""
State before:
 - uid must exist
 - The concept must be in status Draft in a version less then 1.0 (never been approved).
 - The concept must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - The draft concept is deleted.

State after:
 - Activity group is successfully deleted.

Possible errors:
 - Invalid uid or status not Draft or exist in version 1.0 or above (previously been approved) or not in an editable library.
    """,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The activity group was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity group is not in draft status.\n"
            "- The activity group was already in final state or is in use.\n"
            "- The library doesn't allow to delete activity group.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An activity group with the specified 'activity_group_uid' could not be found.",
        },
    },
)
def delete_activity_group(activity_group_uid: Annotated[str, ActivityGroupUID]):
    activity_group_service = ActivityGroupService()
    activity_group_service.soft_delete(uid=activity_group_uid)


@router.post(
    "/activity-groups/{activity_group_uid}/archive",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=f"Move activity group to {settings.archived_library_name} library",
    description="Moves an existing activity group to the target library if not yet in it. Returns new state of ActivityGroup.",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: _generic_descriptions.ERROR_400,
        404: _generic_descriptions.ERROR_404,
    },
)
def archive(
    activity_group_uid: Annotated[str, ActivityGroupUID],
) -> ActivityGroup:
    activity_group_service = ActivityGroupService()
    return activity_group_service.archive(uid=activity_group_uid)
