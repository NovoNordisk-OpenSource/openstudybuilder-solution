"""Schema migrations needed for release 2.4 to PROD"""

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
MIGRATION_DESC = "schema-migration-release-2.4"


def migrate_activity_grouping(db_driver, log) -> bool:
    """
    Migrate the activities and subgroups to the new grouping model
    """

    log.info("Migrating activities to the new grouping model")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (av:ActivityValue)-[hg:HAS_GROUPING]-(ag:ActivityGrouping)-[isg:IN_SUBGROUP]->(avg:ActivityValidGroup)
        MATCH (avg)<-[:HAS_GROUP]-(sgv:ActivitySubGroupValue)
        MATCH (avg)-[:IN_GROUP]->(gv:ActivityGroupValue)
        MERGE (ag)-[:HAS_SELECTED_GROUP]->(gv)
        MERGE (ag)-[:HAS_SELECTED_SUBGROUP]->(sgv)
        DETACH DELETE avg
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = summary.counters.contains_updates

    log.info("Migrating remaining (unused) subgroups to the new grouping model")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (gv:ActivityGroupValue)<-[:IN_GROUP]-(avg:ActivityValidGroup)<-[:HAS_GROUP]-(sgv:ActivitySubGroupValue)
        DETACH DELETE avg
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates

    log.info("Removing ActivityValidGroup counter node")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (c:ActivityValidGroupCounter)
        DETACH DELETE c
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates
    return contains_updates


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])

    ### Common migrations
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_ct_config_values(DB_CONNECTION, logger)
    ### Specific migrations
    migrate_activity_grouping(DB_DRIVER, logger)


if __name__ == "__main__":
    main()
