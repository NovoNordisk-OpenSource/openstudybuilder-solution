"""Helpers for crafting JWTs in auth tests"""

import time
from collections.abc import Iterable, Mapping
from typing import Any

from authlib.jose import Key, jwt

# Obvious test-only UUIDs — never produced by `uuidgen` — so a stray match
# in a log or a leaked token is recognisable as a unit-test fixture.
ISSUER = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
GOOD_AUDIENCE = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

JWT_SIGN_ALG = "RS256"

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


def mk_claims(
    now: float | None = None,
    exp: float = 300,
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
