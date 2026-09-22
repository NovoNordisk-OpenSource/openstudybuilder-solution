"""PRD Data Corrections: Before Release 2.7"""

import os

from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    print_counters_table,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import get_logger
from verifications import correction_verification_018

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-release-2.7"


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    fix_duplicated_study_visits_from_study_cloning(DB_DRIVER, LOGGER, run_label)


@capture_changes(
    verify_func=correction_verification_018.test_fix_duplicated_study_visits_from_study_cloning
)
def fix_duplicated_study_visits_from_study_cloning(db_driver, log, run_label):
    """
    ### Problem description
    Due to a bug in the Study cloning functionality, some StudyVisit nodes are linked to
    multiple StudyEpoch nodes via the STUDY_EPOCH_HAS_STUDY_VISIT relationship. This causes
    the study-visits API endpoint to return duplicate entries for the affected StudyVisit.
    ### Change description
    - Detect StudyVisit duplications by checking if any study visit uid appears more than once
      in the response of the /studies/{study_uid}/study-visits API endpoint.
    - For each duplicated StudyVisit, remove the STUDY_EPOCH_HAS_STUDY_VISIT relationship to
      the StudyEpoch that belongs to a StudyValue which also has HAS_PROTOCOL_SOA_CELL relationships.
    ### Nodes and relationships affected
    - `STUDY_EPOCH_HAS_STUDY_VISIT` relationships
    ### Expected changes: 3 `STUDY_EPOCH_HAS_STUDY_VISIT` relationships removed
    """
    # Hardcoded duplications caused by the Study cloning bug.
    # Each entry: (study_uid, visit_uid, epoch_term_to_keep)
    # The relationship to the StudyEpoch whose CTTerm name does NOT match
    # epoch_term_to_keep will be removed.
    duplicated_visits = [
        ("Study_000203", "StudyVisit_010141", "Basic"),
        ("Study_000203", "StudyVisit_010143", "Basic"),
        ("Study_000224", "StudyVisit_011099", "Treatment"),
    ]

    contains_updates = []

    for study_uid, visit_uid, epoch_term_to_keep in duplicated_visits:
        log.info(
            f"Run: {run_label}, Removing wrong STUDY_EPOCH_HAS_STUDY_VISIT for "
            f"StudyVisit {visit_uid} in Study {study_uid}, "
            f"keeping epoch related to CTTerm '{epoch_term_to_keep}'"
        )
        query = """
            MATCH (study_epoch:StudyEpoch)-[bad_rel:STUDY_EPOCH_HAS_STUDY_VISIT]
                ->(study_visit:StudyVisit {uid: $visit_uid})
            WHERE NOT (study_epoch)-[:HAS_EPOCH]->(:CTTermContext)
                -[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)
                -[:LATEST]->(:CTTermNameValue {name: $epoch_term_to_keep})
            DELETE bad_rel
        """
        _, summary = run_cypher_query(
            db_driver,
            query,
            params={
                "visit_uid": visit_uid,
                "epoch_term_to_keep": epoch_term_to_keep,
            },
        )
        counters = summary.counters
        print_counters_table(counters)
        contains_updates.append(counters.contains_updates)

    return any(contains_updates)


if __name__ == "__main__":
    main()
