"""Consumer sample: read CT terms directly from the OpenStudyBuilder database.

An example of a read-only extension: it queries Neo4j itself (see db.py), protected by the
same authentication and role as the rest of the Extensions API (see README.md in this folder).
"""

from typing import Annotated

from fastapi import APIRouter, Query, Request

from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from extensions.common import PaginatedResponse
from extensions.consumer_sample import db as DB, models

router = APIRouter(
    tags=["Consumer sample"],
)

PAGE_SIZE_QUERY = Query(
    ge=1,
    le=settings.max_page_size,
    description="Number of items to be returned per page. Must be between 1 and the maximum allowed page size.",
)
PAGE_NUMBER_QUERY = Query(
    ge=1,
    le=settings.max_page_number,
    description="Page number of the returned list of entities. Must be between 1 and the maximum allowed page number.",
)


@router.get(
    "/ct-terms",
    dependencies=[security, rbac.LIBRARY_READ],
    status_code=200,
)
def get_ct_terms(
    request: Request,
    codelist_submission_value: Annotated[
        str,
        Query(
            description="Codelist submission value, for example `TIMELB`, `TIMEREF`, `VISCNTMD`, `EPOCHSTP`."
        ),
    ],
    sort_by: models.SortByCTTerms = models.SortByCTTerms.TERM_UID,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: Annotated[int, PAGE_SIZE_QUERY] = settings.page_size_100,
    page_number: Annotated[
        int, PAGE_NUMBER_QUERY
    ] = settings.default_page_number_consumer_api,
) -> PaginatedResponse[models.CTTerm]:
    """
    Returns one page of the CT terms of the codelist with the given submission value
    (only terms whose name and attributes are currently Final).

    A term that is being revised (a new Draft version) or is retired is not returned
    until it is approved again; the status of the codelist itself is not checked.
    An unknown submission value gives an empty page. `total` is the number of such terms
    in the codelist, whatever the page.
    """
    terms, total = DB.get_ct_terms(
        codelist_submission_value=codelist_submission_value,
        sort_by=sort_by,
        sort_order=sort_order,
        page_size=page_size,
        page_number=page_number,
    )
    return PaginatedResponse.from_input(
        request=request,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        page_size=page_size,
        page_number=page_number,
        items=[models.CTTerm.model_validate(term) for term in terms],
        query_param_names=["codelist_submission_value"],
        total=total,
    )
