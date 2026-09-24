"""PRD Data Corrections: Before Release 2.1"""

import os

from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import get_logger
from verifications import correction_verification_015

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-release-2.0"


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    change_visit_window_unit_from_weeks_to_days_study_000137(
        DB_DRIVER, LOGGER, run_label
    )


@capture_changes(
    verify_func=correction_verification_015.test_change_visit_window_unit_from_weeks_to_days_study_000137
)
def change_visit_window_unit_from_weeks_to_days_study_000137(db_driver, log, run_label):
    """
    ### Problem description
    Study_000137 has selected 'weeks' for the window unit for all visits in their Study.
    They would like to change it to 'days' instead but API doesn't allow to change window units after study visits are created.
    This data-correction changes the window unit from 'weeks' to 'days' for all StudyVisits in Study_000137.

    ### Change description
    - Update (:StudyVisit)-[:HAS_WINDOW_UNIT]->(:UnitDefinitionRoot) relationship to point to 'days' unit definition.

    ### Nodes and relationships affected
    - `StudyVisit` node
    - `HAS_WINDOW_UNIT` relationship

    ### Expected changes: 13 relationships removed and 13 relationships created.
    """
    log.info(
        f"Run: {run_label}, Changing weeks visit window unit to days for all StudyVisits in Study_000137"
    )
    query = """
    MATCH (days_root:UnitDefinitionRoot)-[:LATEST_FINAL]->(days_value:UnitDefinitionValue {name: 'days'})
    RETURN days_root.uid
    """
    results, _ = run_cypher_query(db_driver, query)
    if len(results) == 0:
        raise RuntimeError("UnitDefinition 'days' not found in the database.")
    days_unit_uid = results[0][0]

    query = """
        MATCH (sr:StudyRoot {uid:'Study_000137'})--(sv:StudyValue)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit)-[week_window_unit:HAS_WINDOW_UNIT]->(unit_root:UnitDefinitionRoot)
        WHERE unit_root.uid <> $days_unit_uid
        WITH DISTINCT study_visit, week_window_unit
        MATCH (days_unit:UnitDefinitionRoot {uid: $days_unit_uid})
        DELETE week_window_unit
        MERGE (study_visit)-[:HAS_WINDOW_UNIT]->(days_unit)
        """
    _, summary = run_cypher_query(
        db_driver,
        query,
        params={"days_unit_uid": days_unit_uid},
    )
    counters = summary.counters
    return counters.contains_updates


if __name__ == "__main__":
    main()
