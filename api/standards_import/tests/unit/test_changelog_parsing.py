"""Reading a CDISC terminology-changes spreadsheet.

The interesting cases are all things the real files do that the format does not
advertise: a codelist rename repeated once per member term, `CDISC Term Type` that
does not say what it looks like it says, and a release date written as a number.

Sheets are faked rather than written to a real workbook, the same way
`test_pairing_parsing` fakes an openpyxl one. Here there is a second reason: the only
library that writes the legacy `.xls` CDISC publishes is unmaintained, and taking a
dependency on it to build fixtures would be a poor trade for a reader that needs
`.nrows`, `.name` and `.row()`.
"""

from datetime import date

import pytest
import xlrd

from common.exceptions import ValidationException
from standards_import.services.changelog_service import (
    collapse_codelist_name_rows,
    derive_catalogue_from_sheet,
    parse_changelog_workbook,
    read_change_type,
    read_sheet,
    split_request_codes,
    to_models,
)
from standards_import.services.staging_service import derive_catalogue

HEADER = [
    "Release Date",
    "Request Code",
    "Change Type",
    "NCI Code",
    "CDISC Term Type",
    "CDISC Codelist (Short Name)",
    "CDISC Codelist (Long Name)",
    "Change Summary",
    "Original",
    "New",
    "Change Implementation Instructions",
]

# 2025-09-26 as Excel writes it. The real files carry the date this way on every row.
RELEASE_SERIAL = 45926.0
RELEASE_DATE = date(2025, 9, 26)


class FakeCell:
    """Just enough of an xlrd cell: a value and the tag saying how to read it."""

    def __init__(self, value, ctype=xlrd.XL_CELL_TEXT):
        self.value = value
        self.ctype = ctype


class FakeSheet:
    """Just enough of an xlrd worksheet for `read_sheet`."""

    def __init__(self, rows, name="SDTM Terminology Changes", header=None):
        self.name = name
        self._rows = [header if header is not None else HEADER, *rows]

    @property
    def nrows(self):
        return len(self._rows)

    def row(self, index):
        return [as_cell(value) for value in self._rows[index]]


class FakeWorkbook:
    """`read_sheet` needs only the date mode; 0 is the 1900 epoch Excel uses."""

    datemode = 0


def as_cell(value):
    if isinstance(value, FakeCell):
        return value
    return FakeCell(
        value,
        xlrd.XL_CELL_NUMBER if isinstance(value, float) else xlrd.XL_CELL_TEXT,
    )


def row(
    change_type="Add",
    nci_code="C166074",
    term_type="Term",
    short_name="ARMNULRS",
    long_name="Arm Null Reason",
    summary="Add new term to existing codelist",
    original="- - -",
    new="SCREENING NOT COMPLETED",
    instructions="",
    request_code="CDISC-6719",
    release_date=None,
):
    return [
        (
            release_date
            if release_date is not None
            else FakeCell(RELEASE_SERIAL, xlrd.XL_CELL_DATE)
        ),
        request_code,
        change_type,
        nci_code,
        term_type,
        short_name,
        long_name,
        summary,
        original,
        new,
        instructions,
    ]


def parse(rows, effective_date=RELEASE_DATE, **kwargs):
    return read_sheet(FakeWorkbook(), FakeSheet(rows, **kwargs), effective_date)


# --- the sheet title is what says which catalogue this is -------------------------


@pytest.mark.parametrize(
    "sheet_name,expected",
    [
        # the three real ones, including ADaM's mixed casing
        ("SDTM Terminology Changes", "SDTM CT"),
        ("SEND Terminology Changes", "SEND CT"),
        ("ADaM Terminology Changes", "ADAM CT"),
    ],
)
def test_the_catalogue_is_read_from_the_sheet_title(sheet_name, expected):
    assert derive_catalogue_from_sheet(sheet_name) == expected


def test_a_title_of_another_shape_yields_no_catalogue_rather_than_failing():
    """The caller has a `catalogue` parameter to fall back on, so this is not fatal."""

    assert derive_catalogue_from_sheet("Changes") is None


def test_the_catalogue_matches_what_a_package_name_would_produce():
    """Both have to agree, or the entries would never resolve against the catalogue
    the package file staged — and ADaM is spelled differently in the two places."""

    from_package, _ = derive_catalogue("ADAM CT 2025-09-26")

    assert derive_catalogue_from_sheet("ADaM Terminology Changes") == from_package


# --- the release date cross-check -------------------------------------------------


