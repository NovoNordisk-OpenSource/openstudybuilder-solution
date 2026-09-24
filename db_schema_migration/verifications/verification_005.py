"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import pytest

from tests import test_migration_005


@pytest.fixture(scope="module")
def migration():
    """
    This method is empty as we do not want to run any migration script here.
    We just wish to run all tests related to a specific migration.
    """


def test_indexes_and_constraints():
    test_migration_005.test_indexes_and_constraints(migration)


def test_fix_study_epoch_order():
    test_migration_005.test_fix_study_epoch_order(migration)


def test_link_variables_with_value_terms():
    test_migration_005.test_link_variables_with_value_terms(migration)


def test_study_selection_deletion_convention():
    test_migration_005.test_study_field_deletion_convention(migration)


def test_add_missing_latest_relationships():
    test_migration_005.test_add_missing_latest_relationships(migration)


def test_study_activity_group_is_linked_to_real_study_root_audit_trail_node():
    test_migration_005.test_study_activity_group_is_linked_to_real_study_root_audit_trail_node(
        migration
    )


# Disabled for now since the test fails with a timeout,
# and the study activity instances are not yet used.
# def test_migrate_study_activity_instances():
#    test_migration_005.test_migrate_study_activity_instances(migration)


def test_remove_duplicated_study_activity_schedules():
    test_migration_005.test_remove_duplicated_study_activity_schedules(migration)


def test_migrate_week_in_study():
    test_migration_005.test_migrate_week_in_study(migration)


def test_migrate_soa_preferred_time_unit():
    test_migration_005.test_migrate_soa_preferred_time_unit(migration)


def test_migrate_study_activity_grouping_and_audit_trail_duplicates_group():
    test_migration_005.test_migrate_study_activity_grouping_and_audit_trail_duplicates_group(
        migration
    )


def test_migrate_study_activity_grouping_and_audit_trail_duplicates_subgroup():
    test_migration_005.test_migrate_study_activity_grouping_and_audit_trail_duplicates_subgroup(
        migration
    )


def test_migrate_study_activity_grouping_and_audit_trail_edit_group():
    test_migration_005.test_migrate_study_activity_grouping_and_audit_trail_edit_group(
        migration
    )


def test_migrate_study_activity_grouping_and_audit_trail_edit_subgroup():
    test_migration_005.test_migrate_study_activity_grouping_and_audit_trail_edit_subgroup(
        migration
    )


def test_migrate_study_activity_grouping_and_audit_trail_redundant_edits_group():
    test_migration_005.test_migrate_study_activity_grouping_and_audit_trail_redundant_edits_group(
        migration
    )


def test_migrate_study_activity_grouping_and_audit_trail_redundant_edits_subgroup():
    test_migration_005.test_migrate_study_activity_grouping_and_audit_trail_redundant_edits_subgroup(
        migration
    )


def test_migrate_nullify_unit_definition_name_sentence_case():
    test_migration_005.test_migrate_nullify_unit_definition_name_sentence_case(
        migration
    )


def test_migrate_missing_activity_item_class():
    test_migration_005.test_migrate_missing_activity_item_class(migration)


def test_migrate_remove_invalid_activity_instances():
    test_migration_005.test_migrate_remove_invalid_activity_instances(migration)
