"""Unit tests for the generic background-job mechanism.

These tests exercise the decorator and the worker function in isolation, with
the JobRepository and the neomodel transaction context fully mocked. Integration
coverage (real Neo4j round-trip via the clone_study_async endpoint) lives under
clinical_mdr_api/tests/integration.
"""

# `self` is intentionally unused in the dummy service-method stand-ins below —
# the decorator targets bound methods, so the test functions must accept self.
# pylint: disable=unused-argument,useless-return

import json
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from fastapi import BackgroundTasks
from pydantic import BaseModel

from clinical_mdr_api.domains.jobs.job import JobAR, JobStatus
from clinical_mdr_api.models.jobs.job import JobResponse
from clinical_mdr_api.services._background_job import (
    _run_job,
    _serialize_exception,
    _serialize_result,
    background_job,
    job_log,
)
from common.exceptions import BusinessLogicException


class _FakeService:
    """Minimal stand-in for a service class that uses @background_job."""

    def __init__(self, author_id: str = "user-123") -> None:
        self.author_id = author_id


class _SamplePayload(BaseModel):
    uid: str
    name: str


@contextmanager
def _patched_repo_and_db():
    """Patch JobRepository and the neomodel db transaction inside _background_job."""
    with (
        patch("clinical_mdr_api.services._background_job.JobRepository") as repo_cls,
        patch("clinical_mdr_api.services._background_job.db") as db_mock,
    ):
        # `with db.transaction:` no-op
        db_mock.transaction.__enter__ = MagicMock(return_value=None)
        db_mock.transaction.__exit__ = MagicMock(return_value=False)
        repo = MagicMock()
        repo.generate_uid.return_value = "Job_000001"
        repo_cls.return_value = repo
        yield repo


def test_decorator_returns_job_response_immediately_and_schedules_background_task():
    bg_tasks = BackgroundTasks()

    @background_job(default_job_name="sample_job")
    def do_work(self, x):
        return _SamplePayload(uid="x", name=f"hello {x}")

    service = _FakeService()
    with _patched_repo_and_db() as repo:
        result = do_work(service, "world", background_tasks=bg_tasks)

    assert isinstance(result, JobResponse)
    assert result.uid == "Job_000001"
    assert result.status == JobStatus.RUNNING.value
    assert result.author_id == "user-123"
    repo.save.assert_called_once()
    saved_job: JobAR = repo.save.call_args.args[0]
    assert saved_job.status is JobStatus.RUNNING
    assert saved_job.job_name == "sample_job"

    # The actual work must NOT have run yet — only scheduled.
    assert len(bg_tasks.tasks) == 1


def test_decorator_uses_runtime_job_name_override():
    """A caller-supplied `job_name=` kwarg wins over the decorator's default,
    and is consumed by the wrapper — it must NOT be forwarded to the wrapped
    method (which does not declare it as a parameter)."""
    bg_tasks = BackgroundTasks()

    @background_job(default_job_name="default_job")
    def do_work(self):
        return None

    with _patched_repo_and_db() as repo:
        do_work(
            _FakeService(),
            background_tasks=bg_tasks,
            job_name="clone_study:Study_000001",
        )

    saved_job: JobAR = repo.save.call_args.args[0]
    assert saved_job.job_name == "clone_study:Study_000001"
    # `job_name` is a wrapper-only kwarg; the kwargs forwarded to the wrapped
    # method must be empty (the wrapped method only took `self`).
    work_kwargs = bg_tasks.tasks[0].args[3]
    assert "job_name" not in work_kwargs


def test_decorator_falls_back_to_function_name_when_no_default_and_no_override():
    """No decorator default + no runtime override → the wrapped method's `__name__`."""
    bg_tasks = BackgroundTasks()

    @background_job()
    def clone_study(self):
        return None

    with _patched_repo_and_db() as repo:
        clone_study(_FakeService(), background_tasks=bg_tasks)

    saved_job: JobAR = repo.save.call_args.args[0]
    assert saved_job.job_name == "clone_study"


def test_decorator_rejects_async_function():
    with pytest.raises(TypeError, match="cannot be used with async function"):

        @background_job(default_job_name="bad")
        async def _async_method(self):  # pragma: no cover - decorator should raise
            return None


def test_decorator_requires_author_id_on_service():
    bg_tasks = BackgroundTasks()

    @background_job(default_job_name="x")
    def do_work(self):
        return None

    class NoAuthorService:
        pass

    with _patched_repo_and_db():
        with pytest.raises(RuntimeError, match="self.author_id"):
            do_work(NoAuthorService(), background_tasks=bg_tasks)


