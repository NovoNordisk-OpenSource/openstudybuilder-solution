"""PRD Data Corrections, for release 1.12"""

import os

from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    print_counters_table,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import api_get, api_post, get_logger
from verifications import correction_verification_011

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-release-1.12"


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    correct_study_visit_timing_related_nodes(DB_DRIVER, LOGGER, run_label)
    remove_empty_strings_or_replace_them_with_not_provided_text(
        DB_DRIVER, LOGGER, run_label
    )
    migrate_study_selection_metadata_merge(DB_DRIVER, LOGGER, run_label)


@capture_changes(
    verify_func=correction_verification_011.test_correct_study_visit_timing_related_nodes
)
def correct_study_visit_timing_related_nodes(db_driver, log, run_label):
    """
    ### Problem description
    The `StudyDay`, `StudyDurationDays`, `StudyWeek`, `StudyDurationWeeks`, `WeekInStudy` nodes containing information about absolute StudyVisit timing information were based on
        relative timing to the chosen anchor Visit. If StudyVisit is referencing global anchor visit, the timing related nodes are fine.
    If StudyVisit refers to something else, then the timing related nodes are potentially affected.

    ### Change description
    Creates new `StudyDay`, `StudyDurationDays`, `StudyWeek`, `StudyDurationWeeks`, `WeekInStudy` nodes if they don't exist for specific value
    or finds the existing ones and reconnects StudyVisits to reliable timing related nodes.

    ### Nodes and relationships affected
    - `StudyVisit` nodes where timinig related relationships
        (`HAS_STUDY_DAY`, `HAS_STUDY_DURATION_DAYS`, `HAS_STUDY_WEEK`, `HAS_STUDY_DURATION_WEEKS`, `HAS_WEEK_IN_STUDY`) were pointing wrong timing values.
    - Expected changes: 58 StudyVisits affected, for each StudyVisit updated 5 different timing related relationships.
    """

    studies, _ = run_cypher_query(
        db_driver,
        """
        MATCH (study_root:StudyRoot)-[:LATEST]->(study_value:StudyValue)
        WHERE NOT (study_root)-[:LATEST_LOCKED]-(study_value)
        MATCH (study_value)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit)-[:HAS_TIMEPOINT]->(:TimePointRoot)-[:LATEST]->(:TimePointValue)
            -[:HAS_TIME_REFERENCE]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue)
        MATCH (study_visit)-[:HAS_STUDY_DAY]->(:StudyDayRoot)-[:LATEST]->(study_day_value:StudyDayValue)
        MATCH (study_visit)-[:HAS_STUDY_DURATION_DAYS]->(:StudyDurationDaysRoot)-[:LATEST]->(study_duration_days_value:StudyDurationDaysValue)
        MATCH (study_visit)-[:HAS_STUDY_WEEK]->(:StudyWeekRoot)-[:LATEST]->(study_week_value:StudyWeekValue)
        MATCH (study_visit)-[:HAS_STUDY_DURATION_WEEKS]->(:StudyDurationWeeksRoot)-[:LATEST]->(study_duration_weeks_value:StudyDurationWeeksValue)
        MATCH (study_visit)-[:HAS_WEEK_IN_STUDY]->(:WeekInStudyRoot)-[:LATEST]->(week_in_study_value:WeekInStudyValue)
        WHERE NOT (study_visit)-[:BEFORE]-() and term_name_value.name <> "Global anchor visit" and study_visit.is_global_anchor_visit = false
        RETURN DISTINCT study_visit.uid, 
                        study_root.uid AS study_uid, 
                        coalesce(study_value.study_id_prefix, "") + "-" + toString(study_value.study_number) AS study_id,
                        study_day_value.value AS study_day_number,
                        study_duration_days_value.value AS study_duration_days_number,
                        study_week_value.value AS study_week_number,
                        study_duration_weeks_value.value AS study_duration_weeks_number,
                        week_in_study_value.value AS week_in_study_number

        """,
    )

    contains_updates = []
    for study in studies:
        study_visit_uid = study[0]
        study_uid = study[1]
        study_id = study[2]
        current_study_day_number = study[3]
        current_study_duration_days_number = study[4]
        current_study_week_number = study[5]
        current_study_duration_weeks_number = study[6]
        current_week_in_study_number = study[7]
        log.info(
            "Fixing StudyVisit timing related nodes for StudyVisit (%s) in a (%s) Study",
            study_visit_uid,
            study_id,
        )
        study_visit = api_get(
            f"/studies/{study_uid}/study-visits/{study_visit_uid}"
        ).json()
        study_day_number = study_visit["study_day_number"]
        study_duration_days_number = study_visit["study_duration_days"]
        study_week_number = study_visit["study_week_number"]
        study_duration_weeks_number = study_visit["study_duration_weeks"]

        # StudyDay
        if current_study_day_number != study_day_number:
            study_day, _ = run_cypher_query(
                db_driver,
                """
                MATCH (study_visit:StudyVisit {uid:$study_visit_uid})
                WHERE NOT (study_visit)-[:BEFORE]-()
                MATCH (study_day_root:StudyDayRoot)-[:LATEST]->(study_day_value:StudyDayValue{value:$value})
                WHERE NOT (study_visit)-[:HAS_STUDY_DAY]->(study_day_root)
                RETURN study_day_root.uid
                """,
                params={
                    "study_visit_uid": study_visit_uid,
                    "value": study_day_number,
                },
            )
            if study_day:
                study_day_uid = study_day[0][0]
            else:
                study_day_uid = api_post(
                    "/concepts/study-days",
                    payload={
                        "value": study_day_number,
                        "template_parameter": True,
                        "library_name": "Sponsor",
                    },
                ).json()["uid"]
            _, summary = run_cypher_query(
                db_driver,
                """
                    MATCH (study_visit:StudyVisit {uid:$study_visit_uid})-[old_has_study_day:HAS_STUDY_DAY]->(:StudyDayRoot)
                    WHERE NOT (study_visit)-[:BEFORE]-()
                    MATCH (new_study_day_node:StudyDayRoot {uid:$study_day_uid})
                    MERGE (study_visit)-[:HAS_STUDY_DAY]->(new_study_day_node)
                    DETACH DELETE old_has_study_day
                """,
                params={
                    "study_visit_uid": study_visit_uid,
                    "study_day_uid": study_day_uid,
                },
            )
            counters = summary.counters
            contains_updates.append(counters.contains_updates)

        # StudyDurationDays
        if current_study_duration_days_number != study_duration_days_number:
            study_duration_days, _ = run_cypher_query(
                db_driver,
                """
                MATCH (study_visit:StudyVisit {uid:$study_visit_uid})
                WHERE NOT (study_visit)-[:BEFORE]-()
                MATCH (study_duration_days_root:StudyDurationDaysRoot)-[:LATEST]->(study_duration_days_value:StudyDurationDaysValue{value:$value})
                WHERE NOT (study_visit)-[:HAS_STUDY_DURATION_DAYS]->(study_duration_days_root)
                RETURN study_duration_days_root.uid
                """,
                params={
                    "study_visit_uid": study_visit_uid,
                    "value": study_duration_days_number,
                },
            )
            if study_duration_days:
                study_duration_days_uid = study_duration_days[0][0]
            else:
                study_duration_days_uid = api_post(
                    "/concepts/study-duration-days",
                    payload={
                        "value": study_duration_days_number,
                        "template_parameter": True,
                        "library_name": "Sponsor",
                    },
                ).json()["uid"]
            _, summary = run_cypher_query(
                db_driver,
                """
                    MATCH (study_visit:StudyVisit {uid:$study_visit_uid})-[old_has_study_duration_days:HAS_STUDY_DURATION_DAYS]->(:StudyDurationDaysRoot)
                    WHERE NOT (study_visit)-[:BEFORE]-()
                    MATCH (new_study_duration_days_node:StudyDurationDaysRoot {uid:$study_duration_days_uid})
                    MERGE (study_visit)-[:HAS_STUDY_DURATION_DAYS]->(new_study_duration_days_node)
                    DETACH DELETE old_has_study_duration_days
                """,
                params={
                    "study_visit_uid": study_visit_uid,
                    "study_duration_days_uid": study_duration_days_uid,
                },
            )

            counters = summary.counters
            contains_updates.append(counters.contains_updates)

        # StudyWeek
        if current_study_week_number != study_week_number:
            study_week, _ = run_cypher_query(
                db_driver,
                """
                MATCH (study_visit:StudyVisit {uid:$study_visit_uid})
                WHERE NOT (study_visit)-[:BEFORE]-()
                MATCH (study_week_root:StudyWeekRoot)-[:LATEST]->(study_week_value:StudyWeekValue{value:$value})
                WHERE NOT (study_visit)-[:HAS_STUDY_WEEK]->(study_week_root)
                RETURN study_week_root.uid
                """,
                params={
                    "study_visit_uid": study_visit_uid,
                    "value": study_week_number,
                },
            )
            if study_week:
                study_week_uid = study_week[0][0]
            else:
                study_week_uid = api_post(
                    "/concepts/study-weeks",
                    payload={
                        "value": study_week_number,
                        "template_parameter": True,
                        "library_name": "Sponsor",
                    },
                ).json()["uid"]
            _, summary = run_cypher_query(
                db_driver,
                """
                    MATCH (study_visit:StudyVisit {uid:$study_visit_uid})-[old_has_study_week:HAS_STUDY_WEEK]->(:StudyWeekRoot)
                    WHERE NOT (study_visit)-[:BEFORE]-()
                    MATCH (new_study_week_node:StudyWeekRoot {uid:$study_week_uid})
                    MERGE (study_visit)-[:HAS_STUDY_WEEK]->(new_study_week_node)
                    DETACH DELETE old_has_study_week
                """,
                params={
                    "study_visit_uid": study_visit_uid,
                    "study_week_uid": study_week_uid,
                },
            )

            counters = summary.counters
            contains_updates.append(counters.contains_updates)

        # StudyDurationWeeks
        if current_study_duration_weeks_number != study_duration_weeks_number:
            study_duration_weeks, _ = run_cypher_query(
                db_driver,
                """
                MATCH (study_visit:StudyVisit {uid:$study_visit_uid})
                WHERE NOT (study_visit)-[:BEFORE]-()
                MATCH (study_duration_weeks_root:StudyDurationWeeksRoot)-[:LATEST]->(study_duration_weeks_value:StudyDurationWeeksValue{value:$value})
                WHERE NOT (study_visit)-[:HAS_STUDY_DURATION_WEEKS]->(study_duration_weeks_root)
                RETURN study_duration_weeks_root.uid
                """,
                params={
                    "study_visit_uid": study_visit_uid,
                    "value": study_duration_weeks_number,
                },
            )
            if study_duration_weeks:
                study_duration_weeks_uid = study_duration_weeks[0][0]
            else:
                study_duration_weeks_uid = api_post(
                    "/concepts/study-duration-weeks",
                    payload={
                        "value": study_duration_weeks_number,
                        "template_parameter": True,
                        "library_name": "Sponsor",
                    },
                ).json()["uid"]
            _, summary = run_cypher_query(
                db_driver,
                """
                    MATCH (study_visit:StudyVisit {uid:$study_visit_uid})-[old_has_study_duration_weeks:HAS_STUDY_DURATION_WEEKS]->(:StudyDurationWeeksRoot)
                    WHERE NOT (study_visit)-[:BEFORE]-()
                    MATCH (new_study_duration_weeks_node:StudyDurationWeeksRoot {uid:$study_duration_weeks_uid})
                    MERGE (study_visit)-[:HAS_STUDY_DURATION_WEEKS]->(new_study_duration_weeks_node)
                    DETACH DELETE old_has_study_duration_weeks
                """,
                params={
                    "study_visit_uid": study_visit_uid,
                    "study_duration_weeks_uid": study_duration_weeks_uid,
                },
            )

            counters = summary.counters
            contains_updates.append(counters.contains_updates)

        # WeekInStudy contains the same number as StudyDurationWeeks
        # It must be manuall created as week in study doesn't expose enpoints
        if current_week_in_study_number != study_duration_weeks_number:
            week_in_study, _ = run_cypher_query(
                db_driver,
                """
                MATCH (study_visit:StudyVisit {uid:$study_visit_uid})
                WHERE NOT (study_visit)-[:BEFORE]-()
                MATCH (week_in_study_root:WeekInStudyRoot)-[:LATEST]->(week_in_study_value:WeekInStudyValue{value:$value})
                WHERE NOT (study_visit)-[:HAS_WEEK_IN_STUDY]->(week_in_study_root)
                RETURN week_in_study_root.uid
                """,
                params={
                    "study_visit_uid": study_visit_uid,
                    "value": study_duration_weeks_number,
                },
            )
            if week_in_study:
                _, summary = run_cypher_query(
                    db_driver,
                    """
                        MATCH (study_visit:StudyVisit {uid:$study_visit_uid})-[old_has_week_in_study:HAS_WEEK_IN_STUDY]->(:WeekInStudyRoot)
                        WHERE NOT (study_visit)-[:BEFORE]-()
                        MATCH (new_week_in_study_node:WeekInStudyRoot {uid:$week_in_study_uid})
                        MERGE (study_visit)-[:HAS_WEEK_IN_STUDY]->(new_week_in_study_node)
                        DETACH DELETE old_has_week_in_study
                    """,
                    params={
                        "study_visit_uid": study_visit_uid,
                        "week_in_study_uid": week_in_study[0][0],
                    },
                )
            else:
                _, summary = run_cypher_query(
                    db_driver,
                    """
                        MATCH (study_visit:StudyVisit {uid:$study_visit_uid})-[old_has_week_in_study:HAS_WEEK_IN_STUDY]->(:WeekInStudyRoot)
                        WHERE NOT (study_visit)-[:BEFORE]-()
                        // Create WeekInStudy
                        CREATE (week_in_study_root:SimpleConceptRoot:ConceptRoot:NumericValueRoot:WeekInStudyRoot:TemplateParameterTermRoot)
                        CREATE (week_in_study_value:SimpleConceptValue:ConceptValue:NumericValue:WeekInStudyValue:TemplateParameterTermValue)
                        SET week_in_study_value.value=toFloat($week_in_study_value)
                        SET week_in_study_value.name='Week ' + toInteger($week_in_study_value)
                        SET week_in_study_value.name_sentence_case='week ' + toInteger($week_in_study_value)
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
                        SET has_version.change_description=$run_label
                        SET has_version.start_date=datetime()
                        SET has_version.status='Final'
                        SET has_version.user_initials=$run_label
                        SET has_version.version='1.0'
                        MERGE (tp:TemplateParameter {
                            name: "WeekInStudy"
                        })
                        MERGE (week_in_study_root)<-[:HAS_PARAMETER_TERM]-(tp)
                    """,
                    params={
                        "study_visit_uid": study_visit_uid,
                        "week_in_study_value": study_duration_weeks_number,
                        "run_label": run_label,
                    },
                )

            counters = summary.counters
            contains_updates.append(counters.contains_updates)
    return contains_updates


