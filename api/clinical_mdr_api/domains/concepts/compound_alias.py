from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase, ConceptVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from common.config import settings
from common.exceptions import AlreadyExistsException, BusinessLogicException


@dataclass(frozen=True)
class CompoundAliasVO(ConceptVO):
    """
    The CompoundAliasVO acts as the single value object for CompoundAliasAR aggregate.
    """

    compound_uid: str
    is_preferred_synonym: bool = False

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: str | None,
        definition: str | None,
        abbreviation: str | None,
        is_preferred_synonym: bool,
        compound_uid: str,
    ) -> Self:
        compound_alias_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=True,
            is_preferred_synonym=is_preferred_synonym,
            compound_uid=compound_uid,
        )

        return compound_alias_vo

    def validate(
        self,
        uid: str,
        compound_exists_callback: Callable[[str], bool],
        compound_alias_uid_by_property_value_callback: Callable[[str, str], str | None],
        compound_existing_preferred_synonyms_callback: Callable[[str], list[str]],
    ):
        if self.name is not None:
            self.validate_uniqueness(
                lookup_callback=compound_alias_uid_by_property_value_callback,
                uid=uid,
                property_name="name",
                value=self.name,
                error_message=f"Compound Alias with Name '{self.name}' already exists.",
            )

        if self.name_sentence_case is not None:
            self.validate_uniqueness(
                lookup_callback=compound_alias_uid_by_property_value_callback,
                uid=uid,
                property_name="name_sentence_case",
                value=self.name_sentence_case,
                error_message=f"Compound Alias with Name Sentence Case '{self.name_sentence_case}' already exists.",
            )

        if self.abbreviation is not None:
            self.validate_uniqueness(
                lookup_callback=compound_alias_uid_by_property_value_callback,
                uid=uid,
                property_name="abbreviation",
                value=self.abbreviation,
                error_message=f"Compound Alias with Abbreviation '{self.abbreviation}' already exists.",
            )

        compound_ar = compound_exists_callback(self.compound_uid)
        BusinessLogicException.raise_if_not(
            compound_ar,
            msg=f"{type(self).__name__} tried to connect to non-existent Compound with UID '{self.compound_uid}'.",
        )
        BusinessLogicException.raise_if(
            compound_ar.library.name == settings.archived_library_name,
            msg=f"Compound from '{compound_ar.library.name}' library can not be aliased.",
        )

        if self.is_preferred_synonym:
            existing_preferred_synonyms = compound_existing_preferred_synonyms_callback(
                self.compound_uid
            )
            AlreadyExistsException.raise_if(
                existing_preferred_synonyms and existing_preferred_synonyms != [uid],
                msg="Another preferred synonym for compound is already defined.",
            )


class CompoundAliasAR(ConceptARBase):
    _concept_vo: CompoundAliasVO

    @property
    def concept_vo(self) -> CompoundAliasVO:
        return self._concept_vo

    @concept_vo.setter
    def concept_vo(self, value: CompoundAliasVO) -> None:
        self._concept_vo = value

    @property
    def name(self) -> str:
        return self.concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author_id: str,
        concept_vo: CompoundAliasVO,
        library: LibraryVO,
        compound_alias_uid_by_property_value_callback: Callable[[str, str], str | None],
        compound_exists_callback: Callable[[str], bool],
        compound_existing_preferred_synonyms_callback: Callable[[str], list[str]],
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
            compound_alias_uid_by_property_value_callback=compound_alias_uid_by_property_value_callback,
            compound_exists_callback=compound_exists_callback,
            compound_existing_preferred_synonyms_callback=compound_existing_preferred_synonyms_callback,
        )

        compound_alias_ar = cls(
            _uid=uid,
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return compound_alias_ar

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        concept_vo: CompoundAliasVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        compound_existing_preferred_synonyms_callback: Callable[
            [str], list[str]
        ] = lambda _: [],
        compound_exists_callback: Callable[[str], bool] = lambda _: True,
        compound_alias_uid_by_property_value_callback: Callable[
            [str, str], str | None
        ] = lambda x, y: None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            self.uid,
            compound_alias_uid_by_property_value_callback=compound_alias_uid_by_property_value_callback,
            compound_exists_callback=compound_exists_callback,
            compound_existing_preferred_synonyms_callback=compound_existing_preferred_synonyms_callback,
        )

        if self._concept_vo != concept_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._concept_vo = concept_vo
