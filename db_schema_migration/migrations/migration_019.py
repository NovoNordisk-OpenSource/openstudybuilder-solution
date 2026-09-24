"""Schema migrations needed for release 2.5 to PROD"""

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
MIGRATION_DESC = "schema-migration-release-2.5"


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])
    ### Common migrations
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_ct_config_values(DB_CONNECTION, logger)

    ### Specific migrations
    remove_odm_data(DB_DRIVER, logger)
    migrate_codelist_ordinal(DB_DRIVER, logger)


def remove_odm_data(db_driver, log):
    """
    Cleanup the database by removing ODM data.
    This data is hard to migrate, and is not yet used.
    We remove it from the database for now, to be re-imported at a later time.
    """

    contains_updates = False
    for entity in [
        "OdmAlias",
        "OdmDescription",
        "OdmFormalExpression",
    ]:
        log.info(f"Cleaning up the database - Removing {entity} nodes")
        _, summary = run_cypher_query(
            db_driver,
            f"""
            MATCH (n:{entity})
            DETACH DELETE n
            """,
        )
        print_counters_table(summary.counters)
        contains_updates = contains_updates or summary.counters.contains_updates

    for entity in [
        "OdmTemplate",
        "OdmCondition",
        "OdmMethod",
        "OdmForm",
        "OdmItemGroup",
        "OdmItem",
        "OdmStudyEvent",
        "OdmVendorNamespace",
        "OdmVendorAttribute",
        "OdmVendorElement",
    ]:
        log.info(
            f"Cleaning up the database - Removing {entity}Root, {entity}Value and {entity}Counter nodes"
        )
        _, summary = run_cypher_query(
            db_driver,
            f"""
            OPTIONAL MATCH (r:{entity}Root)
            OPTIONAL MATCH (v:{entity}Value)
            OPTIONAL MATCH (c:{entity}Counter)
            DETACH DELETE r, v, c
            """,
        )
        print_counters_table(summary.counters)
        contains_updates = contains_updates or summary.counters.contains_updates

    log.info("Cleaning up the database - Removing DeletedOdm* nodes")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label STARTS WITH 'DeletedOdm')
        OPTIONAL MATCH (n)-[r]-(m)
        WHERE any(label IN labels(m) WHERE label STARTS WITH 'DeletedOdm')
        DETACH DELETE n, r, m;
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates

    return contains_updates


def migrate_codelist_ordinal(db_driver, log) -> bool:
    """
    Migrate the codelist ordinal property
    """

    log.info("Migrating codelist ordinal property")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (n:CTCodelistAttributesValue) WHERE n.ordinal IS NOT NULL
        SET n.is_ordinal = n.ordinal
        REMOVE n.ordinal
        RETURN count(n)
        """,
    )
    print_counters_table(summary.counters)
    return summary.counters.contains_updates


if __name__ == "__main__":
    main()
