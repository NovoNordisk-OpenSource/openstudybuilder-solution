"""medicinal_products router"""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api.models.concepts.medicinal_product import (
    MedicinalProduct,
    MedicinalProductCreateInput,
    MedicinalProductEditInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.concepts.medicinal_products_service import (
    MedicinalProductService,
)
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/concepts"
router = APIRouter()

MedicinalProductUID = Path(description="The unique id of the medicinal product")


@router.get(
    "/medicinal-products",
    dependencies=[rbac.LIBRARY_READ],
    summary="List all medicinal products (for a given library)",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List all medicinal products in their latest version, including properties derived from linked control terminology.

State after:
 - No change

Possible errors:
 - Invalid library name specified.
 
{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[MedicinalProduct],
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
            "external_id",
            "compound=compound.name",
            "pharmaceutical_products=pharmaceutical_products.uid",
            "delivery_device=delivery_device.name",
            "dispenser=dispenser.name",
            "dose_values=dose_values.value",
            "dose_values_units=dose_values.unit_label",
            "dose_frequency=dose_frequency.name",
            "start_date",
            "version",
            "status",
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
def get_medicinal_products(
    request: Request,  # request is actually required by the allow_exports decorator
    library_name: Annotated[str | None, Query()] = None,
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
    medicinal_product_service = MedicinalProductService()
    results = medicinal_product_service.get_all_concepts(
        library=library_name,
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
    "/medicinal-products/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List all versions of medicinal products",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List version history of medicinal products
 - The returned versions are ordered by version start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid library name specified.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[MedicinalProduct],
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
            "external_id",
            "compound=compound.name",
            "pharmaceutical_products=pharmaceutical_products.uid",
            "delivery_device=delivery_device.name",
            "dispenser=dispenser.name",
            "dose_values=dose_values.value",
            "dose_values_units=dose_values.unit_label",
            "dose_frequency=dose_frequency.name",
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
def get_medicinal_products_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    library_name: Annotated[str | None, Query()] = None,
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
    service = MedicinalProductService()
    results = service.get_all_concept_versions(
        library=library_name,
        sort_by={"start_date": False},
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
    "/medicinal-products/headers",
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
    library_name: Annotated[str | None, Query()] = None,
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
    medicinal_product_service = MedicinalProductService()
    return medicinal_product_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/medicinal-products/{medicinal_product_uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get details on a specific medicinal product (in a specific version)",
    description="""
Possible errors:
 - Invalid uid, at_specified_date_time, status or version.
 """,
    response_model=MedicinalProduct,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_activity(
    medicinal_product_uid: Annotated[str, MedicinalProductUID],
):
    medicinal_product_service = MedicinalProductService()
    return medicinal_product_service.get_by_uid(uid=medicinal_product_uid)


@router.get(
    "/medicinal-products/{medicinal_product_uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List version history for medicinal products",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for medicinal products.
 - The returned versions are ordered by start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=list[MedicinalProduct],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The medicinal product with the specified 'medicinal_product_uid' wasn't found.",
        },
    },
)
def get_versions(
    medicinal_product_uid: Annotated[str, MedicinalProductUID],
):
    medicinal_product_service = MedicinalProductService()
    return medicinal_product_service.get_version_history(uid=medicinal_product_uid)


@router.post(
    "/medicinal-products",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates new medicinal product.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).
 - The specified CT term uids must exist, and the term names are in a final state.

Business logic:
 - New node is created for the medicinal product with the set properties.
 - relationships to specified control terminology are created (as in the model).
 - relationships to specified activity parent are created (as in the model)
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'change_description' property will be set automatically to 'Initial version'.

State after:
 - medicinal product is created in status Draft and assigned an initial minor version number as 0.1.
 - Audit trail entry must be made with action of creating new Draft version.

Possible errors:
 - Invalid library or control terminology uid's specified.
""",
    response_model=MedicinalProduct,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The medicinal product was successfully created."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
    },
)
def create(
    medicinal_product_create_input: Annotated[MedicinalProductCreateInput, Body()],
):
    medicinal_product_service = MedicinalProductService()
    return medicinal_product_service.create(
        concept_input=medicinal_product_create_input
    )


@router.patch(
    "/medicinal-products/{medicinal_product_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Update medicinal product",
    description="""
State before:
 - uid must exist and medicinal product must exist in status draft.
 - The medicinal product must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - If medicinal product exist in status draft then attributes are updated.
 - If links to CT are selected or updated then relationships are made to CTTermRoots.
- If the linked medicinal product is updated, the relationships are updated to point to the medicinal product value node.

State after:
 - attributes are updated for the medicinal product.
 - Audit trail entry must be made with update of attributes.

Possible errors:
 - Invalid uid.

""",
    response_model=MedicinalProduct,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The medicinal product is not in draft status.\n"
            "- The medicinal product had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The medicinal product with the specified 'medicinal_product_uid' wasn't found.",
        },
    },
)
def edit(
    medicinal_product_uid: Annotated[str, MedicinalProductUID],
    medicinal_product_edit_input: Annotated[MedicinalProductEditInput, Body()],
):
    medicinal_product_service = MedicinalProductService()
    return medicinal_product_service.edit_draft(
        uid=medicinal_product_uid, concept_edit_input=medicinal_product_edit_input
    )


@router.post(
    "/medicinal-products/{medicinal_product_uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approve draft version of a medicinal product",
    description="""
State before:
 - uid must exist and medicinal product must be in status Draft.
 
Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically to 'Approved version'.
 
State after:
 - MedicinalProduct changed status to Final and assigned a new major version number.
 - Audit trail entry must be made with action of approving to new Final version.
 
Possible errors:
 - Invalid uid or status not Draft.
    """,
    response_model=MedicinalProduct,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The medicinal product is not in draft status.\n"
            "- The library doesn't allow medicinal product approval.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The medicinal product with the specified 'medicinal_product_uid' wasn't found.",
        },
    },
)
def approve(
    medicinal_product_uid: Annotated[str, MedicinalProductUID],
):
    medicinal_product_service = MedicinalProductService()
    return medicinal_product_service.approve(uid=medicinal_product_uid)


@router.post(
    "/medicinal-products/{medicinal_product_uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Create a new version of a medicinal product",
    description="""
State before:
 - uid must exist and the medicinal product must be in status Final.
 
Business logic:
- The medicinal product is changed to a draft state.

State after:
 - MedicinalProduct changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.
 
Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=MedicinalProduct,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't allow to create medicinal products.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The medicinal product is not in final status.\n"
            "- The medicinal product with the specified 'medicinal_product_uid' could not be found.",
        },
    },
)
def create_new_version(
    medicinal_product_uid: Annotated[str, MedicinalProductUID],
):
    medicinal_product_service = MedicinalProductService()
    return medicinal_product_service.create_new_version(uid=medicinal_product_uid)


@router.delete(
    "/medicinal-products/{medicinal_product_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of a medicinal product",
    description="""
State before:
 - uid must exist and medicinal product must be in status Final.
 
Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status will be automatically set to 'Retired'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.
 
State after:
 - MedicinalProduct changed status to Retired.
 - Audit trail entry must be made with action of inactivating to retired version.
 
Possible errors:
 - Invalid uid or status not Final.
    """,
    response_model=MedicinalProduct,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The medicinal product is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The medicinal product with the specified 'medicinal_product_uid' could not be found.",
        },
    },
)
def inactivate(
    medicinal_product_uid: Annotated[str, MedicinalProductUID],
):
    medicinal_product_service = MedicinalProductService()
    return medicinal_product_service.inactivate_final(uid=medicinal_product_uid)


