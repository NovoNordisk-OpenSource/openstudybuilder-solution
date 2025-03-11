from datetime import datetime
from typing import Annotated, Any, Callable, Self, Sequence

from pydantic import Field

from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.models.controlled_terminologies.ct_term_attributes import (
    CTTermAttributes,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term_codelist import (
    CTTermCodelist,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term_name import CTTermName
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, PostInputModel
from common import config


class CTTerm(BaseModel):
    @classmethod
    def from_ct_term_ars(
        cls, ct_term_name_ar: CTTermNameAR, ct_term_attributes_ar: CTTermAttributesAR
    ) -> Self:
        return cls(
            term_uid=ct_term_attributes_ar.uid,
            catalogue_name=ct_term_attributes_ar.ct_term_vo.catalogue_name,
            codelists=[
                CTTermCodelist(
                    codelist_uid=x.codelist_uid,
                    order=x.order,
                    library_name=x.library_name,
                )
                for x in ct_term_name_ar.ct_term_vo.codelists
            ],
            concept_id=ct_term_attributes_ar.ct_term_vo.concept_id,
            code_submission_value=ct_term_attributes_ar.ct_term_vo.code_submission_value,
            name_submission_value=ct_term_attributes_ar.ct_term_vo.name_submission_value,
            nci_preferred_name=ct_term_attributes_ar.ct_term_vo.preferred_term,
            definition=ct_term_attributes_ar.ct_term_vo.definition,
            library_name=Library.from_library_vo(ct_term_attributes_ar.library).name,
            sponsor_preferred_name=ct_term_name_ar.ct_term_vo.name,
            sponsor_preferred_name_sentence_case=ct_term_name_ar.ct_term_vo.name_sentence_case,
            possible_actions=sorted(
                [_.value for _ in ct_term_attributes_ar.get_possible_actions()]
            ),
        )

    @classmethod
    def from_ct_term_name_and_attributes(
        cls, ct_term_name_and_attributes: "CTTermNameAndAttributes"
    ) -> Self:
        return cls(
            term_uid=ct_term_name_and_attributes.term_uid,
            catalogue_name=ct_term_name_and_attributes.catalogue_name,
            codelists=ct_term_name_and_attributes.codelists,
            concept_id=ct_term_name_and_attributes.attributes.concept_id,
            code_submission_value=ct_term_name_and_attributes.attributes.code_submission_value,
            name_submission_value=ct_term_name_and_attributes.attributes.name_submission_value,
            nci_preferred_name=ct_term_name_and_attributes.attributes.nci_preferred_name,
            definition=ct_term_name_and_attributes.attributes.definition,
            library_name=ct_term_name_and_attributes.library_name,
            sponsor_preferred_name=ct_term_name_and_attributes.name.sponsor_preferred_name,
            sponsor_preferred_name_sentence_case=ct_term_name_and_attributes.name.sponsor_preferred_name_sentence_case,
            possible_actions=ct_term_name_and_attributes.attributes.possible_actions,
        )

    term_uid: Annotated[str, Field()]

    catalogue_name: Annotated[str, Field()]

    codelists: Annotated[list[CTTermCodelist], Field()] = []

    concept_id: Annotated[str | None, Field(nullable=True)] = None

    code_submission_value: Annotated[str | None, Field(nullable=True)] = None

    name_submission_value: Annotated[str | None, Field(nullable=True)] = None

    nci_preferred_name: Annotated[str, Field()]

    definition: Annotated[str, Field(remove_from_wildcard=True)]

    sponsor_preferred_name: Annotated[str, Field()]

    sponsor_preferred_name_sentence_case: Annotated[str, Field()]

    library_name: str
    possible_actions: Annotated[
        list[str],
        Field(
            description=(
                "Holds those actions that can be performed on the CTTerm. "
                "Actions are: 'approve', 'edit', 'new_version'."
            )
        ),
    ] = []


class CTTermCreateInput(PostInputModel):
    catalogue_name: Annotated[str, Field(min_length=1)]

    codelist_uid: Annotated[str, Field(min_length=1)]

    code_submission_value: Annotated[str, Field(min_length=1)]

    name_submission_value: Annotated[str | None, Field(nullable=True, min_length=1)] = (
        None
    )

    nci_preferred_name: Annotated[str, Field(min_length=1)]

    definition: Annotated[str, Field(min_length=1)]

    sponsor_preferred_name: Annotated[str, Field(min_length=1)]

    sponsor_preferred_name_sentence_case: Annotated[str, Field(min_length=1)]
    order: Annotated[
        int | None, Field(nullable=True, gt=0, lt=config.MAX_INT_NEO4J)
    ] = 999999
    library_name: Annotated[str, Field(min_length=1)]


class CTTermNameAndAttributes(BaseModel):
    @classmethod
    def from_ct_term_ars(
        cls, ct_term_name_ar: CTTermNameAR, ct_term_attributes_ar: CTTermAttributesAR
    ) -> Self:
        if not ct_term_name_ar or not ct_term_attributes_ar:
            return None
        term_name_and_attributes = cls(
            term_uid=ct_term_attributes_ar.uid,
            catalogue_name=ct_term_attributes_ar.ct_term_vo.catalogue_name,
            library_name=(
                Library.from_library_vo(ct_term_attributes_ar.library).name
                if ct_term_attributes_ar.library
                else None
            ),
            name=CTTermName.from_ct_term_ar_without_common_term_fields(ct_term_name_ar),
            attributes=CTTermAttributes.from_ct_term_ar_without_common_term_fields(
                ct_term_attributes_ar
            ),
        )
        term_name_and_attributes.codelists = [
            CTTermCodelist(
                codelist_uid=x.codelist_uid,
                order=x.order,
                library_name=x.library_name,
            )
            for x in ct_term_name_ar.ct_term_vo.codelists
        ]

        return term_name_and_attributes

    term_uid: Annotated[str, Field()]
    catalogue_name: Annotated[str, Field()]
    codelists: Annotated[list[CTTermCodelist], Field()] = []

    library_name: Annotated[str | None, Field(nullable=True)] = None

    name: Annotated[CTTermName, Field()]

    attributes: Annotated[CTTermAttributes, Field()]


class CTTermNewOrder(BaseModel):
    codelist_uid: Annotated[str, Field(min_length=1)]
    new_order: Annotated[int, Field()] = 999999


class SimpleCTTermAttributes(BaseModel):
    @classmethod
    def from_term_uid(
        cls, uid: str, find_term_by_uid: Callable[[str], Any | None]
    ) -> Self | None:
        term_model = None
        if uid is not None:
            term = find_term_by_uid(uid)
            if term is not None:
                term_model = cls(
                    uid=uid,
                    code_submission_value=term.ct_term_vo.code_submission_value,
                    preferred_term=term.ct_term_vo.preferred_term,
                )
            else:
                term_model = cls(
                    uid=uid, code_submission_value=None, preferred_term=None
                )
        else:
            term_model = None
        return term_model

    uid: Annotated[str, Field()]
    code_submission_value: Annotated[str | None, Field(nullable=True)] = None
    preferred_term: Annotated[str | None, Field(nullable=True)] = None


class SimpleCTTermNameWithConflictFlag(BaseModel):
    @classmethod
    def from_ct_code(
        cls,
        c_code: str,
        find_term_by_uid: Callable[[str], Any | None],
        at_specific_date=None,
    ) -> Self | Sequence[Self] | None:
        simple_ctterm_model = None
        if c_code is not None:
            if "ct_term_generic_repository" in find_term_by_uid.__module__:
                term = find_term_by_uid(c_code, at_specific_date=at_specific_date)
            else:
                term = find_term_by_uid(c_code)

            if term is not None:
                if hasattr(term, "ct_term_vo"):
                    simple_ctterm_model = cls(
                        term_uid=c_code,
                        sponsor_preferred_name=term.ct_term_vo.name,
                        queried_effective_date=term.ct_term_vo.queried_effective_date,
                        date_conflict=term.ct_term_vo.date_conflict,
                    )
            else:
                simple_ctterm_model = cls(term_uid=c_code)
        else:
            simple_ctterm_model = None
        return simple_ctterm_model

    @classmethod
    def from_ct_codes(
        cls,
        c_codes: Sequence[str],
        find_term_by_uids: Callable[[str], Any | None],
        at_specific_date=None,
    ) -> Self | Sequence[Self] | None:
        simple_ctterm_models = []
        if c_codes:
            terms: Sequence[CTTermNameAR] = find_term_by_uids(
                term_uids=c_codes, at_specific_date=at_specific_date
            )
            for term in terms:
                if hasattr(term, "ct_term_vo"):
                    simple_ctterm_models.append(
                        cls(
                            term_uid=term.uid,
                            sponsor_preferred_name=term.ct_term_vo.name,
                            queried_effective_date=term.ct_term_vo.queried_effective_date,
                            date_conflict=term.ct_term_vo.date_conflict,
                        )
                    )
        return simple_ctterm_models

    @classmethod
    def from_ct_term_ar(cls, ct_term_name_ar: CTTermNameAR) -> Self:
        return cls(
            term_uid=ct_term_name_ar.uid,
            sponsor_preferred_name=ct_term_name_ar.ct_term_vo.name,
            queried_effective_date=ct_term_name_ar.ct_term_vo.queried_effective_date,
            date_conflict=ct_term_name_ar.ct_term_vo.date_conflict,
        )

    term_uid: Annotated[str, Field()]
    sponsor_preferred_name: Annotated[str | None, Field(nullable=True)] = None
    queried_effective_date: Annotated[datetime | None, Field(nullable=True)] = None
    date_conflict: Annotated[bool | None, Field(nullable=True)] = None


class SimpleTermModel(BaseModel):
    @classmethod
    def from_ct_code(
        cls,
        c_code: str,
        find_term_by_uid: Callable[[str], Any | None],
        at_specific_date=None,
    ) -> Self | None:
        simple_term_model = None
        if c_code is not None:
            if "ct_term_generic_repository" in find_term_by_uid.__module__:
                term = find_term_by_uid(c_code, at_specific_date=at_specific_date)
            else:
                term = find_term_by_uid(c_code)

            if term is not None:
                if hasattr(term, "ct_term_vo"):
                    simple_term_model = cls(term_uid=c_code, name=term.ct_term_vo.name)
                elif hasattr(term, "dictionary_term_vo"):
                    simple_term_model = SimpleDictionaryTermModel(
                        term_uid=c_code,
                        name=term.dictionary_term_vo.name,
                        dictionary_id=getattr(
                            term.dictionary_term_vo, "dictionary_id", None
                        ),
                    )
            else:
                simple_term_model = cls(term_uid=c_code, name=None)
        else:
            simple_term_model = None
        return simple_term_model

    term_uid: str
    name: Annotated[str | None, Field(nullable=True)] = None


class SimpleDictionaryTermModel(SimpleTermModel):
    dictionary_id: Annotated[
        str | None,
        Field(
            description="Id if item in the external dictionary",
            nullable=True,
        ),
    ] = None


class SimpleTermName(BaseModel):
    sponsor_preferred_name: Annotated[str, Field()]
    sponsor_preferred_name_sentence_case: Annotated[str, Field()]


class SimpleTermAttributes(BaseModel):
    code_submission_value: Annotated[str | None, Field(nullable=True)] = None
    nci_preferred_name: Annotated[str | None, Field(nullable=True)] = None


class SimpleCTTermNameAndAttributes(BaseModel):
    term_uid: Annotated[str, Field()]
    name: Annotated[SimpleTermName, Field()]
    attributes: Annotated[SimpleTermAttributes, Field()]
