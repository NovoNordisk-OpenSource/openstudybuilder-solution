# Architecture

## Three-Layer DDD Architecture

The codebase strictly follows DDD with a three-layer responsibility segregation:

### 1. Domain Layer (`clinical_mdr_api/domains/`)
- Contains all business logic
- Aggregate roots are the central concept
- Independent of all other layers (no external dependencies)
- Each aggregate typically has its own subdirectory

### 2. Repository Layer (`clinical_mdr_api/domain_repositories/`)
- Responsible for persistence and restoration of aggregates to/from Neo4j
- Handles concurrency control and transaction semantics
- Only depends on the domain layer (specifically the aggregate it persists)
- Uses Memento pattern for state transformation between domain objects and database

### 3. Service Layer (`clinical_mdr_api/`)
- **Routers** (`routers/`) - Define FastAPI routes
- **Services** (`services/`) - Convert API requests to repository/domain calls and results to responses
- **Models** (`models/`) - Pydantic models for request/response validation
- Only services depend on repositories; routers depend on services

**Exceptions are NOT part of this layer and do not live under `clinical_mdr_api/`.** They are shared across all three apps and are defined in `common/exceptions.py` — import them with `from common.exceptions import NotFoundException, ...`. There is no `clinical_mdr_api/exceptions/` module; never create one. See `api-conventions.md` for the full exception-to-status-code table.

**Key Principle**: Layers communicate through public interfaces. Names without leading underscores are public API. This enables loose coupling and independent evolution of each layer.

## Packages outside the three layers

`clinical_mdr_api/` contains several packages the three-layer model does not describe. Do not assume a package belongs to a layer because its name resembles one.

### `repositories/` — NOT the repository layer

**This is a second, non-DDD persistence package, distinct from `domain_repositories/`.** Confusing the two is the most likely architectural mistake in this codebase.

- `repositories/libraries.py`, `ct_catalogues.py`, `ct_packages.py`, `system.py` hold plain functions issuing raw Cypher via `neomodel.db.cypher_query`. They return dicts and lists, not aggregates, and there is no Memento round-trip or optimistic locking. Services call them **directly**, bypassing the domain layer entirely — see `services/controlled_terminologies/ct_catalogue.py` and `services/system.py`.
- `repositories/_utils.py` is shared query infrastructure: `CypherQueryBuilder`, `FilterOperator`, `FilterDict`, `ComparisonOperator`, wildcard/sort/version filter helpers. **Routers import `FilterOperator` from here directly** (see `routers/syntax_instances/*.py` and `routers/studies/*.py`). That is established convention, not a layering violation — do not "fix" it.

So there are two persistence paths. Aggregate-backed reads and all writes go through `domain_repositories/`; some read-only and reporting queries go through `repositories/`. When adding a query, follow whichever path the neighbouring code uses rather than converting one to the other.

### The remaining packages

- **`listings/`** (`query_service.py`) - Direct-Cypher listing and reporting queries, built on `repositories/_utils`. Also outside the DDD path.
- **`utils/`** - Top-level helpers (`db_result_to_list`, `snake_to_camel`, `camel_to_snake`, …) plus `api_version.py`, `db_integrity_checks.py`, `neomodel_schema.py`. Imported as `from clinical_mdr_api import utils`. Distinct from `tests/utils/`.
- **`descriptions/`** (`general.py`) - Shared OpenAPI description constants such as `CHANGES_FIELD_DESC`, imported by ~46 modules. Reuse these rather than retyping description strings in a router.
- **`hooks/`** (`schemathesis_hooks.py`) - Hooks for the Schemathesis contract tests.
- **`developer_tools/`** (`networksimulator.py`) - Local developer utility; not part of the served application.

## Development Workflow for New Features

Follow this order when implementing features:

1. **Domain layer first** - Design and test business logic (can be done independently)
2. **Repository layer** - Implement persistence (depends only on domain layer)
3. **Service layer** - Wire up API endpoints (depends on repositories)

This inside-out approach allows incremental development with testing at each layer.
