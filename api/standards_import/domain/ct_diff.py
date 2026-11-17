"""Diff two normalized CDISC CT catalogue snapshots and band the changes by severity.

Ported from `import_standards/src/scripts/package_diff/ct_diff.py`, kept to the pure
diffing and severity-banding logic only — no file loading, no Markdown rendering, no
changelog enrichment. `import_standards` and `api` are separate Pipenv components, so
this is duplicated rather than imported, the same way `changelog_annotate.py`
duplicates `PACKAGE_FILE_RE` instead of pulling in a cross-component dependency.

A snapshot is a dict with three keys, built from one catalogue's `RawCodelist`/
`RawTerm` nodes:

- ``codelists``: ``{conceptId: {name, definition, preferredTerm, submissionValue,
  extensible (bool), synonyms (frozenset)}}``
- ``terms``: ``{conceptId: {definition, preferredTerm, synonyms (frozenset)}}``
- ``memberships``: ``{(codelistId, termId): submissionValue}``
"""

from collections import defaultdict
from typing import Any

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
# already happened. See import_standards' ct_diff.py for the full rationale behind
# the ordering and the four-way split of additions.
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

FIELD_SEVERITY = {
    "submissionValue": 4,
}

PROPERTY_UPDATE = {
    "codelist_changed": 11,
    "term_changed": 12,
}


def diff_fields(
    old: dict[str, Any], new: dict[str, Any], fields: tuple[str, ...]
) -> list[tuple[str, Any, Any]]:
    """Return (field, old_value, new_value) for every field that differs."""
    return [(f, old.get(f), new.get(f)) for f in fields if old.get(f) != new.get(f)]


def _diff_entities(
    old: dict[str, dict[str, Any]],
    new: dict[str, dict[str, Any]],
    fields: tuple[str, ...],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
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


def diff_memberships(
    old: dict[tuple[str, str], Any], new: dict[tuple[str, str], Any]
) -> tuple[list[tuple[str, str]], list[tuple[str, str]], list[dict[str, Any]]]:
    """Diff term-codelist relationships, keyed by (codelist, term) conceptId."""
    added = sorted(new.keys() - old.keys())
    removed = sorted(old.keys() - new.keys())
    changed = [
        {"key": key, "old": old[key], "new": new[key]}
        for key in sorted(old.keys() & new.keys())
        if old[key] != new[key]
    ]
    return added, removed, changed


def derive_moves(
    added: list[tuple[str, str]], removed: list[tuple[str, str]]
) -> tuple[list[dict[str, Any]], list[tuple[str, str]], list[tuple[str, str]]]:
    """A term that both left and entered codelists in one step has moved."""
    entered: dict[str, set[str]] = defaultdict(set)
    for cl_cid, t_cid in added:
        entered[t_cid].add(cl_cid)
    left: dict[str, set[str]] = defaultdict(set)
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


def diff_package_pair(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    cl_added, cl_removed, cl_changed = diff_codelists(
        old["codelists"], new["codelists"]
    )
    t_added, t_removed, t_changed = diff_terms(old["terms"], new["terms"])
    m_added, m_removed, m_changed = diff_memberships(
        old["memberships"], new["memberships"]
    )
    moves, m_added, m_removed = derive_moves(m_added, m_removed)

    return {
        "codelists": {"added": cl_added, "removed": cl_removed, "changed": cl_changed},
        "terms": {"added": t_added, "removed": t_removed, "changed": t_changed},
        "memberships": {
            "added": m_added,
            "removed": m_removed,
            "changed": m_changed,
            "moves": moves,
        },
        "term_labels": {**old["terms"], **new["terms"]},
        "codelist_labels": {**old["codelists"], **new["codelists"]},
    }


def extensible_codelists(package: dict[str, Any]) -> frozenset:
    """conceptIds of codelists this package allows sponsors to extend."""
    return frozenset(
        cl_cid
        for cl_cid, codelist in package["codelists"].items()
        if codelist["extensible"]
    )


def severity_of(  # pylint: disable=too-many-return-statements  # noqa: PLR0911
    change: dict[str, Any],
    extensible_before: frozenset = frozenset(),
    removed_terms: frozenset = frozenset(),
    added_codelists: frozenset = frozenset(),
) -> int:
    """Map one change record to its category (1 = most disruptive)."""
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
            return 9
        return 5 if cl_cid in extensible_before else 7
    if kind == "term_moved":
        entered = change["move"]["entered"]
        return 5 if any(cl in extensible_before for cl in entered) else 6
    if kind == "codelist_added":
        return 8
    if kind == "term_added":
        return 10
    if kind in ("codelist_changed", "term_changed"):
        return FIELD_SEVERITY.get(change["field"], PROPERTY_UPDATE[kind])
    raise ValueError(f"Unknown change kind: {kind}")


def band_changes(
    pair_diff: dict[str, Any], extensible_before: frozenset = frozenset()
) -> dict[int, list[dict[str, Any]]]:
    """Flatten one pair diff into individual changes grouped by severity band."""
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

    removed_terms = frozenset(
        term["conceptId"] for term in pair_diff["terms"]["removed"]
    )
    added_codelists = frozenset(
        codelist["conceptId"] for codelist in pair_diff["codelists"]["added"]
    )

    bands: dict[int, list[dict[str, Any]]] = {level: [] for level in SEVERITIES}
    for change in changes:
        level = severity_of(change, extensible_before, removed_terms, added_codelists)
        bands[level].append(change)
    return bands
