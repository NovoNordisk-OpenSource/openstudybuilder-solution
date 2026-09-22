import datetime

from neomodel import db

from clinical_mdr_api.domain_repositories.models.generic import Library
from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    SponsorModelSchemaRoot,
    SponsorModelSchemaValue,
)
from clinical_mdr_api.domains.standard_data_models.sponsor_model_schema import (
    SponsorModelSchemaAR,
    SponsorModelSchemaVO,
)
from clinical_mdr_api.services.user_info import UserInfoService
from common.exceptions import BusinessLogicException


class SponsorModelSchemaRepository:
    """
    Persists and restores immutable Sponsor Model Schema versions.

    A schema version is uniquely identified by ``(library_name, schema_version)``.
    One :class:`SponsorModelSchemaRoot` exists per library (uid
    ``SponsorModelSchema_<library_name>``); each version is an immutable value node.
    """

    @staticmethod
    def _root_uid(library_name: str) -> str:
        return f"SponsorModelSchema_{library_name}"

    def _value_to_ar(
        self, library_name: str, value: SponsorModelSchemaValue
    ) -> SponsorModelSchemaAR:
        return SponsorModelSchemaAR.from_repository_values(
            schema_vo=SponsorModelSchemaVO.from_repository_values(
                library_name=library_name,
                schema_version=value.schema_version,
                schema=value.schema,
                content_hash=value.content_hash,
                author_id=value.author_id,
                author_username=UserInfoService.get_author_username_from_id(
                    value.author_id
                ),
                created=value.created,
            )
        )

    def get_by_version(
        self, library_name: str, schema_version: int
    ) -> SponsorModelSchemaAR | None:
        root = SponsorModelSchemaRoot.nodes.get_or_none(
            uid=self._root_uid(library_name)
        )
        if root is None:
            return None
        values = root.has_schema_version.filter(schema_version=schema_version)
        if not values:
            return None
        return self._value_to_ar(library_name, values[0])

    def get_all(self, library_name: str) -> list[SponsorModelSchemaAR]:
        root = SponsorModelSchemaRoot.nodes.get_or_none(
            uid=self._root_uid(library_name)
        )
        if root is None:
            return []
        return [
            self._value_to_ar(library_name, value)
            for value in sorted(
                root.has_schema_version.all(), key=lambda v: v.schema_version
            )
        ]

    @db.transaction
    def save(self, ar: SponsorModelSchemaAR) -> SponsorModelSchemaAR:
        """
        Create a new immutable schema version.

        Idempotency (identical re-publish) and conflict (differing content)
        are resolved by the service before calling this method; this method
        only ever performs a fresh create.
        """
        library_name = ar.library_name

        library = Library.nodes.get_or_none(name=library_name)
        BusinessLogicException.raise_if(
            library is None,
            msg=f"The library '{library_name}' doesn't exist.",
        )

        # Reuse-or-create the root atomically. A plain get_or_none + create races
        # under concurrent publishes (both see no root and each creates one),
        # producing duplicate roots with the same uid. MERGE lets concurrent
        # transactions converge on a single root; the uid uniqueness constraint
        # provides the lock that makes this safe.
        root_uid = self._root_uid(library_name)
        db.cypher_query(
            """
            MATCH (lib:Library {name: $library_name})
            MERGE (root:SponsorModelSchemaRoot {uid: $root_uid})
            MERGE (lib)-[:CONTAINS_SPONSOR_MODEL_SCHEMA]->(root)
            """,
            {"library_name": library_name, "root_uid": root_uid},
        )
        root = SponsorModelSchemaRoot.nodes.get(uid=root_uid)

        value = SponsorModelSchemaValue(
            schema_version=ar.schema_vo.schema_version,
            schema=ar.schema_vo.schema,
            content_hash=ar.schema_vo.content_hash,
            author_id=ar.schema_vo.author_id,
            created=datetime.datetime.now(datetime.timezone.utc),
        ).save()
        root.has_schema_version.connect(value)

        # Keep LATEST pointing at the highest version number published so far.
        latest = root.has_latest_value.single()
        if latest is None or value.schema_version >= latest.schema_version:
            if latest is not None:
                root.has_latest_value.disconnect(latest)
            root.has_latest_value.connect(value)

        return self._value_to_ar(library_name, value)

    def close(self) -> None:
        # Kept for symmetry with the service lifecycle; no resources to release.
        pass
