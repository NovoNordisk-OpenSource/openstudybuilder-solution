"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import pytest

from tests import test_migration_004


@pytest.fixture(scope="module")
def migration():
    """
    This method is empty as we do not want to run any migration script here.
    We just wish to run all tests related to a specific migration.
    """


def test_indexes_and_constraints():
    test_migration_004.test_indexes_and_constraints(migration)


def test_study_activity_item_root_value_pairs():
    test_migration_004.test_study_activity_item_root_value_pairs(migration)


def test_single_activity_item_per_class():
    test_migration_004.test_single_activity_item_per_class(migration)


def test_study_activity_subgroup_and_group_selection_migration():
    test_migration_004.test_study_activity_subgroup_and_group_selection_migration(
        migration
    )


def test_study_soa_group_migration():
    test_migration_004.test_study_soa_group_migration(migration)


def test_study_relationships_removal_from_study_subgroup_group_and_soa_group():
    test_migration_004.test_study_relationships_removal_from_study_subgroup_group_and_soa_group(
        migration
    )


def test_syntax_sequence_id_refinement_and_renumbering():
    test_migration_004.test_syntax_sequence_id_refinement_and_renumbering(migration)
