"""class variables router."""

from typing import Annotated, Any

from fastapi import APIRouter, Path, Query
from starlette.requests import Request

from clinical_mdr_api.models.standard_data_models.variable_class import VariableClass
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.standard_data_models.variable_class import (
    VariableClassService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/standards"
router = APIRouter()

ClassVariableUID = Path(description="The unique id of the VariableClass")


@router.get(
    "/class-variables",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all class-variables",
    description=f"""
State before:

Business logic:
 - List all class variables in their latest version.

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
def get_class_variables(
    request: Request,  # request is actually required by the allow_exports decorator
    data_model_name: Annotated[
        str,
        Query(
            description="The name of the selected Data model, for instance 'SDTM'",
        ),
    ],
    data_model_version: Annotated[
        str,
        Query(
            description="The version of the selected Data model, for instance '1.4'",
        ),
    ],
    dataset_class_name: Annotated[
        str,
        Query(
            description="The name of the selected DatasetClass, for instance 'General Observations'",
        ),
    ],
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[VariableClass]:
    class_variable_service = VariableClassService()
    results = class_variable_service.get_all_items(
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        data_model_name=data_model_name,
        data_model_version=data_model_version,
        dataset_class_name=dataset_class_name,
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/class-variables/headers",
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
    data_model_name: Annotated[
        str,
        Query(
            description="The name of the selected Data model, for instance 'SDTM'",
        ),
    ],
    data_model_version: Annotated[
        str,
        Query(
            description="The version of the selected Data model, for instance '1.4'",
        ),
    ],
    dataset_class_name: Annotated[
        str,
        Query(
            description="The name of the selected DatasetClass, for instance 'General Observations'",
        ),
    ],
    field_name: _generic_descriptions.HEADER_FIELD_NAME_QUERY,
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
    class_variable_service = VariableClassService()
    return class_variable_service.get_distinct_values_for_header(
        data_model_name=data_model_name,
        data_model_version=data_model_version,
        dataset_class_name=dataset_class_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/class-variables/{class_variable_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific class variable",
    description="""
State before:
 - a class variable with uid must exist.

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
def get_class_variable(
    class_variable_uid: Annotated[str, ClassVariableUID],
    data_model_name: Annotated[
        str,
        Query(
            description="The name of the selected Data model, for instance 'SDTM'",
        ),
    ],
    data_model_version: Annotated[
        str,
        Query(
            description="The version of the selected Data model, for instance '1.4'",
        ),
    ],
    dataset_class_name: Annotated[
        str,
        Query(
            description="The name of the selected DatasetClass, for instance 'General Observations'",
        ),
    ],
) -> VariableClass:
    class_variable_service = VariableClassService()
    return class_variable_service.get_by_uid(
        uid=class_variable_uid,
        data_model_name=data_model_name,
        data_model_version=data_model_version,
        dataset_class_name=dataset_class_name,
    )
