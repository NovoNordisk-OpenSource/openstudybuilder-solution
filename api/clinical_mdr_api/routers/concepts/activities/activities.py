"""Activity hierarchies router."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from starlette.requests import Request

from clinical_mdr_api.models.concepts.activities.activity import (
    Activity,
    ActivityCreateInput,
    ActivityEditInput,
    ActivityFromRequestInput,
    ActivityOverview,
    ActivityRequestRejectInput,
    ActivityVersionDetailGrouping,
    ActivityVersionWithInstances,
)
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstanceDetail,
)
from clinical_mdr_api.models.utils import CustomPage, GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers.responses import YAMLResponse
from clinical_mdr_api.services.concepts.activities.activity_service import (
    ActivityService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/concepts/activities"
router = APIRouter()

ActivityUID = Path(description="The unique id of the Activity")


@router.get(
    "/activities",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all activities (for a given library)",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List all activities in their latest version, including properties derived from linked control terminology.

State after:
 - No change

Possible errors:
 - Invalid library name specified.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "name",
            "synonyms",
            "activity_group.name=activity_groupings.activity_group_name",
            "activity_subgroup.name=activity_groupings.activity_subgroup_name",
            "sentence_case_name=name_sentence_case",
            "abbreviation",
            "nci_concept_id",
            "is_data_collected",
            "start_date",
            "status",
            "version",
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
def get_activities(
    request: Request,  # request is actually required by the allow_exports decorator
    library_name: Annotated[str | None, Query()] = None,
    activity_subgroup_uid: Annotated[
        str | None,
        Query(
            description="The unique id of the activity sub group to use as a specific filter",
        ),
    ] = None,
    activity_group_uid: Annotated[
        str | None,
        Query(
            description="The unique id of the activity group to use as a specific filter",
        ),
    ] = None,
    activity_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity names to use as a specific filter",
            alias="activity_names[]",
        ),
    ] = None,
    activity_subgroup_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity sub group names to use as a specific filter",
            alias="activity_subgroup_names[]",
        ),
    ] = None,
    activity_group_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity group names to use as a specific filter",
            alias="activity_group_names[]",
        ),
    ] = None,
    group_by_groupings: Annotated[
        bool,
        Query(
            description="A boolean property to specify if the activities will be grouped by sub group and group or not,"
            " so we won't loose the information about which activity instances has each group"
        ),
    ] = True,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[Activity]:
    activity_service = ActivityService()
    results = activity_service.get_all_concepts(
        library=library_name,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        activity_subgroup_uid=activity_subgroup_uid,
        activity_group_uid=activity_group_uid,
        activity_names=activity_names,
        activity_subgroup_names=activity_subgroup_names,
        activity_group_names=activity_group_names,
        group_by_groupings=group_by_groupings,
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/activities/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all versions of activities",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List version history of activities
 - The returned versions are ordered by version start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid library name specified.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "name",
            "synonyms",
            "activity_group=activity_group.name",
            "activity_subgroup=activity_subgroup.name",
            "start_date",
            "status",
            "version",
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
def get_activities_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    library_name: Annotated[str | None, Query()] = None,
    activity_subgroup_uid: Annotated[
        str | None,
        Query(
            description="The unique id of the activity sub group to use as a specific filter",
        ),
    ] = None,
    activity_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity names to use as a specific filter",
            alias="activity_names[]",
        ),
    ] = None,
    activity_subgroup_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity sub group names to use as a specific filter",
            alias="activity_subgroup_names[]",
        ),
    ] = None,
    activity_group_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity group names to use as a specific filter",
            alias="activity_group_names[]",
        ),
    ] = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[Activity]:
    activity_service = ActivityService()
    results = activity_service.get_all_concept_versions(
        library=library_name,
        sort_by={"start_date": False},
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        activity_subgroup_uid=activity_subgroup_uid,
        activity_names=activity_names,
        activity_subgroup_names=activity_subgroup_names,
        activity_group_names=activity_group_names,
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/activities/headers",
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
    activity_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity names to use as a specific filter",
            alias="activity_names[]",
        ),
    ] = None,
    activity_subgroup_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity sub group names to use as a specific filter",
            alias="activity_subgroup_names[]",
        ),
    ] = None,
    activity_group_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity group names to use as a specific filter",
            alias="activity_group_names[]",
        ),
    ] = None,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
    lite: Annotated[
        bool,
        Query(description=_generic_descriptions.HEADERS_QUERY_LITE),
    ] = False,
) -> list[Any]:
    activity_service = ActivityService()
    return activity_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
        activity_names=activity_names,
        activity_subgroup_names=activity_subgroup_names,
        activity_group_names=activity_group_names,
        group_by_groupings=False,
        lite=lite,
    )


@router.get(
    "/activities/{activity_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific activity (in a specific version)",
    description="""
