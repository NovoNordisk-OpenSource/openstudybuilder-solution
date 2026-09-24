import abc
from datetime import datetime
from typing import Generic, Iterable, TypeVar

from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus

_AggregateRootType = TypeVar("_AggregateRootType")


class GenericRepository(Generic[_AggregateRootType], abc.ABC):
    """
    Generic repository class with definition of necessary actions that
    library versioned objects repository have to support
    """

    @abc.abstractmethod
    def find_all(
        self,
        *,
        status: LibraryItemStatus | None = None,
        library_name: str | None = None,
    ) -> Iterable[_AggregateRootType]:
        raise NotImplementedError()

    @abc.abstractmethod
    def find_by_uid_2(
        self,
        uid: str,
        *,
        version: str | None = None,
        status: LibraryItemStatus | None = None,
        at_specific_date: datetime | None = None,
        for_update: bool = False,
    ) -> _AggregateRootType | None:
        raise NotImplementedError()

    @abc.abstractmethod
    def save(self, item: _AggregateRootType) -> None:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def author_id(self) -> str | None:
        raise NotImplementedError()

    @author_id.setter
    @abc.abstractmethod
    def author_id(self, author_id: str) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_all_versions_2(
        self, uid: str, return_study_count: bool = False
    ) -> Iterable[_AggregateRootType]:
        raise NotImplementedError()

    @abc.abstractmethod
    def check_exists_by_name(self, name: str) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def check_exists_final_version(self, uid: str) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def generate_uid_callback(self):
        raise NotImplementedError

    @abc.abstractmethod
    def close(self) -> None:
        pass
