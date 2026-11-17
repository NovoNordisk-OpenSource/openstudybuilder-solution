"""Reshape a flat pair diff into per-codelist buckets for impact review.

``ct_diff`` bands changes by severity, which answers "how bad is this release?".
Deciding whether to import a package needs the other axis - "which codelists does
it touch, and how?" - so this module regroups the same change records by
codelist. It consumes ``pair_diff["bands"]`` rather than re-deriving from the raw
``codelists``/``terms``/``memberships`` sub-dicts, so severity stays defined once,
in ``ct_diff.severity_of``.

Only changes are represented. A codelist nothing happened to never gets a bucket,
so it never gets a page.

Two shapes in the source data need care:

* A move is keyed by *term* (``left``/``entered`` lists of codelists) and
  ``derive_moves`` has already removed those memberships from ``added``/
  ``removed``. One move therefore lands on several codelists, tagged with the
  side it applies to, and never doubles as a plain addition.
* Terms are deduplicated catalogue-wide, so a term attribute change belongs to
  every codelist holding that term. Recovering that list needs the normalized
  packages: a pair diff carries only the membership delta, not a live index.
"""

import logging
from collections import defaultdict

from src.scripts.package_diff.ct_diff import SEVERITIES

LOGGER = logging.getLogger("CDISC CT diff grouping")


def index_memberships_by_term(package):
    """Map each term to the codelists holding it in one package snapshot."""
    homes = defaultdict(set)
    for cl_cid, t_cid in package["memberships"]:
        homes[t_cid].add(cl_cid)
    return homes


def codelists_for_change(change, old_homes, new_homes):
    """Which codelists one change record belongs to.

    Returns a list of ``(codelist_conceptId, extra_fields)``. ``extra_fields``
    is merged into the stored record, which is how a move records whether this
    codelist is the one it left or the one it entered.
    """
    kind = change["kind"]

    if kind in ("codelist_added", "codelist_removed"):
        return [(change["codelist"]["conceptId"], {})]
    if kind == "codelist_changed":
        return [(change["conceptId"], {})]

    if kind in ("membership_added", "membership_removed", "membership_changed"):
        return [(change["key"][0], {})]

    if kind == "term_moved":
        move = change["move"]
        return [(cl, {"role": "left"}) for cl in move["left"]] + [
            (cl, {"role": "entered"}) for cl in move["entered"]
        ]

    # Entity-level term changes carry no codelist of their own - the term exists
    # once catalogue-wide - so they resolve through the membership index.
    if kind == "term_added":
        return [
            (cl, {}) for cl in sorted(new_homes.get(change["term"]["conceptId"], ()))
        ]
    if kind == "term_removed":
        return [
            (cl, {}) for cl in sorted(old_homes.get(change["term"]["conceptId"], ()))
        ]
    if kind == "term_changed":
        t_cid = change["conceptId"]
        homes = set(old_homes.get(t_cid, ())) | set(new_homes.get(t_cid, ()))
        return [(cl, {}) for cl in sorted(homes)]

    raise ValueError(f"Unknown change kind: {kind}")


def _label_for(pair_diff, cl_cid):
    codelist = pair_diff["codelist_labels"].get(cl_cid)
    if not codelist or not codelist.get("name"):
        return cl_cid
    return f'{cl_cid} "{codelist["name"]}"'


def _new_bucket(pair_diff, cl_cid):
    return {
        "conceptId": cl_cid,
        "label": _label_for(pair_diff, cl_cid),
        "entity_status": None,
        # A comprehension, not dict.fromkeys: every band needs its own list.
        "bands": {level: [] for level in SEVERITIES},
        "counts": dict.fromkeys(SEVERITIES, 0) | {"total": 0},
        "min_severity": None,
    }


# A term appearing or vanishing catalogue-wide also produces a membership change
# for every codelist holding it. Both records are correct, but on one codelist's
# page they state the same fact twice, so exactly one of the pair is kept.
#
# The membership record is the one to keep, for two reasons. It is per-codelist,
# which is the axis these pages are organized on; and severity_of bands it by
# whether *this* codelist was extensible, so it is the record that carries the
# extension risk. The entity record is a single catalogue-wide row that cannot
# say anything codelist-specific. What the entity record does know - that the
# term is new to, or gone from, the catalogue entirely - is folded onto the
# surviving membership record as a flag rather than dropped.
_ENTITY_KINDS = {"term_added": "membership_added", "term_removed": "membership_removed"}

_CATALOGUE_FLAG = {"term_added": "catalogue_new", "term_removed": "catalogue_gone"}

_ENTITY_STATUS = {"codelist_added": "added", "codelist_removed": "removed"}


