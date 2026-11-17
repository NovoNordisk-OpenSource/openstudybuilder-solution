"""Reading the terminology-changes spreadsheet that accompanies a CDISC release.

CDISC publishes one of these per catalogue with each quarterly package, listing in
prose what changed and why. It is commentary rather than data: nothing parsed here
feeds the analysis or gates the import.

Two things about the format are worth knowing before changing any of this.

**It is the legacy binary `.xls`,** not the `.xlsx` every other CDISC workbook uses, so
`openpyxl` cannot open it and `xlrd` is used instead. That is also why the release date
arrives as an Excel serial number rather than a date.

**`CDISC Term Type` does not mean what its name suggests.** It is not "term or
codelist" — it doubles as "which property changed", taking values like `CDISC
Definition` and `NCI Preferred Term` alongside `Term` and `CDISC Codelist`. It is
tempting to route each row to its subject by this column, and it does not work:
codelists have definitions and synonyms too, so several `CDISC Definition` and `CDISC
Synonym` rows are about a codelist rather than a term. What the `NCI Code` actually
matches in the staged catalogue is the reliable answer, and resolving it that way is
the repository's job. The column is used here for one thing only — recognising the
`CDISC Codelist Name` fan-out below — and is then discarded.
"""

import logging
import re
import uuid
from datetime import date
from typing import Any

import xlrd

from common.exceptions import ValidationException
from standards_import.config import settings
from standards_import.models.changelog import ChangelogEntry, ChangeType

log = logging.getLogger(__name__)

SHEET_SUFFIX = "Terminology Changes"

# "SDTM Terminology Changes" -> "SDTM". Catalogues are spelled inconsistently across
# CDISC's own artefacts ("ADaM" here, "ADAM CT" in the package documents), so the
# caller upper-cases what this yields, exactly as `derive_catalogue_from_title` does
# for the published package titles.
SHEET_TITLE_RE = re.compile(rf"^(.+?)\s+{SHEET_SUFFIX}$", re.IGNORECASE)

RELEASE_DATE_HEADER = "Release Date"
REQUEST_CODE_HEADER = "Request Code"
CHANGE_TYPE_HEADER = "Change Type"
NCI_CODE_HEADER = "NCI Code"
TERM_TYPE_HEADER = "CDISC Term Type"
SHORT_NAME_HEADER = "CDISC Codelist (Short Name)"
LONG_NAME_HEADER = "CDISC Codelist (Long Name)"
SUMMARY_HEADER = "Change Summary"
INSTRUCTIONS_HEADER = "Change Implementation Instructions"

REQUIRED_HEADERS = [
    RELEASE_DATE_HEADER,
    REQUEST_CODE_HEADER,
    CHANGE_TYPE_HEADER,
    NCI_CODE_HEADER,
    TERM_TYPE_HEADER,
    SHORT_NAME_HEADER,
    SUMMARY_HEADER,
]

# The term type whose rows CDISC repeats once per member term. Every such row carries
# the same before-and-after — the codelist's own renaming — and differs only in the
# `NCI Code` of the member it was copied onto, so they collapse to one entry.
CODELIST_NAME_TERM_TYPE = "CDISC Codelist Name"

# What CDISC writes where a column does not apply, rather than leaving it empty.
NOT_APPLICABLE = {"", "- - -", "N/A", "NA"}


def parse_changelog_workbook(payload: bytes, effective_date: date) -> dict[str, Any]:
    """Extracts the change entries from one terminology-changes spreadsheet.

    Cross-checks the sheet's own `Release Date` against the effective date it is being
    uploaded against, the same way a package file's name is checked against its
    `effectiveDate`: a sheet filed under the wrong release would attach commentary from
    one quarter to the codelists of another.
    """

    ValidationException.raise_if(
        settings.max_package_file_bytes
        and len(payload) > settings.max_package_file_bytes,
        msg=f"The uploaded file is {len(payload)} bytes, which is larger than the "
        f"accepted maximum of {settings.max_package_file_bytes} bytes.",
    )

    try:
        workbook = xlrd.open_workbook(file_contents=payload)
    except Exception as exc:  # pylint: disable=broad-except
        raise ValidationException(
            msg=f"The uploaded file could not be read as a spreadsheet: {exc}. CDISC "
            "publishes the terminology changes as a legacy .xls file; an .xlsx saved "
            "from it will not be read."
        ) from exc

    sheet_names = [
        name for name in workbook.sheet_names() if name.strip().endswith(SHEET_SUFFIX)
    ]
    ValidationException.raise_if_not(
        sheet_names,
        msg=f"No sheet named '… {SHEET_SUFFIX}' in this workbook. Expected a CDISC "
        "terminology-changes export.",
    )
    ValidationException.raise_if(
        len(sheet_names) > 1,
        msg=f"This workbook has {len(sheet_names)} '… {SHEET_SUFFIX}' sheets "
        f"({', '.join(sheet_names)}). One file covers one catalogue, so which "
        "catalogue this is cannot be decided.",
    )

    sheet_name = sheet_names[0]
    rows = read_sheet(workbook, workbook.sheet_by_name(sheet_name), effective_date)
    entries, collapsed = collapse_codelist_name_rows(rows)

    return {
        "entries": entries,
        "collapsed": collapsed,
        "sheet": sheet_name,
        "catalogue": derive_catalogue_from_sheet(sheet_name),
    }


