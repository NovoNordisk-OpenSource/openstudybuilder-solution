"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import pytest

from tests import test_migration_003


@pytest.fixture(scope="module")
def migration():
    """
    This method is empty as we do not want to run any migration script here.
    We just wish to run all tests related to a specific migration.
    """


def test_indexes_and_constraints():
    test_migration_003.test_indexes_and_constraints(migration)


def test_study_selections_labels():
    test_migration_003.test_indexes_and_constraints(migration)
    test_migration_003.test_ct_config_values(migration)
    test_migration_003.test_study_selection_labels(migration)


def test_study_selection_deletion_convention():
    test_migration_003.test_study_selection_deletion_convention(migration)


def test_study_selection_drop_relationships():
    test_migration_003.test_study_selection_drop_relationships(migration)


def test_study_activity_schedule_cascade_deletion():
    test_migration_003.test_study_activity_schedule_cascade_deletion(migration)


def test_study_selection_switch_relationships():
    test_migration_003.test_study_selection_switch_relationships(migration)


def test_activity_groupings():
    test_migration_003.test_activity_groupings(migration)


def test_syntax_sequence_id_refinement():
    test_migration_003.test_syntax_sequence_id_refinement(migration)


def test_study_activity_subgroup_and_group_selection_migration():
    test_migration_003.test_study_activity_subgroup_and_group_selection_migration(
        migration
    )


def test_simple_concept_migration():
    test_migration_003.test_simple_concept_migration(migration)
