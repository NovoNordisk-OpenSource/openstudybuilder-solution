"""Exploring one release codelist by codelist, rather than as one flat review queue.

Nothing here replaces `/preview`, `/inconsistencies` or `/sponsor-impact` — it regroups
what those already compute by the codelist each row belongs to. Findings embedded here
are the same `Inconsistency` objects the flat queue returns, same `uid`, so they are
settled the same way: `POST /inconsistencies/{uid}/resolution`.
"""

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field

from standards_import.models.changelog import ChangelogEntry
from standards_import.models.imports import ChangeCounts, MembershipChanges
from standards_import.models.inconsistencies import Inconsistency


class ChangeStatus(StrEnum):
    """Whether this release adds, changes, or leaves one concept alone."""

    NEW = "NEW"
    """Not in the MDR database yet."""

    UPDATED = "UPDATED"
    """Present, but this release changes its attributes."""

    UNCHANGED = "UNCHANGED"
    """Present and identical. A codelist can still be worth a look while UNCHANGED
    itself — one of its terms changed, or it carries a finding."""


class MembershipChange(StrEnum):
    """Whether this release opens or closes one term's membership of a codelist."""

    ADDED = "ADDED"
    """This release adds the term to the codelist."""

    ENDED = "ENDED"
    """This release closes the term's membership of the codelist. The term itself is
    not deleted — it keeps its own MDR version and may belong to other codelists."""


class CodelistScope(StrEnum):
    """Which codelists `GET .../codelists` returns."""

    IN_SCOPE = "in_scope"
    """Changed itself, holding a changed term, or carrying a finding — what actually
    needs a look. Excludes a codelist that is identical and finding-free."""

    ALL = "all"
    """Every codelist in the release, changed or not."""


class TermScope(StrEnum):
    """Which terms a codelist's detail view returns."""

    CHANGED = "changed"
    """New, updated, a membership just opened or closed, or carrying a finding — what
    actually needs a look."""

    ALL = "all"
    """Every term currently in the codelist, changed or not."""


class ReviewStatus(StrEnum):
    """Where a codelist stands in the review walkthrough. Never blocks import."""

    NOT_REVIEWED = "NOT_REVIEWED"
    """Nobody has marked this codelist as looked at."""

    REVIEWED = "REVIEWED"
    """Marked reviewed, and nothing has reopened on it since."""

    REVIEWED_STALE = "REVIEWED_STALE"
    """Marked reviewed, but a later analysis reopened a finding on it. Who reviewed it
    and when is kept; the flag itself needs re-confirming."""


class CodelistReview(BaseModel):
    """Where a codelist stands in the review walkthrough, and who put it there."""

    status: ReviewStatus = ReviewStatus.NOT_REVIEWED
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None


class FindingStatusCounts(BaseModel):
    """Review items on one scope, broken down by how they stand."""

    open: Annotated[
        int, Field(description="Still to be decided. Blocks import while above zero.")
    ] = 0
    auto_resolved: Annotated[int, Field(description="Settled by a stored rule")] = 0
    resolved: Annotated[
        int, Field(description="Settled by a person, who changed a value")
    ] = 0
    ignored: Annotated[int, Field(description="Accepted as-is")] = 0
    informational: Annotated[
        int,
        Field(
            description="Not blocking import, but still counts toward whether a "
            "codelist is 'reviewed'"
        ),
    ] = 0
    acknowledged: Annotated[
        int,
        Field(
            description="Settled by a person, who considered a fact about today's "
            "database and changed nothing"
        ),
    ] = 0


class AttributeChange(BaseModel):
    """One property this release changes on a codelist, old value beside new."""

    field: str
    old_value: Annotated[
        str | list[str] | None, Field(description="What MDR holds")
    ] = None
    new_value: Annotated[
        str | list[str] | None, Field(description="What this release would write")
    ] = None


class AttributeValue(BaseModel):
    """One property of a codelist, as it stands once this release lands."""

    field: str
    value: str | list[str] | bool | None = None


class CodelistSummary(BaseModel):
    """One codelist's change, finding and review state, for the list view."""

    codelist_id: str
    name: str | None = None
    submission_value: str | None = None
    change_status: ChangeStatus
    term_changes: Annotated[
        ChangeCounts, Field(description="This codelist's own terms, not the release's")
    ]
    memberships: Annotated[
        MembershipChanges,
        Field(description="Terms joining or leaving this codelist specifically"),
    ]
    findings: FindingStatusCounts
    review: CodelistReview


class CodelistPage(BaseModel):
    """A page of `GET .../codelists`, filtered before it was paginated."""

    items: list[CodelistSummary]
    total: Annotated[
        int, Field(description="Matching codelists across all pages, not just this one")
    ]
    page_number: int
    page_size: Annotated[
        int,
        Field(description="0 means every matching codelist was returned on one page"),
    ]


