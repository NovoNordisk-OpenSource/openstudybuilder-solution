import logging
import os
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple

from neomodel import config as neo4j_config
from neomodel import db

from tests.endpoints import GET_ENDPOINTS, GET_ENDPOINTS_CONSUMER_API


def get_logger(name: str = "Locust"):
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


@dataclass
class Params:

    STUDY_ID = load_env("STUDY_ID", "Study_000039")
    STUDY_NUMBER = load_env("STUDY_NUMBER", "3003")
    LIBRARY_NAME = load_env("LIBRARY_NAME", "SNOMED")
    CT_CODELIST_UID = load_env("CT_CODELIST_UID", "CTCodelist_000001")
    CT_TERM_UID = load_env("CT_TERM_UID", "CTTerm_000001")
    PROJECT_ID = load_env("PROJECT_ID", "999")

    API_BASE_URL = load_env("API_BASE_URL", "http://localhost:8000")
    CONSUMER_API_BASE_URL = load_env("CONSUMER_API_BASE_URL", "http://localhost:8008")
    # No default — DATABASE_URL embeds the Neo4j password, so falling back to a
    # shared-default literal would re-introduce a hardcoded credential. load_env
    # raises EnvironmentError when the variable is unset and no default is given.
    DATABASE_URL = load_env("DATABASE_URL")
    DATABASE_NAME = load_env("DATABASE_NAME", "neo4j")
    TARGET_CONSUMER_API = load_env("TARGET_CONSUMER_API", "False").lower() == "true"
    PREFETCH_ENDPOINTS = load_env("PREFETCH_ENDPOINTS", "False").lower() == "true"
    AUTO_DETECT_BIG_STUDY = load_env("AUTO_DETECT_BIG_STUDY", "True").lower() == "true"

    API_HEADERS = {
        "Authorization": f'Bearer {load_env("API_AUTH_TOKEN")}',
        "User-Agent": "Locust",
    }

    PERFORMANCE_THRESHOLD = int(load_env("PERFORMANCE_THRESHOLD", "2000"))


neo4j_config.DATABASE_URL = Params.DATABASE_URL
neo4j_config.DATABASE_NAME = Params.DATABASE_NAME


def get_now() -> str:
    """Returns current time in UTC timezone in ISO-8601 format"""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z")


def get_all_endpoints(target_consumer_api: bool = False) -> list[Tuple[str, str]]:
    """Returns list of tuples [endpoint-url, query-params]
    using the endpoints list defined in the `GET_ENDPOINTS` or `GET_ENDPOINTS_CONSUMER_API` list.
    """

    endpoints = GET_ENDPOINTS_CONSUMER_API if target_consumer_api else GET_ENDPOINTS
    return [replace_placeholder_values(endpoint) for endpoint in endpoints]


def get_random_endpoint(target_consumer_api: bool = False) -> Tuple[str, str]:
    """Returns tuple [endpoint-url, query-params]
    by randomly choosing one of the endpoints defined in the `GET_ENDPOINTS` or `GET_ENDPOINTS_CONSUMER_API` list.
    """

    endpoints = GET_ENDPOINTS_CONSUMER_API if target_consumer_api else GET_ENDPOINTS
    endpoint = random.choice(endpoints)

    return replace_placeholder_values(endpoint)


