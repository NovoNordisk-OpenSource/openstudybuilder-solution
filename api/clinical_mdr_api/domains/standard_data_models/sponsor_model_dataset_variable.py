import datetime
from dataclasses import dataclass
from typing import Any, Self

from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)

# pylint: disable=too-many-arguments


@dataclass(frozen=True)
class SponsorModelDatasetVariableVO:
    """
    Value object for a single SponsorModelDatasetVariable value object.

    Only structural fields (identity, routing, and fields the repository turns into
    graph structure) are modelled here. All sponsor-defined / extensible fields
    travel through ``extra_properties`` and are described by the Sponsor Model Schema.
    """

    dataset_uid: str | None
    variable_uid: str | None
    sponsor_model_name: str
    sponsor_model_version_number: str
    label: str | None

    implemented_parent_dataset_class: str | None
    implemented_variable_class: str | None
    order: int | None
    references_codelists: list[str] | None
    references_terms: list[str] | None
    target_data_model_catalogue: str | None = None
    extra_properties: dict[str, Any] | None = None

    @classmethod
    def from_repository_values(
        cls,
        dataset_uid: str,
        variable_uid: str,
        sponsor_model_name: str,
        sponsor_model_version_number: str,
        label: str | None,
        implemented_parent_dataset_class: str | None,
        implemented_variable_class: str | None,
        order: int | None,
        references_codelists: list[str] | None,
        references_terms: list[str] | None,
        target_data_model_catalogue: str | None = None,
        extra_properties: dict[str, Any] | None = None,
    ) -> Self:
        sponsor_model_dataset_variable_vo = cls(
            dataset_uid=dataset_uid,
            variable_uid=variable_uid,
            sponsor_model_name=sponsor_model_name,
            sponsor_model_version_number=sponsor_model_version_number,
            label=label,
            implemented_parent_dataset_class=implemented_parent_dataset_class,
            implemented_variable_class=implemented_variable_class,
            order=order,
            references_codelists=references_codelists,
            references_terms=references_terms,
            target_data_model_catalogue=target_data_model_catalogue,
            extra_properties=extra_properties or {},
        )

        return sponsor_model_dataset_variable_vo


class SponsorModelDatasetVariableMetadataVO(LibraryItemMetadataVO):
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
class SponsorModelDatasetVariableAR(LibraryItemAggregateRootBase):
    """
    An abstract generic sponsor model variable aggregate for versioned sponsor models
    """

    _sponsor_model_dataset_variable_vo: SponsorModelDatasetVariableVO

    @property
    def sponsor_model_dataset_variable_vo(self) -> SponsorModelDatasetVariableVO:
        return self._sponsor_model_dataset_variable_vo

    @sponsor_model_dataset_variable_vo.setter
    def sponsor_model_dataset_variable_vo(
        self, sponsor_model_dataset_variable_vo: SponsorModelDatasetVariableVO
    ):
        self._sponsor_model_dataset_variable_vo = sponsor_model_dataset_variable_vo

    @property
    def name(self) -> str:
        return self._uid

    @classmethod
    def from_repository_values(
        cls,
        variable_uid: str,
        sponsor_model_dataset_variable_vo: SponsorModelDatasetVariableVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        sponsor_model_dataset_variable_ar = cls(
            _uid=variable_uid,
            _sponsor_model_dataset_variable_vo=sponsor_model_dataset_variable_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return sponsor_model_dataset_variable_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        sponsor_model_dataset_variable_vo: SponsorModelDatasetVariableVO,
        library: LibraryVO,
    ) -> Self:
        item_metadata = SponsorModelDatasetVariableMetadataVO.get_initial_item_metadata(
            author_id=author_id,
            version=sponsor_model_dataset_variable_vo.sponsor_model_version_number,
        )

        sponsor_model_dataset_variable_ar = cls(
            _uid=sponsor_model_dataset_variable_vo.variable_uid,
            _item_metadata=item_metadata,
            _library=library,
            _sponsor_model_dataset_variable_vo=sponsor_model_dataset_variable_vo,
        )
        return sponsor_model_dataset_variable_ar
