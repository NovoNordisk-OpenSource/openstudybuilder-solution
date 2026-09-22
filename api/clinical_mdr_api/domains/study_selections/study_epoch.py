import datetime
from dataclasses import dataclass, field
from typing import Mapping, MutableMapping

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_visit import StudyVisitVO
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameWithConflictFlag,
)
from common.config import settings
from common.telemetry import trace_calls
from common.utils import BaseTimelineAR

# Legacy-only, from the MMA migration. Closed set, will not grow.
# Each entry is a field-name prefix on StudyEpochVO: "ae" -> ae_lag_time,
# ae_lag_time_unit_uid, ae_lag_time_unit_name, has_ae_lag_time_unit.
LAG_TIME_EVENT_TYPES = ("ae", "hypo", "ce")

# MMA recorded lag times as days and weeks. The Study Time unit subset the uids
# are picked from also holds the singular day and week, plus year and years,
# which stay valid for study visits but are not a lag time. Mirrored in
# frontend/src/constants/units.js — the two stacks share no code, and a constant
# this static is not worth an endpoint. Closed set, will not grow.
LAG_TIME_UNIT_NAMES = ("days", "weeks")


@dataclass
class StudyEpochVO:
    study_uid: str
    start_rule: str | None
    end_rule: str | None

    epoch: SimpleCTTermNameWithConflictFlag | None
    subtype: SimpleCTTermNameWithConflictFlag | None
    epoch_type: SimpleCTTermNameWithConflictFlag | None
    description: str | None

    order: int

    status: StudyStatus
    start_date: datetime.datetime
    author_id: str
    author_username: str

    duration: int | None = None
    duration_unit: str | None = None

    color_hash: str | None = None

    ae_lag_time: int | None = None
    ae_lag_time_unit_uid: str | None = None
    ae_lag_time_unit_name: str | None = None
    hypo_lag_time: int | None = None
    hypo_lag_time_unit_uid: str | None = None
    hypo_lag_time_unit_name: str | None = None
    ce_lag_time: int | None = None
    ce_lag_time_unit_uid: str | None = None
    ce_lag_time_unit_name: str | None = None

    change_description: str = "Initial Version"
    name: str = "TBD"
    short_name: str = "TBD"

    accepted_version: bool = False
    number_of_assigned_visits: int = 0

    uid: str | None = None
    _is_deleted: bool = False
    _visits: list[StudyVisitVO] = field(default_factory=list)
    _previous_visit: StudyVisitVO | None = None
    _is_previous_visit_in_previous_epoch: bool | None = None
    _next_visit: StudyVisitVO | None = None
    _is_next_visit_in_next_epoch: bool | None = None

    def edit_core_properties(
        self,
        start_rule: str | None,
        end_rule: str | None,
        description: str | None,
        epoch: SimpleCTTermNameWithConflictFlag | None,
        subtype: SimpleCTTermNameWithConflictFlag | None,
        epoch_type: SimpleCTTermNameWithConflictFlag | None,
        order: int,
        change_description: str,
        color_hash: str | None,
        ae_lag_time: int | None = None,
        ae_lag_time_unit_uid: str | None = None,
        hypo_lag_time: int | None = None,
        hypo_lag_time_unit_uid: str | None = None,
        ce_lag_time: int | None = None,
        ce_lag_time_unit_uid: str | None = None,
    ):
        self.start_rule = start_rule
        self.end_rule = end_rule
        self.description = description
        self.epoch = epoch
        self.subtype = subtype
        self.epoch_type = epoch_type
        self.order = order
        self.change_description = change_description
        self.color_hash = color_hash
        self.ae_lag_time = ae_lag_time
        self.ae_lag_time_unit_uid = ae_lag_time_unit_uid
        self.hypo_lag_time = hypo_lag_time
        self.hypo_lag_time_unit_uid = hypo_lag_time_unit_uid
        self.ce_lag_time = ce_lag_time
        self.ce_lag_time_unit_uid = ce_lag_time_unit_uid

    def set_order(self, order):
        self.order = order

    def get_start_day(self):
        if len(self._visits) == 0:
            # if epoch is not the last one and not the first one, then we return the study day of the visit
            # from the previous epoch as start day to display empty epochs as well
            if self.next_visit and self.previous_visit:
                return self.previous_visit.study_day_number
            return None
        return self.first_visit.study_day_number

    def get_start_week(self):
        if len(self._visits) == 0:
            # if epoch is not the last one and not the first one, then we return the study week of the visit
            # from the previous epoch as start week to display empty epochs as well
            if self.next_visit and self.previous_visit:
                return self.previous_visit.study_week_number
            return None
        return self.first_visit.study_week_number

    def get_end_day(self):
        if len(self._visits) == 0:
            # if epoch is not the last one, then we return the study day of the next visit
            # int the next epoch as we want to display empty epochs as well
            if self.next_visit:
                return self.next_visit.study_day_number
            return None

        if self.next_visit:
            # if next visit exists in next epoch (it's not empty epoch) then return it study day
            if self._is_next_visit_in_next_epoch:
                return self.next_visit.study_day_number
            # next epoch is empty return study day of last visit in current epoch as end day
            return self.last_visit.study_day_number
        # if next visit doesn't exist it means that this is the last epoch
        # if there is one visit in last epoch we want to add a fixed 7 day period to the epoch duration
        # to display it in the visit overview
        if len(self._visits) == 1:
            return (
                self.get_start_day() if self.get_start_day() is not None else 0
            ) + settings.fixed_week_period
        return self.last_visit.study_day_number

    def get_end_week(self):
        if len(self._visits) == 0:
            # if epoch is not the last one, then we return the study week of the next visit
            # int the next epoch as we want to display empty epochs as well
            if self.next_visit:
                return self.next_visit.study_week_number
            return None

        if self.next_visit:
            # if next visit exists in next epoch (it's not empty epoch) then return it study week
            if self._is_next_visit_in_next_epoch:
                return self.next_visit.study_week_number
            # next epoch is empty return study week of last visit in current epoch as end week
            return self.last_visit.study_week_number
        # if next visit doesn't exist it means that this is the last epoch
        # if there is one visit in last epoch we want to add a fixed 7 day period to the epoch duration
        # to display it in the visit overview
        if len(self._visits) == 1:
            return (
                self.get_start_week() if self.get_start_week() is not None else 0
            ) + 1
        return self.last_visit.study_week_number

    @property
    def calculated_duration(self):
        start_day = self.get_start_day()
        end_day = self.get_end_day()
        if start_day and end_day:
            return end_day - start_day
        return 0

    def set_ordered_visits(self, visits: list[StudyVisitVO]):
        self._visits = visits

    @property
    def first_visit(self):
        if len(self._visits) > 0:
            return self._visits[0]
        return None

    @property
    def last_visit(self):
        if len(self._visits) > 0:
            return self._visits[-1]
        return None

    @property
    def next_visit(self):
        return self._next_visit

    def set_next_visit(
        self, visit: StudyVisitVO | None, is_next_visit_in_next_epoch: bool = True
    ):
        self._next_visit = visit
        self._is_next_visit_in_next_epoch = is_next_visit_in_next_epoch

    @property
    def previous_visit(self):
        return self._previous_visit

    def set_previous_visit(
        self,
        visit: StudyVisitVO | None,
        is_previous_visit_in_previous_epoch: bool = True,
    ):
        self._previous_visit = visit
        self._is_previous_visit_in_previous_epoch = is_previous_visit_in_previous_epoch

    @property
    def possible_actions(self):
        if self.status == StudyStatus.DRAFT:
            if len(self._visits) == 0:
                return ["edit", "delete", "lock", "reorder"]
            return ["edit", "delete", "lock"]
        return None

    def visits(self) -> list[StudyVisitVO]:
        return self._visits

    def delete(self):
        self._is_deleted = True

    @property
    def is_deleted(self):
        return self._is_deleted


