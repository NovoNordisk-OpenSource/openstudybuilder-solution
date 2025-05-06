from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api.models.concepts.odms.odm_alias import (
    OdmAlias,
    OdmAliasBatchInput,
    OdmAliasBatchOutput,
    OdmAliasPatchInput,
    OdmAliasPostInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.concepts.odms.odm_aliases import OdmAliasService
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/concepts/odms/aliases"
router = APIRouter()

# Argument definitions
OdmAliasUID = Path(description="The unique id of the ODM Alias.")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Return a listing of ODM Aliases",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[OdmAlias],
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
            "library_name",
            "name",
            "context",
            "start_date",
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
def get_all_odm_aliases(
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
    odm_alias_service = OdmAliasService()
    results = odm_alias_service.get_all_concepts(
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
    odm_alias_service = OdmAliasService()
    return odm_alias_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/{odm_alias_uid}/relationships",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get UIDs of a specific ODM Alias' relationships",
    response_model=dict,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_active_relationships(odm_alias_uid: Annotated[str, OdmAliasUID]):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.get_active_relationships(uid=odm_alias_uid)


@router.get(
    "/{odm_alias_uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="Return a listing of versions of a specific ODM Alias",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Aliases.
 - The returned versions are ordered by start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=list[OdmAlias],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Alias with the specified 'odm_alias_uid' wasn't found.",
        },
    },
)
def get_odm_alias_versions(odm_alias_uid: Annotated[str, OdmAliasUID]):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.get_version_history(uid=odm_alias_uid)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Create a new ODM Alias",
    response_model=OdmAlias,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The ODM Alias was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
        409: _generic_descriptions.ERROR_409,
    },
)
def create_odm_alias(odm_alias_create_input: Annotated[OdmAliasPostInput, Body()]):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.create(concept_input=odm_alias_create_input)


@router.post(
    "/batch",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Batch operations (create, edit) for ODM Aliases",
    response_model=list[OdmAliasBatchOutput],
    status_code=207,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def odm_alias_batch_operations(
    operations: Annotated[
        list[OdmAliasBatchInput], Body(description="List of operation to perform")
    ]
):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.handle_batch_operations(operations)


@router.patch(
    "/{odm_alias_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Update an ODM Alias",
    response_model=OdmAlias,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Alias is not in draft status.\n"
            "- The ODM Alias had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Alias with the specified 'odm_alias_uid' wasn't found.",
        },
    },
)
def edit_odm_alias(
    odm_alias_uid: Annotated[str, OdmAliasUID],
    odm_alias_edit_input: Annotated[OdmAliasPatchInput, Body()],
):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.edit_draft(
        uid=odm_alias_uid, concept_edit_input=odm_alias_edit_input
    )


@router.post(
    "/{odm_alias_uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Create a new version of an ODM Alias",
    description="""
State before:
 - uid must exist and the ODM Alias must be in status Final.

Business logic:
- The ODM Alias is changed to a draft state.

State after:
 - ODM Alias changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=OdmAlias,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't allow to create ODM Aliases.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM Alias is not in final status.\n"
            "- The ODM Alias with the specified 'odm_alias_uid' could not be found.",
        },
    },
)
def create_odm_alias_version(odm_alias_uid: Annotated[str, OdmAliasUID]):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.create_new_version(uid=odm_alias_uid)


@router.post(
    "/{odm_alias_uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approve an ODM Alias",
    response_model=OdmAlias,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Alias is not in draft status.\n"
            "- The library doesn't allow to approve ODM Alias.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Alias with the specified 'odm_alias_uid' wasn't found.",
        },
    },
)
def approve_odm_alias(odm_alias_uid: Annotated[str, OdmAliasUID]):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.approve(uid=odm_alias_uid)


@router.delete(
    "/{odm_alias_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Inactivate an ODM Alias",
    response_model=OdmAlias,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Alias is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Alias with the specified 'odm_alias_uid' could not be found.",
        },
    },
)
def inactivate_odm_alias(odm_alias_uid: Annotated[str, OdmAliasUID]):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.inactivate_final(uid=odm_alias_uid)


@router.post(
    "/{odm_alias_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivate an ODM Alias",
    response_model=OdmAlias,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Alias is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Alias with the specified 'odm_alias_uid' could not be found.",
        },
    },
)
def reactivate_odm_alias(odm_alias_uid: Annotated[str, OdmAliasUID]):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.reactivate_retired(uid=odm_alias_uid)


@router.delete(
    "/{odm_alias_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Delete draft version of ODM Alias",
    response_model=None,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The ODM Alias was successfully deleted."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Alias is not in draft status.\n"
            "- The ODM Alias was already in final state or is in use.\n"
            "- The library doesn't allow to delete ODM Alias.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM Alias with the specified 'odm_alias_uid' could not be found.",
        },
    },
)
def delete_odm_alias(odm_alias_uid: Annotated[str, OdmAliasUID]):
    odm_alias_service = OdmAliasService()
    odm_alias_service.soft_delete(uid=odm_alias_uid)
