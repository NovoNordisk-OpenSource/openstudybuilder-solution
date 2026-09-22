"""CTCodelist router."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api.models.controlled_terminologies.ct_codelist import (
    CTCodelist,
    CTCodelistCompact,
    CTCodelistCreateInput,
    CTCodelistNameAndAttributes,
    CTCodelistPaired,
    CTCodelistPairedInput,
    CTCodelistTerm,
    CTCodelistTermInput,
    CTPairedCodelistCreateInput,
    CTPairedCodelistTerm,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.controlled_terminologies.ct_codelist import (
    CTCodelistService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/ct"
router = APIRouter()

CTCodelistUID = Path(description="The unique id of the CTCodelistRoot")
TermUID = Path(description="The unique id of the Codelist Term")


@router.post(
    "/codelists",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates new codelist.",
    description="""The following nodes are created
* CTCodelistRoot
  * CTCodelistAttributesRoot
  * CTCodelistAttributesValue
  * CTCodelistNameRoot
  * CTCodelistNameValue
""",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The codelist was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The catalogue doesn't exist.\n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
    },
)
def create(
    codelist_input: Annotated[
        CTCodelistCreateInput,
        Body(
            description="Properties to create CTCodelistAttributes and CTCodelistName.",
        ),
    ],
) -> CTCodelist:
    ct_codelist_service = CTCodelistService()
    return ct_codelist_service.create(codelist_input)


@router.get(
    "/codelists",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns all codelists names and attributes.",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
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
            "library_name",
            "concept_id=codelist_uid",
            "sponsor_preferred_name=name.name",
            "template_parameter=name.template_parameter",
            "cd_status=name.status",
            "modified_name=name.start_date",
            "cd_name=attributes.name",
            "submission_value=attributes.submission_value",
            "nci_preferred_name=attributes.nci_preferred_name",
            "extensible=attributes.extensible",
            "attributes_status=attributes.status",
            "modified_attributes=attributes.start_date",
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
def get_codelists(
    request: Request,  # request is actually required by the allow_exports decorator
    catalogue_name: Annotated[
        str | None,
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
    is_sponsor: Annotated[
        bool,
        Query(
            description="Boolean value to indicate desired package is a sponsor package. Defaults to False.",
        ),
    ] = False,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    term_filter: Annotated[
        Json | None,
        Query(
            description="""JSON dictionary consisting of `term_uids` key and `operator` key. Default: `{}` (no term filtering).

`term_uids` Specifies a list of of CT Term UIDs to filter on. Only Codelists with terms with provided UIDs will be returned.

`operator` specifies which logical operation - `and` or `or` - should be used in case multiple CT Term UIDs are provided. Default: `and`""",
            openapi_examples={
                "none": {
                    "value": None,
                    "summary": "No term filtering",
                },
                "basic": {
                    "value": """{"term_uids": ["C12345"], "operator": "and"}""",
                    "summary": "Filter by the provided CT Term UIDs",
                },
            },
        ),
    ] = None,
) -> CustomPage[CTCodelistNameAndAttributes]:
    ct_codelist_service = CTCodelistService()
    results = ct_codelist_service.get_all_codelists(
        catalogue_name=catalogue_name,
        library=library_name,
        package=package,
        is_sponsor=is_sponsor,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        term_filter=term_filter,
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/codelists/full-text-search",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Searches codelists using full-text search on submission value.",
    description="Returns a compact list of codelists matching the search string, "
    "with optional filtering for response codelists and ordinal codelists.",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def search_codelists_fulltext(
    search_string: Annotated[
        str,
        Query(
            description="The search string to use for full-text search on submission value.",
            min_length=1,
        ),
    ],
    only_response_codelists: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="If True, only return codelists that are valid for items (response codelists).",
        ),
    ] = False,
    only_ordinal_codelists: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="If True, only return ordinal codelists.",
        ),
    ] = False,
    match_whole_words: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="If True, match whole words only in the search.",
        ),
    ] = False,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
) -> CustomPage[CTCodelistCompact]:
    ct_codelist_service = CTCodelistService()
    results = ct_codelist_service.search_codelists_fulltext(
        search_string=search_string,
        only_response_codelists=only_response_codelists,
        only_ordinal_codelists=only_ordinal_codelists,
        match_whole_words=match_whole_words,
        page_number=page_number,
        page_size=page_size,
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/codelists/full-text-search-by-term",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Searches codelists by term using full-text search.",
    description="Searches terms using full-text search and returns codelists containing those terms, "
    "with optional filtering for response codelists and ordinal codelists.",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def search_codelists_fulltext_by_term(
    search_string: Annotated[
        str,
        Query(
            description="The search string to use for full-text search on term name and attributes.",
            min_length=1,
        ),
    ],
    only_response_codelists: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="If True, only return codelists that are valid for items (response codelists).",
        ),
    ] = False,
    only_ordinal_codelists: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="If True, only return ordinal codelists.",
        ),
    ] = False,
    match_whole_words: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="If True, match whole words only in the search.",
        ),
    ] = False,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
) -> CustomPage[CTCodelistCompact]:
    ct_codelist_service = CTCodelistService()
    results = ct_codelist_service.search_codelists_fulltext_by_term(
        search_string=search_string,
        only_response_codelists=only_response_codelists,
        only_ordinal_codelists=only_ordinal_codelists,
        match_whole_words=match_whole_words,
        page_number=page_number,
        page_size=page_size,
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/codelists/{codelist_uid}/sub-codelists",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns all sub codelists names and attributes that only have the provided terms.",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_sub_codelists_that_have_given_terms(
    codelist_uid: Annotated[str, CTCodelistUID],
    term_uids: Annotated[
        list[str],
        Query(
            description="A list of term uids",
        ),
    ],
    library_name: Annotated[
        str | None,
        Query(
            description="If specified, only codelists from given library are returned.",
        ),
    ] = None,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[CTCodelistNameAndAttributes]:
    ct_codelist_service = CTCodelistService()
    results = ct_codelist_service.get_sub_codelists_that_have_given_terms(
        codelist_uid=codelist_uid,
        term_uids=term_uids,
        library=library_name,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/codelists/{codelist_uid}/paired",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns any codelist paired with the specified one.",
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
    },
)
def get_paired_codelists(
    codelist_uid: str = CTCodelistUID,
) -> CTCodelistPaired:
    ct_codelist_service = CTCodelistService()
    results = ct_codelist_service.get_paired_codelists(
        codelist_uid=codelist_uid,
    )
    return results


@router.patch(
    "/codelists/{codelist_uid}/paired",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Update any codelist paired with the specified one.",
    response_model=CTCodelistPaired,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
    },
)
def update_paired_codelist(
    codelist_uid: Annotated[str, CTCodelistUID],
    codelist_input: Annotated[
        CTCodelistPairedInput,
        Body(
            description="Properties to pair codelists",
        ),
    ],
) -> CTCodelistPaired:
    ct_codelist_service = CTCodelistService()
    results = ct_codelist_service.update_paired_codelists(
        codelist_uid=codelist_uid,
        paired_codelists=codelist_input,
    )
    return results


@router.post(
    "/paired-codelists",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates a new set of paired codelists.",
    description="""Creates two codelists (one for names, one for codes) and links them as paired codelists.
