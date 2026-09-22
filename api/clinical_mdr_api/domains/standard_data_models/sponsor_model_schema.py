import datetime
import hashlib
from dataclasses import dataclass, field
from typing import Self


@dataclass(frozen=True)
class SponsorModelSchemaVO:
    """
    Value object for a single, immutable Sponsor Model Schema version.

    ``schema`` is the full schema serialized as an opaque string (YAML text).
    The domain never interprets its contents; it only keys and content-addresses
    it via a stable hash for idempotency.
    """

    library_name: str
    schema_version: int
    schema: str

    author_id: str | None = None
    author_username: str | None = None
    created: datetime.datetime | None = None
    content_hash: str = field(default="")

    @staticmethod
    def compute_content_hash(schema: str) -> str:
        """Stable content address of the schema blob (exact-string sha256)."""
        return hashlib.sha256(schema.encode("utf-8")).hexdigest()

    @classmethod
    def from_input_values(
        cls,
        *,
        library_name: str,
        schema_version: int,
        schema: str,
        author_id: str | None = None,
    ) -> Self:
        return cls(
            library_name=library_name,
            schema_version=schema_version,
            schema=schema,
            author_id=author_id,
            content_hash=cls.compute_content_hash(schema),
        )

    @classmethod
    def from_repository_values(
        cls,
        *,
        library_name: str,
        schema_version: int,
        schema: str,
        content_hash: str,
        author_id: str | None = None,
        author_username: str | None = None,
        created: datetime.datetime | None = None,
    ) -> Self:
        return cls(
            library_name=library_name,
            schema_version=schema_version,
            schema=schema,
            content_hash=content_hash,
            author_id=author_id,
            author_username=author_username,
            created=created,
        )


@dataclass
class SponsorModelSchemaAR:
    """
    Aggregate root for an immutable, versioned Sponsor Model Schema.

    Schema versions are immutable once published: there is no draft/final/retired
    lifecycle. A version is uniquely identified by ``(library_name, schema_version)``.
    """

    _schema_vo: SponsorModelSchemaVO

    @property
    def schema_vo(self) -> SponsorModelSchemaVO:
        return self._schema_vo

    @property
    def library_name(self) -> str:
        return self._schema_vo.library_name

    @property
    def schema_version(self) -> int:
        return self._schema_vo.schema_version

    @property
    def content_hash(self) -> str:
        return self._schema_vo.content_hash

    def matches_content(self, other: "SponsorModelSchemaAR") -> bool:
        """True when both aggregates address the same schema blob."""
        return self.content_hash == other.content_hash

    @classmethod
    def from_input_values(
        cls,
        *,
        library_name: str,
        schema_version: int,
        schema: str,
        author_id: str | None = None,
    ) -> Self:
        return cls(
            _schema_vo=SponsorModelSchemaVO.from_input_values(
                library_name=library_name,
                schema_version=schema_version,
                schema=schema,
                author_id=author_id,
            )
        )

    @classmethod
    def from_repository_values(cls, *, schema_vo: SponsorModelSchemaVO) -> Self:
        return cls(_schema_vo=schema_vo)
