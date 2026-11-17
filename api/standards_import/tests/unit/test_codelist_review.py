"""The codelist-by-codelist review layer: pure regrouping and scoping logic.

The Cypher itself — grouping, the MDR diff, finding attribution — is what
`tests/integration/test_codelist_review.py` proves against real databases. This file
is for the logic on top: which codelists are "in scope", how a page is filtered and
sliced, what a diff reports, and that the codelist-scoped reads are actually scoped.
"""

from datetime import date, datetime
from typing import Any

import pytest

from common.exceptions import NotFoundException, ValidationException
from standards_import.models.codelists import (
    ChangeStatus,
    CodelistDetail,
    CodelistReview,
    CodelistSummary,
    CodelistTermSummary,
    FindingStatusCounts,
    ImpactedProperty,
    MembershipChange,
    ReviewStatus,
    TermChangeStatus,
    TermSummary,
)
from standards_import.models.imports import ChangeCounts, MembershipChanges
from standards_import.models.inconsistencies import (
    EntityType,
    Inconsistency,
    InconsistencyStatus,
    InconsistencyType,
)
from standards_import.repositories import (
    changelog_repository,
    codelist_review_repository,
    inconsistency_repository,
    job_repository,
    mdr_repository,
    release_repository,
    review_snapshot_repository,
)
from standards_import.services import (
    codelist_service,
    import_service,
    inconsistency_service,
    review_snapshot_service,
)
from standards_import.services.codelist_service import (
    action_rank,
    any_findings,
    attribute_changes,
    attribute_values,
    bucket_status,
    to_codelist_review,
    to_term_review,
)

# --- attribute_changes -------------------------------------------------------------


def row(attributes, head_props=None):
    return {
        "attributes": attributes,
        "head": {"props": head_props} if head_props else None,
    }


def test_no_head_reports_every_attribute_as_new():
    changes = attribute_changes(row({"name": "N", "definition": "D"}))

    fields = {c.field for c in changes}
    assert "name" in fields and "definition" in fields
    assert all(c.old_value is None for c in changes)


def test_identical_attributes_report_nothing():
    attributes = {
        "name": "N",
        "definition": "D",
        "submission_value": "SV",
        "extensible": True,
        "synonyms": ["a", "b"],
    }
    assert not attribute_changes(row(attributes, attributes))


def test_only_the_field_that_actually_changed_is_reported():
    wanted = {"name": "New name", "definition": "Same"}
    had = {"name": "Old name", "definition": "Same"}

    changes = attribute_changes(row(wanted, had))

    assert [c.field for c in changes] == ["name"]
    assert (changes[0].old_value, changes[0].new_value) == ("Old name", "New name")


def test_extensible_true_and_the_string_true_are_not_a_change():
    """CDISC ships `extensible` as the string `"true"`; comparing it raw to a Python
    bool would report every extensible codelist as changed."""

    wanted = {"extensible": "true"}
    had = {"extensible": True}

    assert not attribute_changes(row(wanted, had))


def test_synonyms_are_compared_regardless_of_order():
    wanted = {"synonyms": ["b", "a"]}
    had = {"synonyms": ["a", "b"]}

    assert not attribute_changes(row(wanted, had))


def test_preferred_term_and_concept_id_are_never_reported():
    """`preferred_term` mirrors `name` by construction; `concept_id` is identity, not
    a property that changes."""

    wanted = {"preferred_term": "New", "concept_id": "C1"}
    had = {"preferred_term": "Old", "concept_id": "C2"}

    assert not attribute_changes(row(wanted, had))


# --- attribute_values --------------------------------------------------------------


def test_attribute_values_lists_every_field_even_when_nothing_changed():
    attributes = {
        "name": "N",
        "definition": "D",
        "submission_value": "SV",
        "extensible": True,
        "synonyms": ["a"],
    }

    values = attribute_values(row(attributes, attributes))

    assert [(v.field, v.value) for v in values] == [
        ("name", "N"),
        ("definition", "D"),
        ("submission_value", "SV"),
        ("extensible", True),
        ("synonyms", ["a"]),
    ]


def test_attribute_values_reads_cdisc_string_extensible_as_a_boolean():
    values = {v.field: v.value for v in attribute_values(row({"extensible": "false"}))}

    assert values["extensible"] is False


def test_attribute_values_reports_missing_synonyms_as_an_empty_list():
    values = {v.field: v.value for v in attribute_values(row({"name": "N"}))}

    assert values["synonyms"] == []
    assert values["definition"] is None


# --- bucket_status -----------------------------------------------------------------


def test_bucket_status_maps_each_concept_id_to_its_bucket():
    bucket = {
        "new": [{"concept_id": "A"}],
        "updated": [{"concept_id": "B"}],
        "unchanged": [{"concept_id": "C"}],
    }

    assert bucket_status(bucket) == {"A": "NEW", "B": "UPDATED", "C": "UNCHANGED"}


# --- any_findings --------------------------------------------------------------


def test_any_findings_is_false_when_every_count_is_zero():
    assert any_findings(FindingStatusCounts()) is False


def test_any_findings_is_true_for_a_single_ignored_finding():
    assert any_findings(FindingStatusCounts(ignored=1)) is True


# --- action_rank -------------------------------------------------------------------


@pytest.mark.parametrize(
    "counts, rank",
    [
        ({"open": 1, "informational": 1}, 0),
        ({"informational": 1, "auto_resolved": 1}, 1),
        ({"auto_resolved": 1, "resolved": 1, "ignored": 1, "acknowledged": 1}, 2),
        ({}, 2),
    ],
)
def test_action_rank_puts_what_blocks_import_first(counts, rank):
    assert action_rank(FindingStatusCounts(**counts)) == rank


# --- list_codelists: filtering and pagination, summaries stubbed -------------------


def summary(
    codelist_id,
    change_status,
    open_count=0,
    findings_total=0,
    review=ReviewStatus.NOT_REVIEWED,
) -> tuple[bool, CodelistSummary]:
    findings = FindingStatusCounts(
        open=open_count, auto_resolved=max(findings_total - open_count, 0)
    )
    in_scope = change_status != ChangeStatus.UNCHANGED or any_findings(findings)
    built = CodelistSummary(
        codelist_id=codelist_id,
        change_status=change_status,
        term_changes=ChangeCounts(),
        memberships=MembershipChanges(),
        findings=findings,
        review=CodelistReview(status=review),
    )
    return in_scope, built


class _NullSession:
    def __enter__(self):
        return None

    def __exit__(self, *exc):
        return False


def null_session():
    return _NullSession()


