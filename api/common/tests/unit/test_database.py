import copy
from contextvars import copy_context
from typing import Any
from unittest.mock import MagicMock

import pytest
from neo4j import Driver, Query, Session
from neomodel import db, get_config

from common.auth.user import transaction_metadata
from common.database import (
    TxMetadataDriver,
    TxMetadataSession,
    configure_app_database,
    configure_database,
)

METADATA = {"user_id": "some-user"}


def no_metadata() -> dict[str, Any]:
    return {}


def failing_metadata() -> dict[str, Any]:
    raise AttributeError("'NoneType' object has no attribute 'id'")


@pytest.fixture(name="session")
def fixture_session():
    return MagicMock(spec=Session)


@pytest.fixture(name="restore_neomodel_config")
def fixture_restore_neomodel_config():
    config = get_config()
    names = ("driver", "database_name", "database_url", "soft_cardinality_check")
    saved = {name: getattr(config, name) for name in names}
    yield
    for name, value in saved.items():
        setattr(config, name, value)


def test_auto_commit_query_carries_metadata(session):
    TxMetadataSession(session, lambda: METADATA).run("RETURN $x", {"x": 1})

    query, parameters = session.run.call_args.args
    assert isinstance(query, Query)
    assert query.text == "RETURN $x"
    assert query.metadata == METADATA
    assert parameters == {"x": 1}


def test_auto_commit_query_without_metadata_is_unchanged(session):
    TxMetadataSession(session, no_metadata).run("RETURN 1")

    session.run.assert_called_once_with("RETURN 1", None)


def test_query_object_is_passed_through_unchanged(session):
    query = Query("RETURN 1", metadata={"caller": "own"})

    TxMetadataSession(session, lambda: METADATA).run(query)

    session.run.assert_called_once_with(query, None)


def test_explicit_transaction_carries_metadata(session):
    TxMetadataSession(session, lambda: METADATA).begin_transaction(timeout=5)

    session.begin_transaction.assert_called_once_with(metadata=METADATA, timeout=5)


def test_explicit_transaction_merges_metadata_from_caller(session):
    TxMetadataSession(session, lambda: METADATA).begin_transaction(
        metadata={"extra": 1}
    )

    session.begin_transaction.assert_called_once_with(
        metadata={"user_id": "some-user", "extra": 1}, timeout=None
    )


def test_explicit_transaction_metadata_from_caller_takes_precedence(session):
    TxMetadataSession(session, lambda: METADATA).begin_transaction(
        metadata={"user_id": "caller"}
    )

    session.begin_transaction.assert_called_once_with(
        metadata={"user_id": "caller"}, timeout=None
    )


def test_explicit_transaction_without_metadata(session):
    TxMetadataSession(session, no_metadata).begin_transaction()

    session.begin_transaction.assert_called_once_with(metadata=None, timeout=None)


def test_failing_metadata_does_not_fail_auto_commit_query(session, caplog):
    TxMetadataSession(session, failing_metadata).run("RETURN 1")

    session.run.assert_called_once_with("RETURN 1", None)
    assert "Running Neo4j transaction without metadata" in caplog.text


def test_failing_metadata_does_not_fail_explicit_transaction(session):
    TxMetadataSession(session, failing_metadata).begin_transaction(
        metadata={"extra": 1}
    )

    session.begin_transaction.assert_called_once_with(
        metadata={"extra": 1}, timeout=None
    )


def test_session_context_manager_yields_proxy_and_closes_session(session):
    proxy = TxMetadataSession(session, no_metadata)

    with proxy as entered:
        assert entered is proxy

    session.__exit__.assert_called_once_with(None, None, None)


def test_session_delegates_other_attributes(session):
    TxMetadataSession(session, no_metadata).last_bookmarks()

    session.last_bookmarks.assert_called_once_with()


def test_session_copy_delegates_to_same_session(session):
    copy.copy(TxMetadataSession(session, no_metadata)).last_bookmarks()

    session.last_bookmarks.assert_called_once_with()


def test_driver_copy_delegates_to_same_driver():
    driver = MagicMock(spec=Driver)

    copy.copy(TxMetadataDriver(driver, no_metadata)).close()

    driver.close.assert_called_once_with()


def test_driver_wraps_sessions_and_delegates_other_attributes():
    driver = MagicMock(spec=Driver)
    proxy = TxMetadataDriver(driver, lambda: METADATA)

    proxy.session(database="mydb").run("RETURN 1")
    proxy.close()

    driver.session.assert_called_once_with(database="mydb")
    assert driver.session.return_value.run.call_args.args[0].metadata == METADATA
    driver.close.assert_called_once_with()


@pytest.mark.usefixtures("restore_neomodel_config")
def test_configure_database_routes_neomodel_through_tx_metadata_driver():
    driver = configure_database(
        "bolt://neo4j:password@localhost:7687/mydb", tx_metadata=lambda: METADATA
    )
    try:
        assert isinstance(driver, Driver)
        assert isinstance(get_config().driver, TxMetadataDriver)
    finally:
        driver.close()


@pytest.mark.usefixtures("restore_neomodel_config")
def test_configure_app_database_initializes_neomodel_with_user_metadata(monkeypatch):
    run_cypher_query = MagicMock(
        return_value=([["5.26.0", "enterprise"]], ("version", "edition"))
    )
    monkeypatch.setattr(db, "_run_cypher_query", run_cypher_query)
    startup_context = copy_context()
    startup_context.run(setattr, db, "driver", None)
    driver = startup_context.run(
        configure_app_database, "bolt://neo4j:password@localhost:7687/mydb"
    )
    try:
        neomodel_driver = get_config().driver
        assert isinstance(neomodel_driver, TxMetadataDriver)
        assert neomodel_driver._tx_metadata is transaction_metadata
        assert neomodel_driver._driver is driver

        for _ in range(3):
            startup_context.copy().run(db.cypher_query, "RETURN 1")

        queries = [call.args[1] for call in run_cypher_query.call_args_list]
        assert queries == [
            "CALL dbms.components() yield versions, edition return versions[0], edition",
            "RETURN 1",
            "RETURN 1",
            "RETURN 1",
        ]
        assert startup_context.run(lambda: db.driver) is neomodel_driver
    finally:
        driver.close()


@pytest.mark.usefixtures("restore_neomodel_config")
def test_configure_database_without_tx_metadata_uses_plain_driver():
    driver = configure_database("bolt://neo4j:password@localhost:7687/mydb")
    try:
        assert get_config().driver is driver
    finally:
        driver.close()
