"""Enrich a CT diff with the rationale from CDISC's per-release change logs.

``changelog_fetch`` downloads the change-log spreadsheets; this reads them and
attaches matching rows onto the change records ``ct_diff.band_changes``
produces, so a diff entry can carry the request code, change type, summary and
CDISC's own implementation instructions alongside "what changed".

The change logs are not reliably complete, so this only ever annotates: an
unmatched change is left alone, an unmatched row is dropped, and a missing or
unreadable file downgrades to an unenriched step. Nothing here raises into the
diff, and nothing here touches the network.

Layering: only ``read_changelog_rows`` touches ``xlrd`` or the filesystem, and
it imports ``xlrd`` lazily, so importing this module costs a caller who never
enriches nothing. Everything below it is plain dicts and lists.

Three columns do the joining, all three measured against the 191 files held
locally rather than assumed:

1. **NCI Code** is the ``conceptId``. It names a term on most rows and a
   codelist on some, and the column itself does not say which - so the subject
   is taken from the change record being matched, never inferred from the row.
2. **CDISC Term Type** is not an entity type despite the name. Six of its nine
   values name the *field* that changed (``CDISC Definition``,
   ``NCI Preferred Term``, ...); only ``Term`` and ``CDISC Codelist`` describe
   an entity being added or removed. It is a far better field discriminator
   than the Change Summary text, which is free-form enough to have shipped
   "Add new term to new codelist." with a trailing period as a distinct value.
3. **CDISC Codelist (Short Name)** is the codelist's ``submissionValue``
   (1437 of 1447 rows resolved in 2025-03-28; submission values are unique
   within a package, so the join is unambiguous).

The one trap - see ``_subject_key`` - is that ``CDISC Codelist Name`` rows are
fanned out per member term.
"""

import logging
import os
import re

LOGGER = logging.getLogger("CDISC CT changelog annotate")

# Mirrors changelog_fetch.PACKAGE_FILE_RE. Duplicated rather than imported so
# this module - and so ct_diff, which imports it - never pulls in `requests`
# just to pick a date out of a filename.
PACKAGE_FILE_RE = re.compile(r"^(?P<catalogue>.+?)-(?P<date>\d{4}-\d{2}-\d{2})\.json$")

# Header text -> normalized row key. Columns whose header is absent from this
# map are ignored, which is also what makes the 12 ten-column files (published
# before "Change Implementation Instructions" existed) need no special case:
# the column is simply missing from the header map and the field stays None.
HEADER_ALIASES = {
    "Release Date": "release_date",
    "Request Code": "request_code",
    "Change Type": "change_type",
    "NCI Code": "nci_code",
    "CDISC Term Type": "term_type",
    "CDISC Codelist (Short Name)": "codelist_short_name",
    "CDISC Codelist (Long Name)": "codelist_long_name",
    "Change Summary": "change_summary",
    "Original": "original",
    "New": "new",
    "Change Implementation Instructions": "instructions",
}
ROW_FIELDS = tuple(HEADER_ALIASES.values())

# "- - -" is CDISC's not-applicable marker, used in Original on an addition.
PLACEHOLDER_VALUES = {"", "- - -", "---", "n/a", "N/A"}

MAX_HEADER_SCAN_ROWS = 10
MIN_HEADER_HITS = 6

# CDISC Term Type -> the ct_diff field it describes. The six field-valued term
# types; `Term` and `CDISC Codelist` are absent because they mark an entity
# being added or removed rather than a field changing.
TERM_TYPE_FIELD = {
    "CDISC Definition": "definition",
    "CDISC Synonym": "synonyms",
    "NCI Preferred Term": "preferredTerm",
    "CDISC Submission Value": "submissionValue",
    "CDISC Codelist Name": "name",
    "CDISC Extensible List": "extensible",
}

# Fallback when Term Type is one we have not seen: look for the field's name in
# the Change Summary. Substring and case-insensitive so that "Add new CDISC
# Synonym" and "Remove CDISC Synonym" both land on `synonyms`.
FIELD_KEYWORDS = {
    "definition": ("definition",),
    "synonyms": ("synonym",),
    "preferredTerm": ("preferred term",),
    "submissionValue": ("submission value",),
    "name": ("codelist name",),
    "extensible": ("extensible",),
}

