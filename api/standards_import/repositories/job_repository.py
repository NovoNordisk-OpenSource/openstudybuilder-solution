"""Job records for every long-running step: import, analysis, sponsor impact
assessment, and discovery — kept in staging alongside the release a job belongs to.

`DISCOVERY` is the one kind with no release to attach to: it looks across every
catalogue before it knows what it will find. Its jobs use the `_global_job` variants
below, which touch no `EffectiveDateImport` at all.

What a job's completion means for its release is decided once, at `start_job` time, not
re-derived at `finish_job` time or guessed at recovery time. `status_on_success` and
`status_on_failure` are captured on the job node itself: `import`'s job sets both to a
fixed target (`IMPORTED`/`READY`); `analysis`'s sets only `status_on_failure`
(`FILES_STAGED`) because its own work already leaves the release ANALYZED or BLOCKED on
success; `sponsor_impact`'s `status_on_failure` is whatever the release's status was
before the job started, since assessment only adds findings and invalidates nothing.
Storing the target rather than recomputing it is what lets `fail_abandoned_jobs` recover
any kind uniformly, with no per-kind branching, even from a process that never ran the
job that started it.
"""

import json
import logging
from typing import Any

from standards_import.repositories.staging_db import StagingSession, run_query

log = logging.getLogger(__name__)

JOB_RETURN = """
    job.uid AS uid,
    job.kind AS kind,
    job.effective_date AS effective_date,
    job.status AS status,
    job.started_at AS started_at,
    job.finished_at AS finished_at,
    job.author_id AS author_id,
    job.stats AS stats,
    job.error AS error
"""


def start_job(
    session: StagingSession,
    uid: str,
    kind: str,
    effective_date: str,
    author_id: str,
    status_while_running: str,
    status_on_success: str | None,
    status_on_failure: str | None,
) -> dict[str, Any] | None:
    """Creates a job attached to its release, and marks the release busy with it.

    One transaction for both: a caller must never observe a `Job` existing with its
    release not yet marked busy, or vice versa. `status_on_success`/`status_on_failure`
    are stored on the job now so `finish_job` and `fail_abandoned_jobs` need not know
    which kind of job they are closing.
    """

    records = run_query(
        session,
        f"""
        MERGE (lock:JobRunLock:CDISCStaging {{scope: $effective_date}})
        ON CREATE SET lock.job_uid = $uid,
                      lock.kind = $kind,
                      lock.effective_date = $effective_date,
                      lock.status_while_running = $status_while_running,
                      lock.status_on_success = $status_on_success,
                      lock.status_on_failure = $status_on_failure
        WITH lock
        WHERE lock.job_uid = $uid
        MATCH (import:EffectiveDateImport {{effective_date: $effective_date}})
        CREATE (job:StagingJob:CDISCStaging {{
            uid: $uid,
            kind: $kind,
            effective_date: $effective_date,
            status: 'RUNNING',
            started_at: datetime(),
            author_id: $author_id,
            status_while_running: $status_while_running,
            status_on_success: $status_on_success,
            status_on_failure: $status_on_failure
        }})
        MERGE (import)-[:HAS_JOB]->(job)
        SET import.status = $status_while_running, import.job_uid = $uid
        RETURN {JOB_RETURN}
        """,
        parameters={
            "uid": uid,
            "kind": kind,
            "effective_date": effective_date,
            "author_id": author_id,
            "status_while_running": status_while_running,
            "status_on_success": status_on_success,
            "status_on_failure": status_on_failure,
        },
    )
    return records[0] if records else None


def start_global_job(
    session: StagingSession, uid: str, kind: str, author_id: str
) -> dict[str, Any] | None:
    """Creates a job with no release to attach to — today, only `DISCOVERY`."""

    records = run_query(
        session,
        f"""
        MERGE (lock:JobRunLock:CDISCStaging {{scope: 'DISCOVERY'}})
        ON CREATE SET lock.job_uid = $uid,
                      lock.kind = $kind,
                      lock.effective_date = NULL,
                      lock.status_while_running = NULL,
                      lock.status_on_success = NULL,
                      lock.status_on_failure = NULL
        WITH lock
        WHERE lock.job_uid = $uid
        CREATE (job:StagingJob:CDISCStaging {{
            uid: $uid,
            kind: $kind,
            effective_date: NULL,
            status: 'RUNNING',
            started_at: datetime(),
            author_id: $author_id,
            status_on_success: NULL,
            status_on_failure: NULL
        }})
        RETURN {JOB_RETURN}
        """,
        parameters={"uid": uid, "kind": kind, "author_id": author_id},
    )
    return records[0] if records else None


