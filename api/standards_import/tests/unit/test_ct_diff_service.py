# pylint: disable=redefined-outer-name,unused-argument
"""Diffing one staged catalogue against the previous release of that catalogue."""

from contextlib import contextmanager
from datetime import date

import pytest

from common.exceptions import NotFoundException
from standards_import.repositories import (
    changelog_repository,
    release_repository,
    staging_repository,
)
from standards_import.services import ct_diff_service

OLD_NAME = "SDTM CT 2025-06-27"
NEW_NAME = "SDTM CT 2025-09-26"

OLD_SNAPSHOT = {
    "name": OLD_NAME,
    "codelists": [
        {
            "conceptId": "C66781",
            "name": "Unit",
            "definition": "old def",
            "preferredTerm": "Unit",
            "submissionValue": "UNIT",
            "extensible": "true",
            "synonyms": ["UNIT"],
        },
        {
            "conceptId": "C66770",
            "name": "Frequency",
            "definition": "freq def",
            "preferredTerm": "Frequency",
            "submissionValue": "FREQ",
            "extensible": "false",
            "synonyms": [],
        },
    ],
    "terms": [
        {
            "codelist_id": "C66781",
            "term": {
                "conceptId": "C29848",
                "definition": "years",
                "preferredTerm": "Years",
                "synonyms": [],
                "submissionValue": "YEARS",
            },
        },
        {
            "codelist_id": "C66770",
            "term": {
                "conceptId": "C25301",
                "definition": "daily",
                "preferredTerm": "Daily",
                "synonyms": [],
                "submissionValue": "DAILY",
            },
        },
    ],
}

NEW_SNAPSHOT = {
    "name": NEW_NAME,
    "codelists": [
        {
            "conceptId": "C66781",
            "name": "Unit",
            "definition": "new def",
            "preferredTerm": "Unit",
            "submissionValue": "UNIT",
            "extensible": "true",
            "synonyms": ["UNIT"],
        },
        {
            "conceptId": "C66770",
            "name": "Frequency",
            "definition": "freq def",
            "preferredTerm": "Frequency",
            "submissionValue": "FREQ",
            "extensible": "false",
            "synonyms": [],
        },
    ],
    "terms": [
        {
            "codelist_id": "C66781",
            "term": {
                "conceptId": "C29848",
                "definition": "years",
                "preferredTerm": "Years",
                "synonyms": [],
                "submissionValue": "YEARS",
            },
        },
        {
            "codelist_id": "C66781",
            "term": {
                "conceptId": "C99999",
                "definition": "months",
                "preferredTerm": "Months",
                "synonyms": [],
                "submissionValue": "MONTHS",
            },
        },
    ],
}


def _no_changelog(monkeypatch, records=None):
    """Stub the changelog read, which every diff now makes.

    Returns nothing by default: a release without a terminology-changes sheet is the
    normal case, and the banding tests must keep passing without one.
    """

    monkeypatch.setattr(
        changelog_repository,
        "get_changelog_for_catalogue",
        lambda _session, _package_date, _package_name: list(records or ()),
    )


def _stub_snapshots(monkeypatch):
    by_name = {OLD_NAME: OLD_SNAPSHOT, NEW_NAME: NEW_SNAPSHOT}
    monkeypatch.setattr(
        release_repository,
        "get_raw_catalogue_snapshot",
        lambda _session, package_name: by_name.get(package_name),
    )
    monkeypatch.setattr(
        release_repository,
        "find_prior_catalogue",
        lambda _session, package_name: (
            {"package_name": OLD_NAME, "effective_date": "2025-06-27"}
            if package_name == NEW_NAME
            else None
        ),
    )

    @contextmanager
    def fake_session():
        yield None

    monkeypatch.setattr(ct_diff_service, "staging_session", fake_session)


@pytest.fixture
def snapshots(monkeypatch):
    _no_changelog(monkeypatch)
    _stub_snapshots(monkeypatch)


