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


def test_change_visit_window_unit_from_weeks_to_days_study_000137():
    LOGGER.info(
        "Checking if all study visits in Study_000137 selected 'days' as visit window unit"
    )
    query = """
        MATCH (sr:StudyRoot{uid:"Study_000137"})--(sv:StudyValue)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit)-[:HAS_WINDOW_UNIT]->(:UnitDefinitionRoot)-[:LATEST_FINAL]->(unit_value:UnitDefinitionValue)
        WHERE unit_value.name <> 'days'
        RETURN study_visit.uid AS study_visit_uid
    """
    res, _ = run_cypher_query(DB_DRIVER, query)
    assert (
        len(res) == 0
    ), f"Found study visits in Study_000137 that do not have 'days' as visit window unit, res:{res}"
