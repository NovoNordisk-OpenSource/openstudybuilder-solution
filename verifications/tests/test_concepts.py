"""
This modules verifies that database nodes/relations look as expected.

Each test should execute a CYPHER query that returns one row with these columns:
 - check_id
 - check_description
 - noncompliant_entity_cnt
 - noncompliant_labels
 - noncompliant_node_ids

Result of each query is appended to `db_checks_results.csv` file.

"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
import os

from pytest_bdd import given, parsers, scenarios, then

from utils.utils import (
    REPORT_FILE_PATH,
    build_root_summary_return_statement,
    execute_query_and_append_result_to_file,
    get_db_connection,
    get_excluded_node_ids,
    get_gherkin_tags,
    get_logger,
)

scenarios("library/concepts.feature")

db = get_db_connection()
logger = get_logger(os.path.basename(__file__))


@given(parsers.parse("the library contains objects of type {object_type}"))
def object_type_exist(object_type):
    query = f"""
        MATCH (root:{object_type}Root)
        RETURN count(root)
    """
    response, _ = db.cypher_query(query)
    assert response[0][0] > 0


@then(
    parsers.parse(
        "there are no objects of type {object_type} with duplicated value of {name_property}"
    )
)
def no_duplicated_names(request, prepare_report_file, object_type, name_property):
    """DB: No duplicated names for given object type"""

    check_id = f"no_duplicated_{name_property}_in_{object_type}s"
    check_description = f"No duplicated {name_property} in {object_type} nodes"
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (lib1:Library)-[:CONTAINS_CONCEPT]->(root1:{object_type}Root)-[hv1:HAS_VERSION]->(value1)
        WHERE hv1.end_date IS NULL AND hv1.status IN ["Draft", "Final"]
        WITH root1, value1, lib1
        MATCH (lib2:Library)-[:CONTAINS_CONCEPT]->(root2:{object_type}Root)-[hv2:HAS_VERSION]->(value2)
            WHERE 
                root1<>root2
                AND hv2.end_date IS NULL AND hv2.status IN ["Draft", "Final"]
                AND value1.{name_property} IS NOT NULL
                AND value1.{name_property} = value2.{name_property}
                AND lib1.name = lib2.name
        {build_root_summary_return_statement('root1')}
    """
    result = execute_query_and_append_result_to_file(
        query,
        REPORT_FILE_PATH,
        check_id,
        check_description,
        tags=tags,
        excluded_node_ids=excluded_node_ids,
    )
    cnt = result["noncompliant_entity_cnt"]
    assert (
        cnt == 0
    ), f"Number of {object_type} nodes with duplicated {name_property}: {cnt})"
