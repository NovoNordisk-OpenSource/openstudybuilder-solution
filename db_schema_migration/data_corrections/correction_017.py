"""PRD Data Corrections: Before Release 2.6"""

import os

from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    print_counters_table,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import api_delete, api_get, api_post, get_logger
from verifications import correction_verification_017

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-release-2.5"


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    remove_duplicated_non_visit_and_unscheduled_visits(DB_DRIVER, LOGGER, run_label)
    fix_duplicated_unique_visit_numbers_and_incorrect_visit_number_visit_name_and_short_name(
        DB_DRIVER, LOGGER, run_label
    )
    rebuild_missing_protocol_soa_snapshots(DB_DRIVER, LOGGER, run_label)
    remove_soa_cell_relationships_without_released_study(DB_DRIVER, LOGGER, run_label)
    remove_study_action_with_broken_after(DB_DRIVER, LOGGER, run_label)
    # fix_studies_different_versions_with_the_same_start_date(
    #     DB_DRIVER, LOGGER, run_label
    # )


@capture_changes(
    verify_func=correction_verification_017.test_remove_duplicated_non_visit_and_unscheduled_visits
)
def remove_duplicated_non_visit_and_unscheduled_visits(db_driver, log, run_label):
    """
    ### Problem description
    There should only exist one Non-visit and Unscheduled-visit in a given Study.
    There was an API issue that when both Non-visit and Unscheduled-visit existed in given Study and we were editing
    Non-visit to be Unscheduled-visit or vice versa, the API allowed to created duplicated Non or Unscheduled visit by edition.
    ### Change description
    - Delete duplicated Non-visit or Unscheduled-visit in the Study.
    ### Nodes and relationships affected
    - `StudyVisit` node
    ### Expected changes: 1 call for DELETE /study-visits/{StudyVisit_000196} to delete duplicated non-visit.
    """
    contains_updates = []
    query = """
        MATCH (sr:StudyRoot)--(sv:StudyValue)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit)
        WHERE NOT (study_visit)-[:BEFORE]-() AND study_visit.visit_class = "NON_VISIT"
        WITH DISTINCT sr, collect(distinct study_visit.uid) as study_visit_uids
        WHERE size(study_visit_uids) > 1
        RETURN sr.uid as study_uid, study_visit_uids
    """
    results, _ = run_cypher_query(db_driver, query)
    for result in results:
        study_uid = result[0]
        non_visit_uids = result[1]
        log.info(
            f"Run: {run_label}, Removing duplicated Non visits in Study {study_uid}"
        )
        for non_visit_uid in non_visit_uids[1:]:
            response = api_delete(f"/studies/{study_uid}/study-visits/{non_visit_uid}")
            contains_updates.append(response)
    query = """
        MATCH (sr:StudyRoot)--(sv:StudyValue)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit)
        WHERE NOT (study_visit)-[:BEFORE]-() AND study_visit.visit_class = "UNSCHEDULED_VISIT"
        WITH DISTINCT sr, collect(distinct study_visit.uid) as study_visit_uids
        WHERE size(study_visit_uids) > 1
        RETURN sr.uid as study_uid, study_visit_uids
    """
    results, _ = run_cypher_query(db_driver, query)
    for result in results:
        study_uid = result[0]
        unscheduled_visit_uids = result[1]
        log.info(
            f"Run: {run_label}, Removing duplicated Unscheduled visits in Study {study_uid}"
        )
        for unscheduled_visit_uid in unscheduled_visit_uids[1:]:
            response = api_delete(
                f"/studies/{study_uid}/study-visits/{unscheduled_visit_uid}"
            )
            contains_updates.append(response)
    return any(contains_updates)


