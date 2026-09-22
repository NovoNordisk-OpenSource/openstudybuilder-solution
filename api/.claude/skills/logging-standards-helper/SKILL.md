---
name: logging-standards-helper
user-invocable: false
description: "Internal shared helper — do NOT invoke directly; it is attached automatically to the agents that need it. Defines the OpenStudyBuilder API logging standards those agents apply: where logging belongs in each DDD layer, how to choose a log level, what must never be written to a log, and the review checklist for logging in changed code."
---

# Logging Standards Helper

> **This skill is a shared helper; it is not meant to be invoked directly.** It is attached to the agents that need it through their `skills:` frontmatter and loads automatically whenever one of them runs — there is nothing to invoke from the slash-command menu.

You are a logging standards specialist for the OpenStudyBuilder API project. Your role is to ensure code has appropriate, secure, and meaningful logging that aids in debugging, monitoring, and operational visibility.

## When to use

- You are one of the agents this skill is attached to (`code-reviewer-api`, `endpoint-implementation-specialist`, `backend-refactoring-assistant`, `code-improvement-advisor`) and you are writing, reviewing, or refactoring Python code in `api/`. Apply these standards to the code in front of you as part of that task.

## When NOT to use

- **Do not invoke this skill directly from the slash-command menu.** It has no task of its own and produces no user-facing output — it shapes how the agents above treat logging within their own work. To get a code review that covers logging, run `/review-api`.
- Do not apply it outside `api/`. These standards describe this FastAPI application's `common/logger.py` setup and its DDD layering; they do not carry over to `frontend/` or the standalone Python components.
- Do not audit logging across files the surrounding task has not put in scope. When a parent skill has bounded the work to a set of changed files, stay inside that set.
- Do not copy these rules into another skill or agent prompt. Attach this skill via `skills:` instead, so all consumers stay in sync.

## Project Logging Context

This FastAPI application uses:
- **Standard Python logging** via `logging` module
- **Structured logging** with custom formatter in `common/logger.py`
- **Log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Logger initialization**: `log = logging.getLogger(__name__)` at module level
- **Telemetry integration**: OpenCensus tracing for distributed tracing

## When to Add Logging

### Repository Layer (`clinical_mdr_api/domain_repositories/`)

**ALWAYS log:**
- Database operations start/completion (INFO level)
- Query failures or exceptions (ERROR level)
- Unexpected empty results when data was expected (WARNING level)
- Concurrency conflicts or versioning issues (WARNING level)
- Complex queries or batch operations (INFO with timing)

**Example:**
```python
import logging

log = logging.getLogger(__name__)

def retrieve_notification(self, sn: int) -> Notification:
    log.info("Retrieving notification with sn=%s", sn)
    rs = db.cypher_query(
        """
        MATCH (n:Notification {sn: $sn})
        RETURN n
        """,
        params={"sn": sn},
        resolve_objects=True,
    )

    if not rs[0]:
        log.warning("Notification with sn=%s not found", sn)

    NotFoundException.raise_if_not(rs[0], "Notification", str(sn), "Serial Number")

    log.debug("Successfully retrieved notification sn=%s", sn)
    return self._transform_to_model(rs[0][0][0])
```

### Service Layer (`clinical_mdr_api/services/`)

**ALWAYS log:**
- Service operation entry/exit for complex operations (INFO/DEBUG)
- Business rule validation failures (WARNING level)
- External service calls (INFO level with timing)
- State transitions or important business events (INFO level)
- Unexpected conditions or fallback logic (WARNING level)

**Example:**
```python
import logging

log = logging.getLogger(__name__)

@db.transaction
def create_notification(
    self,
    notification_input: NotificationPostInput,
) -> Notification:
    log.info("Creating notification: title='%s', type=%s",
             notification_input.title, notification_input.notification_type)

    try:
        result = self.repo.create_notification(
            title=notification_input.title,
            description=notification_input.description,
            notification_type=notification_input.notification_type.value,
            started_at=notification_input.started_at,
            ended_at=notification_input.ended_at,
            published_at=(
                datetime.now(timezone.utc) if notification_input.published else None
            ),
        )
        log.info("Successfully created notification with sn=%s", result.sn)
        return result
    except Exception as e:
        log.error("Failed to create notification: %s", str(e))
        raise
```

### Domain Layer (`clinical_mdr_api/domains/`)

**CAREFULLY log (domain should be pure logic):**
- Only log significant business rule violations or invariant failures (WARNING/ERROR)
- Avoid logging in simple validation methods
- Log complex state changes or aggregate reconstructions (DEBUG)
- Keep domain layer logging minimal to maintain purity

**Example:**
```python
import logging

log = logging.getLogger(__name__)

class StudyDesignAggregate:
    def apply_version_conflict_resolution(self, strategy: str) -> None:
        log.warning("Applying version conflict resolution: strategy=%s, uid=%s",
                    strategy, self.uid)
        # Business logic here
```

### Router Layer (`clinical_mdr_api/routers/`)

**Generally DON'T log here:**
- FastAPI middleware handles request/response logging
- Exception handlers in `common/logger.py` log errors
- Only log if there's router-specific logic not covered by middleware

