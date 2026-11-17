"""Grouping one CDISC release and reading back what its catalogues said.

Ported from the grouping step of `import_standards/cdisc_staging.py`. Every statement
there was already anchored on `(:RawPackage {effectiveDate: …})`; what the script
wrapped in a loop over all dates is here driven by one date supplied by the caller.

Findings themselves live in `inconsistency_repository` — this module only reads the
raw layer and writes the grouped one.

Requires APOC (`apoc.map.fromPairs`) and the scoped `CALL (…) { … }` syntax.
"""

import logging
from typing import Any

from standards_import.config import settings
from standards_import.repositories.staging_db import (
    StagingSession,
    run_query,
    run_query_autocommit,
)

log = logging.getLogger(__name__)

DELETE_BATCH_ROWS = 10000
# " YYYY-MM-DD": the separator plus an ISO date.
DATE_SUFFIX_LENGTH = 11


def clear_derived_layer(session: StagingSession, package_date: str) -> None:
    """Removes everything grouping derives for this release.

    Analysis rebuilds the grouped layer with `MERGE`, which would otherwise leave
    behind concepts the re-uploaded files no longer contain. Review items are not
    touched: they hang off the `EffectiveDateImport`, precisely so that the decisions
    attached to them survive this. The `HAS_INCONSISTENCY` arm of the first pattern
    clears the older `Inconsistent*` nodes that the bootstrap script wrote, should this
    release have been staged by that route.

    The review snapshot is derived too (see `review_snapshot_repository`): its stamp is
    cleared first, so that nothing vouches for rows while they are being swept away,
    and its `TermChange` nodes go with the rest. Its codelist rows live on the
    `GroupedCodelist` nodes, which go anyway.
    """

    run_query(
        session,
        """
        MATCH (import:EffectiveDateImport {effective_date: $package_date})
        SET import.review_snapshot_at = NULL,
            import.review_snapshot_mdr_head = NULL,
            import.review_snapshot_summary = NULL
        """,
        parameters={"package_date": package_date},
    )
    run_query_autocommit(
        session,
        f"""
        MATCH (:RawPackage {{effectiveDate: $package_date}})-[:HAS_TERM_CHANGE]->(change:TermChange)
        CALL (change) {{
            DETACH DELETE change
        }} IN TRANSACTIONS OF {DELETE_BATCH_ROWS} ROWS
        """,
        parameters={"package_date": package_date},
    )

    # The batch size is interpolated rather than parameterised: Cypher does not accept a
    # parameter in `IN TRANSACTIONS OF … ROWS`. Both it and the labels are constants
    # defined in this module, so nothing user-supplied reaches the statement.
    for anchor, group_rel in (
        ("GroupedCodelist", "HAS_GROUPED_CODELIST"),
        ("GroupedTerm", "HAS_GROUPED_TERM"),
    ):
        run_query_autocommit(
            session,
            f"""
            MATCH (:RawPackage {{effectiveDate: $package_date}})-[:{group_rel}]->(:{anchor})
                  -[:HAS_GROUPED_PROPERTIES|HAS_INCONSISTENCY]->(derived)
            CALL (derived) {{
                DETACH DELETE derived
            }} IN TRANSACTIONS OF {DELETE_BATCH_ROWS} ROWS
            """,
            parameters={"package_date": package_date},
        )
        run_query_autocommit(
            session,
            f"""
            MATCH (:RawPackage {{effectiveDate: $package_date}})-[:{group_rel}]->(grouped:{anchor})
            CALL (grouped) {{
                DETACH DELETE grouped
            }} IN TRANSACTIONS OF {DELETE_BATCH_ROWS} ROWS
            """,
            parameters={"package_date": package_date},
        )


