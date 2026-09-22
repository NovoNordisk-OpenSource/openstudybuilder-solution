"""PRD Data Corrections: Remove Veeva-imported codelists and terms"""

import os

from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    print_counters_table,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import get_logger
from verifications import correction_verification_019

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-remove-veeva-imports"

VEEVA_DEFINITIONS = [
    "Created by Library Importer",
    "Created by Veeva Library Importer",
]


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    remove_veeva_terms(DB_DRIVER, LOGGER, run_label)
    remove_veeva_codelists(DB_DRIVER, LOGGER, run_label)


@capture_changes(verify_func=correction_verification_019.test_no_veeva_codelists_remain)
def remove_veeva_codelists(db_driver, log, run_label):
    """
    ### Problem description
    The initial import of ODM data from Veeva created 301 codelists in the library.
    When the ODM data was wiped, these codelists were left behind and need to be removed.
    Some Veeva codelists contain non-Veeva terms that must be unlinked before deletion.
    Runs after term deletion so codelists with remaining protected terms are preserved.
    ### Change description
    - Phase A: Unlink non-Veeva terms from Veeva codelists (remove CTCodelistTerm junctions)
    - Phase B: Delete Veeva codelists that have no remaining terms
    ### Nodes and relationships affected
    - `CTCodelistRoot`, `CTCodelistNameRoot`, `CTCodelistNameValue`
    - `CTCodelistAttributesRoot`, `CTCodelistAttributesValue`
    - `CTCodelistTerm` (junction nodes)
    ### Expected changes: Veeva codelists with no remaining terms deleted
    """
    contains_updates = []

    # Phase A: Unlink non-Veeva terms from Veeva codelists
    log.info(f"Run: {run_label}, Unlinking non-Veeva terms from Veeva codelists")
    query_unlink = """
        MATCH (clr:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)
              -[:HAS_VERSION]->(clav:CTCodelistAttributesValue)
        WHERE clav.definition IN $definitions
        WITH DISTINCT clr
        MATCH (clr)-[:HAS_TERM]->(clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr:CTTermRoot)
        WHERE NOT EXISTS {
            MATCH (tr)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)
                  -[:HAS_VERSION]->(tav:CTTermAttributesValue)
            WHERE tav.definition IN $definitions
        }
        DETACH DELETE clt
    """
    _, summary = run_cypher_query(
        db_driver,
        query_unlink,
        params={"definitions": VEEVA_DEFINITIONS},
    )
    counters = summary.counters
    print_counters_table(counters)
    contains_updates.append(counters.contains_updates)

    # Phase B: Delete Veeva codelists that have no remaining terms
    log.info(f"Run: {run_label}, Deleting Veeva codelists with no remaining terms")
    query_delete = """
        MATCH (clr:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)
              -[:HAS_VERSION]->(clav:CTCodelistAttributesValue)
        WHERE clav.definition IN $definitions
        WITH DISTINCT clr
        WHERE NOT EXISTS { MATCH (clr)-[:HAS_TERM]->(:CTCodelistTerm) }
        CALL {
            WITH clr
            OPTIONAL MATCH (clr)-[:HAS_NAME_ROOT]->(clnr:CTCodelistNameRoot)
            OPTIONAL MATCH (clnr)-[]->(clnv:CTCodelistNameValue)
            DETACH DELETE clnv, clnr
        }
        CALL {
            WITH clr
            OPTIONAL MATCH (clr)-[:HAS_ATTRIBUTES_ROOT]->(clar:CTCodelistAttributesRoot)
            OPTIONAL MATCH (clar)-[]->(clav2:CTCodelistAttributesValue)
            DETACH DELETE clav2, clar
        }
        CALL {
            WITH clr
            OPTIONAL MATCH (clr)-[:HAS_TERM]->(clt:CTCodelistTerm)
            DETACH DELETE clt
        }
        DETACH DELETE clr
    """
    _, summary = run_cypher_query(
        db_driver,
        query_delete,
        params={"definitions": VEEVA_DEFINITIONS},
    )
    counters = summary.counters
    print_counters_table(counters)
    contains_updates.append(counters.contains_updates)

    return any(contains_updates)


