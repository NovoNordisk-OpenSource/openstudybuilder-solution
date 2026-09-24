"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import os

from data_corrections.utils.utils import get_db_driver, run_cypher_query
from migrations.utils.utils import api_get_paged, get_logger

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()


def test_fix_duplicated_study_visits_from_study_cloning():

    duplicated_visits = [
        {"study_uid": "Study_000203", "study_visit_uid": "StudyVisit_010141"},
        {"study_uid": "Study_000203", "study_visit_uid": "StudyVisit_010143"},
        {"study_uid": "Study_000224", "study_visit_uid": "StudyVisit_011099"},
    ]
    duplicated_visit_uids = [entry["study_visit_uid"] for entry in duplicated_visits]
    LOGGER.info(
        "Checking for StudyVisit '%s' nodes linked to multiple StudyEpoch nodes",
        duplicated_visit_uids,
    )
    query = """
        MATCH (study_visit:StudyVisit)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(study_epoch:StudyEpoch)
        WHERE study_visit.uid IN $visit_uids AND NOT (study_visit)-[:BEFORE]-()
        WITH study_visit, collect(distinct study_epoch.uid) AS epoch_uids
        WHERE size(epoch_uids) > 1
        RETURN study_visit.uid, epoch_uids
    """

    res, _ = run_cypher_query(
        DB_DRIVER, query, params={"visit_uids": duplicated_visit_uids}
    )
    assert (
        len(res) == 0
    ), f"Found StudyVisit nodes still linked to multiple StudyEpochs: {res}"

    LOGGER.info(
        "Verifying that no study visit uid is duplicated in the study-visits API response",
    )

    duplicated_study_uids = [entry["study_uid"] for entry in duplicated_visits]
    study_results, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_root:StudyRoot)-[:LATEST]->(study_value:StudyValue)
        WHERE study_root.uid IN $study_uids AND NOT (study_value)<-[:BEFORE]-(:Delete)
        RETURN study_root.uid
        """,
        params={"study_uids": duplicated_study_uids},
    )
    for result in study_results:
        study_uid = result[0]
        study_visits_response = api_get_paged(f"/studies/{study_uid}/study-visits")
        uids = [visit["uid"] for visit in study_visits_response["items"]]
        duplicated = [uid for uid in uids if uids.count(uid) > 1]
        assert len(duplicated) == 0, (
            f"Study {study_uid} still has duplicated StudyVisit uids in the API response: "
            f"{list(set(duplicated))}"
        )
