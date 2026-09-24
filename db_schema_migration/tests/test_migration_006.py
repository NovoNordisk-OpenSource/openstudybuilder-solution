import os

import pytest

from migrations import migration_006
from migrations.utils.utils import (
    api_get,
    api_get_paged,
    api_patch,
    execute_statements,
    get_db_connection,
    get_db_driver,
    get_logger,
    run_cypher_query,
)
from tests import common

try:
    from tests.data.db_before_migration_006 import TEST_DATA
except ImportError:
    TEST_DATA = ""
from tests.utils.utils import clear_db

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=protected-access

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

db = get_db_connection()
DB_DRIVER = get_db_driver()
logger = get_logger(os.path.basename(__file__))


@pytest.fixture(scope="module")
def initial_data():
    """Insert test data"""
    clear_db()
    execute_statements(TEST_DATA)


@pytest.fixture(scope="module")
def migration(initial_data):
    # Run migration
    migration_006.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_migrate_study_activity_instances(migration):
    studies, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_root:StudyRoot) return study_root.uid
        """,
    )
    for study in studies:
        study_uid = study[0]
        logger.info(
            "Verifying that StudyActivityInstances are migrated for the following Study (%s)",
            study_uid,
        )

        res = api_get_paged(
            f"/studies/{study_uid}/study-activities",
            params={
                "filters": '{"activity.library_name":{ "v": ["Requested"], "op": "ne"}}'
            },
            page_size=10,
        )
        study_activities = res["items"]
        if len(study_activities) > 0:
            res = api_get_paged(
                f"/studies/{study_uid}/study-activity-instances",
                page_size=10,
            )
            study_activity_instances = res["items"]
            assert (
                len(study_activity_instances) > 0
            ), "If there exist some StudyActivities, the StudyActivityInstances should also exist"

            ### This is disabled for now, see below
            study_activity_instance_dict: dict = {}
            # vals: list = []
            for study_activity_instance in study_activity_instances:
                assert study_activity_instance["activity"] is not None
                study_activity_uid = study_activity_instance["study_activity_uid"]
                response = api_get(
                    f"/studies/{study_uid}/study-activities/{study_activity_uid}"
                )
                assert response.status_code == 200
                res = response.json()
                assert (
                    study_activity_instance["activity"]["uid"] == res["activity"]["uid"]
                )
                activity_instance = study_activity_instance["activity_instance"]
                if activity_instance:
                    response = api_get(
                        f"/concepts/activities/activity-instances/{activity_instance['uid']}/versions"
                    )
                    assert response.status_code == 200
                    res = response.json()
                    activity_uids = []
                    for activity_instance in res:
                        activity_uids.extend(
                            [
                                activity_grouping["activity"]["uid"]
                                for activity_grouping in activity_instance[
                                    "activity_groupings"
                                ]
                            ]
                        )
                    assert study_activity_instance["activity"]["uid"] in activity_uids

                study_activity_instance_dict[
                    study_activity_instance["study_activity_instance_uid"]
                ] = (
                    study_activity_instance["activity"]["uid"],
                    study_activity_instance["study_activity_subgroup"][
                        "activity_subgroup_uid"
                    ],
                    study_activity_instance["study_activity_group"][
                        "activity_group_uid"
                    ],
                    (
                        study_activity_instance["activity_instance"]["uid"]
                        if study_activity_instance["activity_instance"]
                        else None
                    ),
                )
            #     vals = list(study_activity_instance_dict.values())
            # assert len(set(vals)) == len(
            #     vals
            # ), f"There exists some duplicated StudyActivityInstance in Study ({study_uid})"


@pytest.mark.order(after="test_migrate_study_activity_instances")
def test_repeat_migrate_study_activity_instances(migration):
    assert not any(
        migration_006.migrate_study_activity_instances(DB_DRIVER, logger)
    ), "The second run for migration shouldn't return anything"


def test_update_insertion_visit_to_manually_defined(migration):
    query = """
        MATCH (study_visit:StudyVisit) 
        WHERE study_visit.visit_class = "INSERTION_VISIT"
        RETURN study_visit
    """
    result = run_cypher_query(DB_DRIVER, query)
    assert (
        len(result[0]) == 0
    ), "There shouldn't be any INSERTION_VISITs. All of them should be updated to MANUALLY_DEFINED_VISITs"


@pytest.mark.order(after="test_update_insertion_visit_to_manually_defined")
def test_repeat_update_insertion_visit_to_manually_defined(migration):
    assert not migration_006.update_insertion_visit_to_manually_defined_visit(
        DB_DRIVER, logger
    ), "The second run for migration shouldn't return anything"


def test_fix_duration_properties_for_visits_with_negative_timings(migration):
    res = api_get("/concepts/numeric-values", params={"page_size": 0})
    assert res.status_code == 200
    res = api_get("/concepts/study-days", params={"page_size": 0})
    assert res.status_code == 200
    res = api_get("/concepts/study-duration-days", params={"page_size": 0})
    assert res.status_code == 200
    res = api_get("/concepts/study-weeks", params={"page_size": 0})
    assert res.status_code == 200
    res = api_get("/concepts/study-duration-weeks", params={"page_size": 0})
    assert res.status_code == 200
    res = api_get("/concepts/study-duration-weeks", params={"page_size": 0})
    assert res.status_code == 200

    query = """
        MATCH (study_visit:StudyVisit)-[:HAS_STUDY_DAY]->(:StudyDayRoot)-[:LATEST]->(study_day_value:StudyDayValue)
        MATCH (study_visit)-[:HAS_STUDY_DURATION_DAYS]->(:StudyDurationDaysRoot)-[:LATEST]->(study_duration_days_value:StudyDurationDaysValue)
        MATCH (study_visit:StudyVisit)-[:HAS_STUDY_WEEK]->(:StudyWeekRoot)-[:LATEST]->(study_week_value:StudyWeekValue)
        MATCH (study_visit)-[:HAS_STUDY_DURATION_WEEKS]->(:StudyDurationWeeksRoot)-[:LATEST]->(study_duration_weeks_value:StudyDurationWeeksValue)
        MATCH (study_visit)-[:HAS_WEEK_IN_STUDY]->(:WeekInStudyRoot)-[:LATEST]->(week_in_study_value:WeekInStudyValue)
        RETURN study_visit.uid, study_day_value.value, study_duration_days_value.value, study_week_value.value, study_duration_weeks_value.value, week_in_study_value.value
    """
    study_visits, _ = run_cypher_query(DB_DRIVER, query)
    for study_visit in study_visits:
        study_visit_uid = study_visit[0]
        study_day_value = study_visit[1]
        study_duration_days_value = study_visit[2]
        study_week_value = study_visit[3]
        study_duration_weeks_value = study_visit[4]
        week_in_study_value = study_visit[4]
        if study_day_value % 7 == 0 and study_day_value < 0:
            assert (
                study_day_value == study_duration_days_value
            ), f"The StudyDay-StudyDurationDays contains mismatched values for the Visit ({study_visit_uid})"
            assert (
                study_week_value == study_duration_weeks_value
            ), f"The StudyWeek-StudyDurationWeeks contains mismatched values for the Visit ({study_visit_uid})"
            assert (
                study_week_value == week_in_study_value
            ), f"The StudyWeek-WeekInStudy contains mismatched values for the Visit ({study_visit_uid})"
        elif study_day_value < 0:
            assert (
                study_day_value == study_duration_days_value
            ), f"The StudyDay-StudyDurationDays contains mismatched values for the Visit ({study_visit_uid})"
            assert (
                study_week_value == study_duration_weeks_value - 1
            ), f"The StudyWeek-StudyDurationWeeks contains mismatched values for the Visit ({study_visit_uid})"
            assert (
                study_week_value == week_in_study_value - 1
            ), f"The StudyWeek-WeekInStudy contains mismatched values for the Visit ({study_visit_uid})"
        elif study_day_value > 0:
            assert (
                study_day_value == study_duration_days_value + 1
            ), f"The StudyDay-StudyDurationDays contains mismatched values for the Visit ({study_visit_uid})"
            assert (
                study_week_value == study_duration_weeks_value + 1
            ), f"The StudyWeek-StudyDurationWeeks contains mismatched values for the Visit ({study_visit_uid})"
            assert (
                study_week_value == week_in_study_value + 1
            ), f"The StudyWeek-WeekInStudy contains mismatched values for the Visit ({study_visit_uid})"

    studies, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_root:StudyRoot) return study_root.uid
        """,
    )
    for study in studies:
        study_uid = study[0]
        logger.info(
            "Verifying that StudyVisits have proper timing nodes for the following Study (%s)",
            study_uid,
        )
        res = api_get(f"/studies/{study_uid}/study-visits", params={"page_size": 0})
        study_visits = res.json()["items"]
        for study_visit in study_visits:
            if study_visit["visit_class"] not in (
                "UNSCHEDULED_VISIT",
                "NON_VISIT",
                "SPECIAL_VISIT",
            ):
                study_day_number = study_visit["study_day_number"]
                study_duration_days_number = int(
                    study_visit["study_duration_days_label"].split()[0]
                )
                study_week_number = study_visit["study_week_number"]
                study_duration_weeks_number = int(
                    study_visit["study_duration_weeks_label"].split()[0]
                )
                week_in_study_number = int(
                    study_visit["week_in_study_label"].split()[1]
                )
                if study_day_number % 7 == 0 and study_day_number < 0:
                    assert study_day_number == study_duration_days_number
                    assert study_week_number == study_duration_weeks_number
                    assert study_week_number == week_in_study_number
                elif study_day_number < 0:
                    assert study_day_number == study_duration_days_number
                    assert study_week_number == study_duration_weeks_number - 1
                    assert study_week_number == week_in_study_number - 1
                elif study_day_number > 0:
                    assert study_day_number == study_duration_days_number + 1
                    assert study_week_number == study_duration_weeks_number + 1
                    assert study_week_number == week_in_study_number + 1


