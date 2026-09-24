import inspect
import json
import logging
import os
import pprint
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import neo4j.exceptions
import requests
from jsonpath_ng import parse
from neomodel import config as neoconfig
from neomodel import db

# pylint: disable=duplicate-code
REGEX_SNAKE_CASE = r"^[a-z]+(_[a-z]+)*$"
REGEX_SNAKE_CASE_WITH_DOT = r"^[a-z.]+(_[a-z.]+)*$"
REPORT_FILE_PATH = "db_checks_result.csv"


class ExpectedFailureException(Exception):
    """
    Raised when every noncompliant row from the query was filtered out by
    configured exclusions (IDs contained in EXCLUDED_NODE_IDS / exclusion list).

    Used to mark tests as BROKEN (not PASSED) in Allure: known issues only,
    not a green pass and not an unhandled error.
    """


REPORT_COLUMNS = [
    "check_id",
    "check_description",
    "noncompliant_entity_cnt",
    "noncompliant_labels",
    "noncompliant_node_ids",
    "impact_tags",
    "requirement_ids",
]


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


def load_env(key: str, default: str = None):
    value = os.environ.get(key)
    logger.info("ENV variable fetched: %s=%s", key, value)
    if value is None and default is None:
        logger.error("%s is not set and no default was provided", key)
        raise EnvironmentError(f"Failed because {key} is not set.")
    if value is not None:
        return value
    logger.warning("%s is not set, using default value: %s", key, default)
    return default


STUDY_UID = load_env("STUDY_UID", "Study_000039")
STUDY_NUMBER = load_env("STUDY_NUMBER", "3003")
LIBRARY_NAME = load_env("LIBRARY_NAME", "SNOMED")
CT_CODELIST_UID = load_env("CT_CODELIST_UID", "CTCodelist_000001")
CT_TERM_UID = load_env("CT_TERM_UID", "CTTerm_000001")
PROJECT_ID = load_env("PROJECT_ID", "999")

API_BASE_URL = load_env("API_BASE_URL", "http://localhost:8000")
CONSUMER_API_BASE_URL = load_env("CONSUMER_API_BASE_URL", "http://localhost:8008")

API_HEADERS = {
    "Authorization": f'Bearer {load_env("API_AUTH_TOKEN")}',
    "User-Agent": "Data-Migrator",
}


def get_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f%z")


def get_db_connection():
    db_url = load_env("DATABASE_URL")
    db_name = load_env("DATABASE_NAME")
    logger.info(
        "Getting db connection from ENV params [url, name]: [%s, %s]",
        db_url,
        db_name,
    )

    neoconfig.DATABASE_URL = db_url
    db.set_connection(neoconfig.DATABASE_URL)

    if db_name:
        neoconfig.DATABASE_URL = f"{db_url}/{db_name}"
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


def get_db_result_as_dict(row: List[any], columns: List[str]) -> dict:
    item = {}
    for key, value in zip(columns, row):
        item[key] = value
    return item


def get_list_element(dict_list: list, attribute: str, value: str):
    """Returns first element from a list of dictionaries by specified attribute value"""
    return [x for x in dict_list if x[attribute] == value][0]


def api_get(
    path: str,
    params: any = None,
    consumer_api: bool = False,
    ignore_response_status: bool = False,
):
    """Issues http GET {path} request,
    asserts that http response status is 200 and returns the response."""
    url = (CONSUMER_API_BASE_URL if consumer_api else API_BASE_URL) + path
    logger.info("GET %s %s", url, params)
    res = requests.get(url, params=params, timeout=30, headers=API_HEADERS)
    if res.status_code != 200:
        logger.error("%s GET %s %s", res.status_code, url, params)

    if not ignore_response_status:
        assert (
            res.status_code == 200
        ), f"Response status {res.status_code} is not 200: url={url}, params={params}"

    return res