def derive_catalogue_from_sheet(sheet_name: str) -> str | None:
    """Reads the catalogue out of the sheet title, or `None` if it does not say.

    Returning `None` rather than raising is deliberate: the caller has a `catalogue`
    query parameter to fall back on, so a future file CDISC titles differently is
    something the uploader can work around rather than a wall.
    """

    match = SHEET_TITLE_RE.match(sheet_name.strip())
    if match is None:
        log.warning(
            "Sheet '%s' does not match the '<catalogue> %s' shape, so its catalogue "
            "cannot be derived from it",
            sheet_name,
            SHEET_SUFFIX,
        )
        return None

    return f"{match.group(1).strip().upper()} CT"


def read_sheet(workbook, sheet, effective_date: date) -> list[dict[str, Any]]:
    """Reads one sheet's rows, checking each against the release it is filed under."""

    if sheet.nrows < 1:
        return []

    header = [str(cell.value).strip() for cell in sheet.row(0)]
    missing = [name for name in REQUIRED_HEADERS if name not in header]
    ValidationException.raise_if(
        missing,
        msg=f"Sheet '{sheet.name}' is missing the column(s) {', '.join(missing)}. "
        "Expected a CDISC terminology-changes export.",
    )
    columns = {name: header.index(name) for name in header}

    entries = []
    for index in range(1, sheet.nrows):
        row = sheet.row(index)

        release_date = read_release_date(row, columns, workbook.datemode)
        ValidationException.raise_if(
            release_date is not None and release_date != effective_date,
            msg=f"Row {index + 1} of sheet '{sheet.name}' has release date "
            f"'{release_date}', but this file is being uploaded against effective date "
            f"'{effective_date.isoformat()}'. Upload it against the release it "
            "describes.",
        )

        short_name = text_at(row, columns.get(SHORT_NAME_HEADER))
        change_type = read_change_type(
            text_at(row, columns.get(CHANGE_TYPE_HEADER)), sheet.name, index
        )
        if not short_name or change_type is None:
            # A row naming no codelist has nothing to attach to, and one with no change
            # type says nothing. Neither has been seen in a real file; skipping beats
            # failing the upload over a stray trailing row.
            log.warning(
                "Skipping row %s of sheet '%s': no codelist short name or change type",
                index + 1,
                sheet.name,
            )
            continue

        entries.append(
            {
                "uid": str(uuid.uuid4()),
                "change_type": change_type.value,
                "change_summary": text_at(row, columns.get(SUMMARY_HEADER)) or "",
                "request_codes": split_request_codes(
                    text_at(row, columns.get(REQUEST_CODE_HEADER))
                ),
                "implementation_instructions": text_at(
                    row, columns.get(INSTRUCTIONS_HEADER)
                ),
                "nci_code": text_at(row, columns.get(NCI_CODE_HEADER)),
                "codelist_short_name": short_name,
                "codelist_long_name": text_at(row, columns.get(LONG_NAME_HEADER)),
                "term_type": text_at(row, columns.get(TERM_TYPE_HEADER)) or "",
            }
        )

    return entries


