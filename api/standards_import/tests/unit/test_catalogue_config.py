"""The two catalogue-level admin settings kept beside the pecking order: which
catalogues are mandatory before analysis, and which usually ship a workbook."""

import contextlib

import pytest

from common.exceptions import ValidationException
from standards_import.models.inconsistencies import (
    ExpectedWorkbooksInput,
    MandatoryCataloguesInput,
)
from standards_import.repositories import rules_repository
from standards_import.services import inconsistency_service


def null_session():
    return contextlib.nullcontext(None)


CATALOGUES = [
    {
        "catalogue_name": "SDTM CT",
        "priority": 0,
        "mandatory": False,
        "expects_workbook": False,
    },
    {
        "catalogue_name": "SEND CT",
        "priority": 1,
        "mandatory": False,
        "expects_workbook": False,
    },
]


def test_set_mandatory_catalogues_refuses_a_name_not_in_the_pecking_order(monkeypatch):
    """A flag on an unknown catalogue would silently match nothing."""

    monkeypatch.setattr(inconsistency_service, "staging_session", null_session)
    monkeypatch.setattr(rules_repository, "ensure_seed_data", lambda _: None)
    monkeypatch.setattr(
        rules_repository, "get_catalogue_priority", lambda _: CATALOGUES
    )

    with pytest.raises(ValidationException, match=r"Unknown catalogues.*QRS CT"):
        inconsistency_service.set_mandatory_catalogues(
            MandatoryCataloguesInput(catalogues=["SDTM CT", "QRS CT"])
        )


def test_set_mandatory_catalogues_accepts_known_names(monkeypatch):
    monkeypatch.setattr(inconsistency_service, "staging_session", null_session)
    monkeypatch.setattr(rules_repository, "ensure_seed_data", lambda _: None)
    monkeypatch.setattr(
        rules_repository, "get_catalogue_priority", lambda _: CATALOGUES
    )

    seen = {}

    def fake_set_mandatory(_session, names):
        seen["names"] = names
        return [
            {**row, "mandatory": row["catalogue_name"] in names} for row in CATALOGUES
        ]

    monkeypatch.setattr(
        rules_repository, "set_mandatory_catalogues", fake_set_mandatory
    )

    result = inconsistency_service.set_mandatory_catalogues(
        MandatoryCataloguesInput(catalogues=["SDTM CT"])
    )

    assert seen["names"] == ["SDTM CT"]
    assert [entry.mandatory for entry in result] == [True, False]


def test_set_expected_workbooks_refuses_a_name_not_in_the_pecking_order(monkeypatch):
    monkeypatch.setattr(inconsistency_service, "staging_session", null_session)
    monkeypatch.setattr(rules_repository, "ensure_seed_data", lambda _: None)
    monkeypatch.setattr(
        rules_repository, "get_catalogue_priority", lambda _: CATALOGUES
    )

    with pytest.raises(ValidationException, match=r"Unknown catalogues.*ADAM CT"):
        inconsistency_service.set_expected_workbook_catalogues(
            ExpectedWorkbooksInput(catalogues=["ADAM CT"])
        )


def test_set_expected_workbooks_accepts_known_names(monkeypatch):
    monkeypatch.setattr(inconsistency_service, "staging_session", null_session)
    monkeypatch.setattr(rules_repository, "ensure_seed_data", lambda _: None)
    monkeypatch.setattr(
        rules_repository, "get_catalogue_priority", lambda _: CATALOGUES
    )

    seen = {}

    def fake_set_expected(_session, names):
        seen["names"] = names
        return [
            {**row, "expects_workbook": row["catalogue_name"] in names}
            for row in CATALOGUES
        ]

    monkeypatch.setattr(
        rules_repository, "set_expected_workbook_catalogues", fake_set_expected
    )

    result = inconsistency_service.set_expected_workbook_catalogues(
        ExpectedWorkbooksInput(catalogues=["SEND CT"])
    )

    assert seen["names"] == ["SEND CT"]
    assert [entry.expects_workbook for entry in result] == [False, True]


def test_get_catalogue_priority_carries_the_two_flags(monkeypatch):
    """One read model now serves the ordering, mandatory, and workbook settings."""

    monkeypatch.setattr(inconsistency_service, "staging_session", null_session)
    monkeypatch.setattr(rules_repository, "ensure_seed_data", lambda _: None)
    monkeypatch.setattr(
        rules_repository,
        "get_catalogue_priority",
        lambda _: [
            {
                "catalogue_name": "SDTM CT",
                "priority": 0,
                "mandatory": True,
                "expects_workbook": True,
            }
        ],
    )

    [entry] = inconsistency_service.get_catalogue_priority()

    assert entry.mandatory is True
    assert entry.expects_workbook is True
