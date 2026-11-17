import pytest

import common.auth.dependencies
from common.tests.auth.endpoints_rbac import (
    assert_rbac_correct_roles,
    assert_rbac_no_roles,
    assert_rbac_wrong_roles,
    mk_mock_jwks_service,
    mk_token_factory,
)
from consumer_api.tests.auth.integration.routes import ALL_ROUTES_METHODS_ROLES
from consumer_api.tests.auth.markers import if_oauth_enabled
from consumer_api.tests.conftest import PARAMETER_DEFAULTS

# Skip all tests in this module if OAuth is not enabled
pytestmark = if_oauth_enabled


@pytest.fixture(scope="session")
def mock_jwks_service():
    return mk_mock_jwks_service()


@pytest.fixture(scope="session")
def mock_token(mock_jwks_service):
    return mk_token_factory(mock_jwks_service)


@pytest.mark.parametrize("path, method, required_roles", ALL_ROUTES_METHODS_ROLES)
def test_endpoints_rbac_wrong_roles(
    monkeypatch,
    mock_jwks_service,
    mock_token,
    api_client,
    openapi_schema,
    path,
    method,
    required_roles,
):
    """Ensure that http request with access-token having wrong roles fails"""
    monkeypatch.setattr(common.auth.dependencies, "jwks_service", mock_jwks_service)
    assert_rbac_wrong_roles(
        api_client,
        openapi_schema,
        mock_token,
        path,
        method,
        required_roles,
        PARAMETER_DEFAULTS,
    )


@pytest.mark.parametrize("path, method, required_roles", ALL_ROUTES_METHODS_ROLES)
def test_endpoints_rbac_correct_roles(
    monkeypatch,
    mock_jwks_service,
    mock_token,
    api_client,
    openapi_schema,
    path,
    method,
    required_roles,
):
    """Ensure that endpoint requires specific roles in the access-token"""
    monkeypatch.setattr(common.auth.dependencies, "jwks_service", mock_jwks_service)
    assert_rbac_correct_roles(
        api_client,
        openapi_schema,
        mock_token,
        path,
        method,
        required_roles,
        PARAMETER_DEFAULTS,
    )


@pytest.mark.parametrize("path, method, required_roles", ALL_ROUTES_METHODS_ROLES)
def test_endpoints_rbac_no_roles(
    monkeypatch,
    mock_jwks_service,
    mock_token,
    api_client,
    openapi_schema,
    path,
    method,
    required_roles,
):
    """Ensure that endpoint requires at least one role in the access-token"""
    monkeypatch.setattr(common.auth.dependencies, "jwks_service", mock_jwks_service)
    assert_rbac_no_roles(
        api_client,
        openapi_schema,
        mock_token,
        path,
        method,
        required_roles,
        PARAMETER_DEFAULTS,
    )
