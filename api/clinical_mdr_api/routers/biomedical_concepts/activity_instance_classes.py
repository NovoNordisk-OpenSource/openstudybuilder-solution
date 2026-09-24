"""ActivityInstanceClass hierarchies router."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from starlette.requests import Request

from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
    ActivityInstanceClassEditInput,
    ActivityInstanceClassInput,
    ActivityInstanceClassMappingInput,
    ActivityInstanceClassOverview,
    ActivityInstanceClassWithDataset,
    ActivityInstanceParentClassOverview,
    CompactActivityItemClassForInstanceClass,
    SimpleActivityInstanceClass,
    SimpleActivityItemClass,
)
from clinical_mdr_api.models.utils import CustomPage, GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassService,
)
from clinical_mdr_api.services.biomedical_concepts.activity_item_class import (
    ActivityItemClassService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/activity-instance-classes"
router = APIRouter()

ActivityInstanceClassUID = Path(
    description="The unique id of the ActivityInstanceClass"
)


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all activity-instance-classes (for a given library)",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List all activity-instance-classes in their latest version, including properties derived from theirs parent classes.

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
def get_activity_instance_classes(
    request: Request,  # request is actually required by the allow_exports decorator
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[ActivityInstanceClass]:
    activity_instance_class_service = ActivityInstanceClassService()
    results = activity_instance_class_service.get_all_items(
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
    "/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all versions of activity instance classes",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List version history of activity instance classes
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
def get_activity_instance_classes_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[ActivityInstanceClass]:
    activity_instance_class_service = ActivityInstanceClassService()
    results = activity_instance_class_service.get_all_item_versions(
        sort_by={"start_date": False},
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/headers",
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
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
    activity_instance_class_service = ActivityInstanceClassService()
    return activity_instance_class_service.get_distinct_values_for_header(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/{activity_instance_class_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific activity instance class (in a specific version)",
    description="""
State before:
 - an activity instance class with uid must exist.

State after:
 - No change

Possible errors:
 - ActivityInstanceClass not found
 """,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_activity(
    activity_instance_class_uid: Annotated[str, ActivityInstanceClassUID],
) -> ActivityInstanceClass:
    activity_instance_class_service = ActivityInstanceClassService()
    return activity_instance_class_service.get_by_uid(uid=activity_instance_class_uid)


@router.get(
    "/{activity_instance_class_uid}/activity-item-classes",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List Activity Item Classes linked to given Activity Instance Class",
    description="""
State before:
 - uid must exist.

Business logic:
 - List activity item classes linked to given activity instance class

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
    },
)
def get_activity_item_classes(
    activity_instance_class_uid: Annotated[str, ActivityInstanceClassUID],
    ig_uid: Annotated[
        str | None,
        Query(description="Optionally, the uid of a specific DataModelIG, e.g. SDTMIG"),
    ] = None,
    dataset_uid: Annotated[
        str | None,
        Query(
            description="Optionally, the uid of a dataset to filter relevant activity item classes against"
        ),
    ] = None,
) -> list[CompactActivityItemClassForInstanceClass]:
    service = ActivityItemClassService()
    return service.get_all_for_activity_instance_class(
        activity_instance_class_uid, ig_uid, dataset_uid
    )


@router.get(
    "/{activity_instance_class_uid}/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List version history for activity-instance-classes",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for activity-instance-classes.
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
            "description": "Not Found - The activity with the specified 'activity_instance_class_uid' wasn't found.",
        },
    },
)
def get_versions(
    activity_instance_class_uid: Annotated[str, ActivityInstanceClassUID],
) -> list[ActivityInstanceClass]:
    activity_instance_class_service = ActivityInstanceClassService()
    return activity_instance_class_service.get_version_history(
        uid=activity_instance_class_uid
    )


