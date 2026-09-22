"""Schema migrations needed for release to PROD post Sept 2023."""

import os

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
    migrate_single_node_for_activity_item(DB_CONNECTION, logger)
    migrate_single_activity_item_per_class(DB_CONNECTION, logger)
    migrate_study_activity_subgroup_and_group(DB_CONNECTION, logger)
    migrate_soa_group_selection_node(DB_CONNECTION, logger)
    migrate_removal_of_study_rels_for_study_subgroup_group_and_soa_group(
        DB_CONNECTION, logger
    )
    migrate_labels_for_study_activity_subgroup(DB_CONNECTION, logger)
    migrate_labels_for_study_activity_group(DB_CONNECTION, logger)
    migrate_labels_for_study_soa_group(DB_CONNECTION, logger)
    migrate_refinement_and_renumbering_of_syntax_sequence_id(DB_CONNECTION, logger)


def migrate_single_node_for_activity_item(db_connection, log):
    log.info("Migrating ActivityItemRoot&Value node pairs to single ActivityItem")
    _result, _ = db_connection.cypher_query("""
        MATCH (instval:ActivityInstanceValue)-[cai:CONTAINS_ACTIVITY_ITEM]->(aiv:ActivityItemValue)
        CALL {
            WITH instval, cai, aiv
            WITH instval, collect(cai) as cais, collect(aiv) as aivs
            CREATE (instval)-[cai_new:CONTAINS_ACTIVITY_ITEM]->(ai:ActivityItem)
            WITH aivs, ai
            CALL {
                WITH aivs, ai
                UNWIND aivs AS aiv
                MATCH (aiv)<-[:LATEST]-(air:ActivityItemRoot)<-[:HAS_ACTIVITY_ITEM]-(aicr:ActivityItemClassRoot)
                MERGE (ai)<-[:HAS_ACTIVITY_ITEM]-(aicr)
            }
            CALL {
                WITH aivs, ai
                UNWIND aivs AS aiv
                MATCH (aiv)-[:HAS_CT_TERM]->(tr:CTTermRoot)
                MERGE (ai)-[:HAS_CT_TERM]->(tr)
            }
            CALL {
                WITH aivs, ai
                UNWIND aivs AS aiv
                MATCH (aiv)-[:HAS_UNIT_DEFINITION]->(ur:UnitDefinitionRoot)
                MERGE (ai)-[:HAS_UNIT_DEFINITION]->(ur)
            }
        }
        """)
    _result, _ = db_connection.cypher_query("""
        MATCH (aiv:ActivityItemValue)<-[]-(air:ActivityItemRoot)
        WITH air, collect(aiv) as values
        FOREACH (v IN values | DETACH DELETE v)
        DETACH DELETE air
        """)


def migrate_single_activity_item_per_class(db_connection, log):
    log.info(
        "Migrating ActivityItem nodes of ActivityInstance to single node per ActivityItemClass"
    )
    _result, _ = db_connection.cypher_query("""
        MATCH (instval:ActivityInstanceValue)-[cai:CONTAINS_ACTIVITY_ITEM]->(aiv:ActivityItem)<-[hai:HAS_ACTIVITY_ITEM]-(aicr:ActivityItemClassRoot)
        WITH instval, aicr, collect(aiv) as items
        WHERE size(items) > 1
        CALL apoc.refactor.mergeNodes(items,{
          properties:"overwrite",
          mergeRels:true
        })
        YIELD node
        RETURN node
        """)


def migrate_study_activity_subgroup_and_group(db_connection, log):
    log.info("Migrating StudyActivitySubGroup and StudyActivityGroup nodes")
    _result, _ = db_connection.cypher_query("""
            MATCH (study_activity:StudyActivity)-[:HAS_SELECTED_ACTIVITY]->
                (activity_value:ActivityValue)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->
                (activity_valid_group:ActivityValidGroup)-[:IN_GROUP]->(activity_group_value:ActivityGroupValue)
            WITH *,
                head([(activity_valid_group)<-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue) | activity_subgroup_value ]) AS activity_subgroup_value
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
            MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup)
            MERGE (study_activity_subgroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value)

            WITH study_activity_subgroup, activity_group_value
            // StudyActivityGroup
            CREATE (study_activity_group:StudyActivityGroup:StudySelection)
                MERGE (study_ag_counter:Counter {counterId:'StudyActivityGroupCounter'})
                ON CREATE SET study_ag_counter:StudyActivityGroupCounter, study_ag_counter.count=1
                WITH *
                CALL apoc.atomic.add(study_ag_counter,'count',1,1) yield oldValue, newValue
                WITH *, toInteger(newValue) as uid_number_study_ag
                SET study_activity_group.uid = "StudyActivityGroup_"+apoc.text.lpad(""+(uid_number_study_ag), 6, "0")
            MERGE (study_activity_subgroup)-[:STUDY_ACTIVITY_SUBGROUP_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group)
            MERGE (study_activity_group)-[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value)
        """)


