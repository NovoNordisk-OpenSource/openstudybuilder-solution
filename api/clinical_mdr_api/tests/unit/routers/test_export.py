"""Unit tests for ``clinical_mdr_api.routers.export``.

Focused on the ``variants`` feature of the ``allow_exports`` decorator,
which selects an alternate header set based on a query-string flag while
leaving the legacy declaration shape untouched.
"""

import pytest

from clinical_mdr_api.routers import export as export_module
from clinical_mdr_api.routers.export import (
    _query_param_is_truthy,
    _resolve_export_definition,
    allow_exports,
)


class _FakeRequest:
    """Minimal stand-in for ``starlette.requests.Request`` used by the decorator.

    Only the two surfaces the decorator actually reads are needed:
    ``headers`` (for the Accept negotiation) and ``query_params`` (for
    variant selection).
    """

    def __init__(
        self, accept: str | None = None, query_params: dict[str, str] | None = None
    ):
        self.headers = {"accept": accept} if accept is not None else {}
        self.query_params = query_params or {}


# ---------------------------------------------------------------------------
# _query_param_is_truthy
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", ["true", "TRUE", "True", "1", "yes", "YES", "on"])
def test_query_param_is_truthy_recognises_truthy_values(value):
    assert _query_param_is_truthy(_FakeRequest(query_params={"flag": value}), "flag")


@pytest.mark.parametrize("value", ["false", "0", "no", "off", "", "anything"])
def test_query_param_is_truthy_rejects_falsy_or_unknown_values(value):
    assert not _query_param_is_truthy(
        _FakeRequest(query_params={"flag": value}), "flag"
    )


def test_query_param_is_truthy_handles_missing_param():
    assert not _query_param_is_truthy(_FakeRequest(query_params={}), "flag")


def test_query_param_is_truthy_handles_no_request():
    assert not _query_param_is_truthy(None, "flag")


# ---------------------------------------------------------------------------
# _resolve_export_definition
# ---------------------------------------------------------------------------


def test_resolve_returns_original_dict_when_no_variants_declared():
    definition = {"defaults": ["a", "b"], "formats": ["text/csv"]}
    resolved = _resolve_export_definition(definition, _FakeRequest())
    assert resolved is definition


def test_resolve_drops_variants_key_when_no_variant_matches():
    definition = {
        "defaults": ["a", "b"],
        "formats": ["text/csv"],
        "variants": {"is_nsv": {"defaults": ["a", "nsv"]}},
    }
    resolved = _resolve_export_definition(
        definition, _FakeRequest(query_params={"is_nsv": "false"})
    )
    assert resolved == {"defaults": ["a", "b"], "formats": ["text/csv"]}
    assert "variants" not in resolved


def test_resolve_merges_matching_variant_over_base_definition():
    definition = {
        "defaults": ["a", "b"],
        "formats": ["text/csv"],
        "variants": {"is_nsv": {"defaults": ["a", "b", "nsv.code"]}},
    }
    resolved = _resolve_export_definition(
        definition, _FakeRequest(query_params={"is_nsv": "true"})
    )
    assert resolved["defaults"] == ["a", "b", "nsv.code"]
    assert resolved["formats"] == ["text/csv"]
    assert "variants" not in resolved


def test_resolve_variant_can_override_format_specific_headers():
    definition = {
        "defaults": ["a"],
        "text/csv": ["a", "extra"],
        "variants": {"is_nsv": {"text/csv": ["a", "nsv-csv-col"]}},
    }
    resolved = _resolve_export_definition(
        definition, _FakeRequest(query_params={"is_nsv": "1"})
    )
    assert resolved["text/csv"] == ["a", "nsv-csv-col"]
    # Untouched keys carry through from the base definition.
    assert resolved["defaults"] == ["a"]


def test_resolve_takes_first_matching_variant_in_declaration_order():
    definition = {
        "defaults": ["base"],
        "variants": {
            "flag_a": {"defaults": ["from-a"]},
            "flag_b": {"defaults": ["from-b"]},
        },
    }
    resolved = _resolve_export_definition(
        definition,
        _FakeRequest(query_params={"flag_a": "true", "flag_b": "true"}),
    )
    assert resolved["defaults"] == ["from-a"]