class TimelineAR(BaseTimelineAR):
    """
    TimelineAR is aggregate root implementing idea of time relations between objects.
    Generally timeline consists of visits ordered by their internal relations.
    If there is a need to create ordered setup of visits and epochs you have to
    collect_visits_to_epochs
    """

    @trace_calls
    def collect_visits_to_epochs(
        self, epochs: list[StudyEpochVO]
    ) -> Mapping[str, list[StudyVisitVO]]:
        """
        Creates dictionary mapping of study epoch uids to StudyVisitsVO list. Allows to match visits with
        epochs. Additionally adds information for epoch what is first following visit.
        """
        epochs.sort(key=lambda epoch: epoch.order)

        epoch_visits: MutableMapping[str, list[StudyVisitVO]] = {}
        for epoch in epochs:
            epoch_visits[epoch.uid] = []  # type: ignore[index]

        # removing basic epoch from the epoch list to not derive timings for that epoch
        epochs = [
            epoch
            for epoch in epochs
            if epoch.subtype.sponsor_preferred_name != settings.basic_epoch_name
        ]
        for visit in self.ordered_study_visits:
            if visit.epoch_uid in epoch_visits:
                epoch_visits[visit.epoch_uid].append(visit)
        for epoch in epochs:
            epoch.set_ordered_visits(epoch_visits[epoch.uid])  # type: ignore[index]
        # iterating to the one before last as we are accessing the next element in the for loop
        for i, epoch in enumerate(epochs[:-1]):
            # if next epoch has a visit then we set it as the next visit for the current epoch
            if epochs[i + 1].first_visit:
                epoch.set_next_visit(epochs[i + 1].first_visit)
            # if the next epoch doesn't have a visit inside we have to find a next visit from other
            # visits than the next
            else:
                next_epoch_with_visits = self._get_next_epoch_with_visits(
                    epochs=epochs[i + 1 :]
                )
                if next_epoch_with_visits:
                    epoch.set_next_visit(
                        next_epoch_with_visits.first_visit,
                        is_next_visit_in_next_epoch=False,
                    )
                else:
                    epoch.set_next_visit(None)

        for i, epoch in enumerate(epochs):
            if i - 1 >= 0:
                # if previous epoch has a visit then we set it as a previous visit for the current epoch
                if epochs[i - 1].last_visit:
                    epoch.set_previous_visit(epochs[i - 1].last_visit)
                # if previous epoch doesn't have a visit we have to find a previous visit
                # from the epochs before the previous epoch
                else:
                    previous_epoch_with_visits = self._get_previous_epoch_with_visits(
                        epochs=epochs[: i - 1]
                    )
                    if previous_epoch_with_visits:
                        epoch.set_previous_visit(
                            previous_epoch_with_visits.last_visit,
                            is_previous_visit_in_previous_epoch=False,
                        )
                    else:
                        epoch.set_previous_visit(None)
        return epoch_visits

    def _get_next_epoch_with_visits(self, epochs):
        for epoch in epochs:
            if len(epoch.visits()) > 0:
                return epoch
        return None

    def _get_previous_epoch_with_visits(self, epochs):
        for epoch in reversed(epochs):
            if len(epoch.visits()) > 0:
                return epoch
        return None

    def add_visit(self, visit: StudyVisitVO):
        """
        Add visits to a list of visits - used for preparation of adding new visit - creates order for added visit
        """
        visits = self._visits
        visits.append(visit)
        self._visits = visits
        self._visits = self.ordered_study_visits

    def remove_visit(self, visit: StudyVisitVO):
        visits = [v for v in self._visits if v != visit]
        self._visits = visits

    def update_visit(self, visit: StudyVisitVO):
        """
        Updates visits to a list of visits - used for preparation of adding new visit
        """
        new_visits = [v if v.uid != visit.uid else visit for v in self._visits]
        self._visits = new_visits

    @property
    def ordered_study_visits(self) -> list[StudyVisitVO]:
        """
        Accessor for generated order
        """
        visits = self._generate_timeline()
        return visits


@dataclass
class StudyEpochHistoryVO(StudyEpochVO):
    study_visit_count: int = 0
    change_type: str | None = None
    end_date: datetime.datetime | None = None
