"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import json
import os

from data_corrections.utils.utils import get_db_driver, run_cypher_query
from migrations.utils.utils import api_get_paged, get_logger

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()


def test_correct_study_visit_timing_related_nodes():
    studies, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_root:StudyRoot)-[:LATEST]->(study_value:StudyValue)
        WHERE NOT (study_root)-[:LATEST_LOCKED]-(study_value)
        RETURN study_root.uid
        """,
    )
    for study in studies:
        study_uid = study[0]
        LOGGER.info(
            "Checking for StudyVisit timing related nodes in the following Study (%s)",
            study_uid,
        )
        study_visits = api_get_paged(f"/studies/{study_uid}/study-visits", page_size=10)
        for study_visit in study_visits["items"]:
            if (
                study_visit["visit_class"]
                not in [
                    "UNSCHEDULED_VISIT",
                    "NON_VISIT",
                    "SPECIAL_VISIT",
                ]
                and study_visit["time_reference_name"] != "Global anchor visit"
            ):
                study_visit_uid = study_visit["uid"]
                study_day_number = study_visit["study_day_number"]
                study_duration_days_number = study_visit["study_duration_days"]
                study_week_number = study_visit["study_week_number"]
                study_duration_weeks_number = study_visit["study_duration_weeks"]
                records, _ = run_cypher_query(
                    DB_DRIVER,
                    """
                    MATCH (study_visit:StudyVisit {uid:$study_visit_uid})
                    WHERE NOT (study_visit)-[:BEFORE]-()
                    MATCH (study_visit)-[:HAS_STUDY_DAY]->(:StudyDayRoot)-[:LATEST]->(study_day_value:StudyDayValue {value:$study_day_number})
                    MATCH (study_visit)-[:HAS_STUDY_DURATION_DAYS]->(:StudyDurationDaysRoot)-[:LATEST]->(study_duration_days_value:StudyDurationDaysValue {value:$study_duration_days_number})
                    MATCH (study_visit)-[:HAS_STUDY_WEEK]->(:StudyWeekRoot)-[:LATEST]->(study_week_value:StudyWeekValue {value:$study_week_number})
                    MATCH (study_visit)-[:HAS_STUDY_DURATION_WEEKS]->(:StudyDurationWeeksRoot)-[:LATEST]->(study_duration_weeks_value:StudyDurationWeeksValue {value:$study_duration_weeks_number})
                    MATCH (study_visit)-[:HAS_WEEK_IN_STUDY]->(:WeekInStudyRoot)-[:LATEST]->(week_in_study_value:WeekInStudyValue {value:$study_duration_weeks_number})
                    RETURN study_visit
                    """,
                    params={
                        "study_visit_uid": study_visit_uid,
                        "study_day_number": study_day_number,
                        "study_duration_days_number": study_duration_days_number,
                        "study_week_number": study_week_number,
                        "study_duration_weeks_number": study_duration_weeks_number,
                    },
                )
                assert (
                    len(records) != 0
                ), f"""The StudyVisit {study_visit_uid} contains in db wrong values for some of the following params:
                    StudyDay ({study_day_number}), StudyWeek ({study_week_number}), StudyDurationDays ({study_duration_days_number}), StudyDurationWeeks ({study_duration_weeks_number}), WeekInStudy ({study_duration_weeks_number})
                    """


def test_remove_empty_strings_or_replace_them_with_not_provided_text():
    non_empty_properties = [
        # Properties that should have been removed in the correction
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
        # Properties whose values should have been replaced with "not provided" in the correction
        ("CTTermAttributesValue", "definition"),
        ("CTCodelistAttributesValue", "definition"),
    ]

    err = []
    for label, prop in non_empty_properties:
        rs, _ = run_cypher_query(
            DB_DRIVER,
            f"""
            MATCH (n:{label})
            WHERE n.{prop} = ""
            RETURN COUNT(n)
            """,
        )

        if rs[0][0] != 0:
            err.append(
                f"Found {rs[0][0]} nodes of label `{label}` with empty string in property `{prop}`"
            )

    assert not err

    odm_items = api_get_paged(
        "/concepts/odms/items",
        params={"filters": json.dumps({"comment": {"v": [""], "op": "eq"}})},
        page_size=1,
    )
    assert not odm_items["items"], "Found ODM Items with empty string comment"


def test_migrate_study_selection_metadata_merge():
    studies, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_root:StudyRoot)-[:LATEST]->(study_value:StudyValue)
        WHERE NOT (study_root)-[:LATEST_LOCKED]->(study_value)
        return study_root.uid
        """,
    )
    for study in studies:
        study_uid = study[0]
        LOGGER.info(
            "Verifying successful StudySelectionMetadata merge for the following Study (%s)",
            study_uid,
        )

        # GET all study-activities
        res = api_get_paged(f"/studies/{study_uid}/study-activities")
        study_activities = res["items"]
        study_soa_groups = {}
        study_activity_groups = {}
        study_activity_subgroups = {}

        for study_activity in study_activities:
            study_soa_groups.setdefault(
                study_activity["study_soa_group"]["soa_group_term_uid"],
                study_activity["study_soa_group"]["study_soa_group_uid"],
            )
            if (
                study_activity["study_activity_group"]["study_activity_group_uid"]
                is not None
            ):
                study_activity_groups.setdefault(
                    study_activity["study_soa_group"]["soa_group_term_uid"], {}
                ).setdefault(
                    study_activity["study_activity_group"]["activity_group_uid"],
                    study_activity["study_activity_group"]["study_activity_group_uid"],
                )
            if (
                study_activity["study_activity_subgroup"]["study_activity_subgroup_uid"]
                is not None
            ):
                study_activity_subgroups.setdefault(
                    study_activity["study_soa_group"]["soa_group_term_uid"], {}
                ).setdefault(
                    study_activity["study_activity_group"]["activity_group_uid"], {}
                ).setdefault(
                    study_activity["study_activity_subgroup"]["activity_subgroup_uid"],
                    study_activity["study_activity_subgroup"][
                        "study_activity_subgroup_uid"
                    ],
                )

        for study_activity in study_activities:
            # assert each StudyActivity with the same SoAGroup CTTerm selected should have same SoAGroup selection
            assert (
                study_activity["study_soa_group"]["study_soa_group_uid"]
                == study_soa_groups[
                    study_activity["study_soa_group"]["soa_group_term_uid"]
                ]
            )

            if (
                study_activity["study_activity_group"]["study_activity_group_uid"]
                is not None
            ):
                # assert each StudyActivity with the same SoAGroup CTTerm and ActivityGroup selected should have same StudyActivityGroup
                assert (
                    study_activity["study_activity_group"]["study_activity_group_uid"]
                    == study_activity_groups[
                        study_activity["study_soa_group"]["soa_group_term_uid"]
                    ][study_activity["study_activity_group"]["activity_group_uid"]]
                )

            if (
                study_activity["study_activity_subgroup"]["study_activity_subgroup_uid"]
                is not None
            ):
                # assert each StudyActivity with the same SoAGroup CTTerm, ActivityGroup and ActivitySubGroup selected should have same StudyActivitySubGroup
                assert (
                    study_activity["study_activity_subgroup"][
                        "study_activity_subgroup_uid"
                    ]
                    == study_activity_subgroups[
                        study_activity["study_soa_group"]["soa_group_term_uid"]
                    ][study_activity["study_activity_group"]["activity_group_uid"]][
                        study_activity["study_activity_subgroup"][
                            "activity_subgroup_uid"
                        ]
                    ]
                )

        # StudySoAGroup
        _result, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)
            WITH DISTINCT study_root, study_value
            MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->
                (study_soa_group:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(flowchart_group_term_root:CTTermRoot)
            WHERE NOT (study_soa_group)<-[:BEFORE]-() AND NOT (study_soa_group)<-[]-(:Delete)

            // leave only a few rows that will represent distinct CTTermRoots that represent chosen SoA/Flowchart group
            WITH DISTINCT flowchart_group_term_root
            RETURN flowchart_group_term_root
            """,
            params={"study_uid": study_uid},
        )
        amount_of_soa_group_nodes = len(_result) if _result else 0
        assert amount_of_soa_group_nodes == len(study_soa_groups.keys())

        # StudyActivityGroup
        _result, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)
            WITH DISTINCT study_root, study_value
            MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->
                (study_activity_group:StudyActivityGroup)-[:HAS_SELECTED_ACTIVITY_GROUP]->(:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot)
            MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
            WHERE NOT (study_activity_group)<-[:BEFORE]-() AND NOT (study_activity_group)<-[]-(:Delete)

            // leave only a few rows that will represent distinct ActivityGroups in a specific StudySoAGroup
            WITH DISTINCT activity_group_root, study_soa_group.uid as study_soa_group_uid
            RETURN activity_group_root, study_soa_group_uid
            """,
            params={"study_uid": study_uid},
        )
        amount_of_study_activity_group_nodes = len(_result) if _result else 0
        all_group_nodes = 0
        for study_activity_group_dict in study_activity_groups.values():
            all_group_nodes += len(study_activity_group_dict.keys())
        assert amount_of_study_activity_group_nodes == all_group_nodes

        # StudyActivitySubGroup
        _result, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)
            WITH DISTINCT study_root, study_value
            MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->
                (study_activity_subgroup:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot)
            MATCH (study_activity_group:StudyActivityGroup)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(study_activity)
                -[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
            WHERE NOT (study_activity_subgroup)<-[:BEFORE]-() AND NOT (study_activity_subgroup)<-[]-(:Delete)

            // leave only a few rows that will represent distinct ActivitySubGroups in a specific StudySoAGroup and StudyActivityGroup
            WITH DISTINCT activity_subgroup_root, study_soa_group.uid as study_soa_group_uid, study_activity_group.uid as study_activity_group_uid
            RETURN activity_subgroup_root, study_soa_group_uid, study_activity_group_uid
            """,
            params={"study_uid": study_uid},
        )
        amount_of_study_activity_sub_group_nodes = len(_result) if _result else 0
        all_subgroup_nodes = 0
        for study_activity_group_dict in study_activity_subgroups.values():
            for study_activity_subgroup_dict in study_activity_group_dict.values():
                all_subgroup_nodes += len(study_activity_subgroup_dict.keys())
        assert amount_of_study_activity_sub_group_nodes == all_subgroup_nodes
