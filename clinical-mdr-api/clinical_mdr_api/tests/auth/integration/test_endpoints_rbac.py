# pylint: disable=redefined-outer-name
import datetime
import logging
import random
import uuid

import httpx
import pytest

import common.auth.dependencies
from clinical_mdr_api.tests.auth.integration.routes import ALL_ROUTES_METHODS_ROLES
from clinical_mdr_api.tests.auth.markers import if_oauth_enabled
from clinical_mdr_api.tests.fixtures.routes import PARAMETER_DEFAULTS
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.auth.dependencies import oidc_client
from common.auth.jwk_service import JWKService
from common.tests.auth.unit.test_jwk_service import mk_claims, mk_jwt

log = logging.getLogger(__name__)

# Skip all tests in this module if OAuth is not enabled
pytestmark = if_oauth_enabled

KNOWN_ROLES = {
    "Admin.Read",
    "Admin.Write",
    "Library.Read",
    "Library.Write",
    "Study.Read",
    "Study.Write",
}

IRRELEVANT_ROLES = ["Some, Fake", "Testing", ""]


@pytest.fixture(scope="session")
def mock_jwks_service():
    """A JWKService with a generated key for self-signed tokens"""
    jwks_service = JWKService(oidc_client, audience=str(uuid.uuid4()))
    jwks_service.claims_options["aud"] = {"values": [jwks_service.audience]}
    jwks_service.claims_options["iss"] = {"values": [jwks_service.audience]}
    jwks_service.generate_key()
    return jwks_service


