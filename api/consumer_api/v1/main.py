# RESTful API endpoints used by consumers that want to extract data from OpenStudyBuilder
# pylint: disable=invalid-name
# pylint: disable=redefined-builtin
import csv
import io
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Body, Path, Query, Request, Response

from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.exceptions import ValidationException
from common.models.error import ErrorResponse
from common.utils import BaseTimelineAR
from consumer_api.shared.common import PAGE_NUMBER_QUERY, PAGE_SIZE_QUERY
from consumer_api.shared.responses import (
    PaginatedResponse,
    PaginatedResponseWithStudyVersion,
)
from consumer_api.v1 import api_specs
from consumer_api.v1 import db as DB
from consumer_api.v1 import models
from consumer_api.v1.services.soa import SoAService
from consumer_api.v1.services.study import StudyCreateService

router = APIRouter()

# Reverse of import_sponsor_data's MMA_QORIG_MAP - (origin type name, origin
# source name) -> MMA sdtm_qnam_qorig value, for the Papillons NSV export.
_MMA_QORIG_REVERSE_MAP: dict[tuple[str, str], str] = {
    ("Assigned Value", "Clinical Study Sponsor"): "Assigned",
    ("Collected Value", "Investigator"): "CRF",
    ("Derived Value", "Clinical Study Sponsor"): "Derived",
    ("Collected Value", "Vendor"): "eDT",
}


# GET endpoint to retrieve a list of studies
@router.get(
    "/studies",
    tags=["[V1] Studies"],
    dependencies=[security, rbac.STUDY_READ],
    status_code=200,
)
def get_studies(
    request: Request,
    sort_by: models.SortByStudies = models.SortByStudies.UID,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: Annotated[int, PAGE_SIZE_QUERY] = settings.default_page_size,
    page_number: Annotated[
        int, PAGE_NUMBER_QUERY
    ] = settings.default_page_number_consumer_api,
    id: Annotated[
        str | None,
        Query(
            description="Filter by study ID (case-insensitive partial match), for example `XX1234-5678`."
        ),
    ] = None,
) -> PaginatedResponse[models.Study]:
    """
    Returns a paginated list of studies, sorted by the specified sort criteria and order.

    Each returned study contains a full list of corresponding study versions, sorted by version start date in descending order.

    Returned `version_number` value can be used in other endpoints to retrieve study entities (e.g. visits, activities, etc.)
    associated with a specific study version.

    Codelist details can be retrieved from the `GET /v1/library/ct/codelists` endpoint.

    Details related to the Data Supplier type can be retrieved from the `GET /v1/library/ct/codelist-terms?codelist_submission_value=DATA_SUPPLIER_TYPE` endpoint.
    """
    studies = DB.get_studies(
        sort_by=sort_by,
        sort_order=sort_order,
        page_size=page_size,
        page_number=page_number,
        id=id,
    )

    return PaginatedResponse.from_input(
        request=request,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        page_size=page_size,
        page_number=page_number,
        items=[models.Study.from_input(study) for study in studies],
        query_param_names=["id"],
    )


# POST endpoint to create a study
@router.post(
    "/studies",
    tags=["[V1] Studies"],
    dependencies=[security, rbac.STUDY_WRITE],
    status_code=201,
    responses={
        201: {"description": "Study created successfully"},
        409: {
            "model": ErrorResponse,
            "description": "Conflict - a study with the same number or acronym already exists",
        },
    },
)
def create_study(
    study_input: Annotated[
        models.StudyCreateInput,
        Body(
            openapi_examples={
                "example": {
                    "summary": "Create a study",
                    "value": api_specs.EXAMPLE_POST_STUDY_REQUEST,
                }
            }
        ),
    ],
) -> models.StudyCreateResponse:
    """
    Creates a new study definition in `DRAFT` status.

    - Only top-level studies can be created here. Study subparts are not supported
    by this endpoint.

    - At least one of `study_number` and `study_acronym` must be provided.

    - `study_number` and `study_acronym` must each be unique across all studies,
    not just within the project. A collision is rejected with HTTP 409.

    - The study ID is derived by the server as `{project_id}-{study_number}`
    and cannot be supplied by the caller.

    <br/>
    Valid values for payload fields:

    - **project_id**: Allowed values are retrieved from the `GET /v1/library/projects`
    endpoint (**id** field). The value is matched exactly and case-sensitively.
    """
    return StudyCreateService().create_study(study_input=study_input)


