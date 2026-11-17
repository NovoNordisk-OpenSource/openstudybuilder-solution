"""Match a release's changelog entries onto the changes a CT package diff found.

`ct_diff` says *what* changed between two releases; CDISC's terminology-changes
spreadsheet says *why*. This joins the two, so a reviewer looking at a banded change
can see CDISC's own request code, summary and implementation instructions beside it.

Ported in intent from `import_standards`' `changelog_annotate.py`, but not in mechanism.
That module joins flat spreadsheet rows onto changes at diff time using three columns
(`NCI Code`, `CDISC Term Type`, `CDISC Codelist (Short Name)`), because all it has is
rows and JSON files. Here the join is already done: `changelog_repository`'s
`RESOLVE_TARGET` resolved every entry to the `RawCatalogue`, `RawCodelist` or `RawTerm`
node it is about when the sheet was uploaded, and did it against what the codes actually
matched in the catalogue rather than against the sheet's own self-description. So this
reads the resolved subject and only has to decide *which* of a subject's entries explain
a particular change.

Two consequences of how `RESOLVE_TARGET` degrades matter here, both of them the reason
the highest-severity bands can be annotated at all. An entry about something that no
longer exists in the release it was uploaded against has no node left to point at, so:

  * a codelist retired this release attaches to the **catalogue**, and is found again by
    its `codelist_short_name` (the removed codelist's `submissionValue`);
  * a term removed from a surviving codelist attaches to the **codelist**, and is found
    again by its `nci_code`.

Enrichment only ever annotates. An unmatched change is left alone and an unmatched entry
is dropped — never the reverse, and nothing here raises: a diff is complete and correct
without a changelog, and no missing or surprising spreadsheet should cost a reviewer
the diff itself.
"""

from collections import defaultdict
from typing import Any

# Change kind -> the stored `change_type` values that can plausibly explain it. Stored
# values are upper-cased on the way in (see `models.changelog.ChangeType`), unlike the
# title case the spreadsheet itself uses.
#
# Coarse on purpose: adding a synonym and removing one are both `UPDATE`, because both
# update the term carrying it. `change_summary` is what carries the direction, which is
# why `field_of` reads that and not this.
KIND_CHANGE_TYPES = {
    "codelist_added": ("ADD",),
    "codelist_removed": ("REMOVE",),
    "term_added": ("ADD",),
    "term_removed": ("REMOVE",),
    "membership_added": ("ADD",),
    "membership_removed": ("REMOVE",),
    "codelist_changed": ("UPDATE",),
    "term_changed": ("UPDATE",),
    "membership_changed": ("UPDATE",),
}

# Which `ct_diff` field an entry is about, read out of `change_summary`.
#
# `import_standards` reads the sheet's `CDISC Term Type` column for this and falls back
# to summary keywords only for a term type it has not seen. We only have the fallback:
# `term_type` is dropped before storage (see `changelog_service`'s
# `collapse_codelist_name_rows`), having served its one purpose of spotting the
# codelist-rename fan-out. Substring and case-insensitive, so that "Add new CDISC
# Synonym" and "Remove CDISC Synonym" both land on `synonyms`.
FIELD_KEYWORDS = {
    "submissionValue": ("submission value",),
    "preferredTerm": ("preferred term",),
    "name": ("codelist name",),
    "definition": ("definition",),
    "synonyms": ("synonym",),
    "extensible": ("extensible",),
}


def field_of(entry: dict[str, Any]) -> str | None:
    """The field an entry describes, or None when its summary names none.

    Checked longest-phrase-first via `FIELD_KEYWORDS`' order: "codelist name" has to be
    tried before anything that would also match inside it.
    """

    summary = (entry.get("change_summary") or "").lower()
    for field, keywords in FIELD_KEYWORDS.items():
        if any(keyword in summary for keyword in keywords):
            return field
    return None


