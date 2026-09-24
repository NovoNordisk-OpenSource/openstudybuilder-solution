"""PRD Data Corrections: Before Release 2.4"""

import os

from data_corrections.utils import common
from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import get_logger
from verifications import correction_verification_016

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-batch-016"


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    fix_activity_000317_versioning_gap(DB_DRIVER, LOGGER, run_label)
    remove_cat_submission_value_suffix(DB_DRIVER, LOGGER, run_label)
    add_missing_retired_relationships(DB_DRIVER, LOGGER, run_label)
    solve_duplicate_term_submission_values(DB_DRIVER, LOGGER, run_label)
    solve_duplicate_term_names(DB_DRIVER, LOGGER, run_label)
    solve_negative_duration_has_term(DB_DRIVER, LOGGER, run_label)
    solve_not_latest_has_version_lacks_end_date(DB_DRIVER, LOGGER, run_label)
    remove_isolated_orphan_nodes(DB_DRIVER, LOGGER, run_label)
    remove_orphan_study_selection_nodes(DB_DRIVER, LOGGER, run_label)


@capture_changes(
    verify_func=correction_verification_016.test_activity_000317_versioning_gap
)
def fix_activity_000317_versioning_gap(db_driver, log, run_label):
    """
    ## Fix Activity_000317 versioning gap (Bug #3221548)

    ### Problem description
    Activity_000317 has a 36-day chronological gap in its HAS_VERSION relationships
    between version 7.0 and version 7.1. Version 7.0 ends on 2024-11-14T15:20:11.139020Z
    but version 7.1 doesn't start until 2024-12-20T12:41:58.289320Z, creating a gap
    from November 14 to December 20, 2024. This violates the rule that versions should
    be chronologically continuous without gaps.

    ### Change description
    - Extend the end_date of version 7.0's HAS_VERSION relationship from
      2024-11-14T15:20:11.139020Z to 2024-12-20T12:41:58.289320Z
    - This ensures continuous versioning between version 7.0 and 7.1
    - The correction is idempotent and can be run multiple times safely

    ### Nodes and relationships affected
    - `HAS_VERSION` relationship for Activity_000317 version 7.0
    - Expected changes: 1 relationship property modified
    """

    desc = "Fix Activity_000317 versioning gap between version 7.0 and 7.1"
    log.info(f"Run: {run_label}, {desc}")

    # Query to fix the versioning gap by extending version 7.0 end_date to version 7.1 start_date
    query = """
        MATCH (ar:ActivityRoot {uid: "Activity_000317"})
        MATCH (ar)-[hv1:HAS_VERSION {version: "7.0"}]->(av1:ActivityValue)
        MATCH (ar)-[hv2:HAS_VERSION {version: "7.1"}]->(av2:ActivityValue)
        WHERE hv1.end_date IS NOT NULL
            AND hv2.start_date IS NOT NULL
            AND hv1.end_date < hv2.start_date  // Only update if there's a gap
        SET hv1.end_date = hv2.start_date
        RETURN
            ar.uid AS activity_uid,
            hv1.version AS updated_version,
            hv1.end_date AS new_end_date,
            hv2.start_date AS v7_1_start_date
    """

    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    return counters.contains_updates


