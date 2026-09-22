from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.odms.ar_base import OdmARBase
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from common.exceptions import AlreadyExistsException


@dataclass(frozen=True)
class OdmVendorNamespaceVO:
    name: str
    prefix: str
    url: str
    vendor_element_uids: list[str]
    vendor_attribute_uids: list[str]

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        prefix: str,
        url: str,
        vendor_element_uids: list[str],
        vendor_attribute_uids: list[str],
    ) -> Self:
        return cls(
            name=name,
            prefix=prefix,
            url=url,
            vendor_element_uids=vendor_element_uids,
            vendor_attribute_uids=vendor_attribute_uids,
        )

    def validate(
        self,
        odm_exists_by_callback: Callable[[str, str], bool],
        previous_name: str | None = None,
        previous_prefix: str | None = None,
        previous_url: str | None = None,
    ) -> None:
        for property_name, property_value, previous_value in [
            ("name", self.name, previous_name),
            ("prefix", self.prefix, previous_prefix),
            ("url", self.url, previous_url),
        ]:
            if property_value and property_value != previous_value:
                AlreadyExistsException.raise_if(
                    odm_exists_by_callback(property_name, property_value),
                    "ODM Vendor Namespace",
                    property_value,
                    property_name.capitalize(),
                )


@dataclass
class OdmVendorNamespaceAR(OdmARBase):
    _odm_vo: OdmVendorNamespaceVO

    @property
    def name(self) -> str:
        return self._odm_vo.name

    @property
    def odm_vo(self) -> OdmVendorNamespaceVO:
        return self._odm_vo

    @odm_vo.setter
    def odm_vo(self, value: OdmVendorNamespaceVO) -> None:
        self._odm_vo = value

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        odm_vo: OdmVendorNamespaceVO,
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
        odm_vo: OdmVendorNamespaceVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str] = lambda: "",
        odm_exists_by_callback: Callable[[str, str], bool] = lambda x, y: True,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        odm_vo.validate(
            odm_exists_by_callback=odm_exists_by_callback,
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
        odm_vo: OdmVendorNamespaceVO,
        odm_exists_by_callback: Callable[[str, str], bool] = lambda x, y: True,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        odm_vo.validate(
            odm_exists_by_callback=odm_exists_by_callback,
            previous_name=self.odm_vo.name,
            previous_prefix=self.odm_vo.prefix,
            previous_url=self.odm_vo.url,
        )

        if self._odm_vo != odm_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._odm_vo = odm_vo
