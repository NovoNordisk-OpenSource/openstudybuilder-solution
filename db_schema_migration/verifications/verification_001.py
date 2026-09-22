"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import pytest

from tests import test_migration_001


@pytest.fixture(scope="module")
def migration():
    """
    This method is empty as we do not want to run any migration script here.
    We just wish to run all tests related to a specific migration.
    """


def test_ct_config_values():
    test_migration_001.test_ct_config_values(migration)


def test_study_fields():
    test_migration_001.test_study_fields(migration)


def test_study_criteria():
    test_migration_001.test_study_criteria(migration)


def test_activities():
    test_migration_001.test_activities(migration)


def test_template_parameters():
    test_migration_001.test_template_parameters(migration)


def test_chars_in_uids():
    test_migration_001.test_chars_in_uids(migration)


def test_requested_library():
    test_migration_001.test_requested_library(migration)


def test_null_flavor_codelist():
    test_migration_001.test_null_flavor_codelist(migration)


def test_indexes_and_constraints():
    test_migration_001.test_indexes_and_constraints(migration)


def test_sponsor_codelists_extensible():
    test_migration_001.test_sponsor_codelists_extensible(migration)
