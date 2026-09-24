"""Schema migrations needed for release to PROD post Oct 2023."""

import os

from migrations.common import migrate_ct_config_values, migrate_indexes_and_constraints
from migrations.utils.utils import get_db_connection, get_logger

logger = get_logger(os.path.basename(__file__))
DB_CONNECTION = get_db_connection()
MIGRATION_DESC = "schema-migration-release-1.5"


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])

    ### Common migrations
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_ct_config_values(DB_CONNECTION, logger)

    ### Release-specific migrations
    fix_study_epoch_order(DB_CONNECTION, logger)
    link_variables_with_value_terms(DB_CONNECTION, logger)
    migrate_delete_study_actions_on_study_fields(DB_CONNECTION, logger)
    add_missing_latest_relationships(DB_CONNECTION, logger)
    migrate_study_activity_group_audit_trail_node(DB_CONNECTION, logger)
    remove_duplicated_study_activity_schedules(DB_CONNECTION, logger)
    migrate_week_in_study(DB_CONNECTION, logger)
    migrate_soa_preferred_time_unit(DB_CONNECTION, logger)
    migrate_study_activity_grouping_and_audit_trail(DB_CONNECTION, logger)
    migrate_nullify_unit_definition_name_sentence_case(DB_CONNECTION, logger)
    migrate_missing_activity_item_class(DB_CONNECTION, logger)
    migrate_remove_invalid_activity_instances(DB_CONNECTION, logger)
    remove_broken_study_activity_instances(DB_CONNECTION, logger)
    migrate_study_activity_instances(DB_CONNECTION, logger)


def fix_study_epoch_order(db_connection, log):
    studies, _ = db_connection.cypher_query("""
        MATCH (study_root:StudyRoot) return study_root.uid
        """)
    for study in studies:
        study_uid = study[0]
        log.info("Fixing StudyEpoch order for the following Study (%s)", study_uid)
        _result, _ = db_connection.cypher_query(
            """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)
            WITH DISTINCT study_root, study_value
            MATCH (study_value)-[:HAS_STUDY_EPOCH]->(study_epoch:StudyEpoch)
            WHERE NOT (study_epoch)<-[:BEFORE]-()
            // reverse as apoc.coll.sortNodes returns DESC order by default
            WITH reverse(apoc.coll.sortNodes(collect(study_epoch), 'order')) as ordered_epochs
            WITH ordered_epochs, range(1, size(ordered_epochs)) as orders
            UNWIND orders AS order
            WITH ordered_epochs[order-1] as ordered_epoch, order
            SET ordered_epoch.order = order
            """,
            params={"study_uid": study_uid},
        )


def terms_name_codelist_mapping(db_connection, term_name):
    # This query gets all Terms with code_submission_value = _value
    # It also gets the codelists these belong to
    # And it only returns the most recent version of a term for each codelist
    terms_data, meta = db_connection.cypher_query(
        """
        MATCH (codelist_value:CTCodelistAttributesValue)<-[:LATEST]-(:CTCodelistAttributesRoot)<--(codelist_root:CTCodelistRoot)
            -->(term_root:CTTermRoot)-->(:CTTermAttributesRoot)-[version_rel:HAS_VERSION]->(term:CTTermAttributesValue)
        WHERE term.code_submission_value=$code_submission_value
        WITH codelist_root, codelist_value, version_rel, term_root
        ORDER BY codelist_root.uid, version_rel.start_date DESC
        WITH codelist_root, codelist_value, collect(term_root)[0] AS terms
        UNWIND terms AS term_root
        RETURN DISTINCT term_root.uid AS term_uid, collect(DISTINCT {uid:codelist_root.uid, submission_value: codelist_value.submission_value}) AS codelists
    """,
        {"code_submission_value": term_name},
    )

    return [dict(zip(meta, row)) for row in terms_data]


def list_variables_to_link(db_connection):
    variables_data, meta = db_connection.cypher_query("""
            MATCH (root:DatasetVariable)-[:HAS_INSTANCE]->(v:DatasetVariableInstance)
            WHERE v.value_list IS NOT NULL AND NOT EXISTS ((v)-[:REFERENCES_TERM]->(:CTTermRoot))
            RETURN id(v) AS id, v.value_list AS value_list, root.uid AS uid
        """)
    return [dict(zip(meta, row)) for row in variables_data]


