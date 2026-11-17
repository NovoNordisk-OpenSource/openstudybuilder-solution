"""Reads and writes the MDR database for a CDISC release.

Writes go around the domain aggregates on purpose: they refuse creation in the
non-editable `CDISC` library, enforce global name uniqueness, and stamp every
`start_date` with the server clock. A CDISC release needs the opposite of all three —
it *is* the CDISC library, its names are not unique by our rules, and its versions are
dated by CDISC's effective date, not by when we happened to run the import.

Only `LATEST` and `LATEST_FINAL` are ever moved. `LATEST_DRAFT` and `LATEST_RETIRED`
are historical pointers to the last value that was ever in that state, they legitimately
coexist with the others, and removing one causes real regressions — so nothing here
touches them.

This is the one staging repository that writes MDR, not staging, nodes — so unlike its
siblings, nothing it creates ever gets the `:CDISCStaging` marker label.
"""

import logging
from typing import Any

from neo4j import exceptions as neo4j_exceptions
from neomodel import db, get_config

log = logging.getLogger(__name__)

CDISC_LIBRARY = "CDISC"

_indexes_created: set[str] = set()

# Every write here matches a root or a package node by uid. Without these the import
# label-scans tens of thousands of nodes per row and slows to a crawl. A database
# prepared by `db/` init already has equivalent constraints, in which case these are
# no-ops — but the import must not depend on that having been run.
MDR_INDEX_QUERIES = [
    "CREATE INDEX si_codelist_root_uid IF NOT EXISTS FOR (n:CTCodelistRoot) ON (n.uid)",
    "CREATE INDEX si_term_root_uid IF NOT EXISTS FOR (n:CTTermRoot) ON (n.uid)",
    "CREATE INDEX si_package_uid IF NOT EXISTS FOR (n:CTPackage) ON (n.uid)",
    "CREATE INDEX si_package_codelist_uid IF NOT EXISTS FOR (n:CTPackageCodelist) ON (n.uid)",
    "CREATE INDEX si_package_term_uid IF NOT EXISTS FOR (n:CTPackageTerm) ON (n.uid)",
    "CREATE INDEX si_catalogue_name IF NOT EXISTS FOR (n:CTCatalogue) ON (n.name)",
    "CREATE INDEX si_library_name IF NOT EXISTS FOR (n:Library) ON (n.name)",
    "CREATE INDEX si_codelist_term_submval IF NOT EXISTS FOR (n:CTCodelistTerm) ON (n.submission_value)",
]


def ensure_indexes() -> None:
    """Creates the lookup indexes the import relies on, once per database."""

    database = get_config().database_name or ""

    if database in _indexes_created:
        return

    for query in MDR_INDEX_QUERIES:
        try:
            mdr_query(query)
        except neo4j_exceptions.Neo4jError as exc:
            # An equivalent constraint-backed index already covers this; nothing to do.
            log.debug("Skipping index: %s", exc)

    _indexes_created.add(database)


