"""Data corrections for PROD: Test fix Non and Unscheduled visit labels and visibility, and restore CTCodelistTerm nodes."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from data_corrections import correction_020
from data_corrections.utils.utils import get_db_driver, run_cypher_query, save_md_title
from migrations.utils.utils import execute_statements, get_logger
from tests.data.db_before_correction_020 import (
    STUDY_000083_STUDY_VISITS,
    TEST_DATA_RESTORE_CLT_NODES,
)
from tests.utils.utils import clear_db
from verifications import correction_verification_020

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()

VERIFY_RUN_LABEL = "test_verification"
CORRECTION_ARGS = (DB_DRIVER, LOGGER, VERIFY_RUN_LABEL)


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Initialize logging once at the start of the test session"""
    desc = f"Running verification for data corrections on DB '{os.environ['DATABASE_NAME']}'"
    save_md_title(VERIFY_RUN_LABEL, correction_020.__doc__, desc)
    yield


def _setup_test_data(test_data):
    """Helper to set up test data for a test"""
    clear_db()
    execute_statements(test_data)


def test_fix_non_and_unscheduled_visit_label_and_visibility():
    """Test that Non and Unscheduled visits get 'V' prefix and show_visit=false"""
    # Setup test data
    _setup_test_data(STUDY_000083_STUDY_VISITS)

    # Verify initial state (should fail — visits have wrong label/visibility)
    with pytest.raises(AssertionError):
        correction_verification_020.test_non_and_unscheduled_visits_label_and_visibility()

    # Run correction
    correction_020.fix_non_and_unscheduled_visit_label_and_visibility(*CORRECTION_ARGS)

    # Verify correction worked
    correction_verification_020.test_non_and_unscheduled_visits_label_and_visibility()


@pytest.mark.order(after="test_fix_non_and_unscheduled_visit_label_and_visibility")
def test_repeat_fix_non_and_unscheduled_visit_label_and_visibility():
    """Test that visit label/visibility fix is idempotent"""
    assert not correction_020.fix_non_and_unscheduled_visit_label_and_visibility(
        *CORRECTION_ARGS
    )


