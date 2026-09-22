"""
This modules verifies that:
 - API endpoints works as expected
 - DB nodes/relations look as expected.

Each database test should execute a CYPHER query that returns one row with these columns:
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
# pylint: disable=duplicate-code
import os

from pytest_bdd import parsers, scenarios, step, then

from utils.utils import (
    REPORT_FILE_PATH,
    api_get,
    build_root_summary_return_statement,
    execute_query_and_append_result_to_file,
    extract_values_by_path,
    get_db_connection,
    get_excluded_node_ids,
    get_gherkin_tags,
    get_logger,
    get_name_and_doc,
)

scenarios("general/user_identification.feature")

db = get_db_connection()
logger = get_logger(os.path.basename(__file__))


@then("all relevant nodes have author_id field set")
def nodes_have_author_id_field_set(request, prepare_report_file):
    """All relevant nodes have author_id field set"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (n:CTPackage|StudyAction|Edit|Create|Delete)
        WHERE n.author_id is null
        {build_root_summary_return_statement('n')}
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
    assert cnt == 0, f"Number of relevant nodes that don't have author_id field: {cnt}"


@then("all relevant relations have author_id field set")
def relations_have_author_id_field_set(request, prepare_report_file):
    """All relevant relations have author_id field set"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = """
        MATCH (n)-[rel:HAS_VERSION|HAS_TERM|LATEST_LOCKED|LATEST_RELEASED]->(m)
        WHERE rel.author_id is null
        RETURN
            COUNT(rel) as noncompliant_entity_cnt,
            COLLECT(distinct(type(rel))) as noncompliant_labels,
            COLLECT(distinct(elementId(rel))) as noncompliant_node_ids
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
    ), f"Number of relevant relations that don't have author_id field: {cnt}"


@then(
    "for each node author_id field value there must exist one User node with the same user_id field value"
)
def node_author_id_references_one_user_node(request, prepare_report_file):
    """For each node author_id field value there must exist one User node with the same user_id field value"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (n:CTPackage|StudyAction|Edit|Create|Delete)
        OPTIONAL MATCH (u:User {{user_id: n.author_id}})
        WITH  n,
              COUNT(DISTINCT u) as user_nodes_cnt
        WHERE user_nodes_cnt = 0
        {build_root_summary_return_statement('n')}
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
    assert cnt == 0, f"Number of nodes that don't have corresponding User node: {cnt}"


@step(
    "for each relation author_id field value there must exist one User node with the same user_id field value"
)
def relation_author_id_references_one_user_node(request, prepare_report_file):
    """For each relation author_id field value there must exist one User node with the same user_id field value"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = """
        MATCH (n)-[rel:HAS_VERSION|HAS_TERM|LATEST_LOCKED|LATEST_RELEASED]->(m)
        OPTIONAL MATCH (u:User {user_id: rel.author_id})
        WITH  rel,
            COUNT(DISTINCT u) as user_nodes_cnt
        WHERE user_nodes_cnt = 0
        RETURN
            COUNT(rel) as noncompliant_entity_cnt,
            COLLECT(distinct(type(rel))) as noncompliant_labels,
            COLLECT(distinct(elementId(rel))) as noncompliant_node_ids
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
    ), f"Number of relations that don't have corresponding User node: {cnt}"


@step("there is no User node with user_id set to null")
def no_user_node_with_null_user_id(request, prepare_report_file):
    """There should not exist any User node with user_id field set to null"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (n:User)
        WHERE n.user_id is null
        {build_root_summary_return_statement('n')}
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
    assert cnt == 0, f"Number of User nodes with user_id field set to null: {cnt}"


@step(parsers.parse("get {url} returns not null value for {json_path} field"))
def api_get_returns_not_null_value_for_field(url: str, json_path: str):
    """API: HTTP GET {0} return non-null value for fields with JSON path {1}"""
    params = {"page_size": 100}
    res = api_get(path=url, params=params)

    data = res.json()

    # Extract all fields from data JSON using JSON path
    vals = extract_values_by_path(data, json_path)
    print(f"Values for {json_path}: {vals}")
    for val in vals:
        assert val is not None, f"Value for {json_path} is null"
