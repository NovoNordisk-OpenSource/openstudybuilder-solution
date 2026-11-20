"""
This module verifies that every CDISC staging node carries the `:CDISCStaging`
marker label, which is what will let the staging and MDR halves of the database
share one Neo4j database without one being visible to the other's role.

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
import os

from pytest_bdd import scenarios, then

from utils.utils import (
    REPORT_FILE_PATH,
    execute_query_and_append_result_to_file,
    get_db_connection,
    get_excluded_node_ids,
    get_gherkin_tags,
    get_logger,
    get_name_and_doc,
)

scenarios("general/staging_isolation.feature")

db = get_db_connection()
logger = get_logger(os.path.basename(__file__))

# Every label a staging write path is known to create. A write that forgot the
# `:CDISCStaging` marker on one of these would be invisible to this check
# otherwise, and would silently leak into MDR's unfiltered view once the
# staging and MDR databases merge.
STAGING_LABELS = [
    "RawPackage",
    "RawCatalogue",
    "RawCodelist",
    "RawTerm",
    "GroupedCodelist",
    "GroupedTerm",
    "GroupedCodelistProperties",
    "GroupedTermProperties",
    "Inconsistency",
    "CandidateValue",
    "ResolutionDecision",
    "ResolutionRule",
    "CataloguePriority",
    "SemanticAnswer",
    "StagedFile",
    "StagedPairing",
    "EffectiveDateImport",
    "StagingJob",
    "JobRunLock",
    "VersionedCodelist",
    "VersionedTerm",
    "ChangelogEntry",
    "KnownRelease",
    "CodelistReview",
    "CodelistVersion",
    "TermVersion",
    "InconsistentCodelistTerms",
    "InconsistentTermProperties",
    "InconsistentCodelistProperties",
    "InconsistencySolution",
    "SponsorName",
    "DataModelImport",
    "DataModelClass",
    "DataModelVariable",
    "DataModelScenario",
    "DataModelStagingVersion",
    "TermChange",
    "ImportSettings",
]


@then("every node with a known staging label also has the CDISCStaging label")
def staging_nodes_carry_the_marker_label(request, prepare_report_file):
    """Every node with a known staging label also carries :CDISCStaging"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        // Every node with a known staging label must also carry :CDISCStaging
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label IN {STAGING_LABELS})
          AND NOT n:CDISCStaging
        RETURN
            count(n) as noncompliant_entity_cnt,
            apoc.coll.toSet(apoc.coll.flatten(collect(labels(n)))) as noncompliant_labels,
            collect(elementId(n)) as noncompliant_node_ids
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
    ), f"Number of staging-labelled nodes missing :CDISCStaging: {cnt}, labels: {result.get('noncompliant_labels', [])}"


@then("no node without a known staging label has the CDISCStaging label")
def cdiscstaging_nodes_carry_a_known_label(request, prepare_report_file):
    """No node without a known staging label carries :CDISCStaging"""

    check_id, check_description = get_name_and_doc()
    tags = get_gherkin_tags(request)
    excluded_node_ids = get_excluded_node_ids(check_id)

    query = f"""
        // Every node carrying :CDISCStaging must also have a known staging label
        MATCH (n:CDISCStaging)
        WHERE NOT any(label IN labels(n) WHERE label IN {STAGING_LABELS})
        RETURN
            count(n) as noncompliant_entity_cnt,
            apoc.coll.toSet(apoc.coll.flatten(collect(labels(n)))) as noncompliant_labels,
            collect(elementId(n)) as noncompliant_node_ids
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
    ), f"Number of :CDISCStaging nodes without a known staging label: {cnt}, labels: {result.get('noncompliant_labels', [])}"
