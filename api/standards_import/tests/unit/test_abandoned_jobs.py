"""Clearing jobs left behind by a process that stopped, of any kind."""

import contextlib
import inspect

from standards_import.config import settings
from standards_import.repositories import job_repository
from standards_import.services import job_service


def _null_session():
    return contextlib.nullcontext(None)


def test_the_sweep_passes_the_configured_threshold(monkeypatch):
    seen = {}

    def fake_sweep(_session, stale_after_seconds):
        seen["stale_after_seconds"] = stale_after_seconds
        return [
            {"uid": "job-1", "kind": "IMPORT", "effective_date": "2025-09-26"},
            {"uid": "job-2", "kind": "ANALYSIS", "effective_date": "2025-09-26"},
        ]

    monkeypatch.setattr(job_service, "staging_session", _null_session)
    monkeypatch.setattr(job_repository, "fail_abandoned_jobs", fake_sweep)

    closed = job_service.fail_abandoned_jobs()

    assert [job["uid"] for job in closed] == ["job-1", "job-2"]
    assert seen["stale_after_seconds"] == settings.job_stale_after_seconds


def test_a_quiet_startup_reports_nothing(monkeypatch, caplog):
    monkeypatch.setattr(job_service, "staging_session", _null_session)
    monkeypatch.setattr(job_repository, "fail_abandoned_jobs", lambda *_: [])

    assert job_service.fail_abandoned_jobs() == []
    assert "abandoned" not in caplog.text


def test_the_sweep_spares_jobs_that_could_still_be_running():
    """A restart of one worker must not fail a job running in another.

    Behaviour is verified against a real database; this pins the two conditions that
    make it safe — an age threshold, and only releases whose status still matches the
    job that is meant to be reverting it.
    """

    query = inspect.getsource(job_repository.fail_abandoned_jobs)

    assert (
        "job.started_at < datetime() - duration({seconds: $stale_after_seconds})"
        in query
    )
    assert "FOREACH (_ IN CASE" in query
    assert "coalesce(job.effective_date, 'DISCOVERY')" in query
    assert "{status: 'RUNNING'}" in query


def test_every_kind_shares_one_sweep():
    """Discovery has no release to revert, which is what `OPTIONAL MATCH` is for —
    pinned here because it is easy to reintroduce a plain `MATCH` that would silently
    stop discovery jobs ever being recovered."""

    query = inspect.getsource(job_repository.fail_abandoned_jobs)

    assert "OPTIONAL MATCH (import:EffectiveDateImport" in query
