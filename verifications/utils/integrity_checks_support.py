"""
Run clinical-mdr-api database integrity checks (QUERIES) from verifications.

Uses the same Cypher definitions as ``clinical_mdr_api.utils.db_integrity_checks``
without calling the HTTP API.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    import allure as _allure_module
except ImportError:
    _allure_module = None

_VERIFICATIONS_ROOT = Path(__file__).resolve().parent.parent
_API_ROOT = _VERIFICATIONS_ROOT.parent / "api"

# Non-deleted studies: has at least one HAS_VERSION and is not in deleted-StudyRoot pattern.
NON_DELETED_STUDY_UIDS_CYPHER = """
MATCH (sr:StudyRoot)-[:HAS_VERSION]->(:StudyValue)
WHERE NOT (sr)-[:LATEST]->(:StudyValue)<-[:BEFORE]-(:Delete)
RETURN DISTINCT sr.uid AS study_uid
ORDER BY study_uid
"""


def ensure_clinical_mdr_api_on_path() -> None:
    """Allow ``import api`` from the ../api path."""
    root = str(_API_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


ensure_clinical_mdr_api_on_path()

from clinical_mdr_api.utils.db_integrity_checks import (
    QUERIES,
    CheckResult,
    execute_check_for_study,
)

from utils.utils import append_to_file


def fetch_non_deleted_study_uids(db: Any, env_value: str | None = None) -> list[str]:
    """
    Return study UIDs to run integrity checks against.

    If ``INTEGRITY_STUDY_UIDS`` is set (or ``env_value`` is passed), returns that
    comma-separated list and does not query the database for discovery.
    """
    raw = (
        env_value
        if env_value is not None
        else os.environ.get("INTEGRITY_STUDY_UIDS", "")
    ).strip()
    if raw:
        return [u.strip() for u in raw.split(",") if u.strip()]

    rows, _ = db.cypher_query(NON_DELETED_STUDY_UIDS_CYPHER)
    return [r[0] for r in rows]


def attach_csv_to_allure(
    report_path: str | Path, attachment_name: str = "integrity-db_checks_result.csv"
) -> None:
    """Attach the CSV report to Allure (no-op if allure is unavailable or file missing)."""
    path = Path(report_path)
    if not path.is_file() or _allure_module is None:
        return
    _allure_module.attach.file(
        str(path),
        name=attachment_name,
        attachment_type=_allure_module.attachment_type.CSV,
    )


def attach_integrity_summary_table_to_allure(
    rows: Iterable[tuple[str, str, str]],
) -> None:
    """
    Attach a small HTML table to Allure (e.g. failed study / check / message).

    Safe to call without Allure installed (no-op).
    """
    parts = [
        "<table><thead><tr><th>study_uid</th><th>check_id</th><th>detail</th></tr></thead><tbody>"
    ]
    for study_uid, check_id, detail in rows:
        safe_detail = (
            str(detail).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        parts.append(
            f"<tr><td>{study_uid}</td><td>{check_id}</td><td>{safe_detail}</td></tr>"
        )
    parts.append("</tbody></table>")
    html = "".join(parts)
    if _allure_module is None:
        return
    _allure_module.attach(
        html,
        name="integrity_failures_summary",
        attachment_type=_allure_module.attachment_type.HTML,
    )


def _row_from_check_result(
    check_id: str,
    description: str,
    result: Any,
    impact_tags: list | None = None,
    requirement_ids: list | None = None,
) -> dict:
    assert isinstance(result, CheckResult)
    desc = description
    if result.error:
        desc = f"{description} [ERROR: {result.error}]"
    return {
        "check_id": check_id,
        "check_description": desc,
        "noncompliant_entity_cnt": result.noncompliant_count,
        "noncompliant_labels": result.noncompliant_labels,
        "noncompliant_node_ids": result.noncompliant_node_ids,
        "impact_tags": impact_tags or [],
        "requirement_ids": requirement_ids or [],
    }


def _run_checks_for_study(
    study_uid: str,
    queries: list[tuple[str, str, str]],
    report_path_str: str,
    *,
    impact_tags: list | None,
    requirement_ids: list | None,
) -> tuple[list[str], list[tuple[str, str, str]]]:
    """Run each query for one study; return (failure_messages, failure_table_rows)."""
    failures: list[str] = []
    failure_rows: list[tuple[str, str, str]] = []
    for check_id, description, query in queries:
        result = execute_check_for_study(check_id, description, query, study_uid)
        row = _row_from_check_result(
            check_id,
            description,
            result,
            impact_tags=impact_tags,
            requirement_ids=requirement_ids,
        )
        append_to_file(report_path_str, [row])

        if result.error:
            failures.append(f"{study_uid} :: {check_id} :: ERROR: {result.error}")
            failure_rows.append((study_uid, check_id, result.error))
        elif not result.passed:
            failures.append(
                f"{study_uid} :: {check_id} :: noncompliant_count={result.noncompliant_count}"
            )
            failure_rows.append((study_uid, check_id, str(result.noncompliant_count)))
    return failures, failure_rows


def run_all_api_integrity_checks(
    db: Any,
    report_path: str | Path,
    *,
    check_ids_filter: set[str] | None = None,
    impact_tags: list | None = None,
    requirement_ids: list | None = None,
) -> list[str]:
    """
    Execute every ``QUERIES`` entry (optionally filtered) for each discovered study UID.

    Appends one CSV row per (study_uid, check) using ``utils.utils.append_to_file``.

    Returns a list of human-readable failure messages (empty if all passed).
    """
    study_uids = fetch_non_deleted_study_uids(db)
    failures: list[str] = []
    failure_rows: list[tuple[str, str, str]] = []

    if not study_uids:
        failures.append(
            "No study UIDs found for integrity checks (empty database filter)."
        )
        return failures

    queries = QUERIES
    if check_ids_filter is not None:
        queries = [q for q in QUERIES if q[0] in check_ids_filter]

    report_path_str = str(report_path)

    for study_uid in study_uids:
        study_failures, study_rows = _run_checks_for_study(
            study_uid,
            queries,
            report_path_str,
            impact_tags=impact_tags,
            requirement_ids=requirement_ids,
        )
        failures.extend(study_failures)
        failure_rows.extend(study_rows)

    if failure_rows:
        attach_integrity_summary_table_to_allure(failure_rows)

    return failures


def fail_if_integrity_errors(
    failures: list[str],
    report_path: str | Path,
) -> None:
    """If there are failures, attach CSV to Allure and raise AssertionError."""
    if not failures:
        return
    attach_csv_to_allure(report_path)
    raise AssertionError("API integrity check failures:\n" + "\n".join(failures))
