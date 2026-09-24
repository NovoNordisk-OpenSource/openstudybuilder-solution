import os

import pytest

from migrations import migration_005
from migrations.utils.utils import (
    api_get,
    api_get_paged,
    execute_statements,
    get_db_connection,
    get_logger,
)
from tests import common

try:
    from tests.data.db_before_migration_005 import TEST_DATA
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
logger = get_logger(os.path.basename(__file__))


@pytest.fixture(scope="module")
def initial_data():
    """Insert test data"""
    clear_db()
    execute_statements(TEST_DATA)


@pytest.fixture(scope="module")
def migration(initial_data):
    # Run migration
    migration_005.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_fix_study_epoch_order(migration):
    studies, _ = db.cypher_query("""
        MATCH (study_root:StudyRoot) return study_root.uid
        """)
    for study in studies:
        study_uid = study[0]
        logger.info(
            "Verifying that StudyEpochs have consequent orders for the following Study (%s)",
            study_uid,
        )

        res = api_get(f"/studies/{study_uid}/study-epochs", params={"page_size": 0})
        study_epochs = res.json()["items"]
        for idx, study_epoch in enumerate(study_epochs, start=1):
            assert study_epoch["order"] == idx


def test_link_variables_with_value_terms(migration):
    incomplete_links, _ = db.cypher_query("""
            MATCH (v:DatasetVariable)-->(dvi:DatasetVariableInstance WHERE dvi.value_list IS NOT NULL)
            OPTIONAL MATCH (dvi)-[:REFERENCES_TERM]->(term)
            WITH v, dvi, size(dvi.value_list) AS value_list_size, count(DISTINCT term) AS term_rel_number
            WHERE value_list_size <> term_rel_number
            RETURN v.uid AS variable_uid, dvi.value_list AS value_list, value_list_size, term_rel_number
        """)

    assert incomplete_links == []


def test_study_field_deletion_convention(migration):
    query = """
        MATCH (del:Delete)-[ss_del]-(ss)
        WHERE NOT ss:StudyRoot AND
            (ss:StudyField)
        WITH del,collect(DISTINCT ss) as ss_collected , COUNT(DISTINCT ss) AS count_ss_del
        WHERE count_ss_del<2
        RETURN *
    """
    result = db.cypher_query(query)
    assert len(result[0]) == 0, "There's still a wrong deleted StudyFields"

    params = {"has_study_activity": True}
    study_endpoint = "/studies"
    studies = api_get(study_endpoint, params, check_ok_status=False).json()["items"]
    study_uid = studies[0]["uid"] if studies else None
    if study_uid:
        logger.info("Found a Study with StudyActivity selection")
        study_endpoint = f"/studies/{study_uid}"
        api_get(study_endpoint)


def test_add_missing_latest_relationships(migration):
    excluded_labels = [
        "ClassVariableRoot",
        "DatasetClassRoot",
        "DatasetRoot",
        "DatasetScenarioRoot",
        "DatasetVariableRoot",
        "DataModelIGRoot",
        "DataModelRoot",
        "StudyRoot",
    ]
    for status, relationship in (
        ("Draft", "LATEST_DRAFT"),
        ("Final", "LATEST_FINAL"),
        ("Retired", "LATEST_RETIRED"),
    ):
        query = f"""
            MATCH (roots)-[:HAS_VERSION {{status: '{status}'}}]->()
            WHERE none(label in labels(roots) WHERE label IN {excluded_labels})
            WITH DISTINCT roots as root
            CALL {{
                    WITH root
                    // Sort by version and dates
                    MATCH (root)-[hv:HAS_VERSION {{status: '{status}'}}]->(version)
                    WITH root, hv, version
                    ORDER BY
                        toInteger(split(hv.version, '.')[0]) ASC,
                        toInteger(split(hv.version, '.')[1]) ASC,
                        hv.end_date ASC,
                        hv.start_date ASC
                    WITH last(collect(version)) as latest_via_hv
                    RETURN latest_via_hv
                }}
            WITH root WHERE NOT (root)-[:{relationship}]->(latest_via_hv)
            RETURN root
            """
        result = db.cypher_query(query)
        assert len(result[0]) == 0, f"There are missing {relationship} relationships"