def test_the_release_date_is_read_from_the_excel_serial_number():
    """CDISC writes it as a number, not a date string."""

    assert len(parse([row()])) == 1


def test_a_sheet_describing_another_release_is_refused():
    """The same check a package file's name gets against its `effectiveDate`: filing
    one quarter's commentary against another release's codelists is silent nonsense."""

    with pytest.raises(ValidationException, match="is being uploaded against"):
        parse([row()], effective_date=date(2025, 3, 28))


def test_the_offending_row_is_named():
    """Counting the header, so the number is the one the spreadsheet shows."""

    with pytest.raises(ValidationException, match="Row 4 of sheet"):
        parse(
            [row(release_date="2025-03-28"), row(release_date="2025-03-28"), row()],
            effective_date=date(2025, 3, 28),
        )


def test_an_iso_date_is_accepted_too():
    """Not seen in a real file, but a sheet re-saved by hand can carry text there."""

    assert len(parse([row(release_date="2025-09-26")])) == 1


def test_a_row_with_no_release_date_is_not_rejected():
    """Only a date that disagrees is an error; a blank one says nothing."""

    assert len(parse([row(release_date="")])) == 1


# --- the shape of the file --------------------------------------------------------


def test_a_workbook_missing_a_column_is_refused():
    header = [name for name in HEADER if name != "NCI Code"]

    with pytest.raises(ValidationException, match="missing the column"):
        parse([row()], header=header)


def test_an_xlsx_is_refused_with_a_hint_about_the_format():
    """CDISC publishes the legacy binary .xls; xlrd cannot read what openpyxl writes,
    and somebody will eventually re-save one and try it."""

    with pytest.raises(ValidationException, match=r"legacy \.xls"):
        parse_changelog_workbook(b"PK\x03\x04 not really a workbook", RELEASE_DATE)


# --- the columns ------------------------------------------------------------------


def test_the_entry_carries_what_the_row_said():
    entry = parse([row()])[0]

    assert entry["change_type"] == "ADD"
    assert entry["change_summary"] == "Add new term to existing codelist"
    assert entry["nci_code"] == "C166074"
    assert entry["codelist_short_name"] == "ARMNULRS"
    assert entry["codelist_long_name"] == "Arm Null Reason"
    assert entry["request_codes"] == ["CDISC-6719"]


def test_before_and_after_values_are_not_stored():
    """Both are readable from the raw nodes and their predecessors. A second copy
    that can disagree with them is worse than none."""

    entry = parse([row()])[0]

    assert "original" not in entry
    assert "new" not in entry


@pytest.mark.parametrize(
    "written,expected",
    [
        ("CDISC-6719", ["CDISC-6719"]),
        # the real SDTM file writes six of them on one row
        ("CDISC-6139; CDISC-1231", ["CDISC-6139", "CDISC-1231"]),
        ("CDISC-6139;CDISC-1231", ["CDISC-6139", "CDISC-1231"]),
        # how the sheet says NCI made the change rather than a request
        ("N/A", []),
        ("", []),
        (None, []),
    ],
)
def test_request_codes_are_split_and_n_a_means_none(written, expected):
    assert split_request_codes(written) == expected


def test_an_empty_instructions_cell_becomes_null():
    """Most rows leave it blank; `null` and `""` would otherwise both mean absent."""

    assert parse([row()])[0]["implementation_instructions"] is None


def test_the_not_applicable_marker_becomes_null():
    """CDISC writes `- - -` rather than leaving a cell empty."""

    assert parse([row(instructions="- - -")])[0]["implementation_instructions"] is None


@pytest.mark.parametrize(
    "written,expected", [("Add", "ADD"), ("Update", "UPDATE"), ("Remove", "REMOVE")]
)
def test_the_change_type_is_upper_cased(written, expected):
    assert read_change_type(written, "sheet", 1).value == expected


def test_an_unrecognised_change_type_drops_the_row_rather_than_the_upload():
    assert read_change_type("Deprecate", "sheet", 1) is None


def test_a_row_naming_no_codelist_is_passed_over():
    """It would have nothing to attach to. Skipping beats failing the whole upload."""

    assert len(parse([row(short_name=""), row()])) == 1


def test_adding_a_synonym_and_removing_one_are_both_updates():
    """`Change Type` is coarser than it looks: the direction is in `Change Summary`,
    which is why nothing should colour-code off the type alone."""

    rows = [
        row(
            change_type="Update",
            term_type="CDISC Synonym",
            summary="Add new CDISC Synonym",
        ),
        row(
            change_type="Update",
            term_type="CDISC Synonym",
            summary="Remove CDISC Synonym",
        ),
    ]

    assert [entry["change_type"] for entry in parse(rows)] == ["UPDATE", "UPDATE"]


