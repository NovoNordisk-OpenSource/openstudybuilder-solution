# Project Overview

OpenStudyBuilder API - A FastAPI-based REST API providing read/write access to clinical metadata stored in a Neo4j database. The codebase follows Domain-Driven Design (DDD) principles and uses Python 3.14.

## Multi-API Structure

The repository contains three separate APIs:

- **Main API** (`clinical_mdr_api/`) - Port 8000 - Primary API for clinical metadata
- **Consumer API** (`consumer_api/`) - Port 8008 - Consumer-facing API endpoints. Read-heavy, but **not read-only** — it exposes write endpoints too (e.g. `POST /studies` and `POST /studies/{uid}/soa`, both guarded by `rbac.STUDY_WRITE`). Do not infer its constraints from an HTTP verb. Its consumers are external, so a change to an existing response reaches them as soon as it ships. Backward compatibility is therefore a strong default — but it is not a hard rule: breaking changes are permitted, provided they are reported to the user rather than shipped silently. Cutting a new API version is one way to avoid a break, not a required consequence of one. Only `v1` is currently mounted; `v2` exists but is entirely commented out.
- **Extensions API** (`extensions/`) - Port 8009 - Extension/plugin system

**Common code** is shared via the `common/` directory (config, auth, database, telemetry, exceptions).