def list_with(monkeypatch, summaries, **kwargs):
    monkeypatch.setattr(import_service, "require_release", lambda *_a, **_k: {})
    monkeypatch.setattr(review_snapshot_service, "codelist_rows", lambda *_a, **_k: [])
    monkeypatch.setattr(
        inconsistency_repository,
        "get_finding_counts_by_codelist",
        lambda *_a, **_k: {},
    )
    monkeypatch.setattr(codelist_review_repository, "get_reviews", lambda *_a, **_k: {})
    monkeypatch.setattr(
        codelist_service, "summarise_codelists", lambda *_a, **_k: summaries
    )
    monkeypatch.setattr(codelist_service, "staging_session", null_session)
    return codelist_service.list_codelists(date(2025, 9, 26), **kwargs)


def test_in_scope_is_the_default(monkeypatch):
    summaries = [summary("C1", ChangeStatus.NEW), summary("C2", ChangeStatus.UNCHANGED)]

    page = list_with(monkeypatch, summaries)

    assert [c.codelist_id for c in page.items] == ["C1"]


def test_show_all_includes_the_untouched_codelist(monkeypatch):
    summaries = [summary("C1", ChangeStatus.NEW), summary("C2", ChangeStatus.UNCHANGED)]

    page = list_with(monkeypatch, summaries, show="all")

    assert {c.codelist_id for c in page.items} == {"C1", "C2"}


def test_change_status_filter(monkeypatch):
    summaries = [summary("C1", ChangeStatus.NEW), summary("C2", ChangeStatus.UPDATED)]

    page = list_with(
        monkeypatch, summaries, show="all", change_status=ChangeStatus.UPDATED
    )

    assert [c.codelist_id for c in page.items] == ["C2"]


def test_has_open_findings_filter(monkeypatch):
    summaries = [
        summary("C1", ChangeStatus.UNCHANGED, open_count=1, findings_total=1),
        summary("C1b", ChangeStatus.UNCHANGED, open_count=0, findings_total=1),
    ]

    page = list_with(monkeypatch, summaries, show="all", has_open_findings=True)

    assert [c.codelist_id for c in page.items] == ["C1"]


def test_review_status_not_reviewed_matches_everything_in_phase_one(monkeypatch):
    summaries = [summary("C1", ChangeStatus.NEW)]

    page = list_with(
        monkeypatch, summaries, show="all", review_status=ReviewStatus.NOT_REVIEWED
    )

    assert [c.codelist_id for c in page.items] == ["C1"]


def test_review_status_reviewed_matches_nothing_in_phase_one(monkeypatch):
    """No codelist can be REVIEWED yet — that lands in Phase 2 — so filtering for it
    is a legitimate way to ask "which of these have been reviewed" and correctly get
    an empty answer rather than an error."""

    summaries = [summary("C1", ChangeStatus.NEW)]

    page = list_with(
        monkeypatch, summaries, show="all", review_status=ReviewStatus.REVIEWED
    )

    assert page.items == []
    assert page.total == 0


def test_a_page_size_of_zero_returns_every_matching_row(monkeypatch):
    summaries = [summary(f"C{i}", ChangeStatus.NEW) for i in range(5)]

    page = list_with(monkeypatch, summaries, show="all", page_size=0)

    assert len(page.items) == page.total == 5


def test_pagination_slices_after_filtering(monkeypatch):
    summaries = [summary(f"C{i}", ChangeStatus.NEW) for i in range(5)]

    page = list_with(monkeypatch, summaries, show="all", page_number=2, page_size=2)

    assert page.total == 5
    assert [c.codelist_id for c in page.items] == ["C2", "C3"]


def test_items_are_sorted_by_codelist_id(monkeypatch):
    summaries = [summary("C9", ChangeStatus.NEW), summary("C2", ChangeStatus.NEW)]

    page = list_with(monkeypatch, summaries, show="all")

    assert [c.codelist_id for c in page.items] == ["C2", "C9"]


def test_codelists_needing_action_come_first(monkeypatch):
    summaries = [
        summary("C1", ChangeStatus.NEW),
        summary("C2", ChangeStatus.UNCHANGED, findings_total=1),
        summary("C8", ChangeStatus.UNCHANGED, open_count=1, findings_total=1),
        summary("C9", ChangeStatus.NEW, open_count=2, findings_total=2),
    ]
    in_scope, informational = summary("C5", ChangeStatus.UPDATED)
    informational.findings.informational = 1
    summaries.append((in_scope, informational))

    page = list_with(monkeypatch, summaries, show="all")

    # Open first, then informational, then the rest - by id within each.
    assert [c.codelist_id for c in page.items] == ["C8", "C9", "C5", "C1", "C2"]


def test_needing_action_first_holds_across_pages(monkeypatch):
    summaries = [summary(f"C{i}", ChangeStatus.NEW) for i in range(4)]
    summaries.append(summary("C9", ChangeStatus.NEW, open_count=1, findings_total=1))

    page = list_with(monkeypatch, summaries, show="all", page_number=1, page_size=2)

    assert [c.codelist_id for c in page.items] == ["C9", "C0"]


def named_summary(codelist_id, submission_value, name) -> tuple[bool, CodelistSummary]:
    in_scope, built = summary(codelist_id, ChangeStatus.NEW)
    built.submission_value = submission_value
    built.name = name
    return in_scope, built


@pytest.mark.parametrize(
    "search, expected",
    [
        ("c66742", ["C66742"]),  # codelist id, whatever the case
        ("NY", ["C66742"]),  # submission value
        ("route of", ["C66729"]),  # name
        ("  ny  ", ["C66742"]),  # surrounding blanks ignored
        ("", ["C66729", "C66742"]),  # empty means no search
        ("nothing", []),
    ],
)
def test_search_matches_id_submission_value_or_name(monkeypatch, search, expected):
    summaries = [
        named_summary("C66742", "NY", "No Yes Response"),
        named_summary("C66729", "ROUTE", "Route of Administration"),
    ]

    page = list_with(monkeypatch, summaries, search=search)

    assert [c.codelist_id for c in page.items] == expected
    assert page.total == len(expected)


def test_search_skips_a_codelist_without_name_or_submission_value(monkeypatch):
    summaries = [summary("C1", ChangeStatus.NEW)]

    page = list_with(monkeypatch, summaries, search="route")

    assert page.items == []


# --- list_terms: filtering and pagination, summaries stubbed -----------------------


def term_summary(
    concept_id,
    change_status,
    open_count=0,
    findings_total=0,
    review=ReviewStatus.NOT_REVIEWED,
) -> TermSummary:
    findings = FindingStatusCounts(
        open=open_count, auto_resolved=max(findings_total - open_count, 0)
    )
    return TermSummary(
        concept_id=concept_id,
        change_status=change_status,
        findings=findings,
        review=CodelistReview(status=review),
    )