@router.get(
    "/papillons/study-metadata",
    tags=["[V1] Papillons"],
    dependencies=[security, rbac.STUDY_READ],
    status_code=200,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - No Locked study with the specified study ID.",
        },
    },
)
def get_study_metadata(
    project_id: Annotated[str, Query(description="Project ID of study requested")],
    study_number: Annotated[str, Query(description="Study number of study requested")],
    subpart_acronym: Annotated[
        str | None, Query(description="Subpart, if exists, of study requested")
    ] = None,
    study_value_version: Annotated[
        str | None,
        Query(
            description="Study value version, e.g. 1, 2.1. If specified, study data with that version is returned. "
            "Omit together with datetime to use the latest released study value."
        ),
    ] = None,
    datetime_value: Annotated[
        str | None,
        Query(
            alias="datetime",
            description="If specified, study data with latest released version before this datetime is returned. "
            "Format: YYYY-MM-DDThh:mm:ssZ. Omit together with study_value_version to use the latest released study value.",
        ),
    ] = None,
) -> models.StudyMetadataListingModel:
    """
    Returns study metadata and study selection data for the given study.

    If both ``study_value_version`` and ``datetime`` are omitted, the latest
    released study value is used. The two selectors must not be provided together.
    """
    ValidationException.raise_if(
        study_value_version is not None and datetime_value is not None,
        msg="Please specify either version or datetime, not both.",
    )
    return DB.get_study_metadata_listing(
        project_id=project_id,
        study_number=study_number,
        subpart_acronym=subpart_acronym,
        study_value_version=study_value_version,
        datetime_value=datetime_value,
    )


# GET endpoint to retrieve a study's visits
@router.get(
    "/studies/{uid}/study-visits",
    tags=["[V1] Studies"],
    dependencies=[security, rbac.STUDY_READ],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Item not found",
        },
    },
)
def get_study_visits(
    request: Request,
    uid: Annotated[str, Path(description="Study UID")],
    sort_by: models.SortByStudyVisits = models.SortByStudyVisits.UNIQUE_VISIT_NUMBER,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: Annotated[int, PAGE_SIZE_QUERY] = settings.page_size_100,
    page_number: Annotated[
        int, PAGE_NUMBER_QUERY
    ] = settings.default_page_number_consumer_api,
    study_version_number: Annotated[
        str | None,
        Query(
            description="Study Version Number",
            openapi_examples={"2.1": {"value": "2.1"}},
        ),
    ] = None,
) -> PaginatedResponseWithStudyVersion[models.StudyVisit]:
    """
    Returns a paginated list of study visits, sorted by the specified sort criteria and order.

    If `study_version_number` query parameter is provided, study visits
    associated with the specified study version will be returned.
    Otherwise, visits for the latest study version will be returned.
    """
    study_version = DB.get_study_version(
        study_uid=uid,
        study_version_number=study_version_number,
    )

    # We need to retrieve all study visits to correctly assign `visit_order` and `visit_number` to each visit after timeline generation
    study_visits_all = DB.get_study_visits(
        study_uid=uid,
        sort_by=sort_by,
        sort_order=sort_order,
        page_size=settings.max_page_size,
        page_number=1,
        study_version_number=study_version_number,
    )
    items_all = [
        models.StudyVisit.from_input(study_visit) for study_visit in study_visits_all
    ]

    # Generate timeline to assign `visit_order` and `visit_number` to all study visits
    BaseTimelineAR(study_uid=uid, _visits=items_all)._generate_timeline()

    # Return the requested page of study visits
    items = items_all[(page_number - 1) * page_size : page_number * page_size]
    return PaginatedResponseWithStudyVersion.from_input(
        request=request,
        study_version=study_version,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        page_size=page_size,
        page_number=page_number,
        items=items,
        query_param_names=["study_version_number"],
    )


# GET endpoint to retrieve a study's activities
@router.get(
    "/studies/{uid}/study-activities",
    tags=["[V1] Studies"],
    dependencies=[security, rbac.STUDY_READ],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Item not found",
        },
    },
)
def get_study_activities(
    request: Request,
    uid: Annotated[str, Path(description="Study UID")],
    sort_by: models.SortByStudyActivities = models.SortByStudyActivities.UID,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: Annotated[int, PAGE_SIZE_QUERY] = settings.page_size_100,
    page_number: Annotated[
        int, PAGE_NUMBER_QUERY
    ] = settings.default_page_number_consumer_api,
    study_version_number: Annotated[
        str | None,
        Query(
            description="Study Version Number",
            openapi_examples={"2.1": {"value": "2.1"}},
        ),
    ] = None,
) -> PaginatedResponseWithStudyVersion[models.StudyActivity]:
    """
    Returns a paginated list of study activities, sorted by the specified sort criteria and order.

    If `study_version_number` query parameter is provided, study activities
    associated with the specified study version will be returned.
    Otherwise, activities for the latest study version will be returned.
    """
    study_version = DB.get_study_version(
        study_uid=uid,
        study_version_number=study_version_number,
    )

    study_activities = DB.get_study_activities(
        study_uid=uid,
        sort_by=sort_by,
        sort_order=sort_order,
        page_size=page_size,
        page_number=page_number,
        study_version_number=study_version_number,
    )

    return PaginatedResponseWithStudyVersion.from_input(
        request=request,
        study_version=study_version,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        page_size=page_size,
        page_number=page_number,
        items=[
            models.StudyActivity.from_input(study_activity)
            for study_activity in study_activities
        ],
        query_param_names=["study_version_number"],
    )


