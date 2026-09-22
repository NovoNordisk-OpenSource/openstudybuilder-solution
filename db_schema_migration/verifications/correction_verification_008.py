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


def test_delete_valid_for_epoch_type_relationship():
    LOGGER.info("Check for unwanted VALID_FOR_EPOCH_TYPE relationship")

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH ()-[r:VALID_FOR_EPOCH_TYPE]-()
        RETURN r
        """,
    )
    assert (
        len(records) == 0
    ), f"Found {len(records)} unwanted VALID_FOR_EPOCH_TYPE relationship."


def test_handle_multiple_activity_value_nodes_for_version():
    LOGGER.info("Check for multiple value nodes with the same version number")

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v2)<-[hv2:HAS_VERSION]-(r:ActivityRoot)-[hv1:HAS_VERSION]->(v1)
        WHERE v2 > v1 and hv1.version = hv2.version
        WITH DISTINCT r, v1, v2
        RETURN r
        """,
    )
    assert (
        len(records) == 0
    ), f"Found {len(records)} ActivityRoot nodes with multiple value nodes for the same version number"


def test_handle_multiple_activity_instance_value_nodes_for_version():
    LOGGER.info(
        "Check for multiple Activity Instance value nodes with the same version number"
    )

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (v2)<-[hv2:HAS_VERSION]-(r:ActivityInstanceRoot)-[hv1:HAS_VERSION]->(v1)
        WHERE v2 > v1 and hv1.version = hv2.version
        WITH DISTINCT r, v1, v2
        RETURN r
        """,
    )
    assert (
        len(records) == 0
    ), f"Found {len(records)} ActivityInstanceRoot nodes with multiple value nodes for the same version number"
