"""Background jobs: import, analysis, sponsor impact assessment, and discovery.

One shape for all four, discriminated by `kind`. Three are scoped to one release and
carry its `effective_date`; `DISCOVERY` is not — it looks across every catalogue before
it knows what it will find, so it has no single release to attach to and
`effective_date` is null.
"""

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, Field


class JobKind(StrEnum):
    """What a job does."""

    IMPORT = "IMPORT"
    """Applies a release to the MDR database."""

    ANALYSIS = "ANALYSIS"
    """Groups a release and raises review items."""

    SPONSOR_IMPACT = "SPONSOR_IMPACT"
    """Compares a release against sponsor-defined content already in MDR."""

    DISCOVERY = "DISCOVERY"
    """Asks CDISC what it has published since the last release staging knows about."""


class JobStatus(StrEnum):
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class Job(BaseModel):
    """One run of a background job."""

    uid: str
    kind: JobKind
    effective_date: Annotated[
        date | None,
        Field(description="Null for DISCOVERY, which is not scoped to one release"),
    ] = None
    status: JobStatus
    started_at: datetime
    finished_at: datetime | None = None
    author_id: str
    stats: Annotated[
        dict[str, Any] | None,
        Field(description="What the run did. Empty until the job finishes"),
    ] = None
    error: str | None = None