def api_get_in_a_loop(
    failed_calls: list, path: str, params: any = None, consumer_api: bool = False
):
    """Issues http GET {path} request with {params} query params and appends failed calls to the {failed_calls} list."""
    res = api_get(
        path=path,
        params=params,
        consumer_api=consumer_api,
        ignore_response_status=True,
    )
    if res.status_code != 200:
        failed_calls.append(
            {
                "path": path,
                "params": params.copy() if params else {},
                "status_code": res.status_code,
            }
        )


def append_to_file(file_path: str, db_results: list):
    """Appends results of db query to specified file"""
    with open(file_path, "a", encoding="UTF-8") as file:
        for row in db_results:
            logger.info("DB check: %s", row)
            # keep only the columns defined in REPORT_COLUMNS
            line = [f'"{str(row.get(col))}"' for col in REPORT_COLUMNS]
            file.write(f"{','.join(line)}\n")
        file.close()


def _labels_match(excluded_labels: List[str], result_labels: List[str]) -> bool:
    """
    Check if excluded labels match result labels.

    Args:
        excluded_labels: List of labels to exclude (e.g., ['StudySelection', 'StudyDesignClass'])
        result_labels: List of labels from result (e.g., ['StudySelection', 'StudyDesignClass'])

    Returns:
        True if labels match (exact match or excluded is subset of result)
    """
    excluded_set = set(excluded_labels)
    result_set = set(result_labels)
    # Exact match or excluded labels are subset of result labels
    return excluded_set == result_set or excluded_set.issubset(result_set)


def _ids_match_exclusion(excluded_id: List, result_id: List) -> bool:
    """
    True if every identifier in the result row is covered by the exclusion id list
    (multiset containment: Counter(result_id) is a sub-multiset of Counter(excluded_id)).

    No exact list-length equality: e.g. result ["Activity_000008"] matches a long
    exclusion list that includes that UID.

    Args:
        excluded_id: Values allowed for this exclusion entry (flat list).
        result_id: Normalized id list for one noncompliant row.

    Returns:
        False if either side is empty; otherwise containment as above.
    """
    if not result_id or not excluded_id:
        return False
    cnt_res = Counter(result_id)
    cnt_ex = Counter(excluded_id)
    for key, need in cnt_res.items():
        if cnt_ex[key] < need:
            return False
    return True


def _is_node_excluded(
    label_list: List[str], id_list: List, excluded_nodes: List[Dict[str, Any]]
) -> bool:
    """
    Check if a node matches any exclusion entry.

    When the result row has IDs (id_list non-empty): match **only** on id
    containment (`_ids_match_exclusion`); exclusion ``label`` is informational
    and not required to match.

    When the result row has no ids (label-only / ``noncompliant_node_ids`` is
    ``N/A``): use label rules as before — if exclusion has no id, label match
    suffices; if exclusion has ids, label must match and ids must satisfy
    containment (typically empty result ids => no match).
    """
    if id_list:
        for excluded in excluded_nodes:
            excluded_id = excluded.get("id", [])
            if not excluded_id:
                continue
            if _ids_match_exclusion(excluded_id, id_list):
                return True
        return False

    for excluded in excluded_nodes:
        excluded_label = excluded.get("label", [])
        excluded_id = excluded.get("id", [])

        if not excluded_label:
            if not excluded_id:
                continue
            if _ids_match_exclusion(excluded_id, id_list):
                return True
        else:
            label_matches = _labels_match(excluded_label, label_list)

            if not excluded_id:
                if label_matches:
                    return True
            else:
                if label_matches and _ids_match_exclusion(excluded_id, id_list):
                    return True
    return False


def _get_matching_exclusion(
    label_list: List[str], id_list: List, excluded_nodes: List[Dict[str, Any]]
) -> Dict[str, Any] | None:
    """
    Return the matching exclusion entry (including optional `motivation`),
    or None if the node does not match any exclusion.

    This mirrors the logic in `_is_node_excluded`, but provides the matched dict
    so we can print its motivation in the ExpectedFailureException output.
    """
    if id_list:
        for excluded in excluded_nodes:
            excluded_id = excluded.get("id", [])
            if not excluded_id:
                continue
            if _ids_match_exclusion(excluded_id, id_list):
                return excluded
        return None

    for excluded in excluded_nodes:
        excluded_label = excluded.get("label", [])
        excluded_id = excluded.get("id", [])

        if not excluded_label:
            if not excluded_id:
                continue
            if _ids_match_exclusion(excluded_id, id_list):
                return excluded
        else:
            label_matches = _labels_match(excluded_label, label_list)

            if not excluded_id:
                if label_matches:
                    return excluded
            else:
                if label_matches and _ids_match_exclusion(excluded_id, id_list):
                    return excluded
    return None


