from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class JobAR:
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    _uid: str
    author_id: str
    job_name: str
    status: JobStatus
    started_at: datetime
    ended_at: datetime | None = None
    response_json: str | None = None
    log: list[str] | None = None

    @property
    def uid(self) -> str:
        return self._uid

    @staticmethod
    def create_started(uid: str, author_id: str, job_name: str) -> "JobAR":
        return JobAR(
            _uid=uid,
            author_id=author_id,
            job_name=job_name,
            status=JobStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )

    def mark_completed(self, response_json: str, log: list[str] | None) -> None:
        self.status = JobStatus.COMPLETED
        self.ended_at = datetime.now(timezone.utc)
        self.response_json = response_json
        self.log = log

    def mark_failed(self, error_payload_json: str, log: list[str] | None) -> None:
        self.status = JobStatus.FAILED
        self.ended_at = datetime.now(timezone.utc)
        self.response_json = error_payload_json
        self.log = log
