"""Schema migrations needed for release to PROD post May/June 2023."""

import os
import re

from migrations.common import migrate_ct_config_values, migrate_indexes_and_constraints
from migrations.utils.utils import get_db_connection, get_logger

logger = get_logger(os.path.basename(__file__))
DB_CONNECTION = get_db_connection()


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])

    ### Common migrations
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_ct_config_values(DB_CONNECTION, logger)

    ### Release-specific migrations

    # StudySelections labels to add StudySelection label and to delete OrderedStudySelection label
    migrate_study_selection_labels(DB_CONNECTION)

    # StudySelections labels to add the last deleted node if there's none, and to maintain the required relationships between StudySelections.
    migrate_study_selection_deletion_and_maintain_dropped_and_switched_rels(
        DB_CONNECTION
    )

    # StudySelections to the StudyActivitySchedule to be cascade deleted if there's a StudyVisit deleted
    migrate_study_selection_cascade_delete(DB_CONNECTION)

    migrate_refinement_of_syntax_sequence_id(DB_CONNECTION)

    # migrate new ActivityGrouping hierarchy and remove old relationships
    migrate_activity_groupings(DB_CONNECTION)
    migrate_activities(DB_CONNECTION)

    # migrate StudYActivitySubGroup and StudyActivityGroup
    migrate_study_activity_subgroup_and_group(DB_CONNECTION)

    # migrate SimpleConceptValue to be linked to a single SimpleConceptRoot
    migrate_simple_concept_value_nodes(DB_CONNECTION)


def maintain_relationships_query(db_connection):
    logger.info("Migrating - Maintaining relationships")
    result, _ = db_connection.cypher_query("""
        MATCH (ss1_init:StudySelection)<-[required_rel]-(ss2_init:StudySelection)
        WITH DISTINCT ss1_init.uid as ss1_uid, TYPE(required_rel) AS required_rel_type, ss2_init.uid as ss2_uid
        WHERE TYPE(required_rel) IN [
            "STUDY_EPOCH_HAS_STUDY_VISIT",
            "STUDY_VISIT_HAS_SCHEDULE",
            "STUDY_EPOCH_HAS_DESIGN_CELL",
            "STUDY_ACTIVITY_HAS_SCHEDULE", 
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
                WITH ss1_group_collected
                UNWIND ss1_group_collected as ss1_group

                MATCH (ss1_group)<-[:AFTER]-(ss1_group_after_saction:StudyAction)
                OPTIONAL MATCH (ss1_group)<-[:BEFORE]-(ss1_saction:StudyAction)
                WITH ss1_group_after_saction.date AS ss1_group_start_date, ss1_group, ss1_group_after_saction,
                CASE 
                    WHEN ss1_saction IS NULL AND NOT ss1_group_after_saction:Delete then datetime({epochMillis: apoc.date.currentTimestamp()})
                    WHEN ss1_saction IS NULL AND ss1_group_after_saction:Delete then ss1_group_after_saction.date
                    ELSE ss1_saction.date
                END AS ss1_group_end_date
                RETURN DISTINCT ss1_group_start_date, ss1_group, ss1_group_end_date, ss1_group_after_saction
            }
            // Extract all ss2 before and after date
            CALL{
                WITH  ss2_group_collected
                UNWIND ss2_group_collected as ss2_group

                MATCH (ss2_group)<-[:AFTER]-(ss2_group_after_saction:StudyAction)
                OPTIONAL MATCH (ss2_group)<-[:BEFORE]-(ss2_saction:StudyAction)
                WITH *, ss2_group_after_saction.date AS ss2_group_start_date, ss2_group, ss2_group_after_saction,
                CASE 
                    WHEN ss2_saction IS NULL AND NOT ss2_group_after_saction:Delete then datetime({epochMillis: apoc.date.currentTimestamp()})
                    WHEN ss2_saction IS NULL AND ss2_group_after_saction:Delete then ss2_group_after_saction.date
                    ELSE ss2_saction.date
                END AS ss2_group_end_date
                RETURN DISTINCT ss2_group_start_date, ss2_group, ss2_group_end_date, ss2_group_after_saction

            }
            WITH ss1_group_start_date, ss1_group, ss1_group_end_date, ss1_group_after_saction, ss2_group_start_date, ss2_group, ss2_group_end_date, ss2_group_after_saction, required_rel_type
            // Extract all ss2 before and after date
            FOREACH( _ in CASE WHEN ss1_group_start_date>ss2_group_start_date AND ss1_group_start_date<ss2_group_end_date AND NOT EXISTS((ss1_group)--(ss2_group))  THEN [true] END | MERGE (ss1_group)<-[:REQ1
            ]-(ss2_group))
            FOREACH( _ in CASE WHEN ss2_group_start_date>ss1_group_start_date AND ss2_group_start_date<ss1_group_end_date AND NOT EXISTS((ss1_group)--(ss2_group))  THEN [true] END | MERGE (ss1_group)<-[:REQ2
            ]-(ss2_group))
            WITH required_rel_type
            MATCH ()-[new_rel:REQ1|REQ2]-()
            CALL apoc.refactor.setType(new_rel, required_rel_type)//  "TEMPORAL") //
            YIELD input, output
            RETURN output
        }
        WITH TYPE(output) as output_type, ss1_uid,ss2_uid
        WHERE output IS NOT NULL
        RETURN *
        """)
    logger.info("Output - relationshisp maintained %s", result)


