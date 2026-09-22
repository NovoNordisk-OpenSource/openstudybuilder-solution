"""Schema migrations needed for release 1.17 to PROD post August 2025."""

import json
import os

from migrations.common import migrate_ct_config_values, migrate_indexes_and_constraints
from migrations.utils.utils import (
    api_get,
    api_get_paged,
    api_post,
    get_db_connection,
    get_db_driver,
    get_logger,
    print_counters_table,
    run_cypher_query,
)

logger = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
DB_CONNECTION = get_db_connection()
MIGRATION_DESC = "schema-migration-release-1.17"


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])

    ### Common migrations
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_ct_config_values(DB_CONNECTION, logger)

    ### Release-specific migrations
    migrate_study_design_class(DB_DRIVER, logger)
    migrate_merge_branch_for_this_arm_for_sdtm_adam(DB_DRIVER, logger)


def migrate_study_design_class(_, log):
    contain_updates = []
    # get a list of studies
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
        study_number = study["current_metadata"]["identification_metadata"][
            "study_number"
        ]
        log.info(
            "Migrating StudyDesignClass node with Manual value in a (%s) Study",
            study_number,
        )
        study_design_class = api_get(
            f"/studies/{study_uid}/study-design-classes", check_ok_status=False
        ).json()

        if (
            not study_design_class
            or study_design_class.get("type") == "NotFoundException"
            and study["current_metadata"]["version_metadata"]["study_status"]
            != "LOCKED"
        ):
            created_study_design_class = api_post(
                f"/studies/{study_uid}/study-design-classes",
                payload={
                    "value": "Manual",
                },
            ).json()["value"]

            log.info(
                "Created StudyDesignClass node with Manual value in a (%s) Study",
                study_number,
            )
            contain_updates.append(created_study_design_class)
    return contain_updates


def migrate_merge_branch_for_this_arm_for_sdtm_adam(db_driver, log):
    log.info(
        "Migrating merge_branch_for_this_arm_for_sdtm_adam boolean property for all StudyArms",
    )
    _, merge_branch_for_this_arm_for_sdtm_adam = run_cypher_query(
        db_driver,
        """
        MATCH (study_arm:StudyArm)
        WHERE study_arm.merge_branch_for_this_arm_for_sdtm_adam IS NULL
        SET study_arm.merge_branch_for_this_arm_for_sdtm_adam=false
        """,
    )
    print_counters_table(merge_branch_for_this_arm_for_sdtm_adam.counters)
    return merge_branch_for_this_arm_for_sdtm_adam.counters.contains_updates


if __name__ == "__main__":
    main()
