"""Schema migrations needed for release to PROD post June 2024."""

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
MIGRATION_DESC = "schema-migration-release-1.6.2"


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])

    ### Common migrations
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_ct_config_values(DB_CONNECTION, logger)

    ### Release-specific migrations
    migrate_study_activities_linked_to_deleted_soa_group(
        DB_DRIVER, logger, MIGRATION_DESC
    )
    migrate_remove_soa_group_node_without_any_study_activities(
        DB_DRIVER,
        logger,
    )
    migrate_soa_group_edit_performed_in_wrong_way(DB_DRIVER, logger, MIGRATION_DESC)
    migrate_study_selection_metadata_merge(DB_DRIVER, logger, MIGRATION_DESC)
    migrate_submit_and_reject_activity_requests(
        DB_DRIVER,
        logger,
    )


def migrate_study_activities_linked_to_deleted_soa_group(
    db_driver, log, migration_desc
):
    studies, _ = run_cypher_query(
        db_driver,
        """
        MATCH (study_root:StudyRoot) return study_root.uid
        """,
    )
    contains_updates = []
    for study in studies:
        study_uid = study[0]
        log.info(
            "Creating new StudySoAGroup for StudyActivities linked to a deleted StudySoAGroup in the following Study (%s)",
            study_uid,
        )
        _, summary = run_cypher_query(
            db_driver,
            """
            MATCH (study_root:StudyRoot {uid:$study_uid})--(:StudyValue)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->
                (study_soa_group:StudySoAGroup)-[:AFTER]-(delete:StudyAction:Delete)
            MATCH (study_soa_group)-[:HAS_FLOWCHART_GROUP]->(flowchart_group_term:CTTermRoot)
            WITH DISTINCT study_root, study_soa_group, flowchart_group_term

            // CREATE new StudySoAGroup node for each row of a distinct deleted study_soa_group which is linked to current StudyActivities
        
            CREATE (study_soa_group_new:StudySoAGroup:StudySelectionMetadata)
            MERGE (study_soa_group_counter:Counter {counterId:'StudySoAGroupCounter'})
            ON CREATE SET study_soa_group_counter:StudySoAGroupCounter, study_soa_group_counter.count=1
            WITH study_root, study_soa_group, flowchart_group_term,study_soa_group_new,study_soa_group_counter
            CALL apoc.atomic.add(study_soa_group_counter,'count',1,1) yield oldValue, newValue
            WITH study_root, study_soa_group, flowchart_group_term,study_soa_group_new, toInteger(newValue) as uid_number_study_sog
            SET study_soa_group_new.uid = "StudySoAGroup_"+apoc.text.lpad(""+(uid_number_study_sog), 6, "0")
            WITH study_root, study_soa_group, flowchart_group_term, study_soa_group_new
            SET study_soa_group_new.show_soa_group_in_protocol_flowchart = study_soa_group.show_soa_group_in_protocol_flowchart

            // MERGE newly create StudySoAGroup node with distinct flowchart_group_term
            MERGE (study_soa_group_new)-[:HAS_FLOWCHART_GROUP]->(flowchart_group_term)
            // MERGE audit-trail entry for the newly create StudySoAGroup node that will be reused
            MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:$migration_desc, date:datetime()})-[:AFTER]->(study_soa_group_new)

            WITH *
            MATCH (study_activities_to_reassign:StudyActivity)-[old_rel:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group)
            MERGE (study_activities_to_reassign)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group_new)

            WITH old_rel, study_soa_group, study_soa_group_new,
            apoc.coll.toSet([(study_soa_footnote:StudySoAFootnote)-[ref:REFERENCES_STUDY_SOA_GROUP]->(study_soa_group) | 
            study_soa_footnote]) as footnotes
            FOREACH (footnote in footnotes | MERGE (footnote)-[:REFERENCES_STUDY_SOA_GROUP]->(study_soa_group_new))
            DETACH DELETE old_rel
            """,
            params={"study_uid": study_uid, "migration_desc": migration_desc},
        )

        counters = summary.counters
        print_counters_table(counters)
        contains_updates.append(counters.contains_updates)
    return contains_updates


