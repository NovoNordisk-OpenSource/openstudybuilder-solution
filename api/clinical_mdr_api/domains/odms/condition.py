from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.odms.ar_base import OdmARBase
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmFormalExpressionModel,
    OdmTranslatedTextModel,
)
from common.exceptions import AlreadyExistsException


@dataclass(frozen=True)
class OdmConditionVO:
    name: str
    oid: str | None
    formal_expressions: list[OdmFormalExpressionModel]
    translated_texts: list[OdmTranslatedTextModel]
    aliases: list[OdmAliasModel]

    @classmethod
    def from_repository_values(
        cls,
        oid: str | None,
        name: str,
        formal_expressions: list[OdmFormalExpressionModel],
        translated_texts: list[OdmTranslatedTextModel],
        aliases: list[OdmAliasModel],
    ) -> Self:
        return cls(
            oid=oid,
            name=name,
            formal_expressions=formal_expressions,
            translated_texts=translated_texts,
            aliases=aliases,
        )

    def validate(
        self,
        odm_object_exists_callback: Callable,
        odm_uid: str | None = None,
        library_name: str | None = None,
    ) -> None:
        data = {
            "library_name": library_name,
            "name": self.name,
            "oid": self.oid,
        }
        if uids := odm_object_exists_callback(**data):
            if uids[0] != odm_uid:
                raise AlreadyExistsException(
                    msg=f"ODM Condition already exists with UID ({uids[0]}) and data {data}"
                )


@dataclass
class OdmConditionAR(OdmARBase):
    _odm_vo: OdmConditionVO

    @property
    def name(self) -> str:
        return self._odm_vo.name

    @property
    def odm_vo(self) -> OdmConditionVO:
        return self._odm_vo

    @odm_vo.setter
    def odm_vo(self, value: OdmConditionVO) -> None:
        self._odm_vo = value

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        odm_vo: OdmConditionVO,
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
        odm_vo: OdmConditionVO,
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
        odm_vo: OdmConditionVO,
        odm_object_exists_callback: Callable = lambda _: True,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        odm_vo.validate(
            odm_object_exists_callback=odm_object_exists_callback, odm_uid=self.uid
        )

        super()._edit_draft(change_description=change_description, author_id=author_id)
        self._odm_vo = odm_vo
