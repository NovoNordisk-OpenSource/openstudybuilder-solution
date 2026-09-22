# Essential Commands

## Environment Setup
```bash
pipenv sync --dev              # Install dependencies
cp .env.example .env           # Setup environment variables (edit NEO4J_DSN, UID)
```

## Running APIs
```bash
pipenv run dev                 # Start main API (localhost:8000)
pipenv run consumer-api-dev    # Start consumer API (localhost:8008)
pipenv run extensions-api-dev  # Start extensions API (localhost:8009)
```

## Testing
```bash
# Run specific test
pipenv run pytest clinical_mdr_api/tests/integration/services/test_listing_study_design.py::TestStudyListing::test_registry_identifiers_listing

# Test suites
pipenv run testunit            # Unit tests only
pipenv run testint             # Integration tests (requires Neo4j; parallel via -n auto --dist loadfile)
pipenv run testauth            # OAuth/auth tests
pipenv run test-telemetry      # Telemetry tests
pipenv run test                # All tests

# Consumer API tests
pipenv run consumer-api-test
pipenv run consumer-api-testauth

# Extensions API tests
pipenv run extensions-test
pipenv run extensions-testauth
```

## Code Quality
```bash
pipenv run format              # Auto-format with Black + isort
pipenv run lint                # Run Pylint
pipenv run mypy                # Type checking
pipenv run sblint              # Custom static analysis (SBLint)
```

## API Documentation
```bash
pipenv run openapi             # Generate openapi.json for main API
pipenv run consumer-openapi    # Generate openapi.json for consumer API
pipenv run extensions-openapi  # Generate openapi.json for extensions API
pipenv run schemathesis        # Validate API against OpenAPI spec
```