def test_run_job_marks_completed_on_success():
    """_run_job must serialize the result and call repo.update with COMPLETED."""

    def work(self, value):
        return _SamplePayload(uid="abc", name=value)

    service = _FakeService()
    job = JobAR.create_started(uid="Job_000007", author_id="user-123", job_name="t")
    repo = MagicMock()

    with patch("clinical_mdr_api.services._background_job.db") as db_mock:
        db_mock.transaction.__enter__ = MagicMock(return_value=None)
        db_mock.transaction.__exit__ = MagicMock(return_value=False)
        _run_job(work, service, ("hello",), {}, job, repo)

    repo.update.assert_called_once()
    updated: JobAR = repo.update.call_args.args[0]
    assert updated.status is JobStatus.COMPLETED
    assert updated.ended_at is not None
    payload = json.loads(updated.response_json)
    assert payload == {"uid": "abc", "name": "hello"}


def test_run_job_marks_failed_on_business_logic_exception():
    def work(self):
        raise BusinessLogicException(msg="bad input")

    job = JobAR.create_started(uid="Job_000008", author_id="user-123", job_name="t")
    repo = MagicMock()

    with patch("clinical_mdr_api.services._background_job.db") as db_mock:
        db_mock.transaction.__enter__ = MagicMock(return_value=None)
        db_mock.transaction.__exit__ = MagicMock(return_value=False)
        _run_job(work, _FakeService(), (), {}, job, repo)

    repo.update.assert_called_once()
    updated: JobAR = repo.update.call_args.args[0]
    assert updated.status is JobStatus.FAILED
    payload = json.loads(updated.response_json)
    assert payload["type"] == "BusinessLogicException"
    assert payload["status_code"] == 400
    assert payload["msg"] == "bad input"
    assert "traceback" not in payload


def test_run_job_marks_failed_with_traceback_on_generic_exception():
    def work(self):
        raise RuntimeError("boom")

    job = JobAR.create_started(uid="Job_000009", author_id="user-123", job_name="t")
    repo = MagicMock()

    with patch("clinical_mdr_api.services._background_job.db") as db_mock:
        db_mock.transaction.__enter__ = MagicMock(return_value=None)
        db_mock.transaction.__exit__ = MagicMock(return_value=False)
        _run_job(work, _FakeService(), (), {}, job, repo)

    updated: JobAR = repo.update.call_args.args[0]
    assert updated.status is JobStatus.FAILED
    payload = json.loads(updated.response_json)
    assert payload["type"] == "RuntimeError"
    assert payload["status_code"] == 500
    assert payload["msg"] == "boom"
    assert "traceback" in payload and "RuntimeError: boom" in payload["traceback"]


def test_job_log_captures_lines_inside_a_running_job_only():
    captured: dict[str, list[str]] = {}

    def work(self):
        job_log("hello from inside the job")
        job_log("another line", level="WARNING")
        return None

    job = JobAR.create_started(uid="Job_000010", author_id="user-123", job_name="t")
    repo = MagicMock()

    def _capture_update(j: JobAR):
        captured["log"] = j.log

    repo.update.side_effect = _capture_update

    # job_log called outside any job context must be a silent no-op.
    job_log("this should be ignored")

    with patch("clinical_mdr_api.services._background_job.db") as db_mock:
        db_mock.transaction.__enter__ = MagicMock(return_value=None)
        db_mock.transaction.__exit__ = MagicMock(return_value=False)
        _run_job(work, _FakeService(), (), {}, job, repo)

    log_lines: list[str] = captured["log"]
    assert any("hello from inside the job" in line for line in log_lines)
    assert any("WARNING another line" in line for line in log_lines)
    assert all("this should be ignored" not in line for line in log_lines)


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, "null"),
        (_SamplePayload(uid="u", name="n"), '{"uid":"u","name":"n"}'),
        (
            [_SamplePayload(uid="a", name="A"), _SamplePayload(uid="b", name="B")],
            '[{"uid": "a", "name": "A"}, {"uid": "b", "name": "B"}]',
        ),
        ({"k": 1}, '{"k": 1}'),
        ([], "[]"),
        # Heterogeneous list: a BaseModel followed by a non-BaseModel. The
        # naive `isinstance(result[0], BaseModel)` fast path used to blow up
        # here — the normalization step must serialize each item on its own.
        (
            [_SamplePayload(uid="a", name="A"), None, {"k": 1}],
            '[{"uid": "a", "name": "A"}, null, {"k": 1}]',
        ),
        # And the mirror case: a plain dict first, a BaseModel later. The old
        # fast path silently skipped the model branch and let json.dumps hit
        # the pydantic instance via default=str, producing a repr string.
        (
            [{"k": 1}, _SamplePayload(uid="a", name="A")],
            '[{"k": 1}, {"uid": "a", "name": "A"}]',
        ),
    ],
)
def test_serialize_result_handles_common_shapes(value, expected):
    assert _serialize_result(value) == expected


def test_serialize_exception_uses_status_code_from_mdr_exception():
    payload = json.loads(_serialize_exception(BusinessLogicException(msg="oops")))
    assert payload == {
        "type": "BusinessLogicException",
        "status_code": 400,
        "msg": "oops",
    }
