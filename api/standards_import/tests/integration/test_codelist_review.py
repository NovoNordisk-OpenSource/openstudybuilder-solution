"""The dashboard, codelist list and codelist detail endpoints, against real databases.

These need real databases for the same reason `test_release_loop.py` does: the grouping,
the MDR diff, and the finding-to-codelist attribution are all hand-written Cypher.

FIRST establishes MDR: C1 "Test Codelist" holds T1 and T2, C2 "Stable Codelist" holds T9.
SECOND is what is under test — two catalogues disagreeing over T1's definition (a
`CONFLICTING_VALUES` on the *term*, carrying no `codelist_ids`, the case that needs the
membership join rather than a direct field), T2 dropped, T4 added, C2 brought back
completely unchanged, and a brand new C3.
"""

import pytest

from common.exceptions import NotFoundException, ValidationException
from standards_import.models.codelists import ChangeStatus, TermChangeStatus
from standards_import.repositories import (
    analysis_repository,
    review_snapshot_repository,
    staging_db,
)
from standards_import.services import import_service, inconsistency_service
from standards_import.tests.integration.packages import codelist, package, term
from standards_import.tests.integration.sponsor_data import add_sponsor_term

FIRST = "2025-09-26"
SECOND = "2026-03-27"


def import_first(release):
    upload_first(release)
    release.analyse(FIRST)
    release.assess(FIRST)
    job = release.import_now(FIRST)
    assert job.status.value == "SUCCEEDED", job.error


def upload_first(release):
    release.upload(
        package(
            "SDTM CT",
            FIRST,
            [
                codelist(
                    "C1",
                    "Test Codelist",
                    "TESTCL",
                    terms=[term("T1", "A"), term("T2", "B")],
                ),
                codelist("C2", "Stable Codelist", "STBL", terms=[term("T9", "S9")]),
            ],
        )
    )


def bring_in_second(release):
    release.upload(
        package(
            "SDTM CT",
            SECOND,
            [
                codelist(
                    "C1",
                    "Test Codelist",
                    "TESTCL",
                    terms=[term("T1", "A", definition="From SDTM."), term("T4", "D")],
                ),
                codelist("C2", "Stable Codelist", "STBL", terms=[term("T9", "S9")]),
                codelist("C3", "New Codelist", "NEWCL", terms=[term("T10", "J")]),
            ],
        ),
        package(
            "SEND CT",
            SECOND,
            [
                codelist(
                    "C1",
                    "Test Codelist",
                    "TESTCL",
                    terms=[term("T1", "A", definition="From SEND."), term("T4", "D")],
                )
            ],
        ),
    )
    return release.analyse(SECOND)


def open_findings(release, effective_date=SECOND):
    return release.findings(effective_date, status="OPEN")


class TestDashboard:
    def test_reports_the_release_wide_change_counts(self, release):
        import_first(release)
        bring_in_second(release)

        dashboard = release.dashboard(SECOND)

        # C1 unchanged, C2 unchanged, C3 new.
        assert dashboard.codelists.new == 1
        assert dashboard.codelists.unchanged == 2
        # T1 updated (SDTM/SEND disagree, pecking order settles a value), T4 and T10
        # new, T9 unchanged. T2 is not part of SECOND's own term set at all — no
        # catalogue of this release lists it — so it is not counted here; it only
        # shows up as a membership this release ends (see TestCodelistDetail).
        assert dashboard.terms.new == 2
        assert dashboard.terms.updated == 1
        assert dashboard.terms.unchanged == 1

    def test_splits_review_items_by_which_pass_raised_them(self, release):
        import_first(release)
        bring_in_second(release)

        dashboard = release.dashboard(SECOND)

        # T1's CONFLICTING_VALUES, plus a SPONSOR_NAME for each of the two new terms
        # (T4, T10) — every term new to MDR raises one, auto-resolved by the seeded rule.
        assert dashboard.inconsistencies.analysis.auto_resolved == 3
        assert dashboard.inconsistencies.sponsor_impact.model_dump() == {
            "open": 0,
            "auto_resolved": 0,
            "resolved": 0,
            "ignored": 0,
            "informational": 0,
            "acknowledged": 0,
        }

    def test_review_progress_counts_only_codelists_in_scope(self, release):
        import_first(release)
        bring_in_second(release)

        dashboard = release.dashboard(SECOND)

        # C1 (finding + membership changes) and C3 (new); C2 is untouched.
        assert dashboard.review.in_scope == 2
        assert dashboard.review.not_reviewed == 2
        assert dashboard.review.reviewed == 0
        assert dashboard.review.stale == 0


