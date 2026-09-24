"""Data corrections for PROD April 2024."""

import os

import pytest

from data_corrections import correction_007
from data_corrections.utils.utils import get_db_driver, save_md_title
from migrations.utils.utils import execute_statements, get_logger
from tests.data.db_before_correction_007 import TEST_DATA
from tests.utils.utils import clear_db
from verifications import correction_verification_007

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
    save_md_title(VERIFY_RUN_LABEL, correction_007.__doc__, desc)


@pytest.fixture(scope="module")
def correction(initial_data):
    # Run migration
    correction_007.main("test_correction")


def test_delete_unwanted_studies(correction):
    correction_verification_007.test_delete_unwanted_studies()


@pytest.mark.order(after="test_delete_unwanted_studies")
def test_repeat_delete_unwanted_studies():
    assert not correction_007.delete_unwanted_studies(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_remove_na_version_properties(correction):
    correction_verification_007.test_remove_na_version_properties()


@pytest.mark.order(after="test_remove_na_version_properties")
def test_repeat_remove_na_version_properties():
    assert not correction_007.remove_na_version_properties(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_add_missing_end_dates(correction):
    correction_verification_007.test_add_missing_end_dates()


@pytest.mark.order(after="test_add_missing_end_dates")
def test_repeat_add_missing_end_dates():
    assert not correction_007.add_missing_end_dates(DB_DRIVER, LOGGER, VERIFY_RUN_LABEL)


def test_adjust_late_end_dates(correction):
    correction_verification_007.test_adjust_late_end_dates()


@pytest.mark.order(after="test_adjust_late_end_dates")
def test_repeat_adjust_late_end_dates():
    assert not correction_007.adjust_late_end_dates(DB_DRIVER, LOGGER, VERIFY_RUN_LABEL)


def test_adjust_cdisc_has_had_terms(correction):
    correction_verification_007.test_adjust_cdisc_has_had_terms()


@pytest.mark.order(after="test_adjust_cdisc_has_had_terms")
def test_repeat_adjust_cdisc_has_had_terms():
    assert not correction_007.adjust_cdisc_has_had_terms(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_remove_duplicated_terms_in_objective_cat(correction):
    correction_verification_007.test_remove_duplicated_terms_in_objective_cat()


@pytest.mark.order(after="test_remove_duplicated_terms_in_objective_cat")
def test_repeat_remove_duplicated_terms_in_objective_cat():
    assert not correction_007.remove_duplicated_terms_in_objective_cat(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_capitalize_first_letter_of_syntax_instance_and_pre_instance_if_template_parameter(
    correction,
):
    correction_verification_007.test_capitalize_first_letter_of_syntax_instance_and_pre_instance_if_template_parameter()


@pytest.mark.order(
    after="test_capitalize_first_letter_of_syntax_instance_and_pre_instance_if_template_parameter"
)
def test_repeat_capitalize_first_letter_of_syntax_instance_and_pre_instance_if_template_parameter():
    assert not correction_007.capitalize_first_letter_of_syntax_instance_and_pre_instance_if_template_parameter(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_remove_duplicated_terms_in_operator(correction):
    correction_verification_007.test_remove_duplicated_terms_in_operator()


@pytest.mark.order(after="test_remove_duplicated_terms_in_operator")
def test_repeat_remove_duplicated_terms_in_operator():
    assert not correction_007.remove_duplicated_terms_in_operator(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_remove_duplicated_terms_in_finding_subcat(correction):
    correction_verification_007.test_remove_duplicated_terms_in_finding_subcat()


@pytest.mark.order(after="test_remove_duplicated_terms_in_finding_subcat")
def test_repeat_remove_duplicated_terms_in_finding_subcat():
    assert not correction_007.remove_duplicated_terms_in_finding_subcat(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_remove_duplicated_terms_in_frequency(correction):
    correction_verification_007.test_remove_duplicated_terms_in_frequency()


@pytest.mark.order(after="test_remove_duplicated_terms_in_frequency")
def test_repeat_remove_duplicated_terms_in_frequency():
    assert not correction_007.remove_duplicated_terms_in_frequency(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )
