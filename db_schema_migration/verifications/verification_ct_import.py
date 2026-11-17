"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import pytest

from db_schema_migration.tests import test_migration_ct_import


@pytest.fixture(scope="module")
def migration():
    """
    This method is empty as we do not want to run any migration script here.
    We just wish to run all tests related to a specific migration.
    """


def test_indexes_and_constraints():
    test_migration_ct_import.test_indexes_and_constraints(migration)


def test_copied_nodes_carry_staging_label():
    test_migration_ct_import.test_copied_nodes_carry_staging_label(migration)


def test_rename_staging_relationship_types():
    test_migration_ct_import.test_rename_staging_relationship_types(migration)


def test_rename_staging_labels():
    test_migration_ct_import.test_rename_staging_labels(migration)


def test_staging_graph_copied_to_mdr():
    test_migration_ct_import.test_staging_graph_copied_to_mdr(migration)


def test_staging_node_and_relationship_counts():
    test_migration_ct_import.test_staging_node_and_relationship_counts(migration)


def test_no_relationships_between_staging_and_mdr_data():
    test_migration_ct_import.test_no_relationships_between_staging_and_mdr_data(
        migration
    )


def test_temporary_copy_markers_removed():
    test_migration_ct_import.test_temporary_copy_markers_removed(migration)
