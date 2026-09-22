"""PRD Data Corrections: Release 2.0"""

import os

from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import get_logger, print_counters_table
from verifications import correction_verification_014

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-release-2.0"


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    remove_orphan_activity_instances(DB_DRIVER, LOGGER, run_label)
    remove_orphan_activity_instance_classes(DB_DRIVER, LOGGER, run_label)
    remove_orphan_study_fields(DB_DRIVER, LOGGER, run_label)
    fix_instances_with_multiple_activities(DB_DRIVER, LOGGER, run_label)
    delete_unwanted_studies(DB_DRIVER, LOGGER, run_label)
    remove_unwanted_sponsor_terms(DB_DRIVER, LOGGER, run_label)
    remove_dummy_definitions(DB_DRIVER, LOGGER, run_label)
    fix_baseline2_submission_values(DB_DRIVER, LOGGER, run_label)
    fix_study_selection_drop_relationships(DB_DRIVER, LOGGER, run_label)
    set_author_id_for_cdisc_data(DB_DRIVER, LOGGER, run_label)
    multiple_null_value_reasons(DB_DRIVER, LOGGER, run_label)


@capture_changes(
    verify_func=correction_verification_014.test_study_selection_drop_relationships
)
def fix_study_selection_drop_relationships(db_driver, log, run_label):
    """
    ### Problem description
    In the current database schema, certain relationships between `StudySelection` nodes may be inadvertently dropped
    when `StudyAction` nodes are created or deleted.
    This can lead to loss of important connections that define the timeline of changes (Audit trail) of study selections.
    Specifically, relationships such as `STUDY_EPOCH_HAS_STUDY_VISIT`, `STUDY_VISIT_HAS_SCHEDULE`,
    and others may not be properly maintained during these operations.

    ### Change description
    - Identify and restore any dropped relationships between `StudySelection` nodes
      that should be maintained based on the temporal context provided by `StudyAction` nodes.
    - Ensure that the relationships are only restored when they are temporally relevant, i.e.,
      when the `StudySelection` nodes are active during the same time period as defined by the `StudyAction` nodes.
    - Use temporal logic to determine the validity of relationships based on the dates associated with the `StudyAction` nodes.

    ### Nodes and relationships affected
    - `StudySelection` nodes
    - Relationships: `STUDY_EPOCH_HAS_STUDY_VISIT`, `STUDY_VISIT_HAS_SCHEDULE`, `STUDY_EPOCH_HAS_DESIGN_CELL`, `STUDY_ACTIVITY_HAS_SCHEDULE`,
      `STUDY_ACTIVITY_HAS_INSTRUCTION`, `STUDY_ELEMENT_HAS_DESIGN_CELL`, `STUDY_ARM_HAS_BRANCH_ARM`
    """
    contains_updates = []

    log.info("Migrating - Removing corrupted relationships")
    log.info(
        f"Run: {run_label}, Migrating - Removing corrupted relationships representing'{CORRECTION_DESC}' correction"
    )
    query = """
        /*
        This query is designed to maintain the integrity of relationships between StudySelection nodes
        when they are part of temporal sequences defined by StudyAction nodes. It identifies pairs of StudySelection
        nodes connected by specific relationship types and ensures that these relationships are preserved across
        different time points, as indicated by the StudyAction nodes. The query uses temporal logic to
        determine the validity of relationships based on the dates associated with the StudyAction nodes, ensuring
        that relationships are only connected to those nodes which are time coherent. 
        */
                
        //REMOVE RELS 
        MATCH (ss1_init:StudySelection)-[required_rel]->(ss2_init:StudySelection)
            WHERE
                ss1_init.uid = "StudyEpoch_000182" and ss2_init.uid="StudyDesignCell_000412"
                OR ss1_init.uid = "StudyEpoch_000167" and ss2_init.uid="StudyDesignCell_000344"
        WITH DISTINCT ss1_init.uid as ss1_uid, TYPE(required_rel) AS required_rel_type, ss2_init.uid as ss2_uid
        WHERE required_rel_type IN [
            "STUDY_EPOCH_HAS_STUDY_VISIT",
            "STUDY_VISIT_HAS_SCHEDULE",
            "STUDY_EPOCH_HAS_DESIGN_CELL",
            "STUDY_ACTIVITY_HAS_INSTRUCTION",
            "STUDY_ELEMENT_HAS_DESIGN_CELL",
            "STUDY_ARM_HAS_BRANCH_ARM"
        ]
        CALL {
            WITH ss1_uid,ss2_uid, required_rel_type
            MATCH (ss1_group:StudySelection)
            WHERE ss1_group.uid = ss1_uid
            MATCH (ss2_group:StudySelection)
            WHERE ss2_group.uid = ss2_uid
            WITH COLLECT(DISTINCT ss1_group) as ss1_group_collected, COLLECT(DISTINCT ss2_group) as ss2_group_collected, required_rel_type
            // Extract all ss1 before and after date
            CALL {
                WITH ss1_group_collected, required_rel_type
                UNWIND ss1_group_collected as ss1_group

                MATCH (ss1_group)<-[:AFTER]-(ss1_group_after_saction:StudyAction)
                OPTIONAL MATCH (ss1_group)<-[:BEFORE]-(ss1_saction:StudyAction)
                OPTIONAL MATCH (ss1_group)-[ss1_ss12]-(ss12:StudySelection) // GET THE StudySelection connected to ss1_group
                    WHERE TYPE(ss1_ss12)=required_rel_type
                WITH ss1_group_after_saction.date AS ss1_group_start_date, ss1_group, ss1_group_after_saction, ss12.uid as ss12_uid,
                CASE 
                    WHEN ss1_saction IS NULL AND NOT ss1_group_after_saction:Delete then datetime({epochMillis: apoc.date.currentTimestamp()})
                    WHEN ss1_saction IS NULL AND ss1_group_after_saction:Delete then ss1_group_after_saction.date
                    ELSE ss1_saction.date
                END AS ss1_group_end_date
                RETURN DISTINCT ss1_group_start_date, ss1_group, ss1_group_end_date, ss1_group_after_saction, ss12_uid
            }
            // Extract all ss2 before and after date
            CALL{
                WITH  ss2_group_collected, required_rel_type
                UNWIND ss2_group_collected as ss2_group

                MATCH (ss2_group)<-[:AFTER]-(ss2_group_after_saction:StudyAction)
                OPTIONAL MATCH (ss2_group)<-[:BEFORE]-(ss2_saction:StudyAction)
                OPTIONAL MATCH (ss2_group)-[ss2_ss22]-(ss22:StudySelection) // GET THE StudySelection connected to ss2_group
                    WHERE TYPE(ss2_ss22)=required_rel_type
                WITH *, ss2_group_after_saction.date AS ss2_group_start_date, ss2_group, ss2_group_after_saction, ss22.uid as ss22_uid,
                CASE 
                    WHEN ss2_saction IS NULL AND NOT ss2_group_after_saction:Delete then datetime({epochMillis: apoc.date.currentTimestamp()})
                    WHEN ss2_saction IS NULL AND ss2_group_after_saction:Delete then ss2_group_after_saction.date
                    ELSE ss2_saction.date
                END AS ss2_group_end_date
                RETURN DISTINCT ss2_group_start_date, ss2_group, ss2_group_end_date, ss2_group_after_saction, ss22_uid

            }
            WITH    ss1_group_start_date, ss1_group, ss1_group_end_date, ss1_group_after_saction, 
                    ss2_group_start_date, ss2_group, ss2_group_end_date, ss2_group_after_saction, 
                    required_rel_type, ss12_uid, ss22_uid
            CALL{
                WITH ss1_group_start_date, ss1_group, ss1_group_end_date, ss1_group_after_saction, 
                    ss2_group_start_date, ss2_group, ss2_group_end_date, ss2_group_after_saction, 
                    required_rel_type, ss12_uid, ss22_uid
                MATCH (ss1_group)-[should_not_rel_1_2]->(ss2_group)
                        WHERE
                            NOT (ss1_group_start_date>ss2_group_start_date
                                    AND ss1_group_start_date<ss2_group_end_date)
                MATCH (ss2_group)<-[should_not_rel_2_1]-(ss1_group)
                        WHERE
                            NOT (ss2_group_start_date>ss1_group_start_date
                                        AND ss2_group_start_date<ss1_group_end_date)
                MATCH (ss1_group)-[corrupt_rel]->(ss2_group)
                DELETE corrupt_rel
                return corrupt_rel
            }

            RETURN corrupt_rel
        }
        RETURN *
    """
    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    contains_updates.append(counters.contains_updates)

    log.info("Migrating - Maintaining relationships")
    # Create Migrating - Maintaining relationships this correction (CORRECTION_DESC)
    log.info(
        f"Run: {run_label}, Migrating - Maintaining relationships representing '{CORRECTION_DESC}' correction"
    )
    query = """
        /*
        This query is designed to maintain the integrity of relationships between StudySelection nodes
        when they are part of temporal sequences defined by StudyAction nodes. It identifies pairs of StudySelection
        nodes connected by specific relationship types and ensures that these relationships are preserved across
        different time points, as indicated by the StudyAction nodes. The query uses temporal logic to
        determine the validity of relationships based on the dates associated with the StudyAction nodes, ensuring
        that relationships are only maintained when they are temporally relevant.
        */
        // CREATE RELS
        MATCH (ss1_init:StudySelection)-[required_rel]->(ss2_init:StudySelection)                                           //
            WHERE
                ss1_init.uid = "StudyEpoch_000182" and ss2_init.uid="StudyDesignCell_000412"
                OR ss1_init.uid = "StudyEpoch_000167" and ss2_init.uid="StudyDesignCell_000344"
        WITH DISTINCT ss1_init.uid as ss1_uid, TYPE(required_rel) AS required_rel_type, ss2_init.uid as ss2_uid
        WHERE required_rel_type IN [
            "STUDY_EPOCH_HAS_STUDY_VISIT",
            "STUDY_VISIT_HAS_SCHEDULE",
            "STUDY_EPOCH_HAS_DESIGN_CELL",
            "STUDY_ACTIVITY_HAS_INSTRUCTION",
            "STUDY_ELEMENT_HAS_DESIGN_CELL",
            "STUDY_ARM_HAS_BRANCH_ARM"
        ]
        CALL {
            WITH ss1_uid,ss2_uid, required_rel_type
            MATCH (ss1_group:StudySelection)
            WHERE ss1_group.uid = ss1_uid
            MATCH (ss2_group:StudySelection)
            WHERE ss2_group.uid = ss2_uid
            WITH COLLECT(DISTINCT ss1_group) as ss1_group_collected, COLLECT(DISTINCT ss2_group) as ss2_group_collected, required_rel_type
            // Extract all ss1 before and after date
            CALL {
                WITH ss1_group_collected, required_rel_type
                UNWIND ss1_group_collected as ss1_group

                MATCH (ss1_group)<-[:AFTER]-(ss1_group_after_saction:StudyAction)
                OPTIONAL MATCH (ss1_group)<-[:BEFORE]-(ss1_saction:StudyAction)
                OPTIONAL MATCH (ss1_group)-[ss1_ss12]-(ss12:StudySelection) // GET THE StudySelection connected to ss1_group
                    WHERE TYPE(ss1_ss12)=required_rel_type
                WITH ss1_group_after_saction.date AS ss1_group_start_date, ss1_group, ss1_group_after_saction, ss12.uid as ss12_uid,
                CASE 
                    WHEN ss1_saction IS NULL AND NOT ss1_group_after_saction:Delete then datetime({epochMillis: apoc.date.currentTimestamp()})
                    WHEN ss1_saction IS NULL AND ss1_group_after_saction:Delete then ss1_group_after_saction.date
                    ELSE ss1_saction.date
                END AS ss1_group_end_date
                RETURN DISTINCT ss1_group_start_date, ss1_group, ss1_group_end_date, ss1_group_after_saction, ss12_uid
            }
            // Extract all ss2 before and after date
            CALL{
                WITH  ss2_group_collected, required_rel_type
                UNWIND ss2_group_collected as ss2_group

                MATCH (ss2_group)<-[:AFTER]-(ss2_group_after_saction:StudyAction)
                OPTIONAL MATCH (ss2_group)<-[:BEFORE]-(ss2_saction:StudyAction)
                OPTIONAL MATCH (ss2_group)-[ss2_ss22]-(ss22:StudySelection) // GET THE StudySelection connected to ss2_group
                    WHERE TYPE(ss2_ss22)=required_rel_type
                WITH *, ss2_group_after_saction.date AS ss2_group_start_date, ss2_group, ss2_group_after_saction, ss22.uid as ss22_uid,
                CASE 
                    WHEN ss2_saction IS NULL AND NOT ss2_group_after_saction:Delete then datetime({epochMillis: apoc.date.currentTimestamp()})
                    WHEN ss2_saction IS NULL AND ss2_group_after_saction:Delete then ss2_group_after_saction.date
                    ELSE ss2_saction.date
                END AS ss2_group_end_date
                RETURN DISTINCT ss2_group_start_date, ss2_group, ss2_group_end_date, ss2_group_after_saction, ss22_uid

            }
            WITH    ss1_group_start_date, ss1_group, ss1_group_end_date, ss1_group_after_saction, 
                    ss2_group_start_date, ss2_group, ss2_group_end_date, ss2_group_after_saction, 
                    required_rel_type, ss12_uid, ss22_uid
            // match (ss2_group)-[rel_aux]-(ss1_group)
            // RETURN rel_aux AS output
            // Extract all ss2 before and after date
            FOREACH( _ in CASE 
                            WHEN 
                                ss1_group_start_date>ss2_group_start_date
                                AND ss1_group_start_date<ss2_group_end_date
                                AND (                                           // FOR ss1 should be CREATED the relationships to ss2
                                        NOT EXISTS((ss1_group)--(ss2_group))    // WHEN the relationship does not exist
                                        OR NOT (                                   // AND ss1 is NOT connected to another ss2 (ss12) that is not ss2_group 
                                            ss12_uid IS NOT NULL                        // (i.e. NOT AN EDIT -- CHANGE OF ss2)
                                            AND ss1_group.uid <> ss12_uid // ss2_group is not connected to ss1_group
                                        )
                                    )
                            THEN [true]
                        END |
                    MERGE (ss1_group)<-[:REQ1]-(ss2_group))
            FOREACH( _ in CASE
                            WHEN
                                ss2_group_start_date>ss1_group_start_date
                                AND ss2_group_start_date<ss1_group_end_date
                                AND (                                           // FOR ss2 should be CREATED the relationships to ss1
                                        NOT EXISTS((ss1_group)--(ss2_group))    // WHEN the relationship does not exist
                                        OR NOT (                                   // AND ss2 is NOT connected to another ss1 (ss22) that is not ss1_group
                                            ss22_uid IS NOT NULL                        // (i.e.IS NOT AN EDIT -- CHANGE OF ss1)
                                            AND ss2_group.uid <> ss22_uid       // ss2_group is not connected to ss1_group
                                        )
                                    )
                            THEN [true]
                        END |
                    MERGE (ss1_group)<-[:REQ2]-(ss2_group))
            WITH required_rel_type
            MATCH ()-[new_rel:REQ1|REQ2]-()
            CALL apoc.refactor.setType(new_rel, required_rel_type)
            YIELD input, output
            RETURN output
        }
        WITH TYPE(output) as output_type, ss1_uid,ss2_uid
        WHERE output IS NOT NULL
        RETURN *
    """
    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    contains_updates.append(counters.contains_updates)
    return any(contains_updates)


