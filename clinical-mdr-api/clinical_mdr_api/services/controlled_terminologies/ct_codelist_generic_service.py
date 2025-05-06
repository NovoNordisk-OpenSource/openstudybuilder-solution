import abc
from datetime import datetime
from typing import Any, Generic, TypeVar

from neomodel import db
from pydantic import BaseModel

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_generic_repository import (
    CTCodelistGenericRepository,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import calculate_diffs
from clinical_mdr_api.utils import normalize_string
from common.auth.user import user
from common.exceptions import NotFoundException

_AggregateRootType = TypeVar("_AggregateRootType")


class CTCodelistGenericService(Generic[_AggregateRootType], abc.ABC):
    @abc.abstractmethod
    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: _AggregateRootType
    ) -> BaseModel:
        raise NotImplementedError

    def get_input_or_previous_property(
        self, input_property: Any, previous_property: Any
    ):
        return input_property if input_property is not None else previous_property

    aggregate_class: type
    version_class: type
    repository_interface: type
    _repos: MetaRepository
    author_id: str | None

    def __init__(self):
        self.author_id = user().id()
        self._repos = MetaRepository(self.author_id)

    def __del__(self):
        self._repos.close()

    @property
    def repository(self) -> CTCodelistGenericRepository[_AggregateRootType]:
        assert self._repos is not None
        return self.repository_interface()

    @db.transaction
    def get_all_ct_codelists(
        self,
        catalogue_name: str | None,
        library: str | None,
        package: str | None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[BaseModel]:
        self.enforce_catalogue_library_package(catalogue_name, library, package)

        all_ct_codelists = self.repository.find_all(
            catalogue_name=catalogue_name,
            library_name=library,
            package=package,
            total_count=total_count,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
        )

        all_ct_codelists.items = [
            self._transform_aggregate_root_to_pydantic_model(ct_codelist_ar)
            for ct_codelist_ar in all_ct_codelists.items
        ]
        return all_ct_codelists

    def get_distinct_values_for_header(
        self,
        catalogue_name: str | None,
        library: str | None,
        package: str | None,
        field_name: str,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        page_size: int = 10,
    ) -> list[Any]:
        self.enforce_catalogue_library_package(catalogue_name, library, package)

        header_values = self.repository.get_distinct_headers(
            catalogue_name=catalogue_name,
            library=library,
            package=package,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )

        return header_values

    @db.transaction
    def get_by_uid(
        self,
        codelist_uid: str,
        version: str | None = None,
        at_specific_date: datetime | None = None,
        status: str | None = None,
    ) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(
            codelist_uid=codelist_uid,
            version=version,
            at_specific_date=at_specific_date,
            status=status,
        )
        return self._transform_aggregate_root_to_pydantic_model(item)

    def _find_by_uid_or_raise_not_found(
        self,
        codelist_uid: str,
        version: str | None = None,
        at_specific_date: datetime | None = None,
        status: LibraryItemStatus | None = None,
        for_update: bool | None = False,
    ) -> _AggregateRootType:
        item = self.repository.find_by_uid(
            codelist_uid=codelist_uid,
            at_specific_date=at_specific_date,
            version=version,
            status=status,
            for_update=for_update,
        )

        NotFoundException.raise_if(
            item is None,
            msg=f"{self.aggregate_class.__name__} with UID '{codelist_uid}' doesn't exist or there's no version with requested status or version number.",
        )

        return item

    @db.transaction
    def get_version_history(self, codelist_uid) -> list[BaseModel]:
        if self.version_class is not None:
            all_versions = self.repository.get_all_versions(codelist_uid)

            NotFoundException.raise_if(
                all_versions is None, self.aggregate_class.__name__, codelist_uid
            )

            versions = [
                self._transform_aggregate_root_to_pydantic_model(
                    codelist_ar
                ).model_dump()
                for codelist_ar in all_versions
            ]
            return calculate_diffs(versions, self.version_class)
        return []

    @db.transaction
    def create_new_version(self, codelist_uid: str) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(codelist_uid, for_update=True)
        item.create_new_version(author_id=self.author_id)
        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @abc.abstractmethod
    def edit_draft(self, codelist_uid: str, codelist_input: BaseModel) -> BaseModel:
        raise NotImplementedError()

    def non_transactional_approve(self, codelist_uid: str) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(
            codelist_uid=codelist_uid, for_update=True
        )
        item.approve(author_id=self.author_id)
        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def approve(self, codelist_uid: str) -> BaseModel:
        return self.non_transactional_approve(codelist_uid)

    def enforce_catalogue_library_package(
        self,
        catalogue_name: str | None,
        library: str | None,
        package: str | None,
    ):
        NotFoundException.raise_if(
            catalogue_name is not None
            and not self._repos.ct_catalogue_repository.catalogue_exists(
                normalize_string(catalogue_name)
            ),
            "Catalogue",
            catalogue_name,
            "Name",
        )
        NotFoundException.raise_if(
            library is not None
            and not self._repos.library_repository.library_exists(
                normalize_string(library)
            ),
            "Library",
            library,
            "Name",
        )
        NotFoundException.raise_if(
            package is not None
            and not self._repos.ct_package_repository.package_exists(
                normalize_string(package)
            ),
            "Package",
            package,
            "Name",
        )
