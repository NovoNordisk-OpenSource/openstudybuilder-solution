# pylint: disable=redefined-outer-name,unused-argument
"""One codelist or term across the last releases of a catalogue."""

from contextlib import contextmanager
from datetime import date

import pytest

from common.exceptions import NotFoundException
from standards_import.models.packages import ConceptType
from standards_import.repositories import release_repository
from standards_import.services import concept_history_service

NAMES = [f"SDTM CT 2025-0{month}-01" for month in (1, 2, 3)]


def _chain(rows):
    return lambda _session, _package_name, _concept_id, _releases: rows


@pytest.fixture(autouse=True)
def fake_session(monkeypatch):
    @contextmanager
    def session():
        yield None

    monkeypatch.setattr(concept_history_service, "staging_session", session)


def _release(index, **extra):
    return {
        "package_name": NAMES[index],
        "effective_date": NAMES[index].split()[-1],
        "has_prior": index > 0,
        **extra,
    }


def _membership(codelist_id, value, preferred_term="Years", submission_value="YRS"):
    return {
        "codelist_id": codelist_id,
        "codelist_submission_value": value,
        "term": {
            "conceptId": "T1",
            "preferredTerm": preferred_term,
            "definition": "years",
            "synonyms": ["b", "a"],
            "submissionValue": submission_value,
        },
    }


def _history(monkeypatch, rows, concept_type=ConceptType.TERM):
    attribute = (
        "get_term_history"
        if concept_type == ConceptType.TERM
        else "get_codelist_history"
    )
    monkeypatch.setattr(release_repository, attribute, _chain(rows))
    last_date = date.fromisoformat(rows[-1]["effective_date"] if rows else "2025-03-01")
    return concept_history_service.get_concept_history(
        "SDTM CT", last_date, concept_type, "T1"
    )


def test_a_term_edit_shows_in_the_releases_around_it(monkeypatch):
    history = _history(
        monkeypatch,
        [
            _release(0, memberships=[_membership("CL1", "ONE", "Year")]),
            _release(1, memberships=[_membership("CL1", "ONE")]),
            _release(2, memberships=[_membership("CL1", "ONE")]),
        ],
    )

    preferred = next(a for a in history.attributes if a.field == "preferredTerm")
    assert preferred.values == ["Year", "Years", "Years"]
    assert [r.is_current for r in history.releases] == [False, False, True]
    assert history.releases[0].is_earliest_staged is True
    assert history.releases[1].is_earliest_staged is False


def test_synonyms_are_compared_without_regard_to_order(monkeypatch):
    history = _history(
        monkeypatch,
        [_release(0, memberships=[_membership("CL1", "ONE")])] * 1
        + [_release(1, memberships=[_membership("CL1", "ONE")])],
    )

    synonyms = next(a for a in history.attributes if a.field == "synonyms")
    assert synonyms.values == [["a", "b"], ["a", "b"]]


def test_codelists_a_term_entered_and_left_are_listed_but_not_the_ones_it_stayed_in(
    monkeypatch,
):
    history = _history(
        monkeypatch,
        [
            _release(
                0, memberships=[_membership("CL1", "ONE"), _membership("CL2", "TWO")]
            ),
            _release(
                1, memberships=[_membership("CL2", "TWO"), _membership("CL3", "THREE")]
            ),
            _release(
                2, memberships=[_membership("CL2", "TWO"), _membership("CL3", "THREE")]
            ),
        ],
    )

    first, second, third = history.membership_changes
    assert first.entered == [] and first.left == []
    assert [c.concept_id for c in second.entered] == ["CL3"]
    assert second.entered[0].submission_value == "THREE"
    assert [c.concept_id for c in second.left] == ["CL1"]
    assert third.entered == [] and third.left == []


def test_a_release_without_the_term_is_kept_with_null_values(monkeypatch):
    history = _history(
        monkeypatch,
        [
            _release(0, memberships=[]),
            _release(1, memberships=[_membership("CL1", "ONE")]),
            _release(2, memberships=[_membership("CL1", "ONE")]),
        ],
    )

    assert [r.present for r in history.releases] == [False, True, True]
    preferred = next(a for a in history.attributes if a.field == "preferredTerm")
    assert preferred.values == [None, "Years", "Years"]
    assert [c.concept_id for c in history.membership_changes[1].entered] == ["CL1"]


def test_a_term_in_codelists_with_different_submission_values_joins_them(monkeypatch):
    history = _history(
        monkeypatch,
        [
            _release(
                0,
                memberships=[
                    _membership("CL1", "ONE", submission_value="A"),
                    _membership("CL2", "TWO", submission_value="B"),
                ],
            ),
            _release(1, memberships=[_membership("CL1", "ONE", submission_value="A")]),
        ],
    )

    submission = next(a for a in history.attributes if a.field == "submissionValue")
    assert submission.values == ["A, B", "A"]


def test_a_codelist_history_has_no_membership_changes(monkeypatch):
    codelist = {
        "conceptId": "T1",
        "name": "Unit",
        "preferredTerm": "Unit",
        "submissionValue": "UNIT",
        "definition": "d",
        "extensible": "true",
        "synonyms": [],
    }
    history = _history(
        monkeypatch,
        [_release(0, codelists=[codelist]), _release(1, codelists=[])],
        ConceptType.CODELIST,
    )

    assert history.membership_changes is None
    extensible = next(a for a in history.attributes if a.field == "extensible")
    assert extensible.values == [True, None]


def test_a_concept_in_none_of_the_releases_is_not_found(monkeypatch):
    with pytest.raises(NotFoundException):
        _history(
            monkeypatch, [_release(0, memberships=[]), _release(2, memberships=[])]
        )


def test_an_unstaged_catalogue_is_not_found(monkeypatch):
    with pytest.raises(NotFoundException):
        _history(monkeypatch, [])
