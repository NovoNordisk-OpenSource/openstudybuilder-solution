"""
Loader for the versioned Sponsor Model field schema.

The schema YAML is the single source of truth for how Sponsor Model source data
(CSV columns + model_info.json values) maps to clinical-mdr-api request bodies.
This module loads a given schema version, validates it, and turns its entries
into the ``PropertyDefinition`` objects consumed by ``FieldMapper`` at runtime.

The schema is versioned independently of Sponsor Model versions and is immutable
per version. Each file is named for its library and version -
``<schemas_dir>/<library-tag>.v<N>.yaml`` (e.g. ``sponsor.v1.yaml``) - and
declares its own ``schema_version`` and ``library_name``. A Sponsor Model
declares which version it follows via ``schema_version`` in its model_info.json
(default 1), and its ``library_name`` selects the matching schema file.
"""

import os
import re
from dataclasses import dataclass
from enum import Enum
from functools import partial
from typing import Any, Callable

import yaml

# Relative import is necessary here because this gets imported
# both by import_sponsor_data.importers.run_import_sponsormodels and by
# migration_024 which lives under a different package root.
from .sponsor_model_transformers import (
    get_transformer,
    is_registered,
)

# Repo-root-relative default location of the schema files.
# This module lives at importers/utils/, so three dirnames up is the repo root.
_REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DEFAULT_SCHEMAS_DIR = os.path.join(
    _REPO_ROOT,
    "datafiles",
    "sponsor_library",
    "sponsormodel",
    "schemas",
)

DEFAULT_SCHEMA_VERSION = 1
DEFAULT_LIBRARY = "Sponsor"

# Schema files are named "<library-tag>.v<N>.yaml", e.g. "sponsor.v1.yaml".
_SCHEMA_FILE_RE = re.compile(r"(?P<tag>.+)\.v(?P<version>\d+)\.yaml")


def library_tag(library_name: str) -> str:
    """Filename tag for a library, e.g. 'Sponsor' -> 'sponsor'."""
    return library_name.strip().lower().replace(" ", "_")


# Entities recognised by the schema.
KNOWN_ENTITIES = ("sponsor_model", "dataset", "dataset_variable")


# ---------------------------------------------------------------
# Property Definition System
# ---------------------------------------------------------------
# These live here, rather than next to FieldMapper in run_import_sponsormodels,
# so that there is exactly one PropertyType class. run_import_sponsormodels is
# executed twice when started via 'python -m' (once as __main__, once under its
# real name when this module imports it back), which would otherwise create two
# distinct PropertyType enums whose members compare unequal.


class PropertyType(Enum):
    """Type of property transformation needed"""

    STRING = "string"  # String field (empty → None)
    BOOLEAN = "boolean"  # Parse Y/X to bool
    REVERSE_BOOLEAN = "reverse_boolean"  # Parse and reverse
    INTEGER = "integer"  # Convert to int
    LIST_SPACE_SEPARATED = "list_space_separated"  # Split by space
    LIST_COMMA_SEPARATED = "list_comma_separated"  # Split by comma, strip whitespace
    CUSTOM = "custom"  # Custom transformer function


@dataclass
class PropertyDefinition:
    """
    Definition of how to map and transform a CSV field to an API field.

    Attributes:
        csv_field: The header name in the CSV file
        api_field: The field name to send to the API
        property_type: Type of transformation to apply - Defaults to STRING
        required: Whether this field must be present in CSV - Defaults to False
        custom_transformer: Optional custom transformation function
        default_value: Default value when cell is empty (not when header missing) - Defaults to None
        conditional_check: Optional function to determine if field should be processed
    """

    csv_field: str
    api_field: str
    property_type: PropertyType = PropertyType.STRING
    required: bool = False
    custom_transformer: Callable[[Any], Any] | None = None
    default_value: Any = None
    conditional_check: Callable[[list[str]], bool] | None = None


# Valid values for an entry's `type`.
VALID_TYPES = {member.value for member in PropertyType}

# Fields the API requires for routing/persistence. Each entity's `structural`
# block MUST declare (at least) these api_fields - users cannot remove them.
REQUIRED_STRUCTURAL_FIELDS = {
    "sponsor_model": {
        "ig_uid",
        "ig_version_number",
        "version_number",
        "library_name",
    },
    "dataset": {
        "dataset_uid",
        "sponsor_model_name",
        "sponsor_model_version_number",
        "library_name",
        "target_data_model_catalogue",
        "implemented_dataset_class",
        "is_basic_std",
        "is_cdisc_std",
    },
    "dataset_variable": {
        "target_data_model_catalogue",
        "dataset_uid",
        "dataset_variable_uid",
        "sponsor_model_name",
        "sponsor_model_version_number",
        "is_basic_std",
    },
}


class SponsorModelSchemaError(Exception):
    """Raised when a schema file is missing, unparseable, or fails validation."""


