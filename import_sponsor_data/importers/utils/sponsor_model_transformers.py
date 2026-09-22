"""
Transformer registry for the Sponsor Model field schema.

The YAML schema (``<library-tag>.v*.yaml``) never embeds Python. Entries
of ``type: custom`` instead reference a transformer *by name*; that name is
resolved here to an actual callable.

A transformer is a callable ``(value, parser) -> Any``:

    value   the raw CSV cell (a string)
    parser  the ``SponsorModels`` importer instance, exposing helper methods
            (``parse_dataset_class_name``, ``parse_variable_class_name``, ...)
            and the current row via ``parser.row_context`` (a ``{header: cell}``
            dict for the row being processed).

Registering your own transformer
--------------------------------
Downstream users adapting the importer to their own source data add a callable
and reference it from the YAML - no fork of the importer required::

    from importers.utils.sponsor_model_transformers import register_transformer

    def my_upper(value, parser):
        return value.upper() if value else None

    register_transformer("my_upper", my_upper)

Then in ``<library-tag>.v*.yaml`` (e.g. ``sponsor.v1.yaml``)::

    - api_field: my_field
      source_field: MyColumn
      type: custom
      transformer: my_upper

The schema loader validates at startup that every ``transformer`` name used in
the YAML resolves here, so a typo fails fast rather than at import time.
"""

from typing import Any, Callable

# A transformer receives the raw cell value and the importer (parser) instance.
Transformer = Callable[[Any, Any], Any]

_REGISTRY: dict[str, Transformer] = {}


def register_transformer(
    name: str, func: Transformer, *, overwrite: bool = False
) -> None:
    """Register ``func`` under ``name``. Refuses to clobber unless ``overwrite``."""
    if not overwrite and name in _REGISTRY:
        raise ValueError(
            f"Transformer '{name}' is already registered "
            f"(pass overwrite=True to replace it)"
        )
    _REGISTRY[name] = func


def is_registered(name: str) -> bool:
    """Whether a transformer with this name exists (used by schema validation)."""
    return name in _REGISTRY


def get_transformer(name: str) -> Transformer:
    """Resolve a transformer by name, or raise a clear error listing known names."""
    try:
        return _REGISTRY[name]
    except KeyError:
        raise KeyError(
            f"Transformer '{name}' is not registered. "
            f"Known transformers: {sorted(_REGISTRY)}"
        ) from None


# ---------------------------------------------------------------------------
# Built-in transformers
# ---------------------------------------------------------------------------
# Translated verbatim from the original hardcoded PropertyDefinition lists in
# run_import_sponsormodels.py. The three entries below cover the two underlying
# parser methods wired in three distinct ways.


def _dataset_class_with_table(value: Any, parser: Any) -> Any:
    """dataset ``Class`` -> uses the row's ``Table`` column as the dataset name."""
    return parser.parse_dataset_class_name(value, parser.row_context.get("Table", None))


def _dataset_class(value: Any, parser: Any) -> Any:
    """dataset_variable ``class_table`` -> parsed with no dataset-name context."""
    return parser.parse_dataset_class_name(class_name=value)


def _variable_class(value: Any, parser: Any) -> Any:
    """dataset_variable ``class_column``."""
    return parser.parse_variable_class_name(value)


register_transformer("dataset_class_with_table", _dataset_class_with_table)
register_transformer("dataset_class", _dataset_class)
register_transformer("variable_class", _variable_class)
