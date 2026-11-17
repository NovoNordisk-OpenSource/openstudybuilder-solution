"""
Rewrites downloaded CDISC JSON packages as indented, readable JSON.

The download script writes each package on a single line, which is unreadable
and produces useless diffs. This script re-indents those files in place.

Usage:

> `pipenv run format_jsons [<directory>]`

<directory> is optional and defaults to the environment variable
'CDISC_JSON_DIR'.

Files that are already indented are left untouched. That deliberately includes
the few packages written with ensure_ascii=False - they are readable as they
are, and re-encoding them would only churn the escaping.
"""

import json
import sys
from os import environ, listdir, path

DEFAULT_DIRECTORY = environ.get("CDISC_JSON_DIR", "cdisc_data/packages/cdisc_ct")


def is_minified(raw: str) -> bool:
    """A package written by the downloader is one long line."""
    return "\n" not in raw.strip()


def format_json_files(directory: str):
    """
    Re-indents every minified .json file in <directory>, in place.
    """
    formatted = 0
    skipped = 0

    for filename in sorted(listdir(directory)):
        if not filename.endswith(".json"):
            continue

        filepath = path.join(directory, filename)
        with open(filepath, "r", encoding="utf-8") as file:
            raw = file.read()

        if not is_minified(raw):
            skipped += 1
            continue

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print(f"Error decoding JSON in file: {filepath}")
            continue

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(json.dumps(data, indent=4))
            file.write("\n")

        print(f"Formatted: {filename}")
        formatted += 1

    print(f"Formatted {formatted} file(s), left {skipped} already indented file(s).")


if __name__ == "__main__":
    format_json_files(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DIRECTORY)
