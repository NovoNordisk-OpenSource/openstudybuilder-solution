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

scenarios("library/ct_codelist_rules.feature")

db = get_db_connection()
logger = get_logger(os.path.basename(__file__))


@given("there are codelists containing multiple terms in the database")
def codelist_with_terms_exist():
    query = """
        MATCH (root)-[r:HAS_TERM]->(t)
        WITH root, count(t) as term_count
        WHERE term_count > 1
        RETURN count(root)
    """
    response, _ = db.cypher_query(query)
    assert response[0][0] > 0


@given("there are paired codelists in the database")
def paired_codelists_exist():
    query = """
        MATCH (decode_root:CTCodelistRoot)-[:PAIRED_CODE_CODELIST]->(code_root:CTCodelistRoot)
        RETURN count(decode_root)
    """
    response, _ = db.cypher_query(query)
    assert response[0][0] > 0


@given("there are ordinal codelists containing terms in the database")
def ordinal_codelists_with_terms_exist():
    query = """
        MATCH (clr:CTCodelistRoot)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST]->(cnv:CTCodelistNameValue)
        WHERE cnv.is_ordinal = true
        MATCH (clr)-[ht:HAS_TERM]->(:CTCodelistTerm)
        WHERE ht.end_date IS NULL
        RETURN count(DISTINCT clr)
    """
    response, _ = db.cypher_query(query)
    assert response[0][0] > 0


@then("the list of term names within each codelist contains no duplicates")
def no_duplicated_term_names(request, prepare_report_file):
    """No codelist contains duplicated term names"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (clr:CTCodelistRoot)-[ht:HAS_TERM]->(clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(tnv:CTTermNameValue)
        // Only consider current terms, and exclude the CDISC Glossary, concept id C67497
        WHERE ht.end_date IS NULL AND clr.uid <> "C67497"
        WITH clr, collect(tnv.name) AS term_names
        WITH clr, apoc.coll.duplicates(term_names) AS duplicates
        WHERE size(duplicates) > 0
        WITH COLLECT(DISTINCT duplicates) AS all_duplicates, 
             COLLECT(DISTINCT clr.uid) AS all_clr_uids, 
             COLLECT(clr) AS clr_list
        UNWIND clr_list AS clr
        {build_root_summary_return_statement('clr', extra_return=[('all_duplicates', 'duplicates'), ('all_clr_uids', 'clr_uids')])}
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
    ), f"Number of codelists that contain duplicated term names: {cnt}, codelists: {result.get('clr_uids', [])}, names: {result.get('duplicates', [])}"


@then("the list of term concept ids within each codelist contains no duplicates")
def no_duplicated_term_concept_ids(request, prepare_report_file):
    """No codelist contains duplicated term concept ids"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (clr:CTCodelistRoot)-[ht:HAS_TERM]->(clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(tav:CTTermAttributesValue)
        WHERE ht.end_date IS NULL AND tav.concept_id IS NOT NULL
        WITH clr, collect(tav.concept_id) AS term_concept_ids
        WITH clr, apoc.coll.duplicates(term_concept_ids) AS duplicates
        WHERE size(duplicates) > 0
        WITH COLLECT(DISTINCT duplicates) AS all_duplicates, 
             COLLECT(DISTINCT clr.uid) AS all_clr_uids, 
             COLLECT(clr) AS clr_list
        UNWIND clr_list AS clr
        {build_root_summary_return_statement('clr', extra_return=[('all_duplicates', 'duplicates'), ('all_clr_uids', 'clr_uids')])}
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
    ), f"Number of codelists that contain duplicated term concept ids: {cnt}, codelists: {result.get('clr_uids', [])}, concept ids: {result.get('duplicates', [])}"