def mdr_query(
    cypher: str, params: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    rows, columns = db.cypher_query(cypher, params or {})
    return [dict(zip(columns, row)) for row in rows]


# --- reads ----------------------------------------------------------------------


def get_head_effective_date(excluding: str | None = None) -> str | None:
    """Returns the newest package effective date already in MDR, if any.

    `excluding` leaves out one release, which is what makes a failed import retryable:
    packages are created early in the run, so a run that dies after that would otherwise
    see its own half-written package as the head and refuse to start again.

    Always a plain `YYYY-MM-DD`: packages loaded by `import_standards` carry a datetime
    `effective_date`, this app's own import writes a date, and both can be in one database.
    """

    records = mdr_query(
        """
        MATCH (p:CTPackage)
        WHERE p.effective_date IS NOT NULL
          AND ($excluding IS NULL OR toString(date(p.effective_date)) <> $excluding)
        RETURN toString(max(date(p.effective_date))) AS head
        """,
        {"excluding": excluding},
    )
    return records[0]["head"] if records and records[0]["head"] else None


def get_existing_packages(uids: list[str]) -> set[str]:
    records = mdr_query(
        "MATCH (p:CTPackage) WHERE p.uid IN $uids RETURN p.uid AS uid",
        {"uids": uids},
    )
    return {record["uid"] for record in records}


def get_existing_catalogues(names: list[str]) -> set[str]:
    records = mdr_query(
        "MATCH (c:CTCatalogue) WHERE c.name IN $names RETURN c.name AS name",
        {"names": names},
    )
    return {record["name"] for record in records}


def get_codelist_heads(uids: list[str], package_date: str) -> dict[str, dict[str, Any]]:
    """Returns the head attributes of each codelist that exists in MDR.

    Normally that is the open version. It also accepts one **closed at this release's
    own date**, which means a previous attempt at this release closed it and died before
    creating the replacement. Without that, the retry would find no head, take the
    concept for a new one, and stack a version 1.0 "Initial CDISC import" on top of a
    closed 5.0.
    """

    records = mdr_query(
        """
        MATCH (root:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[hv:HAS_VERSION]->(value)
        WHERE root.uid IN $uids
          AND (hv.end_date IS NULL OR hv.end_date = datetime($package_date))
        // An open version wins over one closed at this date: after a completed run both
        // exist, and the open one is the head.
        WITH root, hv, value
        ORDER BY CASE WHEN hv.end_date IS NULL THEN 0 ELSE 1 END
        WITH root, collect({props: properties(value), version: hv.version})[0] AS head
        RETURN root.uid AS uid, head.props AS props, head.version AS version
        """,
        {"uids": uids, "package_date": package_date},
    )
    return {record["uid"]: record for record in records}


def get_term_heads(uids: list[str], package_date: str) -> dict[str, dict[str, Any]]:
    """Returns the head attributes of each term that exists in MDR.

    Normally that is the open version. It also accepts one **closed at this release's
    own date**, which means a previous attempt at this release closed it and died before
    creating the replacement. Without that, the retry would find no head, take the
    concept for a new one, and stack a version 1.0 "Initial CDISC import" on top of a
    closed 5.0.
    """

    records = mdr_query(
        """
        MATCH (root:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[hv:HAS_VERSION]->(value)
        WHERE root.uid IN $uids
          AND (hv.end_date IS NULL OR hv.end_date = datetime($package_date))
        // An open version wins over one closed at this date: after a completed run both
        // exist, and the open one is the head.
        WITH root, hv, value
        ORDER BY CASE WHEN hv.end_date IS NULL THEN 0 ELSE 1 END
        WITH root, collect({props: properties(value), version: hv.version})[0] AS head
        RETURN root.uid AS uid, head.props AS props, head.version AS version
        """,
        {"uids": uids, "package_date": package_date},
    )
    return {record["uid"]: record for record in records}


def get_open_memberships(codelist_uids: list[str]) -> set[tuple[str, str, str]]:
    """Returns the open memberships of these codelists **that CDISC owns**.

    The library filter is load-bearing, not tidiness. This set is differenced against what
    the release ships to work out which memberships to close, and a release never mentions
    a sponsor term — so without it every sponsor extension of a CDISC codelist would be
    evicted by the next quarterly import, silently, as a term CDISC had dropped. A sponsor
    term leaves a codelist only when somebody decides it should.
    """

    records = mdr_query(
        """
        MATCH (lib:Library {name: $library})-[:CONTAINS_TERM]->(term:CTTermRoot)
              <-[:HAS_TERM_ROOT]-(ct:CTCodelistTerm)<-[ht:HAS_TERM]-(root:CTCodelistRoot)
        WHERE root.uid IN $uids AND ht.end_date IS NULL
        RETURN root.uid AS codelist_uid, term.uid AS term_uid, ct.submission_value AS submission_value
        """,
        {"uids": codelist_uids, "library": CDISC_LIBRARY},
    )
    return {(r["codelist_uid"], r["term_uid"], r["submission_value"]) for r in records}


def get_open_memberships_of_terms(term_uids: list[str]) -> set[tuple[str, str, str]]:
    """`get_open_memberships`, keyed on the terms rather than on the codelists.

    Same shape and the same library filter: these are CDISC terms, and only a CDISC
    term's memberships are the release's to open or close.
    """

    records = mdr_query(
        """
        MATCH (lib:Library {name: $library})-[:CONTAINS_TERM]->(term:CTTermRoot)
              <-[:HAS_TERM_ROOT]-(ct:CTCodelistTerm)<-[ht:HAS_TERM]-(root:CTCodelistRoot)
        WHERE term.uid IN $uids AND ht.end_date IS NULL
        RETURN root.uid AS codelist_uid, term.uid AS term_uid, ct.submission_value AS submission_value
        """,
        {"uids": term_uids, "library": CDISC_LIBRARY},
    )
    return {(r["codelist_uid"], r["term_uid"], r["submission_value"]) for r in records}


def get_existing_term_uids(uids: list[str]) -> set[str]:
    """Returns which of these terms MDR already holds."""

    records = mdr_query(
        "MATCH (t:CTTermRoot) WHERE t.uid IN $uids RETURN t.uid AS uid",
        {"uids": uids},
    )
    return {record["uid"] for record in records}


def get_sponsor_codelists() -> list[dict[str, Any]]:
    """Returns every codelist MDR holds outside the CDISC library.

    "Sponsor-defined" is `NOT CDISC` rather than `= 'Sponsor'`, which is how the main
    API's own queries put it: an installation may have more than one editable library,
    and anything in one of them is a codelist somebody here coined.

    Unscoped, because the question a new CDISC codelist asks is "does *any* sponsor
    codelist already cover this" — the main API's name and submission-value uniqueness
    for codelists is global, not per catalogue, so nothing narrows it. There are usually
    tens to a few hundreds of these, so one query returns the lot.
    """

    return mdr_query(
        """
        MATCH (lib:Library)-[:CONTAINS_CODELIST]->(root:CTCodelistRoot)
              -[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[hv:HAS_VERSION]->(value)
        WHERE lib.name <> $library AND hv.end_date IS NULL
        RETURN root.uid AS uid,
               lib.name AS library_name,
               value.name AS name,
               value.submission_value AS submission_value,
               value.definition AS definition
        ORDER BY uid
        """,
        {"library": CDISC_LIBRARY},
    )


def get_sponsor_terms_in_codelists(codelist_uids: list[str]) -> list[dict[str, Any]]:
    """Returns the sponsor-defined terms sitting in each of these codelists.

    One query for every codelist rather than one per codelist: this is a handful of rows
    against a bootstrapped database, and the scoping that a fetch over HTTP needs to stay
    usable buys nothing here.

    Narrowing to `codelist_uids` is about how much comes back, not about correctness —
    every row carries the codelist it belongs to, and the caller matches within one
    codelist at a time. Widening it would waste rows, not report a false collision.

    A term whose name version is `Retired` is left out, because that is exactly the state
    in which it stops colliding — `term_specific_exists_by_name_in_codelists` in the main
    API exempts retired terms from its uniqueness rule, and reporting one as a collision
    would mean never being able to settle it.

    `Draft` is deliberately *not* excluded, for the mirror-image reason: that same rule
    exempts only retired terms, so a sponsor term still in draft already stands in the way
    of a CDISC term arriving with its name. Leaving it out would report a release as clean
    and then have the import make it collide.

    The submission value comes from the membership, not the term, so a term in two
    codelists yields two rows with the value each codelist knows it by.
    """

    if not codelist_uids:
        return []

    return mdr_query(
        """
        MATCH (lib:Library)-[:CONTAINS_TERM]->(root:CTTermRoot)
              <-[:HAS_TERM_ROOT]-(ct:CTCodelistTerm)<-[ht:HAS_TERM]-(cl:CTCodelistRoot)
        WHERE lib.name <> $library
          AND ht.end_date IS NULL
          AND cl.uid IN $uids
        MATCH (root)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[nv:HAS_VERSION]->(name)
        WHERE nv.end_date IS NULL AND nv.status <> 'Retired'
        OPTIONAL MATCH (root)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[av:HAS_VERSION]->(attributes)
        WHERE av.end_date IS NULL
        RETURN cl.uid AS codelist_uid,
               root.uid AS uid,
               lib.name AS library_name,
               name.name AS name,
               ct.submission_value AS submission_value,
               attributes.definition AS definition
        ORDER BY codelist_uid, uid
        """,
        {"library": CDISC_LIBRARY, "uids": codelist_uids},
    )


def get_term_names(uids: list[str]) -> dict[str, str]:
    """Returns the sponsor preferred name MDR currently holds for each of these terms.

    The name half, not the attributes half: this is the editable one, and the whole point
    of asking is to find where somebody's choice has drifted from what the naming rules
    would produce today.
    """

    if not uids:
        return {}

    records = mdr_query(
        """
        MATCH (root:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[hv:HAS_VERSION]->(value)
        WHERE root.uid IN $uids AND hv.end_date IS NULL
        RETURN root.uid AS uid, value.name AS name
        """,
        {"uids": uids},
    )
    return {record["uid"]: record["name"] for record in records if record["name"]}


# Everything that refers to a term, and the shape each reference takes. Three arms rather
# than one because `CTTermContext` is nearly, but not quite, the single way in: it is how
# activity items, unit definitions, ODM items, study selections and template categories
# all reach a term. The others go around it and reach the *name* half — so a check that
# walked `CTTermRoot` alone would call a term unused while a syntax instance was built
# on it.
#
# Two kinds of relationship are deliberately absent.
#
# The CT-internal ones — `HAS_PARENT_TYPE`, `IS_SPECIALIZATION_OF`, `HAS_PREDECESSOR` —
# describe the terminology's own shape rather than somebody depending on the term.
#
# And `HAS_PARAMETER_TERM`, which is a *listing* rather than a reference: it says the term
# is on offer as a parameter of its codelist, and taking the term out of the codelist is
# supposed to take it off that list. The main API's own `remove_term` deletes the edge for
# exactly that reason, and so does `close_sponsor_memberships`. Counting it as usage would
# make every term that had ever been offered as a parameter impossible to displace.
# `USES_VALUE` on the same node is the opposite: a syntax instance that already uses it.
#
# Only a *live* consumer counts: one whose `HAS_VERSION` is still open. `end_date IS NULL`
# rather than a `{end_date: null}` pattern, which never matches (null = null is null) and
# so would miss a rel with the property absent.
_LIVE_CONSUMER = """EXISTS {
        MATCH (consumer)<-[live:HAS_VERSION]-()
        WHERE live.end_date IS NULL
    }"""


def _usage_query(
    unwind: str, match: str, keys: str, through: str, where: str | None = None
) -> str:
    """Builds one usage arm. `match` must bind `r` (the relationship) and `consumer`."""

    conditions = f"({where}) AND {_LIVE_CONSUMER}" if where else _LIVE_CONSUMER
    return f"""
    {unwind}
    {match}
    WHERE {conditions}
    RETURN {keys}, '{through}' AS through, type(r) AS relationship,
           labels(consumer) AS consumer_labels, count(*) AS count
    """


def _usage_entry(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "through": record["through"],
        "relationship": record["relationship"],
        "consumer_labels": record["consumer_labels"],
        "count": record["count"],
    }


TERM_USAGE_QUERIES = [
    _usage_query("UNWIND $uids AS uid", match, "uid", through)
    for match, through in (
        (
            (
                "MATCH (:CTTermRoot {uid: uid})<-[:HAS_SELECTED_TERM]-(:CTTermContext)"
                "<-[r]-(consumer)"
            ),
            "selected in context",
        ),
        (
            (
                "MATCH (:CTTermRoot {uid: uid})-[:HAS_NAME_ROOT]->(nr:CTTermNameRoot)"
                "\n    MATCH (nr)<-[r:USES_VALUE]-(consumer)"
            ),
            "used by name",
        ),
        (
            (
                "MATCH (:CTTermRoot {uid: uid})-[:HAS_NAME_ROOT]->(:CTTermNameRoot)"
                "-[:HAS_VERSION]->(nv)\n    MATCH (nv)<-[r:USES_VALUE]-(consumer)"
            ),
            "used by name",
        ),
    )
]


def get_term_usage(uids: list[str]) -> dict[str, list[dict[str, Any]]]:
    """Returns what refers to each of these terms, or an empty list where nothing does.

    Three queries rather than one union, because they are cheap on the handful of terms a
    release ever puts up for retirement and because a `UNION` inside a scoped call is the
    sort of Cypher that is easy to get subtly wrong and hard to notice.
    """

    if not uids:
        return {}

    usage: dict[str, list[dict[str, Any]]] = {uid: [] for uid in uids}
    for query in TERM_USAGE_QUERIES:
        for record in mdr_query(query, {"uids": uids}):
            usage[record["uid"]].append(_usage_entry(record))
    return usage


# What a term leaving or re-valuing in *one codelist* can break. Narrower than
# `TERM_USAGE_QUERIES`, which asks about the term wherever it is used.
#
# A `CTTermContext` records the codelist it selected the term through, so only
# contexts naming this codelist are affected; one that picked the same term through
# another codelist is untouched by this membership changing. A context naming no
# codelist at all is counted: calling it harmless would be a guess.
#
# The two "used by name" arms are absent: they hang off the term's *name*, which a
# membership change does not touch.
MEMBERSHIP_USAGE_QUERIES = [
    _usage_query(
        "UNWIND $pairs AS pair",
        match,
        "pair.codelist AS codelist, pair.term AS uid",
        through,
        where,
    )
    for match, through, where in (
        (
            (
                "MATCH (:CTTermRoot {uid: pair.term})<-[:HAS_SELECTED_TERM]-"
                "(ctx:CTTermContext)<-[r]-(consumer)"
            ),
            "selected in context",
            (
                "NOT (ctx)-[:HAS_SELECTED_CODELIST]->(:CTCodelistRoot) "
                "OR (ctx)-[:HAS_SELECTED_CODELIST]->"
                "(:CTCodelistRoot {uid: pair.codelist})"
            ),
        ),
    )
]


def get_membership_usage(
    pairs: list[tuple[str, str]],
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """Returns what refers to each (codelist, term) pair, or an empty list where
    nothing does — the references a change to that one membership could break.

    Not `get_term_usage`: that answers "can this term be retired", this answers "who
    notices this term leaving or re-valuing in this codelist".
    """

    if not pairs:
        return {}

    usage: dict[tuple[str, str], list[dict[str, Any]]] = {pair: [] for pair in pairs}
    params = {
        "pairs": [{"codelist": codelist, "term": term} for codelist, term in pairs]
    }
    for query in MEMBERSHIP_USAGE_QUERIES:
        for record in mdr_query(query, params):
            usage[(record["codelist"], record["uid"])].append(_usage_entry(record))
    return usage


def get_term_name_versions(uids: list[str]) -> dict[str, str]:
    """Returns the open name version of each term, so a new one can be numbered after it."""

    if not uids:
        return {}

    records = mdr_query(
        """
        MATCH (root:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[hv:HAS_VERSION]->()
        WHERE root.uid IN $uids AND hv.end_date IS NULL
        RETURN root.uid AS uid, hv.version AS version
        """,
        {"uids": uids},
    )
    return {record["uid"]: record["version"] for record in records}


def get_paired_codelists(uids: list[str]) -> set[str]:
    """Returns which of these codelists MDR already pairs with a code codelist."""

    records = mdr_query(
        """
        MATCH (c:CTCodelistRoot)-[:PAIRED_CODE_CODELIST]->(:CTCodelistRoot)
        WHERE c.uid IN $uids
        RETURN c.uid AS uid
        """,
        {"uids": uids},
    )
    return {record["uid"] for record in records}


# --- writes ---------------------------------------------------------------------


def ensure_library() -> None:
    mdr_query(
        """
        MERGE (lib:Library {name: $name})
        ON CREATE SET lib.is_editable = false
        """,
        {"name": CDISC_LIBRARY},
    )


def ensure_packages(packages: list[dict[str, Any]], author_id: str) -> None:
    """Creates the catalogues and packages of this release."""

    mdr_query(
        """
        MATCH (lib:Library {name: $library})
        UNWIND $packages AS pkg
        MERGE (lib)-[:CONTAINS_CATALOGUE]->(cat:CTCatalogue {name: pkg.catalogue_name})
        MERGE (cat)-[:CONTAINS_PACKAGE]->(p:CTPackage {uid: pkg.uid})
        ON CREATE SET p.name = pkg.name,
                      p.label = pkg.label,
                      p.description = pkg.description,
                      p.registration_status = pkg.registration_status,
                      p.source = pkg.source,
                      p.href = pkg.href,
                      p.effective_date = date(pkg.effective_date),
                      p.import_date = datetime(),
                      p.author_id = $author_id
        """,
        {"library": CDISC_LIBRARY, "packages": packages, "author_id": author_id},
    )
    # Chain each package to the one it supersedes, where that one is in MDR.
    mdr_query(
        """
        UNWIND $packages AS pkg
        WITH pkg WHERE pkg.prior_uid IS NOT NULL
        MATCH (p:CTPackage {uid: pkg.uid})
        MATCH (prior:CTPackage {uid: pkg.prior_uid})
        MERGE (prior)-[:NEXT_PACKAGE]->(p)
        """,
        {"packages": packages},
    )


def ensure_codelist_roots(uids: list[str]) -> None:
    """Creates the root nodes of codelists that are new to MDR."""

    mdr_query(
        """
        MATCH (lib:Library {name: $library})
        UNWIND $uids AS uid
        MERGE (root:CTCodelistRoot {uid: uid})
        MERGE (lib)-[:CONTAINS_CODELIST]->(root)
        MERGE (root)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)
        MERGE (root)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)
        """,
        {"library": CDISC_LIBRARY, "uids": uids},
    )


def ensure_term_roots(uids: list[str]) -> None:
    """Creates the root nodes of terms that are new to MDR."""

    mdr_query(
        """
        MATCH (lib:Library {name: $library})
        UNWIND $uids AS uid
        MERGE (root:CTTermRoot {uid: uid})
        MERGE (lib)-[:CONTAINS_TERM]->(root)
        MERGE (root)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)
        MERGE (root)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)
        """,
        {"library": CDISC_LIBRARY, "uids": uids},
    )


def link_codelists_to_catalogues(rows: list[dict[str, Any]]) -> None:
    """Records which catalogue each codelist appears in."""

    mdr_query(
        """
        UNWIND $rows AS row
        MATCH (cat:CTCatalogue {name: row.catalogue_name})
        MATCH (root:CTCodelistRoot {uid: row.codelist_uid})
        MERGE (cat)-[:HAS_CODELIST]->(root)
        """,
        {"rows": rows},
    )


def close_versions(label: str, root_label: str, rows: list[dict[str, Any]]) -> None:
    """Ends the open version of each changed concept, as of the release's date.

    Moves `LATEST` and `LATEST_FINAL` off the value being closed. `LATEST_DRAFT` and
    `LATEST_RETIRED` are left alone — they are historical pointers, not current-status
    flags, and may legitimately point at this same value.
    """

    if not rows:
        return

    mdr_query(
        f"""
        UNWIND $rows AS row
        MATCH (root:{root_label} {{uid: row.uid}})-[:HAS_ATTRIBUTES_ROOT]->(ar:{label})-[hv:HAS_VERSION]->(value)
        WHERE hv.end_date IS NULL
        SET hv.end_date = datetime(row.effective_date)
        WITH ar, value
        OPTIONAL MATCH (ar)-[latest:LATEST]->(value)
        DELETE latest
        WITH ar, value
        OPTIONAL MATCH (ar)-[final:LATEST_FINAL]->(value)
        DELETE final
        """,
        {"rows": rows},
    )


def create_attribute_versions(
    root_label: str,
    attributes_root_label: str,
    value_label: str,
    rows: list[dict[str, Any]],
    author_id: str,
) -> None:
    """Creates the new attributes version of each concept this release changes."""

    if not rows:
        return

    mdr_query(
        f"""
        UNWIND $rows AS row
        MATCH (root:{root_label} {{uid: row.uid}})-[:HAS_ATTRIBUTES_ROOT]->(ar:{attributes_root_label})
        CREATE (ar)-[:HAS_VERSION {{
            start_date: datetime(row.effective_date),
            end_date: NULL,
            version: row.version,
            status: 'Final',
            author_id: $author_id,
            change_description: row.change_description
        }}]->(value:{value_label})
        SET value += row.props
        MERGE (ar)-[:LATEST]->(value)
        MERGE (ar)-[:LATEST_FINAL]->(value)
        """,
        {"rows": rows, "author_id": author_id},
    )


def create_name_versions(
    root_label: str,
    name_root_label: str,
    value_label: str,
    rows: list[dict[str, Any]],
    author_id: str,
) -> None:
    """Creates the first name version of concepts new to MDR.

    Only for new concepts. The sponsor preferred name of an existing concept is
    editable through the main API — it is the one thing that API allows in the CDISC
    library — so re-importing must not quietly revert somebody's edit. The CDISC name
    itself is never lost: it lives in the attributes half, which the import does own.
    """

    if not rows:
        return

    mdr_query(
        f"""
        UNWIND $rows AS row
        MATCH (root:{root_label} {{uid: row.uid}})-[:HAS_NAME_ROOT]->(nr:{name_root_label})
        WHERE NOT (nr)-[:HAS_VERSION]->()
        CREATE (nr)-[:HAS_VERSION {{
            start_date: datetime(row.effective_date),
            end_date: NULL,
            version: '1.0',
            status: 'Final',
            author_id: $author_id,
            change_description: 'Initial CDISC import'
        }}]->(value:{value_label})
        SET value += row.props
        MERGE (nr)-[:LATEST]->(value)
        MERGE (nr)-[:LATEST_FINAL]->(value)
        """,
        {"rows": rows, "author_id": author_id},
    )


def create_package_codelists(rows: list[dict[str, Any]]) -> None:
    """Records which codelists a package held, and at which version."""

    if not rows:
        return

    mdr_query(
        """
        UNWIND $rows AS row
        MATCH (pkg:CTPackage {uid: row.package_uid})
        MATCH (root:CTCodelistRoot {uid: row.codelist_uid})-[:HAS_ATTRIBUTES_ROOT]->(ar)-[hv:HAS_VERSION]->(value)
        WHERE hv.end_date IS NULL
        MERGE (pkg)-[:CONTAINS_CODELIST]->(pc:CTPackageCodelist {uid: row.uid})
        MERGE (pc)-[:CONTAINS_ATTRIBUTES]->(value)
        """,
        {"rows": rows},
    )


def create_package_terms(rows: list[dict[str, Any]]) -> None:
    """Records which terms a package's codelist held, and at which version."""

    if not rows:
        return

    mdr_query(
        """
        UNWIND $rows AS row
        MATCH (pc:CTPackageCodelist {uid: row.package_codelist_uid})
        MATCH (root:CTTermRoot {uid: row.term_uid})-[:HAS_ATTRIBUTES_ROOT]->(ar)-[hv:HAS_VERSION]->(value)
        WHERE hv.end_date IS NULL
        MERGE (pt:CTPackageTerm {uid: row.uid})
        MERGE (pc)-[:CONTAINS_TERM]->(pt)
        MERGE (pt)-[:CONTAINS_ATTRIBUTES]->(value)
        MERGE (root)<-[:HAS_TERM_ROOT]-(ct:CTCodelistTerm {submission_value: row.submission_value})
        MERGE (pt)-[:CONTAINS_SUBMISSION_VALUE]->(ct)
        """,
        {"rows": rows},
    )


def pair_codelists(rows: list[dict[str, Any]]) -> None:
    """Records which code codelist each name codelist pairs with."""

    if not rows:
        return

    mdr_query(
        """
        UNWIND $rows AS row
        MATCH (names:CTCodelistRoot {uid: row.codelist_uid})
        MATCH (codes:CTCodelistRoot {uid: row.paired_uid})
        MERGE (names)-[:PAIRED_CODE_CODELIST]->(codes)
        """,
        {"rows": rows},
    )


def set_term_names(rows: list[dict[str, Any]]) -> None:
    """Applies a settled sponsor name to a term's open name version.

    Only touches terms whose name version this import created, which is why the match
    requires the version to start at this release: an existing term's name belongs to
    whoever edited it last.
    """

    if not rows:
        return

    mdr_query(
        """
        UNWIND $rows AS row
        MATCH (root:CTTermRoot {uid: row.uid})-[:HAS_NAME_ROOT]->(nr)-[hv:HAS_VERSION]->(value)
        WHERE hv.end_date IS NULL AND hv.start_date = datetime(row.effective_date)
        SET value.name = row.name, value.name_sentence_case = row.name_sentence_case
        """,
        {"rows": rows},
    )


def add_memberships(rows: list[dict[str, Any]], author_id: str) -> None:
    """Opens the codelist memberships this release introduces."""

    if not rows:
        return

    mdr_query(
        """
        UNWIND $rows AS row
        MATCH (root:CTCodelistRoot {uid: row.codelist_uid})
        MATCH (term:CTTermRoot {uid: row.term_uid})
        MERGE (term)<-[:HAS_TERM_ROOT]-(ct:CTCodelistTerm {submission_value: row.submission_value})
        WITH root, ct, row
        // Deliberately not `MERGE (root)-[:HAS_TERM]->(ct)`: that matches a *closed*
        // membership too, so a term that left the codelist and later came back would
        // silently stay out. Memberships are versioned like everything else — at most
        // one open at a time, and a return opens a new one, leaving the gap visible.
        OPTIONAL MATCH (root)-[open:HAS_TERM]->(ct) WHERE open.end_date IS NULL
        WITH root, ct, row, open
        WHERE open IS NULL
        CREATE (root)-[:HAS_TERM {
            start_date: datetime(row.effective_date),
            author_id: $author_id,
            // Null for a term with no rank, which Neo4j stores as no property at
            // all — exactly what an unscored member should have.
            ordinal: row.ordinal
        }]->(ct)
        """,
        {"rows": rows, "author_id": author_id},
    )


def retire_terms(rows: list[dict[str, Any]], author_id: str) -> None:
    """Retires sponsor terms a release supersedes, both halves, as of its effective date.

    Mirrors what `library_item_repository._recreate_relationship` does when the main API
    inactivates a term: the open version is closed, a new one carrying the **same** version
    number and a status of `Retired` is opened over the *same* value node — nothing about
    the term changed, only its standing — and `LATEST_RETIRED` moves to it. `LATEST` and
    `LATEST_FINAL` are left where they are; they are historical pointers, and the value
    they point at is this same node anyway.

    Both halves, because a term retired in name and Final in attributes is a state nothing
    else in OSB produces. The name half is the one the main API's uniqueness rule reads,
    and retiring it is what makes the collision resolvable at all.

    The one thing this does not do is touch memberships — neither does the main API — so
    `close_sponsor_memberships` is the other half of every retirement.
    """

    if not rows:
        return

    mdr_query(
        """
        UNWIND $rows AS row
        MATCH (root:CTTermRoot {uid: row.uid})-[:HAS_NAME_ROOT|HAS_ATTRIBUTES_ROOT]->(vr)
              -[hv:HAS_VERSION]->(value)
        // Skipping a version already retired is what makes a re-run of a failed import
        // a no-op here rather than a second retirement stacked on the first.
        WHERE hv.end_date IS NULL AND hv.status <> 'Retired'
        SET hv.end_date = datetime(row.effective_date)
        WITH vr, value, hv, row
        CALL (vr) {
            MATCH (vr)-[stale:LATEST_RETIRED]->()
            DELETE stale
        }
        CREATE (vr)-[:HAS_VERSION {
            start_date: datetime(row.effective_date),
            end_date: NULL,
            version: hv.version,
            status: 'Retired',
            author_id: $author_id,
            change_description: row.change_description
        }]->(value)
        MERGE (vr)-[:LATEST_RETIRED]->(value)
        """,
        {"rows": rows, "author_id": author_id},
    )


def close_sponsor_memberships(rows: list[dict[str, Any]], author_id: str) -> None:
    """Takes a sponsor term out of one codelist, without deleting anything.

    Matched on the codelist and the term rather than on a submission value, unlike
    `end_memberships`: that one closes a membership this release is replacing and knows
    exactly which value it carried, while this one is acting on a term the release has
    never seen.

    The `HAS_PARAMETER_TERM` edge goes too. The main API's own `remove_term` deletes it,
    and leaving it would keep the term offered as a template parameter of a codelist it
    is no longer in. The `TemplateParameterTermRoot` label stays: other codelists may
    still be using the term that way.
    """

    if not rows:
        return

    mdr_query(
        """
        UNWIND $rows AS row
        MATCH (root:CTCodelistRoot {uid: row.codelist_uid})-[ht:HAS_TERM]->(ct:CTCodelistTerm)
              -[:HAS_TERM_ROOT]->(term:CTTermRoot {uid: row.term_uid})
        WHERE ht.end_date IS NULL
        SET ht.end_date = datetime(row.effective_date), ht.author_id = $author_id
        WITH root, term
        CALL (root, term) {
            MATCH (root)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST]->(codelist_name)
            MATCH (codelist_name)-[parameter:HAS_PARAMETER_TERM]->(:CTTermNameRoot)
                  <-[:HAS_NAME_ROOT]-(term)
            DELETE parameter
        }
        """,
        {"rows": rows, "author_id": author_id},
    )


def append_name_versions(rows: list[dict[str, Any]], author_id: str) -> None:
    """Gives a term already in MDR a new sponsor preferred name, as a new version.

    The exception to "the import only ever creates the name half, and never touches an
    existing one" — see `create_name_versions`. That rule exists so re-importing cannot
    quietly revert somebody's edit; an explicit decision on a `SPONSOR_NAME_DIVERGED`
    finding is not quiet, and the previous name is kept as a closed version either way.

    A new value node, unlike a retirement: the name really is different, and the old one
    has to stay readable at the version that carried it.
    """

    if not rows:
        return

    mdr_query(
        """
        UNWIND $rows AS row
        MATCH (root:CTTermRoot {uid: row.uid})-[:HAS_NAME_ROOT]->(nr:CTTermNameRoot)
              -[hv:HAS_VERSION]->()
        // A version already starting at this release is one this run wrote, so a retry
        // leaves it alone instead of stacking another on top.
        WHERE hv.end_date IS NULL AND hv.start_date <> datetime(row.effective_date)
        SET hv.end_date = datetime(row.effective_date)
        WITH nr, row
        CALL (nr) {
            MATCH (nr)-[stale:LATEST|LATEST_FINAL]->()
            DELETE stale
        }
        CREATE (nr)-[:HAS_VERSION {
            start_date: datetime(row.effective_date),
            end_date: NULL,
            version: row.version,
            status: 'Final',
            author_id: $author_id,
            change_description: row.change_description
        }]->(value:CTTermNameValue {
            name: row.name, name_sentence_case: row.name_sentence_case
        })
        MERGE (nr)-[:LATEST]->(value)
        MERGE (nr)-[:LATEST_FINAL]->(value)
        """,
        {"rows": rows, "author_id": author_id},
    )


def end_memberships(rows: list[dict[str, Any]], author_id: str) -> None:
    """Closes memberships this release drops, rather than deleting them.

    A term leaving a codelist is part of its history, and studies already built against
    the old package still have to resolve it.
    """

    if not rows:
        return

    mdr_query(
        """
        UNWIND $rows AS row
        MATCH (root:CTCodelistRoot {uid: row.codelist_uid})-[ht:HAS_TERM]->(ct:CTCodelistTerm)
              -[:HAS_TERM_ROOT]->(term:CTTermRoot {uid: row.term_uid})
        WHERE ht.end_date IS NULL AND ct.submission_value = row.submission_value
        SET ht.end_date = datetime(row.effective_date), ht.author_id = $author_id
        """,
        {"rows": rows, "author_id": author_id},
    )