# Change kind -> the Change Type values that can plausibly explain it.
KIND_CHANGE_TYPES = {
    "codelist_added": ("Add",),
    "codelist_removed": ("Remove",),
    "term_added": ("Add",),
    "term_removed": ("Remove",),
    "membership_added": ("Add",),
    "membership_removed": ("Remove",),
    "codelist_changed": ("Update",),
    "term_changed": ("Update",),
    "membership_changed": ("Update",),
}

# Term types whose subject is the codelist named by the Short Name column
# rather than the row's own NCI Code. See _subject_key.
CODELIST_SCOPED_TERM_TYPES = ("CDISC Codelist Name",)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def read_changelog_rows(path):
    """Parse one change-log .xls into a list of normalized row dicts.

    The only function here that touches xlrd or the disk. These are legacy BIFF
    files - openpyxl, used elsewhere in this component, cannot read them.
    """
    import xlrd  # pylint: disable=import-outside-toplevel

    return rows_from_book(xlrd.open_workbook(path))


def rows_from_book(book):
    """Rows from an open workbook.

    Split from read_changelog_rows so tests can pass a fake duck-typing the
    small part of xlrd's API used here, instead of committing a binary fixture.
    """
    sheet = _find_sheet(book)
    header_row, header_map = _find_header(sheet)

    rows = []
    for row_index in range(header_row + 1, sheet.nrows):
        row = dict.fromkeys(ROW_FIELDS)
        empty = True
        for col_index, key in header_map.items():
            value = _clean_cell(sheet, row_index, col_index)
            row[key] = value
            empty = empty and value is None
        if not empty:
            rows.append(row)
    return rows


def _find_sheet(book):
    """The catalogue's changes sheet, else the first sheet.

    Matched on a "Changes" suffix rather than an exact name: the sheet name
    does not always track the file name stem changelog_fetch builds URLs from
    (MRCT's file is "...Clinical Research Glossary Changes", its sheet is
    "MRCT Terminology Changes"). All 191 local files hold exactly one sheet, so
    the fallback is belt-and-braces.
    """
    for name in book.sheet_names():
        if name.strip().endswith("Changes"):
            return book.sheet_by_name(name)
    return book.sheet_by_index(0)


def _find_header(sheet):
    """Locate the header row. Returns (row index, {column index: row key}).

    Every local file has it at row 0, but scanning costs nothing and a title
    row above the header is a common spreadsheet habit.
    """
    for row_index in range(min(MAX_HEADER_SCAN_ROWS, sheet.nrows)):
        mapped = {}
        for col_index in range(sheet.ncols):
            text = str(sheet.cell_value(row_index, col_index)).strip()
            if text in HEADER_ALIASES:
                mapped[col_index] = HEADER_ALIASES[text]
        if len(mapped) >= MIN_HEADER_HITS:
            return row_index, mapped
    raise ValueError("No change-log header row found")


def _clean_cell(sheet, row_index, col_index):
    """One cell as a trimmed string, or None when empty or a placeholder.

    Release Date arrives as an Excel date serial in most files but as an
    already-formatted string in the oldest ones, so both are handled.
    """
    import xlrd  # pylint: disable=import-outside-toplevel

    cell = sheet.cell(row_index, col_index)
    if cell.ctype == xlrd.XL_CELL_DATE:
        datemode = getattr(getattr(sheet, "book", None), "datemode", 0)
        return xlrd.xldate.xldate_as_datetime(cell.value, datemode).date().isoformat()

    value = cell.value
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = str(value).strip() if value is not None else ""
    return None if text.lower() in {p.lower() for p in PLACEHOLDER_VALUES} else text


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------


def row_field(row):
    """The ct_diff field name a row describes, or None if it describes an
    entity being added or removed rather than a field change."""
    term_type = row.get("term_type")
    if term_type in TERM_TYPE_FIELD:
        return TERM_TYPE_FIELD[term_type]
    if term_type in ("Term", "CDISC Codelist"):
        return None

    summary = (row.get("change_summary") or "").lower()
    for field, keywords in FIELD_KEYWORDS.items():
        if any(keyword in summary for keyword in keywords):
            return field
    return None


def _subject_key(row):
    """The key a row should be indexed under: ("code", nci) or ("codelist", sv).

    Almost every row is about the concept its NCI Code names. `CDISC Codelist
    Name` rows are the exception: CDISC fans them out over every member term,
    so a single codelist rename shows up as one row per term, each carrying the
    *term's* NCI code while describing a change to the *codelist*. In
    sdtmct-2014-09-26 that is 392 rows for 4 renames. Indexing those by NCI
    code would hang "the codelist was renamed" off 388 terms that did not
    themselves change, so they are keyed by the codelist's short name instead.
    """
    if row.get("term_type") in CODELIST_SCOPED_TERM_TYPES:
        short_name = row.get("codelist_short_name")
        return ("codelist", short_name) if short_name else None
    nci_code = row.get("nci_code")
    return ("code", nci_code) if nci_code else None


