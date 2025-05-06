"""Service for study activity instructions."""

import datetime

from fastapi import status
from neomodel import db

from clinical_mdr_api.domain_repositories.models._utils import ListDistinct
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivityInstruction as StudyActivityInstructionNeoModel,
)
from clinical_mdr_api.domains.study_selections.study_activity_instruction import (
    StudyActivityInstructionVO,
)
from clinical_mdr_api.domains.syntax_instances.activity_instruction import (
    ActivityInstructionAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.study_selections.study_selection import (
    ActivityInstructionCreateInput,
    StudyActivityInstruction,
    StudyActivityInstructionBatchInput,
    StudyActivityInstructionBatchOutput,
    StudyActivityInstructionCreateInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    ensure_transaction,
    service_level_generic_filtering,
)
from clinical_mdr_api.services.studies.study_selection_base import StudySelectionMixin
from clinical_mdr_api.services.syntax_instances.activity_instructions import (
    ActivityInstructionService,
)
from common import exceptions
from common.auth.user import user


class StudyActivityInstructionService(StudySelectionMixin):
    _repos: MetaRepository

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    @db.transaction
    def get_all_instructions_for_all_studies(
        self,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[StudyActivityInstruction]:
        query = StudyActivityInstructionNeoModel.nodes.fetch_relations(
            "study_value__latest_value",
            "study_activity",
            "activity_instruction_value__activity_instruction_root",
            "has_after__audit_trail",
        )
        items = [
            StudyActivityInstruction.model_validate(sai_node)
            for sai_node in ListDistinct(query.resolve_subgraph()).distinct()
        ]

        # Do filtering, sorting, pagination and count
        filtered_items = service_level_generic_filtering(
            items=items,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        return filtered_items

    @db.transaction
    def get_all_instructions(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudyActivityInstruction]:
        if study_value_version:
            filters = {
                "study_value__has_version|version": study_value_version,
                "study_activity__has_study_activity__has_version|version": study_value_version,
                "study_value__has_version__uid": study_uid,
                "study_activity__has_study_activity__has_version__uid": study_uid,
            }
        else:
            filters = {
                "study_value__latest_value__uid": study_uid,
                "study_activity__has_study_activity__latest_value__uid": study_uid,
            }

        study_activity_instructions_ogm: list[StudyActivityInstruction] = [
            StudyActivityInstruction.model_validate(sai_node)
            for sai_node in ListDistinct(
                StudyActivityInstructionNeoModel.nodes.fetch_relations(
                    "study_activity",
                    "study_value__has_version",
                    "activity_instruction_value__activity_instruction_root",
                    "has_after__audit_trail",
                )
                .filter(**filters)
                .resolve_subgraph()
            ).distinct()
        ]
        study_activity_instruction_response_model = [
            StudyActivityInstruction.from_vo(
                StudyActivityInstructionVO(
                    uid=i_study_activity_instruction_ogm.study_activity_instruction_uid,
                    study_uid=study_uid,
                    study_activity_uid=i_study_activity_instruction_ogm.study_activity_uid,
                    activity_instruction_uid=i_study_activity_instruction_ogm.activity_instruction_uid,
                    activity_instruction_name=i_study_activity_instruction_ogm.activity_instruction_name,
                    start_date=i_study_activity_instruction_ogm.start_date,
                    author_username=i_study_activity_instruction_ogm.author_username,
                ),
                study_value_version=study_value_version,
            )
            for i_study_activity_instruction_ogm in study_activity_instructions_ogm
        ]

        return study_activity_instruction_response_model

    def get_all_study_instructions_for_specific_study_activity(
        self, study_uid: str, study_activity_uid: str
    ) -> list[StudyActivityInstruction]:
        return [
            StudyActivityInstruction.model_validate(sas_node)
            for sas_node in ListDistinct(
                StudyActivityInstructionNeoModel.nodes.fetch_relations(
                    "study_activity",
                    "activity_instruction_value__activity_instruction_root",
                    "has_after__audit_trail",
                )
                .filter(
                    study_value__latest_value__uid=study_uid,
                    study_activity__uid=study_activity_uid,
                    study_activity__has_study_activity__latest_value__uid=study_uid,
                )
                .resolve_subgraph()
            ).distinct()
        ]

    def _create_activity_instruction(
        self, activity_instruction_data: ActivityInstructionCreateInput
    ) -> ActivityInstructionAR:
        service = ActivityInstructionService()
        activity_instruction_ar = service.create_ar_from_input_values(
            activity_instruction_data
        )

        uid = activity_instruction_ar.uid
        if not service.repository.check_exists_by_name(activity_instruction_ar.name):
            service.repository.save(activity_instruction_ar)
        else:
            uid = service.repository.find_uid_by_name(name=activity_instruction_ar.name)
        activity_instruction_ar = service.repository.find_by_uid(uid, for_update=True)

        # if in draft status - approve
        if activity_instruction_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            activity_instruction_ar.approve(self.author)
            service.repository.save(activity_instruction_ar)
        elif activity_instruction_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                msg=f"There is no approved Activity Instruction with UID '{uid}'."
            )
        return activity_instruction_ar

    def _from_input_values(
        self,
        study_uid: str,
        activity_instruction_uid: str,
        study_activity_instruction_input: StudyActivityInstructionCreateInput,
    ) -> StudyActivityInstructionVO:
        return StudyActivityInstructionVO(
            study_uid=study_uid,
            study_activity_uid=study_activity_instruction_input.study_activity_uid,
            activity_instruction_uid=activity_instruction_uid,
            author_id=self.author,
            start_date=datetime.datetime.now(datetime.timezone.utc),
        )

    @ensure_transaction(db)
    def create(
        self,
        study_uid: str,
        study_activity_instruction_input: StudyActivityInstructionCreateInput,
    ) -> StudyActivityInstruction:
        """Create a new study activity instruction."""
        if study_activity_instruction_input.activity_instruction_data:
            # Create a new activity instruction first
            activity_instruction_ar = self._create_activity_instruction(
                study_activity_instruction_input.activity_instruction_data
            )
            activity_instruction_uid = activity_instruction_ar.uid
        else:
            # Link to an existing activity instruction
            activity_instruction_uid = (
                study_activity_instruction_input.activity_instruction_uid
            )
        instruction_vo = self._repos.study_activity_instruction_repository.save(
            self._from_input_values(
                study_uid, activity_instruction_uid, study_activity_instruction_input
            ),
            self.author,
        )
        return StudyActivityInstruction.from_vo(instruction_vo)

    @ensure_transaction(db)
    def delete(self, study_uid: str, instruction_uid: str):
        try:
            self._repos.study_activity_instruction_repository.delete(
                study_uid, instruction_uid, self.author
            )
        finally:
            self._repos.close()

    @ensure_transaction(db)
    def handle_batch_operations(
        self,
        study_uid: str,
        operations: list[StudyActivityInstructionBatchInput],
    ) -> list[StudyActivityInstructionBatchOutput]:
        results = []
        for operation in operations:
            result = {}
            item = None
            try:
                if operation.method == "POST":
                    item = self.create(study_uid, operation.content)
                    response_code = status.HTTP_201_CREATED
                elif operation.method == "DELETE":
                    self.delete(
                        study_uid, operation.content.study_activity_instruction_uid
                    )
                    response_code = status.HTTP_204_NO_CONTENT
                else:
                    raise exceptions.MethodNotAllowedException(method=operation.method)
                result["response_code"] = response_code
                if item:
                    result["content"] = item.model_dump()
                results.append(StudyActivityInstructionBatchOutput(**result))
            except exceptions.MDRApiBaseException as error:
                results.append(
                    StudyActivityInstructionBatchOutput.model_construct(
                        response_code=error.status_code,
                        content=BatchErrorResponse(message=str(error)),
                    )
                )
        return results
