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

from pytest_bdd import given, parsers, scenarios, then, when

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

scenarios("library/ct_versioning.feature")

db = get_db_connection()
logger = get_logger(os.path.basename(__file__))


@given("there are versioned library items")
def versioned_items_exist():
    query = """
        MATCH (root)-[hv:HAS_VERSION]->(value)
        RETURN count(root)
    """
    response, _ = db.cypher_query(query)
    assert response[0][0] > 0


@when(
    "a root-value pair has a LATEST_FINAL, LATEST_DRAFT or LATEST_RETIRED relationship"
)
def latest_items_exist():
    query = """
        MATCH (root)-[lat:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED]->(value)
        RETURN count(root)
    """
    response, _ = db.cypher_query(query)
    assert response[0][0] > 0


@then("the LATEST_nnn relationship has no properties")
def no_properties_on_latest_final_draft_retired(request, prepare_report_file):
    """No LATEST_FINAL, LATEST_DRAFT or LATEST_RETIRED relationship have versioning properties"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    excluded_labels = [
        "ClassVariableRoot",
        "DatasetClassRoot",
        "DatasetRoot",
        "DatasetScenarioRoot",
        "DatasetVariableRoot",
        "StudyRoot",
    ]

    query = f"""
        // No LATEST_FINAL, LATEST_DRAFT or LATEST_RETIRED relationship have versioning properties
        MATCH (root)-[lat:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED]->(value)
        WHERE none(label in labels(root) WHERE label IN {excluded_labels})
            AND size(keys(properties(lat))) > 0

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
    ), f"Number of LATEST_FINAL, LATEST_DRAFT or LATEST_RETIRED with properties: {cnt}"


@then("there is a matching HAS_VERSION for every LATEST_nnn relationship")
def no_latest_final_draft_retired_without_has_version(request, prepare_report_file):
    """All LATEST_FINAL, LATEST_DRAFT or LATEST_RETIRED relationships have a matching HAS_VERSION"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    excluded_labels = [
        "ClassVariableRoot",
        "DatasetClassRoot",
        "DatasetRoot",
        "DatasetScenarioRoot",
        "DatasetVariableRoot",
        "StudyRoot",
    ]

    query = f"""
        // All LATEST_FINAL, LATEST_DRAFT or LATEST_RETIRED relationships have a matching HAS_VERSION
        MATCH (root)-[lat:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED]->(value)
        WHERE none(label in labels(root) WHERE label IN {excluded_labels})
            AND lat.version IS NOT NULL AND lat.status IS NOT NULL
            AND NOT (root)-[:HAS_VERSION {{version: lat.version, status: lat.status}}]->(value)

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
    ), f"Number of LATEST_FINAL, LATEST_DRAFT or LATEST_RETIRED lacking a matching HAS_VERSION: {cnt}"


@then(
    "only the latest HAS_VERSION relationship for a root-value pair lacks an end date"
)
def only_latest_has_version_lacks_end_date(request, prepare_report_file):
    """Only last HAS_VERSION relationship should be without an end date for each root node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    excluded_labels = [
        "ClassVariableRoot",
        "DataModelIGRoot",
        "DatasetClassRoot",
        "DatasetRoot",
        "DatasetScenarioRoot",
        "DatasetVariableRoot",
        "StudyRoot",
    ]

    query = f"""
        // Only last HAS_VERSION relationship should be without an end date for each root node
        MATCH (root)-[:HAS_VERSION]->()
        WHERE none(label in labels(root) WHERE label IN {excluded_labels})
        CALL {{
                WITH root
                MATCH (root)-[hv:HAS_VERSION]-()
                WITH hv
                // Sort by version and dates
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) DESC,
                    toInteger(split(hv.version, '.')[1]) DESC,
                    hv.end_date DESC,
                    hv.start_date DESC
                WITH collect(hv) as hvs
                // Return all except the very latest
                RETURN tail(hvs) as not_latest
            }}
        WITH root WHERE any(v IN not_latest WHERE v.end_date IS NULL)
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
    assert cnt == 0, f"Number of not-latest HAS_VERSIONs that lack an end date: {cnt}"


