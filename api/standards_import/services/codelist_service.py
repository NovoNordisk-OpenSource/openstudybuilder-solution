"""Reading a release codelist by codelist, rather than as one flat review queue.

Everything here regroups what `import_service.compute_delta` and the `Inconsistency`
store already hold — see `models/codelists.py`. The two list views read the delta's
share through `review_snapshot_service`, which works it out once per analysis rather
than once per page. Nothing else is written here; a finding embedded in these responses
carries the same `uid` `/inconsistencies` returns, and is settled the same way.
"""

from collections import defaultdict
from collections.abc import Callable
from datetime import date
from typing import Any

from common.auth.user import user
from common.exceptions import NotFoundException, ValidationException
from standards_import.models.changelog import ChangelogEntry
from standards_import.models.codelists import (
    AttributeChange,
    AttributeValue,
    ChangeStatus,
    CodelistDetail,
    CodelistPage,
    CodelistReview,
    CodelistSummary,
    CodelistTermSummary,
    FindingStatusCounts,
    ImpactedProperty,
    MembershipChange,
    ReleaseDashboard,
    ReleaseInconsistencyStats,
    ReleaseReviewStats,
    ReviewStatus,
    TermChangeStatus,
    TermCodelistMembership,
    TermDetail,
    TermPage,
    TermSummary,
    TermUsage,
)
from standards_import.models.imports import ChangeCounts, MembershipChanges
from standards_import.models.inconsistencies import (
    SPONSOR_IMPACT_TYPES,
    EntityType,
    Inconsistency,
    InconsistencyStatus,
)
from standards_import.repositories import (
    changelog_repository,
    codelist_review_repository,
    inconsistency_repository,
    mdr_repository,
    release_repository,
)
from standards_import.repositories.staging_db import staging_session, to_native
from standards_import.services import (
    analysis_service,
    changelog_service,
    import_service,
    inconsistency_service,
    review_snapshot_service,
)
from standards_import.services.review_snapshot_service import (
    CODELIST_FIELDS,
    TERM_FIELDS,
    attribute_changes,
    bucket_status,
)


def dashboard(effective_date: date) -> ReleaseDashboard:
    """Release-wide change counts, review items by pass, and review progress.

    Nothing here is new data — it is `/preview` and `/inconsistencies` regrouped for a
    first screen. Everything it needs of the delta is read from the review snapshot
    rather than diffed afresh: the change counts and the membership changes the import
    blockers check from its release summary, review progress from its codelist rows.
    The blockers' other questions — open items, running jobs, what is in use in MDR —
    are still asked live, and `start_import` diffs for real before it lets anything
    through.
    """

    package_date = effective_date.isoformat()
    with staging_session() as session:
        release = import_service.require_release(session, package_date)
        summary, rows = review_snapshot_service.dashboard_inputs(session, package_date)
        blockers = import_service.import_blockers(
            session, release, package_date, summary["membership_changes"]
        )
        finding_counts = inconsistency_repository.get_finding_counts_by_codelist(
            session, package_date
        )
        reviews = codelist_review_repository.get_reviews(session, package_date)
        type_counts = analysis_service.summarise(
            inconsistency_repository.count_by_type_and_status(session, package_date)
        )

    analysis_counts = FindingStatusCounts()
    sponsor_counts = FindingStatusCounts()
    for item in type_counts:
        target = (
            sponsor_counts
            if item.type.value in SPONSOR_IMPACT_TYPES
            else analysis_counts
        )
        target.open += item.open
        target.auto_resolved += item.auto_resolved
        target.resolved += item.resolved
        target.ignored += item.ignored
        target.informational += item.informational

    summaries = summarise_codelists(rows, finding_counts, reviews)
    in_scope = [summary for in_scope, summary in summaries if in_scope]
    reviewed = sum(1 for s in in_scope if s.review.status == ReviewStatus.REVIEWED)
    stale = sum(1 for s in in_scope if s.review.status == ReviewStatus.REVIEWED_STALE)

    return ReleaseDashboard(
        effective_date=effective_date,
        release_status=release["status"],
        can_import=not blockers,
        blockers=blockers,
        catalogues=summary["catalogues"],
        codelists=ChangeCounts.model_validate(summary["codelists"]),
        terms=ChangeCounts.model_validate(summary["terms"]),
        memberships=MembershipChanges(
            added=summary["memberships_added"], ended=summary["memberships_ended"]
        ),
        inconsistencies=ReleaseInconsistencyStats(
            analysis=analysis_counts,
            sponsor_impact=sponsor_counts,
            assessed_at=to_native(release.get("assessed_at")),
        ),
        review=ReleaseReviewStats(
            in_scope=len(in_scope),
            reviewed=reviewed,
            stale=stale,
            not_reviewed=len(in_scope) - reviewed - stale,
        ),
    )