def test_study_activity_group_is_linked_to_real_study_root_audit_trail_node(migration):
    query = """
        MATCH (study_activity_group:StudyActivityGroup)--(action:StudyAction)<-[:AUDIT_TRAIL]-(audit_trail_node)
        WHERE NOT audit_trail_node:StudyRoot
        RETURN *
    """
    result = db.cypher_query(query)
    assert (
        len(result[0]) == 0
    ), "There's still a StudyActivityGroup node linked to broken Audit Trail node"


def test_migrate_study_activity_instances(migration):
    studies, _ = db.cypher_query("""
        MATCH (study_root:StudyRoot) return study_root.uid
        """)
    for study in studies:
        study_uid = study[0]
        logger.info(
            "Verifying that StudyActivityInstances are migrated for the following Study (%s)",
            study_uid,
        )

        res = api_get_paged(f"/studies/{study_uid}/study-activities", page_size=50)
        study_activities = res["items"]
        if len(study_activities) > 0:
            res = api_get_paged(
                f"/studies/{study_uid}/study-activity-instances",
                page_size=50,
            )
            study_activity_instances = res["items"]
            assert (
                len(study_activity_instances) > 0
            ), "If there exist some StudyActivities, the StudyActivityInstances should also exist"

            ### This is disabled for now, see below
            study_activity_instance_dict: dict = {}
            vals: list = []
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
                vals = list(study_activity_instance_dict.values())
            assert len(set(vals)) == len(
                vals
            ), f"There exists some duplicated StudyActivityInstance in Study ({study_uid})"


def test_remove_duplicated_study_activity_schedules(migration):
    studies, _ = db.cypher_query("""
        MATCH (study_root:StudyRoot) return study_root.uid
        """)
    for study in studies:
        study_uid = study[0]
        logger.info(
            "Verifying that StudyActivityInstances are migrated for the following Study (%s)",
            study_uid,
        )
        response = api_get(f"/studies/{study_uid}/study-activity-schedules")
        assert response.status_code == 200
        study_activity_schedules = response.json()
        study_activity_schedule_uids = [
            (
                study_activity_schedule["study_activity_uid"],
                study_activity_schedule["study_visit_uid"],
            )
            for study_activity_schedule in study_activity_schedules
        ]
        assert len(study_activity_schedule_uids) == len(
            set(study_activity_schedule_uids)
        ), f"Study {study_uid} contains duplicated StudyActivitySchedules"

        duplicated_schedules = db.cypher_query(
            """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)-[:HAS_STUDY_ACTIVITY_SCHEDULE]
                ->(study_activity_schedule:StudyActivitySchedule)
            WHERE NOT (study_activity_schedule)<-[:BEFORE]-()
            MATCH (study_visit:StudyVisit)-[:STUDY_VISIT_HAS_SCHEDULE]->(study_activity_schedule)
            WHERE NOT (study_visit)<-[:BEFORE]-()
            MATCH (study_activity_schedule)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(study_activity:StudyActivity)
            WHERE NOT (study_activity)<-[:BEFORE]-()
            WITH study_visit, study_activity, apoc.coll.sortNodes(collect(study_activity_schedule), 'uid') as duplicated_schedules
            WHERE size(duplicated_schedules) > 1
            RETURN duplicated_schedules
            """,
            params={"study_uid": study_uid},
        )
        assert (
            len(duplicated_schedules[0]) == 0
        ), f"Study {study_uid} contains duplicated StudyActivitySchedules"


