from datetime import datetime
from typing import Any

from fastapi import status
from neomodel import db

from clinical_mdr_api.domain_repositories.study_selections.study_cohort_repository import (
    SelectionHistoryCohort,
)
from clinical_mdr_api.domains.study_selections.study_selection_cohort import (
    StudySelectionCohortAR,
    StudySelectionCohortVO,
)
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.study_selections.study_selection import (
    StudySelectionArm,
    StudySelectionBranchArm,
    StudySelectionCohort,
    StudySelectionCohortBatchInput,
    StudySelectionCohortBatchOutput,
    StudySelectionCohortBatchUpdateInput,
    StudySelectionCohortCreateInput,
    StudySelectionCohortEditInput,
    StudySelectionCohortHistory,
    StudySelectionCohortVersion,
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
from clinical_mdr_api.services.studies.study_selection_base import StudySelectionMixin
from common import exceptions
from common.auth.user import user


class StudyCohortSelectionService(StudySelectionMixin):
    _repos: MetaRepository

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionCohortAR | None,
        study_value_version: str | None = None,
    ) -> list[StudySelectionCohort]:
        if study_selection is None:
            return []

        result = []
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_selection.study_uid,
            study_value_version=study_value_version,
        )
        for order, selection in enumerate(
            study_selection.study_cohorts_selection, start=1
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
        study_selection: StudySelectionCohortVO,
        order: int,
        study_uid: str,
        terms_at_specific_datetime: datetime | None,
        study_value_version: str | None = None,
    ) -> StudySelectionCohort:
        return StudySelectionCohort.from_study_selection_cohort_ar_and_order(
            study_uid=study_uid,
            selection=study_selection,
            order=order,
            find_arm_root_by_uid=self._get_specific_arm_selection,
            find_branch_arm_root_cohort_by_uid=self._get_specific_branch_arm_selection,
            study_value_version=study_value_version,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    def get_all_selection(
        self,
        study_uid: str,
        project_name: str | None = None,
        project_number: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        arm_uid: str | None = None,
        study_value_version: str | None = None,
        split_if_in_multiple_arms_and_branches: bool = False,
    ) -> GenericFilteringReturn[StudySelectionCohort]:
        repos = self._repos
        try:
            cohort_selection_ar: StudySelectionCohortAR = (
                repos.study_cohort_repository.find_by_study(
                    study_uid,
                    arm_uid=arm_uid,
                    project_name=project_name,
                    project_number=project_number,
                    study_value_version=study_value_version,
                )
            )

            parsed_selections: list[StudySelectionCohort] = (
                self._transform_all_to_response_model(
                    cohort_selection_ar, study_value_version=study_value_version
                )
            )

            # Do filtering, sorting, pagination and count
            filtered_items: GenericFilteringReturn[StudySelectionCohort] = (
                service_level_generic_filtering(
                    items=parsed_selections,
                    filter_by=filter_by,
                    filter_operator=filter_operator,
                    sort_by=sort_by,
                    total_count=total_count,
                    page_number=page_number,
                    page_size=page_size,
                )
            )

            if split_if_in_multiple_arms_and_branches:
                items_to_return: list[StudySelectionCohort] = []
                for item in filtered_items.items:
                    study_arms = item.arm_roots
                    study_branches = item.branch_arm_roots
                    if (
                        study_arms
                        and study_branches
                        and len(study_arms) > 1
                        and len(study_branches) > 1
                        and len(study_arms) == len(study_branches)
                    ):
                        for study_arm, study_branch_arm in zip(
                            study_arms, study_branches
                        ):
                            item.arm_roots = [study_arm]
                            item.branch_arm_roots = [study_branch_arm]
                            items_to_return.append(item)
                    else:
                        items_to_return.append(item)
                return GenericFilteringReturn(
                    items=items_to_return, total=len(items_to_return)
                )
            return filtered_items
        finally:
            repos.close()

    @ensure_transaction(db)
    def delete_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        delete_linked_branches: bool = False,
    ):
        repos = self._repos
        try:
            branch_arms_on_cohort = (
                repos.study_branch_arm_repository.get_branch_arms_connected_to_cohort(
                    study_uid=study_uid, study_cohort_uid=study_selection_uid
                )
            )
            # Load aggregate
            selection_aggregate = repos.study_cohort_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )
            # remove the connection
            selection_aggregate.remove_cohort_selection(study_selection_uid)
            # sync with DB and save the update
            repos.study_cohort_repository.save(selection_aggregate, self.author)

            # delete study branch arms assigned to cohort if that's wanted
            if delete_linked_branches:
                # Load aggregate
                branch_arm_aggregate = repos.study_branch_arm_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
                for study_branch_arm in branch_arms_on_cohort:
                    # remove the connection
                    branch_arm_aggregate.remove_branch_arm_selection(
                        study_branch_arm.uid
                    )
                # sync with DB and save the update
                repos.study_branch_arm_repository.save(
                    branch_arm_aggregate, self.author
                )
        finally:
            repos.close()

    @ensure_transaction(db)
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> StudySelectionCohort:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = repos.study_cohort_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order
            )

            # sync with DB and save the update
            repos.study_cohort_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just added
            new_selection, order = selection_aggregate.get_specific_cohort_selection(
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
        self, study_selection_history: SelectionHistoryCohort, study_uid: str
    ) -> StudySelectionCohortHistory:
        return StudySelectionCohortHistory.from_study_selection_history(
            study_selection_history=study_selection_history,
            study_uid=study_uid,
        )

    def get_all_selection_audit_trail(
        self, study_uid: str
    ) -> list[StudySelectionCohortVersion]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_cohort_repository.find_selection_history(study_uid)
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(msg=value_error.args[0])

            unique_list_uids = list({x.study_selection_uid for x in selection_history})
            unique_list_uids.sort()
            # list of all study_cohorts
            data: list[StudySelectionCohortVersion] = []
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
                    data = calculate_diffs(versions, StudySelectionCohortVersion)
                else:
                    data.extend(calculate_diffs(versions, StudySelectionCohortVersion))
            return data
        finally:
            repos.close()

    @ensure_transaction(db)
    def get_specific_selection_audit_trail(
        self, study_uid: str, study_selection_uid: str
    ) -> list[StudySelectionCohortVersion]:
        repos = self._repos
        try:
            selection_history = repos.study_cohort_repository.find_selection_history(
                study_uid, study_selection_uid
            )
            versions = [
                self._transform_each_history_to_response_model(
                    _, study_uid
                ).model_dump()
                for _ in selection_history
            ]
            data = calculate_diffs(versions, StudySelectionCohortVersion)
            return data
        finally:
            repos.close()

    def _get_specific_arm_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        terms_at_specific_datetime: datetime | None = None,
        study_value_version: str | None = None,
    ) -> StudySelectionArm:
        (
            _,
            new_selection,
            order,
        ) = self._get_specific_arm_selection_by_uids(
            study_uid, study_selection_uid, study_value_version=study_value_version
        )
        terms_at_specific_datetime = (
            self._extract_study_standards_effective_date(
                study_uid=study_uid,
                study_value_version=study_value_version,
            )
            if not terms_at_specific_datetime
            else terms_at_specific_datetime
        )
        # Without Connected BranchArms due to only is necessary to have the StudyArm
        return StudySelectionArm.from_study_selection_arm_ar_and_order(
            study_uid=study_uid,
            selection=new_selection,
            order=order,
            find_codelist_term_arm_type=self._repos.ct_codelist_name_repository.get_codelist_term_by_uid_and_submval,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    def _get_specific_branch_arm_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        study_value_version: str | None = None,
        terms_at_specific_datetime: datetime | None = None,
    ) -> StudySelectionBranchArm:
        (
            _,
            new_selection,
            order,
        ) = self._get_specific_branch_arm_selection_by_uids(
            study_uid,
            study_selection_uid,
            study_value_version=study_value_version,
        )
        terms_at_specific_datetime = (
            self._extract_study_standards_effective_date(
                study_uid=study_uid,
                study_value_version=study_value_version,
            )
            if not terms_at_specific_datetime
            else terms_at_specific_datetime
        )
        return StudySelectionBranchArm.from_study_selection_branch_arm_ar_and_order(
            study_uid=study_uid,
            selection=new_selection,
            order=order,
            find_simple_term_branch_arm_root_by_term_uid=self._get_specific_arm_selection,
            study_value_version=study_value_version,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    @ensure_transaction(db)
    def make_selection(
        self,
        study_uid: str,
        selection_create_input: StudySelectionCohortCreateInput,
        validate: bool = True,
    ) -> StudySelectionCohort:
        repos = self._repos

        try:
            # create new VO to add
            new_selection = StudySelectionCohortVO.from_input_values(
                study_uid=study_uid,
                author_id=self.author,
                name=selection_create_input.name or "",
                short_name=selection_create_input.short_name or "",
                code=selection_create_input.code,
                description=selection_create_input.description,
                number_of_subjects=selection_create_input.number_of_subjects,
                branch_arm_root_uids=selection_create_input.branch_arm_uids,
                arm_root_uids=selection_create_input.arm_uids,
                generate_uid_callback=repos.study_cohort_repository.generate_uid,
            )
            # Load aggregate
            selection_aggregate: StudySelectionCohortAR = (
                repos.study_cohort_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )
            assert selection_aggregate is not None

            # add VO to aggregate
            selection_aggregate.add_cohort_selection(
                study_cohort_selection=new_selection,
                study_arm_exists_callback=self._repos.study_arm_repository.arm_specific_exists_by_uid,
                study_branch_arm_exists_callback=self._repos.study_branch_arm_repository.branch_arm_specific_exists_by_uid,
                cohort_exists_callback_by=repos.study_cohort_repository.cohort_exists_by,
                validate=validate,
            )

            # sync with DB and save the update
            repos.study_cohort_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just added
            (
                new_selection,
                order,
            ) = selection_aggregate.get_specific_cohort_selection(
                new_selection.study_selection_uid
            )
            terms_at_specific_datetime = self._extract_study_standards_effective_date(
                study_uid=study_uid,
            )

            # add the Cohort and return
            return StudySelectionCohort.from_study_selection_cohort_ar_and_order(
                study_uid=study_uid,
                selection=new_selection,
                order=order,
                find_arm_root_by_uid=self._get_specific_arm_selection,
                find_branch_arm_root_cohort_by_uid=self._get_specific_branch_arm_selection,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    def _patch_prepare_new_study_cohort(
        self,
        request_study_cohort: StudySelectionCohortEditInput,
        current_study_cohort: StudySelectionCohortVO,
    ) -> StudySelectionCohortVO:
        # transform current to input model
        transformed_current = StudySelectionCohortEditInput(
            cohort_uid=current_study_cohort.study_selection_uid,
            name=current_study_cohort.name,
            short_name=current_study_cohort.short_name,
            code=current_study_cohort.code,
            description=current_study_cohort.description,
            number_of_subjects=current_study_cohort.number_of_subjects,
            branch_arm_uids=current_study_cohort.branch_arm_root_uids,
            arm_uids=current_study_cohort.arm_root_uids,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_cohort,
            reference_base_model=transformed_current,
        )

        return StudySelectionCohortVO.from_input_values(
            study_uid=current_study_cohort.study_uid,
            name=request_study_cohort.name or "",
            short_name=request_study_cohort.short_name or "",
            code=request_study_cohort.code,
            description=request_study_cohort.description,
            number_of_subjects=request_study_cohort.number_of_subjects,
            branch_arm_root_uids=request_study_cohort.branch_arm_uids,
            arm_root_uids=request_study_cohort.arm_uids,
            study_selection_uid=current_study_cohort.study_selection_uid,
            author_id=self.author,
        )

    @ensure_transaction(db)
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: StudySelectionCohortEditInput,
        validate: bool = True,
    ) -> StudySelectionCohort:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate: StudySelectionCohortAR = (
                repos.study_cohort_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            assert selection_aggregate is not None

            # Load the current VO for updates
            current_vo, order = selection_aggregate.get_specific_object_selection(
                study_selection_uid=study_selection_uid
            )

            # merge current with updates
            updated_selection = self._patch_prepare_new_study_cohort(
                request_study_cohort=selection_update_input,
                current_study_cohort=current_vo,
            )

            selection_vo: StudySelectionCohortVO
            if updated_selection != current_vo:
                # let the aggregate update the value object
                selection_aggregate.update_selection(
                    updated_study_cohort_selection=updated_selection,
                    study_arm_exists_callback=self._repos.study_arm_repository.arm_specific_exists_by_uid,
                    study_branch_arm_exists_callback=self._repos.study_branch_arm_repository.branch_arm_specific_exists_by_uid,
                    cohort_exists_callback_by=repos.study_cohort_repository.cohort_exists_by,
                    validate=validate,
                )
                # sync with DB and save the update
                repos.study_cohort_repository.save(selection_aggregate, self.author)

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
                study_uid=study_uid,
            )

            # add the cohort and return
            return StudySelectionCohort.from_study_selection_cohort_ar_and_order(
                study_uid=study_uid,
                selection=selection_vo,
                order=order,
                find_arm_root_by_uid=self._get_specific_arm_selection,
                find_branch_arm_root_cohort_by_uid=self._get_specific_branch_arm_selection,
                terms_at_specific_datetime=terms_at_specific_datetime,
            )
        finally:
            repos.close()

    def get_specific_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        study_value_version: str | None = None,
    ) -> StudySelectionCohort:
        (
            _,
            new_selection,
            order,
        ) = self._get_specific_cohort_selection_by_uids(
            study_uid, study_selection_uid, study_value_version=study_value_version
        )
        terms_at_specific_datetime = self._extract_study_standards_effective_date(
            study_uid=study_uid,
            study_value_version=study_value_version,
        )
        return StudySelectionCohort.from_study_selection_cohort_ar_and_order(
            study_uid=study_uid,
            selection=new_selection,
            order=order,
            find_arm_root_by_uid=self._get_specific_arm_selection,
            find_branch_arm_root_cohort_by_uid=self._get_specific_branch_arm_selection,
            study_value_version=study_value_version,
            terms_at_specific_datetime=terms_at_specific_datetime,
        )

    @ensure_transaction(db)
    def handle_batch_operations(
        self,
        study_uid: str,
        operations: list[StudySelectionCohortBatchInput],
    ) -> list[StudySelectionCohortBatchOutput]:
        results = []
        try:
            for operation in operations:
                item = None
                if operation.method == "PATCH":
                    if isinstance(
                        operation.content, StudySelectionCohortBatchUpdateInput
                    ):
                        item = self.patch_selection(
                            study_uid=study_uid,
                            study_selection_uid=operation.content.cohort_uid,
                            selection_update_input=operation.content,
                            validate=False,
                        )
                        response_code = status.HTTP_200_OK
                    else:
                        raise exceptions.ValidationException(
                            msg="PATCH operation requires StudySelectionCohortBatchUpdateInput as request payload."
                        )
                elif operation.method == "POST":
                    if isinstance(operation.content, StudySelectionCohortCreateInput):
                        item = self.make_selection(
                            study_uid=study_uid,
                            selection_create_input=operation.content,
                            validate=False,
                        )
                        response_code = status.HTTP_201_CREATED
                    else:
                        raise exceptions.ValidationException(
                            msg="POST operation requires StudySelectionCohortCreateInput as request payload."
                        )
                else:
                    raise exceptions.MethodNotAllowedException(method=operation.method)
                results.append(
                    StudySelectionCohortBatchOutput(
                        response_code=response_code,
                        content=item,
                    )
                )

            # For batch operations we need to perform validation/uniqueness checks after all requests are handled
            study_cohort_ar: StudySelectionCohortAR = (
                self._repos.study_cohort_repository.find_by_study(study_uid=study_uid)
            )
            modified_study_cohorts = {
                study_cohort.content.cohort_uid for study_cohort in results
            }
            for study_cohort_vo in study_cohort_ar.study_cohorts_selection:
                if study_cohort_vo.study_selection_uid in modified_study_cohorts:
                    study_cohort_vo.validate(
                        study_arm_exists_callback=self._repos.study_arm_repository.arm_specific_exists_by_uid,
                        study_branch_arm_exists_callback=self._repos.study_branch_arm_repository.branch_arm_specific_exists_by_uid,
                        cohort_exists_callback_by=self._repos.study_cohort_repository.cohort_exists_by,
                    )
        except exceptions.MDRApiBaseException as error:
            results.append(
                StudySelectionCohortBatchOutput.model_construct(
                    response_code=error.status_code,
                    content=BatchErrorResponse(message=str(error)),
                )
            )
            raise error
        return results