# ---------------------------------------------------------------------------
# allow_exports decorator integration
# ---------------------------------------------------------------------------

# Test functions intentionally take fixtures by their declared name; that's the
# standard pytest pattern and triggers redefined-outer-name across the file.
# pylint: disable=redefined-outer-name


@pytest.fixture
def captured_export(monkeypatch):
    """Patch ``export()`` so we can assert what the decorator passes to it."""

    captured = {}

    # *args/**kwargs swallow the real export() signature; we only inspect the
    # first three positional args.
    # pylint: disable=unused-argument
    def fake_export(export_format, data, export_definition, *args, **kwargs):
        captured["export_format"] = export_format
        captured["data"] = data
        captured["export_definition"] = export_definition
        return "exported"

    monkeypatch.setattr(export_module, "export", fake_export)
    return captured


def _decorated_endpoint(definition):
    @allow_exports(definition)
    # `request` is unused inside the body but must be declared so the decorator
    # can find it via kwargs lookup.
    # pylint: disable=unused-argument
    def endpoint(request):
        return [{"a": 1, "b": 2, "nsv": {"code": "X"}}]

    return endpoint


def test_allow_exports_uses_base_defaults_when_no_variant_flag_set(captured_export):
    definition = {
        "defaults": ["a"],
        "formats": ["text/csv"],
        "variants": {"is_nsv": {"defaults": ["a", "nsv.code"]}},
    }
    endpoint = _decorated_endpoint(definition)

    result = endpoint(request=_FakeRequest(accept="text/csv", query_params={}))

    assert result == "exported"
    assert captured_export["export_format"] == "text/csv"
    assert captured_export["export_definition"]["defaults"] == ["a"]
    assert "variants" not in captured_export["export_definition"]


def test_allow_exports_uses_variant_defaults_when_flag_truthy(captured_export):
    definition = {
        "defaults": ["a"],
        "formats": ["text/csv"],
        "variants": {"is_nsv": {"defaults": ["a", "nsv.code"]}},
    }
    endpoint = _decorated_endpoint(definition)

    endpoint(request=_FakeRequest(accept="text/csv", query_params={"is_nsv": "true"}))

    assert captured_export["export_definition"]["defaults"] == ["a", "nsv.code"]


def test_allow_exports_skips_export_when_accept_does_not_match(captured_export):
    definition = {
        "defaults": ["a"],
        "formats": ["text/csv"],
        "variants": {"is_nsv": {"defaults": ["a", "nsv.code"]}},
    }
    endpoint = _decorated_endpoint(definition)

    # The endpoint's raw payload is returned untouched and ``export`` is not called.
    result = endpoint(
        request=_FakeRequest(accept="application/json", query_params={"is_nsv": "true"})
    )

    assert result == [{"a": 1, "b": 2, "nsv": {"code": "X"}}]
    assert captured_export == {}


def test_allow_exports_does_not_mutate_decorator_definition(captured_export):
    """The closed-over definition must remain pristine across calls.

    Earlier versions extended ``definition["formats"]`` in place, causing
    the list to grow on every request. The fix uses a fresh copy.
    """
    definition = {"defaults": ["a"], "formats": ["text/csv"]}
    original_formats = list(definition["formats"])
    endpoint = _decorated_endpoint(definition)

    for _ in range(3):
        endpoint(request=_FakeRequest(accept="text/csv"))

    assert definition["formats"] == original_formats
    # Sanity-check the fixture's patch was actually invoked, so we know
    # `definition` was passed through the decorator (not short-circuited).
    assert captured_export["export_format"] == "text/csv"


def test_allow_exports_preserves_legacy_definition_shape(captured_export):
    """Definitions without a ``variants`` key must work exactly as before."""
    definition = {"defaults": ["a", "b"], "formats": ["text/csv"]}
    endpoint = _decorated_endpoint(definition)

    endpoint(request=_FakeRequest(accept="text/csv"))

    assert captured_export["export_definition"] is definition