@capture_changes(
    verify_func=correction_verification_016.test_remove_cat_submission_value_suffix
)
def remove_cat_submission_value_suffix(db_driver, log, run_label):
    """
    ## Remove the "nnnn_CAT" and "nnnn_SUB_CAT" suffixes from submission values in category codelists

    ### Problem description
    In StudyBuilder before 2.0, submision values had to be globaly unique.
    To achieve this, a suffix, "nnnn_CAT" or "nnnn_SUB_CAT", was appended to submission values in category codelists.
    With StudyBuilder 2.0, submission values only need to be unique within their codelist,
    so this suffix is no longer necessary and should be removed.
    This corretion needs to be applied in the
    EVNTCAT, EVNTSCAT, FINDCAT, FINDSCAT, INTVCAT and INTVSCAT codelists.

    ### Change description
    - Remove the "nnnn_CAT" and "nnnn_SUB_CAT" suffixes from the `submission_value` property of `CTCodelistTerm` nodes

    ### Nodes and relationships affected
    - `CTCodelistTerm` nodes in the EVNTCAT, EVNTSCAT, FINDCAT, FINDSCAT, INTVCAT and INTVSCAT codelists
    - Expected changes: 872 node properties modified
    """

    desc = "Remove the nnnn_CAT and nnnn_SUB_CAT suffixes from submission values in category codelists"
    log.info(f"Run: {run_label}, {desc}")

    query = """
        MATCH (clr:CTCodelistRoot)-[har:HAS_ATTRIBUTES_ROOT]-(clar:CTCodelistAttributesRoot)-[clalat:LATEST]-(clav:CTCodelistAttributesValue)
        WHERE clav.submission_value IN ["EVNTCAT", "EVNTSCAT", "FINDCAT", "FINDSCAT", "INTVCAT", "INTVSCAT"]
        CALL {
            WITH clr
            MATCH (clr)-[:HAS_TERM]->(clt:CTCodelistTerm)
            WHERE clt.submission_value ENDS WITH "_CAT"
            WITH clt, clt.submission_value AS submval
            WITH clt, replace(submval, " FIND_SUB_CAT", "") AS submval
            WITH clt, replace(submval, " FIND_CAT", "") AS submval
            WITH clt, replace(submval, " INTRV_SUB_CAT", "") AS submval
            WITH clt, replace(submval, " INTRV_CAT", "") AS submval
            WITH clt, replace(submval, " EVNT_SUB_CAT", "") AS submval
            WITH clt, replace(submval, " EVNT_CAT", "") AS submval
            SET clt.submission_value = trim(submval)
        }
        RETURN *
    """

    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    return counters.contains_updates


@capture_changes(
    verify_func=correction_verification_016.test_missing_retired_relationships
)
def add_missing_retired_relationships(db_driver, log, run_label):
    """
    ## Insert a Final HAS_VERSION relationship for Retired library items where the only HAS_VERSION relationship is Retired

    ### Problem description
    In an earlier version of the StdyBuilder API, retiring an item would create a new value node
    linked by a HAS_VERSION relationship with status "Retired".
    It should only have added a new HAS_VERSION relationship with status "Retired" to an the existing latest value node.
    As a result, some value nodes are linked to their root nodes only by a HAS_VERSION relationship with status "Retired",
    without a corresponding "Final" or "Draft" HAS_VERSION relationship.
    This correction inserts a short lived "Final" HAS_VERSION relationship to such value nodes.

    ### Change description
    - Insert a short lived "Final" HAS_VERSION relationship to value nodes that only have a "Retired" HAS_VERSION relationship

    ### Nodes and relationships affected
    - `ActivityRoot`, `ActivityValue`, `ActivityInstanceRoot`, `ActivityInstanceValue` nodes
    - `HAS_VERSION`, `LATEST_FINAL` relationships
    - Expected changes: 18 new relationships created, 9 relationships deleted, 9 relationship properties modified

    """

    desc = "Add missing Final HAS_VERSION relationships for Retired library items"
    log.info(f"Run: {run_label}, {desc}")

    query = """
        MATCH (root)-[ret:HAS_VERSION {status: "Retired"}]->(value)
        WHERE NOT (root)-[:HAS_VERSION {status: "Final"}]->(value) AND NOT (root)-[:HAS_VERSION {status: "Draft"}]->(value)
        WITH root, value, ret, ret.start_date + duration({seconds: 1}) AS adjusted_date
        CREATE (root)-[final:HAS_VERSION {
            version: ret.version,
            status: "Final",
            start_date: ret.start_date,
            end_date: adjusted_date,
            author_id: ret.author_id,
            change_description: ret.change_description
        }]->(value)
        SET ret.start_date = adjusted_date
        WITH root, value
        CALL {
            WITH root, value
            MATCH (root)-[latest_ret:HAS_VERSION {status: "Retired"}]->(value)
            WHERE latest_ret.end_date IS NULL
            MATCH (root)-[lf:LATEST_FINAL]->()
            CREATE (root)-[new_lf:LATEST_FINAL]->(value)
            DELETE lf
        }
    """

    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    return counters.contains_updates


