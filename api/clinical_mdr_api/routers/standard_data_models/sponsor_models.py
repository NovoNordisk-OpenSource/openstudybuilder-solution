"""Sponsor Models router"""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path
from starlette.requests import Request

from clinical_mdr_api.models.standard_data_models.sponsor_model import (
    SponsorModel,
    SponsorModelCreateInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.standard_data_models.sponsor_model import (
    SponsorModelService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/standards/sponsor-models/models"
router = APIRouter()

SponsorModelUID = Path(description="The unique id of the SponsorModel")


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all sponsor models",
    description="""
State before:

Business logic:
 - List all sponsor models in their latest version.

State after:
 - No change

Possible errors:
""",
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
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[SponsorModel]:
    sponsor_model_service = SponsorModelService()
    results = sponsor_model_service.get_all_items(
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
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
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
    dependencies=[security, rbac.LIBRARY_WRITE],
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
        SponsorModelCreateInput,
        Body(description="Parameters of the Sponsor Model that shall be created."),
    ],
) -> SponsorModel:
    sponsor_model_service = SponsorModelService()
    return sponsor_model_service.create(item_input=sponsor_model)
