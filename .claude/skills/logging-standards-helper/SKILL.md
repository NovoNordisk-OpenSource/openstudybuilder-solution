---
name: logging-standards-helper
user-invocable: false
description: "Internal shared helper — do NOT invoke directly; it is attached automatically to the agents that need it. Defines the OpenStudyBuilder API logging standards those agents apply: where logging belongs in each DDD layer, how to choose a log level, what must never be written to a log, and the review checklist for logging in changed code."
---

# Logging Standards Helper

> **This skill is a shared helper; it is not meant to be invoked directly.** It is attached to the agents that need it through their `skills:` frontmatter and loads automatically whenever one of them runs — there is nothing to invoke from the slash-command menu.

**Path convention:** all paths in this file are relative to `api/`, because these standards apply only there. From the repo root, prefix them — `api/common/logger.py`, `api/clinical_mdr_api/domains/`, and so on. The DDD layer headings below are layer names first and paths second; read them as `api/clinical_mdr_api/<layer>/`.

## When to use

- You are one of the agents this skill is attached to (`code-reviewer-api`, `endpoint-implementation-specialist`, `backend-refactoring-assistant`, `code-improvement-advisor`) and you are writing, reviewing, or refactoring Python code in `api/`. Apply these standards to the code in front of you as part of that task.

## When NOT to use

- **Do not invoke this skill directly from the slash-command menu.** It has no task of its own and produces no user-facing output — it shapes how the agents above treat logging within their own work. To get a code review that covers logging, run `/osb-review-api`.
- Do not apply it outside `api/`. These standards describe this FastAPI application's `common/logger.py` setup and its DDD layering; they do not carry over to `frontend/` or the standalone Python components.
- Do not audit logging across files the surrounding task has not put in scope. When a parent skill has bounded the work to a set of changed files, stay inside that set.
- Do not copy these rules into another skill or agent prompt. Attach this skill via `skills:` instead, so all consumers stay in sync.

## Project logging context

- Standard `logging`, configured by `LOGGING_CONFIG` in `common/logger.py`. Each module declares `log = logging.getLogger(__name__)` at module level.
- DEBUG output appears only when `settings.app_debug` is on (`APP_DEBUG`, `common/config.py`); otherwise the root level is INFO.
- Unhandled and `MDRApiBaseException` errors reach the exception handlers in `clinical_mdr_api/main.py`, which call `common/logger.py::log_exception()`. It logs an ERROR line (status, exception class, method, URL, message) followed by the full traceback (`exc_info=True`).
- HTTP requests are covered by the tracing middleware (OpenCensus) and request metrics.

**Consequence: never log-and-reraise.** If an exception propagates, `log_exception()` already records it with its traceback. A `log.error(...)` followed by a bare `raise` logs the same failure twice. Log only an exception you catch and *handle* — fallback, retry, swallow — and then use `log.warning(..., exc_info=True)` or `log.exception(...)`.

## Where logging belongs, per layer

| Layer | Log | Don't log |
|---|---|---|
| `routers/` | Only router-specific logic the middleware cannot see | Requests, responses, errors — middleware and `log_exception()` cover them |
| `services/` | Business events and state transitions (INFO); external service calls (INFO, with timing); fallback paths (WARNING) | Entry/exit of simple methods; exceptions that propagate |
| `domain_repositories/` | Unexpected empty results when data was expected, and concurrency or versioning conflicts (WARNING); batch operations (INFO, with timing) | Every query; failures that propagate as exceptions |
| `domains/` | Rarely — only significant invariant violations (WARNING). Domain code stays pure | Simple validation |

Level choice: DEBUG for diagnostic detail, INFO for normal business events, WARNING for unexpected but handled conditions, ERROR for failures you handle without re-raising.

## Never write to a log

This system holds clinical trial data. Never log:

- Passwords, API keys, bearer tokens, or OAuth credentials
- PII or PHI (personal or health information), including whole request bodies that may contain them

Log UIDs and identifiers instead, and mask anything personal that must appear (`email='u***@example.com'`).

## Review checklist

For each changed `api/` file:

1. `log = logging.getLogger(__name__)` at module level, if the file logs at all.
2. Lazy `%s` formatting: `log.info("uid=%s", uid)`, not an f-string.
3. Messages carry the identifiers needed to find the record (UIDs, names).
4. The level matches the table above.
5. No log-and-reraise.
6. Nothing from **Never write to a log**.
7. No logging inside tight loops above DEBUG.

When reporting, cite `file:line`, name the checklist item, and give the corrected line.
