"""Minimal tests for neomodel schema drift JSON builder."""

from __future__ import annotations

import json

from clinical_mdr_api.utils.neomodel_schema import (
    build_neomodel_schema_payload,
    dumps_neomodel_schema_json,
)


def test_neomodel_schema_payload_shape_and_canonical_roundtrip() -> None:
    payload = build_neomodel_schema_payload(
        include_extensions=True,
        module_prefixes=None,
    )

    assert payload["structured_node_class_count"] == len(payload["nodes"])
    assert len(payload["nodes"]) > 0

    required_node_keys = {"class", "module", "label", "properties", "relationships"}
    for node in payload["nodes"]:
        assert set(node.keys()) == required_node_keys
        assert isinstance(node["properties"], dict)
        for _prop_name, prop_type in node["properties"].items():
            assert isinstance(prop_type, str)

        for rel in node["relationships"]:
            assert isinstance(rel["attribute"], str)
            assert isinstance(rel["relation_type"], str)
            assert isinstance(rel["direction"], str)
            assert isinstance(rel["cardinality"], str)
            assert "target_class" in rel
            if "rel_properties_model" in rel:
                assert isinstance(rel["rel_properties_model"], str)
            if "lookup_error" in rel:
                assert isinstance(rel["lookup_error"], str)

    text = dumps_neomodel_schema_json(payload, compact=False)
    roundtrip = json.loads(text)
    assert roundtrip == payload
