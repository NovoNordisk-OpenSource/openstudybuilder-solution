"""The terminology-change notes CDISC publishes alongside a release.

CDISC ships one "<catalogue> Terminology Changes" spreadsheet per catalogue with each
quarterly package, describing in prose what moved and why. That is editorial commentary
on a release, not an input to it: nothing here feeds analysis, gates an import, or
appears among the blockers. It rides alongside the codelist detail read so a reviewer
looking at a change can see what CDISC said about it.

What a row was *about* is not stored as a type — the node its `ABOUT` relationship
points at already says whether the subject is a term, a codelist or the catalogue. The
before-and-after values are not stored either: both are readable from the raw nodes and
their predecessors, and a second copy that could disagree with them is worse than none.
"""

from datetime import date
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field


class ChangeType(StrEnum):
    """What CDISC did, from the sheet's `Change Type` column.

    Upper-cased on the way in, like every other enum here; the sheet writes these in
    title case.

    Coarser than it looks, and not the verb to show a reader: adding a synonym and
    removing one are both `UPDATE`, because both update the term that carries it.
    `change_summary` is what carries the direction — "Add new CDISC Synonym" against
    "Remove CDISC Synonym" — so anything distinguishing the two reads that instead.
    """

    ADD = "ADD"
    """The subject is new in this release."""

    UPDATE = "UPDATE"
    """One of the subject's properties changed. Covers additions to and removals from
    a list-valued property, such as synonyms."""

    REMOVE = "REMOVE"
    """The subject was withdrawn — a term dropped from a codelist, or a codelist
    retired outright."""


class ChangelogEntry(BaseModel):
    """One change CDISC reported, as one or more rows of a changes spreadsheet.

    One entry, not one row. Catalogues overlap — `LBTEST` belongs to both SDTM and
    SEND, and each ships the same note about it — so a change reported by several
    catalogues is returned once with `catalogues` naming all of them, the same way a
    value several catalogues supplied is reported once. Returning it per catalogue
    would show a reviewer the same sentence two or three times with nothing visibly
    telling them apart.
    """

    change_type: ChangeType
    change_summary: Annotated[
        str,
        Field(
            description="CDISC's own one-line description, for example `Add new term "
            "to existing codelist`. Unlike `change_type` this carries the direction of "
            "a list-valued change"
        ),
    ]
    request_codes: Annotated[
        list[str],
        Field(
            description="The CDISC change requests behind this entry, for example "
            "`CDISC-6139`. Empty where the sheet said `N/A`, which is usual for a "
            "change NCI made rather than one somebody asked for"
        ),
    ] = []
    implementation_instructions: Annotated[
        str | None,
        Field(
            description="What CDISC advises implementers to do about it. Set on a small "
            "minority of entries — typically where a concept was merged into another"
        ),
    ] = None
    nci_code: Annotated[
        str | None,
        Field(
            description="Concept id of what the entry is about. Null where the subject "
            "is the codelist's own name: CDISC repeats one such row for every member "
            "term, each carrying that term's code, and those are folded into one entry"
        ),
    ] = None
    codelist_short_name: Annotated[
        str,
        Field(
            description="Submission value of the codelist the row named — populated on "
            "every row, including those about a term"
        ),
    ]
    codelist_long_name: str | None = None
    catalogues: Annotated[
        list[str],
        Field(
            description="Every catalogue that reported this change, for example "
            "`['SDTM CT', 'SEND CT']`"
        ),
    ] = []
    source_files: Annotated[
        list[str],
        Field(description="The spreadsheets it was read from, one per catalogue"),
    ] = []


class StagedChangelogFile(BaseModel):
    """A terminology-changes spreadsheet uploaded for a release."""

    effective_date: date
    catalogue: Annotated[
        str,
        Field(
            description="Catalogue the sheet title named, or the `catalogue` query "
            "parameter where one was given"
        ),
    ]
    source_file: Annotated[
        str, Field(description="Name you gave the uploaded spreadsheet")
    ]
    sheet: Annotated[str, Field(description="Sheet the rows were read from")]
    entries: Annotated[int, Field(description="Entries stored from it")]
    collapsed: Annotated[
        int,
        Field(
            description="Rows folded into an entry already counted. CDISC repeats a "
            "codelist rename once per member term; those become one entry about the "
            "codelist"
        ),
    ] = 0
