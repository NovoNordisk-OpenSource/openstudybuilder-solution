"""The stored rows of the release review lists, and the stamp saying they still hold.

What `review_snapshot_service` works out from the release-wide delta is kept in two
places, both inside the grouped layer so that re-analysis sweeps them up with
everything else it rebuilds (see `analysis_repository.clear_derived_layer`):

* per codelist, as properties of its `GroupedCodelist` — every codelist of the release
  gets a row, changed or not, because `show=all` lists the untouched ones too;
* per term, as a `TermChange` hung off the `RawPackage` — only the terms the release
  adds, changes or drops, which is what `list_terms` lists. A term the release drops
  has no `GroupedTerm` left to carry it, hence a node of its own rather than
  properties on the grouped one.

The stamp lives on the `EffectiveDateImport`: `review_snapshot_at` (null while there is
no usable snapshot) and `review_snapshot_mdr_head`, the MDR head the delta was taken
against. Alongside it, `review_snapshot_summary` holds the release-wide figures the
dashboard reads, as a JSON string. All three are written last, in one statement, so a
snapshot is never vouched for before its rows are all there.
"""

import json
import logging
from typing import Any

from standards_import.config import settings
from standards_import.repositories.analysis_repository import batched
from standards_import.repositories.staging_db import StagingSession, run_query

log = logging.getLogger(__name__)

CODELIST_ROW_FIELDS = (
    "name",
    "submission_value",
    "change_status",
    "term_new",
    "term_updated",
    "term_unchanged",
    "term_new_examples",
    "term_updated_examples",
    "memberships_added",
    "memberships_ended",
    "changed_in_scope",
)
"""What a codelist row stores on its `GroupedCodelist`, beyond the `conceptId` the node
already has. Interpolated into the queries below as property keys — constants of this
module, so nothing user-supplied reaches the statement."""


def save_codelist_rows(
    session: StagingSession, package_date: str, rows: list[dict[str, Any]]
) -> None:
    """Writes each codelist row onto its `GroupedCodelist`. A plain `SET`, so writing
    the same rows twice leaves the same thing behind."""

    assignments = ", ".join(
        f"gc.{field} = row.{field}" for field in CODELIST_ROW_FIELDS
    )
    for batch in batched(rows, settings.staging_batch_size):
        run_query(
            session,
            f"""
            UNWIND $rows AS row
            MATCH (:RawPackage {{effectiveDate: $package_date}})-[:HAS_GROUPED_CODELIST]->(gc:GroupedCodelist {{conceptId: row.codelist_id}})
            SET {assignments}
            """,
            parameters={"package_date": package_date, "rows": batch},
        )


def get_codelist_rows(
    session: StagingSession, package_date: str
) -> list[dict[str, Any]]:
    """Every stored codelist row of this release, in one read."""

    columns = ", ".join(f"gc.{field} AS {field}" for field in CODELIST_ROW_FIELDS)
    return run_query(
        session,
        f"""
        MATCH (:RawPackage {{effectiveDate: $package_date}})-[:HAS_GROUPED_CODELIST]->(gc:GroupedCodelist)
        WHERE gc.change_status IS NOT NULL
        RETURN gc.conceptId AS codelist_id, {columns}
        """,
        parameters={"package_date": package_date},
    )


