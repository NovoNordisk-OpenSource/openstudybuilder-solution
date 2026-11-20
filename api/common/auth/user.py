import logging

from cachetools import TTLCache, cached
from neo4j.exceptions import Forbidden
from neomodel import db
from starlette_context import context

from common.auth.models import Auth, User

cache_persist_user: TTLCache = TTLCache(maxsize=1000, ttl=10)

log = logging.getLogger(__name__)


def auth() -> Auth:
    """Retrieves authentication-related information from the request context as Auth object."""

    return context.get("auth")


def user() -> User:
    """Retrieves user information as User object, member of the Auth object in the request context."""

    return auth().user


def transaction_metadata() -> dict[str, str]:
    """Neo4j transaction metadata identifying the user of the current request.

    Empty outside a request, or before the request is authenticated. Holds the user id
    only: it shows up in Neo4j's query log and monitoring, so it must not carry PII.
    """

    if not context.exists() or not (auth_info := context.get("auth")):
        return {}

    user_id = auth_info.user.id()
    return {"user_id": user_id} if user_id else {}


@cached(cache=cache_persist_user, key=lambda user_info: user_info.id())
def persist_user(user_info: User):
    """Persists user information in the database."""

    log.info("Persisting user %s", user_info)
    query = """
        MERGE (u:User {user_id: $id})
        ON CREATE
            SET u.created = datetime(),
                u.oid = $oid,
                u.azp = $azp,
                u.username = $username,
                u.name = $name,
                u.email = $email,
                u.roles = $roles
        ON MATCH
            SET u.updated = datetime(),
                u.oid = $oid,
                u.azp = $azp,
                u.username = COALESCE($username, u.username),
                u.name = $name,
                u.email = $email,
                u.roles = $roles
        """
    params = {
        "id": user_info.id(),
        "oid": user_info.oid,
        "azp": user_info.azp,
        "username": user_info.username,
        "name": user_info.name,
        "email": user_info.email,
        "roles": list(user_info.roles),
    }
    try:
        db.cypher_query(
            query=query,
            params=params,
        )
    except Forbidden:
        log.exception("Error persisting user %s", user_info)


def clear_users_cache():
    cache_persist_user.clear()
    log.info("Users cache cleared")
