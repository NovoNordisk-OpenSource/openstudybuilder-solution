"""
Interpreter that turns a stored Sponsor Model Schema blob into the authoritative,
per-entity field model the API projects reads and writes through.

The API never runs transformers and never interprets ``ui`` metadata. It uses the
schema only for: the set of field names per entity, their structural-vs-extensible
split, and (optionally) each extensible field's base type.

Schemas are immutable, so a parsed interpreter is cached by ``(library, version)``
forever — no invalidation is needed here.
"""

import logging
from dataclasses import dataclass
from typing import Any

import yaml

from clinical_mdr_api.domain_repositories.standard_data_models.sponsor_model_schema_repository import (
    SponsorModelSchemaRepository,
)
from common.config import settings

log = logging.getLogger(__name__)

# The three entities the schema describes, keyed exactly as they appear in the blob.
ENTITY_SPONSOR_MODEL = "sponsor_model"
ENTITY_DATASET = "dataset"
ENTITY_DATASET_VARIABLE = "dataset_variable"
ENTITIES = (ENTITY_SPONSOR_MODEL, ENTITY_DATASET, ENTITY_DATASET_VARIABLE)

# Base JSON types the importer collapses its transform types down to before POSTing.
BASE_TYPES = ("string", "boolean", "integer", "list")


@dataclass(frozen=True)
class FieldDescriptor:
    api_field: str
    base_type: str | None
    required: bool
    is_extensible: bool


# Parsed interpreters, cached forever by (library_name, schema_version).
_INTERPRETER_CACHE: dict[tuple[str, int], "SponsorModelSchemaInterpreter"] = {}


class SponsorModelSchemaInterpreter:
    """Parsed, queryable view over a single schema version."""

    def __init__(
        self, schema_version: int, library_name: str, parsed: dict[str, Any] | None
    ) -> None:
        self.schema_version = schema_version
        self.library_name = library_name
        # {entity: {api_field: FieldDescriptor}} preserving declaration order.
        self._by_entity: dict[str, dict[str, FieldDescriptor]] = {}
        self._parse(parsed)

    def _parse(self, parsed: dict[str, Any] | None) -> None:
        if not isinstance(parsed, dict):
            if parsed is not None:
                log.warning(
                    "Sponsor Model Schema v%s for library '%s' is not a mapping; "
                    "treating it as empty.",
                    self.schema_version,
                    self.library_name,
                )
            for entity in ENTITIES:
                self._by_entity[entity] = {}
            return

        entities = parsed.get("entities") or {}
        for entity in ENTITIES:
            fields: dict[str, FieldDescriptor] = {}
            entity_def = entities.get(entity) or {}
            for is_extensible, group_key in (
                (False, "structural"),
                (True, "extensible"),
            ):
                for entry in entity_def.get(group_key, []) or []:
                    if not isinstance(entry, dict):
                        continue
                    api_field = entry.get("api_field")
                    if not api_field:
                        continue
                    base_type = entry.get("type")
                    fields[api_field] = FieldDescriptor(
                        api_field=api_field,
                        base_type=base_type if base_type in BASE_TYPES else None,
                        required=bool(entry.get("required", False)),
                        is_extensible=is_extensible,
                    )
            self._by_entity[entity] = fields

    def field_names(self, entity: str) -> list[str]:
        """All declared field names (structural + extensible), in declaration order."""
        return list(self._by_entity.get(entity, {}).keys())

    def extensible_fields(self, entity: str) -> list[FieldDescriptor]:
        return [
            fd for fd in self._by_entity.get(entity, {}).values() if fd.is_extensible
        ]

    def structural_field_names(self, entity: str) -> set[str]:
        return {
            name
            for name, fd in self._by_entity.get(entity, {}).items()
            if not fd.is_extensible
        }

    def get_field(self, entity: str, api_field: str) -> FieldDescriptor | None:
        return self._by_entity.get(entity, {}).get(api_field)

    def project(
        self,
        entity: str,
        base: dict[str, Any],
        extra_props: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Build the complete, schema-aligned response dict for one row.

        - ``base`` carries the structural (and, on the create path, already-present
          extensible) values.
        - ``extra_props`` carries stored node properties recovered on read.

        Every stored extra is included (declared or not, so nothing is silently
        lost), and every schema-declared field that is still absent is emitted as
        ``None`` so the response shape is complete and stable.
        """
        result = dict(base)
        for key, value in (extra_props or {}).items():
            # Never let a stored prop clobber a structural value already resolved.
            result.setdefault(key, value)
        for api_field in self.field_names(entity):
            result.setdefault(api_field, None)
        return result

    # -- construction / caching ------------------------------------------------

    @classmethod
    def _from_string(
        cls, schema_string: str, schema_version: int, library_name: str
    ) -> "SponsorModelSchemaInterpreter":
        try:
            parsed = yaml.safe_load(schema_string)
        except yaml.YAMLError:
            # Should not happen (validated at publish), but never fail a read on it.
            log.warning(
                "Failed to parse stored Sponsor Model Schema v%s for library '%s'; "
                "projecting structural + stored extras only.",
                schema_version,
                library_name,
            )
            parsed = None
        return cls(schema_version, library_name, parsed)

    @classmethod
    def for_schema_string(
        cls,
        schema_string: str,
        schema_version: int,
        library_name: str,
    ) -> "SponsorModelSchemaInterpreter":
        """Build (and cache) directly from a schema blob already in hand.

        Used when a ``FOLLOWS_SCHEMA``-linked node gives us the version and blob
        without a store round-trip.
        """
        cache_key = (library_name, schema_version)
        cached = _INTERPRETER_CACHE.get(cache_key)
        if cached is not None:
            return cached
        interpreter = cls._from_string(schema_string, schema_version, library_name)
        _INTERPRETER_CACHE[cache_key] = interpreter
        return interpreter

    @classmethod
    def for_version(
        cls,
        schema_version: int,
        library_name: str | None = None,
    ) -> "SponsorModelSchemaInterpreter | None":
        """Load, parse and cache the schema for ``(library, version)``.

        Returns ``None`` when the version is not published (callers decide whether
        that is a hard error on write or a graceful degrade on read).
        """
        library_name = library_name or settings.sponsor_library_name
        cache_key = (library_name, schema_version)
        cached = _INTERPRETER_CACHE.get(cache_key)
        if cached is not None:
            return cached

        ar = SponsorModelSchemaRepository().get_by_version(library_name, schema_version)
        if ar is None:
            return None
        return cls.for_schema_string(
            schema_string=ar.schema_vo.schema,
            schema_version=schema_version,
            library_name=library_name,
        )
