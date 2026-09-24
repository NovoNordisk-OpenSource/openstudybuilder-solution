from typing import Annotated

from fastapi import APIRouter, Path
from starlette.requests import Request

from clinical_mdr_api.models.listings.listings_sdtm import (
    StudyArmListing,
    StudyCriterionListing,
    StudyDiseaseMilestoneListing,
    StudyElementListing,
    StudySummaryListing,
    StudyVisitListing,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.listings.listings_sdtm import (
    SDTMListingsService as ListingsService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings

# Prefixed with "/listings"
router = APIRouter()


@router.get(
    "/studies/{study_uid}/sdtm/tv",
    dependencies=[security, rbac.STUDY_READ],
    summary="SDTM TV domain listing",
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
            "STUDYID",
            "DOMAIN",
            "VISITNUM",
            "VISIT",
            "VISITDY",
            "ARMCD",
            "ARM",
            "TVSTRL",
            "TVENRL",
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
def get_tv(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: Annotated[
        str,
        Path(
            description="Return study visit data of a given study in SDTM TV domain format."
        ),
    ],
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> CustomPage[StudyVisitListing]:
    service = ListingsService()
    all_items = service.list_tv(
        study_uid=study_uid,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
        study_value_version=study_value_version,
    )

    return CustomPage(
        items=all_items.items,
        total=all_items.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/studies/{study_uid}/sdtm/ta",
    dependencies=[security, rbac.STUDY_READ],
    summary="SDTM TA domain listing",
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
            "STUDYID",
            "DOMAIN",
            "ARMCD",
            "ARM",
            "TAETORD",
            "ETCD",
            "ELEMENT",
            "TABRANCH",
            "TATRANS",
            "EPOCH",
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
def get_ta(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: Annotated[
        str,
        Path(
            description="Return study arm data of a given study number in SDTM TA domain format."
        ),
    ],
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> CustomPage[StudyArmListing]:
    service = ListingsService()
    all_items = service.list_ta(
        study_uid=study_uid,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
        study_value_version=study_value_version,
    )

    return CustomPage(
        items=all_items.items,
        total=all_items.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/studies/{study_uid}/sdtm/ti",
    dependencies=[security, rbac.STUDY_READ],
    summary="SDTM TI domain listing",
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
            "STUDYID",
            "DOMAIN",
            "IETESTCD",
            "IETEST",
            "IECAT",
            "IESCAT",
            "TIRL",
            "TIVERS",
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
def get_ti(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: Annotated[
        str,
        Path(
            description="Return study criterion data of a given study in SDTM TI domain format."
        ),
    ],
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> CustomPage[StudyCriterionListing]:
    service = ListingsService()
    all_items = service.list_ti(
        study_uid=study_uid,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
        study_value_version=study_value_version,
    )

    return CustomPage(
        items=all_items.items,
        total=all_items.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/studies/{study_uid}/sdtm/ts",
    dependencies=[security, rbac.STUDY_READ],
    summary="SDTM TS domain listing",
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
            "STUDYID",
            "DOMAIN",
            "TSPARMCD",
            "TSPARM",
            "TSVAL",
            "TSVALNF",
            "TSVALCD",
            "TSVCDREF",
            "TSVCDVER",
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
def get_ts(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: Annotated[
        str,
        Path(
            description="Return study summary data of a given study in SDTM TS domain format."
        ),
    ],
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> CustomPage[StudySummaryListing]:
    service = ListingsService()
    all_items = service.list_ts(
        study_uid=study_uid,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
        study_value_version=study_value_version,
    )

    return CustomPage(
        items=all_items.items,
        total=all_items.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/studies/{study_uid}/sdtm/te",
    dependencies=[security, rbac.STUDY_READ],
    summary="SDTM TE domain listing",
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
            "STUDYID",
            "DOMAIN",
            "ETCD",
            "ELEMENT",
            "TESTRL",
            "TEENRL",
            "TEDUR",
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
def get_te(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: Annotated[
        str,
        Path(
            description="Return study element data of a given study number in SDTM TE domain format."
        ),
    ],
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> CustomPage[StudyElementListing]:
    service = ListingsService()
    all_items = service.list_te(
        study_uid=study_uid,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
        study_value_version=study_value_version,
    )

    return CustomPage(
        items=all_items.items,
        total=all_items.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/studies/{study_uid}/sdtm/tdm",
    dependencies=[security, rbac.STUDY_READ],
    summary="SDTM TDM domain listing",
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
            "STUDYID",
            "DOMAIN",
            "MIDSTYPE",
            "TMDEF",
            "TMRPT",
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
def get_tdm(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: Annotated[
        str,
        Path(
            description="Return study disease milestone data of a given study number in SDTM TDM domain format."
        ),
    ],
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> CustomPage[StudyDiseaseMilestoneListing]:
    service = ListingsService()
    all_items = service.list_tdm(
        study_uid=study_uid,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
        study_value_version=study_value_version,
    )

    return CustomPage(
        items=all_items.items,
        total=all_items.total,
        page=page_number,
        size=page_size,
    )
