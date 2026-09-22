"""Data corrections for PROD: Test XML entity cleanup in node definitions."""

import os

import pytest

from data_corrections import correction_021
from data_corrections.utils.utils import get_db_driver, run_cypher_query, save_md_title
from migrations.utils.utils import execute_statements, get_logger
from tests.data.db_before_correction_021 import TEST_DATA
from tests.utils.utils import clear_db
from verifications import correction_verification_021

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()

VERIFY_RUN_LABEL = "test_verification"
CORRECTION_ARGS = (DB_DRIVER, LOGGER, VERIFY_RUN_LABEL)


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Initialize logging once at the start of the test session"""
    desc = f"Running verification for data corrections on DB '{os.environ['DATABASE_NAME']}'"
    save_md_title(VERIFY_RUN_LABEL, correction_021.__doc__, desc)
    yield


def _setup_test_data():
    """Helper to set up test data for a test"""
    clear_db()
    execute_statements(TEST_DATA)


def test_replace_xml_entities_in_definitions():
    """Test replacement of XML entities in definitions."""
    _setup_test_data()

    # Verify initial state (should fail — xml entities still present)
    with pytest.raises(AssertionError):
        correction_verification_021.test_no_xml_entities_in_definitions()

    # Run correction
    correction_021.replace_xml_entities_in_definitions(*CORRECTION_ARGS)

    # Verify correction worked
    correction_verification_021.test_no_xml_entities_in_definitions()

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n:XmlDefinitionCleanupNode {uid: 1})
        RETURN n.definition AS definition
        """,
    )
    assert records[0]["definition"] == "Alpha · beta - gamma"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n:XmlDefinitionCleanupNode {uid: 2})
        RETURN n.definition AS definition
        """,
    )
    assert records[0]["definition"] == "One more · sample"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n:XmlDefinitionCleanupNode {uid: 3})
        RETURN n.definition AS definition
        """,
    )
    assert records[0]["definition"] == "No xml entities here"


@pytest.mark.order(after="test_replace_xml_entities_in_definitions")
def test_repeat_replace_xml_entities_in_definitions():
    """Test that XML entity replacement is idempotent."""
    assert not correction_021.replace_xml_entities_in_definitions(*CORRECTION_ARGS)