def collapse_codelist_name_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    """Folds each codelist-rename fan-out back into the one change it describes.

    A renamed codelist is reported once per member term, every copy carrying the same
    summary and request codes and differing only in the `NCI Code` of the member it
    landed on. Left alone, a codelist with 35 terms would show a reviewer 35 identical
    "codelist renamed" notes, one against each term — and none of them would be about
    the term it was attached to.

    The surviving entry carries no `nci_code`, which is what marks it as being about
    the codelist itself.

    `term_type` is dropped from every row here, fanned-out or not: it has done its one
    job, and which node the entry ends up attached to says the rest.
    """

    collapsed: list[dict[str, Any]] = []
    seen: dict[tuple, dict[str, Any]] = {}
    folded = 0

    for row in rows:
        entry = {key: value for key, value in row.items() if key != "term_type"}
        if row["term_type"] != CODELIST_NAME_TERM_TYPE:
            collapsed.append(entry)
            continue

        entry["nci_code"] = None
        key = (
            entry["change_type"],
            entry["codelist_short_name"],
            entry["change_summary"],
            tuple(entry["request_codes"]),
        )
        if key in seen:
            folded += 1
            continue
        seen[key] = entry
        collapsed.append(entry)

    return collapsed, folded


def read_release_date(row, columns: dict[str, int], datemode: int) -> date | None:
    """Reads the `Release Date` cell, which CDISC writes as an Excel serial number."""

    index = columns.get(RELEASE_DATE_HEADER)
    if index is None or index >= len(row):
        return None

    cell = row[index]
    if cell.ctype == xlrd.XL_CELL_DATE:
        return xlrd.xldate_as_datetime(cell.value, datemode).date()

    text = str(cell.value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        log.warning("Release date '%s' is neither an Excel date nor ISO-8601", text)
        return None


def read_change_type(
    value: str | None, sheet_name: str, index: int
) -> ChangeType | None:
    """Maps the sheet's title-cased change type onto the enum."""

    if not value:
        return None
    try:
        return ChangeType(value.strip().upper())
    except ValueError:
        log.warning(
            "Row %s of sheet '%s' has unrecognised change type '%s'",
            index + 1,
            sheet_name,
            value,
        )
        return None


def split_request_codes(value: str | None) -> list[str]:
    """Splits the semicolon-separated `Request Code` column.

    `N/A` is how the sheet says a change came from NCI rather than from a request, and
    becomes no codes rather than a code called "N/A".
    """

    if not value:
        return []
    codes = [code.strip() for code in value.split(";")]
    return [code for code in codes if code and code.upper() not in NOT_APPLICABLE]


def text_at(row, index: int | None) -> str | None:
    """Reads one cell as text, treating CDISC's not-applicable markers as absent."""

    if index is None or index >= len(row):
        return None
    value = row[index].value
    if isinstance(value, float) and value.is_integer():
        # xlrd reads every unformatted number as a float; a code typed as a number
        # would otherwise arrive as "123.0".
        value = int(value)
    text = str(value).strip()
    return None if text in NOT_APPLICABLE else text


# --- reading them back out -------------------------------------------------------


def to_models(records: list[dict[str, Any]]) -> list[ChangelogEntry]:
    """Turns stored entries into the response model, folding cross-catalogue repeats.

    Catalogues overlap: `LBTEST` belongs to both SDTM and SEND, and each ships its own
    spreadsheet reporting the same change to it. Stored, those are two entries — they
    came from two files, and a re-upload of either has to replace only its own. Read
    back against a grouped codelist, they are one change, and showing it twice with
    nothing visibly distinguishing the copies would read as a bug.

    So they are folded here rather than at write time, and `catalogues` names all of
    them — the same way a value several catalogues supplied is reported once with the
    catalogues that supplied it.
    """

    merged: dict[tuple[Any, ...], ChangelogEntry] = {}
    for record in records:
        stored = record.get("entry", record)
        key = (
            stored["change_type"],
            stored["change_summary"],
            stored.get("nci_code"),
            stored["codelist_short_name"],
            tuple(stored.get("request_codes") or []),
            stored.get("implementation_instructions"),
        )
        entry = merged.get(key)
        if entry is None:
            entry = ChangelogEntry(
                change_type=ChangeType(stored["change_type"]),
                change_summary=stored["change_summary"],
                request_codes=list(stored.get("request_codes") or []),
                implementation_instructions=stored.get("implementation_instructions"),
                nci_code=stored.get("nci_code"),
                codelist_short_name=stored["codelist_short_name"],
                codelist_long_name=stored.get("codelist_long_name"),
            )
            merged[key] = entry
        if stored.get("catalogue") and stored["catalogue"] not in entry.catalogues:
            entry.catalogues.append(stored["catalogue"])
        if (
            stored.get("source_file")
            and stored["source_file"] not in entry.source_files
        ):
            entry.source_files.append(stored["source_file"])

    for entry in merged.values():
        entry.catalogues.sort()
        entry.source_files.sort()

    return sorted(merged.values(), key=lambda e: (e.nci_code or "", e.change_summary))