@capture_changes(
    verify_func=correction_verification_014.test_remove_orphan_activity_instances
)
def remove_orphan_activity_instances(db_driver, log, run_label):
    """
    ### Problem description
    There are orphan ActivityInstance nodes in the database that need to be removed.
    These nodes were created because of a bug where we would create Root and Value nodes,
    then the operation would be aborted because of a business rule violation,
    and it was happening outside of a transaction, hence the nodes were not deleted.

    ### Change description
    - Delete orphan ActivityInstance nodes - Root and Value.
    - Execute two specific Cypher queries to identify and remove these orphan nodes.

    ### Nodes and relationships affected
    - `ActivityInstanceRoot` nodes
    - `ActivityInstanceValue` nodes
    """
    contains_updates = []

    # Delete orphan ActivityInstanceRoot nodes
    log.info(
        f"Run: {run_label}, Execute first query to remove orphan ActivityInstance nodes"
    )
    query = """
    MATCH (ai:ActivityInstanceRoot) WHERE NOT EXISTS ((ai)-[:LATEST]->(:ActivityInstanceValue))
    DETACH DELETE ai
    RETURN count(ai) as node_count
    """
    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    contains_updates.append(counters.contains_updates)

    # Delete orphan ActivityInstanceValue nodes
    log.info(
        f"Run: {run_label}, Execute second query to remove orphan ActivityInstance nodes"
    )
    query = """
    MATCH (ai:ActivityInstanceValue) WHERE NOT EXISTS ((ai)--())
    DETACH DELETE ai
    RETURN count(ai) as node_count
    """
    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    contains_updates.append(counters.contains_updates)

    return any(contains_updates)