# GET endpoint to retrieve a study's activity instances
@router.get(
    "/studies/{uid}/study-activity-instances",
    tags=["[V1] Studies"],
    dependencies=[security, rbac.STUDY_READ],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Item not found",
        },
    },
)
def get_study_activity_instances(
    request: Request,
    uid: Annotated[str, Path(description="Study UID")],
    sort_by: models.SortByStudyActivityInstances = models.SortByStudyActivityInstances.UID,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: Annotated[int, PAGE_SIZE_QUERY] = settings.page_size_100,
    page_number: Annotated[
        int, PAGE_NUMBER_QUERY
    ] = settings.default_page_number_consumer_api,
    study_version_number: Annotated[
        str | None,
        Query(
            description="Study Version Number",
            openapi_examples={"2.1": {"value": "2.1"}},
        ),
    ] = None,
) -> PaginatedResponseWithStudyVersion[models.StudyActivityInstance]:
    """
    Returns a paginated list of study activity instances, sorted by the specified sort criteria and order.

    If `study_version_number` query parameter is provided, study activity instances
    associated with the specified study version will be returned.
    Otherwise, activity instances for the latest study version will be returned.
    """
    study_version = DB.get_study_version(
        study_uid=uid,
        study_version_number=study_version_number,
    )

    study_activity_instances = DB.get_study_activity_instances(
        study_uid=uid,
        sort_by=sort_by,
        sort_order=sort_order,
        page_size=page_size,
        page_number=page_number,
        study_version_number=study_version_number,
    )

    return PaginatedResponseWithStudyVersion.from_input(
        request=request,
        study_version=study_version,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        page_size=page_size,
        page_number=page_number,
        items=[
            models.StudyActivityInstance.from_input(study_activity_instance)
            for study_activity_instance in study_activity_instances
        ],
        query_param_names=["study_version_number"],
    )


# GET endpoint to retrieve a study's detailed soa
@router.get(
    "/studies/{uid}/detailed-soa",
    tags=["[V1] Studies"],
    dependencies=[security, rbac.STUDY_READ],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Item not found",
        },
    },
)
def get_study_detailed_soa(
    request: Request,
    uid: Annotated[str, Path(description="Study UID")],
    sort_by: models.SortByStudyDetailedSoA = models.SortByStudyDetailedSoA.ACTIVITY_NAME,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: Annotated[int, PAGE_SIZE_QUERY] = settings.page_size_100,
    page_number: Annotated[
        int, PAGE_NUMBER_QUERY
    ] = settings.default_page_number_consumer_api,
    study_version_number: Annotated[
        str | None,
        Query(
            description="Study Version Number",
            openapi_examples={"2.1": {"value": "2.1"}},
        ),
    ] = None,
    include_unscheduled_activities: Annotated[
        bool,
        Query(
            description="If true, includes activities that are not scheduled to any visit.",
        ),
    ] = False,
) -> PaginatedResponseWithStudyVersion[models.StudyDetailedSoA]:
    """
    Returns a paginated list of detailed SoA items representing a point in the activities/visits matrix.
    SoA items are sorted by the specified sort criteria and order.

    If `study_version_number` query parameter is provided, detailed SoA
    associated with the specified study version will be returned.
    Otherwise, detailed SoA items for the latest study version will be returned.
    """
    study_version = DB.get_study_version(
        study_uid=uid,
        study_version_number=study_version_number,
    )

    study_detailed_soas = DB.get_study_detailed_soa(
        study_uid=uid,
        sort_by=sort_by,
        sort_order=sort_order,
        page_size=page_size,
        page_number=page_number,
        study_version_number=study_version_number,
        include_unscheduled_activities=include_unscheduled_activities,
    )

    return PaginatedResponseWithStudyVersion.from_input(
        request=request,
        study_version=study_version,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        page_size=page_size,
        page_number=page_number,
        items=[
            models.StudyDetailedSoA.from_input(study_detailed_soa)
            for study_detailed_soa in study_detailed_soas
        ],
        query_param_names=["study_version_number", "include_unscheduled_activities"],
    )


# GET endpoint to retrieve a study's operational soa
@router.get(
    "/studies/{uid}/operational-soa",
    tags=["[V1] Studies"],
    dependencies=[security, rbac.STUDY_READ],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Item not found",
        },
    },
)
def get_study_operational_soa(
    request: Request,
    uid: Annotated[str, Path(description="Study UID")],
    sort_by: models.SortByStudyOperationalSoA = models.SortByStudyOperationalSoA.ACTIVITY_NAME,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: Annotated[int, PAGE_SIZE_QUERY] = settings.page_size_100,
    page_number: Annotated[
        int, PAGE_NUMBER_QUERY
    ] = settings.default_page_number_consumer_api,
    study_version_number: Annotated[
        str | None,
        Query(
            description="Study Version Number",
            openapi_examples={"2.1": {"value": "2.1"}},
        ),
    ] = None,
    include_unscheduled_activities: Annotated[
        bool,
        Query(
            description="If true, includes activities that are not scheduled to any visit.",
        ),
    ] = False,
) -> PaginatedResponseWithStudyVersion[models.StudyOperationalSoA]:
    """
    Returns a paginated list of operational SoA items representing a point in the activities/visits matrix.
    SoA items are sorted by the specified sort criteria and order.

    If `study_version_number` query parameter is provided, operational SoA
    associated with the specified study version will be returned.
    Otherwise, operational SoA items for the latest study version will be returned.
    """
    study_version = DB.get_study_version(
        study_uid=uid,
        study_version_number=study_version_number,
    )

    study_operational_soas = DB.get_study_operational_soa(
        study_uid=uid,
        sort_by=sort_by,
        sort_order=sort_order,
        page_size=page_size,
        page_number=page_number,
        study_version_number=study_version_number,
        include_unscheduled_activities=include_unscheduled_activities,
    )

    return PaginatedResponseWithStudyVersion.from_input(
        request=request,
        study_version=study_version,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        page_size=page_size,
        page_number=page_number,
        items=[
            models.StudyOperationalSoA.from_input(study_operational_soa)
            for study_operational_soa in study_operational_soas
        ],
        query_param_names=["study_version_number", "include_unscheduled_activities"],
    )


