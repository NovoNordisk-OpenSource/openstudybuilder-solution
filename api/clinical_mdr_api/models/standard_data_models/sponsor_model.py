from datetime import datetime
from typing import Annotated, Any, Self

from pydantic import ConfigDict, Field, field_validator

from clinical_mdr_api.domains.standard_data_models.sponsor_model import SponsorModelAR
from clinical_mdr_api.models import _generic_descriptions
from clinical_mdr_api.models.utils import BaseModel, InputModel
from common.config import settings


class SponsorModelBase(BaseModel):
    pass


class SponsorModel(SponsorModelBase):
    model_config = ConfigDict(from_attributes=True, extra="allow")

    uid: Annotated[
        str | None,
        Field(json_schema_extra={"source": "uid"}),
    ]
    name: Annotated[
        str,
        Field(
            description="The name or the sponsor model. E.g. sdtm_sponsormodel_3.2-NN15",
            json_schema_extra={"source": "has_sponsor_model_version.name"},
        ),
    ]
    start_date: Annotated[
        datetime | None,
        Field(
            description=_generic_descriptions.START_DATE,
            json_schema_extra={
                "source": "has_sponsor_model_version|start_date",
                "nullable": True,
            },
        ),
    ] = None
    end_date: Annotated[
        datetime | None,
        Field(
            description=_generic_descriptions.END_DATE,
            json_schema_extra={
                "source": "has_sponsor_model_version|end_date",
                "nullable": True,
            },
        ),
    ] = None
    status: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_sponsor_model_version|status",
                "nullable": True,
            },
        ),
    ] = None
    version: Annotated[
        str,
        Field(
            description="Version of the sponsor model.",
            json_schema_extra={"source": "has_sponsor_model_version|version"},
        ),
    ]
    extended_implementation_guide: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_sponsor_model_version.extends_version.name",
                "nullable": True,
            },
        ),
    ] = None
    name_qualifier: Annotated[
        str | None,
        Field(
            description="Optional qualifier segment inserted in the generated name, e.g. 'nis'",
            json_schema_extra={
                "source": "has_sponsor_model_version.name_qualifier",
                "nullable": True,
            },
        ),
    ] = None
    # Default None (not 1) so the flattened GET path returns None for a
    # missing FOLLOWS_SCHEMA relation instead of raising; the validator
    # below then coerces that None to 1. validate_default ensures the
    # coercion also runs when the field is absent entirely.
    schema_version: Annotated[
        int,
        Field(
            validate_default=True,
            description="Version of the Sponsor Model Schema this sponsor model follows. "
            "Defaults to 1 for sponsor models created before schemas were introduced.",
            json_schema_extra={
                "source": "has_sponsor_model_version.follows_schema.schema_version",
            },
        ),
    ] = None  # type: ignore[assignment]
    library_name: Annotated[
        str,
        Field(
            validate_default=True,
            json_schema_extra={
                "source": "has_sponsor_model_version.has_library.name",
                "nullable": True,
            },
        ),
    ] = None  # type: ignore[assignment]

    # Legacy sponsor models have no FOLLOWS_SCHEMA link; treat the absence as
    # version 1 at read time (covers both the flattened GET path and construction).
    @field_validator("schema_version", mode="before")
    @classmethod
    def _default_schema_version(cls, value: int | None) -> int:
        return 1 if value is None else value

    @classmethod
    def from_sponsor_model_ar(
        cls,
        sponsor_model_ar: SponsorModelAR,
    ) -> Self:
        return cls(
            uid=sponsor_model_ar.uid,
            name=sponsor_model_ar.name,
            start_date=sponsor_model_ar.item_metadata.start_date,
            end_date=sponsor_model_ar.item_metadata.end_date,
            status=sponsor_model_ar.item_metadata.status.value,
            version=sponsor_model_ar.item_metadata.version,
            name_qualifier=sponsor_model_ar.sponsor_model_vo.name_qualifier,
            library_name=sponsor_model_ar.library.name,
            # Missing link on legacy nodes is treated as version 1 at read time.
            schema_version=sponsor_model_ar.sponsor_model_vo.schema_version or 1,
            **(sponsor_model_ar.sponsor_model_vo.extra_properties or {}),
        )


class SponsorModelCreateInput(InputModel):
    model_config = ConfigDict(extra="allow")  # Allow sponsor-defined extra fields

    ig_uid: Annotated[
        str,
        Field(
            description="Unique identifier of the implementation guide to create the sponsor model from. E.g. SDTMIG",
            min_length=1,
        ),
    ] = "SDTMIG"
    ig_version_number: Annotated[
        str,
        Field(
            description="the version number of the Implementation Guide which the sponsor model is based on",
            min_length=1,
        ),
    ]
    version_number: Annotated[
        str,
        Field(
            description="Version number of the sponsor model to use - will be concatenated at the end of the full name",
            min_length=1,
        ),
    ]
    library_name: Annotated[
        str | None,
        Field(
            description=f"Defaults to {settings.sponsor_library_name}.", min_length=1
        ),
    ] = settings.sponsor_library_name
    name_qualifier: Annotated[
        str | None,
        Field(
            description="Optional qualifier after the IG prefix, e.g. 'nis' → sdtmig_sponsormodel_nis_3.3_DS01",
            min_length=1,
        ),
    ] = None
    schema_version: Annotated[
        int | None,
        Field(
            description="Version of the Sponsor Model Schema this sponsor model follows. "
            "If provided, that schema version must already be published.",
            ge=1,
        ),
    ] = None

    def get_extra_fields(self) -> dict[str, Any]:
        """Return fields that were passed but are not in the defined model."""
        defined_fields = set(self.model_fields.keys())
        all_fields = set(self.model_dump().keys())
        return {field: getattr(self, field) for field in all_fields - defined_fields}


class SponsorModelEditInput(SponsorModelCreateInput):
    change_description: Annotated[
        str, Field(description="Optionally, provide a change description.")
    ] = "Imported new version"
