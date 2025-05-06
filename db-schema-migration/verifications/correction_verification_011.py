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
            if study_visit["visit_class"] not in [
                "UNSCHEDULED_VISIT",
                "NON_VISIT",
                "SPECIAL_VISIT",
            ]:
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
