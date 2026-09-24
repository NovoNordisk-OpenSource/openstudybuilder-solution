import os
import re

import pytest
from import_standards.src.scripts.utils import REPLACEMENTS

from migrations import migration_001
from migrations.utils.utils import (
    REGEX_SNAKE_CASE,
    api_get,
    execute_statements,
    get_db_connection,
    get_logger,
)
from tests import common

try:
    from tests.data.db_before_migration_001 import TEST_DATA
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
    migration_001.main()


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_activities(migration):
    logger.info("Verify activities")
    # Multiple outgoing IN_SUB_GROUP/IN_GROUP relations are no longer allowed:
    # - (n:ActivityValue)-[r:IN_SUB_GROUP]->(m:ActivitySubGroupValue)
    # - (n:ActivitySubGroupValue)-[r:IN_GROUP]->(m:ActivityGroupValue)
    #
    # After migration, only one of these outgoing relations should be left on each node.

    query_activities = """
        MATCH (n:ActivityValue)-[r:IN_SUB_GROUP]->(m:ActivitySubGroupValue)
        WITH n, count(m) as nbr_rels, collect(m) as ms, collect(r) as rels
        WHERE nbr_rels > 1
        RETURN *
        """
    query_groups = """
        MATCH (n:ActivitySubGroupValue)-[r:IN_GROUP]->(m:ActivityGroupValue)
        WITH n, count(m) as nbr_rels, collect(m) as ms, collect(r) as rels
        WHERE nbr_rels > 1
        RETURN *
        """
    result = db.cypher_query(query_activities)
    assert len(result[0]) == 0

    result = db.cypher_query(query_groups)
    assert len(result[0]) == 0

    # Call relevant GET /activities endpoints
    endpoints_to_check = [
        "/concepts/activities/activities",
        "/concepts/activities/activity-groups",
        "/concepts/activities/activity-sub-groups",
        "/concepts/activities/activity-instances",
    ]
    for endpoint in endpoints_to_check:
        api_get(endpoint)


def test_template_parameters(migration):
    logger.info("Verify template parameters")
    node_to_match = 'TemplateParameter {name: "StudyEndpoint"}'
    result = db.cypher_query(f"MATCH (n:{node_to_match}) return n")
    assert (
        len(result[0]) == 1
    ), f"Found {len(result[0])} `{node_to_match}` nodes. Expected: 1."


def test_study_criteria(migration):
    logger.info("Verify study criteria")
    result = db.cypher_query("MATCH (n:StudyCriteria) return n")
    for row in result[0]:
        node_properties: dict = row[0]._properties
        assert (
            "key_criteria" in node_properties.keys()
        ), f"StudyCriteria {{uid: {node_properties['uid']}}} node does not contain 'key_criteria' property"
        assert isinstance(node_properties["key_criteria"], bool)


def test_study_fields(migration):
    logger.info("Verify study fields")
    result, labels = db.cypher_query(
        """MATCH (study_root:StudyRoot)-[:LATEST]->(study_value:StudyValue)-[]->(study_field:StudyField)
        WHERE study_field:StudyArrayField OR study_field:StudyBooleanField OR
        (study_field:StudyTextField AND (study_field.value STARTS WITH "CTTerm_" OR study_field.value STARTS WITH "DictionaryTerm_"))
        RETURN study_root.uid as study_uid, study_field.field_name as field_name"""
    )
    unique_study_uids = []
    for study_uid, field_name in result:
        assert re.match(
            REGEX_SNAKE_CASE, field_name
        ), f"Value 'field_name: {field_name}' is not in snake case"
        study_field_types, labels = db.cypher_query(
            f"MATCH (study_field:StudyField)-[:HAS_TYPE|HAS_DICTIONARY_TYPE]->(type_node) WHERE study_field.field_name='{field_name}' return *"
        )
        # The traversal above should return StudyFields nodes connected to CTTermRoot/DictionaryTermRoot
        assert len(study_field_types) > 0
        study_field_types = study_field_types[0]

        # We check if none of the study_field or type_node is not None
        for study_field_type, label in zip(study_field_types, labels):
            assert (
                study_field_type is not None
            ), f"Returned None for the following label {label}"

        if study_uid not in unique_study_uids:
            unique_study_uids.append(study_uid)

    for study_uid in unique_study_uids:
        # Call relevant trial summary listing endpoint
        ts_listing_endpoint = f"/listings/studies/all/sdtm/ts/{study_uid}"
        listing = api_get(ts_listing_endpoint).json()
        assert (
            len(listing["items"]) > 0
        ), "The returned listing should contain items for the linked study fields"


