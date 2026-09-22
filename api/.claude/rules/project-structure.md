# Project Structure

## Important Files

- `clinical_mdr_api/main.py` - FastAPI app initialization, middleware setup, exception handlers
- `common/config.py` - Centralized settings (loaded from environment variables)
- `common/database.py` - Neo4j/neomodel configuration
- `common/exceptions.py` - Base exception classes
- `Pipfile` - All scripts and dependency definitions
- `pyproject.toml` - Tool configurations (pylint, mypy, isort, pytest)
- `openapi.json` - Generated OpenAPI specification (do not edit manually)

## Special Directories

- `sblint/` - Custom static analysis tool
- `templates/` - Jinja2 templates
- `xml_stylesheets/` - XSLT stylesheets for XML transformations
- `m11-templates/` - ICH M11 clinical trial templates
- `doc/` - Additional documentation
- `reports/` - Generated test/coverage reports

## Git Workflow

- Single long-lived branch: `main`. There is **no** `develop` branch — this is not Git-flow.
- Work happens on topic branches cut from `main`; pull requests target `main`.
- `api/` is one component of a monorepo. A small change spanning `api/` and `frontend/` belongs in **one** PR — see the root `CLAUDE.md` for why the CI coordinator makes splitting it the wrong call.
- Pre-commit hooks: configured in `api/.pre-commit-config.yaml` (per-component, not at the repo root).