def list_terms_with(monkeypatch, summaries, **kwargs):
    monkeypatch.setattr(import_service, "require_release", lambda *_a, **_k: {})
    monkeypatch.setattr(review_snapshot_service, "term_rows", lambda *_a, **_k: [])
    monkeypatch.setattr(
        inconsistency_repository, "get_finding_counts_by_term", lambda *_a, **_k: {}
    )
    monkeypatch.setattr(codelist_review_repository, "get_reviews", lambda *_a, **_k: {})
    monkeypatch.setattr(
        codelist_service, "summarise_terms", lambda *_a, **_k: summaries
    )
    monkeypatch.setattr(codelist_service, "staging_session", null_session)
    return codelist_service.list_terms(date(2025, 9, 26), **kwargs)


def test_terms_change_status_filter_selects_deleted(monkeypatch):
    summaries = [
        term_summary("T1", TermChangeStatus.CHANGED),
        term_summary("T2", TermChangeStatus.DELETED),
    ]

    page = list_terms_with(
        monkeypatch, summaries, change_status=TermChangeStatus.DELETED
    )

    assert [t.concept_id for t in page.items] == ["T2"]


def test_terms_has_findings_filter(monkeypatch):
    summaries = [
        term_summary("T1", TermChangeStatus.CHANGED, findings_total=1),
        term_summary("T2", TermChangeStatus.CHANGED),
    ]

    page = list_terms_with(monkeypatch, summaries, has_findings=True)

    assert [t.concept_id for t in page.items] == ["T1"]


def test_terms_has_open_findings_filter(monkeypatch):
    summaries = [
        term_summary("T1", TermChangeStatus.CHANGED, open_count=1, findings_total=1),
        term_summary("T2", TermChangeStatus.CHANGED, open_count=0, findings_total=1),
    ]

    page = list_terms_with(monkeypatch, summaries, has_open_findings=True)

    assert [t.concept_id for t in page.items] == ["T1"]


def test_terms_review_status_filter(monkeypatch):
    summaries = [
        term_summary("T1", TermChangeStatus.NEW, review=ReviewStatus.REVIEWED),
        term_summary("T2", TermChangeStatus.NEW),
    ]

    page = list_terms_with(monkeypatch, summaries, review_status=ReviewStatus.REVIEWED)

    assert [t.concept_id for t in page.items] == ["T1"]


def test_a_term_page_size_of_zero_returns_every_matching_row(monkeypatch):
    summaries = [term_summary(f"T{i}", TermChangeStatus.NEW) for i in range(5)]

    page = list_terms_with(monkeypatch, summaries, page_size=0)

    assert len(page.items) == page.total == 5


def test_term_pagination_slices_after_filtering(monkeypatch):
    summaries = [term_summary(f"T{i}", TermChangeStatus.NEW) for i in range(5)]

    page = list_terms_with(monkeypatch, summaries, page_number=2, page_size=2)

    assert page.total == 5
    assert [t.concept_id for t in page.items] == ["T2", "T3"]


def test_terms_are_sorted_by_concept_id(monkeypatch):
    summaries = [
        term_summary("T9", TermChangeStatus.NEW),
        term_summary("T2", TermChangeStatus.NEW),
    ]

    page = list_terms_with(monkeypatch, summaries)

    assert [t.concept_id for t in page.items] == ["T2", "T9"]


@pytest.mark.parametrize(
    "search, expected",
    [
        ("c49488", ["C49488"]),  # concept id, whatever the case
        ("unkn", ["C17998"]),  # preferred term
        ("nothing", []),
    ],
)
def test_term_search_matches_concept_id_or_preferred_term(
    monkeypatch, search, expected
):
    summaries = [
        term_summary("C49488", TermChangeStatus.CHANGED),
        term_summary("C17998", TermChangeStatus.CHANGED),
    ]
    summaries[0].preferred_term = "Yes"
    summaries[1].preferred_term = "Unknown"

    page = list_terms_with(monkeypatch, summaries, search=search)

    assert [t.concept_id for t in page.items] == expected
    assert page.total == len(expected)


def test_term_search_applies_before_pagination(monkeypatch):
    summaries = [term_summary(f"T{i}", TermChangeStatus.NEW) for i in range(5)]
    summaries.append(term_summary("X1", TermChangeStatus.NEW))

    page = list_terms_with(monkeypatch, summaries, search="x", page_size=2)

    assert page.total == 1
    assert [t.concept_id for t in page.items] == ["X1"]


# --- attribute_changes for a term --------------------------------------------------


def test_term_fields_match_what_the_import_actually_compares():
    """If these drift apart, a term reports an impacted property the diff never looked
    at, or stays silent about one it did."""

    compared = set(import_service.term_attributes("C1", {})) - {"concept_id"}

    assert compared == set(review_snapshot_service.TERM_FIELDS)


def test_a_terms_preferred_term_change_is_reported():
    """The codelist default suppresses `preferred_term` because it mirrors `name`. For a
    term it is the attribute that carries the CDISC wording, so `TERM_FIELDS` has to
    bring it back."""

    wanted = {"preferred_term": "New", "definition": "Same"}
    had = {"preferred_term": "Old", "definition": "Same"}

    changes = attribute_changes(
        row(wanted, had), fields=review_snapshot_service.TERM_FIELDS
    )

    assert [c.field for c in changes] == ["preferred_term"]


def test_a_terms_name_and_submission_value_are_never_reported_as_attribute_changes():
    """Neither is a term attribute the release diffs: the sponsor name is never
    rewritten, and a submission value belongs to a membership."""

    wanted = {"name": "New", "submission_value": "NEW"}
    had = {"name": "Old", "submission_value": "OLD"}

    assert not attribute_changes(
        row(wanted, had), fields=review_snapshot_service.TERM_FIELDS
    )


# --- to_term_review: inherited from the covering codelists -------------------------


def reviewed(author, at):
    return {"author_id": author, "reviewed_at": at}


def test_a_term_in_no_codelist_is_not_reviewed():
    """Nothing covers it, so nothing vouches for it — not vacuously reviewed."""

    assert to_term_review({}, set(), has_open_finding=False) == CodelistReview()


def test_a_term_is_not_reviewed_while_any_of_its_codelists_is_unmarked():
    reviews = {"C1": reviewed("alice", datetime(2025, 9, 26, 10, 0))}

    result = to_term_review(reviews, {"C1", "C2"}, has_open_finding=False)

    assert result.status == ReviewStatus.NOT_REVIEWED
    assert result.reviewed_by is None


def test_a_term_is_reviewed_once_every_covering_codelist_is():
    reviews = {
        "C1": reviewed("alice", datetime(2025, 9, 26, 10, 0)),
        "C2": reviewed("bob", datetime(2025, 9, 26, 11, 0)),
    }

    result = to_term_review(reviews, {"C1", "C2"}, has_open_finding=False)

    assert result.status == ReviewStatus.REVIEWED


