from datetime import datetime
from typing import Annotated, Any, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermNameAR,
    CTTermNameVO,
    TSParameterCardinality,
    TSParameterRequiredLevel,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel

__all__ = ["TSParameterCardinality", "TSParameterRequiredLevel"]


class SemanticDataType(BaseModel):
    uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    sponsor_preferred_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class CTResponseCodelist(BaseModel):
    """Reference to a CT response codelist (uid + sponsor preferred name)."""

    uid: Annotated[str, Field(description="UID of the response CTCodelistRoot.")]
    sponsor_preferred_name: Annotated[
        str | None,
        Field(
            description="Sponsor preferred name of the response codelist.",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class CTValidNullFlavorTerm(BaseModel):
    """Reference to a Null Flavor CT term (uid + sponsor preferred name)."""

    uid: Annotated[str, Field(description="UID of the Null Flavor CTTermRoot.")]
    sponsor_preferred_name: Annotated[
        str | None,
        Field(
            description="Sponsor preferred name of the Null Flavor CT term.",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class CTTermName(BaseModel):
    @classmethod
    def from_ct_term_ar(
        cls, ct_term_name_ar: CTTermNameAR, include_ts_parameters: bool = True
    ) -> Self:
        catalogue_names = (
            ct_term_name_ar.ct_term_vo.catalogue_names
            if ct_term_name_ar.ct_term_vo.catalogue_names
            else []
        )
        vo = ct_term_name_ar.ct_term_vo
        ts_kwargs = _build_ts_kwargs(vo) if include_ts_parameters else {}
        return cls(
            term_uid=ct_term_name_ar.uid,
            catalogue_names=catalogue_names,
            sponsor_preferred_name=vo.name,
            sponsor_preferred_name_sentence_case=vo.name_sentence_case,
            library_name=Library.from_library_vo(ct_term_name_ar.library).name,
            possible_actions=sorted(
                [_.value for _ in ct_term_name_ar.get_possible_actions()]
            ),
            start_date=ct_term_name_ar.item_metadata.start_date,
            end_date=ct_term_name_ar.item_metadata.end_date,
            status=ct_term_name_ar.item_metadata.status.value,
            version=ct_term_name_ar.item_metadata.version,
            change_description=ct_term_name_ar.item_metadata.change_description,
            author_username=ct_term_name_ar.item_metadata.author_username,
            queried_effective_date=vo.queried_effective_date,
            date_conflict=vo.date_conflict,
            **ts_kwargs,
        )

    @classmethod
    def from_ct_term_ar_without_common_term_fields(
        cls, ct_term_name_ar: CTTermNameAR, include_ts_parameters: bool = True
    ) -> Self:
        vo = ct_term_name_ar.ct_term_vo
        ts_kwargs = _build_ts_kwargs(vo) if include_ts_parameters else {}
        return cls(
            sponsor_preferred_name=vo.name,
            sponsor_preferred_name_sentence_case=vo.name_sentence_case,
            possible_actions=sorted(
                [_.value for _ in ct_term_name_ar.get_possible_actions()]
            ),
            start_date=ct_term_name_ar.item_metadata.start_date,
            end_date=ct_term_name_ar.item_metadata.end_date,
            status=ct_term_name_ar.item_metadata.status.value,
            version=ct_term_name_ar.item_metadata.version,
            change_description=ct_term_name_ar.item_metadata.change_description,
            author_username=ct_term_name_ar.item_metadata.author_username,
            queried_effective_date=vo.queried_effective_date,
            date_conflict=vo.date_conflict,
            **ts_kwargs,
        )

    term_uid: Annotated[str, Field()] = ""

    catalogue_names: Annotated[
        list[str], Field(json_schema_extra={"remove_from_wildcard": True})
    ] = []

    sponsor_preferred_name: Annotated[str, Field()]

    sponsor_preferred_name_sentence_case: Annotated[str, Field()]

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
    queried_effective_date: Annotated[
        datetime | None,
        Field(
            json_schema_extra={"nullable": True},
            description="Indicates the actual date at which the term was queried.",
        ),
    ] = None
    date_conflict: Annotated[
        bool,
        Field(
            description="Indicates if the term had a date conflict upon retrieval. If True, then the Latest Final was returned.",
        ),
    ] = False
    reference: Annotated[
        str | None,
        Field(
            json_schema_extra={"nullable": True},
            description="Reference terminology identifier (e.g. 'ClinicalTrials.gov', 'ISO8601'). Used for TSVCDREF in SDTM TS listings.",
        ),
    ] = None
    required_level: Annotated[
        TSParameterRequiredLevel | None,
        Field(
            json_schema_extra={"nullable": True},
            description="Required | Conditionally Required | If Applicable",
        ),
    ] = None
    cardinality: Annotated[
        TSParameterCardinality | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    notes: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    osb_field_name: Annotated[
        str | None,
        Field(
            json_schema_extra={"nullable": True},
            description="Name of the MetaStudyField this TS parameter maps to.",
        ),
    ] = None
    osb_page_reference: Annotated[
        str | None,
        Field(
            json_schema_extra={"nullable": True},
            description="OSB page reference for this TS parameter.",
        ),
    ] = None
    semantic_data_type: Annotated[
        SemanticDataType | None,
        Field(
            json_schema_extra={"nullable": True},
            description="Nested model representing the data type sponsor term (HAS_DATA_TYPE). Contains uid and sponsor_preferred_name.",
        ),
    ] = None
    response_codelist: Annotated[
        CTResponseCodelist | None,
        Field(
            json_schema_extra={"nullable": True},
            description="Nested model for the CTCodelistRoot providing allowed response values (RESPONSE_CODELIST). Contains uid and sponsor_preferred_name.",
        ),
    ] = None
    response_dictionary_uids: Annotated[
        list[str] | None,
        Field(
            json_schema_extra={"nullable": True},
            description="UIDs of DictionaryCodelistRoot nodes for dictionary response values (RESPONSE_DICTIONARY).",
        ),
    ] = None
    valid_null_flavor_terms: Annotated[
        list[CTValidNullFlavorTerm] | None,
        Field(
            json_schema_extra={"nullable": True},
            description="Nested models for CTTermRoot nodes representing valid null flavors (VALID_NULL_FLAVOR). Each contains uid and sponsor_preferred_name.",
        ),
    ] = None
    possible_actions: list[str] = Field(
        description=(
            "Holds those actions that can be performed on the CTTermName. "
            "Actions are: 'approve', 'edit', 'new_version'."
        ),
        default_factory=list,
    )


class CTTermNameSimple(BaseModel):
    term_uid: Annotated[str, Field()]
    sponsor_preferred_name: Annotated[str, Field()]


class CTTermNameVersion(CTTermName):
    """
    Class for storing CTTermName and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)


class CTTermNameEditInput(PatchInputModel):
    sponsor_preferred_name: Annotated[str | None, Field(min_length=1)] = None
    sponsor_preferred_name_sentence_case: Annotated[str | None, Field(min_length=1)] = (
        None
    )
    change_description: Annotated[str, Field(min_length=1)]


class CTTermNameTSParameterInput(BaseModel):
    osb_field_name: Annotated[
        str | None,
        Field(
            min_length=1,
            description="The MetaStudyField name to link via RELATED_STUDY_FIELD_SELECTION. "
            "Pass null to remove an existing link.",
        ),
    ] = None
    osb_page_reference: Annotated[
        str | None,
        Field(
            min_length=1,
            description="OSB page reference for this TS parameter. Stored on the linked MetaStudyField "
            "(via RELATED_STUDY_FIELD_SELECTION); requires `osb_field_name` to be set.",
        ),
    ] = None
    semantic_data_type_uid: Annotated[
        str | None,
        Field(
            description="UID of the CTTermRoot representing the data type for the MetaStudyField (HAS_DATA_TYPE). "
            "The term must belong to the DataType codelist. Pass null to remove an existing link.",
        ),
    ] = None
    response_codelist_uid: Annotated[
        str | None,
        Field(
            description="UID of the CTCodelistRoot providing allowed response values (RESPONSE_CODELIST). "
            "Pass null to remove an existing link.",
        ),
    ] = None
    response_dictionary_uids: Annotated[
        list[str] | None,
        Field(
            description="UIDs of DictionaryCodelistRoot nodes for dictionary response values (RESPONSE_DICTIONARY). "
            "Replaces all existing links. Pass null or empty list to remove.",
        ),
    ] = None
    valid_null_flavor_term_uids: Annotated[
        list[str] | None,
        Field(
            description="UIDs of CTTermRoot nodes representing valid null flavors (e.g. NA, PINF). "
            "The service manages CTTermContext wrappers. Replaces all existing links. Pass null or empty list to remove.",
        ),
    ] = None
    reference: Annotated[
        str | None,
        Field(
            description="Reference terminology identifier (e.g. 'ClinicalTrials.gov', 'EUDRACT', 'ISO8601'). "
            "Used for TSVCDREF in SDTM TS listings.",
        ),
    ] = None
    required_level: Annotated[
        TSParameterRequiredLevel | None,
        Field(description="Required | Conditionally Required | If Applicable"),
    ] = None
    cardinality: Annotated[
        TSParameterCardinality | None,
        Field(),
    ] = None
    notes: Annotated[str | None, Field()] = None


class CTTermNameTSParameterOutput(BaseModel):
    term_uid: Annotated[str, Field(description="The CT term UID that was updated.")]
    osb_field_name: Annotated[str | None, Field()] = None
    osb_page_reference: Annotated[str | None, Field()] = None
    semantic_data_type: Annotated[SemanticDataType | None, Field()] = None
    response_codelist: Annotated[CTResponseCodelist | None, Field()] = None
    response_dictionary_uids: Annotated[list[str] | None, Field()] = None
    valid_null_flavor_terms: Annotated[list[CTValidNullFlavorTerm] | None, Field()] = (
        None
    )
    reference: Annotated[str | None, Field()] = None
    required_level: Annotated[TSParameterRequiredLevel | None, Field()] = None
    cardinality: Annotated[TSParameterCardinality | None, Field()] = None
    notes: Annotated[str | None, Field()] = None


def build_valid_null_flavor_terms(
    vo: CTTermNameVO,
) -> list[CTValidNullFlavorTerm] | None:
    """Pair valid null flavor uids with names; emit nested models or None."""
    uids = vo.valid_null_flavor_term_uids
    if not uids:
        return None
    names = vo.valid_null_flavor_term_names or ()
    name_by_index = list(names) + [None] * max(0, len(uids) - len(names))
    return [
        CTValidNullFlavorTerm(uid=uid, sponsor_preferred_name=name_by_index[idx])
        for idx, uid in enumerate(uids)
    ]


def _build_ts_kwargs(vo: CTTermNameVO) -> dict[str, Any]:
    """Build the dict of Trial Summary parameter kwargs for CTTermName builders.

    Returned only when the caller wants TS-parameter fields populated; when the
    API caller opts out via ``include_ts_parameters=False`` these keys are left
    unset on the response model so ``response_model_exclude_unset=True`` omits
    them from the serialized payload.
    """
    return {
        "reference": vo.reference,
        "required_level": vo.required_level,
        "cardinality": vo.cardinality,
        "notes": vo.notes,
        "osb_field_name": vo.osb_field_name,
        "osb_page_reference": vo.osb_page_reference,
        "semantic_data_type": (
            SemanticDataType(
                uid=vo.semantic_data_type_uid,
                sponsor_preferred_name=vo.semantic_data_type_name,
            )
            if vo.semantic_data_type_uid
            else None
        ),
        "response_codelist": (
            CTResponseCodelist(
                uid=vo.response_codelist_uid,
                sponsor_preferred_name=vo.response_codelist_name,
            )
            if vo.response_codelist_uid
            else None
        ),
        "response_dictionary_uids": (
            list(vo.response_dictionary_uids) if vo.response_dictionary_uids else None
        ),
        "valid_null_flavor_terms": build_valid_null_flavor_terms(vo),
    }