def test_migrate_week_in_study(migration):
    study_duration_weeks_count = db.cypher_query("""
        MATCH (:StudyVisit)-[hsdw:HAS_STUDY_DURATION_WEEKS]->
        (:ConceptRoot:NumericValueRoot:SimpleConceptRoot:StudyDurationWeeksRoot:TemplateParameterTermRoot)-[:HAS_VERSION]->
        (:ConceptValue:NumericValue:SimpleConceptValue:StudyDurationWeeksValue:TemplateParameterTermValue)
        RETURN COUNT(DISTINCT hsdw)
        """)
    week_in_study_count = db.cypher_query("""
        MATCH (:StudyVisit)-[hwis:HAS_WEEK_IN_STUDY]->
        (:ConceptRoot:NumericValueRoot:SimpleConceptRoot:WeekInStudyRoot:TemplateParameterTermRoot)
        RETURN COUNT(DISTINCT hwis)
        """)
    assert (
        study_duration_weeks_count[0] == week_in_study_count[0]
    ), "Not all StudyVisit nodes that have a HAS_STUDY_DURATION_WEEKS relationship have a HAS_WEEK_IN_STUDY relationship"

    week_in_study_value_nodes = db.cypher_query("""
        MATCH (n:WeekInStudyValue)
        RETURN n.name, n.name_sentence_case
        """)[0]

    for node in week_in_study_value_nodes:
        assert node[0].startswith("Week "), f"{node[0]} doesn't start with Week"
        assert isinstance(int(node[0][4:]), int), f"{node[0][4:]} is not an integer"
        assert node[1].startswith("Week "), f"{node[0]} doesn't start with Week"
        assert isinstance(int(node[1][4:]), int), f"{node[0][4:]} is not an integer"


def test_migrate_soa_preferred_time_unit(migration):
    studies_without_soa_preferred_time_unit_count = db.cypher_query("""
        MATCH (sr:StudyRoot)-[:LATEST]->(sv:StudyValue)
        WHERE NOT (sv)-[:HAS_TIME_FIELD]->(:StudyTimeField {field_name: "soa_preferred_time_unit"})
        
        RETURN COUNT(sr)
        """)
    assert (
        studies_without_soa_preferred_time_unit_count[0][0][0] == 0
    ), "Some Studies are not connected to a StudyTimeField for soa_preferred_time_unit"

    studies_without_preferred_time_unit_count = db.cypher_query("""
        MATCH (sr:StudyRoot)-[:LATEST]->(sv:StudyValue)
        WHERE NOT (sv)-[:HAS_TIME_FIELD]->(:StudyTimeField {field_name: "preferred_time_unit"})

        RETURN COUNT(sr)
        """)
    assert (
        studies_without_preferred_time_unit_count[0][0][0] == 0
    ), "Some Studies are not connected to a StudyTimeField for preferred_time_unit"


def _migrate_study_activity_grouping_and_audit_trail_duplicates(migration, group_class):
    query = f"""
        MATCH (sa:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_{group_class.upper()}]->(sag:StudyActivity{group_class})-[:HAS_SELECTED_ACTIVITY_{group_class.upper()}]-(agv:Activity{group_class}Value)
        WHERE NOT (sag)<-[:AFTER]-(:Delete)
        WITH sa, agv, collect(sag) as sags WHERE size(sags) > 1
        WITH DISTINCT sa, agv
        RETURN COUNT(sa)
        """
    duplicated_groups = db.cypher_query(query)
    assert (
        duplicated_groups[0][0][0] == 0
    ), f"Some StudyActivity nodes have duplicated StudyActivity{group_class} nodes for a given Activity{group_class}Value"


def test_migrate_study_activity_grouping_and_audit_trail_duplicates_group(migration):
    _migrate_study_activity_grouping_and_audit_trail_duplicates(migration, "Group")


def test_migrate_study_activity_grouping_and_audit_trail_duplicates_subgroup(migration):
    _migrate_study_activity_grouping_and_audit_trail_duplicates(migration, "SubGroup")


def _migrate_study_activity_grouping_and_audit_trail_edit(migration, study_node):
    incomplete_edit_actions = db.cypher_query(f"""
        MATCH (sn:{study_node})<-[:BEFORE]-(edit:Edit)
        WHERE NOT (edit)-[:AFTER]->()
        RETURN COUNT(edit)
        """)
    assert (
        incomplete_edit_actions[0][0][0] == 0
    ), f"Some Edit StudyActions for {study_node} nodes do not have an AFTER relationship"


