import os
import re

import pytest

from migrations import migration_003
from migrations.utils.utils import (
    api_get,
    execute_statements,
    get_db_connection,
    get_logger,
)
from tests import common

try:
    from tests.data.db_before_migration_003 import TEST_DATA
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
    migration_003.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_study_selection_labels(migration):
    query = """
        MATCH (n)
        WHERE n:StudyActivitySchedule OR n:StudyActivityInstruction OR n:StudyDesignCell OR n:StudyEpoch OR n:StudyDiseaseMilestone
        WITH n
        WHERE (n:StudyActivitySchedule and not n:StudySelection) OR
        (n:StudyActivityInstruction and not n:StudySelection) OR
        (n:StudyDesignCell and not n:StudySelection) OR
        (n:OrderedStudySelection)
        RETURN n 
    """

    result = db.cypher_query(query)
    assert len(result[0]) == 0, "Some study selections have old labels"

    params = {"has_study_activity": True}
    study_endpoint = "/studies"
    studies = api_get(study_endpoint, params, check_ok_status=False).json()["items"]
    study_uid = studies[0]["uid"] if studies else None
    if study_uid:
        logger.info("Found a Study with StudyActivity selection")
        epoch_endpoint = f"/studies/{study_uid}/study-epochs"
        api_get(epoch_endpoint)
        design_cells_endpoint = f"/studies/{study_uid}/study-design-cells"
        api_get(design_cells_endpoint)
        disease_milestone_endpoint = f"/studies/{study_uid}/study-disease-milestones"
        api_get(disease_milestone_endpoint)
        activity_schedule_endpoint = f"/studies/{study_uid}/study-activity-schedules"
        api_get(activity_schedule_endpoint)
        activity_instruction_endpoint = (
            f"/studies/{study_uid}/study-activity-instructions"
        )
        api_get(activity_instruction_endpoint)


def test_study_selection_deletion_convention(migration):
    query = """
        MATCH (del:Delete)-[ss_del]-(ss:StudySelection)
        WHERE NOT ss:StudyRoot
        WITH del,collect(ss)as ss_collected , COUNT(DISTINCT ss) AS count_ss_del
        WHERE count_ss_del<2
        RETURN *
    """
    result = db.cypher_query(query)
    assert len(result[0]) == 0, "There's still a wrong deleted StudySelection"

    params = {"has_study_activity": True}
    study_endpoint = "/studies"
    studies = api_get(study_endpoint, params, check_ok_status=False).json()["items"]
    study_uid = studies[0]["uid"] if studies else None
    if study_uid:
        logger.info("Found a Study with StudyActivity selection")
        epoch_endpoint = f"/studies/{study_uid}/study-epochs"
        api_get(epoch_endpoint)
        visit_endpoint = f"/studies/{study_uid}/study-visits"
        api_get(visit_endpoint)


def test_study_selection_drop_relationships(migration):
    params = {"has_study_activity": True}
    study_endpoint = "/studies"
    studies = api_get(study_endpoint, params, check_ok_status=False).json()["items"]
    study_uid = studies[0]["uid"] if studies else None
    if study_uid:
        logger.info("Found a Study with StudyActivity selection")
        activity_schedule_endpoint = f"/studies/{study_uid}/study-activity-schedules"
        api_get(activity_schedule_endpoint)

    query = """
        MATCH (ss1:StudySelection)-[:AFTER]-(ss1_after_saction:StudyAction)
        OPTIONAL MATCH (ss1)<-[:BEFORE]-(ss1_before_saction:StudyAction)
        WITH ss1, ss1_after_saction,
        CASE 
            WHEN ss1_before_saction IS NULL AND NOT ss1_after_saction:Delete then datetime({epochMillis: apoc.date.currentTimestamp()})
            WHEN ss1_before_saction IS NULL AND ss1_after_saction:Delete then ss1_after_saction.date
            ELSE ss1_before_saction.date
        END AS ss1_before_date
        MATCH (ss1)-[ss1_ss2]-(ss2:StudySelection)<-[:BEFORE]-(ss2_saction:StudyAction)-[:AFTER]->(ss2_new_version:StudySelection)
            WHERE 
                NOT EXISTS((ss2_new_version)--(ss1)) AND 
                (ss2_saction.date<ss1_before_date AND ss2_saction.date>ss1_after_saction.date)
        WITH ss1, ss1_ss2, ss2, ss2_saction
        WHERE 
        TYPE(ss1_ss2) IN [
            "STUDY_EPOCH_HAS_STUDY_VISIT",
            "STUDY_VISIT_HAS_SCHEDULE",
            "STUDY_EPOCH_HAS_DESIGN_CELL",
            "STUDY_ACTIVITY_HAS_SCHEDULE", 
            "STUDY_ACTIVITY_HAS_INSTRUCTION",
            "STUDY_ELEMENT_HAS_DESIGN_CELL",
            "STUDY_ARM_HAS_BRANCH_ARM"
        ]
        RETURN ss1, ss1_ss2, ss2, ss2_saction
    """
    result = db.cypher_query(query)
    assert len(result[0]) == 0, "There's still a dropped StudySelections"


