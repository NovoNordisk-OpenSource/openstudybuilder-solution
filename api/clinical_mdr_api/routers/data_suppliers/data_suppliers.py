from typing import Annotated, Any

from fastapi import APIRouter, Body, Path
from starlette.requests import Request

from clinical_mdr_api.models.data_suppliers.data_supplier import (
    DataSupplier,
    DataSupplierEditInput,
    DataSupplierInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.data_suppliers.data_supplier import DataSupplierService
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/data-suppliers"
router = APIRouter()

DataSupplierUID = Path(description="The unique id of the DataSupplier")


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all data suppliers (for a given library)",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List all data suppliers in their latest version.

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
def get_data_suppliers(
    request: Request,  # request is actually required by the allow_exports decorator
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: Annotated[
        str | None, _generic_descriptions.FILTER_OPERATOR_QUERY
    ] = settings.default_filter_operator,
    total_count: Annotated[
        bool | None, _generic_descriptions.TOTAL_COUNT_QUERY
    ] = False,
) -> CustomPage[DataSupplier]:
    data_supplier_service = DataSupplierService()
    results = data_supplier_service.get_all_items(
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
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns possible values from the database for a given header",
    description="Allowed parameters include : field name for which to get possible values, "
    "search string to provide filtering for the field name, additional filters to apply on other fields",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_distinct_values_for_header(
    field_name: _generic_descriptions.HEADER_FIELD_NAME_QUERY,
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
    data_supplier_service = DataSupplierService()
    return data_supplier_service.get_distinct_values_for_header(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/{data_supplier_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns the latest/newest version of a specific data supplier identified by 'data_supplier_uid'.",
    description="""
State before:
 - a data supplier with uid must exist.

State after:
 - No change

Possible errors:
 - DataSupplier not found
 """,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_data_supplier(
    data_supplier_uid: Annotated[str, DataSupplierUID],
) -> DataSupplier:
    data_supplier_service = DataSupplierService()
    return data_supplier_service.get_by_uid(uid=data_supplier_uid)


@router.get(
    "/{data_supplier_uid}/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List version history for data suppliers",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for data suppliers.
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
            "description": "Not Found - The data supplier with the specified 'data_supplier_uid' wasn't found.",
        },
    },
)
def get_versions(
    data_supplier_uid: Annotated[str, DataSupplierUID],
) -> list[DataSupplier]:
    data_supplier_service = DataSupplierService()
    return data_supplier_service.get_version_history(uid=data_supplier_uid)


@router.patch(
    "/{data_supplier_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Update a data supplier",
    description="""
State before:
 - uid must exist.
 - The data supplier must belong to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - If data supplier exist in status draft then attributes are updated and then the data supplier is approved.
 - If data supplier exist in status final then new version is created and attributes are updated and then the data supplier is approved.
 - If the linked data supplier is updated, the relationships are updated to point to the data supplier value node.

State after:
 - attributes are updated for the data supplier.
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
            "- The data supplier is not in draft status.\n"
            "- The data supplier had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: _generic_descriptions.ERROR_404,
    },
)
def new_version_edit_approve(
    data_supplier_uid: Annotated[str, DataSupplierUID],
    data_supplier_input: Annotated[DataSupplierEditInput, Body()],
) -> DataSupplier:
    data_supplier_service = DataSupplierService()
    return data_supplier_service.new_version_edit_approve(
        uid=data_supplier_uid, item_edit_input=data_supplier_input
    )


@router.post(
    "",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates new data supplier.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).

Business logic:
 - New node is created for the data supplier with the set properties.
 - relationships to specified parent classes are created (as in the model).
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'change_description' property will be set automatically to 'Initial version'.

State after:
 - DataSupplier is created in status Draft and assigned an initial minor version number as 0.1.
 - Audit trail entry must be made with action of creating new Draft version.

Possible errors:
 - Invalid library or control terminology uid's specified.
""",
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The data supplier was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
    },
)
def create(
    data_supplier_input: Annotated[DataSupplierInput, Body()],
) -> DataSupplier:
    data_supplier_service = DataSupplierService()
    return data_supplier_service.create_approve(item_input=data_supplier_input)


@router.delete(
    "/{data_supplier_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of data supplier",
    description="""
State before:
 - uid must exist and data supplier must be in status Final.

Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status will be automatically set to 'Retired'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - DataSupplier changed status to Retired.
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
            "- The data supplier is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The data supplier with the specified 'data_supplier_uid' could not be found.",
        },
    },
)
def inactivate(
    data_supplier_uid: Annotated[str, DataSupplierUID],
) -> DataSupplier:
    data_supplier_service = DataSupplierService()
    return data_supplier_service.inactivate_final(uid=data_supplier_uid)


@router.post(
    "/{data_supplier_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a data supplier",
    description="""
State before:
 - uid must exist and data supplier must be in status Retired.

Business logic:
 - The latest 'Retired' version will remain the same as before.
 - The status will be automatically set to 'Final'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - DataSupplier changed status to Final.
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
            "- The data supplier is not in retired status.",
        },
        404: _generic_descriptions.ERROR_404,
    },
)
def reactivate(
    data_supplier_uid: Annotated[str, DataSupplierUID],
) -> DataSupplier:
    data_supplier_service = DataSupplierService()
    return data_supplier_service.reactivate_retired(uid=data_supplier_uid)
