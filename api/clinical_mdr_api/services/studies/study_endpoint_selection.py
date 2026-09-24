from datetime import datetime
from typing import Any, Sequence

from neomodel import db

from clinical_mdr_api.domains.study_selections.study_selection_endpoint import (
    StudyEndpointSelectionHistory,
    StudySelectionEndpointsAR,
    StudySelectionEndpointVO,
)
from clinical_mdr_api.domains.syntax_instances.endpoint import EndpointAR
from clinical_mdr_api.domains.syntax_instances.timeframe import TimeframeAR
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.study_selections.study_selection import (
    EndpointUnitsInput,
    StudySelectionEndpoint,
    StudySelectionEndpointCreateInput,
    StudySelectionEndpointInput,
    StudySelectionEndpointTemplateSelectInput,
    StudySelectionObjective,
)
from clinical_mdr_api.models.syntax_instances.endpoint import (
    Endpoint,
    EndpointCreateInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    build_simple_filters,
    ensure_transaction,
    extract_filtering_values,
    fill_missing_values_in_base_model_from_reference_base_model,
    generic_item_filtering,
    generic_pagination,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
    validate_is_dict,
)
from clinical_mdr_api.services.studies.study_selection_base import StudySelectionMixin
from clinical_mdr_api.services.syntax_instances.endpoints import EndpointService
from common import exceptions
from common.auth.user import user
from common.config import settings