def _format_excluded_failures_lines(
    excluded_failures: List[Dict[str, Any]],
) -> str:
    """Human-readable lines listing each failing row that was removed by exclusions."""
    if not excluded_failures:
        return "  (no per-row detail captured)\n"
    lines = []
    for i, item in enumerate(excluded_failures, 1):
        labels = item.get("noncompliant_labels")
        nids = item.get("noncompliant_node_ids")
        props = item.get("root_properties")
        motivation = item.get("motivation")
        lines.append(f"  {i}. labels={labels!r}, node_ids={nids!r}")
        if motivation:
            lines.append(f"      motivation={motivation!r}")
        if props is not None:
            try:
                props_str = json.dumps(props, indent=2, default=str)
            except (TypeError, ValueError):
                props_str = pprint.pformat(props, width=100)
            lines.append(f"      root_properties=\n{props_str}")
    return "\n".join(lines) + "\n"


def _materialize_noncompliant_columns_from_details(row: Dict[str, Any]) -> None:
    """
    Expand noncompliant_row_details (aligned map from Cypher) into parallel lists.

    Queries using build_root_summary_return_statement return a single COLLECT of
    maps so labels, node_id, and properties(root) stay aligned. Legacy rows that
    already have noncompliant_labels / noncompliant_node_ids only are unchanged.
    """
    details = row.pop("noncompliant_row_details", None)
    if not details:
        return
    labels: List = []
    nids: List = []
    props_list: List = []
    for entry in details:
        if not isinstance(entry, dict):
            continue
        labels.append(entry.get("labels"))
        nids.append(entry.get("node_id"))
        props_list.append(entry.get("root_properties"))
    row["noncompliant_labels"] = labels
    row["noncompliant_node_ids"] = nids
    row["noncompliant_root_properties"] = props_list


