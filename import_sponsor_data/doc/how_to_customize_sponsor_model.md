# Customizing the Sponsor Model import

## Overview

The Sponsor Model importer maps source data (CSV columns + `model_info.json`
values) onto clinical-mdr-api request bodies. The mapping is **not hardcoded in
Python** — it is described in a versioned YAML schema that is the single source
of truth for which fields exist, how they are named on the API, and how their
values are transformed.

To adapt the importer to a different source layout you edit one YAML file (and,
for non-trivial value transformations, register a small Python function). You do
not fork the import script.

This supports both the evolution of the sponsor model across versions and
different implementations of sponsor models across sponsor companies.

> The same schema is intended to become the shared source of truth across the
> OpenStudyBuilder codebases (studybuilder-import, clinical-mdr-api, the
> frontend). Only studybuilder-import reads it today; the `ui` metadata is
> there for the future frontend work.

## Where things live

| Thing | Location |
| --- | --- |
| Schema files (one per library + version) | `datafiles/sponsor_library/sponsormodel/schemas/<library-tag>.v<N>.yaml` (e.g. `sponsor.v1.yaml`) |
| Schema loader / validator, `PropertyType`, `PropertyDefinition` | [importers/utils/sponsor_model_schema.py](../importers/utils/sponsor_model_schema.py) |
| Transformer registry | [importers/utils/sponsor_model_transformers.py](../importers/utils/sponsor_model_transformers.py) |
| Runtime (`FieldMapper`) | [importers/run_import_sponsormodels.py](../importers/run_import_sponsormodels.py) |

The loader turns each YAML entry into a `PropertyDefinition`; `FieldMapper`
consumes those at runtime exactly as before. The YAML is just the input that
used to be hardcoded.

## Schema structure

```yaml
schema_version: 1            # integer, must match the file's vN
library_name: Sponsor        # authoritative library name (the filename tag is cosmetic)

entities:
  sponsor_model:            # built from model_info.json only (no CSV)
    structural: [...]
    extensible: [...]
  dataset:
    structural: [...]
    extensible: [...]
  dataset_variable:
    structural: [...]
    extensible: [...]
```

Each entity has two groups:

- **`structural`** — fields the API requires for routing/persistence. Users may
  **not** remove these. They are either read from a CSV column or *injected*
  from `model_info.json` (see `source` below).
- **`extensible`** — everything else. Users may freely **add, remove and
  reorder** these entries to adapt the importer to their own source data.

### Entry fields

| Field | Meaning |
| --- | --- |
| `api_field` | **(required)** Field name sent to the API. |
| `source_field` | CSV column header to read from. Its **presence** marks the entry as CSV-mapped; the loader emits a `PropertyDefinition` for it. |
| `source` | Set to `injected` for fields supplied from `model_info.json` (e.g. `sponsor_model_name`, `library_name`) rather than the CSV. Injected entries have **no** `source_field` and produce **no** `PropertyDefinition` — they document/validate API requirements only. |
| `type` | Transformation to apply (see below). Required for CSV-mapped entries. |
| `required` | Whether the source column must exist in the CSV. Default `false`. |
| `default` | Value used when the column is missing, or present but the cell is empty. |
| `transformer` | Name resolved against the Python transformer registry. **Required** when `type: custom`. |
| `condition` | Restricts when the entry applies, based on CSV headers (see below). |
| `ui` | Optional frontend rendering hints. **Not read by this importer.** |

### `type` values

These match the `PropertyType` enum:

| `type` | Behavior |
| --- | --- |
| `string` | String field; empty string → `None`. |
| `boolean` | `Y`/`X`/`True`/`true`/`1`/`Yes` → `True`, anything else → `False`. |
| `reverse_boolean` | Parse as boolean, then invert. |
| `integer` | Convert to `int` (non-numeric → `None`). |
| `list_space_separated` | Split the string on spaces. |
| `list_comma_separated` | Split on commas, stripping whitespace. |
| `custom` | Use the named `transformer` from the registry. |

### `condition`

Used for **mutually-exclusive** derivations (e.g. `is_cdisc_std`):

```yaml
condition: { header_present: isnotcdiscstd }   # apply only if the column exists
condition: { header_absent:  isnotcdiscstd }   # apply only if it does NOT exist
```

### `ui` block

Hints for the future studybuilder frontend (ignored by the importer):

```yaml
ui: { column_title: sponsor_model.dataset.label, default_visible: true, order: 10 }
```

- `column_title` — i18n key for the column header
- `default_visible` — whether the column is shown by default
- `order` — left-to-right column position

### Duplicate `api_field` rule

Two entries may share an `api_field` **only** when each carries a mutually
exclusive `condition` (this is how `is_cdisc_std` is derived from different
columns depending on the CSV layout). The loader rejects any other duplicate.

## Versioning

The schema is versioned **independently** of Sponsor Model versions, and each
version is **immutable**: any change to the shape or semantics of a schema must
go into a **new file with the next integer** — never edit a released version.

- Each schema lives in `<library-tag>.v<N>.yaml` (e.g. `sponsor.v1.yaml`) and
  declares its own `schema_version: <N>` and `library_name`. A schema is
  identified by its **content** (`library_name` + `schema_version`), not its
  filename: the tag is only a maintainer-friendly label (e.g. a library named
  "Interventional - Core" may live in `interventional_core.v1.yaml`). Only the
  `.v<N>` suffix is enforced — it must match the declared `schema_version`.
- Each Sponsor Model declares which version it follows via `schema_version` in
  its `model_info.json`. **If absent, it defaults to `1`.** Its `library_name`
  (default `Sponsor`) selects the matching schema.