@capture_changes(
    verify_func=correction_verification_014.test_remove_orphan_activity_instance_classes
)
def remove_orphan_activity_instance_classes(db_driver, log, run_label):
    """
    ### Problem description
    There are orphan ActivityInstanceClassValue nodes in the database that need to be removed.
    The source bug has not been identified yet, but it seems probably related to some bad migrations in the past.

    ### Change description
    - Delete orphan ActivityInstanceClassValue nodes.

    ### Nodes and relationships affected
    - `ActivityInstanceClassValue` nodes
    """
    contains_updates = []

    # Delete orphan ActivityInstanceClassValue nodes
    log.info(
        f"Run: {run_label}, Execute query to remove orphan ActivityInstanceClassValue nodes"
    )
    query = """
    MATCH (aic:ActivityInstanceClassValue) WHERE NOT EXISTS ((aic)--())
    DETACH DELETE aic
    RETURN count(aic) as node_count
    """
    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    contains_updates.append(counters.contains_updates)

    return any(contains_updates)


@capture_changes(
    verify_func=correction_verification_014.test_remove_orphan_study_fields
)
def remove_orphan_study_fields(db_driver, log, run_label):
    """
    ### Problem description
    There are orphan StudyField nodes in the database that need to be removed.
    The source bug has not been identified yet, but it seems probably related to some bad migrations in the past.

    ### Change description
    - Delete orphan StudyField nodes.

    ### Nodes and relationships affected
    - `StudyField` nodes
    """
    contains_updates = []

    # Delete orphan StudyField nodes
    log.info(f"Run: {run_label}, Execute query to remove orphan StudyField nodes")
    query = """
    MATCH (sf:StudyField) WHERE NOT EXISTS ((sf)--())
    DETACH DELETE sf
    RETURN count(sf) as node_count
    """
    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    contains_updates.append(counters.contains_updates)


