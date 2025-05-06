""" Data corrections for PROD January 2025. This must be run AFTER the migration script has been successfully run. """

import os

import pytest

from data_corrections import correction_010
from data_corrections.utils.utils import get_db_driver, save_md_title
from migrations.utils.utils import execute_statements, get_logger
from tests.data.db_before_correction_010 import TEST_DATA
from tests.utils.utils import clear_db
from verifications import correction_verification_010

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
    save_md_title(VERIFY_RUN_LABEL, correction_010.__doc__, desc)


@pytest.fixture(scope="module")
def correction(initial_data):
    # Run migration
    correction_010.main("test_correction")


def test_remove_user_initials_field_from_all_nodes(correction):
    correction_verification_010.test_remove_user_initials_field_from_all_nodes()


def test_remove_user_initials_field_from_all_relations(correction):
    correction_verification_010.test_remove_user_initials_field_from_all_relations()


def test_create_qphm_user(correction):
    correction_verification_010.test_create_qphm_user()


def test_remove_relationship_between_intervention_and_activity_instance_template_parameters(
    correction,
):
    correction_verification_010.test_remove_relationship_between_intervention_and_activity_instance_template_parameters()
