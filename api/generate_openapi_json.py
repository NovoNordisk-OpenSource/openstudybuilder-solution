import json
import logging
import os
import sys

log = logging.getLogger(__name__)


def main(filename: str = "openapi.json", stdout: bool = True, basepath: str = "./"):
    from clinical_mdr_api.main import custom_openapi
    from clinical_mdr_api.utils.api_version import (
        increment_api_version_if_needed,
        increment_version_number,
    )

    api_spec_new: dict
    api_spec_old: dict
    schema_path = os.path.join(basepath, filename)
    version_path = os.path.join(basepath, "apiVersion")

    api_spec_new = custom_openapi()
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

        log.info("Successfully updated %s and apiVersion", filename)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Updates OpenAPI JSON specification, "
        "incrementing version number when needed, updates apiVersion file too"
    )
    parser.add_argument(
        "filename",
        metavar="openapi.json",
        type=str,
        nargs="?",
        help="filename of OpenAPI specification (JSON)",
        default="openapi.json",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="dump OpenAPI specification to stdout, skipping update to apiVersion file",
    )

    args = parser.parse_args()
    basepath = os.path.normpath(os.path.dirname(sys.argv[0]))

    main(basepath=basepath, **vars(args))
    sys.exit(0)