@pytest.mark.order(
    after="test_fix_duration_properties_for_visits_with_negative_timings"
)
def test_repeat_fix_duration_properties_for_visits_with_negative_timings(migration):
    assert not migration_006.fix_duration_properties_for_visits_with_negative_timings(
        DB_DRIVER, logger, migration_006.MIGRATION_DESC
    ), "The second run for migration shouldn't return anything"


def test_merge_reuse_study_selection_metadata(migration):
    studies, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_root:StudyRoot) return study_root.uid
        """,
    )
    for study in studies:
        study_uid = study[0]
        logger.info(
            "Verifying successful StudySelectionMetadata merge for the following Study (%s)",
            study_uid,
        )

        # GET all study-activities
        res = api_get(f"/studies/{study_uid}/study-activities", params={"page_size": 0})
        assert res.status_code == 200
        study_activities = res.json()["items"]
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
            WITH DISTINCT activity_group_root, study_soa_group
            RETURN activity_group_root, study_soa_group
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
            WITH DISTINCT activity_subgroup_root, study_soa_group, study_activity_group
            RETURN activity_subgroup_root, study_soa_group, study_activity_group
            """,
            params={"study_uid": study_uid},
        )
        amount_of_study_activity_sub_group_nodes = len(_result) if _result else 0
        all_subgroup_nodes = 0
        for study_activity_group_dict in study_activity_subgroups.values():
            for study_activity_subgroup_dict in study_activity_group_dict.values():
                all_subgroup_nodes += len(study_activity_subgroup_dict.keys())
        assert amount_of_study_activity_sub_group_nodes == all_subgroup_nodes


