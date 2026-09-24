import logging
from typing import Annotated

from authlib.integrations.starlette_client import OAuth
from authlib.jose.errors import JoseError
from authlib.jose.rfc7519.claims import JWTClaims
from fastapi import Depends, Security
from fastapi.security import OAuth2AuthorizationCodeBearer
from opencensus.trace import execution_context
from opencensus.trace.tracer import Tracer
from pydantic import ValidationError
from starlette_context import context

from common.auth.jwk_service import JWKService
from common.auth.models import AccessTokenClaims, Auth, User
from common.auth.user import persist_user, user
from common.config import settings
from common.exceptions import NotAuthenticatedException

log = logging.getLogger(__name__)

oauth = OAuth()
oidc_client = oauth.register(
    "default",
    server_metadata_url=settings.oauth_metadata_url,
)

jwks_service = JWKService(
    oidc_client,
    audience=settings.oauth_api_app_id,
    leeway_seconds=settings.jwt_leeway_seconds,
)

oauth_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="", tokenUrl="", scopes=settings.our_scopes
)


async def validate_token(token: Annotated[str, Depends(oauth_scheme)]):
    """
    Decodes and validates JWT token claims.

    Args:
        security_scopes (SecurityScopes): The security scopes required for the request.
        request (Request): The request object.
        token (str): The JWT access token.

    Returns:
        AccessTokenClaim: The decoded and validated JWT token claims.

    Raises:
        NotAuthenticatedException: If the token is invalid.
        ValidationError: If the JWT claims are invalid.
    """
    try:
        jwt_claims = await jwks_service.validate_jwt(token)

    except JoseError as exc:
        log.info("%s: %s", exc.error, exc.description)
        raise NotAuthenticatedException(
            f"Token validation error: {exc.description or exc.error}"
        ) from exc

    except ValidationError as exc:
        log.info(str(exc))
        raise NotAuthenticatedException("Model validation error") from exc

    access_token_claims = AccessTokenClaims.model_validate(jwt_claims)

    # Attributes to current tracing span
    tracer: Tracer = execution_context.get_opencensus_tracer()
    tracer.add_attribute_to_current_span(
        "ai.user.authUserId", access_token_claims.preferred_username
    )
    tracer.add_attribute_to_current_span(
        "ai.user.accountId", access_token_claims.oid or access_token_claims.sub
    )
    tracer.add_attribute_to_current_span("ai.device.id", access_token_claims.azp)

    # Save to context
    context["auth"] = Auth(
        jwt_claims=jwt_claims, access_token_claims=access_token_claims
    )

    persist_user(user_info=user())


def dummy_user_test_auth(user_id: str = "unknown-user"):
    """
    Sets context Auth object with dummy data when running tests.

    Returns:
        None

    Raises:
        Any exceptions raised during token validation.
    """

    context["auth"] = dummy_auth_object(dummy_access_token_claims(user_id=user_id))
    persist_user(user_info=user())


def dummy_user_auth():
    """
    Sets context Auth object with dummy data when authentication is disabled.

    Returns:
        None

    Raises:
        Any exceptions raised during token validation.
    """

    context["auth"] = dummy_auth_object(
        dummy_access_token_claims(user_id=settings.dummy_user_id)
    )
    persist_user(user_info=user())


if settings.oauth_rbac_enabled:

    class RequiresAnyRole:
        """
        Dependency checks that ANY of the required roles is present in the access token claims.

        Args:
            roles: A set of roles required for the request.
        """

        def __init__(self, roles: set[str]):
            self.required_roles = roles

        def __call__(self):
            user().authorize(*self.required_roles)

else:
    log.warning(
        "WARNING: Role-Based Access Control is disabled. "
        "See OAUTH_ENABLED and OAUTH_RBAC_ENABLED environment variables."
    )

    # pylint: disable=unused-argument
    class RequiresAnyRole:  # type: ignore[no-redef]
        def __init__(self, roles):
            # An empty method to keep instantiation compatible with disabled functionality
            pass

        def __call__(self):
            pass


def dummy_user(roles: set[str] | None = None, user_id: str = "unknown-user") -> User:
    """Returns User object with dummy data"""

    return User(
        sub="xyz",
        azp=user_id,
        oid=user_id,
        name="John Smith",
        username=f"{user_id}@example.com",
        email=f"{user_id}@example.com",
        roles=roles
        or {
            "Admin.Read",
            "Admin.Write",
            "Study.Read",
            "Study.Write",
            "Library.Write",
            "Library.Read",
        },
    )


def dummy_access_token_claims(user_id: str = "unknown-user") -> AccessTokenClaims:
    """Returns AccessTokenClaims with dummy user data"""

    fake_user = dummy_user(user_id=user_id)

    return AccessTokenClaims(
        oid=fake_user.oid,
        azp=fake_user.azp,
        iss="fake",
        aud=["fake"],
        exp=0,
        nbf=0,
        iat=0,
        jti=None,
        sub=fake_user.sub,
        name=fake_user.name,
        username=fake_user.username,
        preferred_username=fake_user.email,
        email=fake_user.email,
        roles=fake_user.roles,
    )


def dummy_auth_object(access_token_claims: AccessTokenClaims) -> Auth:
    """Auth object factory from AccessTokenClaims"""

    return Auth(
        jwt_claims=JWTClaims(
            {
                "iss": access_token_claims.iss,
                "sub": access_token_claims.sub,
                "aud": access_token_claims.aud,
                "exp": access_token_claims.exp,
                "nbf": access_token_claims.nbf,
                "iat": access_token_claims.iat,
                "jti": access_token_claims.jti,
                "name": access_token_claims.name,
                "username": access_token_claims.username,
                "preferred_username": access_token_claims.email,
                "roles": access_token_claims.roles,
            },
            {},
        ),
        access_token_claims=access_token_claims,
    )


if settings.oauth_enabled:
    security = Security(validate_token)
else:
    security = Security(dummy_user_auth)
    log.warning(
        "WARNING: Authentication is disabled. "
        "See OAUTH_ENABLED and OAUTH_RBAC_ENABLED environment variables."
    )
