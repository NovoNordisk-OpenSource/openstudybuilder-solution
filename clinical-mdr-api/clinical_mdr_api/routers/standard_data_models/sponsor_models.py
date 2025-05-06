"""Sponsor Models router"""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api.models.standard_data_models.sponsor_model import (
    SponsorModel,
    SponsorModelInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.standard_data_models.sponsor_model import (
    SponsorModelService,
)
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/standards/sponsor-models/models"
router = APIRouter()

SponsorModelUID = Path(description="The unique id of the SponsorModel")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="List all sponsor models",
    description="""
State before:

Business logic:
 - List all sponsor models in their latest version.

State after:
 - No change

Possible errors:
""",
    response_model=CustomPage[SponsorModel],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
    },
)
@decorators.allow_exports(
    {
        "defaults": ["uid", "name", "start_date", "status", "version"],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_sponsor_models(
    request: Request,  # request is actually required by the allow_exports decorator
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
    sponsor_model_service = SponsorModelService()
    results = sponsor_model_service.get_all_items(
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
    sponsor_model_service = SponsorModelService()
    return sponsor_model_service.get_distinct_values_for_header(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Create a new version of the sponsor model.",
    description="""
    State before:
    - The specified Implementation Guide must exist, in the version provided.

    Business logic :
    - New version is created for the Sponsor Model, with auto-generated name in the format : *ig_uid*_sponsormodel_*igversion*_NN1
    - The status of the new created version will be automatically set to 'Draft'.
    - The 'version' property of the new version will be automatically set to 1.
    - The 'change_description' property will be set automatically to 'Imported new version'.

    State after:
    - SponsorModelValue node is created, assigned a version, and linked with the DataModelIGRoot node.

Possible errors:
    - Missing Implementation Guide, or version of IG.
    """,
    response_model=SponsorModel,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - a new version of the sponsor model was successfully created."
        },
        400: {
            "model": ErrorResponse,
            "description": "BusinessLogicException - Reasons include e.g.: \n"
            "- The target Implementation Guide *ig_uid* doesn't exist.\n"
            "- The target version *ig_version_number* for the Implementation Guide with UID *ig_uid* doesn't exist.\n",
        },
    },
)
# pylint: disable=unused-argument
def create(
    sponsor_model: Annotated[
        SponsorModelInput,
        Body(description="Parameters of the Sponsor Model that shall be created."),
    ],
) -> SponsorModel:
    sponsor_model_service = SponsorModelService()
    return sponsor_model_service.create(item_input=sponsor_model)
