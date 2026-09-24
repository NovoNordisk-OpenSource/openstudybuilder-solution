from enum import Enum
from typing import Annotated

from pydantic import Field

from clinical_mdr_api.models.controlled_terminologies.ct_codelist import (
    CTCodelistNameAndAttributes,
)
from clinical_mdr_api.models.utils import BaseModel


class CodelistCount(BaseModel):
    library_name: Annotated[str, Field()]
    count: Annotated[int, Field()]


class TermCount(BaseModel):
    library_name: Annotated[str, Field()]
    count: Annotated[int, Field()]


class CountTypeEnum(str, Enum):
    ADDED = "added"
    DELETED = "deleted"
    UPDATED = "updated"


class CountByType(BaseModel):
    type: Annotated[CountTypeEnum, Field()]
    count: Annotated[int, Field()]


class CountByTypeByYear(BaseModel):
    year: Annotated[int, Field()]
    counts: Annotated[list[CountByType], Field()]


class CTStats(BaseModel):
    catalogues: Annotated[
        int,
        Field(description="Number of catalogues in the database"),
    ]
    packages: Annotated[int, Field(description="Number of packages in the database")]
    codelist_counts: Annotated[
        list[CodelistCount],
        Field(description="Count of codelists grouped by Library"),
    ]
    term_counts: Annotated[
        list[TermCount],
        Field(description="Count of terms grouped by Library"),
    ]
    codelist_change_percentage: Annotated[
        float,
        Field(
            description="Mean percentage of evolution for codelists",
        ),
    ]
    term_change_percentage: Annotated[
        float,
        Field(
            description="Mean percentage of evolution for terms",
        ),
    ]
    codelist_change_details: Annotated[
        list[CountByTypeByYear],
        Field(
            description="Codelist changes, grouped by type and year",
        ),
    ]
    term_change_details: Annotated[
        list[CountByTypeByYear],
        Field(
            description="Term changes, grouped by type and year",
        ),
    ]
    latest_added_codelists: Annotated[
        list[CTCodelistNameAndAttributes],
        Field(description="List of latest added codelists"),
    ]