def test_study_activity_schedule_cascade_deletion(migration):
    params = {"has_study_activity": True}
    study_endpoint = "/studies"
    studies = api_get(study_endpoint, params, check_ok_status=False).json()["items"]
    study_uid = studies[0]["uid"] if studies else None
    if study_uid:
        logger.info("Found a Study with StudyActivity selection")
        activity_schedule_endpoint = f"/studies/{study_uid}/study-activity-schedules"
        api_get(activity_schedule_endpoint)

    query = """
        Match (sr:StudyRoot)--(:StudyValue)--(ss1:StudySelection)--(ss2:StudySelection)
        WHERE NOT EXISTS((ss2)--(:StudyValue)) AND 
            EXISTS ((ss2)-[:AFTER]-(:Delete)) AND
            ((ss1:StudyActivitySchedule AND ss2:StudyVisit) OR 
            (ss1:StudyActivitySchedule AND ss2:StudyActivity))
        RETURN ss1, ss2
    """
    result = db.cypher_query(query)
    assert len(result[0]) == 0, "There's still a not cascade deleted StudySelections"


def test_study_selection_switch_relationships(migration):
    params = {"has_study_activity_instruction": True}
    study_endpoint = "/studies"
    studies = api_get(study_endpoint, params, check_ok_status=False).json()["items"]
    study_uid = studies[0]["uid"] if studies else None
    if study_uid:
        logger.info("Found a Study with StudyActivity selection")
        activity_schedule_endpoint = f"/studies/{study_uid}/study-activity-schedules"
        api_get(activity_schedule_endpoint)

    query = """
        MATCH (ss1:StudySelection)<-[:AFTER]-(ss1_after_saction:StudyAction)
        OPTIONAL MATCH (ss1)<-[:BEFORE]-(ss1_before_saction:StudyAction)
        WITH ss1, ss1_after_saction,
        CASE 
            WHEN ss1_before_saction IS NULL AND NOT ss1_after_saction:Delete then datetime({epochMillis: apoc.date.currentTimestamp()})
            WHEN ss1_before_saction IS NULL AND ss1_after_saction:Delete then ss1_after_saction.date
            ELSE ss1_before_saction.date
        END AS ss1_before_date
        MATCH (ss1)-[ss1_ss2]-(ss2:StudySelection)<-[:AFTER]-(ss2_saction:StudyAction)-[:BEFORE]->(ss2_old_version:StudySelection)
            WHERE 
                NOT EXISTS((ss2_old_version)--(ss1)) AND 
                (ss2_saction.date<ss1_before_date AND ss2_saction.date>ss1_after_saction.date)
        WITH ss1, ss1_ss2, ss2, ss2_saction
        WHERE 
        TYPE(ss1_ss2) IN [
            "STUDY_EPOCH_HAS_STUDY_VISIT",
            "STUDY_VISIT_HAS_SCHEDULE",
            "STUDY_EPOCH_HAS_DESIGN_CELL",
            "STUDY_ACTIVITY_HAS_SCHEDULE", 
            "STUDY_ACTIVITY_HAS_INSTRUCTION",
            "STUDY_ELEMENT_HAS_DESIGN_CELL",
            "STUDY_ARM_HAS_BRANCH_ARM"
        ]
        RETURN ss1, ss1_ss2, ss2, ss2_saction
    """
    result = db.cypher_query(query)
    assert len(result[0]) == 0, "There's still switched relationships"


