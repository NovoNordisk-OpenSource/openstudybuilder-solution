from typing import Annotated, Any, Literal

from pydantic import Field, StrictBool

from clinical_mdr_api.models.utils import BaseModel, PatchInputModel


class PreferenceMetadata(BaseModel):
    type: Annotated[str, Field()]
    label: Annotated[str, Field()]
    description: Annotated[str, Field()]
    min: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    max: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    default: Annotated[int | bool | str, Field()]
    allowed_values: Annotated[
        list[str] | None, Field(json_schema_extra={"nullable": True})
    ] = None


class PreferencesResponse(BaseModel):
    preferences: Annotated[dict[str, int | bool | str], Field()]
    metadata: Annotated[dict[str, PreferenceMetadata], Field()]


class UserPreferencesResponse(BaseModel):
    preferences: Annotated[dict[str, int | bool | str], Field()]
    overrides: Annotated[dict[str, Any], Field()]
    metadata: Annotated[dict[str, PreferenceMetadata], Field()]


class PreferencesFields(PatchInputModel):
    language: Annotated[Literal["en"] | None, Field()] = None
    theme: Annotated[str | None, Field()] = None
    rows_per_page: Annotated[int | None, Field(ge=5, le=100)] = None
    sidebar_visible: Annotated[StrictBool | None, Field()] = None
    sidebar_auto_minimize: Annotated[StrictBool | None, Field()] = None


class GlobalPreferencesPatchInput(PreferencesFields):
    pass


class UserPreferencesPatchInput(PreferencesFields):
    pass
