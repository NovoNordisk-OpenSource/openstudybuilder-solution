from dataclasses import dataclass
from typing import Any, Callable, Self

from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domains.odms.ar_base import OdmARBase
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmTranslatedTextModel,
)
from common.exceptions import AlreadyExistsException, BusinessLogicException
from common.utils import booltostr


@dataclass(frozen=True)
class OdmItemGroupVO:
    name: str | None
    oid: str | None
    repeating: str | int | None
    is_reference_data: str | int | None
    sas_dataset_name: str | None
    origin: str | None
    purpose: str | None
    comment: str | None
    translated_texts: list[OdmTranslatedTextModel]
    aliases: list[OdmAliasModel]
    sdtm_domain_uids: list[str]
    item_uids: list[str]
    vendor_attribute_uids: list[str]
    vendor_element_uids: list[str]
    vendor_element_attribute_uids: list[str]

    @classmethod
    def from_repository_values(
        cls,
        oid: str | None,
        name: str,
        repeating: str | int | None,
        is_reference_data: str | int | None,
        sas_dataset_name: str | None,
        origin: str | None,
        purpose: str | None,
        comment: str | None,
        translated_texts: list[OdmTranslatedTextModel],
        aliases: list[OdmAliasModel],
        sdtm_domain_uids: list[str],
        item_uids: list[str],
        vendor_element_uids: list[str],
        vendor_attribute_uids: list[str],
        vendor_element_attribute_uids: list[str],
    ) -> Self:
        return cls(
            oid=oid,
            name=name,
            repeating=repeating,
            is_reference_data=is_reference_data,
            sas_dataset_name=sas_dataset_name,
            origin=origin,
            purpose=purpose,
            comment=comment,
            translated_texts=translated_texts,
            aliases=aliases,
            sdtm_domain_uids=sdtm_domain_uids,
            item_uids=item_uids,
            vendor_element_uids=vendor_element_uids,
            vendor_attribute_uids=vendor_attribute_uids,
            vendor_element_attribute_uids=vendor_element_attribute_uids,
        )

    def validate(
        self,
        odm_object_exists_callback: Callable,
        find_term_callback: Callable[[str], CTTermAttributesAR | None],
        odm_uid: str | None = None,
        library_name: str | None = None,
    ) -> None:
        if uids := odm_object_exists_callback(library_name=library_name, oid=self.oid):
            if uids[0] != odm_uid:
                raise AlreadyExistsException(
                    msg=f"ODM Item Group with OID '{self.oid}' already exists in library '{library_name}' with UID ({uids[0]})"
                )

        for sdtm_domain_uid in self.sdtm_domain_uids:
            BusinessLogicException.raise_if_not(
                find_term_callback(sdtm_domain_uid),
                msg=f"ODM Item Group tried to connect to non-existent SDTM Domain with UID '{sdtm_domain_uid}'.",
            )


@dataclass
class OdmItemGroupAR(OdmARBase):
    _odm_vo: OdmItemGroupVO

    @property
    def name(self) -> str:
        return self._odm_vo.name

    @property
    def odm_vo(self) -> OdmItemGroupVO:
        return self._odm_vo

    @odm_vo.setter
    def odm_vo(self, value: OdmItemGroupVO) -> None:
        self._odm_vo = value

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        odm_vo: OdmItemGroupVO,
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
        odm_vo: OdmItemGroupVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str] = lambda: "",
        odm_object_exists_callback: Callable = lambda _: True,
        find_term_callback: Callable[[str], CTTermAttributesAR | None] = lambda _: None,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        odm_vo.validate(
            odm_object_exists_callback=odm_object_exists_callback,
            find_term_callback=find_term_callback,
            library_name=library.name,
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
        odm_vo: OdmItemGroupVO,
        odm_object_exists_callback: Callable = lambda _: True,
        find_term_callback: Callable[[str], CTTermAttributesAR | None] = lambda _: None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        odm_vo.validate(
            odm_object_exists_callback=odm_object_exists_callback,
            find_term_callback=find_term_callback,
            odm_uid=self.uid,
            library_name=self._library.name,
        )

        if self._odm_vo != odm_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._odm_vo = odm_vo


@dataclass(frozen=True)
class OdmItemGroupRefVO:
    uid: str
    oid: str
    name: str
    version: str
    form_uid: str
    order_number: int
    mandatory: str
    collection_exception_condition_oid: str | None
    vendor: dict[Any, Any]

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        oid: str,
        name: str,
        version: str,
        form_uid: str,
        order_number: int,
        mandatory: bool,
        vendor: dict[Any, Any],
        collection_exception_condition_oid: str | None = None,
    ) -> Self:
        return cls(
            uid=uid,
            oid=oid,
            name=name,
            version=version,
            form_uid=form_uid,
            order_number=order_number,
            mandatory=booltostr(mandatory),
            collection_exception_condition_oid=collection_exception_condition_oid,
            vendor=vendor,
        )
