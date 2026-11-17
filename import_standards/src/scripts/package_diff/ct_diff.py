"""Diff CDISC controlled terminology package JSON files across versions.

Standalone and fully offline: reads raw package JSON from disk and reports what
changed between consecutive releases of one catalogue, ordered by severity.
No Neo4j, no API, no network.

Codelists and terms are both identified by their conceptId. A term's submission
value depends on which codelist it sits in, so term attributes and term-codelist
relationships are diffed separately.
"""

import argparse
import datetime
import json
import logging
import os
from collections import defaultdict
from os import environ

from src.scripts.package_diff.change_render import render_change_table
from src.scripts.package_diff.changelog_annotate import (
    annotate_report,
    default_changelog_dir,
)


def get_logger():
    loglevel = environ.get("LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        print(f"Invalid log level: {loglevel}, defaulting to INFO")
        numeric_level = logging.INFO
    logging.basicConfig()
    logger = logging.getLogger("CDISC package diff")
    logger.setLevel(numeric_level)
    return logger


LOGGER = get_logger()

# Fields compared per entity kind. A term's submissionValue is deliberately absent
# here: it belongs to the term-codelist relationship, not to the term.
CODELIST_FIELDS = (
    "name",
    "definition",
    "preferredTerm",
    "submissionValue",
    "extensible",
    "synonyms",
)
TERM_FIELDS = ("definition", "preferredTerm", "synonyms")

# Change categories, ordered by how much trouble each can cause an import that
# already happened. The order is what makes a diff reviewable - a reader can
# stop once it stops mattering - but the *names* are what a reader sees, so they
# describe the change itself rather than an abstract severity grade.
#
# Additions are cut four ways because "something was added" is the bulk of any
# CDISC release and lumping it together hides the only part that needs a human.
# Two independent questions decide which: did the codelist already exist, and
# could the sponsor already have extended it?
#
#                        | already extensible | not extensible
#     existing codelist  |         5          |       7
#     new codelist       |         9          |       9
#
# Only 5 can collide with a sponsor-defined term of the same name or submission
# value. A codelist nobody could extend has no sponsor terms in it, and one this
# package introduces did not exist to be extended - so for a new codelist the
# extensibility question has no answer worth acting on and the two collapse.
#
# The other non-obvious split is a term gone from the catalogue (2) versus one
# that merely left a codelist (3). The first resolves against nothing anywhere;
# the second still exists, just not where it was.
SEVERITIES = {
    1: "Codelists removed",
    2: "Terms removed from the catalogue",
    3: "Terms removed from a codelist",
    4: "Submission values changed",
    5: "Terms added to existing extensible codelists",
    6: "Terms moved between codelists",
    7: "Terms added to existing non-extensible codelists",
    8: "New codelists",
    9: "Terms added to new codelists",
    10: "New terms in the catalogue",
    11: "Codelist names and descriptions updated",
    12: "Term names and descriptions updated",
}

# The one band whose additions could land on a sponsor-defined term: CDISC added a
# term to a codelist that already existed and that the sponsor was already allowed
# to extend. Band 7 (nobody could extend it) and band 9 (the codelist is new in this
# package) cannot. Named rather than written as a bare 5 because the site keys off it.
EXTENSIBLE_ADDITION_LEVEL = 5

# Which category a changed field falls into. Anything not listed is a plain
# property update - a name, a preferred term, a definition, a synonym list.
FIELD_SEVERITY = {
    "submissionValue": 4,
}

# Property updates are split by what was edited, because the two are reviewed by
# different people: a codelist rename is a catalogue-structure question, a term
# definition reword is a clinical one. Keyed by change kind rather than derived,
# since a term can never carry a submissionValue (see TERM_FIELDS) while a
# codelist can, and that one field leaves the property categories entirely.
PROPERTY_UPDATE = {
    "codelist_changed": 11,
    "term_changed": 12,
}

# ---------------------------------------------------------------------------
# Loading and normalization
# ---------------------------------------------------------------------------


def resolve_path(name, json_dir):
    """Return name as given if it exists, else resolve it against json_dir."""
    if os.path.isfile(name):
        return name
    if json_dir:
        candidate = os.path.join(json_dir, name)
        if os.path.isfile(candidate):
            return candidate
    raise FileNotFoundError(f"Package file not found: {name}")


def normalize_codelist(raw_cl):
    return {
        "conceptId": raw_cl["conceptId"],
        "name": raw_cl.get("name"),
        "definition": raw_cl.get("definition"),
        "preferredTerm": raw_cl.get("preferredTerm"),
        "submissionValue": raw_cl.get("submissionValue"),
        "extensible": raw_cl.get("extensible") == "true",
        "synonyms": frozenset(raw_cl.get("synonyms") or []),
    }


def normalize_term(raw_term):
    """Codelist-independent term attributes only."""
    return {
        "conceptId": raw_term["conceptId"],
        "definition": raw_term.get("definition"),
        "preferredTerm": raw_term.get("preferredTerm"),
        "synonyms": frozenset(raw_term.get("synonyms") or []),
    }


def normalize_package(raw, source=None):
    """Split one parsed package JSON into codelists, terms and memberships.

    Terms are deduplicated catalogue-wide by conceptId. A term appearing in
    several codelists yields one term entry and one membership entry per codelist.
    """
    codelists = {}
    terms = {}
    memberships = {}
    term_homes = defaultdict(list)

    for raw_cl in raw.get("codelists") or []:
        cl_cid = raw_cl["conceptId"]
        if cl_cid in codelists:
            LOGGER.warning(
                "Duplicate codelist conceptId %s in %s, keeping the first",
                cl_cid,
                source or raw.get("name"),
            )
        else:
            codelists[cl_cid] = normalize_codelist(raw_cl)

        for raw_term in raw_cl.get("terms") or []:
            t_cid = raw_term["conceptId"]
            term = normalize_term(raw_term)
            term_homes[t_cid].append(cl_cid)
            existing = terms.get(t_cid)
            if existing is None:
                terms[t_cid] = term
            elif existing != term:
                # Should not happen within one catalogue. cdisc_staging.py carries a
                # whole inconsistency subsystem because it does happen across them.
                differing = [f for f in TERM_FIELDS if existing[f] != term[f]]
                LOGGER.warning(
                    "Term %s has conflicting %s across codelists %s in %s "
                    "- keeping the value from %s",
                    t_cid,
                    ", ".join(differing),
                    ", ".join(term_homes[t_cid]),
                    source or raw.get("name"),
                    term_homes[t_cid][0],
                )
            memberships[(cl_cid, t_cid)] = raw_term.get("submissionValue")

    return {
        "source": source,
        "name": raw.get("name"),
        "effectiveDate": raw.get("effectiveDate"),
        "version": raw.get("version"),
        "codelists": codelists,
        "terms": terms,
        "memberships": memberships,
    }


def load_package(path):
    with open(path, encoding="utf-8") as file:
        raw = json.load(file)
    package = normalize_package(raw, source=os.path.basename(path))
    LOGGER.info(
        "Loaded %s: %d codelists, %d terms, %d memberships",
        package["source"],
        len(package["codelists"]),
        len(package["terms"]),
        len(package["memberships"]),
    )
    return package


def catalogue_of(package):
    """'SDTM CT 2025-03-28' -> 'SDTM CT'."""
    name = package.get("name") or ""
    parts = name.rsplit(" ", 1)
    if len(parts) == 2 and parts[1].count("-") == 2:
        return parts[0]
    return name


# ---------------------------------------------------------------------------
# Diffing
# ---------------------------------------------------------------------------


def diff_fields(old, new, fields):
    """Return (field, old_value, new_value) for every field that differs."""
    return [(f, old.get(f), new.get(f)) for f in fields if old.get(f) != new.get(f)]


def _diff_entities(old, new, fields):
    added = [new[cid] for cid in sorted(new.keys() - old.keys())]
    removed = [old[cid] for cid in sorted(old.keys() - new.keys())]
    changed = []
    for cid in sorted(old.keys() & new.keys()):
        field_changes = diff_fields(old[cid], new[cid], fields)
        if field_changes:
            changed.append(
                {
                    "conceptId": cid,
                    "old": old[cid],
                    "new": new[cid],
                    "field_changes": field_changes,
                }
            )
    return added, removed, changed


def diff_codelists(old, new):
    return _diff_entities(old, new, CODELIST_FIELDS)


def diff_terms(old, new):
    return _diff_entities(old, new, TERM_FIELDS)


def diff_memberships(old, new):
    """Diff term-codelist relationships, keyed by (codelist, term) conceptId."""
    added = sorted(new.keys() - old.keys())
    removed = sorted(old.keys() - new.keys())
    changed = [
        {"key": key, "old": old[key], "new": new[key]}
        for key in sorted(old.keys() & new.keys())
        if old[key] != new[key]
    ]
    return added, removed, changed


def derive_moves(added, removed):
    """A term that both left and entered codelists in one step has moved.

    Gaining a codelist without losing one is a plain membership addition, and
    vice versa. Returns (moves, remaining_added, remaining_removed).
    """
    entered = defaultdict(set)
    for cl_cid, t_cid in added:
        entered[t_cid].add(cl_cid)
    left = defaultdict(set)
    for cl_cid, t_cid in removed:
        left[t_cid].add(cl_cid)

    moved_terms = sorted(entered.keys() & left.keys())
    moves = [
        {
            "conceptId": t_cid,
            "left": sorted(left[t_cid]),
            "entered": sorted(entered[t_cid]),
        }
        for t_cid in moved_terms
    ]
    moved = set(moved_terms)
    return (
        moves,
        [key for key in added if key[1] not in moved],
        [key for key in removed if key[1] not in moved],
    )


def diff_package_pair(old, new):
    cl_added, cl_removed, cl_changed = diff_codelists(
        old["codelists"], new["codelists"]
    )
    t_added, t_removed, t_changed = diff_terms(old["terms"], new["terms"])
    m_added, m_removed, m_changed = diff_memberships(
        old["memberships"], new["memberships"]
    )
    moves, m_added, m_removed = derive_moves(m_added, m_removed)

    return {
        "old_date": old["effectiveDate"],
        "new_date": new["effectiveDate"],
        "old_source": old["source"],
        "new_source": new["source"],
        "codelists": {"added": cl_added, "removed": cl_removed, "changed": cl_changed},
        "terms": {"added": t_added, "removed": t_removed, "changed": t_changed},
        "memberships": {
            "added": m_added,
            "removed": m_removed,
            "changed": m_changed,
            "moves": moves,
        },
        # Term attributes needed to label memberships, whose own dicts hold only
        # submission values. Union of both sides so removals stay labelable.
        "term_labels": {**old["terms"], **new["terms"]},
        "codelist_labels": {**old["codelists"], **new["codelists"]},
    }


# ---------------------------------------------------------------------------
# Severity banding
# ---------------------------------------------------------------------------


def extensible_codelists(package):
    """conceptIds of codelists this package allows sponsors to extend.

    Taken from the *old* package when banding a diff: what matters is whether
    the sponsor could already have added a term of their own, not what the
    incoming package permits. A codelist that was extensible and is not any
    more is still a collision risk, and this catches it.
    """
    return frozenset(
        cl_cid
        for cl_cid, codelist in package["codelists"].items()
        if codelist["extensible"]
    )


def severity_of(
    change,
    extensible_before=frozenset(),
    removed_terms=frozenset(),
    added_codelists=frozenset(),
):
    """Map one change record to its category (1 = most disruptive).

    Three optional sets supply context a single change record cannot carry:

    ``extensible_before`` - from ``extensible_codelists(old_package)``. Promotes
    an addition into "terms added to existing extensible codelists", the only
    addition category that can collide with a sponsor-defined term.

    ``removed_terms`` - conceptIds the new package drops entirely. Tells a term
    vanishing from the catalogue apart from one that merely left a codelist.

    ``added_codelists`` - conceptIds of codelists this package introduces.
    Separates terms arriving in a brand new codelist from terms arriving in one
    that was already there.

    All three default to empty so a caller wanting raw categories, with no
    reference to the old package, still gets an answer for every record. The
    defaults describe the *plainest* reading: nothing was extensible, nothing was
    fully deleted, and every codelist already existed.
    """
    kind = change["kind"]
    if kind == "codelist_removed":
        return 1
    if kind == "term_removed":
        return 2
    if kind == "membership_removed":
        return 2 if change["key"][1] in removed_terms else 3
    if kind == "membership_changed":
        return 4
    if kind == "membership_added":
        cl_cid = change["key"][0]
        if cl_cid in added_codelists:
            # Nothing could have been extended into a codelist that did not
            # exist, so extensibility does not distinguish anything here.
            return 9
        return 5 if cl_cid in extensible_before else 7
    if kind == "term_moved":
        # derive_moves strips a moved membership out of "added", so a move into
        # an extensible codelist has no membership_added record to carry the
        # risk. It has to be recognized here or it is missed entirely.
        entered = change["move"]["entered"]
        return 5 if any(cl in extensible_before for cl in entered) else 6
    if kind == "codelist_added":
        return 8
    if kind == "term_added":
        return 10
    if kind in ("codelist_changed", "term_changed"):
        return FIELD_SEVERITY.get(change["field"], PROPERTY_UPDATE[kind])
    raise ValueError(f"Unknown change kind: {kind}")


def band_changes(pair_diff, extensible_before=frozenset()):
    """Flatten one pair diff into individual changes grouped by severity band.

    A codelist or term whose change touches several fields yields one change per
    field, so a naming change and a definition tweak land in different bands.
    """
    changes = []

    for codelist in pair_diff["codelists"]["added"]:
        changes.append({"kind": "codelist_added", "codelist": codelist})
    for codelist in pair_diff["codelists"]["removed"]:
        changes.append({"kind": "codelist_removed", "codelist": codelist})
    for entry in pair_diff["codelists"]["changed"]:
        for field, old_value, new_value in entry["field_changes"]:
            changes.append(
                {
                    "kind": "codelist_changed",
                    "conceptId": entry["conceptId"],
                    "codelist": entry["new"],
                    "field": field,
                    "old": old_value,
                    "new": new_value,
                }
            )

    for term in pair_diff["terms"]["added"]:
        changes.append({"kind": "term_added", "term": term})
    for term in pair_diff["terms"]["removed"]:
        changes.append({"kind": "term_removed", "term": term})
    for entry in pair_diff["terms"]["changed"]:
        for field, old_value, new_value in entry["field_changes"]:
            changes.append(
                {
                    "kind": "term_changed",
                    "conceptId": entry["conceptId"],
                    "term": entry["new"],
                    "field": field,
                    "old": old_value,
                    "new": new_value,
                }
            )

    for key in pair_diff["memberships"]["added"]:
        changes.append({"kind": "membership_added", "key": key})
    for key in pair_diff["memberships"]["removed"]:
        changes.append({"kind": "membership_removed", "key": key})
    for entry in pair_diff["memberships"]["changed"]:
        changes.append(
            {
                "kind": "membership_changed",
                "key": entry["key"],
                "field": "submissionValue",
                "old": entry["old"],
                "new": entry["new"],
            }
        )
    for move in pair_diff["memberships"]["moves"]:
        changes.append({"kind": "term_moved", "move": move})

    # Context severity_of needs but a single change record cannot carry. Derived
    # here rather than asked of the caller: the pair diff already knows both.
    # Terms the new package drops entirely, to separate "gone from the
    # catalogue" from "left one codelist"...
    removed_terms = frozenset(
        term["conceptId"] for term in pair_diff["terms"]["removed"]
    )
    # ...and codelists it introduces, to separate a term arriving in a brand new
    # codelist from one arriving in a codelist that was already there.
    added_codelists = frozenset(
        codelist["conceptId"] for codelist in pair_diff["codelists"]["added"]
    )

    bands = {level: [] for level in SEVERITIES}
    for change in changes:
        level = severity_of(change, extensible_before, removed_terms, added_codelists)
        bands[level].append(change)
    return bands


def build_report(packages):
    """Chain of consecutive diffs, plus a cumulative oldest-to-newest rollup."""
    steps = []
    for old, new in zip(packages, packages[1:]):
        pair = diff_package_pair(old, new)
        pair["bands"] = band_changes(pair, extensible_codelists(old))
        steps.append(pair)

    cumulative = diff_package_pair(packages[0], packages[-1])
    # Extensibility as of the package we are diffing *from* - that is the state
    # a sponsor could have extended.
    cumulative["bands"] = band_changes(cumulative, extensible_codelists(packages[0]))

    return {
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(
            timespec="seconds"
        ),
        "catalogues": sorted({catalogue_of(p) for p in packages}),
        "packages": [
            {
                "source": p["source"],
                "name": p["name"],
                "effectiveDate": p["effectiveDate"],
                "version": p["version"],
                "counts": {
                    "codelists": len(p["codelists"]),
                    "terms": len(p["terms"]),
                    "memberships": len(p["memberships"]),
                },
            }
            for p in packages
        ],
        "steps": steps,
        "cumulative": cumulative,
    }


def step_title(pair_diff):
    return f'{pair_diff["old_date"]} -> {pair_diff["new_date"]}'


def render_step(pair_diff, heading):
    lines = [f"## {heading}", ""]
    lines.append(
        f'Comparing `{pair_diff["old_source"]}` against `{pair_diff["new_source"]}`.'
    )
    lines.append("")

    if not any(pair_diff["bands"].values()):
        lines.append("(no changes)")
        lines.append("")
        return lines

    for level, band_name in SEVERITIES.items():
        changes = pair_diff["bands"][level]
        lines.append(f"### {band_name} ({len(changes)})")
        lines.append("")
        if not changes:
            lines.append("(none)")
            lines.append("")
        else:
            lines.extend(render_change_table(pair_diff, changes))
    return lines


def render_counts_table(report):
    """Counts per category, one row per category and one column per step.

    Transposed relative to the obvious layout. Category names are sentences
    rather than codes, so they only fit down the left-hand side; and steps are
    few (one per consecutive release) while categories are fixed at eight, which
    makes this the orientation that stays readable as more packages are diffed.
    """
    columns = [(step_title(s), s, False) for s in report["steps"]]
    columns.append(
        (f'Cumulative {step_title(report["cumulative"])}', report["cumulative"], True)
    )

    def cell(text, emphasise):
        return f"**{text}**" if emphasise else str(text)

    lines = [
        "| Category | "
        + " | ".join(cell(title, bold) for title, _, bold in columns)
        + " |",
        "|---|" + "---:|" * len(columns),
    ]
    for level, name in SEVERITIES.items():
        counts = (
            cell(len(pair_diff["bands"][level]), bold) for _, pair_diff, bold in columns
        )
        lines.append(f"| {name} | " + " | ".join(counts) + " |")

    totals = (
        cell(sum(len(b) for b in pair_diff["bands"].values()), True)
        for _, pair_diff, _ in columns
    )
    lines.append("| **Total** | " + " | ".join(totals) + " |")
    return lines


def render_report(report):
    lines = ["# CDISC CT Package Diff Report", ""]
    lines.append(f'Generated: {report["generated"]}')
    lines.append("")

    if len(report["catalogues"]) > 1:
        lines.append(
            "> **WARNING — the input files are not all from the same catalogue: "
            + ", ".join(report["catalogues"])
            + ". The diff below is almost certainly meaningless.**"
        )
        lines.append("")
    else:
        lines.append(f'Catalogue: {report["catalogues"][0]}')
        lines.append("")

    lines.append("Input files (chronological):")
    lines.append("")
    for index, package in enumerate(report["packages"], start=1):
        counts = package["counts"]
        lines.append(
            f'{index}. `{package["source"]}` — effectiveDate {package["effectiveDate"]}, '
            f'version {package["version"]} '
            f'({counts["codelists"]} codelists, {counts["terms"]} terms, '
            f'{counts["memberships"]} memberships)'
        )
    lines.append("")

    lines.append("## Summary Counts")
    lines.append("")
    lines.extend(render_counts_table(report))
    lines.append("")

    for step in report["steps"]:
        lines.extend(render_step(step, f"Step: {step_title(step)}"))

    lines.extend(
        render_step(
            report["cumulative"], f'Cumulative: {step_title(report["cumulative"])}'
        )
    )

    return "\n".join(lines) + "\n"


def report_to_json(report):
    """Structured diff for downstream consumers. Tuples and frozensets are not
    JSON types, so membership keys become lists and synonyms sorted lists.

    The per-step label lookups are dropped: they hold every term and codelist in
    the catalogue and exist only for rendering.
    """
    skip = {"term_labels", "codelist_labels"}

    def convert(value):
        if isinstance(value, frozenset):
            return sorted(value)
        if isinstance(value, tuple):
            return [convert(v) for v in value]
        if isinstance(value, dict):
            return {str(k): convert(v) for k, v in value.items() if k not in skip}
        if isinstance(value, list):
            return [convert(v) for v in value]
        return value

    return json.dumps(convert(report), indent=2)


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------


def default_out_path(report):
    catalogue = report["catalogues"][0] if len(report["catalogues"]) == 1 else "mixed"
    slug = catalogue.lower().replace(" ", "_") or "cdisc_ct"
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{slug}_diff_report_{stamp}.md"


def load_sorted_packages(files, json_dir=None):
    """Resolve, load and chronologically sort package files.

    Split out of diff_package_files so callers that need the normalized packages
    themselves get them. Grouping a diff per codelist has to resolve which
    codelists currently contain a given term, and no single pair diff carries
    that - a pair diff holds only the membership delta, not a live index.
    """
    files = list(files)
    if len(files) < 2:
        raise ValueError("At least 2 package files are required to diff.")

    paths = [resolve_path(name, json_dir) for name in files]
    packages = [load_package(path) for path in paths]
    # Stable sort with the filename as secondary key, so runs are reproducible
    # even if two inputs share an effectiveDate.
    packages.sort(key=lambda p: (p["effectiveDate"] or "", p["source"]))

    catalogues = sorted({catalogue_of(p) for p in packages})
    if len(catalogues) > 1:
        LOGGER.warning(
            "Input files span several catalogues (%s) - the diff will be meaningless. "
            "Pass files from one catalogue only.",
            ", ".join(catalogues),
        )

    return packages


def diff_package_files(files, json_dir=None, changelog_dir=None):
    """Resolve, load, sort and diff package files. Returns the structured report.

    This is the entry point for other scripts - a wrapper diffing every
    catalogue of a release calls this once per catalogue. It raises instead of
    exiting, so a caller can carry on with the remaining catalogues; main()
    converts the exceptions into argparse errors.

    Pass `changelog_dir` to annotate the report with CDISC's rationale, exactly as
    the CLI does. It is a parameter rather than a default because enrichment reads
    the filesystem, which a caller diffing in a loop may not want; but a caller
    that does want it should not have to know to call `annotate_report` itself, in
    the right place, to get what `main()` produces.
    """
    report = build_report(load_sorted_packages(files, json_dir))
    if changelog_dir:
        annotate_report(report, changelog_dir)
    return report


def write_report(report, out_path=None, json_out=None):
    """Render and write a report. Returns (path written, rendered Markdown)."""
    text = render_report(report)
    out_path = out_path or default_out_path(report)

    with open(out_path, "w", encoding="utf-8") as file:
        file.write(text)
    LOGGER.info("Wrote report to %s", out_path)

    if json_out:
        with open(json_out, "w", encoding="utf-8") as file:
            file.write(report_to_json(report))
        LOGGER.info("Wrote structured diff to %s", json_out)

    return out_path, text


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Diff CDISC CT package JSON files across versions."
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Package JSON files to diff. Sorted internally by effectiveDate.",
    )
    parser.add_argument(
        "--json-dir",
        default=environ.get("CDISC_JSON_DIR"),
        help="Directory to resolve bare filenames against (default: CDISC_JSON_DIR).",
    )
    parser.add_argument(
        "--changelog-dir",
        default=default_changelog_dir(),
        help="Directory of CDISC change-log .xls files, used to annotate changes "
        "with their request code and rationale (default: "
        "<CDISC_XLS_DIR>/changelogs). Pass an empty string to skip enrichment. "
        "Read locally only - fetch them first with fetch_cdisc_changelogs.",
    )
    parser.add_argument(
        "--out", default=None, help="Report path (default: timestamped file in cwd)."
    )
    parser.add_argument(
        "--json-out", default=None, help="Also write the structured diff as JSON."
    )
    parser.add_argument(
        "--stdout", action="store_true", help="Also print the report to stdout."
    )
    args = parser.parse_args(argv)

    try:
        packages = load_sorted_packages(args.files, args.json_dir)
    except (ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))

    report = build_report(packages)
    annotate_report(report, args.changelog_dir)

    _, text = write_report(report, args.out, args.json_out)

    if args.stdout:
        print(text)


if __name__ == "__main__":
    main()
