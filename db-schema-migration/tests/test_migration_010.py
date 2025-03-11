import os

import pytest

from migrations import migration_010
from migrations.utils.utils import (
    api_get,
    execute_statements,
    get_db_connection,
    get_db_driver,
    get_logger,
    run_cypher_query,
)
from tests import common
from tests.data.db_before_migration_010 import TEST_DATA
from tests.utils.utils import clear_db

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=protected-access
# pylint: disable=broad-except

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
    migration_010.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_migrate_unit_definition_properties(migration):
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (u:UnitDefinitionValue)
        WHERE u.molecular_weight_conv_expon IS NOT NULL
        RETURN *
        """,
    )
    assert (
        len(records) == 0
    ), "There shouldn't exist any UnitDefinitionValue node that has a molecular_weight_conv_expon property"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (u:UnitDefinitionValue)
        WHERE u.use_molecular_weight IS NULL
        RETURN *
        """,
    )
    assert (
        len(records) == 0
    ), "All UnitDefinitionValue nodes must have a use_molecular_weight property"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (u:UnitDefinitionValue)
        WHERE u.use_complex_unit_conversion IS NULL
        RETURN *
        """,
    )
    assert (
        len(records) == 0
    ), "All UnitDefinitionValue nodes must have a use_complex_unit_conversion property"


def test_migrate_preferred_time_unit(migration):
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_root:StudyRoot)-[:HAS_VERSION]-(study_value:StudyValue)
        WHERE NOT (study_value)-[:HAS_TIME_FIELD]->(:StudyTimeField {field_name:"preferred_time_unit"})
        RETURN *
        """,
    )
    assert (
        len(records) == 0
    ), "There shouldn't exist any StudyValue node that doesn't have preferred time unit node assigned"


@pytest.mark.order(after="test_migrate_preferred_time_unit")
def test_repeat_migrate_preferred_time_unit(migration):
    assert not migration_010.migrate_preferred_time_unit(DB_DRIVER, logger)


