"""Endpoints for assessing what a release means for sponsor-defined content."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Path, Query, status

from common.auth import rbac
from common.auth.dependencies import security
from standards_import.common import NOT_FOUND_RESPONSES
from standards_import.models.jobs import Job
from standards_import.models.packages import SponsorImpactSummary
from standards_import.services import sponsor_impact_service

router = APIRouter(prefix="/effective-dates", tags=["Sponsor impact"])

EFFECTIVE_DATE_PATH = Path(description="Effective date of the release, as `YYYY-MM-DD`")


@router.post(
    "/{effective_date}/sponsor-impact",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_202_ACCEPTED,
    responses=NOT_FOUND_RESPONSES,
    summary="Work out what this release would collide with in the MDR database",
    description="""Compares the release against the codelists and terms the sponsor has
defined, and raises a review item for each collision. Writes nothing to the MDR database.
Returns immediately with a job to follow; the release's status is `ASSESSING` until it
finishes. `GET /effective-dates/{effective_date}/sponsor-impact` reads the outcome once
it has — or `GET /jobs/{uid}` to follow the job itself.

Three things are reported: a term this release adds to a codelist that a sponsor-defined
term in the same codelist already covers, a codelist it introduces that a sponsor codelist
already covers, and a term whose sponsor name is no longer what the naming rules would
produce now that CDISC has changed it.

The findings join the same review queue as CDISC inconsistencies and are settled through
`POST /inconsistencies/{uid}/resolution`. Most are settled automatically by the shipped
rules; an **exact** collision on a term is not, because that is the one that breaks a
uniqueness rule the main API enforces, and somebody has to say what to do about it — even
if what they say is to keep both.

Run this after the preview and before the import. It needs an analysed release with
nothing else open, because what a term collides with depends on the name the review items
settled for it. Re-running is safe: decisions already made are kept and reattached, and
are discarded only if the values they were made about have changed. Refused while an
import, an analysis, or another assessment of the same release is already running.""",
)
def assess_sponsor_impact(
    effective_date: Annotated[date, EFFECTIVE_DATE_PATH],
    background_tasks: BackgroundTasks,
    refresh: Annotated[
        bool,
        Query(
            description="Put every question to the language model again instead of "
            "reusing the answers already on file. Not normally needed: an answer is only "
            "reused where the question is identical, so a codelist whose settled names "
            "have moved is asked again on its own. This is for when the answers rather "
            "than the inputs have changed — a new model, or a provider pointed elsewhere."
        ),
    ] = False,
) -> Job:
    job = sponsor_impact_service.start_assessment(effective_date)
    background_tasks.add_task(
        sponsor_impact_service.run_assessment, job.uid, effective_date, refresh
    )
    return job


@router.get(
    "/{effective_date}/sponsor-impact",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="What the last sponsor impact assessment of this release found",
    description="""Reports the findings of the last assessment, without running one.

`404` until a release has been assessed at all — which is a different answer from an
assessment that found nothing, and the two must not be confused. Check `assessed_at` on
`GET /effective-dates/{effective_date}` against its `analyzed_at` to see whether what this
returns still describes the release.""",
)
def get_sponsor_impact(
    effective_date: Annotated[date, EFFECTIVE_DATE_PATH],
) -> SponsorImpactSummary:
    return sponsor_impact_service.get_summary(effective_date)
