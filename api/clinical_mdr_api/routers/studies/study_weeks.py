"""study weeks router."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query

from clinical_mdr_api.models.concepts.concept import NumericValue, NumericValuePostInput
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.concepts.simple_concepts.study_week import (
    StudyWeekService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/concepts/study-weeks"
router = APIRouter()

StudyWeekUID = Path(description="The unique id of the study week")


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all study weeks (for a given library)",
    description="""
State before:
 - The library must exist (if specified)

Business logic:
 - List all study weeks.

State after:
 - No change

Possible errors:
 - Invalid library name specified.""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_study_weeks(
    library_name: Annotated[str | None, Query()] = None,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[NumericValue]:
    study_week_service = StudyWeekService()
    results = study_week_service.get_all_concepts(
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
    "/headers",
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
    study_week_service = StudyWeekService()
    return study_week_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/{study_week_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific study week",
    description="""
State before:
 - a time point with uid must exist.

State after:
 - No change

Possible errors:
 - Invalid uid
 """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_study_week(study_week_uid: Annotated[str, StudyWeekUID]) -> NumericValue:
    study_week_service = StudyWeekService()
    return study_week_service.get_by_uid(uid=study_week_uid)


@router.post(
    "",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates new study week or returns already existing study week.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).

Business logic:
 - New node is created for the study week with the set properties.

Possible errors:
 - Invalid library.
""",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The study week was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
    },
)
def create(
    numeric_value_create_input: Annotated[NumericValuePostInput, Body()],
) -> NumericValue:
    study_week_service = StudyWeekService()
    return study_week_service.create(concept_input=numeric_value_create_input)
