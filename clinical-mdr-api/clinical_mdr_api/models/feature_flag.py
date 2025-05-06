from typing import Annotated

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel


class FeatureFlag(BaseModel):
    sn: int
    name: str
    enabled: bool
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )


class FeatureFlagInput(PostInputModel):
    name: Annotated[str, Field(min_length=1)]
    enabled: bool
    description: Annotated[str | None, Field(min_length=1)] = None


class FeatureFlagPatchInput(PatchInputModel):
    enabled: bool = False
