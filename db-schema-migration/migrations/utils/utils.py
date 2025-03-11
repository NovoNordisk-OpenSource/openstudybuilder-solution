import logging
import math
import os
import re
import time
from typing import Any, List, Optional

import neo4j.exceptions
import requests
from neo4j import GraphDatabase
from neomodel import config as neoconfig
from neomodel import db

REGEX_SNAKE_CASE = r"^[a-z]+(_[a-z]+)*$"
REGEX_SNAKE_CASE_WITH_DOT = r"^[a-z.]+(_[a-z.]+)*$"


def get_logger(name: str = "Migrator"):
    loglevel = os.environ.get("LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {loglevel}")
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)-17s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(name)


logger = get_logger(os.path.basename(__file__))


def load_env(key: str, default: Optional[str] = None):
    value = os.environ.get(key)
    logger.info("ENV variable fetched: %s=%s", key, value)
    if value is None and default is None:
        logger.error("%s is not set and no default was provided", key)
        raise EnvironmentError(f"Failed because {key} is not set.")
    if value is not None:
        return value
    logger.warning("%s is not set, using default value: %s", key, default)
    return default


DATABASE_NAME = load_env("DATABASE_NAME")
DATABASE_URL = load_env("DATABASE_URL")
API_BASE_URL = load_env("API_BASE_URL", "http://localhost:8000")
API_HEADERS = {"User-Agent": "Data-Migrator"}
TOKEN_REFRESH_INTERVAL = 1200  # 20 minutes
LAST_TOKEN_REFRESH = -TOKEN_REFRESH_INTERVAL  # Force refresh on first call


def get_token():
    """Returns authentication token"""
    client_id = os.environ.get("CLIENT_ID", "")
    if client_id:
        client_secret = os.environ.get("CLIENT_SECRET")
        token_endpoint = os.environ.get("TOKEN_ENDPOINT")
        scope = os.environ.get("SCOPE")
        response = requests.post(
            token_endpoint,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
                "scope": scope,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        access_token = payload.get("access_token")
        if not access_token:
            msg = "missing access token from token payload"
            raise RuntimeError(msg)
        if not access_token:
            msg = "missing token type from token payload"
            raise RuntimeError(msg)
        return access_token
    return None


def make_api_header(token):
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Data-Migrator",
    }


# Refresh the token if it's older than TOKEN_REFRESH_INTERVAL
# pylint: disable=global-statement
def refresh_token():
    global LAST_TOKEN_REFRESH
    global API_HEADERS
    if time.time() - LAST_TOKEN_REFRESH > TOKEN_REFRESH_INTERVAL:
        logger.info("Refreshing token")
        API_HEADERS = make_api_header(get_token())
        LAST_TOKEN_REFRESH = time.time()


def get_db_connection():
    db_url = load_env("DATABASE_URL")
    db_name = load_env("DATABASE_NAME")
    create_db = load_env("CREATE_DB", "False")

    logger.info(
        "Getting db connection from ENV params [url, name]: [%s, %s]",
        db_url,
        db_name,
    )

    neoconfig.DATABASE_URL = db_url
    db.set_connection(neoconfig.DATABASE_URL)

    if db_name:
        neoconfig.DATABASE_URL = f"{db_url}/{db_name}"
        logger.info(
            "Creating database '%s' if it doesn't exist",
            db_name,
        )
        if create_db == "true":
            db.cypher_query("CREATE DATABASE $db IF NOT EXISTS", {"db": db_name})
        db.set_connection(neoconfig.DATABASE_URL)

    try_cnt = 1
    db_exists = False
    while try_cnt < 10 and not db_exists:
        try:
            try_cnt = try_cnt + 1
            db.cypher_query("MATCH (n) RETURN n LIMIT 3")
            db_exists = True
        except neo4j.exceptions.ClientError as exc:
            logger.info(
                "Database '%s' still not reachable (%s), pausing for 2 seconds",
                db_name,
                exc.code,
            )
            time.sleep(2)
    if not db_exists:
        raise RuntimeError(f"Database '{db_name}' is not available")

    return db


def execute_statements(statements: str):
    """Splits multiple cypher statements delimited by `;\n`
    and executes them one by one"""
    for statement in statements.split(";\n"):
        if statement.strip():
            logger.info("Cypher statement: %s", statement.strip())
            db.cypher_query(statement.strip())


def drop_indexes_and_constraints():
    """Drops all indexes and constraints"""
    constraints, _ = db.cypher_query("SHOW ALL CONSTRAINTS YIELD name")
    for constraint in constraints:
        drop_statement = "DROP CONSTRAINT " + constraint[0]
        print(drop_statement)
        db.cypher_query(drop_statement)

    indexes, _ = db.cypher_query(
        "SHOW ALL INDEXES YIELD name, type, indexProvider, labelsOrTypes, properties"
    )
    for (
        index_name,
        index_type,
        index_provider,
        index_labels,
        index_properties,
    ) in indexes:
        if (
            index_type == "LOOKUP"
            and index_provider.startswith("token-lookup")
            and index_labels is None
            and index_properties is None
        ):
            print(f"Keeping default index {index_name}")
        else:
            drop_statement = "DROP INDEX " + index_name
            print(drop_statement)
            db.cypher_query(drop_statement)


