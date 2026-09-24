import datetime
from dataclasses import dataclass
from typing import Any, Self

from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)


@dataclass(frozen=True)
class SponsorModelDatasetVO:
    """
    The SponsorModelDatasetVO acts as the value object for a single SponsorModelDataset value object.

    Only structural fields (identity, routing, and fields the repository turns into
    graph structure) are modelled here. All sponsor-defined / extensible fields
    travel through ``extra_properties`` and are described by the Sponsor Model Schema.
    """

    sponsor_model_name: str
    sponsor_model_version_number: str
    dataset_uid: str
    label: str | None
    implemented_dataset_class: str | None
    keys: list[str] | None
    sort_keys: list[str] | None
    enrich_build_order: int | None
    target_data_model_catalogue: str | None = None
    extra_properties: dict[str, Any] | None = None

    @classmethod
    def from_repository_values(
        cls,
        sponsor_model_name: str,
        sponsor_model_version_number: str,
        dataset_uid: str,
        label: str | None,
        implemented_dataset_class: str | None,
        keys: list[str] | None,
        sort_keys: list[str] | None,
        enrich_build_order: int | None,
        target_data_model_catalogue: str | None = None,
        extra_properties: dict[str, Any] | None = None,
    ) -> Self:
        sponsor_model_dataset_vo = cls(
            sponsor_model_name=sponsor_model_name,
            sponsor_model_version_number=str(sponsor_model_version_number),
            dataset_uid=dataset_uid,
            label=label,
            implemented_dataset_class=implemented_dataset_class,
            keys=keys,
            sort_keys=sort_keys,
            enrich_build_order=enrich_build_order,
            target_data_model_catalogue=target_data_model_catalogue,
            extra_properties=extra_properties or {},
        )

        return sponsor_model_dataset_vo


class SponsorModelDatasetMetadataVO(LibraryItemMetadataVO):
    @property
    def version(self) -> str:
        return self._major_version

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


@dataclass
class SponsorModelDatasetAR(LibraryItemAggregateRootBase):
    """
    An abstract generic sponsor model dataset aggregate for versioned sponsor models
    """

    _sponsor_model_dataset_vo: SponsorModelDatasetVO

    @property
    def sponsor_model_dataset_vo(self) -> SponsorModelDatasetVO:
        return self._sponsor_model_dataset_vo

    @sponsor_model_dataset_vo.setter
    def sponsor_model_dataset_vo(self, sponsor_model_dataset_vo: SponsorModelDatasetVO):
        self._sponsor_model_dataset_vo = sponsor_model_dataset_vo

    @property
    def name(self) -> str:
        return self._uid

    @classmethod
    def from_repository_values(
        cls,
        dataset_uid: str,
        sponsor_model_dataset_vo: SponsorModelDatasetVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        sponsor_model_dataset_ar = cls(
            _uid=dataset_uid,
            _sponsor_model_dataset_vo=sponsor_model_dataset_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return sponsor_model_dataset_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        sponsor_model_dataset_vo: SponsorModelDatasetVO,
        library: LibraryVO,
    ) -> Self:
        item_metadata = SponsorModelDatasetMetadataVO.get_initial_item_metadata(
            author_id=author_id,
            version=sponsor_model_dataset_vo.sponsor_model_version_number,
        )

        sponsor_model_dataset_ar = cls(
            _uid=sponsor_model_dataset_vo.dataset_uid,
            _item_metadata=item_metadata,
            _library=library,
            _sponsor_model_dataset_vo=sponsor_model_dataset_vo,
        )
        return sponsor_model_dataset_ar
