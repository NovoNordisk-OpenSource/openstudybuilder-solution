from neomodel import NodeSet, db
from neomodel.sync_.match import Optional

from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    DataModelCatalogue,
    Dataset,
    DatasetVariable,
    SponsorModelDatasetInstance,
    SponsorModelDatasetVariableInstance,
)
from clinical_mdr_api.domain_repositories.neomodel_ext_item_repository import (
    NeomodelExtBaseRepository,
)
from clinical_mdr_api.domain_repositories.standard_data_models.utils import (
    get_sponsor_model_info_from_dataset,
)
from clinical_mdr_api.domains.standard_data_models.sponsor_model_dataset_variable import (
    SponsorModelDatasetVariableAR,
    SponsorModelDatasetVariableVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.standard_data_models.sponsor_model_dataset_variable import (
    SponsorModelDatasetVariable,
)
from common.exceptions import BusinessLogicException


class SponsorModelDatasetVariableRepository(
    NeomodelExtBaseRepository,
    LibraryItemRepositoryImplBase[SponsorModelDatasetVariableAR],
):
    root_class = DatasetVariable
    value_class = SponsorModelDatasetVariableInstance
    return_model = SponsorModelDatasetVariable

    def get_neomodel_extension_query(self) -> NodeSet:
        return DatasetVariable.nodes.fetch_relations(
            "has_sponsor_model_instance__has_variable",
            "has_dataset_variable__has_library",
            Optional(
                "has_sponsor_model_instance__implements_variable_class__is_instance_of"
            ),
            Optional(
                "has_sponsor_model_instance__implements_variable_class__has_variable_class__is_instance_of"
            ),
        )

    def _has_data_changed(
        self,
        ar: SponsorModelDatasetVariableAR,
        value: SponsorModelDatasetVariableInstance,
    ) -> bool:
        return (
            ar.sponsor_model_dataset_variable_vo.is_basic_std != value.is_basic_std
            or ar.sponsor_model_dataset_variable_vo.label != value.label
            or ar.sponsor_model_dataset_variable_vo.variable_type != value.variable_type
            or ar.sponsor_model_dataset_variable_vo.length != value.length
            or ar.sponsor_model_dataset_variable_vo.display_format
            != value.display_format
            or ar.sponsor_model_dataset_variable_vo.xml_datatype != value.xml_datatype
            or ar.sponsor_model_dataset_variable_vo.xml_codelist != value.xml_codelist
            or ar.sponsor_model_dataset_variable_vo.xml_codelist_multi
            != value.xml_codelist_multi
            or ar.sponsor_model_dataset_variable_vo.core != value.core
            or ar.sponsor_model_dataset_variable_vo.origin != value.origin
            or ar.sponsor_model_dataset_variable_vo.origin_type != value.origin_type
            or ar.sponsor_model_dataset_variable_vo.origin_source != value.origin_source
            or ar.sponsor_model_dataset_variable_vo.role != value.role
            or ar.sponsor_model_dataset_variable_vo.term != value.term
            or ar.sponsor_model_dataset_variable_vo.algorithm != value.algorithm
            or ar.sponsor_model_dataset_variable_vo.qualifiers != value.qualifiers
            or ar.sponsor_model_dataset_variable_vo.is_cdisc_std != value.is_cdisc_std
            or ar.sponsor_model_dataset_variable_vo.comment != value.comment
            or ar.sponsor_model_dataset_variable_vo.ig_comment != value.ig_comment
            or ar.sponsor_model_dataset_variable_vo.class_table != value.class_table
            or ar.sponsor_model_dataset_variable_vo.class_column != value.class_column
            or ar.sponsor_model_dataset_variable_vo.map_var_flag != value.map_var_flag
            or ar.sponsor_model_dataset_variable_vo.fixed_mapping != value.fixed_mapping
            or ar.sponsor_model_dataset_variable_vo.include_in_raw
            != value.include_in_raw
            or ar.sponsor_model_dataset_variable_vo.nn_internal != value.nn_internal
            or ar.sponsor_model_dataset_variable_vo.value_lvl_where_cols
            != value.value_lvl_where_cols
            or ar.sponsor_model_dataset_variable_vo.value_lvl_label_col
            != value.value_lvl_label_col
            or ar.sponsor_model_dataset_variable_vo.value_lvl_collect_ct_val
            != value.value_lvl_collect_ct_val
            or ar.sponsor_model_dataset_variable_vo.value_lvl_ct_codelist_id_col
            != value.value_lvl_ct_codelist_id_col
            or ar.sponsor_model_dataset_variable_vo.enrich_build_order
            != value.enrich_build_order
            or ar.sponsor_model_dataset_variable_vo.enrich_rule != value.enrich_rule
            or ar.sponsor_model_dataset_variable_vo.xml_codelist_values
            != value.xml_codelist_values
        )

    def _create(
        self, item: SponsorModelDatasetVariableAR
    ) -> SponsorModelDatasetVariableAR:
        """
        Overrides generic LibraryItemRepository method
        """
        root = DatasetVariable.nodes.get_or_none(uid=item.uid)

        if not root:
            # Create a new "root" node with uid
            root = DatasetVariable(uid=item.uid).save()
            # Link it with the DataModelCatalogue node
            catalogue = DataModelCatalogue.nodes.get_or_none(
                name=item.sponsor_model_dataset_variable_vo.target_data_model_catalogue
            )
            root.has_dataset_variable.connect(catalogue)

        instance = self._get_or_create_instance(root=root, ar=item)

        # Connect with SponsorModelDatasetInstance
        parent_dataset_instance = SponsorModelDatasetInstance.nodes.filter(
            is_instance_of__uid=item.sponsor_model_dataset_variable_vo.dataset_uid,
            has_dataset__name=item.sponsor_model_dataset_variable_vo.sponsor_model_name,
        ).resolve_subgraph()
        BusinessLogicException.raise_if_not(
            parent_dataset_instance,
            msg=f"Dataset with UID '{item.sponsor_model_dataset_variable_vo.dataset_uid}' is not instantiated in this version of the sponsor model.",
        )
        instance.has_variable.connect(
            parent_dataset_instance[0],
            {
                "ordinal": item.sponsor_model_dataset_variable_vo.order,
                "version_number": item.sponsor_model_dataset_variable_vo.sponsor_model_version_number,
            },
        )

        return item

    def _get_or_create_instance(
        self, root: DatasetVariable, ar: SponsorModelDatasetVariableAR
    ) -> SponsorModelDatasetVariableInstance:
        for itm in root.has_sponsor_model_instance.all():
            if not self._has_data_changed(ar, itm):
                return itm

        new_instance = SponsorModelDatasetVariableInstance(
            is_basic_std=ar.sponsor_model_dataset_variable_vo.is_basic_std,
            label=ar.sponsor_model_dataset_variable_vo.label,
            variable_type=ar.sponsor_model_dataset_variable_vo.variable_type,
            length=ar.sponsor_model_dataset_variable_vo.length,
            display_format=ar.sponsor_model_dataset_variable_vo.display_format,
            xml_datatype=ar.sponsor_model_dataset_variable_vo.xml_datatype,
            xml_codelist=ar.sponsor_model_dataset_variable_vo.xml_codelist,
            xml_codelist_multi=ar.sponsor_model_dataset_variable_vo.xml_codelist_multi,
            core=ar.sponsor_model_dataset_variable_vo.core,
            origin=ar.sponsor_model_dataset_variable_vo.origin,
            origin_type=ar.sponsor_model_dataset_variable_vo.origin_type,
            origin_source=ar.sponsor_model_dataset_variable_vo.origin_source,
            role=ar.sponsor_model_dataset_variable_vo.role,
            term=ar.sponsor_model_dataset_variable_vo.term,
            algorithm=ar.sponsor_model_dataset_variable_vo.algorithm,
            qualifiers=ar.sponsor_model_dataset_variable_vo.qualifiers,
            is_cdisc_std=ar.sponsor_model_dataset_variable_vo.is_cdisc_std,
            comment=ar.sponsor_model_dataset_variable_vo.comment,
            ig_comment=ar.sponsor_model_dataset_variable_vo.ig_comment,
            class_table=ar.sponsor_model_dataset_variable_vo.class_table,
            class_column=ar.sponsor_model_dataset_variable_vo.class_column,
            map_var_flag=ar.sponsor_model_dataset_variable_vo.map_var_flag,
            fixed_mapping=ar.sponsor_model_dataset_variable_vo.fixed_mapping,
            include_in_raw=ar.sponsor_model_dataset_variable_vo.include_in_raw,
            nn_internal=ar.sponsor_model_dataset_variable_vo.nn_internal,
            value_lvl_where_cols=ar.sponsor_model_dataset_variable_vo.value_lvl_where_cols,
            value_lvl_label_col=ar.sponsor_model_dataset_variable_vo.value_lvl_label_col,
            value_lvl_collect_ct_val=ar.sponsor_model_dataset_variable_vo.value_lvl_collect_ct_val,
            value_lvl_ct_codelist_id_col=ar.sponsor_model_dataset_variable_vo.value_lvl_ct_codelist_id_col,
            enrich_build_order=ar.sponsor_model_dataset_variable_vo.enrich_build_order,
            enrich_rule=ar.sponsor_model_dataset_variable_vo.enrich_rule,
            xml_codelist_values=ar.sponsor_model_dataset_variable_vo.xml_codelist_values,
        )
        self._db_save_node(new_instance)

        # Connect with root
        root.has_sponsor_model_instance.connect(new_instance)

        # Connect with implemented variable class - if provided
        # Note : This is done through Cypher because the neomodel version with
        # chained traversal-based filters was creating a bad query
        if ar.sponsor_model_dataset_variable_vo.implemented_variable_class:
            results, _ = db.cypher_query(
                """
                    MATCH (vc:VariableClass)-[:`HAS_INSTANCE`]->(vci:VariableClassInstance)<-[:`HAS_VARIABLE_CLASS`]-(dci:DatasetClassInstance)
                    <-[:`HAS_DATASET_CLASS`]-(:DataModelValue)
                    <-[:`IMPLEMENTS`]-(ig:DataModelIGValue)<-[:`EXTENDS_VERSION`]-(smv:SponsorModelValue) 
                    MATCH (dci)<-[:`HAS_INSTANCE`]-(dc:DatasetClass)
                    WHERE 
                        smv.name = $smv_name 
                        AND dc.uid = $dc_uid
                        AND vc.uid = $vc_uid
                    RETURN vci
                """,
                params={
                    "smv_name": ar.sponsor_model_dataset_variable_vo.sponsor_model_name,
                    "dc_uid": ar.sponsor_model_dataset_variable_vo.implemented_parent_dataset_class,
                    "vc_uid": ar.sponsor_model_dataset_variable_vo.implemented_variable_class,
                },
                resolve_objects=True,
            )

            if results:
                implemented_variable_class_instance = results[0][0]
                new_instance.implements_variable_class.connect(
                    implemented_variable_class_instance
                )
            else:
                # If the target variable class is not found
                # Either because it does not exist or exists but not in the target parent dataset class
                # Do not raise an exception, but store information about the inconsistency on the node
                new_instance.implemented_variable_class_inconsistency = True
                new_instance.implemented_variable_class_uid = (
                    ar.sponsor_model_dataset_variable_vo.implemented_variable_class
                )
                new_instance.implemented_parent_dataset_class_uid = (
                    ar.sponsor_model_dataset_variable_vo.implemented_parent_dataset_class
                )
                self._db_save_node(new_instance)

        return new_instance

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: DatasetVariable,
        library: Library,
        relationship: VersionRelationship,
        value: SponsorModelDatasetVariableInstance,
        **_kwargs,
    ) -> SponsorModelDatasetVariableAR:
        # Get parent dataset-related info
        dataset_value: SponsorModelDatasetInstance = value.has_variable.get_or_none()
        dataset_uid = None
        sponsor_model_name = None
        sponsor_model_version = None
        ordinal = None
        if dataset_value is not None:
            # Get parent dataset uid
            dataset: Dataset = dataset_value.has_sponsor_model_instance.single()
            if dataset is not None:
                dataset_uid = dataset.uid

            # Get order in parent class
            dataset_rel = value.has_variable.relationship(dataset_value)
            if dataset_rel is not None:
                ordinal = dataset_rel.ordinal

            # Get sponsor model-related info
            (
                sponsor_model_name,
                sponsor_model_version,
                _,
            ) = get_sponsor_model_info_from_dataset(dataset_value, return_ordinal=False)
        return SponsorModelDatasetVariableAR.from_repository_values(
            variable_uid=root.uid,
            sponsor_model_dataset_variable_vo=SponsorModelDatasetVariableVO.from_repository_values(
                dataset_uid=dataset_uid,
                variable_uid=root.uid,
                sponsor_model_name=sponsor_model_name,
                sponsor_model_version_number=sponsor_model_version,
                is_basic_std=value.is_basic_std,
                implemented_parent_dataset_class=value.implemented_parent_dataset_class,
                implemented_variable_class=value.implemented_variable_class,
                label=value.label,
                order=ordinal,
                variable_type=value.variable_type,
                length=value.length,
                display_format=value.display_format,
                xml_datatype=value.xml_datatype,
                xml_codelist=value.xml_codelist,
                xml_codelist_multi=value.xml_codelist_multi,
                core=value.core,
                origin=value.origin,
                origin_type=value.origin_type,
                origin_source=value.origin_source,
                role=value.role,
                term=value.term,
                algorithm=value.algorithm,
                qualifiers=value.qualifiers,
                is_cdisc_std=value.is_cdisc_std,
                comment=value.comment,
                ig_comment=value.ig_comment,
                class_table=value.class_table,
                class_column=value.class_column,
                map_var_flag=value.map_var_flag,
                fixed_mapping=value.fixed_mapping,
                include_in_raw=value.include_in_raw,
                nn_internal=value.nn_internal,
                value_lvl_where_cols=value.value_lvl_where_cols,
                value_lvl_label_col=value.value_lvl_label_col,
                value_lvl_collect_ct_val=value.value_lvl_collect_ct_val,
                value_lvl_ct_codelist_id_col=value.value_lvl_ct_codelist_id_col,
                enrich_build_order=value.enrich_build_order,
                enrich_rule=value.enrich_rule,
                xml_codelist_values=value.xml_codelist_values,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _maintain_parameters(
        self,
        versioned_object: SponsorModelDatasetVariableAR,
        root: DatasetVariable,
        value: SponsorModelDatasetVariableInstance,
    ) -> None:
        # This method is not needed for this repo, so we use pass to skip implementation
        pass
