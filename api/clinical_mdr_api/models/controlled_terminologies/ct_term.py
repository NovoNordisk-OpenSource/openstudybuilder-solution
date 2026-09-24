from datetime import datetime
from typing import Annotated, Any, Callable, Self, Sequence, overload

import neo4j.time
from pydantic import Field, field_validator

from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_term import (
    CTSimpleCodelistTermAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermNameAR,
    CTTermVO,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term_attributes import (
    CTTermAttributes,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term_codelist import (
    CTTermCodelist,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term_name import (
    CTTermName,
    CTTermNameTSParameterInput,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, PostInputModel
from common.config import settings


class CTTerm(BaseModel):

    term_uid: Annotated[str, Field()]

    catalogue_names: list[str] = Field(
        default_factory=list,
        json_schema_extra={"nullable": True, "remove_from_wildcard": True},
    )

    codelists: list[CTTermCodelist] = Field(default_factory=list)

    concept_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )

    nci_preferred_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    definition: Annotated[str, Field(json_schema_extra={"remove_from_wildcard": True})]

    sponsor_preferred_name: Annotated[str, Field()]

    sponsor_preferred_name_sentence_case: Annotated[str, Field()]

    library_name: Annotated[str, Field()]
    possible_actions: list[str] = Field(
        description=(
            "Holds those actions that can be performed on the CTTerm. "
            "Actions are: 'approve', 'edit', 'new_version'."
        ),
        default_factory=list,
    )

    @classmethod
    def from_ct_term_ars(
        cls,
        ct_term_name_ar: CTTermNameAR,
        ct_term_attributes_ar: CTTermAttributesAR,
        ct_term_codelists: CTTermVO,
    ) -> Self:
        return cls(
            term_uid=ct_term_attributes_ar.uid,
            catalogue_names=(
                ct_term_attributes_ar.ct_term_vo.catalogue_names
                if ct_term_attributes_ar.ct_term_vo.catalogue_names
                else []
            ),
            codelists=[
                CTTermCodelist(
                    codelist_uid=x.codelist_uid,
                    submission_value=x.submission_value,
                    order=x.order,
                    library_name=x.library_name,
                    codelist_submission_value=x.codelist_submission_value,
                    codelist_name=x.codelist_name,
                    codelist_concept_id=x.codelist_concept_id,
                    start_date=x.start_date,
                )
                for x in ct_term_codelists.codelists
            ],
            concept_id=ct_term_attributes_ar.ct_term_vo.concept_id,
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
            catalogue_names=ct_term_name_and_attributes.catalogue_names,
            codelists=ct_term_name_and_attributes.codelists,
            concept_id=ct_term_name_and_attributes.attributes.concept_id,
            nci_preferred_name=ct_term_name_and_attributes.attributes.nci_preferred_name,
            definition=ct_term_name_and_attributes.attributes.definition,
            library_name=ct_term_name_and_attributes.library_name,
            sponsor_preferred_name=ct_term_name_and_attributes.name.sponsor_preferred_name,
            sponsor_preferred_name_sentence_case=ct_term_name_and_attributes.name.sponsor_preferred_name_sentence_case,
            possible_actions=ct_term_name_and_attributes.attributes.possible_actions,
        )


class CTTermCodelistInput(BaseModel):
    codelist_uid: Annotated[str, Field()]
    submission_value: Annotated[str, Field()]
    order: Annotated[int | None, Field()] = None
    ordinal: Annotated[float | None, Field()] = None


class CTTermCreateInput(PostInputModel):
    catalogue_names: Annotated[list[str], Field()]

    codelists: list[CTTermCodelistInput]

    nci_preferred_name: Annotated[str | None, Field(min_length=1)] = None

    definition: Annotated[str, Field(min_length=1)]

    sponsor_preferred_name: Annotated[str, Field(min_length=1)]

    sponsor_preferred_name_sentence_case: Annotated[str, Field(min_length=1)]

    library_name: Annotated[str, Field(min_length=1)]

    concept_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )

    ts_parameter: Annotated[
        CTTermNameTSParameterInput | None,
        Field(
            description="Optional Trial Summary parameter properties to attach to the new CT term's name version. "
            "When provided, the corresponding scalar properties and graph relationships "
            "(`RELATED_STUDY_FIELD_SELECTION`, `HAS_SEMANTIC_DATA_TYPE`, `RESPONSE_CODELIST`, "
            "`RESPONSE_DICTIONARY`, `VALID_NULL_FLAVOR`) are wired on the initial save.",
        ),
    ] = None


class CTTermNameAndAttributes(BaseModel):

    term_uid: Annotated[str, Field()]
    catalogue_names: list[str] = Field(
        json_schema_extra={"remove_from_wildcard": True}, default_factory=list
    )
    codelists: list[CTTermCodelist] = Field(default_factory=list)

    library_name: Annotated[str, Field()]

    name: Annotated[CTTermName, Field()]

    attributes: Annotated[CTTermAttributes, Field()]

    @overload
    @classmethod
    def from_ct_term_ars(
        cls,
        ct_term_name_ar: CTTermNameAR,
        ct_term_attributes_ar: CTTermAttributesAR,
        ct_term_codelists: CTTermVO,
        include_ts_parameters: bool = True,
    ) -> Self: ...
    @overload
    @classmethod
    def from_ct_term_ars(
        cls,
        ct_term_name_ar: None,
        ct_term_attributes_ar: CTTermAttributesAR,
        ct_term_codelists: CTTermVO,
        include_ts_parameters: bool = True,
    ) -> None: ...
    @overload
    @classmethod
    def from_ct_term_ars(
        cls,
        ct_term_name_ar: CTTermNameAR,
        ct_term_attributes_ar: None,
        ct_term_codelists: CTTermVO,
        include_ts_parameters: bool = True,
    ) -> None: ...
    @overload
    @classmethod
    def from_ct_term_ars(
        cls,
        ct_term_name_ar: None,
        ct_term_attributes_ar: None,
        ct_term_codelists: CTTermVO,
        include_ts_parameters: bool = True,
    ) -> None: ...
    @classmethod
    def from_ct_term_ars(
        cls,
        ct_term_name_ar: CTTermNameAR | None,
        ct_term_attributes_ar: CTTermAttributesAR | None,
        ct_term_codelists: CTTermVO,
        include_ts_parameters: bool = True,
    ) -> Self | None:
        if not ct_term_name_ar or not ct_term_attributes_ar:
            return None
        catalogue_names = ct_term_attributes_ar.ct_term_vo.catalogue_names
        if catalogue_names is None:
            catalogue_names = []
        term_name_and_attributes = cls(
            term_uid=ct_term_attributes_ar.uid,
            catalogue_names=catalogue_names,
            library_name=ct_term_attributes_ar.library.name,
            name=CTTermName.from_ct_term_ar_without_common_term_fields(
                ct_term_name_ar, include_ts_parameters=include_ts_parameters
            ),
            attributes=CTTermAttributes.from_ct_term_ar_without_common_term_fields(
                ct_term_attributes_ar
            ),
        )

        term_name_and_attributes.codelists = [
            CTTermCodelist(
                codelist_uid=x.codelist_uid,
                submission_value=x.submission_value,
                order=x.order,
                library_name=x.library_name,
                codelist_submission_value=x.codelist_submission_value,
                codelist_name=x.codelist_name,
                codelist_concept_id=x.codelist_concept_id,
                start_date=x.start_date,
            )
            for x in ct_term_codelists.codelists
        ]

        return term_name_and_attributes


class CTTermNewCodelist(BaseModel):
    codelist_uid: Annotated[str, Field()]
    order: Annotated[int, Field(ge=0, le=settings.max_int_neo4j)]
    submission_value: Annotated[str, Field()]


class SimpleCTTermAttributes(BaseModel):

    uid: Annotated[str, Field()]
    preferred_term: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @overload
    @classmethod
    def from_term_uid(
        cls, uid: str, find_term_by_uid: Callable[[str], Any | None]
    ) -> Self: ...
    @overload
    @classmethod
    def from_term_uid(
        cls, uid: None, find_term_by_uid: Callable[[str], Any | None]
    ) -> None: ...
    @classmethod
    def from_term_uid(
        cls, uid: str | None, find_term_by_uid: Callable[[str], Any | None]
    ) -> Self | None:
        term_model = None

        if uid is not None:
            term = find_term_by_uid(uid)
            if term is not None:
                term_model = cls(
                    uid=uid,
                    preferred_term=term.ct_term_vo.preferred_term,
                )
            else:
                term_model = cls(uid=uid, preferred_term=None)
        else:
            term_model = None
        return term_model


class SimpleCTTermNameWithConflictFlag(BaseModel):

    term_uid: Annotated[str, Field()]
    sponsor_preferred_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    queried_effective_date: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    date_conflict: Annotated[
        bool | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @field_validator("queried_effective_date", mode="before")
    @staticmethod
    def convert_datetime(value: neo4j.time.DateTime | None) -> datetime | None:
        if isinstance(value, neo4j.time.DateTime):
            return value.to_native()
        return value

    @overload
    @classmethod
    def from_ct_code(
        cls,
        c_code: str,
        find_term_by_uid: Callable[[str], Any | None],
        at_specific_date=None,
    ) -> Self: ...
    @overload
    @classmethod
    def from_ct_code(
        cls,
        c_code: None,
        find_term_by_uid: Callable[[str], Any | None],
        at_specific_date=None,
    ) -> None: ...
    @classmethod
    def from_ct_code(
        cls,
        c_code: str | None,
        find_term_by_uid: Callable[..., Any | None],
        at_specific_date=None,
    ) -> Self | None:
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
        return simple_ctterm_model

    @classmethod
    def from_ct_codes(
        cls,
        c_codes: Sequence[str],
        find_term_by_uids: Callable[..., list[CTTermNameAR] | None],
        at_specific_date=None,
    ) -> list[Self]:
        simple_ctterm_models = []
        if c_codes:
            terms: list[CTTermNameAR] | None = (
                find_term_by_uids(term_uids=c_codes, at_specific_date=at_specific_date)
                or []
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


class CTTermUidInput(BaseModel):
    """Minimal input model accepting only a CT term UID.

    Used in POST/PATCH input models to align the input shape with the
    nested-object shape returned by the corresponding GET response model.
    """

    term_uid: Annotated[str, Field()]


class TermWithCodelistMetadata(BaseModel):
    term_uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    submission_value: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    codelist_uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    codelist_submission_value: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class SimpleTermModel(BaseModel):

    term_uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None

    @overload
    @classmethod
    def from_ct_code(
        cls,
        c_code: str,
        find_term_by_uid: Callable[[str], Any | None],
        at_specific_date=None,
    ) -> Self: ...
    @overload
    @classmethod
    def from_ct_code(
        cls,
        c_code: None,
        find_term_by_uid: Callable[[str], Any | None],
        at_specific_date=None,
    ) -> None: ...
    @classmethod
    def from_ct_code(
        cls,
        c_code: str | None,
        find_term_by_uid: Callable[..., Any | None],
        at_specific_date=None,
    ) -> Self | None:
        simple_term_model: Self | SimpleDictionaryTermModel | None = None
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

        return simple_term_model

    @classmethod
    def from_input(cls, input_data) -> Self:
        return cls(
            term_uid=input_data.term_uid,
            name=input_data.name,
        )


# Similar to SimpleTermModel, but includes codelist data
class SimpleCodelistTermModel(BaseModel):
    @classmethod
    def from_term_and_codelist_uids(
        cls,
        term_uid: str,
        codelist_uid: str,
        find_term_by_uid: Callable[..., Any | None],
        find_codelist_by_uid: Callable[[str], Any | None],
        find_codelist_term_by_uids: Callable[[str, str], Any | None],
        at_specific_date=None,
    ) -> Self | None:
        simple_term_model = None
        if term_uid is not None and codelist_uid is not None:
            if "ct_term_generic_repository" in find_term_by_uid.__module__:
                term = find_term_by_uid(term_uid, at_specific_date=at_specific_date)
            else:
                term = find_term_by_uid(term_uid)

            codelist = find_codelist_by_uid(codelist_uid)
            if term is not None and codelist is not None:
                codelist_term_data = find_codelist_term_by_uids(term_uid, codelist_uid)
                simple_term_model = cls(
                    term_uid=term_uid,
                    term_name=term.ct_term_vo.name,
                    codelist_uid=codelist_uid,
                    codelist_name=codelist.ct_codelist_vo.name,
                    order=codelist_term_data.order,
                    preferred_term=codelist_term_data.preferred_term,
                    submission_value=codelist_term_data.submission_value,
                    codelist_submission_value=codelist_term_data.codelist_submission_value,
                    queried_effective_date=at_specific_date,
                )
        else:
            simple_term_model = None
        return simple_term_model

    @classmethod
    def from_term_uid_and_codelist_submval(
        cls,
        term_uid: str | None,
        codelist_submission_value: str | None,
        find_codelist_term_by_uid_and_submission_value: Callable[
            ..., CTSimpleCodelistTermAR | None
        ],
        at_specific_date_time=None,
    ) -> Self | None:
        simple_term_model = None
        if term_uid is not None and codelist_submission_value is not None:
            codelist_term_data = find_codelist_term_by_uid_and_submission_value(
                term_uid,
                codelist_submission_value,
                at_specific_date_time=at_specific_date_time,
            )

            if codelist_term_data is not None:
                queried_date = (
                    at_specific_date_time
                    if not codelist_term_data.ct_simple_codelist_term_vo.date_conflict
                    else None
                )
                simple_term_model = cls(
                    term_uid=term_uid,
                    term_name=codelist_term_data.ct_simple_codelist_term_vo.term_name,
                    preferred_term=codelist_term_data.ct_simple_codelist_term_vo.preferred_term,
                    codelist_uid=codelist_term_data.ct_simple_codelist_term_vo.codelist_uid,
                    codelist_name=codelist_term_data.ct_simple_codelist_term_vo.codelist_name,
                    order=codelist_term_data.ct_simple_codelist_term_vo.order,
                    submission_value=codelist_term_data.ct_simple_codelist_term_vo.submission_value,
                    codelist_submission_value=codelist_term_data.ct_simple_codelist_term_vo.codelist_submission_value,
                    queried_effective_date=queried_date,
                    date_conflict=codelist_term_data.ct_simple_codelist_term_vo.date_conflict,
                )
        else:
            simple_term_model = None
        return simple_term_model

    term_uid: Annotated[str, Field()]
    term_name: Annotated[str, Field()]
    preferred_term: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    codelist_uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    codelist_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    codelist_submission_value: Annotated[
        str | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    order: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    submission_value: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    queried_effective_date: Annotated[datetime | None, Field()] = None
    date_conflict: Annotated[bool | None, Field()] = None


class SimpleDictionaryTermModel(SimpleTermModel):
    dictionary_id: Annotated[
        str | None,
        Field(
            description="Id if item in the external dictionary",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class SimpleTermName(BaseModel):
    sponsor_preferred_name: Annotated[str, Field()]
    sponsor_preferred_name_sentence_case: Annotated[str, Field()]


class SimpleTermAttributes(BaseModel):
    nci_preferred_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ]


class SimpleCTTermNameAndAttributes(BaseModel):
    term_uid: Annotated[str, Field()]
    name: Annotated[SimpleTermName, Field()]
    attributes: Annotated[SimpleTermAttributes, Field()]


class CTTermCodelists(BaseModel):
    @classmethod
    def from_ct_term_codelists(
        cls, term_uid: str, ct_term_codelists: list[CTTermCodelist]
    ) -> Self:
        term_codelists = cls(
            term_uid=term_uid,
            codelists=[
                CTTermCodelist(
                    codelist_uid=x.codelist_uid,
                    submission_value=x.submission_value,
                    order=x.order,
                    library_name=x.library_name,
                    codelist_submission_value=x.codelist_submission_value,
                    codelist_name=x.codelist_name,
                    codelist_concept_id=x.codelist_concept_id,
                    start_date=x.start_date,
                )
                for x in ct_term_codelists
            ],
        )

        return term_codelists

    term_uid: Annotated[str, Field()]
    codelists: Annotated[list[CTTermCodelist], Field()]


class CTTermRelative(BaseModel):
    relationship_type: Annotated[str, Field()]

    name: Annotated[CTTermName, Field()]

    attributes: Annotated[CTTermAttributes, Field()]


class CTTermRelatives(BaseModel):
    @classmethod
    def from_related_terms(
        cls,
        term_uid: str,
        ct_term_parents: list[CTTermRelative],
        ct_term_children: list[CTTermRelative],
    ) -> Self:
        related = cls(
            term_uid=term_uid, parents=ct_term_parents, children=ct_term_children
        )
        return related

    term_uid: Annotated[str, Field()]
    parents: Annotated[list[CTTermRelative], Field()]
    children: Annotated[list[CTTermRelative], Field()]
