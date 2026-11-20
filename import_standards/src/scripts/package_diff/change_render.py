"""Render one CT diff change record as a Markdown table row.

Split out of ct_diff so that module stays about loading, diffing and banding
packages, and this one is only about how a change looks once it reaches a page.
The flat report and every page of the review site render through here, so a
change reads the same wherever it is listed.

Nothing here imports ct_diff: a change record is a plain dict, and rendering one
needs no knowledge of how it was derived. That is what keeps the split honest.
"""

from src.scripts.package_diff.changelog_annotate import changelog_entries

# Definitions run to paragraphs. Long enough to recognise which one it is,
# short enough that a table row stays a row.
DEFINITION_TRUNCATE_AT = 200


def truncate(text, limit=DEFINITION_TRUNCATE_AT):
    if text is None:
        return "(none)"
    text = str(text)
    if len(text) <= limit:
        return text
    return text[:limit] + "… *(truncated)*"


def render_value(field, value):
    if value is None:
        return "(none)"
    if field == "synonyms":
        return "[" + ", ".join(f'"{s}"' for s in sorted(value)) + "]"
    if field == "definition":
        return f'"{truncate(value)}"'
    if isinstance(value, bool):
        return str(value)
    return f'"{value}"'


def _linked(text, cid, link):
    """Wrap a rendered label in a Markdown link when a link builder is given.

    `link` is a callable taking a conceptId and returning a URL, or None for the
    flat single-file report. A builder may return None to leave an individual
    reference unlinked - the multi-page site does that for codelists that have
    no page of their own because nothing about them changed.
    """
    if link is None:
        return text
    href = link(cid)
    return f"[{text}]({href})" if href else text


def label_codelist(pair_diff, cl_cid, link=None):
    codelist = pair_diff["codelist_labels"].get(cl_cid)
    if not codelist:
        return _linked(f"`{cl_cid}`", cl_cid, link)
    return _linked(f'`{cl_cid}` "{codelist.get("name")}"', cl_cid, link)


def label_term(pair_diff, t_cid, link=None):
    term = pair_diff["term_labels"].get(t_cid)
    if not term:
        return _linked(f"`{t_cid}`", t_cid, link)
    return _linked(f'`{t_cid}` "{term.get("preferredTerm")}"', t_cid, link)


# ---------------------------------------------------------------------------
# Change tables
# ---------------------------------------------------------------------------
#
# Every change renders as a table row rather than a sentence. A CDISC release is
# thousands of near-identical facts, and prose buries the only thing a reviewer
# does with them: read one column - which term, which property, what the value
# became - straight down the list. Fixed columns make that possible; a list of
# sentences, however carefully worded, does not.

# What to call each table when a category holds more than one kind of change. A
# lone table needs no caption - the heading above it already names the category.
KIND_TABLE_TITLE = {
    "codelist_added": "Codelists added",
    "codelist_removed": "Codelists removed",
    "codelist_changed": "Codelist properties changed",
    "term_added": "Terms added to the catalogue",
    "term_removed": "Terms removed from the catalogue",
    "term_changed": "Term properties changed",
    "membership_added": "Terms added to codelists",
    "membership_removed": "Terms removed from codelists",
    "membership_changed": "Submission values changed",
    "term_moved": "Terms moved between codelists",
}


def table_cell(text):
    """Make a rendered value safe to drop into a Markdown table cell.

    Definitions are free text straight out of the package: they contain pipes,
    and they contain newlines. Either one silently breaks the table - a pipe
    invents a column, a newline ends the row - so both are neutralized here
    rather than trusted not to occur. The `<br>` separators that `cell_join`
    puts in survive untouched: they are the one intended way a cell holds more
    than one line.
    """
    return str(text).replace("|", "\\|").replace("\r\n", "\n").replace("\n", "<br>")


def cell_join(parts):
    """Stack several values in one cell, one per line.

    A comma-separated run of quoted synonyms, or of codelist links, is
    unreadable at any column width. Markdown tables take no real line break, so
    `<br>` is how a cell gets one. Empty parts are dropped rather than rendered
    as a blank line.
    """
    return "<br>".join(str(part) for part in parts if part)


def render_cell_value(field, value):
    """`render_value`, except a multi-valued field gets a line per value."""
    if field == "synonyms":
        return cell_join(f'"{synonym}"' for synonym in sorted(value or ())) or "(none)"
    return render_value(field, value)


def _codelist_cell(pair_diff, cl_cid, link, context_codelist):
    """A codelist reference, blank when it is the page's own codelist.

    Blank rather than "this codelist": a column blank on every row is dropped
    from the table entirely, which is how a per-codelist page stops repeating
    its own name down a column that would say nothing else.
    """
    if cl_cid == context_codelist:
        return ""
    return label_codelist(pair_diff, cl_cid, link)


def _codelists_cell(pair_diff, cl_cids, link, context_codelist):
    """Several codelists in one cell, a line each, the current one named."""
    return cell_join(
        (
            "**this codelist**"
            if cl_cid == context_codelist
            else label_codelist(pair_diff, cl_cid, link)
        )
        for cl_cid in cl_cids
    )


