from dataclasses import dataclass

from authlib.jose import JWTClaims
from pydantic import BaseModel, field_validator

from common.exceptions import ForbiddenException

AUTHORIZATION_ERROR_CODES = {
    "invalid_request",
    "unauthorized_client",
    "access_denied",
    "unsupported_response_type",
    "invalid_scope",
    "server_error",
    "temporarily_unavailable",
    # OpenID Connect Core 1.0
    "login_required",
    "interaction_required",
    # https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow#error-codes-for-authorization-endpoint-errors
    "invalid_resource",
}


class JWTTokenClaims(BaseModel):
    """ID Token claims -- as per OpenID Connect 1.0 specification"""

    # RFC-7519 defines them optional, but mandated by OpenID Connect Core 1.0 for id-tokens (except nbf and jti)
    iss: str
    sub: str
    aud: list[str]
    exp: int
    nbf: int | None = None
    iat: int
    jti: str | None = None

    # RFC-8693 #4.2 common for both id and access token
    scp: list[str] | None = None

    @field_validator("aud", "scp", mode="before")
    # pylint: disable=no-self-argument
    def split_str(cls, elm):
        """Splits claim space-separated-string into a list of str elements"""
        if isinstance(elm, str):
            return elm.split()
        return elm


class AccessTokenClaims(JWTTokenClaims):
    """Access token claims"""

    roles: set[str] | None = None

    # OpenID Connect Core 1.0 Standard Claims
    name: str | None = None
    preferred_username: str | None = None
    email: str | None = None
    email_verified: bool | None = None

    # Seen in Active Directory tokens
    username: str | None = None
    oid: str | None = None
    tid: str | None = None

    azp: str | None = None


@dataclass(init=False)
class User:
    sub: str
    azp: str
    oid: str
    name: str
    username: str
    email: str
    roles: set[str]

    def __init__(
        self,
        sub: str,
        azp: str,
        oid: str,
        name: str,
        username: str,
        email: str,
        roles: set[str] | None = None,
    ) -> None:
        if roles is None:
            roles = {}

        self.sub = sub
        self.azp = azp
        self.oid = oid
        self.name = name
        self.username = username
        self.email = email
        self.roles = roles

    # pylint: disable=invalid-name
    def id(self):
        """Returns the user id

        For end-users, it is the `oid` claim from the access token.
        For applications authenticated with client secret, it is the `azp` claim from the access token.
        """
        return self.oid or self.azp

    def has_role(self, role: str) -> bool:
        """
        Checks if the user has the specified role.

        Args:
            role (str): The role to check.

        Returns:
            bool: True if the user has the specified role, False otherwise.
        """
        return role in self.roles

    def has_roles(self, *roles: tuple[str], has_all: bool = True) -> bool:
        """
        Checks if the user has any or all of the specified roles.

        Args:
            *roles (tuple[str]): The roles to check.
            has_all (bool): Optional. If True, checks if the user has all of the specified roles.
            If False, checks if the user has any of the specified roles.
            Default is True.

        Returns:
            bool: True if the user has all specified roles (if `has_all` is True)
            or at least one of the specified roles (if `has_all` is False), False otherwise.
        """
        if has_all:
            return all(self.has_role(role) for role in roles)

        return any(self.has_role(role) for role in roles)

    def hasnt_role(self, role: str) -> bool:
        """
        Checks if the user doesn't have the specified role.

        Args:
            role (str): The role to check.

        Returns:
            bool: True if the user doesn't have the specified role, False otherwise.
        """
        return not self.has_role(role)

    def hasnt_roles(self, *roles: tuple[str], hasnt_any: bool = True) -> bool:
        """
        Checks if the user doesn't have any or doesn't have at least one of the specified roles.

        Args:
            *roles (tuple[str]): The roles to check.
            hasnt_any (bool): Optional. If True, checks if the user doesn't have any of the specified roles.
            If False, checks if the user doesn't have at least one of the specified roles.
            Default is True.

        Returns:
            bool: True if the user doesn't have any of the specified roles (if `hasnt_any` is True)
            or doesn't have at least one of the specified roles (if `hasnt_any` is False), False otherwise.

        """
        if hasnt_any:
            return all(self.hasnt_role(role) for role in roles)

        return any(self.hasnt_role(role) for role in roles)

    def has_only_role(self, role: str) -> bool:
        """
        Checks if the user has only the specified role.

        Args:
            role (str): The role to check.

        Returns:
            bool: True if the user has only the specified role, False otherwise.

        """
        return {role} == self.roles

    def has_only_roles(self, *roles: tuple[str]) -> bool:
        """
        Checks if the user has only the specified roles.

        Args:
            *roles (tuple[str]): The roles to check.

        Returns:
            bool: True if the user has only the specified roles, False otherwise.

        """
        return set(roles) == self.roles

    def authorize(self, *roles: tuple[str], has_all: bool = False) -> bool:
        """
        Authorizes the user based on the specified roles.

        Args:
            *roles (tuple[str]): The roles required for authorization.
            has_all (bool): Optional. If True, requires the user to have all specified roles for authorization.
            If False, requires the user to have at least one of the specified roles.
            Default is False.

        Returns:
            bool: True if the user is authorized based on the specified roles, False otherwise.

        Raises:
            ForbiddenException: If the user is not authorized, raises a ForbiddenException with a message indicating which roles are required.

        """
        if self.has_roles(*roles, has_all=has_all):
            return True

        raise ForbiddenException(
            msg=(
                f"At least one of the following roles is required: {list(roles)}"
                if not has_all
                else f"Following roles are required: {list(roles)}"
            )
        )


class Auth:
    user: User
    jwt_claims: JWTClaims
    access_token_claims: AccessTokenClaims

    def __init__(self, jwt_claims: JWTClaims, access_token_claims: AccessTokenClaims):
        self.user = User(
            sub=access_token_claims.sub,
            azp=access_token_claims.azp,
            oid=access_token_claims.oid,
            name=access_token_claims.name,
            username=access_token_claims.preferred_username,
            email=access_token_claims.preferred_username,
            roles=access_token_claims.roles,
        )
        self.jwt_claims = jwt_claims
        self.access_token_claims = access_token_claims
