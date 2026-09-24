"""datasets router."""

from typing import Annotated, Any

from fastapi import APIRouter, Path, Query
from starlette.requests import Request

from clinical_mdr_api.models.standard_data_models.dataset import Dataset
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.standard_data_models.dataset import DatasetService
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/standards"
router = APIRouter()

DatasetUID = Path(description="The unique id of the Dataset")


@router.get(
    "/datasets",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all datasets",
    description=f"""
State before:

Business logic:
 - List all datasets in their latest version.

State after:
 - No change

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
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
def get_datasets(
    request: Request,  # request is actually required by the allow_exports decorator
    data_model_ig_name: Annotated[
        str,
        Query(
            description="The name of the selected Data model implementation guide, for instance 'CDASHIG'",
        ),
    ],
    data_model_ig_version: Annotated[
        str,
        Query(
            description="The version of the selected Data model implementation guide, for instance '2.2'",
        ),
    ],
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[Dataset]:
    dataset_service = DatasetService()
    results = dataset_service.get_all_items(
        data_model_ig_name=data_model_ig_name,
        data_model_ig_version=data_model_ig_version,
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
    "/datasets/headers",
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
    data_model_ig_name: Annotated[
        str,
        Query(
            description="The name of the selected Data model implementation guide, for instance 'CDASHIG'",
        ),
    ],
    data_model_ig_version: Annotated[
        str,
        Query(
            description="The version of the selected Data model implementation guide, for instance '2.2'",
        ),
    ],
    field_name: _generic_descriptions.HEADER_FIELD_NAME_QUERY,
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
    dataset_service = DatasetService()
    return dataset_service.get_distinct_values_for_header(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
        data_model_ig_name=data_model_ig_name,
        data_model_ig_version=data_model_ig_version,
    )


@router.get(
    "/datasets/{dataset_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific dataset",
    description="""
State before:
 - a dataset with uid must exist.

Business logic:

State after:
 - No change

Possible errors:
 - Invalid uid.
 """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_dataset(
    data_model_ig_name: Annotated[
        str,
        Query(
            description="The name of the selected Data model implementation guide, for instance 'CDASHIG'",
        ),
    ],
    data_model_ig_version: Annotated[
        str,
        Query(
            description="The version of the selected Data model implementation guide, for instance '2.2'",
        ),
    ],
    dataset_uid: Annotated[str, DatasetUID],
) -> Dataset:
    dataset_service = DatasetService()
    return dataset_service.get_by_uid(
        uid=dataset_uid,
        data_model_ig_version=data_model_ig_version,
        data_model_ig_name=data_model_ig_name,
    )