def test_the_latest_of_the_covering_reviews_is_the_one_reported():
    """ "This term was reviewed" is only as recent as the last walkthrough covering it."""

    reviews = {
        "C1": reviewed("alice", datetime(2025, 9, 26, 10, 0)),
        "C2": reviewed("bob", datetime(2025, 9, 26, 11, 0)),
    }

    result = to_term_review(reviews, {"C1", "C2"}, has_open_finding=False)

    assert result.reviewed_by == "bob"
    assert result.reviewed_at == datetime(2025, 9, 26, 11, 0)


def test_an_open_finding_makes_a_reviewed_term_stale():
    reviews = {"C1": reviewed("alice", datetime(2025, 9, 26, 10, 0))}

    result = to_term_review(reviews, {"C1"}, has_open_finding=True)

    assert result.status == ReviewStatus.REVIEWED_STALE
    assert result.reviewed_by == "alice"


# --- build_term_rows + summarise_terms: change status, impact, membership ----------


def term_row(concept_id, preferred_term="Term", head=None):
    return {
        "concept_id": concept_id,
        "attributes": {"preferred_term": preferred_term},
        "head": {"props": head} if head else None,
    }


def build_terms(*, terms, memberships, added=(), ended=(), findings=None):
    """Builds the term rows from a hand-made delta, then summarises them the way
    `list_terms` does. Each deleted term is named `Gone <id>`, as if MDR said so."""

    delta = {
        "terms": terms,
        "memberships_added": list(added),
        "memberships_ended": list(ended),
    }
    deleted_heads = {
        uid: {"props": {"preferred_term": f"Gone {uid}"}}
        for uid in review_snapshot_service.deleted_term_ids(delta)
    }
    rows = review_snapshot_service.build_term_rows(delta, memberships, deleted_heads)
    return {
        term.concept_id: term
        for term in codelist_service.summarise_terms(rows, findings or {}, {})
    }


def membership(codelist_id, term_id, submission_value):
    return {
        "codelist_id": codelist_id,
        "term_id": term_id,
        "submission_value": submission_value,
    }


def delta_membership(codelist_uid, term_uid, submission_value):
    return {
        "codelist_uid": codelist_uid,
        "term_uid": term_uid,
        "submission_value": submission_value,
    }


def buckets(new=(), updated=(), unchanged=()):
    return {
        "new": list(new),
        "updated": list(updated),
        "unchanged": list(unchanged),
        "all": [*new, *updated, *unchanged],
    }


def test_a_term_gone_from_every_codelist_is_deleted():
    """Nothing in the release defines it any more and its only membership closed."""

    result = build_terms(
        terms=buckets(),
        memberships=[],
        ended=[delta_membership("C1", "T1", "A")],
    )

    term = result["T1"]
    assert term.change_status == TermChangeStatus.DELETED
    assert term.impacted == [ImpactedProperty.MEMBERSHIP]


def test_a_deleted_terms_name_comes_from_mdr():
    """The release says nothing about it, so there is no staging name to show."""

    result = build_terms(
        terms=buckets(),
        memberships=[],
        ended=[delta_membership("C1", "T1", "A")],
    )

    assert result["T1"].preferred_term == "Gone T1"


def test_a_term_leaving_one_of_two_codelists_is_changed_not_deleted():
    """It still ships in the release — only the set of codelists holding it moved."""

    result = build_terms(
        terms=buckets(unchanged=[term_row("T1")]),
        memberships=[membership("C1", "T1", "A")],
        ended=[delta_membership("C2", "T1", "A")],
    )

    term = result["T1"]
    assert term.change_status == TermChangeStatus.CHANGED
    assert term.impacted == [ImpactedProperty.MEMBERSHIP]
    assert term.codelist_count == 1


def test_the_same_codelist_on_both_sides_is_a_submission_value_change():
    """A value moving looks like an ended membership plus an added one. The term has not
    changed codelists, so reporting `membership` would be wrong."""

    result = build_terms(
        terms=buckets(unchanged=[term_row("T1")]),
        memberships=[membership("C1", "T1", "NEW")],
        added=[delta_membership("C1", "T1", "NEW")],
        ended=[delta_membership("C1", "T1", "OLD")],
    )

    term = result["T1"]
    assert term.impacted == [ImpactedProperty.SUBMISSION_VALUE]
    assert term.change_status == TermChangeStatus.CHANGED


def test_an_updated_terms_impacted_properties_come_from_its_attributes():
    rows = [term_row("T1", "New name", head={"preferred_term": "Old name"})]

    result = build_terms(
        terms=buckets(updated=rows),
        memberships=[membership("C1", "T1", "A")],
    )

    term = result["T1"]
    assert term.impacted == [ImpactedProperty.PREFERRED_TERM]
    assert [(c.old_value, c.new_value) for c in term.changes] == [
        ("Old name", "New name")
    ]


def test_a_new_term_reports_no_impacted_properties():
    """Everything about it is new, so naming individual properties says nothing."""

    result = build_terms(
        terms=buckets(new=[term_row("T1")]),
        memberships=[membership("C1", "T1", "A")],
        added=[delta_membership("C1", "T1", "A")],
    )

    term = result["T1"]
    assert term.change_status == TermChangeStatus.NEW
    assert term.impacted == []


def test_an_untouched_term_is_not_listed():
    result = build_terms(
        terms=buckets(unchanged=[term_row("T1")]),
        memberships=[membership("C1", "T1", "A")],
    )

    assert "T1" not in result


def test_an_untouched_term_with_a_finding_is_still_not_listed():
    """The finding is not lost: it still counts against the codelist holding the term."""

    result = build_terms(
        terms=buckets(unchanged=[term_row("T1")]),
        memberships=[membership("C1", "T1", "A")],
        findings={"T1": {"OPEN": 1}},
    )

    assert "T1" not in result


def test_a_terms_codelist_count_is_the_codelists_holding_it():
    """One per codelist, however the release reaches it."""

    rows = [term_row("T1", "New name", head={"preferred_term": "Old name"})]

    result = build_terms(
        terms=buckets(updated=rows),
        memberships=[membership("C1", "T1", "A"), membership("C2", "T1", "B")],
    )

    assert result["T1"].codelist_count == 2


def test_a_deleted_term_is_held_by_no_codelist():
    """Its memberships are all ending, and an ended membership no longer holds it."""

    result = build_terms(
        terms=buckets(),
        memberships=[],
        ended=[delta_membership("C1", "T1", "A"), delta_membership("C2", "T1", "B")],
    )

    assert result["T1"].codelist_count == 0


# --- build_codelist_rows + summarise_codelists: tallies and scope ------------------


def codelist_delta_row(concept_id, name="Codelist"):
    return {"concept_id": concept_id, "attributes": {"name": name}}


def build_codelists(*, codelists, terms=None, memberships=(), added=(), findings=None):
    """Builds the codelist rows from a hand-made delta, then summarises them the way
    `list_codelists` does, keyed by codelist with whether each is in scope."""

    delta = {
        "codelists": codelists,
        "terms": terms or buckets(),
        "memberships_added": list(added),
        "memberships_ended": [],
    }
    rows = review_snapshot_service.build_codelist_rows(delta, list(memberships))
    return {
        summary.codelist_id: (in_scope, summary)
        for in_scope, summary in codelist_service.summarise_codelists(
            rows, findings or {}, {}
        )
    }


