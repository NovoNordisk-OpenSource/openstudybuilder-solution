"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import pytest

from tests import test_migration_010


@pytest.fixture(scope="module")
def migration():
    """
    This method is empty as we do not want to run any migration script here.
    We just wish to run all tests related to a specific migration.
    """


def test_ct_config_values():
    test_migration_010.test_ct_config_values(migration)


def test_indexes_and_constraints():
    test_migration_010.test_indexes_and_constraints(migration)


def test_migrate_unit_definition_properties():
    test_migration_010.test_migrate_unit_definition_properties(migration)


def test_migrate_preferred_time_unit():
    test_migration_010.test_migrate_preferred_time_unit(migration)


def test_migrate_soa_preferred_time_unit():
    test_migration_010.test_migrate_soa_preferred_time_unit(migration)


def test_locked_study_versions_have_protocol_soa_snapshot():
    test_migration_010.test_locked_study_versions_have_protocol_soa_snapshot(migration)


def test_migrate_user_initials_into_author_id_and_user_nodes():
    test_migration_010.test_migrate_user_initials_into_author_id_and_user_nodes(
        migration
    )


def test_migrate_unify_study_visit_window_units():
    test_migration_010.test_migrate_unify_study_visit_window_units(migration)

def test_migrate_study_selection_metadata_merge():
    test_migration_010.test_migrate_study_selection_metadata_merge(migration)
