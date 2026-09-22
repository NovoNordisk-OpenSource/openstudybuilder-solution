"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import os

from data_corrections.utils.utils import get_db_driver, run_cypher_query
from migrations.utils.utils import api_get, get_logger

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()


def test_remove_duplicated_non_visit_and_unscheduled_visits():
    LOGGER.info(
        "Checking for duplicated Non visits or Unscheduled visits",
    )
    query = """
            MATCH (sr:StudyRoot)--(sv:StudyValue)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit)
            WHERE NOT (study_visit)-[:BEFORE]-() AND study_visit.visit_class = "NON_VISIT"
            WITH DISTINCT sr, collect(distinct study_visit.uid) as study_visit_uids
            WHERE size(study_visit_uids) > 1
            RETURN sr.uid as study_uid, study_visit_uids
    """
    res, _ = run_cypher_query(DB_DRIVER, query)
    assert len(res) == 0, f"Found more than one Non visit, res:{res}"

    query = """
            MATCH (sr:StudyRoot)--(sv:StudyValue)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit)
            WHERE NOT (study_visit)-[:BEFORE]-() AND study_visit.visit_class = "UNSCHEDULED_VISIT"
            WITH DISTINCT sr, collect(distinct study_visit.uid) as study_visit_uids
            WHERE size(study_visit_uids) > 1
            RETURN sr.uid as study_uid, study_visit_uids
    """
    res, _ = run_cypher_query(DB_DRIVER, query)
    assert len(res) == 0, f"Found more than one Unscheduled visit, res:{res}"


def test_fix_duplicated_unique_visit_numbers_and_incorrect_visit_number_visit_name_and_short_name():
    LOGGER.info(
        "Verifying that StudyVisits unique visit numbers are unique",
    )
    query = """
        MATCH (sr:StudyRoot)--(sv:StudyValue)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit)
            WHERE NOT (study_visit)-[:BEFORE]-()
        WITH DISTINCT sr, study_visit.unique_visit_number as unique_visit_number, collect(distinct study_visit.uid) as study_visit_uids
        WHERE size(study_visit_uids) > 1
        RETURN sr.uid as study_uid, study_visit_uids, unique_visit_number
    """
    res, _ = run_cypher_query(DB_DRIVER, query)
    assert len(res) == 0, f"Found duplicated unique visit number, res:{res}"


def test_protocol_soa_response_status_code():
    """Verify that Protocol SoA API endpoint returns HTTP 200 status code for all released versions of all Studies."""

    # Find all released Study versions of all Studies
    results, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (study_root:StudyRoot)-[study_version:HAS_VERSION {status: 'RELEASED'}]->(study_value:StudyValue)
        RETURN study_root.uid, study_version.version, exists((study_value)-[:HAS_STUDY_ACTIVITY]->()) AS has_activities
        """,
    )

    # For all Studies and their versions
    failed = []
    for result in results:
        study_uid, study_version, has_activities = result

        # Check API endpoint returns Protocol SoA
        LOGGER.info(
            "Checking Protocol SoA for Study '%s' Version '%s'",
            study_uid,
            study_version,
        )
        response = api_get(
            f"/studies/{study_uid}/flowchart",
            params={"study_value_version": study_version, "layout": "protocol"},
            check_ok_status=False,
        )

        if response.status_code == 404 and not has_activities:
            # No activities in this Study version, SoA not expected
            LOGGER.info(
                "Study '%s' Version '%s' has no activities, Protocol SoA returned 404, it's OK.",
                study_uid,
                study_version,
            )
        elif response.status_code != 200:
            failed.append(
                f"Study '{study_uid}' Version '{study_version}' {response.request.method} {response.request.url} : {response.status_code} {response.reason} {response.text[:1024]}"
            )
    failed_items = "\n".join(failed)
    assert len(failed) == 0, f"Some Protocol SoA API calls failed: {failed_items}"


def test_remove_study_action_with_broken_after():
    """
    Verify that there are no StudyAction nodes without AFTER relationships.
    StudyAction nodes (except UpdateSoASnapshot) must have an AFTER relationship.
    The check excludes any StudyArrayField with field_name "soa_split_uids" as they
    are not in the scope of the current correction.
    """
    LOGGER.info("Checking for StudyAction nodes without AFTER relationships")
    query = """
        MATCH (sr:StudyRoot)-[:AUDIT_TRAIL]->(sa:StudyAction)
        WHERE 
            NOT (sa)-[:AFTER]->()
            AND NOT sa:UpdateSoASnapshot
            AND NOT (sa)-[:BEFORE]->(:StudyValue)
            AND NOT (sa)-[:BEFORE]->(:StudyArrayField {field_name: "soa_split_uids"})
        RETURN count(sa) AS broken_count
    """
    res, _ = run_cypher_query(DB_DRIVER, query)
    broken_count = res[0][0] if res else 0
    assert (
        broken_count == 0
    ), f"Found {broken_count} StudyAction nodes without AFTER relationships"


# def test_fix_studies_different_versions_with_the_same_start_date():
#     """
#     Verify that no StudyRoot has different versions with the same start_date.
#     The latest version should have a start_date that is greater than all previous versions.
#     """
#     LOGGER.info(
#         "Checking for studies with different versions having the same start_date"
#     )
#     query = """
#         MATCH (root:StudyRoot)-[:LATEST]->(latest)
#         MATCH (root)-[v_latest:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_LOCKED|LATEST_RETIRED|LATEST_RELEASED]->(latest)
#         WITH root, latest, v_latest.start_date as latest_start_date
#         MATCH (root)-[v_prev:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_LOCKED|LATEST_RETIRED|LATEST_RELEASED]->(prev_value)
#         WHERE prev_value <> latest
#           AND v_prev.start_date >= latest_start_date
#           AND v_prev.start_date IS NOT NULL
#         RETURN count(DISTINCT root) AS broken_count
#     """
#     res, _ = run_cypher_query(DB_DRIVER, query)
#     broken_count = res[0][0] if res else 0
#     assert (
#         broken_count == 0
#     ), f"Found {broken_count} studies with different versions having the same or greater start_date compared to the latest version"


def test_remove_soa_cell_relationships_without_released_study():
    """
    Verify that no StudyValue nodes have HAS_PROTOCOL_SOA_CELL or HAS_PROTOCOL_SOA_FOOTNOTE
    relationships when the StudyRoot doesn't have a RELEASED or LOCKED version.
    """
    LOGGER.info(
        "Checking for SOA cell/footnote relationships in studies without RELEASED or LOCKED versions"
    )
    query = """
        MATCH 
            (sv:StudyValue)-[sv_ss]-(ss:StudySelection) 
        WHERE 
            TYPE(sv_ss)='HAS_PROTOCOL_SOA_CELL' 
            OR TYPE(sv_ss)='HAS_PROTOCOL_SOA_FOOTNOTE'
        MATCH 
            (sv)-[versioning:HAS_VERSION]-(sr:StudyRoot)
        WHERE NOT EXISTS(
            (sr)-[:HAS_VERSION {status:'RELEASED'}]->()
        )
        AND NOT EXISTS(
            (sr)-[:HAS_VERSION {status:'LOCKED'}]->()
        )
        RETURN count(DISTINCT sv_ss) AS broken_count
    """
    res, _ = run_cypher_query(DB_DRIVER, query)
    broken_count = res[0][0] if res else 0
    assert (
        broken_count == 0
    ), f"Found {broken_count} SOA cell/footnote relationships in studies without RELEASED or LOCKED versions"
