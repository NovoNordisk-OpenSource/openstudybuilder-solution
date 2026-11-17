import time

import common.auth.dependencies
from common.tests.auth.endpoints_rbac import mk_mock_jwks_service
from common.tests.auth.tokens import mk_claims, mk_jwt


def assert_global_security_requires_auth(
    main_app_all_route_paths, api_client, skip_paths
):
    for path, methods in main_app_all_route_paths:
        if path in skip_paths:
            continue

        for method in methods:
            response = api_client.request(method, path)
            assert response.status_code == 401, f"Bad status code for {method} {path}"


def assert_global_security_rejects_expired_token(
    main_app_all_route_paths, api_client, skip_paths, monkeypatch
):
    """Asserts that every route rejects a correctly signed but expired token with 401

    The token is self-signed by the mock JWKS service, so this covers expiry handling
    in the global security dependency of each route. It does not cover tokens issued
    by a real identity provider; JWT validation itself is covered in
    `common/tests/auth/unit/test_jwk_service.py`.
    """
    jwks_service = mk_mock_jwks_service()
    key = next(iter(jwks_service.keys.values()))
    # Expired by a margin beyond the leeway, so it stays rejected if the leeway changes
    claims = mk_claims(
        exp=-(jwks_service.leeway + 60),
        audience=jwks_service.audience,
        issuer=jwks_service.audience,
    )
    assert (
        claims["exp"] + jwks_service.leeway < time.time()
    ), "Test setup error: token is not expired"
    expired_access_token = mk_jwt(claims, key).decode("utf-8")
    monkeypatch.setattr(common.auth.dependencies, "jwks_service", jwks_service)

    for path, methods in main_app_all_route_paths:
        if path in skip_paths:
            continue

        for method in methods:
            response = api_client.request(
                method,
                path,
                headers={"Authorization": f"Bearer {expired_access_token}"},
            )
            assert response.status_code == 401, (
                f"Bad status code {response.status_code} for {method} {path}"
                f" \n{response.text[:1024]}"
            )
