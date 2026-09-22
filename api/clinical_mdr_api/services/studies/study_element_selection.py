from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from fastapi import status
from neomodel import db

from clinical_mdr_api.domain_repositories.study_selections.study_design_cell_repository import (
    StudyDesignCellRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_element_repository import (
    SelectionHistoryElement,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.study_selections.study_selection_element import (
    StudySelectionElementAR,
    StudySelectionElementVO,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyElementTypes,
    StudySelectionElement,
    StudySelectionElementBatchInput,
    StudySelectionElementBatchOutput,
    StudySelectionElementBatchUpdateInput,
    StudySelectionElementCreateInput,
    StudySelectionElementInput,
    StudySelectionElementVersion,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    create_duration_object_from_api_input,
    ensure_transaction,
    fill_missing_values_in_base_model_from_reference_base_model,
    get_unit_def_uid_or_none,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.studies.study_compound_dosing_selection import (
    StudyCompoundDosingRelationMixin,
)
from clinical_mdr_api.services.studies.study_selection_base import StudySelectionMixin
from common import exceptions
from common.auth.user import user


@dataclass
class _ElementSkipIndexEntry:
    vo: StudySelectionElementVO


@dataclass
class _ElementSkipIndexes:
    by_name: dict[str, list[_ElementSkipIndexEntry]]
    by_short_name: dict[str, list[_ElementSkipIndexEntry]]

    @classmethod
    def from_aggregate(
        cls, aggregate: StudySelectionElementAR
    ) -> "_ElementSkipIndexes":
        indexes = cls(by_name={}, by_short_name={})
        for vo in aggregate.study_elements_selection:
            indexes.register_vo(vo)
        return indexes

    def register_vo(self, vo: StudySelectionElementVO) -> None:
        entry = _ElementSkipIndexEntry(vo=vo)
        if vo.name:
            self.by_name.setdefault(vo.name, []).append(entry)
        if vo.short_name:
            self.by_short_name.setdefault(vo.short_name, []).append(entry)


class StudyElementSelectionService(
    StudyCompoundDosingRelationMixin, StudySelectionMixin
):
    _repos: MetaRepository

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionElementAR | None,
        study_value_version: str | None = None,
    ) -> list[StudySelectionElement]:
        if study_selection is None:
            return []

        result = []
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_selection.study_uid,
            study_value_version=study_value_version,
        )
        # go over each VO study element selection object
        for order, selection in enumerate(
            study_selection.study_elements_selection, start=1
        ):
            result.append(
                self._transform_single_to_response_model(
                    selection,
                    order=order,
                    study_uid=study_selection.study_uid,
                    study_value_version=study_value_version,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
            )
        return result

    def _transform_single_to_response_model(
        self,
        study_selection: StudySelectionElementVO,
        order: int,
        study_uid: str,
        terms_at_specific_datetime: datetime | None,
        study_value_version: str | None = None,
    ) -> StudySelectionElement:
        repos = self._repos
        return StudySelectionElement.from_study_selection_element_ar_and_order(
            study_uid,
            study_selection,
            order,
            get_term_element_type_by_element_subtype=repos.study_element_repository.get_element_type_term_uid_by_element_subtype_term_uid,
            find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            find_all_study_time_units=self._repos.unit_definition_repository.find_all,
            study_value_version=study_value_version,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    def _transform_each_history_to_response_model(
        self,
        study_selection_history: SelectionHistoryElement,
        study_uid: str,
        effective_date: datetime | None = None,
    ) -> StudySelectionElement:
        repos = self._repos
        return StudySelectionElement.from_study_selection_history(
            study_selection_history=study_selection_history,
            study_uid=study_uid,
            get_term_element_type_by_element_subtype=repos.study_element_repository.get_element_type_term_uid_by_element_subtype_term_uid,
            find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            find_all_study_time_units=self._repos.unit_definition_repository.find_all,
            effective_date=effective_date,
        )

    @db.transaction
    def get_all_selection_audit_trail(
        self, study_uid: str
    ) -> list[StudySelectionElementVersion]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_element_repository.find_selection_history(study_uid)
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(msg=value_error.args[0])
            unique_list_uids = list({x.study_selection_uid for x in selection_history})
            unique_list_uids.sort()
            # list of all study_elements
            data: list[StudySelectionElementVersion] = []
            for i_unique in unique_list_uids:
                ith_selection_history = []
                # gather the selection history of the i_unique Uid
                for selection in selection_history:
                    if selection.study_selection_uid == i_unique:
                        ith_selection_history.append(selection)

                # Extract start dates from the selection history
                start_dates = [history.start_date for history in ith_selection_history]

                # Extract effective dates for each version based on the start dates
                effective_dates = (
                    self._extract_multiple_version_study_standards_effective_date(
                        study_uid=study_uid, list_of_start_dates=start_dates
                    )
                )

                # Transform each history to the response model and convert to dictionary format
                versions = [
                    self._transform_each_history_to_response_model(
                        history, study_uid, effective_date
                    ).model_dump()
                    for history, effective_date in zip(
                        ith_selection_history, effective_dates
                    )
                ]
                if not data:
                    data = calculate_diffs(versions, StudySelectionElementVersion)
                else:
                    data.extend(calculate_diffs(versions, StudySelectionElementVersion))
            return data
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection_audit_trail(
        self, study_uid: str, study_selection_uid: str
    ) -> list[StudySelectionElementVersion]:
        repos = self._repos
        try:
            selection_history = repos.study_element_repository.find_selection_history(
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

            # Transform each history to the response model and convert to dictionary format
            versions = [
                self._transform_each_history_to_response_model(
                    history, study_uid, effective_date
                ).model_dump()
                for history, effective_date in zip(selection_history, effective_dates)
            ]
            data = calculate_diffs(versions, StudySelectionElementVersion)
            return data
        finally:
            repos.close()

    def make_selection(
        self,
        study_uid: str,
        selection_create_input: StudySelectionElementCreateInput,
    ) -> StudySelectionElement:
        repos = self._repos

        try:
            # Load aggregate
            with db.transaction:
                # create new VO to add
                new_selection = StudySelectionElementVO.from_input_values(
                    study_uid=study_uid,
                    author_id=self.author,
                    name=selection_create_input.name,
                    short_name=selection_create_input.short_name,
                    code=selection_create_input.code,
                    description=selection_create_input.description,
                    planned_duration=(
                        create_duration_object_from_api_input(
                            value=selection_create_input.planned_duration.duration_value,
                            unit=get_unit_def_uid_or_none(
                                selection_create_input.planned_duration.duration_unit_code
                            ),
                            find_duration_name_by_code=self._repos.unit_definition_repository.find_by_uid_2,
                        )
                        if selection_create_input.planned_duration
                        else None
                    ),
                    start_rule=selection_create_input.start_rule,
                    end_rule=selection_create_input.end_rule,
                    element_colour=selection_create_input.element_colour,
                    element_subtype_uid=selection_create_input.element_subtype_uid,
                    study_compound_dosing_count=0,
                    generate_uid_callback=repos.study_element_repository.generate_uid,
                )
                # add VO to aggregate
                selection_aggregate: StudySelectionElementAR = (
                    repos.study_element_repository.find_by_study(
                        study_uid=study_uid, for_update=True
                    )
                )
                assert selection_aggregate is not None
                selection_aggregate.add_element_selection(
                    new_selection,
                    self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                )

                ## sync with DB and save the update
                repos.study_element_repository.save(selection_aggregate, self.author)

                # Fetch the new selection which was just added
                (
                    new_selection,
                    order,
                ) = selection_aggregate.get_specific_element_selection(
                    new_selection.study_selection_uid
                )
                terms_at_specific_datetime = (
                    self._extract_study_standards_effective_date(study_uid=study_uid)
                )
                # add the element and return
                return StudySelectionElement.from_study_selection_element_ar_and_order(
                    study_uid=study_uid,
                    selection=new_selection,
                    order=order,
                    get_term_element_type_by_element_subtype=repos.study_element_repository.get_element_type_term_uid_by_element_subtype_term_uid,
                    find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                    find_all_study_time_units=self._repos.unit_definition_repository.find_all,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
        finally:
            repos.close()

    @db.transaction
    def get_all_selection(
        self,
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[StudySelectionElement]:
        repos = MetaRepository()
        try:
            element_selection_ar = repos.study_element_repository.find_by_study(
                study_uid, study_value_version=study_value_version
            )
            return service_level_generic_filtering(
                items=self._transform_all_to_response_model(
                    element_selection_ar, study_value_version=study_value_version
                ),
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
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            # cascade delete
            # if the element has connected design cells
            design_cells_on_element = None
            if repos.study_element_repository.element_specific_has_connected_cell(
                study_uid=study_uid, element_uid=study_selection_uid
            ):
                design_cells_on_element = (
                    StudyDesignCellRepository.find_all_design_cells_by_study(
                        study_uid=study_uid,
                        study_element_uid=study_selection_uid,
                    )
                )

            if design_cells_on_element is not None:
                for i_design_cell in design_cells_on_element:
                    study_design_cell = (
                        self._repos.study_design_cell_repository.find_by_uid(
                            study_uid=study_uid, uid=i_design_cell.uid
                        )
                    )
                    self._repos.study_design_cell_repository.delete(
                        study_uid, i_design_cell.uid, self.author
                    )
                    all_design_cells = self._repos.study_design_cell_repository.find_all_design_cells_by_study(
                        study_uid
                    )
                    # shift one order more to fit the modified
                    for design_cell in all_design_cells[study_design_cell.order - 1 :]:
                        design_cell.order -= 1
                        self._repos.study_design_cell_repository.save(
                            design_cell, author_id=self.author, create=False
                        )

            # Load aggregate
            selection_aggregate = repos.study_element_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            selection_aggregate.remove_element_selection(study_selection_uid)

            # cascade delete for compound dosings
            self._delete_compound_dosing_selections(
                study_uid, "study_element_uid", study_selection_uid
            )

            # sync with DB and save the update
            repos.study_element_repository.save(selection_aggregate, self.author)
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        study_value_version: str | None = None,
    ) -> StudySelectionElement:
        repos = self._repos
        (
            _selection_aggregate,
            new_selection,
            order,
        ) = self._get_specific_element_selection_by_uids(
            study_uid, study_selection_uid, study_value_version=study_value_version
        )
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_uid,
            study_value_version=study_value_version,
        )
        return StudySelectionElement.from_study_selection_element_ar_and_order(
            study_uid=study_uid,
            selection=new_selection,
            order=order,
            get_term_element_type_by_element_subtype=repos.study_element_repository.get_element_type_term_uid_by_element_subtype_term_uid,
            find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            find_all_study_time_units=self._repos.unit_definition_repository.find_all,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    def _patch_prepare_new_study_element(
        self,
        request_study_element: StudySelectionElementInput,
        current_study_element: StudySelectionElementVO,
        find_duration_name_by_code: Callable[..., UnitDefinitionAR | None],
    ) -> StudySelectionElementVO:
        # transform current to input model
        transformed_current = StudySelectionElementInput.from_study_selection_element(
            selection=current_study_element,
            find_all_study_time_units=self._repos.unit_definition_repository.find_all,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_element,
            reference_base_model=transformed_current,
        )

        return StudySelectionElementVO.from_input_values(
            study_uid=current_study_element.study_uid,
            name=request_study_element.name,
            short_name=request_study_element.short_name,
            code=request_study_element.code,
            description=request_study_element.description,
            planned_duration=(
                create_duration_object_from_api_input(
                    value=request_study_element.planned_duration.duration_value,
                    unit=get_unit_def_uid_or_none(
                        request_study_element.planned_duration.duration_unit_code
                    ),
                    find_duration_name_by_code=find_duration_name_by_code,
                )
                if request_study_element.planned_duration is not None
                else None
            ),
            start_rule=request_study_element.start_rule,
            end_rule=request_study_element.end_rule,
            element_colour=request_study_element.element_colour,
            element_subtype_uid=request_study_element.element_subtype_uid,
            study_compound_dosing_count=current_study_element.study_compound_dosing_count,
            study_selection_uid=current_study_element.study_selection_uid,
            author_id=self.author,
        )

    @ensure_transaction(db)
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: StudySelectionElementInput,
        validate: bool = True,
    ) -> StudySelectionElement:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate: StudySelectionElementAR = (
                repos.study_element_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            assert selection_aggregate is not None

            # Load the current VO for updates
            current_vo, order = selection_aggregate.get_specific_object_selection(
                study_selection_uid=study_selection_uid
            )

            # merge current with updates
            updated_selection = self._patch_prepare_new_study_element(
                request_study_element=selection_update_input,
                current_study_element=current_vo,
                find_duration_name_by_code=self._repos.unit_definition_repository.find_by_uid_2,
            )

            # let the aggregate update the value object
            selection_aggregate.update_selection(
                updated_study_element_selection=updated_selection,
                ct_term_exists_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                validate=validate,
            )
            # sync with DB and save the update
            repos.study_element_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just updated
            new_selection, order = selection_aggregate.get_specific_object_selection(
                study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            # add the element and return
            return StudySelectionElement.from_study_selection_element_ar_and_order(
                study_uid=study_uid,
                selection=new_selection,
                order=order,
                get_term_element_type_by_element_subtype=repos.study_element_repository.get_element_type_term_uid_by_element_subtype_term_uid,
                find_codelist_term_by_uid_and_submval=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                find_all_study_time_units=self._repos.unit_definition_repository.find_all,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    def get_allowed_configs(self):
        resp = []
        for item in self._repos.study_element_repository.get_allowed_configs():
            resp.append(
                StudyElementTypes(
                    subtype=item[0],
                    subtype_name=item[1],
                    type=item[2],
                    type_name=item[3],
                )
            )
        return resp

    @db.transaction
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> StudySelectionElement:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = repos.study_element_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order
            )

            # sync with DB and save the update
            repos.study_element_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just added
            new_selection, order = selection_aggregate.get_specific_element_selection(
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

    def get_distinct_values_for_header(
        self,
        field_name: str,
        study_uid: str | None = None,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
        study_value_version: str | None = None,
    ):
        all_items = self.get_all_selection(
            study_uid, study_value_version=study_value_version
        )

        header_values = service_level_generic_header_filtering(
            items=all_items.items,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )

        return header_values

    @staticmethod
    def _subtypes_match(
        existing_subtype_uid: str | None, incoming_subtype_uid: str | None
    ) -> bool:
        return (existing_subtype_uid or None) == (incoming_subtype_uid or None)

    def _create_vo_from_create_input(
        self,
        study_uid: str,
        spec: StudySelectionElementCreateInput,
        study_selection_uid: str | None = None,
    ) -> StudySelectionElementVO:
        repos = self._repos
        return StudySelectionElementVO.from_input_values(
            study_uid=study_uid,
            author_id=self.author,
            name=spec.name,
            short_name=spec.short_name,
            code=spec.code,
            description=spec.description,
            planned_duration=(
                create_duration_object_from_api_input(
                    value=spec.planned_duration.duration_value,
                    unit=get_unit_def_uid_or_none(
                        spec.planned_duration.duration_unit_code
                    ),
                    find_duration_name_by_code=repos.unit_definition_repository.find_by_uid_2,
                )
                if spec.planned_duration
                else None
            ),
            start_rule=spec.start_rule,
            end_rule=spec.end_rule,
            element_colour=spec.element_colour,
            element_subtype_uid=spec.element_subtype_uid,
            study_compound_dosing_count=0,
            study_selection_uid=study_selection_uid,
            generate_uid_callback=repos.study_element_repository.generate_uid,
        )

    def _find_skip_match_vo(
        self,
        spec: StudySelectionElementCreateInput,
        indexes: _ElementSkipIndexes,
    ) -> StudySelectionElementVO | None:
        if spec.name and spec.name in indexes.by_name:
            for entry in indexes.by_name[spec.name]:
                if self._subtypes_match(
                    entry.vo.element_subtype_uid, spec.element_subtype_uid
                ):
                    return entry.vo
        if spec.short_name and spec.short_name in indexes.by_short_name:
            for entry in indexes.by_short_name[spec.short_name]:
                if self._subtypes_match(
                    entry.vo.element_subtype_uid, spec.element_subtype_uid
                ):
                    return entry.vo
        return None

    def _vo_to_response_element(
        self,
        study_uid: str,
        selection: StudySelectionElementVO,
        order: int,
        terms_at_specific_datetime: datetime | None,
    ) -> StudySelectionElement:
        return self._transform_single_to_response_model(
            study_selection=selection,
            order=order,
            study_uid=study_uid,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    def _map_source_study_elements_to_create_inputs(
        self, study_source_uid: str
    ) -> list[StudySelectionElementCreateInput]:
        repos = self._repos
        try:
            selection_ar = repos.study_element_repository.find_by_study(
                study_source_uid
            )
            specs: list[StudySelectionElementCreateInput] = []
            for selection in selection_ar.study_elements_selection:
                specs.append(
                    StudySelectionElementCreateInput(
                        name=selection.name,
                        short_name=selection.short_name,
                        code=selection.code,
                        description=selection.description,
                        start_rule=selection.start_rule,
                        end_rule=selection.end_rule,
                        element_colour=selection.element_colour,
                        element_subtype_uid=selection.element_subtype_uid,
                    )
                )
            return specs
        finally:
            repos.close()

    @ensure_transaction(db)
    def _create_elements_with_skip_deduplication(
        self,
        study_uid: str,
        specs: list[StudySelectionElementCreateInput],
    ) -> list[StudySelectionElementBatchOutput]:
        repos = self._repos
        results: list[StudySelectionElementBatchOutput] = []
        if not specs:
            return results

        try:
            selection_aggregate: StudySelectionElementAR = (
                repos.study_element_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )
            assert selection_aggregate is not None
            indexes = _ElementSkipIndexes.from_aggregate(selection_aggregate)
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            created_vo_uids: set[str] = set()

            for spec in specs:
                skip_vo = self._find_skip_match_vo(spec, indexes)
                if skip_vo is not None:
                    _, order = selection_aggregate.get_specific_object_selection(
                        skip_vo.study_selection_uid
                    )
                    notification = None
                    if spec.name and spec.name in indexes.by_name:
                        notification = (
                            f"Element '{spec.name}' with the same name and element sub type "
                            "already exists; creation skipped."
                        )
                    elif spec.short_name and spec.short_name in indexes.by_short_name:
                        notification = (
                            f"Element short name '{spec.short_name}' with the same element "
                            "sub type already exists; creation skipped."
                        )
                    results.append(
                        StudySelectionElementBatchOutput(
                            response_code=status.HTTP_200_OK,
                            content=self._vo_to_response_element(
                                study_uid=study_uid,
                                selection=skip_vo,
                                order=order,
                                terms_at_specific_datetime=terms_at_specific_datetime,
                            ),
                            notification=notification,
                        )
                    )
                    continue

                new_selection = self._create_vo_from_create_input(
                    study_uid=study_uid,
                    spec=spec,
                )
                selection_aggregate.add_element_selection(
                    new_selection,
                    self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                )
                indexes.register_vo(new_selection)
                created_vo_uids.add(new_selection.study_selection_uid)
                new_selection, order = (
                    selection_aggregate.get_specific_element_selection(
                        new_selection.study_selection_uid
                    )
                )
                results.append(
                    StudySelectionElementBatchOutput(
                        response_code=status.HTTP_201_CREATED,
                        content=self._vo_to_response_element(
                            study_uid=study_uid,
                            selection=new_selection,
                            order=order,
                            terms_at_specific_datetime=terms_at_specific_datetime,
                        ),
                    )
                )

            for element_vo in selection_aggregate.study_elements_selection:
                if element_vo.study_selection_uid in created_vo_uids:
                    element_vo.validate(
                        self._repos.ct_term_name_repository.term_specific_exists_by_uid
                    )

            repos.study_element_repository.save(selection_aggregate, self.author)
        finally:
            repos.close()
        return results

    @ensure_transaction(db)
    def copy_elements_from_study(
        self, study_uid: str, study_source_uid: str
    ) -> list[StudySelectionElementBatchOutput]:
        exceptions.ValidationException.raise_if(
            study_source_uid == study_uid,
            msg="study_source_uid must differ from the target study.",
        )
        self.check_if_study_exists(study_uid)
        self.check_if_study_exists(study_source_uid)
        specs = self._map_source_study_elements_to_create_inputs(study_source_uid)
        return self._create_elements_with_skip_deduplication(study_uid, specs)

    @ensure_transaction(db)
    def handle_batch_operations(
        self,
        study_uid: str,
        operations: list[StudySelectionElementBatchInput],
    ) -> list[StudySelectionElementBatchOutput]:
        results: list[StudySelectionElementBatchOutput | None] = [None] * len(
            operations
        )
        patched_element_uids: set[str] = set()
        try:
            index = 0
            while index < len(operations):
                operation = operations[index]
                if operation.method == "PATCH":
                    if isinstance(
                        operation.content, StudySelectionElementBatchUpdateInput
                    ):
                        item = self.patch_selection(
                            study_uid=study_uid,
                            study_selection_uid=operation.content.element_uid,
                            selection_update_input=operation.content,
                            validate=False,
                        )
                        patched_element_uids.add(operation.content.element_uid)
                        results[index] = StudySelectionElementBatchOutput(
                            response_code=status.HTTP_200_OK,
                            content=item,
                        )
                    else:
                        raise exceptions.ValidationException(
                            msg="PATCH operation requires StudySelectionElementBatchUpdateInput as request payload."
                        )
                    index += 1
                elif operation.method == "POST":
                    post_specs: list[StudySelectionElementCreateInput] = []
                    post_indices: list[int] = []
                    while (
                        index < len(operations) and operations[index].method == "POST"
                    ):
                        content = operations[index].content
                        if not isinstance(content, StudySelectionElementCreateInput):
                            raise exceptions.ValidationException(
                                msg="POST operation requires StudySelectionElementCreateInput as request payload."
                            )
                        post_specs.append(content)
                        post_indices.append(index)
                        index += 1
                    create_results = self._create_elements_with_skip_deduplication(
                        study_uid=study_uid,
                        specs=post_specs,
                    )
                    for result_index, create_result in zip(
                        post_indices, create_results
                    ):
                        results[result_index] = create_result
                else:
                    raise exceptions.MethodNotAllowedException(method=operation.method)

            if patched_element_uids:
                element_ar: StudySelectionElementAR = (
                    self._repos.study_element_repository.find_by_study(
                        study_uid=study_uid
                    )
                )
                for element_vo in element_ar.study_elements_selection:
                    if element_vo.study_selection_uid in patched_element_uids:
                        element_vo.validate(
                            self._repos.ct_term_name_repository.term_specific_exists_by_uid
                        )
        except exceptions.MDRApiBaseException as error:
            raise error
        return [result for result in results if result is not None]