def snake_case(val: str) -> str:
    res = "_".join(
        re.sub(
            "([A-Z][a-z]+)", r" \1", re.sub("([A-Z]+)", r" \1", val.replace("-", " "))
        ).split()
    ).lower()
    return res.replace("__", "_")


def get_db_result_as_dict(row: List[Any], columns: List[str]) -> dict:
    item = {}
    for key, value in zip(columns, row):
        item[key] = value
    return item


def api_get(
    path: str, params: Optional[Any] = None, check_ok_status: bool | None = True
):
    """Issues http GET {path} request,
    asserts that http response status is 200 and returns the response."""
    refresh_token()
    url = API_BASE_URL + path
    logger.info("GET %s %s", url, params or "")
    res = requests.get(url, params=params, timeout=60, headers=API_HEADERS)
    if check_ok_status:
        assert res.status_code == 200, f"Response status {res.status_code} is not 200."
    return res


def api_get_paged(
    path: str,
    params: Optional[Any] = None,
    page_size: int = 100,
):
    """Issues http GET {path} request to fetch all items in pages of size {page_size},
    asserts that http response status is 200 and returns the response."""
    page_number = 1
    page_params = {
        "page_number": page_number,
        "page_size": page_size,
        "total_count": True,
    }
    if params is not None:
        page_params.update(params)
    logger.info("Fetch from %s, page: 1, page_size: %i", path, page_size)
    data = api_get(path, params=page_params)
    all_data = data.json()
    total = all_data["total"]

    # Get remaining pages
    page_params["total_count"] = False
    while page_size * page_number < total:
        page_number += 1
        page_params["page_number"] = page_number
        logger.info(
            "Fetch from %s, page: %i / %i",
            path,
            page_number,
            math.ceil(total / page_size),
        )
        data = api_get(path, params=page_params)
        additional = data.json()
        all_data["items"].extend(additional["items"])
    return all_data


def api_post(path: str, payload: dict, params: Optional[Any] = None):
    """Issues http POST request with specified payload.
    Returns the response."""
    refresh_token()
    url = API_BASE_URL + path
    logger.info("POST %s %s", url, params)
    res = requests.post(
        url, json=payload, params=params, timeout=60, headers=API_HEADERS
    )
    assert res.status_code in {
        201,
        204,
    }, f"Response status {res.status_code} is not in [201, 204]"
    return res


def api_patch(path: str, payload: dict, params: Optional[Any] = None):
    """Issues http PATCH request with specified payload.
    Returns the response."""
    url = API_BASE_URL + path
    logger.info("PATCH %s", url)
    res = requests.patch(
        url, json=payload, params=params, timeout=60, headers=API_HEADERS
    )
    assert res.status_code in [200], f"Response status {res.status_code} is not 200."
    return res


def parse_db_url(db_url):
    auth_info = re.search(r"//(.+?)@", db_url).group(1)
    username, password = auth_info.split(":")
    url = db_url.replace(auth_info + "@", "")
    return url, username, password


def get_db_driver():
    url, username, password = parse_db_url(DATABASE_URL)
    logger.info("Getting db connection to (%s)", url)
    driver = GraphDatabase.driver(url, auth=(username, password))
    return driver


def run_cypher_query(
    driver: neo4j.Neo4jDriver, query, params=None
) -> tuple[list[neo4j.Record], neo4j.ResultSummary]:
    with driver.session(database=DATABASE_NAME) as session:
        result: neo4j.Result = session.run(query, params)
        records = list(result)
        summary: neo4j.ResultSummary = result.consume()
        return records, summary


# Simple helper to print aligned columns to the console
def print_aligned(label, col_1, col_2, col_3):
    print(f"{label:12}{col_1:^9}{col_2:^9}{col_3:^9}")


# ---------- Console logging of counters ----------
def print_counters_table(counters: neo4j.SummaryCounters):
    if counters.contains_updates:
        print_aligned("Summary", "Created", "Deleted", "Set")
        print_aligned("Nodes", counters.nodes_created, counters.nodes_deleted, "")
        print_aligned(
            "Rels", counters.relationships_created, counters.relationships_deleted, ""
        )
        print_aligned("Properties", "", "", counters.properties_set)
        print_aligned("Labels", counters.labels_added, counters.labels_removed, "")
        print_aligned("Indexes", counters.indexes_added, counters.indexes_removed, "")
        print_aligned(
            "Constraints", counters.constraints_added, counters.constraints_removed, ""
        )
    else:
        print("No changes made")


def print_query(summary: neo4j.ResultSummary):
    print("---- Query: --------------------------------")
    print(summary.query)
    print(f":params {summary.parameters}")
    print("--------------------------------------------")
