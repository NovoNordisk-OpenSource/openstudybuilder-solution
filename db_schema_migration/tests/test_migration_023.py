import os

import pytest

from migrations import migration_023
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
    from tests.data.db_before_migration_023 import TEST_DATA
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
    migration_023.main()


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
    assert not migration_023.migrate_feature_flags(DB_DRIVER, logger)
