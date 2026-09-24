#!/usr/bin/env python3
"""
Thin CLI for neomodel schema drift JSON (nodes, properties, relationships).

All logic lives in clinical_mdr_api.utils.neomodel_schema.

Default output matches CI baseline: extensions included, all StructuredNode subclasses,
canonical JSON (sorted keys). Override flags only when you know what you are doing.

Usage:
  pipenv run neomodel-schema
  pipenv run neomodel-schema -o neomodel_schema.json
  pipenv run neomodel-schema --compact -o out.json
  pipenv run neomodel-schema --no-extensions --module-prefix clinical_mdr_api
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from clinical_mdr_api.utils.neomodel_schema import (
    build_neomodel_schema_payload,
    dumps_neomodel_schema_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dump minimal neomodel StructuredNode schema as canonical JSON."
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="Write JSON to this file instead of stdout.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Single-line JSON (still sort_keys=True for stable comparison).",
    )
    parser.add_argument(
        "--no-extensions",
        action="store_true",
        help="Skip importing extensions.prodex.db_models.",
    )
    parser.add_argument(
        "--module-prefix",
        action="append",
        default=None,
        metavar="PREFIX",
        help=(
            "If set, only include node classes whose __module__ starts with one "
            "of these prefixes (repeatable)."
        ),
    )
    args = parser.parse_args()

    payload = build_neomodel_schema_payload(
        include_extensions=not args.no_extensions,
        module_prefixes=list(args.module_prefix or []),
    )
    text = dumps_neomodel_schema_json(payload, compact=args.compact)

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
