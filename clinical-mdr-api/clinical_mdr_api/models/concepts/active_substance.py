from typing import Annotated, Callable, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.active_substance import ActiveSubstanceAR
from clinical_mdr_api.domains.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domains.dictionaries.dictionary_term_substance import (
    DictionaryTermSubstanceAR,
)
from clinical_mdr_api.models.concepts.concept import VersionProperties
from clinical_mdr_api.models.dictionaries.dictionary_term import CompoundSubstance
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel


class ActiveSubstance(VersionProperties):
    uid: str

    analyte_number: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    short_number: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    long_number: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    inn: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    external_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    library_name: str
    unii: Annotated[
        CompoundSubstance | None, Field(json_schema_extra={"nullable": True})
    ] = None
    possible_actions: Annotated[
        list[str],
        Field(
            description=(
                "Holds those actions that can be performed on ActiveSubstances. "
                "Actions are: 'approve', 'edit', 'new_version'."
            )
        ),
    ]

    @classmethod
    def from_active_substance_ar(
        cls,
        active_substance_ar: ActiveSubstanceAR,
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_substance_term_by_uid: Callable[[str], DictionaryTermSubstanceAR | None],
    ) -> Self:
        return cls(
            uid=active_substance_ar.uid,
            unii=(
                CompoundSubstance.from_term_uid(
                    uid=active_substance_ar.concept_vo.unii_term_uid,
                    find_term_by_uid=find_dictionary_term_by_uid,
                    find_substance_by_uid=find_substance_term_by_uid,
                )
                if active_substance_ar.concept_vo.unii_term_uid
                else None
            ),
            analyte_number=active_substance_ar.concept_vo.analyte_number,
            short_number=active_substance_ar.concept_vo.short_number,
            long_number=active_substance_ar.concept_vo.long_number,
            inn=active_substance_ar.concept_vo.inn,
            external_id=active_substance_ar.concept_vo.external_id,
            library_name=Library.from_library_vo(active_substance_ar.library).name,
            start_date=active_substance_ar.item_metadata.start_date,
            end_date=active_substance_ar.item_metadata.end_date,
            status=active_substance_ar.item_metadata.status.value,
            version=active_substance_ar.item_metadata.version,
            change_description=active_substance_ar.item_metadata.change_description,
            author_username=active_substance_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in active_substance_ar.get_possible_actions()]
            ),
        )


class ActiveSubstanceCreateInput(PostInputModel):
    external_id: Annotated[str | None, Field(min_length=1)] = None
    analyte_number: Annotated[str | None, Field(min_length=1)] = None
    short_number: Annotated[str | None, Field(min_length=1)] = None
    long_number: Annotated[str | None, Field(min_length=1)] = None
    inn: Annotated[str | None, Field(min_length=1)] = None
    library_name: Annotated[str, Field(min_length=1)]
    unii_term_uid: Annotated[str | None, Field(min_length=1)] = None


class ActiveSubstanceEditInput(PatchInputModel):
    external_id: Annotated[str | None, Field(min_length=1)] = None
    analyte_number: Annotated[str | None, Field(min_length=1)] = None
    short_number: Annotated[str | None, Field(min_length=1)] = None
    long_number: Annotated[str | None, Field(min_length=1)] = None
    inn: Annotated[str | None, Field(min_length=1)] = None
    library_name: Annotated[str | None, Field(min_length=1)] = None
    unii_term_uid: Annotated[str | None, Field(min_length=1)] = None
    change_description: Annotated[str, Field(min_length=1)]


class ActiveSubstanceVersion(ActiveSubstance):
    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []


class SimpleActiveSubstance(BaseModel):
    uid: str
    analyte_number: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    short_number: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    long_number: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    inn: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    external_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    unii: Annotated[
        CompoundSubstance | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_concept_uid(
        cls,
        uid: str,
        find_by_uid: Callable[[str], ActiveSubstanceAR | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_substance_term_by_uid: Callable[[str], DictionaryTermSubstanceAR | None],
    ) -> Self | None:
        concept = None
        if uid is not None:
            val: ActiveSubstanceAR = find_by_uid(uid)

            if val is not None:
                concept = SimpleActiveSubstance(
                    uid=val.uid,
                    analyte_number=val.concept_vo.analyte_number,
                    short_number=val.concept_vo.short_number,
                    long_number=val.concept_vo.long_number,
                    inn=val.concept_vo.inn,
                    external_id=val.concept_vo.external_id,
                    unii=CompoundSubstance.from_term_uid(
                        uid=val.concept_vo.unii_term_uid,
                        find_term_by_uid=find_dictionary_term_by_uid,
                        find_substance_by_uid=find_substance_term_by_uid,
                    ),
                )

        return concept