class TestCodelistList:
    def test_in_scope_excludes_a_codelist_nothing_changed_on(self, release):
        import_first(release)
        bring_in_second(release)

        in_scope = {
            row.codelist_id for row in release.codelists(SECOND, page_size=0).items
        }

        assert in_scope == {"C1", "C3"}

    def test_show_all_includes_the_untouched_codelist_too(self, release):
        import_first(release)
        bring_in_second(release)

        every_id = {
            row.codelist_id
            for row in release.codelists(SECOND, show="all", page_size=0).items
        }

        assert every_id == {"C1", "C2", "C3"}

    def test_an_unchanged_codelist_with_a_changed_term_is_still_in_scope(self, release):
        import_first(release)
        bring_in_second(release)

        [c1] = [
            row
            for row in release.codelists(SECOND, page_size=0).items
            if row.codelist_id == "C1"
        ]

        assert c1.change_status.value == "UNCHANGED"
        assert c1.term_changes.new == 1  # T4
        assert c1.memberships.ended == 1  # T2
        # T1's CONFLICTING_VALUES, plus T4's SPONSOR_NAME — every term new to MDR
        # raises one, auto-resolved by the seeded rule.
        assert c1.findings.auto_resolved == 2

    def test_has_open_findings_filters_to_what_still_blocks(self, release):
        import_first(release)
        bring_in_second(release)

        assert release.codelists(SECOND, has_open_findings=True, page_size=0).total == 0

    def test_change_status_filters_to_new_codelists(self, release):
        import_first(release)
        bring_in_second(release)

        page = release.codelists(
            SECOND, show="all", change_status=ChangeStatus.NEW, page_size=0
        )

        assert [row.codelist_id for row in page.items] == ["C3"]

    def test_pagination_slices_the_filtered_result_not_the_whole_release(self, release):
        import_first(release)
        bring_in_second(release)

        page = release.codelists(SECOND, show="all", page_number=1, page_size=2)

        assert page.total == 3
        assert page.page_size == 2
        assert len(page.items) == 2

    def test_a_page_size_of_zero_returns_everything_on_one_page(self, release):
        import_first(release)
        bring_in_second(release)

        page = release.codelists(SECOND, show="all", page_size=0)

        assert len(page.items) == page.total == 3


