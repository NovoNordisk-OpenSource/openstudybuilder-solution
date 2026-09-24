# pylint: disable=invalid-name
from typing import Any

from neomodel import db

# Importing node models registers them with neomodel for resolve_objects=True
from clinical_mdr_api.domain_repositories.models.preferences import (  # pylint: disable=unused-import
    GlobalPreferences,
    UserPreferences,
)
from clinical_mdr_api.domain_repositories.preferences_registry import (
    PREFERENCE_KEYS,
    PREFERENCES_BY_KEY,
)
from common.exceptions import NotFoundException


def _node_to_dict(node) -> dict[str, Any]:
    """Extract all preference keys from a neomodel node into a dict."""
    return {key: getattr(node, key) for key in PREFERENCE_KEYS}


class PreferencesRepository:
    def get_global_preferences(self) -> dict[str, Any]:
        """MERGE singleton GlobalPreferences node with defaults and return as dict."""
        on_create_parts = [f"gp.{key} = $default_{key}" for key in PREFERENCE_KEYS]
        on_match_parts = [
            f"gp.{key} = COALESCE(gp.{key}, $default_{key})" for key in PREFERENCE_KEYS
        ]
        params = {
            f"default_{key}": PREFERENCES_BY_KEY[key].default for key in PREFERENCE_KEYS
        }

        rs = db.cypher_query(
            f"""
            MERGE (gp:GlobalPreferences)
            ON CREATE SET
                {", ".join(on_create_parts)}
            ON MATCH SET
                {", ".join(on_match_parts)}
            RETURN gp
            """,
            params=params,
            resolve_objects=True,
        )

        if rs[0]:
            return _node_to_dict(rs[0][0][0])
        return {}

    def update_global_preferences(self, updates: dict[str, Any]) -> dict[str, Any]:
        """SET only provided fields on the GlobalPreferences singleton node."""
        set_clauses = []
        params = {}

        for key in PREFERENCE_KEYS:
            if key in updates:
                set_clauses.append(f"gp.{key} = ${key}")
                params[key] = updates[key]

        if not set_clauses:
            return self.get_global_preferences()

        set_clause = ", ".join(set_clauses)
        rs = db.cypher_query(
            f"""
            MATCH (gp:GlobalPreferences)
            SET {set_clause}
            RETURN gp
            """,
            params=params,
            resolve_objects=True,
        )

        if rs[0]:
            return _node_to_dict(rs[0][0][0])
        return {}

    def get_user_preferences(self, user_id: str) -> dict[str, Any] | None:
        """MATCH User node and its UserPreferences, return dict or None."""
        rs = db.cypher_query(
            """
            MATCH (u:User {user_id: $user_id})-[:HAS_PREFERENCES]->(up:UserPreferences)
            RETURN up
            """,
            params={"user_id": user_id},
            resolve_objects=True,
        )

        if rs[0]:
            return _node_to_dict(rs[0][0][0])
        return None

    def update_user_preferences(
        self, user_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        """MERGE relationship + UserPreferences node, SET fields."""
        set_clauses = []
        params: dict[str, Any] = {"user_id": user_id}

        global_preferences = self.get_global_preferences()

        for key in PREFERENCE_KEYS:
            if key in updates:
                set_clauses.append(f"up.{key} = ${key}")

                if updates[key] == global_preferences[key]:
                    params[key] = None
                else:
                    params[key] = updates[key]

        if not set_clauses:
            current = self.get_user_preferences(user_id)
            return current if current else {}

        set_clause = ", ".join(set_clauses)
        rs = db.cypher_query(
            f"""
            MATCH (u:User {{user_id: $user_id}})
            MERGE (u)-[:HAS_PREFERENCES]->(up:UserPreferences)
            SET {set_clause}
            RETURN up
            """,
            params=params,
            resolve_objects=True,
        )

        if not rs[0]:
            raise NotFoundException(msg=f"User with id '{user_id}' not found")
        return _node_to_dict(rs[0][0][0])

    def delete_user_preference_key(self, user_id: str, key: str) -> dict[str, Any]:
        """REMOVE single property from UserPreferences node."""
        if key not in PREFERENCE_KEYS:
            raise ValueError(f"Invalid preference key: {key}")

        rs = db.cypher_query(
            f"""
            MATCH (u:User {{user_id: $user_id}})-[:HAS_PREFERENCES]->(up:UserPreferences)
            REMOVE up.{key}
            RETURN up
            """,
            params={"user_id": user_id},
            resolve_objects=True,
        )

        if not rs[0]:
            raise NotFoundException(msg=f"User with id '{user_id}' not found")
        return _node_to_dict(rs[0][0][0])