@capture_changes(
    verify_func=correction_verification_011.test_remove_empty_strings_or_replace_them_with_not_provided_text
)
def remove_empty_strings_or_replace_them_with_not_provided_text(
    db_driver, log, run_label
):
    """
    ### Problem description
    Some nodes in the database have properties with empty string values. These empty strings are unnecessary and leads to inconsistencies.

    ### Change description
    - For specific properties in certain node types, remove the property if its value is an empty string.
    - For other properties, replace the empty string value with the text "not provided".

    ### Nodes and relationships affected
    - Nodes with the following labels and properties will have the property removed if its value is an empty string:
        - ConceptValue: definition, abbreviation
        - ActivityInstanceValue: legacy_description, topic_code, nci_concept_id
        - ActivityInstanceClassValue: definition
        - ActivityItemClassValue: nci_concept_id
        - OdmDescriptionValue: sponsor_instruction, instruction
        - CriteriaTemplateValue: guidance_text
        - StudyEpoch: start_rule, end_rule, description
        - StudyVisit: start_rule, end_rule, description
        - StudyArm: description, randomization_group, arm_code
        - UnitDefinitionValue: comment
        - OdmItemGroupValue: comment
        - OdmItemValue: comment, prompt
        - CTTermAttributesValue: preferred_term
        - DictionaryTermValue: abbreviation
    - Nodes with the following labels and properties will have the empty string value replaced with "not provided":
        - CTTermAttributesValue: definition
        - CTCodelistAttributesValue: definition
    """

    desc = "Remove empty strings or replace them with 'not provided' text"
    log.info(f"Run: {run_label}, {desc}")

    contains_updates = []

    properties_to_remove = [
        ("ConceptValue", "definition"),
        ("ConceptValue", "abbreviation"),
        ("ActivityInstanceValue", "legacy_description"),
        ("ActivityInstanceValue", "topic_code"),
        ("ActivityInstanceValue", "nci_concept_id"),
        ("ActivityInstanceClassValue", "definition"),
        ("ActivityItemClassValue", "nci_concept_id"),
        ("OdmDescriptionValue", "sponsor_instruction"),
        ("OdmDescriptionValue", "instruction"),
        ("CriteriaTemplateValue", "guidance_text"),
        ("StudyEpoch", "start_rule"),
        ("StudyVisit", "start_rule"),
        ("StudyEpoch", "end_rule"),
        ("StudyVisit", "end_rule"),
        ("StudyEpoch", "description"),
        ("StudyVisit", "description"),
        ("StudyArm", "description"),
        ("StudyArm", "randomization_group"),
        ("StudyArm", "arm_code"),
        ("UnitDefinitionValue", "comment"),
        ("OdmItemGroupValue", "comment"),
        ("OdmItemValue", "comment"),
        ("OdmItemValue", "prompt"),
        ("CTTermAttributesValue", "preferred_term"),
        ("DictionaryTermValue", "abbreviation"),
    ]

    for label, prop in properties_to_remove:
        _, summary = run_cypher_query(
            db_driver,
            f"""
            MATCH (n:{label})
            WHERE n.{prop} = ""
            REMOVE n.{prop}
            """,
        )

        counters = summary.counters
        contains_updates.append(counters.contains_updates)

    properties_to_update = [
        ("CTTermAttributesValue", "definition"),
        ("CTCodelistAttributesValue", "definition"),
    ]

    for label, prop in properties_to_update:
        _, summary = run_cypher_query(
            db_driver,
            f"""
            MATCH (n:{label})
            WHERE n.{prop} = ""
            SET n.{prop} = "not provided"
            """,
        )

        counters = summary.counters
        contains_updates.append(counters.contains_updates)

    return contains_updates