@capture_changes(
    verify_func=correction_verification_014.test_fix_instances_with_multiple_activities
)
def fix_instances_with_multiple_activities(db_driver, log, run_label):
    """
    ### Problem description
    There are ActivityInstanceValue nodes that are connected to multiple ActivityValue nodes through ActivityGrouping.
    This is not allowed and needs to be fixed.

    ### Change description
    - Delete offending, extra relationships between ActivityInstanceValue and ActivityGrouping nodes.

    ### Nodes and relationships affected
    - `HAS_ACTIVITY` relationships
    """

    contains_updates = []

    # Check if there are some cases
    check_query = """
    MATCH (aiv:ActivityInstanceValue)<-[ha:HAS_ACTIVITY]->(ag:ActivityGrouping)<-[hg:HAS_GROUPING]-(av:ActivityValue)
    WITH aiv, collect(DISTINCT av) AS avs
    WITH aiv WHERE size(avs) > 1
    RETURN count(DISTINCT aiv) as multiple_activities_count,
    COLLECT(DISTINCT aiv.name) as multiple_activities_names
    """
    res, _ = run_cypher_query(db_driver, check_query)
    if res[0][0] > 0:
        log.info(
            f"Run: {run_label}, Found {res[0][0]} ActivityInstanceValue nodes connected to multiple ActivityValue nodes through ActivityGrouping"
        )

        # In some cases, the ActivityInstanceValue node has the same name as the ActivityValue node.
        # In these cases, keep the relationship to the corresponding ActivityGroup and delete the others.
        query = """
        MATCH (aiv:ActivityInstanceValue)<-[ha:HAS_ACTIVITY]->(ag:ActivityGrouping)<-[hg:HAS_GROUPING]-(av:ActivityValue)
        WITH aiv, collect(DISTINCT av) AS avs
        WITH aiv WHERE size(avs) > 1
            AND EXISTS ((aiv)<-[:HAS_ACTIVITY]->(:ActivityGrouping)<-[:HAS_GROUPING]-(:ActivityValue {name: aiv.name}))
        MATCH p=(aiv)<-[ha:HAS_ACTIVITY]->(:ActivityGrouping)<-[:HAS_GROUPING]-(bad_av:ActivityValue)
            WHERE aiv.name <> bad_av.name
        DELETE ha
        RETURN count(DISTINCT ha) as deleted_relationships_count
        """
        _, summary = run_cypher_query(db_driver, query)
        counters = summary.counters
        contains_updates.append(counters.contains_updates)

        res, _ = run_cypher_query(db_driver, check_query)
        if res[0][0] > 0:
            # If some cases remain, keep the ActivityValue with same name
            # as the one related to the latest version of the ActivityInstanceValue node and delete the others
            query = """
            MATCH (aiv:ActivityInstanceValue)<-[:HAS_ACTIVITY]->(:ActivityGrouping)<-[:HAS_GROUPING]-(av:ActivityValue)
            WITH aiv, collect(DISTINCT av) AS avs
            WITH aiv WHERE size(avs) > 1 AND NOT EXISTS ((:ActivityInstanceRoot)-->(aiv)<-[:HAS_ACTIVITY]->(:ActivityGrouping)<-[:HAS_GROUPING]-(:ActivityValue {name: aiv.name}))
            MATCH (aiv)<--(:ActivityInstanceRoot)-[:LATEST]->(:ActivityInstanceValue)<-[:HAS_ACTIVITY]->(:ActivityGrouping)<-[:HAS_GROUPING]-(latest_av:ActivityValue)
            WHERE EXISTS ((aiv)<-[:HAS_ACTIVITY]->(:ActivityGrouping)<-[:HAS_GROUPING]-(:ActivityValue {name: latest_av.name}))
            MATCH (aiv)<-[ha:HAS_ACTIVITY]->(:ActivityGrouping)<-[:HAS_GROUPING]-(bad_av:ActivityValue)
                WHERE bad_av.name <> latest_av.name
            DELETE ha
            RETURN count(DISTINCT ha) as deleted_relationships_count
            """
            _, summary = run_cypher_query(db_driver, query)
            counters = summary.counters
            contains_updates.append(counters.contains_updates)

    res, _ = run_cypher_query(db_driver, check_query)
    if res[0][0] > 0:
        log.info(
            f"Run: {run_label}, After running corrections, still found {res[0][0]} ActivityInstanceValue nodes connected to multiple ActivityValue nodes through ActivityGrouping"
        )
        # We should not reach this point, but if we do, we should log the uids of the offending nodes
        log.info(
            f"Run: {run_label}, UIDs of the offending ActivityInstanceValue nodes: {res[0][1]}"
        )
    return any(contains_updates)