Each codelist gets its own name, submission_value, nci_preferred_name, definition, and sponsor_preferred_name
via the name_information and code_information fields respectively.
""",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The paired codelists were successfully created."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The catalogue doesn't exist.\n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
    },
)
def create_paired_codelists(
    paired_codelist_input: Annotated[
        CTPairedCodelistCreateInput,
        Body(
            description="Properties to create a set of paired codelists (names and codes).",
        ),
    ],
) -> CTCodelistPaired:
    ct_codelist_service = CTCodelistService()
    return ct_codelist_service.create_paired_codelists(paired_codelist_input)


@router.get(
    "/paired-codelists/{codelist_uid}/terms",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns terms from the paired codelists identified by the given codelist UID.",
    description="Returns the list of all terms coming from the codelist specified by the given UID and its paired codelist. "
    "Each term includes both the code_submission_value (from the codes codelist) and "
    "the name_submission_value (from the names codelist).",
    response_model=CustomPage[CTPairedCodelistTerm],
    status_code=200,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Bad Request - The codelist does not have a paired codelist.",
        },
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_paired_codelist_terms(
    codelist_uid: str = CTCodelistUID,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
):
    ct_codelist_service = CTCodelistService()
    results = ct_codelist_service.get_paired_codelist_terms(
        codelist_uid=codelist_uid,
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
    "/codelists/headers",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns possibles values from the database for a given header",
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
    catalogue_name: Annotated[
        str | None,
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
    is_sponsor: Annotated[
        bool,
        Query(
            description="Boolean value to indicate desired package is a sponsor package. Defaults to False.",
        ),
    ] = False,
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
    ct_codelist_service = CTCodelistService()
    return ct_codelist_service.get_distinct_values_for_header(
        catalogue_name=catalogue_name,
        library=library_name,
        package=package,
        is_sponsor=is_sponsor,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/codelists/{codelist_uid}/terms",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List the CTTerms of a CTCodelist.",
    response_model=CustomPage[CTCodelistTerm],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_codelist_terms(
    codelist_uid: str = CTCodelistUID,
    package: str | None = Query(
        None,
        description="If specified, only codelists from given package are returned.",
    ),
    include_removed: bool | None = Query(
        False, description="Include removed terms in the lisiting."
    ),
    at_specific_date_time: Annotated[
        _generic_descriptions.AT_SPECIFIC_DATE_TIME_QUERY,
        Query(
            description="""If specified, return the terms that were part of the codelist at the specified date and time in format YYYY-MM-DDThh:mm:ss+hh:mm'""",
        ),
    ] = None,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    include_ts_parameters: _generic_descriptions.INCLUDE_TS_PARAMETERS_QUERY = False,
):
    ct_codelist_service = CTCodelistService()

    results = ct_codelist_service.list_terms(
        codelist_uid,
        package=package,
        include_removed=include_removed,
        at_specific_date_time=at_specific_date_time,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        include_ts_parameters=include_ts_parameters,
    )
    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/codelists/terms",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List the CTTerms of a CTCodelist identified either by codelist uid, submission value or name",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[CTCodelistTerm],
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
            "submission_value",
            "order",
            "library_name",
            "sponsor_preferred_name",
            "sponsor_preferred_name_sentence_case",
            "concept_id",
            "nci_preferred_name",
            "definition",
            "name_date",
            "name_status",
            "attributes_date",
            "attributes_status",
            "start_date",
            "end_date",
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
def get_codelist_terms_by_name_or_submval(
    request: Request,  # request is actually required by the allow_exports decorator
    codelist_uid: str | None = Query(
        None,
        description="UID of the codelist.",
    ),
    codelist_submission_value: str | None = Query(
        None,
        description="Submission value of the codelist.",
    ),
    codelist_name: str | None = Query(
        None,
        description="Name of the codelist.",
    ),
    package: str | None = Query(
        None,
        description="If specified, only codelists from given package are returned.",
    ),
    include_removed: bool | None = Query(
        False, description="Include removed terms in the lisiting."
    ),
    at_specific_date_time: Annotated[
        _generic_descriptions.AT_SPECIFIC_DATE_TIME_QUERY,
        Query(
            description="""If specified, return the terms that were part of the codelist at the specified date and time in format YYYY-MM-DDThh:mm:ss+hh:mm'""",
        ),
    ] = None,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    include_ts_parameters: _generic_descriptions.INCLUDE_TS_PARAMETERS_QUERY = False,
):
    ct_codelist_service = CTCodelistService()

    results = ct_codelist_service.list_terms(
        codelist_uid=codelist_uid,
        codelist_submission_value=codelist_submission_value,
        codelist_name=codelist_name,
        package=package,
        include_removed=include_removed,
        at_specific_date_time=at_specific_date_time,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        include_ts_parameters=include_ts_parameters,
    )
    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.post(
    "/codelists/{codelist_uid}/terms",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Adds new CTTerm to CTCodelist.",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "The HAS_TERM relationship was successfully created.\n"
            "The TemplateParameter labels and HAS_PARAMETER_TERM relationship were successfully added "
            "if codelist identified by codelist_uid is a TemplateParameter."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The codelist doesn't exist.\n"
            "- The term doesn't exist.\n"
            "- The codelist is not extensible.\n"
            "- The codelist already has passed term.\n"
            "- The term submission value is a new one for this term.\n",
        },
    },
)
def add_term(
    codelist_uid: Annotated[str, CTCodelistUID],
    term_input: Annotated[
        CTCodelistTermInput, Body(description="UID of the CTTermRoot node.")
    ],
) -> CTCodelist:
    ct_codelist_service = CTCodelistService()
    return ct_codelist_service.add_term(
        codelist_uid=codelist_uid,
        term_uid=term_input.term_uid,
        order=term_input.order,
        submission_value=term_input.submission_value,
        ordinal=term_input.ordinal,
    )


