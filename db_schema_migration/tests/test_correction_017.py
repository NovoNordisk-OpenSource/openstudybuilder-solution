"""Data corrections for PROD: Test StudyVisits having correct properties based on visit_number/unique_visit_number."""

import os

import pytest

from data_corrections import correction_017
from data_corrections.utils.utils import get_db_driver, save_md_title
from migrations.utils.utils import execute_statements, get_logger
from tests.data.db_before_correction_017 import (  # TEST_DATA_FIX_STUDIES_DIFFERENT_VERSIONS,
    TEST_DATA_FIX_DUPLICATED_UNIQUE_VISIT_NUMBERS,
    TEST_DATA_REMOVE_DUPLICATED_NON_VISIT,
    TEST_DATA_REMOVE_SOA_CELL_WITHOUT_RELEASED,
    TEST_DATA_REMOVE_STUDY_ACTION_BROKEN_AFTER,
)
from tests.utils.utils import clear_db
from verifications import correction_verification_017

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()

VERIFY_RUN_LABEL = "test_verification"
CORRECTION_ARGS = (DB_DRIVER, LOGGER, VERIFY_RUN_LABEL)


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Initialize logging once at the start of the test session"""
    desc = f"Running verification for data corrections on DB '{os.environ['DATABASE_NAME']}'"
    save_md_title(VERIFY_RUN_LABEL, correction_017.__doc__, desc)
    yield


def _setup_test_data(test_data):
    """Helper to set up test data for a test"""
    clear_db()
    execute_statements(test_data)


def test_remove_duplicated_non_visit_and_unscheduled_visits():
    """Test remove_duplicated_non_visit_and_unscheduled_visits correction"""
    # Setup test data
    _setup_test_data(TEST_DATA_REMOVE_DUPLICATED_NON_VISIT)

    # Verify initial state (should fail)
    with pytest.raises(AssertionError):
        correction_verification_017.test_remove_duplicated_non_visit_and_unscheduled_visits()

    # Run correction
    correction_017.remove_duplicated_non_visit_and_unscheduled_visits(*CORRECTION_ARGS)

    # Verify correction worked
    correction_verification_017.test_remove_duplicated_non_visit_and_unscheduled_visits()


@pytest.mark.order(after="test_remove_duplicated_non_visit_and_unscheduled_visits")
def test_repeat_remove_duplicated_non_visit_and_unscheduled_visits():
    """Test that correction is idempotent"""
    assert not correction_017.remove_duplicated_non_visit_and_unscheduled_visits(
        *CORRECTION_ARGS
    )


def test_remove_study_action_with_broken_after():
    """Test remove_study_action_with_broken_after correction"""
    # Setup test data
    _setup_test_data(TEST_DATA_REMOVE_STUDY_ACTION_BROKEN_AFTER)

    # Verify initial state (should fail)
    with pytest.raises(AssertionError):
        correction_verification_017.test_remove_study_action_with_broken_after()

    # Run correction
    correction_017.remove_study_action_with_broken_after(*CORRECTION_ARGS)

    # Verify correction worked
    correction_verification_017.test_remove_study_action_with_broken_after()


@pytest.mark.order(after="test_remove_study_action_with_broken_after")
def test_repeat_remove_study_action_with_broken_after():
    """Test that correction is idempotent"""
    assert not correction_017.remove_study_action_with_broken_after(*CORRECTION_ARGS)


def test_fix_duplicated_unique_visit_numbers_and_incorrect_visit_number_visit_name_and_short_name():
    """Test fix_duplicated_unique_visit_numbers_and_incorrect_visit_number_visit_name_and_short_name correction"""
    # Setup test data
    _setup_test_data(TEST_DATA_FIX_DUPLICATED_UNIQUE_VISIT_NUMBERS)

    # Verify initial state (should fail)
    with pytest.raises(AssertionError):
        correction_verification_017.test_fix_duplicated_unique_visit_numbers_and_incorrect_visit_number_visit_name_and_short_name()

    # Run dependencies first
    correction_017.remove_duplicated_non_visit_and_unscheduled_visits(*CORRECTION_ARGS)
    # Run correction
    correction_017.fix_duplicated_unique_visit_numbers_and_incorrect_visit_number_visit_name_and_short_name(
        *CORRECTION_ARGS
    )

    # Verify correction worked
    correction_verification_017.test_fix_duplicated_unique_visit_numbers_and_incorrect_visit_number_visit_name_and_short_name()


@pytest.mark.order(
    after="test_fix_duplicated_unique_visit_numbers_and_incorrect_visit_number_visit_name_and_short_name"
)
def test_repeat_fix_duplicated_unique_visit_numbers_and_incorrect_visit_number_visit_name_and_short_name():
    """Test that correction is idempotent"""
    assert not correction_017.fix_duplicated_unique_visit_numbers_and_incorrect_visit_number_visit_name_and_short_name(
        *CORRECTION_ARGS
    )


# def test_fix_studies_different_versions_with_the_same_start_date():
#     """Test fix_studies_different_versions_with_the_same_start_date correction"""
#     # Setup test data
#     _setup_test_data(TEST_DATA_FIX_STUDIES_DIFFERENT_VERSIONS)
#
#     # Verify initial state (should fail)
#     with pytest.raises(AssertionError):
#         correction_verification_017.test_fix_studies_different_versions_with_the_same_start_date()
#
#     # Run correction
#     correction_017.fix_studies_different_versions_with_the_same_start_date(
#         *CORRECTION_ARGS
#     )
#
#     # Verify correction worked
#     correction_verification_017.test_fix_studies_different_versions_with_the_same_start_date()


# @pytest.mark.order(after="test_fix_studies_different_versions_with_the_same_start_date")
# def test_repeat_fix_studies_different_versions_with_the_same_start_date():
#     """Test that correction is idempotent"""
#     assert not correction_017.fix_studies_different_versions_with_the_same_start_date(
#         *CORRECTION_ARGS
#     )


def test_remove_soa_cell_relationships_without_released_study():
    """Test remove_soa_cell_relationships_without_released_study correction"""
    # Setup test data
    _setup_test_data(TEST_DATA_REMOVE_SOA_CELL_WITHOUT_RELEASED)

    # Verify initial state (should fail)
    with pytest.raises(AssertionError):
        correction_verification_017.test_remove_soa_cell_relationships_without_released_study()

    # Run correction
    correction_017.remove_soa_cell_relationships_without_released_study(
        *CORRECTION_ARGS
    )

    # Verify correction worked
    correction_verification_017.test_remove_soa_cell_relationships_without_released_study()


@pytest.mark.order(after="test_remove_soa_cell_relationships_without_released_study")
def test_repeat_remove_soa_cell_relationships_without_released_study():
    """Test that correction is idempotent"""
    assert not correction_017.remove_soa_cell_relationships_without_released_study(
        *CORRECTION_ARGS
    )
