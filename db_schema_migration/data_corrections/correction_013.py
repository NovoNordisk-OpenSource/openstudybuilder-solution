"""PRD Data Corrections: Fixing issues with change author information"""

import os

from data_corrections.utils.utils import (
    capture_changes,
    get_db_driver,
    run_cypher_query,
    save_md_title,
)
from migrations.utils.utils import get_logger
from verifications import correction_verification_013

LOGGER = get_logger(os.path.basename(__file__))
DB_DRIVER = get_db_driver()
CORRECTION_DESC = "data-correction-release-1.16"
SB_APP_REGISTRATION_ID = "fd909732-bc9e-492b-a1ed-6e27757a4f00"


def main(run_label="correction"):
    desc = f"Running data corrections on DB '{os.environ['DATABASE_NAME']}'"
    LOGGER.info(desc)
    save_md_title(run_label, __doc__, desc)

    fix_author_id_info(DB_DRIVER, LOGGER, run_label)


@capture_changes(verify_func=correction_verification_013.test_fix_author_id_info)
def fix_author_id_info(db_driver, log, run_label):
    """
    ### Problem description
    Some nodes and relationships in the database have an `author_id` field that does not correspond to any existing `User` node.
    Most of them are storing author information in the `user_initials` field instead of `author_id`.
    The `author_id` field is expected to be set for all relevant nodes and relationships, and it should match the `user_id` of an existing `User` node.

    Some nodes and relationships have the `author_id` set to 'unknown-user' or 'sb-import', which should be replaced with a specific SB app registration ID.

    ### Change description
    - Move `user_initials` values to `author_id` field for all relevant nodes and relationships.
    - Convert 'unknown-user' and 'sb-import' `author_id` values to a specific SB app registration ID.
    - Create `User` nodes for all existing `author_id` values that do not have a corresponding `User` node.
    - Ensure that all relevant nodes and relationships have the `author_id` field set and that it matches an existing `User` node's `user_id`.

    ### Nodes and relationships affected
    - `CTPackage|StudyAction|Edit|Create|Delete` nodes
    - `HAS_VERSION|HAS_TERM|HAD_TERM|LATEST_LOCKED|LATEST_RELEASED` relationships
    """
    contains_updates = []

    # Create User node representing this correction (CORRECTION_DESC)
    log.info(
        f"Run: {run_label}, Create User node representing '{CORRECTION_DESC}' correction"
    )
    query = f"""
    MERGE (u:User {{user_id: "{CORRECTION_DESC}", username: "{CORRECTION_DESC}"}})
    ON CREATE SET u.created = datetime()
    """
    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    contains_updates.append(counters.contains_updates)

    # Create User node representing the SB App Registration ID (already present in VAl/PRD)
    log.info(
        f"Run: {run_label}, Create User node representing '{SB_APP_REGISTRATION_ID}'"
    )
    query = f"""
    MERGE (u:User {{user_id: "{SB_APP_REGISTRATION_ID}", username: "sb-import"}})
    ON CREATE SET u.created = datetime()
    """
    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    contains_updates.append(counters.contains_updates)

    # Get all 'user_initials' value from relevant nodes and relations
    query = """
        MATCH (n:CTPackage|StudyAction|Edit|Create|Delete)
        WHERE n.user_initials is not null
        RETURN distinct(n.user_initials) as user_initials

        UNION        

        MATCH (n)-[rel:HAS_VERSION|HAS_TERM|HAD_TERM|LATEST_LOCKED|LATEST_RELEASED]->(m)
        WHERE rel.user_initials is not null
        RETURN distinct(rel.user_initials) as user_initials
    """
    res, _ = run_cypher_query(db_driver, query)
    author_ids = [r[0] for r in res if r[0] is not None]

    desc = f"Create User nodes for all existing 'user_initials' values: {', '.join(author_ids)}"
    log.info(f"Run: {run_label}, {desc}")
    _, summary = run_cypher_query(
        db_driver,
        f"""
            WITH {author_ids} as author_ids
            UNWIND author_ids as author_id
            MERGE (user:User {{user_id: author_id}})
                ON CREATE SET user.created = datetime(), user.username = author_id
                ON MATCH SET user.updated = datetime(), user.username = author_id
            RETURN user
        """,
        {"author_ids": author_ids},
    )
    counters = summary.counters
    contains_updates.append(counters.contains_updates)

    # Move 'user_initials' values to 'author_id' field
    log.info(
        f"Run: {run_label}, Move 'user_initials' values to 'author_id' field (nodes)"
    )
    query = """ 
        MATCH (n:CTPackage|StudyAction|Edit|Create|Delete)
        WHERE n.user_initials is not null
        SET n.author_id = n.user_initials
        REMOVE n.user_initials
        RETURN n
    """
    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    contains_updates.append(counters.contains_updates)

    log.info(
        f"Run: {run_label}, Move 'user_initials' values to 'author_id' field (relationships)"
    )
    query = """
        MATCH (n)-[rel:HAS_VERSION|HAS_TERM|HAD_TERM|LATEST_LOCKED|LATEST_RELEASED]->(m)
        WHERE rel.user_initials is not null
        SET rel.author_id = rel.user_initials
        REMOVE rel.user_initials
        RETURN rel
    """
    _, summary = run_cypher_query(db_driver, query)
    counters = summary.counters
    contains_updates.append(counters.contains_updates)

    # author_id value 'unknown-user' must be converted to fd909732-bc9e-492b-a1ed-6e27757a4f00
    log.info(
        f"Run: {run_label}, Convert 'unknown-user' author_id to '{SB_APP_REGISTRATION_ID}' (nodes)"
    )
    query = """
        MATCH (n:CTPackage|StudyAction|Edit|Create|Delete)
        WHERE n.author_id = 'unknown-user'
        SET n.author_id = $author_id
        RETURN n
    """
    _, summary = run_cypher_query(
        db_driver, query, {"author_id": SB_APP_REGISTRATION_ID}
    )
    counters = summary.counters
    contains_updates.append(counters.contains_updates)

    log.info(
        f"Run: {run_label}, Convert 'unknown-user' author_id to '{SB_APP_REGISTRATION_ID}' (relationships)"
    )
    query = """
        MATCH (n)-[rel:HAS_VERSION|HAS_TERM|HAD_TERM|LATEST_LOCKED|LATEST_RELEASED]->(m)
        WHERE rel.author_id = 'unknown-user'
        SET rel.author_id = $author_id
        RETURN rel
    """
    _, summary = run_cypher_query(
        db_driver, query, {"author_id": SB_APP_REGISTRATION_ID}
    )
    counters = summary.counters
    contains_updates.append(counters.contains_updates)

    log.info(
        f"Run: {run_label}, Convert 'sb-import' author_id to '{SB_APP_REGISTRATION_ID}' (relationships)"
    )
    query = """
        MATCH (n)-[rel:HAS_VERSION|HAS_TERM|HAD_TERM|LATEST_LOCKED|LATEST_RELEASED]->(m)
        WHERE rel.author_id = 'sb-import'
        SET rel.author_id = $author_id
        RETURN rel
    """
    _, summary = run_cypher_query(
        db_driver, query, {"author_id": SB_APP_REGISTRATION_ID}
    )
    counters = summary.counters
    contains_updates.append(counters.contains_updates)

    return any(contains_updates)


if __name__ == "__main__":
    main()
