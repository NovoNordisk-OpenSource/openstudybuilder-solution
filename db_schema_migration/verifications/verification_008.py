"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import pytest

from tests import test_migration_008


@pytest.fixture(scope="module")
def migration():
    """
    This method is empty as we do not want to run any migration script here.
    We just wish to run all tests related to a specific migration.
    """


def test_ct_config_values():
    test_migration_008.test_ct_config_values(migration)


def test_indexes_and_constraints():
    test_migration_008.test_indexes_and_constraints(migration)


def test_library_compounds():
    test_migration_008.test_library_compounds(migration, True)


def test_study_compounds():
    test_migration_008.test_study_compounds(migration)


def test_non_visit_and_unscheduled_visit_number_reversal():
    test_migration_008.test_migrate_non_visit_and_unscheduled_visit_number_reversal(
        migration
    )