# GET endpoint to retrieve a library of activities
@router.get(
    "/library/activities",
    tags=["[V1] Library"],
    dependencies=[security, rbac.LIBRARY_READ],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Item not found",
        },
    },
)
def get_library_activities(
    request: Request,
    sort_by: Annotated[
        models.SortByLibraryItem, Query()
    ] = models.SortByLibraryItem.NAME,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: Annotated[int, PAGE_SIZE_QUERY] = settings.page_size_100,
    page_number: Annotated[
        int, PAGE_NUMBER_QUERY
    ] = settings.default_page_number_consumer_api,
    library: models.Library | None = None,
    status: models.LibraryItemStatus | None = None,
) -> PaginatedResponse[models.LibraryActivity]:
    """
    Returns a paginated list of library activities, sorted by the specified sort field and order.

    Activities can be filtered by  `library` (_Sponsor, Requested_) and/or `status` (_Final, Draft, Retired_).
    """

    library_activities = DB.get_library_activities(
        sort_by=sort_by,
        sort_order=sort_order,
        page_size=page_size,
        page_number=page_number,
        library=library,
        status=status,
    )

    return PaginatedResponse.from_input(
        request=request,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        page_size=page_size,
        page_number=page_number,
        items=[
            models.LibraryActivity.from_input(library_activity)
            for library_activity in library_activities
        ],
        query_param_names=["status", "library"],
    )


# GET endpoint to retrieve a library of activity instances
@router.get(
    "/library/activity-instances",
    tags=["[V1] Library"],
    dependencies=[security, rbac.LIBRARY_READ],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Item not found",
        },
    },
)
def get_library_activity_instances(
    request: Request,
    sort_by: Annotated[
        models.SortByLibraryItem, Query()
    ] = models.SortByLibraryItem.NAME,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: Annotated[int, PAGE_SIZE_QUERY] = settings.page_size_100,
    page_number: Annotated[
        int, PAGE_NUMBER_QUERY
    ] = settings.default_page_number_consumer_api,
    library: models.Library | None = None,
    status: models.LibraryItemStatus | None = None,
    activity_uid: Annotated[
        str | None, Query(description="Filter by activity UID")
    ] = None,
) -> PaginatedResponse[models.LibraryActivityInstance]:
    """
    Returns a paginated list of library activity instances, sorted by the specified sort field and order.

    Activity instances can be filtered by:
      - **library**: Sponsor, Requested
      - **status**: Final, Draft, Retired
      - **activity_uid**: case-sensitive match, for example 'Activity_000251'
    """

    library_activity_instances = DB.get_library_activity_instances(
        sort_by=sort_by,
        sort_order=sort_order,
        page_size=page_size,
        page_number=page_number,
        library=library,
        status=status,
        activity_uid=activity_uid,
    )

    return PaginatedResponse.from_input(
        request=request,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        page_size=page_size,
        page_number=page_number,
        items=[
            models.LibraryActivityInstance.from_input(library_activity_instance)
            for library_activity_instance in library_activity_instances
        ],
        query_param_names=["status", "library", "activity_uid"],
    )