class SponsorModelSchema:
    """
    Loads, validates and caches versioned Sponsor Model schema files.

    Args:
        parser: the SponsorModels importer instance. Needed to bind custom
            transformers (which call parser methods and read ``parser.row_context``).
        schemas_dir: directory containing ``<library-tag>.v<N>.yaml`` files.
    """

    def __init__(self, parser: Any, schemas_dir: str = DEFAULT_SCHEMAS_DIR):
        self._parser = parser
        self._dir = schemas_dir
        # Caches keyed by absolute file path (identifies a library+version).
        self._cache: dict[str, dict] = {}
        self._raw_text: dict[str, str] = {}
        # (library_name, schema_version) -> path, built lazily from file content.
        self._index: dict[tuple[str, int], str] | None = None

    # -- loading / validation ------------------------------------------------

    def _discover(self) -> dict[tuple[str, int], str]:
        """
        Scan the schemas directory once, validating every schema file, and index
        them by their *content* ``(library_name, schema_version)``.

        A schema is identified by what it declares inside the YAML, not by its
        filename. The filename tag (e.g. ``interventional_core`` for a library
        named "Interventional - Core") is only a visual aid for maintainers; the
        ``.v<N>`` suffix must still match the declared ``schema_version``.
        """
        if self._index is not None:
            return self._index

        index: dict[tuple[str, int], str] = {}
        for name in sorted(os.listdir(self._dir)):
            match = _SCHEMA_FILE_RE.fullmatch(name)
            if not match:
                continue
            path = os.path.join(self._dir, name)
            raw = self._load_path(path, int(match.group("version")))
            key = (raw["library_name"], raw["schema_version"])
            if key in index and index[key] != path:
                raise SponsorModelSchemaError(
                    f"Duplicate schema for library '{key[0]}' version {key[1]}: "
                    f"'{index[key]}' and '{path}'"
                )
            index[key] = path
        self._index = index
        return index

    def _resolve_path(self, version: int, library_name: str) -> str:
        path = self._discover().get((library_name, version))
        if path is None:
            raise SponsorModelSchemaError(
                f"No schema found for library '{library_name}' version {version} "
                f"in '{self._dir}'"
            )
        return path

    def load(
        self,
        version: int = DEFAULT_SCHEMA_VERSION,
        library_name: str = DEFAULT_LIBRARY,
    ) -> dict:
        """Load (and cache) a schema by library + version. Fails fast if invalid."""
        return self._cache[self._resolve_path(version, library_name)]

    def _load_path(self, path: str, filename_version: int) -> dict:
        if path in self._cache:
            return self._cache[path]

        with open(path) as f:
            text = f.read()
        try:
            raw = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise SponsorModelSchemaError(
                f"Failed to parse sponsor model schema '{path}': {exc}"
            ) from exc

        self._validate(raw, filename_version, path)
        self._cache[path] = raw
        self._raw_text[path] = text
        return raw

    def get_raw_text(
        self,
        version: int = DEFAULT_SCHEMA_VERSION,
        library_name: str = DEFAULT_LIBRARY,
    ) -> str:
        """Return the raw (validated) YAML text of a schema, as a string."""
        return self._raw_text[self._resolve_path(version, library_name)]

    def available_schemas(self) -> list[dict]:
        """
        Every schema file in the directory, validated.

        Returns a list of {library_name, schema_version, schema} dicts, where
        `schema` is the raw YAML text - ready to POST to the API.
        """
        index = self._discover()
        out = []
        for (library_name, version), path in sorted(
            index.items(), key=lambda kv: (library_tag(kv[0][0]), kv[0][1])
        ):
            out.append(
                {
                    "library_name": library_name,
                    "schema_version": version,
                    "schema": self._raw_text[path],
                }
            )
        return out

    def _validate(self, raw: Any, filename_version: int, path: str) -> None:
        def fail(msg: str):
            raise SponsorModelSchemaError(
                f"Invalid sponsor model schema '{path}': {msg}"
            )

        if not isinstance(raw, dict):
            fail("top-level document must be a mapping")

        sv = raw.get("schema_version")
        if not isinstance(sv, int) or isinstance(sv, bool):
            fail("'schema_version' must be present and an integer")
        if sv != filename_version:
            fail(
                f"declares schema_version {sv} but its filename says "
                f"v{filename_version}"
            )

        lib = raw.get("library_name")
        if not isinstance(lib, str) or not lib.strip():
            fail("'library_name' must be present and a non-empty string")

        entities = raw.get("entities")
        if not isinstance(entities, dict):
            fail("'entities' must be a mapping")

        for entity_name in KNOWN_ENTITIES:
            if entity_name not in entities:
                fail(f"missing entity '{entity_name}'")
            self._validate_entity(entity_name, entities[entity_name], fail)

    def _validate_entity(
        self, entity_name: str, block: Any, fail: Callable[[str], None]
    ) -> None:
        if not isinstance(block, dict):
            fail(f"entity '{entity_name}' must be a mapping")

        structural = block.get("structural") or []
        extensible = block.get("extensible") or []
        if not isinstance(structural, list) or not isinstance(extensible, list):
            fail(f"entity '{entity_name}': structural/extensible must be lists")

        # Structural must declare every API-required field (users can't remove them).
        structural_fields = {
            e.get("api_field") for e in structural if isinstance(e, dict)
        }
        missing = REQUIRED_STRUCTURAL_FIELDS.get(entity_name, set()) - structural_fields
        if missing:
            fail(
                f"entity '{entity_name}': structural is missing required "
                f"field(s): {sorted(missing)}"
            )

        # api_field -> list of entries, to police duplicates.
        by_api_field: dict[str, list] = {}
        for entry in structural + extensible:
            if not isinstance(entry, dict):
                fail(f"entity '{entity_name}': every entry must be a mapping")
            api_field = entry.get("api_field")
            if not api_field:
                fail(f"entity '{entity_name}': an entry is missing 'api_field'")
            by_api_field.setdefault(api_field, []).append(entry)
            self._validate_entry(entity_name, entry, fail)

        # Duplicate api_fields are allowed only when each carries a `condition`.
        for api_field, entries in by_api_field.items():
            if len(entries) > 1 and not all("condition" in e for e in entries):
                fail(
                    f"entity '{entity_name}': duplicate api_field '{api_field}' "
                    f"without mutually-exclusive conditions"
                )

    def _validate_entry(
        self, entity_name: str, entry: dict, fail: Callable[[str], None]
    ) -> None:
        api_field = entry.get("api_field")
        is_injected = entry.get("source") == "injected"
        has_source = "source_field" in entry

        if is_injected:
            if has_source:
                fail(
                    f"entity '{entity_name}': injected field '{api_field}' "
                    f"must not have a source_field"
                )
            return  # injected fields produce no PropertyDefinition; nothing else to check

        if not has_source:
            fail(
                f"entity '{entity_name}': field '{api_field}' has neither "
                f"'source_field' nor source: injected"
            )

        ptype = entry.get("type")
        if ptype not in VALID_TYPES:
            fail(
                f"entity '{entity_name}': field '{api_field}' has invalid "
                f"type '{ptype}'"
            )

        transformer = entry.get("transformer")
        if ptype == "custom":
            if not transformer:
                fail(
                    f"entity '{entity_name}': field '{api_field}' is type 'custom' "
                    f"but has no transformer"
                )
            if not is_registered(transformer):
                fail(
                    f"entity '{entity_name}': field '{api_field}' references "
                    f"unknown transformer '{transformer}'"
                )
        elif transformer:
            fail(
                f"entity '{entity_name}': field '{api_field}' sets a transformer "
                f"but is not type 'custom'"
            )

        condition = entry.get("condition")
        if condition is not None:
            if not isinstance(condition, dict) or set(condition) - {
                "header_present",
                "header_absent",
            }:
                fail(
                    f"entity '{entity_name}': field '{api_field}' has invalid "
                    f"condition {condition!r}"
                )

    # -- consumption ---------------------------------------------------------

    def get_property_definitions(
        self,
        entity_name: str,
        version: int = DEFAULT_SCHEMA_VERSION,
        library_name: str = DEFAULT_LIBRARY,
    ) -> list:
        """
        Build the ordered ``PropertyDefinition`` list for an entity.

        Only CSV-mapped entries (those with a ``source_field``) become
        PropertyDefinitions; injected fields are documentation/validation only.
        Entries are emitted structural-first, then extensible, preserving order.
        """
        raw = self.load(version, library_name)
        try:
            entity = raw["entities"][entity_name]
        except KeyError:
            raise SponsorModelSchemaError(
                f"Unknown entity '{entity_name}' in schema version {version}"
            ) from None

        entries = list(entity.get("structural") or []) + list(
            entity.get("extensible") or []
        )

        definitions = []
        for entry in entries:
            if "source_field" not in entry:
                continue  # injected -> not a PropertyDefinition

            transformer = None
            if entry.get("transformer"):
                func = get_transformer(entry["transformer"])
                # Bind the parser; FieldMapper calls custom_transformer(value).
                transformer = partial(func, parser=self._parser)

            definitions.append(
                PropertyDefinition(
                    csv_field=entry["source_field"],
                    api_field=entry["api_field"],
                    property_type=PropertyType(entry["type"]),
                    required=bool(entry.get("required", False)),
                    custom_transformer=transformer,
                    default_value=entry.get("default", None),
                    conditional_check=self._build_condition(entry.get("condition")),
                )
            )
        return definitions

    @staticmethod
    def _build_condition(
        condition: dict | None,
    ) -> Callable[[list[str]], bool] | None:
        """Turn a declarative condition into a headers-predicate, or None."""
        if not condition:
            return None
        if "header_present" in condition:
            col = condition["header_present"]
            return lambda headers, _col=col: _col in headers
        if "header_absent" in condition:
            col = condition["header_absent"]
            return lambda headers, _col=col: _col not in headers
        return None
