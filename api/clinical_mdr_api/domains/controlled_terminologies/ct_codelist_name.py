from dataclasses import dataclass
from datetime import datetime
from typing import AbstractSet, Callable, Self

from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    DEFAULT_CODELIST_TYPE,
)
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
class CTCodelistNameVO:
    """
    The CTCodelistNameVO acts as the value object for a single CTCodelist name
    """

    name: str | None
    catalogue_names: list[str]
    is_template_parameter: bool
    is_ordinal: bool
    codelist_type: str

    @classmethod
    def from_repository_values(
        cls,
        name: str | None,
        catalogue_names: list[str],
        is_template_parameter: bool,
        is_ordinal: bool = False,
        codelist_type: str = DEFAULT_CODELIST_TYPE,
    ) -> Self:
        ct_codelist_name_vo = cls(
            name=name,
            catalogue_names=catalogue_names,
            is_template_parameter=is_template_parameter,
            is_ordinal=is_ordinal,
            codelist_type=codelist_type,
        )

        return ct_codelist_name_vo

    @classmethod
    def from_input_values(
        cls,
        name: str | None,
        catalogue_names: list[str],
        is_template_parameter: bool,
        is_ordinal: bool = False,
        codelist_type: str = DEFAULT_CODELIST_TYPE,
        catalogue_exists_callback: Callable[[str], bool] = lambda _: True,
        codelist_exists_by_name_callback: Callable[[str], bool] = lambda _: False,
    ) -> Self:
        for catalogue_name in catalogue_names:
            ValidationException.raise_if_not(
                catalogue_exists_callback(catalogue_name),
                msg=f"Catalogue with Name '{catalogue_name}' doesn't exist.",
            )
        AlreadyExistsException.raise_if(
            name and codelist_exists_by_name_callback(name),
            "CT Codelist Name",
            name,
            "Name",
        )

        ct_codelist_name_vo = cls(
            name=name,
            catalogue_names=catalogue_names,
            is_template_parameter=is_template_parameter,
            is_ordinal=bool(is_ordinal),
            codelist_type=codelist_type,
        )

        return ct_codelist_name_vo


@dataclass
class CTCodelistNameAR(LibraryItemAggregateRootBase):
    _ct_codelist_name_vo: CTCodelistNameVO

    @property
    def name(self) -> str:
        return self._ct_codelist_name_vo.name

    @property
    def ct_codelist_vo(self) -> CTCodelistNameVO:
        return self._ct_codelist_name_vo

    def _is_edit_allowed_in_non_editable_library(self) -> bool:
        return True

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        ct_codelist_name_vo: CTCodelistNameVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        ct_codelist_ar = cls(
            _uid=uid,
            _ct_codelist_name_vo=ct_codelist_name_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return ct_codelist_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        ct_codelist_name_vo: CTCodelistNameVO,
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
            _ct_codelist_name_vo=ct_codelist_name_vo,
        )

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        ct_codelist_vo: CTCodelistNameVO,
        codelist_exists_by_name_callback: Callable[[str], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        AlreadyExistsException.raise_if(
            ct_codelist_vo.name
            and codelist_exists_by_name_callback(ct_codelist_vo.name)
            and self.name != ct_codelist_vo.name,
            "CT Codelist Name",
            ct_codelist_vo.name,
            "Name",
        )
        if self._ct_codelist_name_vo != ct_codelist_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._ct_codelist_name_vo = ct_codelist_vo

    def create_new_version(self, author_id: str) -> None:
        """
        Puts object into DRAFT status with relevant changes to version numbers.
        """
        super()._create_new_version(author_id=author_id)

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        """
        Returns list of possible actions
        """
        if self._item_metadata.status == LibraryItemStatus.DRAFT:
            return {ObjectAction.APPROVE, ObjectAction.EDIT}
        if self._item_metadata.status == LibraryItemStatus.FINAL:
            return {ObjectAction.NEWVERSION}
        return frozenset()

    def inactivate(self, author_id: str, change_description: str | None = None):
        """
        Inactivates latest version.
        """
        raise NotImplementedError()

    def reactivate(self, author_id: str, change_description: str | None = None):
        """
        Reactivates latest retired version and sets the version to draft.
        """
        raise NotImplementedError()

    def soft_delete(self):
        raise NotImplementedError()
