from datetime import datetime, timezone
from typing import Annotated, Any, Generic, Self, TypeVar

from fastapi import Request
from pydantic import BaseModel, Field
from requests.utils import requote_uri

from common.utils import convert_to_datetime
from consumer_api.shared.common import urlencode_link

T = TypeVar("T")


class StudyVersionSimple(BaseModel):
    version_status: Annotated[
        str | None,
        Field(description="Study Status", json_schema_extra={"nullable": True}),
    ] = None
    version_number: Annotated[
        str | None,
        Field(description="Study Version Number", json_schema_extra={"nullable": True}),
    ] = None
    version_started_at: Annotated[
        datetime,
        Field(
            description="Study Version Start Time",
        ),
    ]
    version_ended_at: Annotated[
        datetime | None,
        Field(
            description="Study Version End Time",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    retrieved_at: Annotated[
        datetime,
        Field(
            description="Study Version Retrieved Time",
        ),
    ]

    @classmethod
    def from_input(
        cls,
        version_status: str | None,
        version_number: str | None,
        version_started_at: datetime,
        version_ended_at: datetime | None = None,
    ) -> Self:
        return cls(
            version_status=version_status,
            version_number=version_number,
            version_started_at=version_started_at,
            version_ended_at=version_ended_at,
            retrieved_at=datetime.now(timezone.utc),
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated response model
    """

    self: Annotated[
        str, Field(description="Pagination link pointing to the current page")
    ]
    prev: Annotated[
        str, Field(description="Pagination link pointing to the previous page")
    ]
    next: Annotated[str, Field(description="Pagination link pointing to the next page")]
    items: Annotated[list[T], Field(description="List of items")]

    @classmethod
    def from_input(
        cls,
        request: Request,
        sort_by: str | None,
        sort_order: str | None,
        page_size: int,
        page_number: int,
        items: list[T],
        query_param_names: list[str] | None = None,
    ) -> Self:
        path = request.url.path

        # Extract query parameters not related to sorting/pagination from the request
        query_params = ""
        if query_param_names:
            for query_param_name in query_param_names:
                query_param_val = request.query_params.get(query_param_name)
                if query_param_val:
                    query_params = (
                        f"{query_params}{query_param_name}={query_param_val}&"
                    )
        query_params = requote_uri(query_params)

        prev_page_number = page_number - 1 if page_number > 1 else 1

        self_link = f"{path}?{query_params}sort_by={sort_by}&sort_order={sort_order}&page_size={page_size}&page_number={page_number}"
        prev_link = f"{path}?{query_params}sort_by={sort_by}&sort_order={sort_order}&page_size={page_size}&page_number={prev_page_number}"
        next_link = f"{path}?{query_params}sort_by={sort_by}&sort_order={sort_order}&page_size={page_size}&page_number={page_number + 1}"

        # pylint: disable=kwarg-superseded-by-positional-arg
        return cls(
            self=urlencode_link(self_link),
            prev=urlencode_link(prev_link),
            next=urlencode_link(next_link),
            items=items,
        )


class PaginatedResponseWithStudyVersion(PaginatedResponse, Generic[T]):
    """
    Paginated response model with study version
    """

    study_version: Annotated[
        StudyVersionSimple | None, Field(description="Study version information")
    ] = None

    @classmethod
    # pylint: disable=arguments-renamed
    def from_input(
        cls,
        request: Request,
        study_version: dict[str, Any],
        sort_by: str,
        sort_order: str,
        page_size: int,
        page_number: int,
        items: list[T],
        query_param_names: list[str] | None = None,
    ) -> Self:
        it = super().from_input(
            request=request,
            sort_by=sort_by,
            sort_order=sort_order,
            page_size=page_size,
            page_number=page_number,
            items=items,
            query_param_names=query_param_names,
        )

        it.study_version = StudyVersionSimple.from_input(
            version_status=study_version.get("version_status", None),
            version_number=study_version.get("version_number", None),
            version_started_at=convert_to_datetime(study_version["version_started_at"]),
            version_ended_at=convert_to_datetime(
                study_version.get("version_ended_at", None)
            ),
        )

        return it
