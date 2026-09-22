from dataclasses import dataclass
from typing import Self

from clinical_mdr_api.domains.dictionaries.dictionary_term import (
    DictionaryTermAR,
    DictionaryTermVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)


@dataclass(frozen=True)
class DictionaryTermSubstanceVO(DictionaryTermVO):
    pclass_uid: str | None

    @classmethod
    def from_repository_values(
        cls,
        codelist_uid: str,
        dictionary_id: str,
        name: str,
        name_sentence_case: str,
        abbreviation: str | None,
        definition: str | None,
        pclass_uid: str | None,
    ) -> Self:
        dictionary_term_vo = cls(
            codelist_uid=codelist_uid,
            dictionary_id=dictionary_id,
            name=name,
            name_sentence_case=name_sentence_case,
            abbreviation=abbreviation,
            definition=definition,
            pclass_uid=pclass_uid,
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
        pclass_uid: str | None,
    ) -> Self:
        return cls.from_repository_values(
            codelist_uid=codelist_uid,
            dictionary_id=dictionary_id,
            name=name,
            name_sentence_case=name_sentence_case,
            abbreviation=abbreviation,
            definition=definition,
            pclass_uid=pclass_uid,
        )


class DictionaryTermSubstanceAR(DictionaryTermAR):
    _dictionary_term_vo: DictionaryTermSubstanceVO

    @property
    def dictionary_term_vo(self) -> DictionaryTermSubstanceVO:
        return self._dictionary_term_vo

    @dictionary_term_vo.setter
    def dictionary_term_vo(self, dictionary_term_vo: DictionaryTermSubstanceVO):
        self._dictionary_term_vo = dictionary_term_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        dictionary_term_vo: DictionaryTermSubstanceVO,
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
