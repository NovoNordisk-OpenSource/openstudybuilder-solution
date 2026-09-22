from datetime import datetime
from typing import Any, TypeVar

from neomodel import db

from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCodelistRoot,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesAR,
    CTCodelistAttributesVO,
    CTPairedCodelists,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameAR,
    CTCodelistNameVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import (
    CTCodelist,
    CTCodelistCompact,
    CTCodelistCreateInput,
    CTCodelistNameAndAttributes,
    CTCodelistPaired,
    CTCodelistPairedInput,
    CTCodelistTerm,
    CTPairedCodelistCreateInput,
    CTPairedCodelistInfo,
    CTPairedCodelistTerm,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import ensure_transaction, is_library_editable
from clinical_mdr_api.services.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameService,
)
from clinical_mdr_api.utils import normalize_string
from common.auth.user import user
from common.exceptions import (
    AlreadyExistsException,
    BusinessLogicException,
    NotFoundException,
)

_AggregateRootType = TypeVar("_AggregateRootType")


def _paired_codelist_info_from(
    paired: CTPairedCodelists,
) -> CTPairedCodelistInfo | None:
    # Precedence (codes wins over names) must stay in sync with the
    # paired_codelist_uid/paired_codelist_name coalesce in
    # CTCodelistAggregatedRepository.generic_final_alias_clause, which sorts/filters
    # the codelists listing by the same `paired_codelist` field this builds.
    if paired.paired_codes_codelist_uid:
        return CTPairedCodelistInfo(
            uid=paired.paired_codes_codelist_uid, name=paired.paired_codes_codelist_name
        )
    if paired.paired_names_codelist_uid:
        return CTPairedCodelistInfo(
            uid=paired.paired_names_codelist_uid, name=paired.paired_names_codelist_name
        )
    return None


