import logging
import urllib.parse

from neo4j import Driver, GraphDatabase
from neomodel import config as neomodel_config

log = logging.getLogger(__name__)

# Teach urljoin that Neo4j DSN URLs like bolt:// and neo4j:// semantically similar to http://
for scheme in ("bolt", "bolt+s", "neo4j", "neo4j+s"):
    urllib.parse.uses_relative.append(scheme)
    urllib.parse.uses_netloc.append(scheme)


def configure_database(
    neo4j_dsn: str, /, soft_cardinality_check: bool = True, **driver_options
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

    neomodel_config.DRIVER = driver
    neomodel_config.DATABASE_NAME = database_name
    neomodel_config.DATABASE_URL = None
    neomodel_config.SOFT_CARDINALITY_CHECK = soft_cardinality_check

    return driver


def database_uri(dsn: str) -> str:
    parsed = urllib.parse.urlparse(dsn)
    return f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
