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


def test_remove_user_initials_field_from_all_nodes():
    LOGGER.info("Check for unwanted nodes having user_initials field set")

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n)
        WHERE n.user_initials IS NOT NULL
        AND n.author_id IS NOT NULL
        RETURN COUNT(n) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"Found {len(records)} unwanted nodes having user_initials field set."


def test_remove_user_initials_field_from_all_relations():
    LOGGER.info("Check for unwanted relationships having user_initials field set")

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH ()-[rel]-()
        WHERE rel.user_initials IS NOT NULL
        AND rel.author_id IS NOT NULL
        RETURN COUNT(rel) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"Found {len(records)} unwanted relationships having user_initials field set."


def test_create_qphm_user():
    oid = "5f92937a-09ad-498b-8b43-7f5060753e34"
    email = "qphm@novonordisk.com"
    name = "(QPHM) Jesper Ejlebæk Holm"

    LOGGER.info("Check that the QPHM user has been created")

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n: User)
        WHERE n.oid = $oid
        AND n.user_id = $oid
        AND n.username = $email
        AND n.email = $email
        AND n.name = $name
        RETURN COUNT(n) as count
        """,
        params={
            "oid": oid,
            "email": email,
            "name": name,
        },
    )
    assert records[0]["count"] == 1, "QPHM User node not found."

    LOGGER.info(
        "Check that the QPHM user id has been assigned to all relevant nodes and relationships"
    )
    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n:CTPackage|StudyAction|Edit|Create|Delete)
        WHERE n.author_id = 'qphm'
        RETURN COUNT(n) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"{records[0]['count']} nodes with author_id=qphm found."

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n)-[ver:HAS_VERSION|HAS_TERM|HAD_TERM|LATEST_DRAFT|LATEST_LOCKED|LATEST_RELEASED]->(m)
        WHERE ver.author_id = 'qphm'
        RETURN COUNT(ver) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"{records[0]['count']} relations with author_id=qphm found."

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n:CTPackage|StudyAction|Edit|Create|Delete)
        WHERE n.author_id = $oid
        RETURN COUNT(n) as count
        """,
        params={
            "oid": oid,
        },
    )
    assert (
        records[0]["count"] > 0
    ), f"{records[0]['count']} nodes with author_id={oid} found."

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n)-[ver:HAS_VERSION|HAS_TERM|HAD_TERM|LATEST_DRAFT|LATEST_LOCKED|LATEST_RELEASED]->(m)
        WHERE ver.author_id = $oid
        RETURN COUNT(ver) as count
        """,
        params={
            "oid": oid,
        },
    )
    assert (
        records[0]["count"] > 0
    ), f"{records[0]['count']} relations with author_id={oid} found."


def test_remove_relationship_between_intervention_and_activity_instance_template_parameters():
    LOGGER.info(
        "Check if relationship between Intervention and ActivityInstance :TemplateParameter nodes exists"
    )

    records, _summary = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (:TemplateParameter {name:"Intervention"})-[rel]->(:TemplateParameter {name:"ActivityInstance"})
        RETURN rel
        """,
    )
    print(records)
    assert (
        len(records) == 0
    ), "The :HAS_PARENT_PARAMETER between Intervention and ActivityInstance :TemplateParameter nodes still exists"
