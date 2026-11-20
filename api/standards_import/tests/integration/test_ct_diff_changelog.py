"""CDISC's own rationale, attached to the changes a package diff found.

The unit tests cover the matching rules against a hand-built index. What only a database
can settle is the query underneath them — that `get_changelog_for_catalogue` finds each
entry through the `ABOUT` relationship `RESOLVE_TARGET` actually created, reports the
subject's label and identity the way the matcher expects, and names the codelist a term
sits under rather than an arbitrary one of the codelists that share it.

The three fallback tiers matter most here. An entry about something that left the release
has no node of its own to point at, and those are exactly the changes in the top severity
bands — the ones a reviewer most wants a reason for.
"""

import pytest

from standards_import.tests.integration.packages import codelist, package, term

OLD = "2025-06-27"
NEW = "2025-09-26"


def entry(
    nci_code="C001",
    short_name="LBTEST",
    change_type="UPDATE",
    summary="Update CDISC Definition",
    uid=None,
    request_codes=None,
    instructions=None,
):
    """One row as the parser hands it over: no term type, no before-and-after."""

    return {
        "uid": uid or f"uid-{nci_code}-{short_name}-{summary}",
        "change_type": change_type,
        "change_summary": summary,
        "request_codes": request_codes if request_codes is not None else ["CDISC-1"],
        "implementation_instructions": instructions,
        "nci_code": nci_code,
        "codelist_short_name": short_name,
        "codelist_long_name": "Laboratory Test Name",
    }


def lbtest(effective_date, terms, definition="A lab test.", codelists=(), prior=None):
    return package(
        "SDTM CT",
        effective_date,
        [
            codelist(
                "CL1",
                "Laboratory Test Name",
                "LBTEST",
                [term(code, f"SV{code}") for code in terms],
                definition=definition,
            ),
            *codelists,
        ],
        prior_effective_date=prior,
    )


def two_releases(
    old_terms,
    new_terms,
    old_definition="A lab test.",
    new_definition="A lab test.",
    old_codelists=(),
    new_codelists=(),
):
    """The prior release and the one superseding it, chained the way CDISC chains them."""

    return (
        lbtest(OLD, old_terms, definition=old_definition, codelists=old_codelists),
        lbtest(
            NEW,
            new_terms,
            definition=new_definition,
            codelists=new_codelists,
            prior=OLD,
        ),
    )


def changes_in(report, level):
    band = next((b for b in report.bands if b.level == level), None)
    return band.changes if band else []


def only_changelog(changes):
    return [code for change in changes for code in change.get("changelog", []) or []]


# --- the plain case ----------------------------------------------------------------


def test_a_changed_property_carries_the_entry_about_it(release):
    release.upload(
        *two_releases(
            ("C001",),
            ("C001",),
            old_definition="Old definition.",
            new_definition="New definition.",
        )
    )
    release.load_changelog(
        NEW, "SDTM CT", [entry(nci_code="CL1", summary="Update CDISC Definition")]
    )

    report = release.diff("SDTM CT", NEW)

    assert report.changelog_available is True
    change = next(c for c in changes_in(report, 11) if c["field"] == "definition")
    assert [e.request_codes for e in change["changelog"]] == [["CDISC-1"]]


def test_a_release_with_no_changelog_diffs_exactly_as_before(release):
    release.upload(
        *two_releases(
            ("C001",),
            ("C001",),
            old_definition="Old definition.",
            new_definition="New definition.",
        )
    )

    report = release.diff("SDTM CT", NEW)

    assert report.changelog_available is False
    assert changes_in(report, 11)
    assert all(
        "changelog" not in change for band in report.bands for change in band.changes
    )


def test_include_changelog_off_returns_the_same_bands_unannotated(release):
    release.upload(
        *two_releases(
            ("C001",),
            ("C001",),
            old_definition="Old definition.",
            new_definition="New definition.",
        )
    )
    release.load_changelog(NEW, "SDTM CT", [entry(nci_code="CL1")])

    annotated = release.diff("SDTM CT", NEW)
    plain = release.diff("SDTM CT", NEW, include_changelog=False)

    assert plain.changelog_available is False
    assert plain.counts == annotated.counts
    assert all(
        "changelog" not in change for band in plain.bands for change in band.changes
    )


# --- the three fallback tiers ------------------------------------------------------


def test_a_term_removed_from_a_surviving_codelist_is_annotated(release):
    """Tier two: the entry attaches to the codelist, keeping the term's `nci_code`."""

    release.upload(*two_releases(("C001", "C002"), ("C001",)))
    release.load_changelog(
        NEW,
        "SDTM CT",
        [
            entry(
                nci_code="C002",
                change_type="REMOVE",
                summary="Remove term from codelist",
            )
        ],
    )

    report = release.diff("SDTM CT", NEW)

    removed = changes_in(report, 2) + changes_in(report, 3)
    assert removed, "the removed term should be banded"
    assert only_changelog(removed), "and should carry CDISC's reason for removing it"