State before:
 - an activity with uid must exist.

Business logic:
 - If parameter at_specified_date_time is specified then the latest/newest representation of the concept at this point in time is returned. The point in time needs to be specified in ISO 8601 format including the timezone, e.g.: '2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. If the timezone is ommitted, UTC�0 is assumed.
 - If parameter status is specified then the representation of the concept in that status is returned (if existent). This is useful if the concept has a status 'Draft' and a status 'Final'.
 - If parameter version is specified then the latest/newest representation of the concept in that version is returned. Only exact matches are considered. The version is specified in the following format: <major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0', ...

State after:
 - No change

Possible errors:
 - Invalid uid or at_specified_date_time, status or version.
 """,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_activity(activity_uid: Annotated[str, ActivityUID]) -> Activity:
    activity_service = ActivityService()
    return activity_service.get_by_uid(uid=activity_uid)


@router.get(
    "/activities/{activity_uid}/overview",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get detailed overview a specific activity",
    description="""
Returns detailed description about activity, including information about:
 - Activity
 - Activity subgroups
 - Activity groups
 - Activity instance
 - Activity instance class

State before:
 - an activity with uid must exist.

State after:
 - No change

Possible errors:
 - Invalid uid.
 """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "activity",
            "activity_subgroups",
            "activity_groups",
            "activity_instance",
        ],
        "formats": [
            "text/csv",
            "application/x-yaml",
        ],
    }
)
# pylint: disable=unused-argument
def get_activity_overview(
    request: Request,  # request is actually required by the allow_exports decorator
    activity_uid: Annotated[str, ActivityUID],
    version: Annotated[
        str | None,
        Query(description="Select specific version, omit to view latest version"),
    ] = None,
) -> ActivityOverview:
    activity_service = ActivityService()
    return activity_service.get_activity_overview(
        activity_uid=activity_uid, version=version
    )


@router.get(
    "/activities/{activity_uid}/overview.cosmos",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get a COSMoS compatible representation of a specific activity",
    description="""
Returns detailed description about activity, including information about:
 - Activity
 - Activity subgroups
 - Activity groups
 - Activity instance
 - Activity instance class

State before:
 - an activity with uid must exist.

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
def get_cosmos_activity_overview(
    request: Request,  # request is actually required by the allow_exports decorator
    activity_uid: Annotated[str, ActivityUID],
):
    activity_service = ActivityService()
    return YAMLResponse(
        activity_service.get_cosmos_activity_overview(activity_uid=activity_uid)
    )


