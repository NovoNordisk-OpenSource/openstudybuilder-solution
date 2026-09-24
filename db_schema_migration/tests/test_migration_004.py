import os

import pytest

from migrations import migration_004
from migrations.utils.utils import (
    api_get,
    execute_statements,
    get_db_connection,
    get_logger,
)
from tests import common

try:
    from tests.data.db_before_migration_004 import TEST_DATA
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
    migration_004.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_study_activity_item_root_value_pairs(migration):
    query = """
        MATCH (r:ActivityItemRoot)
        RETURN count(r)
    """
    result, _ = db.cypher_query(query)
    assert result[0][0] == 0, "Some ActivityItemRoot nodes still exist"

    query = """
        MATCH (v:ActivityItemValue)
        RETURN count(v)
    """
    result, _ = db.cypher_query(query)
    assert result[0][0] == 0, "Some ActivityItemValue nodes still exist"


def test_single_activity_item_per_class(migration):
    result = db.cypher_query("""
        MATCH (instval:ActivityInstanceValue)-[cai:CONTAINS_ACTIVITY_ITEM]->(aiv:ActivityItem)<-[hai:HAS_ACTIVITY_ITEM]-(aicr:ActivityItemClassRoot)
        WITH instval, aicr, collect(aiv) as items
        WHERE size(items) > 1
        RETURN instval
        """)

    assert (
        len(result[0]) == 0
    ), "Some ActivityInstances have multiple ActivityItems for a ActivityItemClass"


def test_study_activity_subgroup_and_group_selection_migration(migration):
    query = """
        MATCH (study_activity:StudyActivity)-[:HAS_SELECTED_ACTIVITY]->
              (activity_value:ActivityValue)
        WHERE NOT (activity_value)<-[:LATEST]-(:ActivityRoot)<-[:CONTAINS_CONCEPT]-(:Library {name: "Requested"})
              AND NOT (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(:StudyActivitySubGroup)
        RETURN study_activity"""
    result = db.cypher_query(query)
    assert (
        len(result[0]) == 0
    ), "Some StudyActivity doesn't have related StudyActivitySubgroup and StudyActivityGroup"


def test_study_soa_group_migration(migration):
    query = """
        MATCH (:StudyValue)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)
        WHERE NOT (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->()
        RETURN study_activity"""
    result = db.cypher_query(query)

    assert (
        len(result[0]) == 0
    ), "Some StudyActivity doesn't have related StudySoAGroup node"

    # GET all study-activities
    res = api_get("/study-activities")
    assert res.status_code == 200
    study_activities = res.json()["items"]

    for study_activity in study_activities:
        assert study_activity["study_soa_group"] is not None
        assert study_activity["study_soa_group"]["study_soa_group_uid"] is not None
        assert study_activity["study_soa_group"]["soa_group_term_uid"] is not None
        assert study_activity["study_soa_group"]["soa_group_name"] is not None


