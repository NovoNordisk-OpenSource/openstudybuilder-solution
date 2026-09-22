"""PRD Data Corrections, for release 1.11.2"""

import os

from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    print_counters_table,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import get_logger
from verifications import correction_verification_010_2

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-release-1.11.2"


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    remove_duplicated_activity_instance_class_rels(DB_DRIVER, LOGGER, run_label)
    instances_lacking_activity(DB_DRIVER, LOGGER, run_label)


@capture_changes(
    verify_func=correction_verification_010_2.test_remove_duplicated_activity_instance_class_rels
)
def remove_duplicated_activity_instance_class_rels(db_driver, log, run_label):
    """
    ### Problem description
    A few `ActivityInstanceValue` nodes have multiple `ACTIVITY_INSTANCE_CLASS` relationships to the same `ActivityClassRoot` node.
    This makes a few api endpoints fail.

    ### Change description
    - The duplicated relationships are removed, keeping only one.

    ### Nodes and relationships affected
    - ACTIVITY_INSTANCE_CLASS relationships between ActivityInstanceValue and ActivityClassRoot nodes.
    - Expected changes: 21 relationships removed.
    """
    log.info(
        f"Run: {run_label}, removing duplicated ACTIVITY_INSTANCE_CLASS relationships"
    )

    # Count duplicated relationships
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (av:ActivityInstanceValue)-[raic:ACTIVITY_INSTANCE_CLASS]->(aicr:ActivityInstanceClassRoot)
        WITH av, aicr, collect(raic) as rels
        WHERE size(rels) > 1
        WITH av, aicr, rels[1..] as unwanted_rels
        FOREACH (r IN unwanted_rels | DELETE r)
        RETURN count(av) as node_count
        """,
    )
    print_counters_table(summary.counters)
    return summary.counters.contains_updates


@capture_changes(
    verify_func=correction_verification_010_2.test_instances_lacking_activity
)
def instances_lacking_activity(db_driver, log, run_label):
    """
    ### Problem description
    A few old `ActivityInstanceValue` nodes are missing a `HAS_ACTIVITY` relationship to an `ActivityGrouping` node.
    This makes a few api endpoints fail.

    ### Change description
    - The `HAS_ACTIVITY` relationship is created for the affected nodes,
      linking to the same `ActivityGrouping` node as the next version of the activity instance.

    ### Nodes and relationships affected
    - HAS_ACTIVITY relationships between ActivityInstanceValue and ActivityGrouping nodes.
    - Expected changes: 3 relationships created.
    """

    log.info(f"Run: {run_label}, adding missing activities to activity instances")

    # Count instances missing an activity
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (ar:ActivityInstanceRoot)-[hv:HAS_VERSION]-(av:ActivityInstanceValue) WHERE NOT (av)-[:HAS_ACTIVITY]->(:ActivityGrouping)
        WITH ar, av, hv ORDER BY hv.start_date DESC
        WITH ar, av, head(collect(hv.version)) as last
        WITH ar, av, split(last, ".")[0] as major
        MATCH (ar)-[hvnext:HAS_VERSION {version: toInteger(major) + 1 + ".0"}]-(:ActivityInstanceValue)-[:HAS_ACTIVITY]->(act)
        WITH DISTINCT ar, av, act
        MERGE (av)-[:HAS_ACTIVITY]->(act)
        RETURN count(av) as node_count
        """,
    )
    print_counters_table(summary.counters)
    return summary.counters.contains_updates


if __name__ == "__main__":
    main()
