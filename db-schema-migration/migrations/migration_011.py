"""Schema migrations needed for release 1.12.0 to PROD post April 2025."""

import csv
import json
import os
from collections import defaultdict

from migrations.common import migrate_ct_config_values, migrate_indexes_and_constraints
from migrations.utils.utils import (
    api_get,
    api_get_paged,
    get_db_connection,
    get_db_driver,
    get_logger,
    print_counters_table,
    run_cypher_query,
)

logger = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
DB_CONNECTION = get_db_connection()
MIGRATION_DESC = "schema-migration-release-1.12.0"


def main():
    logger.info("Running migration on DB '%s'", os.environ["DATABASE_NAME"])

    ### Common migrations
    migrate_indexes_and_constraints(DB_CONNECTION, logger)
    migrate_ct_config_values(DB_CONNECTION, logger)

    ### Release-specific migrations
    migrate_soa_group_activity_group_activity_subgroup_activity_orders(
        DB_DRIVER, logger
    )
    change_value_of_name_property_of_activity_instance_class(DB_DRIVER, logger)
    add_level_property_to_activity_instance_class(DB_DRIVER, logger)
    update_parent_class_relationship_of_activity_instance_class(DB_DRIVER, logger)
    remove_old_activity_instance_class_nodes(DB_DRIVER, logger)
    move_rels_from_old_nodes_to_events_node(DB_DRIVER, logger)
    move_rels_from_old_nodes_to_interventions_node(DB_DRIVER, logger)
    update_is_adam_param_specific_property_of_activity_item_to_false_if_it_is_null(
        DB_DRIVER, logger
    )
    move_props_to_has_item_class_rel(DB_DRIVER, logger)
    migrate_data_domain_from_activity_instance_class_to_dataset(DB_DRIVER, logger)
    migrate_related_codelist_from_activity_item_class_to_codelist(DB_DRIVER, logger)


def change_value_of_name_property_of_activity_instance_class(db_driver, log):
    # This migration is based on activity_instance_class.csv file from studybuilder-import repository
    log.info("Rename value of `name` property of Activity Instance Class Value")

    contains_updates = []

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (v1:ActivityInstanceClassValue {name: "Observation"})<--(r1:ActivityInstanceClassRoot)
        WHERE NOT EXISTS ((r1)-[:PARENT_CLASS]->(:ActivityInstanceClassRoot))
        SET v1.name = "GeneralObservation"
        RETURN *
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (v1:ActivityInstanceClassValue {name: "SubjectObservation"})<--(r1:ActivityInstanceClassRoot)
        <-[:PARENT_CLASS]-(r2:ActivityInstanceClassRoot)-->(v2:ActivityInstanceClassValue {name: "Finding"})
        MATCH (r2)<-[:PARENT_CLASS]-(r3:ActivityInstanceClassRoot)-->(v3:ActivityInstanceClassValue {name: "NumericFinding"})
        SET v3.name = "NumericFindings"
        RETURN *
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (v1:ActivityInstanceClassValue {name: "SubjectObservation"})<--(r1:ActivityInstanceClassRoot)
        <-[:PARENT_CLASS]-(r2:ActivityInstanceClassRoot)-->(v2:ActivityInstanceClassValue {name: "Finding"})
        MATCH (r2)<-[:PARENT_CLASS]-(r3:ActivityInstanceClassRoot)-->(v3:ActivityInstanceClassValue {name: "CategoricFinding"})
        SET v3.name = "CategoricFindings"
        RETURN *
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (v1:ActivityInstanceClassValue {name: "SubjectObservation"})<--(r1:ActivityInstanceClassRoot)
        <-[:PARENT_CLASS]-(r2:ActivityInstanceClassRoot)-->(v2:ActivityInstanceClassValue {name: "Finding"})
        MATCH (r2)<-[:PARENT_CLASS]-(r3:ActivityInstanceClassRoot)-->(v3:ActivityInstanceClassValue {name: "TextualFinding"})
        SET v3.name = "TextualFindings"
        RETURN *
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (v1:ActivityInstanceClassValue {name: "SubjectObservation"})<--(r1:ActivityInstanceClassRoot)
        <-[:PARENT_CLASS]-(r2:ActivityInstanceClassRoot)-->(v2:ActivityInstanceClassValue {name: "Event"})
        MATCH (r2)<-[:PARENT_CLASS]-(r3:ActivityInstanceClassRoot)-->(v3:ActivityInstanceClassValue {name: "Event"})
        SET v3.name = "Events"
        RETURN *
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (v1:ActivityInstanceClassValue {name: "SubjectObservation"})<--(r1:ActivityInstanceClassRoot)
        <-[:PARENT_CLASS]-(r2:ActivityInstanceClassRoot)-->(v2:ActivityInstanceClassValue {name: "Intervention"})
        MATCH (r2)<-[:PARENT_CLASS]-(r3:ActivityInstanceClassRoot)-->(v3:ActivityInstanceClassValue {name: "Intervention"})
        SET v3.name = "Interventions"
        RETURN *
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    return summary_nodes.counters.contains_updates


