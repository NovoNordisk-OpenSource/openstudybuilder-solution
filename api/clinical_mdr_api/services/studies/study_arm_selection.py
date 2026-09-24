from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import status
from neomodel import db

from clinical_mdr_api.domain_repositories.study_selections.study_arm_repository import (
    SelectionHistoryArm,
)
from clinical_mdr_api.domains.study_selections.study_selection_arm import (
    StudySelectionArmAR,
    StudySelectionArmVO,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import SimpleTermModel
from clinical_mdr_api.models.study_selections.study_selection import (
    STUDY_ARM_CODE_MAX_LENGTH,
    STUDY_ARM_NAME_MAX_LENGTH,
    STUDY_ARM_SHORT_NAME_MAX_LENGTH,
    CompactStudyArm,
    StudySelectionArm,
    StudySelectionArmBatchInput,
    StudySelectionArmBatchOutput,
    StudySelectionArmBatchUpdateInput,
    StudySelectionArmCreateInput,
    StudySelectionArmInput,
    StudySelectionArmVersion,
    StudySelectionArmWithConnectedBranchArms,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    ensure_transaction,
    fill_missing_values_in_base_model_from_reference_base_model,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.studies.study_selection_base import StudySelectionMixin
from common import exceptions
from common.auth.user import user
from common.config import settings
from common.telemetry import trace_calls


@dataclass
class _ArmConflictIndexEntry:
    vo: StudySelectionArmVO


@dataclass
class _ArmConflictIndexes:
    by_name: dict[str, _ArmConflictIndexEntry]
    by_short_name: dict[str, _ArmConflictIndexEntry]
    by_code: dict[str, _ArmConflictIndexEntry]
    by_randomization_group: dict[str, _ArmConflictIndexEntry]

    @classmethod
    def from_aggregate(cls, aggregate: StudySelectionArmAR) -> "_ArmConflictIndexes":
        indexes = cls(
            by_name={}, by_short_name={}, by_code={}, by_randomization_group={}
        )
        for vo in aggregate.study_arms_selection:
            indexes.register_vo(vo)
        return indexes

    def register_vo(self, vo: StudySelectionArmVO) -> None:
        entry = _ArmConflictIndexEntry(vo=vo)
        if vo.name:
            self.by_name[vo.name] = entry
        if vo.short_name:
            self.by_short_name[vo.short_name] = entry
        if vo.code:
            self.by_code[vo.code] = entry
        if vo.randomization_group:
            self.by_randomization_group[vo.randomization_group] = entry


class StudyArmSelectionService(StudySelectionMixin):
    _repos: MetaRepository

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionArmAR | None,
        study_value_version: str | None = None,
    ) -> list[StudySelectionArmWithConnectedBranchArms]:
        if study_selection is None:
            return []

        result = []
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_selection.study_uid,
            study_value_version=study_value_version,
        )
        for order, selection in enumerate(
            study_selection.study_arms_selection, start=1
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
        study_selection: StudySelectionArmVO,
        order: int,
        study_uid: str,
        study_value_version: str | None = None,
        terms_at_specific_datetime: datetime | None = None,
    ) -> StudySelectionArmWithConnectedBranchArms:
        # pylint: disable=line-too-long
        return StudySelectionArmWithConnectedBranchArms.from_study_selection_arm_ar__order__connected_branch_arms(
            study_uid=study_uid,
            selection=study_selection,
            order=order,
            find_codelist_term_arm_type=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            find_multiple_connected_branch_arm=self._find_branch_arms_connected_to_arm_uid,
            study_value_version=study_value_version,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    def get_all_selections_for_all_studies(
        self,
        project_name: str | None = None,
        project_number: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[StudySelectionArmWithConnectedBranchArms]:
        repos = self._repos
        arm_selection_ars = repos.study_arm_repository.find_all(
            project_name=project_name,
            project_number=project_number,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for selection_ar in arm_selection_ars:
            parsed_selections = self._transform_all_to_response_model(selection_ar)
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
    ):
        repos = self._repos

        if study_uid:
            arm_selection_ar = repos.study_arm_repository.find_by_study(study_uid)

            header_values = service_level_generic_header_filtering(
                items=self._transform_all_to_response_model(arm_selection_ar),
                field_name=field_name,
                search_string=search_string,
                filter_by=filter_by,
                filter_operator=filter_operator,
                page_size=page_size,
            )

            return header_values

        arm_selection_ars = repos.study_arm_repository.find_all(
            project_name=project_name,
            project_number=project_number,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for selection_ar in arm_selection_ars:
            parsed_selections = self._transform_all_to_response_model(selection_ar)
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

    @trace_calls
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
    ) -> GenericFilteringReturn[StudySelectionArmWithConnectedBranchArms]:
        repos = MetaRepository()
        try:
            arm_selection_ar = repos.study_arm_repository.find_by_study(
                study_uid, study_value_version=study_value_version
            )

            filtered_items = service_level_generic_filtering(
                items=self._transform_all_to_response_model(
                    arm_selection_ar, study_value_version=study_value_version
                ),
                filter_by=filter_by,
                filter_operator=filter_operator,
                sort_by=sort_by,
                total_count=total_count,
                page_number=page_number,
                page_size=page_size,
            )

            return filtered_items
        finally:
            repos.close()

    def get_arms_branches_and_cohorts(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> list[CompactStudyArm]:
        repos = MetaRepository()
        try:
            arms_branches_and_cohorts = (
                repos.study_arm_repository.get_arms_branches_and_cohorts(
                    study_uid, study_value_version=study_value_version
                )
            )
            result = []
            for study_arm in arms_branches_and_cohorts:
                result.append(
                    CompactStudyArm.from_repository_output(arm_structure=study_arm)
                )
            return result
        finally:
            repos.close()

    @ensure_transaction(db)
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            # cascade delete
            # delete study branch arms assigned to arm
            branch_arms_on_arm = (
                repos.study_branch_arm_repository.get_branch_arms_connected_to_arm(
                    study_uid=study_uid, study_arm_uid=study_selection_uid
                )
            )
            design_cells_on_branch_arm: list[Any] = []
            design_cells_to_delete_from_branch_arm: list[Any] = []
            for i_branch_arm in branch_arms_on_arm:
                cascade_deletion_last_branch = False
                # if the branch_arm has connected design cells
                if repos.study_branch_arm_repository.branch_arm_specific_has_connected_cell(
                    study_uid=study_uid,
                    branch_arm_uid=i_branch_arm.uid,
                ):
                    design_cells_on_branch_arm = self._repos.study_design_cell_repository.find_all_design_cells_by_study(
                        study_uid=study_uid, study_branch_arm_uid=i_branch_arm.uid
                    )
                    # if the study_branch_arm is the last StudyBranchArm of its StudyArm root
                    if repos.study_branch_arm_repository.branch_arm_specific_is_last_on_arm_root(
                        study_uid=study_uid,
                        arm_root_uid=study_selection_uid,
                        branch_arm_uid=i_branch_arm.uid,
                    ):
                        # switch all the study designcells to the study branch arm
                        cascade_deletion_last_branch = True

                    # else the study_branch_arm is not last StudyBranchArm of its StudyArm root, so delete studyDesignCells
                    else:
                        design_cells_to_delete_in_desc_order = reversed(
                            design_cells_on_branch_arm
                        )
                        for i_design_cell in design_cells_to_delete_in_desc_order:
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
                            for design_cell in all_design_cells[
                                study_design_cell.order - 1 :
                            ]:
                                design_cell.order -= 1
                                self._repos.study_design_cell_repository.save(
                                    design_cell, author_id=self.author, create=False
                                )
                # Load aggregate
                branch_arm_aggregate = repos.study_branch_arm_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
                # remove the connection
                branch_arm_aggregate.remove_branch_arm_selection(i_branch_arm.uid)

                # sync with DB and save the update
                repos.study_branch_arm_repository.save(
                    branch_arm_aggregate, self.author
                )

                if cascade_deletion_last_branch:
                    for i_design_cell in design_cells_on_branch_arm:
                        self._repos.study_design_cell_repository.patch_study_arm(
                            study_uid=study_uid,
                            design_cell_uid=i_design_cell.uid,
                            study_arm_uid=study_selection_uid,
                            author_id=self.author,
                            allow_none_arm_branch_arm=True,
                        )

            # delete study design cells assigned to arm
            design_cells_on_arm = []
            if repos.study_arm_repository.arm_specific_has_connected_cell(
                study_uid=study_uid, arm_uid=study_selection_uid
            ):
                design_cells_on_arm = self._repos.study_design_cell_repository.find_all_design_cells_by_study(
                    study_uid=study_uid, study_arm_uid=study_selection_uid
                )
            if design_cells_on_arm or design_cells_to_delete_from_branch_arm:
                # get design cells to delete that are connected to arm
                design_cells_to_delete_in_desc_order = reversed(design_cells_on_arm)
                for i_design_cell in design_cells_to_delete_in_desc_order:
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

            # delete arm
            # Load aggregate
            selection_aggregate = repos.study_arm_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            selection_aggregate.remove_arm_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_arm_repository.save(selection_aggregate, self.author)
        finally:
            repos.close()

    @ensure_transaction(db)
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> StudySelectionArmWithConnectedBranchArms:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = repos.study_arm_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order
            )

            # sync with DB and save the update
            repos.study_arm_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just added
            new_selection, order = selection_aggregate.get_specific_arm_selection(
                study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid,
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

    def _transform_each_history_to_response_model(
        self,
        study_selection_history: SelectionHistoryArm,
        study_uid: str,
        effective_date: datetime | None = None,
    ) -> StudySelectionArm:
        return StudySelectionArm.from_study_selection_history(
            study_selection_history=study_selection_history,
            study_uid=study_uid,
            find_codelist_term_arm_type=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            effective_date=effective_date,
        )

    def get_all_selection_audit_trail(
        self, study_uid: str
    ) -> list[StudySelectionArmVersion]:
        repos = self._repos
        try:
            try:
                selection_history = repos.study_arm_repository.find_selection_history(
                    study_uid
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(msg=value_error.args[0])

            unique_list_uids = list({x.study_selection_uid for x in selection_history})
            unique_list_uids.sort()
            # list of all study_arms
            data: list[Any] = []
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
                    data = calculate_diffs(versions, StudySelectionArmVersion)
                else:
                    data.extend(calculate_diffs(versions, StudySelectionArmVersion))
            return data
        finally:
            repos.close()

    def get_specific_selection_audit_trail(
        self, study_uid: str, study_selection_uid: str
    ) -> list[StudySelectionArmVersion]:
        repos = self._repos
        try:
            selection_history: list[SelectionHistoryArm] = (
                repos.study_arm_repository.find_selection_history(
                    study_uid, study_selection_uid
                )
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
            data = calculate_diffs(versions, StudySelectionArmVersion)
            return data
        finally:
            repos.close()

    # Helper function to find CT term names
    def find_term_name_by_uid(self, uid):
        return SimpleTermModel.from_ct_code(
            uid, self._repos.ct_term_name_repository.find_by_uid
        )

    @ensure_transaction(db)
    def make_selection(
        self,
        study_uid: str,
        selection_create_input: StudySelectionArmCreateInput,
        validate: bool = True,
    ) -> StudySelectionArm:
        repos = self._repos

        try:
            # create new VO to add
            new_selection = StudySelectionArmVO.from_input_values(
                study_uid=study_uid,
                author_id=self.author,
                name=selection_create_input.name,
                short_name=selection_create_input.short_name,
                label=selection_create_input.label,
                code=selection_create_input.code,
                description=selection_create_input.description,
                randomization_group=selection_create_input.randomization_group,
                number_of_subjects=selection_create_input.number_of_subjects,
                arm_type_uid=selection_create_input.arm_type_uid,
                merge_branch_for_this_arm_for_sdtm_adam=selection_create_input.merge_branch_for_this_arm_for_sdtm_adam,
                generate_uid_callback=repos.study_arm_repository.generate_uid,
            )
            # Load aggregate
            selection_aggregate: StudySelectionArmAR = (
                repos.study_arm_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )
            assert selection_aggregate is not None
            # add VO to aggregate
            selection_aggregate.add_arm_selection(
                new_selection,
                self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                arm_exists_callback_by=repos.study_arm_repository.arm_exists_by,
                validate=validate,
            )

            # sync with DB and save the update
            repos.study_arm_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just added
            new_selection, order = selection_aggregate.get_specific_arm_selection(
                new_selection.study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            # add the arm and return
            # StudyArm without connected BranchArms not make sense that has BranchArms yet
            return StudySelectionArm.from_study_selection_arm_ar_and_order(
                study_uid=study_uid,
                selection=new_selection,
                order=order,
                find_codelist_term_arm_type=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    def _patch_prepare_new_study_arm(
        self,
        request_study_arm: StudySelectionArmInput,
        current_study_arm: StudySelectionArmVO,
    ) -> StudySelectionArmVO:
        # transform current to input model
        transformed_current = StudySelectionArmInput(
            arm_uid=current_study_arm.study_selection_uid,
            name=current_study_arm.name,
            short_name=current_study_arm.short_name,
            label=current_study_arm.label,
            code=current_study_arm.code,
            description=current_study_arm.description,
            randomization_group=current_study_arm.randomization_group,
            number_of_subjects=current_study_arm.number_of_subjects,
            arm_type_uid=current_study_arm.arm_type_uid,
            merge_branch_for_this_arm_for_sdtm_adam=current_study_arm.merge_branch_for_this_arm_for_sdtm_adam,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_arm,
            reference_base_model=transformed_current,
        )

        return StudySelectionArmVO.from_input_values(
            study_uid=current_study_arm.study_uid,
            name=request_study_arm.name,
            short_name=request_study_arm.short_name,
            label=request_study_arm.label,
            code=request_study_arm.code,
            description=request_study_arm.description,
            randomization_group=request_study_arm.randomization_group,
            number_of_subjects=request_study_arm.number_of_subjects,
            arm_type_uid=request_study_arm.arm_type_uid,
            merge_branch_for_this_arm_for_sdtm_adam=request_study_arm.merge_branch_for_this_arm_for_sdtm_adam,
            study_selection_uid=current_study_arm.study_selection_uid,
            author_id=self.author,
        )

    @ensure_transaction(db)
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: StudySelectionArmInput,
        validate: bool = True,
    ) -> StudySelectionArmWithConnectedBranchArms:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate: StudySelectionArmAR = (
                repos.study_arm_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            assert selection_aggregate is not None

            # Load the current VO for updates
            current_vo, order = selection_aggregate.get_specific_object_selection(
                study_selection_uid=study_selection_uid
            )

            # merge current with updates
            updated_selection = self._patch_prepare_new_study_arm(
                request_study_arm=selection_update_input, current_study_arm=current_vo
            )

            selection_vo: StudySelectionArmVO
            if updated_selection != current_vo:
                # let the aggregate update the value object
                selection_aggregate.update_selection(
                    updated_study_arm_selection=updated_selection,
                    ct_term_exists_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                    arm_exists_callback_by=repos.study_arm_repository.arm_exists_by,
                    validate=validate,
                )

                # sync with DB and save the update
                repos.study_arm_repository.save(selection_aggregate, self.author)

                # Fetch the new selection which was just updated
                new_selection, order = (
                    selection_aggregate.get_specific_object_selection(
                        study_selection_uid
                    )
                )
                selection_vo = new_selection
            else:
                selection_vo = current_vo

            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )

            # With Connected BranchArms because can carry out the connected BranchARms
            return StudySelectionArmWithConnectedBranchArms.from_study_selection_arm_ar__order__connected_branch_arms(
                study_uid=study_uid,
                selection=selection_vo,
                order=order,
                find_codelist_term_arm_type=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
                find_multiple_connected_branch_arm=self._find_branch_arms_connected_to_arm_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    @ensure_transaction(db)
    def get_specific_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        study_value_version: str | None = None,
    ) -> StudySelectionArmWithConnectedBranchArms:
        (
            _,
            new_selection,
            order,
        ) = self._get_specific_arm_selection_by_uids(
            study_uid, study_selection_uid, study_value_version=study_value_version
        )
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_uid,
            study_value_version=study_value_version,
        )
        # With Connected BranchArms due to it may has already connected BranchArms to it
        # pylint: disable=line-too-long
        return StudySelectionArmWithConnectedBranchArms.from_study_selection_arm_ar__order__connected_branch_arms(
            study_uid=study_uid,
            selection=new_selection,
            order=order,
            find_codelist_term_arm_type=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            find_multiple_connected_branch_arm=self._find_branch_arms_connected_to_arm_uid,
            study_value_version=study_value_version,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    @staticmethod
    def _arm_types_match(
        existing_arm_type_uid: str | None, incoming_arm_type_uid: str | None
    ) -> bool:
        return (existing_arm_type_uid or None) == (incoming_arm_type_uid or None)

    def _get_arm_type_display_name(
        self,
        arm_type_uid: str | None,
        terms_at_specific_datetime: datetime | None,
    ) -> str | None:
        if not arm_type_uid:
            return None
        codelist_term = self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval(
            term_uid=arm_type_uid,
            codelist_submission_value=settings.study_arm_type_cl_submval,
            at_specific_date_time=terms_at_specific_datetime,
        )
        if codelist_term is None:
            return None
        return codelist_term.ct_simple_codelist_term_vo.term_name

    @staticmethod
    def _with_uid_suffix(
        value: str, arm_uid: str, max_length: int | None = None
    ) -> str:
        suffix = f"_{arm_uid}"
        if max_length is None:
            return f"{value}{suffix}"
        if len(suffix) >= max_length:
            raise exceptions.ValidationException(
                msg=f"Value '{value}' in field code cannot be made unique within max length."
            )
        base_max_length = max_length - len(suffix)
        return f"{value[:base_max_length]}{suffix}"

    def _resolve_ct_display_field_value(
        self,
        *,
        value: str,
        arm_type_uid: str | None,
        field_label: str,
        exists_callback,
        terms_at_specific_datetime: datetime | None,
        max_length: int,
    ) -> str:
        display_name = self._get_arm_type_display_name(
            arm_type_uid, terms_at_specific_datetime
        )
        exceptions.ValidationException.raise_if(
            not display_name,
            msg=(
                f"Value '{value}' in field {field_label} is not unique for the study "
                f"and arm type display name could not be resolved."
            ),
        )
        assert display_name is not None
        candidate = f"{value} - {display_name}"
        counter = 2
        while exists_callback(candidate):
            candidate = f"{value} - {display_name} ({counter})"
            counter += 1
            exceptions.ValidationException.raise_if(
                len(candidate) > max_length,
                msg=f"Value '{value}' in field {field_label} cannot be made unique within max length.",
            )
        return candidate

    def _find_skip_match_vo(
        self,
        spec: StudySelectionArmCreateInput,
        indexes: _ArmConflictIndexes,
    ) -> StudySelectionArmVO | None:
        if spec.name and spec.name in indexes.by_name:
            entry = indexes.by_name[spec.name]
            if self._arm_types_match(entry.vo.arm_type_uid, spec.arm_type_uid):
                return entry.vo
        if spec.short_name and spec.short_name in indexes.by_short_name:
            entry = indexes.by_short_name[spec.short_name]
            if self._arm_types_match(entry.vo.arm_type_uid, spec.arm_type_uid):
                return entry.vo
        return None

    def _resolve_create_input_conflicts(
        self,
        spec: StudySelectionArmCreateInput,
        arm_uid: str,
        indexes: _ArmConflictIndexes,
        terms_at_specific_datetime: datetime | None,
    ) -> tuple[StudySelectionArmCreateInput, list[str]]:
        notifications: list[str] = []
        resolved = spec.model_copy(deep=True)

        if resolved.name and resolved.name in indexes.by_name:
            existing = indexes.by_name[resolved.name]
            if not self._arm_types_match(
                existing.vo.arm_type_uid, resolved.arm_type_uid
            ):
                new_name = self._resolve_ct_display_field_value(
                    value=resolved.name,
                    arm_type_uid=resolved.arm_type_uid,
                    field_label="Arm name",
                    exists_callback=lambda candidate: candidate in indexes.by_name,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                    max_length=STUDY_ARM_NAME_MAX_LENGTH,
                )
                notifications.append(
                    f"Arm name adjusted to '{new_name}' due to name conflict with a different arm type."
                )
                resolved.name = new_name

        if resolved.short_name and resolved.short_name in indexes.by_short_name:
            existing = indexes.by_short_name[resolved.short_name]
            if not self._arm_types_match(
                existing.vo.arm_type_uid, resolved.arm_type_uid
            ):
                new_short_name = self._resolve_ct_display_field_value(
                    value=resolved.short_name,
                    arm_type_uid=resolved.arm_type_uid,
                    field_label="Arm short name",
                    exists_callback=lambda candidate: candidate
                    in indexes.by_short_name,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                    max_length=STUDY_ARM_SHORT_NAME_MAX_LENGTH,
                )
                notifications.append(
                    f"Arm short name adjusted to '{new_short_name}' due to short name conflict with a different arm type."
                )
                resolved.short_name = new_short_name

        if resolved.code and resolved.code in indexes.by_code:
            new_code = self._with_uid_suffix(
                resolved.code, arm_uid, max_length=STUDY_ARM_CODE_MAX_LENGTH
            )
            notifications.append(
                f"Arm code adjusted to '{new_code}' due to code conflict."
            )
            resolved.code = new_code

        if (
            resolved.randomization_group
            and resolved.randomization_group in indexes.by_randomization_group
        ):
            new_randomization_group = self._with_uid_suffix(
                resolved.randomization_group, arm_uid
            )
            notifications.append(
                "Arm randomization group adjusted to "
                f"'{new_randomization_group}' due to randomization group conflict."
            )
            resolved.randomization_group = new_randomization_group

        return resolved, notifications

    def _vo_to_response_arm(
        self,
        study_uid: str,
        selection: StudySelectionArmVO,
        order: int,
        terms_at_specific_datetime: datetime | None,
    ) -> StudySelectionArm:
        return StudySelectionArm.from_study_selection_arm_ar_and_order(
            study_uid=study_uid,
            selection=selection,
            order=order,
            find_codelist_term_arm_type=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    def _map_source_study_arms_to_create_inputs(
        self, study_source_uid: str
    ) -> list[StudySelectionArmCreateInput]:
        source_arms = self.get_all_selection(
            study_uid=study_source_uid, page_size=0
        ).items
        specs: list[StudySelectionArmCreateInput] = []
        for arm in source_arms:
            specs.append(
                StudySelectionArmCreateInput(
                    name=arm.name,
                    short_name=arm.short_name,
                    label=arm.label,
                    code=arm.code,
                    description=arm.description,
                    randomization_group=arm.randomization_group,
                    number_of_subjects=arm.number_of_subjects,
                    arm_type_uid=arm.arm_type.term_uid if arm.arm_type else None,
                    merge_branch_for_this_arm_for_sdtm_adam=arm.merge_branch_for_this_arm_for_sdtm_adam,
                )
            )
        return specs

    @ensure_transaction(db)
    def _create_arms_with_conflict_resolution(
        self,
        study_uid: str,
        specs: list[StudySelectionArmCreateInput],
    ) -> list[StudySelectionArmBatchOutput]:
        repos = self._repos
        results: list[StudySelectionArmBatchOutput] = []
        if not specs:
            return results

        try:
            selection_aggregate: StudySelectionArmAR = (
                repos.study_arm_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )
            assert selection_aggregate is not None
            indexes = _ArmConflictIndexes.from_aggregate(selection_aggregate)
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
                            f"Arm '{spec.name}' with the same name and arm type already exists; "
                            "creation skipped."
                        )
                    elif spec.short_name and spec.short_name in indexes.by_short_name:
                        notification = (
                            f"Arm short name '{spec.short_name}' with the same arm type already "
                            "exists; creation skipped."
                        )
                    results.append(
                        StudySelectionArmBatchOutput(
                            response_code=status.HTTP_200_OK,
                            content=self._vo_to_response_arm(
                                study_uid=study_uid,
                                selection=skip_vo,
                                order=order,
                                terms_at_specific_datetime=terms_at_specific_datetime,
                            ),
                            notification=notification,
                        )
                    )
                    continue

                arm_uid = repos.study_arm_repository.generate_uid()
                resolved_spec, notifications = self._resolve_create_input_conflicts(
                    spec=spec,
                    arm_uid=arm_uid,
                    indexes=indexes,
                    terms_at_specific_datetime=terms_at_specific_datetime,
                )
                new_selection = StudySelectionArmVO.from_input_values(
                    study_uid=study_uid,
                    author_id=self.author,
                    study_selection_uid=arm_uid,
                    name=resolved_spec.name,
                    short_name=resolved_spec.short_name,
                    label=resolved_spec.label,
                    code=resolved_spec.code,
                    description=resolved_spec.description,
                    randomization_group=resolved_spec.randomization_group,
                    number_of_subjects=resolved_spec.number_of_subjects,
                    arm_type_uid=resolved_spec.arm_type_uid,
                    merge_branch_for_this_arm_for_sdtm_adam=resolved_spec.merge_branch_for_this_arm_for_sdtm_adam,
                    generate_uid_callback=repos.study_arm_repository.generate_uid,
                )
                selection_aggregate.add_arm_selection(
                    new_selection,
                    self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                    arm_exists_callback_by=repos.study_arm_repository.arm_exists_by,
                    validate=False,
                )
                indexes.register_vo(new_selection)
                created_vo_uids.add(new_selection.study_selection_uid)
                new_selection, order = selection_aggregate.get_specific_arm_selection(
                    new_selection.study_selection_uid
                )
                notification = " ".join(notifications) if notifications else None
                results.append(
                    StudySelectionArmBatchOutput(
                        response_code=status.HTTP_201_CREATED,
                        content=self._vo_to_response_arm(
                            study_uid=study_uid,
                            selection=new_selection,
                            order=order,
                            terms_at_specific_datetime=terms_at_specific_datetime,
                        ),
                        notification=notification,
                    )
                )

            for study_arm_vo in selection_aggregate.study_arms_selection:
                if study_arm_vo.study_selection_uid in created_vo_uids:
                    study_arm_vo.validate(
                        self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                        arm_exists_callback_by=repos.study_arm_repository.arm_exists_by,
                    )

            repos.study_arm_repository.save(selection_aggregate, self.author)
        finally:
            repos.close()
        return results

    @ensure_transaction(db)
    def copy_arms_from_study(
        self, study_uid: str, study_source_uid: str
    ) -> list[StudySelectionArmBatchOutput]:
        """
        Copy all study arms from a source study into the target study.

        Authorization follows the same in-tenant model as copy-component: the caller
        must have write access to the target study (enforced at the router). The source
        study must exist; cross-study reads are allowed within the tenant when the
        source UID is known, consistent with other copy-from-study operations.
        """
        exceptions.ValidationException.raise_if(
            study_source_uid == study_uid,
            msg="study_source_uid must differ from the target study.",
        )
        self.check_if_study_exists(study_uid)
        self.check_if_study_exists(study_source_uid)
        specs = self._map_source_study_arms_to_create_inputs(study_source_uid)
        return self._create_arms_with_conflict_resolution(study_uid, specs)

    @ensure_transaction(db)
    def handle_batch_operations(
        self,
        study_uid: str,
        operations: list[StudySelectionArmBatchInput],
    ) -> list[StudySelectionArmBatchOutput]:
        results: list[StudySelectionArmBatchOutput | None] = [None] * len(operations)
        patched_arm_uids: set[str] = set()
        try:
            index = 0
            while index < len(operations):
                operation = operations[index]
                if operation.method == "PATCH":
                    if isinstance(operation.content, StudySelectionArmBatchUpdateInput):
                        item = self.patch_selection(
                            study_uid=study_uid,
                            study_selection_uid=operation.content.arm_uid,
                            selection_update_input=operation.content,
                            validate=False,
                        )
                        patched_arm_uids.add(operation.content.arm_uid)
                        results[index] = StudySelectionArmBatchOutput(
                            response_code=status.HTTP_200_OK,
                            content=item,
                        )
                    else:
                        raise exceptions.ValidationException(
                            msg="PATCH operation requires StudySelectionArmBatchUpdateInput as request payload."
                        )
                    index += 1
                elif operation.method == "POST":
                    post_specs: list[StudySelectionArmCreateInput] = []
                    post_indices: list[int] = []
                    while (
                        index < len(operations) and operations[index].method == "POST"
                    ):
                        content = operations[index].content
                        if not isinstance(content, StudySelectionArmCreateInput):
                            raise exceptions.ValidationException(
                                msg="POST operation requires StudySelectionArmCreateInput as request payload."
                            )
                        post_specs.append(content)
                        post_indices.append(index)
                        index += 1
                    create_results = self._create_arms_with_conflict_resolution(
                        study_uid=study_uid,
                        specs=post_specs,
                    )
                    for result_index, create_result in zip(
                        post_indices, create_results
                    ):
                        results[result_index] = create_result
                else:
                    raise exceptions.MethodNotAllowedException(method=operation.method)

            if patched_arm_uids:
                study_arm_ar: StudySelectionArmAR = (
                    self._repos.study_arm_repository.find_by_study(study_uid=study_uid)
                )
                for study_arm_vo in study_arm_ar.study_arms_selection:
                    if study_arm_vo.study_selection_uid in patched_arm_uids:
                        study_arm_vo.validate(
                            self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                            arm_exists_callback_by=self._repos.study_arm_repository.arm_exists_by,
                        )
        except exceptions.MDRApiBaseException as error:
            raise error
        return [result for result in results if result is not None]
