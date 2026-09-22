"""ActivityItemClass hierarchies router."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from starlette.requests import Request

from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityItemClass,
    ActivityItemClassCodelist,
    ActivityItemClassCreateInput,
    ActivityItemClassEditInput,
    ActivityItemClassMappingInput,
    ActivityItemClassOverview,
    SimpleActivityInstanceClassForItem,
    ValidCodelistMappingInput,
)
from clinical_mdr_api.models.utils import CustomPage, GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.biomedical_concepts.activity_item_class import (
    ActivityItemClassService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/activity-item-classes"
router = APIRouter()

ActivityItemClassUID = Path(description="The unique id of the ActivityItemClass")
DatasetUID = Path(description="The unique id of the Dataset")


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all activity item classes (for a given library)",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List all activity item classes in their latest version, including properties derived from connected activity instance class.

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
            "display_name",
            "name",
            "nci_concept_id",
            "nci_concept_name",
            "definition",
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
        "variants": {
            "is_nsv": {
                "defaults": [
                    "uid",
                    "activity_instance_classes.name",
                    "non_standard_variable.code",
                    "display_name",
                    "name",
                    "nci_concept_id",
                    "nci_concept_name",
                    "non_standard_variable.is_multiple",
                    "non_standard_variable.is_cdisc_defined",
                    "data_type.name",
                    "role.name",
                    "non_standard_variable.length",
                    "non_standard_variable.origin_type.name",
                    "non_standard_variable.origin_source.name",
                    "non_standard_variable.algorithm",
                    "definition",
                    "non_standard_variable.derivation_rule",
                    "start_date",
                    "status",
                    "version",
                ],
            },
        },
    }
)
# pylint: disable=unused-argument
def get_activity_item_classes(
    request: Request,  # request is actually required by the allow_exports decorator
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    is_nsv: Annotated[
        bool | None,
        Query(
            description=(
                "When set to true, return only Non Standard Variable nodes. "
                "When set to false, return only Activity Item Class nodes that are not NSV. "
                "When omitted, both are returned."
            )
        ),
    ] = None,
) -> CustomPage[ActivityItemClass]:
    activity_item_class_service = ActivityItemClassService()
    results = activity_item_class_service.get_all_items(
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        is_nsv=is_nsv,
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all versions of activity item classes",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List version history of activity item classes
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
def get_activity_item_classes_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[ActivityItemClass]:
    activity_item_class_service = ActivityItemClassService()
    results = activity_item_class_service.get_all_concept_versions(
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
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.get_distinct_values_for_header(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/{activity_item_class_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific activity item class (in a specific version)",
    description="""
State before:
 - an activity item class with uid must exist.

State after:
 - No change

Possible errors:
 - ActivityItemClass not found
 """,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_activity(
    activity_item_class_uid: Annotated[str, ActivityItemClassUID],
) -> ActivityItemClass:
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.get_by_uid(uid=activity_item_class_uid)


@router.get(
    "/{activity_item_class_uid}/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List version history for activity item classes",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for activity item classes.
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
            "description": "Not Found - The activity with the specified 'activity_item_class_uid' wasn't found.",
        },
    },
)
def get_versions(
    activity_item_class_uid: Annotated[str, ActivityItemClassUID],
) -> list[ActivityItemClass]:
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.get_version_history(uid=activity_item_class_uid)


@router.get(
    "/{activity_item_class_uid}/datasets/{dataset_uid}/codelists",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns all related codelists.",
    description="""
State before:
 - uids of actvity item class and dataset must exist.

Business logic:
 - List the codelists related to the given activity item class.

State after:
 - No change

