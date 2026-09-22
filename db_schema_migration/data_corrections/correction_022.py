"""PRD Data Corrections: Remove unused Neodash dashboard node"""

import os

from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    print_counters_table,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import get_logger
from verifications import correction_verification_022

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()

LONELY_NEODASH_UUID = "6b288611-7f89-482c-a850-b34b19cf6ebb"
LONELY_NEODASH_TITLE = "External Data File Specifications"
LONELY_NEODASH_USER = "devops_adm"
LONELY_NEODASH_DATE = "2025-10-05 13:20:42 +0000"


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    remove_lonely_external_data_file_spec_dashboard(DB_DRIVER, LOGGER, run_label)


@capture_changes(
    verify_func=correction_verification_022.test_unused_neodash_dashboard_removed
)
def remove_lonely_external_data_file_spec_dashboard(db_driver, log, run_label):
    """
    ### Problem description
    The `_Neodash_Dashboard` node for "External Data File Specifications" is no longer
    used and should be removed from the graph.
    ### Change description
    - `DETACH DELETE` the dashboard when `uuid`, `title`, `user`, and `date` match the
      target dashboard **and** the node has no relationships (`NOT (d)--()`), so
      connected rows are never removed.
    ### Nodes and relationships affected
    - `_Neodash_Dashboard` (one node): properties `uuid`, `title`, `user`, `date`,
      `content`, `version`
    ### Expected changes: unused dashboard node removed; idempotent when already absent
    """
    log.info(
        f"Run: {run_label}, Removing lonely Neodash dashboard "
        f"(uuid={LONELY_NEODASH_UUID})"
    )
    query = """
        MATCH (d:_Neodash_Dashboard)
        WHERE d.uuid = $uuid
          AND d.title = $title
          AND d.user = $user
          AND d.date = $date
          AND NOT (d)--()
        DETACH DELETE d
    """
    _, summary = run_cypher_query(
        db_driver,
        query,
        params={
            "uuid": LONELY_NEODASH_UUID,
            "title": LONELY_NEODASH_TITLE,
            "user": LONELY_NEODASH_USER,
            "date": LONELY_NEODASH_DATE,
        },
    )
    counters = summary.counters
    print_counters_table(counters)
    deleted = counters.nodes_deleted
    if deleted > 1:
        raise RuntimeError(
            f"Expected at most one node deleted, got nodes_deleted={deleted}"
        )
    if counters.contains_updates and deleted != 1:
        raise RuntimeError(
            f"Expected exactly one node deleted, got nodes_deleted={deleted}"
        )
    return counters.contains_updates


if __name__ == "__main__":
    main()
