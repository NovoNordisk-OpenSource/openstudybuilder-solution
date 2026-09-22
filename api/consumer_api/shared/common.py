import logging
import os
import urllib.parse
from enum import Enum
from typing import Any

from fastapi import Query
from neomodel import db

from common.config import settings
from common.exceptions import ValidationException
from common.utils import filter_sort_valid_keys_re, get_db_result_as_dict

log = logging.getLogger(__name__)


class SortByType(Enum):
    STRING = "string"
    NUMBER = "number"


def query(
    cypher_query,
    params: dict[Any, Any] | None = None,
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
    if params is None:
        params = {}

    try:
        rows, columns = db.cypher_query(
            query=cypher_query,
            params=params,
            handle_unique=handle_unique,
            retry_on_session_expire=retry_on_session_expire,
            resolve_objects=resolve_objects,
        )
    except Exception as e:
        raise ValidationException(msg=f"Database query failed: {e}") from e

    if to_dict_list:
        return [get_db_result_as_dict(row, columns) for row in rows]

    return rows, columns


def urlencode_link(link: str) -> str:
    """URL encodes a link"""

    url = urllib.parse.urlparse(link)
    query_params = urllib.parse.parse_qs(url.query, keep_blank_values=True)

    url = url._replace(query=urllib.parse.urlencode(query_params, True))
    return urllib.parse.urlunparse(url)


def db_pagination_clause(page_size: int, page_number: int) -> str:
    # Ensure Cypher injection would not be possible even if values weren't integer types
    if not isinstance(page_size, int) or not isinstance(page_number, int):
        raise TypeError("Expected page_size and page_number to be integers")

    return f"SKIP {page_number - 1} * {page_size} LIMIT {page_size}"


def db_sort_clause(
    sort_by: str,
    sort_order: str = "ASC",
    sort_by_type: SortByType = SortByType.STRING,
    secondary_sort_fields: str = "uid",
) -> str:
    # Ensure Cypher injection would not be exploitable even if sort_by keys were not checked
    if not filter_sort_valid_keys_re.fullmatch(sort_by):
        raise ValidationException(msg=f"Invalid sorting key: {sort_by}")

    if sort_by_type == SortByType.NUMBER:
        primary_sort = f"toFloat({sort_by}) {sort_order}"
    else:
        primary_sort = f"toLower(toString({sort_by})) {sort_order}"

    # Add hash of all relevant properties as secondary sort for consistent ordering
    if secondary_sort_fields:
        secondary_sort = f"apoc.util.md5([{secondary_sort_fields}]) ASC"
        return f"ORDER BY {primary_sort}, {secondary_sort}"

    return f"ORDER BY {primary_sort}"


def get_api_version() -> str:
    version_path = os.path.join("./consumer_api", "apiVersion")
    with open(version_path, "r", encoding="utf-8") as file:
        return file.read().strip()


# Reusable Query parameter for page_number with maximum constraint
PAGE_NUMBER_QUERY = Query(
    ge=1,
    le=settings.max_page_number,
    description="Page number of the returned list of entities. Must be between 1 and the maximum allowed page number.",
)

# Reusable Query parameter for page_size with maximum constraint (allows page_size=0 for "all rows")
PAGE_SIZE_QUERY = Query(
    ge=1,
    le=settings.max_page_size,
    description="Number of items to be returned per page. Must be between 1 and the maximum allowed page size.",
)