def link_variables_with_value_terms(db_connection, log):
    variables = list_variables_to_link(db_connection)

    for variable in variables:
        previous_codelist_uid = None
        match_variable_clause = (
            "MATCH (variable_instance) WHERE id(variable_instance)=$variable_id"
        )
        create_relationship_clause = (
            "MERGE (variable_instance)-[:REFERENCES_TERM]->(term)"
        )
        log.info(
            "Linking variable %s with terms for value_list %s",
            variable["uid"],
            ", ".join(variable["value_list"]),
        )
        for _value in variable["value_list"]:
            terms_data = terms_name_codelist_mapping(db_connection, _value)

            # If there is only one CCode, then link the variable with it
            if len(terms_data) == 1:
                match_term = "MATCH (term: CTTermRoot {uid: $term_uid})"
                query = " ".join(
                    [match_variable_clause, match_term, create_relationship_clause]
                )
                db_connection.cypher_query(
                    query,
                    {
                        "term_uid": terms_data[0]["term_uid"],
                        "variable_id": variable["id"],
                    },
                )
                # Store the codelist name in the list for the next case
                if previous_codelist_uid is None:
                    previous_codelist_uid = terms_data[0]["codelists"][0]["uid"]

            # Else, if other elements in the value_list had a single match, then use the term coming from the same codelist
            else:
                if previous_codelist_uid is not None:
                    # Hardcoding based on past data knowledge
                    if _value == "U":
                        _value = "UNKNOWN"

                        # Re-run the terms query for the replacement
                        terms_data = terms_name_codelist_mapping(db_connection, _value)

                    # Link variable with terms
                    # Find the term which belongs to the same codelist as the previous hit
                    # For example, UNKNOWN in the STENRF codelist for the --STRTPT variables
                    term_uid = next(
                        (
                            term_data["term_uid"]
                            for term_data in terms_data
                            if previous_codelist_uid
                            in [codelist["uid"] for codelist in term_data["codelists"]]
                        ),
                        None,
                    )

                    if term_uid is not None:
                        match_term = "MATCH (term: CTTermRoot {uid: $term_uid})<--(:CTCodelistRoot{uid: $codelist_uid})"
                        query = " ".join(
                            [
                                match_variable_clause,
                                match_term,
                                create_relationship_clause,
                            ]
                        )
                        db_connection.cypher_query(
                            query,
                            {
                                "variable_id": variable["id"],
                                "term_uid": term_uid,
                                "codelist_uid": previous_codelist_uid,
                            },
                        )

                        # Relationship created, go to next value in value_list
                        continue

                # If we reach here, it means there was more than one match for the value (or none)
                # It also means the script could not figure out a codelist from other values in the value_list (if any)
                # So, if one of the terms is in a codelist which submission_value is the same name as the variable uid, then use that term
                if len(terms_data) > 0 and (
                    any(
                        variable["uid"]
                        in [
                            codelist["submission_value"]
                            for codelist in term_data["codelists"]
                        ]
                        for term_data in terms_data
                    )
                    or (
                        variable["uid"] == "DOMAIN"
                        and any(
                            "SDOMAIN"
                            in [
                                codelist["submission_value"]
                                for codelist in term_data["codelists"]
                            ]
                            for term_data in terms_data
                        )
                    )
                ):
                    term_uid = next(
                        (
                            term_data["term_uid"]
                            for term_data in terms_data
                            if variable["uid"]
                            in [
                                codelist["submission_value"]
                                for codelist in term_data["codelists"]
                            ]
                        ),
                        None,
                    )

                    if term_uid is None and variable["uid"] == "DOMAIN":
                        term_uid = next(
                            (
                                term_data["term_uid"]
                                for term_data in terms_data
                                if "SDOMAIN"
                                in [
                                    codelist["submission_value"]
                                    for codelist in term_data["codelists"]
                                ]
                            ),
                            None,
                        )

                    match_term = "MATCH (term: CTTermRoot {uid: $term_uid})"
                    query = " ".join(
                        [match_variable_clause, match_term, create_relationship_clause]
                    )
                    db_connection.cypher_query(
                        query,
                        {
                            "term_uid": term_uid,
                            "variable_id": variable["id"],
                        },
                    )