@capture_changes(
    verify_func=correction_verification_017.test_fix_duplicated_unique_visit_numbers_and_incorrect_visit_number_visit_name_and_short_name
)
def fix_duplicated_unique_visit_numbers_and_incorrect_visit_number_visit_name_and_short_name(
    db_driver, log, run_label
):
    """
    ### Problem description
    There exists an issue that some different StudyVisits share the same unique visit number.
    It should not be the case as unique visit number should be a unique value across all StudyVisits within a Study.
    The issue existed only for groups of subvisits when the anchor visit timing was edited and it was not properly updated.
    ### Change description
    - Update unique visit number and other properties (visit_name, short_visit_label, visit_number) for StudyVisits having wrong values
    - Correct values are taken from API that calculates them based on the StudyVisit full schedule.
    ### Nodes and relationships affected
    - `StudyVisit` node
    ### Expected changes: 2 StudyVisits (StudyVisit_004596, StudyVisit_009676) updated by correcting (visit_number, unique_visit_number, short_visit_label) properties and relationship to dependent visit_name node
    """
    contains_updates = []
    query = """
    MATCH (sr:StudyRoot)--(sv:StudyValue)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit)
    WHERE NOT (study_visit)-[:BEFORE]-()
    WITH DISTINCT sr, study_visit.unique_visit_number as unique_visit_number, collect(distinct study_visit.uid) as study_visit_uids
    WHERE size(study_visit_uids) > 1
    RETURN sr.uid as study_uid, study_visit_uids, unique_visit_number
    """
    results, _ = run_cypher_query(db_driver, query)
    for result in results:
        study_uid = result[0]
        study_visit_uids = result[1]
        unique_visit_number = result[2]
        for study_visit_uid in study_visit_uids:
            study_visit = api_get(
                f"/studies/{study_uid}/study-visits/{study_visit_uid}",
                params={"derive_props_based_on_timeline": True},
            ).json()
            correct_study_visit_number = study_visit["unique_visit_number"]
            correct_short_visit_label = study_visit["visit_short_name"]
            correct_visit_number = study_visit["visit_number"]
            correct_visit_name = study_visit["visit_name"]
            if correct_study_visit_number != int(unique_visit_number):
                visit_name, _ = run_cypher_query(
                    db_driver,
                    """
                MATCH (visit_name_root:VisitNameRoot)-[:LATEST]->(visit_name_value:VisitNameValue {name: $value})
                RETURN visit_name_root.uid
                """,
                    params={
                        "value": correct_visit_name,
                    },
                )
                if visit_name:
                    visit_name_uid = visit_name[0][0]
                else:
                    visit_name_uid = api_post(
                        "/concepts/visit-names",
                        payload={
                            "name": correct_visit_name,
                            "template_parameter": True,
                            "library_name": "Sponsor",
                        },
                    ).json()["uid"]
                log.info(
                    f"Run: {run_label}, Modifying unique visit number for {study_visit_uid} from {unique_visit_number} to {correct_study_visit_number}"
                )
                query = """
                    MATCH (study_visit:StudyVisit {uid: $study_visit_uid})-[existing_visit_name_rel:HAS_VISIT_NAME]->(visit_name_root:VisitNameRoot)
                    WHERE NOT (study_visit)-[:BEFORE]-()
                    SET study_visit.unique_visit_number = $unique_visit_number
                    SET study_visit.short_visit_label = $short_visit_label
                    SET study_visit.visit_number = $visit_number
                    WITH study_visit, existing_visit_name_rel
                    MATCH (new_visit_name_root:VisitNameRoot {uid: $visit_name_uid})
                    CREATE (study_visit)-[:HAS_VISIT_NAME]->(new_visit_name_root)
                    DETACH DELETE existing_visit_name_rel
                    """
                _, summary = run_cypher_query(
                    db_driver,
                    query,
                    params={
                        "study_visit_uid": study_visit_uid,
                        "unique_visit_number": correct_study_visit_number,
                        "short_visit_label": correct_short_visit_label,
                        "visit_number": correct_visit_number,
                        "visit_name_uid": visit_name_uid,
                    },
                )
                counters = summary.counters
                print_counters_table(counters)
                contains_updates.append(counters.contains_updates)
    return any(contains_updates)


@capture_changes(
    verify_func=correction_verification_017.test_protocol_soa_response_status_code
)
def rebuild_missing_protocol_soa_snapshots(db_driver, log, run_label):
    """
    ### Problem description
    Some (RELEASED) Study versions do not have a Protocol SoA snapshot created due to a (fixed) bug.
    ### Change description
    - Rebuild missing/failing Protocol SoA snapshots for RELEASED Study versions, using contemporary StudySelections but latest ordering.
    ### Relationships affected
    - (StudyValue)-[:HAS_PROTOCOL_SOA_CELL]->(StudySelection)
    - (StudyValue)-[:HAS_PROTOCOL_SOA_FOOTNOTE]->(StudySelection)
    ### Expected changes
    - Old relationships removed
    - New relationships created
    """

    # Find all RELEASED Study versions of all Studies
    results, _ = run_cypher_query(
        db_driver,
        """
        MATCH (study_root:StudyRoot)-[study_version:HAS_VERSION {status: 'RELEASED'}]->(study_value:StudyValue)
        RETURN study_root.uid, study_version.version
        """,
    )

    # For all Studies and their RELEASED versions
    for result in results:
        study_uid, study_version = result

        # Check API endpoint returns Protocol SoA Snapshot
        log.info(
            "Run: %s, Checking Protocol SoA Snapshot for Study '%s' Version '%s'",
            run_label,
            study_uid,
            study_version,
        )
        response = api_get(
            f"/studies/{study_uid}/flowchart/snapshot",
            params={"study_value_version": study_version, "layout": "protocol"},
            check_ok_status=False,
        )
        log.info(
            "Run: %s, Protocol SoA Snapshot response status code %i for Study '%s' Version '%s'",
            run_label,
            response.status_code,
            study_uid,
            study_version,
        )

        if response.status_code != 200:
            # Rebuild Protocol SoA Snapshot
            log.info(
                "Run: %s, Rebuilding Protocol SoA Snapshot for Study '%s' Version '%s'",
                run_label,
                study_uid,
                study_version,
            )
            response = api_post(
                f"/studies/{study_uid}/flowchart/snapshot",
                payload={},
                params={"study_value_version": study_version, "layout": "protocol"},
            )