def migrate_study_selection_labels(db_connection):
    logger.info(
        "Migrating Study Selections to have StudySelection label on them and delete OrderedStudySelection labels on the Study Selections who has it"
    )
    _result, _ = db_connection.cypher_query("""
        MATCH (n)
        WHERE n:StudyActivitySchedule OR n:StudyActivityInstruction OR n:StudyDesignCell OR n:StudyEpoch OR n:StudyDiseaseMilestone
        WITH n
        CALL apoc.do.case([
            n:StudyActivitySchedule and not n:StudySelection,
            'SET n:StudySelection',

            n:StudyActivityInstruction and not n:StudySelection,
            'SET n:StudySelection',

            n:StudyDesignCell and not n:StudySelection,
            'SET n:StudySelection',

            n:StudyEpoch and n:OrderedStudySelection,
            'REMOVE n:OrderedStudySelection',

            n:StudyDiseaseMilestone and n:OrderedStudySelection,
            'REMOVE n:OrderedStudySelection'
        ],
        '',
        {
            n: n
        })
        YIELD value
        RETURN *
        """)


def migrate_study_selection_deletion_and_maintain_dropped_and_switched_rels(
    db_connection,
):
    logger.info(
        "Migrating - Fixing bad deletions on Visit, Epoch, ActivitySchedule, ActivityInstruction, but dropping relationships on delete after version will be maintained afterwards"
    )
    result, _ = db_connection.cypher_query("""
        // MATCH BAD DELETED StudySelection
        MATCH (del:Delete)-[ss_del]-(ss)
        WHERE NOT ss:StudyRoot AND
            (ss:StudySelection)
        WITH del,collect(DISTINCT ss) as ss_collected , COUNT(DISTINCT ss) AS count_ss_del
        WHERE count_ss_del<2

        //  CLONE NODE
        CALL apoc.refactor.cloneNodes(
        ss_collected,
        true //clone with relationships
        ) YIELD input, output, error
        //GET input nodes
        MATCH (ss_old) WHERE ID(ss_old)= input 
        
        //DISCONNECT NEW NODE
        MATCH (output)-[output_saction]-(saction:StudyAction) // Delete from previous StudyAction, as previous action shouldn't be connected to the new one
        OPTIONAL MATCH (output)-[output_sv]-(:StudyValue)    // Delete StudyValue, because is being deleted
        OPTIONAL MATCH (output)-[output_ss]-(:StudySelection) //Drop all StudySelections relationships, because later will be maintained
        //DISCONNECT OLD NODE
        OPTIONAL MATCH (ss_old)-[ss_old_del:AFTER]-(del)   // From Delete node After rel
        OPTIONAL MATCH (ss_old)-[ss_old_sv]-(:StudyValue)  //From studyValue

        //DISCONNECT NEW
        DELETE output_saction
        DELETE output_sv
        DELETE output_ss
       
        MERGE (output)<-[:AFTER]-(del)

        //DISCONNECT OLD NODE
        DELETE ss_old_del
        DELETE ss_old_sv

        RETURN DISTINCT output.uid
        """)
    logger.info("Output - SS Migrated %s", result)
    maintain_relationships_query(db_connection=db_connection)