# pylint: disable=too-many-locals, too-many-branches
def _filter_excluded_nodes(
    row: Dict, excluded_nodes: List[Dict[str, Any]], original_count: int
) -> None:
    """
    Filter out excluded nodes from a result row (id containment / label-only rules).

    Args:
        row: Result row dictionary to filter (modified in place)
        excluded_nodes: List of excluded node dicts with optional 'label' and 'id' keys
        original_count: Original count before filtering (for logging)
    """
    row["excluded_failures"] = []
    original_node_ids = row.get("noncompliant_node_ids", [])
    original_labels = row.get("noncompliant_labels", [])

    if not original_labels:
        return

    # Handle case where node_ids is 'N/A' (label-only matching)
    if original_node_ids == "N/A":
        # Filter labels only when node_ids is not available
        # original_labels can be a list of strings (single label per item) or list of lists (multiple labels per item)
        filtered_labels = []
        excluded_failures: List[Dict[str, Any]] = []
        for label_item in original_labels:
            # Convert string to list if needed, or use as-is if already a list
            label_list = [label_item] if isinstance(label_item, str) else label_item
            matched_exclusion = _get_matching_exclusion(label_list, [], excluded_nodes)
            if matched_exclusion:
                excluded_failures.append(
                    {
                        "noncompliant_labels": label_item,
                        "noncompliant_node_ids": "N/A",
                        "motivation": matched_exclusion.get("motivation"),
                    }
                )
            else:
                # Keep original format (string or list)
                filtered_labels.append(label_item)
        row["excluded_failures"] = excluded_failures
        filtered_count = len(filtered_labels)
        row["noncompliant_node_ids"] = "N/A"
        row["noncompliant_entity_cnt"] = filtered_count
        row["noncompliant_labels"] = filtered_labels
        excluded_count = len(original_labels) - filtered_count
        if excluded_count > 0:
            logger.info(
                "Filtered out %d excluded labels (original count: %d, filtered count: %d)",
                excluded_count,
                original_count,
                filtered_count,
            )
        return

    if not original_node_ids:
        return

    original_props = row.get("noncompliant_root_properties") or []

    # Build list of (label_list, id_list, root_properties) from results
    result_pairs = []
    for i, label_list in enumerate(original_labels):
        if i >= len(original_node_ids):
            break
        id_list = normalize_id_to_list(original_node_ids[i])
        root_props = original_props[i] if i < len(original_props) else None
        result_pairs.append((label_list, id_list, root_props))

    excluded_pairs = []
    filtered_pairs = []
    for label_list, id_list, root_props in result_pairs:
        matched_exclusion = _get_matching_exclusion(label_list, id_list, excluded_nodes)
        if matched_exclusion:
            excluded_pairs.append(
                (label_list, id_list, root_props, matched_exclusion.get("motivation"))
            )
        else:
            filtered_pairs.append((label_list, id_list, root_props))
    row["excluded_failures"] = [
        {
            "noncompliant_labels": labels,
            "noncompliant_node_ids": ids,
            "root_properties": props,
            "motivation": motivation,
        }
        for labels, ids, props, motivation in excluded_pairs
    ]

    # Rebuild filtered results
    filtered_count = len(filtered_pairs)
    row["noncompliant_node_ids"] = [pair[1] for pair in filtered_pairs]
    row["noncompliant_entity_cnt"] = filtered_count
    row["noncompliant_labels"] = [pair[0] for pair in filtered_pairs]
    row["noncompliant_root_properties"] = [pair[2] for pair in filtered_pairs]

    excluded_count = len(result_pairs) - filtered_count
    if excluded_count > 0:
        logger.info(
            "Filtered out %d excluded nodes (original count: %d, filtered count: %d)",
            excluded_count,
            original_count,
            filtered_count,
        )


