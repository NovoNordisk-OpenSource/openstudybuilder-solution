"""One codelist or term across the last releases of a catalogue, read from the graph.

The unit tests feed the service rows by hand. What only a database settles is the two
queries underneath: that the chain of `HAS_PRIOR_VERSION` links is followed oldest to
newest, that a release without the concept still comes back, and that a term is found
under every codelist holding it.
"""

import pytest

from common.exceptions import NotFoundException
from standards_import.tests.integration.packages import codelist, package, term

DATES = ("2025-01-01", "2025-04-01", "2025-07-01")


def releases(*per_release):
    """One package per date, each chained to the one before, from lists of codelists."""

    return [
        package(
            "SDTM CT",
            DATES[index],
            codelists,
            prior_effective_date=DATES[index - 1] if index else None,
        )
        for index, codelists in enumerate(per_release)
    ]


def values(history, field):
    return next(a for a in history.attributes if a.field == field).values


@pytest.fixture
def staged(release):
    release.upload(
        *releases(
            # The term is not in the first release at all.
            [codelist("CL1", "One", "ONE", []), codelist("CL2", "Two", "TWO", [])],
            [
                codelist("CL1", "One", "ONE", [term("T1", "TERM", "Old name")]),
                codelist("CL2", "Two", "TWO", [term("T1", "TERM", "Old name")]),
            ],
            [
                codelist("CL1", "One", "ONE", [term("T1", "TERM", "New name")]),
                codelist("CL2", "Two", "TWO", [], definition="A codelist, reworded."),
                codelist("CL3", "Three", "THREE", [term("T1", "TERM", "New name")]),
            ],
        )
    )
    return release


def test_a_term_is_followed_oldest_to_newest_through_its_edit(staged):
    history = staged.history("SDTM CT", DATES[2], "term", "T1")

    assert [str(r.effective_date) for r in history.releases] == list(DATES)
    assert [r.present for r in history.releases] == [False, True, True]
    assert values(history, "preferredTerm") == [None, "Old name", "New name"]
    assert history.releases[0].is_earliest_staged is True
    assert history.releases[2].is_current is True


def test_the_codelists_a_term_entered_and_left_are_listed_but_not_those_it_stayed_in(
    staged,
):
    history = staged.history("SDTM CT", DATES[2], "term", "T1")

    first, second, third = history.membership_changes
    assert first.entered == [] and first.left == []
    assert [c.concept_id for c in second.entered] == ["CL1", "CL2"]
    assert second.left == []
    assert [c.concept_id for c in third.entered] == ["CL3"]
    assert third.entered[0].submission_value == "THREE"
    assert [c.concept_id for c in third.left] == ["CL2"]


def test_a_codelist_shows_its_own_edits(staged):
    history = staged.history("SDTM CT", DATES[2], "codelist", "CL2")

    assert values(history, "definition") == [
        "A codelist.",
        "A codelist.",
        "A codelist, reworded.",
    ]
    assert history.membership_changes is None


def test_the_history_stops_at_the_requested_number_of_releases(staged):
    history = staged.history("SDTM CT", DATES[2], "term", "T1", releases=2)

    assert [str(r.effective_date) for r in history.releases] == list(DATES[1:])
    assert history.releases[0].is_earliest_staged is False


def test_a_history_ending_at_an_earlier_release_leaves_the_later_ones_out(staged):
    history = staged.history("SDTM CT", DATES[1], "term", "T1")

    assert [str(r.effective_date) for r in history.releases] == list(DATES[:2])
    assert values(history, "preferredTerm") == [None, "Old name"]


def test_a_concept_in_none_of_the_releases_is_not_found(staged):
    with pytest.raises(NotFoundException):
        staged.history("SDTM CT", DATES[2], "term", "C99999")


def test_a_release_that_is_not_staged_is_not_found(staged):
    with pytest.raises(NotFoundException):
        staged.history("SDTM CT", "2030-01-01", "term", "T1")