def _catalogue_level_terms(pair_diff):
    """Terms with both an entity-level record and membership records.

    Returns ``(suppressed, flags)``: entity records to drop from per-codelist
    attribution, and the flag to stamp on the membership records that replace
    them. A term with no membership record of the matching kind is never
    suppressed - nothing else would report it.
    """
    entity = defaultdict(set)
    membership = defaultdict(set)
    for band in pair_diff["bands"].values():
        for change in band:
            kind = change["kind"]
            if kind in _ENTITY_KINDS:
                entity[kind].add(change["term"]["conceptId"])
            elif kind in _ENTITY_KINDS.values():
                membership[kind].add(change["key"][1])

    suppressed = {
        entity_kind: entity[entity_kind] & membership[membership_kind]
        for entity_kind, membership_kind in _ENTITY_KINDS.items()
    }
    flags = {
        membership_kind: (_CATALOGUE_FLAG[entity_kind], suppressed[entity_kind])
        for entity_kind, membership_kind in _ENTITY_KINDS.items()
    }
    return suppressed, flags


def _is_suppressed(change, suppressed):
    terms = suppressed.get(change["kind"])
    return terms is not None and change["term"]["conceptId"] in terms


def _catalogue_flag(change, flags):
    """The catalogue-wide fact this membership record has to carry, if any."""
    entry = flags.get(change["kind"])
    if entry is None:
        return {}
    flag, terms = entry
    return {flag: True} if change["key"][1] in terms else {}


def _severity_ordered(pair_diff):
    """Every change as ``(level, change)``, most severe band first."""
    for level in SEVERITIES:
        yield from ((level, change) for change in pair_diff["bands"][level])


def _record(buckets, pair_diff, cl_cid, level, change, extra):
    """File one change under one codelist, creating the bucket on first use."""
    bucket = buckets.get(cl_cid)
    if bucket is None:
        bucket = buckets[cl_cid] = _new_bucket(pair_diff, cl_cid)

    status = _ENTITY_STATUS.get(change["kind"])
    if status:
        bucket["entity_status"] = status

    bucket["bands"][level].append({**change, **extra} if extra else change)
    bucket["counts"][level] += 1
    bucket["counts"]["total"] += 1
    if bucket["min_severity"] is None:
        bucket["min_severity"] = level


def _order_worst_first(buckets):
    """Most severe band present, then sheer volume, then a stable label so runs
    are reproducible."""
    return sorted(
        buckets,
        key=lambda cid: (
            buckets[cid]["min_severity"] or len(SEVERITIES) + 1,
            -buckets[cid]["counts"]["total"],
            buckets[cid]["label"],
        ),
    )


def group_by_codelist(pair_diff, old_package, new_package):
    """Regroup one pair diff by codelist, worst impact first.

    ``old_package``/``new_package`` are the normalized packages the pair diff was
    built from; they are needed only to resolve term-to-codelist membership.

    Returns a dict with ``codelists`` (buckets keyed by conceptId), ``order``
    (conceptIds sorted worst first), ``term_attribute_changes`` (each
    codelist-independent term change once, annotated with its home codelists) and
    ``unscoped`` (changes that resolved to no codelist at all).
    """
    old_homes = index_memberships_by_term(old_package)
    new_homes = index_memberships_by_term(new_package)
    suppressed, flags = _catalogue_level_terms(pair_diff)

    buckets = {}
    term_attribute_changes = []
    unscoped = {level: [] for level in SEVERITIES}
    # Distinct surviving facts per band. Not len(pair_diff["bands"][level]):
    # that counts records suppressed as duplicates of a membership change.
    distinct_counts = dict.fromkeys(SEVERITIES, 0)

    for level, change in _severity_ordered(pair_diff):
        if _is_suppressed(change, suppressed):
            continue
        distinct_counts[level] += 1
        extra_for_all = _catalogue_flag(change, flags)

        targets = codelists_for_change(change, old_homes, new_homes)
        if not targets:
            # Should not happen: normalize_package builds memberships from each
            # codelist's own term list, so every term has a home. Keep the
            # record rather than drop it, and say so.
            LOGGER.warning(
                "Change %s resolved to no codelist and is reported unscoped",
                change.get("kind"),
            )
            unscoped[level].append(change)
            continue

        for cl_cid, extra in targets:
            _record(buckets, pair_diff, cl_cid, level, change, extra | extra_for_all)

        if change["kind"] == "term_changed":
            term_attribute_changes.append(
                {**change, "codelists": [cl for cl, _ in targets]}
            )

    return {
        "codelists": buckets,
        "order": _order_worst_first(buckets),
        "term_attribute_changes": term_attribute_changes,
        "distinct_counts": distinct_counts,
        "unscoped": unscoped,
    }


def group_report(report, packages):
    """Group every pair diff in a report.

    ``packages`` must be the ordered, normalized list ``build_report`` was called
    with; the pairing below mirrors its own ``zip(packages, packages[1:])``.
    """
    steps = [
        group_by_codelist(step, old, new)
        for step, old, new in zip(report["steps"], packages, packages[1:])
    ]
    return {
        "cumulative": group_by_codelist(
            report["cumulative"], packages[0], packages[-1]
        ),
        "steps": steps,
    }
