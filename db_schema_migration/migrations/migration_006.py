"""Schema migrations needed for release to PROD post Mar 2024."""

import os
from math import ceil, floor

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
MIGRATION_DESC = "schema-migration-release-1.6"


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])

    ### Common migrations
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_ct_config_values(DB_CONNECTION, logger)

    ### Release-specific migrations
    remove_broken_study_activity_instances(DB_DRIVER, logger)
    migrate_study_activity_instances(DB_DRIVER, logger)
    update_insertion_visit_to_manually_defined_visit(DB_DRIVER, logger)
    fix_study_week_property_for_negative_timings_less_than_one_week(
        DB_DRIVER, logger, MIGRATION_DESC
    )
    fix_duration_properties_for_visits_with_negative_timings(
        DB_DRIVER, logger, MIGRATION_DESC
    )
    fix_not_migrated_study_soa_groups(DB_DRIVER, logger, MIGRATION_DESC)
    merge_multiple_study_activity_subgroup_and_group_nodes(
        DB_DRIVER, logger, MIGRATION_DESC
    )
    migrate_study_selection_metadata_merge(DB_DRIVER, logger, MIGRATION_DESC)


def remove_broken_study_activity_instances(db_driver, log):
    studies, _ = run_cypher_query(
        db_driver,
        """
        MATCH (study_root:StudyRoot) return study_root.uid
        """,
    )
    for study in studies:
        study_uid = study[0]
        log.info(
            "Removing broken StudyActivityInstances for the following Study (%s)",
            study_uid,
        )
        _, _ = run_cypher_query(
            db_driver,
            """
               MATCH (study_activity_instance:StudyActivityInstance)-[:BEFORE|AFTER]-(study_action:StudyAction)
               DETACH DELETE study_activity_instance, study_action
                """,
            params={"study_uid": study_uid},
        )


