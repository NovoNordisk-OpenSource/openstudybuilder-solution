"""CTTerms router."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    CTTerm,
    CTTermCreateInput,
    CTTermNameAndAttributes,
    CTTermNewOrder,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.controlled_terminologies.ct_term import CTTermService
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/ct"
router = APIRouter()

CTTermUID = Path(description="The unique id of the ct term.")


@router.post(
    "/terms",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates new ct term.",
    description="""The following nodes are created
* CTTermRoot
  * CTTermAttributesRoot
  * CTTermAttributesValue
  * CTTermNameRoot
  * CTTermNameValue
""",
    response_model=CTTerm,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The term was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The catalogue doesn't exist.\n"
            "- The library doesn't exist..\n"
            "- The library doesn't allow to add new items.\n",
        },
    },
)
def create(
    term_input: Annotated[
        CTTermCreateInput,
        Body(description="Properties to create CTTermAttributes and CTTermName."),
    ],
):
    ct_term_service = CTTermService()
    return ct_term_service.create(term_input)


@router.get(
    "/terms",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all terms names and attributes.",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[CTTermNameAndAttributes],
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
    codelist_uid: Annotated[
        str | None,
        Query(description="If specified, only terms from given codelist are returned."),
    ] = None,
    codelist_name: Annotated[
        str | None,
        Query(description="If specified, only terms from given codelist are returned."),
    ] = None,
    library_name: Annotated[
        str | None,
        Query(description="If specified, only terms from given library are returned."),
    ] = None,
    package: Annotated[
        str | None,
        Query(description="If specified, only terms from given package are returned."),
    ] = None,
    is_sponsor: Annotated[
        bool | None,
        Query(
            description="Boolean value to indicate desired package is a sponsor package. Defaults to False.",
        ),
    ] = False,
    include_removed_terms: Annotated[
        bool,
        Query(
            description="Boolean value to indicate whether or not to include terms removed from codelists. Defaults to False."
        ),
    ] = False,
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
    ct_term_service = CTTermService()
    results = ct_term_service.get_all_terms(
        codelist_uid=codelist_uid,
        codelist_name=codelist_name,
        library=library_name,
        package=package,
        is_sponsor=is_sponsor,
        include_removed_terms=include_removed_terms,
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
    "/terms/headers",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns possibles values from the database for a given header",
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
    codelist_uid: Annotated[
        str | None,
        Query(description="If specified, only terms from given codelist are returned."),
    ] = None,
    codelist_name: Annotated[
        str | None,
        Query(description="If specified, only terms from given codelist are returned."),
    ] = None,
    library_name: Annotated[
        str | None,
        Query(description="If specified, only terms from given library are returned."),
    ] = None,
    package: Annotated[
        str | None,
        Query(description="If specified, only terms from given package are returned."),
    ] = None,
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
    ct_term_service = CTTermService()
    return ct_term_service.get_distinct_values_for_header(
        codelist_uid=codelist_uid,
        codelist_name=codelist_name,
        library=library_name,
        package=package,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.post(
    "/terms/{term_uid}/parents",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds a CT Term Root node as a parent to the selected term node.",
    response_model=CTTerm,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The term was successfully added as a parent to the term identified by term-uid."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term already has a defined parent of the same type.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'term-uid' wasn't found.",
        },
    },
)
def add_parent(
    term_uid: Annotated[str, CTTermUID],
    parent_uid: Annotated[str, Query(description="The unique id for the parent node.")],
    relationship_type: Annotated[
        str,
        Query(
            description="The type of the parent relationship.\n"
            "Valid types are 'type' or 'subtype'",
        ),
    ],
):
    ct_term_service = CTTermService()
    return ct_term_service.add_parent(
        term_uid=term_uid, parent_uid=parent_uid, relationship_type=relationship_type
    )


@router.delete(
    "/terms/{term_uid}/parents",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Removes a parent term from the selected term node",
    response_model=CTTerm,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The term was successfully removed as a parent to the term identified by term-uid."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term already has no defined parent with given parent-uid and relationship type.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'term-uid' wasn't found.",
        },
    },
)
def remove_parent(
    term_uid: Annotated[str, CTTermUID],
    parent_uid: Annotated[str, Query(description="The unique id for the parent node.")],
    relationship_type: Annotated[
        str,
        Query(
            description="The type of the parent relationship.\n"
            "Valid types are 'type' or 'subtype'",
        ),
    ],
):
    ct_term_service = CTTermService()
    return ct_term_service.remove_parent(
        term_uid=term_uid, parent_uid=parent_uid, relationship_type=relationship_type
    )


@router.patch(
    "/terms/{term_uid}/order",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Change an order of codelist-term relationship",
    description="""Reordering will create new HAS_TERM relationship.""",
    response_model=CTTerm,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Order is larger than the number of selections",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - When there exist no study endpoint with the study endpoint uid.",
        },
    },
)
def patch_new_term_order(
    term_uid: Annotated[str, CTTermUID],
    new_order_input: Annotated[
        CTTermNewOrder, Body(description="Parameters needed for the reorder action.")
    ],
) -> CTTerm:
    ct_term_service = CTTermService()
    return ct_term_service.set_new_order(
        term_uid=term_uid,
        codelist_uid=new_order_input.codelist_uid,
        new_order=new_order_input.new_order,
    )
