"""Render a grouped CT diff as Markdown pages for a static site.

Strings only - this module writes no files and imports nothing from mkdocs, so
the Markdown stays the deliverable and the site generator stays swappable.

Everything here renders changes and nothing else. Codelists without changes have
no bucket and so no page, and an empty category is omitted rather than printed
as a "(none)" heading: on a per-codelist page most categories are empty, and
across hundreds of pages that filler is most of the text.

Pages name the change rather than grade it - "Terms removed from a codelist",
not "S1 Structural". Order still runs most-disruptive-first, because a reviewer
needs somewhere to start, but no page tells them what to conclude.
"""

import re

from src.scripts.package_diff.change_render import (
    cell_join,
    label_term,
    render_cell_value,
    render_change_table,
    table_cell,
)
from src.scripts.package_diff.ct_diff import (
    EXTENSIBLE_ADDITION_LEVEL,
    SEVERITIES,
    render_counts_table,
    step_title,
)
UNSAFE_IN_SLUG = re.compile(r"[^A-Za-z0-9_.-]")

# Where per-codelist pages live, relative to docs/. Every page outside that
# directory links into it with this prefix.
CODELIST_DIR = "codelists/"

# Keep the flat report out of the client-side search index. It restates what the
# per-codelist pages already say, so indexing it only duplicates every hit and
# doubles what the browser downloads: on the 3.5-year diff the index goes from
# 9.3 MB to 2.4 MB. The page itself stays fully browsable.
SEARCH_EXCLUDE = "---\nsearch:\n  exclude: true\n---\n\n"

# Categories that can invalidate data an earlier import already wrote, each with
# the page it gets. The remaining categories - new codelists and terms, and
# property updates - are real changes, but nothing already in the database stops
# resolving because of them, so they appear on codelist pages only.
IMPACT_PAGES = {
    1: "codelists-removed.md",
    2: "terms-removed-from-catalogue.md",
    3: "terms-removed-from-codelist.md",
    4: "submission-values-changed.md",
    5: "terms-added-to-extensible-codelists.md",
    6: "terms-moved-between-codelists.md",
}
IMPACT_BANDS = tuple(IMPACT_PAGES)

# Why each category matters, in the reviewer's terms rather than the diff's.
IMPACT_INTRO = {
    1: "These codelists no longer exist. Study data still referencing one has "
    "nothing left to resolve against.",
    2: "These terms are gone from the catalogue entirely — not just from one "
    "codelist. Nothing resolves against them any more, anywhere.",
    3: "These terms still exist, but no longer belong to the codelist they are "
    "listed under. Data recorded against that pairing no longer matches, even "
    "though the term itself is fine.",
    4: "The value that gets written to a submission changed. Data captured "
    "before this import still carries the old value.",
    5: "CDISC added a term to a codelist that already existed and that the "
    "sponsor was already allowed to extend. This is the only band where an "
    "addition can land on a sponsor-defined term already in your database. "
    "Whether it actually does is a question no offline diff can answer — the "
    "standards import API does, as its sponsor impact assessment. Terms arriving "
    "in a codelist nobody could extend, or in one this package introduces, "
    "cannot collide and are listed separately.",
    6: "A term left one codelist and entered another. Nothing was added or "
    "deleted catalogue-wide, but both codelists changed shape, so anything "
    "pinned to the old pairing needs revisiting.",
}


def slug_for(cl_cid):
    """Filesystem and URL safe page name. CDISC conceptIds are already
    alphanumeric ("C66741"); sanitize anyway so a malformed package cannot write
    outside the output directory."""
    return UNSAFE_IN_SLUG.sub("_", str(cl_cid))


def codelist_page_path(cl_cid):
    return f"{CODELIST_DIR}{slug_for(cl_cid)}.md"


