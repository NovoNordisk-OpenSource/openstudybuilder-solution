"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import os

from data_corrections.utils.utils import get_db_driver, run_cypher_query
from migrations.utils.utils import get_logger

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()


def test_no_xml_entities_in_definitions():
    """Verify that no definitions contain the XML entities &#8729; or &#8722;."""
    LOGGER.info("Checking for remaining XML entities in node definitions")
    query = """
        MATCH (n)
        WHERE n.definition CONTAINS "&#8729;" OR n.definition CONTAINS "&#8722;"
        RETURN count(n) AS count
    """
    res, _ = run_cypher_query(DB_DRIVER, query)
    count = res[0]["count"]
    assert count == 0, f"Found {count} nodes with XML entities in definition"