@pytest.mark.order(after="test_merge_reuse_study_selection_metadata")
def test_repeat_merge_reuse_study_selection_metadata(migration):
    assert not any(
        migration_006.migrate_study_selection_metadata_merge(
            DB_DRIVER, logger, migration_006.MIGRATION_DESC
        )
    ), "The second run for migration shouldn't return anything"


def test_patch_visibility_flags_after_study_selection_reuse_migration(migration):
    studies, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_root:StudyRoot) return study_root.uid
        """,
    )
    for study in studies:
        study_uid = study[0]
        logger.info(
            "Verifying successful StudySelectionMetadata merge for the following Study (%s)",
            study_uid,
        )

        # GET all study-activities
        res = api_get(f"/studies/{study_uid}/study-activities", params={"page_size": 0})
        assert res.status_code == 200
        study_activities = res.json()["items"]
        if study_activities:
            # PATCH protocol-flowchart soa-group visibility flags
            soa_group_to_edit = study_activities[0]["study_soa_group"][
                "study_soa_group_uid"
            ]
            current_show_soa_group = study_activities[0][
                "show_soa_group_in_protocol_flowchart"
            ]
            api_patch(
                path=f"/studies/{study_uid}/study-soa-groups/{soa_group_to_edit}",
                payload={
                    "show_soa_group_in_protocol_flowchart": not current_show_soa_group
                },
                params={"page_size": 0},
            )
            res = api_get(
                f"/studies/{study_uid}/study-activities", params={"page_size": 0}
            )
            study_activities = res.json()["items"]
            for study_activity in study_activities:
                if (
                    study_activity["study_soa_group"]["study_soa_group_uid"]
                    == soa_group_to_edit
                ):
                    assert (
                        study_activity["show_soa_group_in_protocol_flowchart"]
                        is not current_show_soa_group
                    )

            api_patch(
                path=f"/studies/{study_uid}/study-soa-groups/{soa_group_to_edit}",
                payload={
                    "show_soa_group_in_protocol_flowchart": current_show_soa_group
                },
                params={"page_size": 0},
            )
            res = api_get(
                f"/studies/{study_uid}/study-activities", params={"page_size": 0}
            )
            study_activities = res.json()["items"]
            for study_activity in study_activities:
                if (
                    study_activity["study_soa_group"]["study_soa_group_uid"]
                    == soa_group_to_edit
                ):
                    assert (
                        study_activity["show_soa_group_in_protocol_flowchart"]
                        is current_show_soa_group
                    )

            # PATCH protocol-flowchart study-activity-group visibility flags
            study_activity_group_to_edit = study_activities[0]["study_activity_group"][
                "study_activity_group_uid"
            ]
            current_show_activity_group = study_activities[0][
                "show_activity_group_in_protocol_flowchart"
            ]
            api_patch(
                path=f"/studies/{study_uid}/study-activity-groups/{study_activity_group_to_edit}",
                payload={
                    "show_activity_group_in_protocol_flowchart": not current_show_activity_group
                },
                params={"page_size": 0},
            )
            res = api_get(
                f"/studies/{study_uid}/study-activities", params={"page_size": 0}
            )
            study_activities = res.json()["items"]
            for study_activity in study_activities:
                if (
                    study_activity["study_activity_group"]["study_activity_group_uid"]
                    == study_activity_group_to_edit
                ):
                    assert (
                        study_activity["show_activity_group_in_protocol_flowchart"]
                        is not current_show_activity_group
                    )

            api_patch(
                path=f"/studies/{study_uid}/study-activity-groups/{study_activity_group_to_edit}",
                payload={
                    "show_activity_group_in_protocol_flowchart": current_show_activity_group
                },
                params={"page_size": 0},
            )
            res = api_get(
                f"/studies/{study_uid}/study-activities", params={"page_size": 0}
            )
            study_activities = res.json()["items"]
            for study_activity in study_activities:
                if (
                    study_activity["study_activity_group"]["study_activity_group_uid"]
                    == study_activity_group_to_edit
                ):
                    assert (
                        study_activity["show_activity_group_in_protocol_flowchart"]
                        is current_show_activity_group
                    )

            # PATCH protocol-flowchart study-activity-subgroup visibility flags
            study_activity_subgroup_to_edit = study_activities[0][
                "study_activity_subgroup"
            ]["study_activity_subgroup_uid"]
            current_show_activity_subgroup = study_activities[0][
                "show_activity_subgroup_in_protocol_flowchart"
            ]
            api_patch(
                path=f"/studies/{study_uid}/study-activity-subgroups/{study_activity_subgroup_to_edit}",
                payload={
                    "show_activity_subgroup_in_protocol_flowchart": not current_show_activity_subgroup
                },
                params={"page_size": 0},
            )
            res = api_get(
                f"/studies/{study_uid}/study-activities", params={"page_size": 0}
            )
            study_activities = res.json()["items"]
            for study_activity in study_activities:
                if (
                    study_activity["study_activity_subgroup"][
                        "study_activity_subgroup_uid"
                    ]
                    == study_activity_subgroup_to_edit
                ):
                    assert (
                        study_activity["show_activity_subgroup_in_protocol_flowchart"]
                        is not current_show_activity_subgroup
                    )

            api_patch(
                path=f"/studies/{study_uid}/study-activity-subgroups/{study_activity_subgroup_to_edit}",
                payload={
                    "show_activity_subgroup_in_protocol_flowchart": current_show_activity_subgroup
                },
                params={"page_size": 0},
            )
            res = api_get(
                f"/studies/{study_uid}/study-activities", params={"page_size": 0}
            )
            study_activities = res.json()["items"]
            for study_activity in study_activities:
                if (
                    study_activity["study_activity_subgroup"][
                        "study_activity_subgroup_uid"
                    ]
                    == study_activity_subgroup_to_edit
                ):
                    assert (
                        study_activity["show_activity_subgroup_in_protocol_flowchart"]
                        is current_show_activity_subgroup
                    )


def test_merge_multiple_study_activity_subgroup_and_group_nodes(migration):
    logger.info("Check for multiple group/subgroup relationships for StudyActivities")
    # StudyActivityGroup
    result = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
        WITH study_activity, collect(study_activity_group) as sag
        WHERE size(sag) > 1
        RETURN study_activity
        """,
    )
    assert (
        len(result[0]) == 0
    ), f"StudyActivity {result[0]} contains multiple StudyActivityGroups"

    result = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_activity_group:StudyActivityGroup)
        WHERE NOT ((study_activity_group)-[:BEFORE]-() or (study_activity_group)-[:AFTER]-())
        RETURN study_activity_group
        """,
    )
    assert (
        len(result[0]) == 0
    ), f"There exist StudyActivityGroup {result[0]} which doesn't have StudyAction relationship"
    result = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_activity:StudyActivity)-[:HAS_SELECTED_ACTIVITY]->(:ActivityValue)<-[:HAS_VERSION]-(:ActivityRoot)<-[:CONTAINS_CONCEPT]-(activity_library)
        WHERE activity_library.name <> 'Requested' AND NOT (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(:StudyActivityGroup)
        RETURN study_activity
        """,
    )
    assert (
        len(result[0]) == 0
    ), f"Study_activity {result[0]} is missing StudyActivityGroup node"

    # StudyActivitySubGroup
    result = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
        WITH study_activity, collect(study_activity_subgroup) as sags
        WHERE size(sags) > 1
        RETURN study_activity
        """,
    )
    assert (
        len(result[0]) == 0
    ), f"StudyActivity {result[0]} contains multiple StudyActivitySubGroups"
    result = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_activity_subgroup:StudyActivitySubGroup)
        WHERE NOT ((study_activity_subgroup)-[:BEFORE]-() or (study_activity_subgroup)-[:AFTER]-())
        RETURN study_activity_subgroup
        """,
    )
    assert (
        len(result[0]) == 0
    ), f"There exist StudyActivitySubGroup {result[0]} which doesn't have StudyAction relationship"
    result = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_activity:StudyActivity)-[:HAS_SELECTED_ACTIVITY]->(:ActivityValue)<-[:HAS_VERSION]-(:ActivityRoot)<-[:CONTAINS_CONCEPT]-(activity_library)
        WHERE activity_library.name <> 'Requested' AND NOT (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]-(:StudyActivitySubGroup)
        RETURN study_activity
        """,
    )
    assert (
        len(result[0]) == 0
    ), f"Study_activity {result[0]} is missing StudyActivitySubGroup node"

    studies = migration_006.get_correct_groupings()
    for study_number, activities_to_migrate in studies.items():
        for study_activity_uid, correct_groupings in activities_to_migrate.items():
            study_activity_exists, _ = run_cypher_query(
                DB_DRIVER,
                """
                    MATCH (sr:StudyRoot)-[:LATEST]->(sv:StudyValue {study_number: $study_number})-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity {uid:$study_activity_uid})
                    RETURN sr.uid
                        """,
                params={
                    "study_activity_uid": study_activity_uid,
                    "study_number": study_number,
                },
            )

            # StudyActivity has to exists in the test database
            if len(study_activity_exists) > 0:
                study_uid = study_activity_exists[0][0]
                response = api_get(
                    f"/studies/{study_uid}/study-activities/{study_activity_uid}"
                )
                assert response.status_code == 200
                study_activity = response.json()
                # StudyActivityGroup
                corrected_group = correct_groupings.get("correct_group")
                if corrected_group:
                    result, _ = run_cypher_query(
                        DB_DRIVER,
                        """
                        MATCH (study_activity:StudyActivity {uid:$study_activity_uid})-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(:StudyActivityGroup)-
                            [:HAS_SELECTED_ACTIVITY_GROUP]->(agv:ActivityGroupValue)
                        RETURN agv.name
                        """,
                        params={"study_activity_uid": study_activity_uid},
                    )
                    assert (
                        result[0][0] == corrected_group
                    ), f"Study_activity {study_activity_uid} doesn't have a correct group {corrected_group}"
                    assert (
                        study_activity["study_activity_group"]["activity_group_name"]
                        == corrected_group
                    )

                # StudyActivitySubGroup
                corrected_subgroup = correct_groupings.get("correct_subgroup")
                if corrected_subgroup:
                    result, _ = run_cypher_query(
                        DB_DRIVER,
                        """
                        MATCH (study_activity:StudyActivity {uid:$study_activity_uid})-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]-(:StudyActivitySubGroup)-
                            [:HAS_SELECTED_ACTIVITY_SUBGROUP]->(asgv:ActivitySubGroupValue)
                        RETURN asgv.name
                        """,
                        params={"study_activity_uid": study_activity_uid},
                    )
                    assert (
                        result[0][0] == corrected_subgroup
                    ), f"Study_activity {study_activity_uid} doesn't have a correct group {corrected_subgroup}"
                    assert (
                        study_activity["study_activity_subgroup"][
                            "activity_subgroup_name"
                        ]
                        == corrected_subgroup
                    )


@pytest.mark.order(after="test_merge_multiple_study_activity_subgroup_and_group_nodes")
def test_repeat_merge_multiple_study_activity_subgroup_and_group_nodes(migration):
    assert not any(
        migration_006.merge_multiple_study_activity_subgroup_and_group_nodes(
            DB_DRIVER, logger, migration_006.MIGRATION_DESC
        )
    ), "The second run for migration shouldn't return anything"


def test_fix_not_migrated_study_soa_groups(migration):
    logger.info("Check for not migrated StudySoAGroup nodes")
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_activity:StudyActivity)
        WHERE NOT (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(:StudySoAGroup) OR (study_activity)-[:HAS_FLOWCHART_GROUP]->(:CTTermRoot)
        RETURN study_activity
        """,
    )
    assert (
        len(records) == 0
    ), f"Found {len(records)} StudyActivities having SoAGroup defined in the old way - without :StudySoAGroup node"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
        WITH study_activity, collect(study_soa_group) as ct
        WHERE size(ct) > 1
        RETURN study_activity
        """,
    )
    assert (
        len(records) == 0
    ), f"Found {len(records)} StudyActivities having more than one StudySoAGroup"


@pytest.mark.order(after="test_fix_not_migrated_study_soa_groups")
def test_repeat_fix_not_migrated_study_soa_groups(migration):
    assert not migration_006.fix_not_migrated_study_soa_groups(
        DB_DRIVER, logger, migration_006.MIGRATION_DESC
    )
