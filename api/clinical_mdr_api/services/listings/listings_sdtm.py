from typing import Any

from neomodel import db

from clinical_mdr_api.listings.query_service import QueryService
from clinical_mdr_api.models.listings.listings_sdtm import (
    StudyArmListing,
    StudyCriterionListing,
    StudyDiseaseMilestoneListing,
    StudyElementListing,
    StudySummaryListing,
    StudyVisitListing,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._utils import service_level_generic_filtering


class SDTMListingsService:
    def __init__(self):
        self._query_service = QueryService()

    @db.transaction
    def list_tv(
        self,
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[StudyVisitListing]:
        data = self._query_service.get_tv(
            study_uid=study_uid, study_value_version=study_value_version
        )
        result = list(map(StudyVisitListing.from_query, data))

        return service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

    @db.transaction
    def list_ta(
        self,
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[StudyArmListing]:
        data = self._query_service.get_ta(
            study_uid=study_uid, study_value_version=study_value_version
        )
        result = list(map(StudyArmListing.from_query, data))

        return service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

    @db.transaction
    def list_ti(
        self,
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[StudyCriterionListing]:
        data = self._query_service.get_ti(
            study_uid=study_uid, study_value_version=study_value_version
        )
        result = list(map(StudyCriterionListing.from_query, data))

        return service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

    @db.transaction
    def list_ts(
        self,
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[StudySummaryListing]:
        data = self._query_service.get_ts(
            study_uid=study_uid, study_value_version=study_value_version
        )
        result = list(map(StudySummaryListing.from_query, data))

        return service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

    @db.transaction
    def list_te(
        self,
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[StudyElementListing]:
        data = self._query_service.get_te(
            study_uid=study_uid, study_value_version=study_value_version
        )
        result = list(map(StudyElementListing.from_query, data))

        return service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

    @db.transaction
    def list_tdm(
        self,
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[StudyDiseaseMilestoneListing]:
        data = self._query_service.get_tdm(
            study_uid=study_uid, study_value_version=study_value_version
        )
        result = list(map(StudyDiseaseMilestoneListing.from_query, data))

        return service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
