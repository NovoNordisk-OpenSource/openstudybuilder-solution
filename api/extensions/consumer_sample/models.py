"""Response models of the consumer_sample extension."""

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"


class SortByCTTerms(Enum):
    TERM_UID = "term_uid"
    SUBMISSION_VALUE = "submission_value"
    SPONSOR_PREFERRED_NAME = "sponsor_preferred_name"
    NCI_PREFERRED_NAME = "nci_preferred_name"
    CONCEPT_ID = "concept_id"


class CTTerm(BaseModel):
    """A CT term of a codelist, with its Final name and attributes."""

    codelist_uid: Annotated[str, Field(description="Codelist UID")]
    term_uid: Annotated[str, Field(description="Codelist Term UID")]
    order: Annotated[
        int | None,
        Field(
            description="Term order within the codelist",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    ordinal: Annotated[
        float | None,
        Field(
            description="Term ordinal value (only for ordinal codelists)",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    submission_value: Annotated[str, Field(description="Submission Value")]
    sponsor_preferred_name: Annotated[str, Field(description="Sponsor Preferred Name")]
    concept_id: Annotated[
        str | None,
        Field(
            description="Concept ID in e.g. CDISC Library",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    nci_preferred_name: Annotated[
        str | None,
        Field(description="NCI Preferred Name", json_schema_extra={"nullable": True}),
    ] = None
    library_name: Annotated[str, Field(description="Library Name")]
    name_status: Annotated[str, Field(description="Name version status")]
    name_version: Annotated[str, Field(description="Name version number")]
    attributes_status: Annotated[str, Field(description="Attributes version status")]
    attributes_version: Annotated[str, Field(description="Attributes version number")]