@router.delete(
    "/codelists/{codelist_uid}/terms/{term_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Removes given CTTerm from CTCodelist.",
    status_code=200,
    responses={
        200: {
            "description": "The HAS_TERM relationship was successfully ended.\n"
            "The HAS_PARAMETER_TERM relationship was successfully deleted if codelist identified by "
            "codelist_uid is a TemplateParameter"
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The codelist doesn't exist.\n"
            "- The term doesn't exist.\n"
            "- The codelist is not extensible.\n"
            "- The codelist doesn't have passed term.\n",
        },
        403: _generic_descriptions.ERROR_403,
    },
)
def remove_term(
    codelist_uid: Annotated[str, CTCodelistUID],
    term_uid: Annotated[str, TermUID],
) -> CTCodelist:
    ct_codelist_service = CTCodelistService()
    return ct_codelist_service.remove_term(codelist_uid=codelist_uid, term_uid=term_uid)


@router.get(
    "/codelists/terms/headers",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns possibles values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=list[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
    },
)
def get_distinct_term_values_for_header(
    codelist_uid: str,
    field_name: _generic_descriptions.HEADER_FIELD_NAME_QUERY,
    package: str | None = Query(
        None,
        description="If specified, only codelists from given package are returned.",
    ),
    include_removed: bool | None = Query(
        False, description="Include removed terms in the lisiting."
    ),
    include_ts_parameters: _generic_descriptions.INCLUDE_TS_PARAMETERS_QUERY = False,
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
):
    ct_codelist_service = CTCodelistService()
    return ct_codelist_service.get_distinct_term_values_for_header(
        codelist_uid=codelist_uid,
        package=package,
        include_removed=include_removed,
        include_ts_parameters=include_ts_parameters,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )
