"""The admin-configured mandatory-catalogues gate on analysis, against a real database.

Unlike the rest of the suite, this restores the real default (SDTM/SEND/ADaM all
mandatory) — `conftest.py`'s `databases` fixture clears it so the other integration
tests, which build small two-catalogue releases unrelated to this gate, are not blocked
by a missing third catalogue that has nothing to do with what they are testing.
"""

import pytest

from common.exceptions import ValidationException
from standards_import.models.inconsistencies import MandatoryCataloguesInput
from standards_import.repositories import rules_repository
from standards_import.services import inconsistency_service
from standards_import.tests.integration.packages import codelist, package, term

DATE = "2025-09-26"

SDTM = package(
    "SDTM CT",
    DATE,
    [codelist("C1", "Test Codelist", "TESTCL", terms=[term("T1", "A")])],
)
SEND = package(
    "SEND CT",
    DATE,
    [codelist("C1", "Test Codelist", "TESTCL", terms=[term("T1", "A")])],
)
ADAM = package(
    "ADAM CT",
    DATE,
    [codelist("C1", "Test Codelist", "TESTCL", terms=[term("T1", "A")])],
)


def restore_the_real_default(monkeypatch):
    monkeypatch.setattr(
        rules_repository,
        "DEFAULT_MANDATORY_CATALOGUES",
        {"SDTM CT", "SEND CT", "ADAM CT"},
    )


def test_analysis_refuses_a_release_missing_a_default_mandatory_catalogue(
    monkeypatch, release
):
    restore_the_real_default(monkeypatch)
    release.upload(SDTM, SEND)

    with pytest.raises(ValidationException, match="ADAM CT"):
        release.analyse(DATE)


def test_analysis_accepts_a_release_holding_every_mandatory_catalogue(
    monkeypatch, release
):
    restore_the_real_default(monkeypatch)
    release.upload(SDTM, SEND, ADAM)

    summary = release.analyse(DATE)

    assert summary.status.value in ("ANALYZED", "BLOCKED")


def test_clearing_the_mandatory_list_lifts_the_gate(monkeypatch, release):
    """An organisation may narrow the default down to nothing, and analysis follows."""

    restore_the_real_default(monkeypatch)
    release.upload(SDTM)

    inconsistency_service.set_mandatory_catalogues(
        MandatoryCataloguesInput(catalogues=[])
    )

    summary = release.analyse(DATE)

    assert summary.status.value in ("ANALYZED", "BLOCKED")
