from fastapi import status
from neomodel import db

from clinical_mdr_api.domain_repositories._utils.helpers import (
    acquire_write_lock_study_value,
)
from clinical_mdr_api.domain_repositories.models._utils import ListDistinct
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivitySchedule as StudyActivityScheduleNeoModel,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_schedule_repository import (
    SelectionHistory,
)
from clinical_mdr_api.domains.study_selections.study_activity_schedule import (
    StudyActivityScheduleVO,
)
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyActivitySchedule,
    StudyActivityScheduleBatchInput,
    StudyActivityScheduleBatchOutput,
    StudyActivityScheduleCreateInput,
    StudyActivityScheduleHistory,
    StudySelectionActivityInstanceEditInput,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import ensure_transaction
from clinical_mdr_api.services.studies.study_activity_instance_selection import (
    StudyActivityInstanceSelectionService,
)
from clinical_mdr_api.services.studies.study_endpoint_selection import (
    StudySelectionMixin,
)
from common import exceptions
from common.auth.user import user
from common.telemetry import trace_calls


class StudyActivityScheduleService(StudySelectionMixin):
    _repos: MetaRepository

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    @trace_calls
    def get_all_schedules(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        operational: bool = False,
        study_visit_uid: str | None = None,
    ) -> list[StudyActivitySchedule]:
        study_activity_schedules = (
            self._repos.study_activity_schedule_repository._get_all_schedules_in_study(
                study_uid=study_uid,
                study_value_version=study_value_version,
                operational=operational,
                study_visit_uid=study_visit_uid,
            )
        )
        study_activity_schedules_response_model = [
            StudyActivitySchedule.from_vo(
                i_study_activity_schedule_ogm,
            )
            for i_study_activity_schedule_ogm in study_activity_schedules
        ]
        return study_activity_schedules_response_model

    @trace_calls(args=[1, 2], kwargs=["study_uid", "study_activity_uid"])
    def get_all_schedules_for_specific_activity(
        self, study_uid: str, study_activity_uid: str
    ) -> list[StudyActivitySchedule]:
        return [
            StudyActivitySchedule.model_validate(sas_node)
            for sas_node in ListDistinct(
                StudyActivityScheduleNeoModel.nodes.traverse(
                    "has_after__audit_trail",
                    "study_visit__has_visit_name__has_latest_value",
                    "study_activity__has_selected_activity",
                    "study_activity__has_study_activity",
                )
                .filter(
                    study_value__latest_value__uid=study_uid,
                    study_activity__uid=study_activity_uid,
                    study_visit__has_study_visit__latest_value__uid=study_uid,
                    study_activity__has_study_activity__latest_value__uid=study_uid,
                )
                .order_by("uid")
                .resolve_subgraph()
            ).distinct()
        ]

    def _from_input_values(
        self, study_uid: str, schedule_input: StudyActivityScheduleCreateInput
    ) -> StudyActivityScheduleVO:
        return StudyActivityScheduleVO(
            study_uid=study_uid,
            study_activity_uid=schedule_input.study_activity_uid,
            study_activity_instance_uid=None,
            study_visit_uid=schedule_input.study_visit_uid,
        )

    @ensure_transaction(db)
    def create(
        self, study_uid: str, schedule_input: StudyActivityScheduleCreateInput
    ) -> StudyActivitySchedule:
        acquire_write_lock_study_value(study_uid)
        schedule_vo = self._repos.study_activity_schedule_repository.save(
            self._from_input_values(study_uid, schedule_input), self.author
        )
        return StudyActivitySchedule.from_vo(schedule_vo)

    @ensure_transaction(db)
    def delete(self, study_uid: str, schedule_uid: str):
        try:
            acquire_write_lock_study_value(study_uid)

            # Schedules connect a Study visit and activity instance
            # If a child instance of the activity is connected to the visit
            # We should remove that relationship first
            impacted_activity_instances = self._repos.study_activity_instance_repository.get_all_study_activity_instances_impacted_by_schedule_deletion(
                study_uid=study_uid,
                schedule_uid=schedule_uid,
            )
            for activity_instance in impacted_activity_instances:
                # Patch the impacted activity instance to remove the baseline relationship
                # Get current baseline visits
                current_baseline_visits = activity_instance.has_baseline.all()
                current_baseline_visits_uids = [
                    visit.uid for visit in current_baseline_visits
                ]
                # Get corresponding visit for schedule
                visit_to_disconnect_uid = (
                    StudyActivityScheduleNeoModel.nodes.filter(uid=schedule_uid)
                    .study_visit.all()[0]
                    .uid
                )
                # Remove impacted visit from baseline visits for activity instance
                current_baseline_visits_uids.remove(visit_to_disconnect_uid)
                # Patch the impacted activity instance to update the baseline visits
                study_activity_instance_service = (
                    StudyActivityInstanceSelectionService()
                )
                study_activity_instance_service.patch_selection(
                    study_uid=study_uid,
                    study_selection_uid=activity_instance.uid,
                    selection_update_input=StudySelectionActivityInstanceEditInput(
                        baseline_visit_uids=current_baseline_visits_uids,
                    ),
                )
            self._repos.study_activity_schedule_repository.delete(
                study_uid, schedule_uid, self.author
            )
        finally:
            self._repos.close()

    def _transform_history_to_response_model(
        self, study_selection_history: list[SelectionHistory]
    ) -> list[StudyActivitySchedule]:
        result = []
        for history in study_selection_history:
            result.append(
                StudyActivityScheduleHistory(
                    study_activity_schedule_uid=history.study_selection_uid,
                    study_activity_uid=history.study_activity_uid,
                    study_activity_instance_uid=history.study_activity_instance_uid,
                    study_visit_uid=history.study_visit_uid,
                    modified=history.start_date,
                )
            )
        return result

    def _transform_all_to_response_model(
        self, study_selection: list[SelectionHistory]
    ) -> list[StudyActivitySchedule]:
        result = []
        for history in study_selection:
            result.append(
                StudyActivityScheduleHistory(
                    study_activity_schedule_uid=history.study_selection_uid,
                    study_activity_uid=history.study_activity_uid,
                    study_visit_uid=history.study_visit_uid,
                    modified=history.start_date,
                )
            )
        return result

    @db.transaction
    def get_all_schedules_audit_trail(self, study_uid: str):
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_activity_schedule_repository.find_selection_history(
                        study_uid
                    )
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(msg=value_error.args[0])

            return self._transform_history_to_response_model(selection_history)
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection_audit_trail(
        self, study_uid: str, schedule_uid: str
    ) -> list[StudyActivitySchedule]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_activity_schedule_repository.find_selection_history(
                        study_uid, schedule_uid
                    )
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(msg=value_error.args[0])

            return self._transform_history_to_response_model(selection_history)
        finally:
            repos.close()

    @ensure_transaction(db)
    def handle_batch_operations(
        self,
        study_uid: str,
        operations: list[StudyActivityScheduleBatchInput],
    ) -> list[StudyActivityScheduleBatchOutput]:
        results = []
        for operation in operations:
            item = None
            try:
                if operation.method == "POST":
                    if isinstance(operation.content, StudyActivityScheduleCreateInput):
                        item = self.create(study_uid, operation.content)
                        response_code = status.HTTP_201_CREATED
                    else:
                        raise exceptions.ValidationException(
                            msg="POST operation requires StudyActivityScheduleCreateInput as request payload."
                        )

                elif operation.method == "DELETE":
                    self.delete(study_uid, operation.content.uid)
                    response_code = status.HTTP_204_NO_CONTENT
                else:
                    raise exceptions.MethodNotAllowedException(method=operation.method)
                results.append(
                    StudyActivityScheduleBatchOutput(
                        response_code=response_code, content=item
                    )
                )
            except exceptions.MDRApiBaseException as error:
                results.append(
                    StudyActivityScheduleBatchOutput.model_construct(
                        response_code=error.status_code,
                        content=BatchErrorResponse(message=str(error)),
                    )
                )
                raise error
        return results
