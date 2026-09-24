"""Sponsor Model Datasets router"""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from starlette.requests import Request

from clinical_mdr_api.models.standard_data_models.sponsor_model_dataset import (
    SponsorModelDataset,
    SponsorModelDatasetInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.standard_data_models.sponsor_model_dataset import (
    SponsorModelDatasetService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/standards/sponsor-models/datasets"
router = APIRouter()

SponsorModelDatasetUID = Path(description="The unique id of the SponsorModelDataset")


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all sponsor model datasets",
    description=f"""
State before:

Business logic:
 - List all sponsor model datasets in their latest version.

State after:
 - No change

Possible errors:
 - Invalid filter key or sort key specified.
 - Invalid field name in filters.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        400: _generic_descriptions.ERROR_400,
        403: _generic_descriptions.ERROR_403,
    },
)
@decorators.allow_exports(
    {
        "defaults": ["uid", "keys"],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_sponsor_model_datasets(
    request: Request,  # request is actually required by the allow_exports decorator
    sponsor_model_name: Annotated[
        str,
        Query(
            description="The name of the sponsor model, for instance 'sdtmig_mastermodel_3.2_NN15'. "
            "Required: the sponsor model determines which schema version governs the "
            "response shape, so sponsor-defined (extensible) fields cannot be projected without it.",
        ),
    ],
    sponsor_model_version: Annotated[
        str | None,
        Query(description="The version of the sponsor model, for instance '15'"),
    ] = None,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    export_fields: _generic_descriptions.EXPORT_FIELDS_QUERY = None,
) -> CustomPage[SponsorModelDataset]:
    sponsor_model_dataset_service = SponsorModelDatasetService()
    results = sponsor_model_dataset_service.get_all_items(
        sponsor_model_name=sponsor_model_name,
        sponsor_model_version=sponsor_model_version,
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
    sponsor_model_name: Annotated[
        str | None,
        Query(
            description="The name of the sponsor model, for instance 'sdtmig_mastermodel_3.2_NN15'",
        ),
    ] = None,
    field_name: _generic_descriptions.HEADER_FIELD_NAME_QUERY = "",
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
    sponsor_model_dataset_service = SponsorModelDatasetService()
    return sponsor_model_dataset_service.get_distinct_values_for_header(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
        sponsor_model_name=sponsor_model_name,
    )


@router.post(
    "",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Create a new version of the sponsor model dataset.",
    description="""
    State before:
    - The specified parent Sponsor Model version must exist.

    Business logic :
    - New instance is created for the Dataset.

    State after:
    - SponsorModelDatasetInstance node is created, assigned a version, and linked with the Dataset node.

    Possible errors:
    - Missing Sponsor Model version.
    """,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - a new version of the sponsor model dataset was successfully created."
        },
        400: {
            "model": ErrorResponse,
            "description": "BusinessLogicException - Reasons include e.g.: \n"
            "- The target parent Sponsor Model version *sponsor_model_version_number* doesn't exist.\n",
        },
    },
)
def create(
    sponsor_model: Annotated[
        SponsorModelDatasetInput,
        Body(
            description="Parameters of the Sponsor Model Dataset that shall be created.",
        ),
    ],
) -> SponsorModelDataset:
    sponsor_model_dataset_service = SponsorModelDatasetService()
    return sponsor_model_dataset_service.create(item_input=sponsor_model)
