import json
import os
import re
import subprocess
import time
import traceback
from functools import wraps
from inspect import getfullargspec

from jinja2 import Environment, FileSystemLoader, select_autoescape
from neo4j import GraphDatabase, Neo4jDriver, Record, Result, ResultSummary

from migrations.utils.utils import get_logger, load_env

logger = get_logger(os.path.basename(__file__))

DATABASE_NAME = load_env("DATABASE_NAME")
DATABASE_URL = load_env("DATABASE_URL")
CHANGE_LOG_DIR = load_env("CHANGE_LOG_DIR", default="correction_change_logs")
SWITCH_LOG_ENRICHMENT = (
    load_env("SWITCH_LOG_ENRICHMENT", default="true").strip().lower() == "true"
)

environment = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
    autoescape=select_autoescape(["html", "htm", "xml"]),
)

LOG_ENRICHMENT_OFF = "OFF"
LOG_ENRICHMENT_DIFF = "DIFF"
LOG_ENRICHMENT_FULL = "FULL"

# ---------- Database utils ----------


def parse_db_url(db_url):
    auth_info = re.search(r"//(.+?)@", db_url).group(1)
    username, password = auth_info.split(":")
    url = db_url.replace(auth_info + "@", "")
    return url, username, password


def get_db_driver():
    url, username, password = parse_db_url(DATABASE_URL)
    logger.info("Getting db connection to %s", {url})
    driver = GraphDatabase.driver(url, auth=(username, password))
    return driver


def run_cypher_query(
    driver: Neo4jDriver, query, params=None, quiet=False
) -> tuple[list[Record], ResultSummary]:
    with driver.session(database=DATABASE_NAME) as session:
        result: Result = session.run(query, params)
        records = list(result)
        summary = result.consume()
        if not quiet:
            print_counters_table(summary.counters)
        return records, summary


# ---------- Console logging of counters ----------


def print_counters_table(counters):
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


# ---------- Markdown and log writing ----------


# Get the filename for a markdown file.
# Creates the directory if it doesn't exist.
def get_md_filename(run_label):
    if not os.path.exists(CHANGE_LOG_DIR):
        os.makedirs(CHANGE_LOG_DIR)
    filename = f"summary.{run_label}.md"
    return os.path.join(CHANGE_LOG_DIR, filename)


# Write text to a markdown file.
# Set append=False to overwrite any existing file
def write_to_md_file(run_label, text, append=True):
    filename = get_md_filename(run_label)
    if not append:
        openmode = "w"
    else:
        openmode = "a"
    with open(filename, openmode, encoding="UTF-8") as file:
        file.write(text + "\n")


# Start a new markdown file with a title and description
def save_md_title(run_label, title, desc):
    commit_hash = (
        subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
        .strip()
        .decode("utf-8")
    )
    commit_date = (
        subprocess.check_output(["git", "show", "--format=%aI", "--no-patch"])
        .strip()
        .decode("utf-8")
    )
    template = environment.get_template("correction_summary.md.j2")
    rendered = template.render(
        {
            "title": title,
            "description": desc,
            "commit_hash": commit_hash,
            "commit_date": str(commit_date),
        }
    )
    write_to_md_file(run_label, rendered, append=False)


# Simple helper to print aligned columns to the console
def print_aligned(label, val1, val2, val3):
    print(f"{label:12}{val1:^9}{val2:^9}{val3:^9}")


# ---------- CDC utils ----------


def query_log_enrichment_setting(driver, database_name):
    query = f"SHOW DATABASE  {database_name} YIELD options RETURN options.txLogEnrichment AS txLogEnrichment"
    records, _ = run_cypher_query(driver, query)
    return records[0]["txLogEnrichment"]


def set_log_enrichment(driver, database_name, mode):
    if mode is None:
        mode = LOG_ENRICHMENT_OFF
    query = f'ALTER DATABASE {database_name} SET OPTION txLogEnrichment "{mode}"'
    run_cypher_query(driver, query)


