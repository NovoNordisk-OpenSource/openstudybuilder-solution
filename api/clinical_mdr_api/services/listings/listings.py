from datetime import datetime
from typing import Any, Callable

from neomodel import db

from clinical_mdr_api.listings.query_service import QueryService
from clinical_mdr_api.models.listings.listings import (
    CDISCCTList,
    CDISCCTPkg,
    CDISCCTVal,
    CDISCCTVer,
    MetaData,
    TopicCdDef,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._utils import (
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)


class ListingsService:
    def __init__(self):
        self._query_service = QueryService()

    @db.transaction
    def list_topic_cd(
        self,
        at_specified_datetime: datetime | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[TopicCdDef]:
        data = self._query_service.get_topic_codes(
            at_specific_date=at_specified_datetime,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        data.items = list(map(TopicCdDef.from_query, data.items))

        return data

    @db.transaction
    def list_metadata(
        self,
        dataset_name: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[MetaData]:
        data = self._query_service.get_metadata(dataset_name=dataset_name)
        result = list(map(MetaData.from_query, data))

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
    def list_cdisc_ct_ver(
        self,
        catalogue_name: str | None = None,
        after_date: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[CDISCCTList]:
        data = self._query_service.get_cdisc_ct_ver(
            catalogue_name=catalogue_name,
            after_date=after_date,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        data.items = list(map(CDISCCTVer.from_query, data.items))

        return data

    @db.transaction
    def list_cdisc_ct_pkg(
        self,
        catalogue_name: str | None = None,
        after_date: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[CDISCCTList]:
        data = self._query_service.get_cdisc_ct_pkg(
            catalogue_name=catalogue_name,
            after_date=after_date,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        data.items = list(map(CDISCCTPkg.from_query, data.items))

        return data

    @db.transaction
    def list_cdisc_ct_list(
        self,
        catalogue_name: str | None = None,
        package: str | None = None,
        after_date: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[CDISCCTList]:
        data = self._query_service.get_cdisc_ct_list(
            catalogue_name=catalogue_name,
            package=package,
            after_date=after_date,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

        data.items = list(map(CDISCCTList.from_query, data.items))

        return data

    @db.transaction
    def list_cdisc_ct_val(
        self,
        catalogue_name: str | None = None,
        package: str | None = None,
        after_date: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[CDISCCTVal]:
        data = self._query_service.get_cdisc_ct_val(
            catalogue_name=catalogue_name,
            package=package,
            after_date=after_date,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        data.items = list(map(CDISCCTVal.from_query, data.items))

        return data

    def get_distinct_values_for_header(
        self,
        action: Callable,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ):
        all_items = action()

        header_values = service_level_generic_header_filtering(
            items=all_items.items,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )

        return header_values
