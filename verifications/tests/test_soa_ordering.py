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

scenarios("studies/soa_ordering.feature")

db = get_db_connection()
logger = get_logger(os.path.basename(__file__))


@given("there are studies with StudyActivity content")
def study_activities_exists():
    query = """
        MATCH (study_activity:StudyActivity)
        RETURN count(study_activity)
    """
    response, _ = db.cypher_query(query)
    assert response[0][0] > 0


@then("each latest active version of StudyActivity has order assigned")
def each_latest_study_activity_has_order_assigned(request, prepare_report_file):
    """Each latest active version of StudyActivity has order assigned"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (:StudyRoot)-[:LATEST]->(study_value:StudyValue)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)
        WHERE NOT (study_activity)<-[:BEFORE]-() AND NOT (study_activity)--(:Delete) AND NOT (study_value)--(:Delete) AND study_activity.order IS null
        WITH study_activity
        {build_root_summary_return_statement('study_activity')}
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
    assert cnt == 0, f"Number of latest StudyActivities without order: {cnt}"


@then(
    "each StudyActivitySubGroup linked to latest active version of StudyActivity has order assigned"
)
def each_latest_study_activity_subgroup_has_order_assigned(
    request, prepare_report_file
):
    """Each StudyActivitySubGroup linked to latest active version of StudyActivity has order assigned"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (:StudyRoot)-[:LATEST]->(study_value:StudyValue)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)
            -[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
        WHERE NOT (study_activity_subgroup)<-[:BEFORE]-() AND NOT (study_activity_subgroup)--(:Delete) AND NOT (study_value)--(:Delete) AND study_activity_subgroup.order IS null
        WITH study_activity_subgroup
        {build_root_summary_return_statement('study_activity_subgroup')}
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
    assert cnt == 0, f"Number of latest StudyActivitySubGroups without order: {cnt}"


@then(
    "each StudyActivityGroup linked to latest active version of StudyActivity has order assigned"
)
def each_latest_study_activity_group_has_order_assigned(request, prepare_report_file):
    """Each StudyActivityGroup linked to latest active version of StudyActivity has order assigned"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (:StudyRoot)-[:LATEST]->(study_value:StudyValue)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)
            -[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
        WHERE NOT (study_activity_group)<-[:BEFORE]-() AND NOT (study_activity_group)--(:Delete) AND NOT (study_value)--(:Delete) AND study_activity_group.order IS null
        WITH study_activity_group
        {build_root_summary_return_statement('study_activity_group')}
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
    assert cnt == 0, f"Number of latest StudyActivityGroups without order: {cnt}"


@then(
    "each StudySoAGroup linked to latest active version of StudyActivity has order assigned"
)
def each_latest_study_soa_group_has_order_assigned(request, prepare_report_file):
    """Each StudySoAGroup linked to latest active version of StudyActivity has order assigned"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (:StudyRoot)-[:LATEST]->(study_value:StudyValue)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)
            -[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
        WHERE NOT (study_soa_group)<-[:BEFORE]-() AND NOT (study_soa_group)--(:Delete) AND NOT (study_value)--(:Delete) AND study_soa_group.order IS null
        WITH study_soa_group
        {build_root_summary_return_statement('study_soa_group')}
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
    assert cnt == 0, f"Number of latest StudySoAGroups without order: {cnt}"


# These checks are disabled for now since the way ordering is implemented is likely to change soon.
# @then(
#     "each StudyActivity under the same StudyActivitySubGroup has unique order assigned"
# )
# def each_study_activity_under_same_study_activity_subgroup_has_unique_order(
#     request, prepare_report_file
# ):
#     """Each latest version of StudyActivity under the same StudyActivitySubGroup has unique order assigned"""
#
#     check_id, check_description = get_name_and_doc()
#     tags = get_gherkin_tags(request)
#     excluded_node_ids = get_excluded_node_ids(check_id)
#
#     query = f"""
#         MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
#         WHERE NOT (study_activity)-[:BEFORE]-() AND NOT (study_activity_subgroup)-[:BEFORE]-() AND NOT(study_activity)--(:Delete)
#         WITH DISTINCT study_activity_subgroup, study_activity
#         WITH DISTINCT study_activity_subgroup, apoc.coll.duplicates(collect(study_activity.order)) as duplicates
#         WHERE NOT isEmpty(duplicates)
#         WITH study_activity_subgroup
#         {build_root_summary_return_statement('study_activity_subgroup')}
#     """
#     result = execute_query_and_append_result_to_file(
#         query, REPORT_FILE_PATH, check_id, check_description, tags=tags
#     )
#     cnt = result["noncompliant_entity_cnt"]
#     assert (
#         cnt == 0
#     ), f"Number of latest StudyActivitySubGroups that have some StudyActivities with wrong order defined: {cnt}"
#
#
# @then(
#     "each StudyActivitySubgroup under the same StudyActivityGroup has unique order assigned"
# )
# def each_study_activity_subgroup_under_same_study_activity_group_has_unique_order(
#     request, prepare_report_file
# ):
#     """Each latest version of StudyActivitySubGroup under the same StudyActivityGroup has unique order assigned"""
#
#     check_id, check_description = get_name_and_doc()
#     tags = get_gherkin_tags(request)
#     excluded_node_ids = get_excluded_node_ids(check_id)
#
#     query = f"""
#         MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
#         MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
#         WHERE NOT (study_activity)-[:BEFORE]-() AND NOT (study_activity_subgroup)-[:BEFORE]-() AND NOT (study_activity_group)-[:BEFORE]-() AND NOT(study_activity)--(:Delete)
#         WITH DISTINCT study_activity_group, study_activity_subgroup
#         WITH DISTINCT study_activity_group,  apoc.coll.duplicates(collect(study_activity_subgroup.order)) as duplicates
#         WHERE NOT isEmpty(duplicates)
#         WITH study_activity_group
#         {build_root_summary_return_statement('study_activity_group')}
#     """
#     result = execute_query_and_append_result_to_file(
#         query, REPORT_FILE_PATH, check_id, check_description, tags=tags
#     )
#     cnt = result["noncompliant_entity_cnt"]
#     assert (
#         cnt == 0
#     ), f"Number of latest StudyActivityGroups that have some StudyActivitySubGroups with wrong order defined: {cnt}"
#
#
# @then("each StudyActivityGroup under the same StudySoAGroup has unique order assigned")
# def each_study_activity_group_under_same_study_activity_soa_group_has_unique_order(
#     request, prepare_report_file
# ):
#     """Each latest version of StudyActivityGroup under the same StudySoAGroup has unique order assigned"""
#
#     check_id, check_description = get_name_and_doc()
#     tags = get_gherkin_tags(request)
#     excluded_node_ids = get_excluded_node_ids(check_id)
#
#     query = f"""
#         MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
#         MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
#         WHERE NOT (study_activity)-[:BEFORE]-() AND NOT (study_activity_group)-[:BEFORE]-() AND NOT (study_soa_group)-[:BEFORE]-() AND NOT (study_activity)--(:Delete)
#         WITH DISTINCT study_activity_group, study_soa_group
#         WITH DISTINCT study_soa_group,  apoc.coll.duplicates(collect(study_activity_group.order)) as duplicates
#         WHERE NOT isEmpty(duplicates)
#         WITH study_soa_group
#         {build_root_summary_return_statement('study_soa_group')}
#     """
#     result = execute_query_and_append_result_to_file(
#         query, REPORT_FILE_PATH, check_id, check_description, tags=tags
#     )
#     cnt = result["noncompliant_entity_cnt"]
#     assert (
#         cnt == 0
#     ), f"Number of latest StudySoAGroups that have some StudyActivityGroups with wrong order defined: {cnt}"
#
#
# @then(
#     "StudyActivities under the same StudyActivitySubGroup have sequential order assigned"
# )
# def study_activities_under_same_study_activity_subgroup_have_sequential_order(
#     request, prepare_report_file
# ):
#     """All latest version of StudyActivities under the same StudyActivitySubGroup have sequential order assigned"""
#
#     check_id, check_description = get_name_and_doc()
#     tags = get_gherkin_tags(request)
#     excluded_node_ids = get_excluded_node_ids(check_id)
#
#     query = f"""
#         MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
#         WHERE NOT (study_activity)-[:BEFORE]-() AND NOT (study_activity_subgroup)-[:BEFORE]-() AND NOT(study_activity)--(:Delete)
#         WITH DISTINCT study_activity_subgroup, study_activity
#         WITH DISTINCT study_activity_subgroup,  apoc.coll.sort(collect(study_activity.order)) as orders
#         WHERE orders <> range(1, size(orders))
#         WITH study_activity_subgroup
#         {build_root_summary_return_statement('study_activity_subgroup')}
#     """
#     result = execute_query_and_append_result_to_file(
#         query, REPORT_FILE_PATH, check_id, check_description, tags=tags
#     )
#     cnt = result["noncompliant_entity_cnt"]
#     assert (
#         cnt == 0
#     ), f"Number of latest StudyActivitySubGroups that contain StudyActivities with not subsequent orders: {cnt}"
#
#
# @then(
#     "StudyActivitySubGroups under the same StudyActivityGroup have sequential order assigned"
# )
# def study_activity_subgroups_under_same_study_activity_group_have_sequential_order(
#     request, prepare_report_file
# ):
#     """All latest version of StudyActivitySubGroups under the same StudyActivityGroup have sequential order assigned"""
#
#     check_id, check_description = get_name_and_doc()
#     tags = get_gherkin_tags(request)
#     excluded_node_ids = get_excluded_node_ids(check_id)
#
#     query = f"""
#         MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
#         MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
#         WHERE NOT (study_activity)-[:BEFORE]-() AND NOT (study_activity_subgroup)-[:BEFORE]-() AND NOT (study_activity_group)-[:BEFORE]-() AND NOT(study_activity)--(:Delete)
#         WITH DISTINCT study_activity_group, study_activity_subgroup
#         WITH DISTINCT study_activity_group,  apoc.coll.sort(collect(study_activity_subgroup.order)) as orders
#         WHERE orders <> range(1, size(orders))
#         WITH study_activity_group
#         {build_root_summary_return_statement('study_activity_group')}
#     """
#     result = execute_query_and_append_result_to_file(
#         query, REPORT_FILE_PATH, check_id, check_description, tags=tags
#     )
#     cnt = result["noncompliant_entity_cnt"]
#     assert (
#         cnt == 0
#     ), f"Number of latest StudyActivityGroups that contain StudyActivitySubGroups with not subsequent orders: {cnt}"
#
#
# @then("StudyActivityGroups under the same StudySoAGroup have sequential order assigned")
# def study_activity_groups_under_same_study_soa_group_have_sequential_order(
#     request, prepare_report_file
# ):
#     """All latest version of StudyActivityGroups under the same StudySoAGroup have sequential order assigned"""
#
#     check_id, check_description = get_name_and_doc()
#     tags = get_gherkin_tags(request)
#     excluded_node_ids = get_excluded_node_ids(check_id)
#
#     query = f"""
#         MATCH (study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
#         MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
#         WHERE NOT (study_activity)-[:BEFORE]-() AND NOT (study_activity_group)-[:BEFORE]-() AND NOT (study_soa_group)-[:BEFORE]-() AND NOT (study_activity)--(:Delete)
#         WITH DISTINCT study_activity_group, study_soa_group
#         WITH DISTINCT study_soa_group,  apoc.coll.sort(collect(study_activity_group.order)) as orders
#         WHERE orders <> range(1, size(orders))
#         WITH study_soa_group
#         {build_root_summary_return_statement('study_soa_group')}
#     """
#     result = execute_query_and_append_result_to_file(
#         query, REPORT_FILE_PATH, check_id, check_description, tags=tags
#     )
#     cnt = result["noncompliant_entity_cnt"]
#     assert (
#         cnt == 0
#     ), f"Number of latest StudySoAGroups that contain StudyActivityGroups with not subsequent orders: {cnt}"
