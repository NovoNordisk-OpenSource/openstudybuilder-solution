#!/usr/bin/env python3

"""Builds a Software Bill of Materials (SBOM) in Markdown format for Node or Python packages."""

# Features:
# - Uses only standard Python modules.
# - Works with Python and Node projects by discovering installed packages from yarn.lock, package-lock.json, or Pipfile.lock.
# - Discovers license files from packages directories or from an optional fallback directory if package does not include a license file.
# - Raises warnings/errors for missing licenses or when the fallback license filename does not include the current version number of the package.
# - Log messages can be formatted for Azure DevOps pipelines.
# - Outputs SBOM in Markdown format to standard output or a file.
# - The built SBOM includes a summary table which list installed packages with name, version, license type, and (optional) author columns.
# - Includes license files (one or may) in distinct sections for each package.
# - License text get inserted as re-flowable blockquotes or pre-formatted code blocks.
# - Sections get linked from the summary table.
# - The level of markdown headers can be set.
# - Text files can be prepended/appended to beginning/end of the built SBOM.
#
# 1. Discovers installed packages from yarn.lock or Pipfile.lock.
# 2. Finds the package directory in node_modules folder or with importlib.metadata.
# 3. Reads package metadata (METADATA or package.json), updates package name or version based on metadata.
# 3. Looks for license files:
#     1. Prefers license files listed in package metadata
#     2. Otherwise, looks for common license file names in package directory
#     3. Otherwise, looks in the fallback directory for "{name}-{version}*",
#        can match a file or a directory with one or more common files names.
#     4. Otherwise, looks in fallback directory for "{name}*",
#        and warns that the fallback with the specific version is missing.
# 4. Build SBOM in Markdown format with package table and license texts.
#     1. Adds UTF-8 BOM to the beginning of the file.
#     2. Can prepend a text file if specified.
#     3. Adds a header and a summary table of installed packages with links to license sections.
#     4. Includes licence files with section headers for each package.
#     5. Can append a text file to the end.
#
# Exit code is a bitmask with the following bits:
# - 0: No issues.
# - 1: Warning for missing versioned fallback license file.
# - 2: Error for missing fallback license files.
# - 4: Error for missing packages.
# - anything non-0 for an unhandled error.

import argparse
import importlib.metadata
import json
import logging
import mimetypes
import os
import re
import sys
import textwrap
from glob import glob
from typing import Callable

log = logging.getLogger(__name__)


_EXIT_CODE: int = 0


def build_sbom(
    packages: list[tuple[str, str, str, list[str], dict]],
    quote_text: bool = True,
    prefix_headers: str = "#",
    num_licenses: int | None = None,
    show_author: int = 0,
    prepend: str | None = None,
    append: str | None = None,
) -> str:
    """Builds SBOM in Markdown format from the discovered packages."""

    sbom: list[str] = ["\ufeff"]

    if prepend:
        log.info("Prepending file to SBOM: %s", prepend)
        with open(prepend, mode="rt", encoding="utf8", errors="replace") as f:
            sbom.append(f.read())

    if packages:
        sbom.append(f"{prefix_headers}# Installed packages\n")
        sbom.extend(build_packages_table(packages, show_author))

        sbom.append(f"\n\n{prefix_headers}# Third-party package licenses\n")
        sbom.extend(
            include_licence_files(packages, quote_text, prefix_headers, num_licenses)
        )

    else:
        sbom.append(f"{prefix_headers}# Installed packages\n")
        sbom.append(
            "No third-party packages were installed in the runtime environment.\n"
        )

    if append:
        log.info("Appending file to SBOM: %s", append)
        with open(append, mode="rt", encoding="utf8", errors="replace") as f:
            sbom.append(f.read())

    return "\n".join(sbom)


