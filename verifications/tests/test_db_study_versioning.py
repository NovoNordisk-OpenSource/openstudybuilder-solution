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
from textwrap import dedent

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

scenarios("studies/study_versioning.feature")

db = get_db_connection()
logger = get_logger(os.path.basename(__file__))


@given("there are versioned studies")
def versioned_studies_exist():
    pass


@then(
    "only the last HAS_VERSION relationship of each study should be without an end date"
)
def only_latest_study_version_lacks_end_date(request, prepare_report_file):
    """Only last HAS_VERSION relationship should be without an end date for each root node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        // Only last version relationship should be without an end date for each root node
        MATCH (root:StudyRoot)-[v:HAS_VERSION]->(value)
        WITH root, v
        ORDER BY 
            root,
            v.end_date DESC,
            v.start_date DESC 
        WITH root, collect(v) as versions
        WITH root, [v IN tail(versions) WHERE v.end_date IS NULL] as bad
        WITH root WHERE size(bad) > 0
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


@then("the study root node has no more than one each of LATEST_nnn relationships")
def only_one_latest_for_study_root(request, prepare_report_file):
    """No more than one of each of LATEST|LATEST_DRAFT|LATEST_RETIRED|LATEST_FINAL relationship can exist for a study root node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        // No more than one of each of LATEST|LATEST_DRAFT|LATEST_RETIRED|LATEST_FINAL relationship can exist for a study root node
        MATCH (root:StudyRoot)-[v:LATEST|LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED]->()
        WITH root, collect(type(v)) as types
        WHERE size(apoc.coll.duplicates(types)) > 0
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
    ), f"Number of study root nodes with more than one of each of LATEST|LATEST_DRAFT|LATEST_RETIRED|LATEST_FINAL relationships: {cnt}"


@then("there are no duplicated HAS_VALUE relationships by status and date")
def test_no_duplicated_study_version_by_status_and_dates(request, prepare_report_file):
    """No duplicate HAS_VERSION relationship with same status by start or end date for each study root node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        // No duplicate HAS_VERSION relationship by status and start or end date for each study root node
        MATCH (root:StudyRoot)-[v:HAS_VERSION]->()
        WITH root, collect(v.status) as statuses, v
        WITH root, statuses, collect(v.start_date) as starts, collect(v.end_date) as ends
        WHERE (size(apoc.coll.duplicates(starts)) > 0 OR size(apoc.coll.duplicates(ends)) > 0)
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
    ), f"Number of duplicated HAS_VERSION relationships by status and start or end date: {cnt}"


@then("no HAS_VERSION relationship has a negative duration")
def no_study_version_has_negative_duration(request, prepare_report_file):
    """No HAS_VERSION relationship ends before it starts"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        // No HAS_VERSION relationship ends before it starts
        MATCH (root:StudyRoot)-[v:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_LOCKED|LATEST_RETIRED|LATEST_RELEASED]->()
        WHERE v.end_date IS NOT NULL AND v.end_date < v.start_date
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
    ), f"Number of study version relationships with negative duration: {cnt}"


@then("no HAS_VERSION relationship lacks a start date")
def no_study_version_lacks_start_date(request, prepare_report_file):
    """No HAS_VERSION lacks a start date"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        // No version lacks a start date
        MATCH (root:StudyRoot)-[v:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_LOCKED|LATEST_RETIRED|LATEST_RELEASED]->()
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


@then("all HAS_VERSION relationship from a study root node are in chronologic order")
def study_versions_in_chronologic_order(request, prepare_report_file):
    """Study versions must have chronological start and end date for each root node without overlaps or gaps"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = (
        dedent("""
        // Study versions must have chronological start and end date for each root node without overlaps or gaps
        MATCH (root:StudyRoot)-[v:HAS_VERSION]->(value)
        WITH root, value, v.start_date as start_date,
        CASE
            WHEN v.end_date IS NULL
            THEN datetime()
            ELSE v.end_date
        END AS end_date
        ORDER BY root, datetime.truncate('second', start_date), datetime.truncate('second', end_date)
        WITH root, collect(start_date) AS sds, collect(end_date) AS eds
        WHERE size(sds) > 1
        // Check that start date of each version equals end date of the previous.
        UNWIND range(1, size(sds) - 1) AS i
        WITH root, root.uid AS uid,
            eds[i - 1] AS end_date,
            sds[i] AS start_date,
            duration.between(eds[i - 1], sds[i]).microseconds AS diff
        WHERE abs(diff) > 50000  // allowing 50ms deviation
        WITH *
        ORDER BY uid, start_date
        // RETURN uid, diff, start_date, end_date
            """)
        + build_root_summary_return_statement(
            "root", extra_return=[("COLLECT(root.uid)", "root_uids")]
        )
    )

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
    ), f"Number of study root nodes with versions that are not in chronologic order: {cnt}, study roots: {result.get('root_uids', [])}"