# pylint: disable=too-many-arguments, too-many-positional-arguments, too-many-locals
def execute_query_and_append_result_to_file(
    query: str,
    file_path: str,
    check_id: str = "",
    check_description: str = "",
    tags: List[Dict] = None,
    excluded_node_ids: List[Dict[str, Any]] = None,
):
    """
    Executes db query and appends results of db query to specified file.

    Args:
        query: Cypher query to execute
        file_path: Path to the CSV file to append results to
        check_id: Identifier for the check
        check_description: Description of the check
        tags: Dictionary of tags (impact_tags, requirement_ids, etc.)
        excluded_node_ids: List of dicts with optional 'label' and 'id' keys to exclude
            from noncompliant counts (id containment; see EXCLUDED_NODE_IDS).

    Raises:
        ExpectedFailureException: If exclusions are configured, the query reported
            at least one failure before filtering, and every failure was removed by
            exclusions (all raised matches fully contained in exclusion ids). Marks
            the test as BROKEN / known issue, not PASSED.
    """
    logger.info("%s: %s", check_id, check_description)
    rows, columns = db.cypher_query(query)

    db_results = [get_db_result_as_dict(row, columns) for row in rows]

    tags = tags or {}
    impact_tags = tags.get("impact_tags:", [])
    req_tags = tags.get("requirement_ids", [])

    if len(db_results) == 0:
        db_results.append(
            {
                "check_id": check_id,
                "check_description": check_description,
                "noncompliant_entity_cnt": 0,
                "noncompliant_labels": [],
                "noncompliant_node_ids": [],
            }
        )

    # Get excluded nodes (already normalized)
    excluded_nodes = excluded_node_ids if excluded_node_ids else []
    if excluded_nodes:
        logger.info(
            "Excluding %d known issue nodes for check_id: %s",
            len(excluded_nodes),
            check_id,
        )

    # Track original counts before filtering
    original_counts = []
    for row in db_results:
        _materialize_noncompliant_columns_from_details(row)
        # Get original count before filtering
        original_count = row.get("noncompliant_entity_cnt", 0)
        original_counts.append(original_count)

        # Filter out excluded nodes (label+ID pairs)
        if excluded_nodes:
            _filter_excluded_nodes(row, excluded_nodes, original_count)

        row["impact_tags"] = impact_tags
        row["requirement_ids"] = req_tags
        row["check_id"] = check_id
        row["check_description"] = check_description

    append_to_file(file_path, db_results)

    # Check if test should be marked as BROKEN due to exclusions
    result = db_results[0]
    final_count = result.get("noncompliant_entity_cnt", 0)
    original_count = original_counts[0] if original_counts else 0

    excluded_failures_agg: List[Dict[str, Any]] = []
    for r in db_results:
        excluded_failures_agg.extend(r.get("excluded_failures", []))
    result["excluded_failures"] = excluded_failures_agg

    # Get exclusion details if there are exclusions
    exclusion_details = ""
    if excluded_nodes:
        exclusion_details = get_exclusion_details(check_id)
        # Add exclusion details to result for logging/reporting
        result["exclusion_details"] = exclusion_details
        result["excluded_count"] = (
            original_count - final_count
            if original_count > final_count
            else original_count
        )

    # All query failures were filtered by exclusions only -> BROKEN (known issues), not PASSED
    if excluded_nodes and original_count > 0 and final_count == 0:
        failures_txt = _format_excluded_failures_lines(excluded_failures_agg)
        raise ExpectedFailureException(
            f"Test passed but has known exclusions (all {original_count} failure(s) are excluded).\n"
            f"Failing row(s) removed by exclusions (this run):\n{failures_txt}"
            f"Configured exclusion entries for check_id={check_id!r}:\n{exclusion_details}"
        )

    # If final_count > 0, there are more failures than exclusions - log exclusion details
    if excluded_nodes and final_count > 0:
        logger.info(
            "Test has %d failure(s) after excluding %d known issue(s) for check_id: %s",
            final_count,
            (
                original_count - final_count
                if original_count > final_count
                else original_count
            ),
            check_id,
        )
        if exclusion_details:
            logger.info("Exclusion details:\n%s", exclusion_details)

    return result


def execute_query_with_params_and_append_result_to_file(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    query: str,
    file_path: str,
    params: dict,
    check_id: str = "",
    check_description: str = "",
    tags: List[Dict] = None,
):
    """Like ``execute_query_and_append_result_to_file`` but passes Cypher parameters (e.g. ``study_uid``)."""
    logger.info("%s: %s", check_id, check_description)
    rows, columns = db.cypher_query(query, params=params)

    db_results = [get_db_result_as_dict(row, columns) for row in rows]

    tags = tags or {}
    impact_tags = tags.get("impact_tags:", [])
    req_tags = tags.get("requirement_ids", [])

    if len(db_results) == 0:
        db_results.append(
            {
                "check_id": check_id,
                "check_description": check_description,
                "noncompliant_entity_cnt": 0,
                "noncompliant_labels": [],
                "noncompliant_node_ids": [],
            }
        )

    for row in db_results:
        row["impact_tags"] = impact_tags
        row["requirement_ids"] = req_tags
        row["check_id"] = check_id
        row["check_description"] = check_description
    append_to_file(file_path, db_results)
    return db_results[0]


