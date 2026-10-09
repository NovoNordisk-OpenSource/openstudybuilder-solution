# Replace Pipenv with uv + poethepoet for Python dependency and task management

## Status

Accepted

## Context

Every Python component in this monorepo (`api/`, `db/`,
`db_schema_migration/`, `import_standards/`, `import_sponsor_data/`,
`export/`, `verifications/`, `load_tests/`) managed dependencies with
[Pipenv](https://pipenv.pypa.io/), each with its own `Pipfile` /
`Pipfile.lock`, and ran scripts through the flat `Pipfile [scripts]` block via
`pipenv run <script>`.

Pipenv's install/lock resolution had become slow, `Pipfile` is a
Pipenv-specific format rather than the ecosystem-standard `pyproject.toml`,
and the `[scripts]` block only supports flat, single-line commands - it
cannot express composable or sequenced tasks (e.g. "format" running `black`
then `isort`) without ad-hoc shell scripting.

[uv](https://docs.astral.sh/uv/) is a fast, Rust-based Python package/project
manager that reads a standard `pyproject.toml` and produces a `uv.lock`
lockfile, and is now widely adopted as a drop-in replacement for
Pipenv/pip-tools/Poetry. 

[poethepoet](https://poethepoet.natn.io/) (`poe`)
is a task runner that reads task definitions from `[tool.poe.tasks]` in
`pyproject.toml`, supporting composed/sequenced tasks, and integrates
naturally with `uv run`.

## Decision

We replaced Pipenv with uv (dependency management) and poethepoet (task
running) across every Python component:

- Removed `Pipfile` / `Pipfile.lock` from each component; each now has a
  standard `pyproject.toml` (with `[project]`/`[dependency-groups]`) and a
  generated `uv.lock`.
- Moved each component's task scripts from the `Pipfile [scripts]` block to
  `[tool.poe.tasks]` in its `pyproject.toml`, keeping task names the same
  where possible (`dev`, `format`, `testunit`, `testint`, `lint`, `mypy`,
  `openapi`, etc.).
- Updated the developer workflow:
  - Installing dependencies: `pipenv sync --dev` → `uv sync --group dev`.
  - Running scripts: `pipenv run <script>` → `poe <script>` (inside an
    activated venv) or `uv run poe <script>` (without activating one).
- Updated each component's `Dockerfile`/`compose.yaml` (`api/`, `db/`,
  `export/`, `import_sponsor_data/`) to install and run via `uv`/`uv run poe`
  instead of `pipenv`.
- Updated CI workflows for every affected component
  (`.github/workflows/api-build.yml`, `api-dependency-review.yml`,
  `db-build.yml`, `db-schema-migration-build.yml`, `export-build.yml`,
  `import-sponsor-data-build.yml`, `import-standards-build.yml`,
  `load-tests-build.yml`, `verifications-build.yml`,
  `verifications-dependency-review.yml`) to set up `uv` and call `uv run poe
  <task>` instead of `pipenv`.
- Updated the shared SBOM tooling (`_tools/build_sbom.py`) and each
  component's `sbom.md` / `doc/licenses/README.md` to generate license/SBOM
  reports from `uv`'s dependency metadata instead of Pipenv's.
- Updated documentation and agent/skill instructions (root `README.md`,
  `CLAUDE.md`, `api/README.md`, `api/CLAUDE.md`, `api/.claude/rules/*.md`,
  each component's own `README.md`, `.claude/agents/*`, and the
  `osb-develop-*-api` skill docs) that referenced `pipenv`/`Pipfile`.

## Consequences

- Dependency installs and lock resolution are significantly faster across all
  eight components.
- Every component now uses the ecosystem-standard `pyproject.toml` instead of
  the Pipenv-specific `Pipfile`, making tooling (editors, linters, dependency
  scanners) that already understands `pyproject.toml` work without special
  cases.
- Task definitions in `[tool.poe.tasks]` are more expressive than the flat
  `Pipfile [scripts]` block - composed/sequenced tasks (e.g. `format` running
  `black` then `isort`) are now declared directly instead of via ad-hoc shell
  scripting.
- Contributors and CI must have `uv` available; CI workflows across every
  component were updated to install it, and local setup instructions now start
  with `uv sync --group dev` instead of `pipenv sync --dev`.

