import logging
from collections.abc import Callable
from typing import Any

from neomodel import db

from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTermUidInput
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.study_selections import (
    study_epoch,
    study_selection,
    study_visit,
)
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_activity_selection import (
    StudyActivityScheduleService,
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.services.studies.study_visit import StudyVisitService
from common.exceptions import (
    BusinessLogicException,
    MDRApiBaseException,
    ValidationException,
)
from consumer_api.v1 import db as DB
from consumer_api.v1 import models

log = logging.getLogger(__name__)

# Lookup-hint templates appended to invalid-term-UID error messages.
# We do NOT inline the full set of valid UIDs into the error: codelists
# can hold hundreds of entries, producing multi-KB responses and leaking
# codelist contents on every validation failure. Point callers at the
# GET endpoint that lists valid values instead.
_TERM_LOOKUP_HINT = (
    "Valid values can be retrieved from "
    "GET /v1/library/ct/codelist-terms?codelist_submission_value={codelist}."
)
_TIME_UNIT_LOOKUP_HINT = (
    "Valid values can be retrieved from "
    "GET /v1/library/unit-definitions?subset=Study Time."
)


class SoAService:

    @staticmethod
    def _sanitize_for_log(val: str) -> str:
        return val.replace("\r", "").replace("\n", "")

    @db.transaction
    def create_soa(
        self,
        study_uid: str,
        soa_input: models.SoACreateInput,
    ) -> models.SoACreateResponse:
        """
        Creates a new Schedule of Activities (SoA) with epochs, visits, and activities.

        This endpoint accepts a complete study activity schedule including:
        - Epochs: Study phases (Screening, Treatment, Follow-up, etc.)
        - Visits: Scheduled or unscheduled visits with timing and windows
        - Activities: Study activities linked to specific visits

        Returns a confirmation with created resource identifiers.
        """
        self._validate_study(study_uid)
        self._validate_soa_input(soa_input)

        study_epoch_service = StudyEpochService()
        study_visit_service = StudyVisitService(study_uid=study_uid)
        study_activity_service = StudyActivitySelectionService()
        study_activity_schedule_service = StudyActivityScheduleService()

        created_epochs: dict[str, str] = {}
        created_visits: dict[str, str] = {}
        created_activities: dict[str, str] = {}

        # Delete existing epochs, visits and activities for the study before creating new ones
        self._delete_existing_epochs_visits_activities(
            study_uid=study_uid,
            study_epoch_service=study_epoch_service,
            study_visit_service=study_visit_service,
            study_activity_service=study_activity_service,
        )

        self._create_epochs(study_uid, soa_input, study_epoch_service, created_epochs)

        self._create_visits(
            study_uid,
            soa_input,
            study_visit_service,
            created_epochs,
            created_visits,
        )

        self._create_activities_batch(
            study_uid,
            soa_input,
            study_activity_service,
            study_activity_schedule_service,
            created_visits,
            created_activities,
        )

        return models.SoACreateResponse(
            epochs=created_epochs,
            visits=created_visits,
            activities=created_activities,
        )

    def _create_activities_batch(
        self,
        study_uid: str,
        soa_input: models.SoACreateInput,
        study_activity_service: StudyActivitySelectionService,
        study_activity_schedule_service: StudyActivityScheduleService,
        created_visits: dict[str, str],
        created_activities: dict[str, str],
    ):
        batch_operations: list[study_selection.StudySelectionActivityBatchInput] = []

        # Build activity creation payloads
        for activity_input in soa_input.activities:
            activity_payload = study_selection.StudySelectionActivityCreateInput(
                activity_uid=activity_input.activity_uid,
                soa_group_term_uid=activity_input.soa_group_uid,
                activity_group_uid=activity_input.activity_group_uid,
                activity_subgroup_uid=activity_input.activity_subgroup_uid,
                show_activity_in_protocol_flowchart=True,
            )
            batch_operations.append(
                study_selection.StudySelectionActivityBatchInput(
                    method="POST", content=activity_payload
                )
            )

        # Create activities in batch
        log.info("Creating %d activities in batch", len(batch_operations))
        created_activities_response = study_activity_service.handle_batch_operations(
            study_uid=study_uid, operations=batch_operations
        )
        log.info("Created %d activities in batch", len(created_activities_response))

        # Single pass: collect successes into the caller-supplied map and
        # aggregate any failures so we can report all of them at once.
        activity_failures: list[str] = []
        for activity_input, activity_response in zip(
            soa_input.activities, created_activities_response, strict=True
        ):
            if activity_response.response_code == 201 and isinstance(
                activity_response.content, study_selection.StudySelectionActivity
            ):
                study_activity_uid = activity_response.content.study_activity_uid
                if study_activity_uid is None:
                    activity_failures.append(
                        f"'{activity_input.reference_id}': Missing study_activity_uid in success response"
                    )
                    continue
                created_activities[activity_input.reference_id] = study_activity_uid
            else:
                activity_failures.append(
                    f"'{activity_input.reference_id}': "
                    f"{self._extract_batch_error(activity_response.content)}"
                )

        if activity_failures:
            raise ValidationException(
                msg="Failed to create activities: " + "; ".join(activity_failures)
            )

        # Create activity schedules for each activity linked to a visit.
        # Every activity above succeeded (we'd have raised otherwise), so
        # `created_activities` contains a UID for every input reference_id.
        activity_schedules_payloads: list[
            study_selection.StudyActivityScheduleBatchInput
        ] = []
        for activity_input in soa_input.activities:
            study_activity_uid = created_activities[activity_input.reference_id]
            for visit_ref_id in activity_input.visit_reference_ids:
                activity_schedules_payloads.append(
                    study_selection.StudyActivityScheduleBatchInput(
                        method="POST",
                        content=study_selection.StudyActivityScheduleCreateInput(
                            study_activity_uid=study_activity_uid,
                            study_visit_uid=created_visits[visit_ref_id],
                        ),
                    )
                )
        schedule_responses = study_activity_schedule_service.handle_batch_operations(
            study_uid=study_uid,
            operations=activity_schedules_payloads,
        )

        schedule_failures = [
            self._extract_batch_error(resp.content)
            for resp in schedule_responses
            if resp.response_code != 201
        ]
        if schedule_failures:
            raise ValidationException(
                msg="Failed to create activity schedules: "
                + "; ".join(schedule_failures)
            )

        log.info(
            "Created %d activity schedules in batch", len(activity_schedules_payloads)
        )

    @staticmethod
    def _extract_batch_error(content: Any) -> str:
        """Pull a clean error string out of a batch response's `content`.

        Batch endpoints return either the created entity, `None`, or a
        `BatchErrorResponse` on failure. Only the last carries the
        human-readable message; `repr`-ing the whole content (as the
        previous implementation did) embeds a Pydantic dump in the API
        error message.
        """
        if isinstance(content, BatchErrorResponse):
            return content.message or "unknown error"
        return "unknown error"

    def _create_visits(
        self,
        study_uid: str,
        soa_input: models.SoACreateInput,
        study_visit_service: StudyVisitService,
        created_epochs: dict[str, str],
        created_visits: dict[str, str],
    ):
        for visit_input in soa_input.visits:
            log.info("Creating visit for reference ID: %s", visit_input.reference_id)
            visit_payload = study_visit.StudyVisitCreateInput(
                visit_type=CTTermUidInput(term_uid=visit_input.type),
                visit_class=visit_input.visit_class,
                visit_subclass=visit_input.subclass,
                visit_contact_mode=CTTermUidInput(term_uid=visit_input.contact_mode),
                show_visit=True,
                visit_number=visit_input.number,
                unique_visit_number=self._effective_unique_number(visit_input),
                visit_name=visit_input.name,
                visit_short_name=visit_input.short_name,
                study_epoch_uid=created_epochs[visit_input.epoch_reference_id],
                is_global_anchor_visit=visit_input.is_global_anchor_visit,
                min_visit_window_value=(
                    -visit_input.window.before
                    if visit_input.window and visit_input.window.before
                    else 0
                ),
                max_visit_window_value=(
                    visit_input.window.after
                    if visit_input.window and visit_input.window.after
                    else 0
                ),
                visit_window_unit_uid=(
                    visit_input.window.unit_uid if visit_input.window else None
                ),
                time_reference=(
                    CTTermUidInput(term_uid=visit_input.timing.timing_reference_uid)
                    if visit_input.timing
                    else None
                ),
                time_value=visit_input.timing.value if visit_input.timing else None,
                time_unit_uid=(
                    visit_input.timing.unit_uid if visit_input.timing else None
                ),
            )
            try:
                created_visit = study_visit_service.create(
                    study_uid=study_uid, study_visit_input=visit_payload
                )
            except MDRApiBaseException as exc:
                # Add the visit's reference_id so the caller can correlate the
                # failure with their payload, but preserve the original status
                # code (400 / 404 / etc.). Infrastructure errors from outside
                # this hierarchy propagate unchanged and surface as 500.
                exc.msg = (
                    f"Failed to create visit with reference ID "
                    f"'{visit_input.reference_id}': {exc.msg}"
                )
                exc.args = (exc.msg,)
                raise
            created_visits[visit_input.reference_id] = created_visit.uid

    def _create_epochs(
        self,
        study_uid: str,
        soa_input: models.SoACreateInput,
        study_epoch_service: StudyEpochService,
        created_epochs: dict[str, str],
    ):
        # Sort epochs by order to ensure correct creation sequence
        sorted_epochs = sorted(soa_input.epochs, key=lambda e: e.order)

        for epoch_input in sorted_epochs:
            log.info("Creating epoch for reference ID: %s", epoch_input.reference_id)
            epoch_payload = study_epoch.StudyEpochCreateInput(
                study_uid=study_uid,
                epoch_subtype=epoch_input.subtype,
            )
            try:
                created_epoch = study_epoch_service.create(
                    study_uid=study_uid, study_epoch_input=epoch_payload
                )
            except MDRApiBaseException as exc:
                # See _create_visits for the rationale: preserve status code,
                # add reference_id context, let infrastructure errors flow.
                exc.msg = (
                    f"Failed to create epoch with reference ID "
                    f"'{epoch_input.reference_id}': {exc.msg}"
                )
                exc.args = (exc.msg,)
                raise
            created_epochs[epoch_input.reference_id] = created_epoch.uid

    def _delete_existing_epochs_visits_activities(
        self,
        study_uid: str,
        study_epoch_service: StudyEpochService,
        study_visit_service: StudyVisitService,
        study_activity_service: StudyActivitySelectionService,
    ):
        # CR/LF injection in interpolated values is stripped globally by
        # the LogInjectionGuardFilter configured in common/logger.py.
        log.info(
            "Deleting existing activities, visits, and epochs for study UID: %s via service methods",
            self._sanitize_for_log(study_uid),
        )

        # Delete activities first (they depend on visits via activity schedules)
        existing_activities = study_activity_service.get_all_selection(
            study_uid=study_uid, page_size=0
        )
        for activity in existing_activities.items:
            study_activity_service.delete_selection(
                study_uid=study_uid,
                study_selection_uid=activity.study_activity_uid,
            )

        # Delete visits next (they depend on epochs)
        existing_visits = study_visit_service.get_all_visits(
            study_uid=study_uid,
            page_size=0,
            lite=True,
            sort_by={"uid": False},
        )
        for visit in existing_visits.items:
            study_visit_service.delete(study_uid=study_uid, study_visit_uid=visit.uid)

        # Delete epochs last
        existing_epochs = study_epoch_service.get_all_epochs(
            study_uid=study_uid, page_size=0
        )
        for epoch in existing_epochs.items:
            study_epoch_service.delete(study_uid=study_uid, study_epoch_uid=epoch.uid)

    def _validate_study(self, study_uid: str) -> None:
        study_service = StudyService()

        # Raises NotFoundException if the study does not exist.
        study_service.check_if_study_exists(study_uid)

        BusinessLogicException.raise_if(
            study_service.check_if_study_is_locked(study_uid),
            msg=(
                f"Study with UID '{study_uid}' is LOCKED. "
                "SoA creation is not allowed for locked studies."
            ),
        )

    def _validate_soa_input(self, soa_input: models.SoACreateInput):
        self._validate_epochs(soa_input.epochs)
        self._validate_visits(soa_input.visits)
        self._validate_activities(soa_input.activities)
        self._validate_epoch_references(soa_input)
        self._validate_visit_references(soa_input)

    def _validate_epochs(self, epochs: list[models.SoACreateInput.Epoch]):
        epoch_reference_ids = [epoch.reference_id for epoch in epochs]
        if len(epoch_reference_ids) != len(set(epoch_reference_ids)):
            raise ValidationException(msg="All epoch reference IDs must be unique.")

        epoch_orders = [epoch.order for epoch in epochs]
        if len(epoch_orders) != len(set(epoch_orders)):
            raise ValidationException(msg="All epoch orders must be unique.")

        valid_subtypes = self._get_valid_term_uids("EPOCHSTP")
        for epoch in epochs:
            self._validate_term_uid(
                term_uid=epoch.subtype,
                valid_terms=valid_subtypes,
                object_name="Epoch",
                field_name="subtype",
                reference_id=epoch.reference_id,
                lookup_hint=_TERM_LOOKUP_HINT.format(codelist="EPOCHSTP"),
            )

    @staticmethod
    def _effective_unique_number(visit: models.SoACreateInput.Visit) -> int:
        """Return the unique_visit_number to use for ``visit``.

        Callers may supply ``unique_number`` explicitly. When omitted, we
        derive it as ``number * 10`` to leave room (1, 2, … → 10, 20, …)
        for special / sub-visits inserted between scheduled ones.
        """
        return (
            visit.unique_number
            if visit.unique_number is not None
            else visit.number * 10
        )

    def _validate_visits(self, visits: list[models.SoACreateInput.Visit]):
        visit_reference_ids = [visit.reference_id for visit in visits]
        if len(visit_reference_ids) != len(set(visit_reference_ids)):
            raise ValidationException(msg="All visit reference IDs must be unique.")

        # `unique_visit_number` must be unique across all visits in the study.
        # When the caller omits `unique_number` we derive it as `number * 10`
        # (e.g. visit_number 1 → UVN 10) to leave room for inserted special
        # visits. Catch collisions here — both explicit and derived — so they
        # surface as a clean pre-validation error rather than a wrapped 400
        # from deep inside StudyVisitService.
        effective_uvns = [self._effective_unique_number(v) for v in visits]
        if len(effective_uvns) != len(set(effective_uvns)):
            raise ValidationException(
                msg=(
                    "All visits must have a unique unique_visit_number. "
                    "When `unique_number` is omitted it defaults to `number * 10`, "
                    "so visits with `number` values that collide on `* 10` "
                    "(e.g. 10 and 100) must supply `unique_number` explicitly."
                )
            )

        valid_types = self._get_valid_term_uids("TIMELB")
        valid_contact_modes = self._get_valid_term_uids("VISCNTMD")
        valid_time_references = self._get_valid_term_uids("TIMEREF")
        valid_time_units = self._get_valid_unit_uids("Study Time")

        for visit in visits:
            self._validate_term_uid(
                term_uid=visit.type,
                valid_terms=valid_types,
                object_name="Visit",
                field_name="type",
                reference_id=visit.reference_id,
                lookup_hint=_TERM_LOOKUP_HINT.format(codelist="TIMELB"),
            )
            self._validate_term_uid(
                term_uid=visit.contact_mode,
                valid_terms=valid_contact_modes,
                object_name="Visit",
                field_name="contact_mode",
                reference_id=visit.reference_id,
                lookup_hint=_TERM_LOOKUP_HINT.format(codelist="VISCNTMD"),
            )
            if visit.timing and visit.timing.timing_reference_uid:
                self._validate_term_uid(
                    term_uid=visit.timing.timing_reference_uid,
                    valid_terms=valid_time_references,
                    object_name="Visit",
                    field_name="timing.timing_reference_uid",
                    reference_id=visit.reference_id,
                    lookup_hint=_TERM_LOOKUP_HINT.format(codelist="TIMEREF"),
                )
            if visit.timing and visit.timing.unit_uid:
                self._validate_term_uid(
                    term_uid=visit.timing.unit_uid,
                    valid_terms=valid_time_units,
                    object_name="Visit",
                    field_name="timing.unit_uid",
                    reference_id=visit.reference_id,
                    lookup_hint=_TIME_UNIT_LOOKUP_HINT,
                )
            if visit.window and visit.window.unit_uid:
                self._validate_term_uid(
                    term_uid=visit.window.unit_uid,
                    valid_terms=valid_time_units,
                    object_name="Visit",
                    field_name="window.unit_uid",
                    reference_id=visit.reference_id,
                    lookup_hint=_TIME_UNIT_LOOKUP_HINT,
                )

    def _validate_epoch_references(self, soa_input: models.SoACreateInput):
        valid_epoch_refs = {epoch.reference_id for epoch in soa_input.epochs}
        for visit in soa_input.visits:
            if visit.epoch_reference_id not in valid_epoch_refs:
                raise ValidationException(
                    msg=f"Visit with reference ID '{visit.reference_id}' has an invalid epoch reference ID '{visit.epoch_reference_id}'."
                )

    def _validate_visit_references(self, soa_input: models.SoACreateInput):
        valid_visit_refs = {visit.reference_id for visit in soa_input.visits}
        for activity in soa_input.activities:
            for visit_ref_id in activity.visit_reference_ids:
                if visit_ref_id not in valid_visit_refs:
                    raise ValidationException(
                        msg=f"Activity with reference ID '{activity.reference_id}' has an invalid visit reference ID '{visit_ref_id}'."
                    )

    def _validate_activities(self, activities: list[models.SoACreateInput.Activity]):
        activity_reference_ids = [activity.reference_id for activity in activities]
        if len(activity_reference_ids) != len(set(activity_reference_ids)):
            raise ValidationException(msg="All activity reference IDs must be unique.")

        valid_soa_groups = self._get_valid_term_uids("FLWCRTGRP")
        # Maps activity_uid -> set of valid (activity_group_uid, activity_subgroup_uid) pairs
        activity_groupings_map = self._get_activity_groupings_map()
        for activity in activities:
            self._validate_term_uid(
                term_uid=activity.soa_group_uid,
                valid_terms=valid_soa_groups,
                object_name="Activity",
                field_name="soa_group_uid",
                reference_id=activity.reference_id,
                lookup_hint=_TERM_LOOKUP_HINT.format(codelist="FLWCRTGRP"),
            )
            valid_groupings = activity_groupings_map.get(activity.activity_uid)
            if valid_groupings is None:
                raise ValidationException(
                    msg=f"Activity with reference ID '{activity.reference_id}' has an invalid activity_uid '{activity.activity_uid}'. "
                    "Valid values are Final activities from GET /v1/library/activities."
                )
            if (
                activity.activity_group_uid,
                activity.activity_subgroup_uid,
            ) not in valid_groupings:
                raise ValidationException(
                    msg=f"Activity with reference ID '{activity.reference_id}' has an invalid combination of "
                    f"activity_group_uid '{activity.activity_group_uid}' and activity_subgroup_uid '{activity.activity_subgroup_uid}' "
                    f"for activity_uid '{activity.activity_uid}'. "
                    "Valid combinations are groupings from GET /v1/library/activities."
                )

    def _get_activity_groupings_map(self) -> dict[str, set[tuple[str, str]]]:
        """Returns a map of activity_uid -> set of valid (activity_group_uid, activity_subgroup_uid) pairs for all Final library activities."""
        activities = self._fetch_all_pages(
            lambda page_size, page_number: DB.get_library_activities(
                status=models.LibraryItemStatus.FINAL,
                library=models.Library.SPONSOR,
                page_size=page_size,
                page_number=page_number,
            )
        )
        groupings_map: dict[str, set[tuple[str, str]]] = {}
        for act in activities:
            activity_uid = act["uid"]
            groupings_map[activity_uid] = set()
            for grouping in act.get("groupings") or []:
                group_uid = (grouping.get("activity_group") or {}).get("uid")
                subgroup_uid = (grouping.get("activity_subgroup") or {}).get("uid")
                if group_uid and subgroup_uid:
                    groupings_map[activity_uid].add((group_uid, subgroup_uid))
        return groupings_map

    def _get_valid_term_uids(self, codelist_submission_value: str) -> set[str]:
        terms = self._fetch_all_pages(
            lambda page_size, page_number: DB.get_codelist_terms(
                codelist_submission_value, page_size=page_size, page_number=page_number
            )
        )
        return {term["term_uid"] for term in terms}

    def _get_valid_unit_uids(self, subset: str) -> set[str]:
        units = self._fetch_all_pages(
            lambda page_size, page_number: DB.get_unit_definitions(
                subset=subset, page_size=page_size, page_number=page_number
            )
        )
        return {unit["uid"] for unit in units}

    def _fetch_all_pages(
        self, fetcher: Callable[[int, int], list[Any]], page_size: int = 1000
    ) -> list[Any]:
        """Fetches all pages from a paginated data source.

        Args:
            fetcher: Callable that accepts (page_size, page_number) and returns a list of items.
            page_size: Number of items per page.
        """
        page_number = 1
        all_items: list[Any] = []
        while True:
            items = fetcher(page_size, page_number)
            all_items.extend(items)
            if len(items) < page_size:
                break
            page_number += 1
        return all_items

    def _validate_term_uid(
        self,
        term_uid: str,
        valid_terms: set[str],
        object_name: str,
        field_name: str,
        reference_id: str,
        lookup_hint: str | None = None,
    ):
        # We deliberately do NOT inline `valid_terms` into the message:
        # codelists can hold hundreds of UIDs, producing multi-KB responses
        # and leaking the full codelist contents on every validation error.
        # The route docstring tells callers which GET endpoint to query.
        if term_uid not in valid_terms:
            suffix = f" {lookup_hint}" if lookup_hint else ""
            raise ValidationException(
                msg=f"{object_name} with reference ID '{reference_id}' has an invalid {field_name} '{term_uid}'.{suffix}"
            )