def add_level_property_to_activity_instance_class(db_driver, log):
    # This migration is based on activity_instance_class.csv file from studybuilder-import repository
    log.info("Add `level` property to Activity Instance Class Value")

    contains_updates = []

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (r:ActivityInstanceClassRoot)--(v:ActivityInstanceClassValue {name: "GeneralObservation"})
        WHERE v.level IS NULL
        SET v.level = 0
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (r:ActivityInstanceClassRoot)--(v:ActivityInstanceClassValue)
        WHERE v.level IS NULL AND v.name IN ['SubjectObservation', 'Observation']
        SET v.level = 1
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (r:ActivityInstanceClassRoot)--(v:ActivityInstanceClassValue)
        WHERE v.level IS NULL AND v.name IN ['SpecialPurpose', 'DeviceSpecialPurpose', 'Finding', 'Event', 'Intervention']
        SET v.level = 2
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (r:ActivityInstanceClassRoot)--(v:ActivityInstanceClassValue)
        WHERE v.level IS NULL AND v.name IN ['Demographics', 'Comments', 'SubjectVisits', 'DeviceIdentifiers', 'NumericFindings', 'CategoricFindings', 'TextualFindings', 'Events', 'Interventions']
        SET v.level = 3
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    return summary_nodes.counters.contains_updates