Possible errors:
 - Invalid uids.
    """,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
    },
)
# pylint: disable=unused-argument
def get_all_codelists(
    request: Request,  # request is actually required by the allow_exports decorator
    activity_item_class_uid: Annotated[str, ActivityItemClassUID],
    dataset_uid: Annotated[str, DatasetUID],
    use_sponsor_model: Annotated[
        bool,
        Query(
            description=(
                "Whether to use the Sponsor Model to filter Codelists and Terms.\n\n"
                "If set to True, the Sponsor Model will take precedence.\n\n"
                "Defaults to True."
            )
        ),
    ] = True,
    ct_catalogue_name: Annotated[
        str | None,
        Query(
            description="Optionally, the name of a CT Catalogue to filter Codelists."
        ),
    ] = None,
    valid_codelists_for_item: Annotated[
        bool,
        Query(
            description=(
                "Whether to look for codelists using the Valid codelists relationship.\n\n"
                "if set to True, this will take precedence over SDTMIG and Sponsor Model.\n\n"
                "Defaults to False."
            )
        ),
    ] = False,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[ActivityItemClassCodelist]:
    results = ActivityItemClassService().get_codelists_of_activity_item_class(
        activity_item_class_uid=activity_item_class_uid,
        dataset_uid=dataset_uid,
        use_sponsor_model=use_sponsor_model,
        ct_catalogue_name=ct_catalogue_name,
        valid_codelists_for_item=valid_codelists_for_item,
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


@router.post(
    "",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates new activity item class.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).

Business logic:
 - New node is created for the activity item class with the set properties.
 - relationships to specified parent classes are created (as in the model).
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'change_description' property will be set automatically to 'Initial version'.

State after:
 - ActivityItemClass is created in status Draft and assigned an initial minor version number as 0.1.
 - The relationship between ActivityItemClass and ActivityInstanceClass is created.
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
    activity_item_class_input: Annotated[ActivityItemClassCreateInput, Body()],
) -> ActivityItemClass:
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.create(concept_input=activity_item_class_input)


@router.patch(
    "/{activity_item_class_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Update activity item class",
    description="""
State before:
 - uid must exist and activity item class must exist in status draft.
 - The activity item class must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - If activity item class exist in status draft then attributes are updated.
- If the linked activity item class is updated, the relationships are updated to point to the activity item class value node.

State after:
 - attributes are updated for the item class.
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
            "- The item class is not in draft status.\n"
            "- The item class had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The item class with the specified 'activity_item_class_uid' wasn't found.",
        },
    },
)
def edit(
    activity_item_class_uid: Annotated[str, ActivityItemClassUID],
    activity_item_class_input: Annotated[ActivityItemClassEditInput, Body()],
) -> ActivityItemClass:
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.edit_draft(
        uid=activity_item_class_uid, concept_edit_input=activity_item_class_input
    )


@router.patch(
    "/{activity_item_class_uid}/model-mappings",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Edit the mappings to variable classes",
    description="""
State before:
- uid must exist

Business logic:
- Mappings to variable classes are replaced with the provided ones

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
            "- The activity item class with the specified 'activity_item_class_uid' could not be found.",
        },
    },
)
def patch_mappings(
    activity_item_class_uid: Annotated[str, ActivityItemClassUID],
    mapping_input: Annotated[
        ActivityItemClassMappingInput,
        Body(description="The uid of variable classes to map activity item class to."),
    ],
) -> ActivityItemClass:
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.patch_mappings(
        uid=activity_item_class_uid, mapping_input=mapping_input
    )


@router.patch(
    "/{activity_item_class_uid}/valid-codelist-mappings",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Edit the mappings to valid codelists for ActivityItems",
    description="""
State before:
- uid must exist

Business logic:
- Mappings to valid codelists are replaced with the provided ones

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
            "- The activity item class with the specified 'activity_item_class_uid' could not be found.",
        },
    },
)
def patch_valid_codelist_mappings(
    activity_item_class_uid: Annotated[str, ActivityItemClassUID],
    mapping_input: Annotated[
        ValidCodelistMappingInput,
        Body(description="The uid of valid codelists to map activity item class to."),
    ],
) -> ActivityItemClass:
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.patch_valid_codelist_mappings(
        uid=activity_item_class_uid, mapping_input=mapping_input
    )


@router.post(
    "/{activity_item_class_uid}/versions",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Create a new version of activity item class",
    description="""
State before:
 - uid must exist and the activity item class must be in status Final.

Business logic:
- The activity item class is changed to a draft state.

State after:
 - ActivityItemClass changed status to Draft and assigned a new minor version number.
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
            "- The library doesn't allow to create activity item classes.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The activity item class is not in final status.\n"
            "- The activity item class with the specified 'activity_item_class_uid' could not be found.",
        },
    },
)
def new_version(
    activity_item_class_uid: Annotated[str, ActivityItemClassUID],
) -> ActivityItemClass:
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.create_new_version(uid=activity_item_class_uid)


@router.post(
    "/{activity_item_class_uid}/approvals",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Approve draft version of activity item class",
    description="""
State before:
 - uid must exist and activity item class must be in status Draft.

Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically 'Approved version'.

State after:
 - ActivityItemClass changed status to Final and assigned a new major version number.
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
            "- The activity item class is not in draft status.\n"
            "- The library doesn't allow to approve activity item class.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity item class with the specified 'activity_item_class_uid' wasn't found.",
        },
    },
)
def approve(
    activity_item_class_uid: Annotated[str, ActivityItemClassUID],
) -> ActivityItemClass:
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.approve(uid=activity_item_class_uid)


