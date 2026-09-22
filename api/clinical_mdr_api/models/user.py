from datetime import datetime
from typing import Annotated

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field


class UserInfo(PydanticBaseModel):
    user_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})]
    username: Annotated[str | None, Field(json_schema_extra={"nullable": True})]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})]
    email: Annotated[str | None, Field(json_schema_extra={"nullable": True})]
    azp: Annotated[str | None, Field(json_schema_extra={"nullable": True})]
    oid: Annotated[str | None, Field(json_schema_extra={"nullable": True})]
    roles: list[str] = Field(default_factory=list)
    created: Annotated[datetime, Field(json_schema_extra={"nullable": True})]
    updated: Annotated[datetime | None, Field(json_schema_extra={"nullable": True})]


class UserInfoPatchInput(PydanticBaseModel):
    username: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    email: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
