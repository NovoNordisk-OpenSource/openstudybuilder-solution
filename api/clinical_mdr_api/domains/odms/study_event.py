from dataclasses import dataclass
from datetime import date
from typing import Callable, Self

from clinical_mdr_api.domains.odms.ar_base import OdmARBase
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from common.exceptions import AlreadyExistsException


@dataclass(frozen=True)
class OdmStudyEventVO:
    name: str | None
    oid: str | None
    effective_date: date | None
    retired_date: date | None
    description: str | None
    display_in_tree: bool
    form_uids: list[str]

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        oid: str | None,
        effective_date: date | None,
        retired_date: date | None,
        description: str | None,
        display_in_tree: bool,
        form_uids: list[str],
    ) -> Self:
        return cls(
            name=name,
            oid=oid,
            effective_date=effective_date,
            retired_date=retired_date,
            description=description,
            display_in_tree=display_in_tree,
            form_uids=form_uids,
        )

    def validate(
        self, odm_object_exists_callback: Callable, odm_uid: str | None = None
    ) -> None:
        data = {
            "name": self.name,
            "oid": self.oid,
            "effective_date": (
                self.effective_date.strftime("%Y-%m-%d")
                if self.effective_date
                else None
            ),
            "retired_date": (
                self.retired_date.strftime("%Y-%m-%d") if self.retired_date else None
            ),
            "description": self.description,
            "display_in_tree": self.display_in_tree,
        }
        if uids := odm_object_exists_callback(**data):
            if uids[0] != odm_uid:
                raise AlreadyExistsException(
                    msg=f"ODM Study Event already exists with UID ({uids[0]}) and data {data}"
                )


@dataclass
class OdmStudyEventAR(OdmARBase):
    _odm_vo: OdmStudyEventVO

    @property
    def name(self) -> str:
        return self._odm_vo.name

    @property
    def odm_vo(self) -> OdmStudyEventVO:
        return self._odm_vo

    @odm_vo.setter
    def odm_vo(self, value: OdmStudyEventVO) -> None:
        self._odm_vo = value

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        odm_vo: OdmStudyEventVO,
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
        odm_vo: OdmStudyEventVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str] = lambda: "",
        odm_object_exists_callback: Callable = lambda _: True,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        odm_vo.validate(odm_object_exists_callback=odm_object_exists_callback)

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
        odm_vo: OdmStudyEventVO,
        odm_object_exists_callback: Callable = lambda _: True,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        odm_vo.validate(
            odm_object_exists_callback=odm_object_exists_callback, odm_uid=self.uid
        )

        if self._odm_vo != odm_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._odm_vo = odm_vo
