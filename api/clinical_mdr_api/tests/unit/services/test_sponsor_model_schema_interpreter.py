"""Unit tests for the Sponsor Model Schema interpreter.

The interpreter is pure parsing/projection logic over a schema blob; it needs no
database. These tests pin the parsing edge cases and the projection precedence
rules that the integration tests only ever exercise with well-formed schemas.
"""

import pytest

from clinical_mdr_api.services.standard_data_models import (
    sponsor_model_schema_interpreter as interp_mod,
)
from clinical_mdr_api.services.standard_data_models.sponsor_model_schema_interpreter import (
    ENTITY_DATASET,
    ENTITY_DATASET_VARIABLE,
    ENTITY_SPONSOR_MODEL,
    SponsorModelSchemaInterpreter,
)

LIBRARY = "Sponsor"

# A representative, well-formed schema declaring all three entities with a mix of
# structural and extensible fields, plus type / required metadata.
FULL_SCHEMA = {
    "entities": {
        ENTITY_SPONSOR_MODEL: {
            "extensible": [{"api_field": "sm_foo", "type": "string"}],
        },
        ENTITY_DATASET: {
            "structural": [
                {"api_field": "is_basic_std", "type": "boolean", "required": True},
                {"api_field": "structure", "type": "string"},
            ],
            "extensible": [{"api_field": "foo", "type": "string"}],
        },
        ENTITY_DATASET_VARIABLE: {
            "structural": [{"api_field": "order", "type": "integer"}],
            "extensible": [{"api_field": "bar"}],  # no declared type
        },
    }
}


def _interpreter(parsed) -> SponsorModelSchemaInterpreter:
    return SponsorModelSchemaInterpreter(
        schema_version=2, library_name=LIBRARY, parsed=parsed
    )


class TestParsing:
    def test_field_names_are_structural_then_extensible_in_declaration_order(self):
        i = _interpreter(FULL_SCHEMA)
        # Structural fields come first (in order), then extensible (in order).
        assert i.field_names(ENTITY_DATASET) == ["is_basic_std", "structure", "foo"]

    def test_structural_vs_extensible_split(self):
        i = _interpreter(FULL_SCHEMA)
        assert i.structural_field_names(ENTITY_DATASET) == {"is_basic_std", "structure"}
        assert [fd.api_field for fd in i.extensible_fields(ENTITY_DATASET)] == ["foo"]

    def test_get_field_carries_type_and_required(self):
        i = _interpreter(FULL_SCHEMA)
        fd = i.get_field(ENTITY_DATASET, "is_basic_std")
        assert fd is not None
        assert fd.base_type == "boolean"
        assert fd.required is True
        assert fd.is_extensible is False

    def test_unknown_type_collapses_to_none(self):
        i = _interpreter(
            {
                "entities": {
                    ENTITY_DATASET: {
                        "extensible": [{"api_field": "x", "type": "weird"}]
                    }
                }
            }
        )
        assert i.get_field(ENTITY_DATASET, "x").base_type is None

    def test_missing_type_and_required_default(self):
        i = _interpreter(FULL_SCHEMA)
        fd = i.get_field(ENTITY_DATASET_VARIABLE, "bar")
        assert fd.base_type is None
        assert fd.required is False
        assert fd.is_extensible is True

    def test_get_field_returns_none_for_unknown_field(self):
        i = _interpreter(FULL_SCHEMA)
        assert i.get_field(ENTITY_DATASET, "does_not_exist") is None

    @pytest.mark.parametrize("bad_schema", [None, "just a string", ["a", "list"], 42])
    def test_non_mapping_schema_yields_empty_entities(self, bad_schema):
        # A malformed/absent schema must never crash; every entity is simply empty.
        i = _interpreter(bad_schema)
        for entity in (ENTITY_SPONSOR_MODEL, ENTITY_DATASET, ENTITY_DATASET_VARIABLE):
            assert not i.field_names(entity)
            assert i.structural_field_names(entity) == set()

    def test_entries_that_are_not_dicts_are_skipped(self):
        i = _interpreter(
            {"entities": {ENTITY_DATASET: {"extensible": ["not-a-dict", 123, None]}}}
        )
        assert not i.field_names(ENTITY_DATASET)

    def test_entries_without_api_field_are_skipped(self):
        i = _interpreter(
            {
                "entities": {
                    ENTITY_DATASET: {
                        "extensible": [{"type": "string"}, {"api_field": "kept"}]
                    }
                }
            }
        )
        assert i.field_names(ENTITY_DATASET) == ["kept"]

    def test_missing_group_keys_are_tolerated(self):
        # An entity that declares only 'extensible' (no 'structural') and vice versa.
        i = _interpreter(
            {"entities": {ENTITY_DATASET: {"extensible": [{"api_field": "foo"}]}}}
        )
        assert i.field_names(ENTITY_DATASET) == ["foo"]
        assert i.structural_field_names(ENTITY_DATASET) == set()

    def test_unknown_entity_returns_empty(self):
        i = _interpreter(FULL_SCHEMA)
        assert not i.field_names("not_an_entity")


