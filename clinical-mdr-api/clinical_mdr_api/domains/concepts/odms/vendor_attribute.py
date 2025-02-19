from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.concepts.concept_base import ConceptVO
from clinical_mdr_api.domains.concepts.odms.odm_ar_base import OdmARBase
from clinical_mdr_api.domains.concepts.odms.vendor_element import OdmVendorElementAR
from clinical_mdr_api.domains.concepts.odms.vendor_namespace import OdmVendorNamespaceAR
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from common.exceptions import AlreadyExistsException, BusinessLogicException


@dataclass(frozen=True)
class OdmVendorAttributeVO(ConceptVO):
    compatible_types: list[str]
    data_type: str | None
    value_regex: str | None
    vendor_namespace_uid: str | None
    vendor_element_uid: str | None

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        compatible_types: list[str],
        data_type: str | None,
        value_regex: str | None,
        vendor_namespace_uid: str | None,
        vendor_element_uid: str | None,
    ) -> Self:
        return cls(
            name=name,
            compatible_types=compatible_types,
            data_type=data_type,
            value_regex=value_regex,
            vendor_namespace_uid=vendor_namespace_uid,
            vendor_element_uid=vendor_element_uid,
            name_sentence_case=None,
            definition=None,
            abbreviation=None,
            is_template_parameter=False,
        )

    def validate(
        self,
        find_odm_vendor_namespace_callback: Callable[
            [str], OdmVendorNamespaceAR | None
        ],
        find_odm_vendor_element_callback: Callable[[str], OdmVendorElementAR | None],
        find_odm_vendor_attribute_callback: Callable[
            [dict], tuple[list["OdmVendorAttributeAR"], int] | None
        ],
    ) -> None:
        if self.vendor_namespace_uid is not None:
            BusinessLogicException.raise_if_not(
                self.compatible_types,
                msg="compatible_types must be provided for ODM Vendor Attributes belonging to ODM Vendor Namespace.",
            )

            BusinessLogicException.raise_if_not(
                find_odm_vendor_namespace_callback(self.vendor_namespace_uid),
                msg="ODM Vendor Attribute tried to connect to non-existent concepts "
                f"[('Concept Name: ODM Vendor Namespace', 'uids: ({self.vendor_namespace_uid})')].",
            )

        if self.vendor_element_uid is not None:
            BusinessLogicException.raise_if(
                self.compatible_types,
                msg="compatible_types must not be provided for ODM Vendor Attributes belonging to ODM Vendor Element.",
            )

            BusinessLogicException.raise_if_not(
                find_odm_vendor_element_callback(self.vendor_element_uid),
                msg="ODM Vendor Attribute tried to connect to non-existent concepts "
                f"[('Concept Name: ODM Vendor Element', 'uids: ({self.vendor_element_uid})')].",
            )

        odm_vendor_attributes, _ = find_odm_vendor_attribute_callback(
            filter_by={"name": {"v": [self.name], "op": "eq"}}
        )
        for odm_vendor_attribute in odm_vendor_attributes:
            AlreadyExistsException.raise_if(
                (
                    self.vendor_namespace_uid is not None
                    and odm_vendor_attribute.concept_vo.vendor_namespace_uid
                    == self.vendor_namespace_uid
                )
                or (
                    self.vendor_element_uid is not None
                    and odm_vendor_attribute.concept_vo.vendor_element_uid
                    == self.vendor_element_uid
                ),
                "ODM Vendor Attribute",
                self.name,
                "Name",
            )


@dataclass
class OdmVendorAttributeAR(OdmARBase):
    _concept_vo: OdmVendorAttributeVO

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def concept_vo(self) -> OdmVendorAttributeVO:
        return self._concept_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: OdmVendorAttributeVO,
        library: LibraryVO | None,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        return cls(
            _uid=uid,
            _concept_vo=concept_vo,
            _library=library,
            _item_metadata=item_metadata,
        )

    @classmethod
    def from_input_values(
        cls,
        author_id: str,
        concept_vo: OdmVendorAttributeVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
        find_odm_vendor_namespace_callback: Callable[
            [str], OdmVendorNamespaceAR | None
        ] = lambda _: None,
        find_odm_vendor_element_callback: Callable[
            [str], OdmVendorElementAR | None
        ] = lambda _: None,
        find_odm_vendor_attribute_callback: Callable[
            [dict], tuple[list["OdmVendorAttributeAR"], int] | None
        ] = lambda _: None,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        concept_vo.validate(
            find_odm_vendor_namespace_callback=find_odm_vendor_namespace_callback,
            find_odm_vendor_element_callback=find_odm_vendor_element_callback,
            find_odm_vendor_attribute_callback=find_odm_vendor_attribute_callback,
        )

        return cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )

    def edit_draft(
        self,
        author_id: str,
        change_description: str | None,
        concept_vo: OdmVendorAttributeVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
    ) -> None:
        """
        Creates a new draft version for the object.
        """

        if self._concept_vo != concept_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._concept_vo = concept_vo


@dataclass(frozen=True)
class OdmVendorAttributeRelationVO:
    uid: str
    name: str
    compatible_types: list[str]
    data_type: str | None
    value_regex: str | None
    value: str
    vendor_namespace_uid: str

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        name: str,
        compatible_types: list[str],
        data_type: str | None,
        value_regex: str | None,
        value: str,
        vendor_namespace_uid: str,
    ) -> Self:
        return cls(
            uid=uid,
            name=name,
            compatible_types=compatible_types,
            data_type=data_type,
            value_regex=value_regex,
            value=value,
            vendor_namespace_uid=vendor_namespace_uid,
        )


@dataclass(frozen=True)
class OdmVendorElementAttributeRelationVO:
    uid: str
    name: str
    data_type: str | None
    value_regex: str | None
    value: str
    vendor_element_uid: str

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        name: str,
        data_type: str | None,
        value_regex: str | None,
        value: str,
        vendor_element_uid: str,
    ) -> Self:
        return cls(
            uid=uid,
            name=name,
            data_type=data_type,
            value_regex=value_regex,
            value=value,
            vendor_element_uid=vendor_element_uid,
        )
