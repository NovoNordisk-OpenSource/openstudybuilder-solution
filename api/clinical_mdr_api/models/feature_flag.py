from typing import Annotated, Literal

from pydantic import Field, StrictBool

from clinical_mdr_api.models.concepts.concept import VersionProperties
from clinical_mdr_api.models.utils import PatchInputModel, PostInputModel


class FeatureFlag(VersionProperties):
    uid: Annotated[str, Field()]
    section: Annotated[str, Field()]
    feature: Annotated[str, Field()]
    name: Annotated[str, Field()]
    enabled: Annotated[bool, Field()]
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )


class FeatureFlagVersion(FeatureFlag):
    changes: Annotated[list[str], Field()]


class FeatureFlagInput(PostInputModel):
    section: Annotated[Literal["admin", "library", "studies"], Field()]
    feature: Annotated[str, Field(min_length=1)]
    name: Annotated[str, Field(min_length=1)]
    enabled: Annotated[StrictBool, Field()]
    description: Annotated[str | None, Field(min_length=1)] = None
    change_description: Annotated[str | None, Field(min_length=1)] = None


class FeatureFlagPatchInput(PatchInputModel):
    section: Annotated[Literal["admin", "library", "studies"] | None, Field()] = None
    feature: Annotated[str | None, Field(min_length=1)] = None
    enabled: Annotated[StrictBool | None, Field()] = None
    description: Annotated[
        str | None, Field(min_length=1, json_schema_extra={"nullable": True})
    ] = None
    change_description: Annotated[str | None, Field(min_length=1)] = None
