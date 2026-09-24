"""Convert the CDISC Non-Standard Variables registry from Excel to CSV.

Usage:
    python cdisc_nsv_excel_converter.py <input.xls|.xlsx> [output.csv]

If output.csv is omitted, the file is written to
datafiles/sponsor_library/nonstandard_variables/cdisc_nsv.csv.

The output CSV uses the column names expected by
importers/run_import_nonstandard_variables.py:
    variable_name, label, description_and_notes, simple_datatype, xml_datatype,
    limited_to_domains, limited_to_classes, codelist, external_dictionary,
    role, qualifying_variables, sources, used_in_domains
"""

import csv
import os
import sys

DEFAULT_OUTPUT = "datafiles/sponsor_library/nonstandard_variables/cdisc_nsv.csv"
SHEET_NAME = "Approved NSVs"

OUTPUT_HEADERS = [
    "variable_name",
    "label",
    "description_and_notes",
    "simple_datatype",
    "xml_datatype",
    "limited_to_domains",
    "limited_to_classes",
    "codelist_reference",
    "external_dictionary",
    "role",
    "qualifying_variables",
    "sources",
    "used_in_domains",
]

# Mapping from normalised CDISC headers (lowercase, spaces→underscores, parens stripped)
# to the canonical output column name. Allows tolerance for minor formatting variations
# between CDISC revisions.
HEADER_MAP = {
    "variable_name": "variable_name",
    "label": "label",
    "description_and_notes": "description_and_notes",
    "description": "description_and_notes",
    "simple_datatype": "simple_datatype",
    "xml_datatype": "xml_datatype",
    "limited_to_domains": "limited_to_domains",
    "limited_to_domain": "limited_to_domains",
    "limited_to_domain_s": "limited_to_domains",
    "limited_to_classes": "limited_to_classes",
    "limited_to_class": "limited_to_classes",
    "limited_to_class_es": "limited_to_classes",
    "codelist_reference": "codelist_reference",
    "external_dictionary": "external_dictionary",
    "role": "role",
    "qualifying_variables": "qualifying_variables",
    "qualifying_variable": "qualifying_variables",
    "qualifying_variable_s": "qualifying_variables",
    "sources": "sources",
    "source": "sources",
    "source_s": "sources",
    "used_in_domains": "used_in_domains",
    "used_in_domain": "used_in_domains",
    "used_in_domain_s": "used_in_domains",
}


def normalise(header: str) -> str:
    return (
        (header or "")
        .strip()
        .lower()
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
        .replace("-", "_")
        .replace(" ", "_")
    )


def _read_rows_xlsx(path: str) -> list[tuple]:
    from openpyxl import load_workbook

    workbook = load_workbook(filename=path, data_only=True)
    if SHEET_NAME in workbook.sheetnames:
        sheet = workbook[SHEET_NAME]
    else:
        print(
            f"Warning: sheet '{SHEET_NAME}' not found in {path}; "
            f"using active sheet '{workbook.active.title}'. "
            f"Available sheets: {workbook.sheetnames}"
        )
        sheet = workbook.active
    return list(sheet.iter_rows(values_only=True))


def _read_rows_xls(path: str) -> list[tuple]:
    try:
        import xlrd
    except ImportError:
        print(
            "Error: reading the legacy .xls format requires xlrd. Install it with:\n"
            "  pip install 'xlrd<2.1'\n"
            "Or convert the file to .xlsx (open in LibreOffice/Excel, Save As)."
        )
        sys.exit(1)

    book = xlrd.open_workbook(path)
    sheet_names = book.sheet_names()
    if SHEET_NAME in sheet_names:
        sheet = book.sheet_by_name(SHEET_NAME)
    else:
        sheet = book.sheet_by_index(0)
        print(
            f"Warning: sheet '{SHEET_NAME}' not found in {path}; "
            f"using first sheet '{sheet.name}'. Available sheets: {sheet_names}"
        )
    rows: list[tuple] = []
    for row_index in range(sheet.nrows):
        rows.append(
            tuple(sheet.cell_value(row_index, col) for col in range(sheet.ncols))
        )
    return rows


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(
            "Usage: python cdisc_nsv_excel_converter.py <input.xls|.xlsx> [output.csv]"
        )
        sys.exit(1)

    excel_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) == 3 else DEFAULT_OUTPUT
    print(f"Reading CDISC NSV registry from '{excel_file}'")

    if not os.path.isfile(excel_file):
        print(f"Error: file not found: {excel_file}")
        sys.exit(1)

    ext = os.path.splitext(excel_file)[1].lower()
    if ext == ".xls":
        rows = _read_rows_xls(excel_file)
    else:
        rows = _read_rows_xlsx(excel_file)

    if not rows:
        print("Error: empty workbook")
        sys.exit(1)

    raw_headers = [normalise(str(h) if h is not None else "") for h in rows[0]]
    column_indexes: dict[str, int] = {}
    for index, header in enumerate(raw_headers):
        canonical = HEADER_MAP.get(header)
        if canonical and canonical not in column_indexes:
            column_indexes[canonical] = index

    missing = [c for c in OUTPUT_HEADERS if c not in column_indexes]
    if missing:
        print(
            "Warning: input is missing columns "
            f"{missing} - they will be written empty"
        )

    out_rows = []
    for raw_row in rows[1:]:
        if not any(cell is not None and str(cell).strip() for cell in raw_row):
            continue
        out_row = {}
        for canonical in OUTPUT_HEADERS:
            index = column_indexes.get(canonical)
            value = raw_row[index] if index is not None and index < len(raw_row) else ""
            out_row[canonical] = "" if value is None else str(value).strip()
        out_rows.append(out_row)

    with open(output_file, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=OUTPUT_HEADERS)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} rows to '{output_file}'")


if __name__ == "__main__":
    main()