# Enable log enrichment, return the previous setting
def enable_cdc(driver, database_name):
    prev_log_enrichment_setting = query_log_enrichment_setting(driver, database_name)
    if prev_log_enrichment_setting == LOG_ENRICHMENT_DIFF:
        return LOG_ENRICHMENT_DIFF
    set_log_enrichment(driver, database_name, LOG_ENRICHMENT_DIFF)
    current_enrichment_setting = query_log_enrichment_setting(driver, database_name)
    # Wait for the setting to take effect, give up after a few tries
    for _ in range(10):
        if current_enrichment_setting == LOG_ENRICHMENT_DIFF:
            break
        time.sleep(0.1)
        current_enrichment_setting = query_log_enrichment_setting(driver, database_name)
    if current_enrichment_setting != LOG_ENRICHMENT_DIFF:
        raise RuntimeError(
            f"Failed to enable log enrichment, current setting is {current_enrichment_setting}"
        )
    time.sleep(3.0)
    return prev_log_enrichment_setting


def get_current_change_id(driver):
    query = """
        CALL db.cdc.current
    """
    records, _ = run_cypher_query(driver, query)
    return records[0]["id"]


def get_changes_since_id(driver, change_id):
    query = """
        CALL db.cdc.query($change_id)
    """
    records, _ = run_cypher_query(driver, query, params={"change_id": change_id})
    # Convert Neo4j Record objects to lists for JSON serialization
    # Each record from CDC query contains the change data as a list of 5 elements:
    # [id, tx_id, seq, tx_metadata, change_details]
    # The Record object may have the data in different formats, so we handle both cases
    converted_changes = []
    for record in records:
        if hasattr(record, "values"):
            # Record.values() returns a tuple of values
            values = list(record.values())
            # If the record has a single value that is itself a list/array, use it directly
            # Otherwise, use the values as-is
            if len(values) == 1 and isinstance(values[0], (list, tuple)):
                converted_changes.append(list(values[0]))
            else:
                converted_changes.append(values)
        else:
            # If it's already a list/tuple, convert to list
            converted_changes.append(list(record))
    return converted_changes


# ---------- CDC logging wrapper ----------


# Helper to get a unique function name based on the arguments
def _get_func_name(summary_params):
    func_name = summary_params["func_name"]
    if summary_params["func_args"]:
        argstring = ".".join(
            f"{arg[0]}_{arg[1]}" for arg in summary_params["func_args"]
        )
        func_name = f"{func_name}.{argstring}"
    return func_name


# Save change log to json and append a summary to the md file.
def save_change_description(summary_params, label, has_subtasks=False, task_level=0):

    template = environment.get_template("correction_step_desc.md.j2")
    # Append the summary to the markdown file
    if not summary_params["func_doc"]:
        summary_params["func_doc"] = [
            "No description was provided for this correction function."
        ]
    summary_params["has_subtasks"] = has_subtasks
    summary_params["task_level"] = task_level

    rendered = template.render(summary_params)
    write_to_md_file(label, rendered)


# Save change log to json and append a summary to the md file.
def save_change_report(
    changes, summary_params, label, has_subtasks=False, task_level=0
):
    func_name = _get_func_name(summary_params)

    if changes is not None:
        summary = summarize_changes(changes)
        summary_params["filename"] = f"{func_name}.{label}.json"
        # Save the full change log as a separate file
        # Only write if there are actual changes, or if file doesn't exist yet
        json_filepath = os.path.join(CHANGE_LOG_DIR, summary_params["filename"])
        if not os.path.exists(CHANGE_LOG_DIR):
            os.makedirs(CHANGE_LOG_DIR)
        if len(changes) > 0 or not os.path.exists(json_filepath):
            with open(
                json_filepath,
                "w",
                encoding="UTF-8",
            ) as file:
                json.dump(changes, file, indent=4, default=str)
        summary_params["changes_summary"] = format_dict_to_markdown(summary)
    else:
        summary_params["filename"] = None

    summary_params["has_subtasks"] = has_subtasks
    summary_params["task_level"] = task_level

    template = environment.get_template("correction_step_result.md.j2")
    # Append the summary to the markdown file

    if changes is None:
        summary_params["changes_summary"] = None
    elif not summary_params["changes_summary"]:
        summary_params["changes_summary"] = "No changes were required"
    rendered = template.render(summary_params)
    write_to_md_file(label, rendered)


