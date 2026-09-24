"""Data corrections for PROD July 2025. This must be run AFTER the migration script has been successfully run."""

import os

import pytest

from data_corrections import correction_012
from data_corrections.utils.utils import get_db_driver, save_md_title
from migrations.utils.utils import execute_statements, get_logger
from tests.data.db_before_correction_012 import TEST_DATA
from tests.utils.utils import clear_db
from verifications import correction_verification_012

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
    save_md_title(VERIFY_RUN_LABEL, correction_012.__doc__, desc)


@pytest.fixture(scope="module")
def verify_initial_data(initial_data):
    # Verify the test data by calling each verification function.
    # If the test data has been set up correctly, they should all fail at this stage.
    functions = [
        correction_verification_012.test_remove_duplicate_activity_instance_classes,
    ]
    for func in functions:
        with pytest.raises(AssertionError):
            func()


@pytest.fixture(scope="module")
def correction(verify_initial_data):
    # Run migration
    correction_012.main("test_correction")


def test_remove_duplicate_activity_instance_classes(correction):
    correction_verification_012.test_remove_duplicate_activity_instance_classes()


@pytest.mark.order(after="test_remove_duplicate_activity_instance_classes")
def test_repeat_remove_duplicate_activity_instance_classes():
    assert not correction_012.remove_duplicate_activity_instance_classes(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )
