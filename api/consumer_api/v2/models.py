import logging
from enum import Enum
from typing import Annotated, Any

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
    data_completeness_tags: list[str] = Field(
        description="List of data completeness tag names assigned to the study.",
        default_factory=list,
    )

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        log.debug("Create Study from input: %s", val)
        return cls(
            uid=val["uid"],
            acronym=val["acronym"],
            id_prefix=val["id_prefix"],
            number=val["number"],
            data_completeness_tags=val.get("data_completeness_tags", []),
        )