def build_packages_table(
    packages: list[tuple[str, str, str | None, str, list[str]]], show_author: int
) -> list[str]:
    """Builds packages table in Markdown format."""

    headers = ["Package", "Version", "License"]
    if show_author:
        headers.append("Author")

    rows: list[list[str]] = [headers]
    for name, version, _, license_paths, metadata in packages:
        # extract license type from metadata
        licence = metadata.get("license_expression")
        if not licence or len(licence) > 50:
            licence = metadata.get("license")
        if not licence or len(licence) > 50:
            licence = None

        if not licence and license_paths:
            licence = "see below"
        if licence and license_paths:
            # link to section headers
            licence = f"[{licence}](#{to_target(name)})"
        elif licence:
            licence = f"{licence} (missing)"
        else:
            licence = "missing"

        row: list[str] = [name, version, licence]

        if show_author:
            metadata.get("author")
            if show_author > 1:
                author = author_full(metadata)
            else:
                author = author_name(metadata)
            row.append(author)

        rows.append(row)

    # calculate maximum length of column for fixed-width formatting
    max_col_len = [max(len(row[i]) for row in rows) for i in range(len(headers))]

    lines = []
    for j, row in enumerate(rows):
        # convert row to fixed-width cells
        lines.append(
            f"|{'|'.join(f' {c:<{max_col_len[i]}} ' for i, c in enumerate(row))}|"
        )
        if j == 0:
            # header separators |---|---| to fixed column widths
            lines.append(
                f"|{ '|'.join('-' * (max_col_len[i] + 2) for i in range(len(headers))) }|"
            )

    return lines


def include_licence_files(
    packages: list[tuple[str, str, str | None, str, list[str]]],
    quote_text: bool,
    prefix_headers: str,
    num_licenses: int | None,
) -> list[str]:
    """Includes license files into Markdown text."""

    lines = []
    for name, _, module_path, license_paths, _ in packages:
        if not license_paths:
            continue

        lines.append("---")
        lines.append(
            f"{prefix_headers}## {name}\n"
        )  # mind these headers are also link targets

        for license_filename in license_paths[:num_licenses]:
            license_filepath = os.path.join(module_path, license_filename)
            lines.append(
                read_license_file(
                    license_filepath,
                    quote_text=quote_text,
                    prefix_headers=f"{prefix_headers}##",
                )
            )
            lines.append(
                ""
            )  # also separates multiple licenses with blank line (each rendered as distinct block in quote mode)

    return lines


def read_license_file(
    filepath: str, quote_text=True, prefix_headers: str = "###"
) -> str:
    """Reads text file and returns its content quoted for insertion into Markdown."""

    with open(filepath, mode="rt", encoding="utf8", errors="replace") as f:
        text = textwrap.dedent(f.read()).strip("\r\n").rstrip()

    if quote_text and mimetypes.guess_file_type(filepath)[0] in (
        "text/markdown",
        "text/plain",
        None,
    ):
        text = re.sub("^#", f"{prefix_headers}#", text, flags=re.MULTILINE)
        text = textwrap.indent(text, "> ", lambda line: True)
    else:
        text = textwrap.indent(text, " " * 4)

    return text


_non_target_safe_re = re.compile(r"[^\w\s@/-]")
_hyphen_space_re = re.compile(r"[-\s]+")


def to_target(text: str) -> str:
    """Converts Markdown section header text to link target"""

    text = text.strip().lower()
    text = _non_target_safe_re.sub(
        "", text
    )  # remove characters not safe for anchor targets
    text = _hyphen_space_re.sub(
        "-", text
    )  # replace spaces and hyphens with single hyphen
    return text


def author_full(metadata: dict) -> str:
    """Formats author field from package metadata into a string."""
    name, email, url = None, None, None

    if author := metadata.get("author"):
        if isinstance(author, dict):
            name = author.get("name", "").strip()
            email = author.get("email", "").strip()
            url = author.get("url", "").strip()

        elif isinstance(author, str):
            name = author.strip()
            if email := metadata.get("author_email"):
                email = email.strip()
            if url := metadata.get("home_page"):
                url = url.strip()

    parts = []
    if name:
        parts.append(name)
    if email:
        parts.append(f"<{email}>")
    if url:
        parts.append(f"({url})")

    return " ".join(parts) if parts else ""


_parentheses_re = re.compile(r"\s*\(.*\)\s*")
_chevrons_re = re.compile(r"\s*<.*>\s*")


def author_name(metadata: dict) -> str:
    """Extracts author name from package metadata."""

    if author := metadata.get("author"):
        if isinstance(author, str):
            # remove email and url if present
            author = _parentheses_re.sub("", author)
            author = _chevrons_re.sub("", author)
            return author.strip()

        if isinstance(author, dict):
            # return author's name
            return author.get("name", "").strip()

    return ""


