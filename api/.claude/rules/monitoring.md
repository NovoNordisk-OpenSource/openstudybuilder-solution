# Telemetry & Monitoring

This file covers the telemetry **infrastructure**. For log level selection, per-layer logging conventions, and what must never be logged, see `.claude/skills/logging-standards-helper/SKILL.md` — do not duplicate that guidance here.

## Logging

- Get a logger with `log = logging.getLogger(__name__)`. There is no custom factory.
- Format calls lazily — `log.info("cloned study %s", uid)`, never an f-string. `LogInjectionGuardFilter` (`common/logger.py`) strips CR/LF from `record.args` to block log injection (CWE-117), and it only sees values passed as args. It deliberately does not touch the format string, so a value folded into the message directly is unprotected — wrap those in `sanitize_for_log()` from `common/utils.py`.
- The filter is attached to the `console` handler in `LOGGING_CONFIG`, applied once via `default_logging_config()` at startup. A handler configured outside that config bypasses the guard.
- **Nothing redacts secrets or PII.** CR/LF stripping is the only enforced rule; "never log tokens/PII/PHI" is convention, checked by review, with no runtime safety net.
- Log level is derived from `APP_DEBUG` (DEBUG when set, otherwise INFO). There is no `LOG_LEVEL` setting. `neo4j.notifications` is pinned to ERROR and `neo4j.io` to INFO to silence driver noise.
- `log_exception()` in `common/logger.py` is the shared handler-side reporter: ERROR for the message, INFO for the traceback, and a reproducing `curl` at DEBUG when `APP_DEBUG` is on.

## What is instrumented automatically — do not re-implement

- **HTTP access logs and unhandled exceptions** are emitted by `TracingMiddleware` and `ExceptionTracebackMiddleware`. Routers contain zero `log.*` calls, and new ones should not add any.
- **Every Cypher query** is traced and measured once `patch_neomodel_database()` monkey-patches neomodel at startup. Never hand-roll query timing or logging.
- **Repository methods** commonly carry `@trace_calls` from `common.telemetry` (~38 files) to get a span for free. Match the neighbouring code rather than adding manual spans.

## Tracing (OpenCensus)

OpenCensus, not OpenTelemetry — there are no `opentelemetry` imports anywhere in `api/`.

`TRACING_ENABLED` gates the whole subsystem: it controls both the middleware and the neomodel patch. With it off, none of the above instrumentation exists.

Exporter selection happens in `clinical_mdr_api/main.py`, not in the middleware:

1. `APPLICATIONINSIGHTS_CONNECTION_STRING` set → `AzureExporter`
2. else `ZIPKIN_HOST` set → `ZipkinExporter` (`opencensus-ext-zipkin` is a dev-only dependency)
3. else → `PrintExporter` (console)

The sampler is always `AlwaysOnSampler` — every request is traced, with no sampling-rate setting. `*/system/healthcheck` is excluded.

## `common/telemetry/` modules

| Module | Role |
|---|---|
| `tracing.py` | `trace_block` (context manager) and `trace_calls` (decorator); re-exported from the package `__init__` |
| `tracing_middleware.py` | Root HTTP span per request, W3C trace-context propagation, access-log line, `traceresponse` header |
| `traceback_middleware.py` | Catches unhandled exceptions, records them on the span, returns the 500 `ErrorResponse` |
| `request_metrics.py` | `RequestMetrics` per request, `cypher_tracing`, and `patch_neomodel_database()`; optional `X-Metrics` response header |
| `custom_azure_log_handler.py` | **Not wired.** Fork-safe `AzureLogHandler` subclass, referenced nowhere. |
| `logging_filter.py` | **Not wired.** `TracingContextFilter` would stamp `trace_id`/`span_id` onto log records, but it is absent from `LOGGING_CONFIG`, so log lines carry no trace IDs today. |

Treat the last two as dead code. Do not describe trace-correlated logging as an existing capability, and check whether wiring one is actually wanted before extending it.

## Config (`common/config.py`)

`TRACING_ENABLED`, `TRACING_METRICS_HEADER`, `TRACE_REQUEST_BODY`, `TRACE_REQUEST_BODY_MIN_STATUS_CODE`, `TRACE_REQUEST_BODY_TRUNCATE_BYTES`, `TRACE_QUERY_MAX_LEN`, `TRACEBACK_MAX_ENTRIES`, `SLOW_QUERY_DURATION`, `APPLICATIONINSIGHTS_CONNECTION_STRING`, `ZIPKIN_HOST` / `_PORT` / `_ENDPOINT` / `_PROTOCOL`, `APP_DEBUG`, `COLOR_LOGS`, `UVICORN_LOG_CONFIG`.

`SLOW_QUERY_DURATION` (default 1s) is the threshold above which the slowest query's text and params are captured into `RequestMetrics`.
