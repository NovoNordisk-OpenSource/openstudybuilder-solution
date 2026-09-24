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

UNUSED_DASHBOARD_UUID = "6b288611-7f89-482c-a850-b34b19cf6ebb"
UNUSED_DASHBOARD_TITLE = "External Data File Specifications"
UNUSED_DASHBOARD_USER = "devops_adm"
UNUSED_DASHBOARD_DATE = "2025-10-05 13:20:42 +0000"


def test_unused_neodash_dashboard_removed():
    """Verify the unused Neodash dashboard row is no longer present."""
    LOGGER.info(
        "Checking that unused External Data File Specifications dashboard is removed"
    )
    query = """
        MATCH (d:_Neodash_Dashboard)
        WHERE d.uuid = $uuid
          AND d.title = $title
          AND d.user = $user
          AND d.date = $date
        RETURN count(d) AS count
    """
    res, _ = run_cypher_query(
        DB_DRIVER,
        query,
        params={
            "uuid": UNUSED_DASHBOARD_UUID,
            "title": UNUSED_DASHBOARD_TITLE,
            "user": UNUSED_DASHBOARD_USER,
            "date": UNUSED_DASHBOARD_DATE,
        },
    )
    count = res[0]["count"]
    assert (
        count == 0
    ), f"Found {count} matching Neodash dashboard node(s); expected removal"
