"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import pytest

from tests import test_migration_020


@pytest.fixture(scope="module")
def migration():
    """
    This method is empty as we do not want to run any migration script here.
    We just wish to run all tests related to a specific migration.
    """


def test_ct_config_values():
    test_migration_020.test_ct_config_values(migration)


def test_indexes_and_constraints():
    test_migration_020.test_indexes_and_constraints(migration)


def test_add_codelist_type():
    test_migration_020.test_add_codelist_type(migration)


def test_migrate_sponsor_model_ordinal():
    test_migration_020.test_migrate_sponsor_model_ordinal(migration)