def migrate_delete_study_actions_on_study_fields(db_connection, log):
    log.info(
        "Migrating - Fixing bad deletions on deleted StudyFields to have the StudyActions standard convention"
    )
    _result, _ = db_connection.cypher_query("""
        // MATCH BAD DELETED StudySelection
        MATCH (del:Delete)-[ss_del]-(ss:StudyField)

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
        OPTIONAL MATCH (output)-[output_sv]-(:StudyValue)-[:LATEST]-(:StudyRoot)    // Delete StudyValue rel, because is being deleted
        
        //DISCONNECT OLD NODE
        OPTIONAL MATCH (ss_old)-[ss_old_del:AFTER]-(del)   // From Delete node After rel

        //DISCONNECT NEW
        DELETE output_saction
        DELETE output_sv
       
        MERGE (output)<-[:AFTER]-(del)

        //DISCONNECT OLD NODE
        DELETE ss_old_del

        RETURN  DISTINCT ID(ss_old)
        """)
    logger.info("Output - StudyFields ID Migrated %s", _result)


def add_missing_latest_relationships(db_connection, log):
    excluded_labels = [
        "ClassVariableRoot",
        "DatasetClassRoot",
        "DatasetRoot",
        "DatasetScenarioRoot",
        "DatasetVariableRoot",
        "DataModelIGRoot",
        "DataModelRoot",
        "StudyRoot",
    ]
    for status, relationship in (
        ("Draft", "LATEST_DRAFT"),
        ("Final", "LATEST_FINAL"),
        ("Retired", "LATEST_RETIRED"),
    ):
        log.info(f"Migrating - Adding missing {relationship} relationships")

        query = f"""
            MATCH (roots)-[:HAS_VERSION {{status: '{status}'}}]->()
            WHERE none(label in labels(roots) WHERE label IN {excluded_labels})
            WITH DISTINCT roots as root
            CALL {{
                    WITH root
                    // Sort by version and dates
                    MATCH (root)-[hv:HAS_VERSION {{status: '{status}'}}]->(version)
                    WITH root, hv, version
                    ORDER BY
                        toInteger(split(hv.version, '.')[0]) ASC,
                        toInteger(split(hv.version, '.')[1]) ASC,
                        hv.end_date ASC,
                        hv.start_date ASC
                    WITH last(collect(version)) as latest_via_hv
                    RETURN latest_via_hv
                }}
            WITH root, latest_via_hv WHERE NOT (root)-[:{relationship}]->(latest_via_hv)
            MERGE (root)-[:{relationship}]->(latest_via_hv)
            """
        _result, _ = db_connection.cypher_query(query)


def migrate_study_activity_group_audit_trail_node(db_connection, log):
    log.info("Migrating broken Audit Trail nodes for the StudyActivityGroups")
    _result, _ = db_connection.cypher_query(
        """
        MATCH (study_activity_group:StudyActivityGroup)<-[:AFTER|BEFORE]-(study_action:StudyAction)
            <-[old_audit_trail_relationship:AUDIT_TRAIL]-(study_root_audit_trail)
        WHERE NOT study_root_audit_trail:StudyRoot
        MATCH (study_activity_group)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(study_activity:StudyActivity)
            <-[:AFTER|BEFORE]-(:StudyAction)<-[:AUDIT_TRAIL]-(correct_study_root_node)
        WITH DISTINCT correct_study_root_node, old_audit_trail_relationship, study_root_audit_trail, study_action
        MERGE (study_action)<-[:AUDIT_TRAIL]-(correct_study_root_node)
        DETACH DELETE old_audit_trail_relationship, study_root_audit_trail
        """,
    )


def migrate_study_activity_instances(db_connection, log):
    studies, _ = db_connection.cypher_query("""
        MATCH (study_root:StudyRoot) return study_root.uid
        """)
    for study in studies:
        study_uid = study[0]
        log.info(
            "Migrating StudyActivityInstances for the following Study (%s)", study_uid
        )
        _result, _ = db_connection.cypher_query(
            """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)-[:HAS_STUDY_ACTIVITY]
                ->(study_activity:StudyActivity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue)
            WHERE NOT (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]->() AND
                head([(activity_value)<-[:HAS_VERSION]-(activity_root:ActivityRoot)<-[:CONTAINS_CONCEPT]-(library) | library.name]) <> "Requested"

            WITH DISTINCT study_activity, study_root, study_value, activity_value
            // StudyActivityInstance
            CREATE (study_activity_instance:StudyActivityInstance:StudySelection)
                MERGE (study_activity_instance_counter:Counter {counterId:'StudyActivityInstanceCounter'})
                ON CREATE SET study_activity_instance_counter:StudyActivityInstanceCounter, study_activity_instance_counter.count=1
                WITH *
                CALL apoc.atomic.add(study_activity_instance_counter,'count',1,1) yield oldValue, newValue
                WITH *, toInteger(newValue) as uid_number_study_activity_instance
                SET study_activity_instance.uid = "StudyActivityInstance_"+apoc.text.lpad(""+(uid_number_study_activity_instance), 6, "0")
            MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]->(study_activity_instance)
            MERGE (study_value)-[:HAS_STUDY_ACTIVITY_INSTANCE]->(study_activity_instance)
            MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:"schema-migration", date:datetime()})-[:AFTER]->(study_activity_instance)

            WITH study_activity_instance, activity_value
            OPTIONAL MATCH (activity_value)-[:HAS_GROUPING]
                ->(:ActivityGrouping)<-[:HAS_ACTIVITY]-(activity_instance_value:ActivityInstanceValue)
            WITH DISTINCT study_activity_instance, activity_instance_value
            ORDER BY activity_instance_value.is_required_for_activity DESC, activity_instance_value.is_defaulted_for_activity DESC
            CALL apoc.do.case([
                activity_instance_value is not null and not (study_activity_instance)-[:HAS_SELECTED_ACTIVITY_INSTANCE]->(),
                'MERGE (study_activity_instance)-[:HAS_SELECTED_ACTIVITY_INSTANCE]->(activity_instance_value)'
            ],
            '',
            {
                activity_instance_value: activity_instance_value,
                study_activity_instance:study_activity_instance
            })
            YIELD value
            RETURN *
            """,
            params={"study_uid": study_uid},
        )


