from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

from clinical_mdr_api.domains.standard_data_models.sponsor_model_dataset_variable import (
    SponsorModelDatasetVariableAR,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.standard_data_models.sponsor_model import SponsorModelBase
from clinical_mdr_api.models.utils import InputModel


class ReferencedCodelist(BaseModel):
    uid: str
    submission_value: str


class ReferencedTerm(BaseModel):
    uid: str
    submission_value: str


class SimpleSponsorModelDataset(SponsorModelBase):
    uid: str
    ordinal: Annotated[
        int | None,
        Field(
            json_schema_extra={
                "nullable": True,
            }
        ),
    ] = None
    key_order: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    version_number: int
    sponsor_model_name: str


class SponsorModelDatasetVariable(SponsorModelBase):
    # Only structural fields are declared. Sponsor-defined (extensible) fields
    # travel through `extra="allow"` and the schema-driven projection.
    model_config = ConfigDict(from_attributes=True, extra="allow")

    uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    dataset: Annotated[
        SimpleSponsorModelDataset | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    label: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "nullable": True,
            },
        ),
    ] = None
    referenced_codelists: list[ReferencedCodelist] = Field(default_factory=list)
    referenced_terms: list[ReferencedTerm] = Field(default_factory=list)

    @classmethod
    def from_repository_output(cls, input_dict: dict[str, Any]):
        return cls(
            uid=input_dict["uid"],
            dataset=SimpleSponsorModelDataset(
                uid=input_dict.get("dataset", {}).get("uid"),
                ordinal=input_dict.get("dataset", {}).get("ordinal"),
                key_order=input_dict.get("dataset", {}).get("key_order"),
                version_number=input_dict.get("dataset", {}).get("version_number"),
                sponsor_model_name=input_dict.get("dataset", {}).get(
                    "sponsor_model_name"
                ),
            ),
            label=input_dict.get("label"),
            referenced_codelists=[
                ReferencedCodelist(
                    uid=cl["uid"], submission_value=cl["submission_value"]
                )
                for cl in input_dict.get("referenced_codelists", [])
                if cl is not None
            ],
            referenced_terms=[
                ReferencedTerm(uid=t["uid"], submission_value=t["submission_value"])
                for t in input_dict.get("referenced_terms", [])
                if t is not None
            ],
        )

    @classmethod
    def from_sponsor_model_dataset_variable_ar(
        cls,
        sponsor_model_dataset_variable_ar: SponsorModelDatasetVariableAR,
    ) -> "SponsorModelDatasetVariable":
        vo = sponsor_model_dataset_variable_ar.sponsor_model_dataset_variable_vo
        dataset = None
        if vo.dataset_uid is not None:
            dataset = SimpleSponsorModelDataset(
                uid=vo.dataset_uid,
                ordinal=vo.order,
                key_order=None,
                version_number=int(vo.sponsor_model_version_number),
                sponsor_model_name=vo.sponsor_model_name,
            )
        base_data: dict[str, Any] = {
            "uid": sponsor_model_dataset_variable_ar.uid,
            "dataset": dataset,
            "label": vo.label,
            "library_name": Library.from_library_vo(
                sponsor_model_dataset_variable_ar.library
            ).name,
        }

        # Sponsor-defined / extensible fields travel through extra_properties.
        if vo.extra_properties:
            base_data.update(vo.extra_properties)

        return cls(**base_data)  # type: ignore[arg-type]


class SponsorModelDatasetVariableInput(InputModel):
    model_config = ConfigDict(extra="allow")  # Allow sponsor-defined extra fields

    target_data_model_catalogue: Annotated[str | None, Field()] = "SDTMIG"
    dataset_uid: Annotated[
        str,
        Field(
            description="Uid of the dataset in which to create the variable. E.g AE",
            min_length=1,
        ),
    ]
    dataset_variable_uid: Annotated[str, Field(min_length=1)]
    sponsor_model_name: Annotated[
        str,
        Field(
            description="Name of the sponsor model in which to create the variable. E.g sdtmig_sponsormodel...",
            min_length=1,
        ),
    ]
    sponsor_model_version_number: Annotated[
        str,
        Field(
            description="Version number of the sponsor model in which to create the variable",
            min_length=1,
        ),
    ]
    label: Annotated[str | None, Field()] = None
    implemented_parent_dataset_class: Annotated[
        str | None,
        Field(
            description="The uid of the dataset class that the variable class belongs to, e.g. Findings",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    implemented_variable_class: Annotated[
        str | None,
        Field(
            description="The uid of the implemented dataset variable, e.g. --ORRES",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    order: Annotated[int | None, Field()] = None
    references_codelists: Annotated[list[str] | None, Field()] = None
    references_terms: Annotated[list[str] | None, Field()] = None
    library_name: Annotated[
        str | None, Field(description="Defaults to CDISC", min_length=1)
    ] = "CDISC"

    def get_extra_fields(self) -> dict[str, Any]:
        """Return fields that were passed but aren't in the defined model."""
        defined_fields = set(self.model_fields.keys())
        all_fields = set(self.model_dump().keys())
        extra_fields = all_fields - defined_fields
        return {field: getattr(self, field) for field in extra_fields}