def _build_test_change_log():
    """Build a synthetic change log matching the CDC format for test data."""
    tx_meta = {
        "txCommitTime": "2026-04-01T09:58:53.162000000+00:00",
        "executingUser": "neo4j",
        "databaseName": "test",
        "captureMode": "DIFF",
    }
    tx_id = "TEST_TX_001"
    seq = [0]

    def seq_next():
        seq[0] += 1
        return seq[0]

    records = []

    def add_node_delete(element_id, labels, properties):
        records.append(
            [
                tx_id,
                seq_next(),
                0,
                tx_meta,
                {
                    "elementId": element_id,
                    "eventType": "n",
                    "operation": "d",
                    "state": {
                        "before": {"labels": labels, "properties": properties},
                        "after": None,
                    },
                },
            ]
        )

    def add_rel_delete(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        rel_type, start_labels, start_keys, end_labels, end_keys, props=None
    ):
        records.append(
            [
                tx_id,
                seq_next(),
                0,
                tx_meta,
                {
                    "elementId": f"5:test:{seq[0]}",
                    "eventType": "r",
                    "operation": "d",
                    "type": rel_type,
                    "start": {
                        "elementId": f"4:test:start_{seq[0]}",
                        "labels": start_labels,
                        "keys": start_keys,
                    },
                    "end": {
                        "elementId": f"4:test:end_{seq[0]}",
                        "labels": end_labels,
                        "keys": end_keys,
                    },
                    "state": {
                        "before": {"properties": props or {}},
                        "after": None,
                    },
                },
            ]
        )

    # CTCodelistTerm A: C70543 / "NEVER" - with 2 CTPackageTerm + 2 CTCodelistRoot
    clt_a_eid = "4:test:clt_a"
    add_node_delete(clt_a_eid, ["CTCodelistTerm"], {"submission_value": "NEVER"})
    add_rel_delete(
        "HAS_TERM_ROOT",
        ["CTCodelistTerm"],
        {},
        ["CTTermRoot"],
        {"CTTermRoot": [{"uid": "C70543"}]},
    )
    # Override start elementId to match clt_a
    records[-1][4]["start"]["elementId"] = clt_a_eid

    add_rel_delete(
        "HAS_TERM",
        ["CTCodelistRoot"],
        {"CTCodelistRoot": [{"uid": "C78738"}]},
        ["CTCodelistTerm"],
        {},
        props={
            "author_id": "fd909732-bc9e-492b-a1ed-6e27757a4f00",
            "start_date": "2014-09-26T00:00:00.000000000+00:00",
        },
    )
    records[-1][4]["end"]["elementId"] = clt_a_eid

    add_rel_delete(
        "HAS_TERM",
        ["CTCodelistRoot"],
        {"CTCodelistRoot": [{"uid": "C83004"}]},
        ["CTCodelistTerm"],
        {},
        props={
            "author_id": "fd909732-bc9e-492b-a1ed-6e27757a4f00",
            "start_date": "2014-09-26T00:00:00.000000000+00:00",
        },
    )
    records[-1][4]["end"]["elementId"] = clt_a_eid

    add_rel_delete(
        "CONTAINS_SUBMISSION_VALUE",
        ["CTPackageTerm"],
        {"CTPackageTerm": [{"uid": "SDTM__CT__2021-12-17_C70543"}]},
        ["CTCodelistTerm"],
        {},
    )
    records[-1][4]["end"]["elementId"] = clt_a_eid

    add_rel_delete(
        "CONTAINS_SUBMISSION_VALUE",
        ["CTPackageTerm"],
        {"CTPackageTerm": [{"uid": "SDTM__CT__2022-03-25_C70543"}]},
        ["CTCodelistTerm"],
        {},
    )
    records[-1][4]["end"]["elementId"] = clt_a_eid

    # CTCodelistTerm B: CTTerm_000108 / "OBESITY" - with 1 CTCodelistRoot, no CTPackageTerm
    clt_b_eid = "4:test:clt_b"
    add_node_delete(clt_b_eid, ["CTCodelistTerm"], {"submission_value": "OBESITY"})
    add_rel_delete(
        "HAS_TERM_ROOT",
        ["CTCodelistTerm"],
        {},
        ["CTTermRoot"],
        {"CTTermRoot": [{"uid": "CTTerm_000108"}]},
    )
    records[-1][4]["start"]["elementId"] = clt_b_eid

    add_rel_delete(
        "HAS_TERM",
        ["CTCodelistRoot"],
        {"CTCodelistRoot": [{"uid": "CTCodelist_000005"}]},
        ["CTCodelistTerm"],
        {},
        props={
            "author_id": "fd909732-bc9e-492b-a1ed-6e27757a4f00",
            "order": 95,
            "start_date": "2022-09-21T19:39:41.255386000+00:00",
        },
    )
    records[-1][4]["end"]["elementId"] = clt_b_eid

    # Add a second transaction to simulate Phase B (so Phase A is correctly identified)
    phase_b_meta = dict(tx_meta, txCommitTime="2026-04-01T09:58:53.446000000+00:00")
    records.append(
        [
            "TEST_TX_002",
            seq_next(),
            0,
            phase_b_meta,
            {
                "elementId": "4:test:dummy",
                "eventType": "n",
                "operation": "d",
                "state": {
                    "before": {
                        "labels": ["CTCodelistRoot"],
                        "properties": {"uid": "deleted_codelist"},
                    },
                    "after": None,
                },
            },
        ]
    )

    return records