# --- the codelist-rename fan-out --------------------------------------------------


def codelist_name_row(nci_code, short_name="EOR06TC"):
    """What CDISC writes once per member term when it renames a codelist.

    Every copy carries the codelist's own old and new name; only the `NCI Code`
    differs, and it is the member term's, not the codelist's.
    """

    return {
        "uid": f"uid-{nci_code}",
        "change_type": "UPDATE",
        "change_summary": "Update CDISC Codelist Name",
        "request_codes": ["CDISC-6139"],
        "implementation_instructions": None,
        "nci_code": nci_code,
        "codelist_short_name": short_name,
        "codelist_long_name": "EORTC QLQ-CR29 Test Code",
        "term_type": "CDISC Codelist Name",
    }


def test_a_codelist_rename_repeated_per_term_becomes_one_entry():
    """The real SDTM file repeats one rename 36 times, once per member. Left alone a
    reviewer would see 36 identical notes, none of them about the term it sat on."""

    entries, folded = collapse_codelist_name_rows(
        [codelist_name_row("C170657"), codelist_name_row("C170658")]
    )

    assert len(entries) == 1
    assert folded == 1


def test_the_surviving_entry_is_about_the_codelist_not_a_term():
    """A null `nci_code` is what marks an entry as being about the codelist itself."""

    entries, _ = collapse_codelist_name_rows([codelist_name_row("C170657")])

    assert entries[0]["nci_code"] is None


def test_two_codelists_renamed_stay_two_entries():
    entries, folded = collapse_codelist_name_rows(
        [codelist_name_row("C170657"), codelist_name_row("C170659", "EOR18TC")]
    )

    assert len(entries) == 2
    assert folded == 0


def test_rows_of_any_other_term_type_are_left_alone():
    """Only the rename fans out. Two terms each gaining a synonym are two changes —
    and routing by `CDISC Term Type` beyond this point is what this avoids, because
    codelists carry definitions and synonyms too."""

    rows = [
        {**codelist_name_row("C1"), "term_type": "CDISC Synonym"},
        {**codelist_name_row("C2"), "term_type": "CDISC Synonym"},
    ]

    entries, folded = collapse_codelist_name_rows(rows)

    assert [entry["nci_code"] for entry in entries] == ["C1", "C2"]
    assert folded == 0


def test_the_term_type_is_not_stored():
    """It has done its one job by here: which node the entry ends up attached to
    already says whether the subject is a term, a codelist or the catalogue."""

    entries, _ = collapse_codelist_name_rows(
        [{**codelist_name_row("C1"), "term_type": "Term"}]
    )

    assert "term_type" not in entries[0]


# --- reading them back out --------------------------------------------------------


def stored(catalogue="SDTM CT", summary="Update NCI Preferred Term", nci="C15189"):
    return {
        "entry": {
            "change_type": "UPDATE",
            "change_summary": summary,
            "request_codes": [],
            "implementation_instructions": None,
            "nci_code": nci,
            "codelist_short_name": "LBTEST",
            "codelist_long_name": "Laboratory Test Name",
            "catalogue": catalogue,
            "source_file": f"{catalogue}.xls",
        }
    }


def test_the_same_change_reported_by_two_catalogues_is_one_entry():
    """`LBTEST` belongs to both SDTM and SEND, and each ships its own sheet saying the
    same thing about it. Two rows in staging, because a re-upload of either has to
    replace only its own — but one change to show."""

    entries = to_models([stored("SDTM CT"), stored("SEND CT")])

    assert len(entries) == 1
    assert entries[0].catalogues == ["SDTM CT", "SEND CT"]


def test_both_source_files_are_kept_on_the_merged_entry():
    entries = to_models([stored("SDTM CT"), stored("SEND CT")])

    assert entries[0].source_files == ["SDTM CT.xls", "SEND CT.xls"]


def test_different_changes_are_not_merged():
    entries = to_models([stored(summary="Add new CDISC Synonym"), stored()])

    assert len(entries) == 2


def test_the_same_summary_about_different_terms_is_not_merged():
    entries = to_models([stored(nci="C1"), stored(nci="C2")])

    assert len(entries) == 2


def test_an_entry_about_the_codelist_itself_sorts_before_the_terms():
    """Its `nci_code` is null, and a reader wants the codelist's own news first."""

    entries = to_models([stored(nci="C1"), stored(nci=None)])

    assert entries[0].nci_code is None
