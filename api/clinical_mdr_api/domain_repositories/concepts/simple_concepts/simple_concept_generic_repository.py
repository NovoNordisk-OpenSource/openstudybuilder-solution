from abc import ABC
from typing import TypeVar

from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemMetadataVO

_AggregateRootType = TypeVar("_AggregateRootType")


class SimpleConceptGenericRepository(ConceptGenericRepository[_AggregateRootType], ABC):
    def _create(self, item: _AggregateRootType) -> _AggregateRootType:
        relation_data: LibraryItemMetadataVO = item.item_metadata
        root = self.root_class.nodes.get_or_none(uid=item.uid)

        # try to find an existing simple concept root node with given uid
        if root is None:
            root = self.root_class(uid=item.uid)  # type: ignore[call-overload]
            self._db_save_node(root)

            value = self._create_new_value_node(ar=item)
            self._db_save_node(value)

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