def test_diffs_against_the_prior_release(snapshots):
    report = ct_diff_service.get_package_diff("SDTM CT", "2025-09-26")

    assert report.previous_available is True
    assert report.previous_package_name == OLD_NAME
    assert str(report.previous_effective_date) == "2025-06-27"


def test_previous_release_resolves_without_needing_the_snapshots(snapshots):
    """Unlike the full diff, this must not touch `get_raw_catalogue_snapshot`."""

    info = ct_diff_service.get_previous_release("SDTM CT", "2025-09-26")

    assert info.previous_available is True
    assert info.previous_package_name == OLD_NAME
    assert str(info.previous_effective_date) == "2025-06-27"


def test_previous_release_is_unavailable_for_a_first_release(snapshots):
    info = ct_diff_service.get_previous_release("SDTM CT", "2025-06-27")

    assert info.previous_available is False
    assert info.previous_package_name is None


def test_a_term_removed_from_the_catalogue_lands_in_its_band(snapshots):
    report = ct_diff_service.get_package_diff("SDTM CT", "2025-09-26")

    band = next(b for b in report.bands if b.level == 2)
    assert any(c["term"]["conceptId"] == "C25301" for c in band.changes)


def test_a_term_added_to_an_extensible_codelist_lands_in_its_band(snapshots):
    report = ct_diff_service.get_package_diff("SDTM CT", "2025-09-26")

    band = next(b for b in report.bands if b.level == 5)
    assert any(c["key"] == ["C66781", "C99999"] for c in band.changes)


def test_a_codelist_description_update_lands_in_its_band(snapshots):
    report = ct_diff_service.get_package_diff("SDTM CT", "2025-09-26")

    band = next(b for b in report.bands if b.level == 11)
    assert any(c["field"] == "definition" for c in band.changes)


def _entry(**overrides):
    entry = {
        "uid": "e1",
        "change_type": "UPDATE",
        "change_summary": "Update CDISC Definition",
        "request_codes": ["CDISC-6139"],
        "implementation_instructions": None,
        "nci_code": "C66781",
        "codelist_short_name": "UNIT",
        "codelist_long_name": "Unit",
        "catalogue": "SDTM CT",
        "source_file": "sdtmct-2025-09-26.xls",
    }
    entry.update(overrides)
    return entry


def test_a_changed_codelist_carries_the_changelog_entry_about_it(monkeypatch):
    _no_changelog(
        monkeypatch,
        [
            {
                "entry": _entry(),
                "target_labels": ["RawCodelist"],
                "target_concept_id": "C66781",
                "target_submission_value": "UNIT",
                "parent_codelist_id": None,
            }
        ],
    )
    _stub_snapshots(monkeypatch)

    report = ct_diff_service.get_package_diff("SDTM CT", "2025-09-26")

    assert report.changelog_available is True
    band = next(b for b in report.bands if b.level == 11)
    change = next(c for c in band.changes if c["field"] == "definition")
    assert [e.request_codes for e in change["changelog"]] == [["CDISC-6139"]]


def test_a_diff_without_a_changelog_says_so_and_annotates_nothing(snapshots):
    report = ct_diff_service.get_package_diff("SDTM CT", "2025-09-26")

    assert report.changelog_available is False
    assert all(
        "changelog" not in change for band in report.bands for change in band.changes
    )


def test_an_unmatched_change_is_left_alone_rather_than_given_an_empty_list(monkeypatch):
    """Enrichment only ever annotates - a change CDISC did not mention is untouched."""

    _no_changelog(
        monkeypatch,
        [
            {
                "entry": _entry(nci_code="C99999999", codelist_short_name="NOSUCH"),
                "target_labels": ["RawCatalogue"],
                "target_concept_id": None,
                "target_submission_value": None,
                "parent_codelist_id": None,
            }
        ],
    )
    _stub_snapshots(monkeypatch)

    report = ct_diff_service.get_package_diff("SDTM CT", "2025-09-26")

    assert report.changelog_available is True
    assert all(
        "changelog" not in change for band in report.bands for change in band.changes
    )


