"""The codelist pairings uploaded alongside a release."""

import logging
from typing import Any

from standards_import.repositories.staging_db import StagingSession, run_query

log = logging.getLogger(__name__)


def replace_pairings(
    session: StagingSession,
    package_date: str,
    source_file: str,
    pairings: list[dict[str, Any]],
) -> int:
    """Stores the pairings from one workbook, replacing that workbook's previous rows.

    Scoped to the file it came from, so uploading an SDTM workbook does not discard the
    SEND one already provided for the same release.
    """

    run_query(
        session,
        """
        MATCH (:EffectiveDateImport {effective_date: $package_date})
              -[:HAS_PAIRING]->(p:StagedPairing {source_file: $source_file})
        DETACH DELETE p
        """,
        parameters={"package_date": package_date, "source_file": source_file},
    )
    if not pairings:
        return 0

    run_query(
        session,
        """
        MATCH (import:EffectiveDateImport {effective_date: $package_date})
        UNWIND $pairings AS pairing
        CREATE (import)-[:HAS_PAIRING]->(p:StagedPairing:CDISCStaging {
            name_concept_id: pairing.name_concept_id,
            code_concept_id: pairing.code_concept_id,
            name_submission_value: pairing.name_submission_value,
            code_submission_value: pairing.code_submission_value,
            codelist_name: pairing.codelist_name,
            source: pairing.source,
            source_file: $source_file
        })
        """,
        parameters={
            "package_date": package_date,
            "source_file": source_file,
            "pairings": pairings,
        },
    )
    return len(pairings)


def get_pairings(session: StagingSession, package_date: str) -> list[dict[str, Any]]:
    return run_query(
        session,
        """
        MATCH (:EffectiveDateImport {effective_date: $package_date})-[:HAS_PAIRING]->(p:StagedPairing)
        RETURN p.name_concept_id AS name_concept_id,
               p.code_concept_id AS code_concept_id,
               p.name_submission_value AS name_submission_value,
               p.code_submission_value AS code_submission_value,
               p.codelist_name AS codelist_name,
               p.source_file AS source_file
        ORDER BY name_submission_value
        """,
        parameters={"package_date": package_date},
    )