def list_codelists(
    effective_date: date,
    show: str = "in_scope",
    change_status: ChangeStatus | None = None,
    has_findings: bool | None = None,
    has_open_findings: bool | None = None,
    review_status: ReviewStatus | None = None,
    search: str | None = None,
    page_number: int = 1,
    page_size: int = 10,
) -> CodelistPage:
    """One row per codelist this release touches, filtered before it is paginated.

    What changed comes from the review snapshot; findings and reviews, which move while
    people work through the release, are read fresh — one release-wide query each.
    """

    package_date = effective_date.isoformat()
    with staging_session() as session:
        import_service.require_release(session, package_date)
        rows = review_snapshot_service.codelist_rows(session, package_date)
        finding_counts = inconsistency_repository.get_finding_counts_by_codelist(
            session, package_date
        )
        reviews = codelist_review_repository.get_reviews(session, package_date)

    summaries = summarise_codelists(rows, finding_counts, reviews)
    page_items, total = filter_and_paginate(
        [summary for in_scope, summary in summaries if show == "all" or in_scope],
        change_status=change_status,
        has_findings=has_findings,
        has_open_findings=has_open_findings,
        review_status=review_status,
        search=search,
        search_fields=lambda s: (s.codelist_id, s.submission_value, s.name),
        page_number=page_number,
        page_size=page_size,
        # The ones still waiting on a decision first - what blocks import ahead of what
        # only wants acknowledging - so the reviewer's first page is their work rather
        # than the alphabet.
        key=lambda s: (action_rank(s.findings), s.codelist_id),
    )
    return CodelistPage(
        items=page_items, total=total, page_number=page_number, page_size=page_size
    )


def list_terms(
    effective_date: date,
    change_status: TermChangeStatus | None = None,
    has_findings: bool | None = None,
    has_open_findings: bool | None = None,
    review_status: ReviewStatus | None = None,
    search: str | None = None,
    page_number: int = 1,
    page_size: int = 10,
) -> TermPage:
    """One row per term this release changes, filtered before it is paginated.

    Unlike `list_codelists` there is no `show`: a term the release leaves alone is never
    listed, finding or not — its findings still count against the codelists holding it.
    Read the way `list_codelists` is: the change from the snapshot, the rest fresh.
    """

    package_date = effective_date.isoformat()
    with staging_session() as session:
        import_service.require_release(session, package_date)
        rows = review_snapshot_service.term_rows(session, package_date)
        finding_counts = inconsistency_repository.get_finding_counts_by_term(
            session, package_date
        )
        reviews = codelist_review_repository.get_reviews(session, package_date)

    summaries = summarise_terms(rows, finding_counts, reviews)
    page_items, total = filter_and_paginate(
        summaries,
        change_status=change_status,
        has_findings=has_findings,
        has_open_findings=has_open_findings,
        review_status=review_status,
        search=search,
        search_fields=lambda s: (s.concept_id, s.preferred_term),
        page_number=page_number,
        page_size=page_size,
        key=lambda s: s.concept_id,
    )
    return TermPage(
        items=page_items, total=total, page_number=page_number, page_size=page_size
    )


