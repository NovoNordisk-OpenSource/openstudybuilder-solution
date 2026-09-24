import os

import pytest

from migrations import migration_018
from migrations.utils.utils import (
    execute_statements,
    get_db_connection,
    get_db_driver,
    get_logger,
    run_cypher_query,
)
from tests import common
from tests.data.db_before_migration_018 import TEST_DATA
from tests.utils.utils import clear_db

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=protected-access
# pylint: disable=broad-except

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

db = get_db_connection()
DB_DRIVER = get_db_driver()
logger = get_logger(os.path.basename(__file__))


@pytest.fixture(scope="module")
def initial_data():
    """Insert test data"""
    clear_db()
    execute_statements(TEST_DATA)


@pytest.fixture(scope="module")
def migration(initial_data):
    # Run migration
    migration_018.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_migrate_activity_grouping(migration):
    logger.info("Verify activity grouping migration results")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (avg:ActivityValidGroup)
        RETURN avg
        """,
    )

    assert (
        len(records) == 0
    ), "There must not exist any ActivityValidGroup nodes after migration"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (av:ActivityValue)-[hg:HAS_GROUPING]-(ag:ActivityGrouping)
        WHERE NOT (ag)-[:HAS_SELECTED_GROUP]->(:ActivityGroupValue) OR NOT (ag)-[:HAS_SELECTED_SUBGROUP]->(:ActivitySubGroupValue)
        RETURN av
        """,
    )

    assert (
        len(records) == 0
    ), "ActivityGrouping must have both HAS_SELECTED_GROUP and HAS_SELECTED_SUBGROUP relationships"


@pytest.mark.order(after="test_migrate_activity_grouping")
def test_repeat_migrate_activity_grouping(migration):
    assert not migration_018.migrate_activity_grouping(DB_DRIVER, logger)