def save_term_rows(
    session: StagingSession, package_date: str, rows: list[dict[str, Any]]
) -> None:
    """Writes one `TermChange` per term row, and removes those no longer listed.

    `MERGE` on `conceptId` rather than delete-then-create: two rebuilds running at once
    compute the same rows, and merging them twice leaves one set behind, where a delete
    from one could empty what the other had just written. `changes` is stored as JSON
    text, as `job.stats` is: Neo4j cannot hold a list of maps as a property.
    """

    for batch in batched(rows, settings.staging_batch_size):
        run_query(
            session,
            """
            MATCH (p:RawPackage {effectiveDate: $package_date})
            UNWIND $rows AS row
            MERGE (p)-[:HAS_TERM_CHANGE]->(tc:TermChange:CDISCStaging {conceptId: row.concept_id})
            SET tc.preferred_term = row.preferred_term,
                tc.change_status = row.change_status,
                tc.impacted = row.impacted,
                tc.changes = row.changes,
                tc.codelist_count = row.codelist_count,
                tc.covering_codelist_ids = row.covering_codelist_ids
            """,
            parameters={
                "package_date": package_date,
                "rows": [
                    {**row, "changes": json.dumps(row["changes"])} for row in batch
                ],
            },
        )

    listed = {row["concept_id"] for row in rows}
    stale = sorted(set(get_term_change_ids(session, package_date)) - listed)
    for batch in batched(stale, settings.staging_batch_size):
        run_query(
            session,
            """
            MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_TERM_CHANGE]->(tc:TermChange)
            WHERE tc.conceptId IN $concept_ids
            DETACH DELETE tc
            """,
            parameters={"package_date": package_date, "concept_ids": batch},
        )


def get_term_change_ids(session: StagingSession, package_date: str) -> list[str]:
    records = run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_TERM_CHANGE]->(tc:TermChange)
        RETURN tc.conceptId AS concept_id
        """,
        parameters={"package_date": package_date},
    )
    return [record["concept_id"] for record in records]


def get_term_rows(session: StagingSession, package_date: str) -> list[dict[str, Any]]:
    """Every stored term row of this release, in one read, `changes` decoded."""

    records = run_query(
        session,
        """
        MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_TERM_CHANGE]->(tc:TermChange)
        RETURN tc.conceptId AS concept_id,
               tc.preferred_term AS preferred_term,
               tc.change_status AS change_status,
               COALESCE(tc.impacted, []) AS impacted,
               tc.changes AS changes,
               COALESCE(tc.codelist_count, 0) AS codelist_count,
               COALESCE(tc.covering_codelist_ids, []) AS covering_codelist_ids
        """,
        parameters={"package_date": package_date},
    )
    for record in records:
        record["changes"] = json.loads(record["changes"]) if record["changes"] else []
    return records


def get_snapshot_stamp(
    session: StagingSession, package_date: str
) -> dict[str, Any] | None:
    """When the snapshot was taken, against which MDR head, and whether it carries the
    release summary — None for a release staging does not hold.

    `has_summary` rather than the summary itself: every page of the lists checks the
    stamp, and only the dashboard needs what the summary says.
    """

    records = run_query(
        session,
        """
        MATCH (import:EffectiveDateImport {effective_date: $package_date})
        RETURN import.review_snapshot_at AS snapshot_at,
               import.review_snapshot_mdr_head AS mdr_head,
               import.review_snapshot_summary IS NOT NULL AS has_summary
        """,
        parameters={"package_date": package_date},
    )
    return records[0] if records else None


def get_release_summary(
    session: StagingSession, package_date: str
) -> dict[str, Any] | None:
    records = run_query(
        session,
        """
        MATCH (import:EffectiveDateImport {effective_date: $package_date})
        RETURN import.review_snapshot_summary AS summary
        """,
        parameters={"package_date": package_date},
    )
    if not records or not records[0]["summary"]:
        return None
    return json.loads(records[0]["summary"])


def set_snapshot_stamp(
    session: StagingSession,
    package_date: str,
    mdr_head: str | None,
    summary: dict[str, Any],
) -> None:
    run_query(
        session,
        """
        MATCH (import:EffectiveDateImport {effective_date: $package_date})
        SET import.review_snapshot_at = datetime(),
            import.review_snapshot_mdr_head = $mdr_head,
            import.review_snapshot_summary = $summary
        """,
        parameters={
            "package_date": package_date,
            "mdr_head": mdr_head,
            "summary": json.dumps(summary),
        },
    )


def clear_snapshot_stamp(session: StagingSession, package_date: str) -> None:
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
