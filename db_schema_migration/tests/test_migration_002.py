import asyncio
import os
import re

import pytest

from migrations import migration_002
from migrations.utils.utils import (
    api_get,
    execute_statements,
    get_db_connection,
    get_logger,
)
from tests import common

try:
    from tests.data.db_before_migration_002 import TEST_DATA
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
    loop = asyncio.get_event_loop()
    loop.run_until_complete(migration_002.main())


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_syntax_templates_and_instances(migration):
    logger.info("Verify syntax templates & instances")

    result = db.cypher_query("MATCH (t:TemplateParameterValueRoot) RETURN t")
    assert len(result[0]) == 0
    result = db.cypher_query("MATCH (t:TemplateParameterValue) RETURN t")
    assert len(result[0]) == 0
    result = db.cypher_query("MATCH (a:ActivityDescriptionRoot) RETURN a")
    assert len(result[0]) == 0
    result = db.cypher_query("MATCH (a:ActivityDescriptionValue) RETURN a")
    assert len(result[0]) == 0
    result = db.cypher_query(
        "MATCH (:TemplateParameter)-[rel:HAS_VALUE]->() return rel"
    )
    assert len(result[0]) == 0
    result = db.cypher_query(
        "MATCH ()-[rel:HAS_SUB_CATEGORY]->(:CTTermRoot) return rel"
    )
    assert len(result[0]) == 0
    result = db.cypher_query(
        "MATCH (:SyntaxTemplateRoot)-[rel:HAS_DISEASE_DISORDER]->(:DictionaryTermRoot) return rel"
    )
    assert len(result[0]) == 0
    result = db.cypher_query(
        "MATCH ()-[rel:OV_USES_VALUE|EV_USES_VALUE|TV_USES_VALUE|CT_USES_VALUE|AT_USES_VALUE]->() return rel"
    )
    assert len(result[0]) == 0
    result = db.cypher_query(
        "MATCH ()-[rel:OT_USES_PARAMETER|ET_USES_PARAMETER|TT_USES_PARAMETER|CT_USES_PARAMETER|AT_USES_PARAMETER]->() return rel"
    )
    assert len(result[0]) == 0
    result = db.cypher_query(
        "MATCH (:Library)-[rel:CONTAINS_CRITERIA]->(:CriteriaRoot) return rel"
    )
    assert len(result[0]) == 0
    result = db.cypher_query(
        "MATCH (:Library)-[rel:CONTAINS_ENDPOINT]->(:EndpointRoot) return rel"
    )
    assert len(result[0]) == 0
    result = db.cypher_query(
        "MATCH (:Library)-[rel:CONTAINS_OBJECTIVE]->(:ObjectiveRoot) return rel"
    )
    assert len(result[0]) == 0
    result = db.cypher_query(
        "MATCH (:Library)-[rel:CONTAINS_TIMEFRAME]->(:TimeframeRoot) return rel"
    )
    assert len(result[0]) == 0
    result = db.cypher_query(
        "MATCH (:Library)-[rel:CONTAINS_ACTIVITY_DESCRIPTION_TEMPLATE]->() return rel"
    )
    assert len(result[0]) == 0
    result = db.cypher_query(
        "MATCH (:Library)-[rel:CONTAINS_CRITERIA_TEMPLATE]->(:CriteriaTemplateRoot) return rel"
    )
    assert len(result[0]) == 0
    result = db.cypher_query(
        "MATCH (:Library)-[rel:CONTAINS_ENDPOINT_TEMPLATE]->(:EndpointTemplateRoot) return rel"
    )
    assert len(result[0]) == 0
    result = db.cypher_query(
        "MATCH (:Library)-[rel:CONTAINS_OBJECTIVE_TEMPLATE]->(:ObjectiveTemplateRoot) return rel"
    )
    assert len(result[0]) == 0
    result = db.cypher_query(
        "MATCH (:Library)-[rel:CONTAINS_TIMEFRAME_TEMPLATE]->(:TimeframeTemplateRoot) return rel"
    )
    assert len(result[0]) == 0

    # Call endpoints
    endpoints_to_check = [
        "/activity-instruction-templates",
        "/criteria-templates",
        "/endpoint-templates",
        "/objective-templates",
        "/timeframe-templates",
        "/criteria",
        "/endpoints",
        "/objectives",
        "/timeframes",
        "/study-criteria",
    ]
    for endpoint in endpoints_to_check:
        api_get(endpoint)