@pytest.fixture(scope="session")
def mock_token(mock_jwks_service):
    key = mock_jwks_service.keys[list(mock_jwks_service.keys.keys())[0]]

    def factory(roles: list[str] | None = None):
        claims = mk_claims(
            audience=mock_jwks_service.audience, issuer=mock_jwks_service.audience
        )

        if roles:
            claims["roles"] = list(roles)

        token = mk_jwt(claims, key)
        return token.decode("utf-8")

    return factory


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

    (
        path_parameters,
        query_parameters,
        payload,
        is_json,
        content_type,
    ) = _prepare_http_request(openapi_schema, path, method)

    # Patch JWKS service to accept self-signed tokens
    monkeypatch.setattr(common.auth.dependencies, "jwks_service", mock_jwks_service)

    # Assemble a list of known roles
    required_roles = list(required_roles)
    invalid_roles = list(set(KNOWN_ROLES) - set(required_roles)) + IRRELEVANT_ROLES
    assert invalid_roles, "Can not run test with only valid roles"

    # Some valid combinations of roles (any of the required roles are sufficient for access)
    valid_role_sets = []
    for i in range(len(required_roles)):
        roles = random.choices(required_roles, k=i + 1)
        valid_role_sets += [
            roles,
            required_roles + [random.choice(invalid_roles)],
            required_roles
            + random.choices(invalid_roles, k=random.randint(1, len(invalid_roles))),
        ]

    # Randomize all valid role sets
    map(random.shuffle, valid_role_sets)

    # Some insufficient combination of roles
    random.shuffle(invalid_roles)
    insufficient_role_sets = [invalid_roles]
    for i in range(max(len(invalid_roles) - 1, 3)):
        # pick a random number of unique roles (random.choices may return duplicates)
        insufficient_role_sets.append(
            list(
                set(
                    random.choices(
                        invalid_roles, k=random.randint(1, len(invalid_roles) - 1)
                    )
                )
            )
        )

    # Ensure that http request with token having wrong roles fails
    for roles in insufficient_role_sets:
        response = do_request_with_token(
            api_client,
            mock_token(roles=roles),
            method,
            path,
            path_parameters,
            query_parameters,
            payload,
            is_json,
            content_type,
        )
        _assert_insufficient_roles_error(required_roles, roles, response)


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

    (
        path_parameters,
        query_parameters,
        payload,
        is_json,
        content_type,
    ) = _prepare_http_request(openapi_schema, path, method)

    # Patch JWKS service to accept self-signed tokens
    monkeypatch.setattr(common.auth.dependencies, "jwks_service", mock_jwks_service)

    # Assemble a list of known roles
    required_roles = list(required_roles)
    invalid_roles = list(set(KNOWN_ROLES) - set(required_roles)) + IRRELEVANT_ROLES

    # Some valid combinations of roles (any of the required roles are sufficient for access)
    valid_role_sets = []
    for i in range(len(required_roles)):
        roles = random.choices(required_roles, k=i + 1)
        valid_role_sets += [
            roles,
            required_roles + [random.choice(invalid_roles)],
            required_roles
            + random.choices(invalid_roles, k=random.randint(1, len(invalid_roles))),
        ]

    # Randomize all valid role sets
    map(random.shuffle, valid_role_sets)

    # Send requests with correct roles
    # If response status code is different than 401/403, we assume that authentication has passed
    for roles in valid_role_sets:
        response = do_request_with_token(
            api_client,
            mock_token(roles=roles),
            method,
            path,
            path_parameters,
            query_parameters,
            payload,
            is_json,
            content_type,
        )
        assert_response_status_code(
            response, (200, 201, 202, 204, 207, 400, 403, 404, 409, 422)
        )

        if response.status_code == 400:
            payload = response.json()
            assert (payload.get("type") or "") in (
                "BusinessLogicException",
                "ValidationException",
                "ValidationError",
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

    (
        path_parameters,
        query_parameters,
        payload,
        is_json,
        content_type,
    ) = _prepare_http_request(openapi_schema, path, method)

    # Patch JWKS service to accept self-signed tokens
    monkeypatch.setattr(common.auth.dependencies, "jwks_service", mock_jwks_service)

    # Ensure that http request with token with no role claims fails
    response = do_request_with_token(
        api_client,
        mock_token(),  # token with no roles
        method,
        path,
        path_parameters,
        query_parameters,
        payload,
        is_json,
        content_type,
    )
    if int(response.status_code / 100) == 2:
        log.error(
            "Unprotected endpoint %s %s returned status code %d",
            method,
            path,
            response.status_code,
        )
    elif response.status_code != 403:
        log.error(
            "Can not guarantee that the endpoint is protected: %s %s returned status code %d:\n%s",
            method,
            path,
            response.status_code,
            response.content.decode("utf-8"),
        )
    _assert_insufficient_roles_error(required_roles, [], response)


def do_request_with_token(
    api_client,
    token,
    method,
    path,
    path_parameters,
    query_parameters,
    payload,
    is_json,
    content_type,
) -> httpx.Response:
    headers = {"Authorization": f"Bearer {token}"}
    if content_type:
        headers["Content-Type"] = content_type

    log.debug(
        "\n%s %s %s\n%s\n",
        method,
        path.format_map(path_parameters),
        query_parameters,
        headers,
    )

    return api_client.request(
        method,
        path.format_map(path_parameters),
        params=query_parameters,
        json=payload if is_json else None,
        data=None if is_json else payload,
        headers=headers,
    )


def _mk_required_parameters(parameters, where):
    params = {}
    for param in parameters:
        if param.get("required") and param.get("in") == where:
            name = param.get("name")
            params[name] = param.get("schema", {}).get(
                "default", PARAMETER_DEFAULTS.get(name, f"MISSING__{name}")
            )
    return params


def _mk_required_body_payload(schema, openapi_schemas=None):
    schema = schema.get("requestBody", {})
    if not schema:
        return None, None

    required = schema.get("required")
    if not required:
        return None, None

    contents = schema.get("content")
    if not contents:
        return None, None

    content_type, schema = next(iter(contents.items()), (None, None))
    schema = schema and schema.get("schema")
    if not (schema and _content_type_is_json(content_type)):
        return None, None

    payload = _mk_schema_example_payload(schema, openapi_schemas)

    return content_type, payload


def _content_type_is_json(content_type):
    return content_type and "/" in content_type and content_type.split("/")[1] == "json"


def _mk_schema_example_payload(schema, openapi_schemas):
    if schema.get("items"):
        is_array = True
        schema = schema["items"]
    else:
        is_array = False

    schema_ref = schema.get("$ref")
    if schema_ref:
        if not openapi_schemas:
            return None

        schema = openapi_schemas.get(schema_ref.split("/")[-1])
        if not schema:
            raise ValueError(f"Unsupported schema $ref: {schema_ref}")

    properties = schema.get("properties")
    if not properties:
        return None

    required = schema.get("required")
    payload = {}
    for name, schem in properties.items():
        if required is None or name in required:
            if schem.get("$ref"):
                payload[name] = _mk_schema_example_payload(schem, openapi_schemas)
            elif schem.get("anyOf"):
                payload[name] = _mk_schema_example_payload(
                    schem["anyOf"][0], openapi_schemas
                )
            elif schem.get("allOf"):
                payload[name] = {}
                for schem_ in schem["allOf"]:
                    payload[name].update(
                        _mk_schema_example_payload(schem_, openapi_schemas)
                    )
            else:
                payload[name] = _schema_default_value(schem, name)

    if is_array:
        payload = [payload]

    return payload


# pylint: disable=too-many-return-statements
def _schema_default_value(schema, name=None):
    if "default" in schema:
        return schema["default"]

    typ = schema.get("type")

    if typ == "string":
        frmt = schema.get("format")

        if frmt is None:
            if name in PARAMETER_DEFAULTS:
                return PARAMETER_DEFAULTS[name]
            return typ
        if frmt == "date":
            return datetime.date.today().isoformat()
        if frmt == "date-time":
            return datetime.date.today().isoformat()
        if frmt == "json-string":
            return "{}"
        if frmt == "binary":
            return ""

    if typ == "array":
        return []

    if typ == "integer":
        return 42

    if typ == "number":
        return 3.14

    if typ == "boolean":
        return False

    raise ValueError(f"Unsupported JSON schema: {schema}")


def _prepare_http_request(openapi_schema, path, method):
    # Look up schema for endpoint
    schema = openapi_schema["paths"].get(path, {}).get(method.lower())
    assert schema, f"Not in schema, endpoint doesn't exist? {method} {path}"
    parameters = schema.get("parameters") or []

    # Fake required path and query parameters, and required request payload
    path_parameters = _mk_required_parameters(parameters, where="path")

    query_parameters = _mk_required_parameters(parameters, where="query")

    content_type, payload = _mk_required_body_payload(
        schema, openapi_schema["components"]["schemas"]
    )
    is_json = _content_type_is_json(content_type)

    return path_parameters, query_parameters, payload, is_json, content_type


def _assert_insufficient_roles_error(
    required_roles, roles_in_token, response: httpx.Response
):
    """Asserts error response because of insufficient roles"""
    # pylint: disable=unused-variable
    __tracebackhide__ = True

    assert response.status_code == 403, (
        f"Expected `403 Unauthorized` response to http request with Bearer token with insufficient roles. \n"
        f"Required roles: {required_roles} \n"
        f"Roles sent in the Bearer token: {roles_in_token} \n"
        f"Actual response: {response.status_code}: {response.json()} \n"
    )

    payload = response.json()
    message = payload.get("message") or ""
    assert (
        "following roles" in message.lower()
    ), f"Actual response: {response.status_code}: {response.json()} \n"
