"""Numeric values router."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json

from clinical_mdr_api.models.concepts.concept import (
    NumericValueWithUnit,
    NumericValueWithUnitPostInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.concepts.simple_concepts.numeric_value_with_unit import (
    NumericValueWithUnitService,
)
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/concepts/numeric-values-with-unit"
router = APIRouter()

NumericValueUID = Path(description="The unique id of the numeric value")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="List all numeric values with unit (for a given library)",
    description="""
State before:
 - The library must exist (if specified)

Business logic:
 - List all numeric values with units.

State after:
 - No change

Possible errors:
 - Invalid library name specified.""",
    response_model=CustomPage[NumericValueWithUnit],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_numeric_values(
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
    numeric_value_service = NumericValueWithUnitService()
    results = numeric_value_service.get_all_concepts(
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
    numeric_value_service = NumericValueWithUnitService()
    return numeric_value_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/{numeric_value_uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get details on a specific numeric value with unit",
    description="""
State before:
 - a numerical value with specified uid must exist.

State after:
 - No change

Possible errors:
 - Invalid uid
 """,
    response_model=NumericValueWithUnit,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_numeric_value(numeric_value_uid: Annotated[str, NumericValueUID]):
    numeric_value_service = NumericValueWithUnitService()
    return numeric_value_service.get_by_uid(uid=numeric_value_uid)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Creates new numeric value or returns already existing numeric value.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).

Business logic:
 - New node is created for the numeric value with the set properties.

Possible errors:
 - Invalid library.
""",
    response_model=NumericValueWithUnit,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The numeric value was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
    },
)
def create(
    numeric_value_create_input: Annotated[NumericValueWithUnitPostInput, Body()],
):
    numeric_value_service = NumericValueWithUnitService()
    return numeric_value_service.create(concept_input=numeric_value_create_input)
