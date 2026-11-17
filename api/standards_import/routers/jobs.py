"""Endpoints for following background jobs: import, analysis, sponsor impact
assessment, and discovery."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from common.auth import rbac
from common.auth.dependencies import security
from standards_import.common import ERROR_RESPONSES, NOT_FOUND_RESPONSES
from standards_import.models.jobs import Job, JobKind
from standards_import.services import job_service

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=ERROR_RESPONSES,
    summary="List jobs, newest first",
)
def get_jobs(
    effective_date: Annotated[
        date | None,
        Query(description="Only jobs for this release. DISCOVERY jobs never match"),
    ] = None,
    kind: Annotated[JobKind | None, Query(description="Only jobs of this kind")] = None,
) -> list[Job]:
    return job_service.list_jobs(effective_date, kind)


@router.get(
    "/{uid}",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="Get one job",
    description="""While a job is `RUNNING` its `stats` are empty; they are filled in
when it finishes. A `FAILED` job carries the error, and its release (where it has one —
`DISCOVERY` does not) goes back to a usable status so the step can be run again; every
kind is idempotent, so a repeat run picks up rather than duplicating.""",
)
def get_job(uid: Annotated[str, Path(description="Uid of the job")]) -> Job:
    return job_service.get_job(uid)
