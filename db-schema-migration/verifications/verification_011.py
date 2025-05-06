"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import pytest

from tests import test_migration_011


@pytest.fixture(scope="module")
def migration():
    """
    This method is empty as we do not want to run any migration script here.
    We just wish to run all tests related to a specific migration.
    """


def test_ct_config_values():
    test_migration_011.test_ct_config_values(migration)


def test_indexes_and_constraints():
    test_migration_011.test_indexes_and_constraints(migration)


def test_change_value_of_name_property_of_activity_instance_class():
    test_migration_011.test_change_value_of_name_property_of_activity_instance_class()


def test_add_level_property_to_activity_instance_class():
    test_migration_011.test_add_level_property_to_activity_instance_class()


def test_update_parent_class_relationship_of_activity_instance_class():
    test_migration_011.test_update_parent_class_relationship_of_activity_instance_class()


def test_remove_old_activity_instance_class_nodes():
    test_migration_011.test_remove_old_activity_instance_class_nodes()


def test_move_rels_from_old_nodes_to_events_node():
    test_migration_011.test_move_rels_from_old_nodes_to_events_node()


def test_move_rels_from_old_nodes_to_interventions_node():
    test_migration_011.test_move_rels_from_old_nodes_to_interventions_node()


def test_update_is_adam_param_specific_property_of_activity_item_to_false_if_it_is_null():
    test_migration_011.test_update_is_adam_param_specific_property_of_activity_item_to_false_if_it_is_null()


def test_move_props_to_has_item_class_rel():
    test_migration_011.test_move_props_to_has_item_class_rel()


def test_migrate_data_domain_from_activity_instance_class_to_dataset():
    test_migration_011.test_migrate_data_domain_from_activity_instance_class_to_dataset(
        migration
    )


def test_migrate_related_codelist_from_activity_item_class_to_codelist():
    test_migration_011.test_migrate_related_codelist_from_activity_item_class_to_codelist(
        migration
    )


def test_migrate_missings_1():
    test_migration_011.test_migrate_missings_1(migration)


def test_migrate_missings_2():
    test_migration_011.test_migrate_missings_2(migration)


def test_migrate_missings_3():
    test_migration_011.test_migrate_missings_3(migration)


def test_migrate_missings4():
    test_migration_011.test_migrate_missings_4(migration)


def test_migrate_missings_5():
    test_migration_011.test_migrate_missings_5(migration)


def test_migrate_missings_6():
    test_migration_011.test_migrate_missings_6(migration)


def test_migrate_missings_7():
    test_migration_011.test_migrate_missings_7(migration)


def test_migrate_missings_8():
    test_migration_011.test_migrate_missings_8(migration)


def test_migrate_soa_group_activity_group_activity_subgroup_activity_orders():
    test_migration_011.test_migrate_soa_group_activity_group_activity_subgroup_activity_orders(
        migration
    )
