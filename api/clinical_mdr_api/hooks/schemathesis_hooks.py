import os
from typing import Any

import hypothesis
import hypothesis.strategies
import schemathesis
import schemathesis.schemas

STUDY_UID = os.getenv("SCHEMATHESIS_STUDY_UID", "Study_000001")


EXCLUDED_PATHS = [
    "/ct/catalogues/changes",
    "/listings/libraries/all/gcmd/cdisc-ct-val/headers",
    "/listings/libraries/all/gcmd/topic-cd-def",
    "/epochs/allowed-configs",
    "/standards/sponsor-models/datasets",
    "/standards/sponsor-models/datasets/headers",
    "/standards/sponsor-models/dataset-variables",
    "/standards/sponsor-models/dataset-variables/headers",
]


def is_in_range(val):
    """Temporarily filter out all characters outside of 0x20...0xFFFF range"""
    val = str(val)
    return all(0x20 <= ord(char) <= 0xFFFF for char in val)


def is_desired_header(headers: dict[Any, Any]) -> bool:
    """
    Returns True if all headers are within range.

    Args:
        headers (dict): The headers to check.

    Returns:
        bool: True if all headers are within range, False otherwise.
    """
    if headers:
        for name, value in headers.items():
            if not is_in_range(name) or not is_in_range(value):
                return False
    return True


@schemathesis.hook
def before_generate_headers(
    _context: schemathesis.hooks.HookContext,
    strategy: hypothesis.strategies.SearchStrategy,
):
    return strategy.filter(is_desired_header)


@schemathesis.hook
def before_generate_case(
    context: schemathesis.hooks.HookContext,
    strategy: hypothesis.strategies.SearchStrategy,
):
    op = context.operation

    # Pre-compute the set of query parameters that are declared as scalar
    # (non-array) in the OpenAPI schema for this operation. When schemathesis
    # generates a list for such a parameter, it serialises it as repeated
    # ``?name=v1&name=v2`` which Starlette collapses by keeping the last value.
    # That silently masks type violations, so we mirror the runtime behaviour
    # before the request leaves the generator: keep the last element and let
    # the API validators see the real value.
    scalar_query_params = {
        param.name
        for param in op.query
        if param.definition.get("schema", {}).get("type") != "array"
    }

    def tune_case(case: schemathesis.Case):
        # Replace study_uid/uid path param for all paths starting with "/studies/study_uid}/" or "/studies/{uid}/"
        # with the value supplied as STUDY_UID env variable
        if case.path_parameters is None:
            case.path_parameters = {}

        for path_param in ["uid", "study_uid"]:
            if (
                "/studies/{" + path_param + "}" in str(op.path)
                and path_param in case.path_parameters
            ):
                case.path_parameters[path_param] = STUDY_UID

        if case.query:
            # Collapse repeated scalar query params to the last value (see above).
            for name in scalar_query_params:
                value = case.query.get(name)
                if isinstance(value, list):
                    case.query[name] = value[-1] if value else None

            # Set page_size to 10 if it is 0
            if case.query.get("page_size") == 0:
                print(
                    f"Setting page_size to 10 for {case.method} {case.formatted_path}"
                )
                case.query["page_size"] = 10

        return case

    return strategy.map(tune_case)


@schemathesis.hook
def after_load_schema(
    _context: schemathesis.hooks.HookContext, schema: schemathesis.schemas.BaseSchema
) -> None:
    # Remove excluded paths from the schema
    print("Excluding paths from tests:")
    for path in EXCLUDED_PATHS:
        if path in schema.raw_schema["paths"]:
            del schema.raw_schema["paths"][path]
            print(f" - {path}")

    # Remove 'security' field from each operation, as we run tests without authentication
    for _path, path_def in schema.raw_schema["paths"].items():
        for _method, method_def in path_def.items():
            if "security" in method_def:
                del method_def["security"]
