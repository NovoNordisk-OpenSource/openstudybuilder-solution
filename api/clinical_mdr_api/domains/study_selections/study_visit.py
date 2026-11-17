import datetime
from dataclasses import dataclass
from enum import Enum
from math import ceil, floor
from typing import Any, Self

import neo4j.time

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameWithConflictFlag,
)
from common import exceptions
from common.config import settings
from common.utils import TimeUnit, VisitClass, VisitSubclass

MAX_EARLY_DISCONTINUATION_VISITS = 3


class VisitGroupFormat(Enum):
    RANGE = "range"
    LIST = "list"


@dataclass
class VisitGroup:
    uid: str
    group_name: str
    group_format: str


@dataclass
class TimePoint:
    uid: str
    visit_timereference: SimpleCTTermNameWithConflictFlag | None
    time_unit_uid: str
    visit_value: int | None


@dataclass
class NumericValue:
    uid: str
    value: int | float | None


@dataclass
class TextValue:
    uid: str
    name: str


@dataclass
class SimpleStudyEpoch:
    uid: str
    study_uid: str
    epoch: SimpleCTTermNameWithConflictFlag | None
    order: int


@dataclass
class StudyVisitVO:
    visit_window_min: int | None
    visit_window_max: int | None
    window_unit_uid: str | None

    description: str | None
    start_rule: str | None
    end_rule: str | None
    visit_contact_mode: (
        SimpleCTTermNameWithConflictFlag | None  # CT Codelist Visit Contact Mode
    )
    visit_type: SimpleCTTermNameWithConflictFlag | None  # CT Codelist VISIT_TYPE -

    status: StudyStatus
    start_date: datetime.datetime
    author_id: str
    author_username: str

    visit_class: VisitClass | None
    visit_subclass: VisitSubclass | None
    is_global_anchor_visit: bool
    visit_number: float
    visit_order: int
    show_visit: bool
    study_visit_group: VisitGroup | None = None
    epoch_allocation: SimpleCTTermNameWithConflictFlag | None = None
    timepoint: TimePoint | None = None
    study_day: NumericValue | None = None
    study_duration_days: NumericValue | None = None
    study_week: NumericValue | None = None
    study_duration_weeks: NumericValue | None = None
    week_in_study: NumericValue | None = None

    visit_name_sc: TextValue | None = None

    subvisit_number: int | None = None
    visit_suffix: str | None = None
    time_unit_object: TimeUnit | None = None
    window_unit_object: TimeUnit | None = None

    epoch_connector: Any = None
    _study_uid: str | None = None
    anchor_visit: Self | None = None
    is_deleted: bool = False
    is_soa_milestone: bool = False
    uid: str | None = None

    day_unit_object: TimeUnit | None = None
    week_unit_object: TimeUnit | None = None

    # reference (uid) of the first subvisit in subvisit stream,
    # or of the parent visit for an Early Discontinuation visit
    visit_sublabel_reference: str | None = None

    vis_unique_number: int | None = None
    vis_short_name: str | None = None
    # visit_order as persisted, while visit_order itself is overwritten by the timeline position
    stored_visit_order: int | None = None

    expected_time_value: int | None = None

    repeating_frequency: SimpleCTTermNameWithConflictFlag | None = None

    study_id: str | None = None
    study_id_prefix: str | None = None
    study_number: str | None = None

    @property
    def visit_name(self):
        if self.visit_class != VisitClass.MANUALLY_DEFINED_VISIT:
            return self.derive_visit_name()
        return self.visit_name_sc.name

    def derive_visit_name(self):
        if self.visit_class != VisitClass.MANUALLY_DEFINED_VISIT:
            if self.visit_class == VisitClass.NON_VISIT:
                return f"Visit {settings.non_visit_number}"
            if self.visit_class == VisitClass.UNSCHEDULED_VISIT:
                return f"Visit {settings.unscheduled_visit_number}"
            if self.visit_subclass == VisitSubclass.REPEATING_VISIT:
                return f"Visit {int(self.visit_number)}{self.visit_suffix or ''}.n"
            base = f"Visit {int(self.visit_number)}"
            # Visits in a group of subvisits share the name of the group, the suffix only goes into the short name
            if self.visit_class == VisitClass.SINGLE_VISIT and not self.is_in_group:
                return base + (self.visit_suffix or "")
            return base
        return self.visit_name_sc.name

    @property
    def is_in_group(self) -> bool:
        return self.visit_subclass in (
            VisitSubclass.ANCHOR_VISIT_IN_GROUP_OF_SUBV,
            VisitSubclass.ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV,
        )

    @property
    def default_visit_suffix(self) -> str | None:
        """
        Suffix a visit gets when none is given: D1 for the anchor visit in a group of subvisits
        and D<day relative to the anchor> for the additional subvisits.
        """
        if self.visit_class != VisitClass.SINGLE_VISIT:
            return None
        if self.visit_subclass == VisitSubclass.ANCHOR_VISIT_IN_GROUP_OF_SUBV:
            return "D1"
        if self.visit_subclass == VisitSubclass.ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV:
            relative_day = self.derive_study_day_number(relative_duration=True)
            return f"D{relative_day}" if relative_day is not None else None
        return None

    @property
    def effective_visit_suffix(self) -> str | None:
        """
        Suffix used in the short name. Visits in a group of subvisits that have no visit_suffix stored
        (created before their D<day> part became the visit_suffix) use the default one.
        """
        return self.visit_suffix or self.default_visit_suffix

    def _visit_contact_mode_prefix(self) -> str:
        mode = self.visit_contact_mode.sponsor_preferred_name.lower()
        if "on site visit" in mode:
            return "V"
        if "phone contact" in mode:
            return "P"
        if "virtual visit" in mode:
            return "O"
        raise exceptions.BusinessLogicException(
            msg="Unrecognized visit contact mode passed."
        )

    @property
    def visit_short_name(self):
        if self.visit_class == VisitClass.MANUALLY_DEFINED_VISIT:
            return self.vis_short_name
        visit_number = int(self.visit_number)
        prefix = self._visit_contact_mode_prefix()
        short = f"{prefix}{visit_number}"
        if self.visit_subclass == VisitSubclass.REPEATING_VISIT:
            return short + (self.visit_suffix or "") + ".n"
        if self.visit_class in (VisitClass.UNSCHEDULED_VISIT, VisitClass.NON_VISIT):
            return f"V{visit_number}"
        if self.visit_class == VisitClass.SINGLE_VISIT:
            return short + (self.effective_visit_suffix or "")
        return short

    @property
    def epoch_uid(self):
        return self.epoch_connector.uid if self.epoch_connector else None

    @property
    def study_uid(self):
        if self.epoch_connector:
            return self.epoch_connector.study_uid
        return self._study_uid

    @property
    def is_early_discontinuation_visit(self) -> bool:
        return (
            self.visit_type is not None
            and self.visit_type_name
            == settings.study_visit_type_early_discontinuation_visit
        )

    @property
    def has_technical_visit_class(self) -> bool:
        return self.visit_class in (VisitClass.NON_VISIT, VisitClass.UNSCHEDULED_VISIT)

    # The Unscheduled and Non-visit visit type rules (masked timing, fixed visit window, ordering by
    # expected timing) apply to regular visits only. Visits of the Unscheduled or Non-visit visit class
    # carry no timing at all and follow the rules of their class, whatever their visit type.
    @property
    def is_unscheduled_visit_type(self) -> bool:
        return (
            not self.has_technical_visit_class
            and self.visit_type is not None
            and self.visit_type_name == settings.unscheduled_visit_name
        )

    @property
    def is_non_visit_type(self) -> bool:
        return (
            not self.has_technical_visit_class
            and self.visit_type is not None
            and self.visit_type_name == settings.non_visit_name
        )

    @property
    def api_time_value(self) -> int | None:
        if (
            self.is_early_discontinuation_visit
            or self.is_unscheduled_visit_type
            or self.is_non_visit_type
        ):
            return 0
        return getattr(self.timepoint, "visit_value", None)

    @property
    def api_time_reference(self):
        return getattr(self.timepoint, "visit_timereference", None)

    @property
    def api_time_unit_uid(self) -> str | None:
        return getattr(self.timepoint, "time_unit_uid", None)

    def api_visit_window_min(self, manual_visit_mode: bool = False) -> int | None:
        if (
            not manual_visit_mode
            and self.visit_class != VisitClass.MANUALLY_DEFINED_VISIT
            and (
                self.is_early_discontinuation_visit
                or self.is_unscheduled_visit_type
                or self.is_non_visit_type
            )
        ):
            return -9999
        return self.visit_window_min

    def api_visit_window_max(self, manual_visit_mode: bool = False) -> int | None:
        if (
            not manual_visit_mode
            and self.visit_class != VisitClass.MANUALLY_DEFINED_VISIT
            and (
                self.is_early_discontinuation_visit
                or self.is_unscheduled_visit_type
                or self.is_non_visit_type
            )
        ):
            return 9999
        return self.visit_window_max

    @property
    def visit_type_name(self) -> str:
        return self.visit_type.sponsor_preferred_name

    @property
    def time_reference_name(self) -> str | None:
        if self.timepoint:
            return self.timepoint.visit_timereference.sponsor_preferred_name
        return None

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
        if self.epoch_connector:
            return self.epoch_connector.get_order(self)
        return 0

    def get_unified_duration(self):
        return self.time_unit_object.from_timedelta(
            self.time_unit_object, self.timepoint.visit_value
        )

    @property
    def study_day_number(self):
        if self.study_day:
            return self.study_day.value
        return None

    @property
    def study_week_number(self):
        if self.study_week:
            return self.study_week.value
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
            return duration / self.week_unit_object.conversion_factor_to_master
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
        study_week = self.study_week.value if self.study_week else 0
        return f"Week {study_week}"

    @property
    def study_duration_weeks_label(self):
        study_duration_weeks = (
            self.study_duration_weeks.value if self.study_duration_weeks else 0
        )
        return f"{study_duration_weeks} weeks"

    @property
    def week_in_study_label(self):
        week_in_study = self.week_in_study.value if self.week_in_study else 0
        return f"Week {week_in_study}"

    @property
    def study_day_label(self):
        study_day = self.study_day.value if self.study_day else 0
        return f"Day {study_day}"

    @property
    def study_duration_days_label(self):
        study_duration_days = (
            self.study_duration_days.value if self.study_duration_days else 0
        )
        return f"{study_duration_days} days"

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

    def get_absolute_duration(self, _seen: set[str | None] | None = None) -> int | None:
        if _seen is None:
            _seen = set()
        if self.uid in _seen:
            raise exceptions.BusinessLogicException(
                msg=f"Circular anchor visit reference detected at visit '{self.uid}' while resolving absolute duration."
            )
        _seen.add(self.uid)
        # Early Discontinuation visits take place at the timing of the parent visit they reference
        if self.is_early_discontinuation_visit and self.anchor_visit is not None:
            return self.anchor_visit.get_absolute_duration(_seen=_seen)
        # Visits with expected_time_value set (converted special visits, unscheduled)
        # are ordered solely by that value — never by the timepoint, which is 0 for all
        # of them and would incorrectly place them all at day 0.
        # expected_time_value is stored in the same unit as the visit's timepoint.
        if self.expected_time_value is not None and self.time_unit_object is not None:
            return self.time_unit_object.from_timedelta(
                self.time_unit_object, self.expected_time_value
            )
        if self.timepoint:
            if self.timepoint.visit_value == 0:
                return 0
            if self.anchor_visit is not None:
                return (
                    self.get_unified_duration()
                    + self.anchor_visit.get_absolute_duration(_seen=_seen)
                )
            return self.get_unified_duration()
        return None

    def get_unified_window(self):
        absolute_duration: int | None = self.get_absolute_duration()
        if absolute_duration is None:
            raise exceptions.BusinessLogicException(
                msg="Visit has no absolute duration, cannot derive visit window."
            )

        _dur = int(
            absolute_duration / self.time_unit_object.conversion_factor_to_master
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
        other_visit: StudyVisitVO,
    ) -> list[str]:
        different_fields: list[str] = []
        if self.visit_type != other_visit.visit_type:
            different_fields.append("visit_type")
        if self.epoch_uid != other_visit.epoch_uid:
            different_fields.append("epoch")
        if self.visit_contact_mode != other_visit.visit_contact_mode:
            different_fields.append("visit_contact_mode")
        if self.visit_window_min != other_visit.visit_window_min:
            different_fields.append("min_visit_window_value")
        if self.visit_window_max != other_visit.visit_window_max:
            different_fields.append("max_visit_window_value")
        return different_fields


@dataclass
class StudyVisitHistoryVO(StudyVisitVO):
    change_type: str | None = None
    end_date: neo4j.time.DateTime | None = None
