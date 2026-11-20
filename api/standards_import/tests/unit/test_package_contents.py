# pylint: disable=redefined-outer-name
"""What each package is recorded as having contained."""

from typing import Any

import pytest

from standards_import.repositories import mdr_repository, release_repository
from standards_import.services import import_service

SDTM = "SDTM CT 2025-09-26"
SEND = "SEND CT 2025-09-26"

# Both catalogues ship codelist C66781 and both define term C29848 — but only SDTM puts
# that term in that codelist. This is the real 2025-09-26 case.
RAW = [
    {"package_name": SDTM, "codelist_id": "C66781", "term_id": "C29848"},
    {"package_name": SDTM, "codelist_id": "C66781", "term_id": "C25301"},
    {"package_name": SEND, "codelist_id": "C66781", "term_id": "C25301"},
    {"package_name": SEND, "codelist_id": "C66770", "term_id": "C29848"},
    # Shipped by SDTM, but a DROP_TERM_FROM_CODELIST resolution took it out of the
    # release, so it is absent from the grouped memberships below.
    {"package_name": SDTM, "codelist_id": "C66781", "term_id": "C48262"},
]
GROUPED = [
    {"codelist_id": "C66781", "term_id": "C29848", "submission_value": "YEARS"},
    {"codelist_id": "C66781", "term_id": "C25301", "submission_value": "DAYS"},
    {"codelist_id": "C66770", "term_id": "C29848", "submission_value": "YEARS"},
]


@pytest.fixture
def written(monkeypatch):
    rows: dict[str, list[dict[str, Any]]] = {"codelists": [], "terms": []}
    monkeypatch.setattr(
        mdr_repository, "create_package_codelists", rows["codelists"].extend
    )
    monkeypatch.setattr(mdr_repository, "create_package_terms", rows["terms"].extend)
    monkeypatch.setattr(
        release_repository, "count_memberships", lambda *_: len(GROUPED)
    )
    monkeypatch.setattr(
        release_repository, "get_memberships", lambda *_a, **_k: GROUPED
    )
    monkeypatch.setattr(
        release_repository, "count_raw_memberships", lambda *_: len(RAW)
    )
    monkeypatch.setattr(
        release_repository, "get_raw_memberships", lambda *_a, **_k: RAW
    )
    delta = {
        "codelists": {
            "all": [
                {"concept_id": "C66781", "packages": [SDTM, SEND]},
                {"concept_id": "C66770", "packages": [SEND]},
            ]
        },
        "terms": {
            "all": [
                {"concept_id": "C29848", "packages": [SDTM, SEND]},
                {"concept_id": "C25301", "packages": [SDTM, SEND]},
            ]
        },
    }
    import_service.write_package_contents(None, "2025-09-26", delta)
    return rows


def membership(rows):
    return {(r["package_codelist_uid"], r["term_uid"]) for r in rows}


def test_a_package_claims_only_the_memberships_it_shipped(written):
    """SEND defines C66781 and defines C29848 — but not C29848 *in* C66781."""

    assert (
        "SEND__CT__2025-09-26_C66781",
        "C29848",
    ) not in membership(written["terms"])


def test_the_package_that_did_ship_it_still_claims_it(written):
    assert ("SDTM__CT__2025-09-26_C66781", "C29848") in membership(written["terms"])


def test_every_shipped_membership_is_recorded(written):
    assert membership(written["terms"]) == {
        ("SDTM__CT__2025-09-26_C66781", "C29848"),
        ("SDTM__CT__2025-09-26_C66781", "C25301"),
        ("SEND__CT__2025-09-26_C66781", "C25301"),
        ("SEND__CT__2025-09-26_C66770", "C29848"),
    }


def test_the_settled_submission_value_is_used_not_a_per_package_one(written):
    """MDR stores one submission value per membership: the one resolutions settled."""

    values = {(r["uid"], r["submission_value"]) for r in written["terms"]}

    assert ("SDTM__CT__2025-09-26_C29848", "YEARS") in values
    assert ("SEND__CT__2025-09-26_C25301", "DAYS") in values


def test_a_term_dropped_by_a_resolution_is_in_no_package(written):
    """`DROP_TERM_FROM_CODELIST` removes it from the release, however it was shipped.

    C48262 appears in SDTM's raw rows but not in the grouped memberships.
    """

    assert "C48262" not in {r["term_uid"] for r in written["terms"]}


def test_uids_follow_the_bootstrap_scheme(written):
    assert {r["uid"] for r in written["codelists"]} == {
        "SDTM__CT__2025-09-26_C66781",
        "SEND__CT__2025-09-26_C66781",
        "SEND__CT__2025-09-26_C66770",
    }
