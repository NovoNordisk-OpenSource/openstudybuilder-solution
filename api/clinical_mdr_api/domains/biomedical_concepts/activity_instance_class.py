from dataclasses import dataclass
from typing import AbstractSet, Callable, Self

from clinical_mdr_api.domains.biomedical_concepts.activity_item_class import (
    ActivityInstanceClassActivityItemClassRelVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
)
from clinical_mdr_api.models.standard_data_models.dataset_class import DatasetClass
from common.exceptions import AlreadyExistsException, BusinessLogicException


@dataclass(frozen=True)
class ActivityInstanceClassVO:
    """
    The ActivityInstanceClassVO acts as the value object for a single ActivityInstanceClass value object
    """

    name: str
    order: int | None
    definition: str | None
    is_domain_specific: bool | None
    level: int | None
    dataset_class_uid: str | None
    activity_item_classes: list[ActivityInstanceClassActivityItemClassRelVO]
    nci_concept_id: str | None = None
    nci_concept_name: str | None = None

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        order: int | None,
        definition: str | None,
        is_domain_specific: bool | None,
        level: int | None,
        dataset_class_uid: str | None,
        activity_item_classes: list[ActivityInstanceClassActivityItemClassRelVO],
        nci_concept_id: str | None = None,
        nci_concept_name: str | None = None,
    ) -> Self:
        activity_instance_class_vo = cls(
            name=name,
            order=order,
            definition=definition,
            is_domain_specific=is_domain_specific,
            level=level,
            dataset_class_uid=dataset_class_uid,
            activity_item_classes=activity_item_classes,
            nci_concept_id=nci_concept_id,
            nci_concept_name=nci_concept_name,
        )

        return activity_instance_class_vo

    def validate(
        self,
        activity_instance_class_exists_by_name_callback: Callable[[str], bool],
        dataset_class_exists_by_uid: Callable[[str], DatasetClass | None],
        previous_name: str | None = None,
    ) -> None:
        AlreadyExistsException.raise_if(
            activity_instance_class_exists_by_name_callback(self.name)
            and previous_name != self.name,
            "Activity Instance Class",
            self.name,
            "Name",
        )
        BusinessLogicException.raise_if(
            self.dataset_class_uid
            and not dataset_class_exists_by_uid(self.dataset_class_uid),
            msg=f"Activity Instance Class tried to connect to non-existent Dataset Class with UID '{self.dataset_class_uid}'.",
        )


@dataclass
class ActivityInstanceClassAR(LibraryItemAggregateRootBase):
    """
    An abstract generic activity item aggregate for versioned activity items
    """

    _activity_instance_class_vo: ActivityInstanceClassVO

    @property
    def activity_instance_class_vo(self) -> ActivityInstanceClassVO:
        return self._activity_instance_class_vo

    @activity_instance_class_vo.setter
    def activity_instance_class_vo(
        self, activity_instance_class_vo: ActivityInstanceClassVO
    ):
        self._activity_instance_class_vo = activity_instance_class_vo

    @property
    def name(self) -> str:
        return self._activity_instance_class_vo.name

    @property
    def nci_concept_id(self) -> str | None:
        return self._activity_instance_class_vo.nci_concept_id

    @property
    def nci_concept_name(self) -> str | None:
        return self._activity_instance_class_vo.nci_concept_name

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        activity_instance_class_vo: ActivityInstanceClassVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        activity_instance_class_ar = cls(
            _uid=uid,
            _activity_instance_class_vo=activity_instance_class_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return activity_instance_class_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        activity_instance_class_vo: ActivityInstanceClassVO,
        library: LibraryVO,
        activity_instance_class_exists_by_name_callback: Callable[[str], bool],
        dataset_class_exists_by_uid: Callable[..., DatasetClass | None],
        generate_uid_callback: Callable[[], str | None] = lambda: None,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )
        BusinessLogicException.raise_if_not(
            library.is_editable,
            msg=f"Library with Name '{library.name}' doesn't allow creation of objects.",
        )
        activity_instance_class_vo.validate(
            activity_instance_class_exists_by_name_callback=activity_instance_class_exists_by_name_callback,
            dataset_class_exists_by_uid=dataset_class_exists_by_uid,
        )
        activity_instance_class_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _activity_instance_class_vo=activity_instance_class_vo,
        )
        return activity_instance_class_ar

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        activity_instance_class_vo: ActivityInstanceClassVO,
        activity_instance_class_exists_by_name_callback: Callable[[str], bool],
        dataset_class_exists_by_uid: Callable[..., DatasetClass | None],
    ) -> None:
        """
        Creates a new draft version for the object.
        """

        activity_instance_class_vo.validate(
            dataset_class_exists_by_uid=dataset_class_exists_by_uid,
            activity_instance_class_exists_by_name_callback=activity_instance_class_exists_by_name_callback,
            previous_name=self.name,
        )
        if self._activity_instance_class_vo != activity_instance_class_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self.activity_instance_class_vo = activity_instance_class_vo

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
