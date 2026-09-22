from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.study_selections.study_criteria_repository import (
    SelectionHistory,
)
from clinical_mdr_api.domains.study_selections.study_selection_criteria import (
    StudySelectionCriteriaAR,
    StudySelectionCriteriaVO,
)
from clinical_mdr_api.domains.syntax_instances.criteria import CriteriaAR
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.study_selections.study_selection import (
    Criteria,
    StudySelectionCriteria,
    StudySelectionCriteriaCore,
    StudySelectionCriteriaCreateInput,
    StudySelectionCriteriaInput,
    StudySelectionCriteriaTemplateSelectInput,
)
from clinical_mdr_api.models.syntax_instances.criteria import (
    CriteriaCreateInput,
    CriteriaUpdateWithCriteriaKeyInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    build_simple_filters,
    ensure_transaction,
    extract_filtering_values,
    generic_item_filtering,
    generic_pagination,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
    validate_is_dict,
)
from clinical_mdr_api.services.studies.study_selection_base import StudySelectionMixin
from clinical_mdr_api.services.syntax_instances.criteria import CriteriaService
from common import exceptions
from common.auth.user import user


class StudyCriteriaSelectionService(StudySelectionMixin):
    _repos: MetaRepository

    _vo_to_ar_filter_map = {
        "order": "criteria_type_order",
        "start_date": "start_date",
        "author_id": "author_id",
        "key_criteria": "key_criteria",
    }

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionCriteriaAR | None,
        no_brackets: bool,
        study_value_version: str | None = None,
    ) -> list[StudySelectionCriteria]:
        if study_selection is None:
            return []

        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_selection.study_uid,
            study_value_version=study_value_version,
        )
        result = []
        for selection in study_selection.study_criteria_selection:
            if selection.is_instance:
                result.append(
                    StudySelectionCriteria.from_study_selection_criteria_ar(
                        study_selection_criteria_ar=study_selection,
                        study_selection_criteria_vo=selection,
                        accepted_version=selection.accepted_version,
                        get_criteria_by_uid_callback=self._transform_latest_criteria_model,
                        get_criteria_by_uid_version_callback=self._transform_criteria_model,
                        find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                        no_brackets=no_brackets,
                        find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                        study_value_version=study_value_version,
                        terms_at_specific_datetime=terms_at_specific_datetime,
                    )
                )
            else:
                result.append(
                    StudySelectionCriteria.from_study_selection_criteria_template_ar(
                        study_selection_criteria_ar=study_selection,
                        study_selection_criteria_vo=selection,
                        accepted_version=selection.accepted_version,
                        get_criteria_template_by_uid_callback=self._transform_latest_criteria_template_model,
                        get_criteria_template_by_uid_version_callback=self._transform_criteria_template_model,
                        find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                        find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                        study_value_version=study_value_version,
                        terms_at_specific_datetime=terms_at_specific_datetime,
                    )
                )
        return result

    @ensure_transaction(db)
    def batch_select_criteria_template(
        self,
        study_uid: str,
        selection_create_input: list[StudySelectionCriteriaTemplateSelectInput],
    ) -> list[StudySelectionCriteria]:
        """
        Select multiple criteria templates as a batch.

        This will only select the templates and not create instances,
        except for templates that have no parameters and criteria input
        containing parameter values (coming from pre-instances).

        Args:
            study_uid (str)
            selection_create_input (StudySelectionCriteriaBatchSelectInput): [description]

        Returns:
            list[StudySelectionCriteria]
        """
        repos = self._repos
        try:
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            criteria_template_repo = repos.criteria_template_repository
            selections = []
            for template_input in selection_create_input:
                # Get criteria template
                criteria_template = criteria_template_repo.find_by_uid(
                    uid=template_input.criteria_template_uid
                )

                exceptions.NotFoundException.raise_if(
                    criteria_template is None,
                    "Criteria Template",
                    template_input.criteria_template_uid,
                )

                if (
                    criteria_template.template_value.parameter_names is not None
                    and len(criteria_template.template_value.parameter_names) > 0
                    and (
                        template_input.parameter_terms is None
                        or len(template_input.parameter_terms) == 0
                    )
                ):
                    criteria_type_uid = criteria_template_repo.get_template_type_uid(
                        criteria_template_repo.root_class.nodes.get_or_none(
                            uid=criteria_template.uid
                        )
                    )

                    # Get selection aggregate
                    selection_aggregate = repos.study_criteria_repository.find_by_study(
                        study_uid=study_uid, for_update=True
                    )

                    # Create new VO to add
                    new_selection = StudySelectionCriteriaVO.from_input_values(
                        author_id=self.author,
                        syntax_object_uid=criteria_template.uid,
                        syntax_object_version=criteria_template.item_metadata.version,
                        is_instance=False,
                        criteria_type_uid=criteria_type_uid,
                        generate_uid_callback=repos.study_criteria_repository.generate_uid,
                    )

                    # Add template to selection
                    assert selection_aggregate is not None
                    selection_aggregate.add_criteria_selection(
                        new_selection,
                        criteria_template_repo.check_exists_final_version,
                        self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                    )

                    # Sync with DB and save the update
                    repos.study_criteria_repository.save(
                        selection_aggregate, self.author
                    )

                    # Fetch the new selection which was just added
                    (
                        new_selection,
                        order,
                    ) = selection_aggregate.get_specific_criteria_selection(
                        study_criteria_uid=new_selection.study_selection_uid,
                        criteria_type_uid=criteria_type_uid,
                    )

                    # add the criteria and return
                    selections.append(
                        StudySelectionCriteria.from_study_selection_criteria_template_ar_and_order(
                            study_selection_criteria_ar=selection_aggregate,
                            criteria_type_order=order,
                            criteria_type_uid=criteria_type_uid,
                            get_criteria_template_by_uid_callback=self._transform_latest_criteria_template_model,
                            get_criteria_template_by_uid_version_callback=self._transform_criteria_template_model,
                            find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                            find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                            terms_at_specific_datetime=terms_at_specific_datetime,
                        )
                    )
                else:
                    parameter_terms = (
                        template_input.parameter_terms
                        if template_input.parameter_terms is not None
                        else []
                    )
                    new_selection = self.make_selection_create_criteria(
                        study_uid=study_uid,
                        selection_create_input=StudySelectionCriteriaCreateInput(
                            criteria_data=CriteriaCreateInput(
                                criteria_template_uid=template_input.criteria_template_uid,
                                parameter_terms=parameter_terms,
                                library_name=template_input.library_name,
                            )
                        ),
                    )
                    selections.append(new_selection)
            return selections
        finally:
            repos.close()

    def _create_or_get_criteria_instance(
        self,
        criteria_data: CriteriaCreateInput | CriteriaUpdateWithCriteriaKeyInput,
        criteria_type_uid: str,
    ) -> CriteriaAR:
        # check if name exists
        criteria_service: CriteriaService = CriteriaService()
        criteria_ar = criteria_service.create_ar_from_input_values(criteria_data)

        # create criteria
        criteria_uid = criteria_ar.uid
        if not criteria_service.repository.check_exists_by_name_for_type(
            name=criteria_ar.name, criteria_type_uid=criteria_type_uid
        ):
            criteria_service.repository.save(criteria_ar)
        else:
            criteria_uid = criteria_service.repository.find_uid_by_name(
                name=criteria_ar.name
            )
        criteria_ar = criteria_service.repository.find_by_uid(
            criteria_uid, for_update=True
        )

        # if in draft status - approve
        if criteria_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            criteria_ar.approve(self.author)
            criteria_service.repository.save(criteria_ar)
        elif criteria_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.NotFoundException(
                msg=f"There is no approved Criteria with UID '{criteria_uid}'."
            )

        return criteria_ar

    def patch_selection(
        self,
        study_uid: str,
        study_criteria_uid: str,
        criteria_data: CriteriaUpdateWithCriteriaKeyInput,
    ) -> StudySelectionCriteria:
        """Finalizes criteria selection by instantiation the criteria from the selected template.
        It then update the study criteria relationship by selecting the instance instead of the template.

        Args:
            study_uid (str)
            study_criteria_uid (str)
            criteria_data (CriteriaUpdateWithCriteriaKeyInput): Data necessary to create the criteria instance from the template

        Returns:
            StudySelectionCriteria : Newly created and selected criteria instance
        """
        repos = self._repos
        try:
            with db.transaction:
                # Load aggregate
                selection_aggregate = repos.study_criteria_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
                # Load the current VO for updates
                current_vo, _ = selection_aggregate.get_specific_criteria_selection(
                    study_criteria_uid=study_criteria_uid
                )

                criteria_type_uid = (
                    repos.criteria_template_repository.get_template_type_uid(
                        repos.criteria_template_repository.root_class.nodes.get_or_none(
                            uid=criteria_data.criteria_template_uid
                        )
                    )
                )

                criteria_ar = self._create_or_get_criteria_instance(
                    criteria_data=criteria_data, criteria_type_uid=criteria_type_uid
                )

                # merge current with updates
                updated_selection = StudySelectionCriteriaVO.from_input_values(
                    author_id=self.author,
                    syntax_object_uid=criteria_ar.uid,
                    syntax_object_version=criteria_ar.item_metadata.version,
                    criteria_type_uid=current_vo.criteria_type_uid,
                    criteria_type_order=current_vo.criteria_type_order,
                    is_instance=True,
                    key_criteria=criteria_data.key_criteria,
                    study_uid=current_vo.study_uid,
                    study_selection_uid=current_vo.study_selection_uid,
                    start_date=current_vo.start_date,
                    accepted_version=current_vo.accepted_version,
                )
                # let the aggregate update the value object
                selection_aggregate.update_study_criteria_on_aggregated(
                    updated_study_criteria_selection=updated_selection,
                )
                # sync with DB and save the update
                repos.study_criteria_repository.save(selection_aggregate, self.author)

                # Fetch the latest state of the selection
                selection_aggregate = repos.study_criteria_repository.find_by_study(
                    study_uid=study_uid, for_update=False
                )

                _, order = selection_aggregate.get_specific_criteria_selection(
                    study_criteria_uid=study_criteria_uid,
                    criteria_type_uid=criteria_type_uid,
                )
                terms_at_specific_datetime = (
                    self._extract_study_standards_effective_date(study_uid=study_uid)
                )
                # add the criteria and return
                return StudySelectionCriteria.from_study_selection_criteria_ar_and_order(
                    study_selection_criteria_ar=selection_aggregate,
                    criteria_type_order=order,
                    criteria_type_uid=criteria_type_uid,
                    get_criteria_by_uid_callback=self._transform_latest_criteria_model,
                    get_criteria_by_uid_version_callback=self._transform_criteria_model,
                    find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                    find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
        finally:
            repos.close()

    @db.transaction
    def make_selection(
        self, study_uid: str, selection_create_input: StudySelectionCriteriaInput
    ) -> StudySelectionCriteria:
        try:
            selection_aggregate = self._repos.study_criteria_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )
            criteria_repo = self._repos.criteria_repository
            criteria_uid = getattr(selection_create_input, "criteria_uid")
            selected_criteria = criteria_repo.find_by_uid(
                criteria_uid, status=LibraryItemStatus.FINAL
            )
            exceptions.NotFoundException.raise_if_not(
                selected_criteria,
                msg=f"There is no approved Criteria with UID '{criteria_uid}'.",
            )

            criteria_type_uid = self._repos.criteria_template_repository.get_template_type_uid(
                self._repos.criteria_template_repository.root_class.nodes.get_or_none(
                    uid=selected_criteria.template_uid
                )
            )

            new_selection = StudySelectionCriteriaVO.from_input_values(
                syntax_object_uid=criteria_uid,
                syntax_object_version=selected_criteria.item_metadata.version,
                criteria_type_uid=criteria_type_uid,
                generate_uid_callback=self._repos.study_criteria_repository.generate_uid,
                author_id=self.author,
            )

            if new_selection.syntax_object_uid is not None:
                criteria_ar = self._repos.criteria_repository.find_by_uid(
                    new_selection.syntax_object_uid, for_update=True
                )
                exceptions.NotFoundException.raise_if(
                    criteria_ar is None,
                    msg=f"There is no approved Criteria with UID '{new_selection.syntax_object_uid}'.",
                )

                if criteria_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                    criteria_ar.approve(self.author)
                    self._repos.criteria_repository.save(criteria_ar)

                elif criteria_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                    raise exceptions.NotFoundException(
                        msg=f"There is no approved Criteria with UID '{new_selection.syntax_object_uid}'."
                    )

            assert selection_aggregate is not None
            selection_aggregate.add_criteria_selection(
                new_selection,
                self._repos.criteria_repository.check_exists_final_version,
                self._repos.ct_term_name_repository.term_specific_exists_by_uid,
            )
            selection_aggregate.validate()

            self._repos.study_criteria_repository.save(selection_aggregate, self.author)

            new_selection, order = selection_aggregate.get_specific_criteria_selection(
                new_selection.study_selection_uid, criteria_type_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            return StudySelectionCriteria.from_study_selection_criteria_ar_and_order(
                study_selection_criteria_ar=selection_aggregate,
                criteria_type_order=order,
                criteria_type_uid=criteria_type_uid,
                get_criteria_by_uid_callback=self._transform_latest_criteria_model,
                get_criteria_by_uid_version_callback=self._transform_criteria_model,
                find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            self._repos.close()

    def make_selection_create_criteria(
        self,
        study_uid: str,
        selection_create_input: StudySelectionCriteriaCreateInput,
    ) -> StudySelectionCriteria:
        repos = self._repos
        try:
            # get criteria type uid from the criteria template
            criteria_type_uid = repos.criteria_template_repository.get_template_type_uid(
                self._repos.criteria_template_repository.root_class.nodes.get_or_none(
                    uid=selection_create_input.criteria_data.criteria_template_uid
                )
            )

            criteria_ar = self._create_or_get_criteria_instance(
                criteria_data=selection_create_input.criteria_data,
                criteria_type_uid=criteria_type_uid,
            )

            # get pre-existing selection aggregate
            selection_aggregate = repos.study_criteria_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # create new selection VO to add
            new_selection = StudySelectionCriteriaVO.from_input_values(
                author_id=self.author,
                syntax_object_uid=criteria_ar.uid,
                syntax_object_version=criteria_ar.item_metadata.version,
                criteria_type_uid=criteria_type_uid,
                generate_uid_callback=repos.study_criteria_repository.generate_uid,
            )

            # add VO to aggregate
            criteria_repo = repos.criteria_repository
            assert selection_aggregate is not None
            selection_aggregate.add_criteria_selection(
                new_selection,
                criteria_repo.check_exists_final_version,
                self._repos.ct_term_name_repository.term_specific_exists_by_uid,
            )

            # sync with DB and save the update
            repos.study_criteria_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just added
            (
                new_selection,
                order,
            ) = selection_aggregate.get_specific_criteria_selection(
                study_criteria_uid=new_selection.study_selection_uid,
                criteria_type_uid=criteria_type_uid,
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )

            # add the criteria and return
            return StudySelectionCriteria.from_study_selection_criteria_ar_and_order(
                study_selection_criteria_ar=selection_aggregate,
                criteria_type_order=order,
                criteria_type_uid=criteria_type_uid,
                get_criteria_by_uid_callback=self._transform_latest_criteria_model,
                get_criteria_by_uid_version_callback=self._transform_criteria_model,
                find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    def make_selection_preview_criteria(
        self, study_uid: str, selection_create_input: StudySelectionCriteriaCreateInput
    ) -> StudySelectionCriteria:
        repos = self._repos
        try:
            with db.transaction:
                criteria_service: CriteriaService = CriteriaService()

                # get criteria type uid from the criteria template
                criteria_type_uid = repos.criteria_template_repository.get_template_type_uid(
                    self._repos.criteria_template_repository.root_class.nodes.get_or_none(
                        uid=selection_create_input.criteria_data.criteria_template_uid
                    )
                )

                # create criteria instance
                criteria_ar = criteria_service.create_ar_from_input_values(
                    selection_create_input.criteria_data,
                    generate_uid_callback=lambda: "preview",
                )

                criteria_ar.approve(self.author)
                # get pre-existing selection aggregate
                selection_aggregate = repos.study_criteria_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )

                # create new selection VO to add
                new_selection = StudySelectionCriteriaVO.from_input_values(
                    author_id=self.author,
                    syntax_object_uid=criteria_ar.uid,
                    syntax_object_version=criteria_ar.item_metadata.version,
                    criteria_type_uid=criteria_type_uid,
                    generate_uid_callback=lambda: "preview",
                )

                # add VO to aggregate
                selection_aggregate.add_criteria_selection(
                    new_selection,
                    lambda _: True,
                    self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                )

                # Fetch the new selection which was just added
                (
                    new_selection,
                    order,
                ) = selection_aggregate.get_specific_criteria_selection(
                    study_criteria_uid=new_selection.study_selection_uid,
                    criteria_type_uid=criteria_type_uid,
                )
                terms_at_specific_datetime = (
                    self._extract_study_standards_effective_date(study_uid=study_uid)
                )

                # add the criteria and return
                return StudySelectionCriteria.from_study_selection_criteria_ar_and_order(
                    study_selection_criteria_ar=selection_aggregate,
                    criteria_type_order=order,
                    criteria_type_uid=criteria_type_uid,
                    get_criteria_by_uid_callback=(
                        lambda _: Criteria.from_criteria_ar(
                            criteria_ar,
                        )
                    ),
                    get_criteria_by_uid_version_callback=(
                        lambda uid, version: Criteria.from_criteria_ar(
                            criteria_ar,
                        )
                    ),
                    find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                    find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
        finally:
            repos.close()

    @db.transaction
    def get_all_selections_for_all_studies(
        self,
        no_brackets: bool,
        project_name: str | None = None,
        project_number: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[StudySelectionCriteria]:
        # Extract the study uids to use database level filtering for these
        # instead of service level filtering
        if filter_operator is None or filter_operator == FilterOperator.AND:
            study_uids = extract_filtering_values(filter_by, "study_uid")
        else:
            study_uids = None

        repos = self._repos

        criteria_selection_ars = repos.study_criteria_repository.find_all(
            project_name=project_name,
            project_number=project_number,
            study_uids=study_uids,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for criteria_selection_ar in criteria_selection_ars:
            parsed_selections = self._transform_all_to_response_model(
                criteria_selection_ar, no_brackets=no_brackets
            )
            for selection in parsed_selections:
                selections.append(selection)

        # Do filtering, sorting, pagination and count
        filtered_items = service_level_generic_filtering(
            items=selections,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        return filtered_items

    @db.transaction
    def get_distinct_values_for_header(
        self,
        field_name: str,
        study_uid: str | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
        study_value_version: str | None = None,
    ):
        repos = self._repos

        if study_uid:
            if filter_operator is None or filter_operator == FilterOperator.AND:
                criteria_type_name = extract_filtering_values(
                    filter_by,
                    "criteria_type.sponsor_preferred_name_sentence_case",
                    single_value=True,
                )
            else:
                criteria_type_name = None

            criteria_selection_ar = repos.study_criteria_repository.find_by_study(
                study_uid,
                study_value_version=study_value_version,
                criteria_type_name=criteria_type_name,
            )

            header_values = service_level_generic_header_filtering(
                items=self._transform_all_to_response_model(
                    criteria_selection_ar, no_brackets=False
                ),
                field_name=field_name,
                search_string=search_string,
                filter_by=filter_by,
                filter_operator=filter_operator,
                page_size=page_size,
            )

            return header_values

        # Extract the study uids to use database level filtering for these
        # instead of service level filtering
        if filter_operator is None or filter_operator == FilterOperator.AND:
            study_uids = extract_filtering_values(filter_by, "study_uid")
        else:
            study_uids = None

        criteria_selection_ars = repos.study_criteria_repository.find_all(
            project_name=project_name,
            project_number=project_number,
            study_uids=study_uids,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for criteria_selection_ar in criteria_selection_ars:
            parsed_selections = self._transform_all_to_response_model(
                criteria_selection_ar, no_brackets=True
            )
            for selection in parsed_selections:
                selections.append(selection)

        # Do filtering, sorting, pagination and count
        header_values = service_level_generic_header_filtering(
            items=selections,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )
        # Return values for field_name
        return header_values

    @db.transaction
    def get_all_selection(
        self,
        study_uid: str,
        no_brackets: bool,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[StudySelectionCriteria]:
        repos = self._repos
        try:
            if filter_operator is None or filter_operator == FilterOperator.AND:
                criteria_type_name = extract_filtering_values(
                    filter_by,
                    "criteria_type.sponsor_preferred_name_sentence_case",
                    single_value=True,
                )
            else:
                criteria_type_name = None

            criteria_selection_ar = repos.study_criteria_repository.find_by_study(
                study_uid,
                study_value_version=study_value_version,
                criteria_type_name=criteria_type_name,
            )
            if filter_by is not None:
                validate_is_dict("filter_by", filter_by)
            if sort_by is not None:
                validate_is_dict("sort_by", sort_by)
            simple_filters = build_simple_filters(
                self._vo_to_ar_filter_map, filter_by, sort_by
            )
            if simple_filters:
                # Filtering only needs data that is already available in the AR
                items = list(criteria_selection_ar.study_criteria_selection)
                filtered_items = generic_item_filtering(
                    items=items,
                    filter_by=simple_filters["filter_by"],
                    filter_operator=filter_operator,
                    sort_by=simple_filters["sort_by"],
                )

                # Do count
                count = len(filtered_items) if total_count else 0

                # Do pagination
                filtered_items = generic_pagination(
                    items=filtered_items,
                    page_number=page_number,
                    page_size=page_size,
                )
                # Put the sorted and filtered items back into the AR and transform them to the response model
                criteria_selection_ar.study_criteria_selection = tuple(filtered_items)
                filtered_items = self._transform_all_to_response_model(
                    criteria_selection_ar,
                    no_brackets=no_brackets,
                    study_value_version=study_value_version,
                )
                return GenericFilteringReturn(items=filtered_items, total=count)

            # Fall back to full generic filtering
            selection = self._transform_all_to_response_model(
                criteria_selection_ar,
                no_brackets=no_brackets,
                study_value_version=study_value_version,
            )
            # Do filtering, sorting, pagination and count
            return service_level_generic_filtering(
                items=selection,
                filter_by=filter_by,
                filter_operator=filter_operator,
                sort_by=sort_by,
                total_count=total_count,
                page_number=page_number,
                page_size=page_size,
            )
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        study_value_version: str | None = None,
    ) -> StudySelectionCriteria:
        repos = self._repos
        (
            selection_aggregate,
            new_selection,
        ) = self._get_specific_criteria_selection_by_uids(
            study_uid, study_selection_uid, study_value_version
        )
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_uid,
            study_value_version=study_value_version,
        )
        if new_selection.is_instance:
            return StudySelectionCriteria.from_study_selection_criteria_ar_and_order(
                study_selection_criteria_ar=selection_aggregate,
                criteria_type_order=new_selection.criteria_type_order,
                criteria_type_uid=new_selection.criteria_type_uid,
                accepted_version=new_selection.accepted_version,
                get_criteria_by_uid_callback=self._transform_latest_criteria_model,
                get_criteria_by_uid_version_callback=self._transform_criteria_model,
                find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                find_project_by_study_uid=repos.project_repository.find_by_study_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        return StudySelectionCriteria.from_study_selection_criteria_template_ar_and_order(
            study_selection_criteria_ar=selection_aggregate,
            criteria_type_order=new_selection.criteria_type_order,
            criteria_type_uid=new_selection.criteria_type_uid,
            accepted_version=new_selection.accepted_version,
            get_criteria_template_by_uid_callback=self._transform_latest_criteria_template_model,
            get_criteria_template_by_uid_version_callback=self._transform_criteria_template_model,
            find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            find_project_by_study_uid=repos.project_repository.find_by_study_uid,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    def _transform_history_to_response_model(
        self, study_selection_history: list[SelectionHistory], study_uid: str
    ) -> list[StudySelectionCriteriaCore]:
        result = []
        for history in study_selection_history:
            if history.is_instance:
                result.append(
                    StudySelectionCriteriaCore.from_study_selection_history(
                        study_selection_history=history,
                        study_uid=study_uid,
                        get_criteria_by_uid_version_callback=self._transform_criteria_model,
                    )
                )
            else:
                result.append(
                    StudySelectionCriteriaCore.from_study_selection_template_history(
                        study_selection_history=history,
                        study_uid=study_uid,
                        get_criteria_template_by_uid_version_callback=self._transform_criteria_template_model,
                    )
                )
        return result

    @db.transaction
    def get_all_selection_audit_trail(
        self, study_uid: str, criteria_type_uid: str | None
    ) -> list[StudySelectionCriteriaCore]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_criteria_repository.find_selection_history(
                        study_uid=study_uid, criteria_type_uid=criteria_type_uid
                    )
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(msg=value_error.args[0])

            return self._transform_history_to_response_model(
                selection_history, study_uid
            )
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection_audit_trail(
        self, study_uid: str, study_selection_uid: str
    ) -> list[StudySelectionCriteriaCore]:
        repos = self._repos
        try:
            selection_history = repos.study_criteria_repository.find_selection_history(
                study_uid=study_uid, study_selection_uid=study_selection_uid
            )
            return self._transform_history_to_response_model(
                selection_history, study_uid
            )
        finally:
            repos.close()

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = repos.study_criteria_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            assert selection_aggregate is not None
            selection_aggregate.remove_criteria_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_criteria_repository.save(selection_aggregate, self.author)
        finally:
            repos.close()

    @db.transaction
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> StudySelectionCriteria:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = repos.study_criteria_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # Set new order
            assert selection_aggregate is not None
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order, self.author
            )

            # sync with DB and save the update
            repos.study_criteria_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just added
            new_selection, _ = selection_aggregate.get_specific_criteria_selection(
                study_criteria_uid=study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            # add the criteria and return
            if new_selection.is_instance:
                return StudySelectionCriteria.from_study_selection_criteria_ar_and_order(
                    study_selection_criteria_ar=selection_aggregate,
                    criteria_type_order=new_order,
                    criteria_type_uid=new_selection.criteria_type_uid,
                    get_criteria_by_uid_callback=self._transform_latest_criteria_model,
                    get_criteria_by_uid_version_callback=self._transform_criteria_model,
                    find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                    find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
            return StudySelectionCriteria.from_study_selection_criteria_template_ar_and_order(
                study_selection_criteria_ar=selection_aggregate,
                criteria_type_order=new_order,
                criteria_type_uid=new_selection.criteria_type_uid,
                get_criteria_template_by_uid_callback=self._transform_latest_criteria_template_model,
                get_criteria_template_by_uid_version_callback=self._transform_criteria_template_model,
                find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    @db.transaction
    def set_key_criteria(
        self, study_uid: str, study_selection_uid: str, key_criteria: bool
    ) -> StudySelectionCriteria:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = repos.study_criteria_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )
            # Load the current VO for updates
            current_vo, _ = selection_aggregate.get_specific_criteria_selection(
                study_criteria_uid=study_selection_uid
            )

            # merge current with updates
            updated_selection = StudySelectionCriteriaVO.from_input_values(
                author_id=self.author,
                syntax_object_uid=current_vo.syntax_object_uid,
                syntax_object_version=current_vo.syntax_object_version,
                criteria_type_uid=current_vo.criteria_type_uid,
                criteria_type_order=current_vo.criteria_type_order,
                is_instance=current_vo.is_instance,
                key_criteria=key_criteria,
                study_uid=current_vo.study_uid,
                study_selection_uid=current_vo.study_selection_uid,
                start_date=current_vo.start_date,
                accepted_version=current_vo.accepted_version,
            )

            # let the aggregate update the value object
            selection_aggregate.update_study_criteria_on_aggregated(
                updated_study_criteria_selection=updated_selection,
            )

            # sync with DB and save the update
            repos.study_criteria_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just added
            new_selection, _ = selection_aggregate.get_specific_criteria_selection(
                study_criteria_uid=study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            # add the criteria and return
            if new_selection.is_instance:
                return StudySelectionCriteria.from_study_selection_criteria_ar_and_order(
                    study_selection_criteria_ar=selection_aggregate,
                    criteria_type_order=new_selection.criteria_type_order,
                    criteria_type_uid=new_selection.criteria_type_uid,
                    get_criteria_by_uid_callback=self._transform_latest_criteria_model,
                    get_criteria_by_uid_version_callback=self._transform_criteria_model,
                    find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                    find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
            return StudySelectionCriteria.from_study_selection_criteria_template_ar_and_order(
                study_selection_criteria_ar=selection_aggregate,
                criteria_type_order=new_selection.criteria_type_order,
                criteria_type_uid=new_selection.criteria_type_uid,
                get_criteria_template_by_uid_callback=self._transform_latest_criteria_template_model,
                get_criteria_template_by_uid_version_callback=self._transform_criteria_template_model,
                find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    @db.transaction
    def update_selection_to_latest_version(
        self, study_uid: str, study_selection_uid: str
    ):
        selection_ar, selection = self._get_specific_criteria_selection_by_uids(
            study_uid, study_selection_uid, for_update=True
        )
        criteria_ar = self._repos.criteria_repository.find_by_uid(
            selection.syntax_object_uid
        )
        if criteria_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            criteria_ar.approve(self.author)
            self._repos.criteria_repository.save(criteria_ar)
        elif criteria_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                msg="Cannot add retired criteria as selection. Please reactivate."
            )
        new_selection = selection.update_version(criteria_ar.item_metadata.version)
        selection_ar.update_selection(
            new_selection, criteria_exist_callback=lambda x: True
        )
        self._repos.study_criteria_repository.save(selection_ar, self.author)
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_uid
        )
        return StudySelectionCriteria.from_study_selection_criteria_ar_and_order(
            study_selection_criteria_ar=selection_ar,
            criteria_type_order=selection.criteria_type_order,
            criteria_type_uid=selection.criteria_type_uid,
            get_criteria_by_uid_callback=self._transform_latest_criteria_model,
            get_criteria_by_uid_version_callback=self._transform_criteria_model,
            find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    @db.transaction
    def update_selection_accept_version(self, study_uid: str, study_selection_uid: str):
        selection: StudySelectionCriteriaVO
        selection_ar, selection = self._get_specific_criteria_selection_by_uids(
            study_uid, study_selection_uid, for_update=True
        )
        criteria_ar = self._repos.criteria_repository.find_by_uid(
            selection.syntax_object_uid
        )
        if criteria_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            criteria_ar.approve(self.author)
            self._repos.criteria_repository.save(criteria_ar)
        elif criteria_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                msg="Cannot add retired criteria as selection. Please reactivate."
            )
        new_selection = selection.accept_versions()
        selection_ar.update_selection(
            new_selection, criteria_exist_callback=lambda x: True
        )
        self._repos.study_criteria_repository.save(selection_ar, self.author)
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_uid
        )
        return StudySelectionCriteria.from_study_selection_criteria_ar_and_order(
            study_selection_criteria_ar=selection_ar,
            criteria_type_order=selection.criteria_type_order,
            criteria_type_uid=selection.criteria_type_uid,
            accepted_version=new_selection.accepted_version,
            get_criteria_by_uid_callback=self._transform_latest_criteria_model,
            get_criteria_by_uid_version_callback=self._transform_criteria_model,
            find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )
