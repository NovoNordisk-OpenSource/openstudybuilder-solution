"""The rows of the release review lists, worked out once rather than on every page.

`list_codelists` and `list_terms` page through every codelist and term a release
touches, and what each row says about the *change* — new or updated, how many of a
codelist's terms moved, which properties a term's update touches — comes from
`compute_delta`, a diff of the whole release against MDR. Recomputing it for every page
of ten rows is what made the review slow, so it is worked out here at the end of
analysis and stored — see `review_snapshot_repository` for where.

The release-wide figures the dashboard shows — change counts, catalogues, and the
membership changes its import blockers check — come from the same delta, so they are
stored with the rows (`build_release_summary`). The import itself does not read them: it
still diffs live before it starts, since that is the check that actually guards MDR.

Not stored: what moves while a person reviews. Finding counts and review records are
read live by `codelist_service`, one release-wide query each, and joined onto these
rows there. Settling a finding or marking a codelist reviewed therefore never has to
touch the snapshot.

The snapshot holds while MDR's head — the newest package MDR holds, this release's own
left out — is the one it was taken against. That head only moves when a release is
imported, and an import is the only thing that changes what this release's delta
against MDR is. Leaving this release out of the head means importing it does *not*
invalidate its own snapshot: the review keeps showing what the release changed, rather
than a release that, once in MDR, changes nothing. Re-analysing or re-uploading clears
the stamp outright.

A release without a usable snapshot — analysed before snapshots existed, or overtaken
by an import — is rebuilt on its next read, so nothing has to backfill one.
"""

import logging
from collections import Counter, defaultdict
from typing import Any, NamedTuple

from standards_import.models.codelists import (
    AttributeChange,
    ImpactedProperty,
    TermChangeStatus,
)
from standards_import.models.imports import EXAMPLE_LIMIT
from standards_import.repositories import (
    job_repository,
    mdr_repository,
    release_repository,
    review_snapshot_repository,
)
from standards_import.repositories.staging_db import StagingSession
from standards_import.services import import_service

log = logging.getLogger(__name__)

CODELIST_FIELDS = ("name", "definition", "submission_value", "extensible", "synonyms")
"""`codelist_attributes`' keys, less `preferred_term` (which mirrors `name` by
construction) and `concept_id` (identity, not a property)."""

TERM_FIELDS = ("preferred_term", "definition", "synonyms")
"""`term_attributes`' keys, less `concept_id`. Must stay in step with that function, or
what a term reports as impacted disagrees with what `values_differ` called updated."""

MEMBERSHIP_KEYS = ("codelist_uid", "term_uid", "submission_value")
"""What `import_service.changed_and_removed_memberships` and the blocker built on it
read of a membership row; the rest of `as_membership` is for writing it to MDR."""


class ReviewSnapshot(NamedTuple):
    """Everything worked out from the delta: the codelist rows and the term rows, as
    `build_codelist_rows`/`build_term_rows` return them, and the dashboard's
    `build_release_summary`."""

    codelists: list[dict[str, Any]]
    terms: list[dict[str, Any]]
    summary: dict[str, Any]


def codelist_rows(session: StagingSession, package_date: str) -> list[dict[str, Any]]:
    """Every codelist row of the release — stored, or rebuilt first if they no longer
    hold."""

    built = ensure_review_snapshot(session, package_date)
    if built is not None:
        return built.codelists
    return review_snapshot_repository.get_codelist_rows(session, package_date)


def term_rows(session: StagingSession, package_date: str) -> list[dict[str, Any]]:
    """Every term row of the release — stored, or rebuilt first if they no longer
    hold."""

    built = ensure_review_snapshot(session, package_date)
    if built is not None:
        return built.terms
    return review_snapshot_repository.get_term_rows(session, package_date)