def test_a_codelists_term_tally_counts_what_it_holds():
    result = build_codelists(
        codelists=buckets(unchanged=[codelist_delta_row("C1")]),
        terms=buckets(
            new=[term_row("T1")], updated=[term_row("T2")], unchanged=[term_row("T3")]
        ),
        memberships=[
            membership("C1", "T1", "A"),
            membership("C1", "T2", "B"),
            membership("C1", "T3", "C"),
        ],
    )

    _, summary = result["C1"]
    assert (summary.term_changes.new, summary.term_changes.updated) == (1, 1)
    assert summary.term_changes.unchanged == 1
    assert summary.term_changes.new_examples == ["T1"]


def test_an_untouched_codelist_is_out_of_scope():
    result = build_codelists(codelists=buckets(unchanged=[codelist_delta_row("C1")]))

    in_scope, summary = result["C1"]
    assert not in_scope
    assert summary.change_status == ChangeStatus.UNCHANGED


def test_an_untouched_codelist_with_a_finding_is_in_scope():
    """The delta's half of scope is stored; the findings half is decided on reading,
    so settling a finding never needs the snapshot rebuilt."""

    result = build_codelists(
        codelists=buckets(unchanged=[codelist_delta_row("C1")]),
        findings={"C1": {"RESOLVED": 1}},
    )

    in_scope, _ = result["C1"]
    assert in_scope


def test_a_codelist_gaining_a_term_is_in_scope():
    result = build_codelists(
        codelists=buckets(unchanged=[codelist_delta_row("C1")]),
        added=[delta_membership("C1", "T1", "A")],
    )

    in_scope, summary = result["C1"]
    assert in_scope
    assert summary.memberships.added == 1


# --- review snapshot: when the stored rows still hold ------------------------------


def stamp_at(mdr_head, has_summary=True):
    return {
        "snapshot_at": datetime(2025, 9, 26),
        "mdr_head": mdr_head,
        "has_summary": has_summary,
    }


@pytest.mark.parametrize(
    "stamp, mdr_head, holds",
    [
        (None, "2025-06-27", False),
        ({"snapshot_at": None, "mdr_head": None, "has_summary": False}, None, False),
        (stamp_at("2025-03-28"), "2025-06-27", False),
        (stamp_at("2025-06-27"), "2025-06-27", True),
        (stamp_at(None), None, True),
        (stamp_at("2025-06-27", has_summary=False), "2025-06-27", False),
    ],
    ids=[
        "never-taken",
        "cleared",
        "mdr-moved-on",
        "same-head",
        "empty-mdr",
        "taken-before-summaries",
    ],
)
def test_a_snapshot_holds_only_against_the_head_it_was_taken_against(
    stamp, mdr_head, holds
):
    assert review_snapshot_service.snapshot_holds(stamp, mdr_head) is holds


def ensure_with(monkeypatch, *, stamp, mdr_head="2025-06-27", running_job=None):
    """Runs `ensure_review_snapshot` with every read stubbed, recording what it did."""

    calls: list[str] = []
    built = review_snapshot_service.ReviewSnapshot(
        codelists=[{"codelist_id": "C1"}],
        terms=[{"concept_id": "T1"}],
        summary={"catalogues": ["SDTM CT"]},
    )

    def recorded(name):
        def fake(*_args, **_kwargs):
            calls.append(name)
            return built

        return fake

    monkeypatch.setattr(
        review_snapshot_repository, "get_snapshot_stamp", lambda *_a, **_k: stamp
    )
    monkeypatch.setattr(
        mdr_repository, "get_head_effective_date", lambda **_k: mdr_head
    )
    monkeypatch.setattr(
        job_repository, "find_running_job", lambda *_a, **_k: running_job
    )
    monkeypatch.setattr(review_snapshot_service, "build_rows", recorded("build"))
    monkeypatch.setattr(review_snapshot_service, "rebuild", recorded("rebuild"))
    result = review_snapshot_service.ensure_review_snapshot(
        None, "2025-09-26"  # type: ignore[arg-type]
    )
    return result, calls


def test_a_holding_snapshot_is_read_as_stored(monkeypatch):
    result, calls = ensure_with(monkeypatch, stamp=stamp_at("2025-06-27"))

    assert result is None
    assert not calls


def test_a_missing_snapshot_is_rebuilt_and_stored(monkeypatch):
    """A release analysed before snapshots existed needs no backfill: its first read
    builds one."""

    result, calls = ensure_with(monkeypatch, stamp={"snapshot_at": None})

    assert calls == ["rebuild"]
    assert result is not None


def test_a_snapshot_is_not_stored_while_a_step_runs_on_the_release(monkeypatch):
    """The running step is about to change what the rows were built from; storing them
    would vouch for a delta it is replacing."""

    result, calls = ensure_with(
        monkeypatch, stamp=None, running_job={"uid": "job", "kind": "ANALYSIS"}
    )

    assert calls == ["build"]
    assert result is not None


def test_a_running_step_costs_the_dashboard_one_build_not_two(monkeypatch):
    """The summary and the codelist rows come from the same build, not one each."""

    monkeypatch.setattr(
        review_snapshot_service, "ensure_review_snapshot", lambda *_a: None
    )
    monkeypatch.setattr(
        review_snapshot_repository, "get_release_summary", lambda *_a: None
    )
    builds: list[str] = []
    built = review_snapshot_service.ReviewSnapshot(
        codelists=[{"codelist_id": "C1"}], terms=[], summary={"catalogues": []}
    )

    def build(*_args):
        builds.append("build")
        return built

    monkeypatch.setattr(review_snapshot_service, "build_rows", build)

    summary, rows = review_snapshot_service.dashboard_inputs(
        None, "2025-09-26"  # type: ignore[arg-type]
    )

    assert builds == ["build"]
    assert (summary, rows) == (built.summary, built.codelists)


def delta_for_summary(added=(), ended=()):
    return {
        "packages": [{"name": "SDTM CT 2025-09-26"}],
        "codelists": buckets(unchanged=[codelist_delta_row("C1")]),
        "terms": buckets(new=[term_row("T1")]),
        "memberships_added": list(added),
        "memberships_ended": list(ended),
    }


def test_the_release_summary_answers_the_blockers_as_the_full_delta_would():
    delta = delta_for_summary(
        added=[
            delta_membership("C1", "T1", "NEW VALUE"),  # value change
            delta_membership("C1", "T5", "E"),  # plain addition
        ],
        ended=[
            delta_membership("C1", "T1", "OLD VALUE"),
            delta_membership("C1", "T2", "B"),  # removal
        ],
    )

    stored = review_snapshot_service.build_release_summary(delta)["membership_changes"]

    assert import_service.changed_and_removed_memberships(
        stored
    ) == import_service.changed_and_removed_memberships(delta)