def _membership_cells(pair_diff, change, link_codelist, link_term, context_codelist):
    """A term joining, leaving or changing submission value inside one codelist.

    A membership change may carry ``catalogue_new`` / ``catalogue_gone``, stamped
    on by the grouping layer when it drops the catalogue-wide ``term_added`` /
    ``term_removed`` record as a duplicate. Whether a term is brand new or was
    already defined elsewhere changes what a reviewer has to check, so that fact
    is carried over rather than lost. The flat report has both records and
    stamps neither flag, so its Catalogue column drops out as empty.
    """
    cl_cid, t_cid = change["key"]
    cells = {
        "Term": label_term(pair_diff, t_cid, link_term),
        "Codelist": _codelist_cell(pair_diff, cl_cid, link_codelist, context_codelist),
    }
    if change["kind"] == "membership_added":
        cells["Catalogue"] = (
            "new in this package" if change.get("catalogue_new") else ""
        )
    elif change["kind"] == "membership_removed":
        cells["Catalogue"] = (
            "removed from the catalogue" if change.get("catalogue_gone") else ""
        )
    else:
        cells["Before"] = render_cell_value("submissionValue", change["old"])
        cells["After"] = render_cell_value("submissionValue", change["new"])
    return cells


def change_cells(
    pair_diff, change, link_codelist=None, link_term=None, context_codelist=None
):
    """The columns of one change, in display order. Column name -> cell text.

    The single place that says what each change kind *is*. Keys are the table
    headers, so every record of a kind yields the same keys in the same order.

    link_codelist / link_term default to None, giving the flat report's
    unlinked text. The multi-page site passes builders so concept references
    become links to the relevant codelist page.

    context_codelist names the codelist the rows are being rendered *under*.
    References to it come back blank, and the table then drops the column.
    """
    kind = change["kind"]

    if kind in ("codelist_added", "codelist_removed"):
        # The embedded dict, not the label lookup: for a codelist that exists on
        # one side only this record is the authoritative description of it.
        codelist = change["codelist"]
        cl_cid = codelist["conceptId"]
        return {
            "Codelist": (
                ""
                if cl_cid == context_codelist
                else _linked(
                    f'`{cl_cid}` "{codelist.get("name")}"', cl_cid, link_codelist
                )
            ),
            "Submission value": f'`{codelist.get("submissionValue")}`',
        }
    if kind == "codelist_changed":
        field = change["field"]
        return {
            "Codelist": _codelist_cell(
                pair_diff, change["conceptId"], link_codelist, context_codelist
            ),
            "Property": f"`{field}`",
            "Before": render_cell_value(field, change["old"]),
            "After": render_cell_value(field, change["new"]),
        }

    if kind in ("term_added", "term_removed"):
        term = change["term"]
        return {"Term": f'`{term["conceptId"]}` "{term.get("preferredTerm")}"'}
    if kind == "term_changed":
        field = change["field"]
        return {
            "Term": label_term(pair_diff, change["conceptId"], link_term),
            "Property": f"`{field}`",
            "Before": render_cell_value(field, change["old"]),
            "After": render_cell_value(field, change["new"]),
        }

    if kind in ("membership_added", "membership_removed", "membership_changed"):
        return _membership_cells(
            pair_diff, change, link_codelist, link_term, context_codelist
        )
    if kind == "term_moved":
        move = change["move"]
        return {
            "Term": label_term(pair_diff, move["conceptId"], link_term),
            "Left": _codelists_cell(
                pair_diff, move["left"], link_codelist, context_codelist
            ),
            "Entered": _codelists_cell(
                pair_diff, move["entered"], link_codelist, context_codelist
            ),
        }

    raise ValueError(f"Unknown change kind: {kind}")


def render_change_table(
    pair_diff, changes, link_codelist=None, link_term=None, context_codelist=None
):
    """Render change records as Markdown table lines. Empty input, no lines.

    Every renderer goes through here, so a change annotated by
    ``changelog_annotate.annotate_report`` carries CDISC's request code and
    change summary into the flat report and the site alike, one request per
    line of the cell. The free-text implementation instructions stay out of the
    table and in the JSON: they run to paragraphs.

    One table per change kind, in first-seen order. Kinds have genuinely
    different columns, and forcing them into one table would mean columns that
    are blank for most rows; a category almost always holds a single kind, so
    the split rarely shows at all.

    A column blank on every row is dropped rather than printed empty - an
    unannotated diff has no change-log column at all, and a codelist page has no
    column repeating its own name.
    """
    groups = {}
    for change in changes:
        cells = change_cells(
            pair_diff, change, link_codelist, link_term, context_codelist
        )
        cells["Change log"] = cell_join(
            changelog_entries(change.get("changelog") or ())
        )
        groups.setdefault(change["kind"], []).append(cells)

    lines = []
    for kind, rows in groups.items():
        columns = [
            name
            for name in dict.fromkeys(name for row in rows for name in row)
            if any(row.get(name) for row in rows)
        ]
        if len(groups) > 1:
            lines += [f"**{KIND_TABLE_TITLE.get(kind, kind)}**", ""]
        lines.append("| " + " | ".join(columns) + " |")
        lines.append("|" + "---|" * len(columns))
        for row in rows:
            lines.append(
                "| "
                + " | ".join(table_cell(row.get(name, "")) for name in columns)
                + " |"
            )
        lines.append("")
    return lines
