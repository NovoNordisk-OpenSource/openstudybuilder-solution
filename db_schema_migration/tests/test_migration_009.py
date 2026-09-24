import os

import pytest

from migrations import migration_009
from migrations.utils.utils import (
    api_get_paged,
    execute_statements,
    get_db_connection,
    get_db_driver,
    get_logger,
    run_cypher_query,
)
from tests import common
from tests.data.db_before_migration_009 import TEST_DATA
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
    migration_009.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_migrate_study_selection_metadata_into_study_selection(migration):
    logger.info("Check StudySelectionMetadata migration into StudySelection")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_selection_metadata:StudySelectionMetadata)
        RETURN study_selection_metadata
        """,
    )
    assert len(records) == 0, "There shouldn't exist any StudySelectionMetadata nodes"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_value:StudyValue)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)
        WITH study_value, study_activity,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup) | study_soa_group]) AS study_soa_group,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup) | study_activity_group]) AS study_activity_group,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup) | study_activity_subgroup]) AS study_activity_subgroup
        WHERE head([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(:ActivityValue)<-[:HAS_VERSION]-(:ActivityRoot)<-[:CONTAINS_CONCEPT]-(library) | library.name]) <> 'Requested'
            AND (NOT (study_value)-[:HAS_STUDY_SOA_GROUP]->(study_soa_group)
            OR NOT (study_value)-[:HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group)
            OR NOT (study_value)-[:HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup))
        RETURN *
        """,
    )
    assert (
        len(records) == 0
    ), "If StudyActivity node is linked to StudyValue, corresponding StudySoAGroup/StudyActivityGroup/StudyActivitySubGroup node should be also linked to StudyValue"

    studies, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_root:StudyRoot) return study_root.uid
        """,
    )
    for study in studies:
        study_uid = study[0]
        logger.info(
            "Verifying that StudyActivities are being returned without any issues in the following Study (%s)",
            study_uid,
        )
        # Call endpoint to check API response which is asserted under the hood
        api_get_paged(f"/studies/{study_uid}/study-activities", page_size=10)


@pytest.mark.order(after="test_migrate_study_selection_metadata_into_study_selection")
def test_repeat_migrate_study_selection_metadata_into_study_selection(migration):
    assert not migration_009.migrate_study_selection_metadata_into_study_selection(
        DB_DRIVER, logger
    )