## Log Level Guidelines

### DEBUG
- Detailed diagnostic information
- Variable values during processing
- Control flow details
- Query parameters or payloads (sanitized)
- Only visible when `APP_DEBUG=true`

### INFO
- Normal operation events
- Important business operations (create, update, delete)
- External service calls
- Significant state changes
- Operation start/completion

### WARNING
- Unexpected but handled conditions
- Deprecated functionality usage
- Missing optional data
- Performance concerns (slow queries)
- Validation failures
- Recoverable errors

### ERROR
- Operation failures requiring attention
- Unhandled exceptions
- Data integrity issues
- External service failures
- Critical business rule violations

### CRITICAL
- System-level failures
- Data corruption detected
- Security breaches
- Service unavailability

## Security Considerations

**NEVER log:**
- Passwords or API keys
- Bearer tokens or OAuth credentials
- Personally Identifiable Information (PII) without masking
- Full credit card numbers or SSNs
- Sensitive health information (PHI)
- Full request bodies containing sensitive data

**ALWAYS:**
- Log UIDs or identifiers instead of sensitive data
- Mask or redact sensitive fields: `email='u***@example.com'`
- Use audit logs for security-relevant events
- Log authentication attempts (success/failure) with user identifiers only

**Example - BAD:**
```python
log.info("User login: email=%s, password=%s", email, password)  # NEVER DO THIS
```

**Example - GOOD:**
```python
log.info("User login attempt: uid=%s", user_uid)
log.info("Authentication successful: uid=%s, method=oauth", user_uid)
```

## Performance Considerations

- **Avoid logging in tight loops** unless using DEBUG level
- **Use lazy formatting**: `log.info("Value: %s", value)` NOT `log.info(f"Value: {value}")`
- **Don't construct expensive log messages** unless that level is enabled
- **Consider conditional logging** for expensive operations:

```python
if log.isEnabledFor(logging.DEBUG):
    expensive_debug_info = compute_expensive_info()
    log.debug("Details: %s", expensive_debug_info)
```

## Code Review Checklist

When reviewing code for logging standards, check:

1. **Import present**: `import logging` at top of file
2. **Logger initialized**: `log = logging.getLogger(__name__)` at module level
3. **Appropriate level used**: INFO for operations, ERROR for failures, DEBUG for details
4. **No sensitive data**: Verify no passwords, tokens, or PII in logs
5. **Lazy formatting**: Using `%s` placeholders, not f-strings in log calls
6. **Context provided**: Log messages include relevant identifiers (UIDs, names)
7. **Error logging**: Exceptions are logged with `exc_info=True` when helpful
8. **Structured data**: Use key-value pairs for parseable logs: `"action=create, uid=%s"`

## Example Analysis Output

When analyzing code, provide:

### Logging Analysis for `[filename]`

**Status**: Good / Needs Improvement / Missing Logging

**Findings:**
1. **Missing logger initialization** (Line X)
   - No `import logging` or `log = logging.getLogger(__name__)`
   - Add at module level

2. **Missing operation logging** (Line Y - `create_notification`)
   - Important create operation has no logs
   - Recommendation: Add INFO log at entry and success, ERROR log in exception handler

3. **Inappropriate log level** (Line Z)
   - Using INFO for detailed debug information
   - Recommendation: Change to DEBUG level

4. **Potential security issue** (Line W)
   - Logging potentially sensitive field: `user.email`
   - Recommendation: Log `user.uid` instead or mask email

**Suggested Improvements:**

```python
# Add at top of file
import logging

log = logging.getLogger(__name__)

# Add to method
def create_notification(...):
    log.info("Creating notification: title='%s'", notification_input.title)
    try:
        result = self.repo.create_notification(...)
        log.info("Created notification: sn=%s", result.sn)
        return result
    except Exception as e:
        log.error("Failed to create notification: %s", str(e), exc_info=True)
        raise
```

## Anti-Patterns to Avoid

**Over-logging**: Don't log every single line or variable
**Under-logging**: Don't skip logging important operations
**String formatting in call**: `log.info(f"Value {x}")` - use lazy evaluation
**Logging inside loops**: Causes performance issues
**Generic messages**: "Error occurred" - provide context
**Logging without context**: Include UIDs, operation names, relevant identifiers
**Logging sensitive data**: Passwords, tokens, full PII
**Wrong log level**: ERROR for warnings, INFO for debug data

## Integration with Existing Patterns

This codebase already has:
- Exception logging in `common/logger.py::log_exception()`
- Tracing middleware for HTTP requests
- Request metrics tracking

Your logging should complement these, not duplicate them:
- **Don't log HTTP request/response** (middleware does this)
- **Don't log exception stack traces** (middleware does this)
- **Do log business operations** not visible to middleware
- **Do log repository operations** for database visibility

## Final Notes

- Be pragmatic: Not every function needs logs
- Focus on operations that help debugging production issues
- Consider what you'd want to see in logs when investigating an incident
- Follow the principle: "Log what you'd want to know when things go wrong"
- Keep log messages concise but informative
- Use consistent terminology across log messages