class TestCodelistDetail:
    def test_a_new_codelist_reports_its_own_term_as_new(self, release):
        import_first(release)
        bring_in_second(release)

        detail = release.codelist(SECOND, "C3")

        assert detail.change_status.value == "NEW"
        assert detail.term_count == 1
        [t10] = detail.terms
        assert t10.concept_id == "T10"
        assert t10.change_status.value == "NEW"

    def test_a_new_codelist_reports_every_attribute_it_brings(self, release):
        import_first(release)
        bring_in_second(release)

        detail = release.codelist(SECOND, "C3")

        by_field = {c.field: c for c in detail.changes}
        assert by_field["name"].new_value == "New Codelist"
        assert by_field["submission_value"].new_value == "NEWCL"
        assert all(c.old_value is None for c in detail.changes)

    def test_an_unchanged_codelist_reports_no_attribute_change(self, release):
        import_first(release)
        bring_in_second(release)

        assert release.codelist(SECOND, "C2").changes == []

    def test_an_unchanged_codelist_still_reports_its_current_attributes(self, release):
        import_first(release)
        bring_in_second(release)

        detail = release.codelist(SECOND, "C2")

        assert [a.field for a in detail.attributes] == [
            "name",
            "definition",
            "submission_value",
            "extensible",
            "synonyms",
        ]
        by_field = {a.field: a.value for a in detail.attributes}
        assert by_field["submission_value"] == detail.submission_value
        assert by_field["name"] == detail.name

    def test_the_term_level_dispute_is_attributed_to_its_codelist_via_membership(
        self, release
    ):
        """T1's `CONFLICTING_VALUES` carries no `codelist_ids` at all — this is the case
        that needs the membership join, not a direct field match."""

        import_first(release)
        bring_in_second(release)

        detail = release.codelist(SECOND, "C1")

        [t1] = [t for t in detail.terms if t.concept_id == "T1"]
        assert [f.type.value for f in t1.findings] == ["CONFLICTING_VALUES"]
        assert (
            detail.findings == []
        )  # the dispute belongs to the term, not the codelist

    def test_a_dropped_term_is_shown_with_its_membership_ended_and_no_change_status(
        self, release
    ):
        import_first(release)
        bring_in_second(release)

        detail = release.codelist(SECOND, "C1")

        [t2] = [t for t in detail.terms if t.concept_id == "T2"]
        assert t2.membership_change.value == "ENDED"
        assert t2.change_status is None
        assert t2.submission_value == "B"
        # T2 is not part of this release's own term set, so it is excluded from the
        # "currently in the codelist" count even though it is shown.
        assert "T2" not in {
            t.concept_id for t in detail.terms if t.change_status is not None
        }

    def test_show_all_adds_the_untouched_term_back_in(self, release):
        """C2 changed nothing at all — its one term, T9, is invisible by default and
        only appears with `show=all`."""

        import_first(release)
        bring_in_second(release)

        changed_only = release.codelist(SECOND, "C2")
        everything = release.codelist(SECOND, "C2", show="all")

        assert changed_only.terms == []
        assert [t.concept_id for t in everything.terms] == ["T9"]
        assert everything.terms[0].change_status.value == "UNCHANGED"

    def test_an_unknown_codelist_is_a_404(self, release):
        import_first(release)
        bring_in_second(release)

        with pytest.raises(NotFoundException, match="C999"):
            release.codelist(SECOND, "C999")

    def test_an_unstaged_effective_date_is_a_404(self, release):
        with pytest.raises(NotFoundException):
            release.dashboard("2099-01-01")


def drop_one_of_two_memberships(release):
    """T5 sits in both C1 and C2 in MDR, then only in C1 — the release changes which
    codelists hold it without dropping it, the case `DELETED` must not swallow."""

    release.upload(
        package(
            "SDTM CT",
            FIRST,
            [
                codelist("C1", "Test Codelist", "TESTCL", terms=[term("T5", "E")]),
                codelist("C2", "Stable Codelist", "STBL", terms=[term("T5", "E")]),
            ],
        )
    )
    release.analyse(FIRST)
    release.assess(FIRST)
    job = release.import_now(FIRST)
    assert job.status.value == "SUCCEEDED", job.error

    release.upload(
        package(
            "SDTM CT",
            SECOND,
            [
                codelist("C1", "Test Codelist", "TESTCL", terms=[term("T5", "E")]),
                codelist("C2", "Stable Codelist", "STBL", terms=[]),
            ],
        )
    )
    return release.analyse(SECOND)


