"""New Activities router."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from starlette.requests import Request

from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
    ActivityInstanceAttributes,
    ActivityInstanceAttributesEditInput,
    ActivityInstanceCreateInput,
    ActivityInstanceGroupings,
    ActivityInstanceGroupingsBatchInput,
    ActivityInstanceGroupingsEditInput,
    ActivityInstanceOverview,
    ActivityInstancePreviewInput,
    SimplifiedActivityItem,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers.responses import YAMLResponse
from clinical_mdr_api.services.concepts.activities.activity_instance_service import (
    ActivityInstanceAttributesService,
    ActivityInstanceGroupingsService,
    ActivityInstanceService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/concepts/activities/activity-instances"
router = APIRouter()

ActivityInstanceUID = Path(description="The unique id of the ActivityInstance")


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all activity instances (for a given library)",
    description=f"""
State before:
 - The library must exist (if specified)
 
Business logic:
 - List all activity instances in their latest version, including properties derived from linked control terminology.
 
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
        "defaults": [
            "library_name",
            "activity_instance_class=activity_instance_class.name",
            "activity=activity_groupings.activity.name",
            "activity_instance=name",
            "definition",
            "nci_concept_id",
            "nci_concept_name",
            "is_research_lab",
            "molecular_weight",
            "topic_code",
            "adam_param_code",
            "is_required_for_activity",
            "is_default_selected_for_activity",
            "is_data_sharing",
            "is_legacy_usage",
            "start_date",
            "author_username",
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
    names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity instance names to use as a specific filter",
            alias="names[]",
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
            description="A list of activity subgroup names to use as a specific filter",
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
    activity_instance_class_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity_instance_class names to use as a specific filter",
            alias="activity_instance_class_names[]",
        ),
    ] = None,
    status: Annotated[
        str | None,
        Query(
            description="Filter by status, matching either activity instance status or groupings status",
        ),
    ] = None,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[ActivityInstance]:
    activity_instance_service = ActivityInstanceService()
    results = activity_instance_service.get_all_concepts(
        library=library_name,
        activity_names=activity_names,
        activity_subgroup_names=activity_subgroup_names,
        activity_group_names=activity_group_names,
        activity_instance_class_names=activity_instance_class_names,
        activity_instance_names=names,
        status=status,
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
    "/attributes/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all versions of all activity instances (for a given library)",
    description=f"""
State before:
 - The library must exist (if specified)
 
Business logic:
 - List version history of all activity instances
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
        "defaults": [
            "uid",
            "library_name",
            "activity=activities.name",
            "name",
            "definition",
            "nci_concept_id",
            "nci_concept_name",
            "is_research_lab",
            "molecular_weight",
            "topic_code",
            "adam_param_code",
            "is_required_for_activity",
            "is_default_selected_for_activity",
            "is_data_sharing",
            "is_legacy_usage",
            "sdtm_domain=sdtm_domain.name",
            "start_date",
            "author_username",
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
def get_activity_instances_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    library_name: Annotated[str | None, Query()] = None,
    activity_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity names to use as a specific filter",
            alias="activity_names[]",
        ),
    ] = None,
    activity_instance_class_names: Annotated[
        list[str] | None,
        Query(
            description="A list of activity_instance_class names to use as a specific filter",
            alias="activity_instance_class_names[]",
        ),
    ] = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[ActivityInstanceAttributes]:
    activity_instance_service = ActivityInstanceAttributesService()
    results = activity_instance_service.get_all_concept_versions(
        library=library_name,
        activity_names=activity_names,
        activity_instance_class_names=activity_instance_class_names,
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
    "/headers",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns possibles values from the database for a given header",
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
    lite: Annotated[
        bool,
        Query(description=_generic_descriptions.HEADERS_QUERY_LITE),
    ] = False,
) -> list[Any]:
    activity_instance_service = ActivityInstanceService()
    return activity_instance_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
        lite=lite,
    )


@router.get(
    "/{activity_instance_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific activity instance (in a specific version)",
    description="""
State before:
 - a activity instance with uid must exist.

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
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
) -> ActivityInstance:
    activity_instance_service = ActivityInstanceService()
    return activity_instance_service.get_by_uid(uid=activity_instance_uid)


