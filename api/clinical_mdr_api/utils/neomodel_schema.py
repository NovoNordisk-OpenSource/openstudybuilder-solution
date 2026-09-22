"""
JSON-serializable snapshot of neomodel StructuredNode definitions.
Used for drift detection (nodes, properties, relationships) against a committed baseline.
"""

import importlib
import json
import pkgutil
from typing import Any

from neomodel import RelationshipDefinition, StructuredNode
from neomodel.properties import Property
from neomodel.util import RelationshipDirection


def import_submodules(package_name: str) -> None:
    package = importlib.import_module(package_name)
    if not hasattr(package, "__path__"):
        return
    for _finder, name, _is_pkg in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        importlib.import_module(name)


def load_all_node_modules(*, include_extensions: bool) -> None:
    importlib.import_module("clinical_mdr_api.domain_repositories.models")
    import_submodules("clinical_mdr_api.domain_repositories.models")
    if include_extensions:
        try:
            importlib.import_module("extensions.prodex.db_models")
        except ImportError:
            pass


def all_structured_node_subclasses(
    root: type[StructuredNode],
) -> list[type[StructuredNode]]:
    seen: set[type[StructuredNode]] = set()
    out: list[type[StructuredNode]] = []

    def walk(cls: type[StructuredNode]) -> None:
        for sub in cls.__subclasses__():
            if sub not in seen:
                seen.add(sub)
                out.append(sub)
                walk(sub)

    walk(root)
    return out


def type_ref(t: type | None) -> str | None:
    if t is None:
        return None
    return f"{t.__module__}.{t.__name__}"


def direction_name(direction: Any) -> str:
    if isinstance(direction, RelationshipDirection):
        return direction.name
    return str(direction)


def serialize_relationship_minimal(
    attr_name: str, rel: RelationshipDefinition
) -> dict[str, Any]:
    err: str | None = None
    try:
        rel.lookup_node_class()
    except Exception as exc:  # pylint: disable=broad-exception-caught
        err = f"{type(exc).__name__}: {exc}"

    definition = rel.definition
    node_class = definition.get("node_class")
    model = definition.get("model")
    raw = getattr(rel, "_raw_class", None)
    if isinstance(raw, str):
        target_ref: str | None = raw
    elif isinstance(raw, type):
        target_ref = type_ref(raw)
    else:
        target_ref = None
    if isinstance(node_class, type):
        target_ref = type_ref(node_class)

    manager = rel.manager
    cardinality = getattr(manager, "__name__", repr(manager))

    base: dict[str, Any] = {
        "attribute": attr_name,
        "relation_type": definition.get("relation_type"),
        "direction": direction_name(definition.get("direction")),
        "cardinality": cardinality,
        "target_class": target_ref,
    }
    if isinstance(model, type):
        base["rel_properties_model"] = type_ref(model)
    if err is not None:
        base["lookup_error"] = err
    return base


def build_node_entry_minimal(cls: type[StructuredNode]) -> dict[str, Any]:
    rels = cls.defined_properties(rels=True, aliases=False, properties=False)
    props = cls.defined_properties(rels=False, aliases=False, properties=True)

    relationships = [
        serialize_relationship_minimal(name, rel)
        for name, rel in sorted(rels.items(), key=lambda x: x[0])
        if isinstance(rel, RelationshipDefinition)
    ]

    # Single stable type token per property (drift on type or presence).
    properties: dict[str, str] = {
        name: type(prop).__name__
        for name, prop in sorted(props.items(), key=lambda x: x[0])
        if isinstance(prop, Property)
    }

    return {
        "class": cls.__name__,
        "module": cls.__module__,
        "label": getattr(cls, "__label__", None),
        "properties": properties,
        "relationships": relationships,
    }


def build_neomodel_schema_payload(
    *,
    include_extensions: bool = True,
    module_prefixes: list[str] | None = None,
) -> dict[str, Any]:
    """
    Load domain models and return a minimal payload for drift detection.

    CI, tests, and the CLI should call this with the same arguments as the committed baseline.
    """
    load_all_node_modules(include_extensions=include_extensions)
    prefixes = list(module_prefixes or [])
    nodes: list[dict[str, Any]] = []

    for cls in all_structured_node_subclasses(StructuredNode):
        if getattr(cls, "__abstract_node__", False):
            continue
        if prefixes and not any(cls.__module__.startswith(p) for p in prefixes):
            continue
        nodes.append(build_node_entry_minimal(cls))

    nodes.sort(key=lambda x: (x["module"], x["class"]))
    return {
        "structured_node_class_count": len(nodes),
        "nodes": nodes,
    }


def dumps_neomodel_schema_json(
    payload: dict[str, Any], *, compact: bool = False
) -> str:
    """Serialize payload in a canonical form for stable byte-for-byte comparison."""
    text = json.dumps(
        payload,
        sort_keys=True,
        indent=None if compact else 2,
    )
    if not compact and not text.endswith("\n"):
        text += "\n"
    if compact and not text.endswith("\n"):
        text += "\n"
    return text
