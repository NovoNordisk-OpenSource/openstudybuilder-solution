# OpenStudyBuilder API Extensions

Part of the [API](../README.md) component. For repository-wide setup, see the
[root README](../../README.md#prerequisites).

This folder contains API extensions to the OpenStudyBuilder API. The extensions system allows for modular functionality to be added to the main API without modifying the core codebase.

## Architecture Overview

The extensions system provides:
- **Dynamic Extension Loading**: Extensions are automatically discovered and loaded at runtime
- **Isolated API Routers**: Each extension can define its own API endpoints
- **Shared Infrastructure**: Extensions can leverage common utilities, authentication, and database access
- **Independent Testing**: Each extension has its own test suite
- **Separate API Server**: Extensions run on a dedicated FastAPI instance (default port 8009)

## Directory Structure

```
extensions/
├── README.md                    # This file
├── extensions_api.py            # Main FastAPI application for extensions
├── common.py                    # Shared utilities for extensions
├── apiVersion                   # Version file for the extensions API
├── openapi.json                 # Generated OpenAPI specification
├── reports/                     # Test coverage and reports
├── __init__.py                  # Makes extensions a Python package
│
├── hello/                       # Example "hello" extension
│   ├── __init__.py
│   ├── hello_main.py            # Router definition (required)
│   ├── db.py                    # Database operations (recommended)
│   └── tests/                   # Extension tests (recommended)
│       ├── __init__.py
│       └── test_extension.py
│
├── my_extension/                # "my_extension" extension
│   ├── __init__.py
│   ├── my_extension_main.py     # Router definition (required)
│   ├── models.py                # Pydantic models (recommended)
│   ├── db.py                    # Database operations (recommended)
│   ├── db_models.py             # Neomodel database models (optional)
│   ├── api_client.py            # External API client (optional)
│   ├── mock/                    # Mock data for development/testing
│   │   └── *.json
│   └── tests/                   # Extension tests (recommended)
│       ├── __init__.py
│       └── test_extension.py
|
├── system/                      # System/health check extension
│   ├── __init__.py
│   ├── system_main.py
│   └── tests/
│       ├── __init__.py
│       └── test_extension.py
│ 
└── tests/                      # Common and auth tests for extensions
    ├── __init__.py
    ├── auth/
    │    └── integration/
    │        ├── __init__.py
    │        └── routes.py      # Extensions API routes and their required access roles (required)
    ├── conftest.py             # Common pytest fixtures       
    └── test_common.py         

```

## How to run extensions locally

### Prerequisites
- Python 3.14 installed
- Pipenv installed
- Neo4j database running (configure `NEO4J_DSN` environment variable)
- Dependencies installed: `pipenv sync --dev` (run from the `api` directory)

### Start the Extensions API Server

Run the development server with auto-reload:

```bash
pipenv run extensions-api-dev
```

This will start the FastAPI application on `http://localhost:8009`

### Access the API

Once running, you can access:
- **API Documentation (Swagger)**: http://localhost:8009/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8009/redoc
- **OpenAPI Schema**: http://localhost:8009/openapi.json

### Environment Variables

Configure these environment variables in a `.env` file or export them:

```bash
NEO4J_DSN=bolt://neo4j:<your-neo4j-password>@localhost:7687
OAUTH_ENABLED=false  # Set to true if using authentication
```




## How Extensions Are Loaded

1. The `extensions_api.py` file contains the main FastAPI application
2. The `load_extensions()` function automatically discovers all extensions:
   - Scans all subdirectories in the `extensions/` folder
   - Looks for files named `{extension_name}_main.py`
   - Dynamically imports the router from each extension
   - Mounts the router with a prefix based on the extension name (e.g., `/hello`, `/my_extension`)

## Creating a New Extension

Follow these steps to create a new extension:

### 1. Create Extension Directory

Create a new folder in `extensions/` with your extension name (use lowercase, underscores for multi-word names):

```bash
mkdir extensions/my_extension
```

### 2. Create Required Files

#### `__init__.py`
Create an empty `__init__.py` file to make it a Python package:

```bash
touch extensions/my_extension/__init__.py
```

#### `my_extension_main.py` (Required)
This is the main file that defines your extension's API router. The filename must follow the pattern `{extension_name}_main.py`:

```python
from fastapi import APIRouter

from common.auth import rbac
from common.auth.dependencies import security

router = APIRouter(
    tags=["MyExtension"],
)


@router.get(
    "/example",
    dependencies=[security, rbac.ADMIN_READ],
    status_code=200,
)
def get_example():
    """
    Example endpoint that demonstrates the basic structure.
    """
    return {"message": "Hello from my extension!"}
```

**Key Points:**
- The module **must** export a variable named `router` (an instance of `APIRouter`)
- Use `dependencies=[security, rbac.ADMIN_READ]` for authentication (optional)
- The extension will be accessible at `/my-extension/example` (underscores become hyphens)

### 3. Optional: Add Database Operations

If your extension needs database access, create a `db.py` file:

```python
from neomodel.sync_.core import db


def get_data_from_neo4j():
    """Execute Cypher queries against Neo4j database."""
    query = """
    MATCH (n:MyNode)
    RETURN count(n) as count
    """
    results, _ = db.cypher_query(query)
    return results[0][0] if results else 0
```

### 4. Optional: Add Pydantic Models

Create a `models.py` file for request/response models:

```python
from pydantic import BaseModel, Field


class MyRequest(BaseModel):
    name: str = Field(..., description="Name of the resource")
    value: int = Field(gt=0, description="Positive integer value")


class MyResponse(BaseModel):
    id: str
    name: str
    created_at: str
```

### 5. Add Tests

Create a `tests/` directory with test files:

```bash
mkdir extensions/my_extension/tests
touch extensions/my_extension/tests/__init__.py
```

Create `tests/test_extension.py`:

```python
import pytest
from fastapi.testclient import TestClient

from extensions.extensions_api import app


@pytest.fixture(scope="module")
def api_client():
    """Create FastAPI test client"""
    yield TestClient(app)


def test_get_example(api_client):
    res = api_client.get("/my-extension/example")
    assert res.status_code == 200
    assert res.json() == {"message": "Hello from my extension!"}
```

### 6. Run Your Extension

Start the extensions API server:

```bash
pipenv run extensions-api-dev
```

The extension will be automatically loaded and available at:
- Endpoint: `http://localhost:8009/my-extension/example`
- OpenAPI Docs: `http://localhost:8009/docs`

### 7. Run Tests

Run all extension tests:

```bash
pipenv run extensions-test
```

Run schemathesis API tests:

```bash
pipenv run extensions-schemathesis
```

## Available Pipenv Commands

The following commands are available for working with extensions:

### `pipenv run extensions-api-dev`
Starts the extensions API development server with auto-reload enabled on port 8009. This command launches a uvicorn server that automatically detects and loads all extensions from the `extensions/` folder. Any code changes will trigger an automatic reload, making it ideal for development. The API will be accessible at `http://localhost:8009` with interactive documentation at `/docs`.

### `pipenv run extensions-openapi`
Generates the OpenAPI specification file for the extensions API. This command creates or updates the `extensions/openapi.json` file based on all registered endpoints from loaded extensions. The generated OpenAPI schema includes all extension routes, request/response models, authentication requirements, and endpoint documentation. This file is useful for API documentation, client SDK generation, and API testing tools.

### `pipenv run extensions-lint`
Runs PyLint static code analysis on all extension code. This command checks all Python files in the `extensions/` directory for code quality issues, potential bugs, style violations, and adherence to coding standards. It helps maintain consistent code quality across all extensions and catches common programming errors before they reach production.

### `pipenv run extensions-test`
Executes the complete test suite for all extensions. This command runs pytest with coverage reporting enabled, testing all extension endpoints and functionality. Tests are run in parallel using pytest-xdist for faster execution, with coverage reports generated in both HTML and XML formats in `extensions/reports/`. The command automatically discovers and runs all test files in each extension's `tests/` directory, excluding authentication tests by default.

### `pipenv run extensions-testauth`
Executes the authentication test suite for all extensions, with coverage reports generated in both HTML and XML formats in `extensions/reports/`.

### `pipenv run extensions-schemathesis`
Performs automated API testing using Schemathesis, a property-based testing tool for OpenAPI/Swagger specs. This command generates test cases automatically from the OpenAPI schema and sends them to the running extensions API server. It validates that all endpoints conform to their OpenAPI specifications, checking for proper response codes, data types, and edge cases. The tool runs 100 test examples per endpoint and generates detailed reports in `extensions/reports/`, helping identify API contract violations and potential bugs.

## Available Utilities

Extensions can use utilities from `extensions/common.py`:

### Pagination
```python
from extensions.common import (
    PAGE_NUMBER_QUERY,
    PAGE_SIZE_QUERY,
    PaginatedResponse,
)

@router.get("/items")
def get_items(
    page_size: PAGE_SIZE_QUERY = 10,
    page_number: PAGE_NUMBER_QUERY = 1,
):
    items = fetch_items()
    return PaginatedResponse.from_input(
        request=request,
        items=items,
        total=len(items),
        page_size=page_size,
        page_number=page_number,
    )
```

### Logging
```python
from extensions.common import Logger

log = Logger(__name__)
log.info("Extension loaded successfully")
```

### API Version
```python
from extensions.common import get_api_version

version = get_api_version()
```

## Authentication & Authorization

Extensions inherit the authentication system from the main API:

```python
from common.auth import rbac
from common.auth.dependencies import security

# Require authentication
@router.get("/protected", dependencies=[security])
def protected_endpoint():
    return {"message": "You are authenticated!"}

# Require specific role
@router.post("/admin-only", dependencies=[security, rbac.ADMIN_WRITE])
def admin_endpoint():
    return {"message": "Admin access granted!"}
```

Available RBAC permissions:
- `rbac.ADMIN_READ` - Admin read access
- `rbac.ADMIN_WRITE` - Admin write access
- Check `common/auth/rbac.py` for more options

## Best Practices

1. **Naming Convention**: Use lowercase with underscores for folder names (e.g., `my_extension`)
2. **Main Module**: Always name your main file `{extension_name}_main.py`
3. **Router Export**: Always export a `router` variable from your main module
4. **Tags**: Use meaningful tags for your router to organize OpenAPI documentation
5. **Documentation**: Add docstrings to all endpoints for auto-generated API docs
6. **Testing**: Write comprehensive tests for all endpoints
7. **Error Handling**: Use exceptions from `common.exceptions` for consistent error responses
8. **Models**: Define Pydantic models for request/response validation
9. **Database**: Keep database logic separate in a `db.py` module
10. **Dependencies**: Reuse existing services from `clinical_mdr_api.services` when possible

## Common Patterns

### External API Integration
```python
import requests
from common.config import settings


class ExternalApiClient:
    def __init__(self):
        self.base_url = settings.external_api_url
        self.api_key = settings.external_api_key
    
    def fetch_data(self, param: str):
        response = requests.get(
            f"{self.base_url}/data",
            params={"param": param},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        response.raise_for_status()
        return response.json()
```

### Database Models with Neomodel
```python
from neomodel import (
    StructuredNode,
    StringProperty,
    IntegerProperty,
    RelationshipTo,
)


class MyNode(StructuredNode):
    name = StringProperty(unique_index=True, required=True)
    value = IntegerProperty()
    
    # Relationships
    related_to = RelationshipTo('OtherNode', 'RELATED_TO')
```

### Error Handling
```python
from common.exceptions import (
    BusinessLogicException,
    NotFoundException,
    ValidationException,
)

@router.get("/item/{item_id}")
def get_item(item_id: str):
    item = find_item(item_id)
    if not item:
        raise NotFoundException(f"Item with id {item_id} not found")
    return item
```



## Examples

Refer to existing extensions for working examples:
- **hello**: Simple extension showing basic structure
- **system**: Health check and system monitoring endpoints