@capture_changes(verify_func=correction_verification_019.test_no_veeva_terms_remain)
def remove_veeva_terms(db_driver, log, run_label):
    """
    ### Problem description
    The initial import of ODM data from Veeva created 652 terms in the library.
    When the ODM data was wiped, these terms were left behind and need to be removed.
    6 terms have active CTTermContext references (UnitDefinitionValue/ActivityItem) and must
    be preserved.
    ### Change description
    - Step 1: Identify protected terms (those referenced by CTTermContext nodes that
      themselves have incoming relationships, i.e. are actually used by studies/concepts)
    - Step 2: Delete all unprotected Veeva terms (CTTermRoot + name/attributes sub-trees
      + CTCodelistTerm junctions + orphaned CTTermContext nodes)
    ### Nodes and relationships affected
    - `CTTermRoot`, `CTTermNameRoot`, `CTTermNameValue`
    - `CTTermAttributesRoot`, `CTTermAttributesValue`
    - `CTCodelistTerm` (junction nodes linking terms to non-Veeva codelists)
    - `CTTermContext` (orphaned nodes with no incoming relationships)
    ### Expected changes: 646 terms deleted, 6 terms preserved
    """
    # Step 1: Find protected terms (those with CTTermContext references)
    log.info(
        f"Run: {run_label}, Finding protected Veeva terms with CTTermContext references"
    )
    query_protected = """
        MATCH (tr:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)
              -[:HAS_VERSION]->(tav:CTTermAttributesValue)
        WHERE tav.definition IN $definitions
        WITH DISTINCT tr
        WHERE EXISTS {
            MATCH (ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(tr)
            WHERE EXISTS { MATCH ()-[]->(ctx) }
        }
        RETURN tr.uid AS term_uid
    """
    protected_records, _ = run_cypher_query(
        db_driver,
        query_protected,
        params={"definitions": VEEVA_DEFINITIONS},
    )
    protected_uids = [record["term_uid"] for record in protected_records]
    log.info(
        f"Run: {run_label}, Found {len(protected_uids)} protected terms: {protected_uids}"
    )

    # Step 2: Delete unprotected Veeva terms
    log.info(f"Run: {run_label}, Deleting unprotected Veeva terms")
    query_delete = """
        MATCH (tr:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)
              -[:HAS_VERSION]->(tav:CTTermAttributesValue)
        WHERE tav.definition IN $definitions
        WITH DISTINCT tr
        WHERE NOT tr.uid IN $protected_uids
        CALL {
            WITH tr
            OPTIONAL MATCH (tr)-[:HAS_NAME_ROOT]->(tnr:CTTermNameRoot)
            OPTIONAL MATCH (tnr)-[]->(tnv:CTTermNameValue)
            DETACH DELETE tnv, tnr
        }
        CALL {
            WITH tr
            OPTIONAL MATCH (tr)-[:HAS_ATTRIBUTES_ROOT]->(tar:CTTermAttributesRoot)
            OPTIONAL MATCH (tar)-[]->(tav2:CTTermAttributesValue)
            DETACH DELETE tav2, tar
        }
        CALL {
            WITH tr
            OPTIONAL MATCH (clt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr)
            DETACH DELETE clt
        }
        CALL {
            WITH tr
            OPTIONAL MATCH (ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(tr)
            WHERE NOT EXISTS { MATCH ()-[]->(ctx) }
            DETACH DELETE ctx
        }
        DETACH DELETE tr
    """
    _, summary = run_cypher_query(
        db_driver,
        query_delete,
        params={
            "definitions": VEEVA_DEFINITIONS,
            "protected_uids": protected_uids,
        },
    )
    counters = summary.counters
    print_counters_table(counters)
    return counters.contains_updates


if __name__ == "__main__":
    main()
