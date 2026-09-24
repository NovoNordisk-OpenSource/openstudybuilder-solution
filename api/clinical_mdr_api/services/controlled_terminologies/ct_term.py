from datetime import datetime
from typing import Any, TypeVar

from neomodel import db

from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
    CTTermAttributesVO,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermCodelistVO,
    CTTermNameAR,
    CTTermNameVO,
    CTTermVO,
)
from clinical_mdr_api.domains.controlled_terminologies.utils import TermParentType
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    CTTerm,
    CTTermCodelists,
    CTTermCreateInput,
    CTTermNameAndAttributes,
    CTTermNewCodelist,
    CTTermRelative,
    CTTermRelatives,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import ensure_transaction, is_library_editable
from clinical_mdr_api.services.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term_name import (
    CTTermNameService,
)
from clinical_mdr_api.utils import normalize_string
from common import exceptions
from common.auth.user import user
from common.exceptions import BusinessLogicException, NotFoundException

_AggregateRootType = TypeVar("_AggregateRootType")


class CTTermService:
    _repos: MetaRepository
    author_id: str

    def __init__(self):
        self.author_id = user().id()

        self._repos = MetaRepository(self.author_id)

    def __del__(self):
        self._repos.close()

    @ensure_transaction(db)
    def create(
        self,
        term_input: CTTermCreateInput,
        start_date: datetime | None = None,
        approve: bool = False,
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

        if not start_date:
            start_date = datetime.now()

        BusinessLogicException.raise_if(
            term_input.library_name is not None
            and not self._repos.library_repository.library_exists(
                normalize_string(term_input.library_name)
            ),
            msg=f"Library with Name '{term_input.library_name}' doesn't exist.",
        )

        codelists = []
        for codelist in term_input.codelists:
            ct_codelist_attributes_ar = (
                self._repos.ct_codelist_attribute_repository.find_by_uid(
                    codelist_uid=codelist.codelist_uid
                )
            )
            BusinessLogicException.raise_if(
                ct_codelist_attributes_ar
                and ct_codelist_attributes_ar.item_metadata.status
                is LibraryItemStatus.DRAFT,
                msg=f"Attributes of codelist with UID '{codelist.codelist_uid}' is in DRAFT status, no terms can be added.",
            )

            BusinessLogicException.raise_if(
                ct_codelist_attributes_ar is not None
                and not ct_codelist_attributes_ar.ct_codelist_vo.extensible,
                msg=f"Codelist identified by {codelist.codelist_uid} is not extensible",
            )
            ct_codelist_name_ar = self._repos.ct_codelist_name_repository.find_by_uid(
                codelist_uid=codelist.codelist_uid
            )
            if (
                ct_codelist_name_ar is not None
                and not ct_codelist_name_ar.ct_codelist_vo.is_ordinal
                and codelist.ordinal is not None
            ):
                raise BusinessLogicException(
                    msg=f"Codelist identified by {codelist.codelist_uid} is not ordinal, therefore term ordinal value should be None"
                )
            BusinessLogicException.raise_if(
                ct_codelist_name_ar
                and ct_codelist_name_ar.item_metadata.status is LibraryItemStatus.DRAFT,
                msg=f"Name of codelist with UID '{codelist.codelist_uid}' is in DRAFT status, no terms can be added.",
            )
            codelists.append(
                CTTermCodelistVO(
                    codelist_uid=codelist.codelist_uid,
                    order=codelist.order,
                    ordinal=codelist.ordinal,
                    submission_value=codelist.submission_value,
                    library_name=ct_codelist_name_ar.library.name,
                    codelist_submission_value=ct_codelist_attributes_ar.ct_codelist_vo.submission_value,
                    codelist_name=ct_codelist_name_ar.name,
                    codelist_concept_id=ct_codelist_attributes_ar.uid,
                    start_date=start_date,
                )
            )

        library_vo = LibraryVO.from_input_values_2(
            library_name=term_input.library_name,
            is_library_editable_callback=is_library_editable,
        )

        ct_term_attributes_ar = CTTermAttributesAR.from_input_values(
            author_id=self.author_id,
            ct_term_attributes_vo=CTTermAttributesVO.from_input_values(
                catalogue_names=term_input.catalogue_names,
                preferred_term=term_input.nci_preferred_name,
                definition=term_input.definition,
                concept_id=term_input.concept_id,
                catalogue_exists_callback=self._repos.ct_catalogue_repository.catalogue_exists,
                term_uid=None,
                concept_id_exists_callback=self._repos.ct_term_attributes_repository.entity_exists_by_concept_id,
            ),
            library=library_vo,
            start_date=start_date,
            generate_uid_callback=self._repos.ct_term_attributes_repository.generate_uid,
        )

        if approve is True:
            ct_term_attributes_ar.approve(author_id=self.author_id)

        self._repos.ct_term_attributes_repository.save(ct_term_attributes_ar)

        ts_parameter = term_input.ts_parameter
        ct_term_name_ar = CTTermNameAR.from_input_values(
            author_id=self.author_id,
            ct_term_name_vo=CTTermNameVO.from_input_values(
                name=term_input.sponsor_preferred_name,
                name_sentence_case=term_input.sponsor_preferred_name_sentence_case,
                reference=ts_parameter.reference if ts_parameter else None,
                required_level=(ts_parameter.required_level if ts_parameter else None),
                cardinality=ts_parameter.cardinality if ts_parameter else None,
                notes=ts_parameter.notes if ts_parameter else None,
                osb_field_name=(ts_parameter.osb_field_name if ts_parameter else None),
                osb_page_reference=(
                    ts_parameter.osb_page_reference if ts_parameter else None
                ),
                semantic_data_type_uid=(
                    ts_parameter.semantic_data_type_uid if ts_parameter else None
                ),
                response_codelist_uid=(
                    ts_parameter.response_codelist_uid if ts_parameter else None
                ),
                response_dictionary_uids=(
                    tuple(ts_parameter.response_dictionary_uids)
                    if ts_parameter and ts_parameter.response_dictionary_uids
                    else None
                ),
                valid_null_flavor_term_uids=(
                    tuple(ts_parameter.valid_null_flavor_term_uids)
                    if ts_parameter and ts_parameter.valid_null_flavor_term_uids
                    else None
                ),
            ),
            library=library_vo,
            start_date=start_date,
            generate_uid_callback=lambda: ct_term_attributes_ar.uid,
        )

        if approve is True:
            ct_term_name_ar.approve(author_id=self.author_id)

        self._repos.ct_term_name_repository.save(ct_term_name_ar)

        for cl in codelists:
            self._repos.ct_codelist_attribute_repository.add_term(
                codelist_uid=cl.codelist_uid,
                term_uid=ct_term_attributes_ar.uid,
                author_id=self.author_id,
                order=cl.order,
                submission_value=cl.submission_value,
                ordinal=cl.ordinal,
            )
        codelists_vo = CTTermVO(codelists, [])

        return CTTerm.from_ct_term_ars(
            ct_term_name_ar, ct_term_attributes_ar, codelists_vo
        )

    def get_all_terms(
        self,
        codelist_uid: str | None,
        codelist_name: str | None,
        library: str | None,
        package: str | None,
        is_sponsor: bool = False,
        include_removed_terms: bool = False,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        include_ts_parameters: bool = True,
    ) -> GenericFilteringReturn[CTTermNameAndAttributes]:
        self.enforce_codelist_package_library(
            codelist_uid, codelist_name, library, package
        )

        all_aggregated_terms, total = (
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
                include_ts_parameters=include_ts_parameters,
            )
        )

        items = [
            CTTermNameAndAttributes.from_ct_term_ars(
                ct_term_name_ar=term_name_ar,
                ct_term_attributes_ar=term_attributes_ar,
                ct_term_codelists=ct_term_codelists,
                include_ts_parameters=include_ts_parameters,
            )
            for term_name_ar, term_attributes_ar, ct_term_codelists in all_aggregated_terms
        ]

        return GenericFilteringReturn(items=items, total=total)

    def get_distinct_values_for_header(
        self,
        codelist_uid: str | None,
        codelist_name: str | None,
        library: str | None,
        package: str | None,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
        lite: bool = False,
    ) -> list[Any]:
        self.enforce_codelist_package_library(
            codelist_uid, codelist_name, library, package
        )

        if lite:
            header_values = (
                self._repos.ct_term_aggregated_repository.get_distinct_headers_lite(
                    codelist_uid=codelist_uid,
                    codelist_name=codelist_name,
                    library=library,
                    package=package,
                    field_name=field_name,
                    search_string=search_string,
                    filter_by=filter_by,
                    page_size=page_size,
                )
            )
        else:
            header_values = (
                self._repos.ct_term_aggregated_repository.get_distinct_headers(
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
            )

        return header_values

    def add_parent(
        self, term_uid: str, parent_uid: str, relationship_type: TermParentType
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

        self._repos.ct_term_attributes_repository.add_parent(
            term_uid=term_uid,
            parent_uid=parent_uid,
            relationship_type=relationship_type,
        )

        ct_term_attributes_ar = self._repos.ct_term_attributes_repository.find_by_uid(
            term_uid=term_uid
        )
        ct_term_name_ar = self._repos.ct_term_name_repository.find_by_uid(
            term_uid=term_uid
        )
        ct_term_codelists = (
            self._repos.ct_term_aggregated_repository.find_term_codelists(term_uid)
        )
        codelist_vos = [
            CTTermCodelistVO(
                codelist_uid=codelist.codelist_uid,
                order=codelist.order,
                ordinal=codelist.ordinal,
                submission_value=codelist.submission_value,
                library_name=codelist.library_name,
                codelist_submission_value=codelist.codelist_submission_value,
                codelist_name=codelist.codelist_name,
                codelist_concept_id=codelist.codelist_concept_id,
                start_date=codelist.start_date,
            )
            for codelist in ct_term_codelists
        ]
        catalogue_names = ct_term_attributes_ar.ct_term_vo.catalogue_names or []

        codelists = CTTermVO(codelist_vos, catalogue_names)
        return CTTerm.from_ct_term_ars(
            ct_term_name_ar=ct_term_name_ar,
            ct_term_attributes_ar=ct_term_attributes_ar,
            ct_term_codelists=codelists,
        )

    def remove_parent(
        self, term_uid: str, parent_uid: str, relationship_type: TermParentType
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

        self._repos.ct_term_attributes_repository.remove_parent(
            term_uid=term_uid,
            parent_uid=parent_uid,
            relationship_type=relationship_type,
        )

        ct_term_attributes_ar = self._repos.ct_term_attributes_repository.find_by_uid(
            term_uid=term_uid
        )
        ct_term_name_ar = self._repos.ct_term_name_repository.find_by_uid(
            term_uid=term_uid
        )
        ct_term_codelists = (
            self._repos.ct_term_aggregated_repository.find_term_codelists(term_uid)
        )
        codelist_vos = [
            CTTermCodelistVO(
                codelist_uid=codelist.codelist_uid,
                order=codelist.order,
                ordinal=codelist.ordinal,
                submission_value=codelist.submission_value,
                library_name=codelist.library_name,
                codelist_submission_value=codelist.codelist_submission_value,
                codelist_name=codelist.codelist_name,
                codelist_concept_id=codelist.codelist_concept_id,
                start_date=codelist.start_date,
            )
            for codelist in ct_term_codelists
        ]
        catalogue_names = ct_term_attributes_ar.ct_term_vo.catalogue_names or []

        codelists = CTTermVO(codelist_vos, catalogue_names)
        return CTTerm.from_ct_term_ars(
            ct_term_name_ar=ct_term_name_ar,
            ct_term_attributes_ar=ct_term_attributes_ar,
            ct_term_codelists=codelists,
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

    def set_new_order_and_submission_value(
        self,
        term_uid: str,
        codelist_uid: str,
        new_order: int,
        new_submission_value: str,
    ) -> CTTermNewCodelist:
        self._repos.ct_term_name_repository.update_term_codelist(
            term_uid=term_uid,
            codelist_uid=codelist_uid,
            order=new_order,
            submission_value=new_submission_value,
            author=self.author_id,
        )
        return CTTermNewCodelist(
            codelist_uid=codelist_uid,
            order=new_order,
            submission_value=new_submission_value,
        )

    def get_codelists_by_uid(
        self,
        term_uid: str,
        at_specific_date_time: datetime | None = None,
    ) -> CTTermCodelists:
        ct_term_codelists = (
            self._repos.ct_term_aggregated_repository.find_term_codelists(
                term_uid,
                at_specific_date_time=at_specific_date_time,
            )
        )

        return CTTermCodelists.from_ct_term_codelists(
            term_uid=term_uid, ct_term_codelists=ct_term_codelists
        )

    def get_parents_by_uid(
        self,
        term_uid: str,
    ) -> CTTermRelatives:
        ct_term_root = CTTermRoot.nodes.filter(uid=term_uid).get_or_none()
        if ct_term_root is None:
            raise exceptions.BusinessLogicException(
                msg=f"There is no CTTermRoot identified by provided term_uid ({term_uid})"
            )
        has_parent_types = ct_term_root.has_parent_type.all()
        has_parent_subtypes = ct_term_root.has_parent_subtype.all()
        has_predecessors = ct_term_root.has_predecessor.all()
        is_specialization_of = ct_term_root.is_specialization_of.all()

        parent_types_for = ct_term_root.parent_type_for.all()
        parent_subtypes_for = ct_term_root.parent_subtype_for.all()
        predecessors_for = ct_term_root.predecessor_for.all()
        has_specialization = ct_term_root.has_specialization.all()

        attributes_service = CTTermAttributesService()
        names_service = CTTermNameService()

        parents: list[CTTermRelative] = []
        children: list[CTTermRelative] = []
        related_term_details = (
            (has_parent_types, TermParentType.PARENT_TYPE.value, parents),
            (has_parent_subtypes, TermParentType.PARENT_SUB_TYPE.value, parents),
            (has_predecessors, TermParentType.PREDECESSOR.value, parents),
            (is_specialization_of, TermParentType.SPECIALIZATION.value, parents),
            (parent_types_for, TermParentType.PARENT_TYPE.value, children),
            (parent_subtypes_for, TermParentType.PARENT_SUB_TYPE.value, children),
            (predecessors_for, TermParentType.PREDECESSOR.value, children),
            (has_specialization, TermParentType.SPECIALIZATION.value, children),
        )
        for term_nodes, reltype, term_list in related_term_details:
            for term in term_nodes:
                attrs = attributes_service.get_by_uid(term.uid)
                name = names_service.get_by_uid(term.uid)
                term_list.append(
                    CTTermRelative(
                        relationship_type=reltype, name=name, attributes=attrs
                    )
                )

        return CTTermRelatives.from_related_terms(
            term_uid=term_uid, ct_term_parents=parents, ct_term_children=children
        )
