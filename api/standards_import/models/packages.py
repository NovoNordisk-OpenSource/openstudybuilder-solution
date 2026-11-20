"""Models describing staged CDISC package files and their effective dates."""

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Any, Self

from pydantic import BaseModel, Field, SecretStr

from standards_import.models.inconsistencies import InconsistencyType


class EffectiveDateStatus(StrEnum):
    """Lifecycle of one CDISC release, identified by its effective date.

    `ANALYZING`, `ASSESSING` and `IMPORTING` are mutually exclusive with each other,
    not only with themselves: analysis rebuilds the same grouped layer assessment
    reads and import writes from, so any two running at once on the same release
    would race. Uploads and review-item resolutions are refused during all three
    for the same reason.
    """

    FILES_STAGED = "FILES_STAGED"
    """At least one catalogue file uploaded, not analysed yet."""

    ANALYZED = "ANALYZED"
    """Grouped and checked, no review items are blocking."""

    BLOCKED = "BLOCKED"
    """Analysed, but review items remain open and must be resolved first."""

    READY = "READY"
    """An import was attempted and failed; the release can be imported again.

    Only ever reached from a failed run — it is the "cleared, try again" state, not a
    step on the way in. A successful import never passes through it.
    """

    ANALYZING = "ANALYZING"
    """Analysis is under way as a background job. A failed run reverts to
    `FILES_STAGED`: the derived layer was already cleared before the failure, so
    whatever the release was analysed to before is no longer trustworthy."""

    ASSESSING = "ASSESSING"
    """Sponsor impact assessment is under way as a background job. Unlike analysis,
    a failed run reverts to whatever the release's status was before — assessment
    only ever reads the grouped layer and adds its own findings, so nothing it does
    invalidates what analysis had already settled."""

    IMPORTING = "IMPORTING"
    """An import is under way as a background job. While in this status, all other
    import attempts will be blocked to avoid a conflict."""

    IMPORTED = "IMPORTED"
    """Imported successfully. Terminal — nothing moves a release out of this state
    again, and it alone is what stops the release being imported twice."""


class StagedPackageFile(BaseModel):
    """One uploaded CDISC catalogue file."""

    uid: Annotated[str, Field(description="Identifier of the staged file")]
    catalogue: Annotated[
        str, Field(description="Catalogue name, for example `SDTM CT`")
    ]
    package_name: Annotated[
        str,
        Field(
            description="Package name as given by CDISC, for example `SDTM CT 2024-09-27`"
        ),
    ]
    effective_date: Annotated[
        date, Field(description="Effective date of the release this file belongs to")
    ]
    sha256: Annotated[
        str,
        Field(description="Digest of the uploaded bytes, used to detect re-uploads"),
    ]
    size_bytes: Annotated[int, Field(description="Size of the uploaded file in bytes")]
    codelist_count: Annotated[
        int, Field(description="Number of codelists found in the file")
    ]
    term_count: Annotated[
        int, Field(description="Number of term entries found in the file")
    ]
    uploaded_at: Annotated[datetime, Field(description="When the file was uploaded")]
    author_id: Annotated[str, Field(description="Who uploaded the file")]
    replaced_previous_upload: Annotated[
        bool,
        Field(
            description="Whether this upload replaced an earlier one for the same catalogue and effective date"
        ),
    ] = False

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> Self:
        return cls(
            uid=record["uid"],
            catalogue=record["catalogue"],
            package_name=record["package_name"],
            effective_date=(
                record["effective_date"].to_native().date()
                if hasattr(record["effective_date"], "to_native")
                else record["effective_date"]
            ),
            sha256=record["sha256"],
            size_bytes=record["size_bytes"],
            codelist_count=record["codelist_count"],
            term_count=record["term_count"],
            uploaded_at=(
                record["uploaded_at"].to_native()
                if hasattr(record["uploaded_at"], "to_native")
                else record["uploaded_at"]
            ),
            author_id=record["author_id"],
            replaced_previous_upload=record.get("replaced_previous_upload", False),
        )


class DiscoverReleasesInput(BaseModel):
    """What the caller supplies to ask CDISC what it has published."""

    api_key: Annotated[
        SecretStr,
        Field(
            min_length=1,
            description="The caller's own CDISC Library API key, sent to CDISC as the "
            "`api-key` header. Used for this one run only: it is never stored, never "
            "written to the job, and not returned.",
        ),
    ]


