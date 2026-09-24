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

VEEVA_DEFINITIONS = [
    "Created by Library Importer",
    "Created by Veeva Library Importer",
]


def test_no_veeva_codelists_remain():
    """Verify that no empty Veeva-imported codelists remain in the database.

    Veeva codelists that still contain protected terms (terms with active
    CTTermContext references) are expected to be preserved.
    """
    LOGGER.info("Checking for remaining empty Veeva-imported codelists")
    query = """
        MATCH (clr:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)
              -[:HAS_VERSION]->(clav:CTCodelistAttributesValue)
        WHERE clav.definition IN $definitions
        WITH DISTINCT clr
        WHERE NOT EXISTS { MATCH (clr)-[:HAS_TERM]->(:CTCodelistTerm) }
        RETURN count(clr) AS count
    """
    res, _ = run_cypher_query(
        DB_DRIVER, query, params={"definitions": VEEVA_DEFINITIONS}
    )
    count = res[0]["count"]
    assert count == 0, f"Found {count} empty Veeva codelists still in the database"


def test_no_veeva_terms_remain():
    """Verify that no unprotected Veeva-imported terms remain in the database.

    Terms with active CTTermContext references (i.e. the CTTermContext has incoming
    relationships from UnitDefinitionValue, ActivityItem, etc.) are expected to be
    preserved and are excluded from this check.
    """
    LOGGER.info("Checking for remaining unprotected Veeva-imported terms")
    query = """
        MATCH (tr:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)
              -[:HAS_VERSION]->(tav:CTTermAttributesValue)
        WHERE tav.definition IN $definitions
        WITH DISTINCT tr
        WHERE NOT EXISTS {
            MATCH (ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(tr)
            WHERE EXISTS { MATCH ()-[]->(ctx) }
        }
        RETURN count(tr) AS count
    """
    res, _ = run_cypher_query(
        DB_DRIVER, query, params={"definitions": VEEVA_DEFINITIONS}
    )
    count = res[0]["count"]
    assert (
        count == 0
    ), f"Found {count} unprotected Veeva-imported terms still in the database"
