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


def test_remove_duplicated_activity_instance_class_rels():
    """
    This test checks for duplicated relationships between ActivityInstanceValue and ActivityClassRoot nodes.
    """

    # Count duplicated relationships
    rs, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (av:ActivityInstanceValue)-[raic:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)
        WITH av, aicr, collect(raic) as rels
        WHERE size(rels) > 1
        RETURN count(DISTINCT av) as node_count
        """,
    )

    assert not rs[0][
        0
    ], f"Found {rs[0][0]} duplicated ACTIVITY_INSTANCE_CLASS relationships."


def test_instances_lacking_activity():
    """
    This test checks ActivityInstanceValue and ActivityClassRoot nodes.
    """

    # Count instances missing an activity
    rs, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (ar:ActivityInstanceRoot)--(av:ActivityInstanceValue) WHERE NOT (av)-[:HAS_ACTIVITY]->(:ActivityGrouping)
        RETURN count(DISTINCT av) as node_count
        """,
    )

    assert not rs[0][0], f"Found {rs[0][0]} activity instances missing an activity."
