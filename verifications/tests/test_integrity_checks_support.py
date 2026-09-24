"""Fast unit tests for API integrity wiring (mocked Neo4j / Allure)."""

from unittest.mock import MagicMock, patch

import allure
from clinical_mdr_api.utils.db_integrity_checks import QUERIES, execute_check_for_study

from utils import utils as utils_mod
from utils.integrity_checks_support import (
    attach_integrity_summary_table_to_allure,
    fetch_non_deleted_study_uids,
)
from utils.utils import (
    REPORT_COLUMNS,
    execute_query_with_params_and_append_result_to_file,
)


def test_fetch_non_deleted_study_uids_from_cypher(monkeypatch):
    monkeypatch.delenv("INTEGRITY_STUDY_UIDS", raising=False)
    db = MagicMock()
    db.cypher_query.return_value = ([("Study_1",), ("Study_2",)], ["study_uid"])
    uids = fetch_non_deleted_study_uids(db)
    assert uids == ["Study_1", "Study_2"]
    db.cypher_query.assert_called_once()


def test_fetch_non_deleted_study_uids_env_override(monkeypatch):
    monkeypatch.setenv("INTEGRITY_STUDY_UIDS", " X , Y ")
    db = MagicMock()
    assert fetch_non_deleted_study_uids(db) == ["X", "Y"]
    db.cypher_query.assert_not_called()


def test_execute_check_for_study_one_query_mocked():
    check_id, description, query = QUERIES[0]
    with patch("clinical_mdr_api.utils.db_integrity_checks.db.cypher_query") as mock_q:
        mock_q.return_value = (
            [(0, [], [])],
            ["noncompliant_entity_cnt", "noncompliant_labels", "noncompliant_node_ids"],
        )
        result = execute_check_for_study(
            check_id, description, query, "Study_dummy_uid"
        )
    assert result.passed
    mock_q.assert_called_once()
    assert mock_q.call_args.kwargs["params"] == {"study_uid": "Study_dummy_uid"}


def test_execute_query_with_params_appends_data_row(tmp_path, monkeypatch):
    def fake_cypher(_query, params=None):
        assert params == {"study_uid": "S"}
        return (
            [(0, [], [])],
            ["noncompliant_entity_cnt", "noncompliant_labels", "noncompliant_node_ids"],
        )

    monkeypatch.setattr(utils_mod.db, "cypher_query", fake_cypher)

    report = tmp_path / "rep.csv"
    report.write_text(",".join(REPORT_COLUMNS) + "\n", encoding="utf-8")
    execute_query_with_params_and_append_result_to_file(
        "RETURN 1 AS dummy",
        str(report),
        {"study_uid": "S"},
        check_id="unit_check",
        check_description="unit desc",
    )
    lines = report.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 2
    assert "check_id" in lines[0]
    assert "unit_check" in lines[1]


def test_attach_integrity_summary_table_calls_allure_attach():
    with patch.object(allure, "attach") as mock_attach:
        attach_integrity_summary_table_to_allure([("study_u", "check_id", "a <b> & c")])
    mock_attach.assert_called_once()
    body = mock_attach.call_args[0][0]
    assert "study_u" in body
    assert "&lt;" in body
    assert "&amp;" in body