def get_codelist_detail(
    effective_date: date, codelist_id: str, show: str = "changed"
) -> CodelistDetail:
    """What this release changes on one codelist, and everything to review there."""

    package_date = effective_date.isoformat()
    with staging_session() as session:
        import_service.require_release(session, package_date)

        codelists_delta = import_service.diff_codelists(session, package_date)
        codelist_status = bucket_status(codelists_delta)
        row = require_codelist_row(codelists_delta, codelist_id, package_date)
        review_record = codelist_review_repository.get_review(
            session, package_date, codelist_id
        )

        terms_delta = import_service.diff_codelist_terms(
            session, package_date, codelist_id
        )
        term_status = bucket_status(terms_delta)
        added, ended = import_service.diff_codelist_memberships(
            package_date, codelist_id, terms_delta["all"]
        )
        added_ids = {m["term_uid"] for m in added}
        ended_submission_values = {m["term_uid"]: m["submission_value"] for m in ended}
        ended_term_ids = sorted(ended_submission_values)
        ended_heads = (
            mdr_repository.get_term_heads(ended_term_ids, package_date)
            if ended_term_ids
            else {}
        )

        term_ids = [r["concept_id"] for r in terms_delta["all"]] + ended_term_ids
        findings = [
            inconsistency_service.to_model(record)
            for record in inconsistency_repository.get_findings_for_codelist(
                session, package_date, codelist_id, term_ids
            )
        ]
        # Commentary rather than a finding, and read the same way everything else here
        # is: fresh, alongside the rows already being fetched. Empty for a release with
        # no terminology-changes spreadsheet uploaded.
        changelog = changelog_service.to_models(
            changelog_repository.get_changelog_for_codelist(
                session, package_date, codelist_id
            )
        )

    codelist_findings = [f for f in findings if f.entity_type == EntityType.CODELIST]
    findings_by_term: dict[str, list[Inconsistency]] = defaultdict(list)
    for finding in findings:
        if finding.entity_type == EntityType.TERM:
            findings_by_term[finding.concept_id].append(finding)

    # An entry attached to the codelist may still be about one of its terms: a term
    # removed from a surviving codelist has no node left to hang on, so it falls back
    # to the codelist and keeps the term's `nci_code`. Splitting on the code rather
    # than on what the entry is attached to puts it back on the row for the term that
    # left — which `diff_codelist_memberships` has already emitted as `ENDED`.
    codelist_changelog: list[ChangelogEntry] = []
    changelog_by_term: dict[str, list[ChangelogEntry]] = defaultdict(list)
    term_ids_shown = set(term_ids)
    for entry in changelog:
        if entry.nci_code and entry.nci_code in term_ids_shown:
            changelog_by_term[entry.nci_code].append(entry)
        else:
            # Either about the codelist itself (`nci_code` null, or the codelist's own
            # code), or about a term this release no longer lists at all. Both belong
            # on the codelist, where there is something to show them against.
            codelist_changelog.append(entry)

    terms: list[CodelistTermSummary] = []
    for r in terms_delta["all"]:
        term_id = r["concept_id"]
        term_findings = findings_by_term.get(term_id, [])
        membership = MembershipChange.ADDED if term_id in added_ids else None
        in_scope = (
            term_status[term_id] != "UNCHANGED"
            or membership is not None
            or bool(term_findings)
        )
        if show == "all" or in_scope:
            terms.append(
                CodelistTermSummary(
                    concept_id=term_id,
                    preferred_term=r["attributes"].get("preferred_term"),
                    submission_value=r.get("submission_value"),
                    change_status=ChangeStatus(term_status[term_id]),
                    membership_change=membership,
                    findings=term_findings,
                    changelog=changelog_by_term.get(term_id, []),
                )
            )

    for term_id in ended_term_ids:
        head = ended_heads.get(term_id) or {}
        terms.append(
            CodelistTermSummary(
                concept_id=term_id,
                preferred_term=(head.get("props") or {}).get("preferred_term"),
                submission_value=ended_submission_values.get(term_id),
                change_status=None,
                membership_change=MembershipChange.ENDED,
                findings=findings_by_term.get(term_id, []),
                changelog=changelog_by_term.get(term_id, []),
            )
        )
    terms.sort(key=lambda t: t.concept_id)

    change_status = ChangeStatus(codelist_status[codelist_id])
    # A NEW codelist has no head to diff against, so every attribute it brings is
    # reported, each with no old value: that is what there is to look at on it.
    changes = attribute_changes(row) if change_status != ChangeStatus.UNCHANGED else []
    has_open = any(blocks_review(f) for f in findings)

    return CodelistDetail(
        codelist_id=codelist_id,
        name=row["attributes"].get("name"),
        submission_value=row["attributes"].get("submission_value"),
        change_status=change_status,
        changes=changes,
        attributes=attribute_values(row),
        findings=codelist_findings,
        changelog=codelist_changelog,
        terms=terms,
        term_count=len(terms_delta["all"]),
        review=to_codelist_review(review_record, has_open),
    )


