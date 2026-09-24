from typing import Any

from neomodel import db

from clinical_mdr_api.domains.listings.utils import AdamReport
from clinical_mdr_api.listings.query_service import QueryService
from clinical_mdr_api.models.listings.listings_adam import (
    FlowchartMetadataAdamListing,
    StudyEndpntAdamListing,
    StudyVisitAdamListing,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)


class ADAMListingsService:
    _repos: MetaRepository

    def __init__(self):
        self._query_service = QueryService()

    @db.transaction
    def list_mdflow(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> list[FlowchartMetadataAdamListing]:
        data = self._query_service.get_mdflow(
            study_uid=study_uid, study_value_version=study_value_version
        )
        result = [FlowchartMetadataAdamListing.from_query(item) for item in data]
        return result

    @db.transaction
    def list_mdvisit(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> list[StudyVisitAdamListing]:
        data = self._query_service.get_mdvisit(
            study_uid=study_uid, study_value_version=study_value_version
        )
        result = [StudyVisitAdamListing.from_query(item) for item in data]
        return result

    @db.transaction
    def list_mdendpnt(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> list[StudyEndpntAdamListing]:
        data = self._query_service.get_mdendpnt(
            study_uid=study_uid, study_value_version=study_value_version
        )
        result = [StudyEndpntAdamListing.from_query(item) for item in data]
        return result

    def get_report(
        self,
        adam_report: AdamReport,
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> (
        GenericFilteringReturn[StudyVisitAdamListing]
        | GenericFilteringReturn[StudyEndpntAdamListing]
        | GenericFilteringReturn[FlowchartMetadataAdamListing]
    ):
        result = []

        if adam_report == AdamReport.MDVISIT:
            result = self.list_mdvisit(
                study_uid, study_value_version=study_value_version
            )
        elif adam_report == AdamReport.MDENDPNT:
            result = self.list_mdendpnt(
                study_uid, study_value_version=study_value_version
            )
        elif adam_report == AdamReport.MDFLOW:
            result = self.list_mdflow(
                study_uid, study_value_version=study_value_version
            )

        return service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

    def get_distinct_adam_listing_values_for_headers(
        self,
        field_name: str,
        adam_report: AdamReport,
        study_uid: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
        study_value_version: str | None = None,
    ):
        result = []

        if adam_report == AdamReport.MDVISIT:
            result = self.list_mdvisit(
                study_uid, study_value_version=study_value_version
            )
        elif adam_report == AdamReport.MDENDPNT:
            result = self.list_mdendpnt(
                study_uid, study_value_version=study_value_version
            )
        elif adam_report == AdamReport.MDFLOW:
            result = self.list_mdflow(
                study_uid, study_value_version=study_value_version
            )

        filtered_items = service_level_generic_header_filtering(
            items=result,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )
        return filtered_items