@then("the LATEST relationship points to the latest study version")
def latest_points_at_latest_study_version(request, prepare_report_file):
    """LATEST relationship should point at same value as the latest HAS_VERSION"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        // LATEST relationship should point at the latest version
        MATCH (root:StudyRoot)-[:LATEST]->(latest)
        MATCH (root)-[v:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_LOCKED|LATEST_RETIRED|LATEST_RELEASED]->(value)
        WITH root, latest, value
        ORDER BY 
            root,
            v.end_date ASC,
            v.start_date ASC 
        WITH root, latest, collect(value) as values
        WITH root, latest, last(values) as latest_by_date
        WITH root WHERE latest <> latest_by_date
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
    ), f"Number of LATEST relationships that do not point at the latest version: {cnt}"


@then("there is a matching HAS_VERSION for every LATEST_nnn relationship")
def no_latest_without_has_version(request, prepare_report_file):
    """All LATEST_DRAFT, LATEST_FINAL, LATEST_LOCKED, LATEST_RETIRED, LATEST_RELEASED relationships have a matching HAS_VERSION"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        // All LATEST_DRAFT, LATEST_FINAL, LATEST_LOCKED, LATEST_RETIRED, LATEST_RELEASED relationships have a matching HAS_VERSION
        MATCH (root:StudyRoot)-[lat:LATEST_DRAFT|LATEST_FINAL|LATEST_LOCKED|LATEST_RETIRED|LATEST_RELEASED]->(value)
        WHERE lat.version IS NOT NULL AND lat.status IS NOT NULL
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
    ), f"Number of LATEST_DRAFT, LATEST_FINAL, LATEST_LOCKED, LATEST_RETIRED, LATEST_RELEASED lacking a matching HAS_VERSION: {cnt}"


@then(
    "all HAS_VERSION relationships with status LOCKED have a matching HAS_VERSION with status RELEASED"
)
def no_released_without_locked(request, prepare_report_file):
    """All HAS_VERSION relationships with status LOCKED have a matching HAS_VERSION with status RELEASED"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        // All HAS_VERSION relationships with status LOCKED have a matching HAS_VERSION with status RELEASED
        MATCH (root:StudyRoot)-[hvl:HAS_VERSION {{status: "LOCKED"}}]->(value)
        WHERE NOT (root)-[:HAS_VERSION {{change_description: hvl.change_description, status: "RELEASED"}}]->(value)
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
    ), f"Number of HAS_VERSION relationships with status LOCKED lacking a matching HAS_VERSION with status RELEASED: {cnt}"


@then(
    "only one version of each StudySelection node is connected to each StudyValue node"
)
def unique_study_selection_on_each_study_value(request, prepare_report_file):
    """StudyValue nodes should be connected to a single version of each StudySelection node"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (sr:StudyRoot)-[sr_sv]-(sv:StudyValue)-[sv_ss]-(ss:StudySelection) 
            WHERE NOT TYPE(sv_ss) <> "HAS_PROTOCOL_SOA_CELL" AND TYPE(sv_ss) <> "HAS_PROTOCOL_SOA_FOOTNOTE"
        WITH DISTINCT ss, sv
        WITH ss.uid as ss_uid, sv,  count(ss.uid) as ss_uid_count
        WHERE ss_uid_count>=2
        MATCH (sv)--(n)
        WHERE n.uid = ss_uid
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
    ), f"Number of StudySelections with two or more versions connected to the same study value : {cnt}"


@then(
    "only LOCKED or RELEASED study versions have HAS_PROTOCOL_SOA_CELL or HAS_PROTOCOL_SOA_FOOTNOTE relationships"
)
def only_locked_or_released_have_protocol_soa_relationships(
    request, prepare_report_file
):
    """Only LOCKED or RELEASED versions of studies can have HAS_PROTOCOL_SOA_CELL or HAS_PROTOCOL_SOA_FOOTNOTE relationships"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    query = f"""
        // Only LOCKED or RELEASED versions can have HAS_PROTOCOL_SOA_CELL or HAS_PROTOCOL_SOA_FOOTNOTE relationships
        // Note: Checking RELEASED covers both LOCKED and RELEASED since all LOCKED versions are also RELEASED
        MATCH (sv:StudyValue)-[rels]-(ss:StudySelection) 
        WHERE TYPE(rels)="HAS_PROTOCOL_SOA_CELL" OR TYPE(rels)="HAS_PROTOCOL_SOA_FOOTNOTE"
        MATCH (sv)-[versioning:HAS_VERSION]-(sr:StudyRoot)
        WHERE NOT EXISTS((sv)-[:HAS_VERSION {{status:"RELEASED"}}]-(sr))
        {build_root_summary_return_statement('sr')}
    """
    result = execute_query_and_append_result_to_file(
        query, REPORT_FILE_PATH, check_id, check_description, tags=tags
    )
    cnt = result["noncompliant_entity_cnt"]
    assert (
        cnt == 0
    ), f"Number of study versions with HAS_PROTOCOL_SOA_CELL or HAS_PROTOCOL_SOA_FOOTNOTE relationships that are not LOCKED or RELEASED: {cnt}"