def update_parent_class_relationship_of_activity_instance_class(db_driver, log):
    # This migration is based on activity_instance_class.csv file from studybuilder-import repository
    log.info("Update `parent_class` relationship of Activity Instance Class")

    contains_updates = []

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (v1:ActivityInstanceClassValue)<-[:LATEST]-(r1:ActivityInstanceClassRoot)
        WHERE v1.name IN ["Demographics", "Comments", "SubjectVisits"]
        AND NOT EXISTS((r1)-[:PARENT_CLASS]-(:ActivityInstanceClassRoot)-[:LATEST]->(:ActivityInstanceClassValue {name: "SpecialPurpose"}))
        OPTIONAL MATCH (v2:ActivityInstanceClassValue {name: "SpecialPurpose"})<-[:LATEST]-(r2:ActivityInstanceClassRoot)
        OPTIONAL MATCH (r1)-[r:PARENT_CLASS]->()
        DELETE r
        WITH r1, r2 WHERE r2 IS NOT NULL
        CREATE (r1)-[:PARENT_CLASS]->(r2)
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (v1:ActivityInstanceClassValue)<-[:LATEST]-(r1:ActivityInstanceClassRoot)
        WHERE v1.name IN ["DeviceIdentifiers"]
        AND NOT EXISTS((r1)-[:PARENT_CLASS]-(:ActivityInstanceClassRoot)-[:LATEST]->(:ActivityInstanceClassValue {name: "DeviceSpecialPurpose"}))
        OPTIONAL MATCH (v2:ActivityInstanceClassValue {name: "DeviceSpecialPurpose"})<-[:LATEST]-(r2:ActivityInstanceClassRoot)
        OPTIONAL MATCH (r1)-[r:PARENT_CLASS]->()
        DELETE r
        WITH r1, r2 WHERE r2 IS NOT NULL
        CREATE (r1)-[:PARENT_CLASS]->(r2)
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (v1:ActivityInstanceClassValue)<-[:LATEST]-(r1:ActivityInstanceClassRoot)
        WHERE v1.name IN ["NumericFindings", "CategoricFindings", "TextualFindings"]
        AND NOT EXISTS((r1)-[:PARENT_CLASS]-(:ActivityInstanceClassRoot)-[:LATEST]->(:ActivityInstanceClassValue {name: "Finding"}))
        OPTIONAL MATCH (v2:ActivityInstanceClassValue {name: "Finding"})<-[:LATEST]-(r2:ActivityInstanceClassRoot)
        OPTIONAL MATCH (r1)-[r:PARENT_CLASS]->()
        DELETE r
        WITH r1, r2 WHERE r2 IS NOT NULL
        CREATE (r1)-[:PARENT_CLASS]->(r2)
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (v1:ActivityInstanceClassValue)<-[:LATEST]-(r1:ActivityInstanceClassRoot)
        WHERE v1.name IN ["Events"]
        AND NOT EXISTS((r1)-[:PARENT_CLASS]-(:ActivityInstanceClassRoot)-[:LATEST]->(:ActivityInstanceClassValue {name: "Event"}))
        OPTIONAL MATCH (v2:ActivityInstanceClassValue {name: "Event"})<-[:LATEST]-(r2:ActivityInstanceClassRoot)
        OPTIONAL MATCH (r1)-[r:PARENT_CLASS]->()
        DELETE r
        WITH r1, r2 WHERE r2 IS NOT NULL
        CREATE (r1)-[:PARENT_CLASS]->(r2)
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (v1:ActivityInstanceClassValue)<-[:LATEST]-(r1:ActivityInstanceClassRoot)
        WHERE v1.name IN ["Interventions"]
        AND NOT EXISTS((r1)-[:PARENT_CLASS]-(:ActivityInstanceClassRoot)-[:LATEST]->(:ActivityInstanceClassValue {name: "Intervention"}))
        OPTIONAL MATCH (v2:ActivityInstanceClassValue {name: "Intervention"})<-[:LATEST]-(r2:ActivityInstanceClassRoot)
        OPTIONAL MATCH (r1)-[r:PARENT_CLASS]->()
        DELETE r
        WITH r1, r2 WHERE r2 IS NOT NULL
        CREATE (r1)-[:PARENT_CLASS]->(r2)
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (v1:ActivityInstanceClassValue)<-[:LATEST]-(r1:ActivityInstanceClassRoot)
        WHERE v1.name IN ["SpecialPurpose", "Finding", "Event", "Intervention"]
        AND NOT EXISTS((r1)-[:PARENT_CLASS]-(:ActivityInstanceClassRoot)-[:LATEST]->(:ActivityInstanceClassValue {name: "SubjectObservation"}))
        OPTIONAL MATCH (v2:ActivityInstanceClassValue {name: "SubjectObservation"})<-[:LATEST]-(r2:ActivityInstanceClassRoot)
        OPTIONAL MATCH (r1)-[r:PARENT_CLASS]->()
        DELETE r
        WITH r1, r2 WHERE r2 IS NOT NULL
        CREATE (r1)-[:PARENT_CLASS]->(r2)
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (v1:ActivityInstanceClassValue)<-[:LATEST]-(r1:ActivityInstanceClassRoot)
        WHERE v1.name IN ["DeviceSpecialPurpose"]
        AND NOT EXISTS((r1)-[:PARENT_CLASS]-(:ActivityInstanceClassRoot)-[:LATEST]->(:ActivityInstanceClassValue {name: "Observation"}))
        OPTIONAL MATCH (v2:ActivityInstanceClassValue {name: "Observation"})<-[:LATEST]-(r2:ActivityInstanceClassRoot)
        OPTIONAL MATCH (r1)-[r:PARENT_CLASS]->()
        DELETE r
        WITH r1, r2 WHERE r2 IS NOT NULL
        CREATE (r1)-[:PARENT_CLASS]->(r2)
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (v1:ActivityInstanceClassValue)<-[:LATEST]-(r1:ActivityInstanceClassRoot)
        WHERE v1.name IN ["SubjectObservation", "Observation"]
        AND NOT EXISTS((r1)-[:PARENT_CLASS]-(:ActivityInstanceClassRoot)-[:LATEST]->(:ActivityInstanceClassValue {name: "GeneralObservation"}))
        OPTIONAL MATCH (v2:ActivityInstanceClassValue {name: "GeneralObservation"})<-[:LATEST]-(r2:ActivityInstanceClassRoot)
        OPTIONAL MATCH (r1)-[r:PARENT_CLASS]->()
        DELETE r
        WITH r1, r2 WHERE r2 IS NOT NULL
        CREATE (r1)-[:PARENT_CLASS]->(r2)
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    return summary_nodes.counters.contains_updates


