"""
This modules verifies that database nodes/relations and API endpoints look and behave as expected.

It utilizes tests written for verifying a specific migration,
without inserting any test data and without running any migration script on the target database.
"""

import os

from data_corrections.utils.utils import get_db_driver, run_cypher_query
from migrations.utils.utils import get_logger

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()


def test_non_and_unscheduled_visits_label_and_visibility():
    """Verify that all Non and Unscheduled visits have 'V'-prefixed short_visit_label and show_visit=False."""
    LOGGER.info(
        "Checking Non and Unscheduled visits for correct short_visit_label prefix and show_visit"
    )
    query = """
        MATCH (visit:StudyVisit)
        WHERE visit.visit_class IN ['NON_VISIT', 'UNSCHEDULED_VISIT']
          AND (NOT visit.short_visit_label STARTS WITH 'V' OR visit.show_visit <> false)
        RETURN visit.uid AS uid, visit.visit_class AS visit_class,
               visit.short_visit_label AS short_visit_label, visit.show_visit AS show_visit
    """
    res, _ = run_cypher_query(DB_DRIVER, query)
    assert (
        len(res) == 0
    ), f"Found {len(res)} Non/Unscheduled visits with incorrect short_visit_label or show_visit: {res}"


# 79 CTTermRoot UIDs that were completely orphaned by correction 019 Phase A
# (i.e. lost ALL their CTCodelistTerm nodes, leaving the CTTermRoot with zero
# HAS_TERM_ROOT connections). The correction restores additional terms too, but
# those were only partially affected and still had other CTCodelistTerm nodes.
ORPHANED_TERM_UIDS = [
    "C101589",
    "C101888",
    "C105519",
    "C111092",
    "C116244",
    "C116246",
    "C12366",
    "C12377",
    "C12392",
    "C12393",
    "C12402",
    "C12415",
    "C12416",
    "C12432",
    "C12434",
    "C12438",
    "C12470",
    "C12722",
    "C12745",
    "C12971",
    "C13056",
    "C132424",
    "C132447",
    "C139186",
    "C14143",
    "C14172",
    "C15262",
    "C15632",
    "C165873",
    "C166074",
    "C16929",
    "C17822",
    "C182672",
    "C182680",
    "C182681",
    "C182736",
    "C182742",
    "C182743",
    "C183001",
    "C183002",
    "C183035",
    "C25613",
    "C25742",
    "C26784",
    "C28161",
    "C3036",
    "C32525",
    "C33010",
    "C33012",
    "C33763",
    "C33837",
    "C33839",
    "C3390",
    "C38276",
    "C38299",
    "C42678",
    "C48508",
    "C51998",
    "C53287",
    "C64387",
    "C64777",
    "C64783",
    "C67015",
    "C67255",
    "C67326",
    "C67376",
    "C67399",
    "C67432",
    "C67452",
    "C67456",
    "C67474",
    "C70543",
    "C73721",
    "C80383",
    "C94522",
    "C99521",
    "CTTerm_000101",
    "CTTerm_000107",
    "CTTerm_000108",
]


def test_no_orphaned_correction_019_terms():
    """Verify that none of the 79 terms orphaned by correction 019 remain orphaned."""
    query = """
        UNWIND $term_uids AS uid
        MATCH (tr:CTTermRoot {uid: uid})
        WHERE NOT EXISTS { MATCH (:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr) }
        RETURN COLLECT(tr.uid) AS orphaned_uids
    """
    records, _ = run_cypher_query(
        DB_DRIVER, query, params={"term_uids": ORPHANED_TERM_UIDS}
    )
    orphaned = records[0]["orphaned_uids"] if records else []
    assert (
        len(orphaned) == 0
    ), f"Found {len(orphaned)} orphaned terms that should have been restored: {orphaned}"
