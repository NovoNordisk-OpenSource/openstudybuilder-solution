from datetime import datetime
from typing import Any, TypeVar

from neomodel import db

from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
    CTTermAttributesVO,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermCodelistVO,
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domains.controlled_terminologies.utils import TermParentType
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    CTTerm,
    CTTermCreateInput,
    CTTermNameAndAttributes,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import is_library_editable
from clinical_mdr_api.utils import normalize_string
from common.auth.user import user
from common.exceptions import BusinessLogicException, NotFoundException

_AggregateRootType = TypeVar("_AggregateRootType")


class CTTermService:
    _repos: MetaRepository
    author_id: str | None

    def __init__(self):
        self.author_id = user().id()

        self._repos = MetaRepository(self.author_id)

    def __del__(self):
        self._repos.close()

    def non_transactional_create(
        self, term_input: CTTermCreateInput, start_date: datetime | None = None
    ) -> CTTerm:
        """
        Method creates CTTermAttributesAR and saves that object to the database.
        When saving CTTermAttributesAR - CTTermRoot node is created that will become a root node for
        CTTermAttributes and CTTermName nodes.
        The uid for the CTTermRoot is assigned when the CTTermAttributesAR is being created.
        Created CTTermRoot uid is then passed to the CTTermNameAR.
        The uid of CTTermRoot node is used by CTTermName repository to create a
        relationship from CTTermRoot to CTTermName node when saving a CTTermNameAR.
        :param term_input:
        :return term:CTTerm
        """

        BusinessLogicException.raise_if(
            term_input.library_name is not None
            and not self._repos.library_repository.library_exists(
                normalize_string(term_input.library_name)
            ),
            msg=f"Library with Name '{term_input.library_name}' doesn't exist.",
        )

        ct_codelist_attributes_ar = (
            self._repos.ct_codelist_attribute_repository.find_by_uid(
                codelist_uid=term_input.codelist_uid
            )
        )

        BusinessLogicException.raise_if(
            term_input.codelist_uid is not None and ct_codelist_attributes_ar is None,
            msg=f"Codelist with UID '{term_input.codelist_uid}' does not exist.",
        )

        BusinessLogicException.raise_if(
            ct_codelist_attributes_ar is not None
            and not ct_codelist_attributes_ar.ct_codelist_vo.extensible,
            msg=f"Codelist with UID '{term_input.codelist_uid}' is not extensible.",
        )

        ct_codelist_name_ar = self._repos.ct_codelist_name_repository.find_by_uid(
            codelist_uid=term_input.codelist_uid
        )
        BusinessLogicException.raise_if(
            ct_codelist_name_ar
            and ct_codelist_name_ar.item_metadata.status is LibraryItemStatus.DRAFT,
            msg=f"Until Codelist with UID '{term_input.codelist_uid}' is in DRAFT status, no Terms can be added.",
        )

        library_vo = LibraryVO.from_input_values_2(
            library_name=term_input.library_name,
            is_library_editable_callback=is_library_editable,
        )

        ct_term_attributes_ar = CTTermAttributesAR.from_input_values(
            author_id=self.author_id,
            ct_term_attributes_vo=CTTermAttributesVO.from_input_values(
                codelists=[
                    CTTermCodelistVO(
                        codelist_uid=term_input.codelist_uid,
                        order=term_input.order,
                        library_name=ct_codelist_name_ar.library.name,
                    )
                ],
                catalogue_name=term_input.catalogue_name,
                code_submission_value=term_input.code_submission_value,
                name_submission_value=term_input.name_submission_value,
                preferred_term=term_input.nci_preferred_name,
                definition=term_input.definition,
                codelist_exists_callback=self._repos.ct_codelist_attribute_repository.codelist_exists,
                catalogue_exists_callback=self._repos.ct_catalogue_repository.catalogue_exists,
                term_exists_by_name_callback=self._repos.ct_term_attributes_repository.term_specific_exists_by_name,
                term_exists_by_code_submission_value_callback=(
                    self._repos.ct_term_attributes_repository.term_attributes_exists_by_code_submission_value
                ),
            ),
            library=library_vo,
            start_date=start_date,
            generate_uid_callback=self._repos.ct_term_attributes_repository.generate_uid,
        )

        self._repos.ct_term_attributes_repository.save(ct_term_attributes_ar)

        ct_term_name_ar = CTTermNameAR.from_input_values(
            author_id=self.author_id,
            ct_term_name_vo=CTTermNameVO.from_input_values(
                codelists=[
                    CTTermCodelistVO(
                        codelist_uid=term_input.codelist_uid,
                        order=term_input.order,
                        library_name=ct_codelist_name_ar.library.name,
                    )
                ],
                catalogue_name=term_input.catalogue_name,
                name=term_input.sponsor_preferred_name,
                name_sentence_case=term_input.sponsor_preferred_name_sentence_case,
                codelist_exists_callback=self._repos.ct_codelist_attribute_repository.codelist_exists,
                catalogue_exists_callback=self._repos.ct_catalogue_repository.catalogue_exists,
                term_exists_by_name_in_codelists_callback=self._repos.ct_term_name_repository.term_specific_exists_by_name_in_codelists,
            ),
            library=library_vo,
            start_date=start_date,
            generate_uid_callback=lambda: ct_term_attributes_ar.uid,
        )

        self._repos.ct_term_name_repository.save(ct_term_name_ar)

        return CTTerm.from_ct_term_ars(ct_term_name_ar, ct_term_attributes_ar)

    @db.transaction
    def create(
        self, term_input: CTTermCreateInput, start_date: datetime | None = None
    ) -> CTTerm:
        return self.non_transactional_create(term_input, start_date=start_date)

    def get_all_terms(
        self,
        codelist_uid: str | None,
        codelist_name: str | None,
        library: str | None,
        package: str | None,
        is_sponsor: bool = False,
        include_removed_terms: bool = False,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[CTTermNameAndAttributes]:
        self.enforce_codelist_package_library(
            codelist_uid, codelist_name, library, package
        )

        all_aggregated_terms = (
            self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
                codelist_uid=codelist_uid,
                codelist_name=codelist_name,
                library=library,
                package=package,
                is_sponsor=is_sponsor,
                include_removed_terms=include_removed_terms,
                total_count=total_count,
                sort_by=sort_by,
                filter_by=filter_by,
                filter_operator=filter_operator,
                page_number=page_number,
                page_size=page_size,
            )
        )

        all_aggregated_terms.items = [
            CTTermNameAndAttributes.from_ct_term_ars(
                ct_term_name_ar=term_name_ar, ct_term_attributes_ar=term_attributes_ar
            )
            for term_name_ar, term_attributes_ar in all_aggregated_terms.items
        ]

        return all_aggregated_terms

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

        header_values = self._repos.ct_term_aggregated_repository.get_distinct_headers(
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

    def add_parent(
        self, term_uid: str, parent_uid: str, relationship_type: str
    ) -> CTTerm:
        NotFoundException.raise_if_not(
            self._repos.ct_term_name_repository.term_exists(normalize_string(term_uid)),
            "CT Term",
            term_uid,
        )
        NotFoundException.raise_if_not(
            self._repos.ct_term_name_repository.term_exists(
                normalize_string(parent_uid)
            ),
            "CT Term",
            parent_uid,
        )

        relationship_type = relationship_type.lower()
        if relationship_type == "type":
            rel_type = TermParentType.PARENT_TYPE
        elif relationship_type == "subtype":
            rel_type = TermParentType.PARENT_SUB_TYPE
        else:
            raise BusinessLogicException(
                msg=f"The following type '{relationship_type}' isn't valid relationship type."
            )

        self._repos.ct_term_attributes_repository.add_parent(
            term_uid=term_uid, parent_uid=parent_uid, relationship_type=rel_type
        )

        ct_term_attributes_ar = self._repos.ct_term_attributes_repository.find_by_uid(
            term_uid=term_uid
        )
        ct_term_name_ar = self._repos.ct_term_name_repository.find_by_uid(
            term_uid=term_uid
        )
        return CTTerm.from_ct_term_ars(
            ct_term_name_ar=ct_term_name_ar, ct_term_attributes_ar=ct_term_attributes_ar
        )

    def remove_parent(
        self, term_uid: str, parent_uid: str, relationship_type: str
    ) -> CTTerm:
        NotFoundException.raise_if_not(
            self._repos.ct_term_name_repository.term_exists(normalize_string(term_uid)),
            "CT Term",
            term_uid,
        )
        NotFoundException.raise_if_not(
            self._repos.ct_term_name_repository.term_exists(
                normalize_string(parent_uid)
            ),
            "CT Term",
            parent_uid,
        )

        if relationship_type == "type":
            rel_type = TermParentType.PARENT_TYPE
        elif relationship_type == "subtype":
            rel_type = TermParentType.PARENT_SUB_TYPE
        else:
            raise BusinessLogicException(
                msg=f"The following type '{relationship_type}' isn't valid relationship type."
            )

        self._repos.ct_term_attributes_repository.remove_parent(
            term_uid=term_uid, parent_uid=parent_uid, relationship_type=rel_type
        )

        ct_term_attributes_ar = self._repos.ct_term_attributes_repository.find_by_uid(
            term_uid=term_uid
        )
        ct_term_name_ar = self._repos.ct_term_name_repository.find_by_uid(
            term_uid=term_uid
        )
        return CTTerm.from_ct_term_ars(
            ct_term_name_ar=ct_term_name_ar, ct_term_attributes_ar=ct_term_attributes_ar
        )

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
            "CT Codelist Attributes",
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

    def set_new_order(self, term_uid: str, codelist_uid: str, new_order: int) -> CTTerm:
        ct_codelist_name_ar = self._repos.ct_codelist_name_repository.find_by_uid(
            codelist_uid=codelist_uid
        )

        NotFoundException.raise_if_not(
            ct_codelist_name_ar, "CT Codelist Name", codelist_uid
        )

        ct_term_name_ar = self._repos.ct_term_name_repository.find_by_uid(
            term_uid, for_update=True
        )

        NotFoundException.raise_if(ct_term_name_ar is None, "CT Term", term_uid)

        ct_term_name_ar.set_new_order(
            codelist_uid=codelist_uid,
            new_order=new_order,
            codelist_library_name=ct_codelist_name_ar.library.name,
        )

        self._repos.ct_term_name_repository.save(ct_term_name_ar)

        ct_term_attributes_ar = self._repos.ct_term_attributes_repository.find_by_uid(
            term_uid=term_uid
        )
        return CTTerm.from_ct_term_ars(
            ct_term_name_ar=ct_term_name_ar, ct_term_attributes_ar=ct_term_attributes_ar
        )
