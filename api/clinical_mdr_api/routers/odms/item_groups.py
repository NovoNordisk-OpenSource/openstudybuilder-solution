from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from starlette.requests import Request

from clinical_mdr_api.models.odms.common_models import OdmElementWithParentUid
from clinical_mdr_api.models.odms.item_group import (
    OdmItemGroup,
    OdmItemGroupItemPostInput,
    OdmItemGroupPatchInput,
    OdmItemGroupPostInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.odms.item_groups import OdmItemGroupService
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/odms/item-groups"
router = APIRouter()

# Argument definitions
OdmItemGroupUID = Path(description="The unique id of the ODM Item Group.")


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Return every variable related to the selected status and version of the ODM Item Groups",
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
            "translated_texts",
            "repeating",
            "start_date",
            "end_date",
            "effective_date",
            "retired_date",
            "end_date",
            "status",
            "version",
            "sas_dataset_name",
            "sdtm_domains",
            "vendor_attributes",
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
            "translated_texts",
            "repeating",
            "start_date",
            "end_date",
            "effective_date",
            "retired_date",
            "end_date",
            "status",
            "version",
            "sas_dataset_name",
            "sdtm_domains",
            "vendor_attributes",
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
def get_all_odm_item_groups(
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
) -> CustomPage[OdmItemGroup]:
    odm_item_group_service = OdmItemGroupService()
    results = odm_item_group_service.get_all_odms(
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
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/forms",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get all ODM Item Groups that belongs to an ODM Form",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
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
            "oid",
            "library_name",
            "name",
            "description",
            "forms",
            "start_date",
            "end_date",
            "effective_date",
            "retired_date",
            "end_date",
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
def get_odm_item_group_that_belongs_to_form(
    request: Request,  # request is actually required by the allow_exports decorator
) -> list[OdmElementWithParentUid]:
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.get_item_groups_that_belongs_to_form()


@router.get(
    "/{odm_item_group_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific ODM Item Group (in a specific version)",
    status_code=200,
    response_model_exclude_unset=True,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_odm_item_group(
    odm_item_group_uid: Annotated[str, OdmItemGroupUID],
    version: Annotated[
        str | None, Query(description="Get a specific version of the ODM element")
    ] = None,
    fields: _generic_descriptions.SELECTED_FIELDS = None,
) -> OdmItemGroup:
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.get_by_uid(
        uid=odm_item_group_uid, version=version or None, fields=fields
    )


@router.get(
    "/{odm_item_group_uid}/relationships",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get UIDs of a specific ODM Item Group's relationships",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_active_relationships(
    odm_item_group_uid: Annotated[str, OdmItemGroupUID],
) -> dict[str, list[str]]:
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.get_active_relationships(uid=odm_item_group_uid)


@router.get(
    "/{odm_item_group_uid}/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List version history for ODM Item Group",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Item Groups.
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
            "description": "Not Found - The ODM Item Group with the specified 'odm_item_group_uid' wasn't found.",
        },
    },
)
def get_odm_item_group_versions(
    odm_item_group_uid: Annotated[str, OdmItemGroupUID],
) -> list[OdmItemGroup]:
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.get_version_history(uid=odm_item_group_uid)


@router.post(
    "",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates a new Item Group in 'Draft' status with version 0.1",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The ODM Item Group was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
        409: _generic_descriptions.ERROR_409,
    },
)
def create_odm_item_group(
    odm_item_group_create_input: Annotated[OdmItemGroupPostInput, Body()],
) -> OdmItemGroup:
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.create(odm_input=odm_item_group_create_input)


@router.patch(
    "/{odm_item_group_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Update ODM Item Group",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item Group is not in draft status.\n"
            "- The ODM Item Group had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item Group with the specified 'odm_item_group_uid' wasn't found.",
        },
    },
)
def edit_odm_item_group(
    odm_item_group_uid: Annotated[str, OdmItemGroupUID],
    odm_item_group_edit_input: Annotated[OdmItemGroupPatchInput, Body()],
) -> OdmItemGroup:
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.edit_draft(
        uid=odm_item_group_uid, odm_edit_input=odm_item_group_edit_input
    )