_yl_indent_re = re.compile(r"^\s+")
_yl_name_re = re.compile(r'(?:^|,\s*)("?)([^",\s][^"@]*)[^"]*\1(?=:$|,\s*)')
_yl_property_re = re.compile(r"^(\s+)([a-z0-9_.-]+)\s(.*)$")


def read_yarn_lock(filepath="yarn.lock") -> list[tuple[str, str]]:
    """Reads yarn.lock file and returns a list of (package name, version) tuples distinct on package name."""

    package_version_map = {}

    with open(filepath, mode="rt", encoding="utf8") as f:
        indent = None
        name = None

        for line in f:
            line = line.rstrip()  # to remove tailing \n

            # skip comments and empty lines
            if not (stripped := line.strip()) or stripped.startswith("#"):
                continue

            # indented lines
            if m := _yl_indent_re.match(line):
                if not name:  # does not belong to any block
                    continue

                i = m.group(0)
                if not indent:  # first indented line of a block
                    indent = i

                elif i != indent:  # ignore deeper levels
                    continue

                # parse properties
                if not (m := _yl_property_re.match(line)):
                    continue
                key, value = m.group(2, 3)

                if key == "version":
                    # sometimes a package is listed multiple times with different versions,
                    # will try to read current version number from package.json later
                    package_version_map[name] = value.strip('"')

            # non-indented lines signal a new block
            elif m := _yl_name_re.match(line):
                name = m.group(2)
                indent = None

    return list(package_version_map.items())


def read_package_lock_json(filepath="package-lock.json") -> list[tuple[str, str]]:
    """Reads package-lock.json file and returns a list of (package name, version) tuples distinct on package name."""

    with open(filepath, mode="rt", encoding="utf8") as f:
        lock = json.load(f)

    package_version_map = {}

    # lockfileVersion 2 and 3 use "packages" with node_modules/ prefixed keys
    if "packages" in lock:
        for key, meta in lock["packages"].items():
            if not key:  # skip root project entry (empty string key)
                continue
            # key is like "node_modules/package-name" or "node_modules/@scope/package-name"
            name = key.rsplit("node_modules/", 1)[-1]
            if version := meta.get("version"):
                package_version_map.setdefault(name, version)

    # lockfileVersion 1 uses "dependencies"
    elif "dependencies" in lock:
        for name, meta in lock["dependencies"].items():
            if version := meta.get("version"):
                package_version_map[name] = version

    return list(package_version_map.items())


def node_module_dir(
    name: str, modules_path: str = "node_modules", realpath=False
) -> str:
    """Returns the path to the directory of a Node module given its name and the path to node_modules dir."""

    path = os.path.join(modules_path, name)
    if realpath:
        path = os.path.realpath(path)
    return path


def fallback_license_paths(
    name: str, version: str, fallback_dir: str, realpath=False
) -> list[str]:
    """
    Returns a list of fallback licences paths that actually exist for a given module name and version.
    """
    global _EXIT_CODE

    expected_path = os.path.join(fallback_dir, f"{name}-{version}")
    versioned_paths = glob(expected_path)
    versioned_paths.extend(glob(os.path.join(fallback_dir, f"{name}-{version}.*")))

    non_versioned_paths = glob(os.path.join(fallback_dir, f"{name}*"))

    if not versioned_paths:
        if non_versioned_paths:
            # Fallback path for specific version is missing
            log.warning(
                "Fallback license for module '%s' is not for specific version %s,"
                " needs to be updated at: %s",
                name,
                version,
                expected_path,
            )
            _EXIT_CODE &= 1
            paths = non_versioned_paths

        else:
            # No fallback paths exist
            log.error(
                "Missing fallback license for module '%s', needs to be created at: %s",
                name,
                expected_path,
            )
            _EXIT_CODE &= 2
            paths = []

    else:
        paths = versioned_paths

    if realpath:
        return [os.path.realpath(path) for path in paths]
    return paths


