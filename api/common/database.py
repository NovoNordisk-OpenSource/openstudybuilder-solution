import logging
import urllib.parse
from collections.abc import Callable
from typing import Any, Self

from neo4j import Driver, GraphDatabase, Query, Result, Session, Transaction
from neomodel import config as neomodel_config, db, get_config

from common.auth.user import transaction_metadata
from common.config import settings

log = logging.getLogger(__name__)

# Teach urljoin that Neo4j DSN URLs like bolt:// and neo4j:// semantically similar to http://
for scheme in ("bolt", "bolt+s", "neo4j", "neo4j+s"):
    urllib.parse.uses_relative.append(scheme)
    urllib.parse.uses_netloc.append(scheme)

TxMetadataProvider = Callable[[], dict[str, Any]]


class TxMetadataSession:
    """Session proxy that attaches transaction metadata to every transaction it runs"""

    def __init__(self, session: Session, tx_metadata: TxMetadataProvider):
        self._session = session
        self._tx_metadata = tx_metadata

    def run(
        self,
        query: str | Query,
        parameters: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Result:
        # Auto-commit transaction: metadata can only travel on a Query object.
        # A Query from the caller passes through without the user's metadata:
        # neomodel only ever sends query strings, and nothing else builds one.
        if isinstance(query, str) and (metadata := self._metadata()):
            query = Query(query, metadata=metadata)
        return self._session.run(query, parameters, **kwargs)

    def begin_transaction(
        self,
        metadata: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Transaction:
        # Explicit transaction (neomodel's db.transaction): metadata is fixed when it begins
        metadata = {**self._metadata(), **(metadata or {})}
        return self._session.begin_transaction(
            metadata=metadata or None, timeout=timeout
        )

    def _metadata(self) -> dict[str, Any]:
        # Metadata only describes the transaction, so it must never fail it
        try:
            return self._tx_metadata()
        except Exception:
            log.warning("Running Neo4j transaction without metadata", exc_info=True)
            return {}

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self._session.__exit__(*exc_info)

    def __getattr__(self, name: str) -> Any:
        # Unset while copy or pickle rebuilds the proxy; delegating it would recurse
        if name == "_session":
            raise AttributeError(name)
        return getattr(self._session, name)


class TxMetadataDriver:
    """Driver proxy whose sessions attach transaction metadata to every transaction"""

    def __init__(self, driver: Driver, tx_metadata: TxMetadataProvider):
        self._driver = driver
        self._tx_metadata = tx_metadata

    def session(self, **config: Any) -> TxMetadataSession:
        return TxMetadataSession(self._driver.session(**config), self._tx_metadata)

    def __getattr__(self, name: str) -> Any:
        # Unset while copy or pickle rebuilds the proxy; delegating it would recurse
        if name == "_driver":
            raise AttributeError(name)
        return getattr(self._driver, name)


def configure_database(
    neo4j_dsn: str,
    /,
    soft_cardinality_check: bool = True,
    tx_metadata: TxMetadataProvider | None = None,
    **driver_options,
) -> Driver:
    parsed = urllib.parse.urlparse(neo4j_dsn)

    if parsed.scheme not in (
        "bolt",
        "neo4j",
        "bolt+s",
        "neo4j+s",
        "bolt+ssc",
        "neo4j+ssc",
    ):
        raise ValueError(f"Unsupported scheme in NEO4J_DSN: {parsed.scheme}")

    database_name = parsed.path.lstrip("/") or "neo4j"
    username = parsed.username or "neo4j"
    password = parsed.password or ""

    driver = GraphDatabase.driver(
        database_uri(neo4j_dsn),
        auth=(username, password),
        database=database_name,
        **driver_options,
    )

    # neomodel runs every query through the wrapper; callers keep the plain driver
    neomodel_config.DRIVER = (
        TxMetadataDriver(driver, tx_metadata) if tx_metadata else driver
    )
    neomodel_config.DATABASE_NAME = database_name
    neomodel_config.DATABASE_URL = None
    neomodel_config.SOFT_CARDINALITY_CHECK = soft_cardinality_check

    return driver


def configure_app_database(neo4j_dsn: str) -> Driver:
    """Configures neomodel the way every API app runs: tuned driver, user metadata.

    Initialize the connection here so requests inherit its driver and server metadata.
    """

    driver = configure_database(
        neo4j_dsn,
        soft_cardinality_check=settings.soft_cardinality_check,
        tx_metadata=transaction_metadata,
        max_connection_lifetime=settings.neo4j_connection_lifetime,
        liveness_check_timeout=settings.neo4j_liveness_check_timeout,
    )
    db.set_connection(driver=get_config().driver)
    return driver


def database_uri(dsn: str) -> str:
    parsed = urllib.parse.urlparse(dsn)
    return f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"


def log_rbac_guard_result(guard_name: str, isolated: bool) -> None:
    """Logs whether a Neo4j RBAC-based isolation guard is actually in effect.

    Defence in depth only — nothing in either app may depend on this for
    correctness. An environment on Neo4j Community, or one where the `mdr`/`staging`
    roles from `db/init_neo4j.py` have not been provisioned yet, is visibly degraded
    here rather than silently unguarded.
    """

    if isolated:
        log.info("RBAC guard active: %s", guard_name)
    else:
        log.warning(
            "RBAC guard NOT active: %s. This connection is not restricted by Neo4j "
            "role-based access control — either running on Neo4j Community (a "
            "Enterprise-only feature) or the mdr/staging roles have not been "
            "provisioned yet (see db/README.md).",
            guard_name,
        )
