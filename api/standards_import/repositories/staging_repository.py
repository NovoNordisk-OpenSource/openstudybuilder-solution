"""Bookkeeping of uploaded files and the state of each CDISC release.

Effective dates are held as `YYYY-MM-DD` strings throughout, matching
`RawPackage.effectiveDate` in the staging model that the bootstrap import built.
"""

import logging
from typing import Any

from standards_import.repositories.staging_db import StagingSession, run_query

log = logging.getLogger(__name__)

KNOWN_RELEASE_RETURN = """
    known.catalogue AS catalogue,
    known.package_name AS package_name,
    known.effective_date AS effective_date,
    known.href AS href,
    known.discovered_at AS discovered_at
"""

STAGED_FILE_RETURN = """
    staged.uid AS uid,
    staged.catalogue AS catalogue,
    staged.package_name AS package_name,
    staged.effective_date AS effective_date,
    staged.sha256 AS sha256,
    staged.size_bytes AS size_bytes,
    staged.codelist_count AS codelist_count,
    staged.term_count AS term_count,
    staged.uploaded_at AS uploaded_at,
    staged.author_id AS author_id
"""


def find_staged_file(session: StagingSession, uid: str) -> dict[str, Any] | None:
    """Returns the staged file with this uid, if there is one."""

    records = run_query(
        session,
        f"""
        MATCH (staged:StagedFile {{uid: $uid}})
        RETURN {STAGED_FILE_RETURN}
        """,
        parameters={"uid": uid},
    )
    return records[0] if records else None


def get_staged_files(
    session: StagingSession, effective_date: str | None = None
) -> list[dict[str, Any]]:
    """Returns staged files, newest release first."""

    filter_clause = (
        "WHERE staged.effective_date = $effective_date" if effective_date else ""
    )
    return run_query(
        session,
        f"""
        MATCH (staged:StagedFile)
        {filter_clause}
        RETURN {STAGED_FILE_RETURN}
        ORDER BY date(staged.effective_date) DESC, staged.catalogue ASC
        """,
        parameters={"effective_date": effective_date},
    )


def get_known_package_names(session: StagingSession) -> set[str]:
    """The package names staging already holds or has already been told about.

    Both labels count, for different reasons: a `StagedFile` is a release whose content
    is already here; a `KnownRelease` is one a previous discovery run reported but nobody
    has uploaded yet. Together they are what keeps discovery from reporting — and
    auto-staging, which resets the release's analysis — the same release at every call,
    without a second flag saying whether it was reported before.
    """

    records = run_query(
        session,
        """
        CALL () {
            MATCH (staged:StagedFile)
            RETURN staged.package_name AS package_name
            UNION
            MATCH (known:KnownRelease)
            RETURN known.package_name AS package_name
        }
        RETURN package_name
        """,
    )
    return {record["package_name"] for record in records if record["package_name"]}


