from typing import Any

from neomodel import NodeSet, db
from neomodel.sync_.match import (
    Collect,
    Last,
    NodeNameResolver,
    RawCypher,
    RelationNameResolver,
)

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.models._utils import ListDistinct
from clinical_mdr_api.domain_repositories.models.activities import ActivityGrouping
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.data_supplier_rules import (
    DataSupplierRuleRoot,
    DataSupplierRuleValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.neomodel_ext_item_repository import (
    NeomodelExtBaseRepository,
)
from clinical_mdr_api.domains.data_supplier_rules.data_supplier_rule import (
    DataSupplierRuleActivityGroupingVO,
    DataSupplierRuleAR,
    DataSupplierRuleVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.data_supplier_rules.data_supplier_rule import (
    DataSupplierRule,
)
from common.config import settings
from common.exceptions import BusinessLogicException


class DataSupplierRuleRepository(  # type: ignore[misc]
    NeomodelExtBaseRepository, LibraryItemRepositoryImplBase[_AggregateRootType]
):

    root_class = DataSupplierRuleRoot
    value_class = DataSupplierRuleValue
    return_model = DataSupplierRule

    def get_neomodel_extension_query(self) -> NodeSet:
        return DataSupplierRuleRoot.nodes.traverse(
            "has_latest_value",
            "has_library",
        ).subquery(
            DataSupplierRuleRoot.nodes.traverse(latest_version="has_version")
            .intermediate_transform(
                {"rel": {"source": RelationNameResolver("has_version")}},
                ordering=[
                    RawCypher("toInteger(split(rel.version, '.')[0])"),
                    RawCypher("toInteger(split(rel.version, '.')[1])"),
                    "rel.end_date",
                    "rel.start_date",
                ],
            )
            .annotate(latest_version=Last(Collect("rel"))),
            ["latest_version"],
            initial_context=[NodeNameResolver("self")],
        )

    def extend_distinct_headers_query(
        self,
        nodeset: NodeSet,
        field_name: str,
        filter_by: dict[str, dict[str, Any]] | None = None,
    ) -> NodeSet:
        # Get version relationship properties dynamically
        version_properties = set(VersionRelationship.defined_properties().keys())
        # Map author_id to author_username as it's exposed that way in the API
        version_fields = version_properties | {"author_username"}
        version_fields.discard("author_id")

        # Check if we need version data
        need_latest_version = field_name in version_fields
        if not need_latest_version and filter_by:
            need_latest_version = any(key in version_fields for key in filter_by.keys())

        if need_latest_version:
            return nodeset.subquery(
                self.root_class.nodes.traverse("has_version")
                .intermediate_transform(
                    {"rel": {"source": RelationNameResolver("has_version")}},
                    ordering=[
                        RawCypher("toInteger(split(rel.version, '.')[0])"),
                        RawCypher("toInteger(split(rel.version, '.')[1])"),
                        "rel.end_date",
                        "rel.start_date",
                    ],
                )
                .annotate(latest_version=Last(Collect("rel"))),
                ["latest_version"],
                initial_context=[NodeNameResolver("self")],
            )
        return nodeset

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: DataSupplierRuleRoot,
        library: Library,
        relationship: VersionRelationship,
        value: DataSupplierRuleValue,
        **_kwargs,
    ) -> _AggregateRootType:
        return DataSupplierRuleAR.from_repository_values(
            uid=root.uid,
            data_supplier_rule_vo=DataSupplierRuleVO(
                description=value.description,
                name=value.name,
                activity_groupings=self._read_activity_groupings(value),
                data_supplier_type_uid=self._read_data_supplier_type_uid(value),
            ),
            library=LibraryVO.from_input_values_2(
                library.name, lambda _: library.is_editable
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _read_activity_groupings(
        self, value: DataSupplierRuleValue
    ) -> tuple[DataSupplierRuleActivityGroupingVO, ...]:
        groupings = []
        for grouping_node in value.has_activity_grouping.all():
            group_value = grouping_node.has_selected_group.single()
            subgroup_value = grouping_node.has_selected_subgroup.single()
            activity_value = grouping_node.has_grouping.single()
            groupings.append(
                DataSupplierRuleActivityGroupingVO.from_repository_values(
                    activity_uid=activity_value.has_version.single().uid,
                    activity_name=activity_value.name,
                    activity_group_uid=group_value.has_version.single().uid,
                    activity_group_name=group_value.name,
                    activity_subgroup_uid=subgroup_value.has_version.single().uid,
                    activity_subgroup_name=subgroup_value.name,
                )
            )
        return tuple(groupings)

    def find_latest_activity_groupings(
        self, uid: str
    ) -> tuple[DataSupplierRuleActivityGroupingVO, ...]:
        root = DataSupplierRuleRoot.nodes.get_or_none(uid=uid)
        if root is None:
            return ()
        value = root.has_latest_value.single()
        if value is None:
            return ()
        return self._read_activity_groupings(value)

    def _read_data_supplier_type_uid(self, value: DataSupplierRuleValue) -> str | None:
        context_node = value.has_data_supplier_type.single()
        if context_node is None:
            return None
        selected_term = context_node.has_selected_term.single()
        return selected_term.uid if selected_term is not None else None

    def find_latest_data_supplier_type_uid(self, uid: str) -> str | None:
        root = DataSupplierRuleRoot.nodes.get_or_none(uid=uid)
        if root is None:
            return None
        value = root.has_latest_value.single()
        if value is None:
            return None
        return self._read_data_supplier_type_uid(value)

    @staticmethod
    def data_supplier_type_has_submission_value(
        type_uid: str, submission_value: str
    ) -> bool:
        """
        Checks whether the CTTerm identified by `type_uid` is connected, within the
        codelist identified by `settings.data_supplier_type_cl_submval`, to the given
        submission value (the stable, human-independent identifier for a specific
        CTTerm, e.g. "EDC SYSTEM"). Submission values are only unique within a
        codelist, so the match must be scoped to that specific codelist, otherwise a
        term in an unrelated codelist reusing the same submission value would be
        incorrectly matched.
        """
        query = """
            MATCH (codelist_root:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->
                (:CTCodelistAttributesRoot)-[:LATEST_FINAL]->
                (:CTCodelistAttributesValue {submission_value: $codelist_submission_value})
            MATCH (codelist_root)-[:HAS_TERM]->
                (:CTCodelistTerm {submission_value: $submission_value})-[:HAS_TERM_ROOT]->
                (:CTTermRoot {uid: $type_uid})
            RETURN true
            """
        result, _ = db.cypher_query(
            query,
            {
                "type_uid": type_uid,
                "submission_value": submission_value,
                "codelist_submission_value": settings.data_supplier_type_cl_submval,
            },
        )
        return len(result) > 0

    def name_exists(self, name: str, uid_to_exclude: str | None = None) -> bool:
        """
        Checks whether another DataSupplierRule (identified by its latest value) already
        uses the given name, excluding `uid_to_exclude` (used to allow keeping the current
        name unchanged when editing an existing rule).
        """
        query = """
            MATCH (root:DataSupplierRuleRoot)-[:LATEST]->(value:DataSupplierRuleValue {name: $name})
            WHERE any(label IN labels(root) WHERE NOT label STARTS WITH 'Deleted')
            AND ($uid_to_exclude IS NULL OR root.uid <> $uid_to_exclude)
            RETURN root
            """
        result, _ = db.cypher_query(
            query, {"name": name, "uid_to_exclude": uid_to_exclude}
        )
        return len(result) > 0

    def _has_data_changed(
        self, ar: DataSupplierRuleAR, value: DataSupplierRuleValue
    ) -> bool:
        existing_groupings = {
            (g.activity_uid, g.activity_group_uid, g.activity_subgroup_uid)
            for g in self._read_activity_groupings(value)
        }
        new_groupings = {
            (g.activity_uid, g.activity_group_uid, g.activity_subgroup_uid)
            for g in ar.data_supplier_rule_vo.activity_groupings
        }

        existing_type_uid = self._read_data_supplier_type_uid(value)
        new_type_uid = ar.data_supplier_rule_vo.data_supplier_type_uid

        return (
            ar.data_supplier_rule_vo.description != value.description
            or ar.data_supplier_rule_vo.name != value.name
            or existing_groupings != new_groupings
            or existing_type_uid != new_type_uid
        )

    @staticmethod
    def find_activity_grouping_node(
        activity_uid: str,
        activity_group_uid: str,
        activity_subgroup_uid: str,
    ) -> ActivityGrouping | None:
        nodes = ListDistinct(
            ActivityGrouping.nodes.filter(
                has_selected_group__has_version__uid=activity_group_uid,
                has_selected_subgroup__has_version__uid=activity_subgroup_uid,
                has_grouping__latest_final__uid=activity_uid,
            ).resolve_subgraph()
        ).distinct()
        return nodes[0] if nodes else None

    def activity_grouping_exists(
        self,
        activity_uid: str,
        activity_group_uid: str,
        activity_subgroup_uid: str,
    ) -> bool:
        return (
            self.find_activity_grouping_node(
                activity_uid, activity_group_uid, activity_subgroup_uid
            )
            is not None
        )

    def _get_or_create_value(
        self,
        root: DataSupplierRuleRoot,
        ar: DataSupplierRuleAR,
        force_new_value_node: bool = False,
    ) -> DataSupplierRuleValue:
        if not force_new_value_node:
            for itm in root.has_version.all():
                if not self._has_data_changed(ar, itm):
                    return itm
            latest_draft = root.latest_draft.get_or_none()
            if latest_draft and not self._has_data_changed(ar, latest_draft):
                return latest_draft
            latest_final = root.latest_final.get_or_none()
            if latest_final and not self._has_data_changed(ar, latest_final):
                return latest_final
            latest_retired = root.latest_retired.get_or_none()
            if latest_retired and not self._has_data_changed(ar, latest_retired):
                return latest_retired

        new_value = DataSupplierRuleValue(
            description=ar.data_supplier_rule_vo.description,
            name=ar.data_supplier_rule_vo.name,
        )

        self._db_save_node(new_value)

        for grouping in ar.data_supplier_rule_vo.activity_groupings:
            activity_grouping_node = self.find_activity_grouping_node(
                grouping.activity_uid,
                grouping.activity_group_uid,
                grouping.activity_subgroup_uid,
            )
            BusinessLogicException.raise_if(
                activity_grouping_node is None,
                msg=(
                    "The ActivityGrouping wasn't found for Activity with UID "
                    f"'{grouping.activity_uid}', Activity Group with UID "
                    f"'{grouping.activity_group_uid}' and Activity Subgroup with UID "
                    f"'{grouping.activity_subgroup_uid}'."
                ),
            )
            new_value.has_activity_grouping.connect(activity_grouping_node)

        if ar.data_supplier_rule_vo.data_supplier_type_uid:
            data_supplier_type = CTTermRoot.nodes.get_or_none(
                uid=ar.data_supplier_rule_vo.data_supplier_type_uid
            )
            if data_supplier_type is None:
                raise ValueError(
                    f"CTTerm with UID '{ar.data_supplier_rule_vo.data_supplier_type_uid}' not found"
                )
            selected_type_node = (
                CTCodelistAttributesRepository().get_or_create_selected_term(
                    data_supplier_type,
                    codelist_submission_value=settings.data_supplier_type_cl_submval,
                )
            )
            new_value.has_data_supplier_type.connect(selected_type_node)

        return new_value

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: DataSupplierRuleRoot,
        value: DataSupplierRuleValue,
    ) -> None:
        # This method from parent repo is not needed for this repo
        # So we use pass to skip implementation
        pass

    def generate_uid(self) -> str:
        return DataSupplierRuleRoot.get_next_free_uid_and_increment_counter()