def migrate_study_selection_cascade_delete(db_connection):
    logger.info(
        "Migrating - StudyActivitySchedule Cascade Deletion when Study Visit is deleted, leave the last node as dropped relationship, will be maintained afterwards"
    )
    result, _ = db_connection.cypher_query("""

        Match (sr:StudyRoot)--(:StudyValue)--(se:StudyActivitySchedule)
        OPTIONAL MATCH (pre_svis_saction:Delete)-[:AFTER]-(pre_svis:StudyVisit)--(se)
            WHERE NOT EXISTS((pre_svis)--(:StudyValue)) 
        OPTIONAL MATCH (se)--(pre_sactivity:StudyActivity)-[:AFTER]-(pre_sactivity_saction:Delete)
            WHERE NOT EXISTS((pre_sactivity)--(:StudyValue))
        with collect(distinct se) as se_collected, sr,
            CASE 
                WHEN pre_svis_saction.date>pre_sactivity_saction.date then "StudyActivity"
                WHEN pre_svis_saction.date<pre_sactivity_saction.date then "StudyVisit"
                WHEN pre_svis_saction IS NOT NULL then "StudyVisit"
                WHEN pre_sactivity_saction IS NOT NULL then "StudyActivity"
                ELSE NULL
            end as cascade_delete_selected
        WHERE 
            cascade_delete_selected IS NOT NULL
        CALL apoc.refactor.cloneNodes(
            se_collected,
            true //clone with relationships
        ) YIELD input, output, error
        MATCH (se_old) WHERE ID(se_old)= input // Extract old node by uid
        // get the delete StudyAction to extract the date when the StudySelection2 has been deleted
        MATCH (se_old)-[se_old_deleted_after_version]-(deleted_after_version)-[:AFTER]-(saction_ss2_delete:Delete) // Delete the first_version activity_schedule to the deleted StudySelection after version relationship, if it exists, because shouldn't have happened. 
            WHERE cascade_delete_selected in labels(deleted_after_version)
        
        // DETECT WHAT RELATIONSHIPS TO DELETE FROM OUTPUT (CLONED NODE)
        MATCH (output)-[output_saction]-(saction:StudyAction) // delete the cloned node connection to past saction
        MATCH (output)-[output_sv]-(:StudyValue) // delete the cloned node connection to study value
        OPTIONAL MATCH (output)-[output_ss_created_after_deletion]-(ss_created_after_deletion_conn_output:StudySelection)-[:AFTER]-(ss_created_after_deletion_conn_output_saction:StudyAction) // delete the cloned node connection to any other study selection made after the deletion
            WHERE ss_created_after_deletion_conn_output_saction.date>datetime({epochMillis: datetime(saction_ss2_delete.date).epochMillis -10})
        OPTIONAL MATCH (output)-[output_ss_deprecated_before_deletion]-(ss_deprecated_before_deletion_conn_output:StudySelection)-[:BEFORE]-(ss_deprecated_before_deletion_conn_output_saction:StudyAction) // delete the cloned node connection to any other study selection made after the deletion
            WHERE ss_deprecated_before_deletion_conn_output_saction.date<datetime({epochMillis: datetime(saction_ss2_delete.date).epochMillis -10})
        // DETECT WHAT RELATIONSHIPS TO DELETE FROM SE_OLD
        MATCH (se_old)-[se_old_sv]-(:StudyValue) // delete the old node connection to study value
        OPTIONAL MATCH (se_old)-[se_old_ss_created_after_deletion]-(ss_created_after_deletion_conn_se_old:StudySelection)-[:AFTER]-(ss_created_after_deletion_conn_output_saction:StudyAction) // delete the cloned node connection to any other study selection made after the deletion
            WHERE ss_created_after_deletion_conn_output_saction.date>datetime({epochMillis: datetime(saction_ss2_delete.date).epochMillis -10})

        //DISCONNECT OLD NODE (CLONED NODE)
        DELETE se_old_sv //disconnect from Study Value
        DELETE se_old_ss_created_after_deletion // disconnect from StudySelections made after the StudySelection2-10 milis datetime (shouldn't exists because should be deleted)
    
        //DISCONNECT NEW
        DELETE output_saction // delete the cloned node connection to past saction
        DELETE output_sv // delete the cloned node connection to study value
        DELETE output_ss_created_after_deletion // // disconnect from StudySelections made after the StudySelection2-10 milis datetime (shouldn't exists because should be deleted)
        DELETE output_ss_deprecated_before_deletion // disconnect from StudySelections that were deprecated before the Cascade Deletion because they weren't a live at the time of the deletion
        
        //CREATE EXTRA NODES FOR NEW NODE
        MERGE (sr)-[:AUDIT_TRAIL]->(sa:StudyAction:Delete{date:datetime({epochMillis: datetime(saction_ss2_delete.date).epochMillis -10}), user_initials:saction_ss2_delete.user_initials})-[:AFTER]->(output)   
        //CONNECT OLD NODE
        MERGE (sa)-[:BEFORE]->(se_old)
        RETURN DISTINCT output.uid
        """)
    logger.info("Output - nodes cascade deleted %s", result)

    maintain_relationships_query(db_connection=db_connection)