def get_term_detail(effective_date: date, concept_id: str) -> TermDetail:
    """What this release changes on one term, in every codelist holding it.

    The term-side counterpart of `get_codelist_detail`, and read the same way: the term
    and its memberships diffed afresh against MDR, for this one term only. Codelist
    names come from the review snapshot's rows rather than a read of every codelist; a
    codelist the release does not ship is left out, as `diff_memberships` leaves it out
    of what the release opens or closes.
    """

    package_date = effective_date.isoformat()
    with staging_session() as session:
        import_service.require_release(session, package_date)
        codelist_rows = {
            row["codelist_id"]: row
            for row in review_snapshot_service.codelist_rows(session, package_date)
        }
        staged = release_repository.get_term(session, package_date, concept_id)
        head = mdr_repository.get_term_heads([concept_id], package_date).get(concept_id)
        existing = {
            codelist_id: submission_value
            for codelist_id, _term_id, submission_value in (
                mdr_repository.get_open_memberships_of_terms([concept_id])
            )
            if codelist_id in codelist_rows
        }
        findings = [
            inconsistency_service.to_model(record)
            for record in inconsistency_repository.get_findings_for_term(
                session, package_date, concept_id
            )
        ]
        finding_counts = inconsistency_repository.get_finding_counts_by_codelist(
            session, package_date
        )
        reviews = codelist_review_repository.get_reviews(session, package_date)
        changelog = changelog_service.to_models(
            changelog_repository.get_changelog_for_term(
                session, package_date, concept_id
            )
        )

    if staged is None and not existing:
        raise NotFoundException(
            msg=f"No term '{concept_id}' in release '{package_date}'."
        )

    wanted = {
        m["codelist_id"]: m["submission_value"]
        for m in (staged["memberships"] if staged else [])
    }

    row: dict[str, Any]
    change_status: ChangeStatus | None
    if staged is None:
        # Dropped from the release: staging says nothing about it, so what there is to
        # show is what MDR holds, the way a term whose membership ended is named.
        props = (head or {}).get("props") or {}
        row = {"attributes": {field: props.get(field) for field in TERM_FIELDS}}
        change_status = None
    else:
        row = {
            "attributes": import_service.term_attributes(concept_id, staged["props"]),
            "head": head,
        }
        if head is None:
            change_status = ChangeStatus.NEW
        elif import_service.values_differ(row["attributes"], head["props"]):
            change_status = ChangeStatus.UPDATED
        else:
            change_status = ChangeStatus.UNCHANGED
    changes = (
        attribute_changes(row, fields=TERM_FIELDS)
        if change_status in (ChangeStatus.NEW, ChangeStatus.UPDATED)
        else []
    )

    term_findings = [f for f in findings if f.entity_type == EntityType.TERM]
    findings_by_codelist: dict[str, list[Inconsistency]] = defaultdict(list)
    for finding in findings:
        if finding.entity_type != EntityType.TERM:
            findings_by_codelist[finding.concept_id].append(finding)

    # A codelist a finding names may hold the term on neither side - a decision dropped
    # it from there - and is still listed, so that finding has somewhere to be settled.
    codelists: list[TermCodelistMembership] = []
    for codelist_id in sorted(
        wanted.keys() | existing.keys() | findings_by_codelist.keys()
    ):
        membership: MembershipChange | None = None
        previous = None
        if codelist_id in wanted and codelist_id in existing:
            # Both sides: the same membership, unless its submission value moved.
            if wanted[codelist_id] != existing[codelist_id]:
                previous = existing[codelist_id]
        elif codelist_id in wanted:
            membership = MembershipChange.ADDED
        elif codelist_id in existing:
            membership = MembershipChange.ENDED
        codelist_row = codelist_rows.get(codelist_id) or {}
        counts = to_finding_counts(finding_counts.get(codelist_id, {}))
        codelists.append(
            TermCodelistMembership(
                codelist_id=codelist_id,
                name=codelist_row.get("name"),
                submission_value=codelist_row.get("submission_value"),
                term_submission_value=wanted.get(
                    codelist_id, existing.get(codelist_id)
                ),
                previous_submission_value=previous,
                membership_change=membership,
                findings=findings_by_codelist.get(codelist_id, []),
                review=to_codelist_review(
                    reviews.get(codelist_id), bool(counts.open or counts.informational)
                ),
            )
        )

    # Read live rather than taken from the findings: those carry a count only where the
    # term collides or is changed under a reference, and only as of the last assessment.
    # A term MDR does not hold yet has nothing to refer to it.
    usage = (
        mdr_repository.get_term_usage([concept_id]).get(concept_id, [])
        if head is not None or existing
        else []
    )

    return TermDetail(
        concept_id=concept_id,
        preferred_term=row["attributes"].get("preferred_term"),
        change_status=change_status,
        changes=changes,
        attributes=attribute_values(row, fields=TERM_FIELDS),
        findings=term_findings,
        codelists=codelists,
        usage=[
            TermUsage(**entry)
            for entry in sorted(usage, key=lambda entry: -entry["count"])
        ],
        changelog=changelog,
        # The codelists `list_terms` covers the term with: the ones holding it and the
        # ones it is leaving - not one only a finding names.
        review=to_term_review(
            reviews,
            wanted.keys() | existing.keys(),
            any(f.status == InconsistencyStatus.OPEN for f in findings),
        ),
    )


