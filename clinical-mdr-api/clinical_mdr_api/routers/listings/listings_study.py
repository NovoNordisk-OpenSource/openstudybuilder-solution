from typing import Annotated

from fastapi import APIRouter, Query

from clinical_mdr_api.models.listings.listings_study import StudyMetadataListingModel
from clinical_mdr_api.models.utils import PrettyJSONResponse
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.listings.listings_study import (
    StudyMetadataListingService,
)
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/listings"
router = APIRouter()


@router.get(
    "/studies/study-metadata",
    dependencies=[rbac.STUDY_READ],
    summary="Retrieve study metadata of a specific study",
    response_model=StudyMetadataListingModel,
    response_class=PrettyJSONResponse,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {
            "model": StudyMetadataListingModel,
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - No study with the specified study ID.",
        },
    },
)
def get_study_metadata(
    project_id: Annotated[str, Query(description="Project ID of study requested")],
    study_number: Annotated[str, Query(description="Study number of study requested")],
    subpart_acronym: Annotated[
        str, Query(description="subpart, if exists, of study requested")
    ] = None,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
    datetime: Annotated[
        str | None,
        Query(
            description=r"If specified, study data with latest released version of specified datetime is returned. "
            r"format in YYYY-MM-DDThh:mm:ssZ. ",
        ),
    ] = None,
):
    study_metadata_listing_service = StudyMetadataListingService()
    return study_metadata_listing_service.get_study_metadata(
        project_id, study_number, subpart_acronym, study_value_version, datetime
    )