def replace_placeholder_values(endpoint: Tuple[str, dict]) -> Tuple[str, str]:
    """
    Replaces the following placeholder values in endpoint url/params with appropriate values:
     - <now> => current UTC timestamp
     - /{study_uid} => `/STUDY_ID` (using `STUDY_ID` ENV variable)
     - /{study_number} => `/STUDY_NUMBER` (using `STUDY_NUMBER` ENV variable)
     - /studies/{uid} => `/studies/STUDY_ID` (using `STUDY_ID` ENV variable)
     - /{library} => `/LIBRARY_NAME` (using `LIBRARY_NAME` ENV variable)
     - /{codelist_uid} => `/CT_CODELIST_UID` (using `CT_CODELIST_UID` ENV variable)
     - /ct/terms/{term_uid} => `/ct/terms/CT_TERM_UID` (using `CT_TERM_UID` ENV variable)

    Returns tuple: [endpoint-url, query-params]
    """
    url = (
        endpoint[0]
        .replace("/studies/{uid}", f"/studies/{Params.STUDY_ID}")
        .replace("/{study_uid}", f"/{Params.STUDY_ID}")
        .replace("/{study_number}", f"/{Params.STUDY_NUMBER}")
        .replace("/{library}", f"/{Params.LIBRARY_NAME}")
        .replace("/{codelist_uid}", f"/{Params.CT_CODELIST_UID}")
        .replace("/ct/terms/{term_uid}", f"/ct/terms/{Params.CT_TERM_UID}")
    )

    params = endpoint[1]
    if params:
        for key, val in params.items():
            if val == "<now>":
                params[key] = get_now()
            if val == "{study_number}":
                params[key] = Params.STUDY_NUMBER
            if val == "{project_id}":
                params[key] = Params.PROJECT_ID
            if val == "{library}":
                params[key] = Params.LIBRARY_NAME
            if val == "{codelist_uid}":
                params[key] = Params.CT_CODELIST_UID
            if val == "{term_uid}":
                params[key] = Params.CT_TERM_UID

    return url, params


def pretty_print_endpoint(host: str, url: str, params: dict) -> str:
    """Returns a formatted string of the endpoint URL and query parameters"""
    if params:
        query_params_str = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{host}{url}?{query_params_str}"
    return f"{host}{url}"


# pylint: disable=too-many-arguments,too-many-positional-arguments
def query(
    cypher_query,
    params: dict = None,
    handle_unique: bool = True,
    retry_on_session_expire: bool = False,
    resolve_objects: bool = False,
    to_dict_list: bool = True,
):
    """
    Wraps `db.cypher_query()`

    Returns:
    list[dict] | tuple: If `to_dict_list` is True, returns a list of dictionaries representing the query results.
                        If `to_dict_list` is False, returns a tuple containing the rows and columns from the query.
    """
    rows, columns = db.cypher_query(
        query=cypher_query,
        params=params,
        handle_unique=handle_unique,
        retry_on_session_expire=retry_on_session_expire,
        resolve_objects=resolve_objects,
    )

    if to_dict_list:
        return [get_db_result_as_dict(row, columns) for row in rows]

    return rows, columns


def get_db_result_as_dict(row: list[any], columns: list[str]) -> dict:
    item = {}
    for key, value in zip(columns, row):
        item[key] = value
    return item


def get_big_study_id() -> str:
    """Returns a study id of the study with the biggest number of activities * visits"""

    cypher_query = """
    MATCH (sr:StudyRoot)-[:LATEST]-(sv:StudyValue)-[:HAS_STUDY_ACTIVITY]-(a:StudyActivity)
    WITH sr, sv, a
    MATCH (sr:StudyRoot)-[:LATEST]-(sv:StudyValue)-[:HAS_STUDY_VISIT]-(v:StudyVisit)
    WITH sr, sv, a, v
    RETURN  sr.uid as study_uid,
            sv.study_number as study_number,
            count(distinct a) as total_activities,
            count(distinct v) as total_visits
    ORDER BY total_activities * total_visits DESC
    """
    res = query(cypher_query, to_dict_list=True)
    study_uid = res[0]["study_uid"]
    study_number = res[0]["study_number"]
    total_activities = res[0]["total_activities"]
    total_visits = res[0]["total_visits"]

    Params.STUDY_ID = study_uid
    Params.STUDY_NUMBER = study_number

    print(
        f"Study with the biggest number of activities * visits: {study_uid} ({total_activities} activities, {total_visits} visits)"
    )
    return study_uid
