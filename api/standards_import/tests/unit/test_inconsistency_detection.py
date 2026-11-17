import pytest

from standards_import.models.inconsistencies import (
    EntityType,
    InconsistencyType,
    build_inconsistency_uid,
)
from standards_import.services.analysis_service import (
    CODELIST_PROPERTIES,
    build_candidates,
    build_property_rows,
    choose_baseline,
    compare_concept,
    compare_term_sets,
    is_quoted,
    merge_candidates,
    strip_unwanted_quotes,
)

SDTM = {"name": "SDTM CT 2025-09-26"}
ADAM = {"name": "ADAM CT 2025-09-26"}
SEND = {"name": "SEND CT 2025-09-26"}
PRIORITY = ["SDTM CT", "ADAM CT", "SEND CT"]


@pytest.mark.parametrize(
    "value,expected",
    [
        ('"quoted"', True),
        ("plain", False),
        ('"opens only', False),
        (['"first', 'last"'], True),
        (["plain", "values"], False),
        ([], False),
        (None, False),
        (42, False),
        ([1, 2], False),
    ],
)
def test_is_quoted(value, expected):
    assert is_quoted(value) is expected


def test_strip_unwanted_quotes_unescapes_doubled_quotes():
    assert strip_unwanted_quotes('"a ""quoted"" word"') == 'a "quoted" word'


def test_build_candidates_groups_catalogues_by_the_value_they_gave():
    candidates = build_candidates(
        [{"definition": "First"}, {"definition": "Second"}, {"definition": "First"}],
        [SDTM, ADAM, SEND],
        "definition",
    )

    assert candidates == [
        {"value": "First", "catalogues": ["SDTM CT 2025-09-26", "SEND CT 2025-09-26"]},
        {"value": "Second", "catalogues": ["ADAM CT 2025-09-26"]},
    ]


def test_merge_candidates_keeps_first_seen_order():
    merged = merge_candidates(
        [
            {"value": "B", "catalogues": ["one"]},
            {"value": "A", "catalogues": ["two"]},
            {"value": "B", "catalogues": ["three"]},
        ]
    )

    assert [c["value"] for c in merged] == ["B", "A"]
    assert merged[0]["catalogues"] == ["one", "three"]


def test_compare_concept_reports_nothing_when_catalogues_agree():
    findings, baseline = compare_concept(
        "2025-09-26",
        EntityType.CODELIST,
        "C1",
        [{"definition": "Same"}, {"definition": "Same"}],
        [SDTM, ADAM],
        ["definition"],
        PRIORITY,
    )

    assert not findings
    assert baseline == {"definition": "Same"}


def test_compare_concept_reports_a_disagreement():
    findings, _ = compare_concept(
        "2025-09-26",
        EntityType.TERM,
        "C25150",
        [{"preferredTerm": "Age"}, {"preferredTerm": "Different"}],
        [SDTM, ADAM],
        ["preferredTerm"],
        PRIORITY,
    )

    assert len(findings) == 1
    finding = findings[0]
    assert finding["type"] == InconsistencyType.CONFLICTING_VALUES.value
    assert finding["property"] == "preferredTerm"
    assert [c["value"] for c in finding["candidates"]] == ["Age", "Different"]


def test_compare_concept_covers_every_property_it_compares():
    """A codelist differing only in `name` or `extensible` must still be reported.

    The original staging script compared these when deciding a codelist was
    inconsistent but omitted them when building the detail, so such a codelist was
    recorded neither as consistent nor as a finding, and ended up with no properties.
    """
    findings, _ = compare_concept(
        "2025-09-26",
        EntityType.CODELIST,
        "C66742",
        [
            {"name": "One name", "extensible": "true"},
            {"name": "Another name", "extensible": "false"},
        ],
        [SDTM, ADAM],
        CODELIST_PROPERTIES,
        PRIORITY,
    )

    assert {f["property"] for f in findings} == {"name", "extensible"}


def test_quotes_are_reported_even_when_only_one_catalogue_has_them():
    """The original only ever inspected the first catalogue's values."""

    findings, _ = compare_concept(
        "2025-09-26",
        EntityType.CODELIST,
        "C1",
        [{"definition": "plain"}, {"definition": '"plain"'}],
        [SDTM, ADAM],
        ["definition"],
        PRIORITY,
    )

    kinds = {f["type"] for f in findings}
    assert InconsistencyType.UNWANTED_QUOTES.value in kinds
    assert InconsistencyType.CONFLICTING_VALUES.value in kinds


