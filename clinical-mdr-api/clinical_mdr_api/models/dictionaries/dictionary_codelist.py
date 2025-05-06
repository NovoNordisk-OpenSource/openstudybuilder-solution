from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.dictionaries.dictionary_codelist import (
    DictionaryCodelistAR,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel


class DictionaryCodelist(BaseModel):
    @classmethod
    def from_dictionary_codelist_ar(
        cls, dictionary_codelist_ar: DictionaryCodelistAR
    ) -> Self:
        return cls(
            codelist_uid=dictionary_codelist_ar.uid,
            name=dictionary_codelist_ar.name,
            library_name=Library.from_library_vo(dictionary_codelist_ar.library).name,
            template_parameter=dictionary_codelist_ar.dictionary_codelist_vo.is_template_parameter,
            start_date=dictionary_codelist_ar.item_metadata.start_date,
            end_date=dictionary_codelist_ar.item_metadata.end_date,
            status=dictionary_codelist_ar.item_metadata.status.value,
            version=dictionary_codelist_ar.item_metadata.version,
            change_description=dictionary_codelist_ar.item_metadata.change_description,
            author_username=dictionary_codelist_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in dictionary_codelist_ar.get_possible_actions()]
            ),
        )

    codelist_uid: Annotated[str, Field()]

    name: Annotated[str, Field()]

    template_parameter: Annotated[bool, Field()]

    possible_actions: Annotated[
        list[str],
        Field(
            description=(
                "Holds those actions that can be performed on the DictionaryCodelist. "
                "Actions are: 'approve', 'edit', 'new_version'."
            )
        ),
    ]

    library_name: str
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


class DictionaryCodelistEditInput(PatchInputModel):
    name: Annotated[str | None, Field(min_length=1)] = None
    template_parameter: bool | None = None
    change_description: Annotated[str | None, Field(min_length=1)] = None


class DictionaryCodelistCreateInput(PostInputModel):
    name: Annotated[str | None, Field(min_length=1)] = None
    template_parameter: bool | None = None
    library_name: Annotated[str, Field(min_length=1)]


class DictionaryCodelistTermInput(PostInputModel):
    term_uid: Annotated[str, Field(min_length=1)]


class DictionaryCodelistVersion(DictionaryCodelist):
    """
    Class for storing DictionaryCodelist and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []
