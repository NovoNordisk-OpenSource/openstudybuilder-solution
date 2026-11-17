"""Reading jobs, and clearing ones a dead process left behind.

Starting and running a job is each kind's own business — see `import_service.start_import`,
`analysis_service.start_analysis`, `sponsor_impact_service.start_assessment`, and
`staging_service.start_discovery`, each paired with a `run_*` that does the real work in
the background. This module is what every kind then shares: `GET /jobs`, and the startup
sweep for jobs a process died in the middle of.
"""

import json
import logging
from datetime import date
from typing import Any

from common.exceptions import NotFoundException
from standards_import.config import settings
from standards_import.models.jobs import Job, JobKind, JobStatus
from standards_import.repositories import job_repository
from standards_import.repositories.staging_db import staging_session, to_native

log = logging.getLogger(__name__)


def list_jobs(
    effective_date: date | None = None, kind: JobKind | None = None
) -> list[Job]:
    with staging_session() as session:
        records = job_repository.get_jobs(
            session,
            effective_date.isoformat() if effective_date else None,
            kind.value if kind else None,
        )
    return [job_to_model(record) for record in records]


def get_job(uid: str) -> Job:
    with staging_session() as session:
        record = job_repository.find_job(session, uid)
        if record is None:
            raise NotFoundException(msg=f"No job with uid '{uid}'.")
    return job_to_model(record)


def fail_abandoned_jobs() -> list[dict[str, Any]]:
    """Clears jobs left RUNNING by a process that stopped. Called once at startup."""

    with staging_session() as session:
        closed = job_repository.fail_abandoned_jobs(
            session, settings.job_stale_after_seconds
        )
    if closed:
        log.warning(
            "Failed %s abandoned job(s) at startup: %s. Their releases are back to a "
            "usable status and the step can be run again.",
            len(closed),
            ", ".join(f"{job['kind']}:{job['uid']}" for job in closed),
        )
    return closed


def job_to_model(record: dict[str, Any]) -> Job:
    return Job(
        uid=record["uid"],
        kind=JobKind(record["kind"]),
        effective_date=record.get("effective_date"),
        status=JobStatus(record["status"]),
        started_at=to_native(record["started_at"]),
        finished_at=to_native(record.get("finished_at")),
        author_id=record["author_id"],
        stats=json.loads(record["stats"]) if record.get("stats") else None,
        error=record.get("error"),
    )
