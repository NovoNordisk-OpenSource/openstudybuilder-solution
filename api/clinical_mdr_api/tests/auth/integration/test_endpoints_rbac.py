import pytest

import common.auth.dependencies
from clinical_mdr_api.tests.auth.integration.routes import ALL_ROUTES_METHODS_ROLES
from clinical_mdr_api.tests.auth.markers import if_oauth_enabled
from clinical_mdr_api.tests.fixtures.routes import PARAMETER_DEFAULTS
from common.tests.auth.endpoints_rbac import (
    assert_rbac_correct_roles,
    assert_rbac_no_roles,
    assert_rbac_wrong_roles,
    mk_mock_jwks_service,
    mk_token_factory,
)

# Skip all tests in this module if OAuth is not enabled
pytestmark = if_oauth_enabled

ENDPOINTS_WITHOUT_ROLES = [
    ("/user-preferences", "GET"),
    ("/user-preferences", "PATCH"),
    ("/user-preferences/{preference_key}", "DELETE"),
]

# We allow 500 because this test may be running against a database with an outdated data model.
# A 500 error still means that the authentication has passed and the request reached the application code.
# This is acceptable because this test is only for the authentication part,
# and the application logic is covered by other tests.
PASSED_AUTH_STATUS_CODES = (200, 201, 202, 204, 207, 400, 403, 404, 409, 500)


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
    if (path, method) in ENDPOINTS_WITHOUT_ROLES:
        pytest.skip(f"Endpoint {method} {path} does not require any roles")

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
    if (path, method) in ENDPOINTS_WITHOUT_ROLES:
        pytest.skip(f"Endpoint {method} {path} does not require any roles")

    monkeypatch.setattr(common.auth.dependencies, "jwks_service", mock_jwks_service)
    assert_rbac_correct_roles(
        api_client,
        openapi_schema,
        mock_token,
        path,
        method,
        required_roles,
        PARAMETER_DEFAULTS,
        passed_auth_status_codes=PASSED_AUTH_STATUS_CODES,
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
    if (path, method) in ENDPOINTS_WITHOUT_ROLES:
        pytest.skip(f"Endpoint {method} {path} does not require any roles")

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