def record_known_releases(
    session: StagingSession, releases: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Records the releases discovery found, keyed on the package name.

    Bookkeeping only, and deliberately not an `EffectiveDateImport`: a release CDISC has
    published is not a release with a lifecycle in staging, and creating one here would
    show up as an effective date holding no files that could never be analysed.

    `MERGE` on `package_name` makes a re-run of discovery cost nothing and change nothing
    but `discovered_at`. One `UNWIND` rather than the batching the raw load needs: a
    release list runs to dozens of entries, not thousands.
    """

    return run_query(
        session,
        f"""
        UNWIND $releases AS release
            MERGE (known:KnownRelease:CDISCStaging {{package_name: release.package_name}})
            SET known.catalogue = release.catalogue,
                known.effective_date = release.effective_date,
                known.href = release.href,
                known.discovered_at = datetime()
        RETURN {KNOWN_RELEASE_RETURN}
        ORDER BY date(known.effective_date) DESC, known.catalogue ASC
        """,
        parameters={"releases": releases},
    )


def get_unstaged_known_releases(
    session: StagingSession, catalogues: list[str]
) -> list[dict[str, Any]]:
    """Known releases of the given catalogues whose content never made it into staging.

    A `KnownRelease` is written before auto-staging is attempted, so a failed attempt —
    or one this process was never given the chance to finish — leaves a release "known"
    forever with nothing behind it, unless something looks for exactly this gap and
    tries again.
    """

    return run_query(
        session,
        f"""
        MATCH (known:KnownRelease)
        WHERE known.catalogue IN $catalogues
          AND NOT EXISTS {{
            MATCH (:StagedFile {{package_name: known.package_name}})
        }}
        RETURN {KNOWN_RELEASE_RETURN}
        ORDER BY date(known.effective_date) DESC
        """,
        parameters={"catalogues": catalogues},
    )


def reset_release_for_reanalysis(session: StagingSession, package_date: str) -> None:
    """Puts a release back to FILES_STAGED, discarding any analysis of it.

    Used where something the analysis reads has changed but no package file has —
    a replaced pairing workbook. `record_staged_file` does the same for the release
    a package upload belongs to.
    """

    run_query(
        session,
        """
        MATCH (import:EffectiveDateImport {effective_date: $package_date})
        SET import.status = 'FILES_STAGED',
            import.analyzed_at = NULL,
            import.assessed_at = NULL,
            import.open_inconsistency_count = 0,
            import.review_snapshot_at = NULL,
            import.review_snapshot_mdr_head = NULL,
            import.review_snapshot_summary = NULL
        """,
        parameters={"package_date": package_date},
    )


def record_staged_file(
    session: StagingSession, staged_file: dict[str, Any]
) -> dict[str, Any]:
    """Records an uploaded file, links it to what it loaded, and resets the release.

    A newly uploaded file invalidates any analysis of that release, so the status
    is reset here.

    `LOADED_CATALOGUE` records which catalogue this upload produced, making the
    provenance of every codelist and term traversable back to the file and the
    person who sent it.
    It must therefore run after the raw load, and is re-established on replacement
    because deleting the old catalogue takes the relationship with it.
    """

    records = run_query(
        session,
        f"""
        MERGE (staged:StagedFile:CDISCStaging {{uid: $file.uid}})
        SET staged.catalogue = $file.catalogue,
            staged.package_name = $file.package_name,
            staged.effective_date = $file.effective_date,
            staged.sha256 = $file.sha256,
            staged.size_bytes = $file.size_bytes,
            staged.codelist_count = $file.codelist_count,
            staged.term_count = $file.term_count,
            staged.uploaded_at = datetime(),
            staged.author_id = $file.author_id
        WITH staged
        MERGE (import:EffectiveDateImport:CDISCStaging {{effective_date: $file.effective_date}})
        SET import.status = 'FILES_STAGED',
            import.analyzed_at = NULL,
            import.assessed_at = NULL,
            import.open_inconsistency_count = 0,
            import.review_snapshot_at = NULL,
            import.review_snapshot_mdr_head = NULL,
            import.review_snapshot_summary = NULL
        MERGE (import)-[:HAS_FILE]->(staged)
        WITH staged
        // A unit subquery: if the catalogue is somehow absent this links nothing and
        // still returns the staged file, rather than dropping the row and its result.
        CALL (staged) {{
            MATCH (cat:RawCatalogue {{name: staged.package_name}})
            MERGE (staged)-[:LOADED_CATALOGUE]->(cat)
        }}
        RETURN {STAGED_FILE_RETURN}
        """,
        parameters={"file": staged_file},
    )
    return records[0]


def get_effective_dates(session: StagingSession) -> list[dict[str, Any]]:
    """Returns every release held in staging, newest first."""

    return run_query(
        session,
        """
        MATCH (import:EffectiveDateImport)
        RETURN import.effective_date AS effective_date,
               import.status AS status,
               import.analyzed_at AS analyzed_at,
               import.assessed_at AS assessed_at,
               import.imported_at AS imported_at,
               COALESCE(import.open_inconsistency_count, 0) AS open_inconsistency_count,
               // Workbooks, not rows: one workbook contributes hundreds of
               // pairings, and this is reported as a count of files.
               COUNT {
                   MATCH (import)-[:HAS_PAIRING]->(p:StagedPairing)
                   RETURN DISTINCT p.source_file
               } AS pairing_files,
               // Catalogues, not rows and not files: a changelog upload is replaced
               // per catalogue, so that is the unit an uploader is tracking.
               COUNT {
                   MATCH (import)-[:HAS_CHANGELOG_ENTRY]->(e:ChangelogEntry)
                   RETURN DISTINCT e.catalogue
               } AS changelog_catalogues
        ORDER BY date(import.effective_date) DESC
        """,
    )


def find_effective_date(
    session: StagingSession, effective_date: str
) -> dict[str, Any] | None:
    """Returns one release, if it is held in staging."""

    records = run_query(
        session,
        """
        MATCH (import:EffectiveDateImport {effective_date: $effective_date})
        RETURN import.effective_date AS effective_date,
               import.status AS status,
               import.analyzed_at AS analyzed_at,
               import.assessed_at AS assessed_at,
               import.imported_at AS imported_at,
               COALESCE(import.open_inconsistency_count, 0) AS open_inconsistency_count,
               // Workbooks, not rows: one workbook contributes hundreds of
               // pairings, and this is reported as a count of files.
               COUNT {
                   MATCH (import)-[:HAS_PAIRING]->(p:StagedPairing)
                   RETURN DISTINCT p.source_file
               } AS pairing_files,
               COUNT {
                   MATCH (import)-[:HAS_CHANGELOG_ENTRY]->(e:ChangelogEntry)
                   RETURN DISTINCT e.catalogue
               } AS changelog_catalogues
        """,
        parameters={"effective_date": effective_date},
    )
    return records[0] if records else None


def set_open_inconsistency_count(
    session: StagingSession,
    effective_date: str,
    status: str,
    open_inconsistency_count: int,
) -> None:
    """Updates a release after a review item was settled or reopened.

    Deliberately leaves `analyzed_at` alone: deciding something is not re-analysing,
    and the timestamp should keep pointing at the run that produced the findings.
    """

    run_query(
        session,
        """
        MATCH (import:EffectiveDateImport {effective_date: $effective_date})
        SET import.status = $status,
            import.open_inconsistency_count = $open_inconsistency_count
        """,
        parameters={
            "effective_date": effective_date,
            "status": status,
            "open_inconsistency_count": open_inconsistency_count,
        },
    )


def set_analysis_outcome(
    session: StagingSession,
    effective_date: str,
    status: str,
    open_inconsistency_count: int,
) -> dict[str, Any]:
    """Stores the outcome of analysing a release."""

    records = run_query(
        session,
        """
        MERGE (import:EffectiveDateImport:CDISCStaging {effective_date: $effective_date})
        SET import.status = $status,
            import.analyzed_at = datetime(),
            import.open_inconsistency_count = $open_inconsistency_count
        RETURN import.effective_date AS effective_date,
               import.status AS status,
               import.analyzed_at AS analyzed_at,
               import.assessed_at AS assessed_at,
               import.imported_at AS imported_at,
               import.open_inconsistency_count AS open_inconsistency_count
        """,
        parameters={
            "effective_date": effective_date,
            "status": status,
            "open_inconsistency_count": open_inconsistency_count,
        },
    )
    return records[0]


def set_assessment_outcome(
    session: StagingSession,
    effective_date: str,
    status: str,
    open_inconsistency_count: int,
) -> dict[str, Any]:
    """Stores the outcome of assessing a release's impact on sponsor-defined content.

    `analyzed_at` is deliberately left alone, and the two timestamps are then compared to
    tell whether the assessment still describes the release: analysis rewrites the settled
    values the assessment was computed from, so an analysis run that is newer than the
    last assessment means the answer is stale even though both have run.
    """

    records = run_query(
        session,
        """
        MATCH (import:EffectiveDateImport {effective_date: $effective_date})
        SET import.status = $status,
            import.assessed_at = datetime(),
            import.open_inconsistency_count = $open_inconsistency_count
        RETURN import.effective_date AS effective_date,
               import.status AS status,
               import.analyzed_at AS analyzed_at,
               import.assessed_at AS assessed_at,
               import.imported_at AS imported_at,
               import.open_inconsistency_count AS open_inconsistency_count
        """,
        parameters={
            "effective_date": effective_date,
            "status": status,
            "open_inconsistency_count": open_inconsistency_count,
        },
    )
    return records[0]
