"""Schema migrations needed to release 2.8 in PROD"""

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
MIGRATION_DESC = "schema-migration-release-2.8"


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


def migrate_instance_split(db_driver, log) -> bool:
    """
    Split ActivityInstance data into the grouping model.

    For each ActivityInstanceRoot -> ActivityInstanceValue pair that has
    direct HAS_ACTIVITY links and no HAS_GROUPING_ROOT, this migration creates
    an ActivityInstanceGroupingRoot and a corresponding
    ActivityInstanceGroupingValue. It then recreates the existing
    ActivityInstanceRoot -> ActivityInstanceValue relationship types/properties
    between the new grouping nodes and moves HAS_ACTIVITY relationships from
    ActivityInstanceValue to ActivityInstanceGroupingValue.
    """

    log.info("Running instance split migration query")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (air:ActivityInstanceRoot)-[rel]->(aiv:ActivityInstanceValue)-[:HAS_ACTIVITY]->(activity:ActivityGrouping)
        WHERE NOT (air)-[:HAS_GROUPING_ROOT]->(:ActivityInstanceGroupingRoot)
        WITH DISTINCT air, aiv, collect(rel) AS rels, collect(activity) AS activities
        MERGE (air)-[:HAS_GROUPING_ROOT]->(gr:ActivityInstanceGroupingRoot)
        WITH air, aiv, gr, rels, activities
        CALL {
            WITH air, aiv, gr, rels
            CREATE (gv:ActivityInstanceGroupingValue)
            WITH gr, gv, rels
            UNWIND rels AS rel
            CALL apoc.create.relationship(gr,type(rel),properties(rel), gv) YIELD rel AS new_rel 
            RETURN gv
        }
        CALL {
            with air, aiv, gr, gv, activities
            UNWIND activities as activity
            MATCH (aiv)-[ha:HAS_ACTIVITY]->(activity)
            MERGE (gv)-[:HAS_ACTIVITY]->(activity)
            DELETE ha
        }
        RETURN count(aiv)
        """,
    )
    print_counters_table(summary.counters)
    return summary.counters.contains_updates


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])
    ### Common migrations
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_ct_config_values(DB_CONNECTION, logger)

    ### Release migrations
    migrate_feature_flags(DB_DRIVER, logger)
    migrate_instance_split(DB_DRIVER, logger)


if __name__ == "__main__":
    main()
