from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.odms.ar_base import OdmARBase
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from common.exceptions import AlreadyExistsException, BusinessLogicException


@dataclass(frozen=True)
class OdmVendorElementVO:
    name: str
    compatible_types: list[str]
    vendor_namespace_uid: str
    vendor_attribute_uids: list[str]

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        compatible_types: list[str],
        vendor_namespace_uid: str,
        vendor_attribute_uids: list[str],
    ) -> Self:
        return cls(
            name=name,
            compatible_types=compatible_types,
            vendor_namespace_uid=vendor_namespace_uid,
            vendor_attribute_uids=vendor_attribute_uids,
        )

    def check_odms_exist(
        self,
        odm_data_list: list[tuple[list[str], str, Callable[[str, str, bool], bool]]],
        object_name: str = "Object",
    ):
        errors = []

        for values, odm_name, callback in odm_data_list:
            non_existent_values = set()
            for value in values:
                if not callback("uid", value, True):
                    non_existent_values.add(value)

            if non_existent_values:
                errors.append(
                    (
                        f"ODM Name: {odm_name}",
                        f"uids: {non_existent_values}",
                    )
                )

        BusinessLogicException.raise_if(
            errors,
            msg=f"{object_name} tried to connect to non-existent ODMs {errors}.",
        )

    def validate(
        self,
        odm_vendor_namespace_exists_by_callback: Callable[[str, str, bool], bool],
        find_odm_vendor_element_callback: Callable[
            ..., tuple[list["OdmVendorElementAR"], int]
        ],
    ) -> None:
        if (
            self.vendor_namespace_uid is not None
            and not odm_vendor_namespace_exists_by_callback(
                "uid", self.vendor_namespace_uid, True
            )
        ):
            raise BusinessLogicException(
                msg=f"ODM Vendor Element tried to connect to non-existent ODM Vendor Namespace with UID '{self.vendor_namespace_uid}'."
            )

        odm_vendor_element, _ = find_odm_vendor_element_callback(
            filter_by={
                "name": {"v": [self.name], "op": "eq"},
                "vendor_namespace_uid": {"v": [self.vendor_namespace_uid], "op": "eq"},
            }
        )

        AlreadyExistsException.raise_if(
            odm_vendor_element, "ODM Vendor Element", self.name, "Name"
        )


@dataclass
class OdmVendorElementAR(OdmARBase):
    _odm_vo: OdmVendorElementVO

    @property
    def name(self) -> str:
        return self._odm_vo.name

    @property
    def odm_vo(self) -> OdmVendorElementVO:
        return self._odm_vo

    @odm_vo.setter
    def odm_vo(self, value: OdmVendorElementVO) -> None:
        self._odm_vo = value

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        odm_vo: OdmVendorElementVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        return cls(
            _uid=uid,
            _odm_vo=odm_vo,
            _library=library,
            _item_metadata=item_metadata,
        )

    @classmethod
    def from_input_values(
        cls,
        author_id: str,
        odm_vo: OdmVendorElementVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str] = lambda: "",
        odm_vendor_namespace_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        find_odm_vendor_element_callback: Callable[
            ..., tuple[list["OdmVendorElementAR"], int]
        ] = lambda _: ([], 0),
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        odm_vo.validate(
            odm_vendor_namespace_exists_by_callback=odm_vendor_namespace_exists_by_callback,
            find_odm_vendor_element_callback=find_odm_vendor_element_callback,
        )

        return cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _odm_vo=odm_vo,
        )

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        odm_vo: OdmVendorElementVO,
    ) -> None:
        """
        Creates a new draft version for the object.
        """

        if self._odm_vo != odm_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._odm_vo = odm_vo


@dataclass(frozen=True)
class OdmVendorElementRelationVO:
    uid: str
    name: str
    value: str
    compatible_types: list[str]

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        name: str,
        value: str,
        compatible_types: list[str],
    ) -> Self:
        return cls(
            uid=uid,
            name=name,
            value=value,
            compatible_types=compatible_types,
        )