@router.get(
    "/activities/{activity_uid}/versions/{version}/groupings",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get activity groupings for a specific version of an activity",
    description="""
State before:
 - An activity with uid and version must exist.

Business logic:
 - Return activity groupings information for the activity groupings table, including related subgroups, groups, and instances
   at the time the version was created.

State after:
 - No change

Possible errors:
 - Invalid uid or version.
 """,
    response_model=CustomPage[ActivityVersionDetailGrouping],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_specific_activity_version_groupings(
    activity_uid: Annotated[str, ActivityUID],
    version: Annotated[
        str, Path(description="The version of the activity in format 'x.y'")
    ],
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
):
    activity_service = ActivityService()
    results = activity_service.get_specific_activity_version_groupings(
        activity_uid=activity_uid,
        version=version,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
    )

    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/activities/{activity_uid}/versions/{version}/instances",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get activity instances relevant to a specific activity version",
    description=f"""
    Retrieve a paginated list of activity instances that were relevant during
    the time validity window of a *specific* version of an activity.

    For each relevant instance, the latest version active during the activity's
    version window is returned, along with all its older versions in the `children` array.

    Args:
        activity_uid: The unique ID of the activity.
        version: The specific version of the activity (e.g., "16.0").
        page_number: The page number for pagination (default: 1).
        page_size: The number of items per page (default: 10).
        flatten: If true, returns parent and child instances as separate rows (useful for exports).
                 If false, returns hierarchical structure with children nested (default).

    Returns:
        A paginated response containing activity instances relevant to the specified
        activity version's timeframe.
    {_generic_descriptions.DATA_EXPORTS_HEADER}
    """,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
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
            "activity_instance_class.name",
            "topic_code",
            "adam_param_code",
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
def get_instances_for_specific_activity_version(
    request: Request,  # request is actually required by the allow_exports decorator
    activity_uid: Annotated[str, ActivityUID],
    version: Annotated[
        str, Path(description="The specific version of the activity (e.g., '16.0')")
    ],
    page_number: Annotated[
        int,
        Query(
            description=_generic_descriptions.PAGE_NUMBER,
        ),
    ] = settings.default_page_number,
    page_size: Annotated[
        int,
        Query(
            description=_generic_descriptions.PAGE_SIZE,
        ),
    ] = settings.default_page_size,
    flatten: Annotated[
        bool,
        Query(
            description="If true, returns parent and child instances as separate rows. If false, returns hierarchical structure.",
        ),
    ] = False,
) -> GenericFilteringReturn[ActivityInstanceDetail]:
    """
    Get activity instances relevant to a specific activity version's timeframe.

    Args:
        activity_uid: The unique ID of the activity.
        version: The specific version of the activity.
        page_number: The page number for pagination.
        page_size: The number of items per page.
        flatten: Whether to flatten the parent-child hierarchy.

    Returns:
        A paginated response containing relevant activity instances.
    """
    activity_service = ActivityService()
    try:
        if flatten:
            # Return flattened list for exports
            result = activity_service.get_flattened_activity_instances_for_version(
                activity_uid=activity_uid,
                version=version,
                page_number=page_number,
                page_size=page_size,
            )
        else:
            # Return hierarchical structure (default)
            result = activity_service.get_activity_instances_for_version(
                activity_uid=activity_uid,
                version=version,
                page_number=page_number,
                page_size=page_size,
            )
        return result
    except Exception as e:
        raise e


@router.get(
    "/activities/{activity_uid}/versions/instances",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get instances linked to all versions of an activity",
    description="""
For a given activity, find all activity value nodes and their latest Final version number.
For each version, return the linked instances with minimal info: uid, name, topic_code,
and their groupings (group/subgroup uid and name).

The response is a list of activity versions ordered by version number descending,
each containing its linked instances.

State before:
 - An activity with uid must exist and have at least one Final version.

State after:
 - No change

Possible errors:
 - Invalid uid.
""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_versions_instances(
    activity_uid: Annotated[str, ActivityUID],
) -> list[ActivityVersionWithInstances]:
    activity_service = ActivityService()
    return activity_service.get_all_versions_with_instances(
        activity_uid=activity_uid,
    )


@router.get(
    "/activities/{activity_uid}/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List version history for activities",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for activities.
 - The returned versions are ordered by start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity with the specified 'activity_uid' wasn't found.",
        },
    },
)
def get_versions(activity_uid: Annotated[str, ActivityUID]) -> list[Activity]:
    activity_service = ActivityService()
    return activity_service.get_version_history(uid=activity_uid)


@router.post(
    "/activities",
    dependencies=[security, rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Creates new activity.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).
 - The specified CT term uids must exist, and the term names are in a final state.

Business logic:
 - New node is created for the activity with the set properties.
 - relationships to specified control terminology are created (as in the model).
 - relationships to specified activity parent are created (as in the model)
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'change_description' property will be set automatically to 'Initial version'.

State after:
 - Activity is created in status Draft and assigned an initial minor version number as 0.1.
 - Audit trail entry must be made with action of creating new Draft version.

Possible errors:
 - Invalid library or control terminology uid's specified.
""",
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The activity was successfully created."},
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
    activity_create_input: Annotated[ActivityCreateInput, Body()],
) -> Activity:
    activity_service = ActivityService()
    return activity_service.create(concept_input=activity_create_input)


@router.post(
    "/activities/sponsor-activities",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates new sponsor activity and retires activity request.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).
 - The specified CT term uids must exist, and the term names are in a final state.

Business logic:
 - New node is created for the activity with the set properties.
 - relationships to specified control terminology are created (as in the model).
 - relationships to specified activity parent are created (as in the model)
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'change_description' property will be set automatically to 'Initial version'.

State after:
 - Activity is created in status Draft and assigned an initial minor version number as 0.1.
 - Audit trail entry must be made with action of creating new Draft version.

Possible errors:
 - Invalid library or control terminology uid's specified.
""",
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The activity was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
        404: _generic_descriptions.ERROR_404,
    },
)
def create_sponsor_activity_from_activity_request(
    activity_create_input: Annotated[ActivityFromRequestInput, Body()],
) -> Activity:
    activity_service = ActivityService()
    return activity_service.replace_requested_activity_with_sponsor(
        sponsor_activity_input=activity_create_input
    )


@router.patch(
    "/activities/{activity_uid}/activity-request-rejections",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Reject and retire an Activity Request",
    description="""
State before:
 - uid must exist and activity must exist in status Final.
 - The activity must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - The ActivityRequest is edited with the rejection arguments.

State after:
 - After successful rejection, the Activity Request is edited with rejection arguments and set to be retired.

Possible errors:
 - Non existing ActivityRequest specified or specified ActivityRequest is not in Final state..
""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "Created - The activity was successfully edited."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity doesn't exist.\n"
            "- The activity is not in final state.\n",
        },
        404: _generic_descriptions.ERROR_404,
    },
)
def reject_activity_request(
    activity_uid: Annotated[str, ActivityUID],
    activity_request_rejection_input: Annotated[ActivityRequestRejectInput, Body()],
) -> Activity:
    activity_service = ActivityService()
    return activity_service.reject_activity_request(
        activity_request_uid=activity_uid,
        activity_request_rejection_input=activity_request_rejection_input,
    )