@capture_changes(task_level=1)
def migrate_study_soa_groups(db_driver, log, study_uid):
    log.info(
        "Merging StudySoAGroup nodes for the following Study (%s)",
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
            count(distinct study_soa_group) AS distinct_study_soa_group_count, 
            any(vis IN collect(study_soa_group.show_soa_group_in_protocol_flowchart) WHERE vis=true) AS is_visible,
            // picking min order as if study_soa_group nodes are duplicated the first order number will describe the real order it should have
            min(study_soa_group.order) as order_number
        // condition to not perform migration twice
        WHERE distinct_flowchart_group_count <> distinct_study_soa_group_count

        // leave only a few rows that will represent distinct CTTermRoots that represent chosen SoA/Flowchart group
        WITH DISTINCT flowchart_group_term_root, is_visible, order_number

        // CREATE new StudySoAGroup node for each row of a distinct flowchart_group_term_root 
        CREATE (study_soa_group_new:StudySoAGroup:StudySelection)
        MERGE (study_soa_group_counter:Counter {counterId:'StudySoAGroupCounter'})
        ON CREATE SET study_soa_group_counter:StudySoAGroupCounter, study_soa_group_counter.count=1
        WITH flowchart_group_term_root,study_soa_group_new,study_soa_group_counter, is_visible, order_number
        CALL apoc.atomic.add(study_soa_group_counter,'count',1,1) yield oldValue, newValue
        WITH flowchart_group_term_root,study_soa_group_new, toInteger(newValue) as uid_number_study_sog, is_visible, order_number
        SET study_soa_group_new.uid = "StudySoAGroup_"+apoc.text.lpad(""+(uid_number_study_sog), 6, "0")
        SET study_soa_group_new.order=order_number
        WITH flowchart_group_term_root, study_soa_group_new, is_visible

        // MATCH all StudyActivity nodes that had 'old' StudySoAGroups that were using a flowchart_group_term_root
        MATCH (flowchart_group_term_root)<-[:HAS_FLOWCHART_GROUP]-(study_soa_group_to_reassign)<-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-
            (study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value)--(study_root:StudyRoot {uid:$study_uid})
        WITH *
        ORDER BY study_activity.order ASC
        WHERE NOT (study_soa_group_to_reassign)<-[:BEFORE]-() AND NOT (study_soa_group_to_reassign)<-[]-(:Delete)

        // MERGE audit-trail entry for the newly create StudySoAGroup node that will be reused
        MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:$migration_desc, date:datetime()})-[:AFTER]->(study_soa_group_new)
        MERGE (study_value)-[:HAS_STUDY_SOA_GROUP]->(study_soa_group_new)

        // MERGE StudyActivity node with new StudySoAGroup node that will be reused between different StudyActivities
        MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group_new)
        WITH *
        CALL apoc.do.case([
            study_soa_group_new.show_soa_group_in_protocol_flowchart IS NULL,
            'SET study_soa_group_new.show_soa_group_in_protocol_flowchart = is_visible RETURN *'
            ],
            'RETURN *',
            {
                study_soa_group_new: study_soa_group_new,
                study_activity:study_activity,
                is_visible:is_visible
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
        params={"study_uid": study_uid, "migration_desc": CORRECTION_DESC},
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(task_level=1)
def migrate_study_activity_groups(db_driver, log, study_uid):
    log.info(
        "Merging StudyActivityGroup nodes for the following Study (%s)",
        study_uid,
    )
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
            study_soa_group.uid AS study_soa_group_uid,
            collect(distinct activity_group_root) AS distinct_activity_group_root, 
            collect(distinct study_activity_group) AS distinct_study_activity_group,
            any(vis IN collect(study_activity_group.show_activity_group_in_protocol_flowchart) WHERE vis=true) AS is_visible,
            // picking min order as if study_activity_group nodes are duplicated the first order number will describe the real order it should have
            min(study_activity_group.order) AS order_number
        // condition to not perform migration twice
        WHERE size(distinct_activity_group_root) <> size(distinct_study_activity_group)

        // leave only a few rows that will represent distinct ActivityGroups in a specific StudySoAGroup
        WITH DISTINCT activity_group_root, study_soa_group_uid, is_visible, order_number

        // CREATE new StudyActivityGroup node for each row of a distinct activity_group_root 
        CREATE (study_activity_group_new:StudyActivityGroup:StudySelection)
        MERGE (study_activity_group_counter:Counter {counterId:'StudyActivityGroupCounter'})
        ON CREATE SET study_activity_group_counter:StudyActivityGroupCounter, study_activity_group_counter.count=1
        WITH activity_group_root,study_soa_group_uid, study_activity_group_new,study_activity_group_counter, is_visible, order_number
        CALL apoc.atomic.add(study_activity_group_counter,'count',1,1) yield oldValue, newValue
        WITH activity_group_root, study_soa_group_uid, study_activity_group_new, toInteger(newValue) as uid_number_study_sag, is_visible, order_number
        SET study_activity_group_new.uid = "StudyActivityGroup_"+apoc.text.lpad(""+(uid_number_study_sag), 6, "0")
        SET study_activity_group_new.order=order_number
        WITH activity_group_root, study_soa_group_uid, study_activity_group_new, is_visible

        // MATCH all StudyActivity nodes that had 'old' StudyActivityGroup inside specific StudySoAGroup that were using a activity_group_root
        MATCH (activity_group_root)-[:HAS_VERSION]->(:ActivityGroupValue)<-[:HAS_SELECTED_ACTIVITY_GROUP]-(study_activity_group_to_reassign)
            <-[old_rel:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(study_activity:StudyActivity)
            <-[:HAS_STUDY_ACTIVITY]-(study_value)--(study_root:StudyRoot {uid:$study_uid})
        WITH *
        ORDER BY study_activity.order ASC
        MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup {uid:study_soa_group_uid})
        WHERE NOT (study_soa_group)-[:BEFORE]-()

        // MERGE audit-trail entry for the newly create StudyActivityGroup node that will be reused
        MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:$migration_desc, date:datetime()})-[:AFTER]->(study_activity_group_new)
        MERGE (study_value)-[:HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_new)

        // MERGE StudyActivity node with new StudyActivityGroup node that will be reused between different StudyActivities inside same StudySoAGroup
        MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_new)
        WITH *
        CALL apoc.do.case([
            study_activity_group_new.show_activity_group_in_protocol_flowchart IS NULL,
            'SET study_activity_group_new.show_activity_group_in_protocol_flowchart = is_visible RETURN *'
            ],
            'RETURN *',
            {
                study_activity_group_new: study_activity_group_new,
                study_activity:study_activity,
                is_visible:is_visible
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
        params={"study_uid": study_uid, "migration_desc": CORRECTION_DESC},
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(task_level=1)
def migrate_study_activity_subgroups(db_driver, log, study_uid):
    log.info(
        "Merging StudyActivitySubGroup nodes for the following Study (%s)",
        study_uid,
    )
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
            study_activity_group.uid AS study_activity_group_uid,
            study_soa_group.uid AS study_soa_group_uid,
            collect(distinct activity_subgroup_root) AS distinct_activity_subgroup_root, 
            collect(distinct study_activity_subgroup) AS distinct_study_activity_subgroup,
            any(vis IN collect(study_activity_subgroup.show_activity_subgroup_in_protocol_flowchart) WHERE vis=true) AS is_visible,
            // picking min order as if study_activity_subgroup nodes are duplicated the first order number will describe the real order it should have
            min(study_activity_subgroup.order) AS order_number
        // condition to not perform migration twice
        WHERE size(distinct_activity_subgroup_root) <> size(distinct_study_activity_subgroup)
        // leave only a few rows that will represent distinct ActivitySubGroups in a specific StudySoAGroup and StudyActivityGroup
        WITH DISTINCT activity_subgroup_root, study_soa_group_uid, study_activity_group_uid, is_visible, order_number

        // CREATE new StudyActivitySubGroup node for each row of a distinct activity_subgroup_root 
        CREATE (study_activity_subgroup_new:StudyActivitySubGroup:StudySelection)
        MERGE (study_activity_subgroup_counter:Counter {counterId:'StudyActivitySubGroupCounter'})
        ON CREATE SET study_activity_subgroup_counter:StudyActivitySubGroupCounter, study_activity_subgroup_counter.count=1
        WITH activity_subgroup_root, study_soa_group_uid, study_activity_group_uid, study_activity_subgroup_new,study_activity_subgroup_counter, is_visible, order_number
        CALL apoc.atomic.add(study_activity_subgroup_counter,'count',1,1) yield oldValue, newValue
        WITH activity_subgroup_root, study_soa_group_uid, study_activity_group_uid, study_activity_subgroup_new, toInteger(newValue) as uid_number_study_sasg, is_visible, order_number
        SET study_activity_subgroup_new.uid = "StudyActivitySubGroup_"+apoc.text.lpad(""+(uid_number_study_sasg), 6, "0")
        SET study_activity_subgroup_new.order=order_number
        WITH activity_subgroup_root, study_soa_group_uid, study_activity_group_uid, study_activity_subgroup_new, is_visible

        // MATCH all StudyActivity nodes that had 'old' StudyActivitySubGroup inside specific StudySoAGroup and StudyActivityGroup
        MATCH (activity_subgroup_root)-[:HAS_VERSION]->(:ActivitySubGroupValue)<-[:HAS_SELECTED_ACTIVITY_SUBGROUP]-(study_activity_subgroup_to_reassign)
            <-[old_rel:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]-(study_activity:StudyActivity)
            <-[:HAS_STUDY_ACTIVITY]-(study_value)--(study_root:StudyRoot {uid:$study_uid})
        WITH *
        ORDER BY study_activity.order ASC
        MATCH (study_activity_group:StudyActivityGroup {uid:study_activity_group_uid})<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(study_activity)
            -[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup {uid:study_soa_group_uid})
        WHERE NOT (study_activity_group)-[:BEFORE]-() AND NOT (study_soa_group)-[:BEFORE]-()

        // MERGE audit-trail entry for the newly create StudyActivitySubGroup node that will be reused
        MERGE (study_root)-[:AUDIT_TRAIL]->(:Create:StudyAction {user_initials:$migration_desc, date:datetime()})-[:AFTER]->(study_activity_subgroup_new)
        MERGE (study_value)-[:HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_new)

        // MERGE StudyActivity node with new StudyActivitySubGroup node that will be reused between different StudyActivities inside same StudySoAGroup and StudyActivityGroup
        MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_new)
        WITH *
        CALL apoc.do.case([
            study_activity_subgroup_new.show_activity_subgroup_in_protocol_flowchart IS NULL,
            'SET study_activity_subgroup_new.show_activity_subgroup_in_protocol_flowchart = is_visible RETURN *'
            ],
            'RETURN *',
            {
                study_activity_subgroup_new: study_activity_subgroup_new,
                study_activity:study_activity,
                is_visible:is_visible
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
        params={"study_uid": study_uid, "migration_desc": CORRECTION_DESC},
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(
    verify_func=correction_verification_011.test_migrate_study_selection_metadata_merge
)
def migrate_study_selection_metadata_merge(db_driver, log, run_label):
    """
    ### Problem description
    Some StudySoAGroup/StudyActivityGroups or StudyActivitySubGroups can be duplicated in a single Study.
    This means that there exists duplicated StudySoAGroup/StudyActivityGroups or StudyActivitySubGroups in scope of the same parent.

    ### Change description
    - If some StudySoAGroup/StudyActivityGroups or StudyActivitySubGroups is duplicated, it should be merged.
    The visitbility flag is set to true if any of the duplicated nodes had it initialized to true.
    This is how API algorithm currently works so it ensures the visibility remains the same in the Protocol SoA.

    ### Nodes and relationships affected
    - Nodes with the following labels and properties will have the property removed if its value is an empty string:
        - StudySoAGroup
        - StudyActivityGroup
        - StudyActivitySubGroup
        - StudyActivity
        - STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP
        - STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP
        - STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP
        - HAS_STUDY_SOA_GROUP
        - HAS_STUDY_ACTIVITY_GROUP
        - HAS_STUDY_ACTIVITY_SUBGROUP
    """

    desc = "Merge duplicated StudySoAGroup/StudyActivityGroup or StudyActivitySubGroup"
    log.info(f"Run: {run_label}, {desc}")

    studies, _ = run_cypher_query(
        db_driver,
        """
        MATCH (study_root:StudyRoot)-[:LATEST]->(study_value:StudyValue)
        WHERE NOT (study_root)-[:LATEST_LOCKED]->(study_value)
        RETURN study_root.uid
        """,
    )
    contains_updates = []
    for study in studies:
        study_uid = study[0]
        study_activity_soa_group_changes = migrate_study_soa_groups(
            db_driver, log, study_uid
        )
        contains_updates.append(study_activity_soa_group_changes)

        study_activity_group_changes = migrate_study_activity_groups(
            db_driver, log, study_uid
        )
        contains_updates.append(study_activity_group_changes)

        study_activity_subgroup_changes = migrate_study_activity_subgroups(
            db_driver, log, study_uid
        )
        contains_updates.append(study_activity_subgroup_changes)

    return any(contains_updates)


if __name__ == "__main__":
    main()