def test_study_relationships_removal_from_study_subgroup_group_and_soa_group(migration):
    query = """
        MATCH (study_activity_subgroup:StudyActivitySubGroup)
        WHERE (study_activity_subgroup)-[:STUDY_ACTIVITY_SUBGROUP_HAS_STUDY_ACTIVITY_GROUP]->(:StudyActivityGroup)
        RETURN study_activity_subgroup"""
    result = db.cypher_query(query)

    assert (
        len(result[0]) == 0
    ), "Some StudyActivitySubGroup has a STUDY_ACTIVITY_SUBGROUP_HAS_STUDY_ACTIVITY_GROUP relationship to StudyActivityGroup"

    query = """
        MATCH (study_activity_subgroup:StudyActivitySubGroup)
        WHERE (study_activity_subgroup)<-[:HAS_STUDY_ACTIVITY_SUBGROUP]-(:StudyValue)
        RETURN study_activity_subgroup"""
    result = db.cypher_query(query)

    assert (
        len(result[0]) == 0
    ), "Some StudyActivitySubGroup has a HAS_STUDY_ACTIVITY_SUBGROUP relationship to StudyValue"

    query = """
        MATCH (study_activity_subgroup:StudySelection:StudyActivitySubGroup)
        WHERE NOT study_activity_subgroup:StudySelectionMetadata
        RETURN study_activity_subgroup"""
    result = db.cypher_query(query)

    assert (
        len(result[0]) == 0
    ), "Some StudyActivitySubGroup has old StudySelection label"

    query = """
        MATCH (study_activity_group:StudyActivityGroup)
        WHERE (study_activity_group)<-[:HAS_STUDY_ACTIVITY_GROUP]-(:StudyValue)
        RETURN study_activity_group"""
    result = db.cypher_query(query)

    assert (
        len(result[0]) == 0
    ), "Some StudyActivityGroup has a HAS_STUDY_ACTIVITY_GROUP relationship to StudyValue"

    query = """
        MATCH (study_activity_group:StudySelection:StudyActivityGroup)
        WHERE NOT study_activity_group:StudySelectionMetadata
        RETURN study_activity_group"""
    result = db.cypher_query(query)

    assert len(result[0]) == 0, "Some StudyActivityGroup has old StudySelection label"

    query = """
        MATCH (study_soa_group:StudySoAGroup)
        WHERE (study_soa_group)<-[:HAS_STUDY_SOA_GROUP]-(:StudyValue)
        RETURN study_soa_group"""
    result = db.cypher_query(query)

    assert (
        len(result[0]) == 0
    ), "Some StudySoAGroup has a HAS_STUDY_SOA_GROUP relationship to StudyValue"

    query = """
        MATCH (study_soa_group:StudySelection:StudySoAGroup)
        WHERE NOT study_soa_group:StudySelectionMetadata
        RETURN study_soa_group"""
    result = db.cypher_query(query)

    assert len(result[0]) == 0, "Some StudySoAGroup has old StudySelection label"

    query = """
        MATCH (study_activity:StudyActivity)-[:HAS_SELECTED_ACTIVITY]->
            (:ActivityValue)<-[:HAS_VERSION]-(:ActivityRoot)<-[:CONTAINS_CONCEPT]-(library)
        WHERE library.name <> "Requested" AND NOT (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(:StudyActivityGroup)
        RETURN study_activity"""
    result = db.cypher_query(query)

    assert (
        len(result[0]) == 0
    ), "Some StudyActivity does not have a relationship to StudyActivityGroup"

    # GET all study-activities
    res = api_get("/study-activities")
    assert res.status_code == 200
    study_activities = res.json()["items"]

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


def test_syntax_sequence_id_refinement_and_renumbering(migration):
    logger.info(
        "Verify that all SyntaxTemplateRoot and SyntaxPreInstanceRoot have a sequence_id"
    )
    result = db.cypher_query("""
            MATCH (n)
            WHERE (n:SyntaxTemplateRoot OR n:SyntaxPreInstanceRoot) AND n.sequence_id=null
            RETURN n
        """)
    assert not result[0]

    logger.info(
        "Verify that sequence_id of all User Defined SyntaxTemplateRoot have 'U-' prefixed"
    )
    result = db.cypher_query("""
            MATCH (l:Library)-->(n:SyntaxTemplateRoot)
            RETURN n.sequence_id, l.name="User Defined"
        """)
    assert all(seq[0].startswith("U-") for seq in result[0] if seq[1])
    assert all(not seq[0].startswith("U-") for seq in result[0] if not seq[1])

    logger.info(
        "Verify that sequence_id of all SyntaxPreInstanceRoot have prefixed the sequence_id of their SyntaxTemplateRoot"
    )
    result = db.cypher_query("""
            MATCH (n:SyntaxTemplateRoot)--(p:SyntaxPreInstanceRoot)
            RETURN n.sequence_id, p.sequence_id
        """)
    assert all(seq[1].startswith(seq[0]) for seq in result[0])
