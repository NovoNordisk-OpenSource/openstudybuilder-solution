"""Validate the integration matrix without importing or collecting test modules."""

import re
import shlex
import sys
import tomllib
from fnmatch import fnmatchcase
from pathlib import Path

import yaml


def resolve_selector(value: str, api_root: Path, integration_root: Path) -> Path:
    if (
        not value
        or value.startswith(("-", "~"))
        or "::" in value
        or any(character in value for character in "*?[]${}`;|&<>()\\\n\r")
    ):
        raise ValueError(f"Unsupported selector: {value!r}")
    path = (api_root / value).resolve()
    if not path.is_relative_to(integration_root):
        raise ValueError(f"Selector is outside the integration root: {value}")
    if not path.exists():
        raise ValueError(f"Selector does not exist: {value}")
    if not path.is_file() and not path.is_dir():
        raise ValueError(f"Selector is not a file or directory: {value}")
    return path


def validate_shards(repo_root: Path) -> dict[str, int]:
    api_root = repo_root.resolve() / "api"
    integration_root = api_root / "clinical_mdr_api/tests/integration"
    workflow_path = repo_root / ".github/workflows/api-build.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    try:
        matrix = workflow["jobs"]["test-integration"]["strategy"]["matrix"]
    except (KeyError, TypeError) as error:
        raise ValueError("Missing static test-integration matrix") from error
    if (
        not isinstance(matrix, dict)
        or set(matrix) != {"include"}
        or not isinstance(matrix["include"], list)
        or not matrix["include"]
    ):
        raise ValueError(
            "The integration matrix must contain only a nonempty include list"
        )

    config = tomllib.loads((api_root / "pyproject.toml").read_text(encoding="utf-8"))
    patterns = (
        config.get("tool", {})
        .get("pytest", {})
        .get("ini_options", {})
        .get("python_files", ["test_*.py", "*_test.py"])
    )
    if isinstance(patterns, str):
        patterns = patterns.split()
    if not isinstance(patterns, list) or not all(
        isinstance(pattern, str) and pattern for pattern in patterns
    ):
        raise ValueError("python_files must contain filename patterns")
    files = sorted(
        path
        for path in integration_root.rglob("*.py")
        if path.name != "conftest.py"
        and any(fnmatchcase(path.name, pattern) for pattern in patterns)
    )
    if not files:
        raise ValueError("No integration test files were discovered")

    owners: dict[Path, list[str]] = {path: [] for path in files}
    counts: dict[str, int] = {}
    errors = []
    for entry in matrix["include"]:
        if not isinstance(entry, dict) or set(entry) != {"shard", "paths"}:
            raise ValueError(f"Malformed shard entry: {entry!r}")
        name = entry["shard"]
        if not isinstance(name, str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_-]*", name
        ):
            raise ValueError(f"Invalid shard name: {name!r}")
        if name in counts:
            raise ValueError(f"Duplicate shard name: {name}")
        if not isinstance(entry["paths"], str):
            raise ValueError(f"{name}: paths must be a string")
        includes = []
        excludes = []
        for argument in shlex.split(entry["paths"]):
            if argument.startswith("--ignore="):
                excludes.append(
                    resolve_selector(
                        argument.split("=", 1)[1], api_root, integration_root
                    )
                )
            else:
                includes.append(resolve_selector(argument, api_root, integration_root))
        if not includes:
            raise ValueError(f"{name}: no include paths")
        for index, selection in enumerate(includes):
            for previous in includes[:index]:
                if selection.is_relative_to(previous) or previous.is_relative_to(
                    selection
                ):
                    raise ValueError(
                        f"{name}: overlapping include paths: "
                        f"{previous.relative_to(api_root)}, {selection.relative_to(api_root)}"
                    )
        counts[name] = 0
        for path in files:
            if any(
                path.is_relative_to(selection) for selection in includes
            ) and not any(path.is_relative_to(selection) for selection in excludes):
                owners[path].append(name)
                counts[name] += 1
        if not counts[name]:
            errors.append(f"{name}: selects no test files")

    for path, names in owners.items():
        relative = path.relative_to(api_root).as_posix()
        if not names:
            errors.append(f"Unassigned: {relative}")
        elif len(names) != 1:
            errors.append(f"Multiple owners: {relative}: {', '.join(names)}")
    if errors:
        raise ValueError("\n".join(errors))
    return counts


def main() -> int:
    try:
        counts = validate_shards(Path(__file__).resolve().parents[1])
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"Integration shard validation failed:\n{error}", file=sys.stderr)
        return 1
    for name, count in counts.items():
        print(f"{name}: {count} test files")
    print(
        f"PASS: {sum(counts.values())} test files in {len(counts)} shards, exactly once"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