def remove_duplicated_study_activity_schedules(db_connection, log):
    studies, _ = db_connection.cypher_query("""
        MATCH (study_root:StudyRoot) return study_root.uid
        """)
    for study in studies:
        study_uid = study[0]
        log.info(
            "Removing duplicated StudyActivitySchedules for the following Study (%s)",
            study_uid,
        )
        _result, _ = db_connection.cypher_query(
            """
               MATCH (study_root:StudyRoot)-[:LATEST]->(study_value:StudyValue)-[:HAS_STUDY_ACTIVITY_SCHEDULE]
                    ->(study_activity_schedule:StudyActivitySchedule)
                WHERE NOT (study_activity_schedule)<-[:BEFORE]-()
                MATCH (study_visit:StudyVisit)-[:STUDY_VISIT_HAS_SCHEDULE]->(study_activity_schedule)
                WHERE NOT (study_visit)<-[:BEFORE]-()
                MATCH (study_activity_schedule)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(study_activity:StudyActivity)
                WHERE NOT (study_activity)<-[:BEFORE]-()
                WITH study_visit, study_activity, apoc.coll.sortNodes(collect(study_activity_schedule), 'uid') as duplicated_schedules
                WHERE size(duplicated_schedules) > 1
                
                // pick the oldest StudyActivitySchedule that will be the left
                WITH duplicated_schedules, last(duplicated_schedules) AS unique_schedule
                
                // remove StudyActivitySchedule that should be left from the duplicated list
                WITH unique_schedule, [schedule in duplicated_schedules where schedule <> unique_schedule] as duplicated_schedules
                UNWIND duplicated_schedules as duplicated_schedule
                
                // get all StudySoAFootnotes assigned to the duplicated StudyActivitySchedule
                OPTIONAL MATCH (duplicated_schedule)<-[duplicated_footnote:REFERENCES_STUDY_ACTIVITY_SCHEDULE]-(study_soa_footnote:StudySoAFootnote)
    
                CALL apoc.do.case([
                    // We don't want to copy over the StudySoAFootnote relationship if it exists
                    study_soa_footnote IS NOT NULL AND NOT (unique_schedule)<-[:REFERENCES_STUDY_ACTIVITY_SCHEDULE]-(study_soa_footnote),
    
                    'MERGE (unique_schedule)<-[:REFERENCES_STUDY_ACTIVITY_SCHEDULE]-(study_soa_footnote)'
                ],
                '',
                { 
                    study_soa_footnote: study_soa_footnote,
                    duplicated_footnote:duplicated_footnote, 
                    unique_schedule:unique_schedule
                }
                ) YIELD value
    
                MATCH (duplicated_schedule)--(study_action:StudyAction)
                DETACH DELETE duplicated_schedule, study_action
                """,
            params={"study_uid": study_uid},
        )


