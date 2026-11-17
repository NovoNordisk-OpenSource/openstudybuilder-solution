"""RBAC checks shared by the `test_endpoints_rbac.py` modules of all three apps.

Each app parametrizes its tests over its own routes table and calls the `assert_rbac_*`
helpers below, passing in its own `PARAMETER_DEFAULTS`. Tokens are self-signed by
a mock `JWKService`, which the caller must monkeypatch in as
`common.auth.dependencies.jwks_service`.
"""

import datetime
import logging
import random
import uuid
from collections.abc import Callable, Iterable, Mapping
from typing import Any, NamedTuple

import httpx

from common.auth.dependencies import oidc_client
from common.auth.jwk_service import JWKService
from common.tests.auth.tokens import mk_claims, mk_jwt

log = logging.getLogger(__name__)

KNOWN_ROLES = {
    "Admin.Read",
    "Admin.Write",
    "Library.Read",
    "Library.Write",
    "Study.Read",
    "Study.Write",
}

IRRELEVANT_ROLES = ["Some, Fake", "Testing", ""]

# A response with any of these status codes has passed authentication and RBAC
PASSED_AUTH_STATUS_CODES = (200, 201, 204, 207, 400, 404)

# Error types accepted on a 400 response to a request with correct roles
ALLOWED_BAD_REQUEST_TYPES = (
    "BusinessLogicException",
    "RequestValidationError",
    "ValidationException",
    "ValidationError",
    "ValueError",
)

TokenFactory = Callable[..., str]


class PreparedRequest(NamedTuple):
    method: str
    path: str
    path_parameters: dict[str, Any]
    query_parameters: dict[str, Any]
    payload: Any
    is_json: bool
    content_type: str | None


class MockJWKService(JWKService):
    """A JWKService with a single audience, which is also the issuer of its tokens"""

    audience: str


def mk_mock_jwks_service() -> MockJWKService:
    """A JWKService with a generated key for self-signed tokens"""
    jwks_service = MockJWKService(oidc_client, audience=str(uuid.uuid4()))
    jwks_service.claims_options["aud"] = {"values": [jwks_service.audience]}
    jwks_service.claims_options["iss"] = {"values": [jwks_service.audience]}
    jwks_service.generate_key()
    return jwks_service


def mk_token_factory(jwks_service: MockJWKService) -> TokenFactory:
    """Returns `factory(roles=None)` building a token signed by `jwks_service`"""
    key = next(iter(jwks_service.keys.values()))

    def factory(roles: list[str] | None = None) -> str:
        claims = mk_claims(audience=jwks_service.audience, issuer=jwks_service.audience)

        if roles:
            claims["roles"] = list(roles)

        token = mk_jwt(claims, key)
        return token.decode("utf-8")

    return factory


def assert_rbac_wrong_roles(
    api_client,
    openapi_schema,
    mk_token: TokenFactory,
    path: str,
    method: str,
    required_roles: Iterable[str],
    parameter_defaults: Mapping[str, Any],
):
    """Asserts that requests with tokens carrying only wrong roles are rejected"""

    __tracebackhide__ = True

    request = prepare_http_request(openapi_schema, path, method, parameter_defaults)

    required_roles = list(required_roles)
    invalid_roles = _invalid_roles(required_roles)
    assert invalid_roles, "Can not run test with only valid roles"

    # Some insufficient combination of roles
    random.shuffle(invalid_roles)
    insufficient_role_sets = [invalid_roles]
    for _ in range(max(len(invalid_roles) - 1, 3)):
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

    for roles in insufficient_role_sets:
        response = do_request_with_token(api_client, mk_token(roles=roles), request)
        assert_insufficient_roles_error(required_roles, roles, response)


def assert_rbac_correct_roles(
    api_client,
    openapi_schema,
    mk_token: TokenFactory,
    path: str,
    method: str,
    required_roles: Iterable[str],
    parameter_defaults: Mapping[str, Any],
    passed_auth_status_codes: Iterable[int] = PASSED_AUTH_STATUS_CODES,
):
    """Asserts that requests with tokens carrying any of the required roles pass RBAC"""

    __tracebackhide__ = True

    request = prepare_http_request(openapi_schema, path, method, parameter_defaults)

    required_roles = list(required_roles)
    invalid_roles = _invalid_roles(required_roles)

    # Some valid combinations of roles (any of the required roles are sufficient for access)
    valid_role_sets = []
    for i in range(len(required_roles)):
        roles = random.choices(required_roles, k=i + 1)
        valid_role_sets += [
            roles,
            [*required_roles, random.choice(invalid_roles)],
            required_roles
            + random.choices(invalid_roles, k=random.randint(1, len(invalid_roles))),
        ]

    passed_auth_status_codes = tuple(passed_auth_status_codes)

    # If response status code is different than 401/403, we assume that authentication has passed
    for roles in valid_role_sets:
        response = do_request_with_token(api_client, mk_token(roles=roles), request)
        assert response.status_code in passed_auth_status_codes, (
            f"Expected HTTP status code in [{', '.join(map(str, passed_auth_status_codes))}] "
            f"for {response.request.method} {response.request.url}\n"
            f"Actual response: {response.status_code} {response.reason_phrase}: {response.text[:1024]}"
        )

        if response.status_code == 400:
            error = response.json()
            assert (error.get("type") or "") in ALLOWED_BAD_REQUEST_TYPES


