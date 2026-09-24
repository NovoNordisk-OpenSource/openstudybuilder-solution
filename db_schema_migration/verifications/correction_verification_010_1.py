"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import os

from data_corrections.utils.utils import get_db_driver, run_cypher_query
from migrations.utils.utils import api_get, get_logger

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()


def test_separate_study_activity_group_subgroup_from_different_soa_groups():
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
            "Verifying successful separation of study activity group and subgroup that lives in different SoAGroup for (%s) Study",
            study_uid,
        )

        # GET all study-activities
        res = api_get(f"/studies/{study_uid}/study-activities", params={"page_size": 0})
        assert res.status_code == 200
        study_activities = res.json()["items"]
        study_activity_groups_under_soa_groups = {}
        study_activity_subgroups_under_study_activity_groups = {}
        for study_activity in study_activities:

            if (
                study_activity["study_activity_group"]["study_activity_group_uid"]
                is not None
            ):
                # Given StudyActivityGroup should exist only in one SoAGroup
                assert study_activity["study_soa_group"][
                    "soa_group_term_uid"
                ] == study_activity_groups_under_soa_groups.setdefault(
                    study_activity["study_activity_group"]["study_activity_group_uid"],
                    study_activity["study_soa_group"]["soa_group_term_uid"],
                )

            if (
                study_activity["study_activity_subgroup"]["study_activity_subgroup_uid"]
                is not None
            ):
                # Given StudyActivitySubGroup should exist only in one StudyActivityGroup
                assert study_activity["study_activity_group"][
                    "study_activity_group_uid"
                ] == study_activity_subgroups_under_study_activity_groups.setdefault(
                    study_activity["study_activity_subgroup"][
                        "study_activity_subgroup_uid"
                    ],
                    study_activity["study_activity_group"]["study_activity_group_uid"],
                )

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
        
            RETURN study_activity_group, distinct_soa_groups
            """,
            params={"study_uid": study_uid},
        )
        assert (
            len(_result) == 0
        ), f"Found {len(_result)} same StudyActivityGroup node existing in different StudySoAGroups"

        # StudyActivitySubGroup
        _result, _ = run_cypher_query(
            DB_DRIVER,
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
                study_activity_subgroup.show_activity_group_in_protocol_flowchart AS is_visible
            // condition to not perform migration twice
            WHERE size(distinct_study_soa_groups) > 1

            MATCH (study_value)-[:HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]
                -(:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-(study_soa_group:StudySoAGroup)
            RETURN study_activity_subgroup, distinct_study_soa_groups
            """,
            params={"study_uid": study_uid},
        )
        assert (
            len(_result) == 0
        ), f"Found {len(_result)} same StudyActivitySubGroup node existing in different StudyActivityGroups: {_result}"
