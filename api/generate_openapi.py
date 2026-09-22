import argparse
import importlib
import json
import logging
import os
import sys

from clinical_mdr_api.utils.api_version import (
    increment_api_version_if_needed,
    increment_version_number,
)

# from consumer_api.consumer_api import custom_openapi

log = logging.getLogger(__name__)


def generate_openapi(app_import_path, schema_path, version_path, stdout: bool = False):
    # Load FastAPI application
    module_name, app_name = app_import_path.split(":")
    module = importlib.import_module(module_name)
    app = getattr(module, app_name)

    api_spec_new: dict
    api_spec_old: dict
    schema_path = os.path.join("./", schema_path)
    version_path = os.path.join("./", version_path)

    # Generate OpenAPI schema file, increment version number if needed
    custom_openapi_func = getattr(module, "custom_openapi", None)
    if custom_openapi_func:
        api_spec_new = custom_openapi_func()
    else:
        api_spec_new = app.openapi()
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            api_spec_old = json.load(f)
        api_spec_new = increment_api_version_if_needed(api_spec_new, api_spec_old)
    except FileNotFoundError:
        with open(version_path, "r", encoding="utf-8") as f:
            old_version = f.read().strip()
        new_version = increment_version_number(old_version)
        api_spec_new["info"]["version"] = new_version
        log.info(
            "No openapi.json found, read version %s from the apiVersion file",
            old_version,
        )

    if stdout:
        json.dump(
            api_spec_new,
            sys.stdout,
            indent=2,
        )
    else:
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(
                api_spec_new,
                f,
                indent=2,
            )

        with open(version_path, "w", encoding="utf-8") as f:
            f.write(api_spec_new["info"]["version"])

        log.info("Successfully updated %s and %s", schema_path, version_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generates OpenAPI specification for a FastAPI application."
    )
    parser.add_argument(
        "app_import_path",
        metavar="main:app",
        help="The FastAPI application to import (eg: main:app).",
    )

    parser.add_argument(
        "schema_path",
        metavar="openapi.json",
        help="filename of OpenAPI specification",
    )

    parser.add_argument(
        "version_path",
        metavar="apiVersion",
        nargs="?",
        help="filename of api version",
    )

    parser.add_argument(
        "--stdout",
        action="store_true",
        help="dump OpenAPI specification to stdout, skipping update to apiVersion file",
    )

    args = parser.parse_args()

    generate_openapi(
        app_import_path=args.app_import_path,
        schema_path=args.schema_path,
        version_path=args.version_path,
        stdout=args.stdout,
    )
