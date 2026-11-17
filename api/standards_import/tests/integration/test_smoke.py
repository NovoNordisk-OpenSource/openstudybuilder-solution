"""Proves the fixtures reach two separate, empty databases."""

from neomodel import db as neomodel_db

from standards_import.repositories.staging_db import run_query


def test_both_databases_are_reachable_and_empty(staging_session):
    staged, _ = neomodel_db.cypher_query("MATCH (n) RETURN count(n)")

    assert staged[0][0] == 0
    assert run_query(staging_session, "MATCH (n) RETURN count(n) AS n")[0]["n"] == 0


def test_they_are_not_the_same_database(staging_session):
    run_query(staging_session, "CREATE (:OnlyInStaging)")

    mdr, _ = neomodel_db.cypher_query("MATCH (n:OnlyInStaging) RETURN count(n)")

    assert mdr[0][0] == 0
    assert (
        run_query(staging_session, "MATCH (n:OnlyInStaging) RETURN count(n) AS n")[0][
            "n"
        ]
        == 1
    )