def remove_old_activity_instance_class_nodes(db_driver, log):
    log.info("Remove old ActivityInstanceClass nodes")
    contains_updates = []

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (src_to_delete:ActivityInstanceClassRoot)--(src_iacv_to_delete:ActivityInstanceClassValue) 
        WHERE src_iacv_to_delete.name IN ["DeviceFinding", "DeviceNumericFinding", "AssociatedPersonsFinding", "Other", "OtherQualifiers"]
        DETACH DELETE src_to_delete, src_iacv_to_delete
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    return summary_nodes.counters.contains_updates


def move_rels_from_old_nodes_to_events_node(db_driver, log):
    log.info("Move rels from old nodes to Events node and delete old nodes")
    contains_updates = []

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (src:ActivityInstanceClassRoot)-[:LATEST]-(src_iacv:ActivityInstanceClassValue) 
        WHERE src_iacv.name IN ["AdverseEvent", "MedicalHistory", "Disposition", "HypoglycaemicEpisode"]
        MATCH (target:ActivityInstanceClassRoot)-[:LATEST]-(target_iacv:ActivityInstanceClassValue) 
        WHERE target_iacv.name = "Events" 

        MATCH (src)-[r_aicr:HAS_ITEM_CLASS]->(sons_aicr:ActivityItemClassRoot)
        WHERE type(r_aicr) = "HAS_ITEM_CLASS"
        MERGE (target)-[:HAS_ITEM_CLASS]->(sons_aicr)
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (src:ActivityInstanceClassRoot)-[:LATEST]-(src_iacv:ActivityInstanceClassValue) 
        WHERE src_iacv.name IN ["AdverseEvent", "MedicalHistory", "Disposition", "HypoglycaemicEpisode"]
        MATCH (target:ActivityInstanceClassRoot)-[:LATEST]-(target_iacv:ActivityInstanceClassValue) 
        WHERE target_iacv.name = "Events" 

        MATCH (src)<-[r_aiv:ACTIVITY_INSTANCE_CLASS]-(sons_aiv:ActivityInstanceValue)
        WHERE type(r_aiv)= "ACTIVITY_INSTANCE_CLASS" 
        MERGE (target)<-[:ACTIVITY_INSTANCE_CLASS]-(sons_aiv)
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (src_to_delete:ActivityInstanceClassRoot)--(src_iacv_to_delete:ActivityInstanceClassValue) 
        WHERE src_iacv_to_delete.name IN ["AdverseEvent", "MedicalHistory", "Disposition", "HypoglycaemicEpisode"]
        DETACH DELETE src_to_delete, src_iacv_to_delete
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    return summary_nodes.counters.contains_updates


