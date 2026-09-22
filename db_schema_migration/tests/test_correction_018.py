"""Data corrections for PROD: Test StudyVisit duplication caused by Study cloning bug."""

import os

import pytest

from data_corrections import correction_018
from data_corrections.utils.utils import get_db_driver, save_md_title
from migrations.utils.utils import execute_statements, get_logger
from tests.data.db_before_correction_018 import TEST_DATA_FIX_DUPLICATED_STUDY_VISITS
from tests.utils.utils import clear_db
from verifications import correction_verification_018

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()

VERIFY_RUN_LABEL = "test_verification"
CORRECTION_ARGS = (DB_DRIVER, LOGGER, VERIFY_RUN_LABEL)


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Initialize logging once at the start of the test session"""
    desc = f"Running verification for data corrections on DB '{os.environ['DATABASE_NAME']}'"
    save_md_title(VERIFY_RUN_LABEL, correction_018.__doc__, desc)
    yield


def _setup_test_data(test_data):
    """Helper to set up test data for a test"""
    clear_db()
    execute_statements(test_data)


def test_fix_duplicated_study_visits_from_study_cloning():
    """Test fix_duplicated_study_visits_from_study_cloning correction"""
    # Setup test data
    _setup_test_data(TEST_DATA_FIX_DUPLICATED_STUDY_VISITS)

    # Verify initial state (should fail — duplicates exist)
    with pytest.raises(AssertionError):
        correction_verification_018.test_fix_duplicated_study_visits_from_study_cloning()

    # Run correction
    correction_018.fix_duplicated_study_visits_from_study_cloning(*CORRECTION_ARGS)

    # Verify correction worked
    correction_verification_018.test_fix_duplicated_study_visits_from_study_cloning()


@pytest.mark.order(after="test_fix_duplicated_study_visits_from_study_cloning")
def test_repeat_fix_duplicated_study_visits_from_study_cloning():
    """Test that correction is idempotent"""
    assert not correction_018.fix_duplicated_study_visits_from_study_cloning(
        *CORRECTION_ARGS
    )