# GET endpoint to retrieve a library of activity item classes (regular and NSVs)
@router.get(
    "/library/activity-item-classes",
    tags=["[V1] Library"],
    dependencies=[security, rbac.LIBRARY_READ],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Item not found",
        },
    },
)
def get_library_activity_item_classes(
    request: Request,
    sort_by: Annotated[
        models.SortByLibraryActivityItemClass, Query()
    ] = models.SortByLibraryActivityItemClass.NAME,
    sort_order: models.SortOrder = models.SortOrder.ASC,
    page_size: Annotated[int, PAGE_SIZE_QUERY] = settings.page_size_100,
    page_number: Annotated[
        int, PAGE_NUMBER_QUERY
    ] = settings.default_page_number_consumer_api,
    library: models.Library | None = None,
    status: models.LibraryItemStatus | None = None,
    is_nsv: Annotated[
        bool | None,
        Query(
            description=(
                "Filter by Non-Standard Variable flag. "
                "When `true`, only Non-Standard Variables are returned. "
                "When `false`, only regular Activity Item Classes (i.e. NOT NSVs) are returned. "
                "When omitted, both regular Activity Item Classes and Non-Standard Variables are returned."
            )
        ),
    ] = None,
) -> PaginatedResponse[models.LibraryActivityItemClassFull]:
    """
    Returns a paginated list of Activity Item Classes, sorted by the specified
    sort field and order.

    Activity Item Classes can be filtered by:
      - **library**: Sponsor, Requested
      - **status**: Final, Draft, Retired
      - **is_nsv**: Filter by the Non-Standard Variable flag.
        - `true` returns only Non-Standard Variables (NSVs).
        - `false` returns only regular Activity Item Classes.
        - omitted returns both.

    Each item exposes the regular Activity Item Class properties (uid, name,
    library, definition, role, data type, valid codelists, linked Activity
    Instance Classes, version, status, ...). When the Activity Item Class is
    a Non-Standard Variable, the nested `non_standard_variable` field
    contains the NSV-specific information (code, length, derivation rule,
    origin terms, ...). For regular Activity Item Classes,
    `non_standard_variable` is `null`.
    """
    library_activity_item_classes = DB.get_library_activity_item_classes(
        sort_by=sort_by,
        sort_order=sort_order,
        page_size=page_size,
        page_number=page_number,
        library=library,
        status=status,
        is_nsv=is_nsv,
    )

    return PaginatedResponse.from_input(
        request=request,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
        page_size=page_size,
        page_number=page_number,
        items=[
            models.LibraryActivityItemClassFull.from_input(item)
            for item in library_activity_item_classes
        ],
        query_param_names=["status", "library", "is_nsv"],
    )


# GET endpoint to retrieve a study's soa in papillons required structure
@router.get(
    "/papillons/soa",
    tags=["[V1] Papillons"],
    dependencies=[security, rbac.STUDY_READ],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Item not found",
        },
    },
)
def get_papillons_soa(
    project: Annotated[str, Query(description="Project")],
    study_number: Annotated[str, Query(description="Study Number")],
    subpart: Annotated[
        str | None,
        Query(
            description="Study Subpart Identifier, for example `SAD, MAD, EXT, etc..`"
        ),
    ] = None,
    study_version_number: Annotated[
        str | None,
        Query(
            description="Study Version Number, for example `2.1`. "
            "Omit together with datetime to use the latest released study value."
        ),
    ] = None,
    date_time: Annotated[
        str | None,
        Query(
            alias="datetime",
            description="If specified, study data with latest released version of specified datetime is returned. "
            "Format: YYYY-MM-DDThh:mm:ssZ. Omit together with study_version_number to use the latest released study value.",
        ),
    ] = None,
) -> models.PapillonsSoA:
    """
    Returns SoA in the Papillons shape.

    If both ``study_version_number`` and ``datetime`` are omitted, the latest
    released study value is used.
    """
    ValidationException.raise_if(
        study_version_number is not None and date_time is not None,
        msg="Please specify either version or datetime, not both.",
    )
    papilons_soa_res = DB.get_papillons_soa(
        project=project,
        study_number=study_number,
        subpart=subpart,
        date_time=date_time,
        study_version_number=study_version_number,
    )

    return models.PapillonsSoA.from_input(papilons_soa_res)


# GET endpoint to export SEMTCDT Non-Standard Variables in Papillons SDTM_QNAM shape
@router.get(
    "/papillons/non-standard-variables",
    tags=["[V1] Papillons"],
    dependencies=[security, rbac.LIBRARY_READ],
    status_code=200,
    responses={
        200: {
            "content": {"text/csv": {}},
            "description": "CSV of SEMTCDT Non-Standard Variables in SDTM_QNAM shape",
        },
    },
)
def get_papillons_non_standard_variables() -> Response:
    """
    Returns every Final Non-Standard Variable whose Data Type belongs to the
    SEMTCDT (Semantic Data Type) codelist, as a full, unpaged CSV using the
    same columns as the MMA SDTM_QNAM import format.

    The `sdtm_qnam_data_type` column holds the NSVXMLDT (NSV XML Data Type)
    equivalent of the variable's semantic data type, resolved by walking the
    real `IS_SPECIALIZATION_OF` relationship up to the nearest
    NSVXMLDT-tagged ancestor - not a hardcoded table, so it stays correct as
    the term hierarchy evolves.
    """
    rows = DB.get_papillons_non_standard_variables()

    keys = [
        "cd_list_id",
        "cd_val",
        "cd_val_lb",
        "cd_val_short_lb",
        "cd_val_desc",
        "sdtm_qnam_data_type",
        "sdtm_qnam_length",
        "sdtm_qnam_ct",
        "sdtm_qnam_algorithm",
        "sdtm_qnam_multiple",
        "sdtm_qnam_qorig",
        "cd_val_std",
        "cd_list_val_status",
    ]

    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer, fieldnames=keys, delimiter="|", quoting=csv.QUOTE_MINIMAL
    )
    writer.writeheader()
    for row in rows:
        qorig = _MMA_QORIG_REVERSE_MAP.get(
            (row.get("origin_type_name") or "", row.get("origin_source_name") or ""),
            "",
        )
        writer.writerow(
            {
                "cd_list_id": "SDTM_QNAM",
                "cd_val": row.get("variable_name") or "",
                "cd_val_lb": row.get("label") or "",
                "cd_val_short_lb": row.get("label") or "",
                "cd_val_desc": row.get("definition") or "",
                "sdtm_qnam_data_type": row.get("nsv_xml_data_type") or "",
                "sdtm_qnam_length": (
                    "" if row.get("length") is None else row.get("length")
                ),
                "sdtm_qnam_ct": row.get("codelist_submission_value") or "",
                "sdtm_qnam_algorithm": row.get("algorithm") or "",
                "sdtm_qnam_multiple": "Y" if row.get("is_multiple") else "N",
                "sdtm_qnam_qorig": qorig,
                "cd_val_std": "Y" if row.get("is_cdisc_defined") else "N",
                "cd_list_val_status": "A",
            }
        )

    return Response(content=buffer.getvalue(), media_type="text/csv")


