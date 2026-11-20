"""Reading a paired-view workbook: which row names terms, which codes them."""

import pytest

from common.exceptions import ValidationException
from standards_import.services.pairing_service import (
    classify,
    pair_entries,
    read_sheet,
    value_at,
)


class FakeSheet:
    """Just enough of an openpyxl worksheet for `read_sheet`."""

    def __init__(self, title, rows):
        self.title = title
        self._rows = rows

    def iter_rows(self, values_only=True):
        assert values_only is True
        return iter(self._rows)


HEADER = ("Code", "CDISC Submission Value", "Codelist Name")


# --- classify -------------------------------------------------------------------


@pytest.mark.parametrize(
    "submission_value,expected",
    [
        # the three documented pairs
        ("VSTESTCD", ("VSTEST", "code")),
        ("VSTEST", ("VSTEST", "name")),
        ("XTN", ("X", "name")),
        ("XTC", ("X", "code")),
        ("XPN", ("X", "name")),
        ("XPC", ("X", "code")),
        # a value matching nothing is the bare name half of an X / XCD pair
        ("NY", ("NY", "name")),
        ("NYCD", ("NY", "code")),
    ],
)
def test_classify_reads_a_submission_value_one_way_only(submission_value, expected):
    assert classify(submission_value) == expected


def test_code_suffixes_are_tested_before_name_suffixes():
    """Otherwise a value could be read as either half depending on the order."""

    base, role = classify("LBTESTCD")

    assert (base, role) == ("LBTEST", "code")
    # and its partner reduces to the same base, which is what pairs them
    assert classify("LBTEST")[0] == base


# --- pair_entries ---------------------------------------------------------------


def entry(concept_id, submission_value, name=None):
    return {
        "concept_id": concept_id,
        "submission_value": submission_value,
        "codelist_name": name,
    }


def test_a_name_row_and_a_code_row_become_one_pairing():
    pairings, skipped = pair_entries(
        [entry("C1", "VSTEST", "Vital Signs Test Name"), entry("C2", "VSTESTCD")],
        "SDTM.xlsx",
    )

    assert not skipped
    assert pairings == [
        {
            "name_concept_id": "C1",
            "code_concept_id": "C2",
            "name_submission_value": "VSTEST",
            "code_submission_value": "VSTESTCD",
            "codelist_name": "Vital Signs Test Name",
            "source": "SDTM.xlsx",
        }
    ]


def test_the_two_halves_may_appear_in_either_order():
    """The workbook does not guarantee which of the pair comes first."""

    code_first, _ = pair_entries(
        [entry("C2", "VSTESTCD"), entry("C1", "VSTEST")], "SDTM.xlsx"
    )
    name_first, _ = pair_entries(
        [entry("C1", "VSTEST"), entry("C2", "VSTESTCD")], "SDTM.xlsx"
    )

    assert code_first == name_first


def test_a_duplicated_row_does_not_misalign_everything_after_it():
    """Walking the sheet two rows at a time breaks here; grouping by base does not."""

    pairings, skipped = pair_entries(
        [
            entry("C1", "VSTEST"),
            entry("C1", "VSTEST"),  # the duplicate
            entry("C2", "VSTESTCD"),
            entry("C3", "LBTEST"),
            entry("C4", "LBTESTCD"),
        ],
        "SDTM.xlsx",
    )

    assert not skipped
    assert [(p["name_concept_id"], p["code_concept_id"]) for p in pairings] == [
        ("C3", "C4"),
        ("C1", "C2"),
    ]


def test_a_half_with_no_counterpart_is_reported_not_dropped_silently():
    pairings, skipped = pair_entries([entry("C1", "VSTEST")], "SDTM.xlsx")

    assert not pairings
    assert skipped == ["SDTM.xlsx: VSTEST has no counterpart in this workbook"]


def test_an_unpaired_half_does_not_stop_the_others_pairing():
    pairings, skipped = pair_entries(
        [entry("C1", "VSTEST"), entry("C2", "VSTESTCD"), entry("C9", "ORPHANCD")],
        "SDTM.xlsx",
    )

    assert len(pairings) == 1
    assert len(skipped) == 1


def test_pairings_come_out_in_a_stable_order():
    """Sorted by base, so two runs over the same workbook agree."""

    shuffled = [
        entry("C4", "LBTESTCD"),
        entry("C1", "VSTEST"),
        entry("C3", "LBTEST"),
        entry("C2", "VSTESTCD"),
    ]

    pairings, _ = pair_entries(shuffled, "SDTM.xlsx")

    assert [p["name_submission_value"] for p in pairings] == ["LBTEST", "VSTEST"]


# --- value_at -------------------------------------------------------------------


@pytest.mark.parametrize(
    "row,index,expected",
    [
        (("a", "b"), 0, "a"),
        (("  padded  ",), 0, "padded"),
        (("", "b"), 0, None),
        (("   ",), 0, None),
        ((None,), 0, None),
        (("a",), None, None),
        (("a",), 5, None),  # short row
        ((123,), 0, "123"),  # openpyxl hands back numbers
    ],
)
def test_value_at_reads_a_cell_defensively(row, index, expected):
    assert value_at(row, index) == expected


# --- read_sheet -----------------------------------------------------------------


def test_read_sheet_pairs_the_rows_it_finds():
    sheet = FakeSheet(
        "SDTM Paired Codelist Metadata",
        [HEADER, ("C1", "VSTEST", "Vital Signs Test Name"), ("C2", "VSTESTCD", None)],
    )

    pairings, skipped = read_sheet(sheet)

    assert not skipped
    assert pairings[0]["codelist_name"] == "Vital Signs Test Name"
    assert pairings[0]["source"] == "SDTM Paired Codelist Metadata"


def test_read_sheet_finds_its_columns_by_header_not_position():
    sheet = FakeSheet(
        "S",
        [
            ("Codelist Name", "Something Else", "CDISC Submission Value", "Code"),
            ("Vital Signs Test Name", "x", "VSTEST", "C1"),
            (None, "x", "VSTESTCD", "C2"),
        ],
    )

    pairings, _ = read_sheet(sheet)

    assert (pairings[0]["name_concept_id"], pairings[0]["code_concept_id"]) == (
        "C1",
        "C2",
    )


def test_read_sheet_skips_rows_missing_either_required_cell():
    sheet = FakeSheet(
        "S",
        [
            HEADER,
            ("C1", "VSTEST", None),
            ("C2", "VSTESTCD", None),
            (None, "NOCODE", None),
            ("C9", None, None),
        ],
    )

    pairings, skipped = read_sheet(sheet)

    assert len(pairings) == 1
    assert not skipped


def test_read_sheet_works_without_the_optional_name_column():
    sheet = FakeSheet(
        "S",
        [
            ("Code", "CDISC Submission Value"),
            ("C1", "VSTEST"),
            ("C2", "VSTESTCD"),
        ],
    )

    pairings, _ = read_sheet(sheet)

    assert pairings[0]["codelist_name"] is None


def test_read_sheet_refuses_a_sheet_without_the_required_columns():
    sheet = FakeSheet("Wrong Sheet", [("Alpha", "Beta"), ("1", "2")])

    with pytest.raises(ValidationException, match="has no 'Code' and"):
        read_sheet(sheet)


def test_an_empty_sheet_yields_nothing_rather_than_failing():
    assert read_sheet(FakeSheet("S", [])) == ([], [])