class DiscoveredRelease(BaseModel):
    """One catalogue file of a CDISC release that staging had not heard of before this run.

    A release is one effective date; it usually spans several catalogues, so a newly
    discovered release can show up here as more than one entry sharing that date.
    """

    catalogue: Annotated[
        str, Field(description="Catalogue name, for example `SDTM CT`")
    ]
    package_name: Annotated[
        str,
        Field(
            description="Package name as published by CDISC, for example `SDTM CT 2024-09-27`"
        ),
    ]
    effective_date: Annotated[
        date, Field(description="Effective date read from the published package name")
    ]
    href: Annotated[
        str,
        Field(
            description="Path of the package in the CDISC Library, as published. Nothing "
            "has been fetched from it — the content still arrives by upload"
        ),
    ]
    discovered_at: Annotated[
        datetime, Field(description="When this release was first discovered")
    ]
    auto_staged: Annotated[
        bool,
        Field(
            description="Whether this catalogue's content was fetched from CDISC and "
            "staged automatically. Only attempted for SDTM CT; every other catalogue "
            "still needs a manual upload"
        ),
    ] = False
    stage_error: Annotated[
        str | None,
        Field(
            description="Set when auto-staging was attempted and failed. The release is "
            "still reported as discovered — a fetch or staging failure for one catalogue "
            "must not hide that CDISC published it"
        ),
    ] = None

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> Self:
        return cls(
            catalogue=record["catalogue"],
            package_name=record["package_name"],
            effective_date=(
                record["effective_date"].to_native().date()
                if hasattr(record["effective_date"], "to_native")
                else record["effective_date"]
            ),
            href=record["href"],
            discovered_at=(
                record["discovered_at"].to_native()
                if hasattr(record["discovered_at"], "to_native")
                else record["discovered_at"]
            ),
        )


class ReleaseDiscoveryResult(BaseModel):
    """What one discovery run found at CDISC that staging did not already know about."""

    new_releases: Annotated[
        list[DiscoveredRelease],
        Field(
            description="Effective dates newer than anything staging holds, newest "
            "first, one entry per catalogue published under them. Recorded as known, "
            "so a later run reports them no more"
        ),
    ] = []
    skipped_count: Annotated[
        int,
        Field(
            description="Published entries passed over because their name does not end "
            "with an effective date, so no catalogue could be derived from it. Reported "
            "rather than raised: one oddly named package must not stop the rest being seen"
        ),
    ] = 0


class StagedPairingFile(BaseModel):
    """A paired-codelist workbook uploaded for a release."""

    effective_date: date
    source_file: Annotated[
        str, Field(description="Name you gave the uploaded workbook")
    ]
    sheets: Annotated[list[str], Field(description="Paired-codelist sheets read")]
    pairings: Annotated[int, Field(description="Codelist pairs taken from it")]
    skipped: Annotated[
        list[str],
        Field(description="Rows that are not a name/code pair and were passed over"),
    ] = []


class PreviousReleaseInfo(BaseModel):
    """Which release, if any, a catalogue's diff would be compared against.

    Split out from `PackageDiffReport` so the frontend can show which release it is
    comparing against before the full diff — which walks every codelist and term of
    both catalogues — has finished computing.
    """

    previous_available: Annotated[
        bool,
        Field(
            description="Whether a previous release of this catalogue is staged to "
            "compare against. False means either this is the first staged release of "
            "the catalogue, or its predecessor was never staged"
        ),
    ]
    previous_package_name: Annotated[
        str | None, Field(description="Package name of the release compared against")
    ] = None
    previous_effective_date: Annotated[
        date | None,
        Field(description="Effective date of the release compared against"),
    ] = None


class PackageDiffBand(BaseModel):
    """One severity band of a package diff, holding every change of that kind."""

    level: Annotated[
        int,
        Field(description="1 = most disruptive to an import already done, 12 = least"),
    ]
    label: Annotated[
        str, Field(description="What this band of changes is, for display")
    ]
    changes: Annotated[
        list[dict[str, Any]],
        Field(
            description="Changes in this band; shape depends on their kind. Each may "
            "carry a `changelog` array of the entries CDISC published about it, present "
            "only where the release has a terminology-changes sheet that matched"
        ),
    ]


