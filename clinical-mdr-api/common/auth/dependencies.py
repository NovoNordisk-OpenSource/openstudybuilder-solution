import logging
from typing import Annotated

from authlib.integrations.starlette_client import OAuth
from authlib.jose.errors import JoseError
from authlib.jose.rfc7519.claims import JWTClaims
from fastapi import Depends
from fastapi.security import OAuth2AuthorizationCodeBearer
from opencensus.trace import execution_context
from opencensus.trace.tracer import Tracer
from pydantic import ValidationError
from starlette_context import context

from common.auth import config
from common.auth.jwk_service import JWKService
from common.auth.models import AccessTokenClaims, Auth, User
from common.auth.user import persist_user, user
from common.exceptions import NotAuthenticatedException

log = logging.getLogger(__name__)

oauth = OAuth()
oidc_client = oauth.register(
    "default",
    server_metadata_url=config.OAUTH_METADATA_URL,
)

jwks_service = JWKService(
    oidc_client,
    audience=config.OAUTH_API_APP_ID,
    leeway_seconds=config.JWT_LEEWAY_SECONDS,
)

oauth_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=config.OAUTH_AUTHORIZATION_URL,
    tokenUrl=config.OAUTH_TOKEN_URL,
    scopes=config.OUR_SCOPES,
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


def dummy_user_auth():
    """
    Sets context Auth object with dummy data.

    Returns:
        None

    Raises:
        Any exceptions raised during token validation.
    """

    context["auth"] = dummy_auth_object(dummy_access_token_claims())
    persist_user(user_info=user())


if config.OAUTH_RBAC_ENABLED:

    class RequiresAnyRole:
        """
        Dependency checks that required roles are all present in the access token claims.

        Args:
            roles: A list of roles required for the request.
        """

        def __init__(self, roles: list[str]):
            self.required_roles = set(roles)

        def __call__(self):
            user().authorize(*self.required_roles)

else:
    log.warning(
        "WARNING: Role-Based Access Control is disabled. "
        "See OAUTH_ENABLED and OAUTH_RBAC_ENABLED environment variables."
    )

    # pylint: disable=unused-argument
    class RequiresAnyRole:
        def __init__(self, roles):
            # An empty method to keep instantiation compatible with disabled functionality
            pass

        def __call__(self):
            pass


def dummy_user(roles: set[str] | None = None) -> User:
    """Returns User object with dummy data"""

    return User(
        sub="xyz",
        azp="unknown-user",
        oid="unknown-user",
        name="John Smith",
        username="unknown-user@example.com",
        email="unknown-user@example.com",
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


def dummy_access_token_claims(fake_user_id: str | None = None) -> AccessTokenClaims:
    """Returns AccessTokenClaims with dummy user data"""

    fake_user = dummy_user()

    if fake_user_id:
        fake_user.email = f"{fake_user_id}@example.com"

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
