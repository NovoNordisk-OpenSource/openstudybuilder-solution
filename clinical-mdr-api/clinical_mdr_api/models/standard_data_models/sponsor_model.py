from typing import Annotated, Self

from pydantic import ConfigDict, Field

from clinical_mdr_api.domains.standard_data_models.sponsor_model import SponsorModelAR
from clinical_mdr_api.models.concepts.concept import VersionProperties
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, InputModel


class SponsorModelBase(BaseModel):
    pass


class SponsorModel(SponsorModelBase, VersionProperties):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(json_schema_extra={"source": "uid", "nullable": True}),
    ] = None
    name: Annotated[
        str,
        Field(
            description="The name or the sponsor model. E.g. sdtm_sponsormodel_3.2-NN15",
            json_schema_extra={"source": "has_latest_sponsor_model_value.name"},
        ),
    ]
    extended_implementation_guide: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_sponsor_model_value__extends_version.name",
                "nullable": True,
            },
        ),
    ] = None
    library_name: Annotated[
        str | None,
        Field(json_schema_extra={"source": "has_library.name", "nullable": True}),
    ] = None

    @classmethod
    def from_sponsor_model_ar(
        cls,
        sponsor_model_ar: SponsorModelAR,
    ) -> Self:
        return cls(
            uid=sponsor_model_ar.uid,
            name=sponsor_model_ar.name,
            library_name=Library.from_library_vo(sponsor_model_ar.library).name,
            start_date=sponsor_model_ar.item_metadata.start_date,
            end_date=sponsor_model_ar.item_metadata.end_date,
            status=sponsor_model_ar.item_metadata.status.value,
            version=sponsor_model_ar.item_metadata.version,
            change_description=sponsor_model_ar.item_metadata.change_description,
            author_username=sponsor_model_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in sponsor_model_ar.get_possible_actions()]
            ),
        )


class SponsorModelInput(InputModel):
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
    change_description: Annotated[
        str | None,
        Field(description="Optionally, provide a change description."),
    ] = "Imported new version"
    library_name: Annotated[
        str | None, Field(description="Defaults to CDISC", min_length=1)
    ] = "CDISC"
