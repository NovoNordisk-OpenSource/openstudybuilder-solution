"""Unit tests for ``common.openapi`` schema post-processing helpers."""

from copy import deepcopy
from typing import Any

from common.openapi import (
    strip_min_length_from_nullable_input_strings,
    strip_null_from_query_parameter_schemas,
)

# ---------------------------------------------------------------------------
# strip_min_length_from_nullable_input_strings
# ---------------------------------------------------------------------------


def test_strip_min_length_drops_min_length_on_nullable_string_branch():
    """Nullable ``str | None`` fields lose ``minLength`` so ``""`` validates.

    ``InputModel._string_validator`` coerces ``""`` to ``None`` for such
    fields at runtime, so the spec must also accept ``""``.
    """
    schema = {
        "components": {
            "schemas": {
                "OdmConditionPostInput": {
                    "properties": {
                        "oid": {
                            "anyOf": [
                                {"type": "string", "minLength": 1},
                                {"type": "null"},
                            ],
                            "title": "Oid",
                        },
                    },
                },
            },
        },
    }

    strip_min_length_from_nullable_input_strings(schema)

    assert schema["components"]["schemas"]["OdmConditionPostInput"]["properties"][
        "oid"
    ] == {
        "anyOf": [{"type": "string"}, {"type": "null"}],
        "title": "Oid",
    }


def test_strip_min_length_preserves_non_nullable_string_constraints():
    """Required ``str`` fields keep their ``minLength`` constraint.

    ``_string_validator`` only coerces empty strings when the annotation
    permits ``None``. Non-nullable fields continue to reject ``""`` at
    runtime, so the spec must continue to reject it as well.
    """
    schema = {
        "components": {
            "schemas": {
                "OdmConditionPostInput": {
                    "properties": {
                        "name": {
                            "type": "string",
                            "minLength": 1,
                            "title": "Name",
                        },
                    },
                },
            },
        },
    }
    original = deepcopy(schema)

    strip_min_length_from_nullable_input_strings(schema)

    assert schema == original


def test_strip_min_length_ignores_non_string_nullable_branches():
    """Non-string nullable fields are untouched (no ``minLength`` to drop)."""
    schema = {
        "components": {
            "schemas": {
                "Example": {
                    "properties": {
                        "count": {
                            "anyOf": [
                                {"type": "integer", "minimum": 0},
                                {"type": "null"},
                            ],
                        },
                    },
                },
            },
        },
    }
    original = deepcopy(schema)

    strip_min_length_from_nullable_input_strings(schema)

    assert schema == original


def test_strip_min_length_ignores_anyof_without_null_branch():
    """``anyOf`` unions that do not include ``null`` keep ``minLength``.

    ``_string_validator`` only coerces ``""`` for unions containing
    ``NoneType``, so unions like ``str | UUID`` retain their constraints.
    """
    schema = {
        "components": {
            "schemas": {
                "Example": {
                    "properties": {
                        "ident": {
                            "anyOf": [
                                {"type": "string", "minLength": 1},
                                {"type": "string", "format": "uuid"},
                            ],
                        },
                    },
                },
            },
        },
    }
    original = deepcopy(schema)

    strip_min_length_from_nullable_input_strings(schema)

    assert schema == original


def test_strip_min_length_recurses_into_nested_schemas():
    """Nested component schemas (e.g. array items, ``$defs``) are visited."""
    schema: dict[str, Any] = {
        "components": {
            "schemas": {
                "Wrapper": {
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {
                                "properties": {
                                    "tag": {
                                        "anyOf": [
                                            {"type": "string", "minLength": 1},
                                            {"type": "null"},
                                        ],
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    }

    strip_min_length_from_nullable_input_strings(schema)

    tag_schema = schema["components"]["schemas"]["Wrapper"]["properties"]["items"][
        "items"
    ]["properties"]["tag"]
    assert tag_schema == {"anyOf": [{"type": "string"}, {"type": "null"}]}


def test_strip_min_length_handles_missing_components():
    """Schemas without ``components.schemas`` are handled gracefully."""
    schema: dict[str, Any] = {"paths": {}}

    strip_min_length_from_nullable_input_strings(schema)

    assert schema == {"paths": {}}


# ---------------------------------------------------------------------------
# strip_null_from_query_parameter_schemas (regression coverage)
# ---------------------------------------------------------------------------


def test_strip_null_query_parameter_removes_null_branch():
    schema = {
        "paths": {
            "/items": {
                "get": {
                    "parameters": [
                        {
                            "name": "status",
                            "in": "query",
                            "schema": {
                                "anyOf": [
                                    {"type": "string"},
                                    {"type": "null"},
                                ],
                                "default": None,
                            },
                        },
                    ],
                },
            },
        },
    }

    strip_null_from_query_parameter_schemas(schema)

    assert schema["paths"]["/items"]["get"]["parameters"][0]["schema"] == {
        "type": "string",
    }


def test_strip_null_query_parameter_leaves_body_and_path_alone():
    """Only ``in: query`` parameters are mutated — body/path/header/cookie
    schemas legitimately carry null branches and must be left alone."""
    schema = {
        "paths": {
            "/items/{item_id}": {
                "get": {
                    "parameters": [
                        {
                            "name": "item_id",
                            "in": "path",
                            "schema": {
                                "anyOf": [
                                    {"type": "string"},
                                    {"type": "null"},
                                ],
                            },
                        },
                    ],
                },
            },
        },
    }
    original = deepcopy(schema)

    strip_null_from_query_parameter_schemas(schema)

    assert schema == original