def assert_rbac_no_roles(
    api_client,
    openapi_schema,
    mk_token: TokenFactory,
    path: str,
    method: str,
    required_roles: Iterable[str],
    parameter_defaults: Mapping[str, Any],
):
    """Asserts that a request with a token carrying no role claims is rejected"""

    __tracebackhide__ = True

    request = prepare_http_request(openapi_schema, path, method, parameter_defaults)

    response = do_request_with_token(api_client, mk_token(), request)
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
    assert_insufficient_roles_error(list(required_roles), [], response)


def do_request_with_token(
    api_client, token: str, request: PreparedRequest
) -> httpx.Response:
    headers = {"Authorization": f"Bearer {token}"}
    if request.content_type:
        headers["Content-Type"] = request.content_type

    url = request.path.format_map(request.path_parameters)
    log.debug(
        "\n%s %s %s\n%s\n", request.method, url, request.query_parameters, headers
    )

    return api_client.request(
        request.method,
        url,
        params=request.query_parameters,
        json=request.payload if request.is_json else None,
        data=None if request.is_json else request.payload,
        headers=headers,
    )


def prepare_http_request(
    openapi_schema, path: str, method: str, parameter_defaults: Mapping[str, Any]
) -> PreparedRequest:
    """Fakes the required parameters and payload of an endpoint from its OpenAPI schema"""

    schema = openapi_schema["paths"].get(path, {}).get(method.lower())
    assert schema, f"Not in schema, endpoint doesn't exist? {method} {path}"
    parameters = schema.get("parameters") or []

    content_type, payload = _mk_required_body_payload(
        schema, openapi_schema["components"]["schemas"], parameter_defaults
    )

    return PreparedRequest(
        method=method,
        path=path,
        path_parameters=_mk_required_parameters(parameters, "path", parameter_defaults),
        query_parameters=_mk_required_parameters(
            parameters, "query", parameter_defaults
        ),
        payload=payload,
        is_json=_content_type_is_json(content_type),
        content_type=content_type,
    )


def assert_insufficient_roles_error(
    required_roles, roles_in_token, response: httpx.Response
):
    """Asserts error response because of insufficient roles"""

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


def _invalid_roles(required_roles: list[str]) -> list[str]:
    return list(KNOWN_ROLES - set(required_roles)) + IRRELEVANT_ROLES


def _mk_required_parameters(parameters, where, parameter_defaults):
    params = {}
    for param in parameters:
        if param.get("required") and param.get("in") == where:
            name = param.get("name")
            params[name] = param.get("schema", {}).get(
                "default", parameter_defaults.get(name, f"MISSING__{name}")
            )
    return params


def _mk_required_body_payload(schema, openapi_schemas, parameter_defaults):
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

    payload = _mk_schema_example_payload(schema, openapi_schemas, parameter_defaults)

    return content_type, payload


def _content_type_is_json(content_type):
    return content_type and "/" in content_type and content_type.split("/")[1] == "json"


def _mk_schema_example_payload(schema, openapi_schemas, parameter_defaults):
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
                payload[name] = _mk_schema_example_payload(
                    schem, openapi_schemas, parameter_defaults
                )
            elif schem.get("anyOf"):
                payload[name] = _mk_schema_example_payload(
                    schem["anyOf"][0], openapi_schemas, parameter_defaults
                )
            elif schem.get("allOf"):
                payload[name] = {}
                for schem_ in schem["allOf"]:
                    payload[name].update(
                        _mk_schema_example_payload(
                            schem_, openapi_schemas, parameter_defaults
                        )
                    )
            else:
                payload[name] = _schema_default_value(schem, parameter_defaults, name)

    if is_array:
        return [payload]

    return payload


def _schema_default_value(schema, parameter_defaults, name=None):
    if "default" in schema:
        return schema["default"]

    typ = schema.get("type")
    sentinel = object()
    default_value = sentinel

    if typ == "string":
        frmt = schema.get("format", "").lower()

        if not frmt or frmt in {"html", "password"}:
            default_value = parameter_defaults.get(name, typ)
        elif frmt in {"date", "date-time"}:
            default_value = datetime.date.today().isoformat()
        elif frmt == "json-string":
            default_value = "{}"
        elif frmt == "binary":
            default_value = ""
    elif typ == "array":
        default_value = []
    elif typ == "integer":
        default_value = 42
    elif typ == "number":
        default_value = 3.14
    elif typ == "boolean":
        default_value = False

    if default_value is sentinel:
        raise ValueError(f"Unsupported JSON schema: {schema}")

    return default_value
