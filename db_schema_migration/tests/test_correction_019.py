"""Data corrections for PROD: Test removal of Veeva-imported codelists and terms."""

import os

import pytest

from data_corrections import correction_019
from data_corrections.utils.utils import get_db_driver, run_cypher_query, save_md_title
from migrations.utils.utils import execute_statements, get_logger
from tests.data.db_before_correction_019 import TEST_DATA_REMOVE_VEEVA_IMPORTS
from tests.utils.utils import clear_db
from verifications import correction_verification_019

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()

VERIFY_RUN_LABEL = "test_verification"
CORRECTION_ARGS = (DB_DRIVER, LOGGER, VERIFY_RUN_LABEL)


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Initialize logging once at the start of the test session"""
    desc = f"Running verification for data corrections on DB '{os.environ['DATABASE_NAME']}'"
    save_md_title(VERIFY_RUN_LABEL, correction_019.__doc__, desc)
    yield


def _setup_test_data(test_data):
    """Helper to set up test data for a test"""
    clear_db()
    execute_statements(test_data)


def test_remove_veeva_codelists_and_terms():
    """Test removal of Veeva-imported codelists and terms"""
    # Setup test data
    _setup_test_data(TEST_DATA_REMOVE_VEEVA_IMPORTS)

    # Verify initial state (should fail — unprotected Veeva terms exist)
    with pytest.raises(AssertionError):
        correction_verification_019.test_no_veeva_terms_remain()

    # Run corrections (terms first, then codelists)
    correction_019.remove_veeva_terms(*CORRECTION_ARGS)
    correction_019.remove_veeva_codelists(*CORRECTION_ARGS)

    # Verify corrections worked
    correction_verification_019.test_no_veeva_codelists_remain()
    correction_verification_019.test_no_veeva_terms_remain()

    # Assert non-Veeva codelist C is preserved
    res, _ = run_cypher_query(
        DB_DRIVER,
        "MATCH (clr:CTCodelistRoot {uid: 'CTCodelistRoot_cdisc_c'}) RETURN clr",
    )
    assert len(res) == 1, "Non-Veeva codelist C should be preserved"

    # Assert CDISC term from mixed codelist B is preserved (unlinked, not deleted)
    res, _ = run_cypher_query(
        DB_DRIVER,
        "MATCH (tr:CTTermRoot {uid: 'CTTermRoot_cdisc_in_veeva'}) RETURN tr",
    )
    assert len(res) == 1, "CDISC term from mixed codelist B should be preserved"

    # Assert CDISC term is no longer linked to deleted Veeva codelist B
    res, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (clr:CTCodelistRoot {uid: 'CTCodelistRoot_veeva_b'})
              -[:HAS_TERM]->(clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->
              (tr:CTTermRoot {uid: 'CTTermRoot_cdisc_in_veeva'})
        RETURN clt
        """,
    )
    assert len(res) == 0, "CDISC term should be unlinked from deleted Veeva codelist B"

    # Assert protected term D with CTTermContext is preserved
    res, _ = run_cypher_query(
        DB_DRIVER,
        "MATCH (tr:CTTermRoot {uid: 'CTTermRoot_veeva_protected_d'}) RETURN tr",
    )
    assert len(res) == 1, "Protected Veeva term D should be preserved"

    # Assert CTTermContext reference is intact
    res, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (ctx:CTTermContext)-[:HAS_SELECTED_TERM]->
              (tr:CTTermRoot {uid: 'CTTermRoot_veeva_protected_d'})
        RETURN ctx
        """,
    )
    assert len(res) == 1, "CTTermContext reference to protected term should be intact"

    # Assert Veeva term E with orphaned CTTermContext is deleted
    res, _ = run_cypher_query(
        DB_DRIVER,
        "MATCH (tr:CTTermRoot {uid: 'CTTermRoot_veeva_orphaned_e'}) RETURN tr",
    )
    assert len(res) == 0, "Veeva term E with orphaned CTTermContext should be deleted"

    # Assert orphaned CTTermContext is also deleted
    res, _ = run_cypher_query(
        DB_DRIVER,
        "MATCH (ctx:CTTermContext {uid: 'CTTermContext_orphaned_e'}) RETURN ctx",
    )
    assert len(res) == 0, "Orphaned CTTermContext should be deleted"

    # Assert unprotected Veeva terms are deleted
    for term_uid in [
        "CTTermRoot_veeva_a1",
        "CTTermRoot_veeva_a2",
        "CTTermRoot_veeva_b1",
    ]:
        res, _ = run_cypher_query(
            DB_DRIVER,
            "MATCH (tr:CTTermRoot {uid: $uid}) RETURN tr",
            params={"uid": term_uid},
        )
        assert len(res) == 0, f"Veeva term {term_uid} should be deleted"

    # Assert empty Veeva codelists are deleted
    for cl_uid in ["CTCodelistRoot_veeva_a", "CTCodelistRoot_veeva_b"]:
        res, _ = run_cypher_query(
            DB_DRIVER,
            "MATCH (clr:CTCodelistRoot {uid: $uid}) RETURN clr",
            params={"uid": cl_uid},
        )
        assert len(res) == 0, f"Veeva codelist {cl_uid} should be deleted"

    # Assert Veeva codelist F is preserved (still has protected term D)
    res, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (clr:CTCodelistRoot {uid: 'CTCodelistRoot_veeva_f'})
              -[:HAS_TERM]->(clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->
              (tr:CTTermRoot {uid: 'CTTermRoot_veeva_protected_d'})
        RETURN clr
        """,
    )
    assert (
        len(res) == 1
    ), "Veeva codelist F should be preserved (contains protected term D)"

    # Assert non-Veeva CDISC term C1 is untouched
    res, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (clr:CTCodelistRoot {uid: 'CTCodelistRoot_cdisc_c'})
              -[:HAS_TERM]->(clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->
              (tr:CTTermRoot {uid: 'CTTermRoot_cdisc_c1'})
        RETURN tr
        """,
    )
    assert len(res) == 1, "CDISC term C1 should still be linked to CDISC codelist C"


@pytest.mark.order(after="test_remove_veeva_codelists_and_terms")
def test_repeat_remove_veeva_codelists():
    """Test that codelist removal is idempotent"""
    assert not correction_019.remove_veeva_codelists(*CORRECTION_ARGS)


@pytest.mark.order(after="test_remove_veeva_codelists_and_terms")
def test_repeat_remove_veeva_terms():
    """Test that term removal is idempotent"""
    assert not correction_019.remove_veeva_terms(*CORRECTION_ARGS)