class TestReleaseTerms:
    def test_a_term_no_codelist_of_this_release_lists_is_deleted(self, release):
        """T2 was in C1 in MDR and appears nowhere in SECOND. Deleted here means "gone
        from the release" — MDR keeps the term, it only loses the membership."""

        import_first(release)
        bring_in_second(release)

        page = release.terms(SECOND, page_size=0)

        [t2] = [t for t in page.items if t.concept_id == "T2"]
        assert t2.change_status.value == "DELETED"
        assert [p.value for p in t2.impacted] == ["membership"]
        assert t2.codelist_count == 0

    def test_a_deleted_terms_name_is_read_back_from_mdr(self, release):
        """No catalogue of this release mentions it, so staging holds no name for it."""

        import_first(release)
        bring_in_second(release)

        page = release.terms(SECOND, page_size=0)

        [t2] = [t for t in page.items if t.concept_id == "T2"]
        assert t2.preferred_term is not None

    def test_leaving_one_codelist_of_two_is_changed_not_deleted(self, release):
        drop_one_of_two_memberships(release)

        page = release.terms(SECOND, page_size=0)

        [t5] = [t for t in page.items if t.concept_id == "T5"]
        assert t5.change_status.value == "CHANGED"
        assert [p.value for p in t5.impacted] == ["membership"]
        assert t5.codelist_count == 1  # C1 still; C2 ended

    def test_an_updated_term_reports_which_property_the_release_touches(self, release):
        """T1 gains a definition in SECOND; nothing else about it moves."""

        import_first(release)
        bring_in_second(release)

        page = release.terms(SECOND, page_size=0)

        [t1] = [t for t in page.items if t.concept_id == "T1"]
        assert t1.change_status.value == "CHANGED"
        assert [p.value for p in t1.impacted] == ["definition"]
        assert [c.field for c in t1.changes] == ["definition"]

    def test_a_terms_dispute_is_counted_against_the_term(self, release):
        """The mirror of `test_the_term_level_dispute_is_attributed_to_its_codelist_via
        _membership`: the same `CONFLICTING_VALUES` seen from the term's side, and on no
        sibling term."""

        import_first(release)
        bring_in_second(release)

        page = release.terms(SECOND, page_size=0)

        counts = {t.concept_id: t.findings for t in page.items}
        # One `CONFLICTING_VALUES` in the release, attributed to T1 and nowhere else.
        # T4 and T10 do carry a finding, but their own `SPONSOR_NAME`, one each.
        assert counts["T1"].auto_resolved == 1
        assert "T9" not in counts  # unchanged, so not listed at all
        per_term = sum(
            c.open + c.auto_resolved + c.resolved + c.ignored for c in counts.values()
        )
        assert per_term == len(
            [
                item
                for item in release.findings(SECOND)
                if item.entity_type.value == "TERM"
            ]
        )

    def test_a_codelist_wide_dispute_lands_on_no_term(self, release):
        """`INCONSISTENT_TERM_SETS` is about which terms C1 holds, not about T1 or T2 —
        it must not be spread across the terms it happens to be near. It is the only
        thing this release leaves OPEN, so no term may report an open finding."""

        upload_disputed_membership(release)

        page = release.terms(FIRST, page_size=0)

        [dispute] = [
            item
            for item in release.findings(FIRST)
            if item.type.value == "INCONSISTENT_TERM_SETS"
        ]
        assert dispute.status.value == "OPEN"
        assert not any(t.findings.open for t in page.items)

    def test_a_term_nothing_happened_to_is_not_listed(self, release):
        """T9 is in C2, which this release brings back byte-identical."""

        import_first(release)
        bring_in_second(release)

        page = release.terms(SECOND, page_size=0)

        assert "T9" not in {t.concept_id for t in page.items}

    def test_a_new_term_is_counted_in_its_codelist(self, release):
        """T10 arrives with C3, and C3 alone."""

        import_first(release)
        bring_in_second(release)

        page = release.terms(SECOND, change_status=TermChangeStatus.NEW, page_size=0)

        [t10] = [t for t in page.items if t.concept_id == "T10"]
        assert t10.impacted == []
        assert t10.codelist_count == 1

    def test_review_state_is_inherited_from_the_codelists_holding_the_term(
        self, release
    ):
        """There is no per-term mark to set — marking C1 is what makes its terms read
        reviewed, and a term in an unmarked codelist stays `NOT_REVIEWED`."""

        drop_one_of_two_memberships(release)
        for item in release.findings(SECOND, status="OPEN"):
            release.resolve(item.uid, strategy="IGNORE")

        before = release.terms(SECOND, page_size=0)
        assert all(t.review.status.value == "NOT_REVIEWED" for t in before.items)

        release.review(SECOND, "C1")
        half = release.terms(SECOND, page_size=0)
        [t5] = [t for t in half.items if t.concept_id == "T5"]
        # T5's ended C2 membership still counts as covering it, so one mark is not enough.
        assert t5.review.status.value == "NOT_REVIEWED"

        release.review(SECOND, "C2")
        after = release.terms(SECOND, page_size=0)
        [t5] = [t for t in after.items if t.concept_id == "T5"]
        assert t5.review.status.value == "REVIEWED"
        assert t5.review.reviewed_by == "integration-test"

    def test_pagination_slices_the_filtered_result(self, release):
        import_first(release)
        bring_in_second(release)

        everything = release.terms(SECOND, page_size=0)
        first_page = release.terms(SECOND, page_number=1, page_size=2)

        assert first_page.total == everything.total
        assert len(first_page.items) == 2
        assert [t.concept_id for t in first_page.items] == [
            t.concept_id for t in everything.items[:2]
        ]

    def test_an_unstaged_effective_date_is_a_404(self, release):
        with pytest.raises(NotFoundException):
            release.terms("2099-01-01")