# GET endpoint to map a single SEMTCDT term to its NSVXMLDT equivalent
@router.get(
    "/papillons/data-type-mapping/{semtcdt_term}",
    tags=["[V1] Papillons"],
    dependencies=[security, rbac.LIBRARY_READ],
    status_code=200,
    response_model=models.PapillonsNsvXmlDataTypeMapping,
)
def get_papillons_data_type_mapping(
    semtcdt_term: Annotated[
        str,
        Path(
            description="Submission value of a SEMTCDT (Semantic Data Type) term, e.g. `code`, `ctTerm`, `text`"
        ),
    ],
) -> models.PapillonsNsvXmlDataTypeMapping:
    """
    Resolves a single SEMTCDT term to its NSVXMLDT (NSV XML Data Type)
    equivalent, using the same live `IS_SPECIALIZATION_OF` traversal as
    `GET /papillons/non-standard-variables`'s `sdtm_qnam_data_type` column.
    """
    nsv_xml_term = DB.get_nsv_xml_data_type_for_semtcdt_term(semtcdt_term)
    return models.PapillonsNsvXmlDataTypeMapping(
        semtcdt_term=semtcdt_term, nsv_xml_term=nsv_xml_term
    )


# GET endpoint to retrieve study audit trail
@router.get(
    "/studies/audit-trail",
    tags=["[V1] Audit trail"],
    dependencies=[security, rbac.STUDY_READ],
    status_code=200,
    responses={
        200: {
            "content": {"text/csv": {}},
            "description": "CSV of study audit trail data",
        },
    },
)
# pylint: disable=dangerous-default-value
def get_studies_audit_trail(
    from_ts: Annotated[
        datetime,
        Query(
            description="Start timestamp in ISO format with timezone, e.g. 2024-01-01T00:00:00Z"
        ),
    ] = datetime.fromisoformat("2024-01-01T00:00:00Z"),
    to_ts: Annotated[
        datetime,
        Query(
            description="End timestamp in ISO format with timezone, e.g. 2024-01-05T00:00:00Z"
        ),
    ] = datetime.fromisoformat("2024-01-05T00:00:00Z"),
    study_id: Annotated[
        str | None,
        Query(
            description="Filter by study ID (case-insensitive partial match), for example `XX1234-5678`."
        ),
    ] = None,
    entity_type: Annotated[
        models.StudyAuditTrailEntity | None,
        Query(description="Filter by entity type, for example `StudyActivity`."),
    ] = None,
    exclude_study_ids: Annotated[
        list[str] | None,
        Query(
            description="List of study IDs to exclude (case-insensitive partial match), for example `CDISC DEV`."
        ),
    ] = ["CDISC DEV"],
    page_number: Annotated[
        int, PAGE_NUMBER_QUERY
    ] = settings.default_page_number_consumer_api,
) -> Response:
    """
    Returns study audit trail entries between `from_ts` timestamp (including) and `to_ts` timestamp (excluding).

    The audit trail is returned in CSV format with the following columns:
      - **ts**: Timestamp of the action
      - **study_uid**: Study UID
      - **study_id**: Study ID
      - **action**: Action performed (Create, Edit, Delete)
      - **entity_uid**: UID of the entity affected by the action
      - **entity_type**: Type (i.e node labels) of the entity affected by the action (*StudyVisit*, *StudyActivity*, etc..). Multiple labels are separated by '**|**' character.
      - **changed_properties**: List of properties that were changed during the Edit action
      - **author**: Hashed (MD5) value of the ID of a user that performed the action

    Audit trail can be filtered by:
      - `study_id` - returns study audit trail entries for the specified study ID (case-insensitive partial match)
      - `entity_type` - returns study audit trail entries for the specified entity type (e.g. *StudyActivity*)
      - `exclude_study_ids` - returns audit trail without the specified study IDs (case-insensitive partial match)

    Note: the maximum number of rows returned is limited to 10.000.
    """

    audit_trail = DB.get_studies_audit_trail(
        from_ts=from_ts,
        to_ts=to_ts,
        study_id=study_id,
        entity_type=entity_type,
        exclude_study_ids=exclude_study_ids,
        page_number=page_number,
    )

    # Convert audit trail to CSV format
    keys = [
        "ts",
        "study_uid",
        "study_id",
        "action",
        "entity_uid",
        "entity_type",
        "changed_properties",
        "author",
    ]
    csv_output = ",".join(keys) + "\n"
    for entry in audit_trail:
        # None values are returned as empty string
        # lists are returned as val1|val2
        for key in keys:
            if entry[key] is None:
                entry[key] = ""
            elif isinstance(entry[key], list):
                entry[key] = "|".join(entry[key])

        csv_output += ",".join(str(entry[key]) for key in keys)
        csv_output += "\n"

    return Response(content=csv_output, media_type="text/csv")