def migrate_study_activity_instances(db_driver, log):
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
            "Migrating StudyActivityInstances for the following Study (%s)", study_uid
        )
        _, summary = run_cypher_query(
            db_driver,
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
                'MERGE (study_activity_instance)-[:HAS_SELECTED_ACTIVITY_INSTANCE]->(activity_instance_value) RETURN null'
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
        counters = summary.counters
        print_counters_table(counters)
        contains_updates.append(counters.contains_updates)
    return contains_updates


def update_insertion_visit_to_manually_defined_visit(db_driver, log):
    log.info(
        "Updating INSERTION_VISIT to MANUALLY_DEFINED_VISIT as visit_class property."
    )
    _, summary = run_cypher_query(
        db_driver,
        """
            MATCH (study_visit:StudyVisit) 
            WHERE study_visit.visit_class = "INSERTION_VISIT"
            SET study_visit.visit_class = "MANUALLY_DEFINED_VISIT"
        """,
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


def fix_study_week_property_for_negative_timings_less_than_one_week(
    db_driver, log, migration_description
):
    study_visits, _ = run_cypher_query(
        db_driver,
        """
        MATCH (study_visit:StudyVisit)-[:HAS_STUDY_DAY]->(:StudyDayRoot)-[:LATEST]->(study_day_value:StudyDayValue)
        MATCH (study_visit:StudyVisit)-[:HAS_STUDY_WEEK]->(:StudyWeekRoot)-[:LATEST]->(study_week_value:StudyWeekValue)
        WHERE study_day_value.value < 1
        RETURN study_visit.uid, study_day_value.value, study_week_value.value, elementId(study_visit)
    """,
    )
    contains_updates = []
    for study_visit in study_visits:
        study_visit_uid = study_visit[0]
        study_day_value = study_visit[1]
        study_week_value = study_visit[2]
        study_visit_element_id = study_visit[3]

        fixed_study_week_value = floor(study_day_value / 7)
        if fixed_study_week_value != study_week_value:
            log.info(
                "Fixing StudyVisits StudyWeek for %s Visit with negative timings from the following interval -7<value<0",
                study_visit_uid,
            )
            # StudyWeek
            study_week, _ = run_cypher_query(
                db_driver,
                """
                MATCH (study_visit:StudyVisit)
                WHERE elementId(study_visit)=$study_visit_element_id
                MATCH (study_visit:StudyVisit)-[:HAS_STUDY_WEEK]->(study_week_root:StudyWeekRoot)-[:LATEST]->(study_week_value:StudyWeekValue{value:$value})
                WHERE NOT (study_visit)-[:HAS_STUDY_WEEK]->(study_week_root)
                RETURN study_week_root.uid
            """,
                params={
                    "study_visit_element_id": study_visit_element_id,
                    "value": fixed_study_week_value,
                },
            )
            if study_week:
                _, summary = run_cypher_query(
                    db_driver,
                    """
                        MATCH (study_visit:StudyVisit)-[old_has_study_week:HAS_STUDY_WEEK]->(:StudyWeekRoot)
                        WHERE elementId(study_visit)=$study_visit_element_id
                        MATCH (new_study_week_node:StudyWeekRoot {uid:$study_week_uid})
                        MERGE (study_visit)-[:HAS_STUDY_WEEK]->(new_study_week_node)
                        DETACH DELETE old_has_study_week
                    """,
                    params={
                        "study_visit_element_id": study_visit_element_id,
                        "study_week_uid": study_week[0][0],
                    },
                )
            else:
                _, summary = run_cypher_query(
                    db_driver,
                    """
                        MATCH (study_visit:StudyVisit)-[old_has_study_week:HAS_STUDY_WEEK]->(:StudyWeekRoot)
                        WHERE elementId(study_visit)=$study_visit_element_id
                        // Create StudyWeek
                        CREATE (study_week_root:SimpleConceptRoot:ConceptRoot:NumericValueRoot:StudyWeekRoot:TemplateParameterTermRoot)
                        CREATE (study_week_value:SimpleConceptValue:ConceptValue:NumericValue:StudyWeekValue:TemplateParameterTermValue)
                        SET study_week_value.value=toFloat($study_week_value)
                        SET study_week_value.name='Week ' + toInteger($study_week_value)
                        SET study_week_value.name_sentence_case='week ' + toInteger($study_week_value)
                            MERGE (study_week_counter:Counter {counterId:'StudyWeekCounter'})
                            ON CREATE SET study_week_counter:StudyWeekCounter, study_week_counter.count=1
                            WITH *
                            CALL apoc.atomic.add(study_week_counter,'count',1,1) yield oldValue, newValue
                            WITH *, toInteger(newValue) as uid_number_study_week
                            SET study_week_root.uid = "StudyWeek_"+apoc.text.lpad(""+(uid_number_study_week), 6, "0")
                        MERGE (study_visit)-[:HAS_STUDY_WEEK]->(study_week_root)
                        DETACH DELETE old_has_study_week
                        WITH study_week_root, study_week_value
                        MATCH (sponsor_library:Library {name:'Sponsor'})
                        MERGE (sponsor_library)-[:CONTAINS_CONCEPT]->(study_week_root)
                        MERGE (study_week_root)-[:LATEST_FINAL]->(study_week_value)
                        MERGE (study_week_root)-[:LATEST]->(study_week_value)
                        MERGE (study_week_root)-[has_version:HAS_VERSION]->(study_week_value)
                        SET has_version.change_description=$migration_description
                        SET has_version.start_date=datetime()
                        SET has_version.status='Final'
                        SET has_version.user_initials=$migration_description
                        SET has_version.version='1.0'
                        MERGE (tp:TemplateParameter {
                            name: "StudyWeek"
                        })
                        MERGE (study_duration_weeks_root)<-[:HAS_PARAMETER_TERM]-(tp)
                    """,
                    params={
                        "study_visit_element_id": study_visit_element_id,
                        "study_week_value": fixed_study_week_value,
                        "migration_description": migration_description,
                    },
                )
            counters = summary.counters
            print_counters_table(counters)
            contains_updates.append(counters.contains_updates)
    return contains_updates


def fix_duration_properties_for_visits_with_negative_timings(
    db_driver, log, migration_description
):
    study_visits, _ = run_cypher_query(
        db_driver,
        """
        MATCH (study_visit:StudyVisit)-[:HAS_STUDY_DAY]->(:StudyDayRoot)-[:LATEST]->(study_day_value:StudyDayValue)
        MATCH (study_visit)-[:HAS_STUDY_DURATION_DAYS]->(:StudyDurationDaysRoot)-[:LATEST]->(study_duration_days_value:StudyDurationDaysValue)
        MATCH (study_visit)-[:HAS_STUDY_DURATION_WEEKS]->(:StudyDurationWeeksRoot)-[:LATEST]->(study_duration_weeks_value:StudyDurationWeeksValue)
        MATCH (study_visit)-[:HAS_WEEK_IN_STUDY]->(:WeekInStudyRoot)-[:LATEST]->(week_in_study_value:WeekInStudyValue)
        WHERE study_day_value.value < 1
        RETURN study_visit.uid, study_day_value.value, study_duration_days_value.value, study_duration_weeks_value.value, week_in_study_value.value, elementId(study_visit)
    """,
    )
    contains_updates = []
    for study_visit in study_visits:
        study_visit_uid = study_visit[0]
        study_day_value = study_visit[1]
        study_duration_days_value = study_visit[2]
        study_duration_weeks_value = study_visit[3]
        week_in_study_value = study_visit[4]
        study_visit_element_id = study_visit[5]

        # StudyDurationDays
        fixed_study_duration_days_value = study_day_value
        if fixed_study_duration_days_value != study_duration_days_value:
            log.info(
                "Fixing StudyVisits duration properties for %s Visit with negative timings",
                study_visit_uid,
            )
            study_duration_days, _ = run_cypher_query(
                db_driver,
                """
                MATCH (study_visit:StudyVisit)
                WHERE elementId(study_visit)=$study_visit_element_id
                MATCH (study_duration_days_root:StudyDurationDaysRoot)-[:LATEST]-(study_duration_days_value:StudyDurationDaysValue{value:$value})
                WHERE NOT (study_visit)-[:HAS_STUDY_DURATION_DAYS]->(study_duration_days_root)
                RETURN study_duration_days_root.uid
            """,
                params={
                    "study_visit_element_id": study_visit_element_id,
                    "value": fixed_study_duration_days_value,
                },
            )
            if study_duration_days:
                _, summary = run_cypher_query(
                    db_driver,
                    """
                        MATCH (study_visit:StudyVisit)-[old_study_duration_days:HAS_STUDY_DURATION_DAYS]->(:StudyDurationDaysRoot)
                        WHERE elementId(study_visit)=$study_visit_element_id
                        MATCH (new_study_duration_days_node:StudyDurationDaysRoot {uid:$study_duration_days_uid})
                        MERGE (study_visit)-[:HAS_STUDY_DURATION_DAYS]->(new_study_duration_days_node)
                        DETACH DELETE old_study_duration_days
                    """,
                    params={
                        "study_visit_element_id": study_visit_element_id,
                        "study_duration_days_uid": study_duration_days[0][0],
                    },
                )
            else:
                _, summary = run_cypher_query(
                    db_driver,
                    """
                        MATCH (study_visit:StudyVisit)-[old_has_study_duration_days:HAS_STUDY_DURATION_DAYS]->(:StudyDurationDaysRoot)
                        WHERE elementId(study_visit)=$study_visit_element_id
                        // Create StudyDurationDays
                        CREATE (study_duration_days_root:SimpleConceptRoot:ConceptRoot:NumericValueRoot:TemplateParameterTermRoot:StudyDurationDaysRoot)
                        CREATE (study_duration_days_value:SimpleConceptValue:ConceptValue:NumericValue:TemplateParameterTermValue:StudyDurationDaysValue)
                        SET study_duration_days_value.value=toFloat($fixed_study_duration_days_value)
                        SET study_duration_days_value.name=toInteger($fixed_study_duration_days_value) + ' days'
                        SET study_duration_days_value.name_sentence_case=toInteger($fixed_study_duration_days_value) + ' days'
                            MERGE (study_duration_days_counter:Counter {counterId:'StudyDurationDaysCounter'})
                            ON CREATE SET study_duration_days_counter:StudyDurationDaysCounter, study_duration_days_counter.count=1
                            WITH *
                            CALL apoc.atomic.add(study_duration_days_counter,'count',1,1) yield oldValue, newValue
                            WITH *, toInteger(newValue) as uid_number_study_duration_days
                            SET study_duration_days_root.uid = "StudyDurationDays_"+apoc.text.lpad(""+(uid_number_study_duration_days), 6, "0")
                        MERGE (study_visit)-[:HAS_STUDY_DURATION_DAYS]->(study_duration_days_root)
                        DETACH DELETE old_has_study_duration_days
                        WITH study_duration_days_root, study_duration_days_value
                        MATCH (sponsor_library:Library {name:'Sponsor'})
                        MERGE (sponsor_library)-[:CONTAINS_CONCEPT]->(study_duration_days_root)
                        MERGE (study_duration_days_root)-[:LATEST_FINAL]->(study_duration_days_value)
                        MERGE (study_duration_days_root)-[:LATEST]->(study_duration_days_value)
                        MERGE (study_duration_days_root)-[has_version:HAS_VERSION]->(study_duration_days_value)
                        SET has_version.change_description=$migration_description
                        SET has_version.start_date=datetime()
                        SET has_version.status='Final'
                        SET has_version.user_initials=$migration_description
                        SET has_version.version='1.0'
                        MERGE (tp:TemplateParameter {
                            name: "StudyDurationDays"
                        })
                        MERGE (study_duration_weeks_root)<-[:HAS_PARAMETER_TERM]-(tp)
                    """,
                    params={
                        "study_visit_element_id": study_visit_element_id,
                        "fixed_study_duration_days_value": fixed_study_duration_days_value,
                        "migration_description": migration_description,
                    },
                )
            counters = summary.counters
            print_counters_table(counters)
            contains_updates.append(counters.contains_updates)

        # StudyDurationWeeks
        fixed_study_duration_weeks_value = ceil(study_day_value / 7)
        if fixed_study_duration_weeks_value != study_duration_weeks_value:
            study_duration_weeks, _ = run_cypher_query(
                db_driver,
                """
                MATCH (study_visit:StudyVisit)
                WHERE elementId(study_visit)=$study_visit_element_id
                MATCH (study_duration_weeks_root:StudyDurationWeeksRoot)-[:LATEST]-(study_duration_weeks_value:StudyDurationWeeksValue{value:$value})
                WHERE NOT (study_visit)-[:HAS_STUDY_DURATION_WEEKS]->(study_duration_weeks_root)
                RETURN study_duration_weeks_root.uid
            """,
                params={
                    "study_visit_element_id": study_visit_element_id,
                    "value": fixed_study_duration_weeks_value,
                },
            )
            if study_duration_weeks:
                _, summary = run_cypher_query(
                    db_driver,
                    """
                        MATCH (study_visit:StudyVisit)-[old_study_duration_weeks:HAS_STUDY_DURATION_WEEKS]->(:StudyDurationWeeksRoot)
                        WHERE elementId(study_visit)=$study_visit_element_id
                        MATCH (new_study_duration_weeks_node:StudyDurationWeeksRoot {uid:$study_duration_weeks_uid})
                        MERGE (study_visit)-[:HAS_STUDY_DURATION_WEEKS]->(new_study_duration_weeks_node)
                        DETACH DELETE old_study_duration_weeks
                    """,
                    params={
                        "study_visit_element_id": study_visit_element_id,
                        "study_duration_weeks_uid": study_duration_weeks[0][0],
                    },
                )
            else:
                _, summary = run_cypher_query(
                    db_driver,
                    """
                        MATCH (study_visit:StudyVisit)-[old_has_study_duration_weeks:HAS_STUDY_DURATION_WEEKS]->(:StudyDurationWeeksRoot)
                        WHERE elementId(study_visit)=$study_visit_element_id
                        // Create StudyDurationWeeks
                        CREATE (study_duration_weeks_root:SimpleConceptRoot:ConceptRoot:NumericValueRoot:TemplateParameterTermRoot:StudyDurationWeeksRoot)
                        CREATE (study_duration_weeks_value:SimpleConceptValue:ConceptValue:NumericValue:TemplateParameterTermValue:StudyDurationWeeksValue)
                        SET study_duration_weeks_value.value=toFloat($fixed_study_duration_weeks_value)
                        SET study_duration_weeks_value.name=toInteger($fixed_study_duration_weeks_value) + ' weeks'
                        SET study_duration_weeks_value.name_sentence_case=toInteger($fixed_study_duration_weeks_value) + ' weeks'
                            MERGE (study_duration_weeks_counter:Counter {counterId:'StudyDurationWeeksCounter'})
                            ON CREATE SET study_duration_weeks_counter:StudyDurationWeeksCounter, study_duration_weeks_counter.count=1
                            WITH *
                            CALL apoc.atomic.add(study_duration_weeks_counter,'count',1,1) yield oldValue, newValue
                            WITH *, toInteger(newValue) as uid_number_study_duration_weeks
                            SET study_duration_weeks_root.uid = "StudyDurationWeeks_"+apoc.text.lpad(""+(uid_number_study_duration_weeks), 6, "0")
                        MERGE (study_visit)-[:HAS_STUDY_DURATION_WEEKS]->(study_duration_weeks_root)
                        DETACH DELETE old_has_study_duration_weeks
                        WITH study_duration_weeks_root, study_duration_weeks_value
                        MATCH (sponsor_library:Library {name:'Sponsor'})
                        MERGE (sponsor_library)-[:CONTAINS_CONCEPT]->(study_duration_weeks_root)
                        MERGE (study_duration_weeks_root)-[:LATEST_FINAL]->(study_duration_weeks_value)
                        MERGE (study_duration_weeks_root)-[:LATEST]->(study_duration_weeks_value)
                        MERGE (study_duration_weeks_root)-[has_version:HAS_VERSION]->(study_duration_weeks_value)
                        SET has_version.change_description=$migration_description
                        SET has_version.start_date=datetime()
                        SET has_version.status='Final'
                        SET has_version.user_initials=$migration_description
                        SET has_version.version='1.0'
                        MERGE (tp:TemplateParameter {
                            name: "StudyDurationWeeks"
                        })
                        MERGE (study_duration_weeks_root)<-[:HAS_PARAMETER_TERM]-(tp)
                    """,
                    params={
                        "study_visit_element_id": study_visit_element_id,
                        "fixed_study_duration_weeks_value": fixed_study_duration_weeks_value,
                        "migration_description": migration_description,
                    },
                )
            counters = summary.counters
            print_counters_table(counters)
            contains_updates.append(counters.contains_updates)

        # WeekInStudy
        fixed_week_in_study_value = ceil(study_day_value / 7)
        if fixed_week_in_study_value != week_in_study_value:
            week_in_study, _ = run_cypher_query(
                db_driver,
                """
                MATCH (study_visit:StudyVisit)
                WHERE elementId(study_visit)=$study_visit_element_id
                MATCH (week_in_study_root:WeekInStudyRoot)-[:LATEST]-(week_in_study_value:WeekInStudyValue{value:$value})
                WHERE NOT (study_visit)-[:HAS_WEEK_IN_STUDY]->(week_in_study_root)
                RETURN week_in_study_root.uid
            """,
                params={
                    "study_visit_element_id": study_visit_element_id,
                    "value": fixed_week_in_study_value,
                },
            )
            if week_in_study:
                _, summary = run_cypher_query(
                    db_driver,
                    """
                        MATCH (study_visit:StudyVisit)-[old_week_in_study:HAS_WEEK_IN_STUDY]->(:WeekInStudyRoot)
                        WHERE elementId(study_visit)=$study_visit_element_id
                        MATCH (new_week_in_study_root_node:WeekInStudyRoot {uid:$week_in_study_uid})
                        MERGE (study_visit)-[:HAS_WEEK_IN_STUDY]->(new_week_in_study_root_node)
                        DETACH DELETE old_week_in_study
                    """,
                    params={
                        "study_visit_element_id": study_visit_element_id,
                        "week_in_study_uid": week_in_study[0][0],
                    },
                )
            else:
                _, summary = run_cypher_query(
                    db_driver,
                    """
                        MATCH (study_visit:StudyVisit)-[old_has_week_in_study:HAS_WEEK_IN_STUDY]->(:WeekInStudyRoot)
                        WHERE elementId(study_visit)=$study_visit_element_id
                        // Create WeekInStudy
                        CREATE (week_in_study_root:SimpleConceptRoot:ConceptRoot:NumericValueRoot:TemplateParameterTermRoot:WeekInStudyRoot)
                        CREATE (week_in_study_value:SimpleConceptValue:ConceptValue:NumericValue:TemplateParameterTermValue:WeekInStudyValue)
                        SET week_in_study_value.value=toFloat($fixed_week_in_study_value)
                        SET week_in_study_value.name='Week ' + toInteger($fixed_week_in_study_value)
                        SET week_in_study_value.name_sentence_case='week ' + toInteger($fixed_week_in_study_value)
                            MERGE (week_in_study_counter:Counter {counterId:'WeekInStudyCounter'})
                            ON CREATE SET week_in_study_counter:WeekInStudyCounter, week_in_study_counter.count=1
                            WITH *
                            CALL apoc.atomic.add(week_in_study_counter,'count',1,1) yield oldValue, newValue
                            WITH *, toInteger(newValue) as uid_number_week_in_study
                            SET week_in_study_root.uid = "WeekInStudy_"+apoc.text.lpad(""+(uid_number_week_in_study), 6, "0")
                        MERGE (study_visit)-[:HAS_WEEK_IN_STUDY]->(week_in_study_root)
                        DETACH DELETE old_has_week_in_study
                        WITH week_in_study_root, week_in_study_value
                        MATCH (sponsor_library:Library {name:'Sponsor'})
                        MERGE (sponsor_library)-[:CONTAINS_CONCEPT]->(week_in_study_root)
                        MERGE (week_in_study_root)-[:LATEST_FINAL]->(week_in_study_value)
                        MERGE (week_in_study_root)-[:LATEST]->(week_in_study_value)
                        MERGE (week_in_study_root)-[has_version:HAS_VERSION]->(week_in_study_value)
                        SET has_version.change_description=$migration_description
                        SET has_version.start_date=datetime()
                        SET has_version.status='Final'
                        SET has_version.user_initials=$migration_description
                        SET has_version.version='1.0'
                        MERGE (tp:TemplateParameter {
                            name: "WeekInStudy"
                        })
                        MERGE (week_in_study_root)<-[:HAS_PARAMETER_TERM]-(tp)
                    """,
                    params={
                        "study_visit_element_id": study_visit_element_id,
                        "fixed_week_in_study_value": fixed_week_in_study_value,
                        "migration_description": migration_description,
                    },
                )
            counters = summary.counters
            print_counters_table(counters)
            contains_updates.append(counters.contains_updates)

    return contains_updates


def fix_not_migrated_study_soa_groups(db_driver, log, migration_desc):

    log.info("Migrate StudyActivity, SoAGroup information represented in the old way")
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (study_activity:StudyActivity)-[has_flowchart_group:HAS_FLOWCHART_GROUP]->(flowchart_group_term:CTTermRoot)
        WITH *,
            // each StudyActivity, even previous versions have exactly one AFTER relationship assigned from which we can take associated StudyRoot node
            head([(study_root:StudyRoot)-[:AUDIT_TRAIL]->(:StudyAction)-[:AFTER]->(study_activity) | study_root]) AS study_root,
            // If there exists already a StudySoAGroup linked to the flowchart_group_term referenced by the StudyActivity
            // we can reuse StudySoAGroup node
            head([(:StudyActivity {uid:study_activity.uid})-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]
            ->(existing_study_soa_group:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(existing_flowchart_group:CTTermRoot)
                | {existing_study_soa_group:existing_study_soa_group, existing_flowchart_group:existing_flowchart_group}]) AS existing_soa_group
        WITH *,
          existing_soa_group.existing_study_soa_group as existing_study_soa_group,
          existing_soa_group.existing_flowchart_group as existing_flowchart_group
        WHERE existing_flowchart_group = flowchart_group_term
        MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(existing_study_soa_group)
        DETACH DELETE has_flowchart_group
        """,
        params={"correction_desc": migration_desc},
    )
    first_part_counters = summary.counters
    print_counters_table(first_part_counters)

    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (study_activity:StudyActivity)-[:HAS_FLOWCHART_GROUP]->(flowchart_group_term:CTTermRoot)
        WITH *,
            // each StudyActivity, even previous versions have exactly one AFTER relationship assigned from which we can take associated StudyRoot node
            head([(study_root:StudyRoot)-[:AUDIT_TRAIL]->(:StudyAction)-[:AFTER]->(study_activity) | study_root]) AS study_root,
            // If there exists already a StudySoAGroup linked to the flowchart_group_term referenced by the StudyActivity
            // we can reuse StudySoAGroup node
            head([(:StudyActivity {uid:study_activity.uid})-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]
            ->(existing_study_soa_group:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(existing_flowchart_group:CTTermRoot)
                | {existing_study_soa_group:existing_study_soa_group, existing_flowchart_group:existing_flowchart_group}]) AS existing_soa_group
        WITH *,
          existing_soa_group.existing_study_soa_group as existing_study_soa_group,
          existing_soa_group.existing_flowchart_group as existing_flowchart_group
        WHERE existing_flowchart_group <> flowchart_group_term OR existing_flowchart_group IS NULL
        WITH DISTINCT study_activity.uid as study_activity_uid, flowchart_group_term, study_root
    
        // StudySoAGroup
        CREATE (study_soa_group:StudySoAGroup:StudySelectionMetadata)
            MERGE (study_soa_group_counter:Counter {counterId:'StudySoAGroupCounter'})
            ON CREATE SET study_soa_group_counter:StudySoAGroupCounter, study_soa_group_counter.count=1
            WITH *
            CALL apoc.atomic.add(study_soa_group_counter,'count',1,1) yield oldValue, newValue
            WITH *, toInteger(newValue) as uid_number_study_sog
            SET study_soa_group.uid = "StudySoAGroup_"+apoc.text.lpad(""+(uid_number_study_sog), 6, "0")
        WITH DISTINCT
            study_activity_uid,
            flowchart_group_term,
            study_root,
            study_soa_group
        MATCH (study_activity:StudyActivity {uid:study_activity_uid})-[has_flowchart_group:HAS_FLOWCHART_GROUP]->(flowchart_group_term)
        MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:$correction_desc, date:datetime()})-[:AFTER]->(study_soa_group)
        MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group)
        MERGE (study_soa_group)-[:HAS_FLOWCHART_GROUP]->(flowchart_group_term)
        DETACH DELETE has_flowchart_group

        """,
        params={"correction_desc": migration_desc},
    )
    second_part_counters = summary.counters
    print_counters_table(second_part_counters)
    return first_part_counters.contains_updates or first_part_counters.contains_updates


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
                study_soa_group,
                count(distinct flowchart_group_term_root) AS distinct_flowchart_group_count, 
                count(distinct study_soa_group) AS distinct_study_soa_group_count
            // condition to not perform migration twice
            WHERE distinct_flowchart_group_count <> distinct_study_soa_group_count OR study_soa_group.show_soa_group_in_protocol_flowchart IS NULL

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
            WHERE size(distinct_activity_group_root) <> size(distinct_study_activity_group) OR distinct_study_activity_group[0].show_activity_group_in_protocol_flowchart IS NULL

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
            WHERE size(distinct_activity_subgroup_root) <> size(distinct_study_activity_subgroup) OR distinct_study_activity_subgroup[0].show_activity_subgroup_in_protocol_flowchart IS NULL

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


def get_correct_groupings():
    correct_groupings = {
        "0": {
            # Albumin
            "StudyActivity_000396": {
                "correct_subgroup": "Biochemistry",
                "correct_group": "Laboratory Assessments",
            },
            # Medical History/Concomitant Illness
            "StudyActivity_000356": {
                "correct_subgroup": "Medical History/Concomitant Illness"
            },
            # Norepinephrine
            "StudyActivity_000433": {"correct_subgroup": "Urinalysis"},
        },
        "7611": {
            # Drug Dispensing
            "StudyActivity_000379": {
                "correct_subgroup": "Oral Anti-diabetic Drug",
                "correct_group": "Drug Dispensing",
            },
            "StudyActivity_000339": {
                "correct_subgroup": "Drug Accountability",
                "correct_group": "Drug Accountability",
            },
            # Billirubin
            "StudyActivity_000378": {
                "correct_subgroup": "Biochemistry",
                "correct_group": "Laboratory Assessments",
            },
            "StudyActivity_000293": {
                "correct_subgroup": "Biochemistry",
                "correct_group": "Laboratory Assessments",
            },
            # Erythrocytes
            "StudyActivity_000376": {
                "correct_subgroup": "Urinalysis",
                "correct_group": "Laboratory Assessments",
            },
            "StudyActivity_000278": {
                "correct_subgroup": "Urine Dipstick",
                "correct_group": "Laboratory Assessments",
            },
            # Glucose
            "StudyActivity_000375": {
                "correct_subgroup": "Glucose Metabolism",
                "correct_group": "Laboratory Assessments",
            },
            "StudyActivity_000306": {
                "correct_subgroup": "Urinalysis",
                "correct_group": "Laboratory Assessments",
            },
            # Albumin/Creatinine
            "StudyActivity_000374": {
                "correct_subgroup": "Biochemistry",
                "correct_group": "Laboratory Assessments",
            },
            # Creatinine
            "StudyActivity_000296": {
                "correct_subgroup": "Biochemistry",
                "correct_group": "Laboratory Assessments",
            },
            # Nitrite
            "StudyActivity_000312": {
                "correct_subgroup": "Urinalysis",
                "correct_group": "Laboratory Assessments",
            },
            # C Reactive Protein
            "StudyActivity_000297": {
                "correct_subgroup": "Biochemistry",
                "correct_group": "Laboratory Assessments",
            },
            # Hemoglobin
            "StudyActivity_000279": {"correct_subgroup": "Urinalysis"},
            # Potassium
            "StudyActivity_000300": {
                "correct_subgroup": "Urinalysis",
                "correct_group": "Laboratory Assessments",
            },
            # QT Interval, Aggregate
            "StudyActivity_000329": {"correct_subgroup": "ECG"},
            # ECG Mean Heart Rate
            "StudyActivity_000322": {"correct_subgroup": "ECG"},
            # Medical History/Concomitant Illness
            "StudyActivity_000268": {
                "correct_subgroup": "Medical History/Concomitant Illness"
            },
            # Alkaline Phosphatase
            "StudyActivity_000289": {
                "correct_subgroup": "Biochemistry",
                "correct_group": "Laboratory Assessments",
            },
            # pH
            "StudyActivity_000310": {
                "correct_subgroup": "Biochemistry",
                "correct_group": "Laboratory Assessments",
            },
            # Glomerular Filtration Rate, Estimated
            "StudyActivity_000304": {
                "correct_subgroup": "Biochemistry",
                "correct_group": "Laboratory Assessments",
            },
            # Albumin
            "StudyActivity_000288": {
                "correct_subgroup": "Biochemistry",
                "correct_group": "Laboratory Assessments",
            },
            # QTcF Interval, Aggregate
            "StudyActivity_000327": {"correct_subgroup": "ECG"},
            # QTcB Interval, Aggregate
            "StudyActivity_000326": {"correct_subgroup": "ECG"},
            # Protein
            "StudyActivity_000313": {
                "correct_subgroup": "Urinalysis",
                "correct_group": "Laboratory Assessments",
            },
            # QRS Duration, Aggregate
            "StudyActivity_000325": {"correct_subgroup": "Biochemistry"},
            # Platelets
            "StudyActivity_000282": {
                "correct_subgroup": "Haematology",
                "correct_group": "Laboratory Assessments",
            },
            # Urea
            "StudyActivity_000302": {"correct_subgroup": "Biochemistry"},
            # Leukocytes
            "StudyActivity_000377": {
                "correct_subgroup": "Haematology",
                "correct_group": "Laboratory Assessments",
            },
            "StudyActivity_000280": {
                "correct_subgroup": "Urinalysis",
                "correct_group": "Laboratory Assessments",
            },
            # Sodium
            "StudyActivity_000301": {
                "correct_subgroup": "Biochemistry",
                "correct_group": "Laboratory Assessments",
            },
            # Aspartate Aminotransferase
            "StudyActivity_000292": {
                "correct_subgroup": "Biochemistry",
                "correct_group": "Laboratory Assessments",
            },
            # PR Interval, Aggregate
            "StudyActivity_000323": {"correct_subgroup": "ECG"},
            # Alanine Aminotransferase
            "StudyActivity_000290": {
                "correct_subgroup": "Biochemistry",
                "correct_group": "Laboratory Assessments",
            },
            # Amylase
            "StudyActivity_000291": {
                "correct_subgroup": "Biochemistry",
                "correct_group": "Laboratory Assessments",
            },
            # Urea Nitrogen
            "StudyActivity_000294": {
                "correct_subgroup": "Urinalysis",
                "correct_group": "Laboratory Assessments",
            },
            # Interpretation
            "StudyActivity_000328": {"correct_subgroup": "ECG"},
            # Lipase
            "StudyActivity_000299": {
                "correct_subgroup": "Biochemistry",
                "correct_group": "Laboratory Assessments",
            },
            # Subject fasting
            "StudyActivity_000340": {
                "correct_subgroup": "Collection of Samples for Laboratory"
            },
            # Calcium
            "StudyActivity_000295": {"correct_subgroup": "Biochemistry"},
            # RR Interval, Aggregate
            "StudyActivity_000324": {"correct_subgroup": "ECG"},
        },
        "7727": {
            # Medical History/Concomitant Illness
            "StudyActivity_000425": {
                "correct_subgroup": "Medical History/Concomitant Illness"
            },
            # Technical Complaint
            "StudyActivity_000432": {"correct_subgroup": "Technical Complaints"},
        },
        "7890": {
            # Physical Examination
            "StudyActivity_000404": {"correct_subgroup": "Physical Examination"},
            # Medical History/Concomitant Illness
            "StudyActivity_000407": {
                "correct_subgroup": "Medical History/Concomitant Illness"
            },
            # Discontinuation Criteria
            "StudyActivity_000409": {"correct_subgroup": "Discontinuation Criteria"},
            # Drug Dispensing
            "StudyActivity_000416": {
                "correct_subgroup": "Drug Accountability",
                "correct_group": "Drug Accountability",
            },
            "StudyActivity_000417": {
                "correct_subgroup": "Oral Anti-diabetic Drug",
                "correct_group": "Drug Dispensing",
            },
        },
        "7822": {
            # Medical History/Concomitant Illness
            "StudyActivity_000470": {
                "correct_subgroup": "Medical History/Concomitant Illness"
            },
            # Physical Examination
            "StudyActivity_000472": {"correct_subgroup": "Physical Examination"},
            # ECG Mean Heart Rate
            "StudyActivity_000475": {"correct_subgroup": "ECG"},
        },
    }
    return correct_groupings


def merge_multiple_study_activity_subgroup_and_group_nodes(
    db_driver, log, migration_desc
):
    studies = get_correct_groupings()
    contains_updates = []
    for study_number, activities_to_migrate in studies.items():
        for study_activity_uid, correct_groupings in activities_to_migrate.items():
            # StudyActivityGroup
            corrected_group = correct_groupings.get("correct_group")
            if corrected_group:
                log.info(
                    "Merging StudyActivityGroup nodes for the following StudyActivity (%s) in a Study (%s)",
                    study_activity_uid,
                    study_number,
                )
                _, summary = run_cypher_query(
                    db_driver,
                    """
                    MATCH (study_activity:StudyActivity {uid:$study_activity_uid})-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
                    //WITH study_activity, collect(study_activity_group) as sags
                    //WHERE size(sags) > 1
                    MATCH (correct_group_root:ActivityGroupRoot)-[:LATEST]->(agv:ActivityGroupValue {name:$correct_group})
                    //UNWIND sags as study_activity_group
                    WITH study_activity,
                        head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(correct_study_activity_group:StudyActivityGroup)
                        -[:HAS_SELECTED_ACTIVITY_GROUP]->(:ActivityGroupValue)<-[:HAS_VERSION]-(correct_group_root) | correct_study_activity_group]) as correct_study_activity_group,
                        collect(study_activity_group) as study_activity_groups,
                        agv
                    WITH 
                        study_activity,
                        correct_study_activity_group,
                        head([(study_root)-[:AUDIT_TRAIL]->(:StudyAction)-[:AFTER]->(study_activity) | study_root]) as study_root,
                        [sag in study_activity_groups WHERE sag <> coalesce(correct_study_activity_group, false)] as study_activity_group_to_remove,
                        agv

                    CALL apoc.do.case([
                        // StudyActivityGroup linked to correct ActivityGroup wasn't found in multiple StudyActivityGroups linked to StudyActivity
                        // it has to be created
                        correct_study_activity_group IS NULL,
                        '
                        CREATE (study_activity_group:StudyActivityGroup:StudySelectionMetadata)
                            MERGE (study_activity_group_counter:Counter {counterId:"StudyActivityGroupCounter"})
                            ON CREATE SET study_activity_group_counter:StudyActivityGroupCounter, study_activity_group_counter.count=1
                            WITH *
                            CALL apoc.atomic.add(study_activity_group_counter,"count",1,1) yield oldValue, newValue
                            WITH *, toInteger(newValue) as uid_number_study_activity_group
                            SET study_activity_group.uid = "StudyActivityGroup_"+apoc.text.lpad(""+(uid_number_study_activity_group), 6, "0")
                        MERGE (study_activity_group)-[:HAS_SELECTED_ACTIVITY_GROUP]->(agv)
                        MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group)
                        MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:$migration_desc, date:datetime()})-[:AFTER]->(study_activity_group)
                        RETURN *
                        '
                    ],
                    'RETURN *',
                    {
                        study_activity:study_activity,
                        correct_study_activity_group: correct_study_activity_group,
                        study_root: study_root,
                        migration_desc: $migration_desc,
                        agv:agv
                    }
                    ) yield value

                    UNWIND study_activity_group_to_remove as sag_to_remove
                    DETACH DELETE sag_to_remove
                    """,
                    params={
                        "study_activity_uid": study_activity_uid,
                        "correct_group": corrected_group,
                        "migration_desc": migration_desc,
                    },
                )
                counters = summary.counters
                print_counters_table(counters)
                contains_updates.append(counters.contains_updates)

            # StudyActivitySubGroup
            corrected_subgroup = correct_groupings.get("correct_subgroup")
            if corrected_subgroup:
                log.info(
                    "Merging StudyActivitySubGroup nodes for the following StudyActivity (%s) in a Study (%s)",
                    study_activity_uid,
                    study_number,
                )
                _, summary = run_cypher_query(
                    db_driver,
                    """
                    MATCH (study_activity:StudyActivity {uid:$study_activity_uid})-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
                    //WITH study_activity, collect(study_activity_subgroup) as sasgs
                    //WHERE size(sasgs) > 1
                    MATCH (correct_subgroup_root:ActivitySubGroupRoot)-[:LATEST]->(asgv:ActivitySubGroupValue {name:$correct_subgroup})
                    //UNWIND sasgs as study_activity_subgroup
                    WITH study_activity,
                        head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(correct_study_activity_subgroup:StudyActivitySubGroup)
                        -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(:ActivitySubGroupValue)<-[:HAS_VERSION]-(correct_subgroup_root) | correct_study_activity_subgroup]) as correct_study_activity_subgroup,
                        collect(study_activity_subgroup) as study_activity_subgroups,
                        asgv
                    WITH 
                        study_activity,
                        correct_study_activity_subgroup,
                        head([(study_root)-[:AUDIT_TRAIL]->(:StudyAction)-[:AFTER]->(study_activity) | study_root]) as study_root,
                        [sasg in study_activity_subgroups WHERE sasg <> coalesce(correct_study_activity_subgroup, false)] as study_activity_subgroup_to_remove,
                        asgv

                    CALL apoc.do.case([
                        // StudyActivitySubGroup linked to correct ActivitySubGroup wasn't found in multiple StudyActivitySubGroups linked to StudyActivity
                        // it has to be created
                        correct_study_activity_subgroup IS NULL,
                        '
                        CREATE (study_activity_subgroup:StudyActivitySubGroup:StudySelectionMetadata)
                            MERGE (study_activity_subgroup_counter:Counter {counterId:"StudyActivitySubGroupCounter"})
                            ON CREATE SET study_activity_subgroup_counter:StudyActivitySubGroupCounter, study_activity_subgroup_counter.count=1
                            WITH *
                            CALL apoc.atomic.add(study_activity_subgroup_counter,"count",1,1) yield oldValue, newValue
                            WITH *, toInteger(newValue) as uid_number_study_activity_subgroup
                            SET study_activity_subgroup.uid = "StudyActivitySubGroup_"+apoc.text.lpad(""+(uid_number_study_activity_subgroup), 6, "0")
                        MERGE (study_activity_subgroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(asgv)
                        MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup)
                        MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:$migration_desc, date:datetime()})-[:AFTER]->(study_activity_subgroup)
                        RETURN *
                        '
                    ],
                    'RETURN *',
                    {
                        study_activity:study_activity,
                        correct_study_activity_subgroup: correct_study_activity_subgroup,
                        study_root: study_root,
                        migration_desc: $migration_desc,
                        asgv: asgv
                    }
                    ) yield value

                    UNWIND study_activity_subgroup_to_remove as sasg_to_remove
                    DETACH DELETE sasg_to_remove
                    """,
                    params={
                        "study_activity_uid": study_activity_uid,
                        "correct_subgroup": corrected_subgroup,
                        "migration_desc": migration_desc,
                    },
                )
                counters = summary.counters
                print_counters_table(counters)
                contains_updates.append(counters.contains_updates)

    # StudyActivityGroup
    study_activities, _ = run_cypher_query(
        db_driver,
        """
        MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
        WITH study_activity, collect(study_activity_group) as sags
        WHERE size(sags) > 1 AND NOT (study_activity)--(:StudyValue)
        RETURN DISTINCT study_activity.uid
        """,
    )
    for study_activity in study_activities:
        study_activity_uid = study_activity[0]
        log.info(
            "Removing unwanted StudyActivityGroup nodes for the following StudyActivity (%s)",
            study_activity_uid,
        )

        _, summary = run_cypher_query(
            db_driver,
            """
            MATCH (last_study_activity:StudyActivity {uid:$study_activity_uid})
            WHERE NOT (last_study_activity)<-[:BEFORE]-()
            WITH last_study_activity, 
             head([(last_study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup) | study_activity_group]) as last_study_activity_group
            MATCH (study_activity:StudyActivity {uid:$study_activity_uid})-[old_rel:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
            DETACH DELETE old_rel
            MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(last_study_activity_group)
            """,
            params={"study_activity_uid": study_activity_uid},
        )
        counters = summary.counters
        print_counters_table(counters)

    # StudyActivitySubGroup
    study_activities, _ = run_cypher_query(
        db_driver,
        """
        MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
        WITH study_activity, collect(study_activity_subgroup) as sags
        WHERE size(sags) > 1 AND NOT (study_activity)--(:StudyValue)
        RETURN DISTINCT study_activity.uid
        """,
    )
    for study_activity in study_activities:
        study_activity_uid = study_activity[0]
        log.info(
            "Removing unwanted StudyActivitySubGroup nodes for the following StudyActivity (%s)",
            study_activity_uid,
        )
        _, summary = run_cypher_query(
            db_driver,
            """
            MATCH (last_study_activity:StudyActivity {uid:$study_activity_uid})
            WHERE NOT (last_study_activity)<-[:BEFORE]-()
            WITH last_study_activity, 
             head([(last_study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup) | study_activity_subgroup]) as last_study_activity_subgroup
            MATCH (study_activity:StudyActivity {uid:$study_activity_uid})-[old_rel:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
            DETACH DELETE old_rel
            MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(last_study_activity_subgroup)
            """,
            params={"study_activity_uid": study_activity_uid},
        )
        counters = summary.counters
        print_counters_table(counters)
    contains_updates.append(counters.contains_updates)

    return contains_updates


if __name__ == "__main__":
    main()