@router.get(
    "/{activity_instance_uid}/overview",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get detailed overview a specific activity instance",
    description="""
Returns detailed description about activity instance, including information about:
 - Activity
 - Activity subgroups
 - Activity groups
 - Activity instance class
 - Activity items
 - Activity item class

State before:
 - an activity instance with uid must exist.

State after:
 - No change

Possible errors:
 - Invalid uid.

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
        "defaults": [
            "activity_instance_name=activity_instance.name",
            "activity_instance_definition=activity_instance.definition",
            "activity_instance_nci_id=activity_instance.nci_concept_id",
            "activity_instance_nci_name=activity_instance.nci_concept_name",
            "activity_instance_class=activity_instance.activity_instance_class.name",
            "is_research_lab=activity_instance.is_research_lab",
            "molecular_weight=activity_instance.molecular_weight",
            "topic_code=activity_instance.topic_code",
            "adam_param_code=activity_instance.adam_param_code",
            "library_name=activity_instance.library_name",
            "status=activity_instance.status",
            "version=activity_instance.version",
            "activity_groupings_count=activity_groupings",
            "activity_items_count=activity_items",
            "all_versions",
        ],
        "formats": [
            "application/x-yaml",
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_activity_instance_overview(
    request: Request,  # request is actually required by the allow_exports decorator
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
    version: Annotated[
        str | None,
        Query(description="Select specific version, omit to view latest version"),
    ] = None,
) -> ActivityInstanceOverview:
    activity_instance_service = ActivityInstanceService()
    return activity_instance_service.get_activity_instance_overview(
        activity_instance_uid=activity_instance_uid, version=version
    )


@router.get(
    "/{activity_instance_uid}/attributes",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific activity instance attributes (in a specific version)",
    description="""
State before:
 - a activity instance with uid must exist.

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
def get_activity_instance_attributes(
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
) -> ActivityInstanceAttributes:
    activity_instance_service = ActivityInstanceAttributesService()
    return activity_instance_service.get_by_uid(uid=activity_instance_uid)


@router.get(
    "/{activity_instance_uid}/groupings",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific activity instance groupings (in a specific version)",
    description="""
State before:
 - a activity instance with uid must exist.

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
@decorators.allow_exports(
    {
        "defaults": [
            "status=activity_instance.status",
            "version=activity_instance.version",
            "activity_groupings_count=activity_groupings",
            "all_versions",
        ],
        "formats": [
            "application/x-yaml",
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_activity_instance_groupings(
    request: Request,  # request is actually required by the allow_exports decorator
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
    version: Annotated[str | None, Query()] = None,
) -> ActivityInstanceGroupings:
    activity_instance_service = ActivityInstanceGroupingsService()
    return activity_instance_service.get_by_uid(
        uid=activity_instance_uid, version=version
    )


@router.get(
    "/{activity_instance_uid}/activity-items",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get activity items for a specific activity instance",
    status_code=200,
    description="""
Returns activity items for an activity instance, including:
 - Activity item class information (name, role, data type)
 - CT terms (controlled terminology terms)
 - Unit definitions with dimension names
 - ODM forms, item groups, and items
 - ADaM parameter specificity flags

State before:
 - an activity instance with uid must exist.

State after:
 - No change

Possible errors:
 - Invalid uid.

{_generic_descriptions.DATA_EXPORTS_HEADER}
 """,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"model": list[SimplifiedActivityItem]},
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "item_class_name=activity_item_class.name",
            "item_class_order=activity_item_class.order",
            "role_name=activity_item_class.role_name",
            "data_type_name=activity_item_class.data_type_name",
            "is_adam_param_specific",
            "ct_terms[].uid",
            "ct_terms[].name",
            "ct_terms[].library_name",
            "unit_definitions[].name",
            "unit_definitions[].dimension_name",
            "odm_forms[].uid",
            "odm_forms[].name",
            "odm_item_groups[].uid",
            "odm_item_groups[].name",
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
def get_activity_instance_items(
    request: Request,  # request is actually required by the allow_exports decorator
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
    version: Annotated[str | None, Query()] = None,
):
    activity_instance_service = ActivityInstanceService()
    return activity_instance_service.get_activity_instance_items(
        activity_instance_uid=activity_instance_uid, version=version
    )


@router.get(
    "/{activity_instance_uid}/overview.cosmos",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get a COSMoS compatible representation of a specific activity instance",
    description="""
Returns detailed description about activity instance, including information about:
 - Activity subgroups
 - Activity groups
 - Activity instance
 - Activity instance class

State before:
 - an activity instance with uid must exist.

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
def get_cosmos_activity_instance_overview(
    request: Request,  # request is actually required by the allow_exports decorator
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
):
    activity_instance_service = ActivityInstanceService()
    return YAMLResponse(
        activity_instance_service.get_cosmos_activity_instance_overview(
            activity_instance_uid=activity_instance_uid
        )
    )


@router.get(
    "/{activity_instance_uid}/attributes/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List version history for activity instance attributes",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for activity instance.
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
            "description": "Not Found - The activity isntance with the specified 'activity_instance_uid' wasn't found.",
        },
    },
)
def get_versions(
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
) -> list[ActivityInstanceAttributes]:
    activity_instance_service = ActivityInstanceAttributesService()
    return activity_instance_service.get_version_history(uid=activity_instance_uid)


