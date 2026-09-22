import logging

from cachetools import TTLCache, cached
from neo4j.exceptions import Forbidden
from neomodel import db
from starlette_context import context

from common.auth.models import Auth, User

cache_persist_user = TTLCache(maxsize=1000, ttl=10)

log = logging.getLogger(__name__)


def auth() -> Auth:
    """Retrieves authentication-related information from the request context as Auth object."""

    return context.get("auth")


def user() -> User:
    """Retrieves user information as User object, member of the Auth object in the request context."""

    return auth().user


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
    except Forbidden as e:
        log.error("Error persisting user %s: %s", user_info, e)


def clear_users_cache():
    cache_persist_user.clear()
    log.info("Users cache cleared")