def get_arg_value(arg_values, arg_names, arg_name):
    if arg_name in arg_names:
        arg_idx = arg_names.index(arg_name)
        return arg_values[arg_idx]
    return None


# Decorator to capture any changes made by a correction.
# pylint: disable=broad-exception-caught
def capture_changes(
    verify_func=None, docs_only=False, has_subtasks=False, task_level=0
):
    def capture_changes_decorator(func):
        func_name = func.__name__
        summary_params = {
            "func_name": func_name,
            "func_title": func_name.replace("_", " ").capitalize(),
            "func_file": os.path.os.path.relpath(
                func.__code__.co_filename, os.getcwd()
            ),
            "func_doc": trim_docstring(func.__doc__),
            "func_args": [],
            "verify_error": None,
        }

        @wraps(func)
        def wrapper(*args, **kwargs):
            print(summary_params["func_name"])
            func_arg_names = getfullargspec(func).args
            driver = get_arg_value(args, func_arg_names, "db_driver")
            log = get_arg_value(args, func_arg_names, "log")
            label = get_arg_value(args, func_arg_names, "run_label")
            previous_cdc_setting = None
            summary_params["func_args"] = []
            for arg_name in func_arg_names:
                if arg_name not in ["db_driver", "log", "run_label"]:
                    summary_params["func_args"].append(
                        (arg_name, get_arg_value(args, func_arg_names, arg_name))
                    )
            if not docs_only:
                if SWITCH_LOG_ENRICHMENT:
                    previous_cdc_setting = enable_cdc(driver, DATABASE_NAME)
                    log.info(
                        "Log enrichment enabled, previous setting was '%s'",
                        previous_cdc_setting,
                    )
                else:
                    current_log_enrichment_setting = query_log_enrichment_setting(
                        driver, DATABASE_NAME
                    )
                    if current_log_enrichment_setting != LOG_ENRICHMENT_FULL:
                        raise RuntimeError(
                            "SWITCH_LOG_ENRICHMENT is false, but txLogEnrichment is "
                            f"'{current_log_enrichment_setting}'. Expected '{LOG_ENRICHMENT_FULL}'."
                        )
                    log.info(
                        "SWITCH_LOG_ENRICHMENT is false and txLogEnrichment is '%s'.",
                        current_log_enrichment_setting,
                    )
                id_before = get_current_change_id(driver)
            save_change_description(summary_params, label, has_subtasks, task_level)
            try:
                # === Run the wrapped function ===
                return func(*args, **kwargs)
            except Exception as e:
                log.error(f"Correction failed, error: {e}")
                raise
            finally:
                if verify_func:
                    verify_result = "PASSED"
                    summary_params["verify_error"] = None
                    try:
                        verify_func()
                    except Exception as e:
                        if isinstance(e, AssertionError):
                            verify_result = "FAILED"
                        else:
                            verify_result = "ERROR"
                        exc_info = traceback.format_exc()
                        log.error(f"Verification failed: {exc_info}")
                        summary_params["verify_error"] = exc_info
                    summary_params["verify_func_name"] = verify_func.__name__
                    summary_params["verify_func_file"] = os.path.os.path.relpath(
                        verify_func.__code__.co_filename, os.getcwd()
                    )
                    summary_params["verify_result"] = verify_result

                if not docs_only:
                    # Small delay to ensure CDC has captured all changes
                    # This is especially important for API-based corrections that use separate transactions
                    time.sleep(0.5)
                    changes = get_changes_since_id(driver, id_before)
                    if SWITCH_LOG_ENRICHMENT:
                        if previous_cdc_setting != LOG_ENRICHMENT_DIFF:
                            log.info(
                                "Restoring previous log enrichment setting '%s'",
                                previous_cdc_setting,
                            )
                            set_log_enrichment(
                                driver, DATABASE_NAME, previous_cdc_setting
                            )
                        else:
                            log.info(
                                "Log enrichment was already enabled, no need to restore setting"
                            )
                    else:
                        log.info(
                            "SWITCH_LOG_ENRICHMENT is false, keeping existing txLogEnrichment setting"
                        )
                else:
                    changes = None
                save_change_report(
                    changes, summary_params, label, has_subtasks, task_level
                )

        return wrapper

    return capture_changes_decorator


