from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from starlette.requests import Request

from clinical_mdr_api.models.odms.common_models import OdmElementWithParentUid
from clinical_mdr_api.models.odms.item import (
    OdmItem,
    OdmItemPatchInput,
    OdmItemPostInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.odms.items import OdmItemService
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/odms/items"
router = APIRouter()

# Argument definitions
OdmItemUID = Path(description="The unique id of the ODM Item.")


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Return every variable related to the selected status and version of the ODM Items",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    status_code=200,
    response_model_exclude_unset=True,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "oid",
            "library_name",
            "name",
            "aliases",
            "codelist",
            "comment",
            "datatype",
            "length",
            "significant_digits",
            "origin",
            "prompt",
            "translated_texts",
            "repeating",
            "start_date",
            "end_date",
            "effective_date",
            "retired_date",
            "end_date",
            "status",
            "version",
            "sas_field_name",
            "sds_var_name",
            "terms",
            "unit_definitions",
            "sas_dataset_name",
            "vendor_attributes",
            "vendor_element_attributes",
            "vendor_elements",
        ],
        "text/xml": [
            "uid",
            "oid",
            "library_name",
            "name",
            "aliases",
            "codelist",
            "comment",
            "datatype",
            "length",
            "significant_digits",
            "origin",
            "prompt",
            "translated_texts",
            "repeating",
            "start_date",
            "end_date",
            "effective_date",
            "retired_date",
            "end_date",
            "status",
            "version",
            "sas_field_name",
            "sds_var_name",
            "terms",
            "unit_definitions",
            "sas_dataset_name",
            "vendor_attributes",
            "vendor_element_attributes",
            "vendor_elements",
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
def get_all_odm_items(
    request: Request,  # request is actually required by the allow_exports decorator
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
) -> CustomPage[OdmItem]:
    odm_item_service = OdmItemService()
    results = odm_item_service.get_all_odms(
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
    odm_item_service = OdmItemService()
    return odm_item_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/item-groups",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get all ODM Items that belongs to an ODM Item Group",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_odm_items_that_belongs_to_item_group() -> list[OdmElementWithParentUid]:
    odm_item_service = OdmItemService()
    return odm_item_service.get_items_that_belongs_to_item_groups()


@router.get(
    "/{odm_item_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific ODM Item (in a specific version)",
    status_code=200,
    response_model_exclude_unset=True,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_odm_item(
    odm_item_uid: Annotated[str, OdmItemUID],
    version: Annotated[
        str | None, Query(description="Get a specific version of the ODM element")
    ] = None,
    fields: _generic_descriptions.SELECTED_FIELDS = None,
) -> OdmItem:
    odm_item_service = OdmItemService()
    return odm_item_service.get_by_uid(
        uid=odm_item_uid, version=version or None, fields=fields
    )


@router.get(
    "/{odm_item_uid}/relationships",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get UIDs of a specific ODM Item's relationships",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_active_relationships(
    odm_item_uid: Annotated[str, OdmItemUID],
) -> dict[str, list[str]]:
    odm_item_service = OdmItemService()
    return odm_item_service.get_active_relationships(uid=odm_item_uid)


@router.get(
    "/{odm_item_uid}/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List version history for ODM Item",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Items.
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
            "description": "Not Found - The ODM Item with the specified 'odm_item_uid' wasn't found.",
        },
    },
)
def get_odm_item_versions(odm_item_uid: Annotated[str, OdmItemUID]) -> list[OdmItem]:
    odm_item_service = OdmItemService()
    return odm_item_service.get_version_history(uid=odm_item_uid)


@router.post(
    "",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates a new Item in 'Draft' status with version 0.1",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The ODM Item was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
        409: _generic_descriptions.ERROR_409,
    },
)
def create_odm_item(
    odm_item_create_input: Annotated[OdmItemPostInput, Body()],
) -> OdmItem:
    odm_item_service = OdmItemService()
    return odm_item_service.create(odm_input=odm_item_create_input)


@router.patch(
    "/{odm_item_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Update ODM Item",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item is not in draft status.\n"
            "- The ODM Item had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item with the specified 'odm_item_uid' wasn't found.",
        },
    },
)
def edit_odm_item(
    odm_item_uid: Annotated[str, OdmItemUID],
    odm_item_edit_input: Annotated[OdmItemPatchInput, Body()],
) -> OdmItem:
    odm_item_service = OdmItemService()
    return odm_item_service.edit_draft(
        uid=odm_item_uid, odm_edit_input=odm_item_edit_input
    )


@router.post(
    "/{odm_item_uid}/versions",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Create a new version of ODM Item",
    description="""
State before:
 - uid must exist and the ODM Item must be in status Final.

Business logic:
- The ODM Item is changed to a draft state.

State after:
 - ODM Item changed status to Draft and assigned a new minor version number.
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
            "- The library doesn't allow to create ODM Items.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM Item is not in final status.\n"
            "- The ODM Item with the specified 'odm_item_uid' could not be found.",
        },
    },
)
def create_odm_item_version(odm_item_uid: Annotated[str, OdmItemUID]) -> OdmItem:
    odm_item_service = OdmItemService()
    return odm_item_service.create_new_version(
        uid=odm_item_uid, cascade_new_version=True, force_new_value_node=True
    )


@router.post(
    "/{odm_item_uid}/approvals",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Approve draft version of ODM Item",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item is not in draft status.\n"
            "- The library doesn't allow to approve ODM Item.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item with the specified 'odm_item_uid' wasn't found.",
        },
    },
)
def approve_odm_item(odm_item_uid: Annotated[str, OdmItemUID]) -> OdmItem:
    odm_item_service = OdmItemService()
    return odm_item_service.approve(uid=odm_item_uid, cascade_edit_and_approve=True)


@router.delete(
    "/{odm_item_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of ODM Item",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item with the specified 'odm_item_uid' could not be found.",
        },
    },
)
def inactivate_odm_item(odm_item_uid: Annotated[str, OdmItemUID]) -> OdmItem:
    odm_item_service = OdmItemService()
    return odm_item_service.inactivate_final(
        uid=odm_item_uid, cascade_inactivate=True, force_new_value_node=True
    )


@router.post(
    "/{odm_item_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a ODM Item",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item with the specified 'odm_item_uid' could not be found.",
        },
    },
)
def reactivate_odm_item(odm_item_uid: Annotated[str, OdmItemUID]) -> OdmItem:
    odm_item_service = OdmItemService()
    return odm_item_service.reactivate_retired(
        uid=odm_item_uid, cascade_reactivate=True, force_new_value_node=True
    )


@router.delete(
    "/{odm_item_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Delete draft version of ODM Item",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The ODM Item was successfully deleted."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item is not in draft status.\n"
            "- The ODM Item was already in final state or is in use.\n"
            "- The library doesn't allow to delete ODM Item.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM Item with the specified 'odm_item_uid' could not be found.",
        },
    },
)
def delete_odm_item(odm_item_uid: Annotated[str, OdmItemUID]):
    odm_item_service = OdmItemService()
    odm_item_service.soft_delete(uid=odm_item_uid, cascade_delete=True)