@then("the root node has no more than one each of LATEST_nnn relationships")
def only_one_latest_for_root(request, prepare_report_file):
    """No more than one of each of LATEST|LATEST_DRAFT|LATEST_RETIRED|LATEST_FINAL relationship can exist for a root node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    excluded_labels = [
        "ClassVariableRoot",
        "DataModelIGRoot",
        "DatasetClassRoot",
        "DatasetRoot",
        "DatasetScenarioRoot",
        "DatasetVariableRoot",
        "StudyRoot",
    ]

    query = f"""
        // No more than one of each of LATEST|LATEST_DRAFT|LATEST_RETIRED|LATEST_FINAL relationship can exist for a root node
        MATCH (root)-[v:LATEST|LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED]->()
        WITH root, collect(type(v)) as types
        WHERE none(label in labels(root) WHERE label IN {excluded_labels})
        AND size(apoc.coll.duplicates(types)) > 0
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
    ), f"Number of root nodes with more than one of each of LATEST|LATEST_DRAFT|LATEST_RETIRED|LATEST_FINAL relationships: {cnt}"


@then("there are no duplicated HAS_VALUE relationships by date")
def no_duplicated_has_version_by_dates(request, prepare_report_file):
    """No duplicate HAS_VERSION relationship by start and end date for each root node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    excluded_labels = [
        "ClassVariableRoot",
        "DatasetClassRoot",
        "DatasetRoot",
        "DatasetScenarioRoot",
        "DatasetVariableRoot",
        "StudyRoot",
    ]

    query = f"""
        // No duplicate HAS_VERSION relationship by start and end date for each root node
        MATCH (root)-[v:HAS_VERSION]->()
        WITH root, collect(v.start_date) as starts, collect(v.end_date) as ends
        WHERE none(label in labels(root) WHERE label IN {excluded_labels})
        AND (size(apoc.coll.duplicates(starts)) > 0 OR size(apoc.coll.duplicates(ends)) > 0)
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
    ), f"Number of duplicated HAS_VERSION relationships by start or end date: {cnt}"


@then("no HAS_VERSION relationship has a negative duration")
def no_version_has_negative_duration(request, prepare_report_file):
    """No HAS_VERSION relationship ends before it starts"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    # Exclude data models for now
    excluded_labels = [
        "ClassVariableRoot",
        "DatasetClassRoot",
        "DatasetRoot",
        "DatasetScenarioRoot",
        "DatasetVariableRoot",
    ]

    query = f"""
        // No HAS_VERSION relationship ends before it starts
        MATCH (root)-[v:HAS_VERSION]->()
        WHERE none(label in labels(root) WHERE label IN {excluded_labels})
        AND v.end_date IS NOT NULL AND v.end_date < v.start_date
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
    ), f"Number of HAS_VERSION relationships with negative duration: {cnt}"


@then("no HAS_VERSION relationship lacks a start date")
def no_version_lacks_start_date(request, prepare_report_file):
    """No HAS_VERSION lacks a start date"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        // No HAS_VERSION lacks a start date
        MATCH (root)-[v:HAS_VERSION]->()
        WHERE v.start_date IS NULL
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
    assert cnt == 0, f"Number of HAS_VERSION relationships that lacks start date: {cnt}"


@then("all HAS_VERSION relationship from a node are in chronologic order")
def versions_in_chronologic_order(request, prepare_report_file):
    """HAS_VERSION relationship must have chronological start and end date for each root node without overlaps or gaps"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    excluded_labels = [
        "ClassVariableRoot",
        "DatasetClassRoot",
        "DatasetRoot",
        "DatasetScenarioRoot",
        "DatasetVariableRoot",
        "StudyRoot",
    ]

    query = f"""
        // HAS_VERSION relationship must have chronological start and end date for each root node without overlaps or gaps
        MATCH (root)-[hv:HAS_VERSION]->(value)
        WHERE none(label in labels(root) WHERE label IN {excluded_labels})
        WITH root, hv ORDER BY hv.start_date
        WITH root, collect(hv) as hv
        WHERE size(hv)>1
        // Check that start date of each version equals end date of the previous
        WITH root, [n IN range(1,size(hv)) WHERE hv[n-1].end_date <> hv[n].start_date ] AS bad
        WITH root WHERE size(bad)>0
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
    ), f"Number of root nodes with HAS_VERSION relationships that are not in chronologic order: {cnt}"


@then("there are no duplicated HAS_VALUE relationships by version number")
def no_duplicated_has_version_by_version(request, prepare_report_file):
    """
    No duplicate HAS_VERSION relationship by version number for each root node
     - except for changes between 'Final' and 'Retired', as inactivation and reactivation
       should create new HAS_VERSION relationships for the same version number.
    """

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    excluded_labels = [
        "ClassVariableRoot",
        "DatasetClassRoot",
        "DatasetRoot",
        "DatasetScenarioRoot",
        "DatasetVariableRoot",
        "StudyRoot",
    ]

    query = f"""
        // No duplicate HAS_VERSION relationship by version number for each root node
        MATCH (root)-[hv:HAS_VERSION]->()
        WHERE none(label in labels(root) WHERE label IN {excluded_labels})
        WITH root, apoc.coll.duplicates(collect(hv.version)) as version, collect(hv) as hv
        WHERE size(version) > 0
        CALL {{
            WITH root, version
            UNWIND version as v
            MATCH (root)-[hv2:HAS_VERSION {{version: v}}]-()
            WITH root, v, hv2
            ORDER BY hv2.start_date ASC
            WITH root, v, collect(hv2) as hvs
            // Only allow duplicates if the status switches back and forth between Final and Retired
            WITH root, v, [n IN range(1,size(hvs)) WHERE hvs[n-1].status = hvs[n].status OR NOT hvs[n].status IN ["Retired", "Final"] ] AS bad
            RETURN bad
        }}
        WITH root WHERE size(bad)>0
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
    ), f"Number of duplicated HAS_VERSION relationships by version number: {cnt}"


