from dataclasses import dataclass
from typing import AbstractSet, Callable, Self

from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
)
from common.exceptions import AlreadyExistsException, BusinessLogicException


@dataclass(frozen=True)
class ActivityInstanceClassActivityItemClassRelVO:
    """
    The ActivityInstanceClassActivityItemClassRelVO acts as the value object
    """

    uid: str
    mandatory: bool
    is_adam_param_specific_enabled: bool


@dataclass(frozen=True)
class ActivityItemClassVO:
    """
    The ActivityItemClassVO acts as the value object for a single ActivityItemClass value object
    """

    name: str
    definition: str | None
    nci_concept_id: str | None
    order: int
    activity_instance_classes: list[ActivityInstanceClassActivityItemClassRelVO]
    data_type_uid: str
    data_type_name: str | None
    role_uid: str
    role_name: str | None
    variable_class_uids: list[str] | None
    codelist_uids: list[str] | None

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        order: int,
        activity_instance_classes: list[ActivityInstanceClassActivityItemClassRelVO],
        data_type_uid: str,
        role_uid: str,
        definition: str | None = None,
        nci_concept_id: str | None = None,
        data_type_name: str | None = None,
        role_name: str | None = None,
        variable_class_uids: list[str] | None = None,
        codelist_uids: list[str] | None = None,
    ) -> Self:
        activity_item_class_vo = cls(
            name=name,
            order=order,
            activity_instance_classes=activity_instance_classes,
            data_type_uid=data_type_uid,
            data_type_name=data_type_name,
            role_uid=role_uid,
            role_name=role_name,
            variable_class_uids=variable_class_uids,
            codelist_uids=codelist_uids,
            definition=definition,
            nci_concept_id=nci_concept_id,
        )

        return activity_item_class_vo

    def validate(
        self,
        activity_item_class_exists_by_name_callback: Callable[[str], bool],
        activity_instance_class_exists: Callable[[str], bool],
        ct_term_exists: Callable[[str], bool],
        ct_codelist_exists: Callable[[str], bool],
        previous_name: str | None = None,
    ) -> None:
        AlreadyExistsException.raise_if(
            activity_item_class_exists_by_name_callback(self.name)
            and previous_name != self.name,
            "Activity Item Class",
            self.name,
            "Name",
        )
        BusinessLogicException.raise_if_not(
            ct_term_exists(self.role_uid),
            msg=f"Activity Item Class tried to connect to non-existent or non-final CT Term for Role with UID '{self.role_uid}'.",
        )
        BusinessLogicException.raise_if_not(
            ct_term_exists(self.data_type_uid),
            msg=f"Activity Item Class tried to connect to non-existent or non-final CT Term for Data type with UID '{self.data_type_uid}'.",
        )
        for activity_instance_class in self.activity_instance_classes:
            BusinessLogicException.raise_if_not(
                activity_instance_class_exists(activity_instance_class.uid),
                msg=f"Activity Item Class tried to connect to non-existent or non-final Activity Instance Class with UID '{activity_instance_class.uid}'.",
            )

        for codelist_uid in self.codelist_uids or []:
            BusinessLogicException.raise_if_not(
                ct_codelist_exists(codelist_uid),
                msg=f"Activity Item Class tried to connect to non-existent Codelist with UID '{codelist_uid}'.",
            )


@dataclass
class ActivityItemClassAR(LibraryItemAggregateRootBase):
    """
    An abstract generic activity item aggregate for versioned activity items
    """

    _activity_item_class_vo: ActivityItemClassVO

    @property
    def activity_item_class_vo(self) -> ActivityItemClassVO:
        return self._activity_item_class_vo

    @property
    def name(self) -> str:
        return self._activity_item_class_vo.name

    @property
    def definition(self) -> str | None:
        return self._activity_item_class_vo.definition

    @property
    def nci_concept_id(self) -> str | None:
        return self._activity_item_class_vo.nci_concept_id

    @activity_item_class_vo.setter
    def activity_item_class_vo(self, activity_item_class_vo: ActivityItemClassVO):
        self._activity_item_class_vo = activity_item_class_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        activity_item_class_vo: ActivityItemClassVO,
        library: LibraryVO | None,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        activity_item_class_ar = cls(
            _uid=uid,
            _activity_item_class_vo=activity_item_class_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return activity_item_class_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        activity_item_class_vo: ActivityItemClassVO,
        library: LibraryVO,
        activity_instance_class_exists: Callable[[str], bool],
        activity_item_class_exists_by_name_callback: Callable[[str], bool],
        ct_term_exists: Callable[[str], bool],
        ct_codelist_exists: Callable[[str], bool],
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )
        BusinessLogicException.raise_if_not(
            library.is_editable,
            msg=f"Library with Name '{library.name}' doesn't allow creation of objects.",
        )
        activity_item_class_vo.validate(
            activity_instance_class_exists=activity_instance_class_exists,
            activity_item_class_exists_by_name_callback=activity_item_class_exists_by_name_callback,
            ct_term_exists=ct_term_exists,
            ct_codelist_exists=ct_codelist_exists,
        )
        activity_item_class_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _activity_item_class_vo=activity_item_class_vo,
        )
        return activity_item_class_ar

    def edit_draft(
        self,
        author_id: str,
        change_description: str | None,
        activity_item_class_vo: ActivityItemClassVO,
        activity_instance_class_exists: Callable[[str], bool],
        activity_item_class_exists_by_name_callback: Callable[[str], bool],
        ct_term_exists: Callable[[str], bool],
        ct_codelist_exists: Callable[[str], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """

        activity_item_class_vo.validate(
            activity_instance_class_exists=activity_instance_class_exists,
            activity_item_class_exists_by_name_callback=activity_item_class_exists_by_name_callback,
            previous_name=self.name,
            ct_term_exists=ct_term_exists,
            ct_codelist_exists=ct_codelist_exists,
        )
        if self._activity_item_class_vo != activity_item_class_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self.activity_item_class_vo = activity_item_class_vo

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
