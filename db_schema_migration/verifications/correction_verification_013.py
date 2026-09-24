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


def test_fix_author_id_info():
    """
    1. For each author_id field value (defined on any relevant node) there must exist one User node with the same user_id field value
    2. For each author_id field value (defined on any relevant relation) there must exist one User node with the same user_id field value
    3. All relevant nodes have author_id field set
    4. All relevant relations have author_id field set
    """

    # For each author_id field value (defined on any relevant node) there must exist one User node with the same user_id field value
    query = """
        MATCH (n:CTPackage|StudyAction|Edit|Create|Delete)
        OPTIONAL MATCH (u:User {user_id: n.author_id})
        WITH  n, 
              COUNT(DISTINCT u) as user_nodes_cnt
        WHERE user_nodes_cnt = 0
        RETURN
            COUNT(n) as noncompliant_entity_cnt,
            COLLECT(distinct(labels(n))) as noncompliant_labels,
            COLLECT(distinct(id(n))) as noncompliant_node_ids                
    """

    res, _ = run_cypher_query(DB_DRIVER, query)
    assert res[0][0] == 0, (
        f"Expected no non-compliant nodes, found {res[0][0]} "
        f"with labels {res[0][1]}"
    )

    # For each author_id field value (defined on any relevant relation) there must exist one User node with the same user_id field value
    query = """
        MATCH (n)-[rel:HAS_VERSION|HAS_TERM|HAD_TERM|LATEST_LOCKED|LATEST_RELEASED]->(m)
        OPTIONAL MATCH (u:User {user_id: rel.author_id})
        WITH  rel, 
              COUNT(DISTINCT u) as user_nodes_cnt
        WHERE user_nodes_cnt = 0
        RETURN
            COUNT(rel) as noncompliant_entity_cnt,
            COLLECT(distinct(type(rel))) as noncompliant_labels,
            COLLECT(distinct(id(rel))) as noncompliant_node_ids                
    """
    res, _ = run_cypher_query(DB_DRIVER, query)
    assert res[0][0] == 0, (
        f"Expected no non-compliant relationships, found {res[0][0]} "
        f"with labels {res[0][1]}"
    )

    # All relevant nodes have author_id field set
    query = """
        MATCH (n:CTPackage|StudyAction|Edit|Create|Delete)
        WHERE n.author_id is null
        RETURN
            COUNT(n) as noncompliant_entity_cnt,
            COLLECT(distinct(labels(n))) as noncompliant_labels,
            COLLECT(distinct(id(n))) as noncompliant_node_ids 
    """

    res, _ = run_cypher_query(DB_DRIVER, query)
    assert res[0][0] == 0, (
        f"Expected no nodes with null author_id, found {res[0][0]} "
        f"with labels {res[0][1]}"
    )

    # All relevant relationships have author_id field set
    query = """
        MATCH (n)-[rel:HAS_VERSION|HAS_TERM|HAD_TERM|LATEST_LOCKED|LATEST_RELEASED]->(m)
        WHERE rel.author_id is null
        RETURN
            COUNT(rel) as noncompliant_entity_cnt,
            COLLECT(distinct(type(rel))) as noncompliant_labels,
            COLLECT(distinct(id(rel))) as noncompliant_node_ids
    """
    res, _ = run_cypher_query(DB_DRIVER, query)
    assert res[0][0] == 0, (
        f"Expected no relationships with null author_id, found {res[0][0]} "
        f"with labels {res[0][1]}"
    )
