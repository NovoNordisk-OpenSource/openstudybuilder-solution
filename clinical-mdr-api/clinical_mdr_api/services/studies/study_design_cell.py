from datetime import datetime, timezone

from fastapi import status
from neomodel import db
from neomodel.sync_.match import Optional

from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyDesignCell as StudyDesignCellNeoModel,
)
from clinical_mdr_api.domain_repositories.study_selections.study_design_cell_repository import (
    StudyDesignCellHistory,
)
from clinical_mdr_api.domains.study_selections.study_design_cell import (
    StudyDesignCellVO,
)
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyDesignCell,
    StudyDesignCellBatchInput,
    StudyDesignCellBatchOutput,
    StudyDesignCellCreateInput,
    StudyDesignCellEditInput,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyDesignCellHistory as StudyDesignCellHistoryModel,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyDesignCellVersion,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    ensure_transaction,
    fill_missing_values_in_base_model_from_reference_base_model,
)
from clinical_mdr_api.services.studies.study_endpoint_selection import (
    StudySelectionMixin,
)
from common import exceptions
from common.auth.user import user


class StudyDesignCellService(StudySelectionMixin):
    _repos: MetaRepository

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    @db.transaction
    def get_all_design_cells(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> list[StudyDesignCell]:
        design_cell_ar = (
            self._repos.study_design_cell_repository.find_all_design_cells_by_study(
                study_uid=study_uid, study_value_version=study_value_version
            )
        )
        design_cells = [
            StudyDesignCell.from_vo(
                i_design_cell, study_value_version=study_value_version
            )
            for i_design_cell in design_cell_ar
        ]
        return design_cells

    @db.transaction
    def get_all_selection_within_arm(
        self,
        study_uid: str,
        study_arm_uid: str,
        study_value_version: str | None = None,
    ) -> list[StudyDesignCell]:
        sdc_nodes = (
            self._repos.study_design_cell_repository.get_design_cells_connected_to_arm(
                study_uid, study_arm_uid, study_value_version=study_value_version
            )
        )
        return [
            StudyDesignCell.from_vo(
                self._repos.study_design_cell_repository._from_repository_values(
                    study_uid=study_uid,
                    design_cell=sdc_node,
                    study_value_version=study_value_version,
                ),
                study_value_version=study_value_version,
            )
            for sdc_node in sdc_nodes
        ]

    @db.transaction
    def get_all_selection_within_branch_arm(
        self,
        study_uid: str,
        study_branch_arm_uid: str,
        study_value_version: str | None = None,
    ) -> list[StudyDesignCell]:
        sdc_nodes = self._repos.study_design_cell_repository.get_design_cells_connected_to_branch_arm(
            study_uid,
            study_branch_arm_uid,
            study_value_version=study_value_version,
        )
        return [
            StudyDesignCell.from_vo(
                self._repos.study_design_cell_repository._from_repository_values(
                    study_uid=study_uid,
                    design_cell=sdc_node,
                    study_value_version=study_value_version,
                ),
                study_value_version=study_value_version,
            )
            for sdc_node in sdc_nodes
        ]

    @db.transaction
    def get_all_selection_within_epoch(
        self,
        study_uid: str,
        study_epoch_uid: str,
        study_value_version: str | None = None,
    ) -> list[StudyDesignCell]:
        sdc_nodes = self._repos.study_design_cell_repository.get_design_cells_connected_to_epoch(
            study_uid, study_epoch_uid, study_value_version=study_value_version
        )
        return [
            StudyDesignCell.from_vo(
                self._repos.study_design_cell_repository._from_repository_values(
                    study_uid=study_uid,
                    design_cell=sdc_node,
                    study_value_version=study_value_version,
                ),
                study_value_version=study_value_version,
            )
            for sdc_node in sdc_nodes
        ]

    def get_specific_design_cell(
        self, study_uid: str, design_cell_uid: str
    ) -> StudyDesignCell:
        sdc_node = (
            StudyDesignCellNeoModel.nodes.fetch_relations(
                "study_epoch__has_epoch__has_name_root__has_latest_value",
                "study_element",
                "has_after__audit_trail",
                Optional("study_arm"),
                Optional("study_branch_arm"),
            )
            .filter(study_value__latest_value__uid=study_uid, uid=design_cell_uid)
            .resolve_subgraph()
        )

        exceptions.NotFoundException.raise_if(
            sdc_node is None or len(sdc_node) == 0, "Study Design Cell", design_cell_uid
        )
        return StudyDesignCell.model_validate(sdc_node[0])

    def _from_input_values(
        self, study_uid: str, design_cell_input: StudyDesignCellCreateInput
    ) -> StudyDesignCellVO:
        return StudyDesignCellVO(
            study_uid=study_uid,
            study_arm_uid=design_cell_input.study_arm_uid,
            study_arm_name=None,
            study_branch_arm_uid=design_cell_input.study_branch_arm_uid,
            study_branch_arm_name=None,
            study_epoch_uid=design_cell_input.study_epoch_uid,
            study_epoch_name=None,
            study_element_uid=design_cell_input.study_element_uid,
            study_element_name=None,
            order=design_cell_input.order,
            transition_rule=design_cell_input.transition_rule,
            author_id=self.author,
            start_date=datetime.now(timezone.utc),
        )

    @ensure_transaction(db)
    def create(
        self, study_uid: str, design_cell_input: StudyDesignCellCreateInput
    ) -> StudyDesignCell:
        # all_design_cells: list[StudyDesignCellVO]
        all_design_cells = (
            self._repos.study_design_cell_repository.find_all_design_cells_by_study(
                study_uid
            )
        )

        # created_design_cell: StudyDesignVO, from the input
        created_design_cell = self._from_input_values(study_uid, design_cell_input)

        # if the order want an specific order
        if design_cell_input.order:
            exceptions.BusinessLogicException.raise_if(
                len(all_design_cells) + 1 < created_design_cell.order,
                msg="Order is too big.",
            )
            # shift one order more to fit the modified
            for design_cell in all_design_cells[created_design_cell.order - 1 :]:
                design_cell.order += 1
                self._repos.study_design_cell_repository.save(
                    design_cell, self.author, create=False
                )
        # if not just add one to the order
        else:
            created_design_cell.order = len(all_design_cells) + 1

        # created_item: StudyDesignCellVO
        created_item = self._repos.study_design_cell_repository.save(
            created_design_cell, self.author, create=True
        )

        # return json response model
        return StudyDesignCell.from_vo(created_item)

    def _edit_study_design_cell_vo(
        self,
        study_design_cell_to_edit: StudyDesignCellVO,
        study_design_cell_edit_input: StudyDesignCellEditInput,
    ):
        study_design_cell_to_edit.edit_core_properties(
            study_epoch_uid=study_design_cell_to_edit.study_epoch_uid,
            study_element_uid=study_design_cell_edit_input.study_element_uid,
            study_arm_uid=study_design_cell_edit_input.study_arm_uid,
            study_branch_arm_uid=study_design_cell_edit_input.study_branch_arm_uid,
            transition_rule=study_design_cell_edit_input.transition_rule,
            order=study_design_cell_edit_input.order,
        )

    @ensure_transaction(db)
    def patch(
        self, study_uid: str, design_cell_update_input: StudyDesignCellEditInput
    ) -> StudyDesignCell:
        # study_design_cell: StudyDesignCellVO
        study_design_cell = self._repos.study_design_cell_repository.find_by_uid(
            study_uid=study_uid, uid=design_cell_update_input.study_design_cell_uid
        )
        if design_cell_update_input.study_branch_arm_uid is not None:
            design_cell_update_input.study_arm_uid = None
        elif design_cell_update_input.study_arm_uid is not None:
            design_cell_update_input.study_branch_arm_uid = None

        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=design_cell_update_input,
            # return json response model
            reference_base_model=StudyDesignCell.from_vo(study_design_cell),
        )

        self._edit_study_design_cell_vo(
            study_design_cell_to_edit=study_design_cell,
            study_design_cell_edit_input=design_cell_update_input,
        )
        # updated_item: StudyDesignCellVO
        updated_item = self._repos.study_design_cell_repository.save(
            study_design_cell, self.author, create=False
        )
        # return json response model
        return StudyDesignCell.from_vo(updated_item)

    @ensure_transaction(db)
    def delete(self, study_uid: str, design_cell_uid: str):
        study_design_cell = self._repos.study_design_cell_repository.find_by_uid(
            study_uid=study_uid, uid=design_cell_uid
        )
        self._repos.study_design_cell_repository.delete(
            study_uid, design_cell_uid, self.author
        )
        all_design_cells = (
            self._repos.study_design_cell_repository.find_all_design_cells_by_study(
                study_uid
            )
        )
        # shift one order more to fit the modified
        for design_cell in all_design_cells[study_design_cell.order - 1 :]:
            design_cell.order -= 1
            self._repos.study_design_cell_repository.save(
                design_cell, author_id=self.author, create=False
            )

    def _transform_each_history_to_response_model(
        self, study_selection_history: StudyDesignCellHistory, study_uid: str
    ) -> StudyDesignCellHistoryModel:
        return StudyDesignCellHistoryModel(
            study_uid=study_uid,
            study_design_cell_uid=study_selection_history.study_selection_uid,
            study_arm_uid=study_selection_history.study_arm_uid,
            study_branch_arm_uid=study_selection_history.study_branch_arm_uid,
            study_epoch_uid=study_selection_history.study_epoch_uid,
            study_element_uid=study_selection_history.study_element_uid,
            transition_rule=study_selection_history.transition_rule,
            change_type=study_selection_history.change_type,
            modified=study_selection_history.start_date,
            order=study_selection_history.order,
        )

    @db.transaction
    def get_all_design_cells_audit_trail(
        self, study_uid: str
    ) -> list[StudyDesignCellVersion]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_design_cell_repository.find_selection_history(study_uid)
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(msg=value_error.args[0])

            unique_list_uids = list({x.study_selection_uid for x in selection_history})
            unique_list_uids.sort()
            data = []
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
                    data = calculate_diffs(versions, StudyDesignCellVersion)
                else:
                    data.extend(calculate_diffs(versions, StudyDesignCellVersion))
            return data
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection_audit_trail(
        self, study_uid: str, design_cell_uid: str
    ) -> list[StudyDesignCellVersion]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_design_cell_repository.find_selection_history(
                        study_uid, design_cell_uid
                    )
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(msg=value_error.args[0])

            versions = [
                self._transform_each_history_to_response_model(
                    _, study_uid
                ).model_dump()
                for _ in selection_history
            ]
            data = calculate_diffs(versions, StudyDesignCellVersion)
            return data
        finally:
            repos.close()

    @ensure_transaction(db)
    def handle_batch_operations(
        self, study_uid: str, operations: list[StudyDesignCellBatchInput]
    ) -> list[StudyDesignCellBatchOutput]:
        results = []
        for operation in operations:
            result = {}
            item = None
            try:
                if operation.method == "POST":
                    item = self.create(study_uid, operation.content)
                    response_code = status.HTTP_201_CREATED
                elif operation.method == "PATCH":
                    item = self.patch(study_uid, operation.content)
                    response_code = status.HTTP_200_OK
                elif operation.method == "DELETE":
                    self.delete(study_uid, operation.content.uid)
                    response_code = status.HTTP_204_NO_CONTENT
                else:
                    raise exceptions.MethodNotAllowedException(method=operation.method)
                result["response_code"] = response_code
                if item:
                    result["content"] = item.model_dump()
                results.append(StudyDesignCellBatchOutput(**result))
            except exceptions.MDRApiBaseException as error:
                results.append(
                    StudyDesignCellBatchOutput.model_construct(
                        response_code=error.status_code,
                        content=BatchErrorResponse(message=str(error)),
                    )
                )
        return results
