"""Data corrections for PROD: Activity Versioning Gap Fix"""

import os

import pytest

from data_corrections import correction_016
from data_corrections.utils.utils import get_db_driver, save_md_title
from migrations.utils.utils import execute_statements, get_logger
from tests.data.db_before_correction_016 import TEST_DATA
from tests.utils.utils import clear_db
from verifications import correction_verification_016

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()

VERIFY_RUN_LABEL = "test_verification"

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


@pytest.fixture(scope="module")
def initial_data():
    """Insert test data"""
    clear_db()
    execute_statements(TEST_DATA)

    # Prepare md for verification summary
    desc = f"Running verification for data corrections on DB '{os.environ['DATABASE_NAME']}'"
    save_md_title(VERIFY_RUN_LABEL, correction_016.__doc__, desc)


@pytest.fixture(scope="module")
def verify_initial_data(initial_data):
    # Verify the test data by calling each verification function.
    # If the test data has been set up correctly, they should all fail at this stage.
    functions = [
        correction_verification_016.test_activity_000317_versioning_gap,
        correction_verification_016.test_remove_cat_submission_value_suffix,
        correction_verification_016.test_missing_retired_relationships,
        correction_verification_016.test_duplicate_term_names,
        correction_verification_016.test_duplicate_term_submission_values,
        correction_verification_016.test_negative_duration_has_term,
        correction_verification_016.test_not_latest_has_version_lacks_end_date,
        correction_verification_016.test_remove_isolated_orphan_nodes,
        correction_verification_016.test_remove_orphan_study_selection_nodes,
    ]
    for func in functions:
        with pytest.raises(AssertionError):
            func()


@pytest.fixture(scope="module")
def correction(verify_initial_data):
    # Run migration
    correction_016.main("test_correction")


def test_activity_000317_versioning_gap(correction):
    correction_verification_016.test_activity_000317_versioning_gap()


@pytest.mark.order(after="test_activity_000317_versioning_gap")
def test_repeat_activity_000317_versioning_gap():
    assert not correction_016.fix_activity_000317_versioning_gap(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_remove_cat_submission_value_suffix(correction):
    correction_verification_016.test_remove_cat_submission_value_suffix()


@pytest.mark.order(after="test_remove_cat_submission_value_suffix")
def test_repeat_remove_cat_submission_value_suffix():
    assert not correction_016.remove_cat_submission_value_suffix(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_missing_retired_relationships(correction):
    correction_verification_016.test_missing_retired_relationships()


@pytest.mark.order(after="test_missing_retired_relationships")
def test_repeat_missing_retired_relationships():
    assert not correction_016.add_missing_retired_relationships(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_duplicate_term_names(correction):
    correction_verification_016.test_duplicate_term_names()


@pytest.mark.order(after="test_duplicate_term_names")
def test_repeat_duplicate_term_names():
    assert not correction_016.solve_duplicate_term_names(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_remove_isolated_orphan_nodes(correction):
    correction_verification_016.test_remove_isolated_orphan_nodes()


@pytest.mark.order(after="test_remove_isolated_orphan_nodes")
def test_repeat_remove_isolated_orphan_nodes():
    assert not correction_016.remove_isolated_orphan_nodes(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_duplicate_term_submission_values(correction):
    correction_verification_016.test_duplicate_term_submission_values()


@pytest.mark.order(after="test_duplicate_term_submission_values")
def test_repeat_duplicate_term_submission_values():
    assert not correction_016.solve_duplicate_term_submission_values(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_negative_duration_has_term(correction):
    correction_verification_016.test_negative_duration_has_term()


@pytest.mark.order(after="test_negative_duration_has_term")
def test_repeat_negative_duration_has_term():
    assert not correction_016.solve_negative_duration_has_term(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_not_latest_has_version_lacks_end_date(correction):
    correction_verification_016.test_not_latest_has_version_lacks_end_date()


@pytest.mark.order(after="test_not_latest_has_version_lacks_end_date")
def test_repeat_not_latest_has_version_lacks_end_date():
    assert not correction_016.solve_not_latest_has_version_lacks_end_date(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_remove_orphan_study_selection_nodes(correction):
    correction_verification_016.test_remove_orphan_study_selection_nodes()


@pytest.mark.order(after="test_remove_orphan_study_selection_nodes")
def test_repeat_remove_orphan_study_selection_nodes():
    assert not correction_016.remove_orphan_study_selection_nodes(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )
