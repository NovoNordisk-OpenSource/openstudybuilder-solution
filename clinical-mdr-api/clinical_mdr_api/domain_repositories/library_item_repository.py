import abc
import copy
from datetime import datetime
from threading import Lock
from typing import Any, Iterable, Mapping, TypeVar

import neo4j
from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from neomodel import (
    OUTGOING,
    NodeClassNotDefined,
    RelationshipDefinition,
    RelationshipManager,
    Traversal,
    db,
)
from neomodel.exceptions import DoesNotExist

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    GenericRepository,
)
from clinical_mdr_api.domain_repositories.generic_repository import RepositoryImpl
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    ControlledTerminology,
    CTTermNameRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains.syntax_templates.template import InstantiationCountsVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
)
from clinical_mdr_api.repositories._utils import (
    ComparisonOperator,
    FilterOperator,
    sb_clear_cache,
)
from clinical_mdr_api.services.user_info import UserInfoService
from clinical_mdr_api.utils import convert_to_plain, validate_dict
from common import config
from common.exceptions import (
    BusinessLogicException,
    NotFoundException,
    ValidationException,
)
from common.utils import convert_to_datetime, validate_max_skip_clause

_AggregateRootType = TypeVar("_AggregateRootType", bound=LibraryItemAggregateRootBase)
RETRIEVED_READ_ONLY_MARK = object()
MATCH_NODE_BY_ID = "MATCH (node) WHERE elementId(node)=$id RETURN node"