def test_the_release_summary_keeps_no_opening_that_changes_nothing():
    """On a first release every membership is an opening; none of them can be a value
    change or a removal, so none is worth storing."""

    delta = delta_for_summary(added=[delta_membership("C1", "T1", "A")])

    summary = review_snapshot_service.build_release_summary(delta)

    assert summary["membership_changes"]["memberships_added"] == []
    assert summary["memberships_added"] == 1
    assert summary["catalogues"] == ["SDTM CT 2025-09-26"]
    assert ChangeCounts.model_validate(summary["terms"]).new == 1


# --- get_codelist_detail: the 404 guard, repositories stubbed ----------------------


def test_an_unknown_codelist_raises_not_found(monkeypatch):
    monkeypatch.setattr(import_service, "require_release", lambda *_a, **_k: {})
    other = {"concept_id": "OTHER"}
    monkeypatch.setattr(
        import_service,
        "diff_codelists",
        lambda *_a, **_k: {
            "all": [other],
            "new": [],
            "updated": [],
            "unchanged": [other],
        },
    )
    monkeypatch.setattr(codelist_service, "staging_session", null_session)

    with pytest.raises(NotFoundException, match="MISSING"):
        codelist_service.get_codelist_detail(date(2025, 9, 26), "MISSING")


# --- diff_codelist_terms / diff_codelist_memberships: scoping ----------------------


def test_diff_codelist_terms_reads_and_diffs_only_that_codelist(monkeypatch):
    seen = {}

    def fake_get_codelist_terms(_session, package_date, codelist_id):
        seen["package_date"], seen["codelist_id"] = package_date, codelist_id
        return [
            {
                "concept_id": "T1",
                "props": {"preferredTerm": "Term T1"},
                "submission_value": "A",
            }
        ]

    monkeypatch.setattr(
        release_repository, "get_codelist_terms", fake_get_codelist_terms
    )
    monkeypatch.setattr(mdr_repository, "get_term_heads", lambda uids, _pd: {})

    result = import_service.diff_codelist_terms(None, "2025-09-26", "C1")

    assert seen == {"package_date": "2025-09-26", "codelist_id": "C1"}
    assert [r["concept_id"] for r in result["new"]] == ["T1"]


def test_diff_codelist_memberships_compares_only_that_codelists_mdr_state(monkeypatch):
    seen = {}

    def fake_get_open_memberships(codelist_uids):
        seen["codelist_uids"] = codelist_uids
        return {("C1", "T2", "B")}

    monkeypatch.setattr(
        mdr_repository, "get_open_memberships", fake_get_open_memberships
    )

    rows = [{"concept_id": "T1", "submission_value": "A"}]
    added, ended = import_service.diff_codelist_memberships("2025-09-26", "C1", rows)

    assert seen == {"codelist_uids": ["C1"]}
    assert [m["term_uid"] for m in added] == ["T1"]
    assert [m["term_uid"] for m in ended] == ["T2"]


# --- to_codelist_review: deriving status rather than storing it -------------------


def test_no_record_is_not_reviewed():
    review = to_codelist_review(None, has_open_finding=True)

    assert review == CodelistReview()


def test_a_record_with_nothing_open_is_reviewed():
    record = {"author_id": "jdoe", "reviewed_at": datetime(2026, 9, 14, 9, 0)}

    review = to_codelist_review(record, has_open_finding=False)

    assert review.status == ReviewStatus.REVIEWED
    assert review.reviewed_by == "jdoe"
    assert review.reviewed_at == datetime(2026, 9, 14, 9, 0)


def test_a_record_with_something_open_is_stale_but_keeps_the_audit_trail():
    record = {"author_id": "jdoe", "reviewed_at": datetime(2026, 9, 14, 9, 0)}

    review = to_codelist_review(record, has_open_finding=True)

    assert review.status == ReviewStatus.REVIEWED_STALE
    assert review.reviewed_by == "jdoe"
    assert review.reviewed_at == datetime(2026, 9, 14, 9, 0)


# --- mark_reviewed: the OPEN-finding guard, get_codelist_detail stubbed -----------


def finding(status, concept_id="T1"):
    return Inconsistency(
        uid=f"finding-{concept_id}-{status}",
        effective_date=date(2025, 9, 26),
        type=InconsistencyType.CONFLICTING_VALUES,
        entity_type=EntityType.TERM,
        concept_id=concept_id,
        status=status,
        detected_at=datetime(2026, 9, 14, 9, 0),
    )


def detail_with(findings=(), terms=()):
    return CodelistDetail(
        codelist_id="C1",
        change_status=ChangeStatus.UNCHANGED,
        findings=list(findings),
        terms=list(terms),
        term_count=len(terms),
        review=CodelistReview(),
    )


class _FakeUser:
    def id(self):
        return "jdoe"


def test_marking_reviewed_is_refused_while_a_codelist_level_finding_is_open(
    monkeypatch,
):
    monkeypatch.setattr(
        codelist_service,
        "get_codelist_detail",
        lambda *_a, **_k: detail_with(findings=[finding(InconsistencyStatus.OPEN)]),
    )

    with pytest.raises(ValidationException, match="1 open or informational finding"):
        codelist_service.mark_reviewed(date(2025, 9, 26), "C1")


def test_marking_reviewed_is_refused_while_a_term_level_finding_is_open(monkeypatch):
    term = CodelistTermSummary(
        concept_id="T1",
        change_status=ChangeStatus.UPDATED,
        findings=[finding(InconsistencyStatus.OPEN)],
    )
    monkeypatch.setattr(
        codelist_service,
        "get_codelist_detail",
        lambda *_a, **_k: detail_with(terms=[term]),
    )

    with pytest.raises(ValidationException, match="1 open or informational finding"):
        codelist_service.mark_reviewed(date(2025, 9, 26), "C1")


def test_marking_reviewed_is_also_refused_by_an_informational_finding(monkeypatch):
    """Review is a wider guarantee than import: import never waits on INFORMATIONAL,
    but "reviewed" means a person looked at everything on the codelist, informational
    items included."""

    monkeypatch.setattr(
        codelist_service,
        "get_codelist_detail",
        lambda *_a, **_k: detail_with(
            findings=[finding(InconsistencyStatus.INFORMATIONAL)]
        ),
    )

    with pytest.raises(ValidationException, match="1 open or informational finding"):
        codelist_service.mark_reviewed(date(2025, 9, 26), "C1")


