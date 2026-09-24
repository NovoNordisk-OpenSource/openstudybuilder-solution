from datetime import datetime
from typing import Annotated, Any, Self

import yaml
from pydantic import ConfigDict, Field

from clinical_mdr_api.domains.standard_data_models.sponsor_model_schema import (
    SponsorModelSchemaAR,
)
from clinical_mdr_api.models.utils import BaseModel, InputModel
from common.config import settings

# The importer submits the schema as a single opaque string (YAML text).
# The JSON key is `schema`; the Python attribute is `schema_content` to avoid
# shadowing Pydantic's deprecated BaseModel.schema attribute.
_SCHEMA_INPUT_FIELD_DESCRIPTION = (
    "The full Sponsor Model Schema serialized as a string (YAML text). "
    "Stored verbatim and treated as an opaque blob by the API."
)
# On read, the stored YAML blob is parsed and returned as JSON so consumers do
# not have to parse YAML themselves. The database still stores it as YAML text.
_SCHEMA_OUTPUT_FIELD_DESCRIPTION = (
    "The full Sponsor Model Schema, returned as JSON. "
    "It is stored as YAML text and parsed on read."
)


class SponsorModelSchemaCreateInput(InputModel):
    schema_version: Annotated[
        int,
        Field(
            description="Positive integer version of the schema. Immutable once published.",
            ge=1,
        ),
    ]
    schema_content: Annotated[
        str,
        Field(
            description=_SCHEMA_INPUT_FIELD_DESCRIPTION,
            min_length=1,
            # Opaque blob: keep it byte-for-byte as submitted (no whitespace strip).
            json_schema_extra={"preserve_whitespace": True},
        ),
    ] = Field(alias="schema")
    library_name: Annotated[
        str | None,
        Field(description=f"Defaults to {settings.sponsor_library_name}", min_length=1),
    ] = settings.sponsor_library_name


class SponsorModelSchemaMetadata(BaseModel):
    """Lightweight schema descriptor without the (potentially large) blob."""

    schema_version: Annotated[
        int, Field(description="Positive integer version of the schema.")
    ]
    library_name: Annotated[str, Field(description="Library the schema belongs to.")]
    content_hash: Annotated[
        str, Field(description="sha256 of the schema blob, used for idempotency.")
    ]
    created: Annotated[datetime | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_sponsor_model_schema_ar(cls, ar: SponsorModelSchemaAR) -> Self:
        return cls(
            schema_version=ar.schema_vo.schema_version,
            library_name=ar.schema_vo.library_name,
            content_hash=ar.schema_vo.content_hash,
            created=ar.schema_vo.created,
            author_username=ar.schema_vo.author_username,
        )


class SponsorModelSchema(SponsorModelSchemaMetadata):
    """Full schema record, including the schema content parsed as JSON."""

    # Allow constructing by the Python attribute name while still exposing the
    # `schema` JSON key via the field alias.
    model_config = ConfigDict(populate_by_name=True)

    # Stored as YAML text; parsed and returned as JSON on read.
    schema_content: Annotated[
        Any,
        Field(description=_SCHEMA_OUTPUT_FIELD_DESCRIPTION),
    ] = Field(alias="schema")

    @classmethod
    def from_sponsor_model_schema_ar(cls, ar: SponsorModelSchemaAR) -> Self:
        return cls(
            schema_version=ar.schema_vo.schema_version,
            library_name=ar.schema_vo.library_name,
            # `schema_content`'s alias ('schema') is the synthesized constructor
            # parameter name; populate_by_name only affects runtime validation.
            schema=yaml.safe_load(ar.schema_vo.schema),
            content_hash=ar.schema_vo.content_hash,
            created=ar.schema_vo.created,
            author_username=ar.schema_vo.author_username,
        )