def move_rels_from_old_nodes_to_interventions_node(db_driver, log):
    log.info("Move rels from old nodes to Interventions node and delete old nodes")
    contains_updates = []

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (src:ActivityInstanceClassRoot)-[:LATEST]-(src_iacv:ActivityInstanceClassValue) 
        WHERE src_iacv.name IN ["CompoundDosing", "ConcomitantMedication"]
        MATCH (target:ActivityInstanceClassRoot)-[:LATEST]-(target_iacv:ActivityInstanceClassValue) 
        WHERE target_iacv.name = "Interventions" 

        MATCH (src)-[r_aicr:HAS_ITEM_CLASS]->(sons_aicr:ActivityItemClassRoot)
            WHERE type(r_aicr) = "HAS_ITEM_CLASS"
        MERGE (target)-[:HAS_ITEM_CLASS]->(sons_aicr)
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (src:ActivityInstanceClassRoot)-[:LATEST]-(src_iacv:ActivityInstanceClassValue) 
        WHERE src_iacv.name IN ["CompoundDosing", "ConcomitantMedication"]
        MATCH (target:ActivityInstanceClassRoot)-[:LATEST]-(target_iacv:ActivityInstanceClassValue) 
        WHERE target_iacv.name = "Interventions" 

        MATCH (src)<-[r_aiv:ACTIVITY_INSTANCE_CLASS]-(sons_aiv:ActivityInstanceValue)
            WHERE type(r_aiv)= "ACTIVITY_INSTANCE_CLASS" 
        MERGE (target)<-[:ACTIVITY_INSTANCE_CLASS]-(sons_aiv)
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (src_to_delete:ActivityInstanceClassRoot)--(src_iacv_to_delete:ActivityInstanceClassValue) 
        WHERE src_iacv_to_delete.name IN ["CompoundDosing", "ConcomitantMedication"]
        DETACH DELETE src_to_delete, src_iacv_to_delete
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    return summary_nodes.counters.contains_updates


def update_is_adam_param_specific_property_of_activity_item_to_false_if_it_is_null(
    db_driver, log
):
    log.info(
        "Update `is_adam_param_specific` property of Activity Item to False if it is NULL"
    )
    contains_updates = []

    _, summary_nodes = run_cypher_query(
        db_driver,
        """
        MATCH (n:ActivityItem)
        WHERE n.is_adam_param_specific IS NULL
        SET n.is_adam_param_specific = False
        """,
    )
    print_counters_table(summary_nodes.counters)
    contains_updates.append(summary_nodes.counters.contains_updates)

    return summary_nodes.counters.contains_updates


def move_props_to_has_item_class_rel(db_driver, log):
    # This migration is based on activity_item_class.csv file from studybuilder-import repository
    log.info(
        "Move props from node to `HAS_ITEM_CLASS` relationship of Activity Instance Class"
    )

    with open(
        "studybuilder_import/datafiles/sponsor_library/activity/activity_item_class.csv",
        encoding="utf-8",
    ) as f:
        rows = csv.DictReader(f)

        contains_updates = []

        for row in rows:
            _, summary_nodes = run_cypher_query(
                db_driver,
                f"""
                MATCH (:ActivityInstanceClassValue {{name: "{row["ACTIVITY_INSTANCE_CLASS"]}"}})--(:ActivityInstanceClassRoot)
                -[r:HAS_ITEM_CLASS]-(:ActivityItemClassRoot)--(v1:ActivityItemClassValue {{name: "{row["ACTIVITY_ITEM_CLASS"]}"}})
                SET r.mandatory = {row["MANDATORY"] == "Yes"}
                SET r.is_adam_param_specific_enabled = {row["IS_ADAM_PARAM_SPECIFIC_ENABLED"] == "Yes"}
                SET v1.mandatory = NULL
                """,
            )
            print_counters_table(summary_nodes.counters)
            contains_updates.append(summary_nodes.counters.contains_updates)

        _, summary_nodes = run_cypher_query(
            db_driver,
            """
            MATCH (:ActivityInstanceClassValue)--(:ActivityInstanceClassRoot)-[r:HAS_ITEM_CLASS]-(:ActivityItemClassRoot)--(v1:ActivityItemClassValue)
            WHERE r.mandatory IS NULL
            SET r.mandatory = coalesce(v1.mandatory, false)
            SET r.is_adam_param_specific_enabled = false
            SET v1.mandatory = NULL
            """,
        )
        print_counters_table(summary_nodes.counters)
        contains_updates.append(summary_nodes.counters.contains_updates)

    return summary_nodes.counters.contains_updates