def test_an_informational_finding_makes_the_detail_view_report_it_unreviewable():
    """`get_codelist_detail`'s `has_open` feeds `to_codelist_review`, which is what
    decides REVIEWED vs REVIEWED_STALE — an informational finding must widen that the
    same way it widens `mark_reviewed`'s guard."""

    assert codelist_service.blocks_review(finding(InconsistencyStatus.INFORMATIONAL))
    assert codelist_service.blocks_review(finding(InconsistencyStatus.OPEN))
    assert not codelist_service.blocks_review(finding(InconsistencyStatus.RESOLVED))
    assert not codelist_service.blocks_review(finding(InconsistencyStatus.IGNORED))


def test_marking_reviewed_checked_against_show_all_not_the_default_filter(
    monkeypatch,
):
    """A finding on a term hidden behind the default `show=changed` filter must still
    block — the guard has to see what `show=all` sees, not what a caller happened to
    request."""

    seen_kwargs = {}

    def fake_detail(_effective_date, _codelist_id, **kwargs):
        seen_kwargs.update(kwargs)
        return detail_with()

    monkeypatch.setattr(codelist_service, "get_codelist_detail", fake_detail)
    monkeypatch.setattr(codelist_service, "staging_session", null_session)
    monkeypatch.setattr(codelist_service, "user", _FakeUser)
    monkeypatch.setattr(
        codelist_review_repository,
        "mark_reviewed",
        lambda *_a, **_k: {"author_id": "jdoe", "reviewed_at": datetime(2026, 9, 14)},
    )

    codelist_service.mark_reviewed(date(2025, 9, 26), "C1")

    assert seen_kwargs == {"show": "all"}


def test_marking_reviewed_with_nothing_open_records_it(monkeypatch):
    seen = {}

    def fake_mark_reviewed(_session, package_date, codelist_id, author_id):
        seen.update(
            package_date=package_date, codelist_id=codelist_id, author_id=author_id
        )
        return {"author_id": author_id, "reviewed_at": datetime(2026, 9, 14, 9, 0)}

    monkeypatch.setattr(
        codelist_service, "get_codelist_detail", lambda *_a, **_k: detail_with()
    )
    monkeypatch.setattr(codelist_service, "staging_session", null_session)
    monkeypatch.setattr(codelist_review_repository, "mark_reviewed", fake_mark_reviewed)
    monkeypatch.setattr(codelist_service, "user", _FakeUser)

    review = codelist_service.mark_reviewed(date(2025, 9, 26), "C1")

    assert seen == {
        "package_date": "2025-09-26",
        "codelist_id": "C1",
        "author_id": "jdoe",
    }
    assert review.status == ReviewStatus.REVIEWED
    assert review.reviewed_by == "jdoe"


# --- clear_review: exists-or-404, otherwise an unconditional no-op ----------------


def test_clearing_review_of_an_unknown_codelist_is_a_404(monkeypatch):
    monkeypatch.setattr(import_service, "require_release", lambda *_a, **_k: {})
    monkeypatch.setattr(
        import_service,
        "diff_codelists",
        lambda *_a, **_k: {"all": [], "new": [], "updated": [], "unchanged": []},
    )
    monkeypatch.setattr(codelist_service, "staging_session", null_session)

    with pytest.raises(NotFoundException, match="MISSING"):
        codelist_service.clear_review(date(2025, 9, 26), "MISSING")


def test_clearing_review_of_a_known_codelist_calls_the_repository(monkeypatch):
    seen = {}
    other = {"concept_id": "C1"}
    monkeypatch.setattr(import_service, "require_release", lambda *_a, **_k: {})
    monkeypatch.setattr(
        import_service,
        "diff_codelists",
        lambda *_a, **_k: {
            "all": [other],
            "new": [],
            "updated": [],
            "unchanged": [other],
        },
    )
    monkeypatch.setattr(codelist_service, "staging_session", null_session)
    monkeypatch.setattr(
        codelist_review_repository,
        "clear_review",
        lambda _session, package_date, codelist_id: seen.update(
            package_date=package_date, codelist_id=codelist_id
        ),
    )

    review = codelist_service.clear_review(date(2025, 9, 26), "C1")

    assert seen == {"package_date": "2025-09-26", "codelist_id": "C1"}
    assert review == CodelistReview()


# --- get_term_detail: memberships and findings, repositories stubbed --------------


def pair_finding(status, codelist_id, term_id="T1"):
    return Inconsistency(
        uid=f"finding-{codelist_id}-{term_id}-{status}",
        effective_date=date(2025, 9, 26),
        type=InconsistencyType.SPONSOR_TERM_DUPLICATE,
        entity_type=EntityType.CODELIST,
        concept_id=codelist_id,
        related_concept_id=term_id,
        status=status,
        detected_at=datetime(2026, 9, 14, 9, 0),
    )


def term_detail_with(
    monkeypatch,
    *,
    staged=None,
    head=None,
    existing=(),
    findings=(),
    codelists=("C1", "C2", "C3"),
    reviews=None,
    usage=None,
    usage_calls=None,
):
    def get_term_usage(uids):
        if usage_calls is not None:
            usage_calls.append(uids)
        return {"T1": list(usage or [])}

    monkeypatch.setattr(import_service, "require_release", lambda *_a, **_k: {})
    monkeypatch.setattr(
        review_snapshot_service,
        "codelist_rows",
        lambda *_a, **_k: [
            {"codelist_id": c, "name": f"Name {c}", "submission_value": f"SV{c}"}
            for c in codelists
        ],
    )
    monkeypatch.setattr(release_repository, "get_term", lambda *_a, **_k: staged)
    monkeypatch.setattr(
        mdr_repository,
        "get_term_heads",
        lambda *_a, **_k: {"T1": head} if head else {},
    )
    monkeypatch.setattr(
        mdr_repository, "get_open_memberships_of_terms", lambda _ids: set(existing)
    )
    monkeypatch.setattr(inconsistency_service, "to_model", lambda record: record)
    monkeypatch.setattr(
        inconsistency_repository,
        "get_findings_for_term",
        lambda *_a, **_k: list(findings),
    )
    monkeypatch.setattr(
        inconsistency_repository,
        "get_finding_counts_by_codelist",
        lambda *_a, **_k: {},
    )
    monkeypatch.setattr(
        codelist_review_repository, "get_reviews", lambda *_a, **_k: reviews or {}
    )
    monkeypatch.setattr(mdr_repository, "get_term_usage", get_term_usage)
    monkeypatch.setattr(
        changelog_repository, "get_changelog_for_term", lambda *_a, **_k: []
    )
    monkeypatch.setattr(codelist_service, "staging_session", null_session)
    return codelist_service.get_term_detail(date(2025, 9, 26), "T1")


def staged_term(memberships, preferred_term="Term"):
    return {
        "props": {"preferredTerm": preferred_term, "definition": "D", "synonyms": []},
        "memberships": [
            {"codelist_id": c, "submission_value": sv} for c, sv in memberships
        ],
    }


def mdr_head(preferred_term="Term"):
    return {
        "props": {
            "preferred_term": preferred_term,
            "definition": "D",
            "concept_id": "T1",
            "synonyms": [],
        },
        "version": "1.0",
    }