def test_default_study_preferred_time_unit(migration):
    result, _ = db.cypher_query(
        "MATCH (study_root:StudyRoot) RETURN study_root.uid as study_uid"
    )
    assert len(result[0]) > 0
    for study_uid in result[0]:
        logger.info(
            "Verify that Study '%s' has a default preferred time unit set to 'day' unit definition",
            study_uid,
        )

        pref_time_unit_endpoint = f"/studies/{study_uid}/time-units"
        pref_time_unit = api_get(pref_time_unit_endpoint).json()
        assert pref_time_unit["study_uid"] == study_uid
        assert pref_time_unit["time_unit_name"] == "day"


def test_item_versioning(migration):
    logger.info("Verify item versioning relationships")

    # All these queries may return many thousands of results.
    # Applying a limit to avoid drowning!

    # Find LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED that misses a matching HAS_VERSION
    query = """
        MATCH (root)-[lat:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED]->(value)
        WHERE none(label in labels(root) WHERE label IN ["ClassVariableRoot", "DatasetClassRoot", "DatasetRoot", "DatasetScenarioRoot", "DatasetVariableRoot", "StudyRoot"])
            AND lat.version IS NOT NULL AND lat.status IS NOT NULL
            AND NOT (root)-[:HAS_VERSION {version: lat.version, status: lat.status}]->(value)
        RETURN * LIMIT 100
    """
    result = db.cypher_query(query)
    assert (
        len(result[0]) == 0
    ), "Some versioned items are missing a HAS_VERSION relationship"

    # Find duplicated HAS_VERSION
    query = """
        MATCH (root)-[hv1:HAS_VERSION]->(value)
        WHERE none(label in labels(root) WHERE label IN ["ClassVariableRoot", "DatasetClassRoot", "DatasetRoot", "DatasetScenarioRoot", "DatasetVariableRoot", "StudyRoot"])
        MATCH (root)-[hv2:HAS_VERSION {version: hv1.version, start_date: hv1.start_date}]->(value)
        WHERE hv2.end_date < hv1.end_date OR (hv2.end_date IS NULL AND hv1.end_date IS NOT NULL)
        RETURN * LIMIT 100
    """
    result = db.cypher_query(query)
    assert (
        len(result[0]) == 0
    ), "Some versioned items have duplicated HAS_VERSION relationships"

    # Find LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED that has properties
    query = """
        MATCH (root)-[lat:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED]->(value)
        WHERE none(label in labels(root) WHERE label IN ["ClassVariableRoot", "DatasetClassRoot", "DatasetRoot", "DatasetScenarioRoot", "DatasetVariableRoot", "StudyRoot"])
            AND size(keys(properties(lat))) > 0
        RETURN * LIMIT 100
    """
    result = db.cypher_query(query)
    assert (
        len(result[0]) == 0
    ), "Some LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED relationships have unwanted properties"

    # This is a sponsor term. Limit check to the first two versions in case the db contains more
    ct_term_history_ep = "/ct/terms/CTTerm_000006/attributes/versions"
    items = api_get(ct_term_history_ep).json()
    assert (
        len(items) > 1
    ), "The term history should contain at least 2 items for CTTerm_000006"
    assert items[-2]["version"] == "1.0", "The second version should be 1.0"
    assert items[-2]["status"] == "Final", "The second version should be Final"
    assert items[-1]["version"] == "0.1", "The first version should be 0.1"
    assert items[-1]["status"] == "Draft", "The first version should be Draft"

    # This term comes from CDISC, only Final versions should exist
    ct_term_history_ep = "/ct/terms/C98779_RUN-IN/attributes/versions"
    items = api_get(ct_term_history_ep).json()
    assert (
        len(items) > 0
    ), "The term history should contain at least one item for C98779_RUN-IN"
    for idx, item in enumerate(reversed(items)):
        assert (
            item["version"] == f"{idx+1}.0"
        ), f"History item {idx+1} must have version {idx+1}.0"
        assert item["status"] == "Final", "All versions should be Final"


