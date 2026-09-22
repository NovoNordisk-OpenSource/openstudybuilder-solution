# CLAUDE.md
<!--
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

The documentation has been organized into focused rule files in `.claude/rules/` for better maintainability.
-->

## Rule Files

- **[project-overview.md](.claude/rules/project-overview.md)** - Project description and multi-API structure
- **[project-structure.md](.claude/rules/project-structure.md)** - Important files, directories, and git workflow
- **[commands.md](.claude/rules/commands.md)** - Essential commands for development, testing, and quality checks
- **[architecture.md](.claude/rules/architecture.md)** - DDD three-layer architecture and development workflow
- **[database.md](.claude/rules/database.md)** - Neo4j configuration, versioning, and concurrency
- **[api-conventions.md](.claude/rules/api-conventions.md)** - REST API guidelines and error handling
- **[code-standards.md](.claude/rules/code-standards.md)** - Code style, formatting, and FastAPI best practices
- **[authentication.md](.claude/rules/authentication.md)** - OAuth 2.0 and RBAC setup
- **[testing.md](.claude/rules/testing.md)** - Testing strategy and test organization
- **[monitoring.md](.claude/rules/monitoring.md)** - Telemetry, tracing, and logging

## Quick Reference

**Start Development:**
```bash
pipenv sync --dev
cp .env.example .env  # Edit NEO4J_DSN, UID
pipenv run dev        # Start main API (localhost:8000)
```

**Run Tests:**
```bash
pipenv run testunit   # Unit tests
pipenv run testint    # Integration tests (requires Neo4j)
pipenv run test       # All tests
```

**Code Quality:**
```bash
pipenv run format     # Auto-format code
pipenv run lint       # Run Pylint
pipenv run mypy       # Type checking
```

For detailed information, refer to the specific rule files above.
