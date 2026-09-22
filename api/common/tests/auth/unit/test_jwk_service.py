"""Test JWT validation with crafted tokens signed with a test JWK"""

# pylint: disable=redefined-outer-name

import logging
import time
from typing import Any, Iterable, Mapping

import authlib.jose.errors
import pytest
from authlib.jose import JsonWebKey, Key, jwt

from common import exceptions
from common.auth.jwk_service import JWKService

# Obvious test-only UUIDs — never produced by `uuidgen` — so a stray match
# in a log or a leaked token is recognisable as a unit-test fixture.
ISSUER = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
GOOD_AUDIENCE = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
WRONG_AUDIENCE = "cccccccc-cccc-cccc-cccc-cccccccccccc"

JWK_SIGN_KEY_ID = "good-rsa-key"
JWT_SIGN_ALG = "RS256"

# RSA key-pairs used to sign / verify the JWTs in these tests are generated
# fresh per test session via `JsonWebKey.generate_key` — see the `jwk_good_key`
# / `jwk_wrong_key` fixtures below. No private key material is committed.
JWK_RSA_KEY_SIZE = 2048

SCOPES = ("API.call",)

# Payload is similar to what Azure Active Directory provides, but the IDs are random-generated
CLAIMS_TEMPLATE = (
    ("aud", GOOD_AUDIENCE),
    ("iss", ISSUER),
    ("iat", 0),
    ("nbf", 0),
    ("exp", 0),
    # The opaque-string claims below (aio, rh, sub, uti) mimic the *shape* of
    # what Azure AD emits but carry no real values — replaced with obvious
    # test placeholders so a stray hit in a log isn't mistaken for a leak.
    ("aio", "test-aio-opaque-value"),
    ("azp", ISSUER),
    ("azpacr", "1"),
    ("name", "Test User 42"),
    ("oid", "dddddddd-dddd-dddd-dddd-dddddddddddd"),
    ("preferred_username", "testuser42@example.invalid"),
    ("rh", "test-rh-opaque-value"),
    ("scp", " ".join(SCOPES)),
    ("sub", "test-sub-opaque-value"),
    ("tid", "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
    ("uti", "test-uti-opaque-value"),
    ("ver", "2.0"),
)

log = logging.getLogger(__name__)


def _generate_jwk(kid: str) -> dict[str, Any]:
    """Generate a fresh RSA signing JWK for the test session.

    Avoids committing PEM-encoded private keys to the repo (secret scanner
    flags them, even though they were random fixtures never used outside
    these unit tests).
    """
    key = dict(JsonWebKey.generate_key("RSA", JWK_RSA_KEY_SIZE, is_private=True))
    key["kid"] = kid
    key["use"] = "sig"
    key["issuer"] = ISSUER
    return key


@pytest.fixture(scope="session")
def jwk_good_key():
    return _generate_jwk("good-rsa-key")


@pytest.fixture(scope="session")
def jwk_wrong_key():
    return _generate_jwk("wrong-rsa-key")


@pytest.fixture(scope="session")
def jwk_service(jwk_good_key):
    oauth_client = MockOauthClient(
        metadata={
            "issuer": ISSUER,
            "jwks_uri": "fetch_jwk_set is monkey patched",
        }
    )

    log.debug("Creating JWKService with MockOauthClient")
    service = JWKService(oauth_client, audience=GOOD_AUDIENCE)

    log.debug("Patching JWKService._fetch_json() on instance")

    # pylint: disable=unused-argument
    async def return_jwks_doc(url):
        return {"keys": [jwk_good_key]}

    setattr(service, "_fetch_json", return_jwks_doc)

    return service


class MockOauthClient:
    """Mock OauthClient for clinical_mdr_api.auth.jwk_service.JWKService"""

    def __init__(self, metadata):
        self._metadata = metadata

    async def load_server_metadata(self):
        return self._metadata


def mk_claims(
    now: int | float | None = None,
    exp: int | float = 300,
    audience: str | None = GOOD_AUDIENCE,
    issuer: str | None = ISSUER,
    scopes: Iterable[str] = SCOPES,
) -> dict[str, Any]:
    if now is None:
        now = time.time()

    claims = dict(CLAIMS_TEMPLATE)
    claims["iat"] = int(now)
    claims["nbf"] = claims["iat"]
    claims["exp"] = int(now + exp)

    claims["aud"] = audience
    claims["iss"] = issuer
    claims["azp"] = claims["iss"]

    claims["scp"] = " ".join(scopes)

    return claims


def mk_jwt(claims: Mapping, key: Key) -> bytes:
    header = {"alg": JWT_SIGN_ALG}
    return jwt.encode(header, claims, key)


# pylint: disable=unused-argument
@pytest.mark.asyncio
async def test_correct_test_setup(jwk_service, jwk_good_key, jwk_wrong_key):
    """This tests if test setup is correct, other tests rely on this"""

    log.debug("Creating claims")
    claims_in = mk_claims()
    log.debug("Creating token from claims: %s", claims_in)
    token = mk_jwt(claims_in, jwk_good_key)

    log.info("Test JWT: %s", token)

    log.debug("Decoding JWT")
    claims = jwt.decode(token, jwk_good_key)
    assert claims == claims_in, "Claims doesn't match after encoding-decoding cycle"

    log.debug("Validating claims: %s", claims)
    claims.validate()

    log.debug("Same with wrong-key should work too")
    token = mk_jwt(claims_in, jwk_wrong_key)
    claims = jwt.decode(token, jwk_wrong_key)
    claims.validate()
    assert (
        claims == claims_in
    ), "Claims doesn't match after encoding-decoding cycle with wrong-key"


@pytest.mark.asyncio
async def test_good_signing_key(jwk_service, jwk_good_key):
    claims_in = mk_claims()
    token = mk_jwt(claims_in, jwk_good_key)
    claims = await jwk_service.validate_jwt(token)
    assert claims == claims_in, "Claims differ"


@pytest.mark.asyncio
async def test_wrong_signing_key(jwk_service, jwk_wrong_key):
    claims = mk_claims()
    token = mk_jwt(claims, jwk_wrong_key)
    with pytest.raises(exceptions.NotAuthenticatedException):
        # Expected to raise NotAuthenticatedException exception
        await jwk_service.validate_jwt(token)


@pytest.mark.asyncio
async def test_invalid_signature(jwk_service, jwk_good_key):
    claims = mk_claims()
    token: str | bytes | list[str]
    token = mk_jwt(claims, jwk_good_key)

    # change payload part of token #
    claims["scp"] += " God.Mode"
    token2 = mk_jwt(claims, jwk_good_key)
    payload2 = token2.decode("utf8").split(".", 2)[1]
    token = token.decode("utf8").split(".", 2)
    token[1] = payload2
    token = ".".join(token)

    with pytest.raises(authlib.jose.errors.BadSignatureError):
        await jwk_service.validate_jwt(token)


@pytest.mark.asyncio
async def test_token_expired(jwk_service, jwk_good_key):
    exp = 300
    now = time.time() - exp - jwk_service.leeway - 1
    claims = mk_claims(now=now, exp=exp)
    token = mk_jwt(claims, jwk_good_key)
    with pytest.raises(authlib.jose.errors.ExpiredTokenError):
        await jwk_service.validate_jwt(token)


@pytest.mark.asyncio
async def test_token_not_before(jwk_service, jwk_good_key):
    exp = 300
    claims = mk_claims(exp=exp)
    claims["nbf"] = int(time.time() + 60)
    token = mk_jwt(claims, jwk_good_key)
    with pytest.raises(authlib.jose.errors.InvalidTokenError, match="not valid yet"):
        await jwk_service.validate_jwt(token)


@pytest.mark.asyncio
async def test_token_invalid_audience(jwk_service, jwk_good_key):
    claims = mk_claims(audience="pink-panther")
    token = mk_jwt(claims, jwk_good_key)
    with pytest.raises(authlib.jose.errors.InvalidClaimError, match=r"\baud\b"):
        await jwk_service.validate_jwt(token)


@pytest.mark.asyncio
async def test_token_invalid_issuer(jwk_service, jwk_good_key):
    claims = mk_claims(issuer="pink-panther-social-club")
    token = mk_jwt(claims, jwk_good_key)
    with pytest.raises(authlib.jose.errors.InvalidClaimError, match=r"\biss\b"):
        await jwk_service.validate_jwt(token)
