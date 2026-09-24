from typing import Annotated, Any, Self

from pydantic import ConfigDict, Field

from clinical_mdr_api.domains.standard_data_models.sponsor_model_dataset import (
    SponsorModelDatasetAR,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.standard_data_models.sponsor_model import SponsorModelBase
from clinical_mdr_api.models.utils import InputModel


class SimpleSponsorModelDataModelIG(SponsorModelBase):
    ordinal: Annotated[
        int | None,
        Field(
            json_schema_extra={
                "source": "has_sponsor_model_instance.has_dataset|ordinal",
                "nullable": True,
            }
        ),
    ] = None
    name: Annotated[
        str,
        Field(
            json_schema_extra={"source": "has_sponsor_model_instance.has_dataset.name"}
        ),
    ]


class SponsorModelDataset(SponsorModelBase):
    # Only structural fields are declared. Sponsor-defined (extensible) fields
    # travel through `extra="allow"` and the schema-driven projection.
    model_config = ConfigDict(from_attributes=True, extra="allow")

    uid: Annotated[
        str | None,
        Field(json_schema_extra={"source": "uid", "nullable": True}),
    ] = None
    sponsor_model: Annotated[
        SimpleSponsorModelDataModelIG | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    keys: Annotated[
        list[str] | None,
        Field(
            json_schema_extra={
                "source": "has_sponsor_model_instance.has_key.uid",
                "nullable": True,
            },
        ),
    ] = None
    sort_keys: Annotated[
        list[str] | None,
        Field(
            json_schema_extra={
                "source": "has_sponsor_model_instance.has_sort_key.uid",
                "nullable": True,
            },
        ),
    ] = None
    label: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_sponsor_model_instance.label",
                "nullable": True,
            },
        ),
    ] = None
    enrich_build_order: Annotated[
        int | None,
        Field(
            json_schema_extra={
                "source": "has_sponsor_model_instance.has_dataset|ordinal",
                "nullable": True,
            },
        ),
    ] = None

    @classmethod
    def from_sponsor_model_dataset_ar(
        cls,
        sponsor_model_dataset_ar: SponsorModelDatasetAR,
    ) -> Self:
        vo = sponsor_model_dataset_ar.sponsor_model_dataset_vo
        base_data: dict[str, Any] = {
            "uid": sponsor_model_dataset_ar.uid,
            "implemented_dataset_class": vo.implemented_dataset_class,
            "keys": vo.keys,
            "sort_keys": vo.sort_keys,
            "label": vo.label,
            "enrich_build_order": vo.enrich_build_order,
            "library_name": Library.from_library_vo(
                sponsor_model_dataset_ar.library
            ).name,
        }

        # Sponsor-defined / extensible fields travel through extra_properties.
        if vo.extra_properties:
            base_data.update(vo.extra_properties)

        return cls(**base_data)  # type: ignore[arg-type]


class SponsorModelDatasetInput(InputModel):
    model_config = ConfigDict(extra="allow")  # Allow extra fields

    target_data_model_catalogue: Annotated[str | None, Field()] = "SDTMIG"
    dataset_uid: Annotated[str, Field(min_length=1)]
    sponsor_model_name: Annotated[
        str,
        Field(
            description="Name of the sponsor model in which to create the dataset. E.g sdtmig_sponsormodel...",
            min_length=1,
        ),
    ]
    sponsor_model_version_number: Annotated[
        str,
        Field(
            description="Version number of the sponsor model in which to create the dataset",
            min_length=1,
        ),
    ]
    label: Annotated[str | None, Field()] = None
    implemented_dataset_class: Annotated[
        str | None,
        Field(
            description="The uid of the implemented dataset class, e.g. Findings",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    keys: Annotated[list[str] | None, Field()] = None
    sort_keys: Annotated[list[str] | None, Field()] = None
    enrich_build_order: Annotated[int | None, Field()] = None
    library_name: Annotated[
        str | None, Field(description="Defaults to CDISC", min_length=1)
    ] = "CDISC"

    def get_extra_fields(self) -> dict[str, Any]:
        """Return fields that were passed but are not in the defined model."""
        defined_fields = set(self.model_fields.keys())
        all_fields = set(self.model_dump().keys())
        extra_fields = all_fields - defined_fields
        return {field: getattr(self, field) for field in extra_fields}
