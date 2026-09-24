"""OpenAPI schema post-processing utilities shared by the three APIs."""

from typing import Any


def strip_min_length_from_nullable_input_strings(
    openapi_schema: dict[str, Any],
) -> None:
    """Drop ``minLength`` from string branches of nullable union schemas.

    ``InputModel._string_validator`` coerces empty strings to ``None`` for any
    field typed ``str | None`` that also declares a ``min_length`` constraint.
    The OpenAPI schema, however, renders the same field as
    ``anyOf: [{"type": "string", "minLength": 1}, {"type": "null"}]`` and
    reports ``""`` as invalid. Contract testers (Schemathesis v4) see runtime
    accepting requests the spec rejects and raise schema-violation failures.

    This helper walks all request-body component schemas and removes
    ``minLength`` from every string branch that co-exists with a ``null``
    branch in the same ``anyOf``, so the spec matches runtime behaviour.
    Non-nullable string fields retain their ``minLength`` constraint.
    """
    for component in openapi_schema.get("components", {}).get("schemas", {}).values():
        _strip_min_length_from_nullable_strings(component)


def _strip_min_length_from_nullable_strings(node: Any) -> None:
    """Recursively drop ``minLength`` on string branches of nullable unions."""
    if isinstance(node, dict):
        any_of = node.get("anyOf")
        if isinstance(any_of, list) and any(
            branch == {"type": "null"} for branch in any_of
        ):
            for branch in any_of:
                if (
                    isinstance(branch, dict)
                    and branch.get("type") == "string"
                    and "minLength" in branch
                ):
                    del branch["minLength"]
        for value in node.values():
            _strip_min_length_from_nullable_strings(value)
    elif isinstance(node, list):
        for item in node:
            _strip_min_length_from_nullable_strings(item)


def strip_null_from_query_parameter_schemas(openapi_schema: dict[str, Any]) -> None:
    """Remove ``{"type": "null"}`` branches from query parameter ``anyOf`` schemas.

    FastAPI generates ``anyOf: [<type>, {"type": "null"}]`` for any query
    parameter declared with an ``Optional[...]`` (or ``| None``) Python type.
    Query strings cannot natively transmit a null value: an omitted parameter
    is semantically different from one whose value is the literal string
    ``null``. Schemathesis v4 honors the null branch when generating test data
    and produces requests like ``?status=null`` which Pydantic then rejects,
    causing spurious contract-test failures.

    This helper mutates ``openapi_schema`` in place, dropping the null branch
    (and a matching ``default: null`` on the same schema) from every query
    parameter. Path, header, cookie, and request-body schemas are left alone,
    since null is a legitimate JSON value in those contexts.
    """
    for path_item in openapi_schema.get("paths", {}).values():
        if not isinstance(path_item, dict):
            continue
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            for parameter in operation.get("parameters") or []:
                if parameter.get("in") != "query":
                    continue
                _strip_null_from_schema(parameter.get("schema"))


def _strip_null_from_schema(schema: Any) -> None:
    if not isinstance(schema, dict):
        return
    any_of = schema.get("anyOf")
    if not isinstance(any_of, list):
        return
    filtered = [branch for branch in any_of if branch != {"type": "null"}]
    if len(filtered) == len(any_of) or not filtered:
        return
    if "default" in schema and schema["default"] is None:
        del schema["default"]
    if len(filtered) == 1:
        del schema["anyOf"]
        for key, value in filtered[0].items():
            schema.setdefault(key, value)
    else:
        schema["anyOf"] = filtered