@capture_changes(
    verify_func=correction_verification_016.test_duplicate_term_submission_values
)
def solve_duplicate_term_submission_values(db_driver, log, run_label):
    """
    ## Remove duplicate submission values within codelists

    ### Problem description
    In the Unit codelist, there are four pairs of terms that share the same submission value.
    This violates the uniqueness constraint for submission values within a codelist.
    The duplicates are:
    - "Arbitrary U/mL"
    - "mL/min/1.73 m2"
    - "Therapeutic Cells"
    - "ms"
    These issues were created when the latest CDISC packages were imported,
    which included some new terms that previously were added as sponsor-defined terms.

    ### Change description
    - Remove the sponsor defined terms for "mL/min/1.73 m2", "Therapeutic Cells" and "ms",
      and move any links to these terms to the corresponding CDISC-defined terms.
    - For "Arbitrary U/mL", the Sponsor term existed before the CDISC term.
      In this case, set an end date on the HAS_TERM relationship for the sponsor term
      to the start date of the CDISC term's HAS_TERM relationship.
      Move any links to the sponsir term that were created after the start date on the CDSIC term
      over to the CDISC term.

    ### Nodes and relationships affected
    - `CTTermRoot`. `CTCodelistTerm`, `CTTermNameValue`, `CTTermNameRoot`, `CTTermAttributesRoot`, `CTTermAttributesValue` nodes
    - `HAS_TERM`, `HAS_NAME_ROOT`, `HAS_VERSION`, `LATEST_FINAL` relationships
    - Expected changes:
        - 18 nodes deleted
        - 45 relationships deleted
        - 1 relationship property modified
    """

    desc = "Handle duplicated submission values within Unit codelist"
    log.info(f"Run: {run_label}, {desc}")

    contains_updates = False

    codelist_uid = common.find_codelist_uid(db_driver, name="Unit")
    if codelist_uid is None:
        log.warning("Could not find UID for 'Unit' codelist")
        return contains_updates

    # Delete the redundant sponsor-defined term and move relationships to the CDISC-defined term
    for submval in ["mL/min/1.73 m2", "Therapeutic Cells", "ms"]:
        bad_term_uid = common.find_term_uid(
            db_driver,
            submission_value=submval,
            codelist_uid=codelist_uid,
            library="Sponsor",
        )
        good_term_uid = common.find_term_uid(
            db_driver,
            submission_value=submval,
            codelist_uid=codelist_uid,
            library="CDISC",
        )
        if bad_term_uid is None or good_term_uid is None:
            log.info(f"Could not find UIDs for terms with submission value '{submval}'")
            continue
        query, params = common.replace_term_by_deleting_query(
            bad_term_uid, good_term_uid
        )
        _, summary = run_cypher_query(db_driver, query, params)
        counters = summary.counters
        contains_updates = contains_updates or counters.contains_updates

    # Adjust end date of the replaced 'Arbitrary U/mL' sponsor defined term
    bad_term_uid = common.find_term_uid(
        db_driver,
        submission_value="Arbitrary U/mL",
        codelist_uid=codelist_uid,
        library="Sponsor",
    )
    good_term_uid = common.find_term_uid(
        db_driver,
        submission_value="Arbitrary U/mL",
        codelist_uid=codelist_uid,
        library="CDISC",
    )
    if bad_term_uid is None or good_term_uid is None:
        log.info("Could not find UIDs for terms with submission value 'Arbitrary U/mL'")
        return contains_updates
    query, params = common.replace_term_by_updating_dates_query(
        bad_term_uid, good_term_uid, codelist_uid
    )
    _, summary = run_cypher_query(db_driver, query, params)
    counters = summary.counters
    contains_updates = contains_updates or counters.contains_updates
    # Update links from Unit Definitions to point to the CDISC-defined term
    query = """
        MATCH (bad_tr:CTTermRoot {uid: $bad_term_uid})<-[:HAS_TERM_ROOT]-(:CTCodelistTerm)<-[:HAS_TERM]-(clr:CTCodelistRoot {uid: $codelist_uid})
        MATCH (clr)-[:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(good_tr:CTTermRoot {uid: $good_term_uid})
        MATCH (udr:UnitDefinitionRoot)-[:LATEST]->(udv:UnitDefinitionValue)-[hctu:HAS_CT_UNIT]->(ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(bad_tr)
        MERGE (clr)<-[:HAS_SELECTED_CODELIST]-(new_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(good_tr)
        MERGE (udv)-[new_hctu:HAS_CT_UNIT]->(new_ctx)
        DELETE hctu
    """
    params = {
        "bad_term_uid": bad_term_uid,
        "good_term_uid": good_term_uid,
        "codelist_uid": codelist_uid,
    }
    _, summary = run_cypher_query(db_driver, query, params)
    counters = summary.counters
    contains_updates = contains_updates or counters.contains_updates

    return contains_updates


