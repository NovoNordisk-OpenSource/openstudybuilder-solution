"""Working out what a release would change in MDR, and applying it.

The import is **append-only at the head**. It extends the newest state MDR holds with
one newer release; it never reconstructs history. That is what keeps it tractable —
a quarterly release only ever adds a version on top — and why a release older than
what MDR already has is refused rather than merged in. Populating MDR from scratch
stays the bootstrap script's job, run once per environment.

The other half of that bargain is that a run must be safe to repeat. Nothing here is
one large transaction: a release is tens of thousands of concepts. Instead every step
is idempotent, so a run that dies halfway can simply be run again. A version whose start
date already matches this release is recognised as already applied rather than stacked a
second time, and — because closing the old version and creating its replacement are two
separate steps — so is one merely *closed* at this release's date, which is what a run
that died between the two leaves behind.
"""

import logging
import uuid
from collections.abc import Collection
from datetime import date
from typing import Any

from common.auth.user import user
from common.exceptions import NotFoundException, ValidationException
from standards_import.models.imports import (
    EXAMPLE_LIMIT,
    ChangeCounts,
    ImportPreview,
    ImportRequest,
    MembershipChanges,
)
from standards_import.models.inconsistencies import (
    ANALYSIS_TYPES,
    EntityType,
    InconsistencyStatus,
    InconsistencyType,
    ResolutionStrategy,
    build_inconsistency_uid,
)
from standards_import.models.jobs import Job, JobKind, JobStatus
from standards_import.models.packages import EffectiveDateStatus
from standards_import.repositories import (
    analysis_repository,
    inconsistency_repository,
    job_repository,
    mdr_repository,
    release_repository,
    rules_repository,
    staging_repository,
)
from standards_import.repositories.staging_db import staging_session, to_native
from standards_import.services import job_service

log = logging.getLogger(__name__)

PAGE = 2000

# A release runs to tens of thousands of concepts and memberships. Writes go in chunks
# so no single transaction has to hold one, which is also what makes a failed run
# resumable rather than all-or-nothing.
WRITE_BATCH = 2000


def in_batches(rows: list[Any], write, *args) -> None:
    """Applies a write in chunks, skipping the call entirely when there is nothing."""

    for start in range(0, len(rows), WRITE_BATCH):
        write(rows[start : start + WRITE_BATCH], *args)


# Roman numerals and acronyms keep their case when a name is put into sentence case.
ROMAN_NUMERALS = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"}

# Sponsor impact decisions that take a sponsor term out of somebody's way. Both need the
# term to be unused, so both are checked before an import is accepted.
DISPLACING_STRATEGIES = {
    ResolutionStrategy.REMOVE_SPONSOR_FROM_CODELIST.value,
    ResolutionStrategy.RETIRE_SPONSOR_TERM.value,
}

# Everything a settled sponsor impact finding can ask the import to do, renaming included.
SPONSOR_ACTION_STRATEGIES = DISPLACING_STRATEGIES | {
    ResolutionStrategy.ADOPT_CDISC_NAME.value
}


def preview(effective_date: date) -> ImportPreview:
    """Works out what importing this release would do, writing nothing."""

    package_date = effective_date.isoformat()
    with staging_session() as session:
        release = require_release(session, package_date)
        delta = compute_delta(session, package_date)
        blockers = import_blockers(session, release, package_date, delta)

    return ImportPreview(
        effective_date=effective_date,
        release_status=release["status"],
        can_import=not blockers,
        blockers=blockers,
        catalogues=[pkg["name"] for pkg in delta["packages"]],
        new_packages=sorted(delta["new_package_uids"]),
        new_catalogues=sorted(delta["new_catalogue_names"]),
        codelists=counts_of(delta["codelists"]),
        terms=counts_of(delta["terms"]),
        memberships=MembershipChanges(
            added=len(delta["memberships_added"]),
            ended=len(delta["memberships_ended"]),
        ),
    )


