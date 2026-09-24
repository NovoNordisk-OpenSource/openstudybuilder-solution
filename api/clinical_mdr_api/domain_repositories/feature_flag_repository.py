"""Persistence helpers for feature flag Root/Value objects."""

# pylint: disable=invalid-name
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.models.feature_flag import FeatureFlagRoot
from clinical_mdr_api.models.feature_flag import FeatureFlag, FeatureFlagInput
from clinical_mdr_api.services.user_info import UserInfoService
from common.exceptions import NotFoundException
from common.utils import convert_to_datetime

_RETURN_PROJECTION = """
                root.uid AS uid,
                value.section AS section,
                value.feature AS feature,
                value.name AS name,
                value.enabled AS enabled,
                value.description AS description,
                hv.start_date AS start_date,
                hv.end_date AS end_date,
                hv.status AS status,
                hv.version AS version,
                hv.change_description AS change_description,
                hv.author_id AS author_id
"""


class FeatureFlagRepository:
    """Read and write feature flags in Neo4j."""

    def _row_to_model(self, row: dict[str, Any]) -> FeatureFlag:
        author_id = row.get("author_id")
        return FeatureFlag(
            uid=row["uid"],
            section=row["section"],
            feature=row["feature"],
            name=row["name"],
            enabled=row["enabled"],
            description=row.get("description"),
            start_date=convert_to_datetime(row.get("start_date")),
            end_date=convert_to_datetime(row.get("end_date")),
            status=row.get("status"),
            version=row.get("version"),
            change_description=row.get("change_description"),
            author_username=(
                UserInfoService.get_author_username_from_id(author_id)
                if author_id
                else None
            ),
        )

    def _rows_to_models(
        self, rs: tuple[list[list[Any]], list[str]]
    ) -> list[FeatureFlag]:
        columns = rs[1]
        return [self._row_to_model(dict(zip(columns, record))) for record in rs[0]]

    def _bump_version(self, version: str) -> str:
        version_text = str(version or "1.0")
        major_text, _, minor_text = version_text.partition(".")

        try:
            major = int(major_text)
        except TypeError, ValueError:
            major = 1

        try:
            minor = int(minor_text)
        except TypeError, ValueError:
            minor = 0

        return f"{major}.{minor + 1}"

    def retrieve_all_feature_flags(
        self, include_retired: bool = False
    ) -> list[FeatureFlag]:
        """Return all current feature flags, optionally including retired ones."""
        status_filter = (
            "hv.status IN ['Final', 'Retired']"
            if include_retired
            else "hv.status = 'Final'"
        )
        rs = db.cypher_query(
            f"""
            MATCH (root:FeatureFlagRoot)-[:LATEST]->(value:FeatureFlagValue)
            MATCH (root)-[hv:HAS_VERSION]->(value)
            WHERE hv.end_date IS NULL AND {status_filter}
            RETURN
            {_RETURN_PROJECTION}
            ORDER BY root.uid
            """,
            resolve_objects=False,
        )
        return self._rows_to_models(rs)

    def find_feature_flag_by_name(self, name: str) -> FeatureFlag | None:
        """Return the current feature flag with the provided name, if any."""
        rs = db.cypher_query(
            f"""
            MATCH (root:FeatureFlagRoot)-[:LATEST]->(value:FeatureFlagValue {{name: $name}})
            MATCH (root)-[hv:HAS_VERSION]->(value)
            WHERE hv.end_date IS NULL
            RETURN
            {_RETURN_PROJECTION}
            """,
            params={"name": name},
            resolve_objects=False,
        )
        if not rs[0]:
            return None
        return self._rows_to_models(rs)[0]

    def retrieve_feature_flag(self, uid: str) -> FeatureFlag:
        """Return the current feature flag for the provided uid."""
        rs = db.cypher_query(
            f"""
            MATCH (root:FeatureFlagRoot {{uid: $uid}})-[:LATEST]->(value:FeatureFlagValue)
            MATCH (root)-[hv:HAS_VERSION]->(value)
            WHERE hv.end_date IS NULL
            RETURN
            {_RETURN_PROJECTION}
            """,
            params={"uid": uid},
            resolve_objects=False,
        )
        NotFoundException.raise_if_not(rs[0], "Feature Flag", uid)
        return self._rows_to_models(rs)[0]

    def create_feature_flag(
        self,
        feature_flag_input: FeatureFlagInput,
        author_id: str,
    ) -> FeatureFlag:
        """Create a new feature flag as Final version 1.0."""
        uid = FeatureFlagRoot.get_next_free_uid_and_increment_counter()
        rs = db.cypher_query(
            f"""
            CREATE (root:FeatureFlagRoot)
            SET root.uid = $uid
            CREATE (value:FeatureFlagValue)
            SET
                value.section = $section,
                value.feature = $feature,
                value.name = $name,
                value.enabled = $enabled,
                value.description = $description
            CREATE (root)-[:LATEST]->(value)
            CREATE (root)-[:LATEST_FINAL]->(value)
            CREATE (root)-[hv:HAS_VERSION {{
                version: '1.0',
                status: 'Final',
                start_date: datetime(),
                end_date: null,
                author_id: $author_id,
                change_description: $change_description
            }}]->(value)
            RETURN
            {_RETURN_PROJECTION}
            """,
            params={
                "uid": uid,
                "section": feature_flag_input.section,
                "feature": feature_flag_input.feature,
                "name": feature_flag_input.name,
                "enabled": feature_flag_input.enabled,
                "description": feature_flag_input.description,
                "author_id": author_id,
                "change_description": feature_flag_input.change_description
                or "Initial version",
            },
            resolve_objects=False,
        )
        return self._rows_to_models(rs)[0]

    def update_feature_flag(self, uid: str, author_id: str, **updates) -> FeatureFlag:
        """Create a new Final version for the feature flag with updated fields."""
        current = self.retrieve_feature_flag(uid)
        if not updates:
            return current

        change_description = updates.pop("change_description", None)
        section = updates.get("section", current.section)
        feature = updates.get("feature", current.feature)
        enabled = updates.get("enabled", current.enabled)
        name = current.name
        description = (
            updates["description"] if "description" in updates else current.description
        )
        new_version = self._bump_version(current.version or "1.0")

        rs = db.cypher_query(
            f"""
            MATCH (root:FeatureFlagRoot {{uid: $uid}})-[:LATEST]->(old_value:FeatureFlagValue)
            MATCH (root)-[old_hv:HAS_VERSION]->(old_value)
            WHERE old_hv.end_date IS NULL AND old_hv.status = 'Final'
            SET old_hv.end_date = datetime()
            WITH root
            OPTIONAL MATCH (root)-[lf:LATEST_FINAL]->()
            DELETE lf
            WITH root
            OPTIONAL MATCH (root)-[lv:LATEST]->()
            DELETE lv
            WITH root
            CREATE (value:FeatureFlagValue)
            SET
                value.section = $section,
                value.feature = $feature,
                value.name = $name,
                value.enabled = $enabled,
                value.description = $description
            CREATE (root)-[:LATEST]->(value)
            CREATE (root)-[:LATEST_FINAL]->(value)
            CREATE (root)-[hv:HAS_VERSION {{
                version: $version,
                status: 'Final',
                start_date: datetime(),
                end_date: null,
                author_id: $author_id,
                change_description: $change_description
            }}]->(value)
            RETURN
            {_RETURN_PROJECTION}
            """,
            params={
                "uid": uid,
                "section": section,
                "feature": feature,
                "name": name,
                "enabled": enabled,
                "description": description,
                "version": new_version,
                "author_id": author_id,
                "change_description": change_description
                or f"Updated to version {new_version}",
            },
            resolve_objects=False,
        )
        NotFoundException.raise_if_not(rs[0], "Feature Flag", uid)
        return self._rows_to_models(rs)[0]

    def inactivate_final(self, uid: str, author_id: str) -> FeatureFlag:
        """Mark the current Final feature flag version as Retired."""
        rs = db.cypher_query(
            f"""
            MATCH (root:FeatureFlagRoot {{uid: $uid}})-[:LATEST]->(value:FeatureFlagValue)
            MATCH (root)-[old_hv:HAS_VERSION]->(value)
            WHERE old_hv.end_date IS NULL AND old_hv.status = 'Final'
            SET old_hv.end_date = datetime()
            WITH root, value, old_hv
            OPTIONAL MATCH (root)-[lr:LATEST_RETIRED]->()
            DELETE lr
            WITH root, value, old_hv
            CREATE (root)-[:LATEST_RETIRED]->(value)
            CREATE (root)-[hv:HAS_VERSION {{
                version: old_hv.version,
                status: 'Retired',
                start_date: datetime(),
                end_date: null,
                author_id: $author_id,
                change_description: 'Inactivated'
            }}]->(value)
            RETURN
            {_RETURN_PROJECTION}
            """,
            params={"uid": uid, "author_id": author_id},
            resolve_objects=False,
        )
        NotFoundException.raise_if_not(rs[0], "Feature Flag", uid)
        return self._rows_to_models(rs)[0]

    def reactivate_retired(self, uid: str, author_id: str) -> FeatureFlag:
        """Reactivate the current Retired feature flag version as Final."""
        rs = db.cypher_query(
            f"""
            MATCH (root:FeatureFlagRoot {{uid: $uid}})-[:LATEST]->(value:FeatureFlagValue)
            MATCH (root)-[old_hv:HAS_VERSION]->(value)
            WHERE old_hv.end_date IS NULL AND old_hv.status = 'Retired'
            SET old_hv.end_date = datetime()
            WITH root, value, old_hv
            OPTIONAL MATCH (root)-[lf:LATEST_FINAL]->()
            DELETE lf
            WITH root, value, old_hv
            CREATE (root)-[:LATEST_FINAL]->(value)
            CREATE (root)-[hv:HAS_VERSION {{
                version: old_hv.version,
                status: 'Final',
                start_date: datetime(),
                end_date: null,
                author_id: $author_id,
                change_description: 'Reactivated'
            }}]->(value)
            RETURN
            {_RETURN_PROJECTION}
            """,
            params={"uid": uid, "author_id": author_id},
            resolve_objects=False,
        )
        NotFoundException.raise_if_not(rs[0], "Feature Flag", uid)
        return self._rows_to_models(rs)[0]

    def get_all_versions(self, uid: str) -> list[FeatureFlag]:
        """Return the full version history for the provided feature flag uid.

        Newest first, matching library_item_repository.get_all_versions. The
        order is load-bearing: calculate_diffs() diffs each entry against the
        following one, so fed oldest-first it credits every change to the
        version below the one that made it and leaves the newest with no diff
        at all.
        """
        rs = db.cypher_query(
            f"""
            MATCH (root:FeatureFlagRoot {{uid: $uid}})-[hv:HAS_VERSION]->(value:FeatureFlagValue)
            RETURN
            {_RETURN_PROJECTION}
            ORDER BY hv.start_date DESC
            """,
            params={"uid": uid},
            resolve_objects=False,
        )
        NotFoundException.raise_if_not(rs[0], "Feature Flag", uid)
        return self._rows_to_models(rs)
