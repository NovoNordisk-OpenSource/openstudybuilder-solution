"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import pytest

from tests import test_migration_024


@pytest.fixture(scope="module")
def migration():
    """
    This method is empty as we do not want to run any migration script here.
    We just wish to run all tests related to a specific migration.
    """


def test_indexes_and_constraints():
    test_migration_024.test_indexes_and_constraints(migration)


def test_uppercase_project_numbers():
    test_migration_024.test_uppercase_project_numbers(migration)


def test_change_catalogue_of_datatype_codelist():
    test_migration_024.test_change_catalogue_of_datatype_codelist(migration)


def test_codelist_name_values_have_properties():
    test_migration_024.test_codelist_name_values_have_properties(migration)


def test_codelist_attributes_values_cleaned():
    test_migration_024.test_codelist_attributes_values_cleaned(migration)


def test_set_ordinal_for_stresc_codelists():
    test_migration_024.test_set_ordinal_for_stresc_codelists(migration)


def test_non_stresc_codelists_not_marked_ordinal():
    test_migration_024.test_non_stresc_codelists_not_marked_ordinal(migration)


def test_archived_library():
    test_migration_024.test_archived_library(migration)


def test_migrate_feature_flags_to_root_value():
    test_migration_024.test_migrate_feature_flags_to_root_value(migration)


def test_link_sponsor_model_values_to_library():
    test_migration_024.test_link_sponsor_model_values_to_library(migration)


def test_link_dataset_variable_to_data_model_catalogue():
    test_migration_024.test_link_dataset_variable_to_data_model_catalogue(migration)


def test_remove_ct_config_nodes():
    test_migration_024.test_remove_ct_config_nodes(migration)


def test_migrate_meta_study_fields():
    test_migration_024.test_migrate_meta_study_fields(migration)


def test_load_sponsor_model_schemas():
    test_migration_024.test_load_sponsor_model_schemas(migration)


def test_link_sponsor_model_values_to_schema():
    test_migration_024.test_link_sponsor_model_values_to_schema(migration)


def test_no_special_visit_nodes_remain():
    test_migration_024.test_no_special_visit_nodes_remain(migration)


def test_suffix_matches_short_visit_label():
    test_migration_024.test_suffix_matches_short_visit_label(migration)


def test_non_ed_suffix_letters():
    test_migration_024.test_non_ed_suffix_letters(migration)


def test_suffix_visits_keep_visit_sublabel_reference():
    test_migration_024.test_suffix_visits_keep_visit_sublabel_reference(migration)


def test_ed_suffix_visits_have_no_expected_time_value():
    test_migration_024.test_ed_suffix_visits_have_no_expected_time_value(migration)


def test_non_ed_suffix_visits_have_expected_time_value():
    test_migration_024.test_non_ed_suffix_visits_have_expected_time_value(migration)


def test_all_suffix_visits_have_timepoint():
    test_migration_024.test_all_suffix_visits_have_timepoint(migration)


def test_suffix_visit_timepoints_are_zero_global_anchor():
    test_migration_024.test_suffix_visit_timepoints_are_zero_global_anchor(migration)


def test_suffix_visits_have_no_study_day_nodes():
    test_migration_024.test_suffix_visits_have_no_study_day_nodes(migration)


def test_suffix_visits_have_no_study_duration_days_nodes():
    test_migration_024.test_suffix_visits_have_no_study_duration_days_nodes(migration)


def test_all_current_visits_have_visit_order():
    test_migration_024.test_all_current_visits_have_visit_order(migration)


def test_visit_order_is_non_negative():
    test_migration_024.test_visit_order_is_non_negative(migration)


def test_visit_order_unique_per_study():
    test_migration_024.test_visit_order_unique_per_study(migration)


def test_no_odm_item_has_datatype_string_property():
    test_migration_024.test_no_odm_item_has_datatype_string_property(migration)


def test_odm_item_has_no_data_type_relationship_for_comment_and_text():
    test_migration_024.test_odm_item_has_no_data_type_relationship_for_comment_and_text(
        migration
    )


def test_odm_items_with_other_datatypes_have_data_type_relationship():
    test_migration_024.test_odm_items_with_other_datatypes_have_data_type_relationship(
        migration, None
    )


def test_ct_term_context_linked_to_codelist():
    test_migration_024.test_ct_term_context_linked_to_codelist(migration)


def test_remove_unit_definition_deprecated_properties():
    test_migration_024.test_remove_unit_definition_deprecated_properties(migration)


def test_reset_conversion_factor_for_non_convertible_units():
    test_migration_024.test_reset_conversion_factor_for_non_convertible_units(migration)


def test_migrate_control_type_to_array_field():
    test_migration_024.test_migrate_control_type_to_array_field(migration)


def test_rename_activity_item_class_display_name_to_label():
    test_migration_024.test_rename_activity_item_class_display_name_to_label(migration)


def test_convert_non_string_short_visit_labels():
    test_migration_024.test_convert_non_string_short_visit_labels(migration)


def test_save_soa_snapshots_of_locked_and_released_study_versions():
    test_migration_024.test_save_soa_snapshots_of_locked_and_released_study_versions(
        migration
    )


def test_soa_snapshots_are_returned_by_flowchart_endpoints():
    test_migration_024.test_soa_snapshots_are_returned_by_flowchart_endpoints(migration)


def test_remove_legacy_protocol_soa_cell_relationships():
    test_migration_024.test_remove_legacy_protocol_soa_cell_relationships(migration)