def get_catalogues(session: StagingSession, package_date: str) -> list[str]:
    """Returns the catalogue names staged for this release."""

    records = run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_RAW_CATALOGUE]->(cat:RawCatalogue)
        RETURN cat.name AS name ORDER BY name
        """,
        parameters={"package_date": package_date},
    )
    return [record["name"] for record in records]


def catalogue_name(package_name: str) -> str:
    """Strips the trailing effective date, leaving `SDTM CT` from `SDTM CT 2025-09-26`."""

    return (
        package_name[:-DATE_SUFFIX_LENGTH].strip()
        if len(package_name) > DATE_SUFFIX_LENGTH
        else package_name
    )


def get_codelist_cids(session: StagingSession, package_date: str) -> list[str]:
    records = run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_RAW_CATALOGUE]-(:RawCatalogue)-[]-(cl:RawCodelist)
        RETURN DISTINCT cl.conceptId as cid ORDER BY cid
        """,
        parameters={"package_date": package_date},
    )
    return [record["cid"] for record in records]


def create_grouped_codelists(
    session: StagingSession, package_date: str, codelist_cids: list[str]
) -> None:
    """Collapses the per-catalogue definitions of each codelist into one node."""

    for batch in batched(codelist_cids, settings.staging_batch_size):
        run_query(
            session,
            """
            MATCH (p:RawPackage {effectiveDate: $package_date})
            UNWIND $codelist_cids as codelist_cid
                MERGE (p)-[:HAS_GROUPED_CODELIST]->(gc:GroupedCodelist:CDISCStaging {conceptId: codelist_cid})
                WITH p, gc, codelist_cid
                MATCH (p)-[:HAS_RAW_CATALOGUE]-(:RawCatalogue)-[:HAS_RAW_CODELIST]->(cl:RawCodelist {conceptId: codelist_cid})
                MERGE (cl)<-[:SOURCE_CODELIST_DEF]-(gc)
            """,
            parameters={"package_date": package_date, "codelist_cids": batch},
        )


def get_term_cids(
    session: StagingSession, package_date: str, start: int, nbr: int
) -> list[str]:
    records = run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_RAW_CATALOGUE]-(:RawCatalogue)-[]-(:RawCodelist)--(t:RawTerm)
        RETURN DISTINCT t.conceptId as cid ORDER BY cid SKIP $start LIMIT $nbr
        """,
        parameters={"package_date": package_date, "start": start, "nbr": nbr},
    )
    return [record["cid"] for record in records]


def create_grouped_terms(
    session: StagingSession, package_date: str, term_cids: list[str]
) -> None:
    """Collapses the per-catalogue definitions of each term into one node."""

    run_query(
        session,
        """
        MATCH (p:RawPackage {effectiveDate: $package_date})
        UNWIND $term_cids as term_cid
            MERGE (p)-[:HAS_GROUPED_TERM]->(gt:GroupedTerm:CDISCStaging {conceptId: term_cid})
            WITH p, gt, term_cid
            MATCH (p)-[:HAS_RAW_CATALOGUE]-(:RawCatalogue)-[:HAS_RAW_CODELIST]->(:RawCodelist)-[:HAS_RAW_TERM]->(t:RawTerm {conceptId: term_cid})
            MERGE (t)<-[:SOURCE_TERM_DEF]-(gt)
        """,
        parameters={"package_date": package_date, "term_cids": term_cids},
    )


def add_grouped_codelist_terms(
    session: StagingSession, package_date: str, codelist_cid: str
) -> None:
    """Attaches terms to a grouped codelist, collecting every submission value seen."""

    terms = run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_RAW_CATALOGUE]-(:RawCatalogue)-[]-(:RawCodelist {conceptId: $codelist_cid})--(t:RawTerm)
        RETURN DISTINCT t.conceptId as cid, t.submissionValue as submval ORDER BY cid
        """,
        parameters={"package_date": package_date, "codelist_cid": codelist_cid},
    )
    if not terms:
        return

    run_query(
        session,
        """
        MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]-(gc:GroupedCodelist {conceptId: $codelist_cid})
        WITH DISTINCT gc, p
        UNWIND $terms as term
            MATCH (p)-[:HAS_GROUPED_TERM]->(gt:GroupedTerm {conceptId: term.cid})
            MERGE (gc)-[ht:HAS_GROUPED_TERM_MEMBER]->(gt)
            ON CREATE SET ht.rawSubmissionValues = [term.submval], ht.submissionValue = term.submval
            ON MATCH SET ht.rawSubmissionValues = CASE WHEN term.submval IN ht.rawSubmissionValues THEN ht.rawSubmissionValues ELSE ht.rawSubmissionValues + term.submval END
        """,
        parameters={
            "package_date": package_date,
            "codelist_cid": codelist_cid,
            "terms": terms,
        },
    )


