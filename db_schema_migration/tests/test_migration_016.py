import json
import os

import pytest

from migrations import migration_016
from migrations.utils.utils import (
    api_get_paged,
    execute_statements,
    get_db_connection,
    get_db_driver,
    get_logger,
    run_cypher_query,
)
from tests import common
from tests.data.db_before_migration_016 import TEST_DATA
from tests.utils.utils import clear_db

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=protected-access
# pylint: disable=broad-except

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

db = get_db_connection()
DB_DRIVER = get_db_driver()
logger = get_logger(os.path.basename(__file__))


@pytest.fixture(scope="module")
def initial_data():
    """Insert test data"""
    clear_db()
    execute_statements(TEST_DATA)


@pytest.fixture(scope="module")
def migration(initial_data):
    # Run migration
    migration_016.main()


def test_indexes_and_constraints(migration):
    common.test_indexes_and_constraints(db, logger)


def test_ct_config_values(migration):
    common.test_ct_config_values(db, logger)


def test_migrate_ct(migration):
    logger.info("Check CT migration")

    # Check that all non-CT nodes are connected to Terms through CTTermContext
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (us:CTTermRoot)<-[migrate_rel]-(them:!(CTTermRoot|CTCodelistRoot|CTTermNameRoot|CTTermAttributesRoot|Library|CTTermContext|CTCodelistTerm))
        RETURN count(DISTINCT migrate_rel) as count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} relationships between CTTermRoot and non-CT nodes."""

    # Check that CTTermContext nodes are all connected to one CTTermRoot and one CTCodelistRoot
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (ctx:CTTermContext)
        WHERE 
            NOT EXISTS ((ctx)-->(:CTCodelistRoot)) 
            OR NOT EXISTS ((ctx)-->(:CTTermRoot))
        RETURN count(*) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} malformed CTTermContext nodes (missing relationship)."""

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (ctx:CTTermContext)
        WHERE 
            EXISTS ((:CTCodelistRoot)<--(ctx)-->(:CTCodelistRoot))
            OR EXISTS ((:CTTermRoot)<--(ctx)-->(:CTTermRoot))
        RETURN count(*) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} malformed CTTermContext nodes (too many relationships)."""

    # Check that all Term-Term relationships were migrated
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH p=(:!CTTermRoot)-[:HAS_PARENT_TYPE|HAS_PARENT_SUB_TYPE|HAS_PREDECESSOR]-(:!CTTermRoot)
        RETURN count(p) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} non-migrated term-to-term relationships."""

    # Check that all obsolete relationships and properties were removed
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH p=(cl:CTCodelistRoot)-[ht:HAS_TERM]->(us:CTTermRoot) RETURN count(p) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} relationships between CTCodelistRoot and CTTermRoot."""

    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n:CTTermAttributesValue) WHERE n.code_submission_value IS NOT NULL RETURN count(n) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} CTTermAttributesValue nodes with code_submission_value property."""

    # Check there are no _sideload nodes anymore
    records, _ = run_cypher_query(
        DB_DRIVER,
        """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label CONTAINS "_sideload")
        RETURN count(DISTINCT n) AS count
        """,
    )
    assert (
        records[0]["count"] == 0
    ), f"""Found {records[0]["count"]} nodes with _sideload label suffix."""


@pytest.mark.order(after="test_migrate_ct")
def test_repeat_migrate_ct(migration):
    assert not migration_016.migrate_ct(DB_DRIVER, logger)


def test_migrate_ct_with_test_data(migration):

    logger.info(
        "CT migration, check that API returns the expected replies for migrated test data"
    )
    # Get elements from the API and make sure they are properly returned
    # General checks
    codelists_path = "/ct/codelists"
    terms_path = "/ct/terms"
    payload = api_get_paged(
        codelists_path,
        params={
            "library_name": "CDISC",
            "total_count": True,
        },
    )
    codelists = payload["items"]
    total_count = payload["total"]

    assert len(codelists) == 43, f"Expected 43 codelists, got {len(codelists)}"
    assert total_count == 43, f"Expected total count of 43, got {total_count}"

    payload = api_get_paged(
        codelists_path,
        params={
            "library_name": "Sponsor",
            "total_count": True,
        },
    )
    codelists = payload["items"]
    total_count = payload["total"]

    assert len(codelists) == 9, f"Expected 9 codelists, got {len(codelists)}"
    assert total_count == 9, f"Expected total count of 9, got {total_count}"

    payload = api_get_paged(
        terms_path,
        params={
            "library_name": "CDISC",
            "total_count": True,
        },
    )
    term = payload["items"]
    total_count = payload["total"]

    assert len(term) == 20, f"Expected 20 terms, got {len(term)}"
    assert total_count == 20, f"Expected total count of 20, got {total_count}"

    payload = api_get_paged(
        terms_path,
        params={
            "library_name": "Sponsor",
            "total_count": True,
        },
    )
    term = payload["items"]
    total_count = payload["total"]

    assert len(term) == 8, f"Expected 8 terms, got {len(term)}"
    assert total_count == 8, f"Expected total count of 8, got {total_count}"

    # Check Terms are properly attached to their codelists
    # Even when there are multiple, and one of them is Sponsor
    payload = api_get_paged(
        terms_path,
        params={"filters": json.dumps({"term_uid": {"v": ["C48660"], "op": "eq"}})},
    )
    term = payload["items"][0]
    assert len(term["codelists"]) == 3, "Expected C48660 term to be in 3 codelists"
    codelist_uids = [cl["codelist_uid"] for cl in term["codelists"]]
    codelist_term_submission_values = [
        cl["submission_value"] for cl in term["codelists"]
    ]
    assert "C66742" in codelist_uids
    assert "C150810" in codelist_uids
    assert "CTCodelist_000007" in codelist_uids
    assert codelist_term_submission_values == ["NA", "NA", "NA"]

    # Sponsor term, attached to multiple codelists, including a CDISC one
    payload = api_get_paged(
        terms_path,
        params={
            "filters": json.dumps({"term_uid": {"v": ["CTTerm_001123"], "op": "eq"}})
        },
    )
    term = payload["items"][0]
    assert (
        len(term["codelists"]) == 2
    ), "Expected CTTerm_001123 term to be in 2 codelists"
    codelist_uids = [cl["codelist_uid"] for cl in term["codelists"]]
    codelist_term_submission_values = [
        cl["submission_value"] for cl in term["codelists"]
    ]
    assert "CTCodelist_000002" in codelist_uids
    assert "C71620" in codelist_uids
    assert codelist_term_submission_values == ["NO UNIT", "NO UNIT"]