class CodelistTermSummary(BaseModel):
    """One term, in the context of one codelist."""

    concept_id: str
    preferred_term: str | None = None
    submission_value: str | None = None
    change_status: Annotated[
        ChangeStatus | None,
        Field(
            description="Null for a term whose membership just ended: this release "
            "does not define it at all, and it is shown only because it just left"
        ),
    ] = None
    membership_change: Annotated[
        MembershipChange | None,
        Field(description="Set when this release opens or closes this membership"),
    ] = None
    findings: list[Inconsistency] = []
    changelog: Annotated[
        list[ChangelogEntry],
        Field(
            description="What CDISC said it changed about this term, where a "
            "terminology-changes spreadsheet has been uploaded. Commentary only — "
            "nothing here is a finding, and none of it blocks anything"
        ),
    ] = []


class CodelistDetail(BaseModel):
    """What one release changes on one codelist, and everything to review there."""

    codelist_id: str
    name: str | None = None
    submission_value: str | None = None
    change_status: ChangeStatus
    changes: Annotated[
        list[AttributeChange],
        Field(
            description="What changed on the codelist itself. For a NEW codelist, "
            "every attribute it brings, each without an old value. Empty when UNCHANGED"
        ),
    ] = []
    attributes: Annotated[
        list[AttributeValue],
        Field(
            description="Every attribute of the codelist as this release defines it, "
            "changed or not. For an UNCHANGED codelist, exactly what MDR holds today"
        ),
    ] = []
    findings: Annotated[
        list[Inconsistency], Field(description="Findings about the codelist itself")
    ] = []
    changelog: Annotated[
        list[ChangelogEntry],
        Field(
            description="What CDISC said it changed about the codelist itself. Also "
            "carries entries about a term that is no longer there to hold them — a "
            "term removed this release lands here when it left with no trace, and its "
            "`nci_code` says which"
        ),
    ] = []
    terms: Annotated[
        list[CodelistTermSummary],
        Field(description="Changed or flagged terms by default; see `show=all`"),
    ] = []
    term_count: Annotated[
        int, Field(description="Terms currently in the codelist, whether listed or not")
    ]
    review: CodelistReview


class TermChangeStatus(StrEnum):
    """What this release does to one term, across every codelist that holds it.

    Distinct from `ChangeStatus`, which a codelist uses: a term can be touched by a
    membership change while its own attributes are identical, and it can drop out of the
    release altogether — neither of which a codelist does. There is no `UNCHANGED`: a
    term the release leaves alone is not listed at all.
    """

    NEW = "NEW"
    """Not in the MDR database yet."""

    CHANGED = "CHANGED"
    """Its attributes differ, or a codelist membership opens or closes, or both."""

    DELETED = "DELETED"
    """Gone from every grouped codelist of this release, so all of its CDISC memberships
    close. The term is **not** deleted from the MDR — it keeps its own version and its
    attributes, exactly as `MembershipChange.ENDED` describes. Nothing in this app
    retires or deletes a term."""


class ImpactedProperty(StrEnum):
    """Which part of a term this release touches.

    No `name` member, and that is not an oversight: a term's sponsor name is written
    only for a term new to the MDR, never overwritten on one already there, so a release
    never changes it. Where a name is at stake it is a `SPONSOR_NAME` or
    `SPONSOR_NAME_DIVERGED` finding instead, which the finding counts already report.
    """

    PREFERRED_TERM = "preferred_term"
    DEFINITION = "definition"
    SYNONYMS = "synonyms"

    SUBMISSION_VALUE = "submission_value"
    """The term's submission value changed in at least one of its codelists. A term
    holds one per membership, not one of its own; which codelist is in that codelist's
    detail view."""

    MEMBERSHIP = "membership"
    """Not a property: the set of codelists holding the term changed."""


class TermSummary(BaseModel):
    """One term's change, membership, finding and review state, for the list view."""

    concept_id: str
    preferred_term: Annotated[
        str | None,
        Field(
            description="What this release calls it. For a DELETED term the release says "
            "nothing, so this is what MDR holds"
        ),
    ] = None
    change_status: TermChangeStatus
    impacted: Annotated[
        list[ImpactedProperty],
        Field(description="What the change touches. Empty for NEW"),
    ] = []
    changes: Annotated[
        list[AttributeChange],
        Field(
            description="Old value beside new, for each impacted property that has one. "
            "Nothing for `membership` or `submission_value`, which are per codelist"
        ),
    ] = []
    codelist_count: Annotated[
        int,
        Field(
            description="Codelists holding the term once this release lands. Memberships "
            "the release ends are not counted, so a DELETED term reports 0"
        ),
    ] = 0
    findings: FindingStatusCounts
    review: Annotated[
        CodelistReview,
        Field(
            description="Inherited from the codelists holding this term — there is no "
            "per-term review mark, and nothing here can be marked directly"
        ),
    ]


class TermUsage(BaseModel):
    """One kind of thing in the MDR database that refers to a term, and how many."""

    through: Annotated[
        str,
        Field(
            description="How the reference reaches the term: `selected in context` "
            "(through a `CTTermContext` - activity items, unit definitions, ODM items, "
            "study selections, template categories) or "
            "`used by name` (a syntax instance built on the term's name)"
        ),
    ]
    relationship: Annotated[
        str, Field(description="The relationship the referring node holds")
    ]
    consumer_labels: Annotated[
        list[str], Field(description="Labels of the referring nodes")
    ]
    count: int