def test_activity_groupings(migration):
    query = """
        MATCH (activity_instance_value:ActivityInstanceValue)-[:IN_HIERARCHY]->(activity_value:ActivityValue)
        RETURN *
    """
    result = db.cypher_query(query)
    assert len(result[0]) == 0, "Some ActivityInstances have old hierarchies"

    query = """
        MATCH (activity_value:ActivityValue)-[:IN_SUB_GROUP]->(activity_subgroup:ActivitySubGroupValue)
        RETURN *
    """
    result = db.cypher_query(query)
    assert len(result[0]) == 0, "Some Activities have old IN_SUB_GROUP relationship"

    query = """
        MATCH (activity_subgroup_value:ActivitySubGroupValue)-[:IN_GROUP]->(activity_group:ActivityGroupValue)
        RETURN *
    """
    result = db.cypher_query(query)
    assert len(result[0]) == 0, "Some ActivitySubGroups have old IN_GROUP relationship"

    query = """
        MATCH (activity_valid_group:ActivityValidGroup)
        WITH  size([(activity_valid_group)-[:IN_GROUP]->() | activity_valid_group.uid]) as rels
        WHERE rels > 1 OR rels = 0
        RETURN *"""
    result = db.cypher_query(query)
    assert (
        len(result[0]) == 0
    ), "Some ActivityValidGroup has 0 ActivityGroups or links to more than 1 ActivityGroup"

    query = """
        MATCH (activity_valid_group:ActivityValidGroup)
        WITH  size([(activity_valid_group)<-[:HAS_GROUP]-() | activity_valid_group.uid]) as rels
        WHERE rels > 1 OR rels = 0
        RETURN *"""
    result = db.cypher_query(query)
    assert (
        len(result[0]) == 0
    ), "Some ActivityValidGroup has 0 ActivitySubGroups or links to more than 1 ActivitySubGroup"

    query = """
        MATCH (activity_grouping:ActivityGrouping)
        WITH  size([(activity_grouping)-[:IN_SUBGROUP]->() | activity_grouping.uid]) as rels
        WHERE rels = 0
        RETURN *"""
    result = db.cypher_query(query)
    assert len(result[0]) == 0, "Some ActivityGrouping has 0 ActivityValidGroups"

    query = """
        MATCH (activity_grouping:ActivityGrouping)
        WITH  size([(activity_grouping)<-[:HAS_GROUPING]-() | activity_grouping.uid]) as rels
        WHERE rels > 1 OR rels = 0
        RETURN *"""
    result = db.cypher_query(query)
    assert (
        len(result[0]) == 0
    ), "Some ActivityGrouping has 0 Activities or links to more than 1 Activity"

    # ActivityInstances
    res = api_get("/concepts/activities/activity-instances")
    assert res.status_code == 200
    activity_instances = res.json()
    for activity_instance in activity_instances["items"]:
        assert activity_instance["activity_groupings"]

    # Activities
    res = api_get("/concepts/activities/activities")
    assert res.status_code == 200
    activities = res.json()
    for activity in activities["items"]:
        if activity["library_name"] != "Requested":
            assert activity["activity_groupings"]

    # ActivitySubGroups
    res = api_get("/concepts/activities/activity-sub-groups")
    assert res.status_code == 200
    activity_subgroups = res.json()
    for activity_subgroup in activity_subgroups["items"]:
        assert activity_subgroup["activity_groups"]
    assert len(result[0]) == 0, "There's still switched relationships"