@router.get(
    "/model-mappings/datasets",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns all mapped dataset (domain) uids",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
    },
)
# pylint: disable=unused-argument
def get_mapped_datasets(
    request: Request,  # request is actually required by the allow_exports decorator
    activity_instance_class_uid: Annotated[
        str | None,
        Query(description="Optionally, the uid of a specific ActivityInstanceClass"),
    ] = None,
    ig_uid: Annotated[
        str | None,
        Query(description="Optionally, the uid of a specific DataModelIG, e.g. SDTMIG"),
    ] = None,
    include_sponsor: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Whether to include sponsor datasets in the output or not. Defaults to True"
        ),
    ] = True,
) -> list[ActivityInstanceClassWithDataset]:
    activity_instance_class_service = ActivityInstanceClassService()
    return activity_instance_class_service.get_mapped_datasets(
        activity_instance_class_uid=activity_instance_class_uid,
        ig_uid=ig_uid,
        include_sponsor=include_sponsor,
    )


@router.post(
    "",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates new activity instance class.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).

Business logic:
 - New node is created for the activity instance class with the set properties.
 - relationships to specified parent classes are created (as in the model).
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'change_description' property will be set automatically to 'Initial version'.

State after:
 - ActivityInstanceClass is created in status Draft and assigned an initial minor version number as 0.1.
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
    },
)
def create(
    activity_instance_class_input: Annotated[ActivityInstanceClassInput, Body()],
) -> ActivityInstanceClass:
    activity_instance_class_service = ActivityInstanceClassService()
    return activity_instance_class_service.create(
        item_input=activity_instance_class_input
    )


@router.patch(
    "/{activity_instance_class_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Update activity instance class",
    description="""
State before:
 - uid must exist and activity instance class must exist in status draft.
 - The activity instance class must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - If activity instance class exist in status draft then attributes are updated.
- If the linked activity instance class is updated, the relationships are updated to point to the activity instance class value node.

State after:
 - attributes are updated for the instance class.
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
            "- The instance class is not in draft status.\n"
            "- The instance class had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The instance class with the specified 'activity_instance_class_uid' wasn't found.",
        },
    },
)
def edit(
    activity_instance_class_uid: Annotated[str, ActivityInstanceClassUID],
    activity_instance_class_input: Annotated[ActivityInstanceClassEditInput, Body()],
) -> ActivityInstanceClass:
    activity_instance_class_service = ActivityInstanceClassService()
    return activity_instance_class_service.edit_draft(
        uid=activity_instance_class_uid, item_edit_input=activity_instance_class_input
    )


@router.patch(
    "/{activity_instance_class_uid}/model-mappings",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Edit the mapping to dataset class",
    description="""
State before:
 - uid must exist

Business logic:
- Mapping to dataset class is replaced with the provided one

Possible errors:
- Invalid uid
""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The activity instance class with the specified 'activity_instance_class_uid' could not be found.",
        },
    },
)
def patch_mappings(
    activity_instance_class_uid: Annotated[str, ActivityInstanceClassUID],
    mapping_input: Annotated[
        ActivityInstanceClassMappingInput,
        Body(
            description="The uid of dataset classes to map activity instance class to."
        ),
    ],
) -> ActivityInstanceClass:
    activity_instance_class_service = ActivityInstanceClassService()
    return activity_instance_class_service.patch_mappings(
        uid=activity_instance_class_uid, mapping_input=mapping_input
    )


