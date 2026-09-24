from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCodelistRoot,
    CTTermContext,
    CTTermRoot,
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
    SponsorModelValue,
)
from clinical_mdr_api.domain_repositories.standard_data_models.standard_data_model_repository import (
    StandardDataModelRepository,
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


class SponsorModelDatasetVariableRepository(  # type: ignore[misc]
    StandardDataModelRepository,
    LibraryItemRepositoryImplBase[SponsorModelDatasetVariableAR],
):
    root_class = DatasetVariable
    value_class = SponsorModelDatasetVariableInstance
    return_model = SponsorModelDatasetVariable

    # pylint: disable=unused-argument
    def generic_match_clause(self, versioning_relationship: str):
        standard_data_model_label = self.root_class.__label__
        standard_data_model_value_label = self.value_class.__label__
        return f"""MATCH (standard_root:{standard_data_model_label})-[:HAS_INSTANCE]->
                (standard_value:{standard_data_model_value_label})
                <-[has_dataset_variable_rel:HAS_DATASET_VARIABLE]-(dataset_instance:SponsorModelDatasetInstance)
                <-[:HAS_DATASET]-(sponsor_model_value:SponsorModelValue)
                MATCH (dataset_root:Dataset)-[:HAS_INSTANCE]->(dataset_instance)"""

    def specific_alias_clause(self) -> str:
        return """
        *
        OPTIONAL MATCH (standard_value)-[:REFERENCES_CODELIST]->(ref_cl_root:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(ref_cl:CTCodelistAttributesValue)
        OPTIONAL MATCH (standard_value)-[:REFERENCES_TERM]->(ref_t_root:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(ref_t:CTTermAttributesValue)
        OPTIONAL MATCH (standard_root)<-[key:HAS_KEY]-(dataset_instance)
        WITH
            standard_root.uid AS uid,
            standard_value.is_basic_std AS is_basic_std,
            standard_value.label AS label,
            standard_value.variable_type AS variable_type,
            standard_value.length AS length,
            standard_value.display_format AS display_format,
            standard_value.xml_datatype AS xml_datatype,
            standard_value.core AS core,
            standard_value.origin AS origin,
            standard_value.origin_type AS origin_type,
            standard_value.origin_source AS origin_source,
            standard_value.role AS role,
            standard_value.term AS term,
            standard_value.algorithm AS algorithm,
            standard_value.qualifiers AS qualifiers,
            standard_value.is_cdisc_std AS is_cdisc_std,
            standard_value.comment AS comment,
            standard_value.ig_comment AS ig_comment,
            standard_value.class_table AS class_table,
            standard_value.class_column AS class_column,
            standard_value.map_var_flag AS map_var_flag,
            standard_value.fixed_mapping AS fixed_mapping,
            standard_value.include_in_raw AS include_in_raw,
            standard_value.nn_internal AS nn_internal,
            standard_value.value_lvl_where_cols AS value_lvl_where_cols,
            standard_value.value_lvl_label_col AS value_lvl_label_col,
            standard_value.value_lvl_collect_ct_val AS value_lvl_collect_ct_val,
            standard_value.value_lvl_ct_codelist_id_col AS value_lvl_ct_codelist_id_col,
            standard_value.enrich_build_order AS enrich_build_order,
            standard_value.enrich_rule AS enrich_rule,
            collect(DISTINCT CASE WHEN ref_cl IS NOT NULL THEN {uid: ref_cl_root.uid, submission_value: ref_cl.submission_value} END) AS referenced_codelists,
            collect(DISTINCT CASE WHEN ref_t IS NOT NULL THEN {uid: ref_t_root.uid, submission_value: ref_t.code_submission_value} END) AS referenced_terms,
            {ordinal: has_dataset_variable_rel.ordinal, key_order: key.order, version_number: has_dataset_variable_rel.version_number, uid: dataset_root.uid, sponsor_model_name: sponsor_model_value.name} AS dataset
        """

    def create_query_filter_statement(self, **kwargs) -> tuple[str, dict[Any, Any]]:
        (
            filter_statements_from_standard,
            filter_query_parameters,
        ) = super().create_query_filter_statement(**kwargs)
        filter_parameters = []

        sponsor_model_name = kwargs.get("sponsor_model_name")
        sponsor_model_version = kwargs.get("sponsor_model_version")

        if sponsor_model_name:
            filter_parameters.append("sponsor_model_value.name = $sponsor_model_name")
            filter_query_parameters["sponsor_model_name"] = sponsor_model_name

        if sponsor_model_version:
            filter_parameters.append(
                "has_dataset_variable_rel.version_number = $sponsor_model_version"
            )
            filter_query_parameters["sponsor_model_version"] = sponsor_model_version

        extended_filter_statements = " AND ".join(filter_parameters)
        if filter_statements_from_standard != "":
            if len(extended_filter_statements) > 0:
                filter_statements_to_return = " AND ".join(
                    [filter_statements_from_standard, extended_filter_statements]
                )
            else:
                filter_statements_to_return = filter_statements_from_standard
        else:
            filter_statements_to_return = (
                "WHERE " + extended_filter_statements
                if len(extended_filter_statements) > 0
                else ""
            )
        return filter_statements_to_return, filter_query_parameters

    def sort_by(self) -> dict[str, bool] | None:
        return {"dataset.ordinal": True}

    # Internal bookkeeping stored on the variable node that must not surface as
    # sponsor-defined extras.
    _EXTRA_PROPS_DENYLIST = frozenset(
        {
            "implemented_variable_class_inconsistency",
            "implemented_variable_class_uid",
            "implemented_parent_dataset_class_uid",
        }
    )

    # Structural fields persisted as declared node properties (not as sponsor extras).
    _STRUCTURAL_NODE_PROPS = frozenset({"label"})

    def get_instance_properties_by_uids(
        self, sponsor_model_name: str, variable_uids: list[str]
    ) -> dict[tuple[str, str], dict[str, Any]]:
        """
        Return each variable value node's stored property map, keyed by
        (variable_uid, dataset_uid), for the given sponsor model. A variable uid
        can be instantiated under several datasets, so the dataset disambiguates.
        """
        if not variable_uids:
            return {}
        rows, _ = db.cypher_query(
            """
            MATCH (root:DatasetVariable)-[:HAS_INSTANCE]->(value:SponsorModelDatasetVariableInstance)
                  <-[:HAS_DATASET_VARIABLE]-(di:SponsorModelDatasetInstance)
                  <-[:HAS_DATASET]-(sm:SponsorModelValue {name: $sm_name})
            MATCH (dataset_root:Dataset)-[:HAS_INSTANCE]->(di)
            WHERE root.uid IN $uids
            RETURN root.uid AS uid, dataset_root.uid AS dataset_uid,
                   properties(value) AS props
            """,
            {"sm_name": sponsor_model_name, "uids": list(variable_uids)},
        )
        result: dict[tuple[str, str], dict[str, Any]] = {}
        for uid, dataset_uid, props in rows:
            clean = {
                key: val
                for key, val in (props or {}).items()
                if key not in self._EXTRA_PROPS_DENYLIST
                and key not in self._STRUCTURAL_NODE_PROPS
            }
            result[(uid, dataset_uid)] = clean
        return result

    @staticmethod
    def _sanitize_extra_props(props: dict[str, Any] | None) -> dict[str, Any]:
        # Neo4j property keys cannot contain spaces or dashes. Also, `SET n += map`
        # silently drops any key whose value is None instead of storing it, so a
        # None-valued extra prop never actually reaches the node. Excluding it here
        # keeps this the single source of truth for both storage and comparison -
        # otherwise `_has_data_changed` would always see a (spurious) diff between
        # the None-valued key it expects and the absent key Neo4j actually stored.
        return {
            key.replace(" ", "_").replace("-", "_"): value
            for key, value in (props or {}).items()
            if value is not None
        }

    def _stored_extra_props(
        self, value: SponsorModelDatasetVariableInstance
    ) -> dict[str, Any]:
        rows, _ = db.cypher_query(
            "MATCH (n) WHERE elementId(n) = $element_id RETURN properties(n)",
            {"element_id": value.element_id},
        )
        props = rows[0][0] if rows else {}
        return {
            key: val
            for key, val in props.items()
            if key not in self._EXTRA_PROPS_DENYLIST
            and key not in self._STRUCTURAL_NODE_PROPS
        }

    def _has_data_changed(
        self,
        ar: SponsorModelDatasetVariableAR,
        value: SponsorModelDatasetVariableInstance,
    ) -> bool:
        # Structural fields are compared directly; the remaining sponsor data lives
        # in extra_properties, so a value node is reused only when both match exactly.
        return (
            ar.sponsor_model_dataset_variable_vo.label != value.label
            or self._sanitize_extra_props(
                ar.sponsor_model_dataset_variable_vo.extra_properties
            )
            != self._stored_extra_props(value)
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
            label=ar.sponsor_model_dataset_variable_vo.label
        )
        self._db_save_node(new_instance)

        # All sponsor data is stored via Cypher (neomodel only persists declared
        # properties), including the structural/extensible fields the schema owns.
        sanitized_props = self._sanitize_extra_props(
            ar.sponsor_model_dataset_variable_vo.extra_properties
        )
        if sanitized_props:
            db.cypher_query(
                "MATCH (n) WHERE elementId(n) = $element_id SET n += $extra_props",
                {"element_id": new_instance.element_id, "extra_props": sanitized_props},
            )

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
                inconsistency_props = {
                    "implemented_variable_class_inconsistency": True,
                    "implemented_variable_class_uid": ar.sponsor_model_dataset_variable_vo.implemented_variable_class,
                }
                if (
                    ar.sponsor_model_dataset_variable_vo.implemented_parent_dataset_class
                ):
                    inconsistency_props["implemented_parent_dataset_class_uid"] = (
                        ar.sponsor_model_dataset_variable_vo.implemented_parent_dataset_class
                    )
                db.cypher_query(
                    "MATCH (n) WHERE elementId(n) = $element_id SET n += $inconsistency_props",
                    {
                        "element_id": new_instance.element_id,
                        "inconsistency_props": inconsistency_props,
                    },
                )

        # Connect with Codelists & Terms
        for codelist_uid in (
            ar.sponsor_model_dataset_variable_vo.references_codelists or []
        ):
            codelist_node = CTCodelistRoot.nodes.get_or_none(uid=codelist_uid)
            BusinessLogicException.raise_if_not(
                codelist_node,
                msg=f"Could not find codelist with uid '{codelist_uid}'.",
            )
            new_instance.references_codelist.connect(codelist_node)
        for term_uid in ar.sponsor_model_dataset_variable_vo.references_terms or []:
            term_node = CTTermRoot.nodes.get_or_none(uid=term_uid)
            BusinessLogicException.raise_if_not(
                term_node,
                msg=f"Could not find term with uid '{term_uid}'.",
            )
            for codelist_uid in (
                ar.sponsor_model_dataset_variable_vo.references_codelists or []
            ):
                codelist_node = CTCodelistRoot.nodes.get_or_none(uid=codelist_uid)
                term_context = CTTermContext()
                self._db_save_node(term_context)
                term_context.has_selected_codelist.connect(codelist_node)
                term_context.has_selected_term.connect(term_node)
                new_instance.references_term.connect(term_context)
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
        ordinal = 0
        # Get parent dataset uid
        dataset: Dataset = dataset_value.is_instance_of.single()
        if dataset is not None:
            dataset_uid = dataset.uid

        # Get order in parent class
        dataset_rel = value.has_variable.relationship(dataset_value)
        ordinal = dataset_rel.ordinal
        sponsor_model_version = dataset_rel.version_number

        # Get sponsor model-related info
        sponsor_model_value: SponsorModelValue = dataset_value.has_dataset.single()
        sponsor_model_name = sponsor_model_value.name

        # All sponsor data lives in node properties; recover the full map since
        # neomodel does not inflate undeclared properties.
        extra_props = self._stored_extra_props(value)

        return SponsorModelDatasetVariableAR.from_repository_values(
            variable_uid=root.uid,
            sponsor_model_dataset_variable_vo=SponsorModelDatasetVariableVO.from_repository_values(
                dataset_uid=dataset_uid,
                variable_uid=root.uid,
                sponsor_model_name=sponsor_model_name,
                sponsor_model_version_number=sponsor_model_version,
                implemented_parent_dataset_class=None,
                implemented_variable_class=None,
                order=ordinal,
                references_codelists=None,
                references_terms=None,
                label=value.label,
                extra_properties=extra_props if extra_props else None,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
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
