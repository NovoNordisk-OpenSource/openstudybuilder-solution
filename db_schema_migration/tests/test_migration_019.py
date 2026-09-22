import os

import pytest

from migrations import migration_019
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
    from tests.data.db_before_migration_019 import TEST_DATA
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
    migration_019.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_remove_odm_data(migration):
    logger.info("Verify odm data removal migration results")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label STARTS WITH 'DeletedOdm' OR label STARTS WITH 'Odm')
        RETURN n;
        """,
    )

    assert (
        len(records) == 0
    ), "There must not exist any Odm* and DeletedOdm* nodes after migration"


@pytest.mark.order(after="test_remove_odm_data")
def test_repeat_remove_odm_data(migration):
    assert not migration_019.remove_odm_data(DB_DRIVER, logger)


def test_migrate_codelist_ordinal(migration):
    logger.info("Verify codelist ordinal migration results")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n:CTCodelistAttributesValue) WHERE n.ordinal IS NOT NULL
        RETURN count(n) AS count
        """,
    )

    assert (
        records[0]["count"] == 0
    ), "There must not exist a CTCodelistAttributesValue with ordinal property after migration"


@pytest.mark.order(after="test_migrate_codelist_ordinal")
def test_repeat_migrate_codelist_ordinal(migration):
    assert not migration_019.migrate_codelist_ordinal(DB_DRIVER, logger)