def finish_job(
    session: StagingSession,
    uid: str,
    status: str,
    stats: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    """Closes a job and moves its release to the target captured when it started.

    `stats` is stored as JSON text: Neo4j cannot hold a map as a property, and the
    shape of what a run counted is better kept together than spread over columns.
    `COALESCE` against the release's current status is what makes a null target (an
    analysis or assessment success, which already set the release's status as part of
    its own work) a no-op rather than an error.
    """

    run_query(
        session,
        """
        MATCH (job:StagingJob {uid: $uid})
        SET job.status = $status,
            job.finished_at = datetime(),
            job.stats = $stats,
            job.error = $error
        WITH job
        MATCH (import:EffectiveDateImport {effective_date: job.effective_date})
        SET import.status = COALESCE(
            CASE WHEN $status = 'SUCCEEDED' THEN job.status_on_success ELSE job.status_on_failure END,
            import.status
        ),
            import.imported_at = CASE
                WHEN $status = 'SUCCEEDED' AND job.status_on_success = 'IMPORTED'
                THEN datetime()
                ELSE import.imported_at
            END
        WITH job
        OPTIONAL MATCH (lock:JobRunLock {scope: job.effective_date})
        WHERE lock.job_uid = job.uid
        DELETE lock
        """,
        parameters={
            "uid": uid,
            "status": status,
            "stats": json.dumps(stats) if stats is not None else None,
            "error": error,
        },
    )


def finish_global_job(
    session: StagingSession,
    uid: str,
    status: str,
    stats: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    """Closes a job with no release to move — today, only `DISCOVERY`."""

    run_query(
        session,
        """
        MATCH (job:StagingJob {uid: $uid})
        SET job.status = $status,
            job.finished_at = datetime(),
            job.stats = $stats,
            job.error = $error
        WITH job
        OPTIONAL MATCH (lock:JobRunLock {scope: 'DISCOVERY'})
        WHERE lock.job_uid = job.uid
        DELETE lock
        """,
        parameters={
            "uid": uid,
            "status": status,
            "stats": json.dumps(stats) if stats is not None else None,
            "error": error,
        },
    )


def get_jobs(
    session: StagingSession,
    effective_date: str | None = None,
    kind: str | None = None,
) -> list[dict[str, Any]]:
    filters = []
    if effective_date:
        filters.append("job.effective_date = $effective_date")
    if kind:
        filters.append("job.kind = $kind")
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    return run_query(
        session,
        f"""
        MATCH (job:StagingJob)
        {where_clause}
        RETURN {JOB_RETURN}
        ORDER BY job.started_at DESC
        """,
        parameters={"effective_date": effective_date, "kind": kind},
    )


def find_job(session: StagingSession, uid: str) -> dict[str, Any] | None:
    records = run_query(
        session,
        f"""
        MATCH (job:StagingJob {{uid: $uid}})
        RETURN {JOB_RETURN}
        """,
        parameters={"uid": uid},
    )
    return records[0] if records else None


def find_running_job(
    session: StagingSession, effective_date: str, kind: str | None = None
) -> dict[str, Any] | None:
    """The RUNNING job of this release, of the given kind — or of any kind, if `kind`
    is left unset. Unset is what the mutual-exclusion guard needs: `ANALYZING`,
    `ASSESSING` and `IMPORTING` all refuse to start while any of the other two runs.
    """

    filters = ["job.effective_date = $effective_date", "job.status = 'RUNNING'"]
    if kind:
        filters.append("job.kind = $kind")

    records = run_query(
        session,
        f"""
        MATCH (job:StagingJob)
        WHERE {' AND '.join(filters)}
        RETURN {JOB_RETURN}
        """,
        parameters={"effective_date": effective_date, "kind": kind},
    )
    return records[0] if records else None


def find_running_global_job(
    session: StagingSession, kind: str
) -> dict[str, Any] | None:
    """Whether a job of this release-less kind is already running, anywhere."""

    records = run_query(
        session,
        f"""
        MATCH (job:StagingJob {{kind: $kind, status: 'RUNNING'}})
        WHERE job.effective_date IS NULL
        RETURN {JOB_RETURN}
        """,
        parameters={"kind": kind},
    )
    return records[0] if records else None


def fail_abandoned_jobs(
    session: StagingSession, stale_after_seconds: float
) -> list[dict[str, Any]]:
    """Fails RUNNING jobs old enough that no process can still be running them.

    Every job kind here runs in a FastAPI background task, so it dies with its
    process and will never finish or record its own failure. Left RUNNING, it would
    hold its release busy forever — a job kind's own status blocks almost everything
    else about the release, so this would leave it permanently stuck with no way out
    through the API. `OPTIONAL MATCH` is what makes this safe for `DISCOVERY`, which
    has no release to revert.

    The `import.status = job.status_while_running` check is what stops a restarted
    worker reverting a release a *different*, still-live job has since moved on from —
    the mutual-exclusion guard should never let that happen, but this is the one place
    recovering from it costs nothing extra to also guard against.

    Returns what it closed, so startup can say what it did.
    """

    return run_query(
        session,
        """
        MATCH (job:StagingJob {status: 'RUNNING'})
        WHERE job.started_at < datetime() - duration({seconds: $stale_after_seconds})
        SET job.status = 'FAILED',
            job.finished_at = datetime(),
            job.error = 'Abandoned: the process running this job stopped before it '
                      + 'finished. It is safe to run again.'
        WITH job
        OPTIONAL MATCH (import:EffectiveDateImport {effective_date: job.effective_date})
        FOREACH (_ IN CASE
            WHEN import IS NOT NULL AND import.status = job.status_while_running
            THEN [1]
            ELSE []
        END |
            SET import.status = COALESCE(job.status_on_failure, import.status)
        )
        WITH job
        OPTIONAL MATCH (lock:JobRunLock {scope: coalesce(job.effective_date, 'DISCOVERY')})
        WHERE lock.job_uid = job.uid
        DELETE lock
        RETURN job.uid AS uid, job.kind AS kind, job.effective_date AS effective_date
        """,
        parameters={"stale_after_seconds": stale_after_seconds},
    )
