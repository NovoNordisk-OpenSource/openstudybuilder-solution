from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    DEFAULT_CODELIST_TYPE,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameAR,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel


class CTCodelistName(BaseModel):
    @classmethod
    def from_ct_codelist_ar(cls, ct_codelist_ar: CTCodelistNameAR) -> Self:
        return cls(
            catalogue_names=ct_codelist_ar.ct_codelist_vo.catalogue_names,
            codelist_uid=ct_codelist_ar.uid,
            name=ct_codelist_ar.name,
            template_parameter=ct_codelist_ar.ct_codelist_vo.is_template_parameter,
            is_ordinal=ct_codelist_ar.ct_codelist_vo.is_ordinal,
            codelist_type=ct_codelist_ar.ct_codelist_vo.codelist_type,
            library_name=Library.from_library_vo(ct_codelist_ar.library).name,
            start_date=ct_codelist_ar.item_metadata.start_date,
            end_date=ct_codelist_ar.item_metadata.end_date,
            status=ct_codelist_ar.item_metadata.status.value,
            version=ct_codelist_ar.item_metadata.version,
            change_description=ct_codelist_ar.item_metadata.change_description,
            author_username=ct_codelist_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in ct_codelist_ar.get_possible_actions()]
            ),
        )

    @classmethod
    def from_ct_codelist_ar_without_common_codelist_fields(
        cls, ct_codelist_ar: CTCodelistNameAR
    ) -> Self:
        return cls(
            name=ct_codelist_ar.name,
            template_parameter=ct_codelist_ar.ct_codelist_vo.is_template_parameter,
            is_ordinal=ct_codelist_ar.ct_codelist_vo.is_ordinal,
            codelist_type=ct_codelist_ar.ct_codelist_vo.codelist_type,
            start_date=ct_codelist_ar.item_metadata.start_date,
            end_date=ct_codelist_ar.item_metadata.end_date,
            status=ct_codelist_ar.item_metadata.status.value,
            version=ct_codelist_ar.item_metadata.version,
            change_description=ct_codelist_ar.item_metadata.change_description,
            author_username=ct_codelist_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in ct_codelist_ar.get_possible_actions()]
            ),
        )

    catalogue_names: Annotated[
        list[str], Field(json_schema_extra={"remove_from_wildcard": True})
    ] = []

    codelist_uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )

    name: Annotated[str, Field()]

    template_parameter: Annotated[bool, Field()]

    is_ordinal: Annotated[bool, Field()]

    codelist_type: Annotated[
        str, Field(json_schema_extra={"remove_from_wildcard": True})
    ] = DEFAULT_CODELIST_TYPE

    library_name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    start_date: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    end_date: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    status: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    change_description: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    possible_actions: list[str] = Field(
        description=(
            "Holds those actions that can be performed on the CTCodelistName. "
            "Actions are: 'approve', 'edit', 'new_version'."
        ),
        default_factory=list,
    )


class CTCodelistNameVersion(CTCodelistName):
    """
    Class for storing CTCodelistAttributes and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)


class CTCodelistNameEditInput(PatchInputModel):
    name: Annotated[str | None, Field(min_length=1)] = None
    template_parameter: Annotated[bool, Field()] = False
    is_ordinal: Annotated[bool | None, Field()] = None
    codelist_type: Annotated[str | None, Field(min_length=1)] = None
    change_description: Annotated[str, Field(min_length=1)]
