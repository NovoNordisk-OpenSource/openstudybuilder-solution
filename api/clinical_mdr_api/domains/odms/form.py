from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.odms.ar_base import OdmARBase
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmTranslatedTextModel,
)
from common.exceptions import AlreadyExistsException
from common.utils import booltostr


@dataclass(frozen=True)
class OdmFormVO:
    name: str | None
    oid: str | None
    repeating: str | int | None
    sdtm_version: str | None
    translated_texts: list[OdmTranslatedTextModel]
    aliases: list[OdmAliasModel]
    item_group_uids: list[str]
    vendor_attribute_uids: list[str]
    vendor_element_uids: list[str]
    vendor_element_attribute_uids: list[str]

    @classmethod
    def from_repository_values(
        cls,
        oid: str | None,
        name: str,
        sdtm_version: str | None,
        repeating: str | int | None,
        translated_texts: list[OdmTranslatedTextModel],
        aliases: list[OdmAliasModel],
        item_group_uids: list[str],
        vendor_element_uids: list[str],
        vendor_attribute_uids: list[str],
        vendor_element_attribute_uids: list[str],
    ) -> Self:
        return cls(
            oid=oid,
            name=name,
            sdtm_version=sdtm_version,
            repeating=repeating,
            translated_texts=translated_texts,
            aliases=aliases,
            item_group_uids=item_group_uids,
            vendor_element_uids=vendor_element_uids,
            vendor_attribute_uids=vendor_attribute_uids,
            vendor_element_attribute_uids=vendor_element_attribute_uids,
        )

    def validate(
        self,
        odm_object_exists_callback: Callable,
        odm_uid: str | None = None,
        library_name: str | None = None,
    ) -> None:
        if uids := odm_object_exists_callback(library_name=library_name, oid=self.oid):
            if uids[0] != odm_uid:
                raise AlreadyExistsException(
                    msg=f"ODM Form with OID '{self.oid}' already exists in library '{library_name}' with UID ({uids[0]})"
                )


@dataclass
class OdmFormAR(OdmARBase):
    _odm_vo: OdmFormVO

    @property
    def name(self) -> str:
        return self._odm_vo.name

    @property
    def odm_vo(self) -> OdmFormVO:
        return self._odm_vo

    @odm_vo.setter
    def odm_vo(self, value: OdmFormVO) -> None:
        self._odm_vo = value

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        odm_vo: OdmFormVO,
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
        odm_vo: OdmFormVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str] = lambda: "",
        odm_object_exists_callback: Callable = lambda _: True,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        odm_vo.validate(
            odm_object_exists_callback=odm_object_exists_callback,
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
        odm_vo: OdmFormVO,
        odm_object_exists_callback: Callable = lambda _: True,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        odm_vo.validate(
            odm_object_exists_callback=odm_object_exists_callback,
            odm_uid=self.uid,
            library_name=self._library.name,
        )

        if self._odm_vo != odm_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._odm_vo = odm_vo


@dataclass(frozen=True)
class OdmFormRefVO:
    uid: str
    name: str
    oid: str
    version: str
    study_event_uid: str
    order_number: int
    mandatory: str
    locked: str
    collection_exception_condition_oid: str

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        name: str,
        oid: str,
        version: str,
        study_event_uid: str,
        order_number: int,
        mandatory: bool,
        locked: bool,
        collection_exception_condition_oid: str,
    ) -> Self:
        return cls(
            uid=uid,
            name=name,
            oid=oid,
            version=version,
            study_event_uid=study_event_uid,
            order_number=order_number,
            mandatory=booltostr(mandatory),
            locked=booltostr(locked),
            collection_exception_condition_oid=collection_exception_condition_oid,
        )
