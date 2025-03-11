import datetime
from dataclasses import dataclass
from enum import Enum
from math import ceil, floor
from typing import Any, Callable, Self

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameWithConflictFlag,
)
from common import exceptions
from common.config import GLOBAL_ANCHOR_VISIT_NAME

VisitTypeNamedTuple = SimpleCTTermNameWithConflictFlag
StudyVisitType: dict[str, VisitTypeNamedTuple] = {}

VisitRepeatingFrequencyNamedTuple = SimpleCTTermNameWithConflictFlag
StudyVisitRepeatingFrequency: dict[str, VisitRepeatingFrequencyNamedTuple] = {}

VisitTimeReferenceNamedTuple = SimpleCTTermNameWithConflictFlag
StudyVisitTimeReference: dict[str, VisitTimeReferenceNamedTuple] = {}

VisitContactModeNamedTuple = SimpleCTTermNameWithConflictFlag
StudyVisitContactMode: dict[str, VisitContactModeNamedTuple] = {}

VisitEpochAllocationNamedTuple = SimpleCTTermNameWithConflictFlag
StudyVisitEpochAllocation: dict[str, VisitEpochAllocationNamedTuple] = {}


class VisitClass(Enum):
    SINGLE_VISIT = "Single visit"
    SPECIAL_VISIT = "Special visit"
    NON_VISIT = "Non visit"
    UNSCHEDULED_VISIT = "Unscheduled visit"
    MANUALLY_DEFINED_VISIT = "Manually defined visit"


class VisitSubclass(Enum):
    SINGLE_VISIT = "Single visit"
    ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV = (
        "Additional subvisit in a group of subvisits"
    )
    ANCHOR_VISIT_IN_GROUP_OF_SUBV = "Anchor visit in group of subvisits"
    REPEATING_VISIT = "Repeating visit"


@dataclass
class TimeUnit:
    name: str
    conversion_factor_to_master: float
    from_timedelta: Callable


@dataclass
class TimePoint:
    uid: str
    visit_timereference: SimpleCTTermNameWithConflictFlag
    time_unit_uid: str
    visit_value: int


@dataclass
class NumericValue:
    uid: str
    value: int


@dataclass
class TextValue:
    uid: str
    name: str


@dataclass
class SimpleStudyEpoch:
    uid: str
    study_uid: str
    epoch: SimpleCTTermNameWithConflictFlag
    order: int


