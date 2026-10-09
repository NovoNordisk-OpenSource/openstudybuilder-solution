# Essential Commands

## Environment Setup
```bash
uv sync --group dev            # Install dependencies
cp .env.example .env           # Setup environment variables (edit NEO4J_DSN, UID)
```

## Running APIs
```bash
uv run poe dev                 # Start main API (localhost:8000)
uv run poe consumer-api-dev    # Start consumer API (localhost:8008)
uv run poe extensions-api-dev  # Start extensions API (localhost:8009)
```

## Testing
```bash
# Run specific test
uv run poe test -- clinical_mdr_api/tests/integration/services/test_listing_study_design.py::TestStudyListing::test_registry_identifiers_listing

# Test suites
uv run poe testunit            # Unit tests only
uv run poe testint             # Integration tests (requires Neo4j; parallel via -n auto --dist loadfile)
uv run poe testauth            # OAuth/auth tests
uv run poe test-telemetry      # Telemetry tests
uv run poe test                # All tests

# Consumer API tests
uv run poe consumer-api-test
uv run poe consumer-api-testauth

# Extensions API tests
uv run poe extensions-test
uv run poe extensions-testauth
```

## Code Quality
```bash
uv run poe format              # Auto-format with Black + isort
uv run poe lint                # Run Ruff
uv run poe mypy                # Type checking
uv run poe sblint              # Custom static analysis (SBLint)
```

## API Documentation
```bash
uv run poe openapi             # Generate openapi.json for main API
uv run poe consumer-openapi    # Generate openapi.json for consumer API
uv run poe extensions-openapi  # Generate openapi.json for extensions API
uv run poe schemathesis        # Validate API against OpenAPI spec
```