@capture_changes(verify_func=correction_verification_016.test_duplicate_term_names)
def solve_duplicate_term_names(db_driver, log, run_label):
    """
    ## Remove duplicate term names within codelists

    ### Problem description
    There are three codelists that contain terms with duplicate names.
    This violates the uniqueness constraint for term names within a codelist.
    The duplicates are:
    - "Score" in the Unit Dimension codelist
    - "Direct Glomerular Filtration Rate from Beta-Trace Protein Adjusted for Standard BSA Measurement"
      in the "Laboratory Test Name" and "Laboratory Test Code" codelists
    These duplicated "Score"was created when the latest CDISC packages were imported,
    which included a new CDISC "Score" term.
    The duplicated "Direct Glomerular Filtration Rate from Beta-Trace Protein Adjusted for Standard BSA Measurement"
    is a mistake in the package data from CDISC where one of the terms should have had a different name.

    ### Change description
    - Remove the sponsor defined term for "Score",
      and move any links to this terms to the corresponding CDISC-defined term.
    - Change the name property on the CTTermNameValue node for the term with concept id C100450 to
     "Direct Glomerular Filtration Rate from Beta-2 Microglobulin Adjusted for Standard BSA Measurement"

    ### Nodes and relationships affected
    - `CTTermRoot`. `CTCodelistTerm`, `CTTermNameValue`, `CTTermNameRoot`, `CTTermAttributesRoot`, `CTTermAttributesValue` nodes
    - `HAS_TERM`, `HAS_NAME_ROOT`, `HAS_VERSION`, `LATEST_FINAL` relationships
    - Expected changes:
        - 6 node deleted
        - 15 relationships deleted
        - 2 node properties modified
    """

    contains_updates = False
    desc = "Handle duplicated term names within codelists"
    log.info(f"Run: {run_label}, {desc}")
    # Delete the redundant sponsor-defined 'Score' term and move relationships to the CDISC-defined term
    codelist_uid = common.find_codelist_uid(db_driver, name="Unit Dimension")
    if codelist_uid is None:
        log.warning("Could not find UID for 'Unit Dimension' codelist")
    else:
        bad_term_uid = common.find_term_uid(
            db_driver, term_name="Score", codelist_uid=codelist_uid, library="Sponsor"
        )
        good_term_uid = common.find_term_uid(
            db_driver, term_name="Score", codelist_uid=codelist_uid, library="CDISC"
        )
        if bad_term_uid is None or good_term_uid is None:
            log.info("Could not find UIDs for 'Score' terms")
        else:
            query, params = common.replace_term_by_deleting_query(
                bad_term_uid, good_term_uid
            )
            _, summary = run_cypher_query(db_driver, query, params)
            counters = summary.counters
            contains_updates = contains_updates or counters.contains_updates

    # Update the name of the term with concept id C100450
    query = """
        MATCH (tr:CTTermRoot {uid: "C100450"})-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:HAS_VERSION]->
          (tnv:CTTermNameValue {name: "Direct Glomerular Filtration Rate from Beta-Trace Protein Adjusted for Standard BSA Measurement"})
        SET tnv.name = "Direct Glomerular Filtration Rate from Beta-2 Microglobulin Adjusted for Standard BSA Measurement"
        SET tnv.name_sentence_case = "direct glomerular filtration rate from beta-2 microglobulin adjusted for standard BSA measurement"
    """
    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    contains_updates = contains_updates or counters.contains_updates
    return contains_updates


