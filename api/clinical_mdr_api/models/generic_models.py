from typing import Annotated

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class SimpleNameModel(BaseModel):
    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    name_sentence_case: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