@router.post(
    "",
    summary="Creates new activity instance.",
    dependencies=[security, rbac.LIBRARY_WRITE],
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).

Business logic:
 - New node is created for the activity instance with the set properties.
 - relationships to specified activity parent are created (as in the model)
 - relationships to specified activity instance class is created (as in the model)
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'change_description' property will be set automatically to 'Initial version'.

State after:
 - activity instance is created in status Draft and assigned an initial minor version number as 0.1.
 - Audit trail entry must be made with action of creating new Draft version.

Possible errors:
 - Invalid library or control terminology uid's specified.
""",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The activity instance was successfully created."
        },
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
    activity_instance_create_input: Annotated[ActivityInstanceCreateInput, Body()],
) -> ActivityInstance:
    activity_instance_service = ActivityInstanceService()
    return activity_instance_service.create(
        concept_input=activity_instance_create_input
    )


@router.post(
    "/preview",
    summary="Previews the creation of a new activity instance.",
    dependencies=[security, rbac.LIBRARY_WRITE],
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).

Business logic:
 - New node is created for the activity instance with the set properties.
 - relationships to specified activity parent are created (as in the model)
 - relationships to specified activity instance class is created (as in the model)
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'change_description' property will be set automatically to 'Initial version'.

State after:
 - activity instance is created in status Draft and assigned an initial minor version number as 0.1.
 - Audit trail entry must be made with action of creating new Draft version.

Possible errors:
 - Invalid library or control terminology uid's specified.
""",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The activity instance was successfully previewed."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
        404: _generic_descriptions.ERROR_404,
    },
)
def preview(
    activity_instance_create_input: Annotated[
        ActivityInstancePreviewInput,
        Body(
            description="Related parameters of the objective that shall be previewed."
        ),
    ],
) -> ActivityInstance:
    activity_instance_service = ActivityInstanceService()
    return activity_instance_service.create(
        concept_input=activity_instance_create_input, preview=True
    )


@router.patch(
    "/{activity_instance_uid}/attributes",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Update activity instance attributes",
    description="""
State before:
 - uid must exist and activity instance attributes must exist in status draft.
 - The activity instance must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - If activity instance exist in status draft then attributes are updated.
- If the linked activity instance is updated, the relationships are updated to point to the activity instance value node.

State after:
 - attributes are updated for the activity instance.
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
            "- The activity instance is not in draft status.\n"
            "- The activity instance had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance with the specified 'activity_instance_uid' wasn't found.",
        },
    },
)
def edit(
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
    activity_instance_edit_input: Annotated[
        ActivityInstanceAttributesEditInput, Body()
    ],
) -> ActivityInstanceAttributes:
    activity_instance_service = ActivityInstanceAttributesService()
    return activity_instance_service.edit_draft(
        uid=activity_instance_uid,
        concept_edit_input=activity_instance_edit_input,
        patch_mode=False,
    )


@router.post(
    "/{activity_instance_uid}/attributes/versions",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Create a new version of an activity instance attributes",
    description="""
State before:
 - uid must exist and the activity instance must be in status Final.
 
Business logic:
- The activity instance is changed to a draft state.

State after:
 - Activity instance changed status to Draft and assigned a new minor version number.
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
            "- The library doesn't allow to create activity instances.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The activity instance is not in final status.\n"
            "- The activity instance with the specified 'activity_instance_uid' could not be found.",
        },
    },
)
def create_new_version(
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
) -> ActivityInstanceAttributes:
    activity_instance_service = ActivityInstanceAttributesService()
    return activity_instance_service.create_new_version(uid=activity_instance_uid)


