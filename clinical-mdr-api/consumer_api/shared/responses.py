from typing import Annotated, Generic, TypeVar

from fastapi import Request
from pydantic import BaseModel, Field
from requests.utils import requote_uri

from consumer_api.shared.common import urlencode_link

T = TypeVar("T")


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
        sort_by: str,
        sort_order: str,
        page_size: int,
        page_number: int,
        items: list[T],
        query_param_names: list[str] | None = None,
    ):
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