def get_codelist_properties(
    session: StagingSession, package_date: str
) -> list[dict[str, Any]]:
    """Returns, per codelist, every catalogue's definition of it and its terms."""

    return run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_RAW_CATALOGUE]-(:RawCatalogue)-[]-(cl:RawCodelist) WITH DISTINCT cl.conceptId as cid ORDER BY cid
        CALL (cid) {
            MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]-(gc:GroupedCodelist {conceptId: cid})-[:SOURCE_CODELIST_DEF]->(rc:RawCodelist)-[]-(rcat:RawCatalogue)
            WITH *, [(rc)-[:HAS_RAW_TERM]-(rt:RawTerm) | [rt.conceptId, rt.submissionValue]] AS terms_cid_sumbval
            WITH collect(rc) as raw_defs, collect(rcat) as raw_cats, collect(apoc.map.fromPairs(terms_cid_sumbval)) as cl_terms
            RETURN raw_defs, raw_cats, cl_terms
        }
        RETURN cid, raw_defs, raw_cats, cl_terms
        """,
        parameters={"package_date": package_date},
    )


def get_term_properties(
    session: StagingSession, package_date: str, start: int, nbr: int
) -> list[dict[str, Any]]:
    """Returns, per term, every catalogue's definition of it."""

    return run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_RAW_CATALOGUE]-(:RawCatalogue)-[]-(:RawCodelist)--(t:RawTerm) WITH DISTINCT t.conceptId as cid ORDER BY cid SKIP $start LIMIT $nbr
        CALL (cid) {
            MATCH (p:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_TERM]-(gt:GroupedTerm {conceptId: cid})-[:SOURCE_TERM_DEF]->(rt:RawTerm)-[]-(:RawCodelist)-[]-(rcat:RawCatalogue)
            RETURN collect(rt) as raw_defs, collect(rcat) as raw_cats
        }
        RETURN cid, raw_defs, raw_cats
        """,
        parameters={"package_date": package_date, "start": start, "nbr": nbr},
    )


def get_submission_value_conflicts(
    session: StagingSession, package_date: str
) -> list[dict[str, Any]]:
    """Returns each codelist/term pairing whose submission value is disputed or quoted.

    Unlike the aggregated `rawSubmissionValues` on the grouped relationship, this keeps
    the catalogue each value came from — without which a reviewer cannot tell who said
    what, and `PREFER_CATALOGUE` has nothing to work with.
    """

    return run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_RAW_CATALOGUE]->(cat:RawCatalogue)
              -[:HAS_RAW_CODELIST]->(cl:RawCodelist)-[:HAS_RAW_TERM]->(t:RawTerm)
        WITH cl.conceptId AS codelist_cid, t.conceptId AS term_cid,
             collect({catalogue: cat.name, submission_value: t.submissionValue}) AS entries
        WITH codelist_cid, term_cid, entries,
             [entry IN entries | entry.submission_value] AS values
        WHERE size(apoc.coll.toSet(values)) > 1
           OR any(v IN values WHERE v STARTS WITH '"' AND v ENDS WITH '"')
        RETURN codelist_cid, term_cid, entries
        ORDER BY codelist_cid, term_cid
        """,
        parameters={"package_date": package_date},
    )


