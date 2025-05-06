import os

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


def is_desired_header(headers: dict) -> bool:
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


@schemathesis.hooks.register
def before_generate_headers(
    _context: schemathesis.hooks.HookContext,
    strategy: hypothesis.strategies.SearchStrategy,
):
    return strategy.filter(is_desired_header)


@schemathesis.hooks.register
def before_generate_case(
    context: schemathesis.hooks.HookContext,
    strategy: hypothesis.strategies.SearchStrategy,
):
    op = context.operation

    def tune_case(case: schemathesis.models.Case):
        # Replace study_uid/uid path param for all paths starting with "/studies/study_uid}/" or "/studies/{uid}/"
        # with the value supplied as STUDY_UID env variable

        for path_param in ["uid", "study_uid"]:
            if (
                "/studies/{" + path_param + "}" in str(op.path)
                and path_param in case.path_parameters
            ):
                case.path_parameters[path_param] = STUDY_UID

        # Set page_size to 10 if it is 0
        if case.query and "page_size" in case.query and case.query["page_size"] == 0:
            print(f"Setting page_size to 10 for {case.method} {case.full_path}")
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