def dashboard_inputs(
    session: StagingSession, package_date: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """The release summary and every codelist row, behind one validity check — so that
    while a step runs, and nothing is stored, the delta is still worked out only once.
    """

    built = ensure_review_snapshot(session, package_date)
    if built is None:
        summary = review_snapshot_repository.get_release_summary(session, package_date)
        # Held a moment ago; an analysis starting since has just cleared it.
        if summary is not None:
            return summary, review_snapshot_repository.get_codelist_rows(
                session, package_date
            )
        built = build_rows(session, package_date)
    return built.summary, built.codelists


def ensure_review_snapshot(
    session: StagingSession, package_date: str
) -> ReviewSnapshot | None:
    """None while the stored snapshot holds; otherwise the rows, built afresh.

    Built rows are stored too, unless a step is running against the release: an
    analysis is about to replace what they were built from, and an import of this very
    release is moving MDR under them. Those rows are still returned — the reader gets
    what a read would have shown before snapshots existed — just not kept.
    """

    stamp = review_snapshot_repository.get_snapshot_stamp(session, package_date)
    mdr_head = mdr_repository.get_head_effective_date(excluding=package_date)
    if snapshot_holds(stamp, mdr_head):
        return None
    if job_repository.find_running_job(session, package_date) is not None:
        return build_rows(session, package_date)
    log.info(
        "Review snapshot of %s is missing or out of date; rebuilding", package_date
    )
    return rebuild(session, package_date)


def snapshot_holds(stamp: dict[str, Any] | None, mdr_head: str | None) -> bool:
    """Whether a stored snapshot was taken against the MDR head there is now.

    `mdr_head` is None while MDR holds no package at all, which is a head like any
    other: a snapshot taken against an empty MDR holds until something is imported.
    A snapshot taken before it carried a release summary does not hold either, so the
    dashboard never finds the rows without the figures that go with them.
    """

    return (
        stamp is not None
        and stamp.get("snapshot_at") is not None
        and bool(stamp.get("has_summary"))
        and stamp.get("mdr_head") == mdr_head
    )


def rebuild(session: StagingSession, package_date: str) -> ReviewSnapshot:
    """Works the rows out from the release-wide delta and stores them.

    The MDR head is read before the delta, not after: should an import land in between,
    the snapshot is stamped with the older head and the next read rebuilds it, rather
    than vouching for a delta taken half before and half after.
    """

    mdr_head = mdr_repository.get_head_effective_date(excluding=package_date)
    built = build_rows(session, package_date)
    review_snapshot_repository.save_codelist_rows(
        session, package_date, built.codelists
    )
    review_snapshot_repository.save_term_rows(session, package_date, built.terms)
    review_snapshot_repository.set_snapshot_stamp(
        session, package_date, mdr_head, built.summary
    )
    return built


def build_rows(session: StagingSession, package_date: str) -> ReviewSnapshot:
    """The reads the three builders need, done once for all of them.

    `compute_delta` is the expensive part. The memberships pass is the one thing a
    per-codelist and per-term view needs that the delta does not carry: which codelists
    hold which terms *now*, not only which memberships moved.
    """

    delta = import_service.compute_delta(session, package_date)
    memberships = read_memberships(session, package_date)
    deleted_ids = deleted_term_ids(delta)
    deleted_heads = (
        mdr_repository.get_term_heads(deleted_ids, package_date) if deleted_ids else {}
    )
    return ReviewSnapshot(
        codelists=build_codelist_rows(delta, memberships),
        terms=build_term_rows(delta, memberships, deleted_heads),
        summary=build_release_summary(delta),
    )


def read_memberships(
    session: StagingSession, package_date: str
) -> list[dict[str, Any]]:
    """Every current codelist/term membership of the release, in `get_memberships`'
    order — by codelist, then by term."""

    memberships: list[dict[str, Any]] = []
    total = release_repository.count_memberships(session, package_date)
    for skip in range(0, total, import_service.PAGE):
        memberships.extend(
            release_repository.get_memberships(
                session, package_date, skip, import_service.PAGE
            )
        )
    return memberships


def build_release_summary(delta: dict[str, Any]) -> dict[str, Any]:
    """The release-wide figures of the dashboard, in a JSON-ready shape.

    `membership_changes` is the part of the delta `import_service.import_blockers`
    reads, and only as much of it as `changed_and_removed_memberships` needs to give
    the same answer it gives on the full delta: every closed membership, and of the
    opened ones only those reopening a closed pair — the value changes. The rest of the
    opened memberships play no part in it, and on a first release they are every
    membership there is.
    """

    ended_pairs = {
        (m["codelist_uid"], m["term_uid"]) for m in delta["memberships_ended"]
    }
    return {
        "catalogues": [pkg["name"] for pkg in delta["packages"]],
        "codelists": import_service.counts_of(delta["codelists"]).model_dump(
            mode="json"
        ),
        "terms": import_service.counts_of(delta["terms"]).model_dump(mode="json"),
        "memberships_added": len(delta["memberships_added"]),
        "memberships_ended": len(delta["memberships_ended"]),
        "membership_changes": {
            "memberships_added": [
                {key: m[key] for key in MEMBERSHIP_KEYS}
                for m in delta["memberships_added"]
                if (m["codelist_uid"], m["term_uid"]) in ended_pairs
            ],
            "memberships_ended": [
                {key: m[key] for key in MEMBERSHIP_KEYS}
                for m in delta["memberships_ended"]
            ],
        },
    }


def build_codelist_rows(
    delta: dict[str, Any], memberships: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """One row per codelist the release holds, changed or not.

    `changed_in_scope` is the half of "in scope" the delta decides — the codelist, one
    of its terms or one of its memberships changed. The other half, having a finding,
    moves while people review, so it is left to the reader.
    """

    codelist_status = bucket_status(delta["codelists"])
    term_status = bucket_status(delta["terms"])

    codelist_to_terms: dict[str, list[str]] = defaultdict(list)
    for m in memberships:
        codelist_to_terms[m["codelist_id"]].append(m["term_id"])

    added_by_codelist = Counter(m["codelist_uid"] for m in delta["memberships_added"])
    ended_by_codelist = Counter(m["codelist_uid"] for m in delta["memberships_ended"])

    rows: list[dict[str, Any]] = []
    for row in delta["codelists"]["all"]:
        codelist_id = row["concept_id"]
        term_ids = codelist_to_terms.get(codelist_id, [])
        tally = Counter(term_status.get(t, "UNCHANGED") for t in term_ids)
        added = added_by_codelist[codelist_id]
        ended = ended_by_codelist[codelist_id]
        rows.append(
            {
                "codelist_id": codelist_id,
                "name": row["attributes"].get("name"),
                "submission_value": row["attributes"].get("submission_value"),
                "change_status": codelist_status[codelist_id],
                "term_new": tally["NEW"],
                "term_updated": tally["UPDATED"],
                "term_unchanged": tally["UNCHANGED"],
                "term_new_examples": [
                    t for t in term_ids if term_status.get(t) == "NEW"
                ][:EXAMPLE_LIMIT],
                "term_updated_examples": [
                    t for t in term_ids if term_status.get(t) == "UPDATED"
                ][:EXAMPLE_LIMIT],
                "memberships_added": added,
                "memberships_ended": ended,
                "changed_in_scope": (
                    codelist_status[codelist_id] != "UNCHANGED"
                    or tally["NEW"] > 0
                    or tally["UPDATED"] > 0
                    or added > 0
                    or ended > 0
                ),
            }
        )
    return rows


def build_term_rows(
    delta: dict[str, Any],
    memberships: list[dict[str, Any]],
    deleted_heads: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Every term the release adds, changes or drops — and only those.

    A term the release leaves alone gets no row, even when it carries a finding: that
    finding is still counted against the codelists holding it.

    Terms the release has dropped entirely are appended last: staging says nothing about
    them, so their names come from MDR's head — `deleted_heads`, read by the caller for
    `deleted_term_ids` — the way `get_codelist_detail` names a term whose membership
    just ended.

    `covering_codelist_ids` is every codelist whose reviewer answers for the term,
    including one it just left: what `codelist_service.to_term_review` needs.
    """

    term_status = bucket_status(delta["terms"])

    term_to_codelists: dict[str, set[str]] = defaultdict(set)
    for m in memberships:
        term_to_codelists[m["term_id"]].add(m["codelist_id"])

    added_by_term = memberships_by_term(delta["memberships_added"])
    ended_by_term = memberships_by_term(delta["memberships_ended"])

    rows: list[dict[str, Any]] = []
    for row in delta["terms"]["all"]:
        term_id = row["concept_id"]
        added = added_by_term.get(term_id, {})
        ended = ended_by_term.get(term_id, {})
        changes = (
            attribute_changes(row, fields=TERM_FIELDS)
            if term_status[term_id] == "UPDATED"
            else []
        )
        impacted = [ImpactedProperty(change.field) for change in changes]

        # A codelist on both sides is the same membership with a different submission
        # value — the term did not move, its value did. On one side only, it did move.
        if any(added[uid] != ended.get(uid) for uid in added.keys() & ended.keys()):
            impacted.append(ImpactedProperty.SUBMISSION_VALUE)
        if added.keys() ^ ended.keys():
            impacted.append(ImpactedProperty.MEMBERSHIP)

        if term_status[term_id] == "NEW":
            change_status = TermChangeStatus.NEW
            impacted = []
        elif impacted:
            change_status = TermChangeStatus.CHANGED
        else:
            continue

        holding = term_to_codelists.get(term_id, set())
        rows.append(
            {
                "concept_id": term_id,
                "preferred_term": row["attributes"].get("preferred_term"),
                "change_status": change_status.value,
                "impacted": [prop.value for prop in impacted],
                "changes": [change.model_dump(mode="json") for change in changes],
                "codelist_count": len(holding),
                "covering_codelist_ids": sorted(holding | ended.keys()),
            }
        )

    # Dropped from the release entirely: every membership closed and no row of its own
    # left in the delta. A term leaving is the change.
    for term_id in deleted_term_ids(delta):
        head = deleted_heads.get(term_id) or {}
        rows.append(
            {
                "concept_id": term_id,
                "preferred_term": (head.get("props") or {}).get("preferred_term"),
                "change_status": TermChangeStatus.DELETED.value,
                "impacted": [ImpactedProperty.MEMBERSHIP.value],
                "changes": [],
                "codelist_count": 0,
                "covering_codelist_ids": sorted(ended_by_term[term_id]),
            }
        )
    return rows


def deleted_term_ids(delta: dict[str, Any]) -> list[str]:
    """The terms whose memberships all close and which the release no longer ships."""

    ended = {m["term_uid"] for m in delta["memberships_ended"]}
    return sorted(ended - {row["concept_id"] for row in delta["terms"]["all"]})


def memberships_by_term(
    memberships: list[dict[str, Any]],
) -> dict[str, dict[str, str | None]]:
    """`{term: {codelist: submission value}}` for one side of the membership delta."""

    by_term: dict[str, dict[str, str | None]] = defaultdict(dict)
    for m in memberships:
        by_term[m["term_uid"]][m["codelist_uid"]] = m["submission_value"]
    return by_term


def bucket_status(bucket: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    """Maps each row's `concept_id` to which bucket ("new"/"updated"/"unchanged") it
    is in, the way `diff_codelists`/`diff_terms`/`diff_codelist_terms` all return one.
    """

    status = {}
    for key in ("new", "updated", "unchanged"):
        for row in bucket[key]:
            status[row["concept_id"]] = key.upper()
    return status


def attribute_changes(
    row: dict[str, Any], fields: tuple[str, ...] = CODELIST_FIELDS
) -> list[AttributeChange]:
    """What changed between MDR's head and what this release now says, field by field.

    Mirrors `values_differ`'s field-by-field comparison, but reports what changed rather
    than only whether anything did. `fields` says which attributes to walk — a codelist's
    by default, `TERM_FIELDS` for a term.
    """

    head = (row.get("head") or {}).get("props") or {}
    wanted = row["attributes"]
    changes = []
    for field in fields:
        old, new = head.get(field), wanted.get(field)
        if field == "extensible":
            if import_service.as_bool(old) != import_service.as_bool(new):
                changes.append(
                    AttributeChange(field=field, old_value=str(old), new_value=str(new))
                )
        elif field == "synonyms":
            if sorted(old or []) != sorted(new or []):
                changes.append(
                    AttributeChange(
                        field=field, old_value=old or [], new_value=new or []
                    )
                )
        elif old != new:
            changes.append(AttributeChange(field=field, old_value=old, new_value=new))
    return changes
