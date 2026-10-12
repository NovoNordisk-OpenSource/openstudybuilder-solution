# Neo4j Database

- **ORM**: Uses `neomodel` for object-graph mapping
- **Connection**: Configured via `NEO4J_DSN` environment variable (format: `bolt://user:password@host:port/database`)
- **Setup**: Tests require local Neo4j instance (use docker image from `neo4j-mdr-db` repository)
- **Configuration**: Database is configured in `clinical_mdr_api/main.py` on startup via `common.database.configure_database()`

## Special Considerations

- **Versioning**: Domain objects use versioning (see `clinical_mdr_api/domains/versioned_object_aggregate.py`)
- **Concurrency**: Repository layer handles optimistic locking (see tests in `clinical_mdr_api/tests/integration/repositories/concurrency/`)
- **Pagination**: Default page size is 10, max is 1000 (configurable via env vars)

## Versioning Graph Model

Each versioned entity has a `Root` node connected to one or more `Value` nodes via:

- **`HAS_VERSION`** relationships — carry `version`, `status`, `start_date`, `end_date` as rel properties. An open `HAS_VERSION` has `end_date IS NULL`.
- **Pointer relationships**: `LATEST`, `LATEST_DRAFT`, `LATEST_FINAL`, `LATEST_RETIRED`.

### Semantics of the `LATEST_{STATUS}` pointers

**`LATEST_DRAFT` / `LATEST_FINAL` / `LATEST_RETIRED` are historical pointers, not current-status flags.** Each one points to the latest value node that was ever in that status — regardless of the object's current status.

- **They may coexist on the same Root, and may point to the same value node.** Example: an object is approved (Final v1.0), put back to Draft (v1.1 on a new value node), then approved again with no changes (v2.0 reuses the Draft's value node). `LATEST_DRAFT` and `LATEST_FINAL` both legitimately point to that same value node.
- **Do NOT delete `LATEST_DRAFT` when creating `LATEST_FINAL`** (or vice versa). Both are correct and should exist.
- The object's *current* status is derived from the open `HAS_VERSION` (the one with `end_date IS NULL`), not from which `LATEST_{STATUS}` pointer exists.

Misreading these pointers as mutually exclusive "current status" markers has caused real regressions — any change that removes one `LATEST_{STATUS}` pointer when another is set is almost certainly wrong.

### Resolving through `LATEST_FINAL` makes unapproved look absent

Lookups that match through `LATEST_FINAL` cannot see a never-approved entity, and typically report it as missing rather than as draft. `CTCodelistGenericRepository.get_codelist_uid_by_submission_value` is the case to know: a codelist that exists but was never approved resolves to `None`, and the caller raises `"The codelist identified by submission value ... was not found"` — so the codelist sits plainly visible in the Library UI while the API insists it does not exist. That reads as an API bug and is not one. When writing a resolver, decide deliberately whether "draft" should surface as a distinct error rather than falling into the not-found path. See `import_sponsor_data/SYSTEM_CODELISTS.md` for the failure modes this produces downstream.