def index_rows(rows):
    """Group rows by subject key. Rows with no usable key are dropped."""
    index = {}
    for row in rows:
        key = _subject_key(row)
        if key:
            index.setdefault(key, []).append(row)
    return index


def _dedupe(rows):
    """Collapse rows that would render identically.

    The per-term fan-out of a codelist rename yields hundreds of rows that
    differ only in NCI Code, which is not part of the annotation - without this
    a single rename would print its request code once per member term.
    """
    seen = set()
    unique = []
    for row in rows:
        marker = tuple(row.get(key) for key in ROW_FIELDS if key != "nci_code")
        if marker not in seen:
            seen.add(marker)
            unique.append(row)
    return unique


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------


def _narrow(rows, predicate):
    """Filter, but never down to nothing.

    Every narrowing step is a preference, not a gate: if no row satisfies it
    the candidates are returned untouched. A change annotated with several
    plausible rows is useful; one silently annotated with none is not.
    """
    filtered = [row for row in rows if predicate(row)]
    return filtered or rows


def _prefer_change_type(rows, kind):
    wanted = KIND_CHANGE_TYPES.get(kind)
    if not wanted:
        return rows
    return _narrow(rows, lambda row: row.get("change_type") in wanted)


def _prefer_field(rows, field):
    return _narrow(rows, lambda row: row_field(row) == field)


def _prefer_codelist(rows, short_name):
    if not short_name:
        return rows
    return _narrow(rows, lambda row: row.get("codelist_short_name") == short_name)


def _codelist_submission_value(pair_diff, cl_cid):
    codelist = (pair_diff.get("codelist_labels") or {}).get(cl_cid)
    return codelist.get("submissionValue") if codelist else None


def match_rows_for_change(
    index, change, pair_diff
):  # pylint: disable=too-many-return-statements
    """Change-log rows explaining one change record, best candidates first.

    Returns a list - a term added to three codelists is three rows - which is
    empty when nothing matches. Never raises: an unknown change kind returns
    no rows rather than failing the diff.

    One branch per change kind, mirroring ct_diff.change_cells, hence the
    return-count disable: collapsing them into a dispatch table would hide
    which narrowing steps apply to which kind, which is the whole content here.
    """
    kind = change.get("kind")

    def by_code(concept_id):
        return list(index.get(("code", concept_id), ()))

    if kind in ("codelist_added", "codelist_removed"):
        rows = by_code(change["codelist"]["conceptId"])
        return _dedupe(_prefer_change_type(rows, kind))

    if kind == "codelist_changed":
        field = change.get("field")
        rows = by_code(change["conceptId"])
        if field == "name":
            # Renames live under the short name, not the codelist's NCI code.
            rows += list(
                index.get(
                    ("codelist", (change.get("codelist") or {}).get("submissionValue")),
                    (),
                )
            )
        rows = _prefer_change_type(rows, kind)
        return _dedupe(_prefer_field(rows, field))

    if kind in ("term_added", "term_removed"):
        rows = by_code(change["term"]["conceptId"])
        return _dedupe(_prefer_change_type(rows, kind))

    if kind == "term_changed":
        rows = _prefer_change_type(by_code(change["conceptId"]), kind)
        return _dedupe(_prefer_field(rows, change.get("field")))

    if kind in ("membership_added", "membership_removed"):
        cl_cid, t_cid = change["key"]
        rows = _prefer_change_type(by_code(t_cid), kind)
        return _dedupe(
            _prefer_codelist(rows, _codelist_submission_value(pair_diff, cl_cid))
        )

    if kind == "membership_changed":
        cl_cid, t_cid = change["key"]
        rows = _prefer_change_type(by_code(t_cid), kind)
        rows = _prefer_codelist(rows, _codelist_submission_value(pair_diff, cl_cid))
        return _dedupe(_prefer_field(rows, change.get("field")))

    if kind == "term_moved":
        # Spans several codelists at once, so there is no single short name to
        # prefer by; this usually surfaces the paired remove and add rows.
        return _dedupe(by_code(change["move"]["conceptId"]))

    return []


# ---------------------------------------------------------------------------
# Report-level wiring
# ---------------------------------------------------------------------------


