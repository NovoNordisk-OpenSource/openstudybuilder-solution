"""Data corrections for PROD: October 2025."""

import os

import pytest

from data_corrections import correction_014
from data_corrections.utils.utils import get_db_driver, save_md_title
from migrations.utils.utils import execute_statements, get_logger
from tests.data.db_before_correction_014 import TEST_DATA
from tests.utils.utils import clear_db
from verifications import correction_verification_014

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
    save_md_title(VERIFY_RUN_LABEL, correction_014.__doc__, desc)


@pytest.fixture(scope="module")
def verify_initial_data(initial_data):
    # Verify the test data by calling each verification function.
    # If the test data has been set up correctly, they should all fail at this stage.
    functions = [
        correction_verification_014.test_remove_orphan_activity_instances,
        correction_verification_014.test_remove_orphan_activity_instance_classes,
        correction_verification_014.test_remove_orphan_study_fields,
        correction_verification_014.test_fix_instances_with_multiple_activities,
        correction_verification_014.test_remove_unwanted_sponsor_terms,
        correction_verification_014.test_remove_dummy_definitions,
        correction_verification_014.test_fix_baseline2_submission_values,
        correction_verification_014.test_study_selection_drop_relationships,
        correction_verification_014.test_set_author_id_for_cdisc_data,
    ]
    for func in functions:
        with pytest.raises(AssertionError):
            func()


@pytest.fixture(scope="module")
def correction(verify_initial_data):
    # Run migration
    correction_014.main("test_correction")


def test_remove_orphan_activity_instances(correction):
    correction_verification_014.test_remove_orphan_activity_instances()


@pytest.mark.order(after="test_remove_orphan_activity_instances")
def test_repeat_remove_orphan_activity_instances():
    assert not correction_014.remove_orphan_activity_instances(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_remove_orphan_activity_instance_classes(correction):
    correction_verification_014.test_remove_orphan_activity_instance_classes()


@pytest.mark.order(after="test_remove_orphan_activity_instance_classes")
def test_repeat_remove_orphan_activity_instance_classes():
    assert not correction_014.remove_orphan_activity_instance_classes(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_remove_orphan_study_fields(correction):
    correction_verification_014.test_remove_orphan_study_fields()


@pytest.mark.order(after="test_remove_orphan_study_fields")
def test_repeat_remove_orphan_study_fields():
    assert not correction_014.remove_orphan_study_fields(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_fix_instances_with_multiple_activities(correction):
    correction_verification_014.test_fix_instances_with_multiple_activities()


@pytest.mark.order(after="test_fix_instances_with_multiple_activities")
def test_repeat_fix_instances_with_multiple_activities():
    assert not correction_014.fix_instances_with_multiple_activities(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_remove_unwanted_sponsor_terms(correction):
    correction_verification_014.test_remove_unwanted_sponsor_terms()


@pytest.mark.order(after="test_remove_unwanted_sponsor_terms")
def test_repeat_remove_unwanted_sponsor_terms():
    assert not correction_014.remove_unwanted_sponsor_terms(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_remove_dummy_definitions(correction):
    correction_verification_014.test_remove_dummy_definitions()
    query = """
    MATCH (dv:DummyValue) WHERE dv.definition IS NOT NULL
    RETURN COUNT(dv) AS count
    """
    records, _ = correction_014.run_cypher_query(DB_DRIVER, query)
    assert (
        records[0]["count"] == 2
    ), f"Expected 2 DummyValue nodes with non-null definitions remaining, found {records[0]['count']}."


@pytest.mark.order(after="test_remove_dummy_definitions")
def test_repeat_remove_dummy_definitions():
    assert not correction_014.remove_dummy_definitions(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_fix_baseline2_submission_values(correction):
    correction_verification_014.test_fix_baseline2_submission_values()


@pytest.mark.order(after="test_fix_baseline2_submission_values")
def test_repeat_fix_baseline2_submission_values():
    assert not correction_014.fix_baseline2_submission_values(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_fix_study_selection_drop_relationships(correction):
    correction_verification_014.test_study_selection_drop_relationships()


@pytest.mark.order(after="test_fix_study_selection_drop_relationships")
def test_repeat_fix_study_selection_dropped_relationships():
    assert not correction_014.fix_study_selection_drop_relationships(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_set_author_id_for_cdisc_data(correction):
    correction_verification_014.test_set_author_id_for_cdisc_data()


@pytest.mark.order(after="test_set_author_id_for_cdisc_data")
def test_repeat_set_author_id_for_cdisc_data():
    assert not correction_014.set_author_id_for_cdisc_data(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )


def test_multiple_null_value_reasons(correction):
    correction_verification_014.test_multiple_null_value_reasons()


@pytest.mark.order(after="test_multiple_null_value_reasons")
def test_repeat_multiple_null_value_reasons():
    assert not correction_014.multiple_null_value_reasons(
        DB_DRIVER, LOGGER, VERIFY_RUN_LABEL
    )
