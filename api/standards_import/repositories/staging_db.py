"""Connection handling for the CDISC staging database.

The staging database is a second Neo4j database, separate from the MDR one that
neomodel is bound to. Its model is bespoke and query-shaped rather than
object-shaped, so it is accessed with the raw driver instead of neomodel.
"""

import logging
import urllib.parse
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, NewType, cast
from weakref import WeakSet

from neo4j import Driver, GraphDatabase, Session, exceptions as neo4j_exceptions

from common.database import database_uri
from common.exceptions import InternalServerError
from standards_import.config import settings

log = logging.getLogger(__name__)

_driver: Driver | None = None

# A plain `neo4j.Session` carries no information about which database it is bound
# to, so nothing stops a staging repository from accepting a session someone pulled
# off the MDR connection by mistake. `StagingSession` makes that mix-up a type error
# instead of a runtime surprise — every staging repository takes one of these, not a
# bare `Session`, and the only way to get one is `staging_session()` below.
StagingSession = NewType("StagingSession", Session)

# Tracks every session `staging_session()` has actually issued, so a `cast()` or
# `# type: ignore` cannot forge a `StagingSession` and sneak it past `run_query`/
# `run_query_autocommit` — the type checker can be argued with, this cannot. `WeakSet`
# rather than a plain `set`: a session already closed and dropped by its caller must
# not be kept alive forever just because this module remembered it.
_issued_sessions: WeakSet[Session] = WeakSet()


def _get_driver() -> Driver:
    """Returns the staging database driver, creating it on first use."""

    global _driver  # pylint: disable=global-statement

    if _driver is None:
        if not settings.staging_neo4j_dsn:
            raise InternalServerError(
                msg="Neither STANDARDS_IMPORT_STAGING_DSN nor NEO4J_DSN is set, "
                "so the CDISC staging database cannot be reached."
            )

        parsed = urllib.parse.urlparse(settings.staging_neo4j_dsn)
        _driver = GraphDatabase.driver(
            database_uri(settings.staging_neo4j_dsn),
            auth=(parsed.username or "neo4j", parsed.password or ""),
            database=parsed.path.lstrip("/") or "neo4j",
            max_connection_lifetime=settings.staging_connection_lifetime,
            liveness_check_timeout=settings.staging_liveness_check_timeout,
            keep_alive=True,
        )
        log.info(
            "CDISC staging database driver created for %s",
            database_uri(settings.staging_neo4j_dsn),
        )

    return _driver


def close_driver() -> None:
    """Closes the staging database driver, if one was opened."""

    global _driver  # pylint: disable=global-statement

    if _driver is not None:
        _driver.close()
        _driver = None


@contextmanager
def staging_session() -> Iterator[StagingSession]:
    """Yields a session against the staging database."""

    session = _get_driver().session()
    _issued_sessions.add(session)
    try:
        yield cast(StagingSession, session)
    finally:
        session.close()


def run_query(
    session: StagingSession, query: str, parameters: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Runs a single query in its own transaction and returns the records as dicts."""

    if session not in _issued_sessions:
        raise InternalServerError(
            msg="This session was not issued by staging_session() — a StagingSession "
            "cannot be conjured by casting a plain neo4j.Session, however convincing "
            "the type checker found the argument."
        )

    try:
        with session.begin_transaction() as tx:
            return tx.run(query, parameters).data()
    except neo4j_exceptions.Neo4jError as exc:
        raise InternalServerError(msg=f"Staging database query failed: {exc}") from exc


def run_query_autocommit(
    session: StagingSession, query: str, parameters: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Runs a query outside an explicit transaction.

    Needed for `CALL { … } IN TRANSACTIONS`, which Neo4j rejects inside one.
    """

    if session not in _issued_sessions:
        raise InternalServerError(
            msg="This session was not issued by staging_session() — a StagingSession "
            "cannot be conjured by casting a plain neo4j.Session, however convincing "
            "the type checker found the argument."
        )

    try:
        return session.run(query, parameters).data()
    except neo4j_exceptions.Neo4jError as exc:
        raise InternalServerError(msg=f"Staging database query failed: {exc}") from exc


def to_native(value: Any) -> Any:
    """Converts one value the raw driver returned to its native Python equivalent.

    The raw driver hands back its own temporal types (`neo4j.time.DateTime` and
    friends) rather than the `datetime` module's — harmless until a Pydantic model
    field expects the latter and rejects the former.
    """

    return value.to_native() if hasattr(value, "to_native") else value