class TestSponsorImpactThroughCodelistDetail:
    def test_a_sponsor_term_duplicate_surfaces_on_its_codelist(self, release):
        """The same store, the same functions — a sponsor-impact finding needs no
        special casing to appear here, only proof that it actually does."""

        release.upload(
            package(
                "SDTM CT", FIRST, [codelist("C1", "Test Codelist", "TESTCL", terms=[])]
            )
        )
        release.analyse(FIRST)
        release.assess(FIRST)
        job = release.import_now(FIRST)
        assert job.status.value == "SUCCEEDED", job.error

        add_sponsor_term("C1", "SPONSOR1", "Widget", "WIDGET")

        release.upload(
            package(
                "SDTM CT",
                SECOND,
                [
                    codelist(
                        "C1", "Test Codelist", "TESTCL", terms=[term("T1", "WIDGET")]
                    )
                ],
            )
        )
        summary = release.analyse(SECOND)
        assert summary.open_inconsistency_count == 0
        release.assess(SECOND)

        detail = release.codelist(SECOND, "C1")

        assert any(f.type.value == "SPONSOR_TERM_DUPLICATE" for f in detail.findings)
        dashboard = release.dashboard(SECOND)
        assert (
            dashboard.inconsistencies.sponsor_impact.open
            + dashboard.inconsistencies.sponsor_impact.auto_resolved
            > 0
        )


def upload_disputed_membership(release, effective_date=FIRST):
    """Two catalogues disagreeing on which terms C1 holds — `INCONSISTENT_TERM_SETS`
    stays OPEN, nothing auto-resolves it, unlike a plain value dispute."""

    release.upload(
        package(
            "SDTM CT",
            effective_date,
            [
                codelist(
                    "C1",
                    "Test Codelist",
                    "TESTCL",
                    terms=[term("T1", "A"), term("T2", "B")],
                )
            ],
        ),
        package(
            "SEND CT",
            effective_date,
            [
                codelist(
                    "C1",
                    "Test Codelist",
                    "TESTCL",
                    terms=[term("T1", "A"), term("T3", "C")],
                )
            ],
        ),
    )
    return release.analyse(effective_date)