@capture_changes(
    verify_func=correction_verification_016.test_negative_duration_has_term
)
def solve_negative_duration_has_term(db_driver, log, run_label):
    """
    ## Remove HAS_TERM relationships with negative duration
    # ## Problem description
    The database contains a single HAS_TERM relationship with a start start_date that is after its end_date.
    This likely the result of a previous data correction or schema migration that incorrectly set the dates.

    ### Change description
    Remove the HAS_TERM relationship with negative duration.

    ### Nodes and relationships affected
    - `HAS_TERM` relationships
    - Expected changes: 1 relationship deleted
    """
    desc = "Remove HAS_TERM relationships with negative duration"
    log.info(f"Run: {run_label}, {desc}")

    query = """
        MATCH (clr:CTCodelistRoot)-[ht:HAS_TERM]->(clt:CTCodelistTerm)
        WHERE ht.end_date IS NOT NULL AND ht.start_date > ht.end_date
        WITH ht LIMIT 1
        DELETE ht
    """

    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    return counters.contains_updates


@capture_changes(
    verify_func=correction_verification_016.test_not_latest_has_version_lacks_end_date
)
def solve_not_latest_has_version_lacks_end_date(db_driver, log, run_label):
    """
    ## Add an end date to HAS_VERSION relationships that are not latest and lack an end date
    # ## Problem description
    The database contains a single ActivityInstance where both a Final and a Retired HAS_VERSION relationship
    lack an end date. This likely the result of a previous data correction or schema migration that
    did not corectly set the end date on the Final relationship whent he Retired relationship was added.

    ### Change description
    Add an end date the the Final HAS_VERSION, setting it to the start time of the Retired HAS_VERSION.

    ### Nodes and relationships affected
    - `HAS_VERSION` relationships
    - Expected changes: 1 relationship updated
    """
    desc = "Add an end date to HAS_VERSION relationships that are not latest and lack an end date"
    log.info(f"Run: {run_label}, {desc}")

    query = """
        MATCH (air:ActivityInstanceRoot {uid: "ActivityInstance_000638"})
        MATCH (air)-[final:HAS_VERSION {status: "Final"}]->(aiv:ActivityInstanceValue)
        WHERE final.end_date IS NULL
        MATCH (air)-[retired:HAS_VERSION {status: "Retired"}]->(aiv)
        WHERE retired.end_date IS NULL
        SET final.end_date = retired.start_date
    """

    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    return counters.contains_updates


@capture_changes(
    verify_func=correction_verification_016.test_remove_isolated_orphan_nodes
)
def remove_isolated_orphan_nodes(db_driver, log, run_label):
    """
    ## Remove isolated orphan nodes (Bug #3473052)

    ### Problem description
    Some nodes exist in the database with no relationships at all.
    These are orphan nodes that should have been deleted when their
    related nodes were removed.

    ### Change description
    - Delete all nodes with no relationships that are of type:
      StudyAction or StudyActivitySchedule

    ### Nodes and relationships affected
    - `StudyAction`, `StudyActivitySchedule` nodes with no relationships
    """
    log.info(f"Run: {run_label}, Removing isolated orphan nodes")

    query = """
        MATCH (n)
        WHERE NOT EXISTS ((n)--())
        AND (n:StudyAction OR n:StudyActivitySchedule)
        DETACH DELETE n
    """

    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    return counters.contains_updates


@capture_changes(
    verify_func=correction_verification_016.test_remove_orphan_study_selection_nodes
)
def remove_orphan_study_selection_nodes(db_driver, log, run_label):
    """
    ## Remove orphan StudySelection nodes (Bug #3473115)

    ### Problem description
    Some StudySelection nodes exist without being connected to the audit trail.
    They have no AFTER relationship from a StudyAction, meaning they are orphaned
    from the study's action history.

    ### Change description
    - Delete all StudySelection nodes that have no incoming AFTER relationship
      from a StudyAction node

    ### Nodes and relationships affected
    - `StudySelection` nodes not connected via AFTER relationship to StudyAction
    """
    log.info(f"Run: {run_label}, Removing orphan StudySelection nodes")

    query = """
        MATCH (ss:StudySelection)
        WHERE NOT (:StudyAction)-[:AFTER]->(ss)
        DETACH DELETE ss
    """

    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    return counters.contains_updates


if __name__ == "__main__":
    main()
