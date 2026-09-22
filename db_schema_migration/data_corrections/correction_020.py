"""PRD Data Corrections: Fix Non and Unscheduled visit labels and visibility, restore CTCodelistTerm nodes"""

import json
import os

from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    print_counters_table,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import get_logger
from verifications import correction_verification_020

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-fix-visit-label-and-visibility"
CHANGE_LOG_FILE = os.path.join(
    os.path.dirname(__file__),
    "change_logs",
    "remove_veeva_codelists.correction.json",
)


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    fix_non_and_unscheduled_visit_label_and_visibility(DB_DRIVER, LOGGER, run_label)
    restore_codelist_term_nodes(DB_DRIVER, LOGGER, run_label)


@capture_changes(
    verify_func=correction_verification_020.test_non_and_unscheduled_visits_label_and_visibility
)
def fix_non_and_unscheduled_visit_label_and_visibility(db_driver, log, run_label):
    """
    ### Problem description
    Non-visit and Unscheduled-visit StudyVisit nodes have `short_visit_label` values
    that are not prefixed with "V", and their `show_visit` property is not set to `false`.
    ### Change description
    - Prefix `short_visit_label` with "V" for all current Non and Unscheduled visits
      whose label does not already start with "V".
    - Set `show_visit` to `false` for all current Non and Unscheduled visits.
    ### Nodes and relationships affected
    - `StudyVisit` node properties: `short_visit_label`, `show_visit`
    ### Expected changes: Non and Unscheduled visits updated with "V" prefix and show_visit=false
    """
    log.info(
        f"Run: {run_label}, Fixing short_visit_label prefix and show_visit for Non and Unscheduled visits"
    )
    query = """
        MATCH (visit:StudyVisit)
        WHERE visit.visit_class IN ['NON_VISIT', 'UNSCHEDULED_VISIT']
          AND (NOT visit.short_visit_label STARTS WITH 'V' OR visit.show_visit <> false)
        SET visit.short_visit_label = 'V' + visit.short_visit_label
        SET visit.show_visit = false
    """
    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


