"""PRD Data Corrections, for release 1.10"""

import os

from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    print_counters_table,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import get_logger
from verifications import correction_verification_008

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-release-1.10"


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    delete_valid_for_epoch_type_relationship(DB_DRIVER, LOGGER, run_label)
    handle_multiple_activity_value_nodes_for_version(DB_DRIVER, LOGGER, run_label)
    handle_multiple_activity_instance_value_nodes_for_version(
        DB_DRIVER, LOGGER, run_label
    )


@capture_changes(
    verify_func=correction_verification_008.test_delete_valid_for_epoch_type_relationship
)
def delete_valid_for_epoch_type_relationship(db_driver, log, run_label):
    """
    ## Delete VALID_FOR_EPOCH_TYPE relationship

    ### Change Description
    The `VALID_FOR_EPOCH_TYPE` relationship is no longer used,
    and should be removed from the database.

    ### Nodes and relationships affected
    - `VALID_FOR_EPOCH_TYPE` relationships between `CTTermRoot` nodes.
    - Expected changes: 43 relationships deleted.

    """
    desc = "Deleting VALID_FOR_EPOCH_TYPE relationships from CTTermRoot nodes"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH ()-[r:VALID_FOR_EPOCH_TYPE]-()
        DETACH DELETE r
        """,
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(
    docs_only=True,
    verify_func=correction_verification_008.test_handle_multiple_activity_value_nodes_for_version,
    has_subtasks=True,
)
def handle_multiple_activity_value_nodes_for_version(db_driver, log, run_label):
    """
    ## Correct multiple activity value nodes for the same version number

    ### Change Description
    Some ActivityValue nodes have been created when the existing latest value node instead should have been reused.
    This has resulted in multiple ActivityValue nodes for a single version of the activity.

    ### Nodes and relationships affected
    - `ActivityValue` nodes where multiple nodes are linked via `HAS_VERSION` relationships
      with the same version number, to the same `ActivityRoot` node.
    - `ActivityValidGroup` nodes that are linked to the `ActivityValue` nodes.
    - Expected changes: 2003 duplicated nodes merged or modified.
    """
    desc = "Handling duplicate activity value nodes for the same version number"
    log.info(f"Run: {run_label}, {desc}")

    step1 = merge_indentical_activity_value_nodes_for_version(db_driver, log, run_label)
    step2 = merge_indentical_requested_activity_value_nodes_for_version(
        db_driver, log, run_label
    )
    step3 = update_versioning_for_different_activity_values_wih_same_version_number(
        db_driver, log, run_label
    )
    step4 = update_versioning_for_specific_activities(db_driver, log, run_label)
    return step1 or step2 or step3 or step4


@capture_changes(task_level=1)
def merge_indentical_activity_value_nodes_for_version(db_driver, log, run_label):
    """
    ## Merge identical activity value nodes for the same version number

    ### Change Description
    This change merges identical `ActivityValue` nodes that are linked via `HAS_VERSION` relationships.

    See `handle_multiple_activity_value_nodes_for_version` for details.

    ### Nodes and relationships affected
    - `ActivityValue` nodes where multiple nodes are linked via `HAS_VERSION` relationships
      with the same version number, to the same `ActivityRoot` node.
    - `ActivityValidGroup` nodes that are linked to the `ActivityValue` nodes.
    - Expected changes: 1991 duplicated nodes merged.
    """
    desc = "Merging identical activity value nodes for the same version number"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (avg2:ActivityValidGroup)<-[isg2:IN_SUBGROUP]-(g2:ActivityGrouping)<-[hg2:HAS_GROUPING]-(v2)<-[hv2:HAS_VERSION]-(r:ActivityRoot)-[hv1:HAS_VERSION]->(v1)-[hg1:HAS_GROUPING]->(g1:ActivityGrouping)-[isg1:IN_SUBGROUP]->(avg1:ActivityValidGroup)
        WHERE v2 > v1 and hv1.version = hv2.version AND avg1 = avg2
        WITH DISTINCT *
        CALL apoc.refactor.mergeNodes([v1, v2], {properties:"override", mergeRels:false}) YIELD node AS value1
        CALL apoc.refactor.mergeNodes([g1, g2], {properties:"override", mergeRels:true}) YIELD node AS grouping1
        RETURN value1, grouping1
        """,
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(task_level=1)
def merge_indentical_requested_activity_value_nodes_for_version(
    db_driver, log, run_label
):
    """
    ## Merge identical requested activity value nodes for the same version number

    ### Change Description
    This change merges identical `ActivityValue` nodes that are linked via `HAS_VERSION` relationships,
    and are in the `Requested` library.

    See `handle_multiple_activity_value_nodes_for_version` for details.

    ### Nodes and relationships affected
    - `ActivityValue` nodes where multiple nodes are linked via `HAS_VERSION` relationships
      with the same version number, to the same `ActivityRoot` node.
    - Expected changes: 7 duplicated nodes merged.
    """
    desc = (
        "Merging identical requested activity value nodes for the same version number"
    )
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (v2)<-[hv2:HAS_VERSION]-(r:ActivityRoot)-[hv1:HAS_VERSION]->(v1)
        WHERE v2 > v1 and hv1.version = hv2.version
        WITH DISTINCT r, v1, v2, hv1, hv2 
        WHERE NOT (v1)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->(:ActivityValidGroup)
        AND NOT (v2)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->(:ActivityValidGroup)
        CALL apoc.refactor.mergeNodes([v1, v2], {properties:"override", mergeRels:false}) YIELD node AS node1
        RETURN node1
        """,
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(task_level=1)
def update_versioning_for_different_activity_values_wih_same_version_number(
    db_driver, log, run_label
):
    """
    ## Merge identical activity value nodes for the same version number

    ### Change Description
    This change merges identical `ActivityValue` nodes that are linked via `HAS_VERSION` relationships,
    where the value nodes are different but still have the same version number.
    This function handles the easy cases where only the latest version needs to be updated.

    See `handle_multiple_activity_value_nodes_for_version` for details.

    ### Nodes and relationships affected
    - `ActivityValue` nodes where multiple nodes are linked via `HAS_VERSION` relationships
      with the same version number, to the same `ActivityRoot` node.
    - Expected changes: 3 relationships updated.
    """
    desc = "Upversioning unique activity value nodes with the same version number"
    log.info(f"Run: {run_label}, {desc}")

    # "easy" cases where only the latest version needs to be updated
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (avg2:ActivityValidGroup)<-[isg2:IN_SUBGROUP]-(g2:ActivityGrouping)<-[hg2:HAS_GROUPING]-(v2)<-[hv2:HAS_VERSION]-(r:ActivityRoot)-[hv1:HAS_VERSION]->(v1)-[hg1:HAS_GROUPING]->(g1:ActivityGrouping)-[isg1:IN_SUBGROUP]->(avg1:ActivityValidGroup)
        WHERE v2 <> v1 and hv1.version = hv2.version and avg1 <> avg2 and hv2.end_date IS NULL
        WITH r, v2
        MATCH (r)-[hv:HAS_VERSION]-(v2)
        SET hv.version = toInteger(split(hv.version, '.')[0]) + 1 + "." + toInteger(split(hv.version, '.')[1])
        WITH r, v2
        MATCH (r)-[lat:LATEST]->()
        DETACH DELETE lat
        MERGE (r)-[:LATEST]->(v2)
        RETURN r
        """,
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(task_level=1)
def update_versioning_for_specific_activities(db_driver, log, run_label):
    """
    ## Update versioning for specific activities that cannot be handled by the general function

    ### Change Description
    This change updates the `HAS_VERSION` relationships that link `ActivityValue` nodes
    where the value nodes are different but still have the same version number.
    This function handles the complicated cases where a general function is insufficient.

    See `handle_multiple_activity_value_nodes_for_version` for details.

    ### Nodes and relationships affected
    - `ActivityValue` nodes where multiple nodes are linked via `HAS_VERSION` relationships
      with the same version number, to the same `ActivityRoot` node.
    - Expected changes: 14 relationships removed, 15 relationships updated.
    """
    desc = "Upversioning unique activity value nodes with the same version number"
    log.info(f"Run: {run_label}, {desc}")

    # Activity: Diastolic Blood Pressure
    _, summary = run_cypher_query(
        db_driver,
        """
        // version 4.0 is duplicated, bump the second of these and all the following by +1.0
        MATCH (r:ActivityRoot {uid: "Activity_000316"})-[:HAS_VERSION {start_date: datetime("2024-04-29T15:11:26.618602000Z"), version: "4.0"}]-(v)
        MATCH (r)-[hv:HAS_VERSION]-(v)
        SET hv.version = toInteger(split(hv.version, '.')[0]) + 1 + "." + toInteger(split(hv.version, '.')[1])
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000316"})-[:HAS_VERSION {start_date: datetime("2024-04-29T15:14:03.947055000Z"), version: "4.2"}]-(v)
        MATCH (r)-[hv:HAS_VERSION]-(v)
        SET hv.version = toInteger(split(hv.version, '.')[0]) + 1 + "." + toInteger(split(hv.version, '.')[1])
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000316"})-[:HAS_VERSION {start_date: datetime("2024-10-09T12:14:55.424169000Z"), version: "6.2"}]-(v)
        MATCH (r)-[hv:HAS_VERSION]-(v)
        SET hv.version = toInteger(split(hv.version, '.')[0]) + 1 + "." + toInteger(split(hv.version, '.')[1])
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000316"})-[:HAS_VERSION {start_date: datetime("2024-12-20T12:41:59.507428000Z"), version: "7.2"}]-(v)
        MATCH (r)-[hv:HAS_VERSION]-(v)
        SET hv.version = toInteger(split(hv.version, '.')[0]) + 1 + "." + toInteger(split(hv.version, '.')[1])
        RETURN r
        """,
    )
    counters = summary.counters
    print_counters_table(counters)
    step1 = counters.contains_updates

    # Activity: Systolic Blood Pressure
    _, summary = run_cypher_query(
        db_driver,
        """
        // bump the reactivated version to 5.x
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[:HAS_VERSION {start_date: datetime("2024-04-29T15:11:54.425763000Z"), version: "4.0"}]-(v)
        MATCH (r)-[hv:HAS_VERSION]-(v)
        SET hv.version = toInteger(split(hv.version, '.')[0]) + 1 + "." + toInteger(split(hv.version, '.')[1])
        RETURN r
        // bump the next version to 5.2 and 6.x, with correct end date
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-04-29T15:13:05.967199000Z"), version: "4.2"}]-(v)
        SET hv.version = "5.2"
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-04-29T15:21:00.453765000Z"), version: "5.0"}]-(v)
        SET hv.version = "6.0"
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-10-08T13:48:14.045885000Z"), version: "5.1"}]-(v)
        SET hv.version = "6.1"
        SET hv.end_date = datetime("2024-10-09T12:15:01.642110000Z")
        RETURN r
        // remove the excess versions 6.0, 6.1, 7.2, 8.0, 8.1, 9.2, 10.0, 10.1
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-10-08T13:48:39.949977000Z"), version: "6.0"}]-(v)
        DETACH DELETE hv
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-10-09T12:14:39.757060000Z"), version: "6.1"}]-(v)
        DETACH DELETE hv
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-11-14T15:20:51.709509000Z"), version: "7.2"}]-(v)
        DETACH DELETE hv
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-11-14T15:21:03.649389000Z"), version: "8.0"}]-(v)
        DETACH DELETE hv
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-11-14T15:22:33.177468000Z"), version: "8.1"}]-(v)
        DETACH DELETE hv
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-11-14T15:25:34.423007000Z"), version: "9.2"}]-(v)
        DETACH DELETE hv
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-11-14T15:26:42.988125000Z"), version: "10.0"}]-(v)
        DETACH DELETE hv
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-11-14T15:29:02.849030000Z"), version: "10.1"}]-(v)
        DETACH DELETE hv
        RETURN r
        // Bump the second last version to 6.2, 7.0 and 7.1
        //UNION ALL
        //MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-04-29T15:21:00.453765000Z"), version: "6.2"}]-(v)
        //SET hv.version = "6.2"
        //RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-12-20T12:41:58.289320000Z"), version: "11.1"}]-(v)
        SET hv.version = "7.1"
        RETURN r
        // remove the excess versions 7.1, 8.2, 9.0, 9.1, 10.2, 11.0
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-11-14T15:20:11.139020000Z"), version: "7.1"}]-(v)
        DETACH DELETE hv
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-11-14T15:22:48.421014000Z"), version: "8.2"}]-(v)
        DETACH DELETE hv
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-11-14T15:22:56.517367000Z"), version: "9.0"}]-(v)
        DETACH DELETE hv
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-11-14T15:25:19.169280000Z"), version: "9.1"}]-(v)
        DETACH DELETE hv
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-11-14T15:29:23.389651000Z"), version: "10.2"}]-(v)
        DETACH DELETE hv
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-11-14T15:29:29.085469000Z"), version: "11.0"}]-(v)
        DETACH DELETE hv
        RETURN r
        // Change the final version to 7.2 and 8.0
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-12-20T12:42:02.279144000Z"), version: "11.2"}]-(v)
        SET hv.version = "7.2"
        RETURN r
        UNION ALL
        MATCH (r:ActivityRoot {uid: "Activity_000317"})-[hv:HAS_VERSION {start_date: datetime("2024-12-20T12:42:06.446974000Z"), version: "12.0"}]-(v)
        SET hv.version = "8.0"
        RETURN r
        """,
    )
    counters = summary.counters
    print_counters_table(counters)
    step2 = counters.contains_updates

    return step1 or step2