def migrate_activity_groupings(db_connection):
    logger.info(
        "Migrating ActivitySubGroups by adding ActivityValidGroups, and removing old relationships"
    )
    _result, _ = db_connection.cypher_query("""
            // ActivityValidGroups
            MATCH (activity_subgroup_value:ActivitySubGroupValue)-[in_group_hierarchy:IN_GROUP]->(activity_group_value:ActivityGroupValue)
            CREATE (activity_valid_group:ActivityValidGroup)
                MERGE (avg_counter:Counter {counterId:'ActivityValidGroupCounter'})
                ON CREATE SET avg_counter:ActivityValidGroupCounter, avg_counter.count=1
                WITH *
                CALL apoc.atomic.add(avg_counter,'count',1,1) yield oldValue, newValue
                WITH *, toInteger(newValue) as uid_number_avg
                SET activity_valid_group.uid = "ActivityValidGroup_"+apoc.text.lpad(""+(uid_number_avg), 6, "0")
            MERGE (activity_valid_group)<-[:HAS_GROUP]-(activity_subgroup_value)
            MERGE (activity_valid_group)-[:IN_GROUP]->(activity_group_value)
            DETACH DELETE in_group_hierarchy
        """)


def migrate_activities(db_connection):
    logger.info(
        "Migrating Activities by adding ActivityGroupings, and removing old relationships"
    )
    _result, _ = db_connection.cypher_query("""
            MATCH (activity_value:ActivityValue)-[old_in_sub_group_hierarchy:IN_SUB_GROUP]->(activity_subgroup_value:ActivitySubGroupValue)
                -[:HAS_GROUP]->(activity_valid_group:ActivityValidGroup)

            // ActivityGroupings
            CREATE (activity_grouping:ActivityGrouping)
                MERGE (ag_counter:Counter {counterId:'ActivityGroupingCounter'})
                ON CREATE SET ag_counter:ActivityGroupingCounter, ag_counter.count=1
                WITH *
                CALL apoc.atomic.add(ag_counter,'count',1,1) yield oldValue, newValue
                WITH *, toInteger(newValue) as uid_number_ag
                SET activity_grouping.uid = "ActivityGrouping_"+apoc.text.lpad(""+(uid_number_ag), 6, "0")
                
            MERGE (activity_value)-[:HAS_GROUPING]->(activity_grouping)
            MERGE (activity_grouping)-[:IN_SUBGROUP]->(activity_valid_group)
            DETACH DELETE old_in_sub_group_hierarchy

            WITH *
            MATCH (instance_value:ActivityInstanceValue)-[old_in_hierarchy:IN_HIERARCHY]->(activity_value)
            MERGE (instance_value)-[:HAS_ACTIVITY]->(activity_grouping)
            DETACH DELETE old_in_hierarchy
        """)