def test_syntax_sequence_id(migration):
    reg_pattern = "[a-z_-]|(?<=_)[0]*(?=[1-9])"
    logger.info("Verify sequence_id of all Syntax Templates except Criteria Templates")
    result = db.cypher_query("""MATCH (t:SyntaxTemplateRoot)
        WHERE NOT t:CriteriaTemplateRoot
        RETURN t.uid as uid, t.sequence_id as seq_id""")
    for uid, seq_id in result[0]:
        assert seq_id == re.sub(reg_pattern, "", uid)

    logger.info("Verify sequence_id of Criteria Templates")
    result = db.cypher_query("""MATCH (t:CriteriaTemplateRoot)
        MATCH (t)-[:HAS_TYPE]->(:CTTermRoot)-->(:CTTermNameRoot)-[:LATEST]->(ctnv:CTTermNameValue)
        WITH t, apoc.text.replace(t.uid, '[^0-9]', '') as uid_number,
        "Criteria" + apoc.text.replace(ctnv.name, ' |Criteria|CRITERIA|criteria', '') + "Template" as special_abbr
        RETURN special_abbr + "_" + uid_number as uid, t.sequence_id as seq_id""")
    for uid, seq_id in result[0]:
        assert seq_id == re.sub(reg_pattern, "", uid)


def test_activity_instance_classes(migration):
    query = """
        MATCH (activity_instance_root:ActivityInstanceRoot)-[]->(activity_instance_value:ActivityInstanceValue)
        WHERE any(label in labels(activity_instance_root) WHERE label IN ["EventRoot", "TextualFindingRoot", "CategoricFindingRoot", "NumericFindingRoot"])
        RETURN *
    """
    result = db.cypher_query(query)
    assert len(result[0]) == 0, "Some activity instance have old labels"

    activity_instance_endpoint = "/concepts/activities/activity-instances"
    res = api_get(activity_instance_endpoint)
    assert res.status_code == 200

    activity_instances = res.json()
    for activity_instance in activity_instances["items"]:
        assert activity_instance["activity_instance_class"]["name"] in [
            "NumericFinding",
            "CategoricFinding",
            "TextualFinding",
            "Event",
        ]

    query = """
        MATCH (activity_instance_root:ActivityInstanceRoot)-[]->(activity_instance_value:ActivityInstanceValue)
        -[:DEFINED_BY]->(activity_definition:ActivityDefinition)
        RETURN *
    """
    result = db.cypher_query(query)
    assert (
        len(result[0]) == 0
    ), "Some activity instance have extra :DEFINED_BY relationship"


def test_activity_instances_have_activity(migration):
    query = """
        MATCH (n:ActivityInstanceValue)
        WHERE NOT (n)-[:IN_HIERARCHY]->(:ActivityValue)
        RETURN n
    """
    result = db.cypher_query(query)
    assert len(result[0]) == 0, "Some activity instances lack an activity"


def test_odm_template_renaming(migration):
    result = db.cypher_query("MATCH (n:OdmTemplateRoot) RETURN n")
    assert len(result[0]) == 0
    result = db.cypher_query("MATCH (n:OdmTemplateValue) RETURN n")
    assert len(result[0]) == 0

    result = db.cypher_query(
        "MATCH (n:OdmStudyEventValue) WHERE n.display_in_tree IS NOT NULL RETURN n"
    )
    assert len(result[0]) > 0
