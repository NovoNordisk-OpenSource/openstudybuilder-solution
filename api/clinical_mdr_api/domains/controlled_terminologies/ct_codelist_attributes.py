from dataclasses import dataclass
from datetime import datetime
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

DEFAULT_CODELIST_TYPE = "Standard"


@dataclass(frozen=True)
class CTPairedCodelists:
    """
    Small class to hold the paired codelists UIDs and names
    """

    paired_names_codelist_uid: str | None
    paired_codes_codelist_uid: str | None
    paired_names_codelist_name: str | None = None
    paired_codes_codelist_name: str | None = None


@dataclass(frozen=True)
class CTCodelistAttributesVO:
    """
    The CTCodelistAttributesVO acts as the value object for a single CTCodelist attribute
    """

    name: str
    catalogue_names: list[str]
    parent_codelist_uid: str | None
    child_codelist_uids: list[str]
    submission_value: str
    preferred_term: str | None
    definition: str
    extensible: bool

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        catalogue_names: list[str],
        parent_codelist_uid: str | None,
        child_codelist_uids: list[str],
        submission_value: str,
        preferred_term: str | None,
        definition: str,
        extensible: bool,
    ) -> Self:
        if child_codelist_uids is None:
            child_codelist_uids = []
        ct_codelist_attribute_vo = cls(
            name=name,
            catalogue_names=catalogue_names,
            parent_codelist_uid=parent_codelist_uid,
            child_codelist_uids=child_codelist_uids,
            submission_value=submission_value,
            preferred_term=preferred_term,
            definition=definition,
            extensible=extensible,
        )

        return ct_codelist_attribute_vo

    @classmethod
    def from_input_values(
        cls,
        name: str,
        catalogue_names: list[str],
        parent_codelist_uid: str | None,
        submission_value: str,
        preferred_term: str | None,
        definition: str,
        extensible: bool,
        catalogue_exists_callback: Callable[[str], bool],
        codelist_exists_by_uid_callback: Callable[[str], bool] = lambda _: False,
        codelist_exists_by_name_callback: Callable[[str], bool] = lambda _: False,
        codelist_exists_by_submission_value_callback: Callable[
            [str], bool
        ] = lambda _: False,
        child_codelist_uids: list[str] | None = None,
    ) -> Self:
        if child_codelist_uids is None:
            child_codelist_uids = []
        BusinessLogicException.raise_if(
            parent_codelist_uid
            and not codelist_exists_by_uid_callback(parent_codelist_uid),
            msg=f"Codelist with Parent Codelist UID '{parent_codelist_uid}' doesn't exist.",
        )
        for catalogue_name in catalogue_names:
            ValidationException.raise_if_not(
                catalogue_exists_callback(catalogue_name),
                msg=f"Catalogue with Name '{catalogue_name}' doesn't exist.",
            )
        AlreadyExistsException.raise_if(
            name and codelist_exists_by_name_callback(name),
            "CT Codelist Attributes",
            name,
            "Name",
        )
        AlreadyExistsException.raise_if(
            submission_value
            and codelist_exists_by_submission_value_callback(submission_value),
            "CT Codelist Attributes",
            submission_value,
            "Submission Value",
        )

        ct_codelist_attribute_vo = cls(
            name=name,
            parent_codelist_uid=parent_codelist_uid,
            child_codelist_uids=child_codelist_uids,
            catalogue_names=catalogue_names,
            submission_value=submission_value,
            preferred_term=preferred_term,
            definition=definition,
            extensible=extensible,
        )

        return ct_codelist_attribute_vo


@dataclass
class CTCodelistAttributesAR(LibraryItemAggregateRootBase):
    _ct_codelist_attributes_vo: CTCodelistAttributesVO

    @property
    def name(self) -> str:
        return self._ct_codelist_attributes_vo.name

    @property
    def ct_codelist_vo(self) -> CTCodelistAttributesVO:
        return self._ct_codelist_attributes_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        ct_codelist_attributes_vo: CTCodelistAttributesVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        ct_codelist_ar = cls(
            _uid=uid,
            _ct_codelist_attributes_vo=ct_codelist_attributes_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return ct_codelist_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        ct_codelist_attributes_vo: CTCodelistAttributesVO,
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
            _ct_codelist_attributes_vo=ct_codelist_attributes_vo,
        )

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        ct_codelist_vo: CTCodelistAttributesVO,
        codelist_exists_by_name_callback: Callable[[str], bool],
        codelist_exists_by_submission_value_callback: Callable[[str], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        # if codelist_exists_by_name_callback(ct_codelist_vo.name, self.uid):
        AlreadyExistsException.raise_if(
            ct_codelist_vo.name
            and codelist_exists_by_name_callback(ct_codelist_vo.name)
            and self.name != ct_codelist_vo.name,
            "CT Codelist Attributes",
            ct_codelist_vo.name,
            "Name",
        )
        AlreadyExistsException.raise_if(
            ct_codelist_vo.submission_value
            and codelist_exists_by_submission_value_callback(
                ct_codelist_vo.submission_value
            )
            and self.ct_codelist_vo.submission_value != ct_codelist_vo.submission_value,
            "CT Codelist Attributes",
            ct_codelist_vo.submission_value,
            "Submission Value",
        )

        if self._ct_codelist_attributes_vo != ct_codelist_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._ct_codelist_attributes_vo = ct_codelist_vo

    def create_new_version(self, author_id: str) -> None:
        """
        Puts object into DRAFT status with relevant changes to version numbers.
        """
        super()._create_new_version(author_id=author_id)

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        """
        Returns list of possible actions
        """
        if self.library.is_editable:
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