def build_root_summary_return_statement(root_alias, extra_return=None):
    """
    Build the shared OPTIONAL MATCH / CASE / RETURN used by many DB checks.

    ``noncompliant_entity_cnt`` uses ``COUNT(DISTINCT root)`` so it matches the
    number of entries in ``noncompliant_row_details``. A plain ``COUNT(root)``
    would over-count when the same root appears in several duplicate-pair rows.

    Returns ``noncompliant_row_details``: a ``COLLECT(DISTINCT { ... })`` of maps
    with ``labels``, ``node_id`` (same logic as before), and ``root_properties``
    (``properties(root)``) so each failing root is fully described. Python expands
    this into ``noncompliant_labels``, ``noncompliant_node_ids``, and
    ``noncompliant_root_properties`` before filtering and CSV output.
    """
    if extra_return is None:
        extra_return_stmts = ""
        with_vars = root_alias
    else:
        # Parse extra_return items: if tuple (expression, alias), use expression in WITH and alias in RETURN
        # If not tuple, use directly in both
        parsed_return_items = []
        with_expressions = []

        for item in extra_return:
            if isinstance(item, tuple) and len(item) == 2:
                # Tuple: (expression, alias)
                expression, alias = item
                # Add to WITH clause: expression AS alias
                with_expressions.append(f"{expression} AS {alias}")
                # Add alias to RETURN clause
                parsed_return_items.append(alias)
            else:
                with_expressions.append(item)
                # Not a tuple, use directly in both WITH and RETURN
                parsed_return_items.append(item)

        # Build extra_return_stmts for RETURN clause
        extra_return_stmts = f"{', '.join(parsed_return_items)},"

        # Build WITH clause variables
        if with_expressions:
            with_vars = f"{root_alias}, {', '.join(with_expressions)}"
        else:
            with_vars = root_alias

    return f"""
        OPTIONAL MATCH ({root_alias})<-[:AFTER]-(saction:StudyAction)
        WITH {with_vars}, CASE
                WHEN
                    {root_alias} IS NOT NULL
                    AND "StudyRoot" in labels({root_alias})
                THEN {root_alias}.uid
                WHEN
                    saction is not null
                    and {root_alias} IS NOT NULL
                    AND "StudySelection" in labels({root_alias})
                THEN [{root_alias}.uid,saction.date]
                WHEN
                    saction is null
                    and {root_alias} IS NOT NULL
                    AND "StudySelection" in labels({root_alias})
                THEN {root_alias}.uid
                WHEN
                    "StudyAction" in labels({root_alias})
                THEN [{root_alias}.date,{root_alias}.author_id]
                WHEN
                    {root_alias}.uid IS NOT NULL
                THEN {root_alias}.uid
                WHEN
                    {root_alias}.name IS NOT NULL
                THEN {root_alias}.name
                WHEN
                    {root_alias}.submission_value IS NOT NULL
                THEN {root_alias}.submission_value
                WHEN
                    {root_alias}.user_id IS NOT NULL
                THEN {root_alias}.user_id
                WHEN
                    {root_alias}.concept_id IS NOT NULL
                THEN {root_alias}.concept_id
                WHEN
                    {root_alias}.external_id IS NOT NULL
                THEN {root_alias}.external_id
            ELSE elementId({root_alias})
            end as noncompliant_node_id
        RETURN
            COUNT(DISTINCT {root_alias}) as noncompliant_entity_cnt,
            {extra_return_stmts}
            COLLECT(DISTINCT {{
                labels: labels({root_alias}),
                node_id: noncompliant_node_id,
                root_properties: properties({root_alias})
            }}) AS noncompliant_row_details
        """


def extract_values_by_path(data, json_path: str) -> set:
    """Extracts all values from JSON data using JSON path"""
    jsonpath_expr = parse(json_path)
    return {match.value for match in jsonpath_expr.find(data)}


def parse_query_params(query_params: str) -> dict:
    """Parses query params from string to dictionary"""
    params = {}
    if query_params.strip() != "<none>":
        for param in query_params.split(","):
            key, val = param.split("=")
            key = key.strip()
            val = val.strip()
            params[key] = val
    return params