def codelist_link(grouped, prefix, available=None):
    """Build a link function for `change_render.render_change_table`.

    Returns None for any codelist without a page, so no reference ever 404s.
    Two separate reasons a page can be missing: the codelist did not change (so
    it has no bucket), or --max-codelist-pages cut it. ``available`` carries the
    second - pass the set of conceptIds actually written; None means all of them.
    """
    pages = grouped["codelists"] if available is None else available

    def link(cl_cid):
        if cl_cid not in pages:
            return None
        return f"{prefix}{slug_for(cl_cid)}.md"

    return link


def render_bands(pair_diff, bands, link, context=None, heading_level="##"):
    """Render non-empty categories as tables. Empty ones produce nothing at all."""
    lines = []
    for level, band_name in SEVERITIES.items():
        changes = bands.get(level) or []
        if not changes:
            continue
        lines.append(f"{heading_level} {band_name} ({len(changes)})")
        lines.append("")
        lines.extend(
            render_change_table(
                pair_diff, changes, link_codelist=link, context_codelist=context
            )
        )
    return lines


def render_codelist_page(pair_diff, bucket, grouped, available=None):
    """One codelist's changes, most severe band first."""
    link = codelist_link(grouped, prefix="", available=available)
    status = {
        "added": " — codelist added in this release",
        "removed": " — **codelist removed in this release**",
    }.get(bucket["entity_status"], "")

    lines = [
        f'# {bucket["label"]}{status}',
        "",
        f'{bucket["counts"]["total"]} change(s) between '
        f'`{pair_diff["old_source"]}` and `{pair_diff["new_source"]}`.',
        "",
    ]
    lines.extend(
        render_bands(pair_diff, bucket["bands"], link, context=bucket["conceptId"])
    )
    return "\n".join(lines).rstrip() + "\n"


def _categories_in(bucket):
    """Names of the categories this codelist actually has changes in."""
    return [name for level, name in SEVERITIES.items() if bucket["counts"][level]]


