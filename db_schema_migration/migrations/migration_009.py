"""Schema migrations needed for release 1.8 to PROD post August 2024."""

import os

from migrations.common import migrate_ct_config_values, migrate_indexes_and_constraints
from migrations.utils.utils import (
    get_db_connection,
    get_db_driver,
    get_logger,
    print_counters_table,
    run_cypher_query,
)

logger = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
DB_CONNECTION = get_db_connection()
MIGRATION_DESC = "schema-migration-release-1.9"


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])

    ### Common migrations
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_ct_config_values(DB_CONNECTION, logger)

    ### Release-specific migrations
    migrate_study_selection_metadata_into_study_selection(DB_DRIVER, logger)


def migrate_study_selection_metadata_into_study_selection(db_driver, log):
    log.info(
        "Refactoring :StudySelectionMetadata to :StudySelection and linking these nodes to :StudyValue"
    )
    _, soa_group_summary = run_cypher_query(
        db_driver,
        """
        MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
        SET study_soa_group:StudySelection
        REMOVE study_soa_group:StudySelectionMetadata
        WITH study_activity, study_soa_group
        MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(study_activity)
        MERGE (study_value)-[:HAS_STUDY_SOA_GROUP]->(study_soa_group)
        """,
    )

    soa_group_counters = soa_group_summary.counters
    print_counters_table(soa_group_counters)

    _, activity_group_summary = run_cypher_query(
        db_driver,
        """
        MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
        SET study_activity_group:StudySelection
        REMOVE study_activity_group:StudySelectionMetadata
        WITH study_activity, study_activity_group
        MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(study_activity)
        MERGE (study_value)-[:HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group)
        """,
    )

    activity_group_counters = activity_group_summary.counters
    print_counters_table(activity_group_counters)

    _, activity_subgroup_summary = run_cypher_query(
        db_driver,
        """
        MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
        SET study_activity_subgroup:StudySelection
        REMOVE study_activity_subgroup:StudySelectionMetadata
        WITH study_activity, study_activity_subgroup
        MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(study_activity)
        MERGE (study_value)-[:HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup)
        """,
    )

    activity_subgroup_counters = activity_subgroup_summary.counters
    print_counters_table(activity_subgroup_counters)

    _, study_selection_metadata_summary = run_cypher_query(
        db_driver,
        """
        MATCH (study_selection_metadata:StudySelectionMetadata)
        SET study_selection_metadata:StudySelection
        REMOVE study_selection_metadata:StudySelectionMetadata
        """,
    )

    study_selection_metadata_counters = study_selection_metadata_summary.counters
    print_counters_table(study_selection_metadata_counters)
    return (
        soa_group_counters.contains_updates
        or activity_group_counters.contains_updates
        or activity_subgroup_counters.contains_updates
        or study_selection_metadata_counters.contains_updates
    )


if __name__ == "__main__":
    main()
