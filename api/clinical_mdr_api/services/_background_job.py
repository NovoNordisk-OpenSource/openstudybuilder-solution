"""Generic background-job mechanism.

Wraps a service method so the request returns immediately with a Job uid (HTTP 202),
while the actual work runs after the response via FastAPI BackgroundTasks. The
work's outcome is persisted in a Neo4j Job node, which clients can later poll.

Usage:
    @background_job(job_name="clone_study")
    def clone_study_async(self, ...) -> Study:
        ...

    # In the router:
    @router.post(".../clone/async", status_code=202)
    def clone_async(..., background_tasks: BackgroundTasks) -> JobResponse:
        return StudyService().clone_study_async(..., background_tasks=background_tasks)

The wrapped service class is expected to expose `self.author_id` (already true for
`StudyService`, `BrandService`, etc.). The author_id is captured eagerly in the
request thread because starlette_context is not available inside the BackgroundTask.
"""

from __future__ import annotations

import functools
import inspect
import json
import logging
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar

from fastapi import BackgroundTasks
from neomodel import db
from pydantic import BaseModel

from clinical_mdr_api.domain_repositories.jobs.job_repository import JobRepository
from clinical_mdr_api.domains.jobs.job import JobAR
from clinical_mdr_api.models.jobs.job import JobResponse
from common.exceptions import MDRApiBaseException

log = logging.getLogger(__name__)

# Per-job log buffer, set by `_run_job` for the duration of the wrapped call.
# `job_log(...)` reads this and appends; outside a job context the call is a no-op.
_CURRENT_JOB_LOG: ContextVar[list[str] | None] = ContextVar(
    "_CURRENT_JOB_LOG", default=None
)

# Cap on log buffer size (sum of characters across lines) to keep node payload bounded.
_LOG_BUFFER_MAX_CHARS = 256 * 1024
_LOG_TRUNCATION_MARKER = "[truncated — older log lines dropped]"


def job_log(message: str, level: str = "INFO") -> None:
    """Append a log line to the current job's log buffer, if any.

    Outside a job context this is a silent no-op so callers can use it freely.
    """
    buffer = _CURRENT_JOB_LOG.get()
    if buffer is None:
        return
    line = f"{datetime.now(timezone.utc).isoformat()} {level} {message}"
    buffer.append(line)


def _format_log_buffer(buffer: list[str]) -> list[str]:
    """Return the buffer trimmed so total character length stays within the cap.

    Drops oldest entries until the total fits, prepending a truncation marker if
    anything was dropped.
    """
    total = sum(len(line) for line in buffer)
    if total <= _LOG_BUFFER_MAX_CHARS:
        return list(buffer)
    trimmed = list(buffer)
    while trimmed and total > _LOG_BUFFER_MAX_CHARS:
        total -= len(trimmed.pop(0))
    return [_LOG_TRUNCATION_MARKER, *trimmed]


def _serialize_result(result: Any) -> str:
    if result is None:
        return "null"
    if isinstance(result, BaseModel):
        return result.model_dump_json()
    if isinstance(result, list):
        # Normalize per-element: BaseModel → primitive dict, everything else
        # passes through. Guards against heterogeneous lists (e.g. a model
        # followed by None or a plain dict) that would otherwise crash the
        # background task with AttributeError inside model_dump_json.
        normalized = [
            item.model_dump(mode="json") if isinstance(item, BaseModel) else item
            for item in result
        ]
        return json.dumps(normalized, default=str)
    return json.dumps(result, default=str)


def _serialize_exception(exc: BaseException) -> str:
    if isinstance(exc, MDRApiBaseException):
        return json.dumps(
            {
                "type": type(exc).__name__,
                "status_code": exc.status_code,
                "msg": exc.msg,
            }
        )
    return json.dumps(
        {
            "type": type(exc).__name__,
            "status_code": 500,
            "msg": str(exc),
            "traceback": traceback.format_exc(),
        }
    )


def _run_job(
    func: Callable[..., Any],
    instance: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    job: JobAR,
    repo: JobRepository,
) -> None:
    """Execute the wrapped operation and persist its outcome to the Job node.

    Runs after the HTTP response has been sent (FastAPI BackgroundTasks). The
    starlette request context is gone here, but the job already carries the
    author_id captured eagerly before scheduling.
    """
    buffer: list[str] = []
    token = _CURRENT_JOB_LOG.set(buffer)
    try:
        try:
            with db.transaction:
                result = func(instance, *args, **kwargs)
            response_json = _serialize_result(result)
            job.mark_completed(response_json, _format_log_buffer(buffer))
            repo.update(job)
        except MDRApiBaseException as exc:
            job.mark_failed(_serialize_exception(exc), _format_log_buffer(buffer))
            repo.update(job)
        except Exception as exc:  # pylint: disable=broad-except
            log.exception("Background job %s (%s) failed", job.uid, job.job_name)
            job.mark_failed(_serialize_exception(exc), _format_log_buffer(buffer))
            repo.update(job)
    finally:
        _CURRENT_JOB_LOG.reset(token)


_F = TypeVar("_F", bound=Callable[..., Any])


def background_job(default_job_name: str | None = None) -> Callable[[_F], _F]:
    """Decorator: run a service method in the background, return a JobResponse immediately.

    The wrapped method must:
      - be a synchronous instance method (no `async def`),
      - belong to a class that exposes `self.author_id`.

    The decorated method's call signature gains two wrapper-only keyword arguments
    that are consumed by this decorator and are NOT forwarded to the wrapped method:

      - `background_tasks` (required): a FastAPI `BackgroundTasks` instance the
        router injects and forwards.
      - `job_name` (optional): the human-readable name to store on the Job node.
        Falls back to `default_job_name` (this decorator's argument) and then to
        the wrapped method's `__name__`.

    Because `job_name` is a wrapper-only kwarg, the wrapped method's own signature
    stays clean — do NOT declare a `job_name` parameter on the wrapped method to
    receive the value. Inside the wrapped method, obtain the current job's name (or
    any other metadata) by emitting `job_log(...)` calls; the wrapper does not
    expose the JobAR to the wrapped function.

    Returns: a `JobResponse` describing the just-created (RUNNING) job. The original
    method's return value is serialized into the Job node's `response_json` once the
    background task finishes.
    """

    def decorator(func: _F) -> _F:
        if inspect.iscoroutinefunction(func):
            raise TypeError(
                f"@background_job cannot be used with async function '{func.__name__}'"
            )

        @functools.wraps(func)
        def wrapper(
            self: Any,
            *args: Any,
            background_tasks: BackgroundTasks,
            job_name: str | None = None,
            **kwargs: Any,
        ) -> JobResponse:
            author_id = getattr(self, "author_id", None)
            if not author_id:
                raise RuntimeError(
                    f"@background_job requires `self.author_id` on the service "
                    f"instance, but {type(self).__name__} did not provide one."
                )

            resolved_job_name = job_name or default_job_name or func.__name__
            if not isinstance(resolved_job_name, str) or not resolved_job_name:
                raise ValueError("Background job name must be a non-empty string")

            repo = JobRepository()
            uid = repo.generate_uid()
            job = JobAR.create_started(
                uid=uid,
                author_id=author_id,
                job_name=resolved_job_name,
            )
            repo.save(job)

            background_tasks.add_task(_run_job, func, self, args, kwargs, job, repo)
            return JobResponse.from_ar(job, include_response=False)

        return wrapper  # type: ignore[return-value]

    return decorator
