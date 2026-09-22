from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query

from clinical_mdr_api.models.odms.condition import (
    OdmCondition,
    OdmConditionPatchInput,
    OdmConditionPostInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.odms.conditions import OdmConditionService
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/odms/conditions"
router = APIRouter()

# Argument definitions
OdmConditionUID = Path(description="The unique id of the ODM Condition.")


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Return every variable related to the selected status and version of the ODM Conditions",
    status_code=200,
    response_model_exclude_unset=True,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_odm_conditions(
    library_name: Annotated[str | None, Query()] = None,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    version: Annotated[
        str | None, Query(description="Get a specific version of the ODM element")
    ] = None,
    fields: _generic_descriptions.SELECTED_FIELDS = None,
) -> CustomPage[OdmCondition]:
    odm_condition_service = OdmConditionService()
    results = odm_condition_service.get_all_odms(
        library=library_name,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        version=version or None,
        fields=fields,
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/headers",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
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
    odm_condition_service = OdmConditionService()
    return odm_condition_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/{odm_condition_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific ODM Condition (in a specific version)",
    status_code=200,
    response_model_exclude_unset=True,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_odm_condition(
    odm_condition_uid: Annotated[str, OdmConditionUID],
    version: Annotated[
        str | None, Query(description="Get a specific version of the ODM element")
    ] = None,
    fields: _generic_descriptions.SELECTED_FIELDS = None,
) -> OdmCondition:
    odm_condition_service = OdmConditionService()
    return odm_condition_service.get_by_uid(
        uid=odm_condition_uid, version=version or None, fields=fields
    )


@router.get(
    "/{odm_condition_uid}/relationships",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get UIDs of a specific ODM Condition's relationships",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_active_relationships(
    odm_condition_uid: Annotated[str, OdmConditionUID],
) -> dict[str, list[str]]:
    odm_condition_service = OdmConditionService()
    return odm_condition_service.get_active_relationships(uid=odm_condition_uid)


@router.get(
    "/{odm_condition_uid}/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List version history for ODM Condition",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Conditions.
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
            "description": "Not Found - The ODM Condition with the specified 'odm_condition_uid' wasn't found.",
        },
    },
)
def get_odm_condition_versions(
    odm_condition_uid: Annotated[str, OdmConditionUID],
) -> list[OdmCondition]:
    odm_condition_service = OdmConditionService()
    return odm_condition_service.get_version_history(uid=odm_condition_uid)


@router.post(
    "",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates a new Condition in 'Draft' status with version 0.1",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The ODM Condition was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
        409: _generic_descriptions.ERROR_409,
    },
)
def create_odm_condition(
    odm_condition_create_input: Annotated[OdmConditionPostInput, Body()],
) -> OdmCondition:
    odm_condition_service = OdmConditionService()
    return odm_condition_service.create(odm_input=odm_condition_create_input)


@router.patch(
    "/{odm_condition_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Update ODM Condition",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Condition is not in draft status.\n"
            "- The ODM Condition had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Condition with the specified 'odm_condition_uid' wasn't found.",
        },
        409: _generic_descriptions.ERROR_409,
    },
)
def edit_odm_condition(
    odm_condition_uid: Annotated[str, OdmConditionUID],
    odm_condition_edit_input: Annotated[OdmConditionPatchInput, Body()],
) -> OdmCondition:
    odm_condition_service = OdmConditionService()
    return odm_condition_service.edit_draft(
        uid=odm_condition_uid, odm_edit_input=odm_condition_edit_input
    )


@router.post(
    "/{odm_condition_uid}/versions",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Create a new version of ODM Condition",
    description="""
State before:
 - uid must exist and the ODM Condition must be in status Final.

Business logic:
- The ODM Condition is changed to a draft state.

State after:
 - ODM Condition changed status to Draft and assigned a new minor version number.
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
            "- The library doesn't allow to create ODM Conditions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM Condition is not in final status.\n"
            "- The ODM Condition with the specified 'odm_condition_uid' could not be found.",
        },
    },
)
def create_odm_condition_version(
    odm_condition_uid: Annotated[str, OdmConditionUID],
) -> OdmCondition:
    odm_condition_service = OdmConditionService()
    return odm_condition_service.create_new_version(
        uid=odm_condition_uid, cascade_new_version=True
    )


@router.post(
    "/{odm_condition_uid}/approvals",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Approve draft version of ODM Condition",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Condition is not in draft status.\n"
            "- The library doesn't allow to approve ODM Condition.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Condition with the specified 'odm_condition_uid' wasn't found.",
        },
    },
)
def approve_odm_condition(
    odm_condition_uid: Annotated[str, OdmConditionUID],
) -> OdmCondition:
    odm_condition_service = OdmConditionService()
    return odm_condition_service.approve(
        uid=odm_condition_uid, cascade_edit_and_approve=True
    )


@router.delete(
    "/{odm_condition_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of ODM Condition",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Condition is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Condition with the specified 'odm_condition_uid' could not be found.",
        },
    },
)
def inactivate_odm_condition(
    odm_condition_uid: Annotated[str, OdmConditionUID],
) -> OdmCondition:
    odm_condition_service = OdmConditionService()
    return odm_condition_service.inactivate_final(
        uid=odm_condition_uid, cascade_inactivate=True
    )


@router.post(
    "/{odm_condition_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a ODM Condition",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Condition is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Condition with the specified 'odm_condition_uid' could not be found.",
        },
    },
)
def reactivate_odm_condition(
    odm_condition_uid: Annotated[str, OdmConditionUID],
) -> OdmCondition:
    odm_condition_service = OdmConditionService()
    return odm_condition_service.reactivate_retired(
        uid=odm_condition_uid, cascade_reactivate=True
    )


@router.delete(
    "/{odm_condition_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Delete draft version of ODM Condition",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The ODM Condition was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Condition is not in draft status.\n"
            "- The ODM Condition was already in final state or is in use.\n"
            "- The library doesn't allow to delete ODM Condition.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM Condition with the specified 'odm_condition_uid' could not be found.",
        },
    },
)
def delete_odm_condition(odm_condition_uid: Annotated[str, OdmConditionUID]):
    odm_condition_service = OdmConditionService()
    odm_condition_service.soft_delete(uid=odm_condition_uid, cascade_delete=True)
