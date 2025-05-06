from datetime import datetime

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
    StudySelectionArm,
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
    fill_missing_values_in_base_model_from_reference_base_model,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.studies.study_selection_base import StudySelectionMixin
from common import exceptions
from common.auth.user import user


class StudyArmSelectionService(StudySelectionMixin):
    _repos: MetaRepository

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionArmAR,
        study_value_version: str | None = None,
    ) -> list[StudySelectionArmWithConnectedBranchArms]:
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
            find_simple_term_arm_type_by_term_uid=self._find_by_uid_or_raise_not_found,
            find_multiple_connected_branch_arm=self._find_branch_arms_connected_to_arm_uid,
            study_value_version=study_value_version,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    @db.transaction
    def get_all_selections_for_all_studies(
        self,
        project_name: str | None = None,
        project_number: str | None = None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
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

    @db.transaction
    def get_distinct_values_for_header(
        self,
        field_name: str,
        study_uid: str | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
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

    @db.transaction
    def get_all_selection(
        self,
        study_uid: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
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

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            # cascade delete
            # delete study branch arms assigned to arm
            branch_arms_on_arm = None
            if repos.study_arm_repository.arm_specific_has_connected_branch_arms(
                study_uid=study_uid, arm_uid=study_selection_uid
            ):
                branch_arms_on_arm = (
                    repos.study_branch_arm_repository.get_branch_arms_connected_to_arm(
                        study_uid=study_uid, study_arm_uid=study_selection_uid
                    )
                )
            design_cells_on_branch_arm = []
            design_cells_to_delete_from_branch_arm = []
            if branch_arms_on_arm is not None:
                for i_branch_arm in branch_arms_on_arm:
                    cascade_deletion_last_branch = False
                    # if the branch_arm has connected design cells
                    if repos.study_branch_arm_repository.branch_arm_specific_has_connected_cell(
                        study_uid=study_uid,
                        branch_arm_uid=i_branch_arm.uid,
                    ):
                        design_cells_on_branch_arm = self._repos.study_design_cell_repository.get_design_cells_connected_to_branch_arm(
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
                            design_cells_to_delete_in_desc_order = sorted(
                                design_cells_on_branch_arm,
                                key=lambda dc: dc.order,
                                reverse=True,
                            )
                            for i_design_cell in design_cells_to_delete_in_desc_order:
                                study_design_cell = self._repos.study_design_cell_repository.find_by_uid(
                                    study_uid=study_uid, uid=i_design_cell.uid
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
                    branch_arm_aggregate = (
                        repos.study_branch_arm_repository.find_by_study(
                            study_uid=study_uid, for_update=True
                        )
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
                design_cells_on_arm = self._repos.study_design_cell_repository.get_design_cells_connected_to_arm(
                    study_uid=study_uid, study_arm_uid=study_selection_uid
                )
            if design_cells_on_arm or design_cells_to_delete_from_branch_arm:
                # get design cells to delete that are connected to arm
                design_cells_to_delete_in_desc_order = sorted(
                    design_cells_on_arm,
                    key=lambda dc: dc.order,
                    reverse=True,
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

    @db.transaction
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
        effective_date: datetime = None,
    ) -> StudySelectionArm:
        return StudySelectionArm.from_study_selection_history(
            study_selection_history=study_selection_history,
            study_uid=study_uid,
            get_ct_term_arm_type=self._find_by_uid_or_raise_not_found,
            effective_date=effective_date,
        )

    @db.transaction
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
            data = []
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

    @db.transaction
    def get_specific_selection_audit_trail(
        self, study_uid: str, study_selection_uid: str
    ) -> list[StudySelectionArmVersion]:
        repos = self._repos
        try:
            selection_history: list[StudySelectionArmVersion] = (
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

    def make_selection(
        self,
        study_uid: str,
        selection_create_input: StudySelectionArmCreateInput,
    ) -> StudySelectionArm:
        repos = self._repos

        try:
            # Load aggregate
            with db.transaction:
                # create new VO to add
                new_selection = StudySelectionArmVO.from_input_values(
                    study_uid=study_uid,
                    author_id=self.author,
                    name=selection_create_input.name,
                    short_name=selection_create_input.short_name,
                    code=selection_create_input.code,
                    description=selection_create_input.description,
                    arm_colour=selection_create_input.arm_colour,
                    randomization_group=selection_create_input.randomization_group,
                    number_of_subjects=selection_create_input.number_of_subjects,
                    arm_type_uid=selection_create_input.arm_type_uid,
                    generate_uid_callback=repos.study_arm_repository.generate_uid,
                )
                # add VO to aggregate
                selection_aggregate: StudySelectionArmAR = (
                    repos.study_arm_repository.find_by_study(
                        study_uid=study_uid, for_update=True
                    )
                )
                assert selection_aggregate is not None
                selection_aggregate.add_arm_selection(
                    new_selection,
                    self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                    arm_exists_callback_by=repos.study_arm_repository.arm_exists_by,
                )

                # sync with DB and save the update
                repos.study_arm_repository.save(selection_aggregate, self.author)

                # Fetch the new selection which was just added
                new_selection, order = selection_aggregate.get_specific_arm_selection(
                    new_selection.study_selection_uid
                )
                terms_at_specific_datetime = (
                    self._extract_study_standards_effective_date(study_uid=study_uid)
                )
                # add the arm and return
                # StudyArm without connected BranchArms not make sense that has BranchArms yet
                return StudySelectionArm.from_study_selection_arm_ar_and_order(
                    study_uid=study_uid,
                    selection=new_selection,
                    order=order,
                    find_simple_term_arm_type_by_term_uid=self._find_by_uid_or_raise_not_found,
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
            code=current_study_arm.code,
            description=current_study_arm.description,
            arm_colour=current_study_arm.arm_colour,
            randomization_group=current_study_arm.randomization_group,
            number_of_subjects=current_study_arm.number_of_subjects,
            arm_type_uid=current_study_arm.arm_type_uid,
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
            code=request_study_arm.code,
            description=request_study_arm.description,
            arm_colour=request_study_arm.arm_colour,
            randomization_group=request_study_arm.randomization_group,
            number_of_subjects=request_study_arm.number_of_subjects,
            arm_type_uid=request_study_arm.arm_type_uid,
            study_selection_uid=current_study_arm.study_selection_uid,
            author_id=self.author,
        )

    @db.transaction
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: StudySelectionArmInput,
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

            # let the aggregate update the value object
            selection_aggregate.update_selection(
                updated_study_arm_selection=updated_selection,
                ct_term_exists_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                arm_exists_callback_by=repos.study_arm_repository.arm_exists_by,
            )

            # sync with DB and save the update
            repos.study_arm_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just updated
            new_selection, order = selection_aggregate.get_specific_object_selection(
                study_selection_uid
            )

            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            # add the arm and return
            # With Connected BranchArms because can carry out the connected BranchARms
            # pylint: disable=line-too-long
            return StudySelectionArmWithConnectedBranchArms.from_study_selection_arm_ar__order__connected_branch_arms(
                study_uid=study_uid,
                selection=new_selection,
                order=order,
                find_simple_term_arm_type_by_term_uid=self._find_by_uid_or_raise_not_found,
                find_multiple_connected_branch_arm=self._find_branch_arms_connected_to_arm_uid,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    @db.transaction
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
            find_simple_term_arm_type_by_term_uid=self._find_by_uid_or_raise_not_found,
            find_multiple_connected_branch_arm=self._find_branch_arms_connected_to_arm_uid,
            study_value_version=study_value_version,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )
