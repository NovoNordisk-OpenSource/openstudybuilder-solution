"""Data corrections for PROD: August 2025."""

import os

import pytest

from data_corrections import correction_013
from data_corrections.utils.utils import get_db_driver, save_md_title
from migrations.utils.utils import execute_statements, get_logger
from tests.data.db_before_correction_013 import TEST_DATA
from tests.utils.utils import clear_db
from verifications import correction_verification_013

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
    save_md_title(VERIFY_RUN_LABEL, correction_013.__doc__, desc)


@pytest.fixture(scope="module")
def verify_initial_data(initial_data):
    # Verify the test data by calling each verification function.
    # If the test data has been set up correctly, they should all fail at this stage.
    functions = [
        correction_verification_013.test_fix_author_id_info,
    ]
    for func in functions:
        with pytest.raises(AssertionError):
            func()


@pytest.fixture(scope="module")
def correction(verify_initial_data):
    # Run migration
    correction_013.main("test_correction")


def test_fix_author_id_info(correction):
    correction_verification_013.test_fix_author_id_info()


@pytest.mark.order(after="test_fix_author_id_info")
def test_repeat_fix_author_id_info():
    assert not correction_013.fix_author_id_info(DB_DRIVER, LOGGER, VERIFY_RUN_LABEL)
