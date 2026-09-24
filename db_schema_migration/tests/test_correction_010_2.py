"""Data corrections for PROD April 2025. This must be run AFTER the migration script has been succesfully run."""

import os

import pytest

from data_corrections import correction_010_2
from data_corrections.utils.utils import get_db_driver, save_md_title
from migrations.utils.utils import execute_statements, get_logger
from tests.data.db_before_correction_010_2 import TEST_DATA
from tests.utils.utils import clear_db
from verifications import correction_verification_010_2

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
    save_md_title(VERIFY_RUN_LABEL, correction_010_2.__doc__, desc)


@pytest.fixture(scope="module")
def verify_initial_data(initial_data):
    # Verify the test data by calling each verification function.
    # If the test data has been set up correctly, they should all fail at this stage.
    functions = [
        correction_verification_010_2.test_remove_duplicated_activity_instance_class_rels,
        correction_verification_010_2.test_instances_lacking_activity,
    ]
    for func in functions:
        with pytest.raises(AssertionError):
            func()


@pytest.fixture(scope="module")
def correction(verify_initial_data):
    # Run migration
    correction_010_2.main("test_correction")


def test_remove_duplicated_activity_instance_class_rels(correction):
    correction_verification_010_2.test_remove_duplicated_activity_instance_class_rels()


def test_instances_lacking_activity(correction):
    correction_verification_010_2.test_instances_lacking_activity()