def start_import(effective_date: date, request: ImportRequest) -> Job:
    """Checks the release may be imported and records a job to carry it out."""

    package_date = effective_date.isoformat()
    author_id = user().id()

    with staging_session() as session:
        release = require_release(session, package_date)
        delta = compute_delta(session, package_date)
        blockers = import_blockers(session, release, package_date, delta)
        ValidationException.raise_if(
            blockers,
            msg="This release cannot be imported: " + " ".join(blockers),
        )

        if request.expected_catalogues is not None:
            staged = {
                pkg["name"]
                for pkg in release_repository.get_packages(session, package_date)
            }
            expected = set(request.expected_catalogues)
            ValidationException.raise_if(
                staged != expected,
                msg=f"The release holds {sorted(staged)}, not the expected "
                f"{sorted(expected)}. Import is append-only, so a catalogue missing "
                "now could not be added afterwards.",
            )

        job_uid = uuid.uuid4().hex
        record = job_repository.start_job(
            session,
            job_uid,
            JobKind.IMPORT.value,
            package_date,
            author_id,
            status_while_running=EffectiveDateStatus.IMPORTING.value,
            status_on_success=EffectiveDateStatus.IMPORTED.value,
            status_on_failure=EffectiveDateStatus.READY.value,
        )

    ValidationException.raise_if(
        record is None,
        msg=f"Effective date '{package_date}' cannot start now because another step is already running against it.",
    )
    assert record is not None
    return job_service.job_to_model(record)


def run_import(job_uid: str, effective_date: date, author_id: str) -> None:
    """Applies a release to MDR. Runs in the background; failures land on the job."""

    package_date = effective_date.isoformat()
    try:
        with staging_session() as session:
            delta = compute_delta(session, package_date)
            stats = apply_delta(session, package_date, delta, author_id)
        with staging_session() as session:
            job_repository.finish_job(
                session, job_uid, JobStatus.SUCCEEDED.value, stats=stats
            )
        log.info("Import %s of %s finished: %s", job_uid, package_date, stats)
    except Exception as exc:  # pylint: disable=broad-except
        log.exception("Import %s of %s failed", job_uid, package_date)
        with staging_session() as session:
            job_repository.finish_job(
                session, job_uid, JobStatus.FAILED.value, error=str(exc)
            )


# --- guards ---------------------------------------------------------------------


def import_blockers(
    session, release: dict[str, Any], package_date: str, delta: dict[str, Any]
) -> list[str]:
    """Returns the reasons this release may not be imported, in plain words.

    Of `delta`, only `memberships_added` and `memberships_ended` are read — which is
    what lets the dashboard pass the stored `membership_changes` of the review snapshot
    instead of a delta worked out afresh.
    """

    blockers = []

    if not rules_repository.get_import_enabled(session):
        blockers.append(
            "Importing into the OSB database is disabled in the Standards Import "
            "Configuration. Review is still possible; enable the import there to "
            "promote this release."
        )

    if release["status"] == EffectiveDateStatus.FILES_STAGED.value:
        blockers.append("It has not been analysed yet.")
    if release["status"] == EffectiveDateStatus.IMPORTED.value:
        blockers.append("It has already been imported.")
    if release["status"] == EffectiveDateStatus.IMPORTING.value:
        blockers.append("An import of it is already running.")
    if release["status"] == EffectiveDateStatus.ANALYZING.value:
        blockers.append("An analysis of it is currently running.")
    if release["status"] == EffectiveDateStatus.ASSESSING.value:
        blockers.append("A sponsor impact assessment of it is currently running.")

    open_count = release.get("open_inconsistency_count") or 0
    if open_count:
        blockers.append(
            f"{open_count} review items are still open; staging holds the pecking "
            "order's pick for those, which is a guess rather than a decision."
        )

    # Resolving the last open item flips the release to ANALYZED on its own, so status
    # alone would let an import run against values the decisions were never applied to.
    pending = inconsistency_repository.count_decisions_since_analysis(
        session, package_date, sorted(ANALYSIS_TYPES)
    )
    if pending:
        blockers.append(
            f"{pending} decisions have been made since the last analysis. Deciding "
            "records the choice; analysis is what applies it to the staged values. "
            "Re-run the analysis so the import sees them."
        )

    # The sponsor impact assessment is not optional, because it is the only thing that
    # looks at what this release would land on. A CDISC term arriving with the name of a
    # sponsor term already in that codelist breaks a uniqueness rule the main API
    # enforces and this app's Cypher does not — it would import quietly and leave a
    # codelist the main API then refuses to edit.
    assessed_at = to_native(release.get("assessed_at"))
    analyzed_at = to_native(release.get("analyzed_at"))
    if assessed_at is None:
        blockers.append(
            "Sponsor impact has not been assessed. Run "
            f"POST /effective-dates/{package_date}/sponsor-impact first; what this "
            "release collides with in the MDR database is not visible from the CDISC "
            "side of it."
        )
    elif analyzed_at is not None and analyzed_at > assessed_at:
        blockers.append(
            "The release has been analysed since sponsor impact was last assessed, so "
            "that assessment was made against values that have since been rebuilt. "
            "Assess it again."
        )

    # Excluding this release: a retry after a failed run must not be blocked by the
    # packages that run had already created. Its own `IMPORTED` status is what stops a
    # release being imported twice.
    head = mdr_repository.get_head_effective_date(excluding=package_date)
    if head and head >= package_date:
        blockers.append(
            f"The MDR database already holds {head}, and the import only ever appends "
            f"to the head. Loading {package_date} would mean rewriting history, which "
            "is the bootstrap import's job."
        )

    if job_repository.find_running_job(session, package_date):
        blockers.append("A job for this release is already running.")

    blockers.extend(sponsor_terms_no_longer_free(session, package_date))
    blockers.extend(cdisc_term_changes_still_in_use(session, package_date, delta))

    return blockers


