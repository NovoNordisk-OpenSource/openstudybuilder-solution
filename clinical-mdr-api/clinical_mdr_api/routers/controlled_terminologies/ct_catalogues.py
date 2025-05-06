"""CTCatalogue router."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Query

from clinical_mdr_api.models.controlled_terminologies.ct_catalogue import (
    CTCatalogue,
    CTCatalogueChanges,
)
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.controlled_terminologies.ct_catalogue import (
    CTCatalogueService,
)
from common.auth import rbac

# Prefixed with "/ct"
router = APIRouter()


@router.get(
    "/catalogues",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all controlled terminology catalogues.",
    response_model=list[CTCatalogue],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
# pylint: disable=unused-argument
def get_catalogues(
    library_name: Annotated[
        str | None,
        Query(
            description="If specified, only catalogues from given library are returned."
        ),
    ] = None,
):
    ct_catalogue_service = CTCatalogueService()
    return ct_catalogue_service.get_all_ct_catalogues(library_name=library_name)


@router.get(
    "/catalogues/changes",
    dependencies=[rbac.LIBRARY_READ],
    summary="List changes between codelists and terms in CT Catalogues.",
    response_model=CTCatalogueChanges,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_catalogues_changes(
    comparison_type: Annotated[
        str,
        Query(
            description="The type of the comparison.\n"
            "Valid types are `attributes` or `sponsor`",
            openapi_examples={
                "attributes": {"value": "attributes"},
                "sponsor": {"value": "sponsor"},
            },
        ),
    ],
    start_datetime: Annotated[
        datetime,
        Query(
            description="The start datetime to perform comparison (ISO 8601 format with UTC offset)",
            openapi_examples={
                "2023-03-26T00:00:00+00:00": {"value": "2023-03-26T00:00:00+00:00"}
            },
        ),
    ],
    library_name: Annotated[
        str | None,
        Query(
            description="If specified, only codelists and terms from given library_name are compared."
        ),
    ] = None,
    catalogue_name: Annotated[
        str | None,
        Query(
            description="If specified, only codelists and terms from given catalogue_name are compared."
        ),
    ] = None,
    end_datetime: Annotated[
        datetime | None,
        Query(
            description="The end datetime to perform comparison (ISO 8601 format with UTC offset).\n"
            "If it is not passed, then the current datetime is assigned.",
            openapi_examples={
                "2023-03-27T00:00:00+00:00": {"value": "2023-03-27T00:00:00+00:00"}
            },
        ),
    ] = None,
):
    if end_datetime is None:
        end_datetime = datetime.now(timezone.utc)
    ct_catalogue_service = CTCatalogueService()
    return ct_catalogue_service.get_ct_catalogues_changes(
        library_name=library_name,
        catalogue_name=catalogue_name,
        comparison_type=comparison_type,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    )