def discover_node_package(
    module_path: str, as_path: bool = False
) -> tuple[list[str], dict]:
    """Discovers license files and package metadata of a Node package."""

    metadata = read_package_json_if_exists(module_path)

    filenames = []
    filenames.extend(
        glob("LICENSE", root_dir=module_path)
    )  # next will also match, but this takes preference
    filenames.extend(glob("LICENSE*", root_dir=module_path))
    filenames.extend(glob("license", root_dir=module_path))
    filenames.extend(glob("License", root_dir=module_path))
    filenames.extend(glob("license.?*", root_dir=module_path))
    filenames.extend(glob("License.?*", root_dir=module_path))

    filenames = dict.fromkeys(filenames).keys()  # unique
    if as_path:
        filenames = (os.path.join(module_path, filename) for filename in filenames)

    return list(filenames), metadata or {}


def discover_python_package(
    name: str, as_path: bool = False
) -> tuple[list[str], dict, str, str, str]:
    """Discovers license files and package metadata of a Python package."""

    filenames_exist = []

    dist = importlib.metadata.distribution(name)

    name = dist.name
    version = dist.version
    module_path = dist._path
    metadata = dist.metadata.json

    # discover license files by METADATA
    # importlib only returns first value of license-file field, we need to parse METADATA to find them all
    filenames, _ = read_py_metadata_if_exists(module_path)

    for filename in filenames:
        for path in ("", "licenses"):
            # sometimes license files are in licenses/ subdirectory but not prefixed as such in METADATA
            filename = os.path.join(path, filename)
            if os.path.exists(os.path.join(module_path, filename)):
                filenames_exist.append(filename)
                break

    # otherwise look for some common license file names
    if not filenames_exist:
        for prefix in ("", "licenses"):
            filenames_exist.extend(
                glob(os.path.join(prefix, "LICENSE"), root_dir=module_path)
            )
            # also matches LICENSE, but that comes first by repeating it above
            filenames_exist.extend(
                glob(os.path.join(prefix, "LICENSE*"), root_dir=module_path)
            )
            if filenames_exist:
                break

            filenames_exist.extend(
                glob(os.path.join(prefix, "COPYING*"), root_dir=module_path)
            )
            if filenames_exist:
                break

            filenames_exist.extend(
                glob(os.path.join(prefix, "NOTICE*"), root_dir=module_path)
            )
            if filenames_exist:
                break

    filenames_exist = dict.fromkeys(filenames_exist).keys()  # unique
    if as_path:
        filenames_exist = (
            os.path.join(module_path, filename) for filename in filenames_exist
        )

    return (
        list(filenames_exist),
        metadata or {},
        name,
        version,
        module_path,
    )


_metadata_re = re.compile(r"^([\w-]+):\s?(.*)$")


def read_py_metadata_if_exists(module_path: str, filename: str = "METADATA"):
    """
    Reads METADATA file from Python package directory.

    Returns a tuple of list of license files and the metadata dictionary with lowercase keys.
    """

    license_files = []
    metadata = None

    # read METADATA file
    if os.path.exists(path := os.path.join(module_path, filename)):
        with open(path, mode="rt", encoding="utf8") as f:
            metadata = {}
            for line in f:
                if m := _metadata_re.match(line):
                    key = m.group(1).lower().replace("-", "_")
                    value = m.group(2).strip() or None

                    # collect metadata, only the first value of each key
                    metadata.setdefault(key, value)

                    # collect license file names (can be multiple)
                    if key == "license_file" and value:
                        license_files.append(value)

    return license_files, metadata


def read_package_json_if_exists(
    module_path: str, filename: str = "package.json"
) -> dict | None:
    """Reads package.json file from Node package directory and returns as dictionary."""

    filepath = os.path.join(module_path, filename)
    if not os.path.exists(filepath):
        return None

    with open(filepath, mode="rt", encoding="utf8") as f:
        metadata = json.load(f)

    if not isinstance(metadata, dict):
        log.warning(
            "Package JSON file is expected to contain a dictionary, has %s instead: %s",
            type(metadata).__name__,
            filepath,
        )
        return None

    return metadata


