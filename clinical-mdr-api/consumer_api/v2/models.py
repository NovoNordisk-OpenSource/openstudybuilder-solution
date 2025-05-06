import logging
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"


class SortByStudies(Enum):
    UID = "uid"
    ID_PREFIX = "id_prefix"
    NUMBER = "number"


class Study(BaseModel):
    uid: Annotated[str, Field(description="Study UID")]
    acronym: Annotated[
        str | None,
        Field(description="Study acronym", json_schema_extra={"nullable": True}),
    ] = None
    id_prefix: Annotated[str, Field(description="Study ID prefix")]
    number: Annotated[
        str | None,
        Field(description="Study number", json_schema_extra={"nullable": True}),
    ] = None

    @classmethod
    def from_input(cls, val: dict):
        log.debug("Create Study from input: %s", val)
        return cls(
            uid=val["uid"],
            acronym=val["acronym"],
            id_prefix=val["id_prefix"],
            number=val["number"],
        )