@router.post(
    "/{activity_instance_class_uid}/versions",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Create a new version of activity instance class",
    description="""
State before:
 - uid must exist and the activity instance class must be in status Final.

Business logic:
- The activity instance class is changed to a draft state.

State after:
 - ActivityInstanceClass changed status to Draft and assigned a new minor version number.
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
            "- The library doesn't allow to create activity instance classes.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The activity instance class is not in final status.\n"
            "- The activity instance class with the specified 'activity_instance_class_uid' could not be found.",
        },
    },
)
def new_version(
    activity_instance_class_uid: Annotated[str, ActivityInstanceClassUID],
) -> ActivityInstanceClass:
    activity_instance_class_service = ActivityInstanceClassService()
    return activity_instance_class_service.create_new_version(
        uid=activity_instance_class_uid
    )


@router.post(
    "/{activity_instance_class_uid}/approvals",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Approve draft version of activity instance class",
    description="""
State before:
 - uid must exist and activity instance class must be in status Draft.

Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically 'Approved version'.

State after:
 - ActivityInstanceClass changed status to Final and assigned a new major version number.
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
            "- The activity instance class is not in draft status.\n"
            "- The library doesn't allow to approve activity instance class.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance class with the specified 'activity_instance_class_uid' wasn't found.",
        },
    },
)
def approve(
    activity_instance_class_uid: Annotated[str, ActivityInstanceClassUID],
) -> ActivityInstanceClass:
    activity_instance_class_service = ActivityInstanceClassService()
    return activity_instance_class_service.approve(uid=activity_instance_class_uid)


@router.delete(
    "/{activity_instance_class_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of activity instance class",
    description="""
State before:
 - uid must exist and activity instance class must be in status Final.

Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status will be automatically set to 'Retired'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - Activity instance class changed status to Retired.
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
            "description": "BusinessLogicException - Reasons include e.g.: \n"
            "- The activity is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity with the specified 'activity_instance_class_uid' could not be found.",
        },
    },
)
def inactivate(
    activity_instance_class_uid: Annotated[str, ActivityInstanceClassUID],
) -> ActivityInstanceClass:
    activity_instance_class_service = ActivityInstanceClassService()
    return activity_instance_class_service.inactivate_final(
        uid=activity_instance_class_uid
    )


@router.post(
    "/{activity_instance_class_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a activity instance class",
    description="""
State before:
 - uid must exist and activity instance class must be in status Retired.

Business logic:
 - The latest 'Retired' version will remain the same as before.
 - The status will be automatically set to 'Final'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - ActivityInstanceClass changed status to Final.
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
            "- The activity instance class is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance class with the specified 'activity_instance_class_uid' could not be found.",
        },
    },
)
def reactivate(
    activity_instance_class_uid: Annotated[str, ActivityInstanceClassUID],
) -> ActivityInstanceClass:
    activity_instance_class_service = ActivityInstanceClassService()
    return activity_instance_class_service.reactivate_retired(
        uid=activity_instance_class_uid
    )


@router.get(
    "/{activity_instance_class_uid}/parent-class-overview",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get detailed overview of an activity instance parent class",
    description="""
Returns detailed information about an activity instance parent class including:
- Parent class details (name, definition, status, version, etc.)
- Child activity instance classes
- Activity item classes
- Version history

State before:
- UID must exist
- The class must be a parent class (have child classes)

State after:
- No change

Possible errors:
- Invalid uid
- Class is not a parent class
    """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance class with the specified UID wasn't found or is not a parent class.",
        },
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
def get_parent_class_overview(
    # pylint: disable=unused-argument
    request: Request,  # request is actually required by the allow_exports decorator
    activity_instance_class_uid: Annotated[str, ActivityInstanceClassUID],
    version: Annotated[
        str | None,
        Query(description="Select specific version, omit to view latest version"),
    ] = None,
) -> ActivityInstanceParentClassOverview:
    if version == "":
        version = None

    service = ActivityInstanceClassService()
    return service.get_parent_class_overview(
        parent_class_uid=activity_instance_class_uid, version=version
    )


