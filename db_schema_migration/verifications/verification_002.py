"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import pytest

from tests import test_migration_002


@pytest.fixture(scope="module")
def migration():
    """
    This method is empty as we do not want to run any migration script here.
    We just wish to run all tests related to a specific migration.
    """


def test_indexes_and_constraints():
    test_migration_002.test_indexes_and_constraints(migration)


def test_ct_config_values():
    test_migration_002.test_ct_config_values(migration)


def test_syntax_templates_and_instances():
    test_migration_002.test_syntax_templates_and_instances(migration)


def test_default_study_preferred_time_unit():
    test_migration_002.test_default_study_preferred_time_unit(migration)


def test_item_versioning():
    test_migration_002.test_item_versioning(migration)


def test_syntax_sequence_id():
    test_migration_002.test_syntax_sequence_id(migration)


def test_activity_instance_classes():
    test_migration_002.test_activity_instance_classes(migration)


def test_activity_instances_have_activity():
    test_migration_002.test_activity_instances_have_activity(migration)


def test_odm_template_renaming():
    test_migration_002.test_odm_template_renaming(migration)