def blocks_review(finding: Inconsistency) -> bool:
    """Whether a finding must be settled before a codelist can be marked reviewed.

    Wider than what blocks the *import*: an `INFORMATIONAL` finding never holds up the
    release, but "reviewed" means a person looked at everything on the codelist,
    informational items included — import and review are different guarantees, and are
    allowed to disagree.
    """

    return finding.status in (
        InconsistencyStatus.OPEN,
        InconsistencyStatus.INFORMATIONAL,
    )


def mark_reviewed(effective_date: date, codelist_id: str) -> CodelistReview:
    """Marks a codelist reviewed — refused while anything on it is still open or
    informational.

    Checked against exactly what the detail view would show with `show=all`, so a
    finding hiding behind the default `show=changed` filter cannot be reviewed past
    unseen. Reviewing an already-reviewed codelist again refreshes who and when.
    """

    detail = get_codelist_detail(effective_date, codelist_id, show="all")
    open_count = sum(
        1
        for finding in detail.findings + [f for t in detail.terms for f in t.findings]
        if blocks_review(finding)
    )
    ValidationException.raise_if(
        open_count > 0,
        msg=f"Codelist '{codelist_id}' still has {open_count} open or informational "
        "finding(s). Settle or acknowledge them first.",
    )

    package_date = effective_date.isoformat()
    with staging_session() as session:
        record = codelist_review_repository.mark_reviewed(
            session, package_date, codelist_id, user().id()
        )
    return to_codelist_review(record, has_open_finding=False)


def clear_review(effective_date: date, codelist_id: str) -> CodelistReview:
    """Puts a codelist back to `NOT_REVIEWED`. A no-op, not an error, if it never was."""

    package_date = effective_date.isoformat()
    with staging_session() as session:
        import_service.require_release(session, package_date)
        codelists_delta = import_service.diff_codelists(session, package_date)
        require_codelist_row(codelists_delta, codelist_id, package_date)
        codelist_review_repository.clear_review(session, package_date, codelist_id)
    return CodelistReview()


# --- shaping shared by more than one of the above --------------------------------


