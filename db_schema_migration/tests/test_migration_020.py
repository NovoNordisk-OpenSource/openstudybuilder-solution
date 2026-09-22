import os

import pytest

from migrations import migration_020
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
    from tests.data.db_before_migration_020 import TEST_DATA
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
    migration_020.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_add_codelist_type(migration):
    logger.info("Verify codelist_type property addition results")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n:CTCodelistAttributesValue) WHERE n.codelist_type IS NULL
        RETURN count(n) AS count
        """,
    )

    assert (
        records[0]["count"] == 0
    ), "All CTCodelistAttributesValue nodes must have a codelist_type property after migration"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n:CTCodelistAttributesValue) WHERE n.codelist_type = "Standard"
        RETURN count(n) AS count
        """,
    )

    assert (
        records[0]["count"] > 0
    ), "At least one CTCodelistAttributesValue must have codelist_type = 'Standard' after migration"


@pytest.mark.order(after="test_add_codelist_type")
def test_repeat_add_codelist_type(migration):
    assert not migration_020.add_codelist_type(DB_DRIVER, logger)


def test_migrate_sponsor_model_ordinal(migration):
    logger.info("Verify Sponsor Model ordinal migration results")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (:SponsorModelValue)-[r:HAS_DATASET]->(:SponsorModelDatasetInstance)
        WHERE r.ordinal IS NOT NULL AND r.ordinal <> toInteger(r.ordinal)
        RETURN count(r) AS count
        """,
    )

    assert (
        records[0]["count"] == 0
    ), "All HAS_DATASET ordinal values must be integers after migration"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (:SponsorModelDatasetInstance)-[r:HAS_DATASET_VARIABLE]->(:SponsorModelDatasetVariableInstance)
        WHERE r.ordinal IS NOT NULL AND r.ordinal <> toInteger(r.ordinal)
        RETURN count(r) AS count
        """,
    )

    assert (
        records[0]["count"] == 0
    ), "All HAS_DATASET_VARIABLE ordinal values must be integers after migration"


@pytest.mark.order(after="test_migrate_sponsor_model_ordinal")
def test_repeat_migrate_sponsor_model_ordinal(migration):
    assert not migration_020.migrate_sponsor_model_ordinal(DB_DRIVER, logger)
