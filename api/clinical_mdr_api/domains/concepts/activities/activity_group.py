from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase, ConceptVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from common.exceptions import AlreadyExistsException, BusinessLogicException


@dataclass(frozen=True)
class ActivityGroupVO(ConceptVO):
    """
    The ActivityGroupVO acts as the value object for a single ActivityGroup aggregate
    """

    nci_concept_id: str | None = None
    nci_concept_name: str | None = None

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: str | None,
        definition: str | None,
        abbreviation: str | None,
        nci_concept_id: str | None = None,
        nci_concept_name: str | None = None,
    ) -> Self:
        activity_group_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=True,
            nci_concept_id=nci_concept_id,
            nci_concept_name=nci_concept_name,
        )

        return activity_group_vo

    def validate(
        self,
        activity_group_exists_by_name_callback: Callable[
            [str, str], bool
        ] = lambda x, y: True,
        previous_name: str | None = None,
        library_name: str | None = None,
    ) -> None:
        self.validate_name_sentence_case()
        if self.name and library_name is not None:
            existing_name = activity_group_exists_by_name_callback(
                library_name, self.name
            )
            AlreadyExistsException.raise_if(
                existing_name and previous_name != self.name,
                "Activity Group",
                self.name,
                "Name",
            )


@dataclass
class ActivityGroupAR(ConceptARBase):
    _concept_vo: ActivityGroupVO

    @property
    def concept_vo(self) -> ActivityGroupVO:
        return self._concept_vo

    @concept_vo.setter
    def concept_vo(self, value: ActivityGroupVO) -> None:
        self._concept_vo = value

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author_id: str,
        concept_vo: ActivityGroupVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str | None] = lambda: None,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        concept_exists_by_library_and_name_callback: Callable[
            [str, str], bool
        ] = lambda x, y: True,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        BusinessLogicException.raise_if_not(
            library.is_editable,
            msg=f"Library with Name '{library.name}' doesn't allow creation of objects.",
        )

        concept_vo.validate(
            activity_group_exists_by_name_callback=concept_exists_by_library_and_name_callback,
            library_name=library.name,
        )

        activity_group_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return activity_group_ar

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        concept_vo: ActivityGroupVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        concept_exists_by_library_and_name_callback: Callable[
            [str, str], bool
        ] = lambda x, y: True,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            activity_group_exists_by_name_callback=concept_exists_by_library_and_name_callback,
            previous_name=self.name,
            library_name=self.library.name,
        )

        if self._concept_vo != concept_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._concept_vo = concept_vo
