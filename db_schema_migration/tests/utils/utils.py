import os

from migrations.utils.utils import (
    drop_indexes_and_constraints,
    get_db_connection,
    get_logger,
)

db = get_db_connection()
logger = get_logger(os.path.basename(__file__))

MAX_NBR_NODES_TO_CLEAR = 50000


def clear_db():
    """Clear test db"""
    result, _meta = db.cypher_query("MATCH (n) RETURN count(n) AS nbr_nodes")
    nbr_nodes = result[0][0]
    if nbr_nodes > MAX_NBR_NODES_TO_CLEAR:
        raise RuntimeError(
            f"The database has too many nodes! Found nodes {nbr_nodes}, limit: {MAX_NBR_NODES_TO_CLEAR}: Is this a real database? Not clearing data."
        )

    logger.info("Clearing database")
    # Delete nodes and relationships
    db.cypher_query("MATCH (n) DETACH DELETE n")
    # Delete indexes and constraints
    drop_indexes_and_constraints()
