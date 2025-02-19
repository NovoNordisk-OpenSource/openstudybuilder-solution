from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase, ConceptVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from common.exceptions import AlreadyExistsException, BusinessLogicException


@dataclass(frozen=True)
class SimpleActivityGroupVO:
    activity_group_uid: str
    activity_group_version: str | None = None


@dataclass(frozen=True)
class ActivitySubGroupVO(ConceptVO):
    """
    The ActivitySubGroupVO acts as the value object for a single ActivitySubGroup aggregate
    """

    activity_groups: list[SimpleActivityGroupVO]

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: str | None,
        definition: str | None,
        abbreviation: str | None,
        activity_groups: list[SimpleActivityGroupVO],
    ) -> Self:
        activity_subgroup_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=True,
            activity_groups=activity_groups,
        )

        return activity_subgroup_vo

    def validate(
        self,
        activity_group_exists: Callable[[str], bool],
        activity_subgroup_exists_by_name_callback: Callable[
            [str, str], bool
        ] = lambda x, y: True,
        previous_name: str | None = None,
        library_name: str | None = None,
    ):
        self.validate_name_sentence_case()
        existing_name = activity_subgroup_exists_by_name_callback(
            library_name, self.name
        )
        AlreadyExistsException.raise_if(
            existing_name and previous_name != self.name,
            "Activity Subgroup",
            self.name,
            "Name",
        )
        for activity_group in self.activity_groups:
            BusinessLogicException.raise_if_not(
                activity_group_exists(activity_group.activity_group_uid),
                msg="Activity Subgroup tried to connect to non-existent or non-final concepts "
                f"""[('Concept Name: Activity Group', "uids: {{'{activity_group.activity_group_uid}'}}")].""",
            )


@dataclass
class ActivitySubGroupAR(ConceptARBase):
    _concept_vo: ActivitySubGroupVO

    @property
    def concept_vo(self) -> ActivitySubGroupVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author_id: str,
        concept_vo: ActivitySubGroupVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        concept_exists_by_library_and_name_callback: Callable[
            [str, str], bool
        ] = lambda x, y: True,
        activity_group_exists: Callable[[str], bool] = lambda _: False,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        BusinessLogicException.raise_if_not(
            library.is_editable,
            msg=f"Library with Name '{library.name}' doesn't allow creation of objects.",
        )

        concept_vo.validate(
            activity_subgroup_exists_by_name_callback=concept_exists_by_library_and_name_callback,
            activity_group_exists=activity_group_exists,
            library_name=library.name,
        )

        activity_subgroup_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return activity_subgroup_ar

    def edit_draft(
        self,
        author_id: str,
        change_description: str | None,
        concept_vo: ActivitySubGroupVO,
        concept_exists_by_callback: Callable[[str, str, bool], bool] | None = None,
        concept_exists_by_library_and_name_callback: Callable[
            [str, str], bool
        ] = lambda x, y: True,
        activity_group_exists: Callable[[str], bool] | None = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            activity_subgroup_exists_by_name_callback=concept_exists_by_library_and_name_callback,
            activity_group_exists=activity_group_exists,
            previous_name=self.name,
            library_name=self.library.name,
        )
        if self._concept_vo != concept_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._concept_vo = concept_vo
