"""CTTermAttributes router."""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query, Response
from fastapi import status as fast_api_status
from pydantic.types import Json

from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.controlled_terminologies.ct_term_attributes import (
    CTTermAttributes,
    CTTermAttributesEditInput,
    CTTermAttributesVersion,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesService,
)
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/ct"
router = APIRouter()

CTTermUID = Path(description="The unique id of the CTTermAttributes")


@router.get(
    "/terms/attributes",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all terms attributes.",
    response_model=CustomPage[CTTermAttributes],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_terms(
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
    in_codelist: Annotated[
        bool,
        Query(
            description="If false, all terms are returned even those not connected to a codelist. "
            "If true, only terms connected to at least one codelist are returned.",
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
    ct_term_attribute_service = CTTermAttributesService()
    results = ct_term_attribute_service.get_all_ct_terms(
        codelist_uid=codelist_uid,
        codelist_name=codelist_name,
        library=library_name,
        package=package,
        in_codelist=in_codelist,
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
    "/terms/attributes/headers",
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
    ct_term_service = CTTermAttributesService()
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


@router.get(
    "/terms/{term_uid}/attributes",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the latest/newest version of a specific ct term identified by 'term_uid'",
    response_model=CTTermAttributes,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_term_attributes(
    term_uid: Annotated[str, CTTermUID],
    at_specified_date_time: Annotated[
        datetime | None,
        Query(
            description="If specified then the latest/newest representation of the "
            "CTTermAttributesValue at this point in time is returned.\n"
            "The point in time needs to be specified in ISO 8601 format including the timezone, "
            "e.g.: '2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. "
            "If the timezone is omitted, UTC±0 is assumed.",
        ),
    ] = None,
    status: Annotated[
        LibraryItemStatus | None,
        Query(
            description="If specified then the representation of the CTTermAttributesValue "
            "in that status is returned (if existent).\n_this is useful if the"
            " CTTermAttributesValue has a status 'Draft' and a status 'Final'.",
        ),
    ] = None,
    version: Annotated[
        str | None,
        Query(
            description="If specified then the latest/newest representation of the "
            "for CTTermAttributesValue in that version is returned.\n"
            "Only exact matches are considered. The version is specified in the following format:"
            "<major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0',",
        ),
    ] = None,
):
    ct_term_attribute_service = CTTermAttributesService()
    return ct_term_attribute_service.get_by_uid(
        term_uid=term_uid,
        at_specific_date=at_specified_date_time,
        status=status,
        version=version,
    )


@router.get(
    "/terms/{term_uid}/attributes/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the version history of a specific CTTermAttributes identified by 'term_uid'.",
    description="The returned versions are ordered by\n"
    "0. start_date descending (newest entries first)",
    response_model=list[CTTermAttributesVersion],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The codelist with the specified 'codelist_uid' wasn't found.",
        },
    },
)
def get_versions(term_uid: Annotated[str, CTTermUID]):
    ct_term_attribute_service = CTTermAttributesService()
    return ct_term_attribute_service.get_version_history(term_uid=term_uid)


@router.patch(
    "/terms/{term_uid}/attributes",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Updates the term identified by 'term_uid'.",
    description="""This request is only valid if the term
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.
""",
    response_model=CTTermAttributes,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term is not in draft status.\n"
            "- The term had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'term_uid' wasn't found.",
        },
    },
)
def edit(
    term_uid: Annotated[str, CTTermUID],
    term_input: Annotated[
        CTTermAttributesEditInput,
        Body(
            description="The new parameter terms for the term including the change description.",
        ),
    ],
):
    ct_term_attribute_service = CTTermAttributesService()
    return ct_term_attribute_service.edit_draft(
        term_uid=term_uid, term_input=term_input
    )


@router.post(
    "/terms/{term_uid}/attributes/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new term in 'Draft' status.",
    description="""This request is only valid if
* the specified term is in 'Final' status and
* the specified library allows creating term (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'change_description' property will be set automatically to 'new-version'.
* The 'version' property will be increased by '0.1'.
""",
    response_model=CTTermAttributes,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The term was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't allow to create tterm.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The term is not in final status.\n"
            "- The term with the specified 'codelist_uid' could not be found.",
        },
    },
)
def create(term_uid: Annotated[str, CTTermUID]):
    ct_term_attribute_service = CTTermAttributesService()
    return ct_term_attribute_service.create_new_version(term_uid=term_uid)


@router.post(
    "/terms/{term_uid}/attributes/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approves the term identified by 'term_uid'.",
    description="""This request is only valid if the term
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically to 'Approved version'.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=CTTermAttributes,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term is not in draft status.\n"
            "- The library doesn't allow to approve term.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'term_uid' wasn't found.",
        },
    },
)
def approve(term_uid: Annotated[str, CTTermUID]):
    ct_term_attribute_service = CTTermAttributesService()
    return ct_term_attribute_service.approve(term_uid=term_uid)


@router.delete(
    "/terms/{term_uid}/attributes/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Inactivates/deactivates the term identified by 'term_uid'.",
    description="""This request is only valid if the term
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=CTTermAttributes,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'term_uid' could not be found.",
        },
    },
)
def inactivate(term_uid: Annotated[str, CTTermUID]):
    ct_term_attribute_service = CTTermAttributesService()
    return ct_term_attribute_service.inactivate_final(term_uid=term_uid)


@router.post(
    "/terms/{term_uid}/attributes/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivates the term identified by 'term_uid'.",
    description="""This request is only valid if the term
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=CTTermAttributes,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'term_uid' could not be found.",
        },
    },
)
def reactivate(term_uid: Annotated[str, CTTermUID]):
    ct_term_attribute_service = CTTermAttributesService()
    return ct_term_attribute_service.reactivate_retired(term_uid=term_uid)


@router.delete(
    "/terms/{term_uid}/attributes",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Deletes the term identified by 'term_uid'.",
    description="""This request is only valid if \n
* the term is in 'Draft' status and
* the term has never been in 'Final' status and
* the term belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The term was successfully deleted."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term is not in draft status.\n"
            "- The term was already in final state or is in use.\n"
            "- The library doesn't allow to delete term.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An term with the specified 'term_uid' could not be found.",
        },
    },
)
def delete_ct_term(term_uid: Annotated[str, CTTermUID]):
    ct_term_attribute_service = CTTermAttributesService()
    ct_term_attribute_service.soft_delete(term_uid=term_uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)