class LibraryItemRepositoryImplBase(
    RepositoryImpl, GenericRepository[_AggregateRootType], abc.ABC
):
    cache_store_item_by_uid = TTLCache(
        maxsize=config.CACHE_MAX_SIZE, ttl=config.CACHE_TTL
    )
    lock_store_item_by_uid = Lock()
    has_library = True

    @abc.abstractmethod
    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        study_count: int = 0,
        counts: InstantiationCountsVO | None = None,
    ) -> _AggregateRootType:
        raise NotImplementedError

    @abc.abstractmethod
    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: VersionRoot,
        value: VersionValue,
    ) -> None:
        raise NotImplementedError

    value_class: type
    root_class: type

    def exists_by(self, property_name: str, value: str, on_root: bool = False) -> bool:
        """
        Checks whether a node exists in the graph database by a given property name and its value.

        Args:
            property_name (str): The name of the property to match.
            value (str): The value of the property to match.
            on_root (bool, optional): A flag indicating whether to search on the root node. Defaults to False.

        Returns:
            bool: True if a node is found by the given property name and value. False otherwise.
        """
        if not on_root:
            query = f"""
                MATCH (or:{self.root_class.__label__})-[:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED|LATEST]->(:{self.value_class.__label__} {{{property_name}: ${property_name}}})
                RETURN or
                """
        else:
            query = f"""
                MATCH (or:{self.root_class.__label__} {{{property_name}: ${property_name}}})-[:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED|LATEST]->(:{self.value_class.__label__})
                RETURN or
                """

        result, _ = db.cypher_query(query, {property_name: value})
        return len(result) > 0 and len(result[0]) > 0

    def get_uid_by_property_value(self, property_name: str, value: str) -> str | None:
        query = f"""
            MATCH (or:{self.root_class.__label__})-[:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED|LATEST]->(:{self.value_class.__label__} {{{property_name}: ${property_name}}})
            RETURN or
            """
        result, _ = db.cypher_query(query, {property_name: value})
        if len(result) > 0 and len(result[0]) > 0:
            return result[0][0].get("uid")
        return None

    def check_exists_by_name(self, name: str) -> bool:
        return self.exists_by("name", name)

    def find_uid_by_name(self, name: str) -> str | None:
        cypher_query = f"""
            MATCH (or:{self.root_class.__label__})-[:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED]->(ov:{self.value_class.__label__} {{name: $name }})
            RETURN or.uid
        """
        items, _ = db.cypher_query(cypher_query, {"name": name})
        if len(items) > 0:
            return items[0][0]
        return None

    def get_property_by_uid(self, uid: str, prop: str) -> str | None:
        cypher_query = f"""
            MATCH (or:{self.root_class.__label__} {{uid: $uid }})-[:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED]->(ov:{self.value_class.__label__})
            RETURN ov.{prop}
        """
        items, _ = db.cypher_query(cypher_query, {"uid": uid})
        if len(items) > 0:
            return items[0][0]
        return None

    def _is_repository_related_to_ct(self) -> bool:
        return False

    def _lock_object(self, uid: str) -> None:
        if not self._is_repository_related_to_ct():
            itm = self.root_class.nodes.get_or_none(uid=uid)
        else:
            result, _ = db.cypher_query(
                MATCH_NODE_BY_ID,
                {"id": uid},
                resolve_objects=True,
            )
            itm = result[0][0]
        if itm is not None:
            itm.__WRITE_LOCK__ = None
            itm.save()

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _get_or_create_value(
        self, root: VersionRoot, ar: _AggregateRootType
    ) -> VersionValue:
        (
            has_version_rel,
            _,
            latest_draft_rel,
            latest_final_rel,
            latest_retired_rel,
        ) = self._get_version_relation_keys(root)
        for itm in has_version_rel.filter(name=ar.name):
            return itm

        latest_draft = latest_draft_rel.get_or_none()
        if latest_draft and not self._has_data_changed(ar, latest_draft):
            return latest_draft
        latest_final = latest_final_rel.get_or_none()
        if latest_final and not self._has_data_changed(ar, latest_final):
            return latest_final
        latest_retired = latest_retired_rel.get_or_none()
        if latest_retired and not self._has_data_changed(ar, latest_retired):
            return latest_retired

        additional_props = {}

        if hasattr(ar, "name_plain"):
            additional_props["name_plain"] = convert_to_plain(ar.name)

        new_value = self.value_class(name=ar.name, **additional_props)
        self._db_save_node(new_value)
        return new_value

    def _has_data_changed(self, ar: _AggregateRootType, value: VersionValue) -> bool:
        base_comparison = ar.name != value.name
        return base_comparison

    def _is_new_version_necessary(
        self, ar: _AggregateRootType, value: VersionValue
    ) -> bool:
        return self._has_data_changed(ar, value)

    def _update(self, versioned_object: _AggregateRootType):
        """
        Updates the state of the versioned object in the graph.

        First, the properties on the root/value nodes must be updated
        and new value object created if necessary.

        Then, that the version information has changed, new HAS_VERSION
        relationships must be created.
        Additionally, the pointer relationships
        (LATEST_DRAFT, LATEST_FINAL, LATEST) must be removed and added again.
        """
        (
            root,
            value,
            library,
            previous_versioned_object,
        ) = versioned_object.repository_closure_data
        versioning_data = self._library_item_metadata_vo_to_datadict(
            versioned_object.item_metadata
        )

        # condition added because ControlledTerminology items are versioned slightly different than other library items:
        # we have two root nodes - the 'main' root called for instance CTCodelistRoot that contains uid
        # and also contains relationships to nodes called CTCodelistAttributesRoot or CTCodelistNameRoot
        # these two nodes don't contain uids but serves as a roots for versioned relationships
        # Connection to the Library node is attached to the 'main' root not the root that owns versioned relationships
        # this is why we need the following condition
        if self._is_repository_related_to_ct():
            root = root.has_root.single()

        if (
            self.has_library
            and versioned_object.library.name != root.has_library.get().name
        ):
            self._db_remove_relationship(root.has_library)
            try:
                new_library = self._get_library(versioned_object.library.name)
                BusinessLogicException.raise_if_not(
                    library.is_editable,
                    msg=f"Library with Name '{new_library.name}' doesn't allow creation of objects.",
                )
            except DoesNotExist as exc:
                raise NotFoundException(
                    "Library", versioned_object.library.name, "Name"
                ) from exc
            self._db_create_relationship(root.has_library, library)

        # going back from different treatment of ControlledTerminology items
        if self._is_repository_related_to_ct():
            root, _, _, _ = versioned_object.repository_closure_data

        (
            _,
            has_latest_value_rel,
            latest_draft_rel,
            latest_final_rel,
            latest_retired_rel,
        ) = self._get_version_relation_keys(root)
        is_data_changed = False
        changes_possible = self._are_changes_possible(
            versioned_object, previous_versioned_object
        )
        new_version_needed = self._is_new_version_necessary(versioned_object, value)
        if changes_possible and new_version_needed:
            # Creating nev value object if necessary
            new_value = self._get_or_create_value(root, versioned_object)

            # recreating latest_value relationship
            self._db_remove_relationship(has_latest_value_rel)
            self._db_create_relationship(has_latest_value_rel, new_value)
            is_data_changed = True
        else:
            new_value = value

        # we update relationships when the data is changed or the versioning data is changed
        if (
            is_data_changed
            or previous_versioned_object.item_metadata != versioned_object.item_metadata
        ):
            # Updating latest_draft, latest_final or latest_retired relationship if necessary
            if versioned_object.item_metadata.status == LibraryItemStatus.DRAFT:
                self._recreate_relationship(
                    root, latest_draft_rel, new_value, versioning_data
                )

            elif versioned_object.item_metadata.status == LibraryItemStatus.FINAL:
                self._recreate_relationship(
                    root, latest_final_rel, new_value, versioning_data
                )

            elif versioned_object.item_metadata.status == LibraryItemStatus.RETIRED:
                self._recreate_relationship(
                    root, latest_retired_rel, new_value, versioning_data
                )

            # close all previous HAS_VERSIONs
            self._close_previous_versions(root, versioning_data)

        # recreating parameters connections
        self._maintain_parameters(versioned_object, root, new_value)

        return versioned_object

    def _are_changes_possible(
        self,
        versioned_object: _AggregateRootType,
        previous_versioned_object: _AggregateRootType,
    ) -> bool:
        new_status = versioned_object.item_metadata.status
        prev_status = previous_versioned_object.item_metadata.status
        return (
            prev_status == LibraryItemStatus.DRAFT
            and new_status == LibraryItemStatus.DRAFT
        )

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _recreate_relationship(
        self,
        root: VersionRoot,
        relation: VersionRelationship,
        value: VersionValue,
        parameters: Mapping[str, Any],
    ):
        old_value = relation.get_or_none()
        (
            has_version_rel,
            _,
            _,
            _,
            _,
        ) = self._get_version_relation_keys(root)

        if old_value is not None:
            self._db_remove_relationship(relation)
        all_hvs = has_version_rel.all_relationships(value)
        # Set any missing end_date to the new start_date
        for has_version in all_hvs:
            if has_version.end_date is None:
                has_version.end_date = parameters["start_date"]
                has_version.save()
        has_version_rel.connect(value, parameters)
        self._db_create_relationship(relation, value)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _close_previous_versions(
        self,
        root: VersionRoot,
        parameters: Mapping[str, Any],
    ):
        (
            has_version_rel,
            _,
            _,
            _,
            _,
        ) = self._get_version_relation_keys(root)
        all_values = has_version_rel.all()
        for value in all_values:
            all_rels = has_version_rel.all_relationships(value)
            # Set any missing end_date to the new start_date, for all except the new version
            for rel in all_rels:
                if rel.version != parameters["version"] and rel.end_date is None:
                    rel.end_date = parameters["start_date"]
                    rel.save()

    def _get_library(self, library_name: str) -> Library:
        # Finds library in database based on library name
        return Library.nodes.get(name=library_name)

    def retrieve_audit_trail(
        self, page_number: int = 1, page_size: int = 0, total_count: bool = False
    ) -> tuple[list[_AggregateRootType], int]:
        """
        Retrieves an audit trail of the given node type from the database.

        This method queries the database for the given node type, ordered by their start date in descending order.
        It retrieves a subset of the entries based on the provided page number and page size parameters.
        Optionally, it can also return the total count of audit trail entries.

        Args:
            page_number (int, optional): The page number of the results to retrieve. Each page contains a subset of the audit trail. Defaults to 1.
            page_size (int, optional): The number of results per page. If set to 0, all results will be retrieved. Defaults to 0.
            total_count (bool, optional): Flag indicating whether to include the total count of audit trail entries. Defaults to False.

        Returns:
            tuple[list[_AggregateRootType], int]: A tuple containing a list of retrieved audit trail entries and the total count of entries.
                The audit trail entries are instances of the _AggregateRootType class.
        """
        validate_max_skip_clause(page_number=page_number, page_size=page_size)

        query = f"""
            MATCH (root:{self.root_class.__name__})-[rel:HAS_VERSION]->(value:{self.value_class.__name__})
            RETURN root, rel, value
            ORDER BY rel.start_date DESC
        """

        if page_size:
            query += "SKIP $page_number * $page_size LIMIT $page_size"

        result = db.cypher_query(
            query,
            params={
                "page_number": page_number - 1,
                "page_size": page_size,
            },
            resolve_objects=True,
        )

        aggregates = []

        for root, relationship, value in result[0]:
            ar = self._create_aggregate_root_instance_from_version_root_relationship_and_value(
                root=root,
                library=root.has_library.get_or_none(),
                relationship=relationship,
                value=value,
            )
            ar.repository_closure_data = RETRIEVED_READ_ONLY_MARK
            aggregates.append(ar)

        if total_count:
            count = db.cypher_query(
                f"MATCH (:{self.root_class.__name__})-[rel:HAS_VERSION]->(:{self.value_class.__name__}) RETURN COUNT(rel) as total_count"
            )[0][0][0]
        else:
            count = 0

        return aggregates, count

    def find_all(
        self,
        *,
        status: LibraryItemStatus | None = None,
        library_name: str | None = None,
        return_study_count: bool | None = False,
    ) -> Iterable[_AggregateRootType]:
        """
        GetAll implementation - gets all objects. Ignores versions.
        """
        aggregates = []
        items = []
        if status is None:
            items = self.root_class.nodes.order_by("-uid")
        elif status == LibraryItemStatus.FINAL:
            items = self.root_class.nodes.has(latest_final=True)
        elif status == LibraryItemStatus.DRAFT:
            items = self.root_class.nodes.has(latest_draft=True)
        elif status == LibraryItemStatus.RETIRED:
            items = self.root_class.nodes.has(latest_retired=True)

        for item in items:
            root: VersionRoot = item
            library: Library = root.has_library.get_or_none()
            (
                _,
                has_latest_value_rel,
                latest_draft_rel,
                latest_final_rel,
                latest_retired_rel,
            ) = self._get_version_relation_keys(root)

            if library and library_name is not None and library_name != library.name:
                continue

            if status is None:
                value: VersionValue = has_latest_value_rel.single()
            elif status == LibraryItemStatus.FINAL:
                value: VersionValue = latest_final_rel.single()
            elif status == LibraryItemStatus.DRAFT:
                value: VersionValue = latest_draft_rel.single()
            elif status == LibraryItemStatus.RETIRED:
                value: VersionValue = latest_retired_rel.single()

            relationship: VersionRelationship = self._get_latest_version(root, value)

            ar = self._create_aggregate_root_instance_based_on_return_counts(
                library=library,
                root=root,
                value=value,
                relationship=relationship,
                return_instantiation_counts=False,
                return_study_count=return_study_count,
            )

            ar.repository_closure_data = RETRIEVED_READ_ONLY_MARK
            aggregates.append(ar)
        return aggregates

    def _get_study_count(self, item: VersionValue) -> int:
        return item.get_study_count()

    def _get_latest_version_for_status(
        self, root: VersionRoot, value: VersionValue, status: LibraryItemStatus
    ) -> VersionRelationship:
        (
            has_version_rel,
            _,
            _,
            _,
            _,
        ) = self._get_version_relation_keys(root)

        all_rels = has_version_rel.all_relationships(value)
        rels = [rel for rel in all_rels if rel.status == status.value]
        if len(rels) == 0:
            raise RuntimeError(f"No HAS_VERSION was found with status {status}")
        if len(rels) == 1:
            return rels[0]
        all_versions = [rel.version for rel in rels]
        highest_version = max(
            all_versions,
            key=lambda v: 1000000 * int(v.split(".")[0]) + int(v.split(".")[1]),
        )
        all_latest = [rel for rel in all_rels if rel.version == highest_version]
        return self._find_latest_version_in(all_latest)

    def _get_latest_version(
        self,
        root: VersionRoot,
        value: VersionValue,
        status: LibraryItemStatus | None = None,
    ) -> VersionRelationship:
        (
            has_version_rel,
            _,
            _,
            _,
            _,
        ) = self._get_version_relation_keys(root)
        if status is None:
            all_rels = has_version_rel.all_relationships(value)
            if len(all_rels) == 0:
                raise RuntimeError("No HAS_VERSION relationship was found")
            highest_version = self._get_max_version(all_rels)
            all_latest = [rel for rel in all_rels if rel.version == highest_version]
            return self._find_latest_version_in(all_latest)
        return self._get_latest_version_for_status(root, value, status)

    def _get_max_version(self, relationships):
        all_versions = [rel.version for rel in relationships]
        highest_version = max(
            all_versions,
            key=lambda v: 1000000 * int(v.split(".")[0]) + int(v.split(".")[1]),
        )
        return highest_version

    def _find_latest_version_in(self, relationships):
        if len(relationships) == 1:
            return relationships[0]
        all_without_end = [rel for rel in relationships if rel.end_date is None]
        if len(all_without_end) == 1:
            return all_without_end[0]
        if len(all_without_end) > 1:
            return max(all_without_end, key=lambda d: d.start_date)
        return max(relationships, key=lambda d: d.end_date)

    def _get_item_versions(
        self,
        root: VersionRoot,
    ) -> tuple[
        list[tuple[Mapping, VersionValue, VersionRelationship]],
        VersionRelationship | None,
        VersionRelationship | None,
    ]:
        """
        Following code recreates full versioning information based on
        HAS_VERSION relation. First finds all VersionValue-s related to
        specific root, then recreates data dictionaries based on
        relationships between particular nodes (there is more then one
        relation HAS_VERSION) possible between
        single root and value objects)
        """
        (
            has_version_rel,
            _,
            latest_draft_rel,
            latest_final_rel,
            _,
        ) = self._get_version_relation_keys(root)
        latest_final = None
        latest_draft = None
        latest_draft_object: VersionValue | None = latest_draft_rel.single()
        if latest_draft_object is not None:
            latest_draft = latest_draft_rel.relationship(latest_draft_object)

        latest_final_object: VersionValue | None = latest_final_rel.single()
        if latest_final_object is not None:
            latest_final = latest_final_rel.relationship(latest_final_object)

        managed: list[VersionValue] = []
        versions: list[tuple[Mapping, VersionValue, VersionRelationship]] = []
        traversal = Traversal(
            root,
            root.__label__,
            {
                "node_class": self.value_class,
                "direction": OUTGOING,
                "model": VersionRelationship,
            },
        )
        itm: VersionValue
        for itm in traversal.all():
            assert isinstance(
                itm, (VersionValue, ControlledTerminology)
            )  # PIWQ: juts to check whether I understand what's going here
            if itm in managed:
                continue

            managed.append(itm)
            rels: Iterable[VersionRelationship] = has_version_rel.all_relationships(itm)

            for rel in rels:
                assert isinstance(
                    rel, VersionRelationship
                )  # PIWQ: again to check whether I understand
                version_data = self._get_version_data_from_db(root, itm, rel)
                versions.append(version_data)

        versions.sort(key=lambda x: x[2].start_date, reverse=True)
        return versions, latest_draft, latest_final

    def get_all_versions_2(
        self, uid: str, return_study_count: bool | None = False
    ) -> Iterable[_AggregateRootType]:
        library: Library | None = None
        # condition added because ControlledTerminology items are versioned slightly different than other library items:
        # we have two root nodes - the 'main' root called for instance CTCodelistRoot that contains uid
        # and also contains relationships to nodes called CTCodelistAttributesRoot or CTCodelistNameRoot
        # these two nodes don't contain uids but serves as a roots for versioned relationships
        # Connection to the Library node is attached to the 'main' root not the root that owns versioned relationships
        # this is why we need the following condition
        if not self._is_repository_related_to_ct():
            root: VersionRoot | None = self.root_class.nodes.get_or_none(uid=uid)
            if root is not None:
                if self.has_library:
                    library: Library = root.has_library.get()
                else:
                    library = None
        else:
            # ControlledTerminology version root items don't contain uid - then we have to get object by it's id
            result, _ = db.cypher_query(
                MATCH_NODE_BY_ID,
                {"id": uid},
                resolve_objects=True,
            )
            root = result[0][0]
            if root is not None:
                if self.has_library:
                    library: Library = root.has_root.single().has_library.get()
                else:
                    library = None

        result: list[_AggregateRootType] = []
        if root is not None:
            if self.has_library:
                assert library is not None
            else:
                assert library is None
            all_version_nodes_and_relationships: list[
                tuple[VersionValue, VersionRelationship]
            ]
            all_version_nodes_and_relationships = [
                (_[1], _[2]) for _ in self._get_item_versions(root)[0]
            ]
            if return_study_count:
                result = [
                    self._create_aggregate_root_instance_from_version_root_relationship_and_value(
                        root=root,
                        value=_[0],
                        relationship=_[1],
                        library=library,
                        study_count=self._get_study_count(_[0]),
                    )
                    for _ in all_version_nodes_and_relationships
                ]
            else:
                result = [
                    self._create_aggregate_root_instance_from_version_root_relationship_and_value(
                        root=root, value=_[0], relationship=_[1], library=library
                    )
                    for _ in all_version_nodes_and_relationships
                ]
            for _ in result:
                _.repository_closure_data = RETRIEVED_READ_ONLY_MARK
        return result

    def hashkey_library_item(
        self,
        uid: str,
        *,
        version: str | None = None,
        status: LibraryItemStatus | None = None,
        at_specific_date: datetime | None = None,
        for_update: bool = False,
        return_study_count: bool | None = False,
        return_instantiation_counts: bool = False,
    ):
        """
        Returns a hash key that will be used for mapping objects stored in cache,
        which ultimately determines whether a method invocation is a hit or miss.

        We need to define this custom hashing function with the same signature as the method we wish to cache (find_by_uid_2),
        since the target method contains optional/default parameters.
        If this custom hashkey function is not defined, most invocations of find_by_uid_2 method will be misses.
        """
        return hashkey(
            str(type(self)),
            uid,
            version,
            status,
            at_specific_date,
            for_update,
            return_study_count,
            return_instantiation_counts,
        )

    def _create_aggregate_root_instance_based_on_return_counts(
        self,
        library: Library,
        root: VersionRoot,
        value: VersionValue,
        relationship: VersionRelationship,
        return_instantiation_counts: bool,
        return_study_count: bool,
    ) -> _AggregateRootType:
        if return_instantiation_counts:
            final, draft, retired = self._get_counts(root)
            counts = InstantiationCountsVO.from_counts(
                final=final, draft=draft, retired=retired
            )
        else:
            counts = None

        if return_study_count:
            study_count = self._get_study_count(value)
        else:
            study_count = 0

        return self._create_aggregate_root_instance_from_version_root_relationship_and_value(
            root=root,
            library=library,
            relationship=relationship,
            value=value,
            counts=counts,
            study_count=study_count,
        )

    def _get_version_active_at_date_time(
        self,
        has_version_rel: RelationshipDefinition,
        at_specific_date: datetime,
        status=None,
    ) -> tuple[VersionValue | None, VersionRelationship | None]:
        if status:
            matching_values: list[VersionValue] = has_version_rel.match(
                start_date__lte=at_specific_date, status__exact=status.value
            )
        else:
            matching_values: list[VersionValue] = has_version_rel.match(
                start_date__lte=at_specific_date,
            )
        latest_matching_relationship: VersionRelationship | None = None
        latest_matching_value: VersionValue | None = None
        for matching_value in matching_values:
            relationships: list[VersionRelationship] = (
                has_version_rel.all_relationships(matching_value)
            )
            for relationship in relationships:
                if status:
                    if (
                        latest_matching_relationship is None
                        or latest_matching_relationship.start_date
                        < relationship.start_date
                    ) and relationship.status == status.value:
                        latest_matching_relationship = relationship
                        latest_matching_value = matching_value
                else:
                    if (
                        latest_matching_relationship is None
                        or latest_matching_relationship.start_date
                        < relationship.start_date
                    ):
                        latest_matching_relationship = relationship
                        latest_matching_value = matching_value
        return latest_matching_value, latest_matching_relationship

    @cached(
        cache=cache_store_item_by_uid,
        key=hashkey_library_item,
        lock=lock_store_item_by_uid,
    )
    def find_by_uid_2(
        self,
        uid: str,
        *,
        version: str | None = None,
        status: LibraryItemStatus | None = None,
        at_specific_date: datetime | None = None,
        for_update: bool = False,
        return_study_count: bool | None = False,
        return_instantiation_counts: bool = False,
    ) -> _AggregateRootType | None:
        if for_update and (
            version is not None or status is not None or at_specific_date is not None
        ):
            raise NotImplementedError(
                "Retrieval for update supported only for latest version."
            )

        if for_update:
            self._lock_object(uid)

        root, library = self._get_root_and_library(uid)
        if not root:
            return None

        value: VersionValue | None
        relationship: VersionRelationship | None

        (
            has_version_rel,
            has_latest_value_rel,
            latest_draft_rel,
            latest_final_rel,
            latest_retired_rel,
        ) = self._get_version_relation_keys(root)

        result: _AggregateRootType | None = None

        if version is None:
            if status is None:
                if at_specific_date is None:
                    # Find the latest version (regardless of status)
                    value = has_latest_value_rel.single()
                    relationship = self._get_latest_version(root, value)
                else:
                    # Find the latest version (regardless of status) that exists at the specified date
                    value, relationship = self._get_version_active_at_date_time(
                        has_version_rel, at_specific_date
                    )
            else:
                if at_specific_date is None:
                    # Find the latest version with the specified status
                    value, relationship = self._get_latest_value_with_status(
                        root,
                        status,
                        has_version_rel,
                        latest_draft_rel,
                        latest_final_rel,
                        latest_retired_rel,
                    )
                else:
                    # Find the latest version (regardless of status) that exists at the specified date
                    value, relationship = self._get_version_active_at_date_time(
                        has_version_rel, at_specific_date, status=status
                    )
        else:
            # Find the version with the specified version number, and optionally status
            value, relationship = self._get_value_with_version_number(
                root, version, status
            )

        if value and relationship:
            result = self._create_aggregate_root_instance_based_on_return_counts(
                library=library,
                root=root,
                value=value,
                relationship=relationship,
                return_instantiation_counts=return_instantiation_counts,
                return_study_count=return_study_count,
            )
            if for_update:
                result.repository_closure_data = (
                    root,
                    value,
                    library,
                    copy.deepcopy(result),
                )
            else:
                result.repository_closure_data = RETRIEVED_READ_ONLY_MARK
        return result

    def _get_value_with_version_number(
        self, root: VersionRoot, version: str, status: LibraryItemStatus | None = None
    ) -> tuple[VersionValue | None, VersionRelationship | None]:
        matching_value = root.get_value_for_version(version)
        active_relationship: VersionRelationship | None = None
        active_value: VersionValue | None = None
        if matching_value is not None:
            active_relationship = root.get_relation_for_version(version)
            active_value = matching_value

        if active_relationship is None:
            return None, None

        if status is not None and active_relationship.status != status.value:
            return None, None

        return active_value, active_relationship

    def _get_latest_value_with_status(
        self,
        root: VersionRoot,
        status: LibraryItemStatus,
        has_version_rel: RelationshipManager,
        latest_draft_rel: RelationshipManager,
        latest_final_rel: RelationshipManager,
        latest_retired_rel: RelationshipManager,
    ) -> tuple[VersionValue | None, VersionRelationship | None]:
        relationship: VersionRelationship | None = None
        value: VersionValue | None = None

        relationship_manager_to_use: RelationshipManager = latest_retired_rel
        if status == LibraryItemStatus.FINAL:
            relationship_manager_to_use = latest_final_rel
        elif status == LibraryItemStatus.DRAFT:
            relationship_manager_to_use = latest_draft_rel
        value = relationship_manager_to_use.get_or_none()
        if value is None:
            value = has_version_rel.match(status=status.value).all()
            if not value:
                return None, None
            end_dates = {
                has_version_rel.relationship(node).end_date: node for node in value
            }
            last_date = max(end_dates.keys())
            value = end_dates[last_date]

        relationship = self._get_latest_version_for_status(root, value, status)
        return value, relationship

    def _get_root_and_library(
        self, uid: str
    ) -> tuple[VersionRoot | None, Library | None]:
        if not self._is_repository_related_to_ct():
            try:
                root: VersionRoot | None = self.root_class.nodes.get_or_none(uid=uid)
            except NodeClassNotDefined as exc:
                raise NotFoundException(
                    msg="Resource doesn't exist - it was likely deleted in a concurrent transaction."
                ) from exc
            if root is None:
                return None, None
            if self.has_library:
                library: Library = root.has_library.get()
            else:
                library = None
        else:
            result, _ = db.cypher_query(
                MATCH_NODE_BY_ID,
                {"id": uid},
                resolve_objects=True,
            )
            root = result[0][0]
            if root is None:
                return None, None
            ct_root = root.has_root.single()
            if self.has_library:
                library: Library = ct_root.has_library.get()
            else:
                library = None
        return root, library

    def _get_counts(self, item: VersionRoot) -> tuple[int, int, int]:
        finals: int
        drafts: int
        retired: int
        finals, drafts, retired = item.get_instantiations_count()
        return (finals, drafts, retired)

    def _get_version_data_from_db(
        self,
        item: VersionRoot | ControlledTerminology,
        value: VersionValue | ControlledTerminology,
        relation: VersionRelationship,
    ) -> tuple[Mapping, VersionValue, VersionRelationship]:
        if not self.has_library:
            library = None
        elif not self._is_repository_related_to_ct():
            library: Library = item.has_library.get()
        else:
            library: Library = item.has_root.single().has_library.get()
        data = value.to_dict()
        rdata = data.copy()
        rdata.update(relation.to_dict())
        if library is not None:
            rdata["library_name"] = library.name
            rdata["library_is_editable"] = library.is_editable

        return rdata, value, relation

    def _library_item_metadata_vo_to_datadict(
        self, item_metadata: LibraryItemMetadataVO
    ) -> Mapping[str, Any]:
        # if the repository knows who is logged in, domain information will be ignored
        return {
            "author_id": item_metadata.author_id,
            "author_username": UserInfoService.get_author_username_from_id(
                item_metadata.author_id
            ),
            "change_description": item_metadata.change_description,
            "version": item_metadata.version,
            "status": item_metadata.status.value,
            "start_date": item_metadata.start_date,
            "end_date": item_metadata.end_date,
        }

    def _create(self, item: _AggregateRootType) -> _AggregateRootType:
        """
        Creates new VersionedObject AR, checks possibility based on
        library setting, then creates database representation,
        creates TemplateParameters database objects, recreates AR based
        on created database model and returns created AR.
        Saving into database is necessary due to uid creation process that
        require saving object to database.
        """
        relation_data: LibraryItemMetadataVO = item.item_metadata
        root = self.root_class(uid=item.uid)

        self._db_save_node(root)

        value = self._get_or_create_value(root=root, ar=item)

        library = self._get_library(item.library.name)

        (
            root,
            value,
            _,
            _,
            _,
        ) = self._db_create_and_link_nodes(
            root, value, self._library_item_metadata_vo_to_datadict(relation_data)
        )

        # Connect root node to library node
        root.has_library.connect(library)

        self._maintain_parameters(item, root, value)

        return item

    @staticmethod
    def _library_item_metadata_vo_from_relation(
        relationship: VersionRelationship,
    ) -> LibraryItemMetadataVO:
        major, minor = relationship.version.split(".")
        return LibraryItemMetadataVO.from_repository_values(
            change_description=relationship.change_description,
            status=LibraryItemStatus(relationship.status),
            author_id=relationship.author_id,
            author_username=UserInfoService.get_author_username_from_id(
                relationship.author_id
            ),
            start_date=relationship.start_date,
            end_date=relationship.end_date,
            major_version=int(major),
            minor_version=int(minor),
        )

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def save(self, item: _AggregateRootType) -> None:
        if item.repository_closure_data is RETRIEVED_READ_ONLY_MARK:
            raise NotImplementedError(
                "Only instances which were retrieved for update can be saved by the repository."
            )
        if item.repository_closure_data is not None and not item.is_deleted:
            self._update(item)
        elif item.is_deleted:
            assert item.uid is not None
            self._soft_delete(item.uid)
        else:
            self._create(item)
        if item.repository_closure_data is not None:
            (
                root,
                _,
                library,
                _,
            ) = item.repository_closure_data
            value = root.has_latest_value.single()

            item.repository_closure_data = (
                root,
                value,
                library,
                copy.deepcopy(item),
            )

    def _soft_delete(self, uid: str) -> None:
        label = self.root_class.__label__
        db.cypher_query(
            f"""
            MATCH (otr:{label} {{uid: $uid}})-[latest_draft:LATEST_DRAFT]->(otv)
            WHERE NOT (otr)-[:LATEST_FINAL|HAS_VERSION {{version:'Final'}}]->()
            SET otr:Deleted{label}
            WITH otr
            REMOVE otr:{label}
            WITH otr
            MATCH (otr)-[v:HAS_VERSION]->()
            WHERE v.end_date IS NULL
            SET v.end_date = datetime(apoc.date.toISO8601(datetime().epochSeconds, 's'))
            """,
            {"uid": uid},
        )

    def check_exists_final_version(self, uid: str) -> bool:
        root_node = self.root_class.nodes.get_or_none(uid=uid)
        if root_node is not None:
            return root_node.latest_final.get_or_none() is not None
        return False

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass

    def _get_uid_or_none(self, node):
        return node.uid if node is not None else None

    def _create_ar(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        study_count: int = 0,
        **kwargs,
    ) -> _AggregateRootType:
        raise NotImplementedError

    def hashkey_library_item_with_metadata_find_by_uid(
        self,
        uid: str,
        for_update=False,
        *,
        library_name: str | None = None,
        status: LibraryItemStatus | None = None,
        version: str | None = None,
        return_study_count: bool | None = False,
        for_audit_trail: bool = False,
        at_specific_date: datetime | None = None,
    ):
        """
        Returns a hash key that will be used for mapping objects stored in cache,
        which ultimately determines whether a method invocation is a hit or miss.

        We need to define this custom hashing function with the same signature as the method we wish to cache (find_by_uid_optimized),
        since the target method contains optional/default parameters.
        If this custom hashkey function is not defined, most invocations of find_by_uid_optimized method will be misses.
        """
        return hashkey(
            self.make_hashable(type(self)),
            uid,
            for_update,
            library_name,
            status,
            version,
            return_study_count,
            for_audit_trail,
            at_specific_date,
        )

    @cached(
        cache=cache_store_item_by_uid,
        key=hashkey_library_item_with_metadata_find_by_uid,
        lock=lock_store_item_by_uid,
    )
    def find_by_uid_optimized(
        self,
        uid: str,
        *,
        for_update: bool = False,
        library_name: str | None = None,
        status: LibraryItemStatus | None = None,
        version: str | None = None,
        return_study_count: bool | None = False,
        for_audit_trail: bool = False,
        at_specific_date: datetime | None = None,
    ) -> _AggregateRootType | list[_AggregateRootType]:
        if for_update and (version is not None or status is not None):
            raise NotImplementedError(
                "Retrieval for update supported only for latest version."
            )

        if for_update:
            self._lock_object(uid)

        aggregates: list[_AggregateRootType] = []

        match_stmt, return_stmt = self._find_cypher_query_optimized(
            with_status=bool(status),
            with_version=bool(version),
            with_pagination=False,
            with_at_specific_date=bool(at_specific_date),
            return_study_count=return_study_count,
            uid=uid,
            for_audit_trail=for_audit_trail,
        )

        params = {"uid": uid}
        if status:
            params["status"] = status.value
        if version:
            params["version"] = version
        if at_specific_date:
            params["at_specific_date"] = at_specific_date

        cypher_query = match_stmt + return_stmt

        # If a CTTermName is requested at a specific date and we do not want to raise an exception if not found,
        # We retrieve both this version if available and the latest
        # Then we return the latest if there is no available version at the given date
        # This is for returning Terms in the context of a study with a StudyStandardVersion
        if issubclass(self.root_class, CTTermNameRoot) and at_specific_date is not None:
            latest_match_stmt, latest_return_stmt = self._find_cypher_query_optimized(
                get_latest_final=True,
                return_study_count=return_study_count,
                uid=uid,
                for_audit_trail=for_audit_trail,
            )
            cypher_query += (
                ", false AS is_latest_fallback "
                + " UNION ALL "
                + latest_match_stmt
                + latest_return_stmt
                + ", true AS is_latest_fallback"
            )

        try:
            result, _ = db.cypher_query(
                cypher_query,
                params=params,
                resolve_objects=True,
            )
        except NodeClassNotDefined as exc:
            raise NotFoundException(
                msg="Resource doesn't exist - it was likely deleted in a concurrent transaction."
            ) from exc

        if not result:
            NotFoundException.raise_if(
                issubclass(self.root_class, CTTermNameRoot),
                msg=f"No {self.root_class.__label__} with UID '{uid}' found in given status, date and version ; nor was a latest final one found.",
            )

            raise NotFoundException(
                msg=f"No {self.root_class.__label__} with UID '{uid}' found in given status, date and version.",
            )

        if issubclass(self.root_class, CTTermNameRoot):
            for i, _ in enumerate(result):
                result[i][5]["queried_effective_date"] = None
                result[i][5]["date_conflict"] = False
            if at_specific_date is not None:
                # Last entry in each result row is a boolean is_latest_fallback
                # indicating if the returned value is the requested one for date
                # or the default latest final one
                # Drop that last column once it has been used
                non_latest_results = [r[:-1] for r in result if r[-1] is False]
                if len(non_latest_results) > 0:
                    # Keep only non latest results if any
                    result = non_latest_results
                    result[0][5]["queried_effective_date"] = at_specific_date
                else:
                    # Keep only latest results if no results at date
                    # And raise date conflict flag
                    result = [r[:-1] for r in result if r[-1] is True]
                    result[0][5]["date_conflict"] = True

        for (
            library,
            root,
            relationship,
            value,
            study_count,
            ctterm_names,
            activity_instance_root,
            activity_root,
            activity_subgroups_root,
            unit_definition,
            indications,
            categories,
            subcategories,
            activities,
            activity_groups,
            activity_subgroups,
            template_type,
            instance_template,
        ) in result:
            if library and library_name is not None and library_name != library.name:
                continue

            ar: _AggregateRootType = self._create_ar(
                library=library,
                root=root,
                relationship=relationship,
                value=value,
                study_count=study_count,
                ctterm_names=ctterm_names,
                activity_instance_root=activity_instance_root,
                activity_root=activity_root,
                activity_subgroups_root=activity_subgroups_root,
                unit_definition=unit_definition,
                indications=indications[0] if indications else [],
                template_type=template_type,
                categories=categories[0] if categories else [],
                subcategories=subcategories[0] if subcategories else [],
                activities=activities[0] if activities else [],
                activity_groups=activity_groups[0] if activity_groups else [],
                activity_subgroups=activity_subgroups[0] if activity_subgroups else [],
                instance_template=instance_template,
            )

            if value and relationship:
                if for_update:
                    ar.repository_closure_data = (
                        root,
                        value,
                        library,
                        copy.deepcopy(ar),
                    )
                else:
                    ar.repository_closure_data = RETRIEVED_READ_ONLY_MARK
                aggregates.append(ar)

        if not for_audit_trail:
            return aggregates[0]

        return aggregates

    def make_hashable(self, object_to_hash):
        if object_to_hash is None:
            return "None"
        if isinstance(object_to_hash, dict):
            return tuple(
                sorted((k, self.make_hashable(v)) for k, v in object_to_hash.items())
            )
        if isinstance(object_to_hash, list):
            return tuple(self.make_hashable(i) for i in object_to_hash)
        if isinstance(object_to_hash, set):
            return tuple(sorted(self.make_hashable(i) for i in object_to_hash))
        return object_to_hash

    def hashkey_library_item_with_metadata_get_all(
        self,
        *,
        status: LibraryItemStatus | None = None,
        library_name: str | None = None,
        return_study_count: bool | None = False,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        for_audit_trail: bool = False,
        version_specific_uids: dict | None = None,
        at_specific_date: datetime | None = None,
        include_retired_versions: bool = False,
    ):
        """
        Returns a hash key that will be used for mapping objects stored in cache,
        which ultimately determines whether a method invocation is a hit or miss.

        We need to define this custom hashing function with the same signature as the method we wish to cache (find_by_uid_optimized),
        since the target method contains optional/default parameters.
        If this custom hashkey function is not defined, most invocations of find_by_uid_optimized method will be misses.
        """
        return hashkey(
            self.make_hashable(type(self)),
            status,
            library_name,
            return_study_count,
            self.make_hashable(sort_by),
            page_number,
            page_size,
            self.make_hashable(filter_by),
            filter_operator,
            total_count,
            for_audit_trail,
            self.make_hashable(version_specific_uids),
            at_specific_date,
            include_retired_versions,
        )

    @cached(
        cache=cache_store_item_by_uid,
        key=hashkey_library_item_with_metadata_get_all,
        lock=lock_store_item_by_uid,
    )
    # pylint: disable=too-many-locals
    def get_all_optimized(
        self,
        *,
        status: LibraryItemStatus | None = None,
        library_name: str | None = None,
        return_study_count: bool | None = False,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        for_audit_trail: bool = False,
        version_specific_uids: dict | None = None,
        at_specific_date: datetime | None = None,
        include_retired_versions: bool = False,
    ) -> tuple[list, int]:
        validate_dict(filter_by, "filters")
        validate_dict(sort_by, "sort_by")
        validate_max_skip_clause(page_number=page_number, page_size=page_size)

        aggregates = []

        where_stmt, params = self._where_stmt_optimized(
            filter_by, filter_operator, version_specific_uids=version_specific_uids
        )

        match_stmt, return_stmt = self._find_cypher_query_optimized(
            with_status=bool(status),
            with_pagination=bool(page_size),
            with_versions_in_where=bool(version_specific_uids),
            with_at_specific_date=bool(at_specific_date),
            return_study_count=return_study_count,
            where_stmt=where_stmt,
            sort_by=sort_by,
            for_audit_trail=for_audit_trail,
            include_retired_versions=include_retired_versions,
        )

        if status:
            params["status"] = status.value

        if page_size > 0:
            params["page_number"] = page_number - 1
            params["page_size"] = page_size

        if at_specific_date:
            params["at_specific_date"] = at_specific_date

        cypher_query = match_stmt + return_stmt

        # If a CTTermName is requested at a specific date and we do not want to raise an exception if not found,
        # We retrieve both this version if available and the latest
        # Then we return the latest if there is no available version at the given date
        # This is for returning Terms in the context of a study with a StudyStandardVersion
        if issubclass(self.root_class, CTTermNameRoot) and at_specific_date is not None:
            latest_match_stmt, latest_return_stmt = self._find_cypher_query_optimized(
                get_latest_final=True,
                with_pagination=bool(page_size),
                return_study_count=return_study_count,
                where_stmt=where_stmt,
                for_audit_trail=for_audit_trail,
                include_retired_versions=include_retired_versions,
            )
            cypher_query += (
                ", false AS is_latest_fallback "
                + " UNION ALL "
                + latest_match_stmt
                + latest_return_stmt
                + ", true AS is_latest_fallback"
            )

        try:
            result, _ = db.cypher_query(
                cypher_query,
                params=params,
                resolve_objects=True,
            )
        except NodeClassNotDefined as exc:
            raise NotFoundException(
                msg="Resource doesn't exist - it was likely deleted in a concurrent transaction."
            ) from exc

        if not result:
            NotFoundException.raise_if(
                issubclass(self.root_class, CTTermNameRoot),
                msg=f"No {self.root_class.__label__} found in given status, date and version ; nor was a latest final one found.",
            )

        if issubclass(self.root_class, CTTermNameRoot):
            for i, i_result in enumerate(result):
                result[i][5]["queried_effective_date"] = None
                result[i][5]["date_conflict"] = False
            if at_specific_date is not None:
                # Last entry in each result row is a boolean is_latest_fallback
                # indicating if the returned value is the requested one for date
                # or the default latest final one
                # Drop that last column once it has been used
                matched_element_ids = list(
                    set(i_result[5]["ctterm_name_element_id"] for i_result in result)
                )
                not_matched = [
                    param
                    for param in params["uids"]
                    if (param not in matched_element_ids)
                ]
                NotFoundException.raise_if(
                    len(not_matched) > 0,
                    msg=f"No {self.root_class.__label__} found in given status, date and version ; nor was a latest final one found for these ElementID {not_matched}",
                )
                total_result = []
                # for every uid to query
                for param in params["uids"]:
                    # give me the results of the specific uid
                    filtered_result = [
                        i_result
                        for i_result in result
                        if i_result[5]["ctterm_name_element_id"] == param
                    ]
                    non_latest_results = [
                        r[:-1] for r in filtered_result if r[-1] is False
                    ]
                    if len(non_latest_results) > 0:
                        # Keep only non latest results if any
                        non_latest_results[0][5][
                            "queried_effective_date"
                        ] = at_specific_date
                        total_result.append(non_latest_results[0])
                    else:
                        # Keep only latest results if no results at date
                        # And raise date conflict flag
                        latest_result = [
                            r[:-1] for r in filtered_result if r[-1] is True
                        ]
                        latest_result[0][5]["date_conflict"] = True
                        total_result.append(latest_result[0])
                result = total_result

        for (
            library,
            root,
            relationship,
            value,
            study_count,
            ctterm_names,
            activity_instance_root,
            activity_root,
            activity_subgroups_root,
            unit_definition,
            indications,
            categories,
            subcategories,
            activities,
            activity_groups,
            activity_subgroups,
            template_type,
            instance_template,
        ) in result:
            if library and library_name is not None and library_name != library.name:
                continue

            ar = self._create_ar(
                library=library,
                root=root,
                relationship=relationship,
                value=value,
                study_count=study_count,
                ctterm_names=ctterm_names,
                activity_instance_root=activity_instance_root,
                activity_root=activity_root,
                activity_subgroups_root=activity_subgroups_root,
                unit_definition=unit_definition,
                indications=indications[0] if indications else [],
                template_type=template_type,
                categories=categories[0] if categories else [],
                subcategories=subcategories[0] if subcategories else [],
                activities=activities[0] if activities else [],
                activity_groups=activity_groups[0] if activity_groups else [],
                activity_subgroups=activity_subgroups[0] if activity_subgroups else [],
                instance_template=instance_template,
            )

            ar.repository_closure_data = RETRIEVED_READ_ONLY_MARK
            aggregates.append(ar)

        count_result = []
        if total_count:
            count_result, _ = db.cypher_query(
                query=match_stmt + "RETURN count(DISTINCT ver_rel)", params=params
            )
        total_amount = (
            count_result[0][0] if len(count_result) > 0 and total_count else 0
        )
        return aggregates, total_amount

    def get_headers_optimized(
        self,
        *,
        field_name: str,
        status: LibraryItemStatus | None = None,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        page_size: int = 10,
    ):
        if page_size <= 0:
            return []

        validate_dict(filter_by, "filters")

        if filter_by is None:
            filter_by = {}

        try:
            cypher_field_name = self.basemodel_to_cypher_mapping_optimized()[field_name]
        except KeyError as e:
            raise ValidationException(
                msg=f"Unsupported field name parameter: {field_name}. Supported parameters are: {list(self.basemodel_to_cypher_mapping_optimized())}"
            ) from e

        if search_string:
            filter_by[field_name] = {
                "v": [search_string],
                "op": ComparisonOperator.CONTAINS.value,
            }

        where_stmt, params = self._where_stmt_optimized(filter_by, filter_operator)

        match_stmt, return_stmt = self._headers_cypher_query(
            cypher_field_name=cypher_field_name,
            with_status=bool(status),
            where_stmt=where_stmt,
        )

        if status:
            params["status"] = status.value

        result, _ = db.cypher_query(
            match_stmt + return_stmt,
            params=params | {"page_size": page_size},
            resolve_objects=True,
        )

        rs = []
        for item in result:
            if item[0]:
                elm = item[0]
                if isinstance(elm, neo4j.time.DateTime):
                    elm = convert_to_datetime(elm)
                rs.append(elm)

        return rs

    def basemodel_to_cypher_mapping_optimized(self):
        # Mapping between BaseModel attribute names and their corresponding
        # cypher query (as returned by _find_cypher_query() and _headers_cypher_query()) variables for filtering, sorting and headers
        mapping = {
            "library.name": "library.name",
            "uid": "root.uid",
            "sequence_id": "root.sequence_id",
            "name": "value.name",
            "name_plain": "value.name_plain",
            "status": "ver_rel.status",
            "author_id": "ver_rel.author_id",
            "version": "ver_rel.version",
            "start_date": "ver_rel.start_date",
            "end_date": "ver_rel.end_date",
        }

        if "SyntaxTemplateRoot" in [
            ith_class.__label__ if hasattr(ith_class, "__label__") else None
            for ith_class in self.root_class.mro()
        ] or "SyntaxInstanceRoot" in [
            ith_class.__label__ if hasattr(ith_class, "__label__") else None
            for ith_class in self.root_class.mro()
        ]:
            mapping |= {"study_count": "study_count"}

        if hasattr(self.root_class, "is_confirmatory_testing"):
            mapping |= {"is_confirmatory_testing": "root.is_confirmatory_testing"}

        # pylint: disable=no-member
        if hasattr(self, "template_class"):
            mapping |= {"template.name": "template_value.name"}

            if hasattr(self.template_class, "has_type"):
                mapping |= {
                    "template_uid": "template_root.uid",
                    "template_name": "template_value.name",
                    "template_type_uid": "type_root.uid",
                    "type.term_uid": "type_root.uid",
                    "template.type.term_uid": "type_root.uid",
                }

        if hasattr(self.value_class, "guidance_text"):
            mapping |= {"guidance_text": "value.guidance_text"}

        if hasattr(self.root_class, "has_indication"):
            mapping |= {
                "indications.term_uid": "indication_root.uid",
                "indications.name": "indication_value.name",
            }

        if hasattr(self.root_class, "has_type"):
            mapping |= {
                "template_type_uid": "type_root.uid",
                "type.term_uid": "type_root.uid",
                "type.name.sponsor_preferred_name": "type_ct_term_name_value.name",
                "type.name.sponsor_preferred_name_sentence_case": "type_ct_term_name_value.name_sentence_case",
                "type.attributes.code_submission_value": "type_ct_term_attributes_value.code_submission_value",
                "type.attributes.preferred_term": "type_ct_term_attributes_value.preferred_term",
            }

        if hasattr(self.root_class, "has_category"):
            mapping |= {
                "categories.term_uid": "category_root.uid",
                "categories.name.sponsor_preferred_name": "category_ct_term_name_value.name",
                "categories.name.sponsor_preferred_name_sentence_case": "category_ct_term_name_value.name_sentence_case",
                "categories.attributes.code_submission_value": "category_ct_term_attributes_value.code_submission_value",
                "categories.attributes.preferred_term": "category_ct_term_attributes_value.preferred_term",
            }

        if hasattr(self.root_class, "has_subcategory"):
            mapping |= {
                "sub_categories.term_uid": "subcategory_root.uid",
                "sub_categories.name.sponsor_preferred_name": "subcategory_ct_term_name_value.name",
                "sub_categories.name.sponsor_preferred_name_sentence_case": "subcategory_ct_term_name_value.name_sentence_case",
                "sub_categories.attributes.code_submission_value": "subcategory_ct_term_attributes_value.code_submission_value",
                "sub_categories.attributes.preferred_term": "subcategory_ct_term_attributes_value.preferred_term",
                "subCategories.term_uid": "subcategory_root.uid",
                "subCategories.name.sponsor_preferred_name": "subcategory_ct_term_name_value.name",
                "subCategories.name.sponsor_preferred_name_sentence_case": "subcategory_ct_term_name_value.name_sentence_case",
                "subCategories.attributes.code_submission_value": "subcategory_ct_term_attributes_value.code_submission_value",
                "subCategories.attributes.preferred_term": "subcategory_ct_term_attributes_value.preferred_term",
            }

        if hasattr(self.root_class, "has_activity"):
            mapping |= {
                "activities.uid": "activity_root.uid",
                "activities": "activity_value.name",
                "activities.name": "activity_value.name",
                "activities.name_sentence_case": "activity_value.name_sentence_case",
                "activity.uid": "activity_root.uid",
                "activity": "activity_value.name",
                "activity.name": "activity_value.name",
                "activity.name_sentence_case": "activity_value.name_sentence_case",
            }

        if hasattr(self.root_class, "has_activity_group"):
            mapping |= {
                "activity_groups.uid": "activity_group_root.uid",
                "activity_groups": "activity_group_value.name",
                "activity_groups.name": "activity_group_value.name",
                "activity_groups.name_sentence_case": "activity_group_value.name_sentence_case",
                "activity.activity_group.uid": "activity_group_root.uid",
                "activity.activity_group": "activity_group_value.name",
                "activity.activity_group.name": "activity_group_value.name",
                "activity.activity_group.name_sentence_case": "activity_group_value.name_sentence_case",
            }

        if hasattr(self.root_class, "has_activity_subgroup"):
            mapping |= {
                "activity_subgroups.uid": "activity_subgroup_root.uid",
                "activity_subgroups": "activity_subgroup_value.name",
                "activity_subgroups.name": "activity_subgroup_value.name",
                "activity_subgroups.name_sentence_case": "activity_subgroup_value.name_sentence_case",
                "activity.activity_subgroup.uid": "activity_subgroup_root.uid",
                "activity.activity_subgroup": "activity_subgroup_value.name",
                "activity.activity_subgroup.name": "activity_subgroup_value.name",
                "activity.activity_subgroup.name_sentence_case": "activity_subgroup_value.name_sentence_case",
            }

        return mapping

    def _where_stmt_optimized(
        self,
        filter_by: dict | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        version_specific_uids: dict | None = None,
    ):
        def date_stmt(name: str):
            if name in filter_by:
                if (
                    "op" not in filter_by[name]
                    or filter_by[name]["op"] in ComparisonOperator.EQUALS.value
                ):
                    for idx, val in enumerate(filter_by[name]["v"]):
                        fields_non_generic.append(
                            f" date({mapping[name]}) = date(${name}_eq_{idx}) "
                        )
                        params[f"{name}_eq_{idx}"] = val
                        filter_by.pop(name, None)
                elif filter_by[name]["op"] == ComparisonOperator.BETWEEN.value:
                    fields_non_generic.append(
                        f" date({mapping[name]}) >= date(${name}_bw_1) and date({mapping[name]}) <= date(${name}_bw_2) "
                    )
                    params[f"{name}_bw_1"] = filter_by[name]["v"][0]
                    params[f"{name}_bw_2"] = filter_by[name]["v"][1]
                    filter_by.pop(name, None)

        if not filter_by and not version_specific_uids:
            return "", {}

        mapping = self.basemodel_to_cypher_mapping_optimized()

        fields_generic = []
        fields_non_generic = []
        params = {}
        where_stmt = ""

        if filter_by:
            if "*" in filter_by:
                for _, cypher_name in mapping.items():
                    if (
                        "op" in filter_by["*"]
                        and filter_by["*"]["op"] == ComparisonOperator.EQUALS.value
                    ):
                        operator = "="
                    else:
                        operator = "CONTAINS"

                    if any(not isinstance(value, str) for value in filter_by["*"]["v"]):
                        operator = "="

                    for idx, value in enumerate(filter_by["*"]["v"]):
                        param_variable = f"{cypher_name}_generic_{idx}".replace(
                            ".", "_"
                        )
                        params[param_variable] = value
                        fields_generic.append(
                            f" {cypher_name} {operator} ${param_variable} "
                        )

                where_stmt += "(" + " OR ".join(fields_generic) + ")"

            if issubclass(self.root_class, CTTermNameRoot) and "uid" in filter_by:
                fields_non_generic.append(" elementID(root) IN $uids ")
                params["uids"] = filter_by["uid"]["v"]
                filter_by.pop("uid", None)

            date_stmt("start_date")
            date_stmt("end_date")

            filter_by.pop("*", None)
            for filter_name, items in filter_by.items():
                ValidationException.raise_if(
                    filter_name not in mapping,
                    msg=f"Unsupported filtering parameter: {filter_name}. "
                    f"Supported parameters are: {list(self.basemodel_to_cypher_mapping_optimized())}",
                )

                op = items.get("op")
                if op == ComparisonOperator.EQUALS.value:
                    operator = "="
                elif op == ComparisonOperator.IN.value:
                    operator = ComparisonOperator.IN.value
                else:
                    operator = "CONTAINS"

                if any(not isinstance(value, str) for value in items["v"]):
                    operator = "="

                if operator == ComparisonOperator.IN.value:
                    param_variable = f"{mapping[filter_name]}_non_generic".replace(
                        ".", "_"
                    )
                    params[param_variable] = items["v"]
                    fields_non_generic.append(
                        f" {mapping[filter_name]} {operator} ${param_variable} "
                    )

                else:
                    for idx, value in enumerate(items["v"]):
                        param_variable = (
                            f"{mapping[filter_name]}_non_generic_{idx}".replace(
                                ".", "_"
                            )
                        )
                        params[param_variable] = value
                        fields_non_generic.append(
                            f" {mapping[filter_name]} {operator} ${param_variable} "
                        )

            if not where_stmt:
                where_stmt += f" {filter_operator.value} ".join(fields_non_generic)
            elif fields_non_generic:
                where_stmt += (
                    f" {filter_operator.value} ("
                    + f" {filter_operator.value} ".join(fields_non_generic)
                    + ")"
                )

        version_spec_uids_where_stmt_list = []
        if version_specific_uids:
            for uid, versions in version_specific_uids.items():
                specific_versions = []
                for version in versions:
                    if version == "LATEST":
                        version_spec_uids_where_stmt_list.append(
                            f""" (root.uid = "{uid}" AND ver_rel.version = latest_version.version ) """
                        )
                    else:
                        specific_versions.append(version)
                if specific_versions:
                    version_spec_uids_where_stmt_list.append(
                        f""" (root.uid = "{uid}" AND ver_rel.version in {list(specific_versions)}  ) """
                    )

        if version_spec_uids_where_stmt_list:
            if not where_stmt:
                where_stmt += " OR ".join(version_spec_uids_where_stmt_list)
            else:
                where_stmt += (
                    " AND (" + " OR ".join(version_spec_uids_where_stmt_list) + ")"
                )

        return "WHERE " + where_stmt, params

    def _sort_stmt(self, sort_by: dict | None = None):
        if not sort_by:
            return "ORDER BY root.uid DESC"

        mapping = self.basemodel_to_cypher_mapping_optimized()

        fields = []
        for sort_field, direction in sort_by.items():
            ValidationException.raise_if(
                sort_field not in mapping,
                msg=f"Unsupported sorting parameter: {sort_field}. "
                f"Supported parameters are: {list(self.basemodel_to_cypher_mapping_optimized())}",
            )

            fields.append(f'{mapping[sort_field]} {"ASC" if direction else "DESC"}')

        return "ORDER BY " + ", ".join(fields)

    def _headers_cypher_query(
        self,
        cypher_field_name: str,
        with_status: bool = False,
        where_stmt: str = "",
    ):
        version_where_stmt = ""
        retire_exclusion = "WITH root as _root"
        if with_status:
            version_where_stmt += "WHERE ver_rel.status = $status"
            retire_exclusion = """
            CALL {
                WITH root, value
                MATCH (root)-[ver_rel:HAS_VERSION]->()
                WITH * ORDER BY ver_rel.start_date DESC LIMIT 1
                WHERE $status <> "Final" OR (ver_rel.status <> "Retired" AND $status = "Final")
                MATCH (_root)-[ver_rel]->()
                RETURN _root
            }
            """

        match_stmt = f"""
            MATCH (library:Library)-[:{self.root_class.LIBRARY_REL_LABEL}]->(root:{self.root_class.__label__})
            -[:LATEST]->(value:{self.value_class.__label__})
            CALL {{
                WITH root, value
                {retire_exclusion}
                MATCH (_root)-[ver_rel:HAS_VERSION]->(_value)
                WITH ver_rel, _root, _value
                {version_where_stmt}
                RETURN _root, _value, ver_rel ORDER BY ver_rel.start_date DESC LIMIT 1
            }}
            WITH _root AS root, _value AS value, library, ver_rel
        """

        if "SyntaxInstanceRoot" in [
            ith_class.__label__ if hasattr(ith_class, "__label__") else None
            for ith_class in self.root_class.mro()
        ]:
            match_stmt += self._only_instances_with_studies()

            match_stmt += """
                OPTIONAL MATCH (value)<--(:StudySelection)<--(:StudyValue)<-[:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED]-(sr:StudyRoot)
            """

        if "SyntaxInstanceRoot" in [
            ith_class.__label__ if hasattr(ith_class, "__label__") else None
            for ith_class in self.root_class.mro()
        ] or "SyntaxPreInstanceRoot" in [
            ith_class.__label__ if hasattr(ith_class, "__label__") else None
            for ith_class in self.root_class.mro()
        ]:
            stmt, _ = self._instance_template_match_return_stmt()

            match_stmt += stmt

        if hasattr(self.root_class, "has_indication"):
            stmt, _ = self._indication_match_return_stmt()

            match_stmt += stmt

        # pylint: disable=no-member
        if hasattr(self.root_class, "has_type") or (
            hasattr(self, "template_class") and hasattr(self.template_class, "has_type")
        ):
            stmt, _ = self._template_type_match_return_stmt()

            match_stmt += stmt

        if hasattr(self.root_class, "has_category"):
            stmt, _ = self._category_match_return_stmt()

            match_stmt += stmt

        if hasattr(self.root_class, "has_subcategory"):
            stmt, _ = self._subcategory_match_return_stmt()

            match_stmt += stmt

        if hasattr(self.root_class, "has_activity"):
            stmt, _ = self._activity_match_return_stmt()

            match_stmt += stmt

        if hasattr(self.root_class, "has_activity_group"):
            stmt, _ = self._activity_group_match_return_stmt()

            match_stmt += stmt

        if hasattr(self.root_class, "has_activity_subgroup"):
            stmt, _ = self._activity_subgroup_match_return_stmt()

            match_stmt += stmt

        with_agg_study_count = (
            ", COUNT(DISTINCT sr) as study_count "
            if "SyntaxInstanceRoot"
            in [
                ith_class.__label__ if hasattr(ith_class, "__label__") else None
                for ith_class in self.root_class.mro()
            ]
            else ", 0 as study_count "
        )

        match_stmt += f"WITH * {with_agg_study_count} {where_stmt} "

        return_stmt = f"""
            RETURN DISTINCT {cypher_field_name}
            LIMIT $page_size
        """

        return match_stmt, return_stmt

    # pylint: disable=too-many-statements
    def _find_cypher_query_optimized(
        self,
        get_latest_final: bool = False,
        with_status: bool = False,
        with_version: bool = False,
        with_pagination: bool = True,
        with_at_specific_date: bool = False,
        with_versions_in_where: bool = False,
        return_study_count: bool = False,
        where_stmt: str = "",
        sort_by: dict | None = None,
        uid: str | None = None,
        for_audit_trail: bool = False,
        include_retired_versions: bool = False,
    ):
        """
        Default behavior
            with_status
                options:
                    - DRAFT -- return the latest draft version
                    - RETIRED -- return the latest retired version
                    - FINAL -- return the latest final if the current version is not retired, if the current version is retired then it won't be retrieved
            with_version
                options:
                    - version number
                - will give the specific version
            with_at_specific_date
                options:
                    - date
                - will match the version that the range between the start date and the end date matches the queried date,
                    if the end date is null then it will look at the start date to be less than the queried date
            combination of with_status, with_version and with_at_specific_date method parameters is an AND operator between them
                with_versions_in_where:
                    (status = Final and version AND at_specific_date)
            status parameter is provider
                - Final
                    will be excluded those Root that their current status is RETIRED

        Specific behavior
            get_latest_final
                - True : - Will return the latest final version, without the need to pass parameters
                        This allows you to UNION a query getting a term at a date with a specific status,
                        with a second query which returns the latest final regardless of status.
                        - This flag, renders the status, version and specific_date unusable when calling find_cypher_query_optimized




        """
        version_where_stmt = ""
        retire_exclusion = "WITH root as _root"
        if get_latest_final:
            version_where_stmt += "WHERE ver_rel.status = 'Final'"
            retire_exclusion = """
            CALL {
                WITH root
                MATCH (root)-[ver_rel:HAS_VERSION]->()
                WITH * ORDER BY ver_rel.start_date DESC LIMIT 1
                WHERE ver_rel.status = "Final"
                MATCH (_root)-[ver_rel]->()
                RETURN _root
            }
            """
        else:
            if with_status:
                version_where_stmt += "WHERE ver_rel.status = $status"
                retire_exclusion = """
                CALL {
                    WITH root
                    MATCH (root)-[ver_rel:HAS_VERSION]->()
                    WITH * ORDER BY ver_rel.start_date DESC LIMIT 1
                    WHERE $status <> "Final" OR (ver_rel.status <> "Retired" AND $status = "Final")
                    MATCH (_root)-[ver_rel]->()
                    RETURN _root
                }
                """
            if with_version:
                if version_where_stmt:
                    version_where_stmt += " AND ver_rel.version = $version"
                else:
                    version_where_stmt += "WHERE ver_rel.version = $version"
            if with_at_specific_date:
                if version_where_stmt:
                    version_where_stmt += " AND"
                else:
                    version_where_stmt += "WHERE"
                version_where_stmt += """(ver_rel.start_date<= datetime($at_specific_date) < datetime(ver_rel.end_date))
                                            OR (ver_rel.end_date IS NULL AND (ver_rel.start_date <= datetime($at_specific_date)))"""
        if with_versions_in_where:
            # when the versions in where are specified the scope is that we want to retrieve the latest version,
            # so in method _where_stmt_optimized will be used the latest_version to get the the version number of it.
            ver_rel_filtering = f"""
                CALL{{
                    WITH _root
                    MATCH (_root)-[max_ver_rel:HAS_VERSION]->()
                        {'WHERE max_ver_rel.status <> "Retired"' if not include_retired_versions else ''}
                    WITH _root, max_ver_rel ORDER BY max_ver_rel.start_date DESC LIMIT 1
                    RETURN max_ver_rel as latest_version
                }}
                RETURN _root, _value, ver_rel, latest_version
            """
        else:
            ver_rel_filtering = """
                WITH *, NULL as latest_version
                RETURN _root, _value, ver_rel, latest_version ORDER BY ver_rel.start_date DESC LIMIT 1
            """
        version_call = f"""
            CALL {{
                WITH root
                {retire_exclusion}
                MATCH (_root)-[ver_rel:HAS_VERSION]->(_value)
                {version_where_stmt}
                {ver_rel_filtering}
                
            }}
            WITH _root AS root, _value AS value, library, ver_rel, latest_version
        """
        version_rel = "ver_rel:HAS_VERSION"

        if for_audit_trail and not with_status:
            version_call = ""
        else:
            version_rel = (
                "ver_rel:LATEST"
                if not with_version and not with_status and not with_versions_in_where
                else "ver_rel:HAS_VERSION"
            )

        if uid:
            if issubclass(self.root_class, CTTermNameRoot):
                uid_where_stmt = "WHERE elementID(root)  = $uid"
                library__stmt = "MATCH (library:Library)-[:CONTAINS_TERM]->(ctterm_root:CTTermRoot)-[:HAS_NAME_ROOT]->(root)"
            else:
                uid_where_stmt = "WHERE root.uid = $uid"
                library__stmt = f"MATCH (library:Library)-[:{self.root_class.LIBRARY_REL_LABEL}]->(root)"
        else:
            if issubclass(self.root_class, CTTermNameRoot):
                uid_where_stmt = ""
                library__stmt = "MATCH (library:Library)-[:CONTAINS_TERM]->(ctterm_root:CTTermRoot)-[:HAS_NAME_ROOT]->(root)"
            else:
                uid_where_stmt = ""
                library__stmt = f"MATCH (library:Library)-[:{self.root_class.LIBRARY_REL_LABEL}]->(root)"
        value_matching = (
            f"-[{version_rel}]->(value:{self.value_class.__label__})"
            if not version_call
            else ""
        )
        match_stmt = f"""
            MATCH (root:{self.root_class.__label__}){value_matching}
            {uid_where_stmt}
            {library__stmt}
            {version_call}
        """

        if not uid and "SyntaxInstanceRoot" in [
            ith_class.__label__ if hasattr(ith_class, "__label__") else None
            for ith_class in self.root_class.mro()
        ]:
            match_stmt += self._only_instances_with_studies()

        if return_study_count and "SyntaxTemplateRoot" in [
            ith_class.__label__ if hasattr(ith_class, "__label__") else None
            for ith_class in self.root_class.mro()
        ]:
            match_stmt += f"""
                OPTIONAL MATCH (root)-[:{self.root_class.TEMPLATE_REL_LABEL}]->(:SyntaxInstanceRoot)-->(:SyntaxInstanceValue)
                <--(:StudySelection)<--(:StudyValue)<-[:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED]-(sr:StudyRoot)
            """

        if return_study_count and "SyntaxInstanceRoot" in [
            ith_class.__label__ if hasattr(ith_class, "__label__") else None
            for ith_class in self.root_class.mro()
        ]:
            match_stmt += """
                OPTIONAL MATCH (value)<--(:StudySelection)<--(:StudyValue)<-[:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED]-(sr:StudyRoot)
            """

        ctterm_names_return = ", null as ctterm_name"
        activity_instance_root_return = ", null as activity_instance_root"
        activity_root_return = ", null as activity_root"
        activity_subgroups_root_return = ", null as activity_subgroups_root"
        unit_definition_return = ", null as unit_definition"
        instance_template_return = ", null as instance_template"
        indications_return = ", null as indication"
        template_type_return = ", null as template_type"
        categories_return = ", null as categories"
        subcategories_return = ", null as subcategories"
        activities_return = ", null as activities"
        activity_groups_return = ", null as activity_groups"
        activity_subgroups_return = ", null as activity_subgroups"

        if issubclass(self.root_class, CTTermNameRoot):
            stmt, ctterm_names_return = self._ctterm_name_match_return_stmt()
            match_stmt += stmt

        if self.root_class.__label__ == "ActivityInstanceRoot":
            (
                stmt,
                activity_instance_root_return,
            ) = self._activity_instance_root_match_return_stmt()

            match_stmt += stmt

        if self.root_class.__label__ == "ActivityRoot":
            stmt, activity_root_return = self._activity_root_match_return_stmt()

            match_stmt += stmt

        if self.root_class.__label__ == "ActivitySubGroupRoot":
            (
                stmt,
                activity_subgroups_root_return,
            ) = self._activity_subgroup_root_match_return_stmt()

            match_stmt += stmt

        if self.root_class.__label__ == "UnitDefinitionRoot":
            stmt, unit_definition_return = self._unit_definition_match_return_stmt()

            match_stmt += stmt

        if "SyntaxInstanceRoot" in [
            ith_class.__label__ if hasattr(ith_class, "__label__") else None
            for ith_class in self.root_class.mro()
        ] or "SyntaxPreInstanceRoot" in [
            ith_class.__label__ if hasattr(ith_class, "__label__") else None
            for ith_class in self.root_class.mro()
        ]:
            stmt, instance_template_return = self._instance_template_match_return_stmt()

            match_stmt += stmt

        if hasattr(self.root_class, "has_indication"):
            stmt, indications_return = self._indication_match_return_stmt()

            match_stmt += stmt

        # pylint: disable=no-member
        if hasattr(self.root_class, "has_type") or (
            hasattr(self, "template_class") and hasattr(self.template_class, "has_type")
        ):
            stmt, template_type_return = self._template_type_match_return_stmt()

            match_stmt += stmt

        if hasattr(self.root_class, "has_category"):
            stmt, categories_return = self._category_match_return_stmt()

            match_stmt += stmt

        if hasattr(self.root_class, "has_subcategory"):
            stmt, subcategories_return = self._subcategory_match_return_stmt()

            match_stmt += stmt

        if hasattr(self.root_class, "has_activity"):
            stmt, activities_return = self._activity_match_return_stmt()

            match_stmt += stmt

        if hasattr(self.root_class, "has_activity_group"):
            stmt, activity_groups_return = self._activity_group_match_return_stmt()

            match_stmt += stmt

        if hasattr(self.root_class, "has_activity_subgroup"):
            (
                stmt,
                activity_subgroups_return,
            ) = self._activity_subgroup_match_return_stmt()

            match_stmt += stmt

        with_agg_study_count = (
            "COUNT(DISTINCT sr) as study_count "
            if return_study_count
            and (
                "SyntaxTemplateRoot"
                in [
                    ith_class.__label__ if hasattr(ith_class, "__label__") else None
                    for ith_class in self.root_class.mro()
                ]
                or "SyntaxInstanceRoot"
                in [
                    ith_class.__label__ if hasattr(ith_class, "__label__") else None
                    for ith_class in self.root_class.mro()
                ]
            )
            else "0 as study_count "
        )

        match_stmt += "WITH *, " + with_agg_study_count

        if where_stmt:
            match_stmt += f" {where_stmt} "

        return_stmt = f"""
            RETURN DISTINCT
                library
                ,root
                ,ver_rel
                ,value
                ,study_count
                {ctterm_names_return}
                {activity_instance_root_return}
                {activity_root_return}
                {activity_subgroups_root_return}
                {unit_definition_return}
                {indications_return}
                {categories_return}
                {subcategories_return}
                {activities_return}
                {activity_groups_return}
                {activity_subgroups_return}
                {template_type_return}
                {instance_template_return}
            """

        if not for_audit_trail:
            if not uid and not issubclass(self.root_class, CTTermNameRoot):
                return_stmt += f" {self._sort_stmt(sort_by)} "

                if with_pagination:
                    return_stmt += " SKIP $page_number * $page_size LIMIT $page_size "
        else:
            if not uid:
                return_stmt += " ORDER BY ver_rel.start_date DESC "

                if with_pagination:
                    return_stmt += " SKIP $page_number * $page_size LIMIT $page_size "
            else:
                return_stmt += " ORDER BY ver_rel.start_date DESC "

        return match_stmt, return_stmt

    def _ctterm_name_match_return_stmt(self):
        match_stmt = """
            MATCH (root)<-[root_has_name_root__ctterm_root:HAS_NAME_ROOT]-(ctterm_root)
            CALL{
                WITH ctterm_root
                MATCH (ctterm_root)<-[ctterm_root__ct_codelist_root:HAS_TERM]-(ctcodelist_root:CTCodelistRoot)<-[:HAS_CODELIST]-(ct_catalogue:CTCatalogue)
                MATCH (ctcodelist_root)<-[:CONTAINS_CODELIST]-(codelist_library:Library)
                RETURN collect(DISTINCT {
                    uid: ctcodelist_root.uid
                    ,order: ctterm_root__ct_codelist_root.order
                    ,codelist_library_name: codelist_library.name
                    ,ct_catalogue_name: ct_catalogue.name
                }) as codelists
            } 
        """
        ctterm_names_return = """,
            {
                ctterm_root_uid: ctterm_root.uid
                ,catalogue: codelists[0].ct_catalogue_name
                ,codelists: codelists
                ,ctterm_name_element_id: elementID(root)
            } as ctterm_name
        """
        return match_stmt, ctterm_names_return

    def _activity_instance_root_match_return_stmt(self):
        match_stmt = """
            MATCH (root)-[ver_rel]->(activity_instance_value:ActivityInstanceValue)
            // ACTIVITY_INSTANCE_CLASS
            CALL{
               WITH root,ver_rel,activity_instance_value
               MATCH (activity_instance_value:ActivityInstanceValue)-[:ACTIVITY_INSTANCE_CLASS]->(activity_instance_class_root:ActivityInstanceClassRoot)
               MATCH (activity_instance_class_root:ActivityInstanceClassRoot)-[:LATEST]-(activity_instance_class_root_latest_value:ActivityInstanceClassValue)
               RETURN  distinct {activity_instance_class_uid: activity_instance_class_root.uid, activity_instance_class_name: activity_instance_class_root_latest_value.name} as activity_instance_class
            }
            // ACTIVITY INSTANCE GROUPINGS
            CALL{
                WITH root,ver_rel,activity_instance_value
                WITH *, 
                 [(root)-[ver_rel]->(activity_instance_value)-[:HAS_ACTIVITY]->(activity_instance_grouping:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup) | 
                    {
                        activity: head(apoc.coll.sortMulti([(activity_instance_grouping)-[:HAS_GROUPING]-(:ActivityValue)<-[has_version:HAS_VERSION]-
                            (activity_root:ActivityRoot) | 
                            {
                                uid:activity_root.uid,
                                major_version: toInteger(split(has_version.version,'.')[0]),
                                minor_version: toInteger(split(has_version.version,'.')[1])
                            }], ['major_version', 'minor_version'])),
                        activity_subgroup: head(apoc.coll.sortMulti([(activity_valid_group)<-[:HAS_GROUP]-(:ActivitySubGroupValue)<-[has_version:HAS_VERSION]-
                            (activity_subgroup_root:ActivitySubGroupRoot) | 
                            {
                                uid:activity_subgroup_root.uid,
                                major_version: toInteger(split(has_version.version,'.')[0]),
                                minor_version: toInteger(split(has_version.version,'.')[1])
                            }], ['major_version', 'minor_version'])), 
                        activity_group: head(apoc.coll.sortMulti([(activity_valid_group)-[:IN_GROUP]-(:ActivityGroupValue)<-[has_version:HAS_VERSION]-
                            (activity_group_root:ActivityGroupRoot) | 
                            {
                                uid:activity_group_root.uid,
                                major_version: toInteger(split(has_version.version,'.')[0]),
                                minor_version: toInteger(split(has_version.version,'.')[1])
                            }], ['major_version', 'minor_version']))
                    }
                ] as activity_instance_groupings
                RETURN activity_instance_groupings
            }
            // ACTIVITY ITEMS
            CALL{
                WITH root,ver_rel,activity_instance_value
                MATCH (root)-[ver_rel]->(activity_instance_value)-[:CONTAINS_ACTIVITY_ITEM]-(activity_item:ActivityItem)
                // ACTIVITY ITEM ACTIVITY ITEM CLASS VALUE
                MATCH (activity_item:ActivityItem)-[:HAS_ACTIVITY_ITEM]-(activity_item_class_root:ActivityItemClassRoot)-[:LATEST]->(activity_item_class_value:ActivityItemClassValue)
                //ACTIVITY ITEM CTTERMS
                CALL{
                    WITH activity_item
                    MATCH (activity_item)-[:HAS_CT_TERM]->(activity_item_ctterm_root:CTTermRoot)
                    MATCH (activity_item_ctterm_root)-->(:CTTermNameRoot)-[:LATEST_FINAL]->(ct_name_value:CTTermNameValue)
                    RETURN collect(DISTINCT {uid:activity_item_ctterm_root.uid, name:ct_name_value.name }) as ct_terms
                }
                // ACTIVITY ITEM UNIT DEFINITIONS
                CALL{
                    WITH activity_item
                    MATCH (activity_item)-[:HAS_UNIT_DEFINITION]->(activity_item_unit_definition_root:UnitDefinitionRoot)
                    MATCH (activity_item_unit_definition_root)-[:LATEST]->(activity_item_unit_definition_value:UnitDefinitionValue)
                    RETURN collect(DISTINCT {uid:activity_item_unit_definition_root.uid, name:activity_item_unit_definition_value.name }) as unit_definitions
                }
                RETURN  COLLECT( distinct {
                    activity_item_class_uid: activity_item_class_root.uid, 
                    activity_item_class_name: activity_item_class_value.name, 
                    ct_terms:ct_terms, 
                    unit_definitions: unit_definitions
                }) as activity_items
            }
        """

        activity_instance_root_return = """,
            {
                activity_instance_class: activity_instance_class,
                activity_items:activity_items,
                activity_instance_groupings: activity_instance_groupings
            } as activity_instance_root
        """

        return match_stmt, activity_instance_root_return

    def _activity_root_match_return_stmt(self):
        match_stmt = """
            MATCH (root)-[ver_rel]->(activity_value:ActivityValue)
            OPTIONAL MATCH (activity_value)-[:REPLACED_BY_ACTIVITY]->(replaced_by_activity:ActivityRoot)
            CALL
            {
                WITH root,activity_value,ver_rel
                WITH *, [(root)-[ver_rel]->(activity_value:ActivityValue)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup) | 
                    {
                        activity_subgroup: head(apoc.coll.sortMulti([(activity_valid_group)<-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue)<-[has_version:HAS_VERSION]-
                            (activity_subgroup_root:ActivitySubGroupRoot) | 
                            {
                                uid:activity_subgroup_root.uid,
                                major_version: toInteger(split(has_version.version,'.')[0]),
                                minor_version: toInteger(split(has_version.version,'.')[1]),
                                name: activity_subgroup_value.name
                            }], ['major_version', 'minor_version'])), 
                        activity_group: head(apoc.coll.sortMulti([(activity_valid_group)-[:IN_GROUP]-(activity_group_value:ActivityGroupValue)<-[has_version:HAS_VERSION]-
                            (activity_group_root:ActivityGroupRoot) | 
                            {
                                uid:activity_group_root.uid,
                                major_version: toInteger(split(has_version.version,'.')[0]),
                                minor_version: toInteger(split(has_version.version,'.')[1]),
                                name: activity_group_value.name
                            }], ['major_version', 'minor_version']))
                    }
                    ] as activity_groupings,
                    head([(library:Library)--(activity_root)--(activity_value)<-[:HAS_SELECTED_ACTIVITY]-(:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value:StudyValue) WHERE library.name="Requested" | study_value.study_id_prefix + "-" + study_value.study_number]) AS requester_study_id
                RETURN activity_groupings, requester_study_id
            }
        """

        activity_root_return = """,
            {
                activity_groupings: activity_groupings,
                replaced_activity_uid: replaced_by_activity.uid,
                requester_study_id: requester_study_id
            } as activity_root
        """

        return match_stmt, activity_root_return

    def _activity_subgroup_root_match_return_stmt(self):
        match_stmt = """
            CALL{
                WITH root
                WITH *,
                [(root)-[:LATEST]->(concept_value)-[:HAS_GROUP]->(activity_valid_group:ActivityValidGroup) |
                    {
                        activity_group:head(apoc.coll.sortMulti([(activity_valid_group)-[:IN_GROUP]-(activity_group_value:ActivityGroupValue)<-[has_version:HAS_VERSION]-
                            (activity_group_root:ActivityGroupRoot) | 
                            {
                                uid:activity_group_root.uid,
                                major_version: toInteger(split(has_version.version,'.')[0]),
                                minor_version: toInteger(split(has_version.version,'.')[1]),
                                name: activity_group_value.name
                            }], ['major_version', 'minor_version']))
                    }] AS activity_groups
                RETURN activity_groups
            }
        """

        activity_subgroups_root_return = """,
            {
                activity_groups: activity_groups
            } as activity_subgroups_root
        """

        return match_stmt, activity_subgroups_root_return

    def _unit_definition_match_return_stmt(self):
        match_stmt = """
            CALL{
                WITH *
                MATCH (root)-[:LATEST]->(:UnitDefinitionValue)-[:HAS_CT_UNIT]->(ctterm_root_unit_definition:CTTermRoot)
                MATCH (ctterm_root_unit_definition)-->(:CTTermNameRoot)-[:LATEST_FINAL]->(ct_name_value:CTTermNameValue)
                RETURN collect(DISTINCT {uid:ctterm_root_unit_definition.uid, name:ct_name_value.name }) as ct_units
            }
            CALL{
                WITH *
                MATCH (root)-[:LATEST]->(:UnitDefinitionValue)-[:HAS_UNIT_SUBSET]-(ct_unit_subset:CTTermRoot)-->(:CTTermNameRoot)-[:LATEST_FINAL]->(name_value:CTTermNameValue)
                return collect(DISTINCT {uid:ct_unit_subset.uid, name:name_value.name})  as unit_subsets
            }
            OPTIONAL MATCH (root)-[:LATEST]->(:UnitDefinitionValue)-[:HAS_CT_DIMENSION]->(ct_dimension:CTTermRoot)
            OPTIONAL MATCH (root)-[:LATEST]->(:UnitDefinitionValue)-[:HAS_UCUM_TERM]->(ucum_term_root:UCUMTermRoot)

        """

        unit_definition_return = """,
            {
                ct_units: ct_units,
                unit_subsets: unit_subsets,
                ct_dimension_uid: ct_dimension.uid,
                ucum_term_uid: ucum_term_root.uid, 
                bool_template: CASE WHEN "TemplateParameterTermValue" in LABELS(value) THEN TRUE else FALSE END 
            } as unit_definition
        """

        return match_stmt, unit_definition_return

    def _only_instances_with_studies(self):
        return f"""
MATCH (root)-->(:SyntaxInstanceValue)<-[:{self.value_class.STUDY_SELECTION_REL_LABEL}]-(:StudySelection)<--(:StudyValue)<-[:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED]-(isr:StudyRoot)
WITH *, COUNT(isr) as cnt
WHERE cnt > 0
        """

    def _activity_subgroup_match_return_stmt(self):
        match_stmt = """
            OPTIONAL MATCH (root)-[:HAS_ACTIVITY_SUBGROUP]->(activity_subgroup_root:ActivitySubGroupRoot)-[:LATEST]->(activity_subgroup_value:ActivitySubGroupValue)
        """

        activity_subgroups_return = """,
            collect(DISTINCT {
                uid: activity_subgroup_root.uid,
                name: activity_subgroup_value.name,
                name_sentence_case: activity_subgroup_value.name_sentence_case
            }) as activity_subgroups
        """

        return match_stmt, activity_subgroups_return

    def _activity_group_match_return_stmt(self):
        match_stmt = """
            OPTIONAL MATCH (root)-[:HAS_ACTIVITY_GROUP]->(activity_group_root:ActivityGroupRoot)-[:LATEST]->(activity_group_value:ActivityGroupValue)
        """

        activity_groups_return = """,
            collect(DISTINCT {
                uid: activity_group_root.uid,
                name: activity_group_value.name,
                name_sentence_case: activity_group_value.name_sentence_case
            }) as activity_groups
        """

        return match_stmt, activity_groups_return

    def _activity_match_return_stmt(self):
        match_stmt = """
            OPTIONAL MATCH (root)-[:HAS_ACTIVITY]->(activity_root:ActivityRoot)-[:LATEST]->(activity_value:ActivityValue)
        """

        activities_return = """,
            collect(DISTINCT {
                uid: activity_root.uid,
                name: activity_value.name,
                name_sentence_case: activity_value.name_sentence_case
            }) as activities
        """

        return match_stmt, activities_return

    def _subcategory_match_return_stmt(self):
        match_stmt = """
            OPTIONAL MATCH (root)-[:HAS_SUBCATEGORY]->(subcategory_root:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(subcategory_ct_term_name_value:CTTermNameValue)
            OPTIONAL MATCH (subcategory_root:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(subcategory_ct_term_attributes_value:CTTermAttributesValue)
        """

        subcategories_return = """,
            collect(DISTINCT {
                term_uid: subcategory_root.uid,
                name: subcategory_ct_term_name_value.name,
                name_sentence_case: subcategory_ct_term_name_value.name_sentence_case,
                code_submission_value: subcategory_ct_term_attributes_value.code_submission_value,
                preferred_term: subcategory_ct_term_attributes_value.preferred_term
            }) as subcategories
        """

        return match_stmt, subcategories_return

    def _category_match_return_stmt(self):
        match_stmt = """
            OPTIONAL MATCH (root)-[:HAS_CATEGORY]->(category_root:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(category_ct_term_name_value:CTTermNameValue)
            OPTIONAL MATCH (category_root:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(category_ct_term_attributes_value:CTTermAttributesValue)
        """

        categories_return = """,
            collect(DISTINCT {
                term_uid: category_root.uid,
                name: category_ct_term_name_value.name,
                name_sentence_case: category_ct_term_name_value.name_sentence_case,
                code_submission_value: category_ct_term_attributes_value.code_submission_value,
                preferred_term: category_ct_term_attributes_value.preferred_term
            }) as categories
        """

        return match_stmt, categories_return

    def _instance_template_match_return_stmt(self):
        if hasattr(self, "template_class"):
            rel_type = (
                "-[:CREATED_FROM]->"
                if "SyntaxPreInstanceRoot"
                in [
                    ith_class.__label__ if hasattr(ith_class, "__label__") else None
                    for ith_class in self.root_class.mro()
                ]
                else f"<-[:{self.root_class.TEMPLATE_REL_LABEL}]-"
            )
            match_stmt = f"""
                CALL {{
                    WITH root, ver_rel
                    OPTIONAL MATCH (root){rel_type}(template_root)-[template_rel:HAS_VERSION]->(template_value)
                    WHERE template_rel.status = "Final" AND datetime(template_rel.start_date) <= datetime(ver_rel.start_date)
                    OPTIONAL MATCH (template_root)<-[:CONTAINS_SYNTAX_TEMPLATE]-(template_library:Library)
                    RETURN template_root, template_value, template_library
                    ORDER BY template_rel.start_date DESC
                    LIMIT 1
                }}
                OPTIONAL MATCH (template_root)-[:HAS_TYPE]->(type_root:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(type_ct_term_name_value:CTTermNameValue)
                OPTIONAL MATCH (type_root)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(type_ct_term_attributes_value:CTTermAttributesValue)
            """

            instance_template_return = """,
                {
                    template_uid: template_root.uid,
                    template_sequence_id: template_root.sequence_id,
                    template_name: template_value.name,
                    template_guidance_text: template_value.guidance_text,
                    template_library_name: template_library.name,
                    term_uid: type_root.uid,
                    name: type_ct_term_name_value.name,
                    name_sentence_case: type_ct_term_name_value.name_sentence_case,
                    code_submission_value: type_ct_term_attributes_value.code_submission_value,
                    preferred_term: type_ct_term_attributes_value.preferred_term
                } as instance_template_return
            """

            return match_stmt, instance_template_return

        return "", ", null as instance_template "

    def _indication_match_return_stmt(self):
        match_stmt = """
            OPTIONAL MATCH (root)-[:HAS_INDICATION]->(indication_root:DictionaryTermRoot)-[:LATEST]-(indication_value:DictionaryTermValue)
        """

        indications_return = """,
            collect(DISTINCT {
                term_uid: indication_root.uid,
                name: indication_value.name
            }) as indications
        """
        return match_stmt, indications_return

    def _template_type_match_return_stmt(self):
        if hasattr(self.root_class, "has_type"):
            match_stmt = """
                OPTIONAL MATCH (root)-[:HAS_TYPE]->(type_root:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(type_ct_term_name_value:CTTermNameValue)
                OPTIONAL MATCH (type_root)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(type_ct_term_attributes_value:CTTermAttributesValue)
            """

            template_type_return = """,
                {
                    term_uid: type_root.uid,
                    name: type_ct_term_name_value.name,
                    name_sentence_case: type_ct_term_name_value.name_sentence_case,
                    code_submission_value: type_ct_term_attributes_value.code_submission_value,
                    preferred_term: type_ct_term_attributes_value.preferred_term
                } as template_type
            """
        else:
            match_stmt = """
                OPTIONAL MATCH (root)-[:CREATED_FROM]->(template_root)-[:HAS_TYPE]->(type_root:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(type_ct_term_name_value:CTTermNameValue)
                OPTIONAL MATCH (type_root)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(type_ct_term_attributes_value:CTTermAttributesValue)
                OPTIONAL MATCH (template_root)-[:LATEST]->(template_value)
            """

            template_type_return = """,
                {
                    term_uid: type_root.uid,
                    name: type_ct_term_name_value.name,
                    name_sentence_case: type_ct_term_name_value.name_sentence_case,
                    code_submission_value: type_ct_term_attributes_value.code_submission_value,
                    preferred_term: type_ct_term_attributes_value.preferred_term
                } as template_type
            """

        return match_stmt, template_type_return
