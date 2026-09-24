from datetime import datetime, timezone
from typing import Annotated

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel
from common.config import settings


class BatchErrorResponse(BaseModel):
    message: Annotated[
        str | None,
        Field(
            description="More information about the error.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    time: Annotated[
        str, Field(description="The point in time when the error occurred.")
    ]

    def __init__(self, **data) -> None:
        if "time" not in data:
            data["time"] = datetime.now(timezone.utc).strftime(
                settings.date_time_format
            )
        super().__init__(**data)