class PackageDiffReport(BaseModel):
    """A diff of one staged catalogue against the previous release of that catalogue."""

    catalogue: Annotated[
        str, Field(description="Catalogue name, for example `SDTM CT`")
    ]
    effective_date: Annotated[
        date, Field(description="Effective date of the package that was diffed")
    ]
    previous_available: Annotated[
        bool,
        Field(
            description="Whether a previous release of this catalogue is staged to "
            "compare against. False means either this is the first staged release of "
            "the catalogue, or its predecessor was never staged"
        ),
    ]
    previous_package_name: Annotated[
        str | None, Field(description="Package name of the release compared against")
    ] = None
    previous_effective_date: Annotated[
        date | None,
        Field(description="Effective date of the release compared against"),
    ] = None
    changelog_available: Annotated[
        bool,
        Field(
            description="Whether a terminology-changes sheet is staged for this release "
            "and was used to annotate the changes. False means none was uploaded, or "
            "`include_changelog` was off — not that CDISC reported nothing"
        ),
    ] = False
    counts: Annotated[
        dict[int, int], Field(description="Number of changes per severity level")
    ] = {}
    bands: Annotated[
        list[PackageDiffBand],
        Field(description="Non-empty severity bands, most disruptive first"),
    ] = []


class PackageDiffBandCount(BaseModel):
    """How many changes one severity band of a diff holds, without the changes."""

    level: Annotated[
        int,
        Field(description="1 = most disruptive to an import already done, 12 = least"),
    ]
    label: Annotated[
        str, Field(description="What this band of changes is, for display")
    ]
    count: Annotated[int, Field(description="Changes falling in this band")]


class PackageDiffSummary(BaseModel):
    """How much one staged catalogue changed, in counts only.

    What `PackageDiffReport` reports without the changes themselves — enough to show a
    reviewer where to look before they ask for the full diff of a catalogue. A release
    spans several catalogues, and a full diff of each runs to tens of thousands of
    changes, so listing them all at once is not a reasonable thing to ask for.
    """

    catalogue: Annotated[
        str, Field(description="Catalogue name, for example `SDTM CT`")
    ]
    effective_date: Annotated[
        date, Field(description="Effective date of the package that was diffed")
    ]
    previous_available: Annotated[
        bool,
        Field(
            description="Whether a previous release of this catalogue is staged to "
            "compare against. False means either this is the first staged release of "
            "the catalogue, or its predecessor was never staged — the bands are then "
            "empty, which is not an error"
        ),
    ]
    previous_package_name: Annotated[
        str | None, Field(description="Package name of the release compared against")
    ] = None
    previous_effective_date: Annotated[
        date | None,
        Field(description="Effective date of the release compared against"),
    ] = None
    changelog_available: Annotated[
        bool,
        Field(
            description="Whether a terminology-changes sheet is staged for this "
            "catalogue of the release. The full diff would annotate its changes with "
            "what CDISC published; nothing of that is counted here"
        ),
    ] = False
    total_changes: Annotated[
        int, Field(description="Changes found across every band")
    ] = 0
    bands: Annotated[
        list[PackageDiffBandCount],
        Field(description="Non-empty severity bands, most disruptive first"),
    ] = []


class InconsistencyCount(BaseModel):
    """How many review items of one type this release raised, and how they stand."""

    type: InconsistencyType
    total: int
    open: Annotated[
        int,
        Field(description="Still to be decided. Import is blocked while above zero."),
    ]
    auto_resolved: Annotated[int, Field(description="Settled by a stored rule")]
    resolved: Annotated[
        int, Field(description="Settled by a person, who changed a value")
    ]
    ignored: Annotated[int, Field(description="Accepted as-is")]
    informational: Annotated[
        int,
        Field(
            description="Not blocking, and cannot be — an advisory finding a person "
            "may still want to look at"
        ),
    ] = 0
    acknowledged: Annotated[
        int,
        Field(
            description="Settled by a person, who considered a fact about today's "
            "database and changed nothing"
        ),
    ] = 0


class AnalysisSummary(BaseModel):
    """Outcome of analysing one effective date."""

    effective_date: date
    status: EffectiveDateStatus
    analyzed_at: datetime
    catalogues: Annotated[
        list[str], Field(description="Catalogues contributing to this effective date")
    ]
    grouped_codelist_count: Annotated[
        int, Field(description="Distinct codelist concepts across all catalogues")
    ]
    grouped_term_count: Annotated[
        int, Field(description="Distinct term concepts across all catalogues")
    ]
    inconsistencies: Annotated[
        list[InconsistencyCount],
        Field(description="Review items raised, broken down by type and status"),
    ]
    open_inconsistency_count: Annotated[
        int,
        Field(
            description="Review items still to be resolved. Import is blocked while this is above zero."
        ),
    ]