def migrate_week_in_study(db_connection, log):
    log.info(
        "Migration: Adding WeekInStudy relationship to all StudyVisits that have StudyDurationWeeks relationship"
    )
    study_visits_with_duration_weeks, _ = db_connection.cypher_query("""
        MATCH (sv:StudyVisit)-[hsdw:HAS_STUDY_DURATION_WEEKS]->
        (nvr:ConceptRoot:NumericValueRoot:SimpleConceptRoot:StudyDurationWeeksRoot:TemplateParameterTermRoot)-[hv:HAS_VERSION]->
        (nv:ConceptValue:NumericValue:SimpleConceptValue:StudyDurationWeeksValue:TemplateParameterTermValue)
        WHERE NOT (sv)-[:HAS_WEEK_IN_STUDY]->(:WeekInStudyRoot)
        MATCH (nvr)<-[:CONTAINS_CONCEPT]-(lib:Library)
        RETURN DISTINCT
            sv.uid,
            nvr.uid,
            nv.name,
            nv.value,
            hv.change_description,
            hv.start_date,
            hv.status,
            hv.user_initials,
            hv.version,
            lib.is_editable,
            lib.name
        """)

    for visit in study_visits_with_duration_weeks:
        name = "Week " + visit[2].replace(" weeks", "")

        existing_week_in_study, _ = db_connection.cypher_query(
            """
            MATCH (:StudyVisit)-[hwis:HAS_WEEK_IN_STUDY]->
            (root:ConceptRoot:NumericValueRoot:SimpleConceptRoot:WeekInStudyRoot:TemplateParameterTermRoot)-->
            (:ConceptValue:NumericValue:SimpleConceptValue:WeekInStudyValue:TemplateParameterTermValue {
                name: $name
            })
            RETURN DISTINCT root.uid
            """,
            params={"name": name},
        )

        if existing_week_in_study:
            db_connection.cypher_query(
                """
                MATCH (sv:StudyVisit {
                    uid: $study_visit_uid
                })-[:HAS_STUDY_DURATION_WEEKS]->(:StudyDurationWeeksRoot {
                    uid: $study_duration_weeks_uid
                }),
                (root:ConceptRoot {
                    uid: $week_in_study_uid
                })
                CREATE (sv)-[:HAS_WEEK_IN_STUDY]->(root)
                """,
                params={
                    "study_visit_uid": visit[0],
                    "study_duration_weeks_uid": visit[1],
                    "week_in_study_uid": existing_week_in_study[0][0],
                },
            )
        else:
            new_uid = db_connection.cypher_query(
                """
                MATCH (n:NumericValueCounter)
                CALL apoc.atomic.add(n, "count", 1, 1)
                YIELD oldValue, newValue
                WITH *, "NumericValue_"+apoc.text.lpad(""+(toInteger(newValue)), 6, "0") as new_uid
                CREATE (root:ConceptRoot:NumericValueRoot:SimpleConceptRoot:WeekInStudyRoot:TemplateParameterTermRoot {
                    uid: new_uid
                })
                CREATE (value:ConceptValue:NumericValue:SimpleConceptValue:WeekInStudyValue:TemplateParameterTermValue {
                    name: $name,
                    name_sentence_case: $name,
                    value: $numeric_value
                })
                CREATE (root)-[:LATEST]->(value)
                CREATE (root)-[:LATEST_FINAL]->(value)
                CREATE (root)-[:HAS_VERSION {
                    change_description: $change_description,
                    start_date: datetime($start_date),
                    status: $status,
                    user_initials: $user_initials,
                    version: $version
                }]->(value)
                MERGE (tp:TemplateParameter {
                    name: "WeekInStudy"
                })
                CREATE (root)<-[:HAS_PARAMETER_TERM]-(tp)
                MERGE (lib:Library {
                    is_editable: $is_editable,
                    name: $lib_name
                })
                CREATE (root)<-[:CONTAINS_CONCEPT]-(lib)
                RETURN new_uid
                """,
                params={
                    "name": name,
                    "numeric_value": visit[3],
                    "change_description": visit[4],
                    "start_date": visit[5].iso_format(),
                    "status": visit[6],
                    "user_initials": visit[7],
                    "version": visit[8],
                    "is_editable": visit[9],
                    "lib_name": visit[10],
                },
            )[0][0][0]

            db_connection.cypher_query(
                """
                MATCH (root:ConceptRoot:NumericValueRoot:SimpleConceptRoot:WeekInStudyRoot:TemplateParameterTermRoot {
                    uid: $week_in_study_uid
                })
                MATCH (sv:StudyVisit {
                    uid: $study_visit_uid
                })-[:HAS_STUDY_DURATION_WEEKS]->(:StudyDurationWeeksRoot {uid: $study_duration_weeks_uid})
                CREATE (sv)-[:HAS_WEEK_IN_STUDY]->(root)
                """,
                params={
                    "study_visit_uid": visit[0],
                    "study_duration_weeks_uid": visit[1],
                    "week_in_study_uid": new_uid,
                },
            )


