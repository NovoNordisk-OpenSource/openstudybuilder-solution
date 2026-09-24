from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import Field, StrictBool, field_validator, model_validator

from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel
from clinical_mdr_api.models.validators import (
    reject_non_string_datetime,
    transform_to_utc,
)


class NotificationType(Enum):
    INFORMATION = "information"
    WARNING = "warning"
    ERROR = "error"


class Notification(BaseModel):
    sn: Annotated[int, Field()]
    title: Annotated[str, Field()]
    notification_type: Annotated[str, Field()]
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    started_at: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    ended_at: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    published_at: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None


class NotificationPostInput(PostInputModel):
    title: Annotated[str, Field(min_length=1)]
    notification_type: Annotated[NotificationType, Field()] = (
        NotificationType.INFORMATION
    )
    description: Annotated[str | None, Field(min_length=1)] = None
    started_at: Annotated[datetime | None, Field()] = None
    ended_at: Annotated[datetime | None, Field()] = None
    published: Annotated[StrictBool, Field()] = False

    _reject_non_string_date = field_validator("started_at", "ended_at", mode="before")(
        reject_non_string_datetime
    )
    _date_validator = field_validator("started_at", "ended_at")(transform_to_utc)

    @model_validator(mode="after")
    def validate_date_is_after_date(self):
        started_at = self.started_at
        ended_at = self.ended_at
        if started_at and ended_at and ended_at <= started_at:
            raise ValueError("ended_at must be after started_at")
        return self


class NotificationPatchInput(PatchInputModel):
    title: Annotated[str, Field(min_length=1)]
    notification_type: Annotated[NotificationType, Field()] = (
        NotificationType.INFORMATION
    )
    description: Annotated[str | None, Field(min_length=1)] = None
    started_at: Annotated[datetime | None, Field()] = None
    ended_at: Annotated[datetime | None, Field()] = None
    published: Annotated[StrictBool, Field()] = False

    _reject_non_string_date = field_validator("started_at", "ended_at", mode="before")(
        reject_non_string_datetime
    )
    _date_validator = field_validator("started_at", "ended_at")(transform_to_utc)

    @model_validator(mode="after")
    def validate_date_is_after_date(self):
        started_at = self.started_at
        ended_at = self.ended_at
        if started_at and ended_at and ended_at <= started_at:
            raise ValueError("ended_at must be after started_at")
        return self