class TestReview:
    def test_marking_reviewed_is_refused_while_something_is_open(self, release):
        summary = upload_disputed_membership(release)
        assert summary.open_inconsistency_count >= 1

        with pytest.raises(ValidationException, match="open or informational finding"):
            release.review(FIRST, "C1")

    def test_marking_reviewed_succeeds_once_settled(self, release):
        upload_disputed_membership(release)
        for item in release.findings(FIRST, status="OPEN"):
            release.resolve(item.uid, strategy="IGNORE")

        review = release.review(FIRST, "C1")

        assert review.status.value == "REVIEWED"
        assert review.reviewed_by == "integration-test"
        assert review.reviewed_at is not None

    def test_reviewing_again_refreshes_who_and_when(self, release):
        upload_disputed_membership(release)
        for item in release.findings(FIRST, status="OPEN"):
            release.resolve(item.uid, strategy="IGNORE")

        first = release.review(FIRST, "C1")
        second = release.review(FIRST, "C1")

        assert second.reviewed_at >= first.reviewed_at

    def test_the_dashboard_and_list_reflect_a_review(self, release):
        upload_disputed_membership(release)
        for item in release.findings(FIRST, status="OPEN"):
            release.resolve(item.uid, strategy="IGNORE")
        release.review(FIRST, "C1")

        page = release.codelists(FIRST, show="all", page_size=0)
        [c1] = [row for row in page.items if row.codelist_id == "C1"]
        assert c1.review.status.value == "REVIEWED"

        dashboard = release.dashboard(FIRST)
        assert dashboard.review.reviewed == 1
        assert dashboard.review.stale == 0

    def test_a_reopened_item_makes_the_review_stale_but_keeps_the_audit_trail(
        self, release
    ):
        upload_disputed_membership(release)
        [item] = release.findings(FIRST, status="OPEN")
        release.resolve(item.uid, strategy="IGNORE")
        reviewed = release.review(FIRST, "C1")

        inconsistency_service.unresolve(item.uid)

        detail = release.codelist(FIRST, "C1")
        assert detail.review.status.value == "REVIEWED_STALE"
        assert detail.review.reviewed_by == reviewed.reviewed_by
        assert detail.review.reviewed_at == reviewed.reviewed_at

        dashboard = release.dashboard(FIRST)
        assert dashboard.review.stale == 1
        assert dashboard.review.reviewed == 0

    def test_marking_a_stale_review_again_clears_the_staleness(self, release):
        upload_disputed_membership(release)
        [item] = release.findings(FIRST, status="OPEN")
        release.resolve(item.uid, strategy="IGNORE")
        release.review(FIRST, "C1")
        inconsistency_service.unresolve(item.uid)
        release.resolve(item.uid, strategy="IGNORE")

        review = release.review(FIRST, "C1")

        assert review.status.value == "REVIEWED"

    def test_clearing_a_review_puts_it_back_to_not_reviewed(self, release):
        upload_disputed_membership(release)
        for item in release.findings(FIRST, status="OPEN"):
            release.resolve(item.uid, strategy="IGNORE")
        release.review(FIRST, "C1")

        cleared = release.unreview(FIRST, "C1")

        assert cleared.status.value == "NOT_REVIEWED"
        assert cleared.reviewed_by is None
        detail = release.codelist(FIRST, "C1")
        assert detail.review.status.value == "NOT_REVIEWED"

    def test_clearing_a_review_that_was_never_marked_is_a_no_op(self, release):
        upload_disputed_membership(release)

        cleared = release.unreview(FIRST, "C1")

        assert cleared.status.value == "NOT_REVIEWED"

    def test_reviewing_an_unknown_codelist_is_a_404(self, release):
        upload_disputed_membership(release)

        with pytest.raises(NotFoundException, match="C999"):
            release.review(FIRST, "C999")

    def test_clearing_an_unknown_codelists_review_is_a_404(self, release):
        upload_disputed_membership(release)

        with pytest.raises(NotFoundException, match="C999"):
            release.unreview(FIRST, "C999")


def snapshot_stamp(effective_date=SECOND):
    with staging_db.staging_session() as session:
        return review_snapshot_repository.get_snapshot_stamp(session, effective_date)


def in_scope_ids(release, effective_date=SECOND):
    return {
        row.codelist_id for row in release.codelists(effective_date, page_size=0).items
    }


