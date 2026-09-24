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
# pylint: disable=duplicate-code
import os

from pytest_bdd import given, scenarios, then

from utils.utils import (
    REPORT_FILE_PATH,
    build_root_summary_return_statement,
    execute_query_and_append_result_to_file,
    get_db_connection,
    get_excluded_node_ids,
    get_gherkin_tags,
    get_logger,
    get_name_and_doc,
)

scenarios("general/basics.feature")

db = get_db_connection()
logger = get_logger(os.path.basename(__file__))


@then("naming properties on nodes should not have leading or trailing spaces")
def no_leading_trailing_spaces_in_naming_properties(request, prepare_report_file):
    """Naming properties on nodes should not have leading or trailing spaces"""
    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    properties_to_check = [
        "name",
        "short_name",
        "sponsor_preferred_name",
        "name_sentence_case",
    ]
    regex = "(^\\\\s.*|.*\\\\s$)"

    where_clauses = [
        f"(n.{prop} IS NOT NULL AND n.{prop} =~ '{regex}')"
        for prop in properties_to_check
    ]
    where_statement = "\n            OR ".join(where_clauses)

    query = f"""
        MATCH ()-[hv:HAS_VERSION]->(n)
        WHERE {where_statement}
            AND hv.end_date IS NULL 
            AND hv.status IN ["Draft", "Final"]
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
    assert (
        cnt == 0
    ), f"Number of nodes with leading/trailing spaces in naming properties: {cnt}"


@then("definitions do not have leading or trailing spaces or line breaks")
def no_leading_trailing_spaces_or_line_breaks_in_definitions(
    request, prepare_report_file
):
    """Definitions should not have leading or trailing spaces or line breaks"""
    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    regex = "(^\\\\s.*|.*\\\\s$|^\\\\n.*|.*\\\\n$)"

    query = f"""
        MATCH ()-[hv:HAS_VERSION]->(n)
        WHERE n.definition IS NOT NULL AND n.definition =~ '{regex}' AND hv.end_date IS NULL AND hv.status IN ["Draft", "Final"]
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
    assert (
        cnt == 0
    ), f"Number of nodes with leading/trailing spaces or line breaks in definition: {cnt}"


@then("definitions do not contain any formatting control codes")
def no_formatting_codes_in_definitions(request, prepare_report_file):
    """Definitions should not have formatting control codes"""
    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    # regex to match multiline strings containing codes like "&#8729;" or "_x000D_".
    # The codes may appear anywhere, on any line of the string.
    # Ignore line breaks in the matching.
    regex = "[\\\\s\\\\S]*(&#\\\\d+;|_x0{0,3}[0-9A-Fa-f]{2,4}_)[\\\\s\\\\S]*"

    query = f"""
        MATCH ()-[hv:HAS_VERSION]->(n)
        WHERE n.definition IS NOT NULL AND n.definition =~ '{regex}' AND hv.end_date IS NULL AND hv.status IN ["Draft", "Final"]
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
    assert (
        cnt == 0
    ), f"Number of nodes with formatting control codes in definition: {cnt}"


@given("the database is reachable and has CTConfigValue nodes")
def config_nodes_exist():
    query = """
        MATCH (n:CTConfigValue)
        RETURN count(n)
    """
    response, _ = db.cypher_query(query)
    assert response[0][0] > 0


@then("all string properties on CTConfigValue nodes are in snake_case")
def ct_config_value_case(request, prepare_report_file):
    """All string properties on CTConfigValue nodes are in snake_case"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        // All string properties on CTConfigValue nodes are in snake_case
        MATCH (n:CTConfigValue)
        WHERE NOT all(prop in keys(n) WHERE NOT apoc.meta.cypher.isType(n[prop], "STRING") OR n[prop] =~ "^[a-z.]+(_[a-z.]+)*$")
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
    assert cnt == 0, f"Number of properties not in snake_case: {cnt}"


@then("there are no orphan nodes")
def orphan_nodes(request, prepare_report_file):
    """There should be no orphan nodes apart from: Counter, UnitDefinitionCounter, Brand, Library, ClinicalProgramme, TemplateParameterValue, TemplateParameterTermValue, User, FeatureFlagRoot, FeatureFlagValue, _Neodash_Dashboard, ComplexityBurden, Notification"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        // Nodes without any connections should be an inconsistency
        MATCH (n)
        WHERE NOT (n)--()
        AND NOT 'Counter' IN labels(n) 
        AND NOT 'UnitDefinitionCounter' IN labels(n)
        AND NOT 'Brand' IN labels(n)
        AND NOT 'Library' IN labels(n)
        AND NOT 'ClinicalProgramme' IN labels(n)
        AND NOT 'TemplateParameterValue' IN labels(n)
        AND NOT 'TemplateParameterTermValue' IN labels(n)
        AND NOT 'User' IN labels(n)
        AND NOT 'FeatureFlagRoot' IN labels(n)
        AND NOT 'FeatureFlagValue' IN labels(n)
        AND NOT '_Neodash_Dashboard' IN labels(n)
        AND NOT 'ComplexityBurden' IN labels(n)
        AND NOT 'Notification' IN labels(n)
        WITH n, labels(n) as orphan_labels
        {build_root_summary_return_statement('n', extra_return=['orphan_labels'])}
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
    ), f"Number of orphan nodes is too big: {cnt}, labels: {result.get('orphan_labels', [])}"


@then("there are no root nodes lacking a relationship to a value node")
def root_node_without_value_node(request, prepare_report_file):
    """There should be no Root nodes without Value nodes connected to them, apart from: CTCodelistRoot, CTTermRoot"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        // Get all Root nodes with no corresponding Value nodes
        MATCH (n) 
        WHERE ANY(label IN labels(n) WHERE label =~ "(?i).*Root")
        AND NOT 'CTCodelistRoot' IN labels(n) // Points to CTCodelistNameRoot, CTCodelistAttributesRoot
        AND NOT 'CTTermRoot' IN labels(n) // Points to CTTermNameRoot, CTTermAttributesRoot
        AND NOT 'StudyEndpoint' IN labels(n) // TemplateParameterValueRoot:StudyEndpoint:StudySelection nodes do not have Value nodes by design
        AND NOT 'ActivityItem' IN labels(n) // ConceptRoot:ActivityDefinition:ActivityItem nodes do not have Value nodes by design
        AND NOT (n)-[:LATEST]->()
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
    assert cnt == 0, f"Number of root nodes without a value node is too big: {cnt}"
