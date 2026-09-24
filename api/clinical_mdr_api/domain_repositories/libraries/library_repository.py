from typing import MutableMapping

from clinical_mdr_api.domain_repositories.models.generic import Library
from clinical_mdr_api.domains.libraries.library_ar import LibraryAR
from common.exceptions import NotFoundException


class LibraryRepository:
    _cache: MutableMapping[str, LibraryAR | None]

    def __init__(self):
        self._cache = {}

    def library_exists(self, library_name: str) -> bool:
        library_node = Library.nodes.get_or_none(name=library_name)
        return bool(library_node)

    def find_by_name(self, name: str) -> LibraryAR:
        """Returns LibraryAR by doing a db lookup by name,
        otherwise raises NotFoundException if the library does not exist."""
        if name not in self._cache:
            library_node: Library | None = Library.nodes.get_or_none(name=name)

            NotFoundException.raise_if_not(library_node, "Library", name, "Name")

            self._cache[name] = LibraryAR.from_repository_values(
                library_name=library_node.name, is_editable=library_node.is_editable
            )

        return self._cache[name]
