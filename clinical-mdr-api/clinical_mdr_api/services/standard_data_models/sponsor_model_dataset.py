from clinical_mdr_api.domain_repositories.standard_data_models.sponsor_model_dataset_repository import (
    SponsorModelDatasetRepository,
)
from clinical_mdr_api.domains.standard_data_models.sponsor_model_dataset import (
    SponsorModelDatasetAR,
    SponsorModelDatasetVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.standard_data_models.sponsor_model_dataset import (
    SponsorModelDataset,
    SponsorModelDatasetInput,
)
from clinical_mdr_api.services.neomodel_ext_generic import NeomodelExtGenericService


class SponsorModelDatasetService(NeomodelExtGenericService):
    repository_interface = SponsorModelDatasetRepository
    api_model_class = SponsorModelDataset

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: SponsorModelDatasetAR
    ) -> SponsorModelDataset:
        return SponsorModelDataset.from_sponsor_model_dataset_ar(
            sponsor_model_dataset_ar=item_ar,
        )

    def _create_aggregate_root(
        self, item_input: SponsorModelDatasetInput, library: LibraryVO
    ) -> SponsorModelDatasetAR:
        return SponsorModelDatasetAR.from_input_values(
            author_id=self.author_id,
            sponsor_model_dataset_vo=SponsorModelDatasetVO.from_repository_values(
                target_data_model_catalogue=item_input.target_data_model_catalogue,
                sponsor_model_name=item_input.sponsor_model_name,
                sponsor_model_version_number=item_input.sponsor_model_version_number,
                dataset_uid=item_input.dataset_uid,
                is_basic_std=item_input.is_basic_std,
                implemented_dataset_class=item_input.implemented_dataset_class,
                xml_path=item_input.xml_path,
                xml_title=item_input.xml_title,
                structure=item_input.structure,
                purpose=item_input.purpose,
                keys=item_input.keys,
                sort_keys=item_input.sort_keys,
                is_cdisc_std=item_input.is_cdisc_std,
                source_ig=item_input.source_ig,
                standard_ref=item_input.standard_ref,
                comment=item_input.comment,
                ig_comment=item_input.ig_comment,
                map_domain_flag=item_input.map_domain_flag,
                suppl_qual_flag=item_input.suppl_qual_flag,
                include_in_raw=item_input.include_in_raw,
                gen_raw_seqno_flag=item_input.gen_raw_seqno_flag,
                enrich_build_order=item_input.enrich_build_order,
                label=item_input.label,
                state=item_input.state,
                extended_domain=item_input.extended_domain,
            ),
            library=library,
        )

    def _edit_aggregate(
        self, item: SponsorModelDatasetAR, item_edit_input: SponsorModelDatasetInput
    ) -> SponsorModelDatasetAR:
        item.edit_draft(
            author_id=self.author_id,
            sponsor_model_vo=SponsorModelDatasetVO.from_repository_values(
                target_data_model_catalogue=item_edit_input.target_data_model_catalogue,
                sponsor_model_name=item_edit_input.sponsor_model_name,
                sponsor_model_version_number=item_edit_input.sponsor_model_version_number,
                dataset_uid=item_edit_input.dataset_uid,
                is_basic_std=item_edit_input.is_basic_std,
                implemented_dataset_class=item_edit_input.implemented_dataset_class,
                xml_path=item_edit_input.xml_path,
                xml_title=item_edit_input.xml_title,
                structure=item_edit_input.structure,
                purpose=item_edit_input.purpose,
                keys=item_edit_input.keys,
                sort_keys=item_edit_input.sort_keys,
                is_cdisc_std=item_edit_input.is_cdisc_std,
                source_ig=item_edit_input.source_ig,
                standard_ref=item_edit_input.standard_ref,
                comment=item_edit_input.comment,
                ig_comment=item_edit_input.ig_comment,
                map_domain_flag=item_edit_input.map_domain_flag,
                suppl_qual_flag=item_edit_input.suppl_qual_flag,
                include_in_raw=item_edit_input.include_in_raw,
                gen_raw_seqno_flag=item_edit_input.gen_raw_seqno_flag,
                enrich_build_order=item_edit_input.enrich_build_order,
                label=item_edit_input.label,
                state=item_edit_input.state,
                extended_domain=item_edit_input.extended_domain,
            ),
        )
        return item