# POST endpoint to create a Schedule of Activities
@router.post(
    "/studies/{uid}/soa",
    tags=["[V1] Studies"],
    dependencies=[security, rbac.STUDY_WRITE],
    status_code=201,
    responses={
        201: {"description": "Schedule of Activities created successfully"},
        400: {"model": ErrorResponse, "description": "Bad Request"},
        404: {
            "model": ErrorResponse,
            "description": "Item not found",
        },
    },
)
def create_soa(
    uid: str,
    soa_input: Annotated[
        models.SoACreateInput,
        Body(
            openapi_examples={
                "example": {
                    "summary": "Complete SoA Example",
                    "value": api_specs.EXAMPLE_POST_SOA_REQUEST,
                }
            }
        ),
    ],
) -> models.SoACreateResponse:
    """
    Creates a new Schedule of Activities (SoA) with epochs, visits, and activities.

     - Any existing study activities, visits, and epochs for the study will be
     soft-deleted and replaced with the resources described in the request body.
     Nothing is updated in place — every successful call returns a fresh set of UIDs,
     and the prior SoA entities remain in the study's audit trail.

     - Requests to change SoA on studies in LOCKED state are rejected (HTTP 400).

    This endpoint accepts a complete study activity schedule including:
    - **Epochs**: Study phases (Screening, Treatment, Follow-up, etc.)

    - **Visits**: Scheduled or unscheduled visits with timings and windows

    - **Activities**: Study activities linked to specific visits

    <br/>
    Returns a confirmation with created resource identifiers.
    <br/><br/>

    Valid values for payload fields:

    - **epoch.subtype**: Allowed values are retrieved from `GET /v1/library/ct/codelist-terms?codelist_submission_value=EPOCHSTP` endpoint (**term_uid** field)

    - **visit.type**: Allowed values are retrieved from `GET /v1/library/ct/codelist-terms?codelist_submission_value=TIMELB` endpoint (**term_uid** field)

    - **visit.contact_mode**: Allowed values are retrieved from `GET /v1/library/ct/codelist-terms?codelist_submission_value=VISCNTMD` endpoint (**term_uid** field)

    - **visit.window.unit_uid** and **visit.timing.unit_uid**: Allowed values are retrieved from `GET /v1/library/unit-definitions?subset=Study Time` endpoint (**uid** field)

    - **visit.timing.timing_reference_uid**: Allowed values are retrieved from `GET /v1/library/ct/codelist-terms?codelist_submission_value=TIMEREF` endpoint (**term_uid** field)

    - **activity.soa_group_uid**: Allowed values are retrieved from `GET /v1/library/ct/codelist-terms?codelist_submission_value=FLWCRTGRP` endpoint (**term_uid** field)

    - **activity.activity_uid**: Allowed values are retrieved from `GET /v1/library/activities?status=Final&library=Sponsor` endpoint (**uid** field)

    - **activity.activity_group_uid**: Allowed values are retrieved from `GET /v1/library/activities?status=Final&library=Sponsor` endpoint (**groupings.activity_group_uid** field)

    - **activity.activity_subgroup_uid**: Allowed values are retrieved from `GET /v1/library/activities?status=Final&library=Sponsor` endpoint (**groupings.activity_subgroup_uid** field)
    """
    return SoAService().create_soa(
        study_uid=uid,
        soa_input=soa_input,
    )


# GET endpoint to retrieve a list of projects
@router.get(
    "/library/projects",
    tags=["[V1] Library"],
    dependencies=[security, rbac.LIBRARY_READ],
    status_code=200,
)
def get_projects(
    request: Request,
    page_size: Annotated[int, PAGE_SIZE_QUERY] = settings.page_size_100,
    page_number: Annotated[
        int, PAGE_NUMBER_QUERY
    ] = settings.default_page_number_consumer_api,
) -> PaginatedResponse[models.Project]:
    """
    Returns a paginated list of projects, sorted by ascending project ID.

    The returned `id` values are the ones accepted as `project_id` by the
    `POST /v1/studies` endpoint.
    """
    projects = DB.get_projects(
        page_size=page_size,
        page_number=page_number,
    )

    return PaginatedResponse.from_input(
        request=request,
        sort_by="id",
        sort_order=models.SortOrder.ASC.value,
        page_size=page_size,
        page_number=page_number,
        items=[models.Project.from_input(project) for project in projects],
    )