def migrate_soa_preferred_time_unit(db_connection, log):
    log.info("Migration: Adding StudyTimeField for soa_preferred_time_unit.")
    week_unit_definition_uid = db_connection.cypher_query("""
        MATCH (udr:UnitDefinitionRoot)-->(:UnitDefinitionValue {name: "week"})
        RETURN DISTINCT udr.uid
        """)[0][0][0]

    db_connection.cypher_query(
        """
        MATCH (sv:StudyValue)<-[latest:LATEST]-(sr:StudyRoot)
        WHERE NOT (sv)-[:HAS_TIME_FIELD]->(:StudyTimeField {field_name: "soa_preferred_time_unit"})
        CREATE (sr)-[:AUDIT_TRAIL]->(csa:Create:StudyAction {user_initials:"schema-migration", date:datetime()})
        CREATE (csa)-[:AFTER]->(stf:StudyField:StudyTimeField {field_name: "soa_preferred_time_unit", value: $week_unit_definition_uid})
        WITH *
        MATCH (udr:UnitDefinitionRoot {uid: $week_unit_definition_uid})
        CREATE (stf)-[:HAS_UNIT_DEFINITION]->(udr)
        CREATE (sv)-[:HAS_TIME_FIELD]->(stf)
        """,
        params={"week_unit_definition_uid": week_unit_definition_uid},
    )

    db_connection.cypher_query(
        """
        MATCH (sv:StudyValue)<-[latest:LATEST]-(sr:StudyRoot)
        WHERE NOT (sv)-[:HAS_TIME_FIELD]->(:StudyTimeField {field_name: "preferred_time_unit"})
        CREATE (sr)-[:AUDIT_TRAIL]->(csa:Create:StudyAction {user_initials:"schema-migration", date:datetime()})
        CREATE (csa)-[:AFTER]->(stf:StudyField:StudyTimeField {field_name: "preferred_time_unit", value: $week_unit_definition_uid})
        WITH *
        MATCH (udr:UnitDefinitionRoot {uid: $week_unit_definition_uid})
        CREATE (stf)-[:HAS_UNIT_DEFINITION]->(udr)
        CREATE (sv)-[:HAS_TIME_FIELD]->(stf)
        """,
        params={"week_unit_definition_uid": week_unit_definition_uid},
    )


