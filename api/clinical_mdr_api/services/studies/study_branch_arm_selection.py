from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import status
from neomodel import db

from clinical_mdr_api.domain_repositories.study_selections.study_branch_arm_repository import (
    SelectionHistoryBranchArm,
)
from clinical_mdr_api.domains.study_selections.study_selection_arm import (
    StudySelectionArmVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_branch_arm import (
    CompactStudyCohortVO,
    StudySelectionBranchArmAR,
    StudySelectionBranchArmVO,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyDesignCellBatchInput,
    StudyDesignCellBatchOutput,
    StudyDesignCellEditInput,
    StudySelectionArm,
    StudySelectionBranchArm,
    StudySelectionBranchArmBatchInput,
    StudySelectionBranchArmBatchOutput,
    StudySelectionBranchArmBatchUpdateInput,
    StudySelectionBranchArmCreateInput,
    StudySelectionBranchArmEditInput,
    StudySelectionBranchArmHistory,
    StudySelectionBranchArmVersion,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    ensure_transaction,
    fill_missing_values_in_base_model_from_reference_base_model,
    service_level_generic_filtering,
)
from clinical_mdr_api.services.studies.study_design_cell import StudyDesignCellService
from clinical_mdr_api.services.studies.study_selection_base import StudySelectionMixin
from common import exceptions
from common.auth.user import user


@dataclass(frozen=True)
class _BranchArmConflictIndexEntry:
    vo: StudySelectionBranchArmVO


@dataclass
class _BranchArmConflictIndexes:
    by_name: dict[str, _BranchArmConflictIndexEntry]
    by_short_name: dict[str, _BranchArmConflictIndexEntry]

    @classmethod
    def from_aggregate(
        cls, aggregate: StudySelectionBranchArmAR
    ) -> "_BranchArmConflictIndexes":
        indexes = cls(by_name={}, by_short_name={})
        for vo in aggregate.study_branch_arms_selection:
            indexes.register_vo(vo)
        return indexes

    def register_vo(self, vo: StudySelectionBranchArmVO) -> None:
        entry = _BranchArmConflictIndexEntry(vo=vo)
        if vo.name:
            self.by_name[vo.name] = entry
        if vo.short_name:
            self.by_short_name[vo.short_name] = entry


@dataclass(frozen=True)
class _TargetArmIndexEntry:
    vo: StudySelectionArmVO


@dataclass
class _TargetArmIndexes:
    by_name_and_type: dict[tuple[str, str | None], _TargetArmIndexEntry]

    @classmethod
    def from_arm_vos(cls, arm_vos: list[StudySelectionArmVO]) -> "_TargetArmIndexes":
        indexes = cls(by_name_and_type={})
        for vo in arm_vos:
            indexes.register_vo(vo)
        return indexes

    def register_vo(self, vo: StudySelectionArmVO) -> None:
        if vo.name:
            self.by_name_and_type[(vo.name, vo.arm_type_uid or None)] = (
                _TargetArmIndexEntry(vo=vo)
            )


@dataclass
class _BranchArmCreateOrSkip:
    spec: StudySelectionBranchArmCreateInput | None = None
    parent_arm_skip_notification: str | None = None


class StudyBranchArmSelectionService(StudySelectionMixin):
    _repos: MetaRepository

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionBranchArmAR | None,
        study_value_version: str | None = None,
    ) -> list[StudySelectionBranchArm]:
        if study_selection is None:
            return []

        result = []
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_selection.study_uid,
            study_value_version=study_value_version,
        )
        for order, selection in enumerate(
            study_selection.study_branch_arms_selection, start=1
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
        study_selection: StudySelectionBranchArmVO,
        order: int,
        study_uid: str,
        study_value_version: str | None = None,
        terms_at_specific_datetime: datetime | None = None,
    ) -> StudySelectionBranchArm:
        return StudySelectionBranchArm.from_study_selection_branch_arm_ar_and_order(
            study_uid,
            study_selection,
            order,
            find_simple_term_branch_arm_root_by_term_uid=self._get_specific_arm_selection,
            study_value_version=study_value_version,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    def get_all_selection(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[StudySelectionBranchArm]:
        repos = MetaRepository()
        try:
            branch_arm_selection_ar = repos.study_branch_arm_repository.find_by_study(
                study_uid, study_value_version=study_value_version
            )

            selections = self._transform_all_to_response_model(
                branch_arm_selection_ar, study_value_version=study_value_version
            )
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

        finally:
            repos.close()

    def get_all_selection_within_arm(
        self,
        study_uid: str,
        study_arm_uid: str,
        study_value_version: str | None = None,
    ) -> list[StudySelectionBranchArm]:
        repos = MetaRepository()
        try:
            branch_arm_selection_ar = repos.study_branch_arm_repository.find_by_arm(
                study_uid=study_uid,
                study_arm_uid=study_arm_uid,
                study_value_version=study_value_version,
            )
            return self._transform_all_to_response_model(
                branch_arm_selection_ar, study_value_version=study_value_version
            )
        finally:
            repos.close()

    @ensure_transaction(db)
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            # Load aggregate
            branch_arm_aggregate = repos.study_branch_arm_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )
            for selection in branch_arm_aggregate.study_branch_arms_selection:
                if selection.study_selection_uid == study_selection_uid:
                    selection_to_delete = selection

            cascade_deletion_last_branch = False
            # if the branch_arm has connected design cells
            if repos.study_branch_arm_repository.branch_arm_specific_has_connected_cell(
                study_uid=study_uid,
                branch_arm_uid=study_selection_uid,
            ):
                design_cells_on_branch_arm = self._repos.study_design_cell_repository.find_all_design_cells_by_study(
                    study_uid=study_uid, study_branch_arm_uid=study_selection_uid
                )
                # if the study_branch_arm is the last StudyBranchArm of its StudyArm root
                if repos.study_branch_arm_repository.branch_arm_specific_is_last_on_arm_root(
                    study_uid=study_uid,
                    # pylint: disable=possibly-used-before-assignment
                    arm_root_uid=selection_to_delete.arm_root_uid,
                    branch_arm_uid=study_selection_uid,
                ):
                    # switch all the study designcells to the study branch arm
                    cascade_deletion_last_branch = True

                # else the study_branch_arm is not last StudyBranchArm of its StudyArm root and we have to delete them
                else:
                    for i_design_cell in design_cells_on_branch_arm:
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

            # remove the connection
            branch_arm_aggregate.remove_branch_arm_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_branch_arm_repository.save(branch_arm_aggregate, self.author)

            if cascade_deletion_last_branch:
                for i_design_cell in design_cells_on_branch_arm:
                    self._repos.study_design_cell_repository.patch_study_arm(
                        study_uid=study_uid,
                        design_cell_uid=i_design_cell.uid,
                        study_arm_uid=selection_to_delete.arm_root_uid,
                        author_id=self.author,
                        allow_none_arm_branch_arm=True,
                    )
        finally:
            repos.close()

    @ensure_transaction(db)
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> StudySelectionBranchArm:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = repos.study_branch_arm_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order
            )

            # sync with DB and save the update
            repos.study_branch_arm_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just added
            (
                new_selection,
                order,
            ) = selection_aggregate.get_specific_branch_arm_selection(
                study_selection_uid
            )

            # add the objective and return
            return self._transform_single_to_response_model(
                new_selection, order, study_uid
            )
        finally:
            repos.close()

    def _transform_each_history_to_response_model(
        self, study_selection_history: SelectionHistoryBranchArm, study_uid: str
    ) -> StudySelectionBranchArmHistory:
        return StudySelectionBranchArmHistory.from_study_selection_history(
            study_selection_history=study_selection_history,
            study_uid=study_uid,
        )

    def get_all_selection_audit_trail(
        self, study_uid: str
    ) -> list[StudySelectionBranchArmVersion]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_branch_arm_repository.find_selection_history(study_uid)
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(msg=value_error.args[0])

            unique_list_uids = list({x.study_selection_uid for x in selection_history})
            unique_list_uids.sort()
            # list of all study_branch_arms
            data: list[StudySelectionBranchArmVersion] = []
            for i_unique in unique_list_uids:
                ith_selection_history = []
                # gather the selection history of the i_unique Uid
                for selection in selection_history:
                    if selection.study_selection_uid == i_unique:
                        ith_selection_history.append(selection)
                # get the versions and compare
                versions = [
                    self._transform_each_history_to_response_model(
                        _, study_uid
                    ).model_dump()
                    for _ in ith_selection_history
                ]
                if not data:
                    data = calculate_diffs(versions, StudySelectionBranchArmVersion)
                else:
                    data.extend(
                        calculate_diffs(versions, StudySelectionBranchArmVersion)
                    )
            return data
        finally:
            repos.close()

    def get_specific_selection_audit_trail(
        self, study_uid: str, study_selection_uid: str
    ) -> list[StudySelectionBranchArmVersion]:
        repos = self._repos
        try:
            selection_history = (
                repos.study_branch_arm_repository.find_selection_history(
                    study_uid, study_selection_uid
                )
            )
            versions = [
                self._transform_each_history_to_response_model(
                    _, study_uid
                ).model_dump()
                for _ in selection_history
            ]
            data = calculate_diffs(versions, StudySelectionBranchArmVersion)
            return data
        finally:
            repos.close()

    def _get_specific_arm_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        study_value_version: str | None = None,
        terms_at_specific_datetime: datetime | None = None,
    ) -> StudySelectionArm:
        (
            _,
            new_selection,
            order,
        ) = self._get_specific_arm_selection_by_uids(
            study_uid,
            study_selection_uid=study_selection_uid,
            study_value_version=study_value_version,
        )
        # Without Connected BranchArms due to only is necessary to have the StudyArm
        return StudySelectionArm.from_study_selection_arm_ar_and_order(
            study_uid=study_uid,
            selection=new_selection,
            order=order,
            find_codelist_term_arm_type=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    def _cascade_creation(
        self, study_uid: str, study_branch_arm_uid: str, study_arm_uid: str
    ) -> list[StudyDesignCellBatchOutput]:
        repos = self._repos
        design_cells_on_arm = (
            repos.study_design_cell_repository.find_all_design_cells_by_study(
                study_uid=study_uid, study_arm_uid=study_arm_uid
            )
        )

        inputs = [
            StudyDesignCellBatchInput(
                method="PATCH",
                content=StudyDesignCellEditInput(
                    study_design_cell_uid=i_design_cell.uid,
                    study_branch_arm_uid=study_branch_arm_uid,
                ),
            )
            for i_design_cell in design_cells_on_arm
        ]

        design_cell_service = StudyDesignCellService()
        design_cells_updated = design_cell_service.handle_batch_operations(
            study_uid=study_uid, operations=inputs
        )
        assert len(design_cells_updated) > 0
        return design_cells_updated

    @ensure_transaction(db)
    def make_selection(
        self,
        study_uid: str,
        selection_create_input: StudySelectionBranchArmCreateInput,
        validate: bool = True,
    ) -> StudySelectionBranchArm:
        repos = self._repos

        try:
            # create new VO to add
            new_selection = StudySelectionBranchArmVO.from_input_values(
                study_uid=study_uid,
                author_id=self.author,
                name=selection_create_input.name,
                short_name=selection_create_input.short_name,
                code=selection_create_input.code,
                description=selection_create_input.description,
                randomization_group=selection_create_input.randomization_group,
                number_of_subjects=selection_create_input.number_of_subjects,
                arm_root_uid=selection_create_input.arm_uid,
                study_cohorts=(
                    [
                        CompactStudyCohortVO(
                            study_cohort_uid=selection_create_input.study_cohort_uid,
                            study_cohort_code=None,
                            study_cohort_name=None,
                        )
                    ]
                    if selection_create_input.study_cohort_uid
                    else []
                ),
                generate_uid_callback=repos.study_branch_arm_repository.generate_uid,
            )
            # Load aggregate
            selection_aggregate: StudySelectionBranchArmAR = (
                repos.study_branch_arm_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )
            assert selection_aggregate is not None
            # add VO to aggregate
            selection_aggregate.add_branch_arm_selection(
                study_branch_arm_selection=new_selection,
                study_branch_arm_study_arm_update_conflict_callback=(
                    repos.study_branch_arm_repository.branch_arm_arm_update_conflict
                ),
                study_arm_exists_callback=self._repos.study_arm_repository.arm_specific_exists_by_uid,
                branch_arm_exists_callback_by=repos.study_branch_arm_repository.branch_arm_exists_by,
                validate=validate,
            )

            # sync with DB and save the update
            repos.study_branch_arm_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just added
            (
                new_selection,
                order,
            ) = selection_aggregate.get_specific_branch_arm_selection(
                new_selection.study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            # add the Brancharm and return
            return StudySelectionBranchArm.from_study_selection_branch_arm_ar_and_order(
                study_uid=study_uid,
                selection=new_selection,
                order=order,
                find_simple_term_branch_arm_root_by_term_uid=self._get_specific_arm_selection,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()
            # if the studyarm has studydesigncells connected?
            if repos.study_arm_repository.arm_specific_has_connected_cell(
                study_uid=study_uid, arm_uid=new_selection.arm_root_uid
            ):
                # if it is the first study branch to be added
                # switch all the study designcells to the study branch arm
                self._cascade_creation(
                    study_uid=study_uid,
                    study_arm_uid=new_selection.arm_root_uid,
                    study_branch_arm_uid=new_selection.study_selection_uid,
                )

    def _patch_prepare_new_study_branch_arm(
        self,
        request_study_branch_arm: StudySelectionBranchArmEditInput,
        current_study_branch_arm: StudySelectionBranchArmVO,
    ) -> StudySelectionBranchArmVO:
        # transform current to input model
        transformed_current = StudySelectionBranchArmEditInput(
            branch_arm_uid=current_study_branch_arm.study_selection_uid,
            name=current_study_branch_arm.name,
            short_name=current_study_branch_arm.short_name,
            code=current_study_branch_arm.code,
            description=current_study_branch_arm.description,
            randomization_group=current_study_branch_arm.randomization_group,
            number_of_subjects=current_study_branch_arm.number_of_subjects,
            arm_uid=current_study_branch_arm.arm_root_uid,
            study_cohort_uid=(
                current_study_branch_arm.study_cohorts[0].study_cohort_uid
                if current_study_branch_arm.study_cohorts
                else None
            ),
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_branch_arm,
            reference_base_model=transformed_current,
        )

        if request_study_branch_arm.arm_uid is None:
            raise ValueError("arm_uid must not be None")

        return StudySelectionBranchArmVO.from_input_values(
            study_uid=current_study_branch_arm.study_uid,
            name=request_study_branch_arm.name,
            short_name=request_study_branch_arm.short_name,
            code=request_study_branch_arm.code,
            description=request_study_branch_arm.description,
            randomization_group=request_study_branch_arm.randomization_group,
            number_of_subjects=request_study_branch_arm.number_of_subjects,
            arm_root_uid=request_study_branch_arm.arm_uid,
            study_cohorts=(
                [
                    CompactStudyCohortVO(
                        study_cohort_uid=request_study_branch_arm.study_cohort_uid,
                        study_cohort_code=None,
                        study_cohort_name=None,
                    )
                ]
                if request_study_branch_arm.study_cohort_uid
                else []
            ),
            study_selection_uid=current_study_branch_arm.study_selection_uid,
            author_id=self.author,
        )

    @ensure_transaction(db)
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: StudySelectionBranchArmEditInput,
        validate: bool = True,
    ) -> StudySelectionBranchArm:
        repos = self._repos

        if selection_update_input.branch_arm_uid is None:
            raise exceptions.BusinessLogicException(
                msg="branch_arm_uid must not be None"
            )

        try:
            # Load aggregate
            selection_aggregate: StudySelectionBranchArmAR = (
                repos.study_branch_arm_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            assert selection_aggregate is not None

            # Load the current VO for updates
            current_vo, order = selection_aggregate.get_specific_object_selection(
                study_selection_uid=selection_update_input.branch_arm_uid
            )

            # merge current with updates
            updated_selection = self._patch_prepare_new_study_branch_arm(
                request_study_branch_arm=selection_update_input,
                current_study_branch_arm=current_vo,
            )
            selection_vo: StudySelectionBranchArmVO

            if updated_selection != current_vo:
                # let the aggregate update the value object
                selection_aggregate.update_selection(
                    updated_study_branch_arm_selection=updated_selection,
                    study_branch_arm_study_arm_update_conflict_callback=repos.study_branch_arm_repository.branch_arm_arm_update_conflict,
                    study_arm_exists_callback=self._repos.study_arm_repository.arm_specific_exists_by_uid,
                    branch_arm_exists_callback_by=repos.study_branch_arm_repository.branch_arm_exists_by,
                    validate=validate,
                )
                # sync with DB and save the update
                repos.study_branch_arm_repository.save(selection_aggregate, self.author)

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
            # add the branch arm and return
            return StudySelectionBranchArm.from_study_selection_branch_arm_ar_and_order(
                study_uid=study_uid,
                selection=selection_vo,
                order=order,
                find_simple_term_branch_arm_root_by_term_uid=self._get_specific_arm_selection,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    def get_specific_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        study_value_version: str | None = None,
    ) -> StudySelectionBranchArm:
        (
            _,
            new_selection,
            order,
        ) = self._get_specific_branch_arm_selection_by_uids(
            study_uid, study_selection_uid, study_value_version=study_value_version
        )
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_uid,
            study_value_version=study_value_version,
        )
        return StudySelectionBranchArm.from_study_selection_branch_arm_ar_and_order(
            study_uid=study_uid,
            selection=new_selection,
            order=order,
            find_simple_term_branch_arm_root_by_term_uid=self._get_specific_arm_selection,
            study_value_version=study_value_version,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    @staticmethod
    def _arm_types_match(
        existing_arm_type_uid: str | None, incoming_arm_type_uid: str | None
    ) -> bool:
        return (existing_arm_type_uid or None) == (incoming_arm_type_uid or None)

    def _vo_to_response_branch_arm(
        self,
        study_uid: str,
        selection: StudySelectionBranchArmVO,
        order: int,
        terms_at_specific_datetime: datetime | None,
    ) -> StudySelectionBranchArm:
        return self._transform_single_to_response_model(
            study_selection=selection,
            order=order,
            study_uid=study_uid,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    def _find_skip_match_vo(
        self,
        spec: StudySelectionBranchArmCreateInput,
        indexes: _BranchArmConflictIndexes,
    ) -> StudySelectionBranchArmVO | None:
        if spec.name and spec.name in indexes.by_name:
            return indexes.by_name[spec.name].vo
        if spec.short_name and spec.short_name in indexes.by_short_name:
            return indexes.by_short_name[spec.short_name].vo
        return None

    def _create_vo_from_create_input(
        self,
        study_uid: str,
        spec: StudySelectionBranchArmCreateInput,
    ) -> StudySelectionBranchArmVO:
        repos = self._repos
        return StudySelectionBranchArmVO.from_input_values(
            study_uid=study_uid,
            author_id=self.author,
            name=spec.name,
            short_name=spec.short_name,
            code=spec.code,
            description=spec.description,
            randomization_group=spec.randomization_group,
            number_of_subjects=spec.number_of_subjects,
            arm_root_uid=spec.arm_uid,
            study_cohorts=(
                [
                    CompactStudyCohortVO(
                        study_cohort_uid=spec.study_cohort_uid,
                        study_cohort_code=None,
                        study_cohort_name=None,
                    )
                ]
                if spec.study_cohort_uid
                else []
            ),
            generate_uid_callback=repos.study_branch_arm_repository.generate_uid,
        )

    def _format_parent_arm_type_label(self, source_arm: StudySelectionArm) -> str:
        if source_arm.arm_type and source_arm.arm_type.term_name:
            return source_arm.arm_type.term_name
        return "unspecified"

    def _format_parent_arm_skip_notification(
        self, branch_arm_name: str, source_arm: StudySelectionArm
    ) -> str:
        parent_arm_name = source_arm.name or "unnamed"
        arm_type_label = self._format_parent_arm_type_label(source_arm)
        return (
            f"Branch arm '{branch_arm_name}' skipped; no study arm on the target study "
            f"matches parent arm name '{parent_arm_name}' and arm type '{arm_type_label}'."
        )

    def _resolve_target_arm_vo(
        self,
        source_arm: StudySelectionArm,
        target_arm_indexes: _TargetArmIndexes,
    ) -> StudySelectionArmVO | None:
        if not source_arm.name:
            return None
        source_arm_type_uid = (
            source_arm.arm_type.term_uid if source_arm.arm_type else None
        )
        entry = target_arm_indexes.by_name_and_type.get(
            (source_arm.name, source_arm_type_uid)
        )
        return entry.vo if entry else None

    def _build_target_arm_indexes(self, study_uid: str) -> _TargetArmIndexes:
        repos = self._repos
        arm_aggregate = repos.study_arm_repository.find_by_study(study_uid=study_uid)
        if arm_aggregate is None:
            return _TargetArmIndexes(by_name_and_type={})
        return _TargetArmIndexes.from_arm_vos(list(arm_aggregate.study_arms_selection))

    def _map_source_branch_arms_to_create_or_skip(
        self, study_source_uid: str, study_uid: str
    ) -> list[_BranchArmCreateOrSkip]:
        source_branch_arms = self.get_all_selection(
            study_uid=study_source_uid, page_size=0
        ).items
        target_arm_indexes = self._build_target_arm_indexes(study_uid)
        items: list[_BranchArmCreateOrSkip] = []
        for branch_arm in source_branch_arms:
            target_arm_vo = self._resolve_target_arm_vo(
                branch_arm.arm_root, target_arm_indexes
            )
            if target_arm_vo is None:
                branch_arm_name = branch_arm.name or "unnamed"
                items.append(
                    _BranchArmCreateOrSkip(
                        parent_arm_skip_notification=self._format_parent_arm_skip_notification(
                            branch_arm_name=branch_arm_name,
                            source_arm=branch_arm.arm_root,
                        )
                    )
                )
                continue
            items.append(
                _BranchArmCreateOrSkip(
                    spec=StudySelectionBranchArmCreateInput(
                        name=branch_arm.name,
                        short_name=branch_arm.short_name,
                        code=branch_arm.code,
                        description=branch_arm.description,
                        randomization_group=branch_arm.randomization_group,
                        number_of_subjects=branch_arm.number_of_subjects,
                        arm_uid=target_arm_vo.study_selection_uid,
                    )
                )
            )
        return items

    def _run_cascade_for_created_branch_arms(
        self, study_uid: str, created_selections: list[StudySelectionBranchArmVO]
    ) -> None:
        repos = self._repos
        for new_selection in created_selections:
            if repos.study_arm_repository.arm_specific_has_connected_cell(
                study_uid=study_uid, arm_uid=new_selection.arm_root_uid
            ):
                self._cascade_creation(
                    study_uid=study_uid,
                    study_arm_uid=new_selection.arm_root_uid,
                    study_branch_arm_uid=new_selection.study_selection_uid,
                )

    @ensure_transaction(db)
    def _create_branch_arms_with_conflict_resolution(
        self,
        study_uid: str,
        items: list[_BranchArmCreateOrSkip],
    ) -> list[StudySelectionBranchArmBatchOutput]:
        repos = self._repos
        results: list[StudySelectionBranchArmBatchOutput] = []
        if not items:
            return results

        try:
            selection_aggregate: StudySelectionBranchArmAR = (
                repos.study_branch_arm_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )
            assert selection_aggregate is not None
            indexes = _BranchArmConflictIndexes.from_aggregate(selection_aggregate)
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid
            )
            created_vo_uids: set[str] = set()
            created_selections: list[StudySelectionBranchArmVO] = []

            for item in items:
                if item.parent_arm_skip_notification is not None:
                    results.append(
                        StudySelectionBranchArmBatchOutput(
                            response_code=status.HTTP_200_OK,
                            content=None,
                            notification=item.parent_arm_skip_notification,
                        )
                    )
                    continue

                assert item.spec is not None
                spec = item.spec
                skip_vo = self._find_skip_match_vo(spec, indexes)
                if skip_vo is not None:
                    _, order = selection_aggregate.get_specific_object_selection(
                        skip_vo.study_selection_uid
                    )
                    notification = None
                    if spec.name and spec.name in indexes.by_name:
                        notification = f"Branch arm '{spec.name}' already exists; creation skipped."
                    elif spec.short_name and spec.short_name in indexes.by_short_name:
                        notification = (
                            f"Branch arm short name '{spec.short_name}' already exists; "
                            "creation skipped."
                        )
                    results.append(
                        StudySelectionBranchArmBatchOutput(
                            response_code=status.HTTP_200_OK,
                            content=self._vo_to_response_branch_arm(
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
                selection_aggregate.add_branch_arm_selection(
                    study_branch_arm_selection=new_selection,
                    study_branch_arm_study_arm_update_conflict_callback=(
                        repos.study_branch_arm_repository.branch_arm_arm_update_conflict
                    ),
                    study_arm_exists_callback=repos.study_arm_repository.arm_specific_exists_by_uid,
                    branch_arm_exists_callback_by=repos.study_branch_arm_repository.branch_arm_exists_by,
                    validate=False,
                )
                indexes.register_vo(new_selection)
                created_vo_uids.add(new_selection.study_selection_uid)
                created_selections.append(new_selection)
                new_selection, order = (
                    selection_aggregate.get_specific_branch_arm_selection(
                        new_selection.study_selection_uid
                    )
                )
                results.append(
                    StudySelectionBranchArmBatchOutput(
                        response_code=status.HTTP_201_CREATED,
                        content=self._vo_to_response_branch_arm(
                            study_uid=study_uid,
                            selection=new_selection,
                            order=order,
                            terms_at_specific_datetime=terms_at_specific_datetime,
                        ),
                    )
                )

            for branch_arm_vo in selection_aggregate.study_branch_arms_selection:
                if branch_arm_vo.study_selection_uid in created_vo_uids:
                    branch_arm_vo.validate(
                        study_branch_arm_study_arm_update_conflict_callback=repos.study_branch_arm_repository.branch_arm_arm_update_conflict,
                        study_arm_exists_callback=repos.study_arm_repository.arm_specific_exists_by_uid,
                        branch_arm_exists_callback_by=repos.study_branch_arm_repository.branch_arm_exists_by,
                    )

            repos.study_branch_arm_repository.save(selection_aggregate, self.author)
            self._run_cascade_for_created_branch_arms(study_uid, created_selections)
        finally:
            repos.close()
        return results

    @ensure_transaction(db)
    def copy_branch_arms_from_study(
        self, study_uid: str, study_source_uid: str
    ) -> list[StudySelectionBranchArmBatchOutput]:
        exceptions.ValidationException.raise_if(
            study_source_uid == study_uid,
            msg="study_source_uid must differ from the target study.",
        )
        self.check_if_study_exists(study_uid)
        self.check_if_study_exists(study_source_uid)
        items = self._map_source_branch_arms_to_create_or_skip(
            study_source_uid=study_source_uid, study_uid=study_uid
        )
        return self._create_branch_arms_with_conflict_resolution(study_uid, items)

    @ensure_transaction(db)
    def handle_batch_operations(
        self,
        study_uid: str,
        operations: list[StudySelectionBranchArmBatchInput],
    ) -> list[StudySelectionBranchArmBatchOutput]:
        results: list[StudySelectionBranchArmBatchOutput | None] = [None] * len(
            operations
        )
        patched_branch_arm_uids: set[str] = set()
        try:
            index = 0
            while index < len(operations):
                operation = operations[index]
                if operation.method == "PATCH":
                    if isinstance(
                        operation.content, StudySelectionBranchArmBatchUpdateInput
                    ):
                        item = self.patch_selection(
                            study_uid=study_uid,
                            study_selection_uid=operation.content.branch_arm_uid,
                            selection_update_input=operation.content,
                            validate=False,
                        )
                        patched_branch_arm_uids.add(operation.content.branch_arm_uid)
                        results[index] = StudySelectionBranchArmBatchOutput(
                            response_code=status.HTTP_200_OK,
                            content=item,
                        )
                    else:
                        raise exceptions.ValidationException(
                            msg="PATCH operation requires StudySelectionBranchArmBatchUpdateInput as request payload."
                        )
                    index += 1
                elif operation.method == "POST":
                    post_items: list[_BranchArmCreateOrSkip] = []
                    post_indices: list[int] = []
                    while (
                        index < len(operations) and operations[index].method == "POST"
                    ):
                        content = operations[index].content
                        if not isinstance(content, StudySelectionBranchArmCreateInput):
                            raise exceptions.ValidationException(
                                msg="POST operation requires StudySelectionBranchArmCreateInput as request payload."
                            )
                        post_items.append(_BranchArmCreateOrSkip(spec=content))
                        post_indices.append(index)
                        index += 1
                    create_results = self._create_branch_arms_with_conflict_resolution(
                        study_uid=study_uid,
                        items=post_items,
                    )
                    for result_index, create_result in zip(
                        post_indices, create_results
                    ):
                        results[result_index] = create_result
                elif operation.method == "DELETE":
                    branch_arm_uid = getattr(operation.content, "branch_arm_uid", None)
                    if branch_arm_uid:
                        self.delete_selection(
                            study_uid=study_uid,
                            study_selection_uid=branch_arm_uid,
                        )
                        results[index] = StudySelectionBranchArmBatchOutput(
                            response_code=status.HTTP_204_NO_CONTENT,
                            content=None,
                        )
                    else:
                        raise exceptions.ValidationException(
                            msg="DELETE operation requires a branch_arm_uid in the request payload."
                        )
                    index += 1
                else:
                    raise exceptions.MethodNotAllowedException(method=operation.method)

            if patched_branch_arm_uids:
                study_branch_arm_ar: StudySelectionBranchArmAR = (
                    self._repos.study_branch_arm_repository.find_by_study(
                        study_uid=study_uid
                    )
                )
                for (
                    study_branch_arm_vo
                ) in study_branch_arm_ar.study_branch_arms_selection:
                    if (
                        study_branch_arm_vo.study_selection_uid
                        in patched_branch_arm_uids
                    ):
                        study_branch_arm_vo.validate(
                            study_branch_arm_study_arm_update_conflict_callback=self._repos.study_branch_arm_repository.branch_arm_arm_update_conflict,
                            study_arm_exists_callback=self._repos.study_arm_repository.arm_specific_exists_by_uid,
                            branch_arm_exists_callback_by=self._repos.study_branch_arm_repository.branch_arm_exists_by,
                        )
        except exceptions.MDRApiBaseException as error:
            raise error
        return [result for result in results if result is not None]