def parse_change_log(change_log_path):
    """Parse the correction 019 change log and extract deleted CTCodelistTerm data.

    The change log contains two transactions, one for each phase of the correction.
    In the first transaction (phase A) the CTCodelistTerm nodes that link the terms
    to codelists were removed, and in the second (phase B) the Veeva codelists
    themselves were removed. The changes to be undone are all in the first phase.

    Returns a list of dicts, one per deleted CTCodelistTerm node:
    {
        "submission_value": str,
        "term_root_uid": str,
        "has_term_from": [{"codelist_uid": str, "rel_props": dict}],
        "contains_sv_from": [str],
    }
    """
    with open(change_log_path, encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        return []

    # Build set of ALL deleted node elementIds (across all transactions)
    # so we can skip relationships to nodes that were also deleted (e.g. Veeva
    # codelists removed in Phase B).
    deleted_node_ids = {
        r[4]["elementId"]
        for r in data
        if r[4].get("eventType") == "n" and r[4].get("operation") == "d"
    }

    # Phase A is the first (earliest) transaction
    commit_times = sorted({r[3].get("txCommitTime") for r in data})
    phase_a_time = commit_times[0]
    phase_a = [r for r in data if r[3].get("txCommitTime") == phase_a_time]

    # Collect deleted CTCodelistTerm nodes
    clt_nodes = {}
    for r in phase_a:
        event = r[4]
        if event.get("operation") == "d" and event.get("eventType") == "n":
            labels = event.get("state", {}).get("before", {}).get("labels", [])
            if "CTCodelistTerm" in labels:
                eid = event.get("elementId")
                props = event.get("state", {}).get("before", {}).get("properties", {})
                clt_nodes[eid] = {
                    "submission_value": props.get("submission_value"),
                    "term_root_uid": None,
                    "has_term_from": [],
                    "contains_sv_from": [],
                }

    # Collect relationships, skipping any where the other end was also deleted
    for r in phase_a:
        event = r[4]
        if event.get("operation") != "d" or event.get("eventType") != "r":
            continue

        start = event.get("start", {})
        end = event.get("end", {})
        rel_type = event.get("type")
        rel_props = event.get("state", {}).get("before", {}).get("properties", {})

        if rel_type == "HAS_TERM_ROOT":
            start_eid = start.get("elementId")
            if start_eid in clt_nodes:
                for kd in end.get("keys", {}).get("CTTermRoot", []):
                    clt_nodes[start_eid]["term_root_uid"] = kd.get("uid")

        elif rel_type == "HAS_TERM":
            end_eid = end.get("elementId")
            start_eid = start.get("elementId")
            if end_eid in clt_nodes and start_eid not in deleted_node_ids:
                for kd in start.get("keys", {}).get("CTCodelistRoot", []):
                    clt_nodes[end_eid]["has_term_from"].append(
                        {"codelist_uid": kd.get("uid"), "rel_props": rel_props}
                    )

        elif rel_type == "CONTAINS_SUBMISSION_VALUE":
            end_eid = end.get("elementId")
            start_eid = start.get("elementId")
            if end_eid in clt_nodes and start_eid not in deleted_node_ids:
                for kd in start.get("keys", {}).get("CTPackageTerm", []):
                    clt_nodes[end_eid]["contains_sv_from"].append(kd.get("uid"))

    # Skip entries where all codelists and package terms were also deleted
    # (i.e. the term was exclusively on Veeva codelists removed in Phase B).
    # Restoring these would create dangling CTCodelistTerm nodes with no purpose.
    return [
        j for j in clt_nodes.values() if j["has_term_from"] or j["contains_sv_from"]
    ]


def build_restore_query(clt_entry):
    """Build a Cypher statement to restore a single CTCodelistTerm node.

    Pattern:
    1. MATCH CTTermRoot, MERGE CTCodelistTerm + HAS_TERM_ROOT
    2. For each CTPackageTerm: WITH term, MATCH, MERGE CONTAINS_SUBMISSION_VALUE
    3. For each CTCodelistRoot: WITH term, MATCH, MERGE HAS_TERM with properties
    """
    sv = clt_entry["submission_value"]
    tr_uid = clt_entry["term_root_uid"]

    parts = [
        f'MATCH (termRoot:CTTermRoot {{uid: "{tr_uid}"}})',
        f'MERGE (termRoot)<-[:HAS_TERM_ROOT]-(term:CTCodelistTerm {{submission_value: "{sv}"}})',
    ]

    for pkg_uid in clt_entry["contains_sv_from"]:
        parts.append("WITH term")
        parts.append(f'MATCH (other:CTPackageTerm {{uid: "{pkg_uid}"}})')
        parts.append("MERGE (other)-[:CONTAINS_SUBMISSION_VALUE]->(term)")

    for ht in clt_entry["has_term_from"]:
        cl_uid = ht["codelist_uid"]
        props = ht["rel_props"]

        prop_parts = []
        if "author_id" in props:
            prop_parts.append(f'author_id: "{props["author_id"]}"')
        if "start_date" in props:
            prop_parts.append(f'start_date: datetime("{props["start_date"]}")')
        if "end_date" in props:
            prop_parts.append(f'end_date: datetime("{props["end_date"]}")')
        if "order" in props:
            prop_parts.append(f"order: {props['order']}")

        prop_str = ", ".join(prop_parts)
        parts.append("WITH term")
        parts.append(f'MATCH (other:CTCodelistRoot {{uid: "{cl_uid}"}})')
        parts.append(f"MERGE (other)-[:HAS_TERM {{{prop_str}}}]->(term)")

    return "\n".join(parts)


@capture_changes(
    verify_func=correction_verification_020.test_no_orphaned_correction_019_terms
)
def restore_codelist_term_nodes(db_driver, log, run_label):
    """
    ### Problem description
    Correction 019 Phase A (unlink non-Veeva terms from Veeva codelists) used
    `DETACH DELETE clt` on CTCodelistTerm nodes. Because these nodes are shared
    across multiple codelists (HAS_TERM from both Veeva and CDISC codelists),
    deleting the node severed terms from ALL codelists, not just the
    Veeva ones. This left 84 CDISC terms fully orphaned and destroyed 5,670
    CONTAINS_SUBMISSION_VALUE relationships from CTPackageTerm nodes.
    ### Change description
    - Read the correction 019 change log to identify deleted CTCodelistTerm nodes
      and their original relationships (skipping 13 whose codelists were all deleted)
    - Recreate each CTCodelistTerm node with its submission_value
    - Restore HAS_TERM_ROOT relationships to CTTermRoot
    - Restore HAS_TERM relationships to CTCodelistRoot nodes that still exist
    - Restore CONTAINS_SUBMISSION_VALUE relationships from CTPackageTerm nodes
    ### Nodes and relationships affected
    - `CTCodelistTerm` (recreated via MERGE)
    - `HAS_TERM_ROOT` (CTCodelistTerm -> CTTermRoot)
    - `HAS_TERM` (CTCodelistRoot -> CTCodelistTerm, with author_id/start_date/order/end_date)
    - `CONTAINS_SUBMISSION_VALUE` (CTPackageTerm -> CTCodelistTerm)
    ### Expected changes: up to 95 CTCodelistTerm nodes restored with all relationships
    """
    change_log_path = CHANGE_LOG_FILE
    if not os.path.exists(change_log_path):
        log.warning(f"Change log not found at {change_log_path}, skipping")
        return False

    log.info(f"Run: {run_label}, Parsing change log from {change_log_path}")
    clt_entries = parse_change_log(change_log_path)
    if not clt_entries:
        log.info(
            f"Run: {run_label}, No CTCodelistTerm nodes to restore (empty change log)"
        )
        return False

    log.info(f"Run: {run_label}, Restoring {len(clt_entries)} CTCodelistTerm nodes")

    contains_updates = False
    for i, clt_entry in enumerate(clt_entries):
        query = build_restore_query(clt_entry)
        _, summary = run_cypher_query(db_driver, query, quiet=True)
        if summary.counters.contains_updates:
            contains_updates = True
        if (i + 1) % 20 == 0 or i == len(clt_entries) - 1:
            log.info(
                f"Run: {run_label}, Processed {i + 1}/{len(clt_entries)} CTCodelistTerm nodes"
            )

    # Print final summary by running a count query
    log.info(f"Run: {run_label}, Verifying restored CTCodelistTerm nodes")
    query_count = """
        MATCH (tr:CTTermRoot)
        WHERE NOT EXISTS { MATCH (:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr) }
        RETURN COUNT(tr) AS orphaned_terms
    """
    records, _ = run_cypher_query(db_driver, query_count)
    orphaned = records[0]["orphaned_terms"] if records else -1
    log.info(f"Run: {run_label}, Remaining orphaned terms: {orphaned}")

    return contains_updates


if __name__ == "__main__":
    main()