def migrate_remove_soa_group_node_without_any_study_activities(db_driver, log):
    log.info(
        "Cleanup StudySoAGroup node that are not linked to any StudyActivity in the following Study (%s)",
    )
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (study_soa_group:StudySoAGroup)-[:AFTER]-(study_action)
        WHERE 
            NOT (study_soa_group)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-(:StudyActivity) 
            AND NOT (study_soa_group)-[:BEFORE|AFTER]-(:Delete)
            AND NOT (study_soa_group)-[:BEFORE]-()
        DETACH DELETE study_soa_group, study_action
        """,
    )

    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


def migrate_soa_group_edit_performed_in_wrong_way(db_driver, log, migration_desc):
    studies, _ = run_cypher_query(
        db_driver,
        """
        MATCH (study_root:StudyRoot) return study_root.uid
        """,
    )
    contains_updates = []
    for study in studies:
        study_uid = study[0]
        log.info(
            "Fixing StudySoAGroup incorrect edit when we share SoAGroup nodes across different StudyActivities for the following Study (%s)",
            study_uid,
        )
        # StudySoAGroup
        _, summary = run_cypher_query(
            db_driver,
            """
        MATCH (study_root:StudyRoot {uid:$study_uid})-[:HAS_VERSION]->(study_value:StudyValue)-[:HAS_STUDY_ACTIVITY]->
            (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soa_group_before:StudySoAGroup)<-[:BEFORE]-(study_action:StudyAction)
        MATCH (soa_group_after:StudySoAGroup)<-[:AFTER]-(study_action)
        MATCH (soa_group_before)-[:HAS_FLOWCHART_GROUP]->(flowchart_term_before)
        MATCH (soa_group_after)-[:HAS_FLOWCHART_GROUP]->(flowchart_term_after)
        WHERE NOT study_action:Delete and flowchart_term_before <> flowchart_term_after
        WITH DISTINCT study_root, soa_group_before, flowchart_term_before
    
        CREATE (study_soa_group_new:StudySoAGroup:StudySelectionMetadata)
        MERGE (study_soa_group_counter:Counter {counterId:'StudySoAGroupCounter'})
        ON CREATE SET study_soa_group_counter:StudySoAGroupCounter, study_soa_group_counter.count=1
        WITH study_root, soa_group_before, flowchart_term_before,study_soa_group_new,study_soa_group_counter
        CALL apoc.atomic.add(study_soa_group_counter,'count',1,1) yield oldValue, newValue
        WITH study_root, soa_group_before, flowchart_term_before,study_soa_group_new, toInteger(newValue) as uid_number_study_sog
        SET study_soa_group_new.uid = "StudySoAGroup_"+apoc.text.lpad(""+(uid_number_study_sog), 6, "0")
        WITH study_root, soa_group_before, flowchart_term_before, study_soa_group_new
        SET study_soa_group_new.show_soa_group_in_protocol_flowchart = soa_group_before.show_soa_group_in_protocol_flowchart

        // MERGE newly create StudySoAGroup node with distinct flowchart_term_before
        MERGE (study_soa_group_new)-[:HAS_FLOWCHART_GROUP]->(flowchart_term_before)
        // MERGE audit-trail entry for the newly create StudySoAGroup node that will be reused
        MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:$migration_desc, date:datetime()})-[:AFTER]->(study_soa_group_new)

        WITH *
        MATCH (study_activities_to_reassign:StudyActivity)-[old_rel:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soa_group_before)
        MERGE (study_activities_to_reassign)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group_new)

        WITH old_rel, soa_group_before, study_soa_group_new,
        apoc.coll.toSet([(study_soa_footnote:StudySoAFootnote)-[ref:REFERENCES_STUDY_SOA_GROUP]->(soa_group_before) | 
        study_soa_footnote]) as footnotes
        FOREACH (footnote in footnotes | MERGE (footnote)-[:REFERENCES_STUDY_SOA_GROUP]->(study_soa_group_new))
        DETACH DELETE old_rel
        """,
            params={"study_uid": study_uid, "migration_desc": migration_desc},
        )
        counters = summary.counters
        print_counters_table(counters)
        contains_updates.append(counters.contains_updates)

        # StudyActivityGroup
        _, summary = run_cypher_query(
            db_driver,
            """
        MATCH (study_root:StudyRoot {uid:$study_uid})-[:HAS_VERSION]->(study_value:StudyValue)-[:HAS_STUDY_ACTIVITY]->
            (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(sa_group_before:StudyActivityGroup)<-[:BEFORE]-(study_action:StudyAction)
        MATCH (sa_group_after:StudyActivityGroup)<-[:AFTER]-(study_action)
        MATCH (sa_group_before)-[:HAS_SELECTED_ACTIVITY_GROUP]->(agv_before)
        MATCH (sa_group_after)-[:HAS_SELECTED_ACTIVITY_GROUP]->(agv_after)
        WHERE NOT study_action:Delete and agv_before <> agv_after
        WITH DISTINCT study_root, sa_group_before, agv_before
    
        CREATE (study_activity_group_new:StudyActivityGroup:StudySelectionMetadata)
        MERGE (study_activity_group_counter:Counter {counterId:'StudyActivityGroupCounter'})
        ON CREATE SET study_activity_group_counter:StudyActivityGroupCounter, study_activity_group_counter.count=1
        WITH study_root, sa_group_before, agv_before,study_activity_group_new,study_activity_group_counter
        CALL apoc.atomic.add(study_activity_group_counter,'count',1,1) yield oldValue, newValue
        WITH study_root, sa_group_before, agv_before,study_activity_group_new, toInteger(newValue) as uid_number_study_sag
        SET study_activity_group_new.uid = "StudyActivityGroup_"+apoc.text.lpad(""+(uid_number_study_sag), 6, "0")
        WITH study_root, sa_group_before, agv_before, study_activity_group_new
        SET study_activity_group_new.show_activity_group_in_protocol_flowchart = sa_group_before.show_activity_group_in_protocol_flowchart

        // MERGE newly create StudyActivityGroup node with ActivityGroup that was used before
        MERGE (study_activity_group_new)-[:HAS_SELECTED_ACTIVITY_GROUP]->(agv_before)
        // MERGE audit-trail entry for the newly create StudyActivityGroup node that will be reused
        MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:$migration_desc, date:datetime()})-[:AFTER]->(study_activity_group_new)

        WITH *
        MATCH (study_activities_to_reassign:StudyActivity)-[old_rel:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(sa_group_before)
        MERGE (study_activities_to_reassign)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_new)

        WITH old_rel, sa_group_before, study_activity_group_new,
        apoc.coll.toSet([(study_ag_footnote:StudySoAFootnote)-[ref:REFERENCES_STUDY_ACTIVITY_GROUP]->(sa_group_before) | 
        study_ag_footnote]) as footnotes
        FOREACH (footnote in footnotes | MERGE (footnote)-[:REFERENCES_STUDY_ACTIVITY_GROUP]->(study_activity_group_new))
        DETACH DELETE old_rel
        """,
            params={"study_uid": study_uid, "migration_desc": migration_desc},
        )
        counters = summary.counters
        print_counters_table(counters)
        contains_updates.append(counters.contains_updates)

        # StudyActivitySubGroup
        _, summary = run_cypher_query(
            db_driver,
            """
        MATCH (study_root:StudyRoot {uid:$study_uid})-[:HAS_VERSION]->(study_value:StudyValue)-[:HAS_STUDY_ACTIVITY]->
            (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(sa_subgroup_before:StudyActivitySubGroup)<-[:BEFORE]-(study_action:StudyAction)
        MATCH (sa_subgroup_after:StudyActivitySubGroup)<-[:AFTER]-(study_action)
        MATCH (sa_subgroup_before)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(asgv_before)
        MATCH (sa_subgroup_after)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(asgv_after)
        WHERE NOT study_action:Delete and asgv_before <> asgv_after
        WITH DISTINCT study_root, sa_subgroup_before, asgv_before
    
        CREATE (study_activity_subgroup_new:StudyActivitySubGroup:StudySelectionMetadata)
        MERGE (study_activity_subgroup_counter:Counter {counterId:'StudyActivitySubGroupCounter'})
        ON CREATE SET study_activity_subgroup_counter:StudyActivitySubGroupCounter, study_activity_subgroup_counter.count=1
        WITH study_root, sa_subgroup_before, asgv_before,study_activity_subgroup_new,study_activity_subgroup_counter
        CALL apoc.atomic.add(study_activity_subgroup_counter,'count',1,1) yield oldValue, newValue
        WITH study_root, sa_subgroup_before, asgv_before,study_activity_subgroup_new, toInteger(newValue) as uid_number_study_sasg
        SET study_activity_subgroup_new.uid = "StudyActivitySubGroup_"+apoc.text.lpad(""+(uid_number_study_sasg), 6, "0")
        WITH study_root, sa_subgroup_before, asgv_before, study_activity_subgroup_new
        SET study_activity_subgroup_new.show_activity_subgroup_in_protocol_flowchart = sa_subgroup_before.show_activity_subgroup_in_protocol_flowchart

        // MERGE newly create StudyActivitySubGroup node with ActivitySubGroup that was used before
        MERGE (study_activity_subgroup_new)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(asgv_before)
        // MERGE audit-trail entry for the newly create StudyActivitySubGroup node that will be reused
        MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:$migration_desc, date:datetime()})-[:AFTER]->(study_activity_subgroup_new)

        WITH *
        MATCH (study_activities_to_reassign:StudyActivity)-[old_rel:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(sa_subgroup_before)
        MERGE (study_activities_to_reassign)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_new)

        WITH old_rel, sa_subgroup_before, study_activity_subgroup_new,
        apoc.coll.toSet([(study_asg_footnote:StudySoAFootnote)-[ref:REFERENCES_STUDY_ACTIVITY_SUBGROUP]->(sa_subgroup_before) | 
        study_asg_footnote]) as footnotes
        FOREACH (footnote in footnotes | MERGE (footnote)-[:REFERENCES_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_new))
        DETACH DELETE old_rel
        """,
            params={"study_uid": study_uid, "migration_desc": migration_desc},
        )
        counters = summary.counters
        print_counters_table(counters)
        contains_updates.append(counters.contains_updates)
    return contains_updates


def migrate_study_selection_metadata_merge(db_driver, log, migration_desc):
    studies, _ = run_cypher_query(
        db_driver,
        """
        MATCH (study_root:StudyRoot) return study_root.uid
        """,
    )
    contains_updates = []
    for study in studies:
        study_uid = study[0]
        log.info(
            "Merging StudyMetadataSelection nodes for the following Study (%s)",
            study_uid,
        )
        # StudySoAGroup
        _, summary = run_cypher_query(
            db_driver,
            """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[]->(study_value:StudyValue)
            WITH DISTINCT study_root, study_value
            MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->
                (study_soa_group:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(flowchart_group_term_root:CTTermRoot)
            WHERE NOT (study_soa_group)<-[:BEFORE]-() AND NOT (study_soa_group)<-[]-(:Delete)
            WITH  
                flowchart_group_term_root,
                count(distinct flowchart_group_term_root) AS distinct_flowchart_group_count, 
                count(distinct study_soa_group) AS distinct_study_soa_group_count
            // condition to not perform migration twice
            WHERE distinct_flowchart_group_count <> distinct_study_soa_group_count

            // leave only a few rows that will represent distinct CTTermRoots that represent chosen SoA/Flowchart group
            WITH DISTINCT flowchart_group_term_root

            // CREATE new StudySoAGroup node for each row of a distinct flowchart_group_term_root 
            CREATE (study_soa_group_new:StudySoAGroup:StudySelectionMetadata)
            MERGE (study_soa_group_counter:Counter {counterId:'StudySoAGroupCounter'})
            ON CREATE SET study_soa_group_counter:StudySoAGroupCounter, study_soa_group_counter.count=1
            WITH flowchart_group_term_root,study_soa_group_new,study_soa_group_counter
            CALL apoc.atomic.add(study_soa_group_counter,'count',1,1) yield oldValue, newValue
            WITH flowchart_group_term_root,study_soa_group_new, toInteger(newValue) as uid_number_study_sog
            SET study_soa_group_new.uid = "StudySoAGroup_"+apoc.text.lpad(""+(uid_number_study_sog), 6, "0")
            WITH flowchart_group_term_root, study_soa_group_new

            // MATCH all StudyActivity nodes that had 'old' StudySoAGroups that were using a flowchart_group_term_root
            MATCH (flowchart_group_term_root)<-[:HAS_FLOWCHART_GROUP]-(study_soa_group_to_reassign)<-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-
                (study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value)--(study_root:StudyRoot {uid:$study_uid})
            WITH *
            ORDER BY study_activity.order ASC
            WHERE NOT (study_soa_group_to_reassign)<-[:BEFORE]-() AND NOT (study_soa_group_to_reassign)<-[]-(:Delete)

            // MERGE audit-trail entry for the newly create StudySoAGroup node that will be reused
            MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:$migration_desc, date:datetime()})-[:AFTER]->(study_soa_group_new)

            // MERGE StudyActivity node with new StudySoAGroup node that will be reused between different StudyActivities
            MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group_new)
            WITH *
            CALL apoc.do.case([
                study_soa_group_new.show_soa_group_in_protocol_flowchart IS NULL,
                'SET study_soa_group_new.show_soa_group_in_protocol_flowchart = coalesce(study_activity.show_soa_group_in_protocol_flowchart, false) RETURN *'
                ],
                'RETURN *',
                {
                    study_soa_group_new: study_soa_group_new,
                    study_activity:study_activity
                })
            YIELD value

            // MERGE newly create StudySoAGroup node with distinct flowchart_group_term_root
            MERGE (study_soa_group_new)-[:HAS_FLOWCHART_GROUP]->(flowchart_group_term_root)

            WITH study_soa_group_new, study_soa_group_to_reassign,

            // Copy StudySoAFootnotes relationships from the old StudySoAGroup nodes
            apoc.coll.toSet([(study_soa_footnote:StudySoAFootnote)-[ref:REFERENCES_STUDY_SOA_GROUP]->(study_soa_group_to_reassign) | 
            study_soa_footnote]) as footnotes
            FOREACH (footnote in footnotes | MERGE (footnote)-[:REFERENCES_STUDY_SOA_GROUP]->(study_soa_group_new))
            WITH study_soa_group_to_reassign, study_soa_group_new
            MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group_to_reassign)
            MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group_new)
            DETACH DELETE study_soa_group_to_reassign
            """,
            params={"study_uid": study_uid, "migration_desc": migration_desc},
        )
        counters = summary.counters
        print_counters_table(counters)
        contains_updates.append(counters.contains_updates)

        # StudyActivityGroup
        _, summary = run_cypher_query(
            db_driver,
            """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[]->(study_value:StudyValue)
            WITH DISTINCT study_root, study_value
            MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->
                (study_activity_group:StudyActivityGroup)-[:HAS_SELECTED_ACTIVITY_GROUP]->(:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot)
            MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
            WHERE NOT (study_activity_group)<-[:BEFORE]-() AND NOT (study_activity_group)<-[]-(:Delete)

            WITH DISTINCT
                activity_group_root,
                study_soa_group,
                collect(distinct activity_group_root) AS distinct_activity_group_root, 
                collect(distinct study_activity_group) AS distinct_study_activity_group
            // condition to not perform migration twice
            WHERE size(distinct_activity_group_root) <> size(distinct_study_activity_group)

            // leave only a few rows that will represent distinct ActivityGroups in a specific StudySoAGroup
            WITH DISTINCT activity_group_root, study_soa_group

            // CREATE new StudyActivityGroup node for each row of a distinct activity_group_root 
            CREATE (study_activity_group_new:StudyActivityGroup:StudySelectionMetadata)
            MERGE (study_activity_group_counter:Counter {counterId:'StudyActivityGroupCounter'})
            ON CREATE SET study_activity_group_counter:StudyActivityGroupCounter, study_activity_group_counter.count=1
            WITH activity_group_root,study_soa_group, study_activity_group_new,study_activity_group_counter
            CALL apoc.atomic.add(study_activity_group_counter,'count',1,1) yield oldValue, newValue
            WITH activity_group_root, study_soa_group, study_activity_group_new, toInteger(newValue) as uid_number_study_sag
            SET study_activity_group_new.uid = "StudyActivityGroup_"+apoc.text.lpad(""+(uid_number_study_sag), 6, "0")
            WITH activity_group_root, study_soa_group, study_activity_group_new

            // MATCH all StudyActivity nodes that had 'old' StudyActivityGroup inside specific StudySoAGroup that were using a activity_group_root
            MATCH (activity_group_root)-[:HAS_VERSION]->(:ActivityGroupValue)<-[:HAS_SELECTED_ACTIVITY_GROUP]-(study_activity_group_to_reassign)
                <-[old_rel:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(study_activity:StudyActivity)
                <-[:HAS_STUDY_ACTIVITY]-(study_value)--(study_root:StudyRoot {uid:$study_uid})
            WITH *
            ORDER BY study_activity.order ASC
            MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group)

            // MERGE audit-trail entry for the newly create StudyActivityGroup node that will be reused
            MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:$migration_desc, date:datetime()})-[:AFTER]->(study_activity_group_new)

            // MERGE StudyActivity node with new StudyActivityGroup node that will be reused between different StudyActivities inside same StudySoAGroup
            MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_new)
            WITH *
            CALL apoc.do.case([
                study_activity_group_new.show_activity_group_in_protocol_flowchart IS NULL,
                'SET study_activity_group_new.show_activity_group_in_protocol_flowchart = study_activity.show_activity_group_in_protocol_flowchart RETURN *'
                ],
                'RETURN *',
                {
                    study_activity_group_new: study_activity_group_new,
                    study_activity:study_activity
                })
            YIELD value

            // MERGE newly create StudyActivityGroup node with distinct activity_group_value
            MATCH (activity_group_root)-[:LATEST]->(latest_activity_group_value:ActivityGroupValue)
            MERGE (study_activity_group_new)-[:HAS_SELECTED_ACTIVITY_GROUP]->(latest_activity_group_value)

            WITH study_activity_group_new, study_activity_group_to_reassign, study_activity, old_rel,

            // Copy StudySoAFootnotes relationships from the old StudyActivityGroup nodes
            apoc.coll.toSet([(study_soa_footnote:StudySoAFootnote)-[ref:REFERENCES_STUDY_ACTIVITY_GROUP]->(study_activity_group_to_reassign) | 
            study_soa_footnote]) as footnotes
            FOREACH (footnote in footnotes | MERGE (footnote)-[:REFERENCES_STUDY_ACTIVITY_GROUP]->(study_activity_group_new))
            WITH study_activity_group_to_reassign, study_activity_group_new, study_activity, old_rel
            MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_new)
            DETACH DELETE old_rel
            """,
            params={"study_uid": study_uid, "migration_desc": migration_desc},
        )
        counters = summary.counters
        print_counters_table(counters)
        contains_updates.append(counters.contains_updates)

        # StudyActivitySubGroup
        _, summary = run_cypher_query(
            db_driver,
            """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[]->(study_value:StudyValue)
            WITH DISTINCT study_root, study_value
            MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->
                (study_activity_subgroup:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot)
            MATCH (study_activity_group:StudyActivityGroup)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(study_activity)
                -[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
            WHERE NOT (study_activity_subgroup)<-[:BEFORE]-() AND NOT (study_activity_subgroup)<-[]-(:Delete)

            WITH DISTINCT
                activity_subgroup_root,
                study_activity_group,
                study_soa_group,
                collect(distinct activity_subgroup_root) AS distinct_activity_subgroup_root, 
                collect(distinct study_activity_subgroup) AS distinct_study_activity_subgroup
            // condition to not perform migration twice
            WHERE size(distinct_activity_subgroup_root) <> size(distinct_study_activity_subgroup)
            // leave only a few rows that will represent distinct ActivitySubGroups in a specific StudySoAGroup and StudyActivityGroup
            WITH DISTINCT activity_subgroup_root, study_soa_group, study_activity_group

            // CREATE new StudyActivitySubGroup node for each row of a distinct activity_subgroup_root 
            CREATE (study_activity_subgroup_new:StudyActivitySubGroup:StudySelectionMetadata)
            MERGE (study_activity_subgroup_counter:Counter {counterId:'StudyActivitySubGroupCounter'})
            ON CREATE SET study_activity_subgroup_counter:StudyActivitySubGroupCounter, study_activity_subgroup_counter.count=1
            WITH activity_subgroup_root, study_soa_group, study_activity_group, study_activity_subgroup_new,study_activity_subgroup_counter
            CALL apoc.atomic.add(study_activity_subgroup_counter,'count',1,1) yield oldValue, newValue
            WITH activity_subgroup_root, study_soa_group, study_activity_group, study_activity_subgroup_new, toInteger(newValue) as uid_number_study_sasg
            SET study_activity_subgroup_new.uid = "StudyActivitySubGroup_"+apoc.text.lpad(""+(uid_number_study_sasg), 6, "0")
            WITH activity_subgroup_root, study_soa_group, study_activity_group, study_activity_subgroup_new

            // MATCH all StudyActivity nodes that had 'old' StudyActivitySubGroup inside specific StudySoAGroup and StudyActivityGroup
            MATCH (activity_subgroup_root)-[:HAS_VERSION]->(:ActivitySubGroupValue)<-[:HAS_SELECTED_ACTIVITY_SUBGROUP]-(study_activity_subgroup_to_reassign)
                <-[old_rel:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]-(study_activity:StudyActivity)
                <-[:HAS_STUDY_ACTIVITY]-(study_value)--(study_root:StudyRoot {uid:$study_uid})
            WITH *
            ORDER BY study_activity.order ASC
            MATCH (study_activity_group)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(study_activity)
                -[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group)

            // MERGE audit-trail entry for the newly create StudyActivitySubGroup node that will be reused
            MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:$migration_desc, date:datetime()})-[:AFTER]->(study_activity_subgroup_new)

            // MERGE StudyActivity node with new StudyActivitySubGroup node that will be reused between different StudyActivities inside same StudySoAGroup and StudyActivityGroup
            MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_new)
            WITH *
            CALL apoc.do.case([
                study_activity_subgroup_new.show_activity_subgroup_in_protocol_flowchart IS NULL,
                'SET study_activity_subgroup_new.show_activity_subgroup_in_protocol_flowchart = study_activity.show_activity_subgroup_in_protocol_flowchart RETURN *'
                ],
                'RETURN *',
                {
                    study_activity_subgroup_new: study_activity_subgroup_new,
                    study_activity:study_activity
                })
            YIELD value

            // MERGE newly create StudyActivitySubGroup node with distinct activity_subgroup_value
            MATCH (activity_subgroup_root)-[:LATEST]->(latest_activity_subgroup_value:ActivitySubGroupValue)
            MERGE (study_activity_subgroup_new)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(latest_activity_subgroup_value)

            WITH study_activity_subgroup_new, study_activity_subgroup_to_reassign, study_activity, old_rel,
            // Copy StudySoAFootnotes relationships from the old StudyActivitySubGroup nodes
            apoc.coll.toSet([(study_soa_footnote:StudySoAFootnote)-[ref:REFERENCES_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_to_reassign) | 
            study_soa_footnote]) as footnotes
            FOREACH (footnote in footnotes | MERGE (footnote)-[:REFERENCES_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_new))
            WITH study_activity_subgroup_to_reassign, study_activity_subgroup_new, study_activity, old_rel
            MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_new)
            DETACH DELETE old_rel
            """,
            params={"study_uid": study_uid, "migration_desc": migration_desc},
        )
        counters = summary.counters
        print_counters_table(counters)
        contains_updates.append(counters.contains_updates)

    return contains_updates


def migrate_submit_and_reject_activity_requests(db_driver, log):
    log.info(
        "Initialize submit property for all ActivityRequests",
    )
    _, submit_summary = run_cypher_query(
        db_driver,
        """
        MATCH (activity_request_root:ActivityRoot)-[:LATEST]->(activity_request_value:ActivityValue)
        // Submit all ActivityRequests
        WHERE (activity_request_root)<-[:CONTAINS_CONCEPT]-(:Library {name:'Requested'}) AND (activity_request_value.is_request_final <> true OR activity_request_value.is_request_final IS NULL)
        SET activity_request_value.is_request_final = true
        """,
    )
    submit_counters = submit_summary.counters
    print_counters_table(submit_counters)

    log.info(
        "Initialize rejection property for all ActivityRequests",
    )
    _, submit_summary = run_cypher_query(
        db_driver,
        """
        MATCH (activity_request_root:ActivityRoot)-[:LATEST]->(activity_request_value:ActivityValue)
        // Submit all ActivityRequests
        WHERE (activity_request_root)<-[:CONTAINS_CONCEPT]-(:Library {name:'Requested'}) AND activity_request_value.is_request_rejected IS NULL
        SET activity_request_value.is_request_rejected = false
        """,
    )
    submit_counters = submit_summary.counters
    print_counters_table(submit_counters)

    log.info(
        "Rejecting retired ActivityRequests that are not having any Sponsor Activity created out of it",
    )
    _, reject_summary = run_cypher_query(
        db_driver,
        """
        MATCH (activity_request_root:ActivityRoot)-[retired:LATEST_RETIRED]->(activity_request_value:ActivityValue)
        // Reject those that are in Retired state and don't have Sponsor Activity created out of them
        WHERE (activity_request_root)<-[:CONTAINS_CONCEPT]-(:Library {name:'Requested'}) 
            AND retired.end_date IS NULL AND NOT (activity_request_value)-[:REPLACED_BY_ACTIVITY]->(:ActivityRoot)
            AND activity_request_value.is_request_rejected <> true
        SET activity_request_value.is_request_rejected = true
        """,
    )
    reject_counters = reject_summary.counters
    print_counters_table(reject_counters)
    return submit_counters.contains_updates or reject_counters.contains_updates


if __name__ == "__main__":
    main()
