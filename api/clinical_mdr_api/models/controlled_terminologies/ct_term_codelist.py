from datetime import datetime
from typing import Annotated

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class CTTermCodelist(BaseModel):
    codelist_uid: Annotated[str, Field()]
    codelist_name: Annotated[str, Field()]
    codelist_submission_value: Annotated[str, Field()]
    codelist_concept_id: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ]
    submission_value: Annotated[str, Field()]
    order: Annotated[int | None, Field(json_schema_extra={"nullable": True})]
    ordinal: Annotated[float | None, Field(json_schema_extra={"nullable": True})] = None
    start_date: datetime

    library_name: Annotated[str, Field()]