- At startup the importer loads and validates the default schema (fail-fast),
  and logs the library + schema version used for each model.
- During import, every schema file in the directory is POSTed to the API
  (`/standards/sponsor-models/schema`) as `{library_name, schema_version, schema}`
  where `schema` is the raw YAML text — so the API holds the source of truth.

```json
{
    "ig_uid": "SDTMIG",
    "ig_version_number": "3.3",
    "sponsor_model_version_number": "1",
    "sponsor_model_name": "sdtmig_mastermodel_3.3_NN01",
    "library_name": "Sponsor",
    "schema_version": 2
}
```

### Current versions

| Version | Matches | Notes |
| --- | --- | --- |
| `v1` | SDTMIG 3.2 master model | Base header set. |
| `v2` | SDTMIG 3.3 master model | Adds `subclass`, `source_ig` and conditional `is_cdisc_std` on `dataset`; `origin_type`, `origin_source` and conditional `is_cdisc_std` on `dataset_variable`. |

The per-version change details are kept as a comment at the top of the relevant
schema file (e.g. the v1 → v2 changelog in `sponsor.v2.yaml`).

## How to customize

### Add, remove or reorder a field

Edit the `extensible` list of the relevant entity. For example, to add a new
column `RawComment` that should be sent as a string `raw_comment`:

```yaml
- api_field: raw_comment
  source_field: RawComment
  type: string
  ui: { column_title: sponsor_model.dataset.raw_comment, default_visible: false, order: 300 }
```

`structural` entries cannot be removed — the loader fails validation if a
required field is missing.

### Add a field that needs no transformation (dynamic fields)

You don't have to declare every column. Any CSV column **not** present in the
schema is automatically:

- **Sanitized**: lowercased, spaces/hyphens → underscores
- **Null-handled**: empty string → `None`
- **Passed through**: sent to the API as-is

So adding `custom-sponsor-flag` to a CSV results in
`{"custom_sponsor_flag": "..."}` with no schema change. Declaring it explicitly
(as a `string`) is equivalent, but gives you control over the API field name and
a place to attach `ui` metadata — prefer declaring it once the column is stable.

> Make sure the API accepts the resulting body. OpenStudyBuilder's reference
> implementation handles declared fields specifically and stores dynamic fields
> "as-is" with no business rules applied.

### Custom value transformations

For anything beyond the built-in `type`s, write a transformer and reference it
by name. A transformer is a callable `(value, parser) -> Any`:

- `value` — the raw CSV cell
- `parser` — the importer instance, exposing helpers (`parse_dataset_class_name`,
  …) and the current row via `parser.row_context` (a `{header: cell}` dict)

```python
# importers/utils/sponsor_model_transformers.py  (or your own module)
from importers.utils.sponsor_model_transformers import register_transformer

def my_upper(value, parser):
    return value.upper() if value else None

register_transformer("my_upper", my_upper)
```

```yaml
- api_field: my_field
  source_field: MyColumn
  type: custom
  transformer: my_upper
```

To read another column of the same row (as the built-in `dataset_class_with_table`
transformer does), use `parser.row_context.get("OtherColumn")`. The loader
validates at startup that every `transformer` name used in the YAML resolves to
a registered function, so a typo fails fast.

### Create a new schema version

1. Copy the latest `<library-tag>.v<N>.yaml` (e.g. `sponsor.v2.yaml`) to
   `<library-tag>.v<N+1>.yaml`.
2. Bump `schema_version` inside the new file to `N+1` (keep `library_name`).
3. Make your changes and record them in a short changelog comment at the top.
4. Point the relevant `model_info.json` files at the new version.

To support a different library, add files under its own tag (e.g.
`acme.v1.yaml` with `library_name: Acme`) and set `library_name` accordingly in
the models' `model_info.json`.

### Point a model at a version

Set `"schema_version": <N>` in that model's `model_info.json`. Omit it to use
version 1.

## Validation (fail-fast)

When a schema version is loaded, the loader rejects it with a clear error if:

- `schema_version` is missing, not an integer, or doesn't match the file's `vN`
- `library_name` is missing or empty
- two files declare the same `library_name` + `schema_version`
- any required `structural` field for an entity is missing
- an entry has neither `source_field` nor `source: injected`
- a CSV-mapped entry has an invalid `type`
- a `custom` entry has no `transformer`, or names one that isn't registered
- a non-`custom` entry sets a `transformer`
- a `condition` is malformed
- an `api_field` is duplicated within an entity without mutually-exclusive
  `condition`s

## Quick reference: common entry shapes

```yaml
# Required string read from a CSV column
- { api_field: dataset_uid, source_field: Table, type: string, required: true }

# Optional integer with a default when missing/empty
- { api_field: enrich_build_order, source_field: enrich_build_order, type: integer, default: 0 }

# Space-separated list:  "a b c" -> ["a", "b", "c"]
- { api_field: keys, source_field: Keys, type: list_space_separated }

# Custom transformation via the registry
- { api_field: implemented_dataset_class, source_field: Class, type: custom, transformer: dataset_class_with_table }

# Mutually-exclusive derivation of one api_field from different columns
- { api_field: is_cdisc_std, source_field: isnotcdiscstd, type: reverse_boolean, condition: { header_present: isnotcdiscstd } }
- { api_field: is_cdisc_std, source_field: basic_std,     type: boolean,         condition: { header_absent:  isnotcdiscstd } }

# Injected from model_info.json (no CSV column, no transformation)
- { api_field: sponsor_model_name, source: injected }
```