def test_quotes_agreed_across_catalogues_are_reported_without_a_conflict():
    findings, _ = compare_concept(
        "2025-09-26",
        EntityType.CODELIST,
        "C1",
        [{"definition": '"quoted"'}, {"definition": '"quoted"'}],
        [SDTM, ADAM],
        ["definition"],
        PRIORITY,
    )

    assert [f["type"] for f in findings] == [InconsistencyType.UNWANTED_QUOTES.value]


def test_findings_get_a_deterministic_uid():
    """Re-analysis must land on the node a reviewer already decided about."""

    first, _ = compare_concept(
        "2025-09-26",
        EntityType.CODELIST,
        "C1",
        [{"definition": "A"}, {"definition": "B"}],
        [SDTM, ADAM],
        ["definition"],
        PRIORITY,
    )
    second, _ = compare_concept(
        "2025-09-26",
        EntityType.CODELIST,
        "C1",
        [{"definition": "A"}, {"definition": "B"}],
        [SDTM, ADAM],
        ["definition"],
        PRIORITY,
    )

    assert first[0]["uid"] == second[0]["uid"]
    assert first[0]["uid"] == build_inconsistency_uid(
        "2025-09-26",
        EntityType.CODELIST,
        "C1",
        InconsistencyType.CONFLICTING_VALUES,
        property_name="definition",
    )


def test_fingerprint_changes_when_the_competing_values_change():
    unchanged, _ = compare_concept(
        "2025-09-26",
        EntityType.CODELIST,
        "C1",
        [{"definition": "A"}, {"definition": "B"}],
        [SDTM, ADAM],
        ["definition"],
        PRIORITY,
    )
    changed, _ = compare_concept(
        "2025-09-26",
        EntityType.CODELIST,
        "C1",
        [{"definition": "A"}, {"definition": "C"}],
        [SDTM, ADAM],
        ["definition"],
        PRIORITY,
    )

    assert unchanged[0]["uid"] == changed[0]["uid"]
    assert unchanged[0]["fingerprint"] != changed[0]["fingerprint"]


def test_baseline_prefers_the_most_authoritative_catalogue():
    _, baseline = compare_concept(
        "2025-09-26",
        EntityType.CODELIST,
        "C1",
        [{"definition": "from adam"}, {"definition": "from sdtm"}],
        [ADAM, SDTM],
        ["definition"],
        PRIORITY,
    )

    assert baseline["definition"] == "from sdtm"


def test_choose_baseline_falls_back_to_the_first_candidate():
    candidates = [
        {"value": "X", "catalogues": ["UNRANKED CT 2025-09-26"]},
        {"value": "Y", "catalogues": ["OTHER CT 2025-09-26"]},
    ]

    assert choose_baseline(candidates, PRIORITY) == "X"


def test_compare_term_sets_is_quiet_when_catalogues_agree():
    assert (
        compare_term_sets(
            "2025-09-26",
            "C1",
            [{"C1": "A", "C2": "B"}, {"C1": "A", "C2": "B"}],
            [SDTM, ADAM],
        )
        is None
    )


def test_compare_term_sets_ignores_quoting_of_submission_values():
    assert (
        compare_term_sets(
            "2025-09-26", "C1", [{"C1": '"A"'}, {"C1": "A"}], [SDTM, ADAM]
        )
        is None
    )


def test_compare_term_sets_reports_the_terms_that_differ():
    finding = compare_term_sets(
        "2025-09-26", "C1", [{"C1": "A"}, {"C1": "A", "C2": "B"}], [SDTM, ADAM]
    )

    assert finding is not None
    assert finding["type"] == InconsistencyType.INCONSISTENT_TERM_SETS.value
    values = {tuple(c["value"]) for c in finding["candidates"]}
    assert () in values or ("C2:B",) in values


def test_compare_term_sets_needs_more_than_one_catalogue():
    assert compare_term_sets("2025-09-26", "C1", [{"C1": "A"}], [SDTM]) is None


def test_every_concept_is_staged_even_when_its_values_are_disputed():
    """Staging is a working area; open items hold up promotion, not staging.

    An undecided concept keeps the pecking order's pick until somebody decides
    otherwise, so nothing downstream finds a concept with no values at all.
    """
    rows = build_property_rows(
        "2025-09-26",
        EntityType.CODELIST,
        {"C1": {"definition": "settled"}, "C2": {"definition": "still disputed"}},
        overrides={},
    )

    assert {row["codelist_cid"] for row in rows} == {"C1", "C2"}


def test_a_settled_value_replaces_the_baseline():
    rows = build_property_rows(
        "2025-09-26",
        EntityType.TERM,
        {"C1": {"definition": "baseline", "preferredTerm": "kept"}},
        overrides={("TERM", "C1", "definition"): "decided"},
    )

    assert rows[0]["term_props"] == {"definition": "decided", "preferredTerm": "kept"}