def read_pipfile_lock(
    filepath: str = "Pipfile.lock", category: str = "default"
) -> list[tuple[str, str]]:
    """Reads Pipfile.lock file and returns a list of (package name, version) tuples."""

    with open(filepath, mode="rt", encoding="utf8") as f:
        pipfile = json.load(f)
    return [
        (name, meta["version"].lstrip("=")) for name, meta in pipfile[category].items()
    ]


def discover_node_packages(
    root_dir: str = "", fallback_dir: str = "", lock_type: str = "yarn"
) -> list[tuple[str, str, str, list[str], dict]]:
    """
    Discover installed Node packages from yarn.lock or package-lock.json.

    Returns a list of tuples with mostly strings:
    (package name, version, module path, a list of license file paths, a dictionary of package metadata)
    """

    packages = []
    modules_path = os.path.join(root_dir, "node_modules")

    if lock_type == "npm":
        installed = read_package_lock_json(
            filepath=os.path.join(root_dir, "package-lock.json")
        )
    else:
        installed = read_yarn_lock(filepath=os.path.join(root_dir, "yarn.lock"))

    for name, version in installed:
        license_paths, metadata = [], {}

        # look for license file in module directory, also read package.json
        if os.path.exists(
            module_path := node_module_dir(name, modules_path=modules_path)
        ):
            license_paths, metadata = discover_node_package(module_path)

            # update version string from package.json metadata
            # (a module can be listed multiple times with different versions in yarn.lock)
            if m_version := metadata.get("version"):
                version = m_version

        else:
            log.info(
                "Omitting module '%s' directory does not exist: %s", name, module_path
            )
            # Some or all packages may not be installed: package.json may contain different type of dependencies.
            # This script parses yarn.lock which contains all packages, a missing package directory can be because
            # that package is not required for the installed environment type.
            continue

        # otherwise look for license in fallback directory
        if not license_paths and fallback_dir:
            license_paths, metadata = discover_fallback_licenses(
                name, version, metadata, fallback_dir, discover_node_package
            )

        packages.append((name, version, module_path, license_paths, metadata or {}))

    return packages


def discover_python_packages(
    root_dir: str = "", fallback_dir: str = ""
) -> list[tuple[str, str, str, list[str], dict]]:
    """
    Discover installed Python packages from Pipfile.lock.

    Returns a list of tuples with mostly strings:
    (package name, version, license type (if specified), module path, a list of strings of license file paths)
    """
    global _EXIT_CODE

    packages = []

    for name, version in read_pipfile_lock(
        filepath=os.path.join(root_dir, "Pipfile.lock")
    ):
        try:
            license_paths, metadata, name, version, module_path = (
                discover_python_package(name)
            )
        except ModuleNotFoundError as exc:
            log.error("Module '%s' was not found: %s", name, str(exc))
            _EXIT_CODE |= 4
            continue

        # otherwise look for license in fallback directory
        if not license_paths and fallback_dir:
            license_paths, metadata = discover_fallback_licenses(
                name, version, metadata, fallback_dir, discover_python_package
            )

        packages.append((name, version, module_path, license_paths, metadata or {}))

    return packages


def discover_fallback_licenses(
    name: str,
    version: str,
    metadata: dict | None,
    fallback_dir: str,
    discover_package_callback: Callable,
) -> tuple[list[str], dict]:
    """Discovers fallback licenses for a given Python or Node package name and version, can extend metadata."""

    license_paths = []

    for fallback_path in fallback_license_paths(
        name, version, fallback_dir, realpath=True
    ):
        if os.path.exists(fallback_path):
            if os.path.isdir(fallback_path):
                log.info(
                    "Using fallback directory of module '%s': %s", name, fallback_path
                )
                license_paths, extend_metadata, *_ = discover_package_callback(
                    fallback_path, as_path=True
                )

            else:
                log.info(
                    "Using fallback license file of module '%s': %s",
                    name,
                    fallback_path,
                )
                license_paths, extend_metadata = [fallback_path], {}

            # fallback can extend metadata but can't override
            if extend_metadata:
                metadata = dict(extend_metadata, **metadata)

            break

    return license_paths, metadata