# GET endpoint to retrieve a list of codelists
@router.get(
    "/library/ct/codelists",
    tags=["[V1] Library"],
    dependencies=[security, rbac.LIBRARY_READ],
    status_code=200,
)
def get_codelists(
    request: Request,
    page_size: Annotated[int, PAGE_SIZE_QUERY] = settings.page_size_100,
    page_number: Annotated[
        int, PAGE_NUMBER_QUERY
    ] = settings.default_page_number_consumer_api,
    name_status: models.LibraryItemStatus | None = models.LibraryItemStatus.FINAL,
    attributes_status: models.LibraryItemStatus | None = models.LibraryItemStatus.FINAL,
) -> PaginatedResponse[models.Codelist]:
    """
    Returns a paginated list of CT codelists, sorted by ascending name.

    Codelists can be filtered by `name_status` and `attributes_status` (_Final, Draft, Retired_). Both default to _Final_.
    """
    codelists = DB.get_codelists(
        page_size=page_size,
        page_number=page_number,
        name_status=name_status,
        attributes_status=attributes_status,
    )

    return PaginatedResponse.from_input(
        request=request,
        sort_by=None,
        sort_order=None,
        page_size=page_size,
        page_number=page_number,
        items=[models.Codelist.from_input(codelist) for codelist in codelists],
        query_param_names=["name_status", "attributes_status"],
    )


# GET endpoint /library/ct/codelist-terms that returns list of codelist terms, optionally filtered by codelist submission value and/or codelist UID
@router.get(
    "/library/ct/codelist-terms",
    tags=["[V1] Library"],
    dependencies=[security, rbac.LIBRARY_READ],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Item not found",
        },
    },
)
def get_codelist_terms(
    request: Request,
    codelist_submission_value: Annotated[
        str | None,
        Query(
            description="Codelist submission value to filter by, for example `TIMELB`, `TIMEREF`, `VISCNTMD`, `FLWCRTGRP`, `EPOCHSTP` etc."
        ),
    ] = None,
    codelist_uid: Annotated[
        str | None,
        Query(description="Codelist UID to filter by."),
    ] = None,
    page_size: Annotated[int, PAGE_SIZE_QUERY] = settings.page_size_100,
    page_number: Annotated[
        int, PAGE_NUMBER_QUERY
    ] = settings.default_page_number_consumer_api,
    name_status: models.LibraryItemStatus | None = models.LibraryItemStatus.FINAL,
    attributes_status: models.LibraryItemStatus | None = models.LibraryItemStatus.FINAL,
) -> PaginatedResponse[models.CodelistTerm]:
    """
    Returns a paginated list of CT codelist terms, sorted by ascending by codelist UID, then term UID.

    If neither `codelist_submission_value` nor `codelist_uid` is provided, all terms are returned.
    If either is provided, terms are filtered accordingly.

    Terms can also be filtered by `name_status` and `attributes_status` (_Final, Draft, Retired_). Both default to _Final_.
    """
    codelist_terms = DB.get_codelist_terms(
        codelist_submission_value=codelist_submission_value,
        codelist_uid=codelist_uid,
        page_size=page_size,
        page_number=page_number,
        name_status=name_status,
        attributes_status=attributes_status,
    )

    return PaginatedResponse.from_input(
        request=request,
        sort_by=None,
        sort_order=None,
        page_size=page_size,
        page_number=page_number,
        items=[
            models.CodelistTerm.from_input(codelist_term)
            for codelist_term in codelist_terms
        ],
        query_param_names=[
            "codelist_submission_value",
            "codelist_uid",
            "name_status",
            "attributes_status",
        ],
    )


# GET endpoint /library/unit-definitions?subset=XYZ that returns list of unit definitions for the specified subset
@router.get(
    "/library/unit-definitions",
    tags=["[V1] Library"],
    dependencies=[security, rbac.LIBRARY_READ],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Item not found",
        },
    },
)
def get_unit_definitions(
    request: Request,
    subset: Annotated[
        str | None,
        Query(
            description="Unit definition subset to filter by, for example `Study Time`. If omitted, all unit definitions are returned."
        ),
    ] = None,
    page_size: Annotated[int, PAGE_SIZE_QUERY] = settings.page_size_100,
    page_number: Annotated[
        int, PAGE_NUMBER_QUERY
    ] = settings.default_page_number_consumer_api,
    status: models.LibraryItemStatus | None = models.LibraryItemStatus.FINAL,
) -> PaginatedResponse[models.UnitDefinition]:
    """
    Returns a paginated list of unit definitions, sorted by ascending name.

    Unit definitions can optionally be filtered by `subset` name (e.g. `Study Time`).
    Unit definitions can be filtered by `status` (_Final, Draft, Retired_). Defaults to _Final_.
    """
    unit_definitions = DB.get_unit_definitions(
        subset=subset,
        page_size=page_size,
        page_number=page_number,
        status=status,
    )

    return PaginatedResponse.from_input(
        request=request,
        sort_by=None,
        sort_order=None,
        page_size=page_size,
        page_number=page_number,
        items=[
            models.UnitDefinition.from_input(unit_definition)
            for unit_definition in unit_definitions
        ],
        query_param_names=["subset", "status"],
    )