def migrate_refinement_of_syntax_sequence_id(db_connection):
    logger.info("Remove T of Template from sequence_id of SyntaxTemplate")
    regex = "(?<=[A-Z])T(?=\\d)"
    db_connection.cypher_query(f"""
        MATCH (n:SyntaxTemplateRoot)
        SET n.sequence_id = apoc.text.replace(n.sequence_id, '{regex}', '');
        """)
    logger.info("Remove T of Template from sequence_id of SyntaxPreInstance")
    db_connection.cypher_query(f"""
        MATCH (n:SyntaxPreInstanceRoot)
        SET n.sequence_id = apoc.text.replace(n.sequence_id, '{regex}', '');
        """)

    logger.info(
        "Make sequence_id of CriteriaTemplateRoot sequential within the criteria template type"
    )
    result = db_connection.cypher_query(
        "MATCH (n:CriteriaTemplateRoot) RETURN n.sequence_id"
    )

    criteria_templates: dict[str, list[str]] = {}
    for seq_id in result[0]:
        prefix = re.match("[a-zA-Z]*", seq_id[0]).group()
        criteria_templates.setdefault(prefix, []).append(seq_id[0])

    for prefix, seq_uids in criteria_templates.items():
        seq_uids.sort(key=lambda x, p=prefix: int(x.split(p)[1]))

        for idx, elm in enumerate(seq_uids, 1):
            db_connection.cypher_query(f"""
                MATCH (n:CriteriaTemplateRoot {{sequence_id: "{elm}"}})
                SET n.sequence_id = "{prefix}{idx}"
                """)

    logger.info(
        "Make sequence_id of CriteriaPreInstanceRoot sequential within the parent template"
    )
    result = db_connection.cypher_query(
        "MATCH (n:CriteriaPreInstanceRoot)-[:CREATED_FROM]->(t:SyntaxTemplateRoot) RETURN n.sequence_id, t.uid"
    )
    criteria_pre_instances: dict[str, list[str]] = {}
    for seq_id, t_uid in result[0]:
        criteria_pre_instances.setdefault(t_uid, []).append(seq_id)

    for t_uid, seq_uids in criteria_pre_instances.items():
        seq_uids.sort(key=lambda x: int(x.split("P")[1]))

        for idx, seq_id in enumerate(seq_uids, 1):
            prefix = re.match("[a-zA-Z]*\\d*P", seq_id).group()
            db_connection.cypher_query(f"""
                MATCH (n:CriteriaPreInstanceRoot {{sequence_id: "{seq_id}"}})
                SET n.sequence_id = "{prefix}{idx}"
                """)