class CTCodelistService:
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
        codelist_input: CTCodelistCreateInput,
        start_date: datetime | None = None,
        approve: bool = False,
    ) -> CTCodelist:
        """
        Method creates CTCodelistAttributesAR and saves that object to the database.
        When saving CTCodelistAttributesAR - CTCodelistRoot node is created that will become a root node for
        CTCodelistAttributes and CTCodelistName nodes.
        The uid for the CTCodelistRoot is assigned when the CTCodelistAttributesAR is being created.
        Created CTCodelistRoot uid is then passed to the CTCodelistNameAR.
        The uid of CTCodelistRoot node is used by CTCodelistName repository to create a
        relationship from CTCodelistRoot to CTCodelistName node when saving a CTCodelistNameAR.
        If terms are provided then the codelist will be approved and the terms will be connected to the codelist.
        When no terms are provided the codelist is created in draft state.
        :param codelist_input:
        :return codelist:CTCodelist
        """

        BusinessLogicException.raise_if_not(
            self._repos.library_repository.library_exists(
                normalize_string(codelist_input.library_name)
            ),
            msg=f"Library with Name '{codelist_input.library_name}' doesn't exist.",
        )

        library_vo = LibraryVO.from_input_values_2(
            library_name=codelist_input.library_name,
            is_library_editable_callback=is_library_editable,
        )

        ct_codelist_attributes_ar = CTCodelistAttributesAR.from_input_values(
            author_id=self.author_id,
            ct_codelist_attributes_vo=CTCodelistAttributesVO.from_input_values(
                name=codelist_input.name,
                parent_codelist_uid=codelist_input.parent_codelist_uid,
                catalogue_names=codelist_input.catalogue_names,
                submission_value=codelist_input.submission_value,
                preferred_term=codelist_input.nci_preferred_name,
                definition=codelist_input.definition,
                extensible=codelist_input.extensible,
                catalogue_exists_callback=self._repos.ct_catalogue_repository.catalogue_exists,
                codelist_exists_by_uid_callback=self._repos.ct_codelist_attribute_repository.codelist_specific_exists_by_uid,
                codelist_exists_by_name_callback=self._repos.ct_codelist_attribute_repository.codelist_specific_exists_by_name,
                codelist_exists_by_submission_value_callback=(
                    self._repos.ct_codelist_attribute_repository.codelist_attributes_exists_by_submission_value
                ),
            ),
            library=library_vo,
            start_date=start_date,
            generate_uid_callback=self._repos.ct_codelist_attribute_repository.generate_uid,
        )

        if codelist_input.terms or approve is True:
            ct_codelist_attributes_ar.approve(author_id=self.author_id)

        self._repos.ct_codelist_attribute_repository.save(ct_codelist_attributes_ar)

        # Link to paired codelist if provided
        if codelist_input.paired_codes_codelist_uid:
            BusinessLogicException.raise_if_not(
                self._repos.ct_codelist_attribute_repository.codelist_specific_exists_by_uid(
                    codelist_input.paired_codes_codelist_uid
                ),
                msg=f"The given paired codes codelist with UID '{codelist_input.paired_codes_codelist_uid}' doesn't exist.",
            )
            self._repos.ct_codelist_aggregated_repository.merge_link_to_codes_codelist(
                ct_codelist_attributes_ar.uid,
                codelist_input.paired_codes_codelist_uid,
            )
        if codelist_input.paired_names_codelist_uid:
            BusinessLogicException.raise_if_not(
                self._repos.ct_codelist_attribute_repository.codelist_specific_exists_by_uid(
                    codelist_input.paired_names_codelist_uid
                ),
                msg=f"The given paired names codelist with UID '{codelist_input.paired_names_codelist_uid}' doesn't exist.",
            )
            self._repos.ct_codelist_aggregated_repository.merge_link_to_codes_codelist(
                codelist_input.paired_names_codelist_uid,
                ct_codelist_attributes_ar.uid,
            )

        ct_codelist_name_ar = CTCodelistNameAR.from_input_values(
            author_id=self.author_id,
            ct_codelist_name_vo=CTCodelistNameVO.from_input_values(
                name=codelist_input.sponsor_preferred_name,
                catalogue_names=codelist_input.catalogue_names,
                is_template_parameter=codelist_input.template_parameter,
                is_ordinal=codelist_input.is_ordinal,
                codelist_type=codelist_input.codelist_type,
                catalogue_exists_callback=self._repos.ct_catalogue_repository.catalogue_exists,
                codelist_exists_by_name_callback=self._repos.ct_codelist_name_repository.codelist_specific_exists_by_name,
            ),
            library=library_vo,
            start_date=start_date,
            generate_uid_callback=lambda: ct_codelist_attributes_ar.uid,
        )

        if approve is True:
            ct_codelist_name_ar.approve(author_id=self.author_id)

        self._repos.ct_codelist_name_repository.save(ct_codelist_name_ar)

        if codelist_input.terms:
            parent_codelist_uid = (
                ct_codelist_attributes_ar.ct_codelist_vo.parent_codelist_uid
            )

            term_uids = [term.term_uid for term in codelist_input.terms]

            if parent_codelist_uid:
                sub_codelist_with_given_terms = (
                    self.get_sub_codelists_that_have_given_terms(
                        parent_codelist_uid, term_uids
                    )
                )

                AlreadyExistsException.raise_if(
                    sub_codelist_with_given_terms.items,
                    msg=f"""Sub codelists with these terms already exist.
                        Codelist UIDs ({[item.codelist_uid for item in sub_codelist_with_given_terms.items]})""",
                )

            for term in codelist_input.terms:
                BusinessLogicException.raise_if(
                    parent_codelist_uid
                    and len(
                        self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
                            filter_by={
                                "codelists.codelist_uid": {
                                    "v": [parent_codelist_uid],
                                    "op": "eq",
                                },
                                "term_uid": {"v": [term.term_uid], "op": "eq"},
                            }
                        )[
                            0
                        ]
                    )
                    <= 0,
                    msg=f"Term with UID '{term.term_uid}' isn't in use by Parent Codelist with UID '{parent_codelist_uid}'.",
                )

                self._repos.ct_codelist_attribute_repository.add_term(
                    codelist_uid=ct_codelist_attributes_ar.uid,
                    term_uid=term.term_uid,
                    author_id=self.author_id,
                    order=term.order,
                    submission_value=term.submission_value,
                    ordinal=term.ordinal,
                )

        if ct_codelist_name_ar is None or ct_codelist_attributes_ar is None:
            raise ValueError("CodelistNameAR or CodelistAttributesAR is None.")

        return CTCodelist.from_ct_codelist_ar(
            ct_codelist_name_ar,
            ct_codelist_attributes_ar,
            paired_codes_codelist_uid=codelist_input.paired_codes_codelist_uid,
            paired_names_codelist_uid=codelist_input.paired_names_codelist_uid,
        )

    def create_paired_codelists(
        self,
        paired_codelist_input: CTPairedCodelistCreateInput,
    ) -> CTCodelistPaired:
        names_codelist_input = CTCodelistCreateInput(
            catalogue_names=paired_codelist_input.catalogue_names,
            name=paired_codelist_input.name_information.name,
            submission_value=paired_codelist_input.name_information.submission_value,
            nci_preferred_name=paired_codelist_input.name_information.nci_preferred_name,
            definition=paired_codelist_input.name_information.definition,
            extensible=paired_codelist_input.extensible,
            is_ordinal=paired_codelist_input.is_ordinal,
            codelist_type=paired_codelist_input.codelist_type,
            sponsor_preferred_name=paired_codelist_input.name_information.sponsor_preferred_name,
            template_parameter=paired_codelist_input.template_parameter,
            parent_codelist_uid=paired_codelist_input.parent_codelist_uid,
            terms=[],
            library_name=paired_codelist_input.library_name,
        )
        codes_codelist_input = CTCodelistCreateInput(
            catalogue_names=paired_codelist_input.catalogue_names,
            name=paired_codelist_input.code_information.name,
            submission_value=paired_codelist_input.code_information.submission_value,
            nci_preferred_name=paired_codelist_input.code_information.nci_preferred_name,
            definition=paired_codelist_input.code_information.definition,
            extensible=paired_codelist_input.extensible,
            is_ordinal=paired_codelist_input.is_ordinal,
            codelist_type=paired_codelist_input.codelist_type,
            sponsor_preferred_name=paired_codelist_input.code_information.sponsor_preferred_name,
            template_parameter=paired_codelist_input.template_parameter,
            parent_codelist_uid=paired_codelist_input.parent_codelist_uid,
            terms=[],
            library_name=paired_codelist_input.library_name,
        )

        names_codelist = self.create(names_codelist_input)
        codes_codelist = self.create(codes_codelist_input)

        self._repos.ct_codelist_aggregated_repository.merge_link_to_codes_codelist(
            names_codelist.codelist_uid,
            codes_codelist.codelist_uid,
        )

        attributes_service = CTCodelistAttributesService()
        names_service = CTCodelistNameService()

        return CTCodelistPaired.from_ct_codelists(
            paired_names_codelist_name=names_service.get_by_uid(
                names_codelist.codelist_uid
            ),
            paired_names_codelist_attrs=attributes_service.get_by_uid(
                names_codelist.codelist_uid
            ),
            paired_codes_codelist_name=names_service.get_by_uid(
                codes_codelist.codelist_uid
            ),
            paired_codes_codelist_attrs=attributes_service.get_by_uid(
                codes_codelist.codelist_uid
            ),
        )

    def get_all_codelists(
        self,
        catalogue_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
        is_sponsor: bool = False,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        term_filter: dict[str, str | list[Any]] | None = None,
    ) -> GenericFilteringReturn[CTCodelistNameAndAttributes]:
        self.enforce_catalogue_library_package(catalogue_name, library, package)

        all_aggregated_codelists, total = (
            self._repos.ct_codelist_aggregated_repository.find_all_aggregated_result(
                catalogue_name=catalogue_name,
                library=library,
                package=package,
                is_sponsor=is_sponsor,
                total_count=total_count,
                sort_by=sort_by,
                filter_by=filter_by,
                filter_operator=filter_operator,
                page_number=page_number,
                page_size=page_size,
                term_filter=term_filter,
            )
        )

        items = [
            CTCodelistNameAndAttributes.from_ct_codelist_ar(
                ct_codelist_name_ar,
                ct_codelist_attributes_ar,
                paired_codelist=_paired_codelist_info_from(paired),
            )
            for ct_codelist_name_ar, ct_codelist_attributes_ar, paired in all_aggregated_codelists
        ]

        return GenericFilteringReturn(items=items, total=total)

    def search_codelists_fulltext(
        self,
        search_string: str,
        only_response_codelists: bool = False,
        only_ordinal_codelists: bool = False,
        match_whole_words: bool = False,
        page_number: int = 1,
        page_size: int = 20,
    ) -> GenericFilteringReturn[CTCodelistCompact]:
        items_dicts, total = (
            self._repos.ct_codelist_aggregated_repository.search_fulltext(
                search_string=search_string,
                only_response_codelists=only_response_codelists,
                only_ordinal_codelists=only_ordinal_codelists,
                match_whole_words=match_whole_words,
                page_number=page_number,
                page_size=page_size,
            )
        )
        items = [
            CTCodelistCompact(
                uid=item["uid"],
                sponsor_preferred_name=item["sponsor_preferred_name"],
                submission_value=item["submission_value"],
                library_name=item["library_name"],
            )
            for item in items_dicts
        ]
        return GenericFilteringReturn(items=items, total=total)

    def search_codelists_fulltext_by_term(
        self,
        search_string: str,
        only_response_codelists: bool = False,
        only_ordinal_codelists: bool = False,
        match_whole_words: bool = False,
        page_number: int = 1,
        page_size: int = 20,
    ) -> GenericFilteringReturn[CTCodelistCompact]:
        items_dicts, total = (
            self._repos.ct_codelist_aggregated_repository.search_fulltext_by_term(
                search_string=search_string,
                only_response_codelists=only_response_codelists,
                only_ordinal_codelists=only_ordinal_codelists,
                match_whole_words=match_whole_words,
                page_number=page_number,
                page_size=page_size,
            )
        )
        items = [
            CTCodelistCompact(
                uid=item["uid"],
                sponsor_preferred_name=item["sponsor_preferred_name"],
                submission_value=item["submission_value"],
                library_name=item["library_name"],
            )
            for item in items_dicts
        ]
        return GenericFilteringReturn(items=items, total=total)

    def get_sub_codelists_that_have_given_terms(
        self,
        codelist_uid: str,
        term_uids: list[str],
        catalogue_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[CTCodelistNameAndAttributes]:
        self.enforce_catalogue_library_package(catalogue_name, library, package)

        all_aggregated_sub_codelists, total = (
            self._repos.ct_codelist_aggregated_repository.find_all_aggregated_result(
                library=library,
                total_count=total_count,
                sort_by=sort_by,
                filter_by={"parent_codelist_uid": {"v": [codelist_uid], "op": "eq"}},
                filter_operator=filter_operator,
                page_number=page_number,
                page_size=page_size,
            )
        )

        uid_of_sub_codelist_with_terms = []

        for sub_codelist in all_aggregated_sub_codelists:
            all_aggregated_terms, _ = (
                self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
                    codelist_uid=sub_codelist[1].uid,
                    codelist_name=None,
                    library=library,
                    package=package,
                    total_count=total_count,
                    sort_by=sort_by,
                    filter_by=filter_by,
                    filter_operator=filter_operator,
                    page_number=page_number,
                    page_size=page_size,
                )
            )

            if set(term_uids) == {term[1].uid for term in all_aggregated_terms}:
                uid_of_sub_codelist_with_terms.append(sub_codelist[1].uid)

        items = [
            CTCodelistNameAndAttributes.from_ct_codelist_ar(
                ct_codelist_name_ar,
                ct_codelist_attributes_ar,
                paired_codelist=_paired_codelist_info_from(paired),
            )
            for ct_codelist_name_ar, ct_codelist_attributes_ar, paired in all_aggregated_sub_codelists
            if ct_codelist_attributes_ar.uid in uid_of_sub_codelist_with_terms
        ]

        return GenericFilteringReturn(items=items, total=total)

    def get_distinct_values_for_header(
        self,
        catalogue_name: str | None,
        library: str | None,
        package: str | None,
        field_name: str,
        is_sponsor: bool = False,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ):
        self.enforce_catalogue_library_package(catalogue_name, library, package)

        header_values = (
            self._repos.ct_codelist_aggregated_repository.get_distinct_headers(
                catalogue_name=catalogue_name,
                library=library,
                package=package,
                is_sponsor=is_sponsor,
                field_name=field_name,
                search_string=search_string,
                filter_by=filter_by,
                filter_operator=filter_operator,
                page_size=page_size,
            )
        )

        return header_values

    @ensure_transaction(db)
    def add_term(
        self,
        codelist_uid: str,
        term_uid: str,
        order: int | None,
        submission_value: str,
        ordinal: float | None = None,
    ) -> CTCodelist:
        ct_codelist_attributes_ar = (
            self._repos.ct_codelist_attribute_repository.find_by_uid(
                codelist_uid=codelist_uid
            )
        )

        if ct_codelist_attributes_ar is not None:
            BusinessLogicException.raise_if(
                not ct_codelist_attributes_ar.library.is_editable
                and not ct_codelist_attributes_ar.ct_codelist_vo.extensible,
                msg=f"Codelist with UID '{codelist_uid}' isn't extensible.",
            )

            parent_codelist_uid = (
                ct_codelist_attributes_ar.ct_codelist_vo.parent_codelist_uid
            )
            BusinessLogicException.raise_if(
                parent_codelist_uid
                and not self._repos.ct_codelist_attribute_repository.is_term_in_codelist(
                    term_uid=term_uid, codelist_uid=parent_codelist_uid
                ),
                msg=f"Term with UID '{term_uid}' isn't in use by Parent Codelist with UID '{parent_codelist_uid}'.",
            )

        ct_codelist_name_ar = self._repos.ct_codelist_name_repository.find_by_uid(
            codelist_uid=codelist_uid
        )

        if ct_codelist_name_ar is not None:
            if (
                ordinal is not None
                and not ct_codelist_name_ar.ct_codelist_vo.is_ordinal
            ):
                raise BusinessLogicException(
                    msg=f"Codelist identified by {codelist_uid} is not ordinal, therefore term ordinal value should be None"
                )

        paired_codes_codelist_uid, paired_names_codelist_uid = (
            self._repos.ct_codelist_aggregated_repository.get_paired_codelist_uids(
                codelist_uid=codelist_uid
            )
        )

        # Validation logic for adding terms to codelists
        # Check if the term's library is editable (single DB call instead of fetching name)
        is_term_library_editable = (
            self._repos.ct_term_name_repository.is_library_editable_for_term(term_uid)
        )

        # Get all existing submission values for this term
        existing_submission_values = (
            self._repos.ct_term_name_repository.get_submission_values_for_term(term_uid)
        )

        # Validation for non-editable library terms (e.g. CDISC)
        if not is_term_library_editable:
            # Non-editable library terms: all possible submission values are already defined, no new submission values can be added
            BusinessLogicException.raise_if(
                submission_value not in existing_submission_values,
                msg=f"Term with UID '{term_uid}' belongs to a non-editable library. Cannot add a new submission value '{submission_value}'. All possible submission values are already defined.",
            )
        else:
            # Sponsor terms validation
            if submission_value not in existing_submission_values:
                # New submission value:
                # Either it is a term with no pre-existing submission value
                # Or it is targeting a paired codelist
                # Or it is targeting a codelist in a different catalogue
                # If none of the above, then it is not allowed

                # This means it is not a term with no pre-existing submission value
                if len(existing_submission_values) > 0:
                    # Check if targeting a codelist in a different catalogue.
                    # A codelist can belong to multiple catalogues, so we use set disjointness:
                    # only bypass the restriction when none of the target codelist's catalogues
                    # overlap with any catalogue the term is already in.
                    target_catalogues = set(
                        self._repos.ct_codelist_attribute_repository.get_catalogue_names_for_codelist(
                            codelist_uid
                        )
                    )
                    existing_catalogues = set(
                        self._repos.ct_term_name_repository.get_catalogue_names_for_term_codelists(
                            term_uid
                        )
                    )
                    is_different_catalogue = len(
                        target_catalogues
                    ) > 0 and target_catalogues.isdisjoint(existing_catalogues)

                    if not is_different_catalogue:
                        # Check if is targeting a paired codelist
                        paired_codelist_uid = self._repos.ct_codelist_attribute_repository.get_paired_codelist_uid(
                            codelist_uid
                        )

                        term_in_paired = False
                        if paired_codelist_uid:
                            # Check if term is in the paired codelist with the same submission value
                            term_in_paired = self._repos.ct_codelist_attribute_repository.is_term_in_codelist(
                                term_uid, paired_codelist_uid
                            )

                        # If so, continue to creation ; otherwise raise an exception
                        BusinessLogicException.raise_if(
                            not term_in_paired,
                            # pylint: disable=line-too-long
                            msg=f"Term with UID '{term_uid}' is already part of a codelist with submission value '{existing_submission_values[0]}'. Cannot add a new submission value '{submission_value}', except for a paired codelist or a different catalogue. Please reuse the existing submission value.",
                        )

        self._repos.ct_codelist_attribute_repository.add_term(
            codelist_uid=codelist_uid,
            term_uid=term_uid,
            author_id=self.author_id,
            order=order,
            submission_value=submission_value,
            ordinal=ordinal,
        )

        if ct_codelist_attributes_ar is None or ct_codelist_name_ar is None:
            raise BusinessLogicException(
                msg=f"Codelist with UID '{codelist_uid}' doesn't exist."
            )

        return CTCodelist.from_ct_codelist_ar(
            ct_codelist_name_ar,
            ct_codelist_attributes_ar,
            paired_codes_codelist_uid=paired_codes_codelist_uid,
            paired_names_codelist_uid=paired_names_codelist_uid,
        )

    @db.transaction
    def remove_term(self, codelist_uid: str, term_uid: str) -> CTCodelist:
        ct_codelist_attributes_ar = (
            self._repos.ct_codelist_attribute_repository.find_by_uid(
                codelist_uid=codelist_uid
            )
        )
        if ct_codelist_attributes_ar is not None:
            BusinessLogicException.raise_if(
                not ct_codelist_attributes_ar.library.is_editable
                and not ct_codelist_attributes_ar.ct_codelist_vo.extensible,
                msg=f"Codelist with UID '{codelist_uid}' isn't extensible.",
            )

            child_codelist_uids = (
                ct_codelist_attributes_ar.ct_codelist_vo.child_codelist_uids
            )
            if child_codelist_uids:
                terms = self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
                    filter_by={
                        "codelists.codelist_uid": {
                            "v": child_codelist_uids,
                            "op": "eq",
                        },
                        "term_uid": {"v": [term_uid], "op": "eq"},
                    }
                )[
                    0
                ]
                BusinessLogicException.raise_if(
                    len(terms) > 0,
                    msg=f"The term with UID '{term_uid}' is in use by child codelists"
                    f" with UIDs {[term[1]._ct_term_attributes_vo.codelist_uid for term in terms]}",
                )
        ct_codelist_name_ar = self._repos.ct_codelist_name_repository.find_by_uid(
            codelist_uid=codelist_uid
        )
        paired_codes_codelist_uid, paired_names_codelist_uid = (
            self._repos.ct_codelist_aggregated_repository.get_paired_codelist_uids(
                codelist_uid=codelist_uid
            )
        )

        self._repos.ct_codelist_attribute_repository.remove_term(
            codelist_uid=codelist_uid, term_uid=term_uid, author_id=self.author_id
        )

        if ct_codelist_attributes_ar is None or ct_codelist_name_ar is None:
            raise BusinessLogicException(
                msg=f"Codelist with UID '{codelist_uid}' doesn't exist."
            )

        return CTCodelist.from_ct_codelist_ar(
            ct_codelist_name_ar,
            ct_codelist_attributes_ar,
            paired_codes_codelist_uid=paired_codes_codelist_uid,
            paired_names_codelist_uid=paired_names_codelist_uid,
        )

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
            )
        )

    def list_terms(
        self,
        codelist_uid: str | None = None,
        codelist_submission_value: str | None = None,
        codelist_name: str | None = None,
        package: str | None = None,
        include_removed: bool | None = None,
        at_specific_date_time: datetime | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        include_ts_parameters: bool = True,
    ) -> GenericFilteringReturn[CTCodelistTerm]:
        all_aggregated_terms, count = (
            self._repos.ct_codelist_aggregated_repository.find_all_terms_aggregated_result(
                package=package,
                include_removed=include_removed,
                at_specific_date_time=at_specific_date_time,
                codelist_uid=codelist_uid,
                codelist_submission_value=codelist_submission_value,
                codelist_name=codelist_name,
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
            CTCodelistTerm.from_ct_codelist_term_ar(
                ct_codelist_term_ar, include_ts_parameters=include_ts_parameters
            )
            for ct_codelist_term_ar in all_aggregated_terms
        ]

        return GenericFilteringReturn.create(items=items, total=count)

    def get_distinct_term_values_for_header(
        self,
        codelist_uid: str,
        package: str | None,
        field_name: str,
        include_removed: bool | None = None,
        include_ts_parameters: bool = False,
        search_string: str | None = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ):
        header_values = (
            self._repos.ct_codelist_aggregated_repository.get_distinct_term_headers(
                codelist_uid=codelist_uid,
                package=package,
                include_removed=include_removed,
                include_ts_parameters=include_ts_parameters,
                field_name=field_name,
                search_string=search_string,
                filter_by=filter_by,
                filter_operator=filter_operator,
                page_size=page_size,
            )
        )
        return header_values

    def get_paired_codelists(self, codelist_uid) -> CTCodelistPaired:
        ct_cl_root = CTCodelistRoot.nodes.filter(uid=codelist_uid).get_or_none()
        BusinessLogicException.raise_if(
            ct_cl_root is None,
            msg=f"There is no CTCodelistRoot identified by provided codelist_uid ({codelist_uid})",
        )
        codes_pair_root = ct_cl_root.has_paired_code_codelist.get_or_none()
        names_pair_root = ct_cl_root.has_paired_name_codelist.get_or_none()

        attributes_service = CTCodelistAttributesService()
        names_service = CTCodelistNameService()

        if codes_pair_root is not None:
            codes_attrs = attributes_service.get_by_uid(codes_pair_root.uid)
            codes_name = names_service.get_by_uid(codes_pair_root.uid)
        else:
            codes_attrs = None
            codes_name = None

        if names_pair_root is not None:
            names_attrs = attributes_service.get_by_uid(names_pair_root.uid)
            names_name = names_service.get_by_uid(names_pair_root.uid)
        else:
            names_attrs = None
            names_name = None

        return CTCodelistPaired.from_ct_codelists(
            paired_names_codelist_name=names_name,
            paired_names_codelist_attrs=names_attrs,
            paired_codes_codelist_name=codes_name,
            paired_codes_codelist_attrs=codes_attrs,
        )

    def update_paired_codelists(
        self, codelist_uid: str, paired_codelists: CTCodelistPairedInput
    ) -> CTCodelist:
        ct_cl_root = CTCodelistRoot.nodes.filter(uid=codelist_uid).get_or_none()
        BusinessLogicException.raise_if(
            ct_cl_root is None,
            msg=f"There is no CTCodelistRoot identified by provided codelist_uid ({codelist_uid})",
        )
        BusinessLogicException.raise_if(
            paired_codelists.paired_codes_codelist_uid is not None
            and paired_codelists.paired_names_codelist_uid is not None,
            msg=f"Not allowed to link both paired codes and names codelists to the same codelist ({codelist_uid}).",
        )

        if paired_codelists.paired_codes_codelist_uid:
            BusinessLogicException.raise_if_not(
                self._repos.ct_codelist_attribute_repository.codelist_specific_exists_by_uid(
                    paired_codelists.paired_codes_codelist_uid
                ),
                msg=f"The given paired codes codelist with UID '{paired_codelists.paired_codes_codelist_uid}' doesn't exist.",
            )
            self._repos.ct_codelist_aggregated_repository.merge_link_to_codes_codelist(
                codelist_uid, paired_codelists.paired_codes_codelist_uid
            )
        elif (
            paired_codelists.paired_codes_codelist_uid is None
            and "paired_codes_codelist_uid" in paired_codelists.model_fields_set
        ):
            self._repos.ct_codelist_aggregated_repository.remove_link_to_codes_codelist(
                codelist_uid
            )

        if paired_codelists.paired_names_codelist_uid:
            BusinessLogicException.raise_if_not(
                self._repos.ct_codelist_attribute_repository.codelist_specific_exists_by_uid(
                    paired_codelists.paired_names_codelist_uid
                ),
                msg=f"The given paired names codelist with UID '{paired_codelists.paired_names_codelist_uid}' doesn't exist.",
            )
            self._repos.ct_codelist_aggregated_repository.merge_link_to_codes_codelist(
                paired_codelists.paired_names_codelist_uid, codelist_uid
            )
        elif (
            paired_codelists.paired_names_codelist_uid is None
            and "paired_names_codelist_uid" in paired_codelists.model_fields_set
        ):
            self._repos.ct_codelist_aggregated_repository.remove_link_from_codes_codelist(
                codelist_uid
            )

        return self.get_paired_codelists(codelist_uid)

    def get_paired_codelist_terms(
        self,
        codelist_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[CTPairedCodelistTerm]:
        paired_codes_uid, paired_names_uid = (
            self._repos.ct_codelist_aggregated_repository.get_paired_codelist_uids(
                codelist_uid
            )
        )

        BusinessLogicException.raise_if(
            paired_codes_uid is None and paired_names_uid is None,
            msg=f"Codelist with UID '{codelist_uid}' does not have a paired codelist.",
        )

        if paired_codes_uid is not None:
            names_codelist_uid = codelist_uid
            codes_codelist_uid = paired_codes_uid
        else:
            assert paired_names_uid is not None
            codes_codelist_uid = codelist_uid
            names_codelist_uid = paired_names_uid

        all_paired_terms, count = (
            self._repos.ct_codelist_aggregated_repository.find_paired_codelist_terms(
                names_codelist_uid=names_codelist_uid,
                codes_codelist_uid=codes_codelist_uid,
                sort_by=sort_by,
                page_number=page_number,
                page_size=page_size,
                total_count=total_count,
                filter_by=filter_by,
                filter_operator=filter_operator,
            )
        )

        items = [
            CTPairedCodelistTerm.from_ct_paired_codelist_term_ar(paired_term_ar)
            for paired_term_ar in all_paired_terms
        ]

        return GenericFilteringReturn.create(items=items, total=count)