@capture_changes(
    docs_only=True,
    verify_func=correction_verification_008.test_handle_multiple_activity_instance_value_nodes_for_version,
    has_subtasks=True,
)
def handle_multiple_activity_instance_value_nodes_for_version(
    db_driver, log, run_label
):
    """
    ## Correct multiple activity instance value nodes for the same version number

    ### Change Description
    Some ActivityInstanceValue nodes have been created when the existing latest value node instead should have been reused.
    This has resulted in multiple ActivityInstanceValue nodes for a single version of the activity instance.

    ### Nodes and relationships affected
    - `ActivityInstanceValue` nodes where multiple nodes are linked via `HAS_VERSION` relationships
      with the same version number, to the same `ActivityInstanceRoot` node.
    - Expected changes: 23 duplicated nodes merged or modified.
    """
    desc = (
        "Handling duplicate activity instance value nodes for the same version number"
    )
    log.info(f"Run: {run_label}, {desc}")

    step1 = merge_indentical_activity_instance_value_nodes_for_version(
        db_driver, log, run_label
    )
    step2 = update_versioning_for_specific_instances(db_driver, log, run_label)
    return step1 or step2


@capture_changes(task_level=1)
def merge_indentical_activity_instance_value_nodes_for_version(
    db_driver, log, run_label
):
    """
    ## Merge identical activity instance value nodes for the same version number

    ### Change Description
    This change merges identical `ActivityInstanceValue` nodes that are linked via `HAS_VERSION` relationships.

    See `handle_multiple_activity_instance_value_nodes_for_version` for details.

    ### Nodes and relationships affected
    - `ActivityInstanceValue` nodes where multiple nodes are linked via `HAS_VERSION` relationships
      with the same version number, to the same `ActivityInstanceRoot` node.
    - Expected changes: 21 duplicated nodes merged.
    """
    desc = "Merging identical activity instance value nodes for the same version number"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (ag2:ActivityGrouping)<-[ha2:HAS_ACTIVITY]-(v2)<-[hv2:HAS_VERSION]-(r:ActivityInstanceRoot)-[hv1:HAS_VERSION]->(v1)-[ha1:HAS_ACTIVITY]->(ag1:ActivityGrouping)
        WHERE v2 > v1 and hv1.version = hv2.version AND ag1 = ag2
        WITH DISTINCT *
        CALL apoc.refactor.mergeNodes([v1, v2], {properties:"override", mergeRels:false}) YIELD node AS value1
        // We don't want to merge the HAS_VERSION relationships, so we run mergeNodes with mergeRelse=false.
        // This means we get duplicated HAS_ACTIVITY relationships that need to be deleted manually.
        MATCH (value1)-[ha:HAS_ACTIVITY]-(ag:ActivityGrouping)
        WITH value1, ag, collect(ha) as has
        FOREACH (rel IN tail(has) | DELETE rel)
        RETURN value1
        """,
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(task_level=1)
def update_versioning_for_specific_instances(db_driver, log, run_label):
    """
    ## Update versioning for specific activity instances that cannot be handled by the general function

    ### Change Description
    This change updates the `HAS_VERSION` relationships that link `ActivityInstanceValue` nodes
    where the value nodes are different but still have the same version number.
    This function handles the few cases where a general function is insufficient.

    See `handle_multiple_activity_instance_value_nodes_for_version` for details.

    ### Nodes and relationships affected
    - `ActivityInstanceValue` nodes where multiple nodes are linked via `HAS_VERSION` relationships
      with the same version number, to the same `ActivityInstanceRoot` node.
    - Expected changes: 8 relationships updated.
    """
    desc = (
        "Upversioning unique activity instance value nodes with the same version number"
    )
    log.info(f"Run: {run_label}, {desc}")

    # Instance: Physical Examination
    _, summary = run_cypher_query(
        db_driver,
        """
        // version 3.0 is duplicated, bump the second of these to 4.0
        MATCH (r:ActivityInstanceRoot {uid: "ActivityInstance_000623"})-[:HAS_VERSION {start_date: datetime("2024-03-27T08:55:56.038070000Z"), version: "3.0"}]-(v)
        MATCH (r)-[hv:HAS_VERSION]-(v)
        SET hv.version = toInteger(split(hv.version, '.')[0]) + 1 + "." + toInteger(split(hv.version, '.')[1])
        RETURN r
        """,
    )
    counters = summary.counters
    print_counters_table(counters)
    step1 = counters.contains_updates

    # Instance: Bilirubin Dipstick Urine
    _, summary = run_cypher_query(
        db_driver,
        """
        // version 1.0 is duplicated, bump the second of these and all following versions by +1.0
        MATCH (r:ActivityInstanceRoot {uid: "CategoricFinding_000201"})-[:HAS_VERSION {start_date: datetime("2024-09-13T15:41:58.565492000Z"), version: "1.0"}]-(v)
        MATCH (r)-[hv:HAS_VERSION]-(v)
        SET hv.version = toInteger(split(hv.version, '.')[0]) + 1 + "." + toInteger(split(hv.version, '.')[1])
        RETURN r
        UNION ALL
        MATCH (r:ActivityInstanceRoot {uid: "CategoricFinding_000201"})-[:HAS_VERSION {start_date: datetime("2024-09-27T12:00:33.408117000Z"), version: "1.2"}]-(v)
        MATCH (r)-[hv:HAS_VERSION]-(v)
        SET hv.version = toInteger(split(hv.version, '.')[0]) + 1 + "." + toInteger(split(hv.version, '.')[1])
        RETURN r
        UNION ALL
        MATCH (r:ActivityInstanceRoot {uid: "CategoricFinding_000201"})-[:HAS_VERSION {start_date: datetime("2024-12-13T15:34:40.241081000Z"), version: "2.2"}]-(v)
        MATCH (r)-[hv:HAS_VERSION]-(v)
        SET hv.version = toInteger(split(hv.version, '.')[0]) + 1 + "." + toInteger(split(hv.version, '.')[1])
        RETURN r
        """,
    )
    counters = summary.counters
    print_counters_table(counters)
    step2 = counters.contains_updates

    # Instance: Mean Pulse
    _, summary = run_cypher_query(
        db_driver,
        """
        // version 4.0 is duplicated, bump the second of these and all following versions by +1.0
        MATCH (r:ActivityInstanceRoot {uid: "NumericFinding_000234"})-[:HAS_VERSION {start_date: datetime("2024-03-25T13:44:32.488514000Z"), version: "4.0"}]-(v)
        MATCH (r)-[hv:HAS_VERSION]-(v)
        SET hv.version = toInteger(split(hv.version, '.')[0]) + 1 + "." + toInteger(split(hv.version, '.')[1])
        RETURN r
        UNION ALL
        MATCH (r:ActivityInstanceRoot {uid: "NumericFinding_000234"})-[:HAS_VERSION {start_date: datetime("2024-03-25T13:47:43.677245000Z"), version: "4.2"}]-(v)
        MATCH (r)-[hv:HAS_VERSION]-(v)
        SET hv.version = toInteger(split(hv.version, '.')[0]) + 1 + "." + toInteger(split(hv.version, '.')[1])
        RETURN r
        UNION ALL
        MATCH (r:ActivityInstanceRoot {uid: "NumericFinding_000234"})-[:HAS_VERSION {start_date: datetime("2024-07-12T13:38:14.059328000Z"), version: "5.2"}]-(v)
        MATCH (r)-[hv:HAS_VERSION]-(v)
        SET hv.version = toInteger(split(hv.version, '.')[0]) + 1 + "." + toInteger(split(hv.version, '.')[1])
        RETURN r
        UNION ALL
        MATCH (r:ActivityInstanceRoot {uid: "NumericFinding_000234"})-[:HAS_VERSION {start_date: datetime("2024-09-27T12:38:51.535904000Z"), version: "6.2"}]-(v)
        MATCH (r)-[hv:HAS_VERSION]-(v)
        SET hv.version = toInteger(split(hv.version, '.')[0]) + 1 + "." + toInteger(split(hv.version, '.')[1])
        RETURN r
        UNION ALL
        MATCH (r:ActivityInstanceRoot {uid: "NumericFinding_000234"})-[:HAS_VERSION {start_date: datetime("2024-10-08T10:22:05.833753000Z"), version: "7.2"}]-(v)
        MATCH (r)-[hv:HAS_VERSION]-(v)
        SET hv.version = toInteger(split(hv.version, '.')[0]) + 1 + "." + toInteger(split(hv.version, '.')[1])
        RETURN r
        """,
    )
    counters = summary.counters
    print_counters_table(counters)
    step3 = counters.contains_updates

    return step1 or step2 or step3


if __name__ == "__main__":
    main()
