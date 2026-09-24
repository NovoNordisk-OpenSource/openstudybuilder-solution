"""Unit tests for exclusion id containment (no tests/conftest — no DB)."""

import os
from unittest.mock import patch

import pytest

# utils.utils requires API_AUTH_TOKEN at import time; pylint imports modules
# during analysis without executing our env setup, so we disable the import
# check for this line.
os.environ.setdefault("API_AUTH_TOKEN", "test-token-placeholder")

from utils.utils import (  # noqa: E402  # pylint: disable=import-error,wrong-import-position; pylint: disable=import-error,wrong-import-position
    ExpectedFailureException,
    _ids_match_exclusion,
    _is_node_excluded,
    execute_query_and_append_result_to_file,
)

RESULT_COLUMNS = [
    "noncompliant_entity_cnt",
    "noncompliant_labels",
    "noncompliant_node_ids",
]


def test_ids_match_exclusion_singleton_in_long_list():
    excluded = ["Activity_000008", "Activity_003366", "Activity_003791"]
    assert _ids_match_exclusion(excluded, ["Activity_000008"])


def test_ids_match_exclusion_all_components_must_be_in_excluded():
    excluded = ["a", "b", "extra"]
    assert _ids_match_exclusion(excluded, ["a", "b"])
    assert not _ids_match_exclusion(excluded, ["a", "c"])


def test_ids_match_exclusion_multiset_requires_counts():
    assert _ids_match_exclusion(["x", "x"], ["x", "x"])
    assert not _ids_match_exclusion(["x"], ["x", "x"])


def test_ids_match_exclusion_empty_never_matches():
    assert not _ids_match_exclusion([], ["a"])
    assert not _ids_match_exclusion(["a"], [])


def test_is_node_excluded_uid_path_ignores_exclusion_label():
    excluded_nodes = [{"label": ["WrongLabel"], "id": ["A", "B", "C"]}]
    assert _is_node_excluded(["ActivityRoot"], ["A"], excluded_nodes)


def test_is_node_excluded_uid_path_skips_entries_without_id():
    excluded_nodes = [{"label": ["ActivityRoot"], "id": []}]
    assert not _is_node_excluded(
        [["ActivityRoot"]], ["Activity_000008"], excluded_nodes
    )


def test_is_node_excluded_label_only_path():
    excluded_nodes = [{"label": ["StudyThing"], "id": []}]
    assert _is_node_excluded(["StudyThing"], [], excluded_nodes)
    assert not _is_node_excluded(["Other"], [], excluded_nodes)


@patch("utils.utils.append_to_file")
@patch("utils.utils.db.cypher_query")
def test_execute_raises_expected_failure_when_all_failures_excluded(
    mock_cypher, _mock_append
):
    motivation = (
        "Known legacy data issue: duplicated ActivityRoot.name_sentence_case "
        "entries. Work item: TBD"
    )
    mock_cypher.return_value = (
        [[1, [["ActivityRoot"]], ["Activity_000008"]]],
        RESULT_COLUMNS,
    )
    excluded = [
        {
            "label": ["ActivityRoot"],
            "id": ["Activity_000008", "Activity_003366"],
            "motivation": motivation,
        },
    ]
    with pytest.raises(ExpectedFailureException) as excinfo:
        execute_query_and_append_result_to_file(
            "MATCH (n) RETURN 1",
            "/tmp/db_checks_result_test.csv",
            check_id="no_duplicated_name_sentence_case_in_Activitys",
            excluded_node_ids=excluded,
        )
    msg = str(excinfo.value)
    assert "Failing row(s) removed by exclusions" in msg
    assert "Activity_000008" in msg
    assert "labels=" in msg and "node_ids=" in msg
    assert "motivation=" in msg
    assert "Work item: TBD" in msg


@patch("utils.utils.append_to_file")
@patch("utils.utils.db.cypher_query")
def test_execute_does_not_raise_when_some_failures_remain(mock_cypher, _mock_append):
    mock_cypher.return_value = (
        [[1, [["ActivityRoot"]], ["Activity_UNKNOWN"]]],
        RESULT_COLUMNS,
    )
    motivation = "Known legacy data issue. Work item: TBD"
    excluded = [
        {
            "label": ["ActivityRoot"],
            "id": ["Activity_000008", "Activity_003366"],
            "motivation": motivation,
        },
    ]
    result = execute_query_and_append_result_to_file(
        "MATCH (n) RETURN 1",
        "/tmp/db_checks_result_test.csv",
        check_id="no_duplicated_name_sentence_case_in_Activitys",
        excluded_node_ids=excluded,
    )
    assert result["noncompliant_entity_cnt"] == 1


@patch("utils.utils.append_to_file")
@patch("utils.utils.db.cypher_query")
def test_execute_no_expected_failure_without_exclusions(mock_cypher, _mock_append):
    mock_cypher.return_value = (
        [[0, [], []]],
        RESULT_COLUMNS,
    )
    result = execute_query_and_append_result_to_file(
        "MATCH (n) RETURN 1",
        "/tmp/db_checks_result_test.csv",
        check_id="some_check",
        excluded_node_ids=None,
    )
    assert result["noncompliant_entity_cnt"] == 0
