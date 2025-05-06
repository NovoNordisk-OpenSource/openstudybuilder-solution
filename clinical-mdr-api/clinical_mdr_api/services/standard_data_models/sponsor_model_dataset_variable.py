from clinical_mdr_api.domain_repositories.standard_data_models.sponsor_model_dataset_variable_repository import (
    SponsorModelDatasetVariableRepository,
)
from clinical_mdr_api.domains.standard_data_models.sponsor_model_dataset_variable import (
    SponsorModelDatasetVariableAR,
    SponsorModelDatasetVariableVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.standard_data_models.sponsor_model_dataset_variable import (
    SponsorModelDatasetVariable,
    SponsorModelDatasetVariableInput,
)
from clinical_mdr_api.services.neomodel_ext_generic import NeomodelExtGenericService


class SponsorModelDatasetVariableService(NeomodelExtGenericService):
    repository_interface = SponsorModelDatasetVariableRepository
    api_model_class = SponsorModelDatasetVariable

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: SponsorModelDatasetVariableAR
    ) -> SponsorModelDatasetVariable:
        return SponsorModelDatasetVariable.from_sponsor_model_dataset_variable_ar(
            sponsor_model_dataset_variable_ar=item_ar,
        )

    def _create_aggregate_root(
        self, item_input: SponsorModelDatasetVariableInput, library: LibraryVO
    ) -> SponsorModelDatasetVariableAR:
        return SponsorModelDatasetVariableAR.from_input_values(
            author_id=self.author_id,
            sponsor_model_dataset_variable_vo=SponsorModelDatasetVariableVO.from_repository_values(
                target_data_model_catalogue=item_input.target_data_model_catalogue,
                dataset_uid=item_input.dataset_uid,
                variable_uid=item_input.dataset_variable_uid,
                sponsor_model_name=item_input.sponsor_model_name,
                sponsor_model_version_number=item_input.sponsor_model_version_number,
                is_basic_std=item_input.is_basic_std,
                implemented_parent_dataset_class=item_input.implemented_parent_dataset_class,
                implemented_variable_class=item_input.implemented_variable_class,
                label=item_input.label,
                order=item_input.order,
                variable_type=item_input.variable_type,
                length=item_input.length,
                display_format=item_input.display_format,
                xml_datatype=item_input.xml_datatype,
                xml_codelist=item_input.xml_codelist,
                xml_codelist_multi=item_input.xml_codelist_multi,
                core=item_input.core,
                origin=item_input.origin,
                origin_type=item_input.origin_type,
                origin_source=item_input.origin_source,
                role=item_input.role,
                term=item_input.term,
                algorithm=item_input.algorithm,
                qualifiers=item_input.qualifiers,
                is_cdisc_std=item_input.is_cdisc_std,
                comment=item_input.comment,
                ig_comment=item_input.ig_comment,
                class_table=item_input.class_table,
                class_column=item_input.class_column,
                map_var_flag=item_input.map_var_flag,
                fixed_mapping=item_input.fixed_mapping,
                include_in_raw=item_input.include_in_raw,
                nn_internal=item_input.nn_internal,
                value_lvl_where_cols=item_input.value_lvl_where_cols,
                value_lvl_label_col=item_input.value_lvl_label_col,
                value_lvl_collect_ct_val=item_input.value_lvl_collect_ct_val,
                value_lvl_ct_codelist_id_col=item_input.value_lvl_ct_codelist_id_col,
                enrich_build_order=item_input.enrich_build_order,
                enrich_rule=item_input.enrich_rule,
                xml_codelist_values=item_input.xml_codelist_values,
            ),
            library=library,
        )

    def _edit_aggregate(
        self,
        item: SponsorModelDatasetVariableAR,
        item_edit_input: SponsorModelDatasetVariableInput,
    ) -> SponsorModelDatasetVariableAR:
        item.edit_draft(
            author_id=self.author_id,
            sponsor_model_vo=SponsorModelDatasetVariableVO.from_repository_values(
                target_data_model_catalogue=item_edit_input.target_data_model_catalogue,
                dataset_uid=item_edit_input.dataset_uid,
                variable_uid=item_edit_input.dataset_variable_uid,
                sponsor_model_name=item_edit_input.sponsor_model_name,
                sponsor_model_version_number=item_edit_input.sponsor_model_version_number,
                is_basic_std=item_edit_input.is_basic_std,
                implemented_variable_class=item_edit_input.implemented_variable_class,
                implemented_parent_dataset_class=item_edit_input.implemented_parent_dataset_class,
                label=item_edit_input.label,
                order=item_edit_input.order,
                variable_type=item_edit_input.variable_type,
                length=item_edit_input.length,
                display_format=item_edit_input.display_format,
                xml_datatype=item_edit_input.xml_datatype,
                xml_codelist=item_edit_input.xml_codelist,
                xml_codelist_multi=item_edit_input.xml_codelist_multi,
                core=item_edit_input.core,
                origin=item_edit_input.origin,
                origin_type=item_edit_input.origin_type,
                origin_source=item_edit_input.origin_source,
                role=item_edit_input.role,
                term=item_edit_input.term,
                algorithm=item_edit_input.algorithm,
                qualifiers=item_edit_input.qualifiers,
                is_cdisc_std=item_edit_input.is_cdisc_std,
                comment=item_edit_input.comment,
                ig_comment=item_edit_input.ig_comment,
                class_table=item_edit_input.class_table,
                class_column=item_edit_input.class_column,
                map_var_flag=item_edit_input.map_var_flag,
                fixed_mapping=item_edit_input.fixed_mapping,
                include_in_raw=item_edit_input.include_in_raw,
                nn_internal=item_edit_input.nn_internal,
                value_lvl_where_cols=item_edit_input.value_lvl_where_cols,
                value_lvl_label_col=item_edit_input.value_lvl_label_col,
                value_lvl_collect_ct_val=item_edit_input.value_lvl_collect_ct_val,
                value_lvl_ct_codelist_id_col=item_edit_input.value_lvl_ct_codelist_id_col,
                enrich_build_order=item_edit_input.enrich_build_order,
                enrich_rule=item_edit_input.enrich_rule,
                xml_codelist_values=item_edit_input.xml_codelist_values,
            ),
        )
        return item