@router.get(
    "/{activity_instance_class_uid}/overview",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get detailed overview of an activity instance class",
    description="""
Returns detailed information about an activity instance class including:
- Activity instance class details (name, definition, status, version, hierarchy, etc.)
- Activity item classes
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
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance class with the specified UID wasn't found.",
        },
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
def get_activity_instance_class_overview(
    # pylint: disable=unused-argument
    request: Request,  # request is actually required by the allow_exports decorator
    activity_instance_class_uid: Annotated[str, ActivityInstanceClassUID],
    version: Annotated[
        str | None,
        Query(description="Select specific version, omit to view latest version"),
    ] = None,
) -> ActivityInstanceClassOverview:
    if version == "":
        version = None

    service = ActivityInstanceClassService()
    return service.get_activity_instance_class_overview(
        activity_instance_class_uid=activity_instance_class_uid, version=version
    )


@router.get(
    "/{activity_instance_class_uid}/child-classes",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get paginated child activity instance classes",
    description="""
Retrieves a paginated list of child activity instance classes for a parent class.

When a version is specified, returns the child classes that were valid at that version's date.
Otherwise returns the latest version of each child class.

State before:
- Parent class UID must exist
- Parent class must have child classes (otherwise empty list)

State after:
- No change

Possible errors:
- Invalid uid
    """,
    response_model=GenericFilteringReturn[SimpleActivityInstanceClass],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance class with the specified UID wasn't found.",
        },
    },
)
@decorators.allow_exports(
    {
        "defaults": ["uid", "name", "version", "status", "modified_date"],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
def get_child_instance_classes(
    # pylint: disable=unused-argument
    request: Request,  # request is actually required by the allow_exports decorator
    activity_instance_class_uid: Annotated[str, ActivityInstanceClassUID],
    version: Annotated[
        str | None,
        Query(description="Select specific version, omit to view latest version"),
    ] = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
) -> GenericFilteringReturn[SimpleActivityInstanceClass]:
    if version == "":
        version = None

    service = ActivityInstanceClassService()
    return service.get_child_instance_classes_paginated(
        parent_uid=activity_instance_class_uid,
        version=version,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        sort_by=sort_by,
    )


@router.get(
    "/{activity_instance_class_uid}/item-classes",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get paginated activity item classes",
    description="""
Retrieves a paginated list of activity item classes for an activity instance class.

When a version is specified, returns the item classes that were valid at that version's date.
Otherwise returns the latest version of each item class.

State before:
- Activity instance class UID must exist

State after:
- No change

Possible errors:
- Invalid uid
    """,
    response_model=GenericFilteringReturn[SimpleActivityItemClass],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance class with the specified UID wasn't found.",
        },
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "name",
            "parent_name",
            "version",
            "status",
            "modified_date",
        ],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
def get_activity_item_classes_paginated(
    # pylint: disable=unused-argument
    request: Request,  # request is actually required by the allow_exports decorator
    activity_instance_class_uid: Annotated[str, ActivityInstanceClassUID],
    version: Annotated[
        str | None,
        Query(description="Select specific version, omit to view latest version"),
    ] = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
) -> GenericFilteringReturn[SimpleActivityItemClass]:
    if version == "":
        version = None

    service = ActivityInstanceClassService()
    return service.get_activity_item_classes_paginated(
        activity_instance_class_uid=activity_instance_class_uid,
        version=version,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        sort_by=sort_by,
    )


@router.delete(
    "/{activity_instance_class_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Delete draft version of activity instance class",
    description="""
State before:
 - uid must exist
 - The concept must be in status Draft in a version less then 1.0 (never been approved).
 - The concept must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - The draft concept is deleted.

State after:
 - ActivityInstanceClass is successfully deleted.

Possible errors:
 - Invalid uid or status not Draft or exist in version 1.0 or above (previously been approved) or not in an editable library.
    """,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The activity instance class was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity instance class is not in draft status.\n"
            "- The activity instance class was already in final state or is in use.\n"
            "- The library doesn't allow to delete activity instance class.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An activity instance class with the specified 'activity_instance_class_uid' could not be found.",
        },
    },
)
def delete_activity_instance_class(
    activity_instance_class_uid: Annotated[str, ActivityInstanceClassUID],
):
    activity_instance_class_service = ActivityInstanceClassService()
    activity_instance_class_service.soft_delete(uid=activity_instance_class_uid)
