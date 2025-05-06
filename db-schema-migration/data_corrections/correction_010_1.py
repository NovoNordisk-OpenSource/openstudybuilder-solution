""" PRD Data Corrections, for release 1.11.2"""

import os

from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    print_counters_table,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import get_logger
from verifications import correction_verification_010_1

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-release-1.11.2"


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    separate_study_activity_group_subgroup_from_different_soa_groups(DB_DRIVER, LOGGER)


@capture_changes(task_level=1)
def separate_study_activity_group(db_driver, log, study_uid):
    log.info(
        "Splitting StudyActivityGroup from different SoAGroup in the following Study (%s)",
        study_uid,
    )
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
            study_value,
            activity_group_root,
            study_activity_group,
            collect(DISTINCT study_soa_group.uid) as distinct_soa_groups,
            study_activity_group.show_activity_group_in_protocol_flowchart AS is_visible
        // condition to not perform migration twice
        WHERE size(distinct_soa_groups) > 1

        MATCH (study_value)-[:HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-
            (:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
        // leave only a few rows that will represent distinct ActivityGroups in a specific StudySoAGroup
        WITH DISTINCT activity_group_root, is_visible, study_activity_group, study_soa_group.uid as study_soa_group_uid

        // CREATE new StudyActivityGroup node for each row of a distinct activity_group_root 
        CREATE (study_activity_group_new:StudyActivityGroup:StudySelection)
        MERGE (study_activity_group_counter:Counter {counterId:'StudyActivityGroupCounter'})
        ON CREATE SET study_activity_group_counter:StudyActivityGroupCounter, study_activity_group_counter.count=1
        WITH activity_group_root, study_activity_group_new,study_activity_group_counter, is_visible, study_activity_group, study_soa_group_uid
        CALL apoc.atomic.add(study_activity_group_counter,'count',1,1) yield oldValue, newValue
        WITH activity_group_root, study_activity_group_new, toInteger(newValue) as uid_number_study_sag, is_visible, study_activity_group, study_soa_group_uid
        SET study_activity_group_new.uid = "StudyActivityGroup_"+apoc.text.lpad(""+(uid_number_study_sag), 6, "0")
        WITH activity_group_root, study_activity_group_new, is_visible, study_activity_group, study_soa_group_uid

        // MATCH all StudyActivity nodes that had 'old' StudyActivityGroup inside specific StudySoAGroup that were using a activity_group_root
        MATCH (study_activity_group)<-[old_rel:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(study_activity:StudyActivity)
            -[:HAS_STUDY_ACTIVITY]-(study_value:StudyValue)--(study_root:StudyRoot{uid:$study_uid})
        MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(:StudySoAGroup{uid:study_soa_group_uid})
        WITH *

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
                is_visible:is_visible
            })
        YIELD value

        // MERGE newly create StudyActivityGroup node with distinct activity_group_value
        MATCH (activity_group_root)-[:LATEST]->(latest_activity_group_value:ActivityGroupValue)
        MERGE (study_activity_group_new)-[:HAS_SELECTED_ACTIVITY_GROUP]->(latest_activity_group_value)

        WITH study_activity_group_new, study_activity_group, study_activity, old_rel,

        // Copy StudySoAFootnotes relationships from the old StudyActivityGroup nodes
        apoc.coll.toSet([(study_soa_footnote:StudySoAFootnote)-[ref:REFERENCES_STUDY_ACTIVITY_GROUP]->(study_activity_group) | 
        study_soa_footnote]) as footnotes
        FOREACH (footnote in footnotes | MERGE (footnote)-[:REFERENCES_STUDY_ACTIVITY_GROUP]->(study_activity_group_new))
        WITH study_activity_group, study_activity_group_new, study_activity, old_rel
        MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_new)
        DETACH DELETE old_rel
        """,
        params={"study_uid": study_uid, "migration_desc": CORRECTION_DESC},
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(task_level=1)
def separate_study_activity_subgroup(db_driver, log, study_uid):
    log.info(
        "Splitting StudyActivitySubGroup from different SoAGroup in the following Study (%s)",
        study_uid,
    )
    _, summary = run_cypher_query(
        db_driver,
        """
        MATCH (study_root:StudyRoot {uid: $study_uid})-[]->(study_value:StudyValue)
        WITH DISTINCT study_root, study_value
        MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->
            (study_activity_subgroup:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot)
        MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-(study_soa_group:StudySoAGroup)
        WHERE NOT (study_activity_subgroup)<-[:BEFORE]-() AND NOT (study_activity_subgroup)<-[]-(:Delete)

        WITH DISTINCT
            study_value,
            activity_subgroup_root,
            study_activity_subgroup,
            collect(DISTINCT study_soa_group.uid) as distinct_study_soa_groups,
            study_activity_subgroup.show_activity_subgroup_in_protocol_flowchart AS is_visible
        // condition to not perform migration twice
        WHERE size(distinct_study_soa_groups) > 1

        MATCH (study_value)-[:HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]
            -(:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-(study_soa_group:StudySoAGroup)
        // leave only a few rows that will represent distinct ActivitySubGroups in a specific StudySoAGroup
        WITH DISTINCT activity_subgroup_root, study_activity_subgroup, is_visible, study_soa_group.uid as study_soa_group_uid

        // CREATE new StudyActivitySubGroup node for each row of a distinct activity_subgroup_root 
        CREATE (study_activity_subgroup_new:StudyActivitySubGroup:StudySelection)
        MERGE (study_activity_subgroup_counter:Counter {counterId:'StudyActivitySubGroupCounter'})
        ON CREATE SET study_activity_subgroup_counter:StudyActivitySubGroupCounter, study_activity_subgroup_counter.count=1
        WITH activity_subgroup_root, study_activity_subgroup_new,study_activity_subgroup_counter, is_visible, study_activity_subgroup, study_soa_group_uid
        CALL apoc.atomic.add(study_activity_subgroup_counter,'count',1,1) yield oldValue, newValue
        WITH activity_subgroup_root, study_activity_subgroup_new, toInteger(newValue) as uid_number_study_sasg, is_visible, study_activity_subgroup, study_soa_group_uid
        SET study_activity_subgroup_new.uid = "StudyActivitySubGroup_"+apoc.text.lpad(""+(uid_number_study_sasg), 6, "0")
        WITH activity_subgroup_root, study_activity_subgroup_new, is_visible, study_activity_subgroup, study_soa_group_uid


        // MATCH all StudyActivity nodes that had 'old' StudyActivitySubGroup inside specific StudySoAGroup
        MATCH (study_activity_subgroup)<-[old_rel:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]-(study_activity:StudyActivity)
            -[:HAS_STUDY_ACTIVITY]-(study_value:StudyValue)--(study_root:StudyRoot{uid:$study_uid})
        MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-(:StudySoAGroup {uid:study_soa_group_uid})
        WITH *

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
                is_visible:is_visible
            })
        YIELD value

        // MERGE newly create StudyActivitySubGroup node with distinct activity_subgroup_value
        MATCH (activity_subgroup_root)-[:LATEST]->(latest_activity_subgroup_value:ActivitySubGroupValue)
        MERGE (study_activity_subgroup_new)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(latest_activity_subgroup_value)

        WITH study_activity_subgroup_new, study_activity_subgroup, study_activity, old_rel,
        // Copy StudySoAFootnotes relationships from the old StudyActivitySubGroup nodes
        apoc.coll.toSet([(study_soa_footnote:StudySoAFootnote)-[ref:REFERENCES_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup) | 
        study_soa_footnote]) as footnotes
        FOREACH (footnote in footnotes | MERGE (footnote)-[:REFERENCES_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_new))
        WITH study_activity_subgroup, study_activity_subgroup_new, study_activity, old_rel
        MERGE (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_new)
        DETACH DELETE old_rel
        """,
        params={"study_uid": study_uid, "migration_desc": CORRECTION_DESC},
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


@capture_changes(
    verify_func=correction_verification_010_1.test_separate_study_activity_group_subgroup_from_different_soa_groups,
    has_subtasks=True,
    docs_only=True,
)
def separate_study_activity_group_subgroup_from_different_soa_groups(db_driver, log):
    """
    ### Problem description
    There was an issue in the API that if StudyActivities was having same SoAGroup and it was edited to be different
    the underlying StudyActivityGroup, StudyActivitySubGroup nodes were not changed to be different.
    ### Change description
    If the same StudyActivityGroup, StudyActivitySubGroup exists in a few different StudySoAGroup nodes, then StudyActivityGroup/Subgroup
    nodes have to be separated so that each StudyActityGroup/Subgroup exists in each own different SoAGroup.
    ### Nodes and relationships affected
    - `StudyActivity`, `StudyActivitySubGroup`, `StudyActivityGroup` nodes
    - `STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP`, `STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP`, `HAS_STUDY_ACTIVITY_SUBGROUP`, `HAS_STUDY_ACTIVITY_GROUP` relationships
    """
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
        study_activity_group_changes = separate_study_activity_group(
            db_driver, log, study_uid
        )
        contains_updates.append(study_activity_group_changes)
        study_activity_subgroup_changes = separate_study_activity_subgroup(
            db_driver, log, study_uid
        )
        contains_updates.append(study_activity_subgroup_changes)

    return any(contains_updates)


if __name__ == "__main__":
    main()
