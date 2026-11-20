"""Tests for enriching a CT diff with CDISC's change logs.

Almost everything here runs on plain dicts. The parsing layer is driven through
a fake that duck-types the handful of xlrd calls ``rows_from_book`` makes, so no
binary .xls fixture is committed - the real files are legacy BIFF, unreviewable
in a diff, and only available from the private mirror. The one test that reads a
real file skips unless that mirror is present.
"""

import json
import os

import pytest
import xlrd

from src.scripts.package_diff.changelog_annotate import (
    annotate_report,
    catalogue_and_date,
    changelog_entries,
    default_changelog_dir,
    index_rows,
    match_rows_for_change,
    read_changelog_rows,
    row_field,
    rows_from_book,
)
from src.scripts.package_diff.ct_diff import (
    build_report,
    normalize_package,
    render_change_table,
    report_to_json,
)
from src.scripts.package_diff.ct_diff_grouping import group_report
from src.tests.package_diff.factories import make_codelist, make_package, make_term

HEADERS = [
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


class FakeSheet:
    """The slice of xlrd's Sheet that rows_from_book actually uses.

    Cells are given as plain values; a (ctype, value) tuple opts one cell into a
    specific xlrd cell type, which is how the date-serial case is exercised.
    """

    def __init__(self, name, rows, datemode=0):
        self.name = name
        self._rows = rows
        self.nrows = len(rows)
        self.ncols = max((len(row) for row in rows), default=0)
        self.book = type("Book", (), {"datemode": datemode})()

    def _raw(self, row_index, col_index):
        row = self._rows[row_index]
        return row[col_index] if col_index < len(row) else ""

    def cell_value(self, row_index, col_index):
        raw = self._raw(row_index, col_index)
        return raw[1] if isinstance(raw, tuple) else raw

    def cell(self, row_index, col_index):
        raw = self._raw(row_index, col_index)
        if isinstance(raw, tuple):
            ctype, value = raw
        else:
            value = raw
            ctype = xlrd.XL_CELL_EMPTY if value == "" else xlrd.XL_CELL_TEXT
        return type("Cell", (), {"ctype": ctype, "value": value})()


class FakeBook:
    def __init__(self, *sheets):
        self._sheets = list(sheets)

    def sheet_names(self):
        return [sheet.name for sheet in self._sheets]

    def sheet_by_name(self, name):
        return next(sheet for sheet in self._sheets if sheet.name == name)

    def sheet_by_index(self, index):
        return self._sheets[index]


def make_row(**kwargs):
    """A normalized row dict, defaulting every unmentioned column to None."""
    row = {
        "release_date": "2025-03-28",
        "request_code": "CDISC-1",
        "change_type": "Update",
        "nci_code": None,
        "term_type": None,
        "codelist_short_name": None,
        "codelist_long_name": None,
        "change_summary": None,
        "original": None,
        "new": None,
        "instructions": None,
    }
    row.update(kwargs)
    return row


def sheet_of(rows, name="SDTM Terminology Changes", lead=(), headers=None):
    """A FakeSheet with `lead` rows above the header, then `rows` beneath it."""
    return FakeSheet(name, [*lead, headers or HEADERS, *rows])


class Test:
    # -- parsing ----------------------------------------------------------

    def test__rows_from_book_reads_a_row_into_normalized_keys(self):
        sheet = sheet_of(
            [
                [
                    "2025-03-28",
                    "CDISC-6662",
                    "Update",
                    "C100449",
                    "CDISC Definition",
                    "LBTESTCD",
                    "Lab Test Code",
                    "Update CDISC Definition",
                    "old text",
                    "new text",
                    "Apply on import.",
                ]
            ]
        )

        (row,) = rows_from_book(FakeBook(sheet))

        assert row["request_code"] == "CDISC-6662"
        assert row["nci_code"] == "C100449"
        assert row["term_type"] == "CDISC Definition"
        assert row["codelist_short_name"] == "LBTESTCD"
        assert row["instructions"] == "Apply on import."

    def test__rows_from_book_finds_a_header_below_a_title_row(self):
        sheet = sheet_of(
            [["2025-03-28", "CDISC-1", "Add", "C1", "Term", "CL", "", "", "", "", ""]],
            lead=[["SDTM Terminology Changes 2025-03-28"], []],
        )

        (row,) = rows_from_book(FakeBook(sheet))

        assert row["nci_code"] == "C1"

    def test__rows_from_book_picks_the_changes_sheet_not_the_first(self):
        # MRCT's sheet name does not match its file-name stem, so the sheet is
        # chosen on a "Changes" suffix rather than by an expected name.
        cover = FakeSheet("Cover", [["nothing here"]])
        changes = sheet_of(
            [["2025-03-28", "CDISC-1", "Add", "C1", "Term", "CL", "", "", "", "", ""]],
            name="MRCT Terminology Changes",
        )

        (row,) = rows_from_book(FakeBook(cover, changes))

        assert row["nci_code"] == "C1"

    def test__rows_from_book_handles_the_ten_column_variant(self):
        # Files published before "Change Implementation Instructions" existed.
        sheet = sheet_of(
            [["2014-09-26", "CDISC-1", "Add", "C1", "Term", "CL", "", "", "", ""]],
            headers=HEADERS[:-1],
        )

        (row,) = rows_from_book(FakeBook(sheet))

        assert row["nci_code"] == "C1"
        assert row["instructions"] is None

    def test__rows_from_book_normalizes_placeholders_and_blanks_to_none(self):
        sheet = sheet_of(
            [
                [
                    "2025-03-28",
                    "CDISC-1",
                    "Add",
                    "C1",
                    "Term",
                    "CL",
                    "",
                    "Add new term",
                    "- - -",
                    "new",
                    "",
                ]
            ]
        )

        (row,) = rows_from_book(FakeBook(sheet))

        assert row["original"] is None
        assert row["codelist_long_name"] is None
        assert row["new"] == "new"

    def test__rows_from_book_renders_a_date_serial_cell_as_iso(self):
        sheet = sheet_of(
            [
                [
                    (xlrd.XL_CELL_DATE, 45744.0),
                    "CDISC-1",
                    "Add",
                    "C1",
                    "Term",
                    "CL",
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            ]
        )

        (row,) = rows_from_book(FakeBook(sheet))

        assert row["release_date"] == "2025-03-28"

    def test__rows_from_book_drops_entirely_empty_rows(self):
        sheet = sheet_of([["", "", "", "", "", "", "", "", "", "", ""]])

        assert rows_from_book(FakeBook(sheet)) == []

    def test__rows_from_book_rejects_a_sheet_with_no_header(self):
        with pytest.raises(ValueError, match="header"):
            rows_from_book(FakeBook(FakeSheet("Changes", [["a", "b"], ["c", "d"]])))

    # -- field discrimination --------------------------------------------

    def test__row_field_maps_term_type_to_the_diff_field(self):
        assert row_field(make_row(term_type="CDISC Definition")) == "definition"
        assert row_field(make_row(term_type="NCI Preferred Term")) == "preferredTerm"
        assert row_field(make_row(term_type="CDISC Codelist Name")) == "name"

    def test__row_field_is_none_for_whole_entity_rows(self):
        assert row_field(make_row(term_type="Term")) is None
        assert row_field(make_row(term_type="CDISC Codelist")) is None

    def test__row_field_falls_back_to_the_summary_for_an_unseen_term_type(self):
        row = make_row(term_type="Something New", change_summary="Add CDISC Synonym")

        assert row_field(row) == "synonyms"

    # -- indexing ---------------------------------------------------------

    def test__index_rows_keys_a_codelist_rename_by_short_name_not_nci_code(self):
        # CDISC fans a codelist rename out over every member term, each row
        # carrying that term's NCI code. Indexing those by NCI code would hang
        # "the codelist was renamed" off every unchanged term in the codelist.
        rows = [
            make_row(
                nci_code=f"T{i}",
                term_type="CDISC Codelist Name",
                codelist_short_name="LBTESTCD",
            )
            for i in range(5)
        ]

        index = index_rows(rows)

        assert list(index) == [("codelist", "LBTESTCD")]
        assert not any(key[0] == "code" for key in index)

    def test__index_rows_drops_rows_with_no_usable_key(self):
        assert index_rows([make_row(nci_code=None)]) == {}

    # -- matching ---------------------------------------------------------

    def test__match_prefers_the_row_describing_the_changed_field(self):
        index = index_rows(
            [
                make_row(
                    nci_code="C1", term_type="CDISC Definition", request_code="DEF"
                ),
                make_row(
                    nci_code="C1", term_type="NCI Preferred Term", request_code="PT"
                ),
            ]
        )
        change = {"kind": "term_changed", "conceptId": "C1", "field": "definition"}

        (row,) = match_rows_for_change(index, change, {})

        assert row["request_code"] == "DEF"

    def test__match_prefers_the_row_with_the_matching_change_type(self):
        index = index_rows(
            [
                make_row(nci_code="C1", change_type="Add", request_code="ADD"),
                make_row(nci_code="C1", change_type="Remove", request_code="REM"),
            ]
        )
        change = {"kind": "term_removed", "term": {"conceptId": "C1"}}

        (row,) = match_rows_for_change(index, change, {})

        assert row["request_code"] == "REM"

    def test__match_prefers_the_row_scoped_to_the_right_codelist(self):
        index = index_rows(
            [
                make_row(
                    nci_code="T1",
                    change_type="Add",
                    codelist_short_name="AAA",
                    request_code="A",
                ),
                make_row(
                    nci_code="T1",
                    change_type="Add",
                    codelist_short_name="BBB",
                    request_code="B",
                ),
            ]
        )
        pair_diff = {"codelist_labels": {"CL1": {"submissionValue": "BBB"}}}
        change = {"kind": "membership_added", "key": ("CL1", "T1")}

        (row,) = match_rows_for_change(index, change, pair_diff)

        assert row["request_code"] == "B"

    def test__match_narrowing_never_empties_the_candidates(self):
        # A row that satisfies no preference is still better than no rationale
        # at all: every narrowing step is a preference, not a gate.
        index = index_rows(
            [make_row(nci_code="C1", change_type="Update", term_type="Term")]
        )
        change = {"kind": "term_removed", "term": {"conceptId": "C1"}}

        assert len(match_rows_for_change(index, change, {})) == 1

    def test__match_finds_a_codelist_rename_under_its_short_name(self):
        index = index_rows(
            [
                make_row(
                    nci_code="T1",
                    term_type="CDISC Codelist Name",
                    codelist_short_name="LBTESTCD",
                ),
                make_row(
                    nci_code="T2",
                    term_type="CDISC Codelist Name",
                    codelist_short_name="LBTESTCD",
                ),
            ]
        )
        change = {
            "kind": "codelist_changed",
            "conceptId": "CL1",
            "field": "name",
            "codelist": {"submissionValue": "LBTESTCD"},
        }

        rows = match_rows_for_change(index, change, {})

        # Two source rows, one real rename: deduped down to a single annotation.
        assert len(rows) == 1

    def test__match_returns_nothing_for_an_unmatched_or_unknown_change(self):
        index = index_rows([make_row(nci_code="C1")])

        assert (
            match_rows_for_change(
                index,
                {"kind": "term_changed", "conceptId": "C9", "field": "definition"},
                {},
            )
            == []
        )
        assert match_rows_for_change(index, {"kind": "invented_kind"}, {}) == []

    # -- rendering --------------------------------------------------------

    def test__changelog_entries_name_the_request_code_and_summary(self):
        rows = [
            make_row(
                request_code="CDISC-6662", change_summary="Update CDISC Definition"
            )
        ]

        assert changelog_entries(rows) == ["CDISC-6662: Update CDISC Definition"]

    def test__changelog_entries_render_whichever_parts_a_row_has(self):
        # A fifth of all rows carry no request code, almost all from 2014-2015.
        rows = [make_row(request_code=None, change_summary="Add new term")]

        assert changelog_entries(rows) == ["Add new term"]

    def test__changelog_entries_are_empty_when_there_is_nothing_to_say(self):
        assert changelog_entries([]) == []
        assert (
            changelog_entries([make_row(request_code=None, change_summary=None)]) == []
        )

    def test__an_unannotated_table_has_no_change_log_column(self):
        change = {
            "kind": "term_added",
            "term": {"conceptId": "C1", "preferredTerm": "A term"},
        }

        table = render_change_table({}, [change])

        assert table[0] == "| Term |"
        assert table[2] == '| `C1` "A term" |'

    def test__the_annotation_becomes_the_change_log_column(self):
        change = {
            "kind": "term_added",
            "term": {"conceptId": "C1", "preferredTerm": "A term"},
            "changelog": [
                make_row(request_code="CDISC-1", change_summary="Add new term")
            ],
        }

        table = render_change_table({}, [change])

        assert table[0] == "| Term | Change log |"
        assert table[2] == '| `C1` "A term" | CDISC-1: Add new term |'

    def test__several_requests_get_a_line_each_in_the_cell(self):
        # Markdown tables take no real line break, so <br> is the only way a
        # cell holds more than one value legibly.
        change = {
            "kind": "term_added",
            "term": {"conceptId": "C1", "preferredTerm": "A term"},
            "changelog": [
                make_row(request_code="CDISC-1", change_summary="Add new term"),
                make_row(request_code="CDISC-2", change_summary="And again"),
            ],
        }

        table = render_change_table({}, [change])

        assert table[2] == (
            '| `C1` "A term" | CDISC-1: Add new term<br>CDISC-2: And again |'
        )

    # -- report-level wiring ----------------------------------------------

    def test__catalogue_and_date_splits_a_package_filename(self):
        assert catalogue_and_date("sdtmct-2025-03-28.json") == ("sdtmct", "2025-03-28")
        assert catalogue_and_date("not-a-package.txt") == (None, None)
        assert catalogue_and_date(None) == (None, None)

    def test__default_changelog_dir_follows_the_fetch_location(self, monkeypatch):
        monkeypatch.setenv("CDISC_XLS_DIR", "/tmp/xls")
        assert default_changelog_dir() == os.path.join("/tmp/xls", "changelogs")

        monkeypatch.delenv("CDISC_XLS_DIR")
        assert default_changelog_dir() is None

    def test__annotate_report_is_a_no_op_without_a_directory(self):
        report = self._report()

        annotate_report(report, None)
        annotate_report(report, "/definitely/not/here")

        assert not self._annotated(report)

    def test__annotate_report_survives_a_missing_or_unreadable_file(self, tmp_path):
        # The directory exists but holds no change log for this release, which
        # is normal: CDISC does not publish one for every package.
        report = self._report()

        annotate_report(report, str(tmp_path))

        assert not self._annotated(report)

    def test__annotate_report_annotates_a_step_from_its_own_release(
        self, tmp_path, monkeypatch
    ):
        self._place(tmp_path, "sdtmct-2024-02-02.xls")
        monkeypatch.setattr(
            "src.scripts.package_diff.changelog_annotate.read_changelog_rows",
            lambda path: [
                make_row(nci_code="T2", change_type="Add", request_code="CDISC-NEW")
            ],
        )
        report = self._report()

        annotate_report(report, str(tmp_path))

        codes = {
            row["request_code"]
            for change in self._annotated(report)
            for row in change["changelog"]
        }
        assert codes == {"CDISC-NEW"}

    def test__annotate_report_survives_a_file_that_will_not_parse(
        self, tmp_path, monkeypatch
    ):
        self._place(tmp_path, "sdtmct-2024-02-02.xls")

        def explode(path):
            raise xlrd.XLRDError("not a spreadsheet")

        monkeypatch.setattr(
            "src.scripts.package_diff.changelog_annotate.read_changelog_rows", explode
        )
        report = self._report()

        annotate_report(report, str(tmp_path))

        assert not self._annotated(report)

    def test__annotation_survives_grouping(self, tmp_path, monkeypatch):
        # The ordering rule, pinned. Grouping copies a change record whenever it
        # has to stamp anything extra on it, so annotating after grouping would
        # reach the flat report and only some of the grouped copies.
        self._place(tmp_path, "sdtmct-2024-02-02.xls")
        monkeypatch.setattr(
            "src.scripts.package_diff.changelog_annotate.read_changelog_rows",
            lambda path: [
                make_row(nci_code="T2", change_type="Add", request_code="CDISC-NEW")
            ],
        )
        packages = self._packages()
        report = build_report(packages)
        annotate_report(report, str(tmp_path))

        grouped = group_report(report, packages)

        annotated = [
            change
            for bucket in grouped["cumulative"]["codelists"].values()
            for changes in bucket["bands"].values()
            for change in changes
            if change.get("changelog")
        ]
        assert annotated, "grouped copies lost their annotation"

    def test__report_to_json_carries_the_annotation_through(
        self, tmp_path, monkeypatch
    ):
        self._place(tmp_path, "sdtmct-2024-02-02.xls")
        monkeypatch.setattr(
            "src.scripts.package_diff.changelog_annotate.read_changelog_rows",
            lambda path: [
                make_row(
                    nci_code="T2",
                    change_type="Add",
                    request_code="CDISC-NEW",
                    instructions="Long free text that stays out of the Markdown.",
                )
            ],
        )
        report = self._report()
        annotate_report(report, str(tmp_path))

        payload = json.loads(report_to_json(report))

        instructions = [
            row["instructions"]
            for step in payload["steps"]
            for changes in step["bands"].values()
            for change in changes
            for row in change.get("changelog", [])
        ]
        assert "Long free text that stays out of the Markdown." in instructions

    @pytest.mark.skipif(
        not os.environ.get("CDISC_XLS_DIR"),
        reason="needs the private mirror of CDISC change logs",
    )
    def test__reads_a_real_changelog_file(self):
        directory = default_changelog_dir()
        names = sorted(n for n in os.listdir(directory) if n.endswith(".xls"))
        rows = read_changelog_rows(os.path.join(directory, names[0]))

        assert rows
        assert any(row["nci_code"] for row in rows)

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _place(tmp_path, name):
        """A placeholder file, so the reader is reached and can be faked."""
        (tmp_path / name).write_text("")

    @staticmethod
    def _packages():
        # `source` is what a release is matched to its change log by, so these
        # are named exactly as load_package would name them.
        old = normalize_package(
            make_package(
                "2024-01-01",
                [make_codelist("CL1", "SUBCL1", [make_term("T1", "SUB1")])],
            ),
            source="sdtmct-2024-01-01.json",
        )
        new = normalize_package(
            make_package(
                "2024-02-02",
                [
                    make_codelist(
                        "CL1",
                        "SUBCL1",
                        [make_term("T1", "SUB1"), make_term("T2", "SUB2")],
                    )
                ],
            ),
            source="sdtmct-2024-02-02.json",
        )
        return [old, new]

    def _report(self):
        return build_report(self._packages())

    @staticmethod
    def _annotated(report):
        return [
            change
            for step in report["steps"]
            for changes in step["bands"].values()
            for change in changes
            if change.get("changelog")
        ]
