# REST API Conventions

Following [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/):

## Naming Conventions

- **Paths**: Nouns only (plural form), `kebab-case`, minimize nesting and root endpoints
- **Parameters**: `snake_case` for query params and JSON fields
- **UID Parameters**: Include entity type prefix (e.g., `study_uid`, `concept_uid`)

## HTTP Methods

- GET (200) - Read operations
- POST (201) - Create new entities
- PUT (200) - Overwrite entirely (avoid if possible)
- PATCH (200) - Partial updates
- DELETE (204) - Delete operations

## Error Handling

All custom exceptions are defined in `common/exceptions.py` and imported as `from common.exceptions import NotFoundException, ...`. There is no `clinical_mdr_api/exceptions/` module — never create one.

Every exception derives from `MDRApiBaseException`, which carries a `status_code` class attribute; subclasses inherit it unless they override it:

| Status | Exception | Use for |
|--------|-----------|---------|
| 400 | `BusinessLogicException` | Business rule violation |
| 400 | `ValidationException` | Subclass of `BusinessLogicException`; invalid input or failed validation |
| 401 | `NotAuthenticatedException` | Missing or invalid Bearer token |
| 403 | `ForbiddenException` | Authenticated but insufficient permissions |
| 404 | `NotFoundException` | Referenced entity does not exist |
| 405 | `MethodNotAllowedException` | Method not permitted on this resource |
| 409 | `AlreadyExistsException` | Conflicts with an existing entity |
| 500 | `MDRApiBaseException` / `InternalServerError` | Base class; the default when nothing more specific is raised |

Raise the most specific type that fits — never a generic `Exception`. `VisitsAreNotEqualException` (400) exists because one endpoint needs to distinguish several 400 cases; follow that pattern only when a caller must tell them apart.

Error responses are built by `ErrorResponse` in `common/models/error.py` and carry `time`, `path`, `method`, `type`, `message`, and a `details` array (note: `details`, not `errors`). Each entry in `details` is a `ValidationDetail` with `error_code`, `field`, `msg`, and `ctx`.

## OpenAPI Specifications

The OpenAPI specifications are generated from code, not written manually:

- Use `pipenv run openapi` to regenerate after endpoint changes
- Specifications are committed to version control
- Schemathesis uses these for contract testing