@router.post(
    "/{odm_item_group_uid}/versions",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Create a new version of ODM Item Group",
    description="""
State before:
 - uid must exist and the ODM Item Group must be in status Final.

Business logic:
- The ODM Item Group is changed to a draft state.

State after:
 - ODM Item Group changed status to Draft and assigned a new minor version number.
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
            "- The library doesn't allow to create ODM Item Groups.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM Item Group is not in final status.\n"
            "- The ODM Item Group with the specified 'odm_item_group_uid' could not be found.",
        },
    },
)
def create_odm_item_group_version(
    odm_item_group_uid: Annotated[str, OdmItemGroupUID],
    cascade_new_version: Annotated[
        bool,
        Query(description="If true, all child elements will also get a new version."),
    ] = False,
) -> OdmItemGroup:
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.create_new_version(
        uid=odm_item_group_uid,
        cascade_new_version=cascade_new_version,
        force_new_value_node=True,
    )


@router.post(
    "/{odm_item_group_uid}/approvals",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Approve draft version of ODM Item Group",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item Group is not in draft status.\n"
            "- The library doesn't allow to approve ODM Item Group.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item Group with the specified 'odm_item_group_uid' wasn't found.",
        },
    },
)
def approve_odm_item_group(
    odm_item_group_uid: Annotated[str, OdmItemGroupUID],
) -> OdmItemGroup:
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.approve(
        uid=odm_item_group_uid, cascade_edit_and_approve=True
    )


@router.delete(
    "/{odm_item_group_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of ODM Item Group",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item Group is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item Group with the specified 'odm_item_group_uid' could not be found.",
        },
    },
)
def inactivate_odm_item_group(
    odm_item_group_uid: Annotated[str, OdmItemGroupUID],
) -> OdmItemGroup:
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.inactivate_final(
        uid=odm_item_group_uid, cascade_inactivate=True, force_new_value_node=True
    )


@router.post(
    "/{odm_item_group_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a ODM Item Group",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item Group is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item Group with the specified 'odm_item_group_uid' could not be found.",
        },
    },
)
def reactivate_odm_item_group(
    odm_item_group_uid: Annotated[str, OdmItemGroupUID],
) -> OdmItemGroup:
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.reactivate_retired(
        uid=odm_item_group_uid, cascade_reactivate=True, force_new_value_node=True
    )


@router.post(
    "/{odm_item_group_uid}/items",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Adds items to the ODM Item Group.",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The items were successfully added to the ODM Item Group."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The items with the specified 'odm_item_group_uid' wasn't found.",
        },
    },
)
def add_item_to_odm_item_group(
    odm_item_group_uid: Annotated[str, OdmItemGroupUID],
    odm_item_group_item_post_input: Annotated[list[OdmItemGroupItemPostInput], Body()],
    override: Annotated[
        bool,
        Query(
            description="""
When true, replaces all existing item relationships with the provided ones.  
When false, appends the provided item relationships to existing ones, continuing the order sequence.
            """,
        ),
    ] = False,
) -> OdmItemGroup:
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.add_items(
        uid=odm_item_group_uid,
        odm_item_group_item_post_input=odm_item_group_item_post_input,
        override=override,
    )


@router.delete(
    "/{odm_item_group_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Delete draft version of ODM Item Group",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The ODM Item Group was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item Group is not in draft status.\n"
            "- The ODM Item Group was already in final state or is in use.\n"
            "- The library doesn't allow to delete ODM Item Group.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM Item Group with the specified 'odm_item_group_uid' could not be found.",
        },
    },
)
def delete_odm_item_group(odm_item_group_uid: Annotated[str, OdmItemGroupUID]):
    odm_item_group_service = OdmItemGroupService()
    odm_item_group_service.soft_delete(uid=odm_item_group_uid, cascade_delete=True)