def replace_url_and_query_params(url: str, query_params: dict) -> Tuple[str, dict]:
    """Returns tuple of endpoint url and query params.

    Replaces the following placeholder values in url/params with appropriate values:
     - <now> => current UTC timestamp
     - /{study_uid} => `/STUDY_UID` (using `STUDY_UID` ENV variable)
     - /{study_number} => `/STUDY_NUMBER` (using `STUDY_NUMBER` ENV variable)
     - /studies/{uid} => `/studies/STUDY_UID` (using `STUDY_UID` ENV variable)
     - /{library} => `/LIBRARY_NAME` (using `LIBRARY_NAME` ENV variable)
     - /{codelist_uid} => `/CT_CODELIST_UID` (using `CT_CODELIST_UID` ENV variable)
     - /ct/terms/{term_uid} => `/ct/terms/CT_TERM_UID` (using `CT_TERM_UID` ENV variable)
    """

    url = (
        url.replace("/studies/{uid}", f"/studies/{STUDY_UID}")
        .replace("/{study_uid}", f"/{STUDY_UID}")
        .replace("/{study_number}", f"/{STUDY_NUMBER}")
        .replace("/{library}", f"/{LIBRARY_NAME}")
        .replace("/{codelist_uid}", f"/{CT_CODELIST_UID}")
        .replace("/ct/terms/{term_uid}", f"/ct/terms/{CT_TERM_UID}")
    )

    if query_params:
        for key, val in query_params.items():
            if val == "<now>":
                query_params[key] = get_now()
            if val == "{study_number}":
                query_params[key] = STUDY_NUMBER
            if val == "{project_id}":
                query_params[key] = PROJECT_ID
            if val == "{library}":
                query_params[key] = LIBRARY_NAME
            if val == "{codelist_uid}":
                query_params[key] = CT_CODELIST_UID
            if val == "{term_uid}":
                query_params[key] = CT_TERM_UID

    return url, query_params


def assert_items_sorted_alphabetically(
    items: list,
    query_params: dict,
) -> bool:
    """Asserts that items are sorted alphabetically by specified key and order"""
    if "sort_by" in query_params:
        sort_by = query_params["sort_by"]
        sort_order = query_params.get("sort_order", "asc")

        if "." in sort_by:
            # Handle nested attributes
            key1, key2 = sort_by.split(".")
            sorted_items = sorted(
                items,
                key=lambda x: (
                    x[key1] is None or x[key1][key2] is None,
                    x[key1][key2].lower() if x[key1] and x[key1][key2] else "",
                ),
                reverse=sort_order == "desc",
            )
        else:
            # Handle flat attributes
            sorted_items = sorted(
                items,
                key=lambda x, sort_key=sort_by: (
                    x[sort_key] is None,
                    x[sort_key].lower() if x[sort_key] else "",
                ),
                reverse=sort_order == "desc",
            )

        assert items == sorted_items, (
            f"Items are not sorted correctly by '{sort_by}' in '{sort_order}' order. "
            f"Expected: {sorted_items}, Actual: {items}"
        )


def assert_items_sorted_numerically(
    items: list,
    query_params: dict,
) -> bool:
    """Asserts that items are sorted numerically by specified key and order"""
    if "sort_by" in query_params:
        sort_by = query_params["sort_by"]
        sort_order = query_params.get("sort_order", "asc")

        assert items == sorted(
            items,
            key=lambda x, sort_key=sort_by: (
                x[sort_key] is None,
                int(x[sort_key]) if x[sort_key] else 0,
            ),
            reverse=sort_order == "desc",
        )


def get_name_and_doc():
    """Helper to get the name and docstring of the calling function"""
    check_id = inspect.currentframe().f_back.f_code.co_name
    module_name = inspect.getmodule(inspect.currentframe().f_back).__name__
    check_description = inspect.getdoc(getattr(sys.modules[module_name], check_id))
    # if there are multiple lines in docstring, return only the first line
    if check_description and "\n" in check_description:
        check_description = check_description.split("\n", 1)[0]
    return check_id, check_description


def get_gherkin_tags(request) -> dict:
    """Helper to get the impact tags from the scenario markers"""
    impact_tags = []
    req_tags = []
    others = []
    for marker in request.node.own_markers:
        if ":" in marker.name:
            key, value = marker.name.split(":", 1)
            if key == "impact":
                impact_tags.append(value.strip())
            elif key == "REQ_ID":
                req_tags.append(value.strip())
            else:
                others.append(marker.name)
        else:
            others.append(marker.name)
    return {
        "impact_tags:": impact_tags,
        "requirement_ids": req_tags,
        "other_tags": others,
    }


