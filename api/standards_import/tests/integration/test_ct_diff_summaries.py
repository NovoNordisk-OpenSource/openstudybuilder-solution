"""Counts per severity band for every catalogue of a release, in one call.

The unit tests already pin the arithmetic against stubbed snapshots. What only a database
settles is what the summary reads from one: that the staged-file list, the prior-version
chain and the new changelog *count* query line up on the same catalogue, and that the
counts are the same diff the full endpoint lists rather than a second, drifting one.

`changelog_available` is the part worth a database most. The full diff derives it from
the entries it already read; a summary reads nothing but a count, through its own Cypher,
and that query has to scope to the catalogue exactly as the read does — a release usually
has a sheet for one catalogue and not the others.
"""

from standards_import.tests.integration.packages import codelist, package, term
from standards_import.tests.integration.test_ct_diff_changelog import (
    NEW,
    OLD,
    entry,
    lbtest,
    two_releases,
)


def sendct(effective_date, terms, prior=None):
    """A second catalogue of the same release, sharing none of the first's concepts."""

    return package(
        "SEND CT",
        effective_date,
        [
            codelist(
                "CL9",
                "Species",
                "SPECIES",
                [term(code, f"SV{code}") for code in terms],
            )
        ],
        prior_effective_date=prior,
    )


def summary_for(summaries, catalogue):
    return next(s for s in summaries if s.catalogue == catalogue)


def test_a_summary_counts_what_the_full_diff_of_the_same_catalogue_lists(release):
    release.upload(
        *two_releases(
            ("C001", "C002"),
            ("C001", "C003"),
            old_definition="Old definition.",
            new_definition="New definition.",
        )
    )

    report = release.diff("SDTM CT", NEW)
    summary = summary_for(release.diff_summaries(NEW), "SDTM CT")

    assert summary.previous_available is True
    assert summary.previous_package_name == f"SDTM CT {OLD}"
    assert str(summary.previous_effective_date) == OLD
    assert {band.level: band.count for band in summary.bands} == {
        band.level: len(band.changes) for band in report.bands
    }
    assert summary.total_changes == sum(len(band.changes) for band in report.bands)


def test_a_first_release_is_reported_with_no_predecessor_rather_than_omitted(release):
    release.upload(lbtest(NEW, ("C001",)))

    summaries = release.diff_summaries(NEW)

    assert [s.catalogue for s in summaries] == ["SDTM CT"]
    assert summaries[0].previous_available is False
    assert summaries[0].bands == []
    assert summaries[0].total_changes == 0


def test_every_catalogue_of_the_release_gets_a_summary(release):
    release.upload(
        *two_releases(("C001",), ("C001", "C002")),
        sendct(OLD, ("C900",)),
        sendct(NEW, ("C900", "C901"), prior=OLD),
    )

    summaries = release.diff_summaries(NEW)

    assert sorted(s.catalogue for s in summaries) == ["SDTM CT", "SEND CT"]
    assert all(s.previous_available for s in summaries)
    assert all(s.total_changes for s in summaries)


def test_a_staged_changelog_is_reported_only_for_the_catalogue_it_covers(release):
    """The count query has to scope to the catalogue the way the full read does: a
    release normally has a sheet for some of its catalogues and not the rest."""

    release.upload(
        *two_releases(("C001",), ("C001", "C002")),
        sendct(OLD, ("C900",)),
        sendct(NEW, ("C900", "C901"), prior=OLD),
    )
    release.load_changelog(
        NEW,
        "SDTM CT",
        [entry(nci_code="C002", change_type="ADD", summary="Add new term")],
    )

    summaries = release.diff_summaries(NEW)

    assert summary_for(summaries, "SDTM CT").changelog_available is True
    assert summary_for(summaries, "SEND CT").changelog_available is False


def test_a_release_without_any_changelog_says_so(release):
    release.upload(*two_releases(("C001",), ("C001", "C002")))

    summary = summary_for(release.diff_summaries(NEW), "SDTM CT")

    assert summary.changelog_available is False


def test_the_predecessors_changelog_does_not_count_for_this_release(release):
    """Same scoping the full diff has: a sheet for release D-1 describes the step
    before the one being summarised."""

    release.upload(*two_releases(("C001",), ("C001", "C002")))
    release.load_changelog(OLD, "SDTM CT", [entry(nci_code="CL1")])

    summary = summary_for(release.diff_summaries(NEW), "SDTM CT")

    assert summary.changelog_available is False
