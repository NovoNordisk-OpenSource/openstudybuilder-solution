from dataclasses import dataclass, field
from typing import AbstractSet, Any, Callable, Self

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


@dataclass(frozen=True)
class DictionaryTermVO:
    """
    The DictionaryTermVO acts as the value object for a single DictionaryTermAR item
    """

    codelist_uid: str
    dictionary_id: str
    name: str
    name_sentence_case: str
    abbreviation: str | None
    definition: str | None

    @classmethod
    def from_repository_values(
        cls,
        codelist_uid: str,
        dictionary_id: str,
        name: str,
        name_sentence_case: str,
        abbreviation: str | None,
        definition: str | None,
    ) -> Self:
        dictionary_term_vo = cls(
            codelist_uid=codelist_uid,
            dictionary_id=dictionary_id,
            name=name,
            name_sentence_case=name_sentence_case,
            abbreviation=abbreviation,
            definition=definition,
        )

        return dictionary_term_vo

    @classmethod
    def from_input_values(
        cls,
        codelist_uid: str,
        dictionary_id: str,
        name: str,
        name_sentence_case: str,
        abbreviation: str | None,
        definition: str | None,
    ) -> Self:
        return cls.from_repository_values(
            codelist_uid=codelist_uid,
            dictionary_id=dictionary_id,
            name=name,
            name_sentence_case=name_sentence_case,
            abbreviation=abbreviation,
            definition=definition,
        )

    def validate(
        self,
        term_exists_by_name_callback: Callable[[str, str], bool],
        previous_name: str | None = None,
    ) -> None:
        AlreadyExistsException.raise_if(
            term_exists_by_name_callback(self.name, self.codelist_uid)
            and self.name != previous_name,
            msg=f"Dictionary Term with Name '{self.name}' already exists in Dictionary Codelist with UID '{self.codelist_uid}'.",
        )
        ValidationException.raise_if(
            self.name_sentence_case.lower() != self.name.lower(),
            msg=f"{self.name_sentence_case} isn't an independent case version of {self.name}",
        )


@dataclass
class DictionaryTermAR(LibraryItemAggregateRootBase):
    _dictionary_term_vo: DictionaryTermVO
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    @property
    def name(self) -> str:
        return self._dictionary_term_vo.name

    @property
    def dictionary_term_vo(self) -> DictionaryTermVO:
        return self._dictionary_term_vo

    @dictionary_term_vo.setter
    def dictionary_term_vo(self, dictionary_term_vo: DictionaryTermVO):
        self._dictionary_term_vo = dictionary_term_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        dictionary_term_vo: DictionaryTermVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        dictionary_codelist_ar = cls(
            _uid=uid,
            _dictionary_term_vo=dictionary_term_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return dictionary_codelist_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        dictionary_term_vo: DictionaryTermVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str | None] = lambda: None,
        term_exists_by_name_callback: Callable[[str, str], bool],
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )
        BusinessLogicException.raise_if_not(
            library.is_editable,
            msg=f"Library with Name '{library.name}' doesn't allow creation of objects.",
        )

        dictionary_term_vo.validate(
            term_exists_by_name_callback=term_exists_by_name_callback
        )

        return cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _dictionary_term_vo=dictionary_term_vo,
        )

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        dictionary_term_vo: DictionaryTermVO,
        term_exists_by_name_callback: Callable[[str, str], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        dictionary_term_vo.validate(
            term_exists_by_name_callback=term_exists_by_name_callback,
            previous_name=self.name,
        )
        if self._dictionary_term_vo != dictionary_term_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self.dictionary_term_vo = dictionary_term_vo

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