@then(
    parsers.parse(
        "every {relationship} relationship points to the latest value in state {status}"
    )
)
def latest_points_at_latest_value(request, relationship, status):
    """LATEST relationship should point at same value as the latest HAS_VERSION"""

    check_id = f"{relationship.lower()}_points_at_latest_value"
    check_description = f"{relationship} relationship should point at same value as the latest HAS_VERSION with status {status}"
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    excluded_labels = [
        "ClassVariableRoot",
        "DatasetClassRoot",
        "DatasetRoot",
        "DatasetScenarioRoot",
        "DatasetVariableRoot",
        "DataModelIGRoot",
        "StudyRoot",
    ]

    status_statement = ""
    if status in ["Final", "Draft", "Retired"]:
        status_statement = f"{{status: '{status}'}}"

    query = f"""
        // LATEST relationship points at same value as the latest HAS_VERSION
        MATCH (root)-[:{relationship}]->(latest)
        WHERE none(label in labels(root) WHERE label IN {excluded_labels})
        CALL {{
                WITH root
                MATCH (root)-[hv:HAS_VERSION {status_statement}]->(has_value)
                WITH hv, has_value
                // Sort by version and dates
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs, collect(has_value) as sorted_vals
                RETURN last(sorted_vals) as latest_via_hv
            }}
        WITH root WHERE latest <> latest_via_hv
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
    ), f"Number of {relationship} relationships that do not point at the latest corresponding HAS_VERSION: {cnt}"


@then(
    parsers.parse(
        "the latest HAS_VERSION relationship with status {status} has a corresponding {relationship} relationship"
    )
)
def latest_version_of_each_status_has_corresponding_latest_rel(
    request, relationship, status
):
    """The latest HAS_VERSION relationship of each status has a matching LATEST_nnnn relationship"""

    check_id = f"latest_{status}_has_corresponding_{relationship.lower()}_relationship"
    check_description = f"the latest HAS_VERSION relationship with status {status} has a corresponding {relationship} relationship"
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

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
    ), f"Number of latest {status} HAS_VERSIONS that lack a corresponding {relationship}: {cnt}"


@then("each Retired HAS_VERSION relationship has a corresponsding Final")
def retired_version_has_final(request, prepare_report_file):
    """Each Retired HAS_VERSION relationship has a corresponsding Final"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (root)-[ret:HAS_VERSION {{status: "Retired"}}]->(value)
        WHERE NOT (root)-[:HAS_VERSION {{status: "Final"}}]->(value)
        {build_root_summary_return_statement('root', extra_return=[("COLLECT(root.uid)", "root_uids")])}
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
    ), f"Number of nodes with Retired HAS_VERSION relationships without corresponding Final: {cnt}, uids: {result.get('root_uids', [])}"
