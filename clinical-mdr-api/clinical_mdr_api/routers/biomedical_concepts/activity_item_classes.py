"""ActivityItemClass hierarchies router."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query, Response, status
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityItemClass,
    ActivityItemClassCreateInput,
    ActivityItemClassEditInput,
    ActivityItemClassMappingInput,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    TermWithCodelistMetadata,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.biomedical_concepts.activity_item_class import (
    ActivityItemClassService,
)
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/activity-item-classes"
router = APIRouter()

ActivityItemClassUID = Path(description="The unique id of the ActivityItemClass")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
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
    response_model=CustomPage[ActivityItemClass],
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
def get_activity_item_classes(
    request: Request,  # request is actually required by the allow_exports decorator
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
    activity_item_class_service = ActivityItemClassService()
    results = activity_item_class_service.get_all_items(
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
    )
    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/headers",
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
    search_string: Annotated[
        str | None, Query(description=_generic_descriptions.HEADER_SEARCH_STRING)
    ] = "",
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
    dependencies=[rbac.LIBRARY_READ],
    summary="Get details on a specific activity item class (in a specific version)",
    description="""
State before:
 - an activity item class with uid must exist.

State after:
 - No change

Possible errors:
 - ActivityItemClass not found
 """,
    response_model=ActivityItemClass,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_activity(
    activity_item_class_uid: Annotated[str, ActivityItemClassUID],
):
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.get_by_uid(uid=activity_item_class_uid)


@router.get(
    "/{activity_item_class_uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
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
    response_model=list[ActivityItemClass],
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
):
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.get_version_history(uid=activity_item_class_uid)


@router.get(
    "/{activity_item_class_uid}/terms",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all terms names and attributes.",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[TermWithCodelistMetadata],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "term_uid",
            "catalogue_name",
            "codelist_uid",
            "library_name",
            "name.sponsor_preferred_name",
            "name.sponsor_preferred_name_sentence_case",
            "name.order",
            "name.start_date",
            "name.end_date",
            "name.status",
            "name.version",
            "name.change_description",
            "name.author_username",
            "attributes.code_submission_value",
            "attributes.name_submission_value",
            "attributes.nci_preferred_name",
            "attributes.definition",
            "attributes.start_date",
            "attributes.end_date",
            "attributes.status",
            "attributes.version",
            "attributes.change_description",
            "attributes.author_username",
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
def get_all_terms(
    request: Request,  # request is actually required by the allow_exports decorator
    activity_item_class_uid: Annotated[str, ActivityItemClassUID],
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
    results = ActivityItemClassService().get_terms_of_activity_item_class(
        activity_item_class_uid=activity_item_class_uid,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
    )
    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
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
    response_model=ActivityItemClass,
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
):
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.create(item_input=activity_item_class_input)


@router.patch(
    "/{activity_item_class_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
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
    response_model=ActivityItemClass,
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
):
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.edit_draft(
        uid=activity_item_class_uid, item_edit_input=activity_item_class_input
    )


@router.patch(
    "/{activity_item_class_uid}/model-mappings",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Edit the mappings to variable classes",
    description="""
State before:
- uid must exist

Business logic:
- Mappings to variable classes are replaced with the provided ones

Possible errors:
- Invalid uid
""",
    response_model=ActivityItemClass,
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
):
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.patch_mappings(
        uid=activity_item_class_uid, mapping_input=mapping_input
    )


@router.post(
    "/{activity_item_class_uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
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
    response_model=ActivityItemClass,
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
):
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.create_new_version(uid=activity_item_class_uid)


@router.post(
    "/{activity_item_class_uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
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
    response_model=ActivityItemClass,
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
):
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.approve(uid=activity_item_class_uid)


@router.delete(
    "/{activity_item_class_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
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
    response_model=ActivityItemClass,
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
):
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.inactivate_final(uid=activity_item_class_uid)


@router.post(
    "/{activity_item_class_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
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
    response_model=ActivityItemClass,
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
):
    activity_item_class_service = ActivityItemClassService()
    return activity_item_class_service.reactivate_retired(uid=activity_item_class_uid)


@router.delete(
    "/{activity_item_class_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
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
    response_model=None,
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
    return Response(status_code=status.HTTP_204_NO_CONTENT)