@router.put(
    "/activities/{activity_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Update activity",
    description="""
State before:
 - uid must exist and activity must exist in status draft.
 - The activity must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - If activities exist in status draft then attributes are updated.
 - If links to CT are selected or updated then relationships are made to CTTermRoots.
 - If the linked activity is updated, the relationships are updated to point to the activity value node.

State after:
 - attributes are updated for the activity.
 - Audit trail entry must be made with update of attributes.

Possible errors:
 - Invalid uid.

""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity is not in draft status.\n"
            "- The activity had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity with the specified 'activity_uid' wasn't found.",
        },
    },
)
def edit(
    activity_uid: Annotated[str, ActivityUID],
    activity_edit_input: Annotated[ActivityEditInput, Body()],
) -> Activity:
    activity_service = ActivityService()
    return activity_service.edit_draft(
        uid=activity_uid, concept_edit_input=activity_edit_input, patch_mode=False
    )


@router.post(
    "/activities/{activity_uid}/versions",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Create a new version of activity",
    description="""
State before:
 - uid must exist and the activity must be in status Final.

Business logic:
- The activity is changed to a draft state.

State after:
 - Activity changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't allow to create activities.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The activity is not in final status.\n"
            "- The activity with the specified 'activity_uid' could not be found.",
        },
    },
)
def new_version(activity_uid: Annotated[str, ActivityUID]) -> Activity:
    activity_service = ActivityService()
    return activity_service.create_new_version(uid=activity_uid)


