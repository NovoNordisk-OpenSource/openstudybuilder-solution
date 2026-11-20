"""Reading the paired-codelist spreadsheets that accompany a CDISC release.

Which code codelist a name codelist belongs with is not reliably derivable from the
data: the submission values usually imply it, but not always, so the pairing is taken
from the spreadsheets CDISC publishes alongside the packages. Those have to be uploaded
with the release, the same way the package files are.
This is the same process as the bootstrap script.

The suffix table below is still used, but only to work out which row of a pair is the
name and which is the code — not to guess that a pairing exists.
"""

import io
import logging
from typing import Any

import openpyxl

from common.exceptions import ValidationException
from standards_import.config import settings

log = logging.getLogger(__name__)

SHEET_SUFFIX = "Paired Codelist Metadata"
CONCEPT_ID_HEADER = "Code"
SUBMISSION_VALUE_HEADER = "CDISC Submission Value"
CODELIST_NAME_HEADER = "Codelist Name"

# How a code codelist's submission value relates to its name codelist's. Used to tell
# the two rows of a pair apart.
NAME_CODE_SUFFIXES = [("TN", "TC"), ("PN", "PC"), ("", "CD")]


def parse_pairing_workbook(payload: bytes) -> dict[str, Any]:
    """Extracts the codelist pairings from a paired-view workbook.

    Rows come in consecutive pairs, one naming the terms and one coding them, in no
    guaranteed order — which of the two is which is decided by their submission values.
    """

    ValidationException.raise_if(
        settings.max_package_file_bytes
        and len(payload) > settings.max_package_file_bytes,
        msg=f"The uploaded file is {len(payload)} bytes, which is larger than the "
        f"accepted maximum of {settings.max_package_file_bytes} bytes.",
    )

    try:
        workbook = openpyxl.load_workbook(io.BytesIO(payload), read_only=True)
    except Exception as exc:  # pylint: disable=broad-except
        raise ValidationException(
            msg=f"The uploaded file could not be read as a spreadsheet: {exc}"
        ) from exc

    sheets = [name for name in workbook.sheetnames if name.endswith(SHEET_SUFFIX)]
    ValidationException.raise_if_not(
        sheets,
        msg=f"No sheet named '… {SHEET_SUFFIX}' in this workbook. Expected a CDISC "
        "paired-view export.",
    )

    pairings: list[dict[str, Any]] = []
    skipped: list[str] = []
    for sheet_name in sheets:
        sheet_pairings, sheet_skipped = read_sheet(workbook[sheet_name])
        pairings.extend(sheet_pairings)
        skipped.extend(sheet_skipped)

    return {"pairings": pairings, "skipped": skipped, "sheets": sheets}


def read_sheet(sheet) -> tuple[list[dict[str, Any]], list[str]]:
    """Reads one sheet's consecutive row pairs."""

    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return [], []

    header = [str(cell).strip() if cell is not None else "" for cell in rows[0]]
    try:
        concept_column = header.index(CONCEPT_ID_HEADER)
        submission_column = header.index(SUBMISSION_VALUE_HEADER)
    except ValueError as exc:
        raise ValidationException(
            msg=f"Sheet '{sheet.title}' has no '{CONCEPT_ID_HEADER}' and "
            f"'{SUBMISSION_VALUE_HEADER}' columns."
        ) from exc
    name_column = (
        header.index(CODELIST_NAME_HEADER) if CODELIST_NAME_HEADER in header else None
    )

    entries = []
    for row in rows[1:]:
        concept_id = value_at(row, concept_column)
        submission_value = value_at(row, submission_column)
        if concept_id and submission_value:
            entries.append(
                {
                    "concept_id": concept_id,
                    "submission_value": submission_value,
                    "codelist_name": value_at(row, name_column),
                }
            )

    return pair_entries(entries, sheet.title)


def pair_entries(
    entries: list[dict[str, Any]], source: str
) -> tuple[list[dict[str, Any]], list[str]]:
    """Matches name rows to code rows by their submission values.

    The workbook lists the two halves of a pair on consecutive rows, but walking it two
    at a time goes wrong the moment a row is duplicated: every later pair is then
    misaligned. Grouping by the shared base of the submission values instead is immune
    to that, and to the two halves appearing in either order.
    """

    groups: dict[str, dict[str, dict[str, Any]]] = {}
    for entry in entries:
        base, role = classify(entry["submission_value"])
        groups.setdefault(base, {})[role] = entry

    pairings, skipped = [], []
    for base, halves in sorted(groups.items()):
        name_entry, code_entry = halves.get("name"), halves.get("code")
        if name_entry and code_entry:
            pairings.append(
                {
                    "name_concept_id": name_entry["concept_id"],
                    "code_concept_id": code_entry["concept_id"],
                    "name_submission_value": name_entry["submission_value"],
                    "code_submission_value": code_entry["submission_value"],
                    "codelist_name": name_entry.get("codelist_name"),
                    "source": source,
                }
            )
        else:
            present = (name_entry or code_entry or {}).get("submission_value", base)
            skipped.append(f"{source}: {present} has no counterpart in this workbook")

    return pairings, skipped


def classify(submission_value: str) -> tuple[str, str]:
    """Works out whether a submission value names terms or codes them, and its base.

    Code suffixes are tested before name suffixes so a value can only be read one way,
    and a value matching nothing is treated as the bare name half of an `X`/`XCD` pair.
    """

    for name_suffix, code_suffix in NAME_CODE_SUFFIXES:
        if code_suffix and submission_value.endswith(code_suffix):
            return submission_value[: -len(code_suffix)], "code"
    for name_suffix, _ in NAME_CODE_SUFFIXES:
        if name_suffix and submission_value.endswith(name_suffix):
            return submission_value[: -len(name_suffix)], "name"
    # The bare form is the name half of an `X` / `XCD` pair.
    return submission_value, "name"


def value_at(row: tuple[Any, ...], index: int | None) -> str | None:
    if index is None or index >= len(row) or row[index] is None:
        return None
    text = str(row[index]).strip()
    return text or None