def _write_test_change_log():
    """Write the test change log to a temporary file and return the path."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, prefix="correction_020_test_"
    ) as tmpfile:
        json.dump(_build_test_change_log(), tmpfile)
    return tmpfile.name


def test_restore_codelist_term_nodes():
    """Test restoration of CTCodelistTerm nodes from change log"""
    _setup_test_data(TEST_DATA_RESTORE_CLT_NODES)

    # Verify initial orphaned state - verification should fail before correction
    with pytest.raises(AssertionError):
        correction_verification_020.test_no_orphaned_correction_019_terms()

    # Write test change log and patch the constant to point at it
    change_log_path = _write_test_change_log()

    try:
        with patch.object(correction_020, "CHANGE_LOG_FILE", change_log_path):
            # Run correction
            result = correction_020.restore_codelist_term_nodes(*CORRECTION_ARGS)
            assert result, "Correction should report changes were made"

        # Verification should pass after correction
        correction_verification_020.test_no_orphaned_correction_019_terms()

        # Verify CTCodelistTerm A: C70543 / "NEVER"
        res, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (tr:CTTermRoot {uid: 'C70543'})
                  <-[:HAS_TERM_ROOT]-(clt:CTCodelistTerm {submission_value: 'NEVER'})
            RETURN clt
            """,
        )
        assert (
            len(res) == 1
        ), "CTCodelistTerm 'NEVER' should be created with HAS_TERM_ROOT to C70543"

        # Verify HAS_TERM from C78738
        res, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (clr:CTCodelistRoot {uid: 'C78738'})
                  -[ht:HAS_TERM]->(clt:CTCodelistTerm {submission_value: 'NEVER'})
            RETURN ht.author_id AS author_id, ht.start_date AS start_date
            """,
        )
        assert len(res) == 1, "HAS_TERM from C78738 to 'NEVER' should be restored"
        assert res[0]["author_id"] == "fd909732-bc9e-492b-a1ed-6e27757a4f00"

        # Verify HAS_TERM from C83004
        res, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (clr:CTCodelistRoot {uid: 'C83004'})
                  -[ht:HAS_TERM]->(clt:CTCodelistTerm {submission_value: 'NEVER'})
            RETURN ht
            """,
        )
        assert len(res) == 1, "HAS_TERM from C83004 to 'NEVER' should be restored"

        # Verify CONTAINS_SUBMISSION_VALUE
        res, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (pt:CTPackageTerm)-[:CONTAINS_SUBMISSION_VALUE]->
                  (clt:CTCodelistTerm {submission_value: 'NEVER'})
            RETURN pt.uid AS uid ORDER BY uid
            """,
        )
        assert len(res) == 2, "Two CONTAINS_SUBMISSION_VALUE should be restored"
        assert res[0]["uid"] == "SDTM__CT__2021-12-17_C70543"
        assert res[1]["uid"] == "SDTM__CT__2022-03-25_C70543"

        # Verify CTCodelistTerm B: CTTerm_000108 / "OBESITY"
        res, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (clr:CTCodelistRoot {uid: 'CTCodelist_000005'})
                  -[ht:HAS_TERM]->(clt:CTCodelistTerm {submission_value: 'OBESITY'})
                  -[:HAS_TERM_ROOT]->(tr:CTTermRoot {uid: 'CTTerm_000108'})
            RETURN ht.order AS order
            """,
        )
        assert len(res) == 1, "CTCodelistTerm B should be fully restored"
        assert res[0]["order"] == 95, "HAS_TERM order property should be preserved"

        # Verify scenario C: existing CTCodelistTerm is not duplicated
        res, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (clr:CTCodelistRoot {uid: 'C78738'})
                  -[:HAS_TERM]->(clt:CTCodelistTerm {submission_value: 'EXISTING_SV'})
                  -[:HAS_TERM_ROOT]->(tr:CTTermRoot {uid: 'CTTermRoot_existing'})
            RETURN clt
            """,
        )
        assert len(res) == 1, "Existing CTCodelistTerm should still be intact"

    finally:
        os.unlink(change_log_path)


@pytest.mark.order(after="test_restore_codelist_term_nodes")
def test_repeat_restore_is_idempotent():
    """Test that running the correction again makes no changes (MERGE idempotency)"""
    change_log_path = _write_test_change_log()

    try:
        with patch.object(correction_020, "CHANGE_LOG_FILE", change_log_path):
            result = correction_020.restore_codelist_term_nodes(*CORRECTION_ARGS)
            assert not result, "Second run should report no changes (idempotent)"
    finally:
        os.unlink(change_log_path)
