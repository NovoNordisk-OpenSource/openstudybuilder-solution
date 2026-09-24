"""Data corrections for PROD: Test removal of lonely Neodash dashboard node."""

import os

import pytest

from data_corrections import correction_022
from data_corrections.utils.utils import get_db_driver, run_cypher_query, save_md_title
from migrations.utils.utils import execute_statements, get_logger
from tests.data.db_before_correction_022 import TEST_DATA
from tests.utils.utils import clear_db
from verifications import correction_verification_022

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()

VERIFY_RUN_LABEL = "test_verification"
CORRECTION_ARGS = (DB_DRIVER, LOGGER, VERIFY_RUN_LABEL)


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Initialize logging once at the start of the test session"""
    desc = f"Running verification for data corrections on DB '{os.environ['DATABASE_NAME']}'"
    save_md_title(VERIFY_RUN_LABEL, correction_022.__doc__, desc)
    yield


def _setup_test_data():
    """Helper to set up test data for a test"""
    clear_db()
    execute_statements(TEST_DATA)


def test_remove_lonely_neodash_dashboard():
    """Test deletion of the unused _Neodash_Dashboard row."""
    _setup_test_data()

    with pytest.raises(AssertionError):
        correction_verification_022.test_unused_neodash_dashboard_removed()

    correction_022.remove_lonely_external_data_file_spec_dashboard(*CORRECTION_ARGS)

    correction_verification_022.test_unused_neodash_dashboard_removed()

    res, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (d:_Neodash_Dashboard {uuid: 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'})
        RETURN d
        """,
    )
    assert len(res) == 1, "Unrelated Neodash dashboard must remain"


@pytest.mark.order(after="test_remove_lonely_neodash_dashboard")
def test_repeat_remove_lonely_neodash_dashboard():
    """Test that removal is idempotent."""
    assert not correction_022.remove_lonely_external_data_file_spec_dashboard(
        *CORRECTION_ARGS
    )