def normalize_id_to_list(id_value):
    """
    Normalizes an ID value to always be a list.

    Args:
        id_value: Single value (string/number) or list

    Returns:
        List: If input is already a list, returns as-is. If single value, returns [value].
    """
    if isinstance(id_value, list):
        return id_value
    return [id_value]


# Known issues: excluded nodes per check_id, stored in JSON.
#
# Format: {check_id: [{"label": [...], "id": [...]}, ...]}
#
# - id: Flat list of allowed identifiers for that entry. Matching is **containment**
#   (multiset): each id value reported for a failing row must appear at least as
#   often in the exclusion entry's list. One entry may list many UIDs (OR-style).
# - label: Optional documentation. When results include node ids for a row,
#   matching uses **only** id containment; labels on the exclusion are not compared.
#   When results are label-only (noncompliant_node_ids == "N/A"), labels are used
#   as before.
#
# To add exclusions: run the test, copy ids from results, add {"label": [...], "id": [...]}.
# Single values still use a one-element list, e.g. ["elementId123"].

_EXCLUDED_NODE_IDS_JSON_PATH = os.path.join(
    os.path.dirname(__file__), "excluded_node_ids.json"
)


def _load_excluded_node_ids() -> Dict[str, Any]:
    try:
        with open(_EXCLUDED_NODE_IDS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.warning(
            "Exclusion JSON not found (%s). No exclusions will be applied.",
            _EXCLUDED_NODE_IDS_JSON_PATH,
        )
        return {}
    return data if isinstance(data, dict) else {}


EXCLUDED_NODE_IDS = _load_excluded_node_ids()


def get_excluded_node_ids(check_id: str) -> List[Dict[str, Any]]:
    """
    Returns exclusion entries for a check_id (known issues).

    Matching uses id **containment** (see `_ids_match_exclusion`). When results
    include node ids, exclusion labels are not used for matching.

    Args:
        check_id: The check identifier (usually the test function name)

    Returns:
        List of dicts with optional ``label`` and ``id`` (``id`` always normalized to a list).
    """
    excluded = EXCLUDED_NODE_IDS.get(check_id, [])
    # Ensure all IDs are normalized to lists
    normalized = []
    for item in excluded:
        normalized_item = item.copy()
        normalized_item["id"] = normalize_id_to_list(item["id"])
        # Label is optional - if not provided, set to empty list (matches on ID only)
        if "label" not in normalized_item:
            normalized_item["label"] = []
        normalized.append(normalized_item)
    return normalized


def check_exclusions_exist(check_id: str) -> bool:
    """
    Check if a test has exclusions defined in EXCLUDED_NODE_IDS.

    Args:
        check_id: The check identifier (usually the test function name)

    Returns:
        True if check_id has entries in EXCLUDED_NODE_IDS, False otherwise
    """
    return (
        check_id in EXCLUDED_NODE_IDS and len(EXCLUDED_NODE_IDS.get(check_id, [])) > 0
    )


def get_exclusion_details(check_id: str) -> str:
    """
    Get human-readable exclusion details from EXCLUDED_NODE_IDS for reporting.

    Args:
        check_id: The check identifier (usually the test function name)

    Returns:
        Human-readable string describing the exclusions, or empty string if no exclusions
    """
    if not check_exclusions_exist(check_id):
        return ""

    excluded = EXCLUDED_NODE_IDS.get(check_id, [])
    exclusion_count = len(excluded)

    # Format exclusion details for display
    details_parts = []
    for idx, exclusion in enumerate(excluded, 1):
        label = exclusion.get("label", [])
        exclusion_id = exclusion.get("id", [])

        detail_parts = []
        if label:
            detail_parts.append(f"label={label}")
        if exclusion_id:
            detail_parts.append(f"id={exclusion_id}")
        if not detail_parts:
            detail_parts.append("(empty exclusion)")

        details_parts.append(f"  {idx}. {', '.join(detail_parts)}")

    details_str = "\n".join(details_parts)
    return f"{exclusion_count} excluded node(s):\n{details_str}"