def sponsor_terms_no_longer_free(session, package_date: str) -> list[str]:
    """Refuses an import that would displace a sponsor term something has started using.

    The same check the resolution endpoint makes, made again here because the answer can
    change between deciding and importing — somebody builds a study on the sponsor term
    in the meantime, and the decision to retire it is suddenly a decision to break their
    study. Caught before the run starts rather than during it, so nothing is half-written.
    """

    actions = inconsistency_repository.get_sponsor_actions(
        session, package_date, sorted(DISPLACING_STRATEGIES)
    )
    if not actions:
        return []

    usage = mdr_repository.get_term_usage(
        sorted({action["resolved_value"] for action in actions})
    )
    in_use = sorted(uid for uid, entries in usage.items() if entries)
    if not in_use:
        return []

    return [
        (
            f"{len(in_use)} sponsor term(s) settled for removal are now referred to by "
            f"something else ({', '.join(in_use)}). Move that usage through the main API, "
            "then assess this release again and decide afresh."
        )
    ]


def changed_and_removed_memberships(
    delta: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Splits `diff_memberships`' `ended` rows into value changes and genuine removals.

    A submission-value change and a term leaving the codelist look identical there —
    both close the old (codelist, term, value) triple, and a change also opens a new
    one for the same (codelist, term) pair. Pairing by that pair is what tells them
    apart, and it is done here once rather than by every caller that needs it.
    """

    added_by_pair = {
        (row["codelist_uid"], row["term_uid"]): row
        for row in delta["memberships_added"]
    }
    ended_by_pair = {
        (row["codelist_uid"], row["term_uid"]): row
        for row in delta["memberships_ended"]
    }

    changed = [
        {
            "codelist_uid": pair[0],
            "term_uid": pair[1],
            "old": ended_by_pair[pair],
            "new": added_by_pair[pair],
        }
        for pair in sorted(added_by_pair.keys() & ended_by_pair.keys())
    ]
    removed = [row for pair, row in ended_by_pair.items() if pair not in added_by_pair]
    return changed, removed


def cdisc_term_changes_still_in_use(
    session, package_date: str, delta: dict[str, Any]
) -> list[str]:
    """Refuses an import that would carry a CDISC change past a reference nobody has
    acknowledged.

    A term this release changes or removes from a codelist only ever gets a finding
    when something already refers to it — see `sponsor_impact_service`
    `collect_used_term_changes` — so a term that fell into use *after* a clean
    assessment has no finding for the generic "open review items" blocker to catch.
    Checked again here for the same reason `sponsor_terms_no_longer_free` is: the answer
    can change between assessing and importing.
    """

    changed, removed = changed_and_removed_memberships(delta)
    pairs = [
        (
            row["codelist_uid"],
            row["term_uid"],
            InconsistencyType.CDISC_TERM_SUBMISSION_VALUE_CHANGED,
        )
        for row in changed
    ] + [
        (
            row["codelist_uid"],
            row["term_uid"],
            InconsistencyType.CDISC_TERM_REMOVED_FROM_CODELIST,
        )
        for row in removed
    ]
    if not pairs:
        return []

    usage = mdr_repository.get_membership_usage(
        sorted({(pair[0], pair[1]) for pair in pairs})
    )
    uids = {
        pair: build_inconsistency_uid(
            package_date,
            EntityType.CODELIST,
            pair[0],
            pair[2],
            related_concept_id=pair[1],
        )
        for pair in pairs
    }
    statuses = inconsistency_repository.statuses_of(session, sorted(set(uids.values())))

    # None means no finding exists at all — usage that appeared after a clean
    # assessment, which never raised one. OPEN means it did and nobody has settled it.
    # Either way there is nothing acknowledging the reference; anything else (RESOLVED,
    # via ACKNOWLEDGE) means somebody already has.
    unacknowledged = [
        pair
        for pair in pairs
        if sum(entry["count"] for entry in usage.get((pair[0], pair[1]), ())) > 0
        and statuses.get(uids[pair]) in (None, InconsistencyStatus.OPEN.value)
    ]
    if not unacknowledged:
        return []

    return [
        (
            f"{len(unacknowledged)} CDISC term change(s)/removal(s) are referred to by "
            "something else and have not been acknowledged "
            f"({', '.join(sorted({pair[1] for pair in unacknowledged}))}). Assess this "
            "release again, or settle it with ACKNOWLEDGE."
        )
    ]


def require_release(session, package_date: str) -> dict[str, Any]:
    record = staging_repository.find_effective_date(session, package_date)
    if record is None:
        raise NotFoundException(
            msg=f"No files have been staged for effective date '{package_date}'."
        )
    return record


# --- the delta ------------------------------------------------------------------


def compute_delta(session, package_date: str) -> dict[str, Any]:
    """Compares the release against what MDR currently holds."""

    packages = release_repository.get_packages(session, package_date)
    for pkg in packages:
        pkg["uid"] = package_uid(pkg["name"])
        pkg["catalogue_name"] = analysis_repository.catalogue_name(pkg["name"])
        pkg["prior_uid"] = package_uid(pkg["prior_name"]) if pkg["prior_name"] else None

    existing_packages = mdr_repository.get_existing_packages(
        [pkg["uid"] for pkg in packages]
    )
    existing_catalogues = mdr_repository.get_existing_catalogues(
        [pkg["catalogue_name"] for pkg in packages]
    )

    codelists = diff_codelists(session, package_date)
    terms = diff_terms(session, package_date)
    names = {
        row["concept_id"]: (row["props"] or {}).get("name") or ""
        for row in codelists["all"]
    }
    added, ended, ordinal_uids = diff_memberships(
        session, package_date, codelists["all_uids"], names
    )

    return {
        "packages": packages,
        "new_package_uids": {
            pkg["uid"] for pkg in packages if pkg["uid"] not in existing_packages
        },
        "new_catalogue_names": {
            pkg["catalogue_name"]
            for pkg in packages
            if pkg["catalogue_name"] not in existing_catalogues
        },
        "codelists": codelists,
        "terms": terms,
        "memberships_added": added,
        "memberships_ended": ended,
        "ordinal_codelist_uids": ordinal_uids,
    }


def diff_codelists(session, package_date: str) -> dict[str, Any]:
    rows = release_repository.get_codelists(session, package_date)
    heads = mdr_repository.get_codelist_heads(
        [row["concept_id"] for row in rows], package_date
    )

    new, updated, unchanged = [], [], []
    for row in rows:
        wanted = codelist_attributes(row["concept_id"], row["props"])
        row["attributes"] = wanted
        head = heads.get(row["concept_id"])
        # Kept on the row, mirroring `diff_terms`, for the codelist review endpoints —
        # showing what changed means showing what it changed *from*.
        row["head"] = head
        if head is None:
            row["version"] = "1.0"
            new.append(row)
        elif values_differ(wanted, head["props"]):
            row["version"] = next_version(head["version"])
            updated.append(row)
        else:
            unchanged.append(row)

    return {
        "new": new,
        "updated": updated,
        "unchanged": unchanged,
        "all": rows,
        "all_uids": [row["concept_id"] for row in rows],
    }


def diff_codelist_terms(session, package_date: str, codelist_id: str) -> dict[str, Any]:
    """Same shape as `diff_terms`, scoped to one codelist's current members.

    `diff_terms` walks every term in the release — tens of thousands — to build the
    release-wide picture `preview()` needs. A reviewer looking at one codelist needs
    only its own members, typically a handful to a few hundred, so this reads and
    diffs only those rather than paying the whole release's cost for one row of it.
    """

    rows = release_repository.get_codelist_terms(session, package_date, codelist_id)
    heads = mdr_repository.get_term_heads(
        [row["concept_id"] for row in rows], package_date
    )

    new, updated, unchanged = [], [], []
    for row in rows:
        wanted = term_attributes(row["concept_id"], row["props"])
        row["attributes"] = wanted
        head = heads.get(row["concept_id"])
        row["head"] = head
        if head is None:
            row["version"] = "1.0"
            new.append(row)
        elif values_differ(wanted, head["props"]):
            row["version"] = next_version(head["version"])
            updated.append(row)
        else:
            unchanged.append(row)

    return {"new": new, "updated": updated, "unchanged": unchanged, "all": rows}


def diff_codelist_memberships(
    package_date: str,
    codelist_id: str,
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Which of one codelist's memberships this release opens or closes.

    `rows` is what `diff_codelist_terms` already read for the same codelist — its
    current members with their settled submission values — so this reads staging no
    further; only MDR's own open memberships need a fresh read. Ordinal scoring is left
    to the release-wide `diff_memberships`, which is what the import itself uses; these
    two are for display, not for writing.
    """

    wanted = {(codelist_id, row["concept_id"], row["submission_value"]) for row in rows}
    existing = mdr_repository.get_open_memberships([codelist_id])
    added = [as_membership(item, package_date) for item in sorted(wanted - existing)]
    ended = [as_membership(item, package_date) for item in sorted(existing - wanted)]
    return added, ended


def diff_terms(session, package_date: str) -> dict[str, Any]:
    total = release_repository.count_terms(session, package_date)
    new, updated, unchanged, everything = [], [], [], []

    for skip in range(0, total, PAGE):
        rows = release_repository.get_terms(session, package_date, skip, PAGE)
        heads = mdr_repository.get_term_heads(
            [row["concept_id"] for row in rows], package_date
        )
        for row in rows:
            wanted = term_attributes(row["concept_id"], row["props"])
            row["attributes"] = wanted
            head = heads.get(row["concept_id"])
            # Kept on the row for the sponsor impact assessment, which has to ask what
            # the naming rules produced from the *previous* CDISC preferred term to tell
            # a name this release moved from one that was already adrift.
            row["head"] = head
            if head is None:
                row["version"] = "1.0"
                new.append(row)
            elif values_differ(wanted, head["props"]):
                row["version"] = next_version(head["version"])
                updated.append(row)
            else:
                unchanged.append(row)
            everything.append(row)

    return {
        "new": new,
        "updated": updated,
        "unchanged": unchanged,
        "all": everything,
    }


def diff_memberships(
    session, package_date: str, codelist_uids: list[str], names: dict[str, str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], set[str]]:
    """Works out which codelist memberships this release opens and which it closes.

    Also reports which codelists are scored scales, which is decided here because it
    takes the whole release's memberships — a codelist can be scored by terms MDR
    already holds, not only by the ones this release adds.
    """

    total = release_repository.count_memberships(session, package_date)
    wanted: set[tuple[str, str, str]] = set()
    for skip in range(0, total, PAGE):
        for row in release_repository.get_memberships(
            session, package_date, skip, PAGE
        ):
            wanted.add((row["codelist_id"], row["term_id"], row["submission_value"]))

    existing = mdr_repository.get_open_memberships(codelist_uids)

    ordinal_uids = ordinal_codelists(wanted, names)
    added = [
        as_membership(item, package_date, ordinal_uids)
        for item in sorted(wanted - existing)
    ]
    ended = [as_membership(item, package_date) for item in sorted(existing - wanted)]
    return added, ended, ordinal_uids


# --- applying -------------------------------------------------------------------


def apply_delta(
    session, package_date: str, delta: dict[str, Any], author_id: str
) -> dict[str, Any]:
    """Writes the release to MDR, in an order that leaves it usable if interrupted."""

    mdr_repository.ensure_indexes()
    mdr_repository.ensure_library()
    mdr_repository.ensure_packages(delta["packages"], author_id)

    codelists, terms = delta["codelists"], delta["terms"]

    mdr_repository.ensure_codelist_roots(
        [row["concept_id"] for row in codelists["new"]]
    )
    mdr_repository.ensure_term_roots([row["concept_id"] for row in terms["new"]])

    mdr_repository.link_codelists_to_catalogues(
        [
            {
                "catalogue_name": analysis_repository.catalogue_name(pkg),
                "codelist_uid": row["concept_id"],
            }
            for row in codelists["all"]
            for pkg in row["packages"]
        ]
    )

    for spec, changed in (
        (
            ("CTCodelistRoot", "CTCodelistAttributesRoot", "CTCodelistAttributesValue"),
            codelists,
        ),
        (("CTTermRoot", "CTTermAttributesRoot", "CTTermAttributesValue"), terms),
    ):
        root_label, attributes_root_label, value_label = spec
        in_batches(
            [
                {"uid": row["concept_id"], "effective_date": package_date}
                for row in changed["updated"]
            ],
            lambda rows, a=attributes_root_label, r=root_label: mdr_repository.close_versions(
                a, r, rows
            ),
        )
        in_batches(
            [
                {
                    "uid": row["concept_id"],
                    "effective_date": package_date,
                    "version": row["version"],
                    "props": row["attributes"],
                    "change_description": description,
                }
                for rows, description in (
                    (changed["new"], "Initial CDISC import"),
                    (changed["updated"], f"CDISC release {package_date}"),
                )
                for row in rows
            ],
            lambda rows, r=root_label, a=attributes_root_label, v=value_label: mdr_repository.create_attribute_versions(
                r, a, v, rows, author_id
            ),
        )

    in_batches(
        [
            {
                "uid": row["concept_id"],
                "effective_date": package_date,
                "props": codelist_name(
                    row["props"],
                    row["concept_id"] in delta["ordinal_codelist_uids"],
                ),
            }
            for row in codelists["new"]
        ],
        lambda rows: mdr_repository.create_name_versions(
            "CTCodelistRoot",
            "CTCodelistNameRoot",
            "CTCodelistNameValue",
            rows,
            author_id,
        ),
    )
    in_batches(
        [
            {
                "uid": row["concept_id"],
                "effective_date": package_date,
                "props": term_name(row["props"]),
            }
            for row in terms["new"]
        ],
        lambda rows: mdr_repository.create_name_versions(
            "CTTermRoot", "CTTermNameRoot", "CTTermNameValue", rows, author_id
        ),
    )

    in_batches(delta["memberships_added"], mdr_repository.add_memberships, author_id)
    in_batches(delta["memberships_ended"], mdr_repository.end_memberships, author_id)

    paired, renamed = apply_review_decisions(session, package_date, delta)
    sponsor = apply_sponsor_decisions(session, package_date, author_id)
    write_package_contents(session, package_date, delta)

    return {
        "codelists_created": len(codelists["new"]),
        "codelists_versioned": len(codelists["updated"]),
        "codelists_unchanged": len(codelists["unchanged"]),
        "terms_created": len(terms["new"]),
        "terms_versioned": len(terms["updated"]),
        "terms_unchanged": len(terms["unchanged"]),
        "memberships_added": len(delta["memberships_added"]),
        "memberships_ended": len(delta["memberships_ended"]),
        "packages_created": len(delta["new_package_uids"]),
        "codelists_paired": paired,
        "sponsor_names_applied": renamed,
        **sponsor,
    }


def apply_review_decisions(
    session, package_date: str, delta: dict[str, Any]
) -> tuple[int, int]:
    """Applies the pairing and naming decisions taken during review.

    Sponsor names are applied only to terms this import created. The name of a term MDR
    already held belongs to whoever edited it last, and a review item is never raised
    for one.
    """

    resolutions = inconsistency_repository.get_resolutions_for_date(
        session, package_date
    )
    new_term_ids = {row["concept_id"] for row in delta["terms"]["new"]}

    pairings: list[dict[str, Any]] = []
    names: list[dict[str, Any]] = []
    for resolution in resolutions:
        value = resolution.get("resolved_value")
        if not value:
            continue
        if resolution["type"] == InconsistencyType.CODELIST_PAIRING.value:
            pairings.append(
                {"codelist_uid": resolution["concept_id"], "paired_uid": value}
            )
        elif (
            resolution["type"] == InconsistencyType.SPONSOR_NAME.value
            and resolution["concept_id"] in new_term_ids
        ):
            names.append(
                {
                    "uid": resolution["concept_id"],
                    "name": value,
                    "name_sentence_case": sentence_case(str(value)),
                    "effective_date": package_date,
                }
            )

    in_batches(pairings, mdr_repository.pair_codelists)
    in_batches(names, mdr_repository.set_term_names)
    return len(pairings), len(names)


def apply_sponsor_decisions(
    session, package_date: str, author_id: str
) -> dict[str, int]:
    """Carries out what was decided about the sponsor content this release lands on.

    The only place this app writes to something the sponsor owns rather than to the CDISC
    library, and every row here traces back to a person settling a review item — nothing
    is inferred and no rule can produce one, which is why `RETIRE_SPONSOR_TERM` and its
    two siblings are refused as standing rules.

    Retiring implies removal from the codelist as well: retirement is what satisfies the
    main API's name-uniqueness rule, and closing the membership is what actually takes the
    duplicate out of the codelist. Doing one without the other leaves the job half done in
    a way that is hard to see afterwards.
    """

    actions = inconsistency_repository.get_sponsor_actions(
        session, package_date, sorted(SPONSOR_ACTION_STRATEGIES)
    )
    if not actions:
        return {
            "sponsor_terms_retired": 0,
            "sponsor_memberships_closed": 0,
            "sponsor_names_adopted": 0,
        }

    retire: list[dict[str, Any]] = []
    close: list[dict[str, Any]] = []
    rename: list[dict[str, Any]] = []

    for action in actions:
        term_uid, strategy = action["resolved_value"], action["strategy"]
        if strategy == ResolutionStrategy.ADOPT_CDISC_NAME.value:
            rename.append(
                {
                    "uid": action["concept_id"],
                    "name": term_uid,
                    "name_sentence_case": sentence_case(str(term_uid)),
                    "effective_date": package_date,
                    "change_description": f"Renamed with CDISC release {package_date}",
                }
            )
            continue

        close.append(
            {
                "codelist_uid": action["concept_id"],
                "term_uid": term_uid,
                "effective_date": package_date,
            }
        )
        if strategy == ResolutionStrategy.RETIRE_SPONSOR_TERM.value:
            retire.append(
                {
                    "uid": term_uid,
                    "effective_date": package_date,
                    "change_description": f"Superseded by CDISC release {package_date}",
                }
            )

    heads = mdr_repository.get_term_name_versions([row["uid"] for row in rename])
    for row in rename:
        row["version"] = next_version(heads.get(row["uid"]))

    in_batches(close, mdr_repository.close_sponsor_memberships, author_id)
    in_batches(retire, mdr_repository.retire_terms, author_id)
    in_batches(rename, mdr_repository.append_name_versions, author_id)

    return {
        "sponsor_terms_retired": len(retire),
        "sponsor_memberships_closed": len(close),
        "sponsor_names_adopted": len(rename),
    }


def write_package_contents(session, package_date: str, delta: dict[str, Any]) -> None:
    """Records what each package held, which is what the package-changes views read."""

    codelist_rows = [
        {
            "package_uid": package_uid(pkg),
            "codelist_uid": row["concept_id"],
            "uid": f"{package_uid(pkg)}_{row['concept_id']}",
        }
        for row in delta["codelists"]["all"]
        for pkg in row["packages"]
    ]
    in_batches(codelist_rows, mdr_repository.create_package_codelists)

    # The settled submission value, which is what MDR stores for the membership.
    submission_values = {
        (row["codelist_id"], row["term_id"]): row["submission_value"]
        for skip in range(
            0, release_repository.count_memberships(session, package_date), PAGE
        )
        for row in release_repository.get_memberships(session, package_date, skip, PAGE)
    }

    # Which term each package put in which codelist has to come from the raw layer.
    # Crossing the grouped memberships with the packages that merely *define* a term
    # would let a package claim a membership it never shipped, whenever catalogues
    # disagree on a codelist's terms and the union was kept.
    term_rows = []
    for skip in range(
        0, release_repository.count_raw_memberships(session, package_date), PAGE
    ):
        for row in release_repository.get_raw_memberships(
            session, package_date, skip, PAGE
        ):
            uid = package_uid(row["package_name"])
            key = (row["codelist_id"], row["term_id"])
            if key not in submission_values:
                # Dropped from the codelist by a resolution, so it is not a membership
                # of this release however the package shipped it.
                continue
            term_rows.append(
                {
                    "package_codelist_uid": f"{uid}_{row['codelist_id']}",
                    "term_uid": row["term_id"],
                    "uid": f"{uid}_{row['term_id']}",
                    "submission_value": submission_values[key],
                }
            )
    in_batches(term_rows, mdr_repository.create_package_terms)


# --- shaping --------------------------------------------------------------------


def codelist_attributes(concept_id: str, props: dict[str, Any]) -> dict[str, Any]:
    """Maps a settled codelist onto the properties MDR stores.

    `preferred_term` takes the codelist's name rather than its CDISC `preferredTerm`,
    matching what the bootstrap import writes. Diverging would make every codelist look
    changed the first time this runs against a bootstrapped database.
    """

    return {
        "name": props.get("name"),
        "preferred_term": props.get("name"),
        "submission_value": props.get("submissionValue"),
        "definition": props.get("definition"),
        "concept_id": concept_id,
        "extensible": as_bool(props.get("extensible")),
        "synonyms": props.get("synonyms") or [],
    }


def term_attributes(concept_id: str, props: dict[str, Any]) -> dict[str, Any]:
    return {
        "preferred_term": props.get("preferredTerm"),
        "definition": props.get("definition"),
        "concept_id": concept_id,
        "synonyms": props.get("synonyms") or [],
    }


ORDINAL_NAME_MARKER = "STRESC"


def ordinal_value(submission_value: str | None) -> float | None:
    """The rank a submission value carries, or None where it does not carry one.

    Ordinal codelists are scored scales, but they still hold terms like `Unknown`
    alongside the numbers. Those are members of the codelist with no rank, so they get
    no `ordinal` at all rather than a placeholder.
    """

    try:
        return float(int(str(submission_value)))
    except TypeError, ValueError:
        return None


def ordinal_codelists(
    memberships: set[tuple[str, str, str]], names: dict[str, str]
) -> set[str]:
    """The codelists in this release that are scored scales.

    Two conditions, both required: the name marks it as a result scale, and at least one
    term is actually scored. `Rutgeerts Score … STRESC` grades `i0` to `i4` and `Tanner
    Scale … STRESC` grades `Stage 1` to `Stage 5`, so the name alone is not enough.
    """

    scored: set[str] = set()
    for codelist_id, _term_id, submission_value in memberships:
        if codelist_id in scored:
            continue
        if ORDINAL_NAME_MARKER not in (names.get(codelist_id) or ""):
            continue
        if ordinal_value(submission_value) is not None:
            scored.add(codelist_id)
    return scored


def codelist_name(props: dict[str, Any], is_ordinal: bool = False) -> dict[str, Any]:
    name = props.get("name") or ""
    return {
        "name": name,
        "name_sentence_case": sentence_case(name),
        "is_ordinal": is_ordinal,
        "codelist_type": "Standard",
    }


def term_name(props: dict[str, Any]) -> dict[str, Any]:
    """The sponsor preferred name of a term new to MDR.

    Falls back to the CDISC preferred term, which is where the bootstrap script's
    sponsor-naming rules also start. Those rules are per-codelist and hand-written;
    turning them into review items belongs with the pairing work, not here.
    """

    name = props.get("preferredTerm") or ""
    return {"name": name, "name_sentence_case": sentence_case(name)}


def sentence_case(value: str) -> str:
    """Lowercases a name, leaving acronyms and roman numerals alone.

    Approximates the bootstrap script's transform. The main API only requires that this
    be a case-variant of the name, which any result here satisfies.
    """

    words = []
    for word in value.split(" "):
        if (word.isupper() and len(word) > 1) or word.upper() in ROMAN_NUMERALS:
            words.append(word)
        else:
            words.append(word.lower())
    return " ".join(words)


def values_differ(wanted: dict[str, Any], head: dict[str, Any]) -> bool:
    """Compares what this release says with what MDR holds.

    `extensible` is normalised on both sides: CDISC ships it as the string `"true"`,
    and the bootstrap import stores that string even though the schema declares a
    boolean. Comparing them raw would mark every codelist as changed.
    """

    for key, value in wanted.items():
        current = head.get(key)
        if key == "extensible":
            if as_bool(value) != as_bool(current):
                return True
        elif key == "synonyms":
            if sorted(value or []) != sorted(current or []):
                return True
        elif value != current:
            return True
    return False


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "y")
    return bool(value)


def next_version(current: str | None) -> str:
    """Bumps to the next major version, which is what a new Final release is."""

    try:
        major = int(str(current or "0.0").split(".", maxsplit=1)[0])
    except ValueError:
        major = 0
    return f"{major + 1}.0"


def package_uid(name: str) -> str:
    return name.replace(" ", "__")


def as_membership(
    item: tuple[str, str, str],
    package_date: str,
    ordinal_uids: Collection[str] = frozenset(),
) -> dict[str, Any]:
    codelist_uid, term_uid, submission_value = item
    return {
        "codelist_uid": codelist_uid,
        "term_uid": term_uid,
        "submission_value": submission_value,
        "effective_date": package_date,
        "ordinal": (
            ordinal_value(submission_value) if codelist_uid in ordinal_uids else None
        ),
    }


def counts_of(bucket: dict[str, Any]) -> ChangeCounts:
    return ChangeCounts(
        new=len(bucket["new"]),
        updated=len(bucket["updated"]),
        unchanged=len(bucket["unchanged"]),
        new_examples=[row["concept_id"] for row in bucket["new"][:EXAMPLE_LIMIT]],
        updated_examples=[
            row["concept_id"] for row in bucket["updated"][:EXAMPLE_LIMIT]
        ],
    )