def filter_and_paginate[Summary: (CodelistSummary, TermSummary)](
    rows: list[Summary],
    *,
    change_status: ChangeStatus | TermChangeStatus | None,
    has_findings: bool | None,
    has_open_findings: bool | None,
    review_status: ReviewStatus | None,
    search: str | None,
    search_fields: Callable[[Summary], tuple[str | None, ...]],
    page_number: int,
    page_size: int,
    key: Callable[[Summary], Any],
) -> tuple[list[Summary], int]:
    """The filter-sort-slice `list_codelists` and `list_terms` both apply.

    `Summary` is one of the two list-view summaries, which agree on the three fields
    filtered on without sharing a base class.

    `rows` is already scoped by the caller. Filtering happens before pagination, so
    `total` is what matched rather than what the release holds. `page_size` 0 means one
    page with everything on it. `search` is a case-insensitive substring of any of
    `search_fields`.
    """

    filtered = list(rows)
    needle = (search or "").strip().casefold()
    if needle:
        filtered = [
            s
            for s in filtered
            if any(needle in field.casefold() for field in search_fields(s) if field)
        ]
    if change_status is not None:
        filtered = [s for s in filtered if s.change_status == change_status]
    if has_findings is not None:
        filtered = [s for s in filtered if any_findings(s.findings) == has_findings]
    if has_open_findings is not None:
        filtered = [s for s in filtered if bool(s.findings.open) == has_open_findings]
    if review_status is not None:
        filtered = [s for s in filtered if s.review.status == review_status]
    filtered.sort(key=key)

    total = len(filtered)
    if page_size == 0:
        return filtered, total
    start = (page_number - 1) * page_size
    return filtered[start : start + page_size], total


def summarise_codelists(
    rows: list[dict[str, Any]],
    finding_counts: dict[str, dict[str, int]],
    reviews: dict[str, dict[str, Any]],
) -> list[tuple[bool, CodelistSummary]]:
    """Every codelist the release holds, each paired with whether it is in scope.

    `rows` are `review_snapshot_service.build_codelist_rows`' — what the delta says.
    `finding_counts` and `reviews` are what `get_finding_counts_by_codelist` and
    `get_reviews` return, read once by the caller rather than once per codelist here.
    In scope is the delta's half (`changed_in_scope`) or a finding of any kind.
    """

    results: list[tuple[bool, CodelistSummary]] = []
    for row in rows:
        codelist_id = row["codelist_id"]
        findings = to_finding_counts(finding_counts.get(codelist_id, {}))
        summary = CodelistSummary(
            codelist_id=codelist_id,
            name=row["name"],
            submission_value=row["submission_value"],
            change_status=ChangeStatus(row["change_status"]),
            term_changes=ChangeCounts(
                new=row["term_new"],
                updated=row["term_updated"],
                unchanged=row["term_unchanged"],
                new_examples=row["term_new_examples"] or [],
                updated_examples=row["term_updated_examples"] or [],
            ),
            memberships=MembershipChanges(
                added=row["memberships_added"], ended=row["memberships_ended"]
            ),
            findings=findings,
            review=to_codelist_review(
                reviews.get(codelist_id), bool(findings.open or findings.informational)
            ),
        )
        in_scope = bool(row["changed_in_scope"]) or any_findings(findings)
        results.append((in_scope, summary))
    return results


def summarise_terms(
    rows: list[dict[str, Any]],
    finding_counts: dict[str, dict[str, int]],
    reviews: dict[str, dict[str, Any]],
) -> list[TermSummary]:
    """Every term the release adds, changes or drops, with its findings and review.

    `rows` are `review_snapshot_service.build_term_rows`', which already leaves out the
    terms the release does not touch. A term's review comes from the codelists covering
    it — `covering_codelist_ids`, which keeps a codelist the term just left.
    """

    results: list[TermSummary] = []
    for row in rows:
        findings = to_finding_counts(finding_counts.get(row["concept_id"], {}))
        results.append(
            TermSummary(
                concept_id=row["concept_id"],
                preferred_term=row["preferred_term"],
                change_status=TermChangeStatus(row["change_status"]),
                impacted=[ImpactedProperty(prop) for prop in row["impacted"]],
                changes=[
                    AttributeChange.model_validate(change) for change in row["changes"]
                ],
                codelist_count=row["codelist_count"],
                findings=findings,
                review=to_term_review(
                    reviews, set(row["covering_codelist_ids"]), bool(findings.open)
                ),
            )
        )
    return results