def parse_args() -> argparse.Namespace:
    """Parses command line arguments."""

    def validate_level(value: str) -> int:
        """Validates that level argument: integer between 1 and 5."""

        try:
            if 0 < (value := int(value)) < 6:
                return value
        except ValueError:
            pass
        raise argparse.ArgumentTypeError("Level must be an integer between 1 and 5.")

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "DIR",
        nargs="?",
        default="",
        help="Root directory of the project with yarn.lock, package-lock.json, or Pipfile.lock (default: current directory)",
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "-p",
        "--pipfile",
        action="store_true",
        help="Discover Python packages using Pipfile.lock",
    )
    mode.add_argument(
        "-y",
        "--yarn",
        action="store_true",
        help="Discover Node packages using yarn.lock",
    )
    mode.add_argument(
        "-n",
        "--npm",
        action="store_true",
        help="Discover Node packages using package-lock.json",
    )

    parser.add_argument(
        "--ado",
        action="store_true",
        help="Prefix log messages so they get included in Azure DevOps pipeline logs",
    )
    parser.add_argument(
        "--append",
        type=str,
        help="Append the contents of this file to the end of the SBOM",
    )
    parser.add_argument(
        "--author",
        action="store_const",
        const=1,
        dest="author",
        default=0,
        help="Show authors in packages table (default: do not show)",
    )
    parser.add_argument(
        "--author-details",
        action="store_const",
        const=3,
        dest="author",
        help="Show authors with details (email and homepage) in packages table",
    )
    parser.add_argument(
        "-1",
        action="store_const",
        const=1,
        dest="num",
        help="Include only the first license file found per package (default: include all)",
    )
    parser.add_argument(
        "-f",
        "--fallback-dir",
        type=str,
        help="Directory with fallback license files",
    )
    parser.add_argument(
        "-l",
        "--level",
        type=validate_level,
        metavar="INTEGER",
        default=1,
        help="Level of headers in the generated markdown (default: %(default)s)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w"),
        default=sys.stdout,
        help="Output file (example: sbom.md, default: standard output)",
    )
    parser.add_argument(
        "--prepend",
        type=str,
        help="Prepend the contents of this file to the beginning of the SBOM",
    )
    parser.add_argument(
        "-q",
        "--quote",
        action="store_true",
        help="Insert license texts as reflowable block-quotes (by default uses code blocks)",
    )

    return parser.parse_args()


class ADOFormatter(logging.Formatter):
    """Formatter mapping Python log levels to Azure DevOps-style logs messages."""

    LEVELS_MAP = {
        logging.CRITICAL: "##vso[task.logissue type=error]",
        logging.ERROR: "##vso[task.logissue type=error]",
        logging.WARNING: "##vso[task.logissue type=warning]",
        logging.INFO: "##[command]",
    }

    def format(self, record):
        prefix = self.LEVELS_MAP.get(record.levelno, "##[debug]")
        message = super().format(record)
        return f"{prefix}{message}"


def main() -> int:
    """Main entry point. Errors are communicated by log messages and bits set on _EXIT_CODE global bitmask."""

    global _EXIT_CODE
    _EXIT_CODE = 0

    mimetypes.init()
    log.debug("Known MIME type map files: %s", " ".join(mimetypes.knownfiles))

    args = parse_args()

    if args.ado:
        handler = logging.StreamHandler()
        handler.setFormatter(ADOFormatter("%(message)s"))
        logging.basicConfig(
            level=logging.INFO,
            handlers=[handler],
        )
    else:
        logging.basicConfig(level=logging.INFO)

    if args.yarn:
        packages = discover_node_packages(
            root_dir=args.DIR, fallback_dir=args.fallback_dir, lock_type="yarn"
        )
    elif args.npm:
        packages = discover_node_packages(
            root_dir=args.DIR, fallback_dir=args.fallback_dir, lock_type="npm"
        )
    elif args.pipfile:
        packages = discover_python_packages(
            root_dir=args.DIR, fallback_dir=args.fallback_dir
        )
    else:
        raise RuntimeError("neither --yarn, --npm, nor --pipfile specified")

    print(
        build_sbom(
            packages,
            quote_text=args.quote,
            prefix_headers=("#" * (args.level - 1)),
            num_licenses=args.num,
            show_author=args.author,
            prepend=args.prepend,
            append=args.append,
        ),
        file=args.output,
    )

    return _EXIT_CODE


if __name__ == "__main__":
    sys.exit(main())
