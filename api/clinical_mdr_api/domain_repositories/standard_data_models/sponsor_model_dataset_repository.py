import logging
from typing import Any

from neomodel import NodeSet, db
from neomodel.sync_.match import Collect, NodeNameResolver, Path, RelationNameResolver

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
    DatasetClass,
    DatasetVariable,
    SponsorModelDatasetInstance,
    SponsorModelValue,
)
from clinical_mdr_api.domain_repositories.neomodel_ext_item_repository import (
    NeomodelExtBaseRepository,
)
from clinical_mdr_api.domains.standard_data_models.sponsor_model_dataset import (
    SponsorModelDatasetAR,
)
from clinical_mdr_api.models.standard_data_models.sponsor_model_dataset import (
    SponsorModelDataset,
)
from clinical_mdr_api.repositories._utils import FilterOperator
from common.exceptions import BusinessLogicException

log = logging.getLogger(__name__)


class SponsorModelDatasetRepository(  # type: ignore[misc]
    NeomodelExtBaseRepository, LibraryItemRepositoryImplBase[SponsorModelDatasetAR]
):
    root_class = Dataset
    value_class = SponsorModelDatasetInstance
    return_model = SponsorModelDataset

    def get_neomodel_extension_query(self) -> NodeSet:
        return (
            Dataset.nodes.traverse(
                "has_sponsor_model_instance__has_dataset",
                Path(
                    value="has_sponsor_model_instance__has_key",
                    optional=True,
                    include_rels_in_return=False,
                ),
                Path(
                    value="has_sponsor_model_instance__has_sort_key",
                    optional=True,
                    include_rels_in_return=False,
                ),
            )
            .unique_variables("has_sponsor_model_instance")
            .annotate(
                Collect(
                    NodeNameResolver("has_sponsor_model_instance__has_key"),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver("has_sponsor_model_instance__has_key"),
                    distinct=True,
                ),
                Collect(
                    NodeNameResolver("has_sponsor_model_instance__has_sort_key"),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver("has_sponsor_model_instance__has_sort_key"),
                    distinct=True,
                ),
            )
            .order_by("has_sponsor_model_instance__has_dataset|ordinal")
        )

    def _get_subgraph_and_filters(
        self,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        **kwargs,
    ) -> tuple[list[Any], list[Any]]:
        """
        Override to add sponsor_model_name filtering support.
        """
        sponsor_model_name = kwargs.get("sponsor_model_name")
        if sponsor_model_name:
            if filter_by is None:
                filter_by = {}
            filter_by["sponsor_model.name"] = {"v": [sponsor_model_name], "op": "eq"}

        return super()._get_subgraph_and_filters(
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=filter_by,
            filter_operator=filter_operator,
        )

    def _build_models_from_subgraph(
        self, subgraph: list[Any]
    ) -> list[SponsorModelDataset]:
        """
        Override to extract ordered keys and sort_keys from subgraph relationships.
        """
        all_data_model = []
        for node in subgraph:
            model = self.return_model.model_validate(node)

            # Extract ordered keys and sort_keys from subgraph relationships
            if (
                hasattr(node, "_relations")
                and "has_sponsor_model_instance" in node._relations
            ):
                instance = node._relations["has_sponsor_model_instance"]

                # Extract keys with order
                if (
                    hasattr(instance, "_relations")
                    and "has_key" in instance._relations
                    and "has_key_relationship" in instance._relations
                ):
                    key_nodes = instance._relations["has_key"]
                    key_rels = instance._relations["has_key_relationship"]

                    if isinstance(key_nodes, list) and isinstance(key_rels, list):
                        # Build a map of element_id -> uid from nodes
                        node_map = {}
                        for key_node in key_nodes:
                            if hasattr(key_node, "element_id") and hasattr(
                                key_node, "uid"
                            ):
                                node_map[key_node.element_id] = key_node.uid

                        # Match relationships to nodes and build ordered list
                        key_list = []
                        for rel in key_rels:
                            if hasattr(rel, "_end_node_element_id") and hasattr(
                                rel, "order"
                            ):
                                end_id = rel._end_node_element_id
                                if end_id in node_map:
                                    key_list.append((rel.order, node_map[end_id]))

                        if key_list:
                            key_list.sort(key=lambda x: x[0])
                            model.keys = [uid for _, uid in key_list]

                # Extract sort_keys with order
                if (
                    hasattr(instance, "_relations")
                    and "has_sort_key" in instance._relations
                    and "has_sort_key_relationship" in instance._relations
                ):
                    sort_key_nodes = instance._relations["has_sort_key"]
                    sort_key_rels = instance._relations["has_sort_key_relationship"]

                    if isinstance(sort_key_nodes, list) and isinstance(
                        sort_key_rels, list
                    ):
                        # Build a map of element_id -> uid from nodes
                        node_map = {}
                        for sort_key_node in sort_key_nodes:
                            if hasattr(sort_key_node, "element_id") and hasattr(
                                sort_key_node, "uid"
                            ):
                                node_map[sort_key_node.element_id] = sort_key_node.uid

                        # Match relationships to nodes and build ordered list
                        sort_key_list = []
                        for rel in sort_key_rels:
                            if hasattr(rel, "_end_node_element_id") and hasattr(
                                rel, "order"
                            ):
                                end_id = rel._end_node_element_id
                                if end_id in node_map:
                                    sort_key_list.append((rel.order, node_map[end_id]))

                        if sort_key_list:
                            sort_key_list.sort(key=lambda x: x[0])
                            model.sort_keys = [uid for _, uid in sort_key_list]

            all_data_model.append(model)

        return all_data_model

    def get_distinct_headers(
        self,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
        **kwargs,
    ) -> list[Any]:
        sponsor_model_name = kwargs.get("sponsor_model_name")
        if sponsor_model_name:
            if filter_by is None:
                filter_by = {}
            filter_by["sponsor_model.name"] = {"v": [sponsor_model_name], "op": "eq"}
        return super().get_distinct_headers(
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )

    def get_instance_properties_by_uids(
        self, sponsor_model_name: str, dataset_uids: list[str]
    ) -> dict[str, dict[str, Any]]:
        """
        Return the full stored property map of each dataset's value node, keyed by
        dataset uid, for the given sponsor model. Used to recover extensible /
        undeclared fields that neomodel does not inflate onto the node.
        """
        if not dataset_uids:
            return {}
        rows, _ = db.cypher_query(
            """
            MATCH (root:Dataset)-[:HAS_INSTANCE]->(value:SponsorModelDatasetInstance)
                  <-[:HAS_DATASET]-(sm:SponsorModelValue {name: $sm_name})
            WHERE root.uid IN $uids
            RETURN root.uid AS uid, properties(value) AS props
            """,
            {"sm_name": sponsor_model_name, "uids": list(dataset_uids)},
        )
        return {row[0]: row[1] or {} for row in rows}

    # Structural fields persisted as declared node properties (not sponsor extras):
    # they must be excluded from the extras comparison / recovery and handled directly.
    _STRUCTURAL_NODE_PROPS = frozenset({"label"})

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
        self,
        value: SponsorModelDatasetInstance,
    ) -> dict[str, Any]:
        rows, _ = db.cypher_query(
            "MATCH (n) WHERE elementId(n) = $element_id RETURN properties(n)",
            {"element_id": value.element_id},
        )
        props = rows[0][0] if rows else {}
        return {
            key: val
            for key, val in props.items()
            if key not in self._STRUCTURAL_NODE_PROPS
        }

    @staticmethod
    def _get_ordered_keys_and_sort_keys(
        value: SponsorModelDatasetInstance,
    ) -> tuple[list[str] | None, list[str] | None]:
        """
        Extract keys and sort_keys with their order from already-loaded relationships.
        Returns tuple of (keys, sort_keys) as ordered lists of UIDs.
        """
        # Extract keys with their order from relationships
        keys = None
        if hasattr(value, "has_key"):
            key_nodes = value.has_key.all()
            if key_nodes:
                # Get all relationships to access order properties
                key_rels = value.has_key.all_relationships(*key_nodes)
                if key_rels:
                    # Build list of (order, uid) tuples and sort
                    key_list = [
                        (rel.order, node.uid)
                        for rel, node in zip(key_rels, key_nodes)
                        if hasattr(rel, "order")
                    ]
                    if key_list:
                        key_list.sort(key=lambda x: x[0])
                        keys = [uid for _, uid in key_list]

        # Extract sort_keys with their order from relationships
        sort_keys = None
        if hasattr(value, "has_sort_key"):
            sort_key_nodes = value.has_sort_key.all()
            if sort_key_nodes:
                # Get all relationships to access order properties
                sort_key_rels = value.has_sort_key.all_relationships(*sort_key_nodes)
                if sort_key_rels:
                    # Build list of (order, uid) tuples and sort
                    sort_key_list = [
                        (rel.order, node.uid)
                        for rel, node in zip(sort_key_rels, sort_key_nodes)
                        if hasattr(rel, "order")
                    ]
                    if sort_key_list:
                        sort_key_list.sort(key=lambda x: x[0])
                        sort_keys = [uid for _, uid in sort_key_list]

        return keys, sort_keys

    def _has_data_changed(
        self, ar: SponsorModelDatasetAR, value: SponsorModelDatasetInstance
    ) -> bool:
        # Structural fields are compared directly; the remaining sponsor data lives
        # in extra_properties, so a value node is reused only when both match exactly.
        return (
            ar.sponsor_model_dataset_vo.label != value.label
            or self._sanitize_extra_props(ar.sponsor_model_dataset_vo.extra_properties)
            != self._stored_extra_props(value)
        )

    def _create(self, item: SponsorModelDatasetAR) -> SponsorModelDatasetAR:
        """
        Overrides generic LibraryItemRepository method
        """
        root = Dataset.nodes.get_or_none(uid=item.uid)

        if not root:
            # Create a new "root" node with uid
            root = Dataset(uid=item.uid).save()
            # Link it with the DataModelCatalogue node
            catalogue = DataModelCatalogue.nodes.get_or_none(
                name=item.sponsor_model_dataset_vo.target_data_model_catalogue
            )
            root.has_dataset.connect(catalogue)

        instance = self._get_or_create_instance(root=root, ar=item)

        # Connect with SponsorModelValue node
        parent_node = SponsorModelValue.nodes.get_or_none(
            name=item.sponsor_model_dataset_vo.sponsor_model_name
        )

        BusinessLogicException.raise_if_not(
            parent_node,
            msg=f"Sponsor Model with Name '{item.sponsor_model_dataset_vo.sponsor_model_name}' doesn't exist.",
        )

        instance.has_dataset.connect(
            parent_node,
            {"ordinal": item.sponsor_model_dataset_vo.enrich_build_order},
        )

        return item

    def _get_or_create_instance(
        self, root: Dataset, ar: SponsorModelDatasetAR
    ) -> SponsorModelDatasetInstance:
        for itm in root.has_sponsor_model_instance.all():
            if not self._has_data_changed(ar, itm):
                return itm

        new_instance = SponsorModelDatasetInstance(
            label=ar.sponsor_model_dataset_vo.label
        )
        self._db_save_node(new_instance)

        # Remaining sponsor data is stored via Cypher (neomodel only persists
        # declared properties), i.e. the extensible fields the schema owns.
        sanitized_props = self._sanitize_extra_props(
            ar.sponsor_model_dataset_vo.extra_properties
        )
        if sanitized_props:
            db.cypher_query(
                "MATCH (n) WHERE elementId(n) = $element_id SET n += $extra_props",
                {"element_id": new_instance.element_id, "extra_props": sanitized_props},
            )

        # Connect with root
        root.has_sponsor_model_instance.connect(new_instance)

        # Create relations
        # Find key & sort-key variable nodes
        if ar.sponsor_model_dataset_vo.keys is not None:
            keys = DatasetVariable.nodes.filter(
                uid__in=ar.sponsor_model_dataset_vo.keys
            )
            keys_dict = {key.uid: key for key in keys}
            for index, key in enumerate(ar.sponsor_model_dataset_vo.keys):
                if key in keys_dict:
                    # Connect the instance node to its keys - represented by DatasetVariable nodes
                    new_instance.has_key.connect(keys_dict[key], {"order": index})
                else:
                    # If the key does not exist yet, create a new DatasetVariable node
                    # This will be a placeholder until instantiated,
                    # probably by this version of the sponsor model
                    new_root = DatasetVariable(uid=key)
                    self._db_save_node(new_root)
                    data_model_catalogue = DataModelCatalogue.nodes.get_or_none(
                        name=ar.sponsor_model_dataset_vo.target_data_model_catalogue
                    )
                    BusinessLogicException.raise_if_not(
                        data_model_catalogue,
                        msg=(
                            "Data model catalogue "
                            f"'{ar.sponsor_model_dataset_vo.target_data_model_catalogue}' not found."
                        ),
                    )
                    new_root.has_dataset_variable.connect(data_model_catalogue)

                    new_instance.has_key.connect(new_root, {"order": index})

        if ar.sponsor_model_dataset_vo.sort_keys is not None:
            sort_keys = DatasetVariable.nodes.filter(
                uid__in=ar.sponsor_model_dataset_vo.sort_keys
            )
            sort_keys_dict = {key.uid: key for key in sort_keys}
            for index, key in enumerate(ar.sponsor_model_dataset_vo.sort_keys):
                if key in sort_keys_dict:
                    new_instance.has_sort_key.connect(
                        sort_keys_dict[key], {"order": index}
                    )

        # Connect with implemented dataset class - if provided
        if ar.sponsor_model_dataset_vo.implemented_dataset_class:
            implemented_dataset_class = DatasetClass.nodes.filter(
                uid=ar.sponsor_model_dataset_vo.implemented_dataset_class,
                has_instance__has_dataset_class__implements__extended_by__name=ar.sponsor_model_dataset_vo.sponsor_model_name,
            ).traverse("has_instance")
            if not implemented_dataset_class:
                log.warning(
                    "Dataset class with uid '%s' not found for sponsor model '%s'; "
                    "dataset '%s' will be created without a dataset class link.",
                    ar.sponsor_model_dataset_vo.implemented_dataset_class,
                    ar.sponsor_model_dataset_vo.sponsor_model_name,
                    ar.sponsor_model_dataset_vo.dataset_uid,
                )
            else:
                implemented_dataset_class_instance = (
                    implemented_dataset_class.resolve_subgraph()[0]._relations[
                        "has_instance"
                    ]
                )
                new_instance.implements_dataset_class.connect(
                    implemented_dataset_class_instance
                )

        return new_instance

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: Dataset,
        library: Library,
        relationship: VersionRelationship,
        value: SponsorModelDatasetInstance,
        **_kwargs,
    ) -> None:
        # This method from parent repo is not needed for this repo
        # So we use pass to skip implementation
        pass

    def _maintain_parameters(
        self,
        versioned_object: SponsorModelDatasetAR,
        root: Dataset,
        value: SponsorModelDatasetInstance,
    ) -> None:
        # This method from parent repo is not needed for this repo
        # So we use pass to skip implementation
        pass