@router.post(
    "/{activity_instance_uid}/attributes/approvals",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Approve draft version of an activity instance attributes",
    description="""
State before:
 - uid must exist and activity instance must be in status Draft.
 
Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically 'Approved version'.
 
State after:
 - Activity instance changed status to Final and assigned a new major version number.
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
            "- The activity instance is not in draft status.\n"
            "- The library doesn't allow to approve activity instance.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance with the specified 'activity_instance_uid' wasn't found.",
        },
    },
)
def approve(
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
) -> ActivityInstanceAttributes:
    activity_instance_service = ActivityInstanceAttributesService()
    return activity_instance_service.approve(uid=activity_instance_uid)


@router.delete(
    "/{activity_instance_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Inactivate final version of an activity instance (attributes and groupings)",
    description="""
State before:
 - uid must exist.
 - Both attributes and groupings must be in status Final or Retired.
 - At least one of them must be in status Final.

Business logic:
 - Any part currently in Final is moved to Retired (latest Final version kept,
   change_description set, version preserved).
 - Any part already in Retired is left unchanged. This makes the endpoint
   idempotent and lets it recover from a mixed-state instance whose attributes
   and groupings diverged for any reason.

State after:
 - Both attributes and groupings end up in status Retired.
 - Audit trail entries are added only for the part that was transitioned.

Possible errors:
 - Invalid uid.
 - Attributes or groupings are in Draft (not allowed).
 - Both attributes and groupings are already Retired (nothing to do).
    """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Bad Request - Reasons include e.g.: \n"
            "- Attributes or groupings are in Draft status.\n"
            "- Both attributes and groupings are already in Retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance with the specified 'activity_instance_uid' could not be found.",
        },
    },
)
def inactivate(
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
) -> ActivityInstanceAttributes:
    activity_instance_service = ActivityInstanceAttributesService()
    return activity_instance_service.inactivate_final(uid=activity_instance_uid)


@router.post(
    "/{activity_instance_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of an activity instance (attributes and groupings)",
    description="""
State before:
 - uid must exist.
 - Both attributes and groupings must be in status Retired or Final.
 - At least one of them must be in status Retired.

Business logic:
 - Any part currently in Retired is moved to Final (latest Retired version kept,
   change_description set, version preserved).
 - Any part already in Final is left unchanged. This makes the endpoint
   idempotent and lets it recover from a mixed-state instance whose attributes
   and groupings diverged for any reason.

State after:
 - Both attributes and groupings end up in status Final.
 - Audit trail entries are added only for the part that was transitioned.

Possible errors:
 - Invalid uid.
 - Attributes or groupings are in Draft (not allowed).
 - Both attributes and groupings are already Final (nothing to do).
    """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Bad Request - Reasons include e.g.: \n"
            "- Attributes or groupings are in Draft status.\n"
            "- Both attributes and groupings are already in Final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance with the specified 'activity_instance_uid' could not be found.",
        },
    },
)
def reactivate(
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
) -> ActivityInstanceAttributes:
    activity_instance_service = ActivityInstanceAttributesService()
    return activity_instance_service.reactivate_retired(uid=activity_instance_uid)


@router.patch(
    "/{activity_instance_uid}/groupings",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Update activity instance groupings",
    description="""
State before:
 - uid must exist and activity instance groupings must exist in status draft.
 - The activity instance must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - If activity instance exist in status draft then groupings are updated.
- If the linked activity instance is updated, the relationships are updated to point to the activity instance value node.

State after:
 - groupings are updated for the activity instance.
 - Audit trail entry must be made with update of groupings.

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
            "- The activity instance is not in draft status.\n"
            "- The activity instance had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance with the specified 'activity_instance_uid' wasn't found.",
        },
    },
)
def edit_groupings(
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
    activity_instance_edit_input: Annotated[ActivityInstanceGroupingsEditInput, Body()],
) -> ActivityInstanceGroupings:
    activity_instance_service = ActivityInstanceGroupingsService()
    return activity_instance_service.edit_draft(
        uid=activity_instance_uid,
        concept_edit_input=activity_instance_edit_input,
        patch_mode=True,
    )