def migrate_data_domain_from_activity_instance_class_to_dataset(db_driver, log):
    log.info("Migrate data domain from activity instance class to dataset")

    with open(
        "studybuilder_import/datafiles/sponsor_library/activity/sdtm_mastermodel_3.2-NN15_domain_to_activityInstanceClass.csv",
        encoding="utf-8",
    ) as file:
        data_domain_relationships = csv.reader(file)

        # Skip the header row
        next(data_domain_relationships)

        # table, label, activity_class, level_2_class = row
        data_domain_relationships_tuple = [
            [table.strip(), level_2_class.strip()]
            for table, label, activity_class, level_2_class in data_domain_relationships
        ]

    print(data_domain_relationships_tuple)
    number_of_relationships_created, _ = run_cypher_query(
        db_driver,
        """
        UNWIND $data_domain_relationships_csv AS data_domain_relationships_rows
        WITH data_domain_relationships_rows[0] as  data_domain_rel_0, tolower(data_domain_relationships_rows[1]) as data_domain_rel_1
        MATCH (codelist:CTCodelistRoot)--(cttermroot:CTTermRoot)--(cttermattroot:CTTermAttributesRoot)-[:LATEST]-(cttermattvalue:CTTermAttributesValue)
            WHERE  cttermattvalue.code_submission_value =data_domain_rel_0 and (codelist.uid = "C66734" or codelist.uid = "C111113")
        MATCH (ainstcv:ActivityInstanceClassValue)-[:LATEST]-(ainstcr:ActivityInstanceClassRoot)
            WHERE tolower(ainstcv.name) = data_domain_rel_1
        MERGE (cttermroot)<-[:HAS_DATA_DOMAIN]-(ainstcr)
        return cttermroot.uid, cttermattvalue.code_submission_value, ainstcv.name
        """,
        params={"data_domain_relationships_csv": data_domain_relationships_tuple},
    )
    print(number_of_relationships_created)
    print(f"relationships matched {len(number_of_relationships_created)}")


def migrate_related_codelist_from_activity_item_class_to_codelist(db_driver, log):
    log.info(
        "Create relationship form Activity Item Class to Codelists with the relationship`RELATED_CODELIST`"
    )

    with open(
        "studybuilder_import/datafiles/sponsor_library/activity/activity_item_class.csv",
        encoding="utf-8",
    ) as f:
        rows = csv.DictReader(f)

        contains_updates = []
        for row in rows:
            codelists = (
                row["CODELIST"].split(";")
                if ";" in row["CODELIST"]
                else [row["CODELIST"]]
            )
            for codelist in codelists:
                _, summary_nodes = run_cypher_query(
                    db_driver,
                    f"""
                    MATCH (v_root:ActivityItemClassRoot)--(:ActivityItemClassValue {{name: "{row["ACTIVITY_ITEM_CLASS"].strip()}"}})
                    MATCH (ct:CTCodelistRoot)--(d:CTCodelistAttributesRoot)--(c:CTCodelistAttributesValue{{submission_value:"{codelist.strip()}"}} )
                    MERGE (v_root)-[:RELATED_CODELIST]->(ct)
                    """,
                )
            print_counters_table(summary_nodes.counters)
            contains_updates.append(summary_nodes.counters.contains_updates)

    return summary_nodes.counters.contains_updates


