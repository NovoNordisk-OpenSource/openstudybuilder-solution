from textwrap import dedent
from typing import Any

from neomodel import db

from common.utils import get_db_result_as_dict, validate_max_skip_clause


def _query(
    node_name: str,
    fields: list[str],
    page_number: int,
    page_size: int,
    sort_by: str,
    search: str | None,
    op: str,
) -> tuple[list[dict[str, str]], int]:
    """
    Generic query function to get paginated results from a given node.

    :param node_name: Name of the node to query
    :param fields: List of fields to return
    :param page_number: Page number
    :param page_size: Number of items per page
    :param sort_by: Comma separated list of fields to sort by
    :param search: Search term to filter results
    :param op: Operator to use for filtering.
    :return: Tuple of list of results and total count
    """

    validate_max_skip_clause(page_number=page_number, page_size=page_size)

    params: dict[str, list[Any] | str | int] = {}

    operator = "CONTAINS" if op == "co" else "="

    where_stmt = ""

    if search is not None and search.strip() != "":
        for key in fields:
            if where_stmt:
                where_stmt += f"OR toLower(n.{key}) {operator} ${key} "
                params[key] = search.casefold()
            else:
                where_stmt += f"WHERE (toLower(n.{key}) {operator} ${key} "
                params[key] = search.casefold()
        where_stmt += ") "

    exclude_old_stmt = """
    MATCH (n)<--(value)<-[:LATEST]-(root)
    WHERE any(
        label IN labels(value)
            WHERE label ENDS WITH 'Value'
    )
    AND any(
        label IN labels(root)
            WHERE NOT label STARTS WITH 'Deleted'
            AND label ENDS WITH 'Root'
            AND label <> 'OdmRoot'
    )
    """

    if sort_by:
        order_clauses = []
        for sort_field in sort_by.split(","):
            sort_field = sort_field.strip()

            direction = "ASC"
            field_name = sort_field

            if sort_field.startswith("-"):
                direction = "DESC"
                field_name = sort_field[1:]

            if field_name in fields:
                order_clauses.append(f"toLower(n.{field_name}) {direction}")

        if order_clauses:
            order_stmt = "ORDER BY " + ", ".join(order_clauses)
        else:
            order_stmt = f"ORDER BY toLower(n.{fields[0]})"
    else:
        order_stmt = f"ORDER BY toLower(n.{fields[0]})"

    if page_size > 0:
        limit_stmt = "SKIP $skip LIMIT $limit"
        params["skip"] = page_size * (page_number - 1)
        params["limit"] = page_size
    else:
        limit_stmt = ""

    results, columns = db.cypher_query(
        dedent(f"""
        MATCH (n:{node_name})
        {where_stmt}
        {exclude_old_stmt}
        RETURN DISTINCT {', '.join([f'n.{field} AS {field}' for field in fields])}
        {order_stmt}
        {limit_stmt}
        """),
        params=params,
    )

    total, _ = db.cypher_query(
        dedent(
            f"MATCH (n:{node_name}) {where_stmt} {exclude_old_stmt} RETURN COUNT(DISTINCT n) as total",
        ),
        params=params,
    )

    return [get_db_result_as_dict(result, columns) for result in results], total[0][0]


def get_odm_aliases(
    page_number: int,
    page_size: int,
    sort_by: str,
    search: str | None,
    op: str,
) -> tuple[list[dict[str, str]], int]:
    """
    Get all ODM Aliases.

    :param page_size: Number of items per page
    :param page_number: Page number
    :param sort_by: Comma separated list of fields to sort by
    :param search: Search term to filter results
    :param op: Operator to use for filtering.
    :return: List of ODM Aliases
    """

    return _query(
        "OdmAlias",
        ["name", "context"],
        page_number,
        page_size,
        sort_by,
        search,
        op,
    )


def get_odm_translated_texts(
    page_number: int,
    page_size: int,
    sort_by: str,
    search: str | None,
    op: str,
) -> tuple[list[dict[str, str]], int]:
    """
    Get all ODM Translated Texts.

    :param page_number: Page number
    :param page_size: Number of items per page
    :param sort_by: Comma separated list of fields to sort by
    :param search: Search term to filter results
    :param op: Operator to use for filtering.
    :return: List of ODM Translated Texts
    """

    return _query(
        "OdmTranslatedText",
        ["text_type", "language", "text"],
        page_number,
        page_size,
        sort_by,
        search,
        op,
    )


def get_odm_formal_expressions(
    page_number: int,
    page_size: int,
    sort_by: str,
    search: str | None,
    op: str,
) -> tuple[list[dict[str, str]], int]:
    """
    Get all ODM Formal Expressions.

    :param page_number: Page number
    :param page_size: Number of items per page
    :param sort_by: Comma separated list of fields to sort by
    :param search: Search term to filter results
    :param op: Operator to use for filtering.
    :return: List of ODM Formal Expressions
    """

    return _query(
        "OdmFormalExpression",
        ["context", "expression"],
        page_number,
        page_size,
        sort_by,
        search,
        op,
    )
