from datetime import datetime
from typing import Annotated, Any, Callable, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domains.dictionaries.dictionary_term_substance import (
    DictionaryTermSubstanceAR,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleDictionaryTermModel,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel


class DictionaryTerm(BaseModel):
    @classmethod
    def from_dictionary_term_ar(
        cls, dictionary_term_ar: DictionaryTermAR
    ) -> Self | None:
        if not dictionary_term_ar:
            return None
        return cls(
            term_uid=dictionary_term_ar.uid,
            dictionary_id=dictionary_term_ar.dictionary_term_vo.dictionary_id,
            name=dictionary_term_ar.name,
            name_sentence_case=dictionary_term_ar.dictionary_term_vo.name_sentence_case,
            abbreviation=dictionary_term_ar.dictionary_term_vo.abbreviation,
            definition=dictionary_term_ar.dictionary_term_vo.definition,
            library_name=Library.from_library_vo(dictionary_term_ar.library).name,
            start_date=dictionary_term_ar.item_metadata.start_date,
            end_date=dictionary_term_ar.item_metadata.end_date,
            status=dictionary_term_ar.item_metadata.status.value,
            version=dictionary_term_ar.item_metadata.version,
            change_description=dictionary_term_ar.item_metadata.change_description,
            author_username=dictionary_term_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in dictionary_term_ar.get_possible_actions()]
            ),
        )

    term_uid: str
    dictionary_id: str
    name: str
    name_sentence_case: str
    abbreviation: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    definition: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )

    possible_actions: Annotated[
        list[str],
        Field(
            description=(
                "Holds those actions that can be performed on the DictionaryTerm. "
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


class DictionaryTermEditInput(PatchInputModel):
    dictionary_id: Annotated[str | None, Field(min_length=1)] = None
    name: Annotated[str | None, Field(min_length=1)] = None
    name_sentence_case: Annotated[str | None, Field(min_length=1)] = None
    abbreviation: Annotated[str | None, Field(min_length=1)] = None
    definition: Annotated[str | None, Field(min_length=1)] = None
    change_description: Annotated[str | None, Field(min_length=1)] = None


class DictionaryTermCreateInput(PostInputModel):
    dictionary_id: Annotated[str, Field(min_length=1)]
    name: Annotated[str, Field(min_length=1)]
    name_sentence_case: Annotated[str | None, Field(min_length=1)] = None
    abbreviation: Annotated[str | None, Field(min_length=1)] = None
    definition: Annotated[str | None, Field(min_length=1)] = None
    codelist_uid: Annotated[str, Field(min_length=1)]
    library_name: Annotated[str, Field(min_length=1)]


class DictionaryTermSubstance(DictionaryTerm):
    pclass: Annotated[
        SimpleDictionaryTermModel | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_dictionary_term_ar(
        cls,
        dictionary_term_ar: DictionaryTermSubstanceAR,
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
    ) -> Self | None:
        if not dictionary_term_ar:
            return None
        return cls(
            term_uid=dictionary_term_ar.uid,
            dictionary_id=dictionary_term_ar.dictionary_term_vo.dictionary_id,
            name=dictionary_term_ar.name,
            name_sentence_case=dictionary_term_ar.dictionary_term_vo.name_sentence_case,
            abbreviation=dictionary_term_ar.dictionary_term_vo.abbreviation,
            definition=dictionary_term_ar.dictionary_term_vo.definition,
            library_name=Library.from_library_vo(dictionary_term_ar.library).name,
            pclass=SimpleDictionaryTermModel.from_ct_code(
                c_code=dictionary_term_ar.dictionary_term_vo.pclass_uid,
                find_term_by_uid=find_dictionary_term_by_uid,
            ),
            start_date=dictionary_term_ar.item_metadata.start_date,
            end_date=dictionary_term_ar.item_metadata.end_date,
            status=dictionary_term_ar.item_metadata.status.value,
            version=dictionary_term_ar.item_metadata.version,
            change_description=dictionary_term_ar.item_metadata.change_description,
            author_username=dictionary_term_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in dictionary_term_ar.get_possible_actions()]
            ),
        )


class CompoundSubstance(BaseModel):
    substance_term_uid: str
    substance_name: str
    substance_unii: str
    pclass_term_uid: str | None = None
    pclass_name: str | None = None
    pclass_id: str | None = None

    @classmethod
    def from_term_uid(
        cls,
        uid: str,
        find_term_by_uid: Callable[[str], Any | None],
        find_substance_by_uid: Callable[[str], Any | None],
    ) -> Self | None:
        substance = None
        if uid is not None:
            substance_term: DictionaryTermSubstanceAR = find_substance_by_uid(uid)

            if substance_term is not None:
                pclass_term: SimpleDictionaryTermModel = (
                    SimpleDictionaryTermModel.from_ct_code(
                        c_code=substance_term.dictionary_term_vo.pclass_uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                )

                substance = cls(
                    substance_term_uid=uid,
                    substance_name=substance_term.dictionary_term_vo.name,
                    substance_unii=substance_term.dictionary_term_vo.dictionary_id,
                    pclass_term_uid=pclass_term.term_uid if pclass_term else None,
                    pclass_name=pclass_term.name if pclass_term else None,
                    pclass_id=pclass_term.dictionary_id if pclass_term else None,
                )

        return substance


class DictionaryTermSubstanceCreateInput(DictionaryTermCreateInput):
    pclass_uid: Annotated[str | None, Field(min_length=1)] = None


class DictionaryTermSubstanceEditInput(DictionaryTermEditInput):
    pclass_uid: Annotated[str | None, Field(min_length=1)] = None


class DictionaryTermVersion(DictionaryTerm):
    """
    Class for storing DictionaryTerm and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []
