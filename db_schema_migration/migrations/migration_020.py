"""Schema migrations needed for release 2.6 to PROD"""

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
MIGRATION_DESC = "schema-migration-release-2.6"


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])
    ### Common migrations
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_ct_config_values(DB_CONNECTION, logger)

    ### Specific migrations
    add_codelist_type(DB_DRIVER, logger)
    migrate_sponsor_model_ordinal(DB_DRIVER, logger)


def add_codelist_type(db_driver, log) -> bool:
    """
    Add the codelist_type property to CTCodelistAttributesValue nodes.
    By default, the value is set to "Standard".
    """

    log.info("Adding codelist_type property to CTCodelistAttributesValue nodes")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (n:CTCodelistAttributesValue) WHERE n.codelist_type IS NULL 
        WITH n, 
        CASE WHEN toLower(n.name) CONTAINS "response"
        THEN "Response"
        ELSE "Standard"
        END AS codelist_type
        SET n.codelist_type = codelist_type
        """,
    )
    print_counters_table(summary.counters)
    return summary.counters.contains_updates


def migrate_sponsor_model_ordinal(db_driver, log) -> bool:
    """
    Convert the ordinal property on Sponsor Model relationships from string to integer.
    Affects the HAS_DATASET relationship (SponsorModelValue -> SponsorModelDatasetInstance)
    and the HAS_DATASET_VARIABLE relationship
    (SponsorModelDatasetInstance -> SponsorModelDatasetVariableInstance).
    """

    log.info("Migrating Sponsor Model ordinal property from string to integer")

    contains_updates = False

    log.info("Migrating ordinal on HAS_DATASET relationships")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (n:SponsorModelDatasetInstance)<-[rel:HAS_DATASET]-(:SponsorModelValue)
        WHERE rel.ordinal IS NOT NULL AND rel.ordinal <> toInteger(rel.ordinal)
        SET rel.ordinal=toInteger(rel.ordinal)
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates

    log.info("Migrating ordinal on HAS_DATASET_VARIABLE relationships")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (n:SponsorModelDatasetInstance)-[rel:HAS_DATASET_VARIABLE]->(:SponsorModelDatasetVariableInstance)
        WHERE rel.ordinal IS NOT NULL AND rel.ordinal <> toInteger(rel.ordinal)
        SET rel.ordinal=toInteger(rel.ordinal)
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates

    return contains_updates


if __name__ == "__main__":
    main()