def default_changelog_dir():
    """``$CDISC_XLS_DIR/changelogs`` - where changelog_fetch writes by default.

    Shared by the ct_diff and site_gen CLIs so the location is defined once.
    """
    xls_dir = (os.environ.get("CDISC_XLS_DIR") or "").strip()
    return os.path.join(xls_dir, "changelogs") if xls_dir else None


def catalogue_and_date(source):
    """``sdtmct-2025-03-28.json`` -> ``("sdtmct", "2025-03-28")``, else Nones."""
    match = PACKAGE_FILE_RE.match(source or "")
    if not match:
        return None, None
    return match.group("catalogue"), match.group("date")


def annotate_pair(pair_diff, index):
    """Attach matching rows to every banded change in one pair diff, in place."""
    for changes in (pair_diff.get("bands") or {}).values():
        for change in changes:
            rows = match_rows_for_change(index, change, pair_diff)
            if rows:
                change["changelog"] = rows


def annotate_report(report, changelog_dir):
    """Attach change-log rows to every change in a report, in place.

    Each step is matched against exactly the release it describes: a change log
    for release D covers the step D-1 -> D, which is the step whose new package
    is D. The cumulative pair can span many releases, so it is matched against
    every intermediate release's rows combined.

    Call this **after ct_diff.build_report and before
    ct_diff_grouping.group_report**. Grouping copies a `term_moved` change as
    a new dict rather than by reference, so annotating afterwards would leave
    moved terms silently unenriched while every other kind looked fine.

    Degrades rather than failing: a missing directory, a release with no change
    log, or a file that will not parse each log a warning and leave the changes
    they would have covered untouched.
    """
    if not changelog_dir:
        # Not configured is a choice, not a problem: the diff is complete
        # without enrichment, so this is INFO where a missing directory - which
        # means someone asked for enrichment and will not get it - is a warning.
        LOGGER.info(
            "No change-log directory configured - the report will not be "
            "enriched. Set CDISC_XLS_DIR or pass --changelog-dir."
        )
        return report

    if not os.path.isdir(changelog_dir):
        LOGGER.warning(
            "No change-log directory at %s - the report will not be enriched",
            changelog_dir,
        )
        return report

    cache = {}

    def rows_for(catalogue, date):
        key = (catalogue, date)
        if key not in cache:
            cache[key] = _read_release(changelog_dir, catalogue, date)
        return cache[key]

    every_row = []
    for step in report.get("steps", []):
        catalogue, date = catalogue_and_date(step.get("new_source"))
        rows = rows_for(catalogue, date) if catalogue else []
        annotate_pair(step, index_rows(rows))
        every_row.extend(rows)

    if report.get("cumulative"):
        annotate_pair(report["cumulative"], index_rows(every_row))

    return report


def _read_release(changelog_dir, catalogue, date):
    path = os.path.join(changelog_dir, f"{catalogue}-{date}.xls")
    if not os.path.isfile(path):
        LOGGER.warning(
            "No change log for %s %s - that step stays unenriched", catalogue, date
        )
        return []
    try:
        return read_changelog_rows(path)
    except Exception as exc:  # pylint: disable=broad-except
        # Deliberately broad: xlrd raises several unrelated types on a damaged
        # file, and no parse failure is worth losing the whole diff over.
        LOGGER.warning("Could not read change log %s: %s", path, exc)
        return []


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def changelog_entries(rows):
    """One rendered string per change-log row behind a change.

    Request code and summary only. CDISC's implementation instructions are
    free text and only present on about one row in ten, so they stay in the
    JSON output rather than widening every row of an already dense report.

    Both columns are optional in practice - a fifth of all rows carry no
    request code, nearly all of them from 2014 and 2015 - so a row renders as
    whichever parts it has, and rows with neither are dropped. Returns an empty
    list when nothing is left to say, which callers should treat as "no
    change-log" rather than rendering an empty cell's worth of punctuation.

    A list rather than one joined string because a change can cite several
    requests, and the renderer puts each on its own line in the table cell.

    Deduplicated on the rendered text, in first-seen order. CDISC files one
    change-log row per affected codelist, so a term edited across five
    codelists matches five rows carrying the same request code and the same
    summary; a cell repeating one sentence five times says nothing the first
    one did not. Rows differing in either column are kept separately.
    """
    entries = []
    for row in rows:
        described = [
            part
            for part in (row.get("request_code"), row.get("change_summary"))
            if part
        ]
        if described:
            entries.append(": ".join(described))
    return list(dict.fromkeys(entries))
