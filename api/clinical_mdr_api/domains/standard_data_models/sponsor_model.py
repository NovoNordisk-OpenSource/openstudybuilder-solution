import datetime
from dataclasses import dataclass
from typing import AbstractSet, Any, Self

from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
)


@dataclass(frozen=True)
class SponsorModelVO:
    """
    The SponsorModelVO acts as the value object for a single SponsorModel value object
    """

    ig_uid: str
    ig_version_number: str
    version_number: str

    name: str
    name_qualifier: str | None = None
    schema_version: int | None = None
    extra_properties: dict[str, Any] | None = None

    @classmethod
    def from_repository_values(
        cls,
        ig_uid: str,
        ig_version_number: str,
        name: str,
        version_number: str,
        name_qualifier: str | None = None,
        schema_version: int | None = None,
        extra_properties: dict[str, Any] | None = None,
    ) -> Self:
        sponsor_model_vo = cls(
            ig_uid=ig_uid,
            ig_version_number=ig_version_number,
            version_number=version_number,
            name=name,
            name_qualifier=name_qualifier,
            schema_version=schema_version,
            extra_properties=extra_properties or {},
        )

        return sponsor_model_vo


class SponsorModelMetadataVO(LibraryItemMetadataVO):
    @property
    def version(self) -> str:
        return str(self._major_version)

    # pylint: disable=arguments-renamed
    @classmethod
    def get_initial_item_metadata(cls, author_id: str, version: str) -> Self:
        return cls(
            _change_description="Approved version",
            _status=LibraryItemStatus.FINAL,
            _author_id=author_id,
            _start_date=datetime.datetime.now(datetime.timezone.utc),
            _end_date=None,
            _major_version=int(version),
            _minor_version=0,
        )

    def _get_new_version(
        self, new_status: LibraryItemStatus = LibraryItemStatus.FINAL
    ) -> tuple[int, int]:
        """
        Overriding the method to generate version number.
        SponsorModel only have a major version, updated when a new version is created.
        """
        v_major = self._major_version

        return v_major, 0


@dataclass
class SponsorModelAR(LibraryItemAggregateRootBase):
    """
    An abstract generic sponsor model aggregate for versioned sponsor models
    """

    _sponsor_model_vo: SponsorModelVO

    @property
    def sponsor_model_vo(self) -> SponsorModelVO:
        return self._sponsor_model_vo

    @sponsor_model_vo.setter
    def sponsor_model_vo(self, sponsor_model_vo: SponsorModelVO):
        self._sponsor_model_vo = sponsor_model_vo

    @property
    def name(self) -> str:
        return self._sponsor_model_vo.name

    def _is_edit_allowed_in_non_editable_library(self) -> bool:
        return True

    @classmethod
    def from_repository_values(
        cls,
        ig_uid: str,
        sponsor_model_vo: SponsorModelVO,
        library: LibraryVO,
        item_metadata: SponsorModelMetadataVO,
    ) -> Self:
        sponsor_model_ar = cls(
            _uid=ig_uid,
            _sponsor_model_vo=sponsor_model_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return sponsor_model_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        sponsor_model_vo: SponsorModelVO,
        library: LibraryVO,
    ) -> Self:
        item_metadata = SponsorModelMetadataVO.get_initial_item_metadata(
            author_id=author_id, version=sponsor_model_vo.version_number
        )

        sponsor_model_ar = cls(
            _uid=sponsor_model_vo.ig_uid,
            _item_metadata=item_metadata,
            _library=library,
            _sponsor_model_vo=sponsor_model_vo,
        )
        return sponsor_model_ar

    def edit_draft(
        self, author_id: str, change_description: str, sponsor_model_vo: SponsorModelVO
    ) -> None:
        """
        Creates a new draft version for the object.
        """

        if self._sponsor_model_vo != sponsor_model_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self.sponsor_model_vo = sponsor_model_vo

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