@router.post(
    "/activities/{activity_uid}/approvals",
    dependencies=[security, rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Approve draft version of activity",
    description="""
State before:
 - uid must exist and activity must be in status Draft.

Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically 'Approved version'.
 - If cascade_edit_and_approve is set to True, all activity instances that are linked to the latest 'Final' version of this activity
   are updated to link to the newly approved activity, and then approved.

State after:
 - Activity changed status to Final and assigned a new major version number.
 - Audit trail entry must be made with action of approving to new Final version.

Possible errors:
 - Invalid uid or status not Draft.
    """,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity is not in draft status.\n"
            "- The library doesn't allow to approve activity.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity with the specified 'activity_uid' wasn't found.",
        },
    },
)
def approve(
    activity_uid: Annotated[str, ActivityUID],
    cascade_edit_and_approve: Annotated[
        bool, Query(description="Approve all linked activity instances")
    ] = False,
) -> Activity:
    activity_service = ActivityService()
    return activity_service.approve(
        uid=activity_uid, cascade_edit_and_approve=cascade_edit_and_approve
    )


@router.delete(
    "/activities/{activity_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of activity",
    description="""
State before:
 - uid must exist and activity must be in status Final.

Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status will be automatically set to 'Retired'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - Activity changed status to Retired.
 - Audit trail entry must be made with action of inactivating to retired version.

Possible errors:
 - Invalid uid or status not Final.
    """,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity with the specified 'activity_uid' could not be found.",
        },
    },
)
def inactivate(activity_uid: Annotated[str, ActivityUID]) -> Activity:
    activity_service = ActivityService()
    return activity_service.inactivate_final(uid=activity_uid)


@router.post(
    "/activities/{activity_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a activity",
    description="""
State before:
 - uid must exist and activity  must be in status Retired.

Business logic:
 - The latest 'Retired' version will remain the same as before.
 - The status will be automatically set to 'Final'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - Activity changed status to Final.
 - An audit trail entry must be made with action of reactivating to final version.

Possible errors:
 - Invalid uid or status not Retired.
    """,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity with the specified 'activity_uid' could not be found.",
        },
    },
)
def reactivate(activity_uid: Annotated[str, ActivityUID]) -> Activity:
    activity_service = ActivityService()
    return activity_service.reactivate_retired(uid=activity_uid)


@router.delete(
    "/activities/{activity_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Delete draft version of activity",
    description="""
State before:
 - uid must exist
 - The concept must be in status Draft in a version less then 1.0 (never been approved).
 - The concept must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - The draft concept is deleted.

State after:
 - Activity is successfully deleted.

Possible errors:
 - Invalid uid or status not Draft or exist in version 1.0 or above (previously been approved) or not in an editable library.
    """,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The activity was successfully deleted."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity is not in draft status.\n"
            "- The activity was already in final state or is in use.\n"
            "- The library doesn't allow to delete activity.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An activity with the specified 'activity_uid' could not be found.",
        },
    },
)
def delete_activity(activity_uid: Annotated[str, ActivityUID]):
    activity_service = ActivityService()
    activity_service.soft_delete(uid=activity_uid)


@router.post(
    "/activities/{activity_uid}/archive",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=f"Move activity to {settings.archived_library_name} library",
    description="Moves an existing activity to the target library if not yet in it. Returns new state of Activity.",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: _generic_descriptions.ERROR_400,
        404: _generic_descriptions.ERROR_404,
    },
)
def archive(
    activity_uid: Annotated[str, ActivityUID],
) -> Activity:
    activity_service = ActivityService()
    return activity_service.archive(uid=activity_uid)
