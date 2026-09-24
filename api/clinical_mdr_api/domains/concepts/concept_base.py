from abc import abstractmethod
from dataclasses import dataclass
from typing import AbstractSet, Callable, Generic, Self, TypeVar

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
class ConceptVO:
    """
    The ConceptVO acts as the value object for a single ActivityInstance value object
    """

    name: str | None
    name_sentence_case: str | None
    definition: str | None
    abbreviation: str | None
    is_template_parameter: bool

    def validate_uniqueness(
        self,
        lookup_callback: Callable[[str, str], str | None],
        uid: str,
        property_name: str,
        value: str,
        error_message: str,
    ):
        existing_node_uid = lookup_callback(property_name, value)

        AlreadyExistsException.raise_if(
            existing_node_uid and existing_node_uid != uid, msg=error_message
        )

    @classmethod
    def duplication_check(
        cls,
        property_data_list: list[tuple[str, str, str | None]],
        exists_by_callback: Callable[[str, str, bool], bool],
        object_name: str = "Object",
        on_root: bool = False,
    ):
        """
        Checks for object duplicates based on property data and raises an exception if any duplicates are found.

        Args:
            property_data_list (list[tuple[str, str, str | None]]): A list of tuples containing property data. Each tuple contains three elements:
                elm1 (str): property_name: A string representing the name of the property.
                elm2 (str): property_value: A string representing the value of the property.
                elm3 (str | None): property_previous_value: A string representing the previous value of the property or None.
            exists_by_callback (Callable[[str, str, bool], bool]): A callback function that takes a property name, property value,
            and on_root flag as arguments and returns a boolean value indicating whether the property value already exists.
            object_name: (str, optional) A string representing the name of the object being checked for duplicates. Defaults to "Object".
            on_root: (bool, optional) A boolean flag indicating whether to perform the existence check on the root node. Defaults to False.

        Returns:
            None: This method does not return a value directly, but it raises an exception if duplicates are found.

        Raises:
            BusinessLogicException: If duplicates are found in the property data list, an exception is raised with
            a message indicating the object name and the properties with duplicate values.
        """
        duplicates = []

        for (
            property_name,
            property_value,
            property_previous_value,
        ) in property_data_list:
            if (
                exists_by_callback(property_name.lower(), property_value, on_root)
                and property_previous_value != property_value
            ):
                duplicates.append(f"{property_name}: {property_value}")

        AlreadyExistsException.raise_if(
            duplicates, msg=f"{object_name} with {duplicates} already exists."
        )

    def check_concepts_exist(
        self,
        concept_data_list: list[
            tuple[list[str], str, Callable[[str, str, bool], bool]]
        ],
        object_name: str = "Object",
        property_name: str = "uid",
        on_root: bool = True,
    ):
        """
        Checks if the provided concept values exist based on the concept data list and raises an exception if any do not exist.

        Args:
            concept_data_list (list[tuple[list[str], str, Callable[[str, str, bool], bool]]]): A list of tuples containing concept data.
            Each tuple contains three elements:
                elm1 (list[str]): A list of strings representing the property values to check for existence.
                elm2 (str): A string representing the name of the concept being checked.
                elm3 (Callable[[str, str, bool], bool]): A callback function that takes a property name,
                concept value, and on_root flag as arguments and returns a boolean value indicating whether the concept value exists.
            object_name: (str, optional) A string representing the name of the object performing the concept existence check. Defaults to "Object".
            property_name: (str, optional) A string representing the name of the property used to identify the concept. Defaults to "uid".
            on_root: (bool, optional) A boolean flag indicating whether to perform the concept existence check on the root object. Defaults to True.

        Returns:
            None: This method does not return a value directly, but it raises an exception if non-existent concept values are found.

        Raises:
            BusinessLogicException: If any of the provided concept values do not exist based on the concept data list, an exception is raised with
            a message indicating the object name, concept name, property name, and the non-existent concept values.
        """
        errors = []

        for values, concept_name, callback in concept_data_list:
            non_existent_values = set()
            for value in values:
                if not callback(property_name, value, on_root):
                    non_existent_values.add(value)

            if non_existent_values:
                errors.append(
                    (
                        f"Concept Name: {concept_name}",
                        f"{property_name}s: {non_existent_values}",
                    )
                )

        BusinessLogicException.raise_if(
            errors,
            msg=f"{object_name} tried to connect to non-existent concepts {errors}.",
        )

    def validate_name_sentence_case(self):
        ValidationException.raise_if(
            self.name_sentence_case is None
            or self.name_sentence_case.lower() != self.name.lower(),
            msg=f"Lowercase versions of '{self.name}' and '{self.name_sentence_case}' must be equal",
        )


# pylint: disable=invalid-name
_ConceptVOType = TypeVar("_ConceptVOType", bound=ConceptVO)
_AggregateRootType = TypeVar("_AggregateRootType")


@dataclass
class ConceptARBase(LibraryItemAggregateRootBase, Generic[_ConceptVOType]):
    """
    An abstract generic activity item aggregate for versioned activity items
    """

    _concept_vo: _ConceptVOType

    @property
    @abstractmethod
    def concept_vo(self) -> _ConceptVOType:
        raise NotImplementedError

    @concept_vo.setter
    def concept_vo(self, concept_vo: _ConceptVOType):
        self._concept_vo = concept_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: _ConceptVOType,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        concept_ar = cls(
            _uid=uid,
            _concept_vo=concept_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return concept_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        concept_vo: _ConceptVOType,
        library: LibraryVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        generate_uid_callback: Callable[[], str | None] = lambda: None,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        BusinessLogicException.raise_if_not(
            library.is_editable,
            msg=f"Library with Name '{library.name}' doesn't allow creation of objects.",
        )

        ConceptVO.duplication_check(
            [("name", concept_vo.name or "", None)], concept_exists_by_callback
        )
        concept_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return concept_ar

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        concept_vo: _ConceptVOType,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        ConceptVO.duplication_check(
            [("name", concept_vo.name or "", self.name)], concept_exists_by_callback
        )
        if self._concept_vo != concept_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self.concept_vo = concept_vo

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
