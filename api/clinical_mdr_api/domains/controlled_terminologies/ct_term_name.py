from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import AbstractSet, Callable, Self

from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
)
from common.exceptions import (
    AlreadyExistsException,
    BusinessLogicException,
    ValidationException,
)


class TSParameterRequiredLevel(StrEnum):
    """Allowed values for the ``required_level`` of a Trial Summary parameter CT term."""

    REQUIRED = "Required"
    IF_APPLICABLE = "If Applicable"
    CONDITIONALLY_REQUIRED = "Conditionally Required"
    OPTIONAL = "Optional"


class TSParameterCardinality(StrEnum):
    """Allowed values for the ``cardinality`` of a Trial Summary parameter CT term."""

    ONE = "One"
    MANY = "Many"


@dataclass(frozen=True)
class CTTermCodelistVO:
    codelist_uid: str
    submission_value: str
    start_date: datetime
    order: int | None
    codelist_name: str
    codelist_submission_value: str
    library_name: str
    codelist_concept_id: str | None = None
    ordinal: float | None = None


@dataclass(frozen=True)
class CTTermVO:
    codelists: list[CTTermCodelistVO]
    catalogues: list[str]


@dataclass(frozen=True)
class CTTermNameVO:
    """
    The CTTermNameVO acts as the value object for a single CTTerm name
    """

    name: str
    name_sentence_case: str
    catalogue_names: list[str] | None = None
    queried_effective_date: datetime | None = None
    date_conflict: bool = False
    reference: str | None = None
    required_level: TSParameterRequiredLevel | None = None
    cardinality: TSParameterCardinality | None = None
    notes: str | None = None
    # TS relationship targets — carried through the edit flow, wired by _maintain_parameters
    osb_field_name: str | None = None
    osb_page_reference: str | None = None
    semantic_data_type_uid: str | None = None
    semantic_data_type_name: str | None = None
    response_codelist_uid: str | None = None
    response_codelist_name: str | None = None
    response_dictionary_uids: tuple[str, ...] | None = None
    valid_null_flavor_term_uids: tuple[str, ...] | None = None
    valid_null_flavor_term_names: tuple[str | None, ...] | None = None

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: str,
        catalogue_names: list[str],
        queried_effective_date: datetime | None = None,
        date_conflict: bool = False,
        reference: str | None = None,
        required_level: str | None = None,
        cardinality: str | None = None,
        notes: str | None = None,
        osb_field_name: str | None = None,
        osb_page_reference: str | None = None,
        semantic_data_type_uid: str | None = None,
        semantic_data_type_name: str | None = None,
        response_codelist_uid: str | None = None,
        response_codelist_name: str | None = None,
        response_dictionary_uids: tuple[str, ...] | None = None,
        valid_null_flavor_term_uids: tuple[str, ...] | None = None,
        valid_null_flavor_term_names: tuple[str | None, ...] | None = None,
    ) -> Self:
        ct_term_name_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            catalogue_names=catalogue_names,
            queried_effective_date=queried_effective_date,
            date_conflict=date_conflict,
            reference=reference,
            required_level=(
                TSParameterRequiredLevel(required_level) if required_level else None
            ),
            cardinality=TSParameterCardinality(cardinality) if cardinality else None,
            notes=notes,
            osb_field_name=osb_field_name,
            osb_page_reference=osb_page_reference,
            semantic_data_type_uid=semantic_data_type_uid,
            semantic_data_type_name=semantic_data_type_name,
            response_codelist_uid=response_codelist_uid,
            response_codelist_name=response_codelist_name,
            response_dictionary_uids=response_dictionary_uids,
            valid_null_flavor_term_uids=valid_null_flavor_term_uids,
            valid_null_flavor_term_names=valid_null_flavor_term_names,
        )

        return ct_term_name_vo

    @classmethod
    def from_input_values(
        cls,
        name: str,
        name_sentence_case: str,
        catalogue_names: list[str] | None = None,
        reference: str | None = None,
        required_level: str | None = None,
        cardinality: str | None = None,
        notes: str | None = None,
        osb_field_name: str | None = None,
        osb_page_reference: str | None = None,
        semantic_data_type_uid: str | None = None,
        response_codelist_uid: str | None = None,
        response_dictionary_uids: tuple[str, ...] | None = None,
        valid_null_flavor_term_uids: tuple[str, ...] | None = None,
    ) -> Self:

        ct_term_name_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            catalogue_names=catalogue_names,
            reference=reference,
            required_level=(
                TSParameterRequiredLevel(required_level) if required_level else None
            ),
            cardinality=TSParameterCardinality(cardinality) if cardinality else None,
            notes=notes,
            osb_field_name=osb_field_name,
            osb_page_reference=osb_page_reference,
            semantic_data_type_uid=semantic_data_type_uid,
            response_codelist_uid=response_codelist_uid,
            response_dictionary_uids=response_dictionary_uids,
            valid_null_flavor_term_uids=valid_null_flavor_term_uids,
        )

        return ct_term_name_vo

    def validate(
        self,
    ) -> None:
        ValidationException.raise_if(
            self.name_sentence_case.lower() != self.name.lower(),
            msg=f"{self.name_sentence_case} isn't an independent case version of {self.name}",
        )