class StudyEndpointSelectionService(StudySelectionMixin):
    _repos: MetaRepository

    _vo_to_ar_filter_map = {
        "order": "endpoint_level_order",
        "start_date": "start_date",
        "author_id": "author_id",
    }

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    def _transform_single_study_objective_to_model(
        self,
        study_uid: str,
        study_selection_uid: str,
        terms_at_specific_datetime: datetime | None,
        no_brackets: bool = False,
        study_value_version: str | None = None,
    ) -> StudySelectionObjective:
        repos = self._repos
        selection_aggregate = repos.study_objective_repository.find_by_study(
            study_uid, study_value_version=study_value_version
        )
        assert selection_aggregate is not None
        _, order = selection_aggregate.get_specific_objective_selection(
            study_selection_uid
        )
        result = StudySelectionObjective.from_study_selection_objectives_ar_and_order(
            study_selection_objectives_ar=selection_aggregate,
            order=order,
            get_objective_by_uid_callback=self._transform_latest_objective_model,
            get_objective_by_uid_version_callback=self._transform_objective_model,
            find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            get_study_endpoint_count_callback=self._repos.study_endpoint_repository.quantity_of_study_endpoints_in_study_objective_uid,
            no_brackets=no_brackets,
            find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
            study_value_version=study_value_version,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )
        return result

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionEndpointsAR | None,
        no_brackets: bool = False,
        study_value_version: str | None = None,
    ) -> list[StudySelectionEndpoint]:
        if study_selection is None:
            return []

        result = []
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_selection.study_uid,
            study_value_version=study_value_version,
        )
        for order, selection in enumerate(
            study_selection.study_endpoints_selection, start=1
        ):
            result.append(
                self._transform_single_to_response_model(
                    selection,
                    order=order,
                    study_uid=study_selection.study_uid,
                    no_brackets=no_brackets,
                    study_value_version=study_value_version,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
            )
        return result

    def _transform_single_to_response_model(
        self,
        study_selection: StudySelectionEndpointVO,
        order: int,
        study_uid: str,
        terms_at_specific_datetime: datetime | None,
        no_brackets: bool = False,
        get_latest_endpoint_by_uid=None,
        get_endpoint_by_uid_and_version=None,
        study_value_version: str | None = None,
    ) -> StudySelectionEndpoint:
        if study_selection.is_instance:
            get_endpoint_by_uid_and_version = (
                self._transform_endpoint_model
                if get_endpoint_by_uid_and_version is None
                else get_endpoint_by_uid_and_version
            )
            get_latest_endpoint_by_uid = (
                self._transform_latest_endpoint_model
                if get_latest_endpoint_by_uid is None
                else get_latest_endpoint_by_uid
            )
        else:
            get_endpoint_by_uid_and_version = (
                self._transform_endpoint_template_model
                if get_endpoint_by_uid_and_version is None
                else get_endpoint_by_uid_and_version
            )
            get_latest_endpoint_by_uid = (
                self._transform_latest_endpoint_template_model
                if get_latest_endpoint_by_uid is None
                else get_endpoint_by_uid_and_version
            )
        return StudySelectionEndpoint.from_study_selection_endpoint(
            study_selection=study_selection,
            study_uid=study_uid,
            get_endpoint_by_uid_and_version=get_endpoint_by_uid_and_version,
            get_latest_endpoint_by_uid=get_latest_endpoint_by_uid,
            get_timeframe_by_uid_and_version=self._transform_timeframe_model,
            get_latest_timeframe=self._transform_latest_timeframe_model,
            find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            get_study_objective_by_uid=self._transform_single_study_objective_to_model,
            order=order,
            accepted_version=study_selection.accepted_version,
            no_brackets=no_brackets,
            find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
            study_value_version=study_value_version,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    @db.transaction
    def make_selection(
        self, study_uid: str, selection_create_input: StudySelectionEndpointInput
    ) -> StudySelectionEndpoint:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = repos.study_endpoint_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            endpoint_repo = repos.endpoint_repository
            timeframe_repo = repos.timeframe_repository

            endpoint_ar: EndpointAR | None
            if selection_create_input.endpoint_uid:
                endpoint_ar = endpoint_repo.find_by_uid(
                    selection_create_input.endpoint_uid, for_update=True
                )
                exceptions.NotFoundException.raise_if(
                    endpoint_ar is None,
                    msg=f"There is no approved Endpoint with UID '{selection_create_input.endpoint_uid}'.",
                )
                # if in draft status - approve
                if endpoint_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                    endpoint_ar.approve(self.author)
                    endpoint_repo.save(endpoint_ar)
                # if in retired then we return a error
                elif endpoint_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                    raise exceptions.NotFoundException(
                        msg=f"There is no approved Endpoint with UID '{selection_create_input.endpoint_uid}'."
                    )
            else:
                endpoint_ar = None

            timeframe_ar: TimeframeAR | None
            if selection_create_input.timeframe_uid:
                timeframe_ar = timeframe_repo.find_by_uid(
                    selection_create_input.timeframe_uid, for_update=True
                )
                exceptions.NotFoundException.raise_if(
                    timeframe_ar is None,
                    msg=f"There is no approved Timeframe with UID '{selection_create_input.timeframe_uid}'.",
                )
                # if in draft status - approve
                if timeframe_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                    timeframe_ar.approve(self.author)
                    timeframe_repo.save(timeframe_ar)
                # if in retired then we return a error
                elif timeframe_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                    raise exceptions.NotFoundException(
                        msg=f"There is no approved Timeframe with UID '{selection_create_input.timeframe_uid}'."
                    )
            else:
                timeframe_ar = None

            if (
                selection_create_input.endpoint_units
                and selection_create_input.endpoint_units.units is not None
            ):
                units = tuple(
                    {"uid": unit}
                    for unit in selection_create_input.endpoint_units.units
                )
                separator = selection_create_input.endpoint_units.separator

            else:
                units = None
                separator = None

            # get order from the endpoint level CT term
            if selection_create_input.endpoint_level_uid is not None:
                endpoint_level_order = self._repos.ct_term_name_repository.term_specific_order_by_uid_and_cl_submval(
                    uid=selection_create_input.endpoint_level_uid,
                    cl_submval=settings.study_endpoint_level_cl_submval,
                )
            else:
                endpoint_level_order = None
            new_selection = StudySelectionEndpointVO.from_input_values(
                endpoint_uid=selection_create_input.endpoint_uid,
                endpoint_version=(
                    endpoint_ar.item_metadata.version if endpoint_ar else None
                ),
                endpoint_level_uid=selection_create_input.endpoint_level_uid,
                endpoint_sublevel_uid=selection_create_input.endpoint_sublevel_uid,
                endpoint_units=units,
                timeframe_uid=selection_create_input.timeframe_uid,
                timeframe_version=(
                    timeframe_ar.item_metadata.version if timeframe_ar else None
                ),
                unit_separator=separator,
                study_objective_uid=selection_create_input.study_objective_uid,
                generate_uid_callback=repos.study_endpoint_repository.generate_uid,
                author_id=self.author,
                endpoint_level_order=endpoint_level_order,
            )

            # add VO to aggregate
            selection_aggregate.add_endpoint_selection(
                study_endpoint_selection=new_selection,
                study_objective_exist_callback=repos.study_objective_repository.study_objective_exists,
                endpoint_exist_callback=endpoint_repo.check_exists_final_version,
                timeframe_exist_callback=timeframe_repo.check_exists_final_version,
                ct_term_exists_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                unit_definition_exists_callback=repos.unit_definition_repository.check_exists_final_version,
            )
            selection_aggregate.validate()
            # sync with DB and save the update
            repos.study_endpoint_repository.save(selection_aggregate, self.author)
            # Fetch the new selection which was just added
            new_selection, order = selection_aggregate.get_specific_endpoint_selection(
                new_selection.study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            # add the objective and return
            return self._transform_single_to_response_model(
                new_selection,
                order,
                study_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    @ensure_transaction(db)
    def make_selection_create_endpoint(
        self,
        study_uid: str,
        selection_create_input: (
            StudySelectionEndpointCreateInput | StudySelectionEndpointInput
        ),
    ) -> StudySelectionEndpoint:
        repos = self._repos
        try:
            # check if name exists
            endpoint_service: EndpointService = EndpointService()
            endpoint_ar = endpoint_service.create_ar_from_input_values(
                selection_create_input.endpoint_data
            )

            endpoint_uid = endpoint_ar.uid
            if not endpoint_service.repository.check_exists_by_name(endpoint_ar.name):
                endpoint_service.repository.save(endpoint_ar)
            else:
                endpoint_uid = endpoint_service.repository.find_uid_by_name(
                    name=endpoint_ar.name
                )
            endpoint_ar = endpoint_service.repository.find_by_uid(
                endpoint_uid, for_update=True
            )

            # getting selection aggregate
            selection_aggregate = repos.study_endpoint_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # if in draft status - approve
            if endpoint_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                endpoint_ar.approve(self.author)
                endpoint_service.repository.save(endpoint_ar)
            elif endpoint_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                raise exceptions.NotFoundException(
                    msg=f"There is no approved Objective with UID '{endpoint_uid}'."
                )

            timeframe_ar: TimeframeAR | None
            if selection_create_input.timeframe_uid:
                timeframe_ar = repos.timeframe_repository.find_by_uid(
                    selection_create_input.timeframe_uid, for_update=True
                )
                exceptions.NotFoundException.raise_if(
                    timeframe_ar is None,
                    msg=f"There is no approved Timeframe with UID '{selection_create_input.timeframe_uid}'.",
                )
                # if in draft status - approve
                if timeframe_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                    timeframe_ar.approve(self.author)
                    repos.timeframe_repository.save(timeframe_ar)
                # if in retired then we return a error
                elif timeframe_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                    raise exceptions.NotFoundException(
                        msg=f"There is no approved Timeframe with UID '{selection_create_input.timeframe_uid}'."
                    )
            else:
                timeframe_ar = None

            if (
                selection_create_input.endpoint_units
                and selection_create_input.endpoint_units.units is not None
            ):
                units = []
                for unit in selection_create_input.endpoint_units.units:
                    name = self._repos.unit_definition_repository.get_property_by_uid(
                        unit, "name"
                    )
                    units += [{"uid": unit, "name": name}]
                separator = selection_create_input.endpoint_units.separator

            else:
                units = None
                separator = None

            # get order from the Objective level CT term
            if selection_create_input.endpoint_level_uid is not None:
                endpoint_level_order = (
                    self._repos.ct_term_name_repository.term_specific_order_by_uid(
                        uid=selection_create_input.endpoint_level_uid
                    )
                )
            else:
                endpoint_level_order = None

            # create new VO to add
            new_selection = StudySelectionEndpointVO.from_input_values(
                endpoint_uid=endpoint_uid,
                endpoint_version=endpoint_ar.item_metadata.version,
                endpoint_level_uid=selection_create_input.endpoint_level_uid,
                endpoint_sublevel_uid=selection_create_input.endpoint_sublevel_uid,
                endpoint_units=tuple(units or []),
                unit_separator=separator,
                timeframe_uid=selection_create_input.timeframe_uid,
                timeframe_version=(
                    timeframe_ar.item_metadata.version if timeframe_ar else None
                ),
                study_objective_uid=selection_create_input.study_objective_uid,
                generate_uid_callback=repos.study_endpoint_repository.generate_uid,
                author_id=self.author,
                endpoint_level_order=endpoint_level_order,
            )
            # add VO to aggregate
            endpoint_repo = repos.endpoint_repository
            assert selection_aggregate is not None
            selection_aggregate.add_endpoint_selection(
                study_endpoint_selection=new_selection,
                endpoint_exist_callback=endpoint_repo.check_exists_final_version,
                study_objective_exist_callback=repos.study_objective_repository.study_objective_exists,
                timeframe_exist_callback=repos.timeframe_repository.check_exists_final_version,
                ct_term_exists_callback=repos.ct_term_name_repository.term_specific_exists_by_uid,
                unit_definition_exists_callback=repos.unit_definition_repository.check_exists_final_version,
            )
            selection_aggregate.validate()

            # sync with DB and save the update
            repos.study_endpoint_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just added
            (
                new_selection,
                order,
            ) = selection_aggregate.get_specific_endpoint_selection(
                new_selection.study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            return self._transform_single_to_response_model(
                new_selection,
                order,
                study_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    @ensure_transaction(db)
    def batch_select_endpoint_template(
        self,
        study_uid: str,
        selection_create_input: list[StudySelectionEndpointTemplateSelectInput],
    ) -> list[StudySelectionEndpoint]:
        """
        Select multiple endpoint templates as a batch.

        This will only select the templates and not create instances,
        except for templates that have no parameters and endpoint input
        containing parameter values (coming from pre-instances).

        Args:
            study_uid (str)
            selection_create_input (StudySelectionEndpointBatchSelectInput): [description]

        Returns:
            list[StudySelectionEndpoint]
        """
        repos = self._repos
        try:
            endpoint_template_repo = repos.endpoint_template_repository
            selections = []
            for template_input in selection_create_input:
                # Get endpoint template
                endpoint_template = endpoint_template_repo.find_by_uid(
                    uid=template_input.endpoint_template_uid
                )

                exceptions.NotFoundException.raise_if(
                    endpoint_template is None,
                    "Endpoint Template",
                    template_input.endpoint_template_uid,
                )

                if (
                    endpoint_template.template_value.parameter_names is not None
                    and len(endpoint_template.template_value.parameter_names) > 0
                    and (
                        template_input.parameter_terms is None
                        or len(template_input.parameter_terms) == 0
                    )
                ):
                    # Get selection aggregate
                    selection_aggregate = repos.study_endpoint_repository.find_by_study(
                        study_uid=study_uid, for_update=True
                    )

                    # Create new VO to add
                    new_selection = StudySelectionEndpointVO.from_input_values(
                        author_id=self.author,
                        is_instance=False,
                        endpoint_uid=endpoint_template.uid,
                        endpoint_version=endpoint_template.item_metadata.version,
                        endpoint_level_uid=None,
                        endpoint_sublevel_uid=None,
                        unit_separator=None,
                        study_objective_uid=template_input.study_objective_uid,
                        timeframe_uid=None,
                        timeframe_version=None,
                        endpoint_units=None,
                        endpoint_level_order=None,
                        generate_uid_callback=repos.study_endpoint_repository.generate_uid,
                    )

                    # Add template to selection
                    try:
                        assert selection_aggregate is not None
                        selection_aggregate.add_endpoint_selection(
                            new_selection,
                            endpoint_exist_callback=endpoint_template_repo.check_exists_final_version,
                            ct_term_exists_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                        )
                    except ValueError as value_error:
                        raise exceptions.ValidationException(msg=value_error.args[0])

                    # Sync with DB and save the update
                    repos.study_endpoint_repository.save(
                        selection_aggregate, self.author
                    )

                    # Fetch the new selection which was just added
                    (
                        new_selection,
                        order,
                    ) = selection_aggregate.get_specific_endpoint_selection(
                        study_selection_uid=new_selection.study_selection_uid
                    )

                    # add the endpoint and return
                    selections.append(
                        StudySelectionEndpoint.from_study_selection_endpoint_template_ar_and_order(
                            study_selection_endpoint_ar=selection_aggregate,
                            order=order,
                            get_endpoint_template_by_uid_callback=self._transform_latest_endpoint_template_model,
                            get_endpoint_template_by_uid_version_callback=self._transform_endpoint_template_model,
                            get_study_objective_by_uid=self._transform_single_study_objective_to_model,
                            find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                        )
                    )
                else:
                    parameter_terms = (
                        template_input.parameter_terms
                        if template_input.parameter_terms is not None
                        else []
                    )
                    new_selection = self.make_selection_create_endpoint(
                        study_uid=study_uid,
                        selection_create_input=StudySelectionEndpointCreateInput(
                            endpoint_data=EndpointCreateInput(
                                endpoint_template_uid=template_input.endpoint_template_uid,
                                parameter_terms=parameter_terms,
                                library_name=template_input.library_name,
                            )
                        ),
                    )
                    selections.append(new_selection)
            return selections
        finally:
            repos.close()

    def make_selection_preview_endpoint(
        self, study_uid: str, selection_create_input: StudySelectionEndpointCreateInput
    ) -> StudySelectionEndpoint:
        repos = self._repos
        try:
            # Load aggregate
            with db.transaction:
                # check if name exists
                endpoint_service: EndpointService = EndpointService()
                endpoint_ar = endpoint_service.create_ar_from_input_values(
                    selection_create_input.endpoint_data,
                    generate_uid_callback=lambda: "preview",
                )

                endpoint_uid = endpoint_ar.uid
                endpoint_ar.approve(self.author)
                # getting selection aggregate
                selection_aggregate = repos.study_endpoint_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )

                timeframe_repo = repos.timeframe_repository
                timeframe_ar: TimeframeAR | None
                if selection_create_input.timeframe_uid:
                    timeframe_ar = timeframe_repo.find_by_uid(
                        selection_create_input.timeframe_uid, for_update=True
                    )
                    exceptions.NotFoundException.raise_if(
                        timeframe_ar is None,
                        msg=f"There is no approved Timeframe with UID '{selection_create_input.timeframe_uid}'.",
                    )
                    # if in draft status - approve
                    if timeframe_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                        timeframe_ar.approve(self.author)
                        timeframe_repo.save(timeframe_ar)
                    # if in retired then we return a error
                    elif timeframe_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                        raise exceptions.NotFoundException(
                            msg=f"There is no approved Timeframe with UID '{selection_create_input.timeframe_uid}'."
                        )
                else:
                    timeframe_ar = None

                units = None
                separator = None

                # create new VO to add
                new_selection = StudySelectionEndpointVO.from_input_values(
                    endpoint_uid=endpoint_uid,
                    endpoint_version=endpoint_ar.item_metadata.version,
                    endpoint_level_uid=selection_create_input.endpoint_level_uid,
                    endpoint_sublevel_uid=selection_create_input.endpoint_sublevel_uid,
                    endpoint_units=units,
                    unit_separator=separator,
                    timeframe_uid=selection_create_input.timeframe_uid,
                    timeframe_version=(
                        timeframe_ar.item_metadata.version if timeframe_ar else None
                    ),
                    study_objective_uid=selection_create_input.study_objective_uid,
                    generate_uid_callback=lambda: "preview",
                    author_id=self.author,
                    endpoint_level_order=None,
                )
                # add VO to aggregate
                selection_aggregate.add_endpoint_selection(
                    study_endpoint_selection=new_selection,
                    endpoint_exist_callback=lambda _: True,
                    study_objective_exist_callback=repos.study_objective_repository.study_objective_exists,
                    timeframe_exist_callback=repos.timeframe_repository.check_exists_final_version,
                    ct_term_exists_callback=repos.ct_term_name_repository.term_specific_exists_by_uid,
                    unit_definition_exists_callback=repos.unit_definition_repository.check_exists_final_version,
                )

                # Fetch the new selection which was just added
                (
                    new_selection,
                    order,
                ) = selection_aggregate.get_specific_endpoint_selection(
                    new_selection.study_selection_uid
                )
                terms_at_specific_datetime = (
                    self._extract_study_standards_effective_date(study_uid=study_uid)
                )
                return self._transform_single_to_response_model(
                    new_selection,
                    order,
                    study_uid,
                    get_latest_endpoint_by_uid=(
                        lambda _: Endpoint.from_endpoint_ar(endpoint_ar)
                    ),
                    get_endpoint_by_uid_and_version=(
                        lambda a, b: Endpoint.from_endpoint_ar(endpoint_ar)
                    ),
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
    ) -> GenericFilteringReturn[StudySelectionEndpoint]:
        # Extract the study uids to use database level filtering for these
        # instead of service level filtering
        if filter_operator is None or filter_operator == FilterOperator.AND:
            study_uids = extract_filtering_values(filter_by, "study_uid")
        else:
            study_uids = None

        repos = self._repos
        endpoint_selection_ars = repos.study_endpoint_repository.find_all(
            project_name=project_name,
            project_number=project_number,
            study_uids=study_uids,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        # TODO check if filtering can be done before unwinding
        selections = []
        for ar in endpoint_selection_ars:
            parsed_selections = self._transform_all_to_response_model(
                ar, no_brackets=no_brackets
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

        if filter_by is not None:
            validate_is_dict("filter_by", filter_by)

        if study_uid:
            endpoint_selection_ar = repos.study_endpoint_repository.find_by_study(
                study_uid, study_value_version=study_value_version
            )

            simple_filters = build_simple_filters(
                self._vo_to_ar_filter_map, filter_by, None
            )
            if simple_filters:
                # Filtering only needs data that is already available in the AR
                if field_name not in self._vo_to_ar_filter_map:
                    # We can filter using data only fromt he AR,
                    # but we need to transform all to response model to be able to get header values
                    items = list(endpoint_selection_ar.study_endpoints_selection)
                    filtered_items = generic_item_filtering(
                        items=items,
                        filter_by=simple_filters["filter_by"],
                        filter_operator=filter_operator,
                        sort_by=None,
                    )
                    endpoint_selection_ar.study_endpoints_selection = tuple(
                        filtered_items
                    )
                    filtered_items = self._transform_all_to_response_model(
                        endpoint_selection_ar, no_brackets=False
                    )

                else:
                    # Both filtering and header values can be done using data from the AR
                    field_name = self._vo_to_ar_filter_map[field_name]
                    filter_by = simple_filters["filter_by"]
                    filtered_items = list(
                        endpoint_selection_ar.study_endpoints_selection
                    )
            else:
                # We need to transform all to response model to filter
                filtered_items = self._transform_all_to_response_model(
                    endpoint_selection_ar, no_brackets=False
                )

            header_values = service_level_generic_header_filtering(
                items=self._transform_all_to_response_model(
                    endpoint_selection_ar, no_brackets=False
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

        endpoint_selection_ars = repos.study_endpoint_repository.find_all(
            project_name=project_name,
            project_number=project_number,
            study_uids=study_uids,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        # TODO check if filtering can be done before unwinding
        selections = []
        for ar in endpoint_selection_ars:
            parsed_selections = self._transform_all_to_response_model(
                ar, no_brackets=False
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
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn:
        repos = MetaRepository()
        try:
            endpoint_selection_ar = repos.study_endpoint_repository.find_by_study(
                study_uid, study_value_version=study_value_version
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
                items = list(endpoint_selection_ar.study_endpoints_selection)
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
                endpoint_selection_ar.study_endpoints_selection = tuple(filtered_items)
                filtered_items = self._transform_all_to_response_model(
                    endpoint_selection_ar,
                    no_brackets=no_brackets,
                    study_value_version=study_value_version,
                )
                return GenericFilteringReturn(items=filtered_items, total=count)

            # Fall back to full generic filtering
            selection = self._transform_all_to_response_model(
                endpoint_selection_ar,
                no_brackets=no_brackets,
                study_value_version=study_value_version,
            )
            # Do filtering, sorting, pagination and count
            return service_level_generic_filtering(
                items=selection,
                sort_by=sort_by,
                filter_by=filter_by,
                filter_operator=filter_operator,
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
        for_update: bool = False,
        study_value_version: str | None = None,
    ) -> StudySelectionEndpoint:
        repos = self._repos
        try:
            selection_aggregate = repos.study_endpoint_repository.find_by_study(
                study_uid,
                for_update=for_update,
                study_value_version=study_value_version,
            )
            (
                new_selection,
                order,
            ) = selection_aggregate.get_specific_endpoint_selection(study_selection_uid)
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid,
                study_value_version=study_value_version,
            )
            return self._transform_single_to_response_model(
                new_selection,
                order,
                study_uid,
                study_value_version=study_value_version,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            # Verify that the study endpoint is not being used as a template parameter
            exceptions.BusinessLogicException.raise_if(
                repos.study_endpoint_repository.is_used_as_parameter(
                    study_selection_uid
                ),
                msg="This study endpoint is currently used as a parameter by a study objective.",
            )

            # Load aggregate
            selection_aggregate = repos.study_endpoint_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            selection_aggregate.remove_endpoint_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_endpoint_repository.save(selection_aggregate, self.author)
        finally:
            repos.close()

    @db.transaction
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> StudySelectionEndpoint:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = repos.study_endpoint_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order
            )

            # sync with DB and save the update
            repos.study_endpoint_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just added
            new_selection, order = selection_aggregate.get_specific_endpoint_selection(
                study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            # add the objective and return
            return self._transform_single_to_response_model(
                new_selection,
                order,
                study_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    def _patch_prepare_new_study_endpoint(
        self,
        request_study_endpoint: StudySelectionEndpointInput,
        current_study_endpoint: StudySelectionEndpointVO,
    ) -> StudySelectionEndpointVO:
        endpoint_repo = self._repos.endpoint_repository
        timeframe_repo = self._repos.timeframe_repository
        endpoint_ar: EndpointAR | None
        if request_study_endpoint.endpoint_uid:
            endpoint_ar = endpoint_repo.find_by_uid(request_study_endpoint.endpoint_uid)
        elif current_study_endpoint.endpoint_uid:
            endpoint_ar = endpoint_repo.find_by_uid(current_study_endpoint.endpoint_uid)
        else:
            endpoint_ar = None
        timeframe_ar: TimeframeAR | None
        if request_study_endpoint.timeframe_uid:
            timeframe_ar = timeframe_repo.find_by_uid(
                request_study_endpoint.timeframe_uid
            )
        elif current_study_endpoint.timeframe_uid:
            timeframe_ar = timeframe_repo.find_by_uid(
                current_study_endpoint.timeframe_uid
            )
        else:
            timeframe_ar = None

        # transform current to input model
        transformed_current = StudySelectionEndpointInput(
            endpoint_uid=current_study_endpoint.endpoint_uid,
            endpoint_level_uid=current_study_endpoint.endpoint_level_uid,
            endpoint_sublevel_uid=current_study_endpoint.endpoint_sublevel_uid,
            endpoint_units=EndpointUnitsInput(
                units=[unit["uid"] for unit in current_study_endpoint.endpoint_units],
                separator=current_study_endpoint.unit_separator,
            ),
            study_objective_uid=current_study_endpoint.study_objective_uid,
            timeframe_uid=current_study_endpoint.timeframe_uid,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_endpoint,
            reference_base_model=transformed_current,
        )

        # get order from the endpoint level CT term
        if request_study_endpoint.endpoint_level_uid is not None:
            endpoint_level_order = (
                self._repos.ct_term_name_repository.term_specific_order_by_uid(
                    uid=request_study_endpoint.endpoint_level_uid
                )
            )
        else:
            endpoint_level_order = None

        if request_study_endpoint.endpoint_units:
            units = [
                {"uid": unit} for unit in request_study_endpoint.endpoint_units.units
            ]
            separator = request_study_endpoint.endpoint_units.separator
        else:
            units = None
            separator = None

        return StudySelectionEndpointVO.from_input_values(
            endpoint_uid=request_study_endpoint.endpoint_uid,
            endpoint_version=endpoint_ar.item_metadata.version if endpoint_ar else None,
            endpoint_level_uid=request_study_endpoint.endpoint_level_uid,
            endpoint_sublevel_uid=request_study_endpoint.endpoint_sublevel_uid,
            endpoint_units=tuple(units or []),
            timeframe_uid=request_study_endpoint.timeframe_uid,
            timeframe_version=(
                timeframe_ar.item_metadata.version if timeframe_ar else None
            ),
            unit_separator=separator,
            study_objective_uid=request_study_endpoint.study_objective_uid,
            study_selection_uid=current_study_endpoint.study_selection_uid,
            endpoint_level_order=endpoint_level_order,
            author_id=self.author,
        )

    @db.transaction
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: StudySelectionEndpointInput,
    ) -> StudySelectionEndpoint:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = repos.study_endpoint_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # Load the current VO for updates
            current_vo, order = selection_aggregate.get_specific_endpoint_selection(
                study_selection_uid=study_selection_uid
            )

            # merge current with updates
            updated_selection = self._patch_prepare_new_study_endpoint(
                request_study_endpoint=selection_update_input,
                current_study_endpoint=current_vo,
            )

            endpoint_repo = self._repos.endpoint_repository
            timeframe_repo = self._repos.timeframe_repository
            # let the aggregate update the value object
            selection_aggregate.update_selection(
                updated_study_endpoint_selection=updated_selection,
                study_objective_exist_callback=repos.study_objective_repository.study_objective_exists,
                endpoint_exist_callback=endpoint_repo.check_exists_final_version,
                timeframe_exist_callback=timeframe_repo.check_exists_final_version,
                ct_term_exists_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                unit_definition_exists_callback=repos.unit_definition_repository.check_exists_final_version,
            )
            selection_aggregate.validate()

            # sync with DB and save the update
            repos.study_endpoint_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just updated
            new_selection, order = selection_aggregate.get_specific_endpoint_selection(
                study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            # add the objective and return
            return self._transform_single_to_response_model(
                new_selection,
                order,
                study_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    @db.transaction
    def update_selection_to_latest_version_of_endpoint(
        self, study_uid: str, study_selection_uid: str
    ):
        selection_ar, selection, order = self._get_specific_endpoint_selection_by_uids(
            study_uid, study_selection_uid, for_update=True
        )
        endpoint_uid = selection.endpoint_uid
        endpoint_ar = self._repos.endpoint_repository.find_by_uid(endpoint_uid)
        if endpoint_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            endpoint_ar.approve(self.author)
            self._repos.endpoint_repository.save(endpoint_ar)
        elif endpoint_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                msg="Cannot add retired objective as selection. Please reactivate."
            )
        new_selection = selection.update_endpoint_version(
            endpoint_ar.item_metadata.version
        )
        selection_ar.update_selection(
            new_selection, endpoint_exist_callback=lambda x: True
        )
        self._repos.study_endpoint_repository.save(selection_ar, self.author)
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_uid
        )
        return self._transform_single_to_response_model(
            new_selection,
            order,
            study_uid,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    @db.transaction
    def update_selection_to_latest_version_of_timeframe(
        self, study_uid: str, study_selection_uid: str
    ):
        selection_ar, selection, order = self._get_specific_endpoint_selection_by_uids(
            study_uid, study_selection_uid, for_update=True
        )
        timeframe_uid = selection.timeframe_uid
        timeframe_ar = self._repos.timeframe_repository.find_by_uid(timeframe_uid)
        if timeframe_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            timeframe_ar.approve(self.author)
            self._repos.timeframe_repository.save(timeframe_ar)
        elif timeframe_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                msg="Cannot add retired timeframe as selection. Please reactivate."
            )
        new_selection = selection.update_timeframe_version(
            timeframe_ar.item_metadata.version
        )
        selection_ar.update_selection(
            new_selection, timeframe_exist_callback=lambda x: True
        )
        self._repos.study_endpoint_repository.save(selection_ar, self.author)
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_uid
        )
        return self._transform_single_to_response_model(
            new_selection,
            order,
            study_uid,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    @db.transaction
    def update_selection_accept_versions(
        self, study_uid: str, study_selection_uid: str
    ):
        selection: StudySelectionEndpointVO
        selection_ar, selection, order = self._get_specific_endpoint_selection_by_uids(
            study_uid, study_selection_uid, for_update=True
        )
        endpoint_uid = selection.endpoint_uid
        endpoint_ar = self._repos.endpoint_repository.find_by_uid(endpoint_uid)
        if endpoint_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            endpoint_ar.approve(self.author)
            self._repos.endpoint_repository.save(endpoint_ar)
        elif endpoint_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                msg="Cannot add retired objective as selection. Please reactivate."
            )
        new_selection = selection.accept_versions()
        selection_ar.update_selection(
            new_selection, endpoint_exist_callback=lambda x: True
        )
        self._repos.study_endpoint_repository.save(selection_ar, self.author)
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_uid
        )
        return self._transform_single_to_response_model(
            new_selection,
            order,
            study_uid,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    def _transform_history_to_response_model(
        self,
        study_selection_history: list[StudyEndpointSelectionHistory],
        study_uid: str,
        effective_dates: Sequence[datetime | None],
    ) -> list[StudySelectionEndpoint]:
        # Transform each history to the response model
        result = []

        for history, effective_date in zip(study_selection_history, effective_dates):
            result.append(
                StudySelectionEndpoint.from_study_selection_history(
                    study_selection_history=history,
                    study_uid=study_uid,
                    get_endpoint_by_uid=self._transform_endpoint_model,
                    get_timeframe_by_uid=self._transform_timeframe_model,
                    get_study_objective_by_uid=self._transform_single_study_objective_to_model,
                    find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                    effective_date=effective_date,
                )
            )
        return result

    @db.transaction
    def get_all_selection_audit_trail(
        self, study_uid: str
    ) -> list[StudySelectionEndpoint]:
        repos = self._repos
        try:
            selection_history = repos.study_endpoint_repository.find_selection_history(
                study_uid
            )
            # Extract start dates from the selection history
            start_dates = [history.start_date for history in selection_history]

            # Extract effective dates for each version based on the start dates
            effective_dates = (
                self._extract_multiple_version_study_standards_effective_date(
                    study_uid=study_uid, list_of_start_dates=start_dates
                )
            )
            return self._transform_history_to_response_model(
                selection_history,
                study_uid,
                effective_dates=effective_dates,
            )
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection_audit_trail(
        self, study_uid: str, study_selection_uid: str
    ) -> list[StudySelectionEndpoint]:
        repos = self._repos
        try:
            selection_history = repos.study_endpoint_repository.find_selection_history(
                study_uid, study_selection_uid
            )
            # Extract start dates from the selection history
            start_dates = [history.start_date for history in selection_history]

            # Extract effective dates for each version based on the start dates
            effective_dates = (
                self._extract_multiple_version_study_standards_effective_date(
                    study_uid=study_uid, list_of_start_dates=start_dates
                )
            )
            return self._transform_history_to_response_model(
                selection_history,
                study_uid,
                effective_dates=effective_dates,
            )
        finally:
            repos.close()
