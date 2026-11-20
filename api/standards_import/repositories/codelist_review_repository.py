"""Marking a codelist reviewed, and reading who did and when.

Hangs off `EffectiveDateImport` rather than the grouped layer, for the same reason
`Inconsistency` findings do — see `inconsistency_repository`'s module docstring:
analysis tears down and rebuilds the grouped layer on every run, and a review record
has to survive that the same way a decision does. `analysis_repository.clear_derived_layer`
only ever reaches nodes hung off the grouped layer, so a `CodelistReview` here is never
swept up by it.

What is *not* here: whether a review is stale. That is derived at read time from
whether the codelist currently has an OPEN finding — see `codelist_service.to_codelist_review`
— rather than stored, so a review record is never silently rewritten by re-analysis.
"""

import logging
from typing import Any

from standards_import.repositories.staging_db import StagingSession, run_query

log = logging.getLogger(__name__)

REVIEW_RETURN = """
    review.codelist_id AS codelist_id,
    review.author_id AS author_id,
    review.reviewed_at AS reviewed_at
"""


def mark_reviewed(
    session: StagingSession, package_date: str, codelist_id: str, author_id: str
) -> dict[str, Any]:
    """Records that a person reviewed this codelist, replacing any earlier record.

    `MERGE` on `codelist_id` scoped by the `EffectiveDateImport` match, so reviewing
    twice refreshes who and when rather than stacking a second record.
    """

    records = run_query(
        session,
        f"""
        MATCH (import:EffectiveDateImport {{effective_date: $package_date}})
        MERGE (import)-[:HAS_CODELIST_REVIEW]->(review:CodelistReview:CDISCStaging {{codelist_id: $codelist_id}})
        SET review.author_id = $author_id, review.reviewed_at = datetime()
        RETURN {REVIEW_RETURN}
        """,
        parameters={
            "package_date": package_date,
            "codelist_id": codelist_id,
            "author_id": author_id,
        },
    )
    return records[0]


def clear_review(session: StagingSession, package_date: str, codelist_id: str) -> None:
    """Removes the review record. Never an error not to find one to remove."""

    run_query(
        session,
        """
        MATCH (:EffectiveDateImport {effective_date: $package_date})
              -[:HAS_CODELIST_REVIEW]->(review:CodelistReview {codelist_id: $codelist_id})
        DETACH DELETE review
        """,
        parameters={"package_date": package_date, "codelist_id": codelist_id},
    )


def get_review(
    session: StagingSession, package_date: str, codelist_id: str
) -> dict[str, Any] | None:
    """One codelist's review record, or `None` if it was never marked."""

    records = run_query(
        session,
        f"""
        MATCH (:EffectiveDateImport {{effective_date: $package_date}})
              -[:HAS_CODELIST_REVIEW]->(review:CodelistReview {{codelist_id: $codelist_id}})
        RETURN {REVIEW_RETURN}
        """,
        parameters={"package_date": package_date, "codelist_id": codelist_id},
    )
    return records[0] if records else None


def get_reviews(
    session: StagingSession, package_date: str
) -> dict[str, dict[str, Any]]:
    """Every review recorded for this release, keyed by codelist id.

    One read for the whole release rather than one per codelist — the same shape as
    `inconsistency_repository.get_finding_counts_by_codelist`, and for the same reason:
    the list and dashboard endpoints need this for every codelist at once.
    """

    records = run_query(
        session,
        f"""
        MATCH (:EffectiveDateImport {{effective_date: $package_date}})
              -[:HAS_CODELIST_REVIEW]->(review:CodelistReview)
        RETURN {REVIEW_RETURN}
        """,
        parameters={"package_date": package_date},
    )
    return {record["codelist_id"]: record for record in records}