@dataclass
class CTTermNameAR(LibraryItemAggregateRootBase):
    _ct_term_name_vo: CTTermNameVO

    @property
    def name(self) -> str:
        return self._ct_term_name_vo.name

    @property
    def ct_term_vo(self) -> CTTermNameVO:
        return self._ct_term_name_vo

    def _is_edit_allowed_in_non_editable_library(self) -> bool:
        return True

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        ct_term_name_vo: CTTermNameVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        ct_term_ar = cls(
            _uid=uid,
            _ct_term_name_vo=ct_term_name_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return ct_term_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        ct_term_name_vo: CTTermNameVO,
        library: LibraryVO,
        start_date: datetime | None = None,
        generate_uid_callback: Callable[[], str | None] = lambda: None,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id, start_date=start_date
        )
        BusinessLogicException.raise_if_not(
            library.is_editable,
            msg=f"Library with Name '{library.name}' doesn't allow creation of objects.",
        )
        return cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _ct_term_name_vo=ct_term_name_vo,
        )

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        ct_term_vo: CTTermNameVO,
        term_uid: str,
        term_exists_by_name_in_codelists_callback: Callable[[str, str], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        AlreadyExistsException.raise_if(
            ct_term_vo.name
            and term_exists_by_name_in_codelists_callback(
                ct_term_vo.name,
                term_uid,
            )
            and self.ct_term_vo.name != ct_term_vo.name,
            "CT Term Name",
            ct_term_vo.name,
            "Name",
        )
        ct_term_vo.validate()
        if self._ct_term_name_vo != ct_term_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._ct_term_name_vo = ct_term_vo

    def create_new_version(self, author_id: str) -> None:
        """
        Puts object into DRAFT status with relevant changes to version numbers.
        """
        super()._create_new_version(author_id=author_id)

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        """
        Returns list of possible actions
        """
        if (
            self._item_metadata.status == LibraryItemStatus.DRAFT
            and self._item_metadata.major_version == 0
        ):
            return {ObjectAction.APPROVE, ObjectAction.EDIT, ObjectAction.DELETE}
        if self._item_metadata.status == LibraryItemStatus.DRAFT:
            return {ObjectAction.APPROVE, ObjectAction.EDIT}
        if self._item_metadata.status == LibraryItemStatus.FINAL:
            return {ObjectAction.NEWVERSION, ObjectAction.INACTIVATE}
        if self._item_metadata.status == LibraryItemStatus.RETIRED:
            return {ObjectAction.REACTIVATE}
        return frozenset()