@capture_changes(task_level=1)
def delete_unwanted_study(db_driver, log, run_label, study_number):
    """
    ## Delete one complete study

    See `delete_unwanted_studies` for details.
    """
    desc = f"Deleting study number {study_number} from the database"
    log.info(f"Run: {run_label}, {desc}")

    # This query deletes a complete study from the database
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (sr:StudyRoot)-[hsv]-(sv:StudyValue)
        WHERE (sr)--(:StudyValue {study_number: $study_number})
        CALL {
          WITH sr
          MATCH (sr)-[at:AUDIT_TRAIL]->(sa:StudyAction)
          MATCH (sa)-[before_after_sel:BEFORE|AFTER]->(ss:StudySelection)
          DETACH DELETE ss, sa
        } IN TRANSACTIONS
        CALL {
            WITH sv
            MATCH (sv)-[hsf]->(sf:StudyField)
            DETACH DELETE sf
        } IN TRANSACTIONS
        CALL {
            WITH sv
            MATCH (sv)-[hss]->(ss2:StudySelection)
            DETACH DELETE ss2
        } IN TRANSACTIONS
        DETACH DELETE sr, sv
        """,
        {"study_number": study_number},
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(
    docs_only=True,
    verify_func=correction_verification_014.test_delete_unwanted_studies,
    has_subtasks=True,
)
def delete_unwanted_studies(db_driver, log, run_label):
    """
    ## Remove unwanted studies

    ### Problem description
    Some studies have been created by mistake in the production environment.
    These occupy some Study IDs and cause confusion.
    There are also unused template studies that are outdated and should be removed
    to avoid confusion.

    ### Change description
    Delete all nodes and relationships related to the following studies:
    - 80_35_DELETE
    - 85_09_DELETE
    - 85_62_DELETE
    - 82_66_DELETE
    - 80_34_DELETE
    - 79_10_DELETE
    - 79_11_DELETE
    - 0030
    - 0050

    ### Nodes and relationships affected
    - All study nodes for the studies where the study number has a _DELETE:
    - Expected changes: ~2000 nodes deleted, ~5000 relationships deleted
    """

    desc = "Deleting unwanted studies from the database"
    log.info(f"Run: {run_label}, {desc}")

    unwanted = [
        "80_35_DELETE",
        "85_09_DELETE",
        "85_62_DELETE",
        "82_66_DELETE",
        "80_34_DELETE",
        "79_10_DELETE",
        "79_11_DELETE",
        "0030",
        "0050",
    ]
    any_did_update = False
    for study_number in unwanted:
        did_update = delete_unwanted_study(db_driver, log, run_label, study_number)
        any_did_update = any_did_update or did_update
    return any_did_update


@capture_changes(
    verify_func=correction_verification_014.test_remove_unwanted_sponsor_terms
)
def remove_unwanted_sponsor_terms(db_driver, log, run_label):
    """
    ## Remove three unwanted sponsor terms.

    ### Problem description
    The database contains a few sponsor terms that were added by mistake.
    The UIDs of the unwanted terms are:
    - CTTerm_001775
    - CTTerm_001776
    - CTTerm_001777

    ### Change Description
    The three unwanted terms need to be removed from the database,
    including all nodes and relationships related to these terms.

    ### Nodes and relationships affected
    - All nodes and relationships related to the unwanted terms are deleted:
      - Term root: `CTTermRoot`,
      - Term names: `CTTermNameRoot`, `CTTermNameValue`, `HAS_NAME_ROOT`, `HAS_VERSION`
      - Term attributes: `CTTermAttributesRoot`, `CTTermAttributesValue`, `HAS_ATTRIBUTES_ROOT`, `HAS_VERSION`
      - Term-codelist linking: `CTCodelistTerm`, `HAS_TERM`, `HAS_TERM_ROOT`
    - Expected changes: 26 nodes deleted, 44 relationships deleted
    """

    desc = "Remove unwanted sponsor terms in Finding Subcategory codelist"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (tnv:CTTermNameValue)<-[:HAS_VERSION]-(tnr:CTTermNameRoot)<-[:HAS_NAME_ROOT]-(tr:CTTermRoot)
            -[:HAS_ATTRIBUTES_ROOT]->(tar:CTTermAttributesRoot)-[:HAS_VERSION]->(tav:CTTermAttributesValue)
        WHERE tr.uid IN ["CTTerm_001775", "CTTerm_001776", "CTTerm_001777"]
        MATCH (tr)-[htr:HAS_TERM_ROOT]-(clt:CTCodelistTerm)
        DETACH DELETE tr, tar, tav, tnr, tnv, clt
        """,
    )

    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(verify_func=correction_verification_014.test_remove_dummy_definitions)
