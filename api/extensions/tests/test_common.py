# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

import pytest

from common.config import settings
from extensions.extensions_api import app, custom_openapi


@pytest.fixture
def reset_openapi_schema():
    """Reset the openapi schema before each test"""
    original_schema = app.openapi_schema
    app.openapi_schema = None
    yield
    app.openapi_schema = original_schema


def test_custom_openapi_returns_cached_schema(reset_openapi_schema):
    """Test that custom_openapi returns cached schema if already generated"""
    # First call generates the schema
    schema1 = custom_openapi()
    assert schema1 is not None

    # Second call should return the same cached instance
    schema2 = custom_openapi()
    assert schema1 is schema2


def test_custom_openapi_basic_structure(reset_openapi_schema):
    """Test that custom_openapi generates basic OpenAPI structure"""
    schema = custom_openapi()

    assert "openapi" in schema
    assert "info" in schema
    assert schema["info"]["title"] == "OpenStudyBuilder API Extensions"
    assert "version" in schema["info"]
    assert "paths" in schema
    assert "servers" in schema
    assert schema["servers"][0]["url"] == settings.openapi_schema_api_root_path


def test_custom_openapi_adds_400_responses(reset_openapi_schema):
    """Test that custom_openapi adds 400 Bad Request responses to all endpoints"""
    schema = custom_openapi()

    # Check that all endpoints have 400 response
    for _, path_item in schema["paths"].items():
        for method, operation in path_item.items():
            if method in ["get", "post", "put", "patch", "delete"]:
                assert "responses" in operation
                assert "400" in operation["responses"]
                assert operation["responses"]["400"]["description"] == "Bad Request"
                assert "application/json" in operation["responses"]["400"]["content"]


@pytest.mark.skipif(not settings.oauth_enabled, reason="OAuth is disabled in settings")
def test_custom_openapi_adds_bearer_jwt_auth_when_oauth_enabled(reset_openapi_schema):
    """Test that custom_openapi adds BearerJwtAuth security scheme when OAuth is enabled"""
    schema = custom_openapi()

    assert "components" in schema
    assert "securitySchemes" in schema["components"]
    assert "BearerJwtAuth" in schema["components"]["securitySchemes"]

    bearer_auth = schema["components"]["securitySchemes"]["BearerJwtAuth"]
    assert bearer_auth["type"] == "http"
    assert bearer_auth["scheme"] == "bearer"
    assert bearer_auth["bearerFormat"] == "JWT"
    assert bearer_auth["in"] == "header"
    assert bearer_auth["name"] == "Authorization"


@pytest.mark.skipif(not settings.oauth_enabled, reason="OAuth is disabled in settings")
def test_custom_openapi_adds_oauth_scopes_when_oauth_enabled(reset_openapi_schema):
    """Test that custom_openapi adds OAuth scopes when OAuth is enabled"""
    schema = custom_openapi()

    assert "components" in schema
    assert "securitySchemes" in schema["components"]

    if "OAuth2AuthorizationCodeBearer" in schema["components"]["securitySchemes"]:
        oauth_scheme = schema["components"]["securitySchemes"][
            "OAuth2AuthorizationCodeBearer"
        ]
        assert "flows" in oauth_scheme
        assert "authorizationCode" in oauth_scheme["flows"]
        assert "scopes" in oauth_scheme["flows"]["authorizationCode"]
        assert "api:///API.call" in oauth_scheme["flows"]["authorizationCode"]["scopes"]


@pytest.mark.skipif(settings.oauth_enabled, reason="Test requires OAuth to be disabled")
def test_custom_openapi_without_oauth(reset_openapi_schema):
    """Test that custom_openapi works correctly when OAuth is disabled"""
    schema = custom_openapi()

    # Should still have basic structure
    assert "paths" in schema
    assert "servers" in schema

    # Should still add 400 responses
    for _, path_item in schema["paths"].items():
        for method, operation in path_item.items():
            if method in ["get", "post", "put", "patch", "delete"]:
                assert "400" in operation.get("responses", {})
