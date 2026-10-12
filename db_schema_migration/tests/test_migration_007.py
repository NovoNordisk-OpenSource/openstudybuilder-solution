import os

import pytest

from migrations import migration_007
from migrations.utils.utils import (  # api_get,; api_get_paged,; api_patch,; run_cypher_query,
    execute_statements,
    get_db_connection,
    get_db_driver,
    get_logger,
)
from tests import common

try:
    from tests.data.db_before_migration_007 import TEST_DATA
except ImportError:
    TEST_DATA = ""
from tests.utils.utils import clear_db

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
    migration_007.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)