def remove_dummy_definitions(db_driver, log, run_label):
    """
    ## Remove dummy definitions from concept values

    ### Problem description
    Some concept values, such as activities, have dummy definitions.
    The definition field is optional, so these dummy definitions should be removed.


    ### Change Description
    Remove the dummy definitions from the affected concept values.

    ### Nodes and relationships affected
    - Concept value nodes (ActivityValue, UnitDefinitionValue etc.) with dummy definitions.
    """

    desc = "Remove dummy definitions from concept value nodes"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        f"""
        MATCH (root)-[:HAS_VERSION]->(value)
        WHERE value.definition is not null and (
            value.definition =~ "{correction_verification_014.NONSENSE_DEFINITION_REGEX}" OR
            value.definition IN {correction_verification_014.DUMMY_DEFINITIONS})
        REMOVE value.definition
        """,
    )

    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(
    verify_func=correction_verification_014.test_fix_baseline2_submission_values
)
def fix_baseline2_submission_values(db_driver, log, run_label):
    """
    ## Correct Baseline 2 Visit Type term

    ### Problem description
    The Baseline 2 term is linked twice to the VisitType codelist, due to a bug in the data migration
    for the new CT model in release 2.0.
    This needs to be corrected by setting an end date for the unwanted link.

    ### Change description
    - Look up the change date by getting the start date for version 1.3 of the term attributes.
    - Set an end date for the `HAS_TERM` relationship for the "BASELINE 2" submission value
    - Adjust the start date of the `HAS_TERM` relationship for the "BASELINE 2 VISIT TYPE" submission value.
    - Expected changes: 1 relationship property added, 1 modified
    """

    desc = "Correct Baseline 2 Visit Type term in Submission Values"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (clr:CTCodelistRoot)-[:HAS_NAME_ROOT]->(clnr:CTCodelistNameRoot)-[:LATEST]->(clnv:CTCodelistNameValue {name: "VisitType"})
        MATCH (clr)-[ht1:HAS_TERM]->(clt1:CTCodelistTerm {submission_value: "BASELINE 2"})-[htr1:HAS_TERM_ROOT]->(tr:CTTermRoot)
        MATCH (clr)-[ht2:HAS_TERM]->(clt2:CTCodelistTerm {submission_value: "BASELINE 2 VISIT TYPE"})-[htr2:HAS_TERM_ROOT]->(tr)
        WHERE ht1.end_date IS NULL AND ht2.end_date IS NULL
        WITH ht1, ht2, tr
        MATCH (tr)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[attr_hv:HAS_VERSION {version: "1.3"}]->(:CTTermAttributesValue)
        SET ht1.end_date = attr_hv.start_date
        SET ht2.start_date = attr_hv.start_date
        """,
    )

    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(
    verify_func=correction_verification_014.test_set_author_id_for_cdisc_data
)
def set_author_id_for_cdisc_data(db_driver, log, run_label):
    """
    ## Correct author id for CDISC data

    ### Problem description
    The new CDISC import script has imported the data using the old "user_intitals" property
    instead of the new "author_id" on `HAS_VERSION` relationships.
    On `HAS_TERM` relationships the field is missing completely.
    The author id for these should always be the "sb-import" user.

    ### Change description
    - Find the author id for the "sb-import" user
    - Add the id for this user in the `author_id` property on all `HAS_TERM` and `HAS_VERSION` relationships
      and `CTPackage` nodes where it is missing.
    - Remove all `user_initials` properties.

    ### Expected changes
    - approx. 200 000 properties updated
    """

    desc = "Correcting author_id for CDISC data"
    log.info(f"Run: {run_label}, {desc}")

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (u:User {username: "sb-import"})
        WITH u.user_id AS sb_import_user_id
        CALL {
            WITH sb_import_user_id
            // Update HAS_VERSION relationships
            MATCH ()-[hv:HAS_VERSION]->()
            WHERE hv.author_id IS NULL
            SET hv.author_id = sb_import_user_id
            REMOVE hv.user_initials
        }
        CALL {
            WITH sb_import_user_id
            // Update HAS_TERM relationships
            MATCH ()-[ht:HAS_TERM]->()
            WHERE ht.author_id IS NULL
            SET ht.author_id = sb_import_user_id
        }
        CALL {
            WITH sb_import_user_id
            // Update CTPackage nodes
            MATCH (ctp:CTPackage)
            WHERE ctp.author_id IS NULL
            SET ctp.author_id = sb_import_user_id
            REMOVE ctp.user_initials
        }
        """,
    )

    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(
    verify_func=correction_verification_014.test_multiple_null_value_reasons
)
def multiple_null_value_reasons(db_driver, log, run_label):
    """
    ## Correct selected term for null flavor reason

    ### Problem description
    The migration script for the new CT model mistakenly created a second `CTTermContext`
    node linked to a `StudyTextField` via a `HAS_REASON_FOR_NULL_VALUE` relationship.
    This links to a null value term in the wrong codelist, and should be removed.

    ### Change description
    - Find `StudyTextField` nodes with more than one `HAS_REASON_FOR_NULL_VALUE` relationships.
    - Remove the unwanted `HAS_REASON_FOR_NULL_VALUE` relationship and the corresponding `CTTermContext` node.
    - Expected changes: 1 node deleted, 3 relationships deleted.
    """

    desc = "Remove unwanted null value reason contexts"
    log.info(f"Run: {run_label}, {desc}")

    query = """
        MATCH (text_field:StudyTextField)-[:HAS_REASON_FOR_NULL_VALUE]->(context:CTTermContext)
        WITH text_field, collect(context) as ctxs
        WITH * WHERE size(ctxs)>1
        UNWIND ctxs AS context
        MATCH (context)-[:HAS_SELECTED_CODELIST]->(codelist:CTCodelistRoot)
        WHERE codelist.uid <> 'C150810'  // Codelist for Null Value Reasons
        DETACH DELETE context
    """
    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


if __name__ == "__main__":
    main()