def test_migrate_soa_preferred_time_unit(migration):
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_root:StudyRoot)-[:HAS_VERSION]-(study_value:StudyValue)
        WHERE NOT (study_value)-[:HAS_TIME_FIELD]->(:StudyTimeField {field_name:"soa_preferred_time_unit"})
        RETURN *
        """,
    )
    assert (
        len(records) == 0
    ), "There shouldn't exist any StudyValue node that doesn't have SoA preferred time unit node assigned"


@pytest.mark.order(after="test_migrate_soa_preferred_time_unit")
def test_repeat_soa_migrate_preferred_time_unit(migration):
    assert not migration_010.migrate_soa_preferred_time_unit(DB_DRIVER, logger)


def test_locked_study_versions_have_protocol_soa_snapshot(migration):
    # Get all locked study versions
    study_versions, _ = run_cypher_query(
        DB_DRIVER,
        "MATCH (sr:StudyRoot)-[hv:HAS_VERSION {status: $study_status}]->(sv:StudyValue)"
        " RETURN sr.uid, hv.version",
        params={"study_status": "LOCKED"},
    )

    if len(study_versions) < 1:
        logger.warning("There are no studies with locked versions in the db.")
        return

    for study_uid, study_version in study_versions:
        study_activities, _ = run_cypher_query(
            DB_DRIVER,
            "MATCH (sr:StudyRoot {uid: $study_uid})"
            "-[hv:HAS_VERSION {status: $study_status, version: $study_version}]->(sv:StudyValue)"
            "-->(ss:StudyActivity)"
            " RETURN sr.uid, hv.version, ss.uid LIMIT 1",
            params={
                "study_uid": study_uid,
                "study_status": "LOCKED",
                "study_version": study_version,
            },
        )

        if len(study_activities) < 1:
            # has no StudySelection
            logger.info(
                "Skipping protocol SoA snapshot verification of study %s version %s has no StudyActivity nodes.",
                study_uid,
                study_version,
            )
            continue

        soa_cells, _ = run_cypher_query(
            DB_DRIVER,
            "MATCH (sr:StudyRoot {uid: $study_uid})"
            "-[hv:HAS_VERSION {status: $study_status, version: $study_version}]->(sv:StudyValue)"
            "-[cell:HAS_PROTOCOL_SOA_CELL]->(ss:StudySelection)"
            " RETURN sr.uid, hv.version, ss.uid",
            params={
                "study_uid": study_uid,
                "study_status": "LOCKED",
                "study_version": study_version,
            },
        )
        assert len(soa_cells) > 0, (
            f"Failed verifying protocol SoA snapshot of study {study_uid} version {study_version}"
            f" has no HAS_PROTOCOL_SOA_CELL relationship."
        )

        soa_footnotes, _ = run_cypher_query(
            DB_DRIVER,
            "MATCH (sr:StudyRoot {uid: $study_uid})"
            "-[hv:HAS_VERSION {status: $study_status, version: $study_version}]->(sv:StudyValue)"
            "-[fn:HAS_PROTOCOL_SOA_FOOTNOTE]->(sfn:StudySoAFootnote)-[]->(ss)"
            " RETURN DISTINCT sfn.uid",
            params={
                "study_uid": study_uid,
                "study_status": "LOCKED",
                "study_version": study_version,
            },
        )

        logger.info(
            "Verified protocol SoA snapshot of study %s version %s has %d cell references and %d footnotes",
            study_uid,
            study_version,
            len(soa_cells),
            len(soa_footnotes),
        )


def test_migrate_user_initials_into_author_id_and_user_nodes(migration):
    logger.info("Check User Identification migrations")

    # Assert that:
    # - Some User nodes exist. Each of them has not-null `user_id` and `username` field values.
    # - For each `author_id` field value there is one `User` node with the same `user_id` field value.
    # - Call some GET endpoints and assert that `author_username` is not null.

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n:CTPackage|StudyAction|Edit|Create|Delete)
        WHERE n.author_id is null
        RETURN n
        """,
    )
    assert (
        len(records) == 0
    ), "There shouldn't exist any relevant nodes with `author_id` field set to null"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n)-[rel:HAS_VERSION|HAS_TERM|HAD_TERM|LATEST_LOCKED|LATEST_RELEASED]->(m)
        WHERE rel.author_id is null
        RETURN rel
        """,
    )
    assert (
        len(records) == 0
    ), "There shouldn't exist any relevant relations with `author_id` field set to null"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n:CTPackage|StudyAction|Edit|Create|Delete)
        OPTIONAL MATCH (u:User {user_id: n.author_id})
        RETURN  n.author_id as node_author_id, 
                COUNT(DISTINCT u) as user_nodes_cnt
        """,
    )
    for row in records:
        assert (
            row["user_nodes_cnt"] == 1
        ), "For each node `author_id` value there must be one `User` node with the same `user_id` value"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n)-[rel:HAS_VERSION|HAS_TERM|HAD_TERM|LATEST_LOCKED|LATEST_RELEASED]->(m)
        OPTIONAL MATCH (u:User {user_id: rel.author_id})
        RETURN  rel.author_id as rel_author_id, 
                COUNT(DISTINCT u) as user_nodes_cnt
        """,
    )
    for row in records:
        assert (
            row["user_nodes_cnt"] == 1
        ), "For each relation `author_id` value there must be one `User` node with the same `user_id` value"

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n:User)
        WHERE n.user_id is null
        RETURN n
        """,
    )
    assert (
        len(records) == 0
    ), "There shouldn't exist any `User` node with `user_id` field set to null"

    # Call some GET endpoints and assert that `author_username` or `version_author` is not null
    endpoints1 = ["/configurations", "/ct/packages"]
    for endpoint in endpoints1:
        response = api_get(endpoint, params={"page_size": 100})
        data = response.json()
        for item in data:
            assert item.get("author_username") is not None

    endpoints2 = ["/studies"]
    for endpoint in endpoints2:
        response = api_get(endpoint, params={"page_size": 100})
        data = response.json()
        for item in data["items"]:
            assert (
                item["current_metadata"]["version_metadata"]["version_author"]
                is not None
            )


@pytest.mark.order(after="test_migrate_user_initials_into_author_id_and_user_nodes")
def test_repeat_migrate_user_initials_into_author_id_and_user_nodes(migration):
    migration_010.migrate_user_initials_into_author_id_and_user_nodes(DB_DRIVER, logger)
    test_migrate_user_initials_into_author_id_and_user_nodes(migration)


def test_migrate_unify_study_visit_window_units(migration):
    logger.info("Check StudyVisit window unit unification")

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_root:StudyRoot)-[:LATEST]->(study_value:StudyValue)
        WHERE NOT (study_root)-[:LATEST_LOCKED]-(study_value)
        MATCH (study_value)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit)-[:HAS_WINDOW_UNIT]->(unit_root:UnitDefinitionRoot)-[:LATEST]->(unit_value:UnitDefinitionValue)
        WITH DISTINCT study_root, collect(DISTINCT unit_value.name) AS units
        WHERE size(units) > 1
        RETURN study_root.uid
        """,
    )
    assert (
        len(records) == 0
    ), "There shouldn't exist any Study with StudyVisits that have different units used for StudyVisit window."

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_visit:StudyVisit)
        WHERE NOT (study_visit)-[:HAS_WINDOW_UNIT]-()
        RETURN study_visit
        """,
    )
    assert (
        len(records) == 0
    ), "There shouldn't exist any StudyVisit without defined relationship to window unit Unit Definition."


@pytest.mark.order(after="test_migrate_unify_study_visit_window_units")
def test_repeat_migrate_unify_study_visit_window_units(migration):
    assert not migration_010.migrate_unify_study_visit_window_units(DB_DRIVER, logger)


def test_migrate_study_selection_metadata_merge(migration):
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

@pytest.mark.order(after="test_migrate_study_selection_metadata_merge")
def test_repeat_migrate_study_selection_metadata_merge(migration):
    assert not migration_010.migrate_study_selection_metadata_merge(DB_DRIVER, logger)
