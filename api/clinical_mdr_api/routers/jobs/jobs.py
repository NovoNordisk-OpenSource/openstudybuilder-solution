from typing import Annotated

from fastapi import APIRouter, Path

from clinical_mdr_api.models.jobs.job import JobResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.jobs.job_service import JobService
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings

# Endpoints prefixed with "/jobs"
router = APIRouter()

JobUID = Path(description="The unique id of the Job.")


@router.get(
    "",
    dependencies=[security, rbac.ANY],
    summary="Returns all background jobs.",
    description=(
        "Returns a paginated list of background jobs. "
        "Non-admin callers only see jobs they started themselves; callers with "
        "the `Admin.Read` role see every user's jobs. "
        "The `response` field is omitted from list items to keep payloads small — "
        "fetch a single job via `GET /jobs/{job_uid}` to retrieve it."
    ),
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
    },
)
def list_jobs(
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
) -> CustomPage[JobResponse]:
    return JobService().list_jobs(
        page_number=page_number,
        page_size=page_size,
        sort_by=sort_by,
    )


@router.get(
    "/{job_uid}",
    dependencies=[security, rbac.ANY],
    summary="Returns the job identified by 'job_uid', including the captured response and log.",
    description=(
        "Returns the specified job, its full response payload, and its captured log. "
        "Non-admin callers may only retrieve jobs they started themselves; a request "
        "for another user's job returns 404 (identical to a missing uid) rather than "
        "403, to avoid leaking the existence of jobs the caller cannot read. "
        "Callers with the `Admin.Read` role may retrieve any user's job."
    ),
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_job(job_uid: Annotated[str, JobUID]) -> JobResponse:
    return JobService().get_job(job_uid)