def test_include_changelog_off_skips_the_read_entirely(monkeypatch):
    def explode(*_args, **_kwargs):
        raise AssertionError("the changelog must not be read when it was not asked for")

    monkeypatch.setattr(changelog_repository, "get_changelog_for_catalogue", explode)
    _stub_snapshots(monkeypatch)

    report = ct_diff_service.get_package_diff(
        "SDTM CT", "2025-09-26", include_changelog=False
    )

    assert report.changelog_available is False
    assert report.bands


def test_the_first_staged_release_has_no_previous(monkeypatch):
    monkeypatch.setattr(
        release_repository,
        "get_raw_catalogue_snapshot",
        lambda _session, _package_name: OLD_SNAPSHOT,
    )
    monkeypatch.setattr(
        release_repository, "find_prior_catalogue", lambda _session, _package_name: None
    )

    @contextmanager
    def fake_session():
        yield None

    monkeypatch.setattr(ct_diff_service, "staging_session", fake_session)

    report = ct_diff_service.get_package_diff("SDTM CT", "2025-06-27")

    assert report.previous_available is False
    assert not report.bands


def _stub_staged_files(monkeypatch, catalogues=("SDTM CT",)):
    monkeypatch.setattr(
        staging_repository,
        "get_staged_files",
        lambda _session, effective_date=None: [
            {
                "catalogue": catalogue,
                "package_name": f"{catalogue} {effective_date}",
            }
            for catalogue in catalogues
        ],
    )


def _stub_changelog_count(monkeypatch, entries):
    monkeypatch.setattr(
        changelog_repository,
        "count_changelog_for_catalogue",
        lambda _session, _package_date, _package_name: entries,
    )


def test_a_summary_counts_exactly_what_the_full_diff_lists(monkeypatch):
    """The point of the summary is to be the same diff, so the two must not drift."""

    _no_changelog(monkeypatch)
    _stub_snapshots(monkeypatch)
    _stub_staged_files(monkeypatch)
    _stub_changelog_count(monkeypatch, 0)

    report = ct_diff_service.get_package_diff("SDTM CT", "2025-09-26")
    summary = ct_diff_service.get_diff_summaries(date(2025, 9, 26))[0]

    assert summary.catalogue == "SDTM CT"
    assert summary.previous_available is True
    assert summary.previous_package_name == OLD_NAME
    assert {band.level: band.count for band in summary.bands} == {
        band.level: len(band.changes) for band in report.bands
    }
    assert summary.total_changes == sum(len(band.changes) for band in report.bands)
    assert [band.label for band in summary.bands] == [
        band.label for band in report.bands
    ]


def test_a_summary_reports_a_catalogue_with_no_predecessor_rather_than_omitting_it(
    monkeypatch,
):
    _no_changelog(monkeypatch)
    _stub_snapshots(monkeypatch)
    _stub_staged_files(monkeypatch)
    _stub_changelog_count(monkeypatch, 0)

    # 2025-06-27 is the oldest snapshot stubbed, so it has no prior version.
    summaries = ct_diff_service.get_diff_summaries(date(2025, 6, 27))

    assert [summary.catalogue for summary in summaries] == ["SDTM CT"]
    assert summaries[0].previous_available is False
    assert summaries[0].bands == []
    assert summaries[0].total_changes == 0


def test_a_summary_says_whether_a_changelog_is_staged_without_reading_it(monkeypatch):
    """Counting is enough here - the summary annotates nothing, so the entries are
    never wanted."""

    def explode(*_args, **_kwargs):
        raise AssertionError("a summary must not read the changelog entries themselves")

    monkeypatch.setattr(changelog_repository, "get_changelog_for_catalogue", explode)
    _stub_snapshots(monkeypatch)
    _stub_staged_files(monkeypatch)
    _stub_changelog_count(monkeypatch, 3)

    summary = ct_diff_service.get_diff_summaries(date(2025, 9, 26))[0]

    assert summary.changelog_available is True