def test_chars_in_uids(migration):
    logger.info("Verify CDISC term uids")
    bad_chars = [char[0] for char in REPLACEMENTS]
    # Check that no term uids contain reserved chars that cause trouble in URLs
    # bad_chars = [" ", "/", "&", "*", "+", "^", "=", "<", ">", "(", ")", "[", "]", "{", "}", "%", "?", "'", ";", ":", "$", "#", "!", "@", ","]
    for char in bad_chars:
        query_terms = """
        MATCH (n:CTTermRoot)<-[:CONTAINS_TERM]-(:Library {name: "CDISC"})
        WHERE n.uid CONTAINS $bad_char
        RETURN n
        """
        logger.info("Verify that no uid contains '%s'", char)
        result = db.cypher_query(query_terms, {"bad_char": char})
        assert len(result[0]) == 0

    term_uids = [
        # "C116242_mmol__per__min__per__kPa",
        "C67423_mmol__per__min__per__kPa__per__L",
        "C85722_mmol__per__min",
    ]
    for term_uid in term_uids:
        ct_term_endpoint = f"/ct/terms/{term_uid}/attributes"
        api_get(ct_term_endpoint).json()


def test_requested_library(migration):
    logger.info("Verify that Requested library exists")
    query = """
    MATCH (n:Library {name: "Requested"})
    RETURN n
    """
    result = db.cypher_query(query)
    assert len(result[0]) == 1

    lib_endpoint = "/libraries"
    libs = api_get(lib_endpoint).json()
    assert any(lib["name"] == "Requested" for lib in libs)


def test_null_flavor_codelist(migration):
    # Call the api to get the terms
    null_flavor_endpoint = (
        "/ct/terms?codelist_name=Null%20Flavor&page_number=1&page_size=0"
    )
    listing = api_get(null_flavor_endpoint).json()
    items = listing["items"]
    assert len(items) > 0, "The null flavor codelist should contain items"
    term_na = list(
        filter(lambda t: t["attributes"]["code_submission_value"] == "NA", items)
    )
    term_not_applicable = list(
        filter(
            lambda t: t["attributes"]["code_submission_value"] == "NOT APPLICABLE",
            items,
        )
    )
    term_qs = list(
        filter(
            lambda t: t["name"]["sponsor_preferred_name"] == "Questionnaire Domain",
            items,
        )
    )
    assert (
        len(term_na) > 0
    ), "The null flavor codelist must contain a term with submission value NA"
    assert (
        len(term_not_applicable) == 0
    ), "The null flavor codelist must not contain a term with submission value NOT APPLICABLE"
    assert (
        len(term_qs) == 0
    ), "The null flavor codelist must not contain a term with name Questionnaire Domain"


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_sponsor_codelists_extensible(migration):
    logger.info("Verify that all sponsor codelists are extensible")
    logger.debug("Verify that there is at least one sponsor codelist")
    query = """
    MATCH (clr:CTCodelistRoot)-[har:HAS_ATTRIBUTES_ROOT]-(ar)-[]-(av {extensible: true}), (clr)-[:CONTAINS_CODELIST]-(lib {name: "Sponsor"})
    RETURN av
    """
    result = db.cypher_query(query)
    assert len(result[0]) > 0

    logger.debug("Verify that there are no sponsor codelists that are not extensible")
    query = """
    MATCH (clr:CTCodelistRoot)-[har:HAS_ATTRIBUTES_ROOT]-(ar)-[]-(av {extensible: false}), (clr)-[:CONTAINS_CODELIST]-(lib {name: "Sponsor"})
    RETURN av
    """
    result = db.cypher_query(query)
    assert len(result[0]) == 0
