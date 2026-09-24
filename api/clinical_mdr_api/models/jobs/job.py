import json
from datetime import datetime
from typing import Annotated, Any, Self

from pydantic import Field

from clinical_mdr_api.domains.jobs.job import JobAR
from clinical_mdr_api.models.utils import BaseModel


class JobResponse(BaseModel):
    uid: Annotated[str, Field(description="The unique id of the Job.")]
    job_name: Annotated[
        str, Field(description="The logical name of the wrapped operation.")
    ]
    status: Annotated[
        str, Field(description="One of 'RUNNING', 'COMPLETED', 'FAILED'.")
    ]
    author_id: Annotated[
        str, Field(description="Identity of the user who started the job.")
    ]
    started_at: Annotated[
        datetime, Field(description="UTC timestamp when the job started.")
    ]
    ended_at: Annotated[
        datetime | None,
        Field(
            description="UTC timestamp when the job ended; null while running.",
        ),
    ] = None
    response: Annotated[
        Any | None,
        Field(
            description=(
                "On success, the JSON response of the wrapped operation. "
                "On failure, a structured error payload. Null while the job is RUNNING. "
                "Omitted from list responses to keep payloads small."
            ),
        ),
    ] = None
    log: Annotated[
        list[str] | None,
        Field(
            description="Captured log lines emitted by the wrapped operation via `job_log(...)`.",
        ),
    ] = None

    @classmethod
    def from_ar(cls, job: JobAR, include_response: bool = True) -> Self:
        response: Any | None = None
        if include_response and job.response_json is not None:
            try:
                response = json.loads(job.response_json)
            except json.JSONDecodeError:
                response = job.response_json

        return cls(
            uid=job.uid,
            job_name=job.job_name,
            status=job.status.value,
            author_id=job.author_id,
            started_at=job.started_at,
            ended_at=job.ended_at,
            response=response,
            log=job.log if include_response else None,
        )
