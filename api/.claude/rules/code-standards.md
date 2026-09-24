# Code Style & Standards

## Formatting and Linting

- **Formatter**: Black + isort (isort runs `profile = 'black'`). **Line length is Black's default of 88** — `[tool.black]` in `pyproject.toml` sets only `target-version`, no `line-length` override, and `setup.cfg`'s flake8 agrees at 88. Write to 88; anything longer gets rewritten by `pipenv run format`.
- **Do not confuse the two line limits**: the `max-line-length = 200` in `pyproject.toml` belongs to `[tool.pylint.'FORMAT']`. It is the *linter's* ceiling, deliberately loose so Pylint does not fight Black — it is NOT the formatting target.
- **Linter**: Pylint with custom rules in `pyproject.toml`
- **Type Checking**: mypy with `check_untyped_defs = true` and `disallow_untyped_defs = true` — but note that `disable_error_code` mutes `no-untyped-def`, which is the very code `disallow_untyped_defs` emits, so missing annotations are not actually reported. Also muted: `attr-defined`, `import-untyped`, `override`, `return-value`, `union-attr`. Enforcement is looser than the flag names suggest. `clinical_mdr_api/tests` is excluded from type checking entirely.
- **Naming**: Follow PEP 8, public API = no leading underscore
- **Disabled Pylint Checks**: Missing docstrings, fixme, too-few-public-methods, too-many-ancestors, cyclic-import, etc. (see `pyproject.toml`)
- **Descriptive variable names over clever abbreviations**
- **Imports always at the top of the file** - never use inline/local imports inside functions or test methods

## FastAPI Best Practices

- Use dependency injection for database sessions, authentication, and shared services
- Leverage Pydantic models for request/response validation
- Implement proper exception handling with custom exception types
- Include comprehensive OpenAPI documentation