def test_a_term_in_neither_release_nor_mdr_raises_not_found(monkeypatch):
    with pytest.raises(NotFoundException, match="T1"):
        term_detail_with(monkeypatch)


def test_a_term_new_to_mdr_reports_every_attribute_as_a_change(monkeypatch):
    detail = term_detail_with(monkeypatch, staged=staged_term([("C1", "A")]))

    assert detail.change_status == ChangeStatus.NEW
    assert {c.field for c in detail.changes} == {"preferred_term", "definition"}
    assert [c.membership_change for c in detail.codelists] == [MembershipChange.ADDED]


def test_an_unchanged_term_reports_no_changes_but_every_attribute(monkeypatch):
    detail = term_detail_with(
        monkeypatch,
        staged=staged_term([("C1", "A")]),
        head=mdr_head(),
        existing=[("C1", "T1", "A")],
    )

    assert detail.change_status == ChangeStatus.UNCHANGED
    assert detail.changes == []
    assert [a.field for a in detail.attributes] == [
        "preferred_term",
        "definition",
        "synonyms",
    ]
    assert detail.codelists[0].membership_change is None
    assert detail.codelists[0].previous_submission_value is None


def test_each_codelist_reports_whether_the_release_opens_or_closes_it(monkeypatch):
    detail = term_detail_with(
        monkeypatch,
        staged=staged_term([("C1", "A"), ("C2", "NEW")], preferred_term="Renamed"),
        head=mdr_head(),
        existing=[("C1", "T1", "A"), ("C2", "T1", "OLD"), ("C3", "T1", "GONE")],
    )

    assert detail.change_status == ChangeStatus.UPDATED
    by_id = {c.codelist_id: c for c in detail.codelists}
    assert list(by_id) == ["C1", "C2", "C3"]
    assert by_id["C1"].membership_change is None
    assert by_id["C2"].membership_change is None
    assert by_id["C2"].term_submission_value == "NEW"
    assert by_id["C2"].previous_submission_value == "OLD"
    assert by_id["C3"].membership_change == MembershipChange.ENDED
    assert by_id["C3"].term_submission_value == "GONE"
    assert by_id["C1"].name == "Name C1"
    assert by_id["C1"].submission_value == "SVC1"


def test_an_mdr_membership_outside_the_release_is_left_out(monkeypatch):
    detail = term_detail_with(
        monkeypatch,
        staged=staged_term([("C1", "A")]),
        head=mdr_head(),
        existing=[("C1", "T1", "A"), ("OTHER", "T1", "X")],
    )

    assert [c.codelist_id for c in detail.codelists] == ["C1"]


def test_a_term_the_release_no_longer_ships_is_read_from_mdr(monkeypatch):
    detail = term_detail_with(
        monkeypatch,
        head=mdr_head(preferred_term="Old name"),
        existing=[("C1", "T1", "A")],
    )

    assert detail.change_status is None
    assert detail.preferred_term == "Old name"
    assert detail.changes == []
    assert detail.codelists[0].membership_change == MembershipChange.ENDED


def test_term_findings_stay_top_level_and_pair_findings_go_to_their_codelist(
    monkeypatch,
):
    term_wide = finding(InconsistencyStatus.OPEN)
    in_c2 = pair_finding(InconsistencyStatus.IGNORED, "C2")
    detail = term_detail_with(
        monkeypatch,
        staged=staged_term([("C1", "A"), ("C2", "B")]),
        head=mdr_head(),
        existing=[("C1", "T1", "A"), ("C2", "T1", "B")],
        findings=[term_wide, in_c2],
    )

    assert detail.findings == [term_wide]
    by_id = {c.codelist_id: c for c in detail.codelists}
    assert by_id["C1"].findings == []
    assert by_id["C2"].findings == [in_c2]


def test_a_codelist_only_a_finding_names_is_listed_without_a_membership(
    monkeypatch,
):
    detail = term_detail_with(
        monkeypatch,
        staged=staged_term([("C1", "A")]),
        head=mdr_head(),
        existing=[("C1", "T1", "A")],
        findings=[pair_finding(InconsistencyStatus.RESOLVED, "C2")],
    )

    by_id = {c.codelist_id: c for c in detail.codelists}
    assert by_id["C2"].membership_change is None
    assert by_id["C2"].term_submission_value is None
    assert len(by_id["C2"].findings) == 1


def test_a_terms_review_is_inherited_from_the_codelists_holding_it(monkeypatch):
    marked = reviewed("jdoe", datetime(2026, 9, 14, 9, 0))
    detail = term_detail_with(
        monkeypatch,
        staged=staged_term([("C1", "A")]),
        head=mdr_head(),
        existing=[("C1", "T1", "A"), ("C2", "T1", "B")],
        reviews={"C1": marked, "C2": marked},
    )

    assert detail.review.status == ReviewStatus.REVIEWED
    assert detail.codelists[0].review.status == ReviewStatus.REVIEWED


def test_an_open_finding_makes_an_inherited_review_stale(monkeypatch):
    marked = reviewed("jdoe", datetime(2026, 9, 14, 9, 0))
    detail = term_detail_with(
        monkeypatch,
        staged=staged_term([("C1", "A")]),
        head=mdr_head(),
        existing=[("C1", "T1", "A")],
        findings=[finding(InconsistencyStatus.OPEN)],
        reviews={"C1": marked},
    )

    assert detail.review.status == ReviewStatus.REVIEWED_STALE


def usage_entry(count, labels=("ActivityItem",)):
    return {
        "through": "selected in context",
        "relationship": "HAS_CT_TERM",
        "consumer_labels": list(labels),
        "count": count,
    }


def test_a_terms_usage_is_listed_by_kind_most_used_first(monkeypatch):
    detail = term_detail_with(
        monkeypatch,
        staged=staged_term([("C1", "A")]),
        head=mdr_head(),
        existing=[("C1", "T1", "A")],
        usage=[usage_entry(2), usage_entry(5, labels=("StudyActivity",))],
    )

    assert [(u.consumer_labels, u.count) for u in detail.usage] == [
        (["StudyActivity"], 5),
        (["ActivityItem"], 2),
    ]


def test_a_new_term_is_not_looked_up_for_usage(monkeypatch):
    calls: list[Any] = []
    detail = term_detail_with(
        monkeypatch,
        staged=staged_term([("C1", "A")]),
        usage=[usage_entry(1)],
        usage_calls=calls,
    )

    assert not calls
    assert detail.usage == []


def test_a_dropped_terms_usage_is_still_read(monkeypatch):
    detail = term_detail_with(
        monkeypatch,
        head=mdr_head(),
        existing=[("C1", "T1", "A")],
        usage=[usage_entry(3)],
    )

    assert [u.count for u in detail.usage] == [3]