@router.post(
    "/medicinal-products/{medicinal_product_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a medicinal product",
    description="""
State before:
 - uid must exist and medicinal product must be in status Retired.
 
Business logic:
 - The latest 'Retired' version will remain the same as before.
 - The status will be automatically set to 'Final'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - MedicinalProduct changed status to Final.
 - An audit trail entry must be made with action of reactivating to final version.
 
Possible errors:
 - Invalid uid or status not Retired.
    """,
    response_model=MedicinalProduct,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The medicinal product is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The medicinal product with the specified 'medicinal_product_uid' could not be found.",
        },
    },
)
def reactivate(
    medicinal_product_uid: Annotated[str, MedicinalProductUID],
):
    medicinal_product_service = MedicinalProductService()
    return medicinal_product_service.reactivate_retired(uid=medicinal_product_uid)


@router.delete(
    "/medicinal-products/{medicinal_product_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Delete draft version of a medicinal product",
    description="""
State before:
 - uid must exist
 - The concept must be in status Draft in a version less then 1.0 (never been approved).
 - The concept must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).
 
Business logic:
 - The draft concept is deleted.
 
State after:
 - MedicinalProduct is successfully deleted.
 
Possible errors:
 - Invalid uid or status not Draft or exist in version 1.0 or above (previously been approved) or not in an editable library.
    """,
    response_model=None,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The medicinal product was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The medicinal product is not in draft status.\n"
            "- The medicinal product was already in final state or is in use.\n"
            "- The library doesn't allow to delete medicinal product.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - A medicinal product with the specified 'medicinal_product_uid' could not be found.",
        },
    },
)
def delete(
    medicinal_product_uid: Annotated[str, MedicinalProductUID],
):
    medicinal_product_service = MedicinalProductService()
    medicinal_product_service.soft_delete(uid=medicinal_product_uid)
