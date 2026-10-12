# Replace Pylint with Ruff for static code analysis

## Status

Accepted

## Context

Every Python component in this monorepo - `api/` (the main Clinical MDR API,
plus its shared `common/`, `consumer_api/`, and `extensions/` code), `db/`,
`db_schema_migration/`, `import_standards/`, `import_sponsor_data/`,
`load_tests/`, and `verifications/` - used [Pylint](https://pylint.pycqa.org/)
as its static code analysis (linting) tool, each with its own `pylint`
dev-dependency pin and its own `uv run poe lint` task, enforced in each
component's local pre-commit hook and CI build.

Pylint has become noticeably slower as the codebases have grown, and each
component's `pyproject.toml` had accumulated its own long list of globally
disabled checks (missing docstrings, `fixme`, `global-statement`,
`import-outside-toplevel`, `protected-access`, `too-few-public-methods`, and
others) plus custom naming/design overrides needed to keep it passing.
Maintaining near-duplicate configuration across seven components, and waiting
on lint runs in local development and CI, had become friction for
contributors.

Beyond raw speed, Pylint's own suppression handling had become unreliable:
findings that were already accepted and explicitly disabled would intermittently
reappear and fail the lint step anyway, with no underlying code change to justify it.
This wasn't Pylint surfacing genuinely new issues - it was Pylint sporadically
disregarding suppressions that had already been reviewed and approved.
This was especially disruptive in CI: a pipeline could fail the lint step on
a PR with no relevant code changes, or fail on one run and pass on a retry of
the exact same commit, which made the lint gate feel unreliable and forced
unnecessary re-runs/investigation instead of catching real issues. That
non-determinism eroded trust in the lint gate and added rework on top of the
performance problem.

[Ruff](https://docs.astral.sh/ruff/) is a static analysis and formatting tool
written in Rust that reimplements a large subset of Pylint's rules (plus many
from Flake8, pyupgrade, and other tools) and runs orders of magnitude faster.
It is now widely adopted across the Python ecosystem as a drop-in (or
near-drop-in) replacement for Pylint/Flake8.

## Decision

We replaced Pylint with Ruff as the static code analysis tool across every
Python component in the monorepo: `api/`, `db/`, `db_schema_migration/`,
`import_standards/`, `import_sponsor_data/`, `load_tests/`, and
`verifications/`. Each component's dependency and configuration are managed
independently (there is no shared root `pyproject.toml`), so the change was
applied component-by-component but followed the same pattern in each:

- Removed the `pylint` dev dependency and added `ruff~=0.16.8` in the
  component's `pyproject.toml`, updating its `uv.lock`.
- Replaced the component's `[tool.pylint.*]` sections with `[tool.ruff]` /
  `[tool.ruff.lint]` (and `[tool.ruff.lint.pylint]` for design thresholds such
  as `max-args`, `max-branches`, `max-locals`, `max-statements`).
  - `api/` opted into a broader rule surface - `PL` (Pylint), `UP`
    (pyupgrade), `F` (Pyflakes), `E` (pycodestyle errors), `RUF`
    (Ruff-specific), `I` (isort), `C4` (comprehensions), and `ASYNC`.
  - `db/`, `db_schema_migration/`, `import_standards/`,
    `import_sponsor_data/`, `load_tests/`, and `verifications/` select just
    `PL` (Pylint-equivalent rules), matching their narrower previous Pylint
    configuration.
  - Each component keeps its own `ignore` list (e.g. `PLC0415`
    import-outside-toplevel, `PLR0917` too-many-positional-arguments,
    `PLW0603` global-statement, `PLR2004` magic-value-comparison for test/API
    status-code assertions) and, where needed, `per-file-ignores` (e.g. `E402`
    for the `api/` app entrypoints that import after `sys.path` setup).
- Updated each component's `poe lint` task (and any app-scoped variants, e.g.
  `consumer-api-lint`, `extensions-lint` in `api/`, or the `ruff` alias task in
  `verifications/`) to run `ruff check` instead of `pylint`.
- Updated the pre-commit hooks (`api/.pre-commit-config.yaml`,
  `db_schema_migration/.pre-commit-config.yaml`,
  `import_sponsor_data/.pre-commit-config.yaml`,
  `verifications/.pre-commit-config.yaml`) to run the `ruff` entry point
  instead of `pylint`.
- Updated documentation and agent/skill instructions (`README.md`,
  `api/README.md`, `api/CLAUDE.md`, `api/.claude/rules/*.md`,
  `db_schema_migration/README.md`, `verifications/README.md`,
  `.claude/agents/*`, `.claude/skills/osb-develop-main-api/SKILL.md`) that
  referenced Pylint.
- Fixed the violations Ruff surfaced across each codebase (mostly in
  `api/`'s `domain_repositories/`, plus smaller fixes in
  `db_schema_migration/`, `import_sponsor_data/`, `load_tests/`, and
  `verifications/`) so the new tool passes cleanly everywhere.
- Updated the CI workflows (`.github/workflows/api-build.yml`,
  `db-schema-migration-build.yml`, `import-sponsor-data-build.yml`,
  `load-tests-build.yml`, `verifications-build.yml`,
  `pr-required-checks.yml`) that invoke each component's `lint` task.

`isort`/Black remain the formatting tools in every component for now - only
static analysis (linting) moved to Ruff. `api/` additionally configured
`[tool.ruff.lint.isort]` to match its existing `isort` settings.

## Consequences

- Lint runs (locally, in pre-commit, and in CI) are significantly faster
  across all seven components, and - just as importantly - deterministic:
  once a finding is suppressed via Ruff's `ignore`/`per-file-ignores`
  configuration or a `# noqa` comment, it stays suppressed, removing the
  flaky re-triage cycles Pylint caused.
- Each component's lint configuration is more compact and rule intent is
  clearer through named rule codes (`PLC0415`, `PLR0917`, `PLW0603`, ...)
  instead of Pylint's free-text `disable` list.
- Contributors must have Ruff available; it ships as a dev dependency in every
  component (`uv sync --group dev`), so no separate install step is required.
- Rule selection and thresholds are still configured per component rather
  than shared, mirroring how Pylint was configured before - this preserves
  each component's existing tolerance level but means the same divergence
  risk (configs drifting apart over time) remains.
- Some Pylint rules have no exact Ruff equivalent; if a gap is found to matter
  in any component, it should be raised and addressed in a follow-up ADR or
  configuration change rather than silently reintroducing Pylint.