def test_migrate_study_activity_grouping_and_audit_trail_edit_group(migration):
    _migrate_study_activity_grouping_and_audit_trail_edit(
        migration, "StudyActivityGroup"
    )


def test_migrate_study_activity_grouping_and_audit_trail_edit_subgroup(migration):
    _migrate_study_activity_grouping_and_audit_trail_edit(
        migration, "StudyActivitySubGroup"
    )


def _migrate_study_activity_grouping_and_audit_trail_redundant_edits(
    migration, study_node
):
    incomplete_edit_actions = db.cypher_query(f"""
        MATCH (s:{study_node})-[:AFTER|BEFORE]-(study_action)
        WHERE (s)-[:AFTER]-(study_action) and (s)-[:BEFORE]-(study_action)
        RETURN COUNT(s)
        """)
    assert (
        incomplete_edit_actions[0][0][0] == 0
    ), f"Some StudyActions for {study_node} are redundant as their BEFORE and AFTER link to the same node"


def test_migrate_study_activity_grouping_and_audit_trail_redundant_edits_group(
    migration,
):
    _migrate_study_activity_grouping_and_audit_trail_redundant_edits(
        migration, "StudyActivityGroup"
    )


def test_migrate_study_activity_grouping_and_audit_trail_redundant_edits_subgroup(
    migration,
):
    _migrate_study_activity_grouping_and_audit_trail_redundant_edits(
        migration, "StudyActivitySubGroup"
    )


def test_migrate_nullify_unit_definition_name_sentence_case(migration):
    rs = db.cypher_query("""
        MATCH (uv:UnitDefinitionValue)
        WHERE uv.name_sentence_case IS NOT NULL
        RETURN COUNT(uv)
        """)
    assert (
        rs[0][0][0] == 0
    ), f"{rs[0][0][0]} UnitDefinitionValue.name_sentence_case are not null"

    rs = db.cypher_query("""
        MATCH (uv:UnitDefinitionValue)--(ur:UnitDefinitionRoot:TemplateParameterTermRoot)--(i:SyntaxInstanceValue)
        WHERE i.name CONTAINS uv.name_sentence_case
        RETURN COUNT(ur)
        """)
    assert (
        rs[0][0][0] == 0
    ), f"{rs[0][0][0]} SyntaxInstanceValue.name contains UnitDefinitionValue.name_sentence_case should contain UnitDefinitionValue.name instead"

    rs = db.cypher_query("""
        MATCH (uv:UnitDefinitionValue)--(ur:UnitDefinitionRoot:TemplateParameterTermRoot)--(i:SyntaxInstanceValue)
        WHERE i.name_plain CONTAINS uv.name_sentence_case
        RETURN COUNT(ur)
        """)
    assert (
        rs[0][0][0] == 0
    ), f"{rs[0][0][0]} SyntaxInstanceValue.name_plain contains UnitDefinitionValue.name_sentence_case should contain UnitDefinitionValue.name instead"


def test_migrate_missing_activity_item_class(migration):
    rs = db.cypher_query("""
        MATCH (ai:ActivityItem) WHERE NOT (ai)<-[:HAS_ACTIVITY_ITEM]-()
        RETURN COUNT(ai)
        """)
    assert (
        rs[0][0][0] == 0
    ), f"{rs[0][0][0]} ActivityItem nodes are missing a relationship to an ActivityItemClassRoot node"


def test_migrate_remove_invalid_activity_instances(migration):
    rs = db.cypher_query("""
        MATCH (aiv:ActivityInstanceValue) WHERE NOT (aiv)-[:HAS_ACTIVITY]->(:ActivityGrouping) 
        MATCH (aiv)<-[]-(air:ActivityInstanceRoot)-[:CONTAINS_CONCEPT]-(:Library {name: "Sponsor"})
        RETURN COUNT(DISTINCT aiv)
        """)
    assert (
        rs[0][0][0] == 0
    ), f"{rs[0][0][0]} ActivityInstanceValue nodes are missing a relationship to an ActivityGrouping node"
