import datetime
from dataclasses import dataclass, field
from typing import Mapping

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_visit import (
    StudyVisitVO,
    VisitClass,
    VisitSubclass,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameWithConflictFlag,
)
from common.config import (
    BASIC_EPOCH_NAME,
    FIXED_WEEK_PERIOD,
    NON_VISIT_NUMBER,
    PREVIOUS_VISIT_NAME,
    STUDY_VISIT_TYPE_INFORMATION_VISIT,
    UNSCHEDULED_VISIT_NUMBER,
    VISIT_0_NUMBER,
)

StudyEpochType: dict[str, SimpleCTTermNameWithConflictFlag] = {}

StudyEpochSubType: dict[str, SimpleCTTermNameWithConflictFlag] = {}

StudyEpochEpoch: dict[str, SimpleCTTermNameWithConflictFlag] = {}


@dataclass
class StudyEpochVO:
    study_uid: str
    start_rule: str
    end_rule: str

    epoch: SimpleCTTermNameWithConflictFlag
    subtype: SimpleCTTermNameWithConflictFlag
    epoch_type: SimpleCTTermNameWithConflictFlag
    description: str

    order: int

    status: StudyStatus
    start_date: datetime.datetime
    author_id: str
    author_username: str

    duration: int | None = None
    duration_unit: str | None = None

    color_hash: str | None = None

    change_description: str = "Initial Version"
    name: str = "TBD"
    short_name: str = "TBD"

    accepted_version: bool = False
    number_of_assigned_visits: int | None = 0

    uid: str | None = None
    _is_deleted: bool = False
    _visits: list[StudyVisitVO] = field(default_factory=list)
    _previous_visit: StudyVisitVO | None = None
    _is_previous_visit_in_previous_epoch: bool | None = None
    _next_visit: StudyVisitVO | None = None
    _is_next_visit_in_next_epoch: bool | None = None

    def edit_core_properties(
        self,
        start_rule: str,
        end_rule: str,
        description: str,
        epoch: SimpleCTTermNameWithConflictFlag,
        subtype: SimpleCTTermNameWithConflictFlag,
        epoch_type: SimpleCTTermNameWithConflictFlag,
        order: int,
        change_description: str,
        color_hash: str | None,
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
            return self.get_start_day() + FIXED_WEEK_PERIOD
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
            return self.get_start_week() + 1
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
        self, visit: StudyVisitVO, is_next_visit_in_next_epoch: bool = True
    ):
        self._next_visit = visit
        self._is_next_visit_in_next_epoch = is_next_visit_in_next_epoch

    @property
    def previous_visit(self):
        return self._previous_visit

    def set_previous_visit(
        self, visit: StudyVisitVO, is_previous_visit_in_previous_epoch: bool = True
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


@dataclass
class TimelineAR:
    """
    TimelineAR is aggregate root implementing idea of time relations between objects.
    Generally timeline consists of visits ordered by their internal relations.
    If there is a need to create ordered setup of visits and epochs you have to
    collect_visits_to_epochs
    """

    study_uid: str
    _visits: list[StudyVisitVO]

    def _generate_timeline(self):
        """
        Function creating ordered list of visits based on _visits list
        """

        @dataclass
        class Subvisit:
            visit: StudyVisitVO
            number: int

        anchors = {}
        # There can be multiple Visits with same VisitType that can work as TimeRef
        # If Study contains multiple such Visits, the first occurence of the Visit with given VisitType
        # that works as TimeRef will be picked to be an anchor for the other visits
        for visit in self._visits:
            anchors.setdefault(visit.visit_type.sponsor_preferred_name, visit)

        subvisit_sets = {}
        amount_of_subvisits_for_visit = {}
        special_visit_anchors = {}
        for visit in self._visits:
            if visit.visit_subclass == VisitSubclass.ANCHOR_VISIT_IN_GROUP_OF_SUBV:
                if visit.uid:
                    subvisit_sets[visit.uid] = [Subvisit(visit, 0)]
            elif visit.visit_class == VisitClass.SPECIAL_VISIT:
                special_visit_anchors[visit.visit_sublabel_reference] = None
        for order, visit in enumerate(self._visits):
            if visit.timepoint:
                time_anchor = visit.timepoint.visit_timereference.sponsor_preferred_name
            else:
                time_anchor = None
            if time_anchor == PREVIOUS_VISIT_NAME:
                if len(self._visits) > 1:
                    visit.set_anchor_visit(self._visits[order - 1])
            elif time_anchor in anchors and visit.uid != anchors[time_anchor].uid:
                visit.set_anchor_visit(anchors[time_anchor])
            if visit.uid in special_visit_anchors:
                special_visit_anchors[visit.uid] = visit
            if (
                visit.visit_subclass
                == VisitSubclass.ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
            ):
                visits = subvisit_sets[visit.visit_sublabel_reference]
                visit.set_subvisit_anchor(visits[0].visit)
        ordered_visits = sorted(
            self._visits,
            key=lambda x: (
                x.get_absolute_duration() is None,
                x.get_absolute_duration(),
            ),
        )
        last_visit_num = 1
        order = 1
        for idx, visit in enumerate(ordered_visits):
            if (
                visit.visit_type.sponsor_preferred_name
                == STUDY_VISIT_TYPE_INFORMATION_VISIT
                and idx == 0
            ):
                visit.set_order_and_number(VISIT_0_NUMBER, VISIT_0_NUMBER)
                continue
            if visit.visit_class == VisitClass.NON_VISIT:
                visit.set_order_and_number(NON_VISIT_NUMBER, NON_VISIT_NUMBER)
            elif visit.visit_class == VisitClass.UNSCHEDULED_VISIT:
                visit.set_order_and_number(
                    UNSCHEDULED_VISIT_NUMBER, UNSCHEDULED_VISIT_NUMBER
                )
            elif visit.visit_class == VisitClass.MANUALLY_DEFINED_VISIT:
                visit.set_order_and_number(order, visit.visit_number)
            elif visit.visit_class == VisitClass.SPECIAL_VISIT:
                anchor_for_special_vis = special_visit_anchors[
                    visit.visit_sublabel_reference
                ]
                visit.set_subvisit_anchor(anchor_for_special_vis)
                visit.set_order_and_number(
                    visit.subvisit_anchor.visit_order,
                    visit.subvisit_anchor.visit_number,
                )
                visit.set_subvisit_number(1)
            elif (
                visit.visit_subclass
                != VisitSubclass.ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
            ):
                visit.set_order_and_number(order, last_visit_num)
            if (
                visit.visit_subclass
                == VisitSubclass.ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
            ):
                amount_of_subvisits_for_visit[visit.visit_sublabel_reference] = (
                    amount_of_subvisits_for_visit.get(visit.visit_sublabel_reference, 0)
                    + 1
                )
                visit.set_order_and_number(
                    order,
                    visit.subvisit_anchor.visit_number,
                )
            elif visit.visit_class not in [
                VisitClass.MANUALLY_DEFINED_VISIT,
                VisitClass.SPECIAL_VISIT,
            ]:
                last_visit_num += 1
            order += 1

        for order, visit in enumerate(ordered_visits):
            if (
                visit.visit_subclass
                == VisitSubclass.ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
            ):
                # we have to assign subvisit numbers after we assign anchor visit numbers because some of subvisits may
                # happen before the anchor visit in group of subvisits and that will influence numbering
                visits = subvisit_sets[visit.visit_sublabel_reference]
                amount_of_subvists = amount_of_subvisits_for_visit[
                    visit.visit_sublabel_reference
                ]
                if amount_of_subvists < 10:
                    increment_step = 10
                elif 10 <= amount_of_subvists < 20:
                    increment_step = 5
                else:
                    increment_step = 1
                num = visits[-1].number + increment_step
                # if additional visit is taking place before anchor visit in group of subvisits
                if (
                    visits[-1].visit.get_absolute_duration()
                    > visit.get_absolute_duration()
                ):
                    last_subvisit_number = visits[-1].number
                    # take subvisit number from the last visit
                    visit.set_subvisit_number(last_subvisit_number)
                    # insert subvisit before the last visit
                    visits.insert(-1, Subvisit(visit, last_subvisit_number))
                    # the last visit obtains the currently calculated number
                    visits[-1].number = num
                    visits[-1].visit.set_subvisit_number(num)
                else:
                    visit.set_subvisit_number(num)
                    visits.append(Subvisit(visit, num))

            # derive timing properties in the end when all subvisits are set
            # for the Visit that is currently being created timepoint will be filled but study_day will be empty as it's
            # being assigned afterwards
            if visit.timepoint and visit.study_day:
                visit.study_day.value = visit.derive_study_day_number()
                visit.study_duration_days.value = (
                    visit.derive_study_duration_days_number()
                )
                visit.study_week.value = visit.derive_study_week_number()
                visit.study_duration_weeks.value = (
                    visit.derive_study_duration_weeks_number()
                )
                visit.week_in_study.value = visit.derive_week_in_study_number()

        # sort visits that are returned in the end to capture all timing changes
        ordered_visits = sorted(
            self._visits,
            key=lambda x: (
                x.get_absolute_duration() is None,
                x.get_absolute_duration(),
            ),
        )

        return ordered_visits

    def collect_visits_to_epochs(
        self, epochs: list[StudyEpochVO]
    ) -> Mapping[str, list[StudyVisitVO]]:
        """
        Creates dictionary mapping of study epoch uids to StudyVisitsVO list. Allows to match visits with
        epochs. Additionally adds information for epoch what is first following visit.
        """
        epochs.sort(key=lambda epoch: epoch.order)

        epoch_visits: Mapping[str, list[StudyVisitVO]] = {}
        for epoch in epochs:
            epoch_visits[epoch.uid] = []

        # removing basic epoch from the epoch list to not derive timings for that epoch
        epochs = [
            epoch
            for epoch in epochs
            if epoch.subtype.sponsor_preferred_name != BASIC_EPOCH_NAME
        ]
        for visit in self.ordered_study_visits:
            if visit.epoch_uid in epoch_visits:
                epoch_visits[visit.epoch_uid].append(visit)
        for epoch in epochs:
            epoch.set_ordered_visits(epoch_visits[epoch.uid])
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
        new_visits = [v for v in self._visits if v.uid != visit.uid]
        new_visits.append(visit)
        self._visits = new_visits

    @property
    def ordered_study_visits(self):
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
