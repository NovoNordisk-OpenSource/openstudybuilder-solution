import json
import os

import pytest

from migrations import migration_015
from migrations.utils.utils import (
    api_get,
    api_get_paged,
    execute_statements,
    get_db_connection,
    get_db_driver,
    get_logger,
    run_cypher_query,
)
from tests import common
from tests.data.db_before_migration_015 import TEST_DATA
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
    migration_015.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_migrate_study_design_class(migration):
    logger.info(
        "Check if StudyDesignClass is migrated with Manual value for existing Studies"
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
        if study["current_metadata"]["version_metadata"]["study_status"] == "LOCKED":
            continue
        study_uid = study["uid"]
        records, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (study_root:StudyRoot {uid:$study_uid})-[:LATEST]->(study_value:StudyValue)-[:HAS_STUDY_DESIGN_CLASS]->(study_design_class:StudyDesignClass)
            RETURN study_design_class
            """,
            params={"study_uid": study_uid},
        )
        assert (
            len(records) != 0
        ), f"There must exist a StudyDesignClass node in {study_uid} Study"

        study_design_class = api_get(f"/studies/{study_uid}/study-design-classes")
        assert (
            study_design_class is not None
        ), f"There must exist a StudyDesignClass node in {study_uid} Study"


@pytest.mark.order(after="test_migrate_study_design_class")
def test_repeat_migrate_study_design_class(migration):
    assert not migration_015.migrate_study_design_class(DB_DRIVER, logger)


def test_migrate_merge_branch_for_this_arm_for_sdtm_adam(migration):
    logger.info(
        "Verify merge_branch_for_this_arm_for_sdtm_adam boolean property migration for all StudyArms"
    )
    payload = api_get_paged(
        "/study-arms",
        page_size=50,
    )
    study_arms = payload["items"]
    for study_arm in study_arms:
        assert (
            study_arm["merge_branch_for_this_arm_for_sdtm_adam"] is not None
        ), "The merge_branch_for_this_arm_for_sdtm_adam property must exists for StudyArm"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_arm:StudyArm)
        WHERE study_arm.merge_branch_for_this_arm_for_sdtm_adam IS NULL
        RETURN study_arm.uid
        """,
    )

    assert (
        len(records) == 0
    ), "There must exist merge_branch_for_this_arm_for_sdtm_adam property for each StudyArm"


@pytest.mark.order(after="test_migrate_merge_branch_for_this_arm_for_sdtm_adam")
def test_repeat_migrate_merge_branch_for_this_arm_for_sdtm_adam(migration):
    assert not migration_015.migrate_merge_branch_for_this_arm_for_sdtm_adam(
        DB_DRIVER, logger
    )