def render_codelists_index_page(grouped, available=None):
    """Table of changed codelists. The browse surface for the site.

    Names the categories each codelist falls into rather than grading it. The
    rows are still ordered most-disruptive-first, because some order is needed
    and that one is useful, but the page states no verdict: which of these
    matters is the reviewer's call, and they may well not share ours.

    Every changed codelist gets a row even when --max-codelist-pages cut its
    page: the count is the honest answer to "what changed", and a row without a
    link is better than a row that is missing or one that 404s.
    """
    lines = [
        "# Changed codelists",
        "",
        f'{len(grouped["order"])} codelist(s) changed. Codelists with no changes '
        "are not listed.",
        "",
        "Ordered with the most disruptive categories first, and labelled with "
        "what actually changed, so you can judge the impact for yourself.",
        "",
        "| Codelist | Changes | What changed |",
        "|---|---:|---|",
    ]
    link = codelist_link(grouped, prefix="", available=available)
    for cl_cid in grouped["order"]:
        bucket = grouped["codelists"][cl_cid]
        href = link(cl_cid)
        name = f'[{bucket["label"]}]({href})' if href else bucket["label"]
        lines.append(
            f'| {name} | {bucket["counts"]["total"]} '
            f"| {cell_join(_categories_in(bucket))} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_impact_page(pair_diff, grouped, level, available=None):
    """Every change in one category, a table per codelist.

    These categories are what can invalidate data an earlier import wrote, so
    they get their own read-this-first pages rather than being buried per
    codelist. The page cap never trims them: they are listed in full whether or
    not their codelist got a page of its own.

    Still one section per codelist rather than a single table with a codelist
    column: a change touching several codelists is filed under each, so a flat
    table would repeat rows that no longer say which codelist they were listed
    for. The heading carries that, and each table then leaves it out.
    """
    band_name = SEVERITIES[level]
    link = codelist_link(grouped, prefix=CODELIST_DIR, available=available)
    affected = [
        cl_cid
        for cl_cid in grouped["order"]
        if grouped["codelists"][cl_cid]["counts"][level]
    ]
    total = sum(grouped["codelists"][c]["counts"][level] for c in affected)

    lines = [f"# {band_name}", ""]
    intro = IMPACT_INTRO.get(level)
    if intro:
        lines += [intro, ""]
    if not affected:
        lines += [f"Nothing in this diff: {band_name.lower()} — none.", ""]
        return "\n".join(lines)

    distinct = grouped["distinct_counts"][level]
    lines += [
        f"{distinct} change(s) affecting {len(affected)} codelist(s).",
        "",
    ]
    if total > distinct:
        # A term can belong to several codelists, so one removal is listed under
        # each of them. Say so rather than let the rows appear to disagree
        # with the count above.
        lines += [
            f"Listed {total} times below: a term in several codelists appears "
            "under each one.",
            "",
        ]
    for cl_cid in affected:
        bucket = grouped["codelists"][cl_cid]
        # link(), not codelist_page_path(): under a cap this codelist may have
        # no page even though its changes are listed here in full.
        href = link(cl_cid)
        heading = f'[{bucket["label"]}]({href})' if href else bucket["label"]
        lines.append(f'## {heading} ({bucket["counts"][level]})')
        lines.append("")
        lines.extend(
            render_change_table(
                pair_diff,
                bucket["bands"][level],
                link_codelist=link,
                context_codelist=cl_cid,
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def new_codelists_in(grouped):
    """Codelists absent from the old package entirely, in worst-first order.

    Returns ``(conceptId, bucket, codelist)`` triples. The codelist dict comes
    off the ``codelist_added`` record, which carries the new package's version.
    """
    found = []
    for cl_cid in grouped["order"]:
        bucket = grouped["codelists"][cl_cid]
        if bucket["entity_status"] != "added":
            continue
        codelist = next(
            (
                change["codelist"]
                for band in bucket["bands"].values()
                for change in band
                if change["kind"] == "codelist_added"
            ),
            {},
        )
        found.append((cl_cid, bucket, codelist))
    return found


def _added_codelist_change(bucket):
    """The ``codelist_added`` record behind one new-codelist bucket.

    Needed because this page builds its table by hand rather than through
    ``render_change_table``, so the sponsor verdict has to be read off the
    record directly.
    """
    return next(
        (
            change
            for band in bucket["bands"].values()
            for change in band
            if change["kind"] == "codelist_added"
        ),
        {},
    )


def _added_term_count(bucket):
    """Terms the diff puts into this codelist. For a brand new codelist that is
    every term it has, since none of its memberships existed before."""
    return sum(
        1
        for band in bucket["bands"].values()
        for change in band
        if change["kind"] == "membership_added"
    )


# Per-column alignment for the new-codelists table. Kept beside the builder
# because the column set is now conditional - a fixed separator string would
# silently mis-align the moment the Sponsor column is dropped.
NEW_CODELIST_ALIGN = {
    "Codelist": "---",
    "Submission value": "---",
    "Extensible": "---",
    "Terms": "---:",
    "Sponsor": "---",
}


def render_new_codelists_page(grouped, available=None):
    """Codelists this package introduces.

    Lower risk than a term arriving in an extensible codelist: one that did not
    exist cannot have been extended, so none of its terms can collide with a
    sponsor-defined one. What can still collide is the *codelist itself* - a
    sponsor may already have defined one covering the same ground under their own
    conceptId, which no package diff can see.

    That is not a question a package diff can answer, so this page is a
    worklist: check each row below against the sponsor-defined codelists in the
    database you are importing into.
    """
    new_codelists = new_codelists_in(grouped)
    lines = ["# New codelists", ""]
    if not new_codelists:
        lines += ["This package introduces no new codelists.", ""]
        return "\n".join(lines)

    lines += [
        f"{len(new_codelists)} codelist(s) are new in this package. Their terms "
        "cannot collide with sponsor-defined terms, because there was nothing to "
        "extend — they are listed separately from [terms added to extensible "
        f"codelists]({IMPACT_PAGES[5]}) for that reason.",
        "",
    ]
    lines += [
        "What still needs checking is whether a sponsor-defined codelist already "
        "covers the same ground. That is rare, but importing a duplicate of one is "
        "expensive to unpick, so confirm each row below against the sponsor-defined "
        "codelists in the database you are importing into.",
        "",
    ]
    rows = []
    link = codelist_link(grouped, prefix=CODELIST_DIR, available=available)
    for cl_cid, bucket, codelist in new_codelists:
        href = link(cl_cid)
        name = f'[{bucket["label"]}]({href})' if href else bucket["label"]
        rows.append(
            {
                "Codelist": name,
                "Submission value": f'`{codelist.get("submissionValue") or "—"}`',
                "Extensible": "yes" if codelist.get("extensible") else "no",
                "Terms": str(_added_term_count(bucket)),
            }
        )

    # Same rule the change tables follow: a column blank on every row is dropped
    # rather than printed empty, so an unannotated run renders as it always did.
    columns = [name for name in rows[0] if any(row.get(name) for row in rows)]
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("|" + "|".join(NEW_CODELIST_ALIGN[name] for name in columns) + "|")
    for row in rows:
        lines.append(
            "| " + " | ".join(table_cell(row[name]) for name in columns) + " |"
        )
    lines.append("")
    return "\n".join(lines)


def render_term_attribute_changes_page(pair_diff, grouped, available=None):
    """Term attribute changes, listed once with every codelist they reach.

    A term is deduplicated catalogue-wide, so one definition edit shows up on
    every codelist page holding that term. This page is the de-duplicated view.

    Its own table rather than `render_change_table`: the extra column is the set
    of codelists the term lives in, which is a property of the grouping and not
    of the change record, so no shared row builder can know it.
    """
    changes = grouped["term_attribute_changes"]
    lines = ["# Term attribute changes", ""]
    if not changes:
        lines += ["No codelist-independent term attribute changes.", ""]
        return "\n".join(lines)

    lines += [
        f"{len(changes)} change(s) to term attributes (definition, preferred "
        "term, synonyms). Each affects every codelist listed beside it.",
        "",
        "| Term | Property | Before | After | Codelists |",
        "|---|---|---|---|---|",
    ]
    link = codelist_link(grouped, prefix=CODELIST_DIR, available=available)
    for change in changes:
        # A line per codelist: a term can sit in a dozen, and a comma-separated
        # run of them makes the row unreadable at any width.
        homes = cell_join(
            (
                f"[{grouped['codelists'][cl]['label']}]({link(cl)})"
                if link(cl)
                else grouped["codelists"].get(cl, {}).get("label", cl)
            )
            for cl in change["codelists"]
        )
        field = change["field"]
        lines.append(
            "| "
            + " | ".join(
                table_cell(value)
                for value in (
                    label_term(pair_diff, change["conceptId"]),
                    f"`{field}`",
                    render_cell_value(field, change["old"]),
                    render_cell_value(field, change["new"]),
                    homes,
                )
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def render_overview_page(report, grouped, capped=None, available=None):
    """Landing page: what was compared, and where the risk is."""
    order = grouped["order"]

    lines = ["# CDISC CT package diff", ""]

    if len(report["catalogues"]) > 1:
        lines += [
            '!!! danger "Mixed catalogues"',
            "    The input files are not all from the same catalogue ("
            + ", ".join(report["catalogues"])
            + "). This diff is almost certainly meaningless.",
            "",
        ]
    else:
        lines += [f'Catalogue: **{report["catalogues"][0]}**', ""]

    lines += [f'Generated: {report["generated"]}', ""]

    lines += [
        "## Compared",
        "",
        "| # | Package | effectiveDate | Version | Codelists | Terms | Memberships |",
        "|---:|---|---|---|---:|---:|---:|",
    ]
    for index, package in enumerate(report["packages"], start=1):
        counts = package["counts"]
        lines.append(
            f'| {index} | `{package["source"]}` | {package["effectiveDate"]} '
            f'| {package["version"]} | {counts["codelists"]} | {counts["terms"]} '
            f'| {counts["memberships"]} |'
        )
    lines.append("")

    # The shortlist. Most changes in a CDISC release are additions to codelists
    # nobody had extended, which cannot collide with anything; the categories
    # below are the ones worth a human.
    lines += ["## What changed", ""]
    total_codelists = report["packages"][-1]["counts"]["codelists"]
    lines.append(
        f"**{len(order)}** of {total_codelists} codelists changed. "
        "Codelists with no changes are excluded from this site."
    )
    lines += ["", "| Category | Changes | Codelists |", "|---|---:|---:|"]
    for level, page in IMPACT_PAGES.items():
        affected = [c for c in order if grouped["codelists"][c]["counts"][level]]
        changes = grouped["distinct_counts"][level]
        lines.append(
            f"| **[{SEVERITIES[level]}]({page})** | {changes} | {len(affected)} |"
        )
    new_codelists = new_codelists_in(grouped)
    lines.append(
        f"| **[New codelists](new-codelists.md)** | {len(new_codelists)} "
        f"| {len(new_codelists)} |"
    )
    lines += [
        "",
        "New codelists are low risk — nothing could have been extended before "
        "they existed — but each one still has to be checked against "
        "sponsor-defined codelists.",
        "",
    ]

    if capped:
        shown, total = capped
        lines += [
            '!!! warning "Output capped"',
            f"    {shown} of {total} changed codelists have pages "
            "(`--max-codelist-pages`). The remainder are still complete in "
            "[the full flat report](full-report.md) and `full-report.json`.",
            "",
        ]

    lines += ["## Summary counts", ""]
    lines.extend(render_counts_table(report))
    lines += [
        "",
        # The table is the raw flat-diff record count, which is deliberately
        # larger: deleting a term catalogue-wide emits one record for the term
        # plus one per codelist that held it. The pages above state each fact
        # once, so the two will not match and a reader should know why.
        "Counts above are raw diff records. A term removed from several "
        "codelists is recorded once catalogue-wide *and* once per codelist, so "
        "these totals run higher than the change counts on the pages above.",
        "",
        "## Browse",
        "",
        "| Page | What it holds |",
        "|---|---|",
        "| [Changed codelists](codelists/index.md) | Every changed codelist, "
        "labelled with what changed |",
        "| [Term attribute changes](term-attribute-changes.md) | Definition, "
        "preferred term and synonym edits, listed once per term |",
        "| [Full flat report](full-report.md) | The complete, uncapped diff |",
        "",
    ]
    return "\n".join(lines)


def build_mkdocs_config(report, site_name=None):
    """Generate mkdocs.yml as text.

    Written by hand rather than with yaml.dump so this module keeps no
    dependency on the site generator at all. Nav lists index pages only - one
    entry per codelist would be hundreds of entries.
    """
    if site_name is None:
        catalogue = (
            report["catalogues"][0] if len(report["catalogues"]) == 1 else "CDISC CT"
        )
        site_name = f'{catalogue} diff: {step_title(report["cumulative"])}'

    escaped = site_name.replace('"', '\\"')
    # Built from the same mapping the pages are written from, so a category
    # cannot be renamed in one place and left stale in the nav.
    impact_nav = "\n".join(
        f'      - "{SEVERITIES[level]}": {page}' for level, page in IMPACT_PAGES.items()
    )
    return f"""site_name: "{escaped}"
docs_dir: docs
theme:
  name: material
  features:
    - navigation.instant
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy
markdown_extensions:
  - admonition
  - tables
  - attr_list
  # Collapsible `???` blocks, for the sponsor-defined term listings. Ships with
  # mkdocs-material, so it costs no extra dependency.
  - pymdownx.details
nav:
  - Overview: index.md
  - What changed:
{impact_nav}
      - "New codelists": new-codelists.md
  - Changed codelists: codelists/index.md
  - Term attribute changes: term-attribute-changes.md
  - Full flat report: full-report.md
"""
