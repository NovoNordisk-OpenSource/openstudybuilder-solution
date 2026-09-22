"""PRD Data Corrections: Replace XML entities in node definition text"""

import os

from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    print_counters_table,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import get_logger
from verifications import correction_verification_021

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-clean-definition-xml-entities"


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    replace_xml_entities_in_definitions(DB_DRIVER, LOGGER, run_label)


@capture_changes(
    verify_func=correction_verification_021.test_no_xml_entities_in_definitions
)
def replace_xml_entities_in_definitions(db_driver, log, run_label):
    """
    ### Problem description
    Some nodes store XML-encoded text in `definition`, such as `&#8729;` and `&#8722;`,
    instead of plain characters.
    ### Change description
    - Replace `&#8729;` with `·` in `definition`
    - Replace `&#8722;` with `-` in `definition`
    - Apply the replacement only to nodes where `definition` contains `&#8729;`
    ### Nodes and relationships affected
    - Any node with a `definition` property containing XML entities
    ### Expected changes: XML entities removed from affected `definition` values
    """
    log.info(f"Run: {run_label}, Replacing XML entities in node definitions")
    query = """
        MATCH (n)
        WHERE n.definition CONTAINS "&#8729;"
        SET n.definition = replace(n.definition, '&#8729;', '·')
        SET n.definition = replace(n.definition, '&#8722;', '-')
        RETURN n.definition
    """
    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


if __name__ == "__main__":
    main()