def migrate_study_activity_subgroup_and_group(db_connection):
    logger.info("Migrating StudyActivitySubGroup and StudyActivityGroup nodes")
    _result, _ = db_connection.cypher_query("""
            MATCH (study_value:StudyValue)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)-[:HAS_SELECTED_ACTIVITY]->
                (activity_value:ActivityValue)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->
                (activity_valid_group:ActivityValidGroup)-[:IN_GROUP]->(activity_group_value:ActivityGroupValue)
            WITH *,
                head([(activity_valid_group)<-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue) | activity_subgroup_value ]) AS activity_subgroup_value,
                head([(study_root:StudyRoot)-[]->(study_value) | study_root]) AS study_root
            WHERE NOT (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(:StudyActivitySubGroup)
                -[:STUDY_ACTIVITY_SUBGROUP_HAS_STUDY_ACTIVITY_GROUP]->(:StudyActivityGroup)

            // StudyActivitySubGroup
            CREATE (study_activity_subgroup:StudyActivitySubGroup:StudySelection)
                MERGE (study_asg_counter:Counter {counterId:'StudyActivitySubGroupCounter'})
                ON CREATE SET study_asg_counter:StudyActivitySubGroupCounter, study_asg_counter.count=1
                WITH *
                CALL apoc.atomic.add(study_asg_counter,'count',1,1) yield oldValue, newValue
                WITH *, toInteger(newValue) as uid_number_study_asg
                SET study_activity_subgroup.uid = "StudyActivitySubGroup_"+apoc.text.lpad(""+(uid_number_study_asg), 6, "0")
            MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:"schema-migration", date:datetime()})-[:AFTER]->(study_activity_subgroup)
            MERGE (study_value)-[:HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup)
            MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup)
            MERGE (study_activity_subgroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value)

            WITH study_value, study_activity_subgroup, activity_group_value
            // StudyActivityGroup
            CREATE (study_activity_group:StudyActivityGroup:StudySelection)
                MERGE (study_ag_counter:Counter {counterId:'StudyActivityGroupCounter'})
                ON CREATE SET study_ag_counter:StudyActivityGroupCounter, study_ag_counter.count=1
                WITH *
                CALL apoc.atomic.add(study_ag_counter,'count',1,1) yield oldValue, newValue
                WITH *, toInteger(newValue) as uid_number_study_ag
                SET study_activity_group.uid = "StudyActivityGroup_"+apoc.text.lpad(""+(uid_number_study_ag), 6, "0")
            MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:"schema-migration", date:datetime()})-[:AFTER]->(study_activity_group)
            MERGE (study_value)-[:HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group)
            MERGE (study_activity_subgroup)-[:STUDY_ACTIVITY_SUBGROUP_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group)
            MERGE (study_activity_group)-[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value)
        """)


def migrate_simple_concept_value_nodes(db_connection):
    logger.info("Migrating SimpleConceptValue nodes")
    _result, _ = db_connection.cypher_query("""            
            MATCH (n:SimpleConceptRoot)-[:HAS_VERSION]->(m:SimpleConceptValue)
            WITH m, apoc.coll.sortNodes(collect(n), 'uid') as duplicated_roots
            
            // MATCH these SimpleConceptValues which have multiple SimpleConceptRoots assigned
            WHERE size(duplicated_roots) > 1
            
            // pick one SimpleConceptRoot node that will be left linked with SimpleConceptValue node 
            WITH duplicated_roots, last(duplicated_roots) AS unique_root
            
            // remove SimpleConceptRoot to be left node from the list of all SimpleConceptRoot nodes
            WITH unique_root, [root in duplicated_roots where root <> unique_root] as duplicated_roots
            UNWIND duplicated_roots as duplicated_root

            // get all relationships linked with the SimpleConceptRoot nodes to be deleted
            OPTIONAL MATCH (duplicated_root)-[duplicated_rel]-(dependent_node)

            CALL apoc.do.case([
                // We don't want to copy over the (versioning, library and template parameter type relationships)
                not (
                    duplicated_rel:LATEST OR 
                    duplicated_rel:LATEST_FINAL OR 
                    duplicated_rel:LATEST_DRAFT OR  
                    duplicated_rel:LATEST_RELEASED OR
                    duplicated_rel:HAS_VERSION OR 
                    dependent_node:Library OR dependent_node:TemplateParameter),

                // copy relationships from SimpleConceptRoot to be deleted nodes to the unique SimpleConceptRoot node
                'CALL apoc.refactor.to(duplicated_rel, unique_root) YIELD input, output RETURN input, output'
            ],
            '',
            {
                dependent_node:dependent_node, 
                duplicated_rel:duplicated_rel, 
                unique_root:unique_root}
            ) YIELD value
            DETACH DELETE duplicated_root
            RETURN *
        """)


if __name__ == "__main__":
    main()
