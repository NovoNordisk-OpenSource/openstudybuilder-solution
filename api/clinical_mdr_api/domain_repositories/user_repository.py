# pylint: disable=invalid-name
import json
from datetime import datetime

from cachetools import TTLCache, cached
from neomodel import db

from clinical_mdr_api.domain_repositories.models.user import User as UserNode
from clinical_mdr_api.models.user import UserInfo, UserInfoPatchInput


class UserRepository:
    cache_get_user = TTLCache(maxsize=1000, ttl=10)

    def _transform_to_model(self, item: UserNode) -> UserInfo:
        def extract_roles(roles: str) -> list[str]:
            if roles:
                return json.loads(roles.replace("'", '"'))
            return []

        return UserInfo(
            user_id=item.user_id,
            username=item.username,
            name=item.name,
            email=item.email,
            azp=item.azp,
            oid=item.oid,
            roles=extract_roles(item.roles),
            created=item.created,
            updated=item.updated,
        )

    def get_all_users(self) -> list[UserInfo]:
        rs = db.cypher_query(
            """
            MATCH (n:User)
            RETURN n
            ORDER BY n.username, n.user_id
            """,
            resolve_objects=True,
        )

        return [self._transform_to_model(item[0]) for item in rs[0]]

    def get_users_by_ids(self, ids: list[str]) -> list[UserInfo]:
        rs = db.cypher_query(
            """
            MATCH (n:User)
            WHERE n.user_id IN $ids
            RETURN n
            """,
            params={"ids": ids},
            resolve_objects=True,
        )

        return [self._transform_to_model(item[0]) for item in rs[0]]

    @cached(cache=cache_get_user, key=lambda _self, user_id: user_id)
    def get_user(self, user_id: str) -> UserInfo:
        rs = db.cypher_query(
            """
            MATCH (n:User {user_id: $id})
            RETURN n
            """,
            params={"id": user_id},
            resolve_objects=True,
        )

        if not rs[0]:
            return UserInfo(
                user_id=user_id,
                username=user_id,
                name="",
                email="",
                azp=None,
                oid=user_id,
                roles=[],
                created=datetime.now(),
                updated=None,
            )
        return self._transform_to_model(rs[0][0][0])

    def patch_user(self, user_id: str, payload: UserInfoPatchInput) -> UserInfo | None:
        rs = db.cypher_query(
            """
            MATCH (n:User {user_id: $id})
            SET n.username = COALESCE($username, n.username),
                n.email = COALESCE($email, n.email),
                n.name = COALESCE($name, n.name),
                n.updated = datetime()
            RETURN n
            """,
            params={
                "id": user_id,
                "username": payload.username,
                "email": payload.email,
                "name": payload.name,
            },
            resolve_objects=True,
        )

        if rs[0]:
            return self._transform_to_model(rs[0][0][0])
        return None
