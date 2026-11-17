"""The whole workflow against real databases: upload, analyse, resolve, import.

This is the path that only ever ran by hand before. Everything here goes through the
service layer, so the repositories' Cypher is what is actually under test.
"""

from neomodel import db as neomodel_db

from standards_import.models.packages import EffectiveDateStatus
from standards_import.tests.integration.packages import codelist, package, term

DATE = "2025-09-26"

# Both catalogues carry codelist C1, but they disagree twice over: on its definition,
# and on which terms it holds. SEND is missing T2 and adds T3.
SDTM = package(
    "SDTM CT",
    DATE,
    [
        codelist(
            "C1",
            "Test Codelist",
            "TESTCL",
            definition="From SDTM.",
            terms=[term("T1", "A"), term("T2", "B")],
        )
    ],
)
SEND = package(
    "SEND CT",
    DATE,
    [
        codelist(
            "C1",
            "Test Codelist",
            "TESTCL",
            definition="From SEND.",
            terms=[term("T1", "A"), term("T3", "C")],
        )
    ],
)


def mdr(query, **params):
    rows, _ = neomodel_db.cypher_query(query, params)
    return rows


def test_uploading_two_catalogues_stages_both(release):
    staged = release.upload(SDTM, SEND)

    assert [file.package_name for file in staged] == [
        "SDTM CT 2025-09-26",
        "SEND CT 2025-09-26",
    ]
    assert all(file.replaced_previous_upload is False for file in staged)


def test_analysis_raises_the_disagreements_and_blocks_the_release(release):
    release.upload(SDTM, SEND)

    summary = release.analyse(DATE)

    assert summary.grouped_codelist_count == 1
    assert summary.grouped_term_count == 3  # the union: T1, T2, T3
    assert summary.status is EffectiveDateStatus.BLOCKED

    kinds = {finding.type.value for finding in release.findings(DATE)}
    assert "INCONSISTENT_TERM_SETS" in kinds
    assert "CONFLICTING_VALUES" in kinds


def test_the_catalogue_pecking_order_settles_the_definition_by_itself(release):
    release.upload(SDTM, SEND)
    release.analyse(DATE)

    settled = [
        finding
        for finding in release.findings(DATE)
        if finding.type.value == "CONFLICTING_VALUES"
    ]

    assert len(settled) == 1
    assert settled[0].status.value == "AUTO_RESOLVED"
    assert settled[0].resolution.resolved_value == "From SDTM."


def test_only_the_membership_disagreement_is_left_for_a_person(release):
    release.upload(SDTM, SEND)

    summary = release.analyse(DATE)

    open_items = release.findings(DATE, status="OPEN")
    assert summary.open_inconsistency_count == 1
    assert [item.type.value for item in open_items] == ["INCONSISTENT_TERM_SETS"]


def test_settling_it_and_re_analysing_unblocks_the_release(release):
    release.upload(SDTM, SEND)
    release.analyse(DATE)
    open_item = release.findings(DATE, status="OPEN")[0]

    release.resolve(open_item.uid, strategy="IGNORE")
    summary = release.analyse(DATE)

    assert summary.status is EffectiveDateStatus.ANALYZED
    assert summary.open_inconsistency_count == 0


def test_a_decision_survives_re_analysis(release):
    release.upload(SDTM, SEND)
    release.analyse(DATE)
    open_item = release.findings(DATE, status="OPEN")[0]
    release.resolve(open_item.uid, strategy="IGNORE")

    release.analyse(DATE)

    same = [f for f in release.findings(DATE) if f.uid == open_item.uid]
    assert len(same) == 1
    assert same[0].status.value == "IGNORED"
