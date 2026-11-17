"""What may still change about a release, once it has reached MDR."""

import contextlib
from datetime import date

import pytest

from common.exceptions import ValidationException
from standards_import.models.packages import EffectiveDateStatus
from standards_import.repositories import (
    analysis_repository,
    mdr_repository,
    pairing_repository,
    rules_repository,
    staging_repository,
)
from standards_import.services import pairing_service, staging_service
from standards_import.services.analysis_service import (
    guard_mandatory_catalogues_present,
)
from standards_import.services.staging_service import guard_release_accepts_uploads


def release(status):
    return {"effective_date": "2025-09-26", "status": status.value}


@pytest.fixture(autouse=True)
def empty_mdr(monkeypatch):
    monkeypatch.setattr(
        mdr_repository, "get_head_effective_date", lambda excluding=None: None
    )


@pytest.mark.parametrize(
    "status", [EffectiveDateStatus.IMPORTING, EffectiveDateStatus.IMPORTED]
)
def test_a_release_already_in_mdr_refuses_new_files(monkeypatch, status):
    """Any upload resets the release, which would clear the status analysis checks."""

    monkeypatch.setattr(
        staging_repository, "find_effective_date", lambda *_: release(status)
    )

    with pytest.raises(ValidationException, match="can no longer be changed"):
        guard_release_accepts_uploads(None, "2025-09-26")


@pytest.mark.parametrize(
    "status", [EffectiveDateStatus.ANALYZING, EffectiveDateStatus.ASSESSING]
)
def test_a_release_with_another_step_running_refuses_new_files(monkeypatch, status):
    """Uploading mid-run would change the files a concurrent job is reading."""

    monkeypatch.setattr(
        staging_repository, "find_effective_date", lambda *_: release(status)
    )

    with pytest.raises(ValidationException, match="Another step is already running"):
        guard_release_accepts_uploads(None, "2025-09-26")


@pytest.mark.parametrize(
    "status",
    [
        EffectiveDateStatus.FILES_STAGED,
        EffectiveDateStatus.ANALYZED,
        EffectiveDateStatus.BLOCKED,
    ],
)
def test_a_release_still_in_staging_accepts_new_files(monkeypatch, status):
    monkeypatch.setattr(
        staging_repository, "find_effective_date", lambda *_: release(status)
    )

    guard_release_accepts_uploads(None, "2025-09-26")


def test_an_unknown_release_accepts_files(monkeypatch):
    """The first upload for a date is what creates the release."""

    monkeypatch.setattr(staging_repository, "find_effective_date", lambda *_: None)

    guard_release_accepts_uploads(None, "2099-01-01")


def test_replacing_the_pairings_invalidates_the_analysis(monkeypatch):
    """Otherwise an ANALYZED release imports while ignoring the workbook just sent."""

    reset_for = []
    monkeypatch.setattr(
        staging_service, "staging_session", lambda: contextlib.nullcontext(None)
    )
    monkeypatch.setattr(
        staging_repository,
        "find_effective_date",
        lambda *_: release(EffectiveDateStatus.ANALYZED),
    )
    monkeypatch.setattr(
        staging_repository,
        "reset_release_for_reanalysis",
        lambda _session, package_date: reset_for.append(package_date),
    )
    monkeypatch.setattr(pairing_repository, "replace_pairings", lambda *_: 12)
    monkeypatch.setattr(
        pairing_service,
        "parse_pairing_workbook",
        lambda _payload: {"pairings": [{"a": 1}], "sheets": ["Sheet1"], "skipped": []},
    )

    staging_service.stage_pairing_file(date(2025, 9, 26), "SDTM_paired_view.xlsx", b"x")

    assert reset_for == ["2025-09-26"]


def test_pairings_are_refused_once_the_release_is_imported(monkeypatch):
    monkeypatch.setattr(
        staging_service, "staging_session", lambda: contextlib.nullcontext(None)
    )
    monkeypatch.setattr(
        staging_repository,
        "find_effective_date",
        lambda *_: release(EffectiveDateStatus.IMPORTED),
    )
    monkeypatch.setattr(
        pairing_service,
        "parse_pairing_workbook",
        lambda _payload: {"pairings": [], "sheets": [], "skipped": []},
    )

    with pytest.raises(ValidationException, match="can no longer be changed"):
        staging_service.stage_pairing_file(
            date(2025, 9, 26), "SDTM_paired_view.xlsx", b"x"
        )


def test_analysis_refuses_a_release_missing_a_mandatory_catalogue(monkeypatch):
    monkeypatch.setattr(
        rules_repository, "get_mandatory_catalogues", lambda _: ["SDTM CT", "SEND CT"]
    )
    monkeypatch.setattr(
        analysis_repository, "get_catalogues", lambda *_: ["SDTM CT 2025-09-26"]
    )

    with pytest.raises(
        ValidationException, match=r"missing mandatory catalogues.*SEND CT"
    ):
        guard_mandatory_catalogues_present(None, "2025-09-26")


def test_analysis_accepts_a_release_holding_every_mandatory_catalogue(monkeypatch):
    monkeypatch.setattr(
        rules_repository, "get_mandatory_catalogues", lambda _: ["SDTM CT", "SEND CT"]
    )
    monkeypatch.setattr(
        analysis_repository,
        "get_catalogues",
        lambda *_: ["SDTM CT 2025-09-26", "SEND CT 2025-09-26", "ADAM CT 2025-09-26"],
    )

    guard_mandatory_catalogues_present(None, "2025-09-26")


def test_analysis_skips_the_check_when_nothing_is_configured_as_mandatory(monkeypatch):
    """An organisation that has cleared the mandatory list is not blocked by it.

    Also checks the staged catalogues are never even read in that case — there is
    nothing to compare them against.
    """

    def fail_if_called(*_args):
        raise AssertionError(
            "staged catalogues should not be read when nothing is mandatory"
        )

    monkeypatch.setattr(rules_repository, "get_mandatory_catalogues", lambda _: [])
    monkeypatch.setattr(analysis_repository, "get_catalogues", fail_if_called)

    guard_mandatory_catalogues_present(None, "2025-09-26")


@pytest.mark.parametrize(
    "head, accepted",
    [("2025-06-27", True), ("2025-09-26", False), ("2025-12-19", False)],
)
def test_a_release_not_newer_than_the_mdr_head_refuses_files(
    monkeypatch, head, accepted
):
    """Import only appends to the head, so such a release could never be imported."""

    monkeypatch.setattr(staging_repository, "find_effective_date", lambda *_: None)
    monkeypatch.setattr(
        mdr_repository, "get_head_effective_date", lambda excluding=None: head
    )

    if accepted:
        guard_release_accepts_uploads(None, "2025-09-26")
    else:
        with pytest.raises(ValidationException, match="already holds"):
            guard_release_accepts_uploads(None, "2025-09-26")