def _get_order_of_soa_group_activity_group_and_activity_subgroup_in_soa(
    study_activities: list,
) -> dict:
    # sort list of study activities to group them by flowchart_group->activity_group->activity_subgroup
    uniq_flowchart_groups = defaultdict(dict)
    # print(study_activities)
    for study_activity in study_activities:
        # flowchart_group = study_activity.study_soa_group.study_soa_group_uid
        flowchart_group = study_activity["study_soa_group"]["study_soa_group_uid"]

        uniq_flowchart_groups[flowchart_group].setdefault(
            "order", len(uniq_flowchart_groups)
        )
        # the sort order of activity_groups and activity_subgroups is kept for each flowchart_group
        # because we may have the same activity_subgroups, activity_groups for different flowchart_group
        uniq_flowchart_groups[flowchart_group].setdefault("groups", {})

        # the sort order of ActivityPlaceholders is kept for each flowchart_group
        uniq_flowchart_groups[flowchart_group].setdefault("activities", {})

        # create list of unique activity_groups in the order they should be sorted
        if (
            study_activity["study_activity_group"]["study_activity_group_uid"]
            is not None
        ):
            activity_group = study_activity["study_activity_group"][
                "study_activity_group_uid"
            ]

            uniq_flowchart_groups[flowchart_group]["groups"].setdefault(
                activity_group, {}
            ).setdefault(
                "order",
                len(uniq_flowchart_groups[flowchart_group]["groups"]),
            )

            uniq_flowchart_groups[flowchart_group]["groups"][activity_group].setdefault(
                "subgroups", {}
            )

            # create list of unique activity_subgroups in the order they should be sorted
            if (
                study_activity["study_activity_subgroup"]["study_activity_subgroup_uid"]
                is not None
            ):
                activity_subgroup = study_activity["study_activity_subgroup"][
                    "study_activity_subgroup_uid"
                ]
                uniq_flowchart_groups[flowchart_group]["groups"][activity_group][
                    "subgroups"
                ].setdefault(activity_subgroup, {}).setdefault(
                    "order",
                    len(
                        uniq_flowchart_groups[flowchart_group]["groups"][
                            activity_group
                        ]["subgroups"]
                    ),
                )

                uniq_flowchart_groups[flowchart_group]["groups"][activity_group][
                    "subgroups"
                ][activity_subgroup].setdefault("activities", {})
                activity = study_activity["study_activity_uid"]
                uniq_flowchart_groups[flowchart_group]["groups"][activity_group][
                    "subgroups"
                ][activity_subgroup]["activities"].setdefault(activity, {}).setdefault(
                    "order",
                    len(
                        uniq_flowchart_groups[flowchart_group]["groups"][
                            activity_group
                        ]["subgroups"][activity_subgroup]["activities"]
                    ),
                )
        else:
            activity = study_activity["study_activity_uid"]
            uniq_flowchart_groups[flowchart_group]["activities"].setdefault(
                activity, {}
            ).setdefault(
                "order",
                len(uniq_flowchart_groups[flowchart_group]["activities"]),
            )

    return uniq_flowchart_groups


def _sort_study_activities(
    study_selection_activities: list,
):
    """Sort StudySelectionActivities in place, grouping by SoAGroup, ActivityGroup, ActivitySubgroup"""

    soa_groups = {}
    activity_groups = {}
    activity_subgroups = {}
    order_keys = {}

    for activity in study_selection_activities:
        key = []

        key.append(
            soa_groups.setdefault(
                activity["study_soa_group"]["soa_group_term_uid"], len(soa_groups) + 1
            )
        )

        key.append(
            activity_groups.setdefault(
                activity["study_activity_group"]["activity_group_uid"],
                (
                    len(activity_groups) + 1
                    if activity["study_activity_group"]["activity_group_uid"]
                    else -1
                ),
            )
        )

        key.append(
            activity_subgroups.setdefault(
                activity["study_activity_subgroup"]["activity_subgroup_uid"],
                (
                    len(activity_subgroups) + 1
                    if activity["study_activity_subgroup"]["activity_subgroup_uid"]
                    else -1
                ),
            )
        )

        order_keys[activity["study_activity_uid"]] = tuple(key)

    list.sort(
        study_selection_activities,
        key=lambda activity: order_keys.get(activity["study_activity_uid"]),
    )
    return order_keys


