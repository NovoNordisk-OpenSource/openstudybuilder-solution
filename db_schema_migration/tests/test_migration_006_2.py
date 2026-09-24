import os

import pytest

from migrations import migration_006_2
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
    from tests.data.db_before_migration_006_2 import TEST_DATA
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


class MigrationStorage:

    study_act_soa_group_mapping_before_running_migration = None

    @classmethod
    def save_study_activities_before_migration(cls):
        studies, _ = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (study_root:StudyRoot) return study_root.uid
            """,
        )
        study_activities = []
        for study in studies:
            study_uid = study[0]
            res = api_get_paged(f"/studies/{study_uid}/study-activities", page_size=100)
            study_activities += res["items"]

        cls.study_act_soa_group_mapping_before_running_migration = {
            study_activity["study_activity_uid"]: study_activity["study_soa_group"][
                "soa_group_name"
            ]
            for study_activity in study_activities
        }


@pytest.fixture(scope="module")
def migration(initial_data):
    MigrationStorage.save_study_activities_before_migration()
    # Run migration
    migration_006_2.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


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
        migration_006_2.migrate_study_selection_metadata_merge(
            DB_DRIVER, logger, migration_006_2.MIGRATION_DESC
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


def test_fix_study_soa_group_edit_in_a_wrong_not_shared_way(migration):
    studies, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_root:StudyRoot) return study_root.uid
        """,
    )
    study_activities = []
    for study in studies:
        study_uid = study[0]
        logger.info(
            "Verifying StudySoAGroups are edited in the correct-shared across different StudyActivities way for the following Study (%s)",
            study_uid,
        )

        result = run_cypher_query(
            DB_DRIVER,
            """
            MATCH (study_root:StudyRoot {uid:$study_uid})-[:HAS_VERSION]->(study_value:StudyValue)-[:HAS_STUDY_ACTIVITY]->
                (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soa_group_before:StudySoAGroup)<-[:BEFORE]-(study_action:StudyAction)
            MATCH (soa_group_after:StudySoAGroup)<-[:AFTER]-(study_action)
            MATCH (soa_group_before)-[:HAS_FLOWCHART_GROUP]->(flowchart_term_before)
            MATCH (soa_group_after)-[:HAS_FLOWCHART_GROUP]->(flowchart_term_after)
            WHERE NOT study_action:Delete and flowchart_term_before <> flowchart_term_after
            RETURN study_activity.uid
            """,
            params={"study_uid": study_uid},
        )
        assert (
            len(result[0]) == 0
        ), f"There exist StudyActivity {result[0]} which links to the StudySoAGroup which is not the latest version of the StudySoAGroup"

        res = api_get_paged(f"/studies/{study_uid}/study-activities", page_size=100)
        study_activities += res["items"]

    # If test script is run, the before dictionary will be initailized
    # If verification script is run, the before_dictionary will be empty hence we shouldn't compare SoAGroups before migration and after
    if MigrationStorage.study_act_soa_group_mapping_before_running_migration:
        study_act_soa_group_mapping_after_running_migration = {
            study_activity["study_activity_uid"]: study_activity["study_soa_group"][
                "soa_group_name"
            ]
            for study_activity in study_activities
        }
        assert (
            MigrationStorage.study_act_soa_group_mapping_before_running_migration
            == study_act_soa_group_mapping_after_running_migration
        )


@pytest.mark.order(after="test_fix_study_soa_group_edit_in_a_wrong_not_shared_way")
def test_repeat_migrate_soa_group_edit_performed_in_wrong_way(migration):
    assert not any(
        migration_006_2.migrate_soa_group_edit_performed_in_wrong_way(
            DB_DRIVER, logger, migration_006_2.MIGRATION_DESC
        )
    ), "The second run for migration shouldn't return anything"


def test_submit_and_reject_activity_requests(migration):
    logger.info(
        "Verifying that all ActivityRequests are having is_request_final and is_request_rejected properties assigned"
    )
    result = run_cypher_query(
        DB_DRIVER,
        """    
            MATCH (:Library {name:'Requested'})-[:CONTAINS_CONCEPT]->(activity_request_root:ActivityRoot)-[:LATEST]->(activity_request_value:ActivityValue)
            WHERE activity_request_value.is_request_final IS NULL or activity_request_value.is_request_rejected IS NULL
            RETURN activity_request_value.name
        """,
    )
    assert (
        len(result[0]) == 0
    ), f"There exist ActivityRequest {result[0]} which has is_request_final or is_request_rejected property not set"


@pytest.mark.order(after="test_submit_and_reject_activity_requests")
def test_repeat_submit_and_reject_activity_requests(migration):
    assert not migration_006_2.migrate_submit_and_reject_activity_requests(
        DB_DRIVER, logger
    ), "The second run for migration shouldn't return anything"


def test_study_activities_linked_to_deleted_soa_group(migration):
    logger.info(
        "Verifying that all StudyActivities are linked to activte StudySoAGroups"
    )
    result = run_cypher_query(
        DB_DRIVER,
        """    
            MATCH (study_root:StudyRoot)--(:StudyValue)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->
                (study_soa_group:StudySoAGroup)-[:AFTER]-(delete:StudyAction:Delete)
            RETURN DISTINCT study_activity
        """,
    )
    assert (
        len(result[0]) == 0
    ), f"There exist StudyActivity {result[0]} which is linked to a deleted StudySoAGroup node"


@pytest.mark.order(after="test_study_activities_linked_to_deleted_soa_group")
def test_repeat_study_activities_linked_to_deleted_soa_group(migration):
    assert not any(
        migration_006_2.migrate_study_activities_linked_to_deleted_soa_group(
            DB_DRIVER, logger, migration_006_2.MIGRATION_DESC
        )
    ), "The second run for migration shouldn't return anything"


def test_migrate_remove_soa_group_node_without_any_study_activities(migration):
    logger.info(
        "Verifying that all StudyActivities are linked to activte StudySoAGroups"
    )
    result = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_soa_group:StudySoAGroup)-[:AFTER]-(study_action)
        WHERE 
            NOT (study_soa_group)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-(:StudyActivity) 
            AND NOT (study_soa_group)-[:BEFORE|AFTER]-(:Delete)
            AND NOT (study_soa_group)-[:BEFORE]-()
        RETURN study_soa_group
        """,
    )
    assert (
        len(result[0]) == 0
    ), f"There exist StudySoAGroup {result[0]} which is not Delete and it's not linked to any StudyActivities"


@pytest.mark.order(
    after="test_migrate_remove_soa_group_node_without_any_study_activities"
)
def test_repeat_migrate_remove_soa_group_node_without_any_study_activities(migration):
    assert (
        not migration_006_2.migrate_remove_soa_group_node_without_any_study_activities(
            DB_DRIVER, logger
        )
    ), ("The second run for migration shouldn't return anything")
