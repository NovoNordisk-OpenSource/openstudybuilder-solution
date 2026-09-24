"""Schema migrations needed to release 2.9 in PROD"""

import os

from migrations.common import migrate_ct_config_values, migrate_indexes_and_constraints
from migrations.utils.utils import (
    SchemaMigrationNode,
    get_db_connection,
    get_db_driver,
    get_logger,
    print_counters_table,
    run_cypher_query,
)

logger = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
DB_CONNECTION = get_db_connection()
MIGRATION_DESC = "schema-migration-release-2.9"


def migrate_feature_flags(db_driver, log) -> bool:
    """
    Add 2 new fields to FeatureFlag node: section and feature.
    """
    log.info(
        "Adding new fields section and feature with dummy values to `FeatureFlag` nodes"
    )
    _, summary1 = run_cypher_query(
        db_driver,
        """
        MATCH (ff:FeatureFlag) WHERE ff.section IS NULL
        SET ff.section = 'admin'
        """,
    )
    print_counters_table(summary1.counters)

    _, summary2 = run_cypher_query(
        db_driver,
        """
        MATCH (ff:FeatureFlag) WHERE ff.feature IS NULL
        SET ff.feature = 'FIXME'
        """,
    )
    print_counters_table(summary2.counters)
    return summary1.counters.contains_updates or summary2.counters.contains_updates


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])

    with SchemaMigrationNode(filename=__file__, driver=DB_DRIVER):
        ### Common migrations
        migrate_indexes_and_constraints(DB_CONNECTION, logger)
        migrate_ct_config_values(DB_CONNECTION, logger)
        ### FeatureFlag migration
        migrate_feature_flags(DB_DRIVER, logger)


if __name__ == "__main__":
    main()