def migrate_soa_group_selection_node(db_connection, log):
    log.info("Migrating StudySoAGroup node for each StudyActivity node")
    _result, _ = db_connection.cypher_query("""
        MATCH (study_value:StudyValue)-[:HAS_STUDY_ACTIVITY]->
            (study_activity:StudyActivity)-[has_flowchart_group:HAS_FLOWCHART_GROUP]->(flowchart_group_term:CTTermRoot)
        WITH *, head([(study_root)-[]->(study_value) | study_root]) AS study_root
        WHERE NOT (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-()

        // StudySoAGroup
        CREATE (study_soa_group:StudySoAGroup:StudySelection)
            MERGE (study_soa_group_counter:Counter {counterId:'StudySoAGroupCounter'})
            ON CREATE SET study_soa_group_counter:StudySoAGroupCounter, study_soa_group_counter.count=1
            WITH *
            CALL apoc.atomic.add(study_soa_group_counter,'count',1,1) yield oldValue, newValue
            WITH *, toInteger(newValue) as uid_number_study_sog
            SET study_soa_group.uid = "StudySoAGroup_"+apoc.text.lpad(""+(uid_number_study_sog), 6, "0")

        MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:"schema-migration", date:datetime()})-[:AFTER]->(study_soa_group)
        MERGE (study_value)-[:HAS_STUDY_SOA_GROUP]->(study_soa_group)
        MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group)
        MERGE (study_soa_group)-[:HAS_FLOWCHART_GROUP]->(flowchart_group_term)
        DETACH DELETE has_flowchart_group
        """)


def migrate_removal_of_study_rels_for_study_subgroup_group_and_soa_group(
    db_connection, log
):
    log.info(
        "Migrating removal of Study relationships for StudyActivitySubGroup, StudyActivityGroup and StudySoAGroup and "
        "migrating (:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(:StudyActivityGroup) relationship"
    )
    _result, _ = db_connection.cypher_query("""
        MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->
            (study_activity_subgroup:StudyActivitySubGroup)-[study_subgroup_has_group:STUDY_ACTIVITY_SUBGROUP_HAS_STUDY_ACTIVITY_GROUP]->
            (study_activity_group:StudyActivityGroup)
        MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group)
        WITH *, 
            [(:StudyValue)-[has_sas:HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup) | has_sas] AS has_study_activity_subgroup,
            [(:StudyValue)-[has_sag:HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group) | has_sag] AS has_study_activity_group,
            [(:StudyValue)-[has_ssg:HAS_STUDY_SOA_GROUP]->(:StudySoAGroup) | has_ssg] AS has_study_soa_group

        DETACH DELETE study_subgroup_has_group
        FOREACH (hsas IN has_study_activity_subgroup | DETACH DELETE hsas)
        FOREACH (hsag IN has_study_activity_group | DETACH DELETE hsag)
        FOREACH (hsoag IN has_study_soa_group | DETACH DELETE hsoag)
        """)


def migrate_labels_for_study_activity_subgroup(db_connection, log):
    log.info("Migrating node labels for StudyActivitySubGroup nodes")
    _result, _ = db_connection.cypher_query("""
        MATCH (study_activity_subgroup:StudyActivitySubGroup)
        SET study_activity_subgroup:StudySelectionMetadata
        REMOVE study_activity_subgroup:StudySelection
        """)


def migrate_labels_for_study_activity_group(db_connection, log):
    log.info("Migrating node labels for StudyActivityGroup nodes")
    _result, _ = db_connection.cypher_query("""
        MATCH (study_activity_group:StudyActivityGroup)
        SET study_activity_group:StudySelectionMetadata
        REMOVE study_activity_group:StudySelection
        """)


def migrate_labels_for_study_soa_group(db_connection, log):
    log.info("Migrating node labels for StudySoAGroup nodes")
    _result, _ = db_connection.cypher_query("""
        MATCH (study_soa_group:StudySoAGroup)
        SET study_soa_group:StudySelectionMetadata
        REMOVE study_soa_group:StudySelection
        """)