def test_a_retired_codelist_is_annotated_through_the_catalogue(release):
    """Tier three: nothing under the codelist was staged, so the entry sits on the
    catalogue and is found again by its submission value."""

    gone = codelist("CL2", "Frequency", "FREQ", [term("C900", "SV900")])
    release.upload(*two_releases(("C001",), ("C001",), old_codelists=(gone,)))
    release.load_changelog(
        NEW,
        "SDTM CT",
        [
            entry(
                nci_code="CL2",
                short_name="FREQ",
                change_type="REMOVE",
                summary="Remove codelist",
            )
        ],
    )

    report = release.diff("SDTM CT", NEW)

    retired = [c for c in changes_in(report, 1) if c["codelist"]["conceptId"] == "CL2"]
    assert retired, "the retired codelist should be banded"
    assert only_changelog(retired), "and should carry CDISC's reason for retiring it"


def test_an_added_term_is_annotated(release):
    release.upload(*two_releases(("C001",), ("C001", "C002")))
    release.load_changelog(
        NEW,
        "SDTM CT",
        [
            entry(
                nci_code="C002",
                change_type="ADD",
                summary="Add new term to existing codelist",
            )
        ],
    )

    report = release.diff("SDTM CT", NEW)

    added = [change for level in (5, 7, 10) for change in changes_in(report, level)]
    assert only_changelog(added)


# --- scoping ----------------------------------------------------------------------


def test_the_predecessors_changelog_is_not_used(release):
    """A changelog for release D describes D-1 -> D. The prior release's own sheet
    describes the step before the one being diffed, and must not leak into it."""

    release.upload(
        *two_releases(
            ("C001",),
            ("C001",),
            old_definition="Old definition.",
            new_definition="New definition.",
        )
    )
    release.load_changelog(
        OLD, "SDTM CT", [entry(nci_code="CL1", summary="Update CDISC Definition")]
    )

    report = release.diff("SDTM CT", NEW)

    assert report.changelog_available is False
    assert all(
        "changelog" not in change for band in report.bands for change in band.changes
    )


def test_an_entry_about_a_change_cdisc_did_not_mention_is_left_alone(release):
    release.upload(
        *two_releases(
            ("C001",),
            ("C001",),
            old_definition="Old definition.",
            new_definition="New definition.",
        )
    )
    release.load_changelog(
        NEW,
        "SDTM CT",
        [
            entry(
                nci_code="C404", short_name="NOSUCH", summary="Update CDISC Definition"
            )
        ],
    )

    report = release.diff("SDTM CT", NEW)

    assert report.changelog_available is True
    assert all(
        "changelog" not in change for band in report.bands for change in band.changes
    )


def test_a_term_shared_by_two_codelists_is_annotated_under_the_right_one(release):
    """`RawTerm` nodes are not unique by `conceptId`, so the query has to report the
    parent codelist or a membership change gets annotated from the wrong one."""

    other_old = codelist("CL2", "Frequency", "FREQ", [term("C001", "SV001")])
    other_new = codelist("CL2", "Frequency", "FREQ", [term("C001", "SV001")])
    release.upload(
        *two_releases(
            ("C001",),
            ("C001", "C002"),
            old_codelists=(other_old,),
            new_codelists=(other_new,),
        )
    )
    release.load_changelog(
        NEW,
        "SDTM CT",
        [
            entry(
                nci_code="C002",
                change_type="ADD",
                summary="Add new term to existing codelist",
            )
        ],
    )

    report = release.diff("SDTM CT", NEW)

    annotated = [
        change
        for band in report.bands
        for change in band.changes
        if change.get("changelog")
    ]
    assert annotated
    assert all(
        change.get("key", ["CL1"])[0] == "CL1"
        for change in annotated
        if change["kind"].startswith("membership")
    )


def test_a_first_release_has_no_diff_to_annotate(release):
    release.upload(lbtest(NEW, ("C001",)))
    release.load_changelog(NEW, "SDTM CT", [entry(nci_code="CL1")])

    report = release.diff("SDTM CT", NEW)

    assert report.previous_available is False
    assert report.changelog_available is False
    assert not report.bands


@pytest.mark.parametrize("instructions", [None, "Use LBTESTCD instead."])
def test_implementation_instructions_ride_along_where_present(release, instructions):
    """Unlike the Markdown report, which leaves them out to keep its table narrow."""

    release.upload(
        *two_releases(
            ("C001",),
            ("C001",),
            old_definition="Old definition.",
            new_definition="New definition.",
        )
    )
    release.load_changelog(
        NEW,
        "SDTM CT",
        [entry(nci_code="CL1", instructions=instructions)],
    )

    report = release.diff("SDTM CT", NEW)

    change = next(c for c in changes_in(report, 11) if c["field"] == "definition")
    assert [e.implementation_instructions for e in change["changelog"]] == [
        instructions
    ]
