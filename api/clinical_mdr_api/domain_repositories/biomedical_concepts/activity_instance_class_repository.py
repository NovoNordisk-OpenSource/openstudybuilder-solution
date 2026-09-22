from typing import Any

from neomodel import NodeSet, db
from neomodel.sync_.match import (
    Collect,
    Last,
    NodeNameResolver,
    Path,
    RawCypher,
    RelationNameResolver,
)

from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.models.biomedical_concepts import (
    ActivityInstanceClassRoot,
    ActivityInstanceClassValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.standard_data_model import DatasetClass
from clinical_mdr_api.domain_repositories.neomodel_ext_item_repository import (
    NeomodelExtBaseRepository,
)
from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassActivityItemClassRelVO,
    ActivityInstanceClassAR,
    ActivityInstanceClassVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
    ActivityInstanceClassWithDataset,
)
from common.utils import validate_page_number_and_page_size


class ActivityInstanceClassRepository(  # type: ignore[misc]
    NeomodelExtBaseRepository, LibraryItemRepositoryImplBase[_AggregateRootType]
):
    root_class = ActivityInstanceClassRoot
    value_class = ActivityInstanceClassValue
    return_model = ActivityInstanceClass

    def get_neomodel_extension_query(self) -> NodeSet:
        return (
            ActivityInstanceClassRoot.nodes.traverse(
                "has_latest_value",
                "has_library",
                Path(
                    value="parent_class",
                    optional=True,
                    include_rels_in_return=False,
                ),
                Path(
                    value="parent_class__has_latest_value",
                    optional=True,
                    include_rels_in_return=False,
                ),
            )
            .unique_variables(
                "parent_class",
            )
            .subquery(
                ActivityInstanceClassRoot.nodes.traverse(latest_version="has_version")
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
        )

    def find_all_versions(
        self,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
    ) -> tuple[list[ActivityInstanceClass], int]:
        validate_page_number_and_page_size(page_number=page_number, page_size=page_size)
        skip = (page_number - 1) * page_size
        sort_order = "DESC" if sort_by and sort_by.get("start_date") is False else "ASC"

        query = f"""
            MATCH (lib:Library)-[:CONTAINS]->(root:ActivityInstanceClassRoot)-[ver:HAS_VERSION]->(val:ActivityInstanceClassValue)
            OPTIONAL MATCH (author:User)
            WHERE author.user_id = ver.author_id
            WITH root, val, ver, lib, author
            ORDER BY ver.start_date {sort_order}
            SKIP $skip LIMIT $limit
            RETURN
                root.uid AS uid,
                val.name AS name,
                val.order AS order_val,
                val.definition AS definition,
                val.is_domain_specific AS is_domain_specific,
                val.level AS level,
                val.nci_concept_id AS nci_concept_id,
                val.nci_concept_name AS nci_concept_name,
                lib.name AS library_name,
                ver.start_date AS start_date,
                ver.end_date AS end_date,
                ver.status AS status,
                ver.version AS version,
                ver.change_description AS change_description,
                COALESCE(author.username, ver.author_id) AS author_username
        """

        count_query = """
            MATCH (root:ActivityInstanceClassRoot)-[ver:HAS_VERSION]->(val:ActivityInstanceClassValue)
            RETURN count(*) AS total
        """

        results, meta = db.cypher_query(query, {"skip": skip, "limit": page_size})

        items = [
            ActivityInstanceClass.from_cypher_row(dict(zip(meta, row)))
            for row in results
        ]

        total = 0
        if total_count:
            count_result, _ = db.cypher_query(count_query)
            total = count_result[0][0] if count_result else 0

        return items, total

    def extend_distinct_headers_query(
        self,
        nodeset: NodeSet,
        field_name: str,
        filter_by: dict[str, dict[str, Any]] | None = None,
    ) -> NodeSet:
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

    def _has_data_changed(
        self, ar: ActivityInstanceClassAR, value: ActivityInstanceClassValue
    ) -> bool:
        if dataset_class := value.has_latest_value.get_or_none():
            dataset_class = dataset_class.maps_dataset_class.get_or_none()

        return (
            ar.activity_instance_class_vo.name != value.name
            or ar.activity_instance_class_vo.order != value.order
            or ar.activity_instance_class_vo.definition != value.definition
            or ar.activity_instance_class_vo.is_domain_specific
            != value.is_domain_specific
            or ar.activity_instance_class_vo.level != value.level
            or ar.activity_instance_class_vo.nci_concept_id != value.nci_concept_id
            or ar.activity_instance_class_vo.nci_concept_name != value.nci_concept_name
            or (
                ar.activity_instance_class_vo.dataset_class_uid != dataset_class.uid
                if dataset_class
                else None
            )
        )

    def _get_or_create_value(
        self,
        root: ActivityInstanceClassRoot,
        ar: ActivityInstanceClassAR,
        force_new_value_node: bool = False,
    ) -> ActivityInstanceClassValue:
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

        new_value = ActivityInstanceClassValue(
            name=ar.activity_instance_class_vo.name,
            order=ar.activity_instance_class_vo.order,
            definition=ar.activity_instance_class_vo.definition,
            is_domain_specific=ar.activity_instance_class_vo.is_domain_specific,
            level=ar.activity_instance_class_vo.level,
            nci_concept_id=ar.activity_instance_class_vo.nci_concept_id,
            nci_concept_name=ar.activity_instance_class_vo.nci_concept_name,
        )

        self._db_save_node(new_value)

        if ar.activity_instance_class_vo.dataset_class_uid:
            dataset = DatasetClass.nodes.get_or_none(
                uid=ar.activity_instance_class_vo.dataset_class_uid
            )
            root.maps_dataset_class.connect(dataset)

        return new_value

    def generate_uid(self) -> str:
        return ActivityInstanceClassRoot.get_next_free_uid_and_increment_counter()

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: ActivityInstanceClassRoot,
        library: Library,
        relationship: VersionRelationship,
        value: ActivityInstanceClassValue,
        **_kwargs,
    ) -> ActivityInstanceClassAR:
        dataset_class = root.maps_dataset_class.get_or_none()
        activity_item_classes = root.has_activity_item_class.all()

        return ActivityInstanceClassAR.from_repository_values(
            uid=root.uid,
            activity_instance_class_vo=ActivityInstanceClassVO.from_repository_values(
                name=value.name,
                order=value.order,
                definition=value.definition,
                is_domain_specific=value.is_domain_specific,
                level=value.level,
                nci_concept_id=value.nci_concept_id,
                nci_concept_name=value.nci_concept_name,
                dataset_class_uid=dataset_class.uid if dataset_class else None,
                activity_item_classes=[
                    ActivityInstanceClassActivityItemClassRelVO(
                        uid=activity_item_class.uid,
                        mandatory=activity_item_class.has_activity_instance_class.relationship(
                            root
                        ).mandatory,
                        is_adam_param_specific_enabled=activity_item_class.has_activity_instance_class.relationship(
                            root
                        ).is_adam_param_specific_enabled,
                        is_additional_optional=activity_item_class.has_activity_instance_class.relationship(
                            root
                        ).is_additional_optional,
                        is_default_linked=activity_item_class.has_activity_instance_class.relationship(
                            root
                        ).is_default_linked,
                    )
                    for activity_item_class in activity_item_classes
                ],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def patch_mappings(self, uid: str, dataset_class_uid: str) -> None:
        root = ActivityInstanceClassRoot.nodes.get(uid=uid)
        root.maps_dataset_class.disconnect_all()
        dataset_class = DatasetClass.nodes.get(uid=dataset_class_uid)
        root.maps_dataset_class.connect(dataset_class)

    def get_mapped_datasets(
        self,
        activity_instance_class_uid: str | None = None,
        ig_uid: str | None = None,
        include_sponsor: bool = True,
    ) -> list[ActivityInstanceClassWithDataset]:
        dataset_label = (
            "DatasetInstance|SponsorModelDatasetInstance"
            if include_sponsor
            else "DatasetInstance"
        )
        model_value_label = (
            "DataModelIGValue|SponsorModelValue"
            if include_sponsor
            else "DataModelIGValue"
        )
        query = "MATCH (aicv:ActivityInstanceClassValue)<-[:LATEST]-(aicr:ActivityInstanceClassRoot) "
        if activity_instance_class_uid:
            query += "WHERE aicr.uid=$activity_instance_class_uid"
        query += f"""
            OPTIONAL MATCH (aicr)-[:MAPS_DATASET_CLASS]->(:DatasetClass)-[:HAS_INSTANCE]->(:DatasetClassInstance)<-[:IMPLEMENTS_DATASET_CLASS]-(di:{dataset_label})<-[:HAS_INSTANCE]-(d:Dataset)
        """
        if ig_uid:
            query += f"""
                WHERE EXISTS ((di)<-[:HAS_DATASET]-(:{model_value_label})<-[:HAS_VERSION]-(:DataModelIGRoot {{uid: $ig_uid}}))
            """
        query += f"""
            OPTIONAL MATCH (aicr)-[:PARENT_CLASS]->{{1,3}}()-[:MAPS_DATASET_CLASS]->(:DatasetClass)
            -[:HAS_INSTANCE]->(:DatasetClassInstance)<-[:IMPLEMENTS_DATASET_CLASS]-(parent_di:{dataset_label})<-[:HAS_INSTANCE]-(parent_d:Dataset)
        """
        if ig_uid:
            query += f"""
                WHERE EXISTS ((parent_di)<-[:HAS_DATASET]-(:{model_value_label})<-[:HAS_VERSION]-(:DataModelIGRoot {{uid: $ig_uid}}))
            """
        query += """
            WITH DISTINCT aicr.uid AS uid, aicv.name AS name, d.uid AS dataset_uid, parent_d.uid AS parent_dataset_uid ORDER BY name, dataset_uid, parent_dataset_uid 
            WITH uid, name, apoc.coll.sort(apoc.coll.toSet(collect(dataset_uid) + collect(parent_dataset_uid))) AS dataset_uids WHERE size(dataset_uids) > 0
            RETURN uid, name, dataset_uids
        """

        results, meta = db.cypher_query(
            query,
            params={
                "activity_instance_class_uid": activity_instance_class_uid,
                "ig_uid": ig_uid,
            },
        )

        mapped_datasets = [dict(zip(meta, row)) for row in results]

        output = [
            ActivityInstanceClassWithDataset(
                uid=el["uid"], name=el["name"], datasets=el["dataset_uids"]
            )
            for el in mapped_datasets
        ]

        return output

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: ActivityInstanceClassRoot,
        value: ActivityInstanceClassValue,
    ) -> None:
        # This method from parent repo is not needed for this repo
        # So we use pass to skip implementation
        pass

    def update_parent(self, parent_uid: str | None, uid: str) -> None:
        root = ActivityInstanceClassRoot.nodes.get(uid=uid)
        root.parent_class.disconnect_all()

        if parent_uid:
            parent = ActivityInstanceClassRoot.nodes.get_or_none(uid=parent_uid)
            root.parent_class.connect(parent)

    def get_parent_class(self, uid: str) -> tuple[str, str] | None:
        root = ActivityInstanceClassRoot.nodes.get_or_none(uid=uid)
        if not root:
            return None

        parent_root = root.parent_class.get_or_none()
        if not parent_root:
            return None

        parent_value = parent_root.has_latest_value.get_or_none()

        return parent_root.uid, parent_value.name

    def get_child_instance_classes(
        self,
        parent_uid: str,
        version: str | None = None,
        page_number: int = 1,
        page_size: int = 10,
        total_count: bool = False,
        sort_by: dict[str, bool] | None = None,
        ignore_parent_version: bool = False,
    ) -> tuple[list[dict[str, Any]], int]:
        """Get paginated child activity instance classes for a parent class at a specific version

        Args:
            parent_uid: UID of the parent class
            version: Specific version to query, or None for parent's latest version
            page_number: Page number for pagination
            page_size: Number of items per page
            total_count: Whether to compute total count
            sort_by: Dictionary mapping field names to sort order (True=ascending, False=descending)
            ignore_parent_version: If True, returns latest version of all structural children regardless of parent version
                                  (used for checking if a class is structurally a parent)
        """
        # Build ORDER BY clause
        order_clause = "ORDER BY name"  # default
        if sort_by:
            fields = [
                f"{field} {'ASC' if ascending else 'DESC'}"
                for field, ascending in sort_by.items()
            ]
            order_clause = f"ORDER BY {', '.join(fields)}"

        if ignore_parent_version:
            # Structural check: get latest version of all children regardless of parent version
            query = """
                MATCH (parent:ActivityInstanceClassRoot {uid: $parent_uid})
                MATCH (child:ActivityInstanceClassRoot)-[:PARENT_CLASS]->(parent)
                MATCH (child)-[:LATEST]->(childValue:ActivityInstanceClassValue)
                OPTIONAL MATCH (child)-[ver:HAS_VERSION]->(childValue)
                WITH child, childValue, ver
                ORDER BY ver.start_date DESC
                WITH child, childValue, COLLECT(ver)[0] as latest_ver
                OPTIONAL MATCH (child)<-[:HAS_DATA_DOMAIN]-(lib:Library)
                WITH child.uid as uid,
                       childValue.name as name,
                       childValue.definition as definition,
                       childValue.is_domain_specific as is_domain_specific,
                       latest_ver.status as status,
                       latest_ver.version as version,
                       latest_ver.start_date as modified_date,
                       latest_ver.author_username as modified_by,
                       lib.name as library_name
            """
            query += f"\n                {order_clause}"
        else:
            # Temporal query: Get children that existed during/after the parent version's lifetime
            # If no version specified, use parent's LATEST version
            query = """
                // Get the parent at the specific version (or LATEST if not specified)
                MATCH (parent:ActivityInstanceClassRoot {uid: $parent_uid})
                MATCH (parent)-[pv:HAS_VERSION]->(parentValue:ActivityInstanceClassValue)
                WHERE ($version IS NOT NULL AND pv.version = $version)
                   OR ($version IS NULL AND EXISTS((parent)-[:LATEST]->(parentValue)))

                // Get all children that have a parent relationship
                MATCH (child:ActivityInstanceClassRoot)-[:PARENT_CLASS]->(parent)

                // For each child, get versions that existed during the parent version's lifetime
                MATCH (child)-[cv:HAS_VERSION]->(childValue:ActivityInstanceClassValue)
                WHERE cv.start_date >= pv.start_date
                  AND (pv.end_date IS NULL OR cv.start_date < pv.end_date)

                // Get the latest version of each child
                WITH child, childValue, cv
                ORDER BY
                    toInteger(split(cv.version, '.')[0]) DESC,
                    toInteger(split(cv.version, '.')[1]) DESC,
                    cv.start_date DESC
                WITH child, collect({value: childValue, ver: cv})[0] as childData

                OPTIONAL MATCH (child)<-[:HAS_DATA_DOMAIN]-(lib:Library)
                WITH child.uid as uid,
                       childData.value.name as name,
                       childData.value.definition as definition,
                       childData.value.is_domain_specific as is_domain_specific,
                       childData.ver.status as status,
                       childData.ver.version as version,
                       childData.ver.start_date as modified_date,
                       childData.ver.author_username as modified_by,
                       lib.name as library_name
            """
            query += f"\n                {order_clause}"

        # Get total count if requested
        if total_count:
            count_query = query + " RETURN COUNT(*) as total"
            count_params = {"parent_uid": parent_uid, "version": version}
            count_results, _ = db.cypher_query(count_query, params=count_params)
            total = count_results[0][0] if count_results else 0
        else:
            total = 0

        # Add pagination to main query
        if page_size > 0:
            query += "\n                SKIP $skip LIMIT $limit"

        # Build final query
        final_query = query + """
                RETURN uid, name, definition, is_domain_specific,
                       status, version, modified_date, modified_by, library_name
            """

        params: dict[str, Any] = {"parent_uid": parent_uid, "version": version}
        if page_size > 0:
            params["skip"] = (page_number - 1) * page_size
            params["limit"] = page_size

        results, meta = db.cypher_query(final_query, params=params)

        return [dict(zip(meta, row)) for row in results], total

    def get_activity_item_classes(
        self,
        activity_instance_class_uid: str,
        version: str | None = None,
        page_number: int = 1,
        page_size: int = 10,
        total_count: bool = False,
        sort_by: dict[str, bool] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Get paginated activity item classes for an activity instance class at a specific version"""

        # Build ORDER BY clause
        order_clause = "ORDER BY name"  # default
        if sort_by:
            fields = [
                f"{field} {'ASC' if ascending else 'DESC'}"
                for field, ascending in sort_by.items()
            ]
            order_clause = f"ORDER BY {', '.join(fields)}"

        # When no version specified, show current state with latest item versions
        if not version:
            # Query to get the latest versions of all connected items
            query = """
                // Get the activity instance class
                MATCH (aic:ActivityInstanceClassRoot {uid: $uid})

                // Get all item classes DIRECTLY connected to this activity instance class
                // or its direct parent (not items the parent inherits from its ancestors)
                OPTIONAL MATCH (aic)-[:HAS_ITEM_CLASS]->(directItem:ActivityItemClassRoot)
                OPTIONAL MATCH (aic)-[:PARENT_CLASS]->(directParent:ActivityInstanceClassRoot)
                OPTIONAL MATCH (directParent)-[:HAS_ITEM_CLASS]->(parentItem:ActivityItemClassRoot)
                WITH aic, COLLECT(DISTINCT directItem) + COLLECT(DISTINCT parentItem) as items
                UNWIND items as item

                // Get the LATEST version of each item (current state)
                MATCH (item)-[:LATEST]->(itemLatest:ActivityItemClassValue)
                MATCH (item)-[iv:HAS_VERSION]->(itemLatest)
                WHERE iv.end_date IS NULL

                // Get the direct parent UID and name for this item
                OPTIONAL MATCH (directParentItem:ActivityInstanceClassRoot)-[:HAS_ITEM_CLASS]->(item)
                WHERE directParentItem.uid <> $uid
                OPTIONAL MATCH (directParentItem)-[:LATEST]->(directParentValue:ActivityInstanceClassValue)
                WITH item, iv, itemLatest,
                     COLLECT(DISTINCT {parent_uid: directParentItem.uid, parent_name: directParentValue.name})[0] as parentInfo

                WITH item.uid as uid,
                       itemLatest.name as name,
                       parentInfo.parent_name as parent_name,
                       parentInfo.parent_uid as parent_uid,
                       itemLatest.definition as definition,
                       iv.status as status,
                       iv.version as version,
                       iv.start_date as modified_date,
                       iv.author_username as modified_by
            """
            query += f"\n                {order_clause}"
        else:
            # For specific version, show items as they were at that time
            query = """
                // First get the activity instance class at the specific version
                MATCH (aic:ActivityInstanceClassRoot {uid: $uid})
                MATCH (aic)-[av:HAS_VERSION {version: $version}]->(aicValue:ActivityInstanceClassValue)

                // Get all item classes DIRECTLY connected to this activity instance class
                // or its direct parent (not items the parent inherits from its ancestors)
                OPTIONAL MATCH (aic)-[:HAS_ITEM_CLASS]->(directItem:ActivityItemClassRoot)
                OPTIONAL MATCH (aic)-[:PARENT_CLASS]->(directParent:ActivityInstanceClassRoot)
                OPTIONAL MATCH (directParent)-[:HAS_ITEM_CLASS]->(parentItem:ActivityItemClassRoot)
                WITH aic, av, COLLECT(DISTINCT directItem) + COLLECT(DISTINCT parentItem) as items
                UNWIND items as item

                // Get all versions of each item
                MATCH (item)-[iv:HAS_VERSION]->(itemValue:ActivityItemClassValue)
                WITH aic, item, av, iv, itemValue
                ORDER BY iv.start_date ASC
                WITH aic, item, av, COLLECT({ver: iv, value: itemValue}) as allVersions

                // Find the appropriate version for this ActivityInstanceClass version
                WITH aic, item, av, allVersions,
                     CASE
                         // For current ActivityInstanceClass versions (no end date), show the latest item versions
                         WHEN av.end_date IS NULL THEN
                             // Get the latest version, preferring Final over Draft
                             CASE
                                 WHEN SIZE([v IN allVersions WHERE v.ver.end_date IS NULL]) > 0 THEN
                                     [v IN allVersions WHERE v.ver.end_date IS NULL][0]
                                 WHEN SIZE([v IN allVersions WHERE v.ver.status = 'Final']) > 0 THEN
                                     [v IN allVersions WHERE v.ver.status = 'Final' | v][-1]
                                 ELSE allVersions[-1]
                             END
                         // For historical versions, find what was valid at that time
                         WHEN SIZE([v IN allVersions WHERE v.ver.start_date <= av.start_date AND (v.ver.end_date IS NULL OR v.ver.end_date > av.start_date)]) > 0 THEN
                             [v IN allVersions WHERE v.ver.start_date <= av.start_date AND (v.ver.end_date IS NULL OR v.ver.end_date > av.start_date)][-1]
                         // If item was created after, find the version valid during the ActivityInstanceClass's lifetime
                         // Prefer Final versions that existed while this ActivityInstanceClass version was active
                         WHEN SIZE([v IN allVersions WHERE v.ver.start_date <= av.end_date AND v.ver.status = 'Final']) > 0 THEN
                             [v IN allVersions WHERE v.ver.start_date <= av.end_date AND v.ver.status = 'Final'][0]
                         // If no Final version during lifetime, get any version that overlapped
                         WHEN SIZE([v IN allVersions WHERE v.ver.start_date <= av.end_date]) > 0 THEN
                             [v IN allVersions WHERE v.ver.start_date <= av.end_date][0]
                         // Item was created after this version ended - don't show it
                         ELSE NULL
                     END as itemData
                WHERE itemData IS NOT NULL

                // Get the direct parent UID and name for this item
                // Show which ActivityInstanceClass directly owns this item (not the one we're querying from)
                OPTIONAL MATCH (directParent:ActivityInstanceClassRoot)-[:HAS_ITEM_CLASS]->(item)
                WHERE directParent.uid <> $uid
                OPTIONAL MATCH (directParent)-[:LATEST]->(directParentValue:ActivityInstanceClassValue)
                WITH item, itemData,
                     COLLECT(DISTINCT {parent_uid: directParent.uid, parent_name: directParentValue.name})[0] as parentInfo

                WITH item.uid as uid,
                       itemData.value.name as name,
                       parentInfo.parent_name as parent_name,
                       parentInfo.parent_uid as parent_uid,
                       itemData.value.definition as definition,
                       itemData.ver.status as status,
                       itemData.ver.version as version,
                       itemData.ver.start_date as modified_date,
                       itemData.ver.author_username as modified_by
            """
            query += f"\n                {order_clause}"

        # Get total count if requested
        if total_count:
            count_query = query + " RETURN COUNT(DISTINCT uid) as total"
            count_params = {"uid": activity_instance_class_uid}
            if version:
                count_params["version"] = version
            count_results, _ = db.cypher_query(count_query, params=count_params)
            total = count_results[0][0] if count_results else 0
        else:
            total = 0

        # Add pagination to main query
        if page_size > 0:
            query += "\n                SKIP $skip LIMIT $limit"

        # Build final query
        final_query = query + """
                RETURN DISTINCT uid, name, parent_name, parent_uid, definition,
                       status, version, modified_date, modified_by
            """

        params: dict[str, Any] = {"uid": activity_instance_class_uid}
        if version:
            params["version"] = version
        if page_size > 0:
            params["skip"] = (page_number - 1) * page_size
            params["limit"] = page_size

        results, meta = db.cypher_query(final_query, params=params)

        return [dict(zip(meta, row)) for row in results], total

    def get_all_version_numbers(self, uid: str) -> list[str]:
        """Get all version numbers of a given activity instance class"""

        rs, _ = db.cypher_query(
            "MATCH (:ActivityInstanceClassRoot {uid: $uid})-[hv:HAS_VERSION]-(:ActivityInstanceClassValue) RETURN DISTINCT hv.version",
            params={"uid": uid},
        )

        return [row[0] for row in rs]
