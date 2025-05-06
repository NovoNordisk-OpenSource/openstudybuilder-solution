from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json

from clinical_mdr_api.models.concepts.odms.odm_formal_expression import (
    OdmFormalExpression,
    OdmFormalExpressionPatchInput,
    OdmFormalExpressionPostInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.concepts.odms.odm_formal_expressions import (
    OdmFormalExpressionService,
)
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/concepts/odms/formal-expressions"
router = APIRouter()

# Argument definitions
OdmFormalExpressionUID = Path(description="The unique id of the ODM Formal Expression.")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Return every variable related to the selected status and version of the ODM Formal Expressions",
    response_model=CustomPage[OdmFormalExpression],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_odm_formal_expressions(
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
    odm_formal_expression_service = OdmFormalExpressionService()
    results = odm_formal_expression_service.get_all_concepts(
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
    "/headers",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
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
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/{odm_formal_expression_uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get details on a specific ODM Formal Expression (in a specific version)",
    response_model=OdmFormalExpression,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_odm_formal_expression(
    odm_formal_expression_uid: Annotated[str, OdmFormalExpressionUID]
):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.get_by_uid(uid=odm_formal_expression_uid)


@router.get(
    "/{odm_formal_expression_uid}/relationships",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get UIDs of a specific ODM Formal Expression's relationships",
    response_model=dict,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_active_relationships(
    odm_formal_expression_uid: Annotated[str, OdmFormalExpressionUID]
):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.get_active_relationships(
        uid=odm_formal_expression_uid
    )


@router.get(
    "/{odm_formal_expression_uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List version history for ODM Formal Expression",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Formal Expressions.
 - The returned versions are ordered by start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=list[OdmFormalExpression],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Formal Expression with the specified 'odm_formal_expression_uid' wasn't found.",
        },
    },
)
def get_odm_formal_expression_versions(
    odm_formal_expression_uid: Annotated[str, OdmFormalExpressionUID],
):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.get_version_history(
        uid=odm_formal_expression_uid
    )


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new Form in 'Draft' status with version 0.1",
    response_model=OdmFormalExpression,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The ODM Formal Expression was successfully created."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
        409: _generic_descriptions.ERROR_409,
    },
)
def create_odm_formal_expression(
    odm_formal_expression_create_input: Annotated[OdmFormalExpressionPostInput, Body()],
):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.create(
        concept_input=odm_formal_expression_create_input
    )


@router.patch(
    "/{odm_formal_expression_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Update ODM Formal Expression",
    response_model=OdmFormalExpression,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Formal Expression is not in draft status.\n"
            "- The ODM Formal Expression had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Formal Expression with the specified 'odm_formal_expression_uid' wasn't found.",
        },
    },
)
def edit_odm_formal_expression(
    odm_formal_expression_uid: Annotated[str, OdmFormalExpressionUID],
    odm_formal_expression_edit_input: Annotated[OdmFormalExpressionPatchInput, Body()],
):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.edit_draft(
        uid=odm_formal_expression_uid,
        concept_edit_input=odm_formal_expression_edit_input,
    )


@router.post(
    "/{odm_formal_expression_uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Create a new version of ODM Formal Expression",
    description="""
State before:
 - uid must exist and the ODM Formal Expression must be in status Final.

Business logic:
- The ODM Formal Expression is changed to a draft state.

State after:
 - ODM Formal Expression changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=OdmFormalExpression,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't allow to create ODM Formal Expressions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM Formal Expression is not in final status.\n"
            "- The ODM Formal Expression with the specified 'odm_formal_expression_uid' could not be found.",
        },
    },
)
def create_odm_formal_expression_version(
    odm_formal_expression_uid: Annotated[str, OdmFormalExpressionUID],
):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.create_new_version(
        uid=odm_formal_expression_uid
    )


@router.post(
    "/{odm_formal_expression_uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approve draft version of ODM Formal Expression",
    response_model=OdmFormalExpression,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Formal Expression is not in draft status.\n"
            "- The library doesn't allow to approve ODM Formal Expression.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Formal Expression with the specified 'odm_formal_expression_uid' wasn't found.",
        },
    },
)
def approve_odm_formal_expression(
    odm_formal_expression_uid: Annotated[str, OdmFormalExpressionUID],
):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.approve(uid=odm_formal_expression_uid)


@router.delete(
    "/{odm_formal_expression_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of ODM Formal Expression",
    response_model=OdmFormalExpression,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Formal Expression is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Formal Expression with the specified 'odm_formal_expression_uid' could not be found.",
        },
    },
)
def inactivate_odm_formal_expression(
    odm_formal_expression_uid: Annotated[str, OdmFormalExpressionUID],
):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.inactivate_final(uid=odm_formal_expression_uid)


@router.post(
    "/{odm_formal_expression_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a ODM Formal Expression",
    response_model=OdmFormalExpression,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Formal Expression is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Formal Expression with the specified 'odm_formal_expression_uid' could not be found.",
        },
    },
)
def reactivate_odm_formal_expression(
    odm_formal_expression_uid: Annotated[str, OdmFormalExpressionUID],
):
    odm_formal_expression_service = OdmFormalExpressionService()
    return odm_formal_expression_service.reactivate_retired(
        uid=odm_formal_expression_uid
    )


@router.delete(
    "/{odm_formal_expression_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Delete draft version of ODM Formal Expression",
    response_model=None,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The ODM Formal Expression was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Formal Expression is not in draft status.\n"
            "- The ODM Formal Expression was already in final state or is in use.\n"
            "- The library doesn't allow to delete ODM Formal Expression.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM Formal Expression with the specified 'odm_formal_expression_uid' could not be found.",
        },
    },
)
def delete_odm_formal_expression(
    odm_formal_expression_uid: Annotated[str, OdmFormalExpressionUID],
):
    odm_formal_expression_service = OdmFormalExpressionService()
    odm_formal_expression_service.soft_delete(uid=odm_formal_expression_uid)