class TermCodelistMembership(BaseModel):
    """One codelist a term belongs to, seen from the term."""

    codelist_id: str
    name: str | None = None
    submission_value: Annotated[
        str | None, Field(description="The codelist's own submission value")
    ] = None
    term_submission_value: Annotated[
        str | None,
        Field(
            description="The term's submission value in this codelist once this release "
            "lands. For a membership the release ends, the one MDR holds. Null for a "
            "codelist only a finding ties the term to — one a decision took it out of"
        ),
    ] = None
    previous_submission_value: Annotated[
        str | None,
        Field(
            description="What MDR holds, set only where this release gives the term a "
            "different submission value in this codelist"
        ),
    ] = None
    membership_change: Annotated[
        MembershipChange | None,
        Field(description="Set when this release opens or closes this membership"),
    ] = None
    findings: Annotated[
        list[Inconsistency],
        Field(
            description="Findings about the term inside this codelist: keyed on the "
            "codelist, naming the term in `related_concept_id`"
        ),
    ] = []
    review: Annotated[CodelistReview, Field(description="The codelist's own review")]


class TermDetail(BaseModel):
    """What one release changes on one term, in every codelist holding it."""

    concept_id: str
    preferred_term: Annotated[
        str | None,
        Field(
            description="What this release calls it. For a term the release no longer "
            "ships, what MDR holds"
        ),
    ] = None
    change_status: Annotated[
        ChangeStatus | None,
        Field(
            description="Of the term's own attributes. Null for a term the release no "
            "longer ships at all: it is shown only because its memberships close"
        ),
    ] = None
    changes: Annotated[
        list[AttributeChange],
        Field(
            description="What changed on the term itself. For a NEW term, every "
            "attribute it brings, each without an old value. Empty when UNCHANGED"
        ),
    ] = []
    attributes: Annotated[
        list[AttributeValue],
        Field(
            description="Every attribute of the term as this release defines it, or as "
            "MDR holds it for a term the release no longer ships"
        ),
    ] = []
    findings: Annotated[
        list[Inconsistency],
        Field(description="Findings about the term itself, wherever it is held"),
    ] = []
    codelists: Annotated[
        list[TermCodelistMembership],
        Field(
            description="Every codelist holding the term once this release lands, plus "
            "the ones it is leaving, by codelist id"
        ),
    ] = []
    usage: Annotated[
        list[TermUsage],
        Field(
            description="What in the MDR database refers to the term today, read at "
            "request time, by kind - the same check the sponsor impact assessment "
            "counts for `usage_count`. Empty for a term MDR does not hold yet, or one "
            "nothing refers to"
        ),
    ] = []
    changelog: Annotated[
        list[ChangelogEntry],
        Field(
            description="What CDISC said it changed about this term, in any codelist "
            "holding it, where a terminology-changes spreadsheet has been uploaded. "
            "Commentary only — nothing here is a finding, and none of it blocks anything"
        ),
    ] = []
    review: Annotated[
        CodelistReview,
        Field(
            description="Inherited from the codelists holding this term, as in "
            "`/terms` — there is no per-term review mark"
        ),
    ]


class TermPage(BaseModel):
    """A page of `GET .../terms`, filtered before it was paginated."""

    items: list[TermSummary]
    total: Annotated[
        int, Field(description="Matching terms across all pages, not just this one")
    ]
    page_number: int
    page_size: Annotated[
        int,
        Field(description="0 means every matching term was returned on one page"),
    ]


class ReleaseInconsistencyStats(BaseModel):
    """Review items of one release, split by which pass raised them."""

    analysis: FindingStatusCounts
    sponsor_impact: FindingStatusCounts
    assessed_at: Annotated[
        datetime | None,
        Field(description="Null if sponsor impact has never been assessed"),
    ] = None


class ReleaseReviewStats(BaseModel):
    """How far the codelist-by-codelist walkthrough has got. Never blocks import."""

    in_scope: Annotated[
        int, Field(description="Codelists worth a look: changed, or carrying a finding")
    ]
    reviewed: int = 0
    stale: Annotated[
        int,
        Field(
            description="Reviewed, then reopened by a later analysis; see `REVIEWED_STALE`"
        ),
    ] = 0
    not_reviewed: int = 0


class ReleaseDashboard(BaseModel):
    """Overview of one release: what changed, what's outstanding, review progress."""

    effective_date: date
    release_status: str
    can_import: Annotated[
        bool, Field(description="Whether the import endpoint would accept this release")
    ]
    blockers: list[str] = []
    catalogues: list[str] = []
    codelists: ChangeCounts
    terms: ChangeCounts
    memberships: MembershipChanges
    inconsistencies: ReleaseInconsistencyStats
    review: ReleaseReviewStats
