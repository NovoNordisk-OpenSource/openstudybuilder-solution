"""PRD Data Corrections: Single Study Wipe"""

import argparse
import os

from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import get_logger

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-single-study-wipe"


def main(study_number, study_uid):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title("correction", __doc__, desc)

    delete_unwanted_study(DB_DRIVER, LOGGER, "correction", study_number, study_uid)


@capture_changes()
def delete_unwanted_study(db_driver, log, run_label, study_number, study_uid):
    """
    ## Delete one complete study

    ### Problem description
    Sometimes studies are created by mistake in the production environment.
    These occupy some Study IDs and cause confusion.
    This script deletes all nodes and relationships related to a specific study.

    ### Change description
    Delete all nodes and relationships related to the study identified by the given study number and study UID.
    If the study number and study UID do not match, no deletion will occur.

    ### Nodes and relationships affected
    - All study nodes for the study identified by the given study number and study UID.
    """
    desc = (
        f"Deleting study number {study_number} with uid {study_uid} from the database"
    )
    log.info(f"Run: {run_label}, {desc}")

    # This query deletes a complete study from the database
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (sr:StudyRoot {uid: $study_uid})-[hsv]-(sv:StudyValue)
        WHERE (sr)-[:LATEST]->(:StudyValue {study_number: $study_number})
        CALL {
            WITH sr
            MATCH (sr)-[at:AUDIT_TRAIL]->(sa:StudyAction)
            MATCH (sa)-[before_after_sel:BEFORE|AFTER]->(ss:StudySelection)
            DETACH DELETE ss, sa
        } IN TRANSACTIONS
        CALL {
            WITH sv
            MATCH (sv)-[hsf]->(sf:StudyField)
            DETACH DELETE sf
        } IN TRANSACTIONS
        CALL {
            WITH sv
            MATCH (sv)-[hss]->(ss2:StudySelection)
            DETACH DELETE ss2
        } IN TRANSACTIONS
        DETACH DELETE sr, sv
        """,
        {"study_number": study_number, "study_uid": study_uid},
    )
    counters = summary.counters
    return counters.contains_updates


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Data correction script to delete one complete study from the database.
        Requires both study number and study UID in order to ensure the correct study is deleted.
        """
    )
    parser.add_argument(
        "--study-number",
        type=str,
        required=True,
        help="The study number of the study to be deleted",
    )
    parser.add_argument(
        "--study-uid",
        type=str,
        required=True,
        help="The study UID of the study to be deleted",
    )
    args = parser.parse_args()
    main(study_number=args.study_number, study_uid=args.study_uid)