def migrate_soa_group_activity_group_activity_subgroup_activity_orders(db_driver, log):
    # get a list of studies
    payload = api_get(
        "/studies",
        params={
            "page_size": 1000,
            "total_count": True,
            "sort_by": json.dumps({"uid": True}),
        },
    ).json()
    studies = payload["items"]
    contains_updates = []
    for study in studies:
        study_uid = study["uid"]
        study_number = study["current_metadata"]["identification_metadata"][
            "study_number"
        ]

        log.info(
            "Assiging StudySoAGroup, StudyActivityGroup, StudyActivitySubGroup orders in a (%s) Study",
            study_number,
        )

        # get order of StudyActivities
        study_activities = api_get_paged(
            f"/studies/{study_uid}/study-activities",
            params={
                "sort_by": json.dumps({"order": True}),
            },
        )["items"]
        soa_group_orders = [
            study_activity["study_soa_group"]["order"]
            for study_activity in study_activities
        ]
        _sort_study_activities(study_selection_activities=study_activities)
        soa_orders = (
            _get_order_of_soa_group_activity_group_and_activity_subgroup_in_soa(
                study_activities=study_activities
            )
        )
        # If some SoAGroup order is null, the migration should be performed
        if not all(soa_group_orders):
            for study_activity in study_activities:
                # StudySoAGroup
                soa_group_uid = study_activity["study_soa_group"]["study_soa_group_uid"]
                soa_group_order = soa_orders[soa_group_uid]["order"]
                # StudyActivityGroup
                study_activity_group_uid = study_activity["study_activity_group"][
                    "study_activity_group_uid"
                ]
                study_activity_group_order = (
                    soa_orders[soa_group_uid]["groups"][study_activity_group_uid][
                        "order"
                    ]
                    if study_activity_group_uid
                    else None
                )
                # StudyActivitySubGroup
                study_activity_subgroup_uid = study_activity["study_activity_subgroup"][
                    "study_activity_subgroup_uid"
                ]
                study_activity_subgroup_order = (
                    soa_orders[soa_group_uid]["groups"][study_activity_group_uid][
                        "subgroups"
                    ][study_activity_subgroup_uid]["order"]
                    if study_activity_subgroup_uid
                    else None
                )
                # StudyActivity
                study_activity_uid = study_activity["study_activity_uid"]
                if study_activity_group_uid and study_activity_subgroup_uid:
                    study_activity_order = soa_orders[soa_group_uid]["groups"][
                        study_activity_group_uid
                    ]["subgroups"][study_activity_subgroup_uid]["activities"][
                        study_activity_uid
                    ][
                        "order"
                    ]
                else:
                    study_activity_order = soa_orders[soa_group_uid]["activities"][
                        study_activity_uid
                    ]["order"]

                _, summary = run_cypher_query(
                    db_driver,
                    """
                    MATCH (study_activity:StudyActivity {uid:$study_activity_uid})                
                    MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soa_group:StudySoAGroup {uid: $study_soa_group_uid})
                    WHERE NOT (study_activity)-[:BEFORE]-()

                    OPTIONAL MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup {uid: $study_activity_group_uid})
                    OPTIONAL MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup {uid: $study_activity_subgroup_uid})

                    SET study_activity.legacy_order_number = study_activity.order
                    SET study_activity.order = $study_activity_order
                    SET soa_group.order = $study_soa_group_order
                    SET study_activity_group.order = $study_activity_group_order
                    SET study_activity_subgroup.order = $study_activity_subgroup_order
                    """,
                    params={
                        "study_activity_uid": study_activity_uid,
                        "study_soa_group_uid": soa_group_uid,
                        "study_soa_group_order": soa_group_order,
                        "study_activity_group_uid": study_activity_group_uid,
                        "study_activity_group_order": study_activity_group_order,
                        "study_activity_subgroup_uid": study_activity_subgroup_uid,
                        "study_activity_subgroup_order": study_activity_subgroup_order,
                        "study_activity_order": study_activity_order,
                    },
                )
                counters = summary.counters
                print_counters_table(counters)
                contains_updates.append(counters.contains_updates)
    return contains_updates


if __name__ == "__main__":
    main()