# ---------- Postprocessing of CDC logs ----------

EVENT_MAP = {
    "c": "created",
    "d": "deleted",
    "u": "updated",
}
TYPE_MAP = {
    "n": "nodes",
    "r": "relationships",
}


# Increment the counter _key_ in the dict _group_, creating as needed
def increment_counter(key, counters, group):
    if group not in counters:
        counters[group] = {}
    if key in counters[group]:
        counters[group][key] += 1
    else:
        counters[group][key] = 1


# Count changes in the _state_ of a change event
def count_changes(state, summary):
    after = state.get("after", {})
    # after is None for deleted nodes
    if after is None:
        after = {}
    before = state.get("before", {})
    # before is None for new nodes
    if before is None:
        before = {}

    # Check property changes, both for nodes and relationships
    props_after = after.get("properties", {})
    props_before = before.get("properties", {})
    for prop in props_after.keys():
        if prop not in props_before:
            increment_counter(prop, summary, "properties_added")
        elif props_after[prop] != props_before[prop]:
            increment_counter(prop, summary, "properties_updated")
    for prop in props_before.keys():
        if prop not in props_after:
            increment_counter(prop, summary, "properties_removed")

    # Check label changes, only for nodes
    labels_after = after.get("labels", [])
    labels_before = before.get("labels", [])
    for label in labels_after:
        if label not in labels_before:
            increment_counter(label, summary, "labels_added")
        elif props_after[prop] != props_before[prop]:
            increment_counter(label, summary, "labels_updated")
    for label in labels_before:
        if label not in labels_after:
            increment_counter(label, summary, "labels_removed")


# Extract summary from CDC log
def summarize_changes(changes):
    summary = {
        "nodes": {
            "created": {},
            "deleted": {},
            "updated": {},
        },
        "relationships": {
            "created": {},
            "deleted": {},
            "updated": {},
        },
    }

    for event in changes:
        details = event[4]
        operation = EVENT_MAP[details["operation"]]
        evtype = TYPE_MAP[details["eventType"]]
        state = details["state"]
        labels_or_type = ""
        if evtype == "nodes":
            # Use all the node labels joined together as the name
            labels_or_type = "+".join(sorted(details["labels"]))
        elif evtype == "relationships":
            # Relationships can only have one type, just use this as name
            labels_or_type = details["type"]
        increment_counter(labels_or_type, summary[evtype][operation], "count")
        count_changes(state, summary[evtype][operation])
    return summary


# Format a dict as a markdown indented list
def format_dict_to_markdown(data_dict, level=0):
    text = ""
    for key, item in data_dict.items():
        if isinstance(item, dict):
            sub_text = format_dict_to_markdown(item, level + 1)
            if sub_text:
                text += f"{'  '*level}- {key}:\n"
                text += sub_text
        else:
            text += f"{'  '*level}- {key}: {item}\n"
    return text


# Trim indentation from docstring.
# Adapted from https://peps.python.org/pep-0257/#handling-docstring-indentation
# Returns a list of lines.
def trim_docstring(docstring):
    if not docstring:
        return ""
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = 1000
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < 1000:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    return trimmed