@router.post(
    "/groupings/batch-update",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Batch update groupings for multiple activity instances",
    description="""
State before:
 - All specified activity instance UIDs must exist.
 - Each activity instance must belong to a library that allows editing.

Business logic:
 - For each activity instance in the batch:
   1. A new groupings version is created (Draft) if not already in Draft status.
   2. The groupings are updated with the provided data.
   3. The new groupings version is approved (Final).
 - All operations are executed in a single transaction: if any step fails,
   the entire batch is rolled back.

State after:
 - All specified activity instances have their groupings updated and approved.
 - Audit trail entries are created for each version creation, edit, and approval.

Possible errors:
 - One or more activity instance UIDs do not exist.
 - A library does not allow editing.
 - Invalid activity, group, or subgroup UIDs in groupings.
""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK - All groupings were updated and approved."},
        400: {
            "model": ErrorResponse,
            "description": "Bad Request - Reasons include e.g.: \n"
            "- An activity instance does not exist.\n"
            "- Invalid grouping data provided.\n"
            "- A library does not allow editing.",
        },
        404: _generic_descriptions.ERROR_404,
    },
)
def batch_update_groupings(
    batch_input: Annotated[ActivityInstanceGroupingsBatchInput, Body()],
) -> list[ActivityInstanceGroupings]:
    activity_instance_service = ActivityInstanceGroupingsService()
    return activity_instance_service.batch_update_groupings(
        batch_input=batch_input,
    )


@router.get(
    "/{activity_instance_uid}/groupings/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List version history for activity instance groupings",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for activity instance groupings.
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
            "description": "Not Found - The activity isntance with the specified 'activity_instance_uid' wasn't found.",
        },
    },
)
def get_groupings_versions(
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
) -> list[ActivityInstanceGroupings]:
    activity_instance_service = ActivityInstanceGroupingsService()
    return activity_instance_service.get_version_history(uid=activity_instance_uid)


@router.post(
    "/{activity_instance_uid}/groupings/versions",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Create a new version of an activity instance groupings",
    description="""
State before:
 - uid must exist and the activity instance must be in status Final.
 
Business logic:
- The activity instance is changed to a draft state.

State after:
 - Activity instance changed status to Draft and assigned a new minor version number.
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
            "- The library doesn't allow to create activity instances.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The activity instance is not in final status.\n"
            "- The activity instance with the specified 'activity_instance_uid' could not be found.",
        },
    },
)
def create_new_groupings_version(
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
) -> ActivityInstanceGroupings:
    activity_instance_service = ActivityInstanceGroupingsService()
    return activity_instance_service.create_new_version(uid=activity_instance_uid)


@router.post(
    "/{activity_instance_uid}/groupings/approvals",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Approve draft version of an activity instance groupings",
    description="""
State before:
 - uid must exist and activity instance must be in status Draft.
 
Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically 'Approved version'.
 
State after:
 - Activity instance changed status to Final and assigned a new major version number.
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
            "- The activity instance is not in draft status.\n"
            "- The library doesn't allow to approve activity instance.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance with the specified 'activity_instance_uid' wasn't found.",
        },
    },
)
def approve_groupings(
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
) -> ActivityInstanceGroupings:
    activity_instance_service = ActivityInstanceGroupingsService()
    return activity_instance_service.approve(uid=activity_instance_uid)


@router.delete(
    "/{activity_instance_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Delete draft version of an activity instance",
    description="""
State before:
 - uid must exist
 - The concept must be in status Draft in a version less then 1.0 (never been approved).
 - The concept must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).
 
Business logic:
 - The draft concept is deleted.
 
State after:
 - Activity instance is successfully deleted.
 
Possible errors:
 - Invalid uid or status not Draft or exist in version 1.0 or above (previously been approved) or not in an editable library.
    """,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The activity instance was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity instance is not in draft status.\n"
            "- The activity instance was already in final state or is in use.\n"
            "- The library doesn't allow to delete activity instance.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An activity instance with the specified 'activity_instance_uid' could not be found.",
        },
    },
)
def delete_activity_instance(
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
):
    activity_instance_service = ActivityInstanceService()
    activity_instance_service.soft_delete(uid=activity_instance_uid)


@router.post(
    "/{activity_instance_uid}/archive",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=f"Move activity instance to {settings.archived_library_name} library",
    description="Moves an existing activity instance to the target library if not yet in it. Returns new state of ActivityInstance.",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: _generic_descriptions.ERROR_400,
        404: _generic_descriptions.ERROR_404,
    },
)
def archive(
    activity_instance_uid: Annotated[str, ActivityInstanceUID],
) -> ActivityInstance:
    activity_instance_service = ActivityInstanceService()
    return activity_instance_service.archive(uid=activity_instance_uid)
