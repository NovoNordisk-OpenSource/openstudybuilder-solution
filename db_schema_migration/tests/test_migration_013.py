import json
import os

import pytest

from migrations import migration_013
from migrations.utils.utils import (
    api_get_paged,
    execute_statements,
    get_db_connection,
    get_db_driver,
    get_logger,
    run_cypher_query,
)
from tests import common
from tests.data.db_before_migration_013 import TEST_DATA
from tests.utils.utils import clear_db

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=protected-access
# pylint: disable=broad-except

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

db = get_db_connection()
DB_DRIVER = get_db_driver()
logger = get_logger(os.path.basename(__file__))


@pytest.fixture(scope="module")
def initial_data():
    """Insert test data"""
    clear_db()
    execute_statements(TEST_DATA)


@pytest.fixture(scope="module")
def migration(initial_data):
    # Run migration
    migration_013.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_migrate_visit_group_into_node(migration):
    logger.info(
        "Check if StudyVisit groups are represented as standalone StudyVisitGroup node"
    )
    payload = api_get_paged(
        "/studies",
        page_size=50,
        params={
            "sort_by": json.dumps({"uid": True}),
        },
    )
    studies = payload["items"]
    for study in studies:
        study_uid = study["uid"]
        records, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (study_root:StudyRoot {uid:$study_uid})--(study_value:StudyValue)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit)
            WHERE study_visit.consecutive_visit_group IS NOT NULL AND NOT (study_visit)-[:BEFORE]-() and NOT (study_visit)-[]-(:Delete)
            RETURN study_visit
            """,
            params={"study_uid": study_uid},
        )
        assert (
            len(records) == 0
        ), "There shouldn't exist any current StudyVisit having old consecutive_visit_group property"
        study_visits = api_get_paged(
            f"/studies/{study_uid}/study-visits", page_size=20
        )["items"]
        for study_visit in study_visits:
            if (
                consecutive_visit_group := study_visit["consecutive_visit_group"]
            ) is not None:
                study_visit_uid = study_visit["uid"]
                records, _ = run_cypher_query(
                    DB_DRIVER,
                    """
                    MATCH (study_root:StudyRoot {uid:$study_uid})--(study_value:StudyValue)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit {uid:$study_visit_uid})
                    WHERE (study_visit)-[:IN_VISIT_GROUP]->(:StudyVisitGroup) AND NOT (study_visit)-[:BEFORE]-() and NOT (study_visit)-[]-(:Delete)
                    RETURN study_visit
                    """,
                    params={"study_uid": study_uid, "study_visit_uid": study_visit_uid},
                )
                assert (
                    len(records) != 0
                ), f"StudyVisit {study_visit_uid} should be linked to {consecutive_visit_group} StudyVisitGroup node"


@pytest.mark.order(after="test_migrate_visit_group_into_node")
def test_repeat_migrate_visit_group_into_node(migration):
    assert not migration_013.migrate_visit_group_into_node(DB_DRIVER, logger)