def test_a_summary_covers_every_staged_catalogue_of_the_release(monkeypatch):
    _no_changelog(monkeypatch)
    _stub_snapshots(monkeypatch)
    _stub_staged_files(monkeypatch, catalogues=("SDTM CT", "SEND CT"))
    _stub_changelog_count(monkeypatch, 0)

    summaries = ct_diff_service.get_diff_summaries(date(2025, 9, 26))

    assert [summary.catalogue for summary in summaries] == ["SDTM CT", "SEND CT"]
    # Only SDTM CT is stubbed with snapshots; the other is still reported.
    assert summaries[1].previous_available is False


def test_an_unstaged_catalogue_is_not_found(monkeypatch):
    monkeypatch.setattr(
        release_repository,
        "get_raw_catalogue_snapshot",
        lambda _session, _package_name: None,
    )

    @contextmanager
    def fake_session():
        yield None

    monkeypatch.setattr(ct_diff_service, "staging_session", fake_session)

    with pytest.raises(NotFoundException):
        ct_diff_service.get_package_diff("SDTM CT", "2025-09-26")


def test_a_term_change_names_the_term_by_its_submission_value(snapshots):
    report = ct_diff_service.get_package_diff("SDTM CT", "2025-09-26")

    removed = next(b for b in report.bands if b.level == 2).changes
    assert next(c for c in removed if c["term"]["conceptId"] == "C25301")[
        "term_submission_values"
    ] == ["DAILY"]


def test_a_membership_change_names_the_term_and_the_codelist_by_submission_value(
    snapshots,
):
    report = ct_diff_service.get_package_diff("SDTM CT", "2025-09-26")

    added = next(b for b in report.bands if b.level == 5).changes
    change = next(c for c in added if c["key"] == ["C66781", "C99999"])
    assert change["term_submission_values"] == ["MONTHS"]
    assert change["term_name"] == "Months"
    assert change["codelist_submission_values"] == {"C66781": "UNIT"}


def test_a_removed_term_is_one_change_listing_the_codelists_it_left(snapshots):
    report = ct_diff_service.get_package_diff("SDTM CT", "2025-09-26")

    band = next(b for b in report.bands if b.level == 2)
    assert [c["kind"] for c in band.changes] == ["term_removed"]
    change = band.changes[0]
    assert change["term"]["conceptId"] == "C25301"
    assert change["codelists"] == ["C66770"]
    assert change["codelist_submission_values"] == {"C66770": "FREQ"}


def _snapshot(memberships):
    return {
        "codelists": {
            cid: {"conceptId": cid, "submissionValue": value}
            for cid, value in (("CL1", "ONE"), ("CL2", "TWO"), ("CL3", "THREE"))
        },
        "terms": {},
        "memberships": memberships,
    }


def test_a_term_leaving_one_codelist_reports_the_ones_it_stays_in():
    old = _snapshot({("CL1", "T1"): "A", ("CL2", "T1"): "A"})
    new = _snapshot({("CL2", "T1"): "A"})
    change = {"kind": "membership_removed", "key": ("CL1", "T1")}

    ct_diff_service._add_submission_values({3: [change]}, old, new)

    assert change["stays_in"] == ["CL2"]
    assert change["codelist_submission_values"] == {"CL1": "ONE", "CL2": "TWO"}


def test_a_term_entering_a_codelist_reports_the_ones_it_already_was_in():
    old = _snapshot({("CL1", "T1"): "A"})
    new = _snapshot({("CL1", "T1"): "A", ("CL3", "T1"): "A"})
    change = {"kind": "membership_added", "key": ("CL3", "T1")}

    ct_diff_service._add_submission_values({5: [change]}, old, new)

    assert change["stays_in"] == ["CL1"]


def test_a_moved_term_reports_the_codelists_it_stays_in():
    old = _snapshot({("CL1", "T1"): "A", ("CL2", "T1"): "A"})
    new = _snapshot({("CL2", "T1"): "A", ("CL3", "T1"): "A"})
    change = {
        "kind": "term_moved",
        "move": {"conceptId": "T1", "left": ["CL1"], "entered": ["CL3"]},
    }

    ct_diff_service._add_submission_values({6: [change]}, old, new)

    assert change["stays_in"] == ["CL2"]
