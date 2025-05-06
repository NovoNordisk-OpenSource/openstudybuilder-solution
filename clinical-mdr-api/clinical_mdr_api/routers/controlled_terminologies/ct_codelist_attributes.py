"""CTCodelistAttributes router."""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json

from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributes,
    CTCodelistAttributesEditInput,
    CTCodelistAttributesVersion,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesService,
)
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/ct"
router = APIRouter()

CTCodelistUID = Path(description="The unique id of the CTCodelistAttributes")


@router.get(
    "/codelists/attributes",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all codelists attributes.",
    response_model=CustomPage[CTCodelistAttributes],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_codelists(
    catalogue_name: Annotated[
        str,
        Query(
            description="If specified, only codelists from given catalogue are returned.",
        ),
    ] = None,
    library_name: Annotated[
        str | None,
        Query(
            description="If specified, only codelists from given library are returned.",
        ),
    ] = None,
    package: Annotated[
        str | None,
        Query(
            description="If specified, only codelists from given package are returned.",
        ),
    ] = None,
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
    ct_codelist_attribute_service = CTCodelistAttributesService()
    results = ct_codelist_attribute_service.get_all_ct_codelists(
        catalogue_name=catalogue_name,
        library=library_name,
        package=package,
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
    "/codelists/attributes/headers",
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
    catalogue_name: Annotated[
        str,
        Query(
            description="If specified, only codelists from given catalogue are returned.",
        ),
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
    ct_codelist_attribute_service = CTCodelistAttributesService()
    return ct_codelist_attribute_service.get_distinct_values_for_header(
        catalogue_name=catalogue_name,
        library=library_name,
        package=package,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/codelists/{codelist_uid}/attributes",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the latest/newest version of a specific codelist identified by 'codelist_uid'",
    response_model=CTCodelistAttributes,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_codelist_attributes(
    codelist_uid: Annotated[str, CTCodelistUID],
    at_specified_date_time: Annotated[
        datetime | None,
        Query(
            description="If specified then the latest/newest representation of the sponsor defined name "
            "for CTCodelistAttributesValue at this point in time is returned.\n"
            "The point in time needs to be specified in ISO 8601 format including the timezone, "
            "e.g.: '2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. "
            "If the timezone is omitted, UTC±0 is assumed.",
        ),
    ] = None,
    status: Annotated[
        LibraryItemStatus | None,
        Query(
            description="If specified then the representation of the sponsor defined name for "
            "CTCodelistAttributesValue in that status is returned (if existent).\n_this is useful if the"
            " CTCodelistAttributesValue has a status 'Draft' and a status 'Final'.",
        ),
    ] = None,
    version: Annotated[
        str | None,
        Query(
            description="If specified then the latest/newest representation of the sponsor defined name "
            "for CTCodelistAttributesValue in that version is returned.\n"
            "Only exact matches are considered. The version is specified in the following format:"
            "<major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0',",
        ),
    ] = None,
):
    ct_codelist_attribute_service = CTCodelistAttributesService()
    return ct_codelist_attribute_service.get_by_uid(
        codelist_uid=codelist_uid,
        at_specific_date=at_specified_date_time,
        status=status,
        version=version,
    )


@router.get(
    "/codelists/{codelist_uid}/attributes/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the version history of a specific CTCodelistAttributes identified by 'codelist_uid'.",
    description="The returned versions are ordered by\n"
    "0. start_date descending (newest entries first)",
    response_model=list[CTCodelistAttributesVersion],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The codelist with the specified 'codelist_uid' wasn't found.",
        },
    },
)
def get_versions(
    codelist_uid: Annotated[str, CTCodelistUID],
):
    ct_codelist_attribute_service = CTCodelistAttributesService()
    return ct_codelist_attribute_service.get_version_history(codelist_uid=codelist_uid)


@router.patch(
    "/codelists/{codelist_uid}/attributes",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Updates the codelist identified by 'codelist_uid'.",
    description="""This request is only valid if the codelist
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.
""",
    response_model=CTCodelistAttributes,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The codelist is not in draft status.\n"
            "- The codelist had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The codelist with the specified 'codelist_uid' wasn't found.",
        },
    },
)
def edit(
    codelist_uid: Annotated[str, CTCodelistUID],
    codelist_input: Annotated[
        CTCodelistAttributesEditInput,
        Body(
            description="The new parameter terms for the codelist including the change description.",
        ),
    ],
):
    ct_codelist_attribute_service = CTCodelistAttributesService()
    return ct_codelist_attribute_service.edit_draft(
        codelist_uid=codelist_uid, codelist_input=codelist_input
    )


@router.post(
    "/codelists/{codelist_uid}/attributes/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new codelist in 'Draft' status.",
    description="""This request is only valid if
* the specified codelist is in 'Final' status and
* the specified library allows creating codelists (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'change_description' property will be set automatically to 'new-version'.
* The 'version' property will be increased by '0.1'.
""",
    response_model=CTCodelistAttributes,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The codelist was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't allow to create codelists.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The codelist is not in final status.\n"
            "- The codelist with the specified 'codelist_uid' could not be found.",
        },
    },
)
def create(
    codelist_uid: Annotated[str, CTCodelistUID],
):
    ct_codelist_attribute_service = CTCodelistAttributesService()
    return ct_codelist_attribute_service.create_new_version(codelist_uid=codelist_uid)


@router.post(
    "/codelists/{codelist_uid}/attributes/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approves the codelist identified by 'codelist_uid'.",
    description="""This request is only valid if the codelist
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically to 'Approved version'.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=CTCodelistAttributes,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The codelist is not in draft status.\n"
            "- The library doesn't allow to approve codelist.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The codelist with the specified 'codelist_uid' wasn't found.",
        },
    },
)
def approve(
    codelist_uid: Annotated[str, CTCodelistUID],
):
    ct_codelist_attribute_service = CTCodelistAttributesService()
    return ct_codelist_attribute_service.approve(codelist_uid=codelist_uid)
