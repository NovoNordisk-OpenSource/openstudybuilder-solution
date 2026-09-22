"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import pytest

from tests import test_migration_006_2


@pytest.fixture(scope="module")
def migration():
    """
    This method is empty as we do not want to run any migration script here.
    We just wish to run all tests related to a specific migration.
    """


def test_indexes_and_constraints():
    test_migration_006_2.test_indexes_and_constraints(migration)


def test_merge_reuse_study_selection_metadata():
    test_migration_006_2.test_merge_reuse_study_selection_metadata(migration)


def test_fix_study_soa_group_edit_in_a_wrong_not_shared_way():
    test_migration_006_2.test_fix_study_soa_group_edit_in_a_wrong_not_shared_way(
        migration
    )


def test_submit_and_reject_activity_requests():
    test_migration_006_2.test_submit_and_reject_activity_requests(migration)


def test_migrate_remove_soa_group_node_without_any_study_activities():
    test_migration_006_2.test_migrate_remove_soa_group_node_without_any_study_activities(
        migration
    )


def test_study_activities_linked_to_deleted_soa_group():
    test_migration_006_2.test_study_activities_linked_to_deleted_soa_group(migration)
