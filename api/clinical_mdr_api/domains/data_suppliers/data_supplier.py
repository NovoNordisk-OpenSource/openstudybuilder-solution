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
class DataSupplierVO:
    """
    The DataSupplierVO acts as the value object for a single DataSupplier value object
    """

    name: str
    order: int | None
    supplier_type_uid: str
    description: str | None
    origin_source_uid: str | None
    origin_type_uid: str | None
    api_base_url: str | None
    ui_base_url: str | None

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        order: int | None,
        supplier_type_uid: str,
        description: str | None,
        origin_source_uid: str | None,
        origin_type_uid: str | None,
        api_base_url: str | None,
        ui_base_url: str | None,
    ) -> Self:
        data_supplier_vo = cls(
            name=name,
            order=order,
            description=description,
            supplier_type_uid=supplier_type_uid,
            origin_source_uid=origin_source_uid,
            origin_type_uid=origin_type_uid,
            api_base_url=api_base_url,
            ui_base_url=ui_base_url,
        )

        return data_supplier_vo

    def validate(
        self,
        data_supplier_exists_by_name_callback: Callable[[str], bool],
        ct_term_exists_by_uid_callback: Callable[[str], bool],
        previous_name: str | None = None,
    ) -> None:
        AlreadyExistsException.raise_if(
            previous_name != self.name
            and data_supplier_exists_by_name_callback(self.name),
            "Data Supplier",
            self.name,
            "Name",
        )
        BusinessLogicException.raise_if(
            self.supplier_type_uid is not None
            and not ct_term_exists_by_uid_callback(self.supplier_type_uid),
            msg=f"Supplier Type with UID '{self.supplier_type_uid}' does not exist.",
        )

        BusinessLogicException.raise_if(
            self.origin_type_uid is not None
            and not ct_term_exists_by_uid_callback(self.origin_type_uid),
            msg=f"Supplier Origin Type with UID '{self.origin_type_uid}' does not exist.",
        )

        BusinessLogicException.raise_if(
            self.origin_source_uid is not None
            and not ct_term_exists_by_uid_callback(self.origin_source_uid),
            msg=f"Supplier Origin Source with UID '{self.origin_source_uid}' does not exist.",
        )


@dataclass
class DataSupplierAR(LibraryItemAggregateRootBase):
    """
    An abstract generic data supplier item aggregate for versioned data suppliers
    """

    _data_supplier_vo: DataSupplierVO

    @property
    def data_supplier_vo(self) -> DataSupplierVO:
        return self._data_supplier_vo

    @data_supplier_vo.setter
    def data_supplier_vo(self, data_supplier_vo: DataSupplierVO):
        self._data_supplier_vo = data_supplier_vo

    @property
    def name(self) -> str:
        return self._data_supplier_vo.name

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        data_supplier_vo: DataSupplierVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        data_supplier_ar = cls(
            _uid=uid,
            _data_supplier_vo=data_supplier_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return data_supplier_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        data_supplier_vo: DataSupplierVO,
        library: LibraryVO,
        data_supplier_exists_by_name_callback: Callable[[str], bool],
        ct_term_exists_by_uid_callback: Callable[[str], bool],
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )
        BusinessLogicException.raise_if_not(
            library.is_editable,
            msg=f"Library with Name '{library.name}' doesn't allow creation of objects.",
        )
        data_supplier_vo.validate(
            data_supplier_exists_by_name_callback=data_supplier_exists_by_name_callback,
            ct_term_exists_by_uid_callback=ct_term_exists_by_uid_callback,
        )
        data_supplier_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _data_supplier_vo=data_supplier_vo,
        )
        return data_supplier_ar

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        data_supplier_vo: DataSupplierVO,
        data_supplier_exists_by_name_callback: Callable[[str], bool],
        ct_term_exists_by_uid_callback: Callable[[str], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """

        data_supplier_vo.validate(
            data_supplier_exists_by_name_callback=data_supplier_exists_by_name_callback,
            ct_term_exists_by_uid_callback=ct_term_exists_by_uid_callback,
            previous_name=self.name,
        )
        if self._data_supplier_vo != data_supplier_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._data_supplier_vo = data_supplier_vo

    def create_new_version(self, author_id: str) -> None:
        """
        Puts object into DRAFT status with relevant changes to version numbers.
        """
        super()._create_new_version(author_id=author_id)

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        """
        Returns list of possible actions
        """
        if self._item_metadata.status == LibraryItemStatus.FINAL:
            return {ObjectAction.EDIT, ObjectAction.INACTIVATE}
        if self._item_metadata.status == LibraryItemStatus.RETIRED:
            return {ObjectAction.REACTIVATE}
        return frozenset()