@capture_changes(
    verify_func=correction_verification_017.test_remove_study_action_with_broken_after
)
def remove_study_action_with_broken_after(db_driver, log, run_label):
    """
    ### Problem description
    Some StudyAction nodes exist without AFTER relationships. These are leftover from migrated study selections
    where the StudySelection nodes were deleted but the StudyAction nodes remained. Every StudyAction (except
    UpdateSoASnapshot) must have an AFTER relationship.
    ### Change description
    - Delete StudyAction nodes that don't have AFTER relationships (excluding UpdateSoASnapshot nodes).
    ### Nodes and relationships affected
    - `StudyAction` nodes
    """
    log.info(
        f"Run: {run_label}, Removing StudyAction nodes without AFTER relationships"
    )

    query = """
        MATCH (sr:StudyRoot)-[:AUDIT_TRAIL]->(sa:StudyAction)
        WHERE 
            NOT (sa)-[:AFTER]->()
            AND NOT sa:Delete
            AND NOT (sa)-[:BEFORE]->(:StudyValue)
            AND NOT sa:UpdateSoASnapshot
        DETACH DELETE sa
    """

    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


# Commented out for this batch. This will have to be updated, adjusting only start_date can create new gaps in the version history
# @capture_changes(
#     verify_func=correction_verification_017.test_fix_studies_different_versions_with_the_same_start_date
# )
# def fix_studies_different_versions_with_the_same_start_date(db_driver, log, run_label):
#     """
#     ### Problem description
#     Some StudyRoot nodes have different versions with the same start_date, which violates
#     the constraint that no version should have a start_date greater than or equal to the
#     latest version's start_date. This happens when a previous version has the same start_date
#     as the latest version.
#     ### Change description
#     - For each StudyRoot, find versions with start_date >= the latest version's start_date
#     - Subtract 1 millisecond from those previous versions' start_date to make them earlier
#     - This ensures proper chronological ordering of versions
#     ### Nodes and relationships affected
#     - `HAS_VERSION` relationships for StudyRoot nodes
#     """
#     log.info(
#         f"Run: {run_label}, Fixing studies with different versions having the same start_date"
#     )
#
#     # Find StudyRoot nodes where a previous version has start_date >= latest version's start_date
#     # Subtract 1 millisecond from the previous version's start_date
#     query = """
#         MATCH (root:StudyRoot)-[:LATEST]->(latest)
#         MATCH (root)-[v_latest:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_LOCKED|LATEST_RETIRED|LATEST_RELEASED]->(latest)
#         WITH root, latest, v_latest.start_date as latest_start_date
#         MATCH (root)-[v_prev:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_LOCKED|LATEST_RETIRED|LATEST_RELEASED]->(prev_value)
#         WHERE prev_value <> latest
#           AND v_prev.start_date >= latest_start_date
#           AND v_prev.start_date IS NOT NULL
#         SET v_prev.start_date = v_prev.start_date - duration({milliseconds: 1})
#         RETURN count(v_prev) AS updated_count
#     """
#
#     _, summary = run_cypher_query(db_driver, query)
#     counters = summary.counters
#     print_counters_table(counters)
#     return counters.contains_updates


@capture_changes(
    verify_func=correction_verification_017.test_remove_soa_cell_relationships_without_released_study
)
def remove_soa_cell_relationships_without_released_study(db_driver, log, run_label):
    """
    ### Problem description
    Some StudyValue nodes have HAS_PROTOCOL_SOA_CELL or HAS_PROTOCOL_SOA_FOOTNOTE relationships
    when the StudyRoot doesn't have a RELEASED or LOCKED version. These relationships were created
    as a result of bad cloning and should not exist without a released or locked version.
    ### Change description
    - Delete HAS_PROTOCOL_SOA_CELL and HAS_PROTOCOL_SOA_FOOTNOTE relationships from StudyValue nodes
      where the StudyRoot doesn't have a RELEASED or LOCKED version
    ### Nodes and relationships affected
    - `HAS_PROTOCOL_SOA_CELL` relationships
    - `HAS_PROTOCOL_SOA_FOOTNOTE` relationships
    """
    log.info(
        f"Run: {run_label}, Removing SOA cell/footnote relationships from studies without RELEASED or LOCKED versions"
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
        DELETE sv_ss
        RETURN count(sv_ss) AS deleted_count
    """

    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


if __name__ == "__main__":
    main()
