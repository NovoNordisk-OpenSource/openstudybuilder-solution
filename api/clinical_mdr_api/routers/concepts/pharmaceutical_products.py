"""pharmaceutical_products router"""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from starlette.requests import Request

from clinical_mdr_api.models.concepts.pharmaceutical_product import (
    PharmaceuticalProduct,
    PharmaceuticalProductCreateInput,
    PharmaceuticalProductEditInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.concepts.pharmaceutical_products_service import (
    PharmaceuticalProductService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/concepts"
router = APIRouter()

PharmaceuticalProductUID = Path(
    description="The unique id of the pharmaceutical product"
)


@router.get(
    "/pharmaceutical-products",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all pharmaceutical products (for a given library)",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List all pharmaceutical products in their latest version, including properties derived from linked control terminology.

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
            "derived_name",
            "external_id",
            "dosage_forms=dosage_forms.term_name",
            "routes_of_administration=routes_of_administration.term_name",
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
def get_pharmaceutical_products(
    request: Request,  # request is actually required by the allow_exports decorator
    library_name: Annotated[str | None, Query()] = None,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[PharmaceuticalProduct]:
    pharmaceutical_product_service = PharmaceuticalProductService()
    results = pharmaceutical_product_service.get_all_concepts(
        library=library_name,
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
    "/pharmaceutical-products/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all versions of pharmaceutical products",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List version history of pharmaceutical products
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
            "external_id",
            "dosage_forms=dosage_forms.name",
            "routes_of_administration=routes_of_administration.name",
            "formulations",
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
def get_pharmaceutical_products_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    library_name: Annotated[str | None, Query()] = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[PharmaceuticalProduct]:
    service = PharmaceuticalProductService()
    results = service.get_all_concept_versions(
        library=library_name,
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
    "/pharmaceutical-products/headers",
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
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/pharmaceutical-products/{pharmaceutical_product_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific pharmaceutical product (in a specific version)",
    description="""
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
    pharmaceutical_product_uid: Annotated[str, PharmaceuticalProductUID],
) -> PharmaceuticalProduct:
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.get_by_uid(uid=pharmaceutical_product_uid)


@router.get(
    "/pharmaceutical-products/{pharmaceutical_product_uid}/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List version history for pharmaceutical products",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for pharmaceutical products.
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
            "description": "Not Found - The pharmaceutical product with the specified 'pharmaceutical_product_uid' wasn't found.",
        },
    },
)
def get_versions(
    pharmaceutical_product_uid: Annotated[str, PharmaceuticalProductUID],
) -> list[PharmaceuticalProduct]:
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.get_version_history(
        uid=pharmaceutical_product_uid
    )


@router.post(
    "/pharmaceutical-products",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates new pharmaceutical product.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).
 - The specified CT term uids must exist, and the term names are in a final state.

Business logic:
 - New node is created for the pharmaceutical product with the set properties.
 - relationships to specified control terminology are created (as in the model).
 - relationships to specified activity parent are created (as in the model)
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'change_description' property will be set automatically to 'Initial version'.

State after:
 - pharmaceutical product is created in status Draft and assigned an initial minor version number as 0.1.
 - Audit trail entry must be made with action of creating new Draft version.

Possible errors:
 - Invalid library or control terminology uid's specified.
""",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The pharmaceutical product was successfully created."
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
    pharmaceutical_product_create_input: Annotated[
        PharmaceuticalProductCreateInput, Body()
    ],
) -> PharmaceuticalProduct:
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.create(
        concept_input=pharmaceutical_product_create_input
    )


@router.patch(
    "/pharmaceutical-products/{pharmaceutical_product_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Update pharmaceutical product",
    description="""
State before:
 - uid must exist and pharmaceutical product must exist in status draft.
 - The pharmaceutical product must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - If pharmaceutical product exist in status draft then attributes are updated.
 - If links to CT are selected or updated then relationships are made to CTTermRoots.
- If the linked pharmaceutical product is updated, the relationships are updated to point to the pharmaceutical product value node.

State after:
 - attributes are updated for the pharmaceutical product.
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
            "- The pharmaceutical product is not in draft status.\n"
            "- The pharmaceutical product had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The pharmaceutical product with the specified 'pharmaceutical_product_uid' wasn't found.",
        },
    },
)
def edit(
    pharmaceutical_product_uid: Annotated[str, PharmaceuticalProductUID],
    pharmaceutical_product_edit_input: Annotated[
        PharmaceuticalProductEditInput, Body()
    ],
) -> PharmaceuticalProduct:
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.edit_draft(
        uid=pharmaceutical_product_uid,
        concept_edit_input=pharmaceutical_product_edit_input,
    )


@router.post(
    "/pharmaceutical-products/{pharmaceutical_product_uid}/approvals",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Approve draft version of a pharmaceutical product",
    description="""
State before:
 - uid must exist and pharmaceutical product must be in status Draft.
 
Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically to 'Approved version'.
 
State after:
 - PharmaceuticalProduct changed status to Final and assigned a new major version number.
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
            "- The pharmaceutical product is not in draft status.\n"
            "- The library doesn't allow pharmaceutical product approval.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The pharmaceutical product with the specified 'pharmaceutical_product_uid' wasn't found.",
        },
    },
)
def approve(
    pharmaceutical_product_uid: Annotated[str, PharmaceuticalProductUID],
) -> PharmaceuticalProduct:
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.approve(uid=pharmaceutical_product_uid)


@router.post(
    "/pharmaceutical-products/{pharmaceutical_product_uid}/versions",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Create a new version of a pharmaceutical product",
    description="""
State before:
 - uid must exist and the pharmaceutical product must be in status Final.
 
Business logic:
- The pharmaceutical product is changed to a draft state.

State after:
 - PharmaceuticalProduct changed status to Draft and assigned a new minor version number.
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
            "- The library doesn't allow to create pharmaceutical products.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The pharmaceutical product is not in final status.\n"
            "- The pharmaceutical product with the specified 'pharmaceutical_product_uid' could not be found.",
        },
    },
)
def create_new_version(
    pharmaceutical_product_uid: Annotated[str, PharmaceuticalProductUID],
) -> PharmaceuticalProduct:
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.create_new_version(
        uid=pharmaceutical_product_uid
    )


@router.delete(
    "/pharmaceutical-products/{pharmaceutical_product_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of a pharmaceutical product",
    description="""
State before:
 - uid must exist and pharmaceutical product must be in status Final.
 
Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status will be automatically set to 'Retired'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.
 
State after:
 - PharmaceuticalProduct changed status to Retired.
 - Audit trail entry must be made with action of inactivating to retired version.
 
Possible errors:
 - Invalid uid or status not Final.
    """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The pharmaceutical product is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The pharmaceutical product with the specified 'pharmaceutical_product_uid' could not be found.",
        },
    },
)
def inactivate(
    pharmaceutical_product_uid: Annotated[str, PharmaceuticalProductUID],
) -> PharmaceuticalProduct:
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.inactivate_final(
        uid=pharmaceutical_product_uid
    )


@router.post(
    "/pharmaceutical-products/{pharmaceutical_product_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a pharmaceutical product",
    description="""
State before:
 - uid must exist and pharmaceutical product must be in status Retired.
 
Business logic:
 - The latest 'Retired' version will remain the same as before.
 - The status will be automatically set to 'Final'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - PharmaceuticalProduct changed status to Final.
 - An audit trail entry must be made with action of reactivating to final version.
 
Possible errors:
 - Invalid uid or status not Retired.
    """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The pharmaceutical product is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The pharmaceutical product with the specified 'pharmaceutical_product_uid' could not be found.",
        },
    },
)
def reactivate(
    pharmaceutical_product_uid: Annotated[str, PharmaceuticalProductUID],
) -> PharmaceuticalProduct:
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.reactivate_retired(
        uid=pharmaceutical_product_uid
    )


@router.delete(
    "/pharmaceutical-products/{pharmaceutical_product_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Delete draft version of a pharmaceutical product",
    description="""
State before:
 - uid must exist
 - The concept must be in status Draft in a version less then 1.0 (never been approved).
 - The concept must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).
 
Business logic:
 - The draft concept is deleted.
 
State after:
 - PharmaceuticalProduct is successfully deleted.
 
Possible errors:
 - Invalid uid or status not Draft or exist in version 1.0 or above (previously been approved) or not in an editable library.
    """,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The pharmaceutical product was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The pharmaceutical product is not in draft status.\n"
            "- The pharmaceutical product was already in final state or is in use.\n"
            "- The library doesn't allow to delete pharmaceutical product.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - A pharmaceutical product with the specified 'pharmaceutical_product_uid' could not be found.",
        },
    },
)
def delete(
    pharmaceutical_product_uid: Annotated[str, PharmaceuticalProductUID],
):
    pharmaceutical_product_service = PharmaceuticalProductService()
    pharmaceutical_product_service.soft_delete(uid=pharmaceutical_product_uid)


@router.post(
    "/pharmaceutical-products/{pharmaceutical_product_uid}/archive",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=f"Move pharmaceutical product to {settings.archived_library_name} library",
    description="Moves an existing pharmaceutical product to the target library if not yet in it. Returns new state of PharmaceuticalProduct.",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: _generic_descriptions.ERROR_400,
        404: _generic_descriptions.ERROR_404,
    },
)
def archive(
    pharmaceutical_product_uid: Annotated[str, PharmaceuticalProductUID],
) -> PharmaceuticalProduct:
    pharmaceutical_product_service = PharmaceuticalProductService()
    return pharmaceutical_product_service.archive(uid=pharmaceutical_product_uid)
