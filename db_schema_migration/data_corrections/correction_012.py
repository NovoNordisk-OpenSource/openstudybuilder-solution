"""PRD Data Corrections, for release 1.14"""

import os

from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import get_logger
from verifications import correction_verification_012

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-release-1.14"


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    remove_duplicate_activity_instance_classes(DB_DRIVER, LOGGER, run_label)


@capture_changes(
    verify_func=correction_verification_012.test_remove_duplicate_activity_instance_classes
)
def remove_duplicate_activity_instance_classes(db_driver, log, run_label):
    """
    ### Problem description
    There are duplicate root-value pairs of Activity Instance Classes for the following:
    `TextualFindings`, `NumericFindings`, `GeneralObservation` and `CategoricFindings`.


    ### Change description
    - Move the `ACTIVITY_INSTANCE_CLASS` relationship between redundant Activity Instance Class nodes to
    the corresponding usable Activity Instance Class nodes.
    - Remove the redundant Activity Instance Class root-value pairs.

    ### Nodes and relationships affected
    - `ActivityInstanceClassValue` nodes
    - `ACTIVITY_INSTANCE_CLASS` relationships
    """

    desc = "Remove duplicate Activity Instance Classes"
    log.info(f"Run: {run_label}, {desc}")

    contains_updates = []

    activity_instance_class_nodes_to_remove_and_their_replacements = [
        (
            "ActivityInstanceClass_000041",
            "ActivityInstanceClass_000014",
        ),  # CategoricFindings
        (
            "ActivityInstanceClass_000036",
            "ActivityInstanceClass_000001",
        ),  # GeneralObservation
        (
            "ActivityInstanceClass_000040",
            "ActivityInstanceClass_000017",
        ),  # NumericFindings
        (
            "ActivityInstanceClass_000042",
            "ActivityInstanceClass_000019",
        ),  # TextualFindings
    ]

    for (
        to_be_removed,
        replacement,
    ) in activity_instance_class_nodes_to_remove_and_their_replacements:
        _, summary = run_cypher_query(
            db_driver,
            f"""
MATCH (r:ActivityInstanceClassRoot {{uid: "{to_be_removed}"}})-[:LATEST]-(v:ActivityInstanceClassValue)
MATCH (pr:ActivityInstanceClassRoot {{uid: "{replacement}"}})-[:LATEST]-(pv:ActivityInstanceClassValue)

OPTIONAL MATCH (activity_instance_node:ActivityInstanceValue)-[:ACTIVITY_INSTANCE_CLASS]->(r)
OPTIONAL MATCH (activity_item_class_node:ActivityItemClassRoot)<-[:HAS_ITEM_CLASS]-(r)

DETACH DELETE r, v

WITH pr, activity_instance_node, activity_item_class_node
WHERE activity_instance_node IS NOT NULL AND activity_item_class_node IS NOT NULL

MERGE (activity_instance_node)-[:ACTIVITY_INSTANCE_CLASS]->(pr)
MERGE (activity_item_class_node)<-[:HAS_ITEM_CLASS]-(pr)

            """,
        )

        counters = summary.counters
        contains_updates.append(counters.contains_updates)

    return any(contains_updates)


if __name__ == "__main__":
    main()
