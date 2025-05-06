from typing import Sequence

from clinical_mdr_api.domain_repositories.models.generic import VersionRelationship
from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    DataModelIGRoot,
    SponsorModelDatasetInstance,
    SponsorModelValue,
)


def get_sponsor_model_info_from_dataset(
    dataset_node: SponsorModelDatasetInstance, return_ordinal: bool = True
) -> tuple[str, str, int]:
    sponsor_model: SponsorModelValue = dataset_node.has_dataset.get_or_none()
    sponsor_model_name = None
    sponsor_model_version = None
    enrich_build_order = None
    if sponsor_model is not None:
        data_model_ig: DataModelIGRoot = (
            sponsor_model.has_sponsor_model_version.single()
        )
        sponsor_model_name = sponsor_model.name
        rels: Sequence[VersionRelationship] = (
            sponsor_model.has_sponsor_model_version.all_relationships(data_model_ig)
        )
        sponsor_model_version = rels[0].version

        if return_ordinal:
            sponsor_model_rel = dataset_node.has_dataset.relationship(sponsor_model)
            if sponsor_model_rel is not None:
                enrich_build_order = sponsor_model_rel.ordinal

    return sponsor_model_name, sponsor_model_version, enrich_build_order
