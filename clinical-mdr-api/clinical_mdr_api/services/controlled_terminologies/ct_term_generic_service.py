import abc
from datetime import datetime
from typing import Any, Generic, TypeVar

from neomodel import db
from pydantic import BaseModel

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_generic_repository import (
    CTTermGenericRepository,
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


class CTTermGenericService(Generic[_AggregateRootType], abc.ABC):
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
    def repository(self) -> CTTermGenericRepository[_AggregateRootType]:
        assert self._repos is not None
        return self.repository_interface()

    def non_transactional_get_all_ct_terms(
        self,
        codelist_uid: str | None = None,
        codelist_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
        in_codelist: bool = False,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[BaseModel]:
        self.enforce_codelist_package_library(
            codelist_uid, codelist_name, library, package
        )

        all_ct_terms = self.repository.find_all(
            codelist_uid=codelist_uid,
            codelist_name=codelist_name,
            library_name=library,
            package=package,
            in_codelist=in_codelist,
            total_count=total_count,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
        )

        all_ct_terms.items = [
            self._transform_aggregate_root_to_pydantic_model(ct_term_ar)
            for ct_term_ar in all_ct_terms.items
        ]

        return all_ct_terms

    @db.transaction
    def get_all_ct_terms(
        self,
        codelist_uid: str | None = None,
        codelist_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
        in_codelist: bool = False,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[BaseModel]:
        return self.non_transactional_get_all_ct_terms(
            codelist_uid,
            codelist_name,
            library,
            package,
            in_codelist,
            sort_by,
            page_number,
            page_size,
            filter_by,
            filter_operator,
            total_count,
        )

    def get_distinct_values_for_header(
        self,
        codelist_uid: str | None,
        codelist_name: str | None,
        library: str | None,
        package: str | None,
        field_name: str,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        page_size: int = 10,
    ) -> list[Any]:
        self.enforce_codelist_package_library(
            codelist_uid, codelist_name, library, package
        )

        header_values = self.repository.get_distinct_headers(
            codelist_uid=codelist_uid,
            codelist_name=codelist_name,
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
    def get_term_name_and_attributes_by_codelist_uids(
        self, codelist_uids: list[str]
    ) -> list[Any]:
        (
            items,
            prop_names,
        ) = self.repository.get_term_name_and_attributes_by_codelist_uids(codelist_uids)

        return [dict(zip(prop_names, item)) for item in items]

    @db.transaction
    def get_by_uid(
        self,
        term_uid: str,
        version: str | None = None,
        at_specific_date: datetime | None = None,
        status: str | None = None,
    ) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(
            term_uid=term_uid,
            version=version,
            at_specific_date=at_specific_date,
            status=status,
        )
        return self._transform_aggregate_root_to_pydantic_model(item)

    def _find_by_uid_or_raise_not_found(
        self,
        term_uid: str,
        version: str | None = None,
        at_specific_date: datetime | None = None,
        status: LibraryItemStatus | None = None,
        for_update: bool | None = False,
    ) -> _AggregateRootType:
        item = self.repository.find_by_uid(
            term_uid=term_uid,
            at_specific_date=at_specific_date,
            version=version,
            status=status,
            for_update=for_update,
        )

        NotFoundException.raise_if(
            item is None,
            msg=f"{self.aggregate_class.__name__} with UID '{term_uid}' doesn't exist or there's no version with requested status or version number.",
        )

        return item

    @db.transaction
    def get_version_history(self, term_uid) -> list[BaseModel]:
        if self.version_class is not None:
            all_versions = self.repository.get_all_versions(term_uid)

            NotFoundException.raise_if(
                all_versions is None, self.aggregate_class.__name__, term_uid
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
    def create_new_version(self, term_uid: str) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(term_uid, for_update=True)
        item.create_new_version(author_id=self.author_id)
        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def edit_draft(self, term_uid: str, term_input: BaseModel) -> BaseModel:
        raise NotImplementedError()

    def non_transactional_approve(self, term_uid: str) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(term_uid=term_uid, for_update=True)
        item.approve(author_id=self.author_id)
        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def approve(self, term_uid: str) -> BaseModel:
        return self.non_transactional_approve(term_uid)

    @db.transaction
    def inactivate_final(self, term_uid: str) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(term_uid, for_update=True)

        item.inactivate(author_id=self.author_id)

        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def reactivate_retired(self, term_uid: str) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(term_uid, for_update=True)

        item.reactivate(author_id=self.author_id)

        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def soft_delete(self, term_uid: str) -> None:
        item = self._find_by_uid_or_raise_not_found(term_uid, for_update=True)
        item.soft_delete()
        self.repository.save(item)

    def enforce_codelist_package_library(
        self,
        codelist_uid: str | None,
        codelist_name: str | None,
        library: str | None,
        package: str | None,
    ) -> None:
        NotFoundException.raise_if(
            codelist_uid is not None
            and not self._repos.ct_codelist_attribute_repository.codelist_exists(
                normalize_string(codelist_uid)
            ),
            "CT Codelist",
            codelist_uid,
        )
        NotFoundException.raise_if(
            codelist_name is not None
            and not self._repos.ct_codelist_name_repository.codelist_specific_exists_by_name(
                normalize_string(codelist_name)
            ),
            "CT Codelist Name",
            codelist_name,
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
