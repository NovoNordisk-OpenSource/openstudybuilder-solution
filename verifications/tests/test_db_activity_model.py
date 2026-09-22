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

scenarios("library/activities.feature")

db = get_db_connection()
logger = get_logger(os.path.basename(__file__))


@given("the library contains activities")
def activties_exist():
    query = """
        MATCH (root:ActivityRoot)
        RETURN count(root)
    """
    response, _ = db.cypher_query(query)
    assert response[0][0] > 0


@then("ActivityValidGroup nodes link to both a group and a subgroup")
def incomplete_subgroup_grouping_nodes(request, prepare_report_file):
    """All subgroup grouping nodes are complete"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (avg:ActivityValidGroup) WHERE NOT (avg)<-[:HAS_GROUP]-(:ActivitySubGroupValue) OR NOT (avg)-[:IN_GROUP]->(:ActivityGroupValue)
        {build_root_summary_return_statement('avg')}
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
    assert cnt == 0, f"Number of incomplete subgroup grouping nodes: {cnt}"


@then("ActivityGrouping nodes link to both an activity and a group/subgroup pair")
def incomplete_activity_grouping_nodes(request, prepare_report_file):
    """All activity grouping nodes are complete"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (ag:ActivityGrouping) 
        WHERE NOT (ag)<-[:HAS_GROUPING]-(:ActivityValue)
            OR NOT (ag)-[:HAS_SELECTED_SUBGROUP]->(:ActivitySubGroupValue)
            OR NOT (ag)-[:HAS_SELECTED_GROUP]->(:ActivityGroupValue)
        {build_root_summary_return_statement('ag')}
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
    assert cnt == 0, f"Number of incomplete activity grouping nodes: {cnt}"


@then("each activity instances link to a single activity")
def no_instance_links_to_several_activities(request, prepare_report_file):
    """All activity instances link to a single activity"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (aiv:ActivityInstanceValue)<-[ha:HAS_ACTIVITY]->(ag:ActivityGrouping)<-[hg:HAS_GROUPING]-(av:ActivityValue)
        WITH aiv, collect(DISTINCT av) AS avs
        WITH aiv as root WHERE size(avs) > 1
        {build_root_summary_return_statement('root')}
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
    ), f"Number of activity instances linking to multiple activities: {cnt}"


@then("activities without data collection have no instances")
def activities_without_data_collection_have_no_instances(request, prepare_report_file):
    """Activities without data collection have no instances"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (aiv:ActivityInstanceValue)<-[ha:HAS_ACTIVITY]->(ag:ActivityGrouping)<-[hg:HAS_GROUPING]-(av:ActivityValue {{is_data_collected: false}})
        <-[hv:HAS_VERSION]-(:ActivityRoot)
        WHERE hv.end_date IS NULL AND hv.status IN ["Draft", "Final"]
        {build_root_summary_return_statement('av')}
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
    ), f"Number of activities without data collection that have instances: {cnt}"


@then("no instances are linked to activities without data collection")
def no_instances_linked_to_activities_without_data_collection(
    request, prepare_report_file
):
    """Instances are not linked to activities without data collection"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (:ActivityRoot)-[hv:HAS_VERSION]->(aiv:ActivityInstanceValue)<-[ha:HAS_ACTIVITY]->(ag:ActivityGrouping)<-[hg:HAS_GROUPING]-(av:ActivityValue {{is_data_collected: false}})
        WHERE hv.end_date IS NULL AND hv.status IN ["Draft", "Final"]
        {build_root_summary_return_statement('av')}
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
    ), f"Number of instances linked to activities without data collection: {cnt}"


@then("requested activities have no instances")
def requested_activities_have_no_instances(request, prepare_report_file):
    """Requested activities have no instances"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (aiv:ActivityInstanceValue)-[ha:HAS_ACTIVITY]->(ag:ActivityGrouping)<-[hg:HAS_GROUPING]-(av:ActivityValue)<-[hv:HAS_VERSION]-(ar:ActivityRoot)<-[CONTAINS_CONCEPT]-(:Library {{name: "Requested"}})
        WHERE hv.end_date IS NULL AND hv.status IN ["Draft", "Final"]
        {build_root_summary_return_statement('av')}
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
    assert cnt == 0, f"Number of requested activities that have instances: {cnt}"


@then("no instances are linked to requested activities")
def no_instances_linked_to_requested_activities(request, prepare_report_file):
    """No instances are linked to requested activities"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (air:ActivityInstanceRoot)-[hv:HAS_VERSION]->(aiv:ActivityInstanceValue)-[ha:HAS_ACTIVITY]->(ag:ActivityGrouping)<-[hg:HAS_GROUPING]-(av:ActivityValue)<-[:HAS_VERSION]-(ar:ActivityRoot)<-[CONTAINS_CONCEPT]-(:Library {{name: "Requested"}})
        WHERE hv.end_date IS NULL AND hv.status IN ["Draft", "Final", "Retired"]
        {build_root_summary_return_statement('av')}
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
    assert cnt == 0, f"Number of instances linked to requested activities: {cnt}"


@then(
    "HAS_VALID_CODELIST_FOR_ITEMS relationships are only from ActivityItemClassRoot to CTCodelistRoot and are irreflexive with at most one relationship per pair"
)
def has_valid_codelist_for_items_consistency(request, prepare_report_file):
    """
    HAS_VALID_CODELIST_FOR_ITEMS must be from ActivityItemClassRoot to CTCodelistRoot,
    irreflexive, and at most one relationship per (activity item class, codelist) pair.
    """

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    query = f"""
        MATCH (c)-[c_b:HAS_VALID_CODELIST_FOR_ITEMS]->(b)
        WITH c, b, count(c_b) AS rel_counting
        WHERE NOT "ActivityItemClassRoot" IN labels(c)
           OR NOT "CTCodelistRoot" IN labels(b)
           OR c = b
           OR rel_counting > 1
        WITH c AS root
        {build_root_summary_return_statement('root')}
    """
    result = execute_query_and_append_result_to_file(
        query, REPORT_FILE_PATH, check_id, check_description, tags=tags
    )
    cnt = result["noncompliant_entity_cnt"]
    assert cnt == 0, (
        f"Number of HAS_VALID_CODELIST_FOR_ITEMS relationship violations: {cnt}. "
        "Expected: source=ActivityItemClassRoot, target=CTCodelistRoot, irreflexive, "
        "at most one relationship per (activity item class, codelist) pair."
    )
