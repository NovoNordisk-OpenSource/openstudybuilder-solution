"""Endpoints for inspecting and analysing one CDISC release."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Path, status

from common.auth import rbac
from common.auth.dependencies import security
from standards_import.common import NOT_FOUND_RESPONSES
from standards_import.models.jobs import Job
from standards_import.models.packages import AnalysisSummary, EffectiveDateSummary
from standards_import.services import analysis_service, staging_service

router = APIRouter(prefix="/effective-dates", tags=["Effective dates"])

EFFECTIVE_DATE_PATH = Path(description="Effective date of the release, as `YYYY-MM-DD`")


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="List the CDISC releases held in staging",
)
def get_effective_dates() -> list[EffectiveDateSummary]:
    return staging_service.get_effective_dates()


@router.get(
    "/{effective_date}",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="Get one CDISC release",
)
def get_effective_date(
    effective_date: Annotated[date, EFFECTIVE_DATE_PATH],
) -> EffectiveDateSummary:
    return staging_service.get_effective_date(effective_date)


@router.post(
    "/{effective_date}/analysis",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_202_ACCEPTED,
    responses=NOT_FOUND_RESPONSES,
    summary="Group and check one CDISC release",
    description="""Groups the staged catalogue files of this effective date by concept id
and raises a review item wherever the catalogues disagree. Returns immediately with a
job to follow; the release's status is `ANALYZING` until it finishes, then `ANALYZED`
or `BLOCKED`. `GET /effective-dates/{effective_date}/analysis` reads the outcome once
it has — or `GET /jobs/{uid}` to follow the job itself.

Call this once every file of the release has been uploaded — a release analysed while
files are still missing will be grouped against an incomplete set of catalogues.

Re-running is safe and is how you re-check after resolving review items: earlier findings
for this effective date are discarded and derived again from the staged files. Refused
while an import, another analysis, or a sponsor impact assessment of the same release is
already running.

Nothing is written to the MDR database here.""",
)
def analyse_effective_date(
    effective_date: Annotated[date, EFFECTIVE_DATE_PATH],
    background_tasks: BackgroundTasks,
) -> Job:
    job = analysis_service.start_analysis(effective_date)
    background_tasks.add_task(analysis_service.run_analysis, job.uid, effective_date)
    return job


@router.get(
    "/{effective_date}/analysis",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="What the last analysis of this release found",
    description="""Reports the outcome of the last analysis, without running one.

`404` until a release has been analysed at all — which is a different answer from an
analysis that found nothing to disagree about, and the two must not be confused.""",
)
def get_analysis(
    effective_date: Annotated[date, EFFECTIVE_DATE_PATH],
) -> AnalysisSummary:
    return analysis_service.get_summary(effective_date)