@router.delete(
    "/{activity_item_class_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of activity item class",
    description="""
State before:
 - uid must exist and activity item class must be in status Final.

Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status will be automatically set to 'Retired'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - Activity item class changed status to Retired.
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
            "description": "Not Found - The activity with the specified 'activity_item_class_uid' could not be found.",
        },
    },
)
def inactivate(
    activity_item_class_uid: Annotated[str, ActivityItemClassUID],
) -> ActivityItemClass:
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.inactivate_final(uid=activity_item_class_uid)


@router.post(
    "/{activity_item_class_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a activity item class",
    description="""
State before:
 - uid must exist and activity item class must be in status Retired.

Business logic:
 - The latest 'Retired' version will remain the same as before.
 - The status will be automatically set to 'Final'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - ActivityItemClass changed status to Final.
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
            "- The activity item class is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity item class with the specified 'activity_item_class_uid' could not be found.",
        },
    },
)
def reactivate(
    activity_item_class_uid: Annotated[str, ActivityItemClassUID],
) -> ActivityItemClass:
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.reactivate_retired(uid=activity_item_class_uid)


@router.get(
    "/{activity_item_class_uid}/overview",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get detailed overview of an activity item class",
    description="""
Returns detailed information about an activity item class including:
- Activity item class details (name, definition, NCI code, status, version, etc.)
- Activity Instance Classes that use this item class
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
            "description": "Not Found - The activity item class with the specified UID wasn't found.",
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
def get_activity_item_class_overview(
    # pylint: disable=unused-argument
    request: Request,  # request is actually required by the allow_exports decorator
    activity_item_class_uid: Annotated[str, ActivityItemClassUID],
    version: Annotated[
        str | None,
        Query(description="Select specific version, omit to view latest version"),
    ] = None,
) -> ActivityItemClassOverview:
    if version == "":
        version = None

    service = ActivityItemClassService()
    return service.get_activity_item_class_overview(
        activity_item_class_uid=activity_item_class_uid, version=version
    )


@router.get(
    "/{activity_item_class_uid}/activity-instance-classes",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get paginated Activity Instance Classes that use this item",
    description="""
Retrieves a paginated list of Activity Instance Classes that use this Activity Item Class.

When a version is specified, returns the instance classes that were using this item at that version's date.
Otherwise returns the latest version of each instance class.

State before:
- Activity item class UID must exist

State after:
- No change

Possible errors:
- Invalid uid
    """,
    response_model=GenericFilteringReturn[SimpleActivityInstanceClassForItem],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity item class with the specified UID wasn't found.",
        },
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "name",
            "mandatory",
            "adam_param_specific_enabled",
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
def get_activity_instance_classes_using_item(
    # pylint: disable=unused-argument
    request: Request,  # request is actually required by the allow_exports decorator
    activity_item_class_uid: Annotated[str, ActivityItemClassUID],
    version: Annotated[
        str | None,
        Query(description="Select specific version, omit to view latest version"),
    ] = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> GenericFilteringReturn[SimpleActivityInstanceClassForItem]:
    if version == "":
        version = None

    service = ActivityItemClassService()
    return service.get_activity_instance_classes_using_item_paginated(
        activity_item_class_uid=activity_item_class_uid,
        version=version,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
    )


@router.delete(
    "/{activity_item_class_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Delete draft version of activity item class",
    description="""
State before:
 - uid must exist
 - The concept must be in status Draft in a version less then 1.0 (never been approved).
 - The concept must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - The draft concept is deleted.

State after:
 - ActivityItemClass is successfully deleted.

Possible errors:
 - Invalid uid or status not Draft or exist in version 1.0 or above (previously been approved) or not in an editable library.
    """,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The activity item class was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity item class is not in draft status.\n"
            "- The activity item class was already in final state or is in use.\n"
            "- The library doesn't allow to delete activity item class.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An activity item class with the specified 'activity_item_class_uid' could not be found.",
        },
    },
)
def delete_activity_item_class(
    activity_item_class_uid: Annotated[str, ActivityItemClassUID],
):
    activity_item_class_service = ActivityItemClassService()
    activity_item_class_service.soft_delete(uid=activity_item_class_uid)