@then("the list of term submission values within each codelist contains no duplicates")
def no_duplicated_term_submission_values(request, prepare_report_file):
    """No codelist contains duplicated term submission values"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (clr:CTCodelistRoot)-[ht:HAS_TERM]->(clt:CTCodelistTerm)
        WHERE ht.end_date IS NULL
        WITH clr, collect(clt.submission_value) AS term_submvals
        WITH clr, apoc.coll.duplicates(term_submvals) AS duplicates
        WHERE size(duplicates) > 0
        WITH COLLECT(DISTINCT duplicates) AS all_duplicates, 
             COLLECT(DISTINCT clr.uid) AS all_clr_uids, 
             COLLECT(clr) AS clr_list
        UNWIND clr_list AS clr
        {build_root_summary_return_statement('clr', extra_return=[('all_duplicates', 'duplicates'), ('all_clr_uids', 'clr_uids')])}
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
    ), f"Number of codelists that contain duplicated term submission values: {cnt}, codelists: {result.get('clr_uids', [])}, values: {result.get('duplicates', [])}"


@then("the two codelists contain the same terms")
def paired_codelists_have_same_terms(request, prepare_report_file):
    """Paired codelists for code and decode values contain the same terms"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (decode_root:CTCodelistRoot)-[:PAIRED_CODE_CODELIST]->(code_root:CTCodelistRoot)
        CALL {{
            WITH decode_root
            MATCH (decode_root)-[ht:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr:CTTermRoot)
            WHERE ht.end_date IS NULL
            WITH DISTINCT tr.uid AS decode_term ORDER BY decode_term
            RETURN collect(decode_term) AS decode_terms
        }}
        CALL {{
            WITH code_root
            MATCH (code_root)-[ht:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr:CTTermRoot)
            WHERE ht.end_date IS NULL
            WITH DISTINCT tr.uid AS code_term ORDER BY code_term
            RETURN collect(code_term) AS code_terms
        }}
        WITH decode_root, code_root,
          [t IN decode_terms WHERE NOT t IN code_terms] as decode_only,
          [t IN code_terms WHERE NOT t IN decode_terms] as code_only
        WITH decode_root, code_root, decode_only + code_only AS non_matching_terms
        WHERE size(non_matching_terms) > 0
        WITH COLLECT(DISTINCT non_matching_terms) AS all_non_matching_terms,
             COLLECT(DISTINCT decode_root.uid) AS all_decode_root_uid,
             COLLECT(DISTINCT code_root.uid) AS all_code_root_uid,
             COLLECT(decode_root) AS decode_root_list
        UNWIND decode_root_list AS decode_root
        {build_root_summary_return_statement('decode_root', extra_return=[('all_non_matching_terms', 'non_matching_terms'), ('all_decode_root_uid', 'decode_root_uid'), ('all_code_root_uid', 'code_root_uid')])}
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
    ), f"Number of codelist pairs that have inconsistent terms: {cnt}, codelists: {result.get('decode_root_uid', [])}, non-matching terms: {result.get('non_matching_terms', [])}"


@then("the two codelists have matching names")
def paired_codelists_have_matching_names(request, prepare_report_file):
    """Paired codelists for code and decode values have matching names"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (decode_name:CTCodelistNameValue)-[:LATEST]-(:CTCodelistNameRoot)--(decode_root:CTCodelistRoot)-[:PAIRED_CODE_CODELIST]->(code_root:CTCodelistRoot)--(:CTCodelistNameRoot)-[:LATEST]-(code_name:CTCodelistNameValue)
        WITH decode_root, code_root, replace(decode_name.name, "Long Name", "") as decode, replace(code_name.name, "Short Name", "") as code
        WITH decode_root, code_root, replace(decode, "Name", "") as decode, replace(code, "Code", "") as code
        WHERE trim(code) <> trim(decode)
        WITH COLLECT(DISTINCT decode_root.uid) AS all_decode_root_uid,
             COLLECT(DISTINCT code_root.uid) AS all_code_root_uid,
             COLLECT(DISTINCT decode) AS all_decode,
             COLLECT(DISTINCT code) AS all_code,
             COLLECT(decode_root) AS decode_root_list
        UNWIND decode_root_list AS decode_root
        {build_root_summary_return_statement('decode_root', extra_return=[('all_decode_root_uid', 'decode_root_uid'), ('all_code_root_uid', 'code_root_uid'), ('all_decode', 'decode'), ('all_code', 'code')])}
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
    ), f"Number of codelist pairs that have inconsistent names: {cnt}, codelists: {result.get('decode_root_uid', [])}"


@then("each ordinal codelist has at least one term with a defined ordinal value")
def ordinal_codelists_have_at_least_one_ordinal_term(request, prepare_report_file):
    """Each ordinal codelist has at least one term with a defined ordinal value"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        MATCH (clr:CTCodelistRoot)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST]->(cnv:CTCodelistNameValue)
        WHERE cnv.is_ordinal = true
        MATCH (clr)-[ht:HAS_TERM]->(:CTCodelistTerm)
        WHERE ht.end_date IS NULL
        WITH clr, collect(ht.ordinal) AS ordinals
        WHERE all(o IN ordinals WHERE o IS NULL)
        WITH COLLECT(DISTINCT clr.uid) AS all_clr_uids,
             COLLECT(clr) AS clr_list
        UNWIND clr_list AS clr
        {build_root_summary_return_statement('clr', extra_return=[('all_clr_uids', 'clr_uids')])}
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
    ), f"Number of ordinal codelists with no term defining an ordinal value: {cnt}, codelists: {result.get('clr_uids', [])}"