class TestProject:
    def test_declared_but_absent_fields_are_null_filled(self):
        i = _interpreter(FULL_SCHEMA)
        result = i.project(ENTITY_DATASET, base={"is_basic_std": True})
        # Every declared field is present; the ones with no value become None.
        assert result["is_basic_std"] is True
        assert result["structure"] is None
        assert result["foo"] is None

    def test_stored_extra_props_are_included(self):
        i = _interpreter(FULL_SCHEMA)
        result = i.project(
            ENTITY_DATASET, base={"is_basic_std": True}, extra_props={"foo": "stored"}
        )
        assert result["foo"] == "stored"

    def test_undeclared_stored_extras_are_kept(self):
        # A stored prop the schema never declares is still surfaced (never dropped).
        i = _interpreter(FULL_SCHEMA)
        result = i.project(
            ENTITY_DATASET, base={"is_basic_std": True}, extra_props={"qux": "kept"}
        )
        assert result["qux"] == "kept"

    def test_stored_prop_never_clobbers_a_resolved_structural_value(self):
        # base already carries the authoritative structural value; a stored prop of
        # the same name must not overwrite it.
        i = _interpreter(FULL_SCHEMA)
        result = i.project(
            ENTITY_DATASET,
            base={"is_basic_std": True},
            extra_props={"is_basic_std": False},
        )
        assert result["is_basic_std"] is True

    def test_base_only_projection_without_extras(self):
        i = _interpreter(FULL_SCHEMA)
        result = i.project(ENTITY_SPONSOR_MODEL, base={"name": "sm"})
        assert result["name"] == "sm"
        assert result["sm_foo"] is None


class TestConstructionAndCaching:
    def setup_method(self):
        interp_mod._INTERPRETER_CACHE.clear()

    def test_from_string_parses_yaml(self):
        i = SponsorModelSchemaInterpreter._from_string(
            "entities:\n  dataset:\n    extensible:\n      - api_field: foo\n",
            2,
            LIBRARY,
        )
        assert i.field_names(ENTITY_DATASET) == ["foo"]

    def test_from_string_degrades_on_invalid_yaml(self):
        # Should not raise; a read must never fail on a stored blob it can't parse.
        i = SponsorModelSchemaInterpreter._from_string(
            "key: [unbalanced\n bad", 2, LIBRARY
        )
        assert not i.field_names(ENTITY_DATASET)

    def test_for_schema_string_caches_by_library_and_version(self):
        first = SponsorModelSchemaInterpreter.for_schema_string(
            "entities:\n  dataset:\n    extensible:\n      - api_field: foo\n",
            2,
            LIBRARY,
        )
        # A second call with different content but the same key returns the cached one
        # (schemas are immutable, so the key is authoritative).
        second = SponsorModelSchemaInterpreter.for_schema_string(
            "entities:\n  dataset:\n    extensible:\n      - api_field: other\n",
            2,
            LIBRARY,
        )
        assert first is second
        assert second.field_names(ENTITY_DATASET) == ["foo"]

    def test_different_version_is_cached_separately(self):
        v2 = SponsorModelSchemaInterpreter.for_schema_string(
            "entities:\n  dataset:\n    extensible:\n      - api_field: foo\n",
            2,
            LIBRARY,
        )
        v3 = SponsorModelSchemaInterpreter.for_schema_string(
            "entities:\n  dataset:\n    extensible:\n      - api_field: baz\n",
            3,
            LIBRARY,
        )
        assert v2 is not v3
        assert v3.field_names(ENTITY_DATASET) == ["baz"]
