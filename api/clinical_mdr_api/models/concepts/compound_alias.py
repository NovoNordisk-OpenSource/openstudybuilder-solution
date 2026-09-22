from typing import Annotated, Callable, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.compound import CompoundAR
from clinical_mdr_api.domains.concepts.compound_alias import CompoundAliasAR
from clinical_mdr_api.models.concepts.compound import SimpleCompound
from clinical_mdr_api.models.concepts.concept import (
    Concept,
    ExtendedConceptPatchInput,
    ExtendedConceptPostInput,
)
from clinical_mdr_api.models.libraries.library import Library


class CompoundAlias(Concept):
    possible_actions: Annotated[
        list[str],
        Field(
            description=(
                "Holds those actions that can be performed on CompoundAlias. "
                "Actions are: 'approve', 'edit', 'new_version'."
            ),
        ),
    ]

    compound: Annotated[SimpleCompound, Field()]
    is_preferred_synonym: Annotated[bool, Field()] = False

    @classmethod
    def from_ar(
        cls,
        ar: CompoundAliasAR,
        find_compound_by_uid: Callable[[str], CompoundAR | None],
    ) -> Self:
        return cls(
            uid=ar.uid,
            name=ar.name,
            name_sentence_case=ar.concept_vo.name_sentence_case,
            definition=ar.concept_vo.definition,
            abbreviation=ar.concept_vo.abbreviation,
            compound=SimpleCompound.from_uid(
                ar.concept_vo.compound_uid, find_by_uid=find_compound_by_uid
            ),
            is_preferred_synonym=(
                ar.concept_vo.is_preferred_synonym
                if ar.concept_vo.is_preferred_synonym
                else False
            ),
            library_name=Library.from_library_vo(ar.library).name,
            start_date=ar.item_metadata.start_date,
            end_date=ar.item_metadata.end_date,
            status=ar.item_metadata.status.value,
            version=ar.item_metadata.version,
            change_description=ar.item_metadata.change_description,
            author_username=ar.item_metadata.author_username,
            possible_actions=sorted([_.value for _ in ar.get_possible_actions()]),
        )


class CompoundAliasCreateInput(ExtendedConceptPostInput):
    compound_uid: Annotated[str, Field(min_length=1)]
    is_preferred_synonym: Annotated[bool, Field()] = False


class CompoundAliasEditInput(ExtendedConceptPatchInput):
    compound_uid: Annotated[str, Field(min_length=1)]
    is_preferred_synonym: Annotated[bool, Field()] = False
    change_description: Annotated[str, Field(min_length=1)]


class CompoundAliasVersion(CompoundAlias):
    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)
