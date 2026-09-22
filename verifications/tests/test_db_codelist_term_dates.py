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

scenarios("library/ct_term_dates.feature")

db = get_db_connection()
logger = get_logger(os.path.basename(__file__))


@given("there are codelists with obsolete terms")
def obsolete_items_exist():
    query = """
        MATCH (root)-[r:HAS_TERM]->()
        WHERE r.end_date IS NOT NULL
        RETURN count(root)
    """
    response, _ = db.cypher_query(query)
    assert response[0][0] > 0


@given("there are codelists with current terms")
def current_items_exist():
    query = """
        MATCH (root)-[r:HAS_TERM]->()
        WHERE r.end_date IS NULL
        RETURN count(root)
    """
    response, _ = db.cypher_query(query)
    assert response[0][0] > 0


@then("the codelists link to the terms in chronologic order")
def codelist_terms_in_chronologic_order(request, prepare_report_file):
    """HAS_TERM relationships from a root node to terms with a given concept id must have chronological start and end dates without overlaps"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        // HAS_TERM relationships from a root node to terms with a given concept id must have chronological start and end dates without overlaps
        MATCH (clr)-[ht:HAS_TERM]-(clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]-(:CTTermAttributesRoot)-[:LATEST]->(attrs:CTTermAttributesValue)
        WITH clr, ht, collect(DISTINCT attrs.concept_id) as cid ORDER BY cid, ht.start_date
        UNWIND cid as c
        WITH clr, c, collect(ht) as hts
        WHERE size(hts)>1
        // Check that start date of each version is equal or later than end date of the previous
        WITH clr, [n IN range(1,size(hts)) WHERE hts[n-1].end_date > hts[n].start_date ] AS bad
        WITH clr, bad WHERE size(bad)>0
        WITH DISTINCT clr AS root
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
    ), f"Number of root nodes with HAS_TERM relationships that are not in chronologic order: {cnt}"


@then("codelists only link to terms that are active")
def codelists_use_existing_terms(request, prepare_report_file):
    """The start_date of a HAS_TERM relationship must be equal to or later than the first start_date of the term it points at"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        // The start_date of a HAS_TERM relationship must be equal to or later than the first start_date of the term it points at
        MATCH (clr)-[ht:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(ar)-[hv:HAS_VERSION]->(av) 
        WITH clr, ht.start_date as tstart, hv.start_date as vstart ORDER BY clr, tstart, vstart DESC
        WITH clr, tstart, collect(vstart) as vstart
        WITH clr, tstart, last(vstart) as vstart
        WHERE tstart < vstart
        WITH DISTINCT clr AS root
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
    ), f"Number of root nodes with HAS_TERM relationships that starts before the term exists: {cnt}"


@then("no obsolete term has a negative duration")
def no_past_term_has_negative_duration(request, prepare_report_file):
    """No HAS_TERM relationship ends before it starts"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)

    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        // No HAS_TERM relationship ends before it starts
        MATCH (root)-[v:HAS_TERM]->(clt:CTCodelistTerm)
        WHERE v.end_date IS NOT NULL AND v.end_date < v.start_date
        WITH COLLECT(DISTINCT root.uid) AS all_root_uids,
             COLLECT(DISTINCT clt.submission_value) AS all_clt_submission_values,
             COLLECT(root) AS root_list
        UNWIND root_list AS root
        {build_root_summary_return_statement('root', extra_return=[('all_root_uids', 'root_uids'), ('all_clt_submission_values', 'clt_submission_values')])}
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
    ), f"Number of HAS_TERM relationships with negative duration: {cnt}, codelists: {result.get('root_uid', [])}, terms: {result.get('clt_submission_value', [])}"