def migrate_study_activity_grouping_and_audit_trail(db_connection, log):
    log.info(
        "Migration: Merging duplicated StudyActivitySubGroup nodes for StudyActivity linked to Albumin Activity in the Study_000002"
    )
    _ = db_connection.cypher_query("""
        MATCH (sa:StudyActivity {uid:"StudyActivity_000351"})-[sahasg:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(sasg:StudyActivitySubGroup)-[hsasg:HAS_SELECTED_ACTIVITY_SUBGROUP]-(asgv:ActivitySubGroupValue)
        WITH sa, collect(sasg) as sasgs WHERE size(sasgs) > 1
        WITH sa
        MATCH (sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(sasg2:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]-(asgv)
        WHERE NOT (sasg2)-[:AFTER]-(:Delete) AND asgv.name <> "Biochemistry"
        WITH collect(sasg2) as gs
        FOREACH(duplicated_subgroup in gs | DETACH DELETE duplicated_subgroup)
        return *
        """)
    log.info(
        "Migration: Merging duplicated StudyActivityGroup nodes for StudyActivity linked to Albumin Activity in the Study_000002"
    )
    _ = db_connection.cypher_query("""
        MATCH (sa:StudyActivity {uid:"StudyActivity_000351"})-[sahag:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(sag:StudyActivityGroup)-[hsag:HAS_SELECTED_ACTIVITY_GROUP]-(agv:ActivityGroupValue)
        WITH sa, collect(sag) as sags WHERE size(sags) > 1
        WITH sa
        MATCH (sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(sag2:StudyActivityGroup)-[:HAS_SELECTED_ACTIVITY_GROUP]-(agv)
        WHERE NOT (sag2)-[:AFTER]-(:Delete) AND agv.name <> "Laboratory Assessments"
        WITH collect(sag2) as gs
        FOREACH(duplicated_group in gs | DETACH DELETE duplicated_group)
        return *
        """)
    log.info("Migration: Add missing StudyAction nodes for StudyActivitySubGroup nodes")
    _ = db_connection.cypher_query("""
        MATCH (study_activity_subgroup:StudyActivitySubGroup)
        WHERE NOT (study_activity_subgroup)<-[:AFTER|BEFORE]-()
        MATCH (study_activity_subgroup)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]-(study_activity:StudyActivity)
            <-[:AFTER|BEFORE]-(:StudyAction)<-[:AUDIT_TRAIL]-(correct_study_root_node)
        WITH DISTINCT correct_study_root_node, study_activity_subgroup
        MERGE (correct_study_root_node)-[:AUDIT_TRAIL]->(study_action:Create:StudyAction {user_initials:"schema-migration", date:datetime()})-[:AFTER]->(study_activity_subgroup)
        """)

    log.info("Migration: Add missing StudyAction nodes for StudyActivityGroup nodes")
    _ = db_connection.cypher_query("""
        MATCH (study_activity_group:StudyActivityGroup)
        WHERE NOT (study_activity_group)<-[:AFTER|BEFORE]-()
        MATCH (study_activity_group)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(study_activity:StudyActivity)
            <-[:AFTER|BEFORE]-(:StudyAction)<-[:AUDIT_TRAIL]-(correct_study_root_node)
        WITH DISTINCT correct_study_root_node, study_activity_group
        MERGE (correct_study_root_node)-[:AUDIT_TRAIL]->(study_action:Create:StudyAction {user_initials:"schema-migration", date:datetime()})-[:AFTER]->(study_activity_group)
        """)

    log.info("Migration: Merging duplicated StudyActivitySubGroup nodes")
    _ = db_connection.cypher_query("""
        MATCH (sa:StudyActivity)-[sahasg:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(sasg:StudyActivitySubGroup)-[hsasg:HAS_SELECTED_ACTIVITY_SUBGROUP]-(asgv:ActivitySubGroupValue)
        WITH sa, asgv, collect(sasg) as sasgs WHERE size(sasgs) > 1
        CALL {
            WITH sa, asgv
            MATCH (sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(sasg2:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]-(asgv)
            WHERE NOT (sasg2)-[:AFTER]-(:Delete)
            WITH collect(sasg2) as gs
            CALL apoc.refactor.mergeNodes(gs, {properties:"override", mergeRels:true}) YIELD node
            RETURN node
        } IN TRANSACTIONS
        return sa
        """)

    log.info(
        "Migration: Remove redundant StudyAction nodes for StudyActivitySubGroup nodes"
    )
    _ = db_connection.cypher_query("""
        MATCH (s:StudyActivitySubGroup)-[:AFTER|BEFORE]-(study_action)
        WHERE (s)-[:AFTER]-(study_action) and (s)-[:BEFORE]-(study_action)
        DETACH DELETE study_action
        RETURN *
        """)

    for rel in ["BEFORE", "AFTER"]:
        log.info(
            f"Migration: Removing duplicated {rel} StudyAction nodes for StudyActivitySubGroup nodes"
        )
        _ = db_connection.cypher_query(f"""
            MATCH (sasg:StudyActivitySubGroup)-[:{rel}]-(action:StudyAction)
            WITH sasg, collect(action) as actions WHERE size(actions) > 1
            CALL {{
                WITH sasg
                MATCH (sasg)-[:{rel}]-(action2:StudyAction)
                WITH sasg, collect(action2) as actions2 WHERE size(actions2) > 1
                WITH sasg, apoc.coll.sortNodes(actions2, 'date') as sorted_actions
                WITH tail(sorted_actions) as actions_to_delete
                FOREACH (n IN actions_to_delete | DETACH DELETE n)
            }} IN TRANSACTIONS
            return sasg
            """)

    log.info("Migration: Merging duplicated StudyActivityGroup nodes")
    _ = db_connection.cypher_query("""
        MATCH (sa:StudyActivity)-[sahsag:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(sag:StudyActivityGroup)-[hsag:HAS_SELECTED_ACTIVITY_GROUP]-(agv:ActivityGroupValue)
        WITH sa, agv, collect(sag) as sags WHERE size(sags) > 1
        CALL {
            WITH sa, agv
            MATCH (sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(sag2:StudyActivityGroup)-[:HAS_SELECTED_ACTIVITY_GROUP]-(agv)
            WHERE NOT (sag2)-[:AFTER]-(:Delete)
            WITH collect(sag2) as gs
            CALL apoc.refactor.mergeNodes(gs, {properties:"override", mergeRels:true}) YIELD node
            RETURN node
        } IN TRANSACTIONS
        return sa
        """)

    log.info(
        "Migration: Remove redundant StudyAction nodes for StudyActivityGroup nodes"
    )
    _ = db_connection.cypher_query("""
        MATCH (s:StudyActivityGroup)-[:AFTER|BEFORE]-(study_action)
        WHERE (s)-[:AFTER]-(study_action) and (s)-[:BEFORE]-(study_action)
        DETACH DELETE study_action
        RETURN *
        """)

    for rel in ["BEFORE", "AFTER"]:
        log.info(
            f"Migration: Removing duplicated {rel} StudyAction nodes for StudyActivityGroup nodes"
        )
        _ = db_connection.cypher_query(f"""
            MATCH (sag:StudyActivityGroup)-[:{rel}]-(action:StudyAction)
            WITH sag, collect(action) as actions WHERE size(actions) > 1
            CALL {{
                WITH sag
                MATCH (sag)-[:{rel}]-(action2:StudyAction)
                WITH sag, collect(action2) as actions2 WHERE size(actions2) > 1
                WITH sag, apoc.coll.sortNodes(actions2, 'date') as sorted_actions
                WITH tail(sorted_actions) as actions_to_delete
                FOREACH (n IN actions_to_delete | DETACH DELETE n)
            }} IN TRANSACTIONS
            return sag
            """)

    for group_class in ["StudyActivityGroup", "StudyActivitySubGroup"]:
        log.info(f"Migration: Removing incomplete Edits for {group_class} nodes")
        _ = db_connection.cypher_query(f"""
            MATCH (sasg:{group_class})<-[:BEFORE]-(edit:Edit)
            WHERE NOT (edit)-[:AFTER]->()
            DETACH DELETE edit
            """)


