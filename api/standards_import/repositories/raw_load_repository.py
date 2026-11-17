"""Loads one CDISC package file into the raw layer of the staging database.

Ported from the raw-load step of `import_standards/cdisc_staging.py`, narrowed to a
single catalogue file. Two things are done differently compared to that script:

* the prior-version link is a query of its own, so a missing predecessor is reported
  rather than silently dropping the row of a combined statement;
* codelists and terms are written in batched `UNWIND` statements instead of one
  transaction per codelist and one `FOREACH` over a whole term list.
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


def merge_catalogue(session: StagingSession, package_props: dict[str, Any]) -> None:
    """Creates the package and catalogue nodes for this file."""

    run_query(
        session,
        """
        MERGE (p:RawPackage:CDISCStaging {effectiveDate: $props.effectiveDate})
        MERGE (p)-[:HAS_RAW_CATALOGUE]->(cat:RawCatalogue:CDISCStaging {name: $props.name})
        SET cat += $props
        """,
        parameters={"props": package_props},
    )


def merge_codelists(
    session: StagingSession, package_name: str, codelists: list[dict[str, Any]]
) -> None:
    """Creates the codelist nodes of this catalogue, in batches."""

    for batch in _batched(codelists, settings.staging_batch_size):
        run_query(
            session,
            """
            MATCH (cat:RawCatalogue {name: $package_name})
            UNWIND $codelists AS props
                MERGE (cat)-[:HAS_RAW_CODELIST]->(cl:RawCodelist:CDISCStaging {conceptId: props.conceptId})
                SET cl += props
            """,
            parameters={"package_name": package_name, "codelists": batch},
        )


def merge_terms(
    session: StagingSession, package_name: str, term_rows: list[dict[str, Any]]
) -> None:
    """Creates the term nodes of this catalogue, in batches.

    Each row is `{codelist_id, term}`. A term concept that appears in two codelists
    of the same catalogue gets a node under each, as in the original staging model.
    """

    for batch in _batched(term_rows, settings.staging_batch_size):
        run_query(
            session,
            """
            MATCH (cat:RawCatalogue {name: $package_name})
            UNWIND $rows AS row
                MATCH (cat)-[:HAS_RAW_CODELIST]->(cl:RawCodelist {conceptId: row.codelist_id})
                MERGE (cl)-[:HAS_RAW_TERM]->(t:RawTerm:CDISCStaging {conceptId: row.term.conceptId})
                SET t += row.term
            """,
            parameters={"package_name": package_name, "rows": batch},
        )


def link_prior_version(session: StagingSession, package_name: str) -> str | None:
    """Links this catalogue to the one it supersedes, matching on the CDISC links.

    Returns the name of the predecessor, or None when it is not in staging — which
    is expected for the very first release loaded, and a warning otherwise.
    """

    records = run_query(
        session,
        """
        MATCH (cat:RawCatalogue {name: $package_name})
        MATCH (prevcat:RawCatalogue {`_links.self.href`: cat.`_links.priorVersion.href`})
        MERGE (cat)-[:HAS_PRIOR_VERSION]->(prevcat)
        RETURN prevcat.name AS prior_name
        """,
        parameters={"package_name": package_name},
    )
    return records[0]["prior_name"] if records else None


def link_next_version(session: StagingSession, package_name: str) -> str | None:
    """Links any already-staged catalogue that supersedes this one.

    Only relevant when a file is re-uploaded or a release is loaded out of order;
    without it the successor would keep pointing at nothing.
    """

    records = run_query(
        session,
        """
        MATCH (cat:RawCatalogue {name: $package_name})
        MATCH (nextcat:RawCatalogue {`_links.priorVersion.href`: cat.`_links.self.href`})
        MERGE (nextcat)-[:HAS_PRIOR_VERSION]->(cat)
        RETURN nextcat.name AS next_name
        """,
        parameters={"package_name": package_name},
    )
    return records[0]["next_name"] if records else None


def link_codelist_prior_versions(session: StagingSession, package_name: str) -> None:
    """Links each codelist of this catalogue to its counterpart in the predecessor."""

    run_query(
        session,
        """
        MATCH (cat:RawCatalogue {name: $package_name})-[:HAS_PRIOR_VERSION]->(prevcat:RawCatalogue)
        MATCH (cat)-[:HAS_RAW_CODELIST]->(cl:RawCodelist)
        MATCH (prevcat)-[:HAS_RAW_CODELIST]->(prevcl:RawCodelist {conceptId: cl.conceptId})
        MERGE (cl)-[:HAS_PRIOR_VERSION]->(prevcl)
        """,
        parameters={"package_name": package_name},
    )


def delete_raw_catalogue(session: StagingSession, package_name: str) -> None:
    """Removes a catalogue and everything under it, so it can be loaded afresh.

    `SET x += props` never removes a property and `MERGE` never removes a node, so
    replacing a file means deleting what it previously produced. Deletion is batched
    because a single catalogue can hold six figures' worth of term nodes.
    """

    # The batch size is interpolated rather than parameterised: Cypher does not accept a
    # parameter in `IN TRANSACTIONS OF … ROWS`. DELETE_BATCH_ROWS is an int constant, so
    # there is nothing user-supplied in the statement.
    run_query_autocommit(
        session,
        f"""
        MATCH (:RawCatalogue {{name: $package_name}})-[:HAS_RAW_CODELIST]->(:RawCodelist)-[:HAS_RAW_TERM]->(t:RawTerm)
        CALL (t) {{
            DETACH DELETE t
        }} IN TRANSACTIONS OF {DELETE_BATCH_ROWS} ROWS
        """,
        parameters={"package_name": package_name},
    )
    run_query_autocommit(
        session,
        f"""
        MATCH (:RawCatalogue {{name: $package_name}})-[:HAS_RAW_CODELIST]->(cl:RawCodelist)
        CALL (cl) {{
            DETACH DELETE cl
        }} IN TRANSACTIONS OF {DELETE_BATCH_ROWS} ROWS
        """,
        parameters={"package_name": package_name},
    )
    run_query(
        session,
        """
        MATCH (cat:RawCatalogue {name: $package_name})
        DETACH DELETE cat
        """,
        parameters={"package_name": package_name},
    )


def _batched(rows: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [rows[start : start + size] for start in range(0, len(rows), size)]
