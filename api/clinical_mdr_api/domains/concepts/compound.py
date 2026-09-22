from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase, ConceptVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from common.exceptions import BusinessLogicException


@dataclass(frozen=True)
class CompoundVO(ConceptVO):
    """
    The CompoundVO acts as the single value object for CompoundAR aggregate.
    """

    external_id: str | None = None

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: str | None,
        definition: str | None,
        abbreviation: str | None,
        external_id: str | None,
    ) -> Self:
        compound_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=True,
            external_id=external_id,
        )

        return compound_vo

    def validate(
        self,
        uid: str,
        compound_uid_by_property_value_callback: Callable[[str, str], str | None],
    ):
        if self.name is not None:
            self.validate_uniqueness(
                lookup_callback=compound_uid_by_property_value_callback,
                uid=uid,
                property_name="name",
                value=self.name,
                error_message=f"Compound with Name '{self.name}' already exists.",
            )

        if self.name_sentence_case is not None:
            self.validate_uniqueness(
                lookup_callback=compound_uid_by_property_value_callback,
                uid=uid,
                property_name="name_sentence_case",
                value=self.name_sentence_case,
                error_message=f"Compound with Name Sentence Case '{self.name_sentence_case}' already exists.",
            )

        if self.external_id is not None:
            self.validate_uniqueness(
                lookup_callback=compound_uid_by_property_value_callback,
                uid=uid,
                property_name="external_id",
                value=self.external_id,
                error_message=f"Compound with external_id '{self.external_id}' already exists.",
            )


class CompoundAR(ConceptARBase):
    _concept_vo: CompoundVO

    @property
    def concept_vo(self) -> CompoundVO:
        return self._concept_vo

    @concept_vo.setter
    def concept_vo(self, value: CompoundVO) -> None:
        self._concept_vo = value

    @property
    def name(self) -> str:
        return self.concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author_id: str,
        concept_vo: CompoundVO,
        library: LibraryVO,
        compound_uid_by_property_value_callback: Callable[[str, str], str | None],
        generate_uid_callback: Callable[[], str],
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )
        uid = generate_uid_callback()

        BusinessLogicException.raise_if_not(
            library.is_editable,
            msg=f"Library with Name '{library.name}' doesn't allow creation of objects.",
        )

        concept_vo.validate(
            uid=uid,
            compound_uid_by_property_value_callback=compound_uid_by_property_value_callback,
        )

        compound_ar = cls(
            _uid=uid,
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return compound_ar

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        concept_vo: CompoundVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: False,
        compound_uid_by_property_value_callback: Callable[
            [str, str], str | None
        ] = lambda x, y: None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            self.uid,
            compound_uid_by_property_value_callback=compound_uid_by_property_value_callback,
        )

        if self._concept_vo != concept_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._concept_vo = concept_vo