def migrate_refinement_and_renumbering_of_syntax_sequence_id(db_connection, log):
    def refine_pre_instance_sequence(template_uid):
        syntax_pre_instances = db_connection.cypher_query(f"""
                MATCH (n:{node_label} {{uid: "{template_uid}"}})<-[:CREATED_FROM]-(p:SyntaxPreInstanceRoot)
                RETURN n.sequence_id, p.uid ORDER BY n.uid
            """)
        if syntax_pre_instances[0]:
            for idx, syntax_pre_instance in enumerate(syntax_pre_instances[0], 1):
                pre_seq_id = f"{syntax_pre_instance[0]}P{idx}"
                db_connection.cypher_query(f"""
                        MATCH (n:SyntaxPreInstanceRoot {{uid: "{syntax_pre_instance[1]}"}})
                        SET n.sequence_id = "{pre_seq_id}"
                    """)
                log.info(
                    f"Renumbered sequence_id of {syntax_pre_instance[1]}, {seq_id} to {pre_seq_id}"
                )

    log.info(
        "Migrating renumbering of sequence_id of SyntaxTemplateRoot and related SyntaxPreInstanceRoot"
    )
    syntax_templates_without_types = {
        "ActivityInstructionTemplateRoot": "AI",
        "EndpointTemplateRoot": "E",
        "ObjectiveTemplateRoot": "O",
        "TimeframeTemplateRoot": "T",
    }
    for node_label, prefix in syntax_templates_without_types.items():
        log.info(f"Migrating renumbering of sequence_id of {node_label}")

        syntax_templates = db_connection.cypher_query(f"""
                MATCH (n:{node_label})<-[:CONTAINS_SYNTAX_TEMPLATE]-(l:Library)
                RETURN DISTINCT(n.uid), l.name="User Defined" ORDER BY n.uid
            """)

        non_user_defined_syntax_template_uids = [
            item[0] for item in syntax_templates[0] if not item[1]
        ]
        user_defined_syntax_template_uids = [
            item[0] for item in syntax_templates[0] if item[1]
        ]

        for idx, syntax_template_uid in enumerate(
            non_user_defined_syntax_template_uids, 1
        ):
            seq_id = f"{prefix}{idx}"
            db_connection.cypher_query(f"""
                    MATCH (n:{node_label} {{uid: "{syntax_template_uid}"}})
                    SET n.sequence_id = "{seq_id}"
                """)
            log.info(f"Renumbered sequence_id of {syntax_template_uid} to {seq_id}")
            refine_pre_instance_sequence(syntax_template_uid)
        for idx, syntax_template_uid in enumerate(user_defined_syntax_template_uids, 1):
            seq_id = f"U-{prefix}{idx}"
            db_connection.cypher_query(f"""
                    MATCH (n:{node_label} {{uid: "{syntax_template_uid}"}})
                    SET n.sequence_id = "{seq_id}"
                """)
            log.info(
                f"Renumbered sequence_id of User Defined {syntax_template_uid} to {seq_id}"
            )
            refine_pre_instance_sequence(syntax_template_uid)

    syntax_template_with_types = {
        "CriteriaTemplateRoot": {
            "Inclusion Criteria": "CI",
            "Exclusion Criteria": "CE",
            "Run-in Criteria": "CRI",
            "Randomisation Criteria": "CR",
            "Dosing Criteria": "CD",
            "Withdrawal Criteria": "CW",
        },
        "FootnoteTemplateRoot": {"SoA Footnote": "FSA"},
    }
    for node_label, prefixes in syntax_template_with_types.items():
        log.info(f"Migrating renumbering of sequence_id of {node_label}")
        for name, prefix in prefixes.items():
            syntax_templates = db_connection.cypher_query(f"""
                    MATCH (n:{node_label})<-[:CONTAINS_SYNTAX_TEMPLATE]-(l:Library)
                    MATCH (n)-[:HAS_TYPE]->(:CTTermRoot)--(:CTTermNameRoot)--(t:CTTermNameValue {{name: "{name}"}})
                    RETURN DISTINCT(n.uid), l.name="User Defined" ORDER BY n.uid
                """)

            non_user_defined_syntax_template_uids = [
                item[0] for item in syntax_templates[0] if not item[1]
            ]
            user_defined_syntax_template_uids = [
                item[0] for item in syntax_templates[0] if item[1]
            ]

            for idx, syntax_template_uid in enumerate(
                non_user_defined_syntax_template_uids, 1
            ):
                seq_id = f"{prefix}{idx}"
                db_connection.cypher_query(f"""
                        MATCH (n:{node_label} {{uid: "{syntax_template_uid}"}})
                        SET n.sequence_id = "{seq_id}"
                    """)
                log.info(f"Renumbered sequence_id of {syntax_template_uid} to {seq_id}")
                refine_pre_instance_sequence(syntax_template_uid)
            for idx, syntax_template_uid in enumerate(
                user_defined_syntax_template_uids, 1
            ):
                seq_id = f"U-{prefix}{idx}"
                db_connection.cypher_query(f"""
                        MATCH (n:{node_label} {{uid: "{syntax_template_uid}"}})
                        SET n.sequence_id = "{seq_id}"
                    """)
                log.info(f"Renumbered sequence_id of {syntax_template_uid} to {seq_id}")
                refine_pre_instance_sequence(syntax_template_uid)


if __name__ == "__main__":
    main()
