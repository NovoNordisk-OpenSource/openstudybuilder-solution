"""What an import would change.

The job that carries it out is `models.jobs.Job` — shared with analysis, sponsor
impact assessment and discovery, not import-specific.
"""

from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field

EXAMPLE_LIMIT = 20


class ChangeCounts(BaseModel):
    """How many concepts of one kind the import would create, version, or leave alone."""

    new: Annotated[int, Field(description="Not in the MDR database yet")] = 0
    updated: Annotated[
        int, Field(description="Present, but this release changes their values")
    ] = 0
    unchanged: Annotated[
        int, Field(description="Present and identical; no new version is created")
    ] = 0
    new_examples: Annotated[
        list[str], Field(description=f"Up to {EXAMPLE_LIMIT} concept ids")
    ] = []
    updated_examples: Annotated[
        list[str], Field(description=f"Up to {EXAMPLE_LIMIT} concept ids")
    ] = []


class MembershipChanges(BaseModel):
    """Terms joining or leaving codelists in this release."""

    added: int = 0
    ended: Annotated[
        int,
        Field(
            description="Memberships this release drops; the relationship is closed, not deleted"
        ),
    ] = 0


class ImportPreview(BaseModel):
    """What importing this release would do, computed without writing anything."""

    effective_date: date
    release_status: str
    can_import: Annotated[
        bool, Field(description="Whether the import endpoint would accept this release")
    ]
    blockers: Annotated[
        list[str],
        Field(description="Why it would be refused; empty when it would be accepted"),
    ] = []
    catalogues: list[str]
    new_packages: Annotated[
        list[str], Field(description="Packages this import would create in MDR")
    ] = []
    new_catalogues: Annotated[
        list[str], Field(description="Catalogues not in MDR yet")
    ] = []
    codelists: ChangeCounts
    terms: ChangeCounts
    memberships: MembershipChanges


class ImportRequest(BaseModel):
    """Options for starting an import."""

    expected_catalogues: Annotated[
        list[str] | None,
        Field(
            description="Assert the release holds exactly these catalogues. A half-uploaded "
            "release would otherwise import quietly, and its missing catalogues could "
            "never be added afterwards — the import is append-only."
        ),
    ] = None