@dataclass
class StudyVisitVO:
    consecutive_visit_group: str
    visit_window_min: int | None
    visit_window_max: int | None
    window_unit_uid: str | None

    description: str
    start_rule: str  # Free text
    end_rule: str  # Free text
    visit_contact_mode: (
        SimpleCTTermNameWithConflictFlag  # CT Codelist Visit Contact Mode
    )
    visit_type: SimpleCTTermNameWithConflictFlag  # CT Codelist VISIT_TYPE -

    status: StudyStatus
    start_date: datetime.datetime
    author_id: str
    author_username: str

    visit_class: VisitClass
    visit_subclass: VisitSubclass
    is_global_anchor_visit: bool
    visit_number: float
    visit_order: int
    show_visit: bool
    epoch_allocation: SimpleCTTermNameWithConflictFlag | None = None
    timepoint: TimePoint | None = None
    study_day: NumericValue | None = None
    study_duration_days: NumericValue | None = None
    study_week: NumericValue | None = None
    study_duration_weeks: NumericValue | None = None
    week_in_study: NumericValue | None = None

    visit_name_sc: TextValue | None = None

    subvisit_number: int | None = None
    subvisit_anchor: Self | None = None
    time_unit_object: TimeUnit | None = None
    window_unit_object: TimeUnit | None = None

    epoch_connector: Any = None
    anchor_visit = None
    is_deleted: bool = False
    is_soa_milestone: bool = False
    uid: str | None = None

    day_unit_object: TimeUnit | None = None
    week_unit_object: TimeUnit | None = None

    visit_sublabel_reference: str | None = (
        None  # reference (uid) of the first subvisit in subvisit stream
    )

    vis_unique_number: int | None = None
    vis_short_name: str | None = None

    repeating_frequency: SimpleCTTermNameWithConflictFlag | None = None

    study_id: str | None = None
    study_id_prefix: str | None = None
    study_number: str | None = None
    number_of_assigned_activities: int | None = None

    @property
    def visit_name(self):
        if self.visit_class != VisitClass.MANUALLY_DEFINED_VISIT:
            return self.derive_visit_name()
        return self.visit_name_sc.name

    def derive_visit_name(self):
        if self.visit_class != VisitClass.MANUALLY_DEFINED_VISIT:
            if self.visit_subclass == VisitSubclass.REPEATING_VISIT:
                return f"Visit {int(self.visit_number)}.n"
            return f"Visit {int(self.visit_number)}"
        return self.visit_name_sc.name

    @property
    def visit_short_name(self):
        if self.visit_class != VisitClass.MANUALLY_DEFINED_VISIT:
            visit_number = int(self.visit_number)
            if (
                "on site visit"
                in self.visit_contact_mode.sponsor_preferred_name.lower()
            ):
                visit_prefix = "V"
            elif (
                "phone contact"
                in self.visit_contact_mode.sponsor_preferred_name.lower()
            ):
                visit_prefix = "P"
            elif (
                "virtual visit"
                in self.visit_contact_mode.sponsor_preferred_name.lower()
            ):
                visit_prefix = "O"
            else:
                raise exceptions.ValidationException(
                    msg="Unrecognized visit contact mode passed."
                )
            visit_short_name = f"{visit_prefix}{visit_number}"

            if self.visit_subclass == VisitSubclass.REPEATING_VISIT:
                return visit_short_name + ".n"

            if (
                self.visit_subclass
                == VisitSubclass.ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
            ):
                return (
                    visit_short_name
                    + f"D{self.derive_study_day_number(relative_duration=True)}"
                )
            if self.visit_subclass == VisitSubclass.ANCHOR_VISIT_IN_GROUP_OF_SUBV:
                return visit_short_name + "D1"
            if self.visit_class == VisitClass.SPECIAL_VISIT:
                return visit_short_name + "A"
            if self.visit_class in (VisitClass.NON_VISIT, VisitClass.UNSCHEDULED_VISIT):
                return visit_number
            return visit_short_name
        return self.vis_short_name

    @property
    def epoch_uid(self):
        return self.epoch_connector.uid

    @property
    def study_uid(self):
        return self.epoch_connector.study_uid

    def set_anchor_visit(self, visit):
        self.anchor_visit = visit

    def set_order_and_number(self, order: int, number: int):
        self.visit_order = order
        self.visit_number = number

    def set_subvisit_anchor(self, subvisit_anchor):
        self.subvisit_anchor = subvisit_anchor

    def set_subvisit_number(self, number):
        self.subvisit_number = number

    @property
    def unique_visit_number(self):
        if self.visit_class != VisitClass.MANUALLY_DEFINED_VISIT:
            visit_number = int(self.visit_number)
            if self.subvisit_number is not None:
                return int(f"{visit_number}{self.subvisit_number:02d}")
            if (
                self.visit_subclass
                and self.visit_subclass == VisitSubclass.ANCHOR_VISIT_IN_GROUP_OF_SUBV
            ):
                return int(f"{visit_number}{0:02d}")
            if self.visit_class in (VisitClass.NON_VISIT, VisitClass.UNSCHEDULED_VISIT):
                return visit_number
            return visit_number * 100
        return self.vis_unique_number

    @property
    def epoch(self):
        return self.epoch_connector

    @property
    def order(self):
        return self.epoch_connector.get_order(self)

    def get_unified_duration(self):
        return self.time_unit_object.from_timedelta(
            self.time_unit_object, self.timepoint.visit_value
        )

    @property
    def study_day_number(self):
        if self.study_day:
            return self.study_day.value
        if self.visit_class == VisitClass.SPECIAL_VISIT and self.subvisit_anchor:
            return self.subvisit_anchor.study_day_number
        return None

    @property
    def study_week_number(self):
        if self.study_week:
            return self.study_week.value
        if self.visit_class == VisitClass.SPECIAL_VISIT and self.subvisit_anchor:
            return self.subvisit_anchor.study_week_number
        return None

    def derive_study_day_number(self, relative_duration=False) -> int | None:
        if not relative_duration:
            duration = self.get_absolute_duration()
        else:
            duration = self.get_unified_duration()
        if self.day_unit_object and duration is not None:
            days = int(duration / self.day_unit_object.conversion_factor_to_master)
            if days < 0:
                return days
            return days + 1
        return None

    def derive_study_duration_days_number(self) -> int | None:
        derived_study_day_number = self.derive_study_day_number()
        if derived_study_day_number:
            if derived_study_day_number > 0:
                return derived_study_day_number - 1
            return derived_study_day_number
        return None

    def derive_week_value(self) -> float | None:
        duration = self.get_absolute_duration()
        if self.week_unit_object and duration is not None:
            weeks = duration / self.week_unit_object.conversion_factor_to_master
            return weeks
        return None

    def derive_study_week_number(self) -> int | None:
        week_value = self.derive_week_value()
        if week_value is not None:
            if week_value < 0:
                return floor(week_value)
            return floor(week_value) + 1
        return None

    def derive_study_duration_weeks_number(self) -> int | None:
        week_value = self.derive_week_value()
        if week_value is not None:
            if week_value < 0:
                return ceil(week_value)
            return floor(week_value)
        return None

    def derive_week_in_study_number(self) -> int | None:
        return self.derive_study_duration_weeks_number()

    @property
    def study_week_label(self):
        return f"Week {self.study_week.value}"

    @property
    def study_duration_weeks_label(self):
        return f"{self.study_duration_weeks.value} weeks"

    @property
    def week_in_study_label(self):
        return f"Week {self.week_in_study.value}"

    @property
    def study_day_label(self):
        return f"Day {self.study_day.value}"

    @property
    def study_duration_days_label(self):
        return f"{self.study_duration_days.value} days"

    @property
    def visit_subnumber(self):
        return (
            self.subvisit_number
            if (self.subvisit_number is not None and self.subvisit_number != "")
            else 0
        )

    @property
    def visit_subname(self):
        return f"{self.visit_name}"

    @property
    def possible_actions(self):
        if self.status == StudyStatus.DRAFT:
            return ["edit", "delete", "lock"]
        return None

    def get_absolute_duration(self) -> int | None:
        # Special visit doesn't have a timing but we want to place it
        # after the anchor visit for the special visit hence we derive timing based on the anchor visit
        if self.visit_class == VisitClass.SPECIAL_VISIT and self.subvisit_anchor:
            return self.subvisit_anchor.get_absolute_duration()
        if self.timepoint:
            if self.timepoint.visit_value == 0:
                return 0
            if self.anchor_visit is not None:
                if (
                    self.timepoint.visit_timereference.sponsor_preferred_name.lower()
                    == GLOBAL_ANCHOR_VISIT_NAME.lower()
                ):
                    return self.get_unified_duration()
                return (
                    self.get_unified_duration()
                    + self.anchor_visit.get_absolute_duration()
                )
            if self.subvisit_anchor is not None:
                return (
                    self.get_unified_duration()
                    + self.subvisit_anchor.get_absolute_duration()
                )
            if self.anchor_visit is None:
                return self.get_unified_duration()
            return None
        return None

    def get_unified_window(self):
        _dur = int(
            self.get_absolute_duration()
            / self.time_unit_object.conversion_factor_to_master
        )
        _dur += 1  # value for baseline visit.
        _min = int(
            self.window_unit_object.from_timedelta(
                self.window_unit_object, self.visit_window_min
            )
            / self.window_unit_object.conversion_factor_to_master
        )
        _min = _dur + _min

        _max = int(
            self.window_unit_object.from_timedelta(
                self.window_unit_object, self.visit_window_max
            )
            / self.window_unit_object.conversion_factor_to_master
        )
        _max = _dur + _max
        return (int(_min), int(_max))

    def delete(self):
        self.is_deleted = True

    def compare_cons_group_equality(
        self,
        other_visit: "StudyVisitVO",
    ) -> bool:
        return (
            self.visit_type == other_visit.visit_type
            and self.epoch_uid == other_visit.epoch_uid
            and self.visit_contact_mode == other_visit.visit_contact_mode
            and self.timepoint.visit_timereference
            == other_visit.timepoint.visit_timereference
            and self.visit_window_min == other_visit.visit_window_min
            and self.visit_window_max == other_visit.visit_window_max
        )


@dataclass
class StudyVisitHistoryVO(StudyVisitVO):
    change_type: str | None = None
    end_date: datetime.datetime | None = None
