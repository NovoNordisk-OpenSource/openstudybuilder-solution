"""CTTerms router."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from starlette.requests import Request

from clinical_mdr_api.domains.controlled_terminologies.utils import TermParentType
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    CTTerm,
    CTTermCodelists,
    CTTermCreateInput,
    CTTermNameAndAttributes,
    CTTermNewCodelist,
    CTTermRelatives,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.controlled_terminologies.ct_term import CTTermService
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/ct"
router = APIRouter()

CTTermUID = Path(description="The unique id of the ct term.")


@router.post(
    "/terms",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates new ct term.",
    description="""The following nodes are created
* CTTermRoot
  * CTTermAttributesRoot
  * CTTermAttributesValue
  * CTTermNameRoot
  * CTTermNameValue

Optionally, Trial Summary parameter properties can be supplied via the
`ts_parameter` field. When provided, the corresponding scalar properties
(reference, required_level, cardinality, notes) are
stored on the new CTTermNameValue, the `osb_page_reference` is stored on
the linked `MetaStudyField`, and the graph relationships
(`RELATED_STUDY_FIELD_SELECTION`, `HAS_SEMANTIC_DATA_TYPE`,
`RESPONSE_CODELIST`, `RESPONSE_DICTIONARY`, `VALID_NULL_FLAVOR`) are wired
on the initial save.
""",
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
) -> CTTerm:
    ct_term_service = CTTermService()
    return ct_term_service.create(term_input)


@router.get(
    "/terms",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns all terms names and attributes.",
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
        bool,
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
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    include_ts_parameters: _generic_descriptions.INCLUDE_TS_PARAMETERS_QUERY = False,
) -> CustomPage[CTTermNameAndAttributes]:
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
        include_ts_parameters=include_ts_parameters,
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/terms/headers",
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
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
    lite: Annotated[
        bool,
        Query(description=_generic_descriptions.HEADERS_QUERY_LITE),
    ] = False,
) -> list[Any]:
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
        lite=lite,
    )


@router.post(
    "/terms/{term_uid}/parents",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Adds a CT Term Root node as a parent to the selected term node.",
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
        TermParentType,
        Query(
            description="The type of the parent relationship.\n"
            "Valid types are 'type', 'subtype', 'specialization' or 'predecessor'",
        ),
    ],
) -> CTTerm:
    ct_term_service = CTTermService()
    return ct_term_service.add_parent(
        term_uid=term_uid, parent_uid=parent_uid, relationship_type=relationship_type
    )


@router.delete(
    "/terms/{term_uid}/parents",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Removes a parent term from the selected term node",
    status_code=200,
    responses={
        200: {
            "description": "Created - The term was successfully removed as a parent to the term identified by term-uid."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term already has no defined parent with given parent-uid and relationship type.\n",
        },
        403: _generic_descriptions.ERROR_403,
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
        TermParentType,
        Query(
            description="The type of the parent relationship.\n"
            "Valid types are 'type', 'subtype', 'specialization' or 'predecessor'",
        ),
    ],
) -> CTTerm:
    ct_term_service = CTTermService()
    return ct_term_service.remove_parent(
        term_uid=term_uid, parent_uid=parent_uid, relationship_type=relationship_type
    )


@router.patch(
    "/terms/{term_uid}/codelists",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Change an order of codelist-term relationship",
    description="""Reordering will create new HAS_TERM relationship.""",
    response_model=CTTermNewCodelist,
    status_code=200,
    responses={
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
def patch_new_term_codelist(
    term_uid: str = CTTermUID,
    new_order_input: CTTermNewCodelist = Body(
        description="Parameters needed for the reorder action."
    ),
) -> CTTermNewCodelist:
    ct_term_service = CTTermService()
    return ct_term_service.set_new_order_and_submission_value(
        term_uid=term_uid,
        codelist_uid=new_order_input.codelist_uid,
        new_order=new_order_input.order,
        new_submission_value=new_order_input.submission_value,
    )


@router.get(
    "/terms/{term_uid}/codelists",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns the latest/newest version of the codelists that the ct term identified by 'term_uid' is included in",
    response_model=CTTermCodelists,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
    },
)
def get_term_codelists(
    term_uid: str = CTTermUID,
    at_specified_date_time: Annotated[
        _generic_descriptions.AT_SPECIFIC_DATE_TIME_QUERY,
        Query(
            description="If specified then the latest/newest representation of the "
            "CTTermAttributesValue at this point in time is returned.\n"
            "The point in time needs to be specified in ISO 8601 format including the timezone, "
            "e.g.: '2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. "
            "If the timezone is omitted, UTC±0 is assumed.",
        ),
    ] = None,
):
    ct_term_service = CTTermService()
    return ct_term_service.get_codelists_by_uid(
        term_uid=term_uid,
        at_specific_date_time=at_specified_date_time,
    )


@router.get(
    "/terms/{term_uid}/parents",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns the latest/newest version of the codelists that the ct term identified by 'term_uid' is included in",
    response_model=CTTermRelatives,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
    },
)
def get_term_parents(
    term_uid: str = CTTermUID,
):
    ct_term_service = CTTermService()
    return ct_term_service.get_parents_by_uid(
        term_uid=term_uid,
    )
