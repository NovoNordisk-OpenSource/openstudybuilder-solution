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


def test_remove_duplicate_activity_instance_classes():
    activity_instance_class_nodes_to_remove = [
        "TextualFindings",
        "NumericFindings",
        "GeneralObservation",
        "CategoricFindings",
    ]

    for name in activity_instance_class_nodes_to_remove:
        nodes, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (r:ActivityInstanceClassRoot)--(v:ActivityInstanceClassValue)
            WHERE v.name = $name
            RETURN COUNT(DISTINCT r)
            """,
            {"name": name},
        )
        assert (
            nodes[0][0] == 1
        ), f"Expected one node with name '{name}', found {nodes[0][0]}"
