# Project Overview

OpenStudyBuilder API - A FastAPI-based REST API providing read/write access to clinical metadata stored in a Neo4j database. The codebase follows Domain-Driven Design (DDD) principles and uses Python 3.14.

## Multi-API Structure

The repository contains four separate APIs:

- **Main API** (`clinical_mdr_api/`) - Port 8000 - Primary API for clinical metadata
- **Consumer API** (`consumer_api/`) - Port 8008 - Consumer-facing API endpoints. Read-heavy, but **not read-only** — it exposes write endpoints too (e.g. `POST /studies` and `POST /studies/{uid}/soa`, both guarded by `rbac.STUDY_WRITE`). Do not infer its constraints from an HTTP verb. Its consumers are external, so a change to an existing response reaches them as soon as it ships. Backward compatibility is therefore a strong default — but it is not a hard rule: breaking changes are permitted, provided they are reported to the user rather than shipped silently. Cutting a new API version is one way to avoid a break, not a required consequence of one. Only `v1` is currently mounted; `v2` exists but is entirely commented out.
- **Extensions API** (`extensions/`) - Port 8009 - Extension/plugin system
- **Standards Import API** (`standards_import/`) - Port 8010 - Ingests CDISC controlled terminology packages

**Common code** is shared via the `common/` directory (config, auth, database, telemetry, exceptions).

The Standards Import API is the exception to two rules that hold everywhere else:

- it uses a **second database**. neomodel stays bound to the MDR database (`NEO4J_DSN`); the CDISC staging database is reached with the raw Neo4j driver (`STANDARDS_IMPORT_STAGING_DSN`), because its model is bespoke and query-shaped rather than object-shaped. Staging and MDR share one Neo4j instance, kept apart by the `:CDISCStaging` marker label on every staging node and by Neo4j RBAC roles (`mdr`/`staging`) provisioned by `db/init_neo4j.py`.
- it writes CDISC content **around** the domain aggregates, which reject creation in the non-editable `CDISC` library and stamp `start_date` with the server clock. Those guards are what make it a separately deployed app with its own `Library.Import` role rather than a router in the main API.

**The `standards_import` package stays a separate top-level module tree** — intentionally, even though its routers are now also served by the main app on port 8000 under `/standards-import` (when `STANDARDS_IMPORT_ENABLED=true`). Two enforcement tools depend on this:
- the **import-linter** contracts verified by `pipenv run lint-imports`: `standards_import` must not import `clinical_mdr_api`, and `clinical_mdr_api` must not *directly* import `standards_import.repositories/.services/.domain` (only `.routers` is the intended public mount point — transitive imports through the routers are expected);
- the **sblint** Cypher linter (`api/sblint/linters/no_staging_label_without_cdisc_staging_marker.py`) that flags a staging label in a Cypher write without `:CDISCStaging` alongside it.

Collapsing the namespace would break both. The router-mounting code in `clinical_mdr_api/main.py` imports from `standards_import.routers.*` directly — never from `standards_import.main`, which calls `configure_database()` at module level and must not be imported in the same process as `clinical_mdr_api.main`.

**The `:CDISCStaging` marker label** is placed on every node the staging side writes (e.g. `CREATE (p:RawPackage:CDISCStaging {...})`). `mdr_repository.py` must never create nodes with this label — a comment in its module docstring enforces this by convention, and the `verifications/` drift check (`test_db_staging_isolation.py`) enforces it against a live database. The `mdr` Neo4j role has a DENY on `:CDISCStaging` nodes; the `staging` role is an allowlist. These are **defence in depth**: nothing in either app may rely on the DENY being active (Community edition, or roles not yet provisioned). Correctness comes from the marker label always being set (static guarantees), not from the DENY always being live (runtime guard).
