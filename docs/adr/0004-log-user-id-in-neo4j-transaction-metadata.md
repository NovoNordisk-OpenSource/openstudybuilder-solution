# Log user ID in Neo4j transaction metadata

## Status

Accepted

## Context

The APIs connect to Neo4j using a shared database account. Database query logs
and transaction monitoring therefore identify the service account, not the
API user responsible for an operation. Application-level authorship records
do not provide this attribution for every database read or write.

Queries run through neomodel in auto-commit and explicit transactions, in
worker threads, and in background jobs. Adding metadata separately at each
query call site would duplicate infrastructure concerns and risk leaving
some operations unattributed.

## Decision

Attach the current request's user ID as Neo4j transaction metadata at the
shared driver/session boundary, rather than modifying Cypher statements or
issuing a separate metadata-setting query for each operation.

- **Resolve identity from the request context.**
  `common.auth.user.transaction_metadata()` returns `{"user_id": user.id()}`.
  The existing identity rule uses the token's `oid` for an end user, falling
  back to `azp` for a client application. Outside a request, before
  authentication, or without an ID, it returns an empty dictionary. Do not
  attach names, email addresses, roles, or tokens.
- **Use shared database configuration across all three APIs.**
  `configure_app_database()` installs `TxMetadataDriver` for neomodel and
  initializes its connection at startup. The main, Consumer, and Extensions
  APIs use this entry point. The lower-level `configure_database()` keeps
  metadata optional and returns the underlying driver, so non-API callers
  can continue without request attribution.
- **Handle both transaction paths without extra database calls.**
  `TxMetadataSession.run()` wraps string queries in a Neo4j `Query` carrying
  metadata for auto-commit transactions. A caller-supplied `Query` passes
  through unchanged. `begin_transaction()` merges request metadata with
  caller-supplied metadata, with the caller's values taking precedence;
  explicit transaction metadata is fixed when the transaction begins.
  Other driver and session operations delegate to the underlying objects.
- **Propagate context without sharing transactions.**
  `RequestContextThreadPoolExecutor` copies `contextvars` separately for
  each submitted task, carrying authentication, request metrics, the
  OpenCensus tracer, and neomodel's initialized driver/connection state.
  It clears the copied active transaction and session before running the
  task, leaving the submitter's state untouched. Worker tasks must never
  share the calling thread's active transaction. Parallel SoA snapshot
  builders use this executor; snapshot writes remain sequential in the
  calling thread's transaction.
- **Keep background jobs attributable.** FastAPI background jobs run after
  the response is sent but within the request context, so their database
  transactions retain the initiating user's ID.
- **Treat attribution as best-effort observability.** If the metadata
  provider fails, log a warning and execute the database operation without
  request metadata. Attribution must not make an otherwise valid operation
  fail.

The implementation lives in [database configuration](../../api/common/database.py),
[request identity](../../api/common/auth/user.py), and the
[context-aware executor](../../api/common/concurrency.py).

## Consequences

- Neo4j transaction monitoring and query logs, when enabled and configured
  to include metadata, can associate database activity with an API user or
  client application without changing individual repository queries.
- This is diagnostic attribution, not database impersonation, authorization,
  or a replacement for the application's versioning and audit trail. The
  database connection still uses the service account. No graph schema
  migration or API response change is required.
- Queries outside authenticated request context, callers using the plain
  driver, and caller-supplied `Query` objects are not automatically enriched.
  Explicit callers can override metadata, so it is not tamper-proof evidence
  of identity.
- User IDs are linkable identifiers even without names or email addresses.
  Access to database monitoring and logs, and their retention, must reflect
  that sensitivity.
- New threaded database work must use the context-aware executor to retain
  attribution and isolate transaction state. Worker reads do not see the
  caller's uncommitted changes because they run outside its transaction.
- The executor depends on neomodel's internal transaction and session state.
  Unit tests cover context propagation, isolation, and session wrapping;
  integration tests verify metadata in real auto-commit, explicit, worker,
  and background-job transactions. These are compatibility checks when
  upgrading neomodel or the Neo4j driver.