class TestReviewSnapshot:
    """The review lists read rows worked out at analysis, not a fresh MDR diff."""

    def test_reading_after_analysis_never_diffs_against_mdr(self, release, monkeypatch):
        import_first(release)
        bring_in_second(release)

        def no_delta(*_args, **_kwargs):
            raise AssertionError("the review lists recomputed the delta")

        monkeypatch.setattr(import_service, "compute_delta", no_delta)

        assert in_scope_ids(release) == {"C1", "C3"}
        terms = {t.concept_id: t for t in release.terms(SECOND, page_size=0).items}
        assert terms["T2"].change_status == TermChangeStatus.DELETED
        assert terms["T4"].change_status == TermChangeStatus.NEW
        dashboard = release.dashboard(SECOND)
        assert (dashboard.codelists.new, dashboard.codelists.unchanged) == (1, 2)
        assert dashboard.memberships.ended == 1  # T2 leaving C1
        assert dashboard.review.in_scope == 2

    def test_analysis_stamps_the_snapshot_with_mdrs_head(self, release):
        import_first(release)
        bring_in_second(release)

        stamp = snapshot_stamp()

        assert stamp["snapshot_at"] is not None
        assert stamp["mdr_head"] == FIRST

    def test_a_snapshot_cleared_away_is_rebuilt_on_the_next_read(self, release):
        import_first(release)
        bring_in_second(release)
        with staging_db.staging_session() as session:
            review_snapshot_repository.clear_snapshot_stamp(session, SECOND)
            review_snapshot_repository.save_term_rows(session, SECOND, [])

        terms = {t.concept_id for t in release.terms(SECOND, page_size=0).items}

        assert {"T2", "T4"} <= terms
        assert snapshot_stamp()["snapshot_at"] is not None
        with staging_db.staging_session() as session:
            stored = review_snapshot_repository.get_term_change_ids(session, SECOND)
        assert set(stored) == terms

    def test_importing_an_older_release_overtakes_the_snapshot(self, release):
        """Analysed against an empty MDR, SECOND changes everything; once FIRST is in,
        C2 comes back unchanged. It stays listed, because the SPONSOR_NAME finding
        analysis raised for its term is not recomputed — only the delta is."""

        upload_first(release)
        release.analyse(FIRST)
        bring_in_second(release)
        assert in_scope_ids(release) == {"C1", "C2", "C3"}
        assert snapshot_stamp()["mdr_head"] is None

        release.assess(FIRST)
        job = release.import_now(FIRST)
        assert job.status.value == "SUCCEEDED", job.error

        rows = {
            row.codelist_id: row
            for row in release.codelists(SECOND, page_size=0, show="all").items
        }
        assert rows["C2"].term_changes.unchanged == 1
        assert rows["C2"].term_changes.new == rows["C2"].term_changes.updated == 0
        assert rows["C1"].term_changes.new == 1
        assert rows["C3"].term_changes.new == 1
        assert snapshot_stamp()["mdr_head"] == FIRST

    def test_importing_the_release_itself_keeps_what_it_changed(self, release):
        import_first(release)
        bring_in_second(release)
        for item in open_findings(release):
            release.resolve(item.uid, strategy="IGNORE")
        release.assess(SECOND)
        job = release.import_now(SECOND)
        assert job.status.value == "SUCCEEDED", job.error

        assert in_scope_ids(release) == {"C1", "C3"}
        assert snapshot_stamp()["mdr_head"] == FIRST

    def test_re_uploading_clears_the_stamp(self, release):
        import_first(release)
        bring_in_second(release)

        release.upload(
            package(
                "SDTM CT",
                SECOND,
                [codelist("C3", "New Codelist", "NEWCL", terms=[term("T10", "J")])],
            )
        )

        assert snapshot_stamp()["snapshot_at"] is None

    def test_clearing_the_derived_layer_takes_the_snapshot_with_it(self, release):
        import_first(release)
        bring_in_second(release)

        with staging_db.staging_session() as session:
            analysis_repository.clear_derived_layer(session, SECOND)
            stored = review_snapshot_repository.get_term_change_ids(session, SECOND)

        assert stored == []
        assert snapshot_stamp()["snapshot_at"] is None