def get_codelists_by_term(
    session: StagingSession, package_date: str
) -> dict[str, list[dict[str, Any]]]:
    """Returns, per term, the codelists it belongs to and its submission value in each.

    The submission value is per membership, not per term: more than half of all terms
    carry a different one in each codelist they belong to.
    """

    records = run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]->(gc:GroupedCodelist)
              -[ht:HAS_GROUPED_TERM_MEMBER]->(gt:GroupedTerm)
        RETURN gt.conceptId AS term_id,
               collect(DISTINCT {codelist_id: gc.conceptId, submission_value: ht.submissionValue}) AS memberships
        """,
        parameters={"package_date": package_date},
    )
    return {record["term_id"]: record["memberships"] for record in records}


def save_codelist_properties(
    session: StagingSession, codelists: list[dict[str, Any]]
) -> None:
    """Stores the agreed properties of codelists, conflicts already settled."""

    for batch in batched(codelists, settings.staging_batch_size):
        run_query(
            session,
            """
            UNWIND $codelists as props
            MATCH (p:RawPackage {effectiveDate: props.package_date})-[:HAS_GROUPED_CODELIST]-(gc:GroupedCodelist {conceptId: props.codelist_cid})
            MERGE (gc)-[:HAS_GROUPED_PROPERTIES]->(cp:GroupedCodelistProperties:CDISCStaging)
            SET cp += props.cl_props
            """,
            parameters={"codelists": batch},
        )


def save_term_properties(session: StagingSession, terms: list[dict[str, Any]]) -> None:
    """Stores the agreed properties of terms, conflicts already settled."""

    for batch in batched(terms, settings.staging_batch_size):
        run_query(
            session,
            """
            UNWIND $terms as props
            MATCH (p:RawPackage {effectiveDate: props.package_date})-[:HAS_GROUPED_TERM]-(gt:GroupedTerm {conceptId: props.term_cid})
            MERGE (gt)-[:HAS_GROUPED_PROPERTIES]->(tp:GroupedTermProperties:CDISCStaging)
            SET tp += props.term_props
            """,
            parameters={"terms": batch},
        )


def set_grouped_submission_value(
    session: StagingSession, package_date: str, rows: list[dict[str, Any]]
) -> None:
    """Applies a settled submission value to the grouped codelist/term relationship."""

    if not rows:
        return

    run_query(
        session,
        """
        UNWIND $rows AS row
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]->(gc:GroupedCodelist {conceptId: row.codelist_cid})
              -[ht:HAS_GROUPED_TERM_MEMBER]->(:GroupedTerm {conceptId: row.term_cid})
        SET ht.submissionValue = row.submission_value
        """,
        parameters={"package_date": package_date, "rows": rows},
    )


def drop_terms_from_codelists(
    session: StagingSession, package_date: str, rows: list[dict[str, Any]]
) -> None:
    """Removes settled-away terms from their grouped codelist."""

    if not rows:
        return

    run_query(
        session,
        """
        UNWIND $rows AS row
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]->(gc:GroupedCodelist {conceptId: row.codelist_cid})
              -[ht:HAS_GROUPED_TERM_MEMBER]->(:GroupedTerm {conceptId: row.term_cid})
        DELETE ht
        """,
        parameters={"package_date": package_date, "rows": rows},
    )


def count_grouped_concepts(
    session: StagingSession, package_date: str
) -> dict[str, int]:
    records = run_query(
        session,
        """
        MATCH (p:RawPackage {effectiveDate: $package_date})
        RETURN COUNT { (p)-[:HAS_GROUPED_CODELIST]->(:GroupedCodelist) } AS codelist_count,
               COUNT { (p)-[:HAS_GROUPED_TERM]->(:GroupedTerm) } AS term_count
        """,
        parameters={"package_date": package_date},
    )
    if not records:
        return {"codelist_count": 0, "term_count": 0}
    return records[0]


def batched(rows: list[Any], size: int) -> list[list[Any]]:
    return [rows[start : start + size] for start in range(0, len(rows), size)]