def to_codelist_review(
    record: dict[str, Any] | None, has_open_finding: bool
) -> CodelistReview:
    """Derives the displayed review status rather than storing it.

    A review record is never rewritten by re-analysis — see `codelist_review_repository`
    — so whether it still holds is worked out here, every time, from whether the
    codelist currently has a finding that blocks review (see `blocks_review` — open or
    informational, not only open). `REVIEWED_STALE` when one does: the record of who
    reviewed it and when is kept, but the flag itself needs re-confirming.
    """

    if record is None:
        return CodelistReview()
    status = ReviewStatus.REVIEWED_STALE if has_open_finding else ReviewStatus.REVIEWED
    return CodelistReview(
        status=status,
        reviewed_by=record["author_id"],
        reviewed_at=to_native(record["reviewed_at"]),
    )


def to_term_review(
    reviews: dict[str, dict[str, Any]],
    codelist_ids: set[str],
    has_open_finding: bool,
) -> CodelistReview:
    """Derives a term's review state from the codelists that cover it.

    A term has no review mark of its own — `codelist_review_repository` keys every record
    on a codelist — so "this term has been reviewed" can only mean "every codelist it
    belongs to has been walked through". A term still waiting on any one of them is
    `NOT_REVIEWED`; `reviewed_at` is the latest of those walkthroughs, because that is as
    recent as the claim gets.

    Stale works exactly as it does per codelist, and for the same reason: `mark_reviewed`
    refuses while anything on a codelist is open, so an OPEN finding on a term whose
    codelists are all marked means a later analysis reopened it.
    """

    records = [reviews.get(codelist_id) for codelist_id in codelist_ids]
    if not records or any(record is None for record in records):
        return CodelistReview()
    latest = max(records, key=lambda record: record["reviewed_at"])  # type: ignore[index]
    status = ReviewStatus.REVIEWED_STALE if has_open_finding else ReviewStatus.REVIEWED
    return CodelistReview(
        status=status,
        reviewed_by=latest["author_id"],  # type: ignore[index]
        reviewed_at=to_native(latest["reviewed_at"]),  # type: ignore[index]
    )


def to_finding_counts(raw_counts: dict[str, int]) -> FindingStatusCounts:
    """Turns one row of `get_finding_counts_by_*` into the four counts it reports."""

    return FindingStatusCounts(
        open=raw_counts.get("OPEN", 0),
        auto_resolved=raw_counts.get("AUTO_RESOLVED", 0),
        resolved=raw_counts.get("RESOLVED", 0),
        ignored=raw_counts.get("IGNORED", 0),
        informational=raw_counts.get("INFORMATIONAL", 0),
        acknowledged=raw_counts.get("ACKNOWLEDGED", 0),
    )


def require_codelist_row(
    codelists_delta: dict[str, Any], codelist_id: str, package_date: str
) -> dict[str, Any]:
    row = next(
        (r for r in codelists_delta["all"] if r["concept_id"] == codelist_id), None
    )
    if row is None:
        raise NotFoundException(
            msg=f"No codelist '{codelist_id}' in release '{package_date}'."
        )
    return row


def any_findings(counts: FindingStatusCounts) -> bool:
    return bool(
        counts.open
        or counts.auto_resolved
        or counts.resolved
        or counts.ignored
        or counts.informational
        or counts.acknowledged
    )


def action_rank(counts: FindingStatusCounts) -> int:
    """0 while something blocks import, 1 while something only wants acknowledging,
    2 once nothing waits on a person."""
    if counts.open:
        return 0
    if counts.informational:
        return 1
    return 2


def attribute_values(
    row: dict[str, Any], fields: tuple[str, ...] = CODELIST_FIELDS
) -> list[AttributeValue]:
    """Every attribute this release says, changed or not, in `fields` order.

    `extensible` is normalised the way `attribute_changes` compares it: CDISC ships it as
    the string `"true"`, which would otherwise read as text rather than as a yes or no.
    """

    wanted = row["attributes"]
    values = []
    for field in fields:
        value = wanted.get(field)
        if field == "extensible" and value is not None:
            value = import_service.as_bool(value)
        elif field == "synonyms":
            value = value or []
        values.append(AttributeValue(field=field, value=value))
    return values