class SponsorImpactSummary(BaseModel):
    """What this release would mean for the sponsor-defined content already in MDR."""

    effective_date: date
    status: EffectiveDateStatus
    assessed_at: datetime
    findings: Annotated[
        list[InconsistencyCount],
        Field(description="What the assessment raised, by kind and how it stands"),
    ] = []
    open_finding_count: Annotated[
        int,
        Field(
            description="Sponsor impact findings still to be settled. Import is blocked "
            "while this is above zero"
        ),
    ] = 0
    by_match_tier: Annotated[
        dict[str, int],
        Field(
            description="Collisions by how closely the values agree. Only `EXACT` breaks "
            "a uniqueness rule the main API enforces, and only those are left open by "
            "the shipped rules"
        ),
    ] = {}
    checked_codelists: Annotated[
        int,
        Field(
            description="Codelists this release introduces that were compared against "
            "every sponsor-defined codelist"
        ),
    ] = 0
    checked_memberships: Annotated[
        int,
        Field(
            description="Terms this release adds to a codelist that already holds "
            "sponsor-defined terms, each compared against them. A count of zero with no "
            "findings means nothing was comparable, not that nothing collides"
        ),
    ] = 0
    checked_semantically: Annotated[
        int,
        Field(
            description="Terms a language model was asked about, having found no string "
            "match. Zero means the question was never put — either no provider is "
            "configured or the strings had already answered for every addition — which is "
            "not the same as nothing being found"
        ),
    ] = 0
    checked_updated_terms: Annotated[
        int,
        Field(
            description="Terms this release changes whose name in MDR was compared "
            "against what the naming rules would produce today"
        ),
    ] = 0
    checked_removed_or_changed_terms: Annotated[
        int,
        Field(
            description="Terms this release changes the submission value of, or takes "
            "out of a codelist, checked against the MDR database for a downstream "
            "reference. A finding is raised only for the ones that have one — a count "
            "here with no matching finding means the rest were unreferenced, not that "
            "nothing was checked"
        ),
    ] = 0


class EffectiveDateSummary(BaseModel):
    """State of one CDISC release in the staging database."""

    effective_date: date
    status: EffectiveDateStatus
    files: list[StagedPackageFile]
    analyzed_at: datetime | None = None
    assessed_at: Annotated[
        datetime | None,
        Field(
            description="When sponsor impact was last assessed. An `analyzed_at` newer "
            "than this means the assessment no longer describes the release"
        ),
    ] = None
    imported_at: datetime | None = None
    open_inconsistency_count: int = 0
    pairing_files: Annotated[
        int,
        Field(
            description="Paired-codelist workbooks uploaded. Zero means no codelist "
            "pairings will be recorded for this release."
        ),
    ] = 0
    changelog_catalogues: Annotated[
        int,
        Field(
            description="Catalogues a terminology-changes spreadsheet has been "
            "uploaded for. Counted by catalogue rather than by file, because that is "
            "what a re-upload replaces. Purely informational — zero blocks nothing."
        ),
    ] = 0


class ConceptType(StrEnum):
    """What a history is of."""

    CODELIST = "codelist"
    TERM = "term"


class ConceptHistoryRelease(BaseModel):
    """One release in a concept's history."""

    package_name: Annotated[str, Field(description="For example `SDTM CT 2025-09-26`")]
    effective_date: date
    present: Annotated[
        bool, Field(description="Whether this release holds the concept at all")
    ]
    is_current: Annotated[
        bool, Field(description="The release the history was asked up to")
    ]
    is_earliest_staged: Annotated[
        bool,
        Field(
            description="Whether no earlier release of the catalogue is staged, so "
            "the history cannot go further back than this"
        ),
    ]


class ConceptHistoryAttribute(BaseModel):
    """One attribute of the concept, across the releases of the history."""

    field: Annotated[str, Field(description="Snapshot field name, e.g. `definition`")]
    values: Annotated[
        list[Any],
        Field(
            description="The value in each release, in the order of `releases`; null "
            "where the release does not hold the concept"
        ),
    ]


class ConceptHistoryCodelist(BaseModel):
    """A codelist named in a term's history."""

    concept_id: str
    submission_value: str | None = None


class ConceptHistoryMembershipChange(BaseModel):
    """The codelists a term entered and left in one release, against the one before."""

    entered: list[ConceptHistoryCodelist] = []
    left: list[ConceptHistoryCodelist] = []


class ConceptHistory(BaseModel):
    """A codelist or term across the last releases of a catalogue, up to one of them."""

    catalogue: str
    concept_id: str
    concept_type: ConceptType
    releases: Annotated[list[ConceptHistoryRelease], Field(description="Oldest first")]
    attributes: list[ConceptHistoryAttribute]
    membership_changes: Annotated[
        list[ConceptHistoryMembershipChange] | None,
        Field(
            description="Terms only: per release, in the order of `releases`, the "
            "codelists it entered and left since the release before. Empty for the "
            "oldest release, which has nothing before it in the history. Codelists "
            "the term stayed in are not listed"
        ),
    ] = None
