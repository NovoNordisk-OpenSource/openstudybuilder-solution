"""Endpoints for previewing and running the import into the OSB database."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Path, status

from common.auth import rbac
from common.auth.dependencies import security
from common.auth.user import user
from standards_import.common import NOT_FOUND_RESPONSES
from standards_import.models.imports import ImportPreview, ImportRequest
from standards_import.models.jobs import Job
from standards_import.services import import_service

router = APIRouter(prefix="/effective-dates", tags=["Import"])

EFFECTIVE_DATE_PATH = Path(description="Effective date of the release, as `YYYY-MM-DD`")


@router.get(
    "/{effective_date}/preview",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="See what importing this release would change",
    description="""Compares the release against what the OSB database currently holds and
reports what the import would create, what it would version, and what it would leave
alone. Writes nothing.

`can_import` and `blockers` say whether the import would be accepted and, if not, why —
so this is also the way to check a release is ready without attempting it.""",
)
def preview_import(
    effective_date: Annotated[date, EFFECTIVE_DATE_PATH],
) -> ImportPreview:
    return import_service.preview(effective_date)


@router.post(
    "/{effective_date}/import",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_202_ACCEPTED,
    responses=NOT_FOUND_RESPONSES,
    summary="Import this release into the OSB database",
    description="""Applies the release and returns immediately with a job to follow.

The import is **append-only at the head**: it extends what OSB already holds with one
newer release. A release older than the newest package already there is refused, because
loading it would mean rewriting history — that is the bootstrap import's job, run once
per environment.

Refused as well if anything is still open for review, if the release has already been
imported, or if a job for it is already running. Pass `expected_catalogues` to assert the
release holds exactly the catalogues you think it does: a half-uploaded release would
otherwise import quietly, and its missing catalogues could never be added afterwards.

Concepts whose values are unchanged get no new version — only what CDISC actually
changed is versioned.""",
)
def start_import(
    effective_date: Annotated[date, EFFECTIVE_DATE_PATH],
    request: ImportRequest,
    background_tasks: BackgroundTasks,
) -> Job:
    job = import_service.start_import(effective_date, request)
    background_tasks.add_task(
        import_service.run_import, job.uid, effective_date, user().id()
    )
    return job
