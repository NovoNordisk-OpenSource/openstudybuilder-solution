"""Schema migrations needed for release 2.7 to PROD"""

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
MIGRATION_DESC = "schema-migration-release-2.7"


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])
    ### Common migrations
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_ct_config_values(DB_CONNECTION, logger)

    ### Specific migrations
    migrate_odm_nodes_and_relationships(DB_DRIVER, logger)


def migrate_odm_nodes_and_relationships(db_driver, log) -> bool:
    """
    - Replace `ConceptRoot`/`ConceptValue` labels with `OdmRoot`/`OdmValue` for all ODM nodes
    - Add new `Odm` label for all ODM nodes
    - Replace relationship `CONTAINS_CONCEPT` from `Library` to `Odm*Root` with `CONTAINS_ODM`
    """

    contains_updates = False
    log.info("Replacing `ConceptRoot` labels with `OdmRoot` for all ODM nodes")

    all_odm_nodes = [
        "OdmAlias",
        "OdmTranslatedText",
        "OdmFormalExpression",
        "OdmConditionValue",
        "OdmConditionRoot",
        "DeletedOdmConditionRoot",
        "OdmMethodValue",
        "OdmMethodRoot",
        "DeletedOdmMethodRoot",
        "OdmFormValue",
        "OdmFormRoot",
        "DeletedOdmFormRoot",
        "OdmItemGroupValue",
        "OdmItemGroupRoot",
        "DeletedOdmItemGroupRoot",
        "OdmItemValue",
        "OdmItemRoot",
        "DeletedOdmItemRoot",
        "OdmStudyEventValue",
        "OdmStudyEventRoot",
        "DeletedOdmStudyEventRoot",
        "OdmVendorNamespaceValue",
        "OdmVendorNamespaceRoot",
        "DeletedOdmVendorNamespaceRoot",
        "OdmVendorAttributeValue",
        "OdmVendorAttributeRoot",
        "DeletedOdmVendorAttributeRoot",
        "OdmVendorElementValue",
        "OdmVendorElementRoot",
        "DeletedOdmVendorElementRoot",
    ]

    root_odm_nodes = [root for root in all_odm_nodes if "Root" in root]
    value_odm_nodes = [value for value in all_odm_nodes if "Value" in value]

    _, summary = run_cypher_query(
        db_driver,
        f"""
        MATCH (n:{"|".join(root_odm_nodes)})
        WHERE n:ConceptRoot
        REMOVE n:ConceptRoot
        SET n:OdmRoot
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates

    log.info("Replacing `ConceptValue` labels with `OdmValue` for all ODM nodes")

    _, summary = run_cypher_query(
        db_driver,
        f"""
        MATCH (n:{"|".join(value_odm_nodes)})
        WHERE n:ConceptValue
        REMOVE n:ConceptValue
        SET n:OdmValue
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates

    log.info("Adding `Odm` label to all ODM nodes")

    _, summary = run_cypher_query(
        db_driver,
        f"""
        MATCH (n:{"|".join(all_odm_nodes)})
        SET n:Odm
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates

    log.info(
        "Replacing `CONTAINS_CONCEPT` relationships from `Library` with `CONTAINS_ODM`"
    )

    _, summary = run_cypher_query(
        db_driver,
        f"""
        MATCH (n:{"|".join(root_odm_nodes)})<-[r:CONTAINS_CONCEPT]-(l:Library)
        DELETE r
        CREATE (l)-[:CONTAINS_ODM]->(n)
        """,
    )
    print_counters_table(summary.counters)
    contains_updates = contains_updates or summary.counters.contains_updates

    return summary.counters.contains_updates


if __name__ == "__main__":
    main()
