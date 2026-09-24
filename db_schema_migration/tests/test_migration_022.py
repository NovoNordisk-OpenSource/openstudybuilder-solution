import os

import pytest

from migrations import migration_022
from migrations.utils.utils import (
    execute_statements,
    get_db_connection,
    get_db_driver,
    get_logger,
    run_cypher_query,
)
from tests import common
from tests.utils.utils import clear_db

try:
    from tests.data.db_before_migration_022 import TEST_DATA
except ImportError:
    TEST_DATA = ""


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
    migration_022.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_migrate_featureflag_nodes(migration):
    logger.info("Verify migrate_feature_flags results")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n:FeatureFlag) WHERE n.section IS NULL
        RETURN count(n) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), "All FeatureFlag nodes must have a section property after migration"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n:FeatureFlag) WHERE n.feature IS NULL
        RETURN count(n) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), "All FeatureFlag nodes must have a feature property after migration"


@pytest.mark.order(after="test_migrate_featureflag_nodes")
def test_repeat_migrate_featureflag_nodes(migration):
    assert not migration_022.migrate_feature_flags(DB_DRIVER, logger)


def test_migrate_instance_split(migration):
    logger.info("Verify instance split migration results")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (air:ActivityInstanceRoot)-[rel]->(aiv:ActivityInstanceValue)-[:HAS_ACTIVITY]->(:ActivityGrouping)
        RETURN count(DISTINCT aiv) AS unmigrated_count
        """,
    )

    assert (
        records[0]["unmigrated_count"] == 0
    ), "There are still ActivityInstanceValue nodes linked to ActivityGrouping nodes after migration"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (air:ActivityInstanceRoot)
        WHERE NOT (air)-[:HAS_GROUPING_ROOT]-(:ActivityInstanceGroupingRoot)
        RETURN count(DISTINCT air) AS unmigrated_count
        """,
    )
    assert (
        records[0]["unmigrated_count"] == 0
    ), "There are still ActivityInstanceRoot nodes not linked to an ActivityInstanceGroupingRoot node after migration"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (gr:ActivityInstanceGroupingRoot)
        WHERE NOT (gr)-[:HAS_VERSION]->(:ActivityInstanceGroupingValue)
        OR NOT (gr)-[:LATEST]->(:ActivityInstanceGroupingValue)
        RETURN count(DISTINCT gr) AS unmigrated_count
        """,
    )
    assert (
        records[0]["unmigrated_count"] == 0
    ), "There are ActivityInstanceGroupingRoot nodes not linked to a ActivityInstanceGroupingValue node with HAS_VERSION and LATEST relationships after migration"


@pytest.mark.order(after="test_migrate_instance_split")
def test_repeat_migrate_instance_split(migration):
    assert not migration_022.migrate_instance_split(DB_DRIVER, logger)