def remove_broken_study_activity_instances(db_connection, log):
    studies, _ = db_connection.cypher_query("""
        MATCH (study_root:StudyRoot) return study_root.uid
        """)
    for study in studies:
        study_uid = study[0]
        log.info(
            "Removing broken StudyActivityInstances for the following Study (%s)",
            study_uid,
        )
        _result, _ = db_connection.cypher_query(
            """
               MATCH (study_activity_instance:StudyActivityInstance)-[:BEFORE|AFTER]-(study_action:StudyAction)
               DETACH DELETE study_activity_instance, study_action
                """,
            params={"study_uid": study_uid},
        )


def migrate_nullify_unit_definition_name_sentence_case(db_connection, log):
    log.info(
        "Replace UnitDefinitionValue.name_sentence_case usage in Syntax Instances with UnitDefinitionValue.name"
    )
    db_connection.cypher_query("""
        MATCH (uv:UnitDefinitionValue)--(ur:UnitDefinitionRoot:TemplateParameterTermRoot)--(i:SyntaxInstanceValue)
        WHERE uv.name_sentence_case IS NOT NULL
        SET i.name = replace(i.name, "[" + uv.name_sentence_case + "]", "[" + uv.name + "]")
        SET i.name_plain = replace(i.name_plain, uv.name_sentence_case, uv.name)
        """)

    log.info("Nullifying UnitDefinitionValue.name_sentence_case")
    db_connection.cypher_query(
        "MATCH (uv:UnitDefinitionValue) SET uv.name_sentence_case = NULL"
    )


def migrate_missing_activity_item_class(db_connection, log):
    log.info(
        "Add missing HAS_ACTIVITY_ITEM relationship from ActivityItemClassRoot to ActivityItem"
    )
    db_connection.cypher_query("""
        MATCH (ai:ActivityItem) WHERE NOT (ai)<-[:HAS_ACTIVITY_ITEM]-()
        MATCH (aicr:ActivityItemClassRoot)-[:LATEST]->(aicv:ActivityItemClassValue {name: "test_name_code"})
        MERGE (aicr)-[:HAS_ACTIVITY_ITEM]->(ai) RETURN *
        """)


def migrate_remove_invalid_activity_instances(db_connection, log):
    log.info(
        "Removing invalid ActivityInstances that miss the HAS_ACTIVITY relationship"
    )
    db_connection.cypher_query("""
        MATCH (aiv:ActivityInstanceValue) WHERE NOT (aiv)-[:HAS_ACTIVITY]->(:ActivityGrouping) 
        MATCH (aiv)<-[]-(air:ActivityInstanceRoot)-[:CONTAINS_CONCEPT]-(:Library {name: "Sponsor"})
        OPTIONAL MATCH (aiv)-[:CONTAINS_ACTIVITY_ITEM]-(ai:ActivityItem)
        DETACH DELETE aiv, air, ai
        """)


if __name__ == "__main__":
    main()