def test_syntax_sequence_id_refinement(
    migration,
):
    logger.info("Verify that no sequence_id contains T of Template before the number")
    result = db.cypher_query("MATCH (n:SyntaxTemplateRoot) RETURN n.sequence_id")
    for seq_id in result[0]:
        assert not re.search(
            "(?<=[A-Z])T(?=\\d)", seq_id[0]
        ), f"Sequence id ({seq_id[0]}) contains T of Template before the number"

    logger.info(
        "Verify that sequence_id of CriteriaTemplateRoot is sequential within the criteria template type"
    )
    result = db.cypher_query("MATCH (n:CriteriaTemplateRoot) RETURN n.sequence_id")
    criteria_templates: dict[str, list[str]] = {}
    for seq_id in result[0]:
        prefix = re.match("[a-zA-Z]*", seq_id[0]).group()
        criteria_templates.setdefault(prefix, []).append(seq_id[0])

    for prefix, seq_uids in criteria_templates.items():
        seq_uids.sort(key=lambda x, p=prefix: int(x.split(p)[1]))

        for idx, seq_id in enumerate(seq_uids, 1):
            assert f"{prefix}{idx}" == seq_id

    logger.info(
        "Verify that sequence_id of CriteriaPreInstanceRoot is sequential within the parent template"
    )
    result = db.cypher_query(
        "MATCH (n:CriteriaPreInstanceRoot)-[:CREATED_FROM]->(t:SyntaxTemplateRoot) RETURN n.sequence_id, t.uid"
    )
    criteria_pre_instances: dict[str, list[str]] = {}
    for seq_id, t_uid in result[0]:
        criteria_pre_instances.setdefault(t_uid, []).append(seq_id)

    for t_uid, seq_uids in criteria_pre_instances.items():
        seq_uids.sort(key=lambda x: int(x.split("P")[1]))

        for idx, seq_id in enumerate(seq_uids, 1):
            prefix = re.match("[a-zA-Z]*\\d*P", seq_id).group()
            assert f"{prefix}{idx}" == seq_id


def test_study_activity_subgroup_and_group_selection_migration(migration):
    query = """
        MATCH (:StudyValue)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)
        WHERE NOT head([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue)
                <-[:HAS_VERSION]-(activity_root)<-[:CONTAINS_CONCEPT]-(library) | library.name]) = "Requested"
        WITH size([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->()-[:STUDY_ACTIVITY_SUBGROUP_HAS_STUDY_ACTIVITY_GROUP]->() 
            | study_activity.uid]) as selections
        WHERE selections = 0
        RETURN *"""
    result = db.cypher_query(query)
    assert (
        len(result[0]) == 0
    ), "Some StudyActivity doesn't have related StudyActivitySubgroup and StudyActivityGroup"

    # GET all study-activities
    res = api_get("/study-activities")
    assert res.status_code == 200
    study_activities = res.json()["items"]
    assert len(study_activities) > 0

    for study_activity in study_activities:
        # ActivityPlaceholder won't have any groups assigned
        if study_activity["activity"]["activity_groupings"]:
            assert study_activity["study_activity_subgroup"] is not None
            assert (
                study_activity["study_activity_subgroup"]["study_activity_subgroup_uid"]
                is not None
            )
            assert (
                study_activity["study_activity_subgroup"]["activity_subgroup_uid"]
                is not None
            )
            assert study_activity["study_activity_group"] is not None
            assert (
                study_activity["study_activity_group"]["study_activity_group_uid"]
                is not None
            )
            assert (
                study_activity["study_activity_group"]["activity_group_uid"] is not None
            )


def test_simple_concept_migration(migration):
    logger.info(
        "Verify that a single SimpleConceptValue is not linked with many SimpleConceptRoots"
    )
    query = """
    MATCH (n:SimpleConceptRoot)-[:HAS_VERSION]->(m:SimpleConceptValue)
    WITH m, collect(n) as ns
    WHERE size(ns) > 1
    return *"""
    result = db.cypher_query(query)
    assert (
        len(result[0]) == 0
    ), "Some SimpleConceptValue is assigned to multiple SimpleConceptRoots"

    query = """
        MATCH (visit_name_root:VisitNameRoot)
        RETURN visit_name_root"""
    result = db.cypher_query(query)
    amount_of_visit_names = len(result[0])

    # GET all visit-names
    res = api_get("/concepts/visit-names", params={"page_size": 0})
    assert res.status_code == 200
    visit_names = res.json()["items"]
    if amount_of_visit_names > 0:
        assert len(visit_names) > 0

    visit_names = [visit_name["name"] for visit_name in visit_names]
    assert len(visit_names) == len(
        set(visit_names)
    ), "There exists a duplicated Visit name"
