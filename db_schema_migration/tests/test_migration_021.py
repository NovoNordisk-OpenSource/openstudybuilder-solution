import os

import pytest

from migrations import migration_021
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
    from tests.data.db_before_migration_021 import TEST_DATA
except ImportError:
    TEST_DATA = ""


# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name

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
    migration_021.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_migrate_odm_nodes_and_relationships(migration):
    logger.info("Verify migrate_odm_nodes_and_relationships results")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n)
        WHERE
            any(label IN labels(n) WHERE (label STARTS WITH 'DeletedOdm' OR label STARTS WITH 'Odm') AND label ENDS WITH 'Root')
            AND n:ConceptRoot
        RETURN n;
        """,
    )

    assert (
        len(records) == 0
    ), "There must not exist any Odm* and DeletedOdm* nodes with ConceptRoot label after migration"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n)
        WHERE
            any(label IN labels(n) WHERE (label STARTS WITH 'DeletedOdm' OR label STARTS WITH 'Odm') AND label ENDS WITH 'Value')
            AND n:ConceptValue
        RETURN n;
        """,
    )

    assert (
        len(records) == 0
    ), "There must not exist any Odm* and DeletedOdm* nodes with ConceptValue label after migration"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n)
        WHERE
            any(label IN labels(n) WHERE (label STARTS WITH 'DeletedOdm' OR label STARTS WITH 'Odm') AND NOT label ENDS WITH 'Counter')
            AND NOT n:Odm
        RETURN n;
        """,
    )

    assert (
        len(records) == 0
    ), "There must not exist any Odm* and DeletedOdm* nodes without Odm label after migration"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n)
        WHERE
            any(label IN labels(n) WHERE (label STARTS WITH 'DeletedOdm' OR label STARTS WITH 'Odm') AND label ENDS WITH 'Root')
            AND Not n:OdmRoot
        RETURN n;
        """,
    )

    assert (
        len(records) == 0
    ), "There must not exist any Odm*Root and DeletedOdm*Root nodes without OdmRoot label after migration"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n)
        WHERE
            any(label IN labels(n) WHERE (label STARTS WITH 'DeletedOdm' OR label STARTS WITH 'Odm') AND label ENDS WITH 'Value')
            AND Not n:OdmValue
        RETURN n;
        """,
    )

    assert (
        len(records) == 0
    ), "There must not exist any Odm*Value and DeletedOdm*Value nodes without OdmValue label after migration"

    existing_odms, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE (label STARTS WITH 'DeletedOdm' OR label STARTS WITH 'Odm') AND label ENDS WITH 'Root')
        RETURN n;
        """,
    )
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n)<-[:CONTAINS_ODM]-(:Library)
        WHERE any(label IN labels(n) WHERE (label STARTS WITH 'DeletedOdm' OR label STARTS WITH 'Odm') AND label ENDS WITH 'Root')
        RETURN n;
        """,
    )

    assert (len(existing_odms) > 0 and len(records) > 0) or (
        len(existing_odms) == 0 and len(records) == 0
    ), "All Odm*Root and DeletedOdm*Root nodes must have `CONTAINS_ODM` relationship from Library after migration"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n)<-[:CONTAINS_CONCEPT]-(:Library)
        WHERE any(label IN labels(n) WHERE (label STARTS WITH 'DeletedOdm' OR label STARTS WITH 'Odm') AND label ENDS WITH 'Root')
        RETURN n;
        """,
    )

    assert (
        len(records) == 0
    ), "There must not exist any Odm*Root and DeletedOdm*Root nodes with `CONTAINS_CONCEPT` relationship from Library after migration"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE (label STARTS WITH 'DeletedOdm' OR label STARTS WITH 'Odm') AND label ENDS WITH 'Root')
        AND NOT (n)<-[:CONTAINS_ODM]-(:Library)
        RETURN n;
        """,
    )

    assert (
        len(records) == 0
    ), "There must not exist any Odm*Root and DeletedOdm*Root nodes without `CONTAINS_ODM` relationship from Library after migration"


@pytest.mark.order(after="test_migrate_odm_nodes_and_relationships")
def test_repeat_migrate_odm_nodes_and_relationships(migration):
    assert not migration_021.migrate_odm_nodes_and_relationships(DB_DRIVER, logger)