def index_entries(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Index one catalogue's changelog entries by the subject they resolved to.

    `records` is what `changelog_repository.get_changelog_for_catalogue` returns: the
    stored entry plus the labels and identity of the node its `ABOUT` points at.

    Terms are indexed both under their own codelist and catalogue-wide. Both are needed:
    a `membership_*` change knows which codelist it is about and should not be annotated
    from a different one, while a `term_changed` change is catalogue-wide — `ct_diff`
    deduplicates terms by `conceptId` across the release — and has no codelist to scope
    by.
    """

    index: dict[str, Any] = {
        "codelist": defaultdict(list),
        "term": defaultdict(list),
        "term_any": defaultdict(list),
        "removed_term": defaultdict(list),
        "removed_term_any": defaultdict(list),
        "retired_codelist": defaultdict(list),
    }

    for record in records:
        entry = record["entry"]
        labels = set(record.get("target_labels") or ())
        concept_id = record.get("target_concept_id")
        nci_code = entry.get("nci_code")

        if "RawTerm" in labels:
            parent = record.get("parent_codelist_id")
            index["term"][(parent, concept_id)].append(entry)
            index["term_any"][concept_id].append(entry)
        elif "RawCodelist" in labels:
            if nci_code is None or nci_code == concept_id:
                # About the codelist itself. A rename arrives here too: the fan-out is
                # collapsed at parse time into one entry carrying no `nci_code`.
                index["codelist"][concept_id].append(entry)
            else:
                # The subject left this release; `nci_code` is the term it was about.
                index["removed_term"][(concept_id, nci_code)].append(entry)
                index["removed_term_any"][nci_code].append(entry)
        elif "RawCatalogue" in labels:
            # Nothing under the codelist was staged, so it was retired this release.
            index["retired_codelist"][entry.get("codelist_short_name")].append(entry)

    return index


def _narrow(entries: list[dict[str, Any]], predicate) -> list[dict[str, Any]]:
    """Filter, but never down to nothing.

    Every narrowing step is a preference, not a gate: where no entry satisfies it the
    candidates are returned untouched. A change annotated with several plausible entries
    is useful; one silently annotated with none is not.
    """

    filtered = [entry for entry in entries if predicate(entry)]
    return filtered or entries


def _prefer_change_type(
    entries: list[dict[str, Any]], kind: str
) -> list[dict[str, Any]]:
    wanted = KIND_CHANGE_TYPES.get(kind)
    if not wanted:
        return entries
    return _narrow(entries, lambda entry: entry.get("change_type") in wanted)


def _prefer_field(
    entries: list[dict[str, Any]], field: str | None
) -> list[dict[str, Any]]:
    if not field:
        return entries
    return _narrow(entries, lambda entry: field_of(entry) == field)


def _dedupe(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop entries reached by more than one index, keeping first-seen order."""

    seen = set()
    unique = []
    for entry in entries:
        uid = entry.get("uid")
        if uid in seen:
            continue
        seen.add(uid)
        unique.append(entry)
    return unique


def match_entries(  # pylint: disable=too-many-return-statements  # noqa: PLR0911
    index: dict[str, Any], change: dict[str, Any]
) -> list[dict[str, Any]]:
    """The changelog entries explaining one banded change, best candidates first.

    Returns a list — a term added to three codelists is three entries — which is empty
    when nothing matches. Never raises: an unrecognised change kind returns no entries
    rather than failing the diff.

    One branch per kind, mirroring `ct_diff.band_changes`. Collapsing them into a
    dispatch table would hide which narrowing steps apply to which kind, which is the
    whole content here.
    """

    kind = change.get("kind")

    if kind == "codelist_added":
        return _dedupe(
            _prefer_change_type(
                index["codelist"][change["codelist"]["conceptId"]], kind
            )
        )

    if kind == "codelist_removed":
        codelist = change["codelist"]
        candidates = (
            index["retired_codelist"][codelist.get("submissionValue")]
            + index["codelist"][codelist["conceptId"]]
        )
        return _dedupe(_prefer_change_type(candidates, kind))

    if kind == "codelist_changed":
        entries = _prefer_change_type(index["codelist"][change["conceptId"]], kind)
        return _dedupe(_prefer_field(entries, change.get("field")))

    if kind == "term_added":
        return _dedupe(
            _prefer_change_type(index["term_any"][change["term"]["conceptId"]], kind)
        )

    if kind == "term_removed":
        concept_id = change["term"]["conceptId"]
        candidates = (
            index["removed_term_any"][concept_id] + index["term_any"][concept_id]
        )
        return _dedupe(_prefer_change_type(candidates, kind))

    if kind == "term_changed":
        entries = _prefer_change_type(index["term_any"][change["conceptId"]], kind)
        return _dedupe(_prefer_field(entries, change.get("field")))

    if kind == "membership_added":
        cl_cid, t_cid = change["key"]
        candidates = index["term"][(cl_cid, t_cid)] or index["term_any"][t_cid]
        return _dedupe(_prefer_change_type(candidates, kind))

    if kind == "membership_removed":
        cl_cid, t_cid = change["key"]
        candidates = (
            index["removed_term"][(cl_cid, t_cid)]
            + index["term"][(cl_cid, t_cid)]
            + index["removed_term_any"][t_cid]
        )
        return _dedupe(_prefer_change_type(candidates, kind))

    if kind == "membership_changed":
        cl_cid, t_cid = change["key"]
        candidates = index["term"][(cl_cid, t_cid)] or index["term_any"][t_cid]
        entries = _prefer_change_type(candidates, kind)
        return _dedupe(_prefer_field(entries, change.get("field")))

    if kind == "term_moved":
        # Spans several codelists at once, so there is no single codelist to scope by;
        # this usually surfaces the paired remove and add entries.
        concept_id = change["move"]["conceptId"]
        return _dedupe(
            index["term_any"][concept_id] + index["removed_term_any"][concept_id]
        )

    return []
