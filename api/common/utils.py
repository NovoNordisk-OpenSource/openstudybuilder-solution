import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import GenericAlias, NoneType, UnionType
from typing import Any, Callable, Generic, TypeVar, get_args, get_origin, overload

import neo4j.time
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from common.config import settings
from common.exceptions import ValidationException
from common.telemetry import trace_calls

log = logging.getLogger(__name__)


class VisitClass(Enum):
    SINGLE_VISIT = "SINGLE_VISIT"
    SPECIAL_VISIT = "SPECIAL_VISIT"
    NON_VISIT = "NON_VISIT"
    UNSCHEDULED_VISIT = "UNSCHEDULED_VISIT"
    MANUALLY_DEFINED_VISIT = "MANUALLY_DEFINED_VISIT"


class VisitSubclass(Enum):
    SINGLE_VISIT = "SINGLE_VISIT"
    ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV = "ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV"
    ANCHOR_VISIT_IN_GROUP_OF_SUBV = "ANCHOR_VISIT_IN_GROUP_OF_SUBV"
    REPEATING_VISIT = "REPEATING_VISIT"


@dataclass
class TimeUnit:
    name: str
    conversion_factor_to_master: float
    from_timedelta: Callable = lambda u, x: u.conversion_factor_to_master * x


StudyVisit = TypeVar("StudyVisit")


@dataclass
class Subvisit(Generic[StudyVisit]):
    visit: StudyVisit
    number: int


@dataclass
class BaseTimelineAR(Generic[StudyVisit]):
    """
    TimelineAR is aggregate root implementing idea of time relations between objects.
    Generally timeline consists of visits ordered by their internal relations.
    If there is a need to create ordered setup of visits and epochs you have to
    collect_visits_to_epochs
    """

    study_uid: str
    _visits: list[StudyVisit]

    @trace_calls
    def _generate_timeline(self):
        """
        Function creating ordered list of visits based on _visits list
        """
        anchors: dict[str, StudyVisit] = {}
        visits_dict: dict[str, StudyVisit] = {
            visit.uid: visit for visit in self._visits
        }
        subvisit_sets: dict[str, list[Subvisit]] = {}
        references = [
            visit.visit_sublabel_reference
            for visit in self._visits
            if visit.visit_sublabel_reference
        ]
        amount_of_subvisits_for_visit: dict[str, int] = {
            ref: references.count(ref) for ref in references
        }
        special_visits_for_visit_anchor: dict[str, StudyVisit] = {}

        # Create Anchor lookups
        for visit in self._visits:
            # There can be multiple Visits with same VisitType that can work as TimeRef
            # If Study contains multiple such Visits, the first occurence of the Visit with given VisitType
            # that works as TimeRef will be picked to be an anchor for the other visits
            anchors.setdefault(visit.visit_type_name, visit)

            if (
                visit.visit_subclass == VisitSubclass.ANCHOR_VISIT_IN_GROUP_OF_SUBV
                and visit.uid
            ):
                visit.subvisit_number = 0
                subvisit_sets[visit.uid] = [Subvisit(visit, 0)]
            elif visit.visit_class == VisitClass.SPECIAL_VISIT:
                # SpecialVisits anchored to same StudyVisit have the same timing, in scope of the same anchor visit
                # the early discontinuation visits should be ordered in the end of special visit set
                all_special_visits_anchoring_visit = special_visits_for_visit_anchor.get(
                    visit.visit_sublabel_reference, []  # type: ignore[arg-type]
                )
                all_special_visits_anchoring_visit.append(visit)
                special_visits_for_visit_anchor.setdefault(
                    visit.visit_sublabel_reference,
                    sorted(  # type: ignore[call-overload]
                        all_special_visits_anchoring_visit,
                        key=lambda x: x.visit_type_name
                        == settings.study_visit_type_early_discontinuation_visit,
                    ),
                )

        # Assign Anchors
        for order, visit in enumerate(self._visits):
            time_anchor = visit.time_reference_name
            if time_anchor == settings.previous_visit_name and len(self._visits) > 1:
                visit.anchor_visit = self._visits[order - 1]
            elif time_anchor in anchors and visit.uid != anchors[time_anchor].uid:
                visit.anchor_visit = anchors[time_anchor]

            if (
                visit.visit_subclass
                == VisitSubclass.ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
            ):
                visits = subvisit_sets[visit.visit_sublabel_reference]
                visit.anchor_visit = visits[0].visit
            elif visit.visit_class == VisitClass.SPECIAL_VISIT:
                visit.anchor_visit = visits_dict.get(visit.visit_sublabel_reference)

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
                visit.visit_type_name == settings.study_visit_type_information_visit
                and idx == 0
            ):
                visit.visit_order = settings.visit_0_number
                visit.visit_number = settings.visit_0_number
                continue
            if visit.visit_class == VisitClass.NON_VISIT:
                visit.visit_order = settings.non_visit_number
                visit.visit_number = settings.non_visit_number
            elif visit.visit_class == VisitClass.UNSCHEDULED_VISIT:
                visit.visit_order = settings.unscheduled_visit_number
                visit.visit_number = settings.unscheduled_visit_number
            elif visit.visit_class == VisitClass.MANUALLY_DEFINED_VISIT:
                visit.visit_order = order
            elif visit.visit_class == VisitClass.SPECIAL_VISIT:
                visit.visit_order = order
                visit.visit_number = visit.anchor_visit.visit_number
            elif (
                visit.visit_subclass
                != VisitSubclass.ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
            ):
                visit.visit_order = order
                visit.visit_number = last_visit_num
            if (
                visit.visit_subclass
                == VisitSubclass.ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
            ):
                visit.visit_order = order
                visit.visit_number = visit.anchor_visit.visit_number
            elif visit.visit_class not in [
                VisitClass.MANUALLY_DEFINED_VISIT,
                VisitClass.SPECIAL_VISIT,
            ]:
                last_visit_num += 1
            order += 1

        self._assign_subvisit_numbers(
            ordered_visits=ordered_visits,
            subvisit_sets=subvisit_sets,
            amount_of_subvisits_for_visit=amount_of_subvisits_for_visit,
            special_visits_for_visit_anchor=special_visits_for_visit_anchor,
        )

        # sort visits that are returned in the end to capture all timing changes
        ordered_visits = sorted(
            self._visits,
            key=lambda x: (
                x.get_absolute_duration() is None,
                x.get_absolute_duration(),
            ),
        )

        return ordered_visits

    @trace_calls
    def _assign_subvisit_numbers(
        self,
        ordered_visits: list[StudyVisit],
        subvisit_sets: dict[str, list[Subvisit]],
        amount_of_subvisits_for_visit: dict[str, int],
        special_visits_for_visit_anchor: dict[str, StudyVisit],
    ) -> None:
        for visit in ordered_visits:
            if (
                visit.visit_subclass
                == VisitSubclass.ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
            ):
                # we have to assign subvisit numbers after we assign anchor visit numbers because some of subvisits may
                # happen before the anchor visit in group of subvisits and that will influence numbering
                visits: list[Subvisit] = subvisit_sets[visit.visit_sublabel_reference]
                amount_of_subvisits = amount_of_subvisits_for_visit[
                    visit.visit_sublabel_reference
                ]
                if amount_of_subvisits < 10:
                    increment_step = 10
                elif 10 <= amount_of_subvisits < 20:
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
                    visit.subvisit_number = last_subvisit_number
                    # insert subvisit before the last visit
                    visits.insert(-1, Subvisit(visit, last_subvisit_number))
                    # the last visit obtains the currently calculated number
                    visits[-1].number = num
                    visits[-1].visit.subvisit_number = num
                else:
                    visit.subvisit_number = num
                    visits.append(Subvisit(visit, num))
            elif visit.visit_class == VisitClass.SPECIAL_VISIT:
                special_visits_for_same_anchor_list: list[StudyVisit] = (
                    special_visits_for_visit_anchor[visit.visit_sublabel_reference]  # type: ignore[assignment]
                )
                # Subvisit number should be derived for special visits pointed to the same anchor visit
                # no matter what type of special visit it is (early_discontinuation or other special visit)
                subvisit_index = special_visits_for_same_anchor_list.index(visit)
                if (
                    visit.visit_type_name
                    == settings.study_visit_type_early_discontinuation_visit
                ):
                    special_visits_of_same_type: list[StudyVisit] = [
                        special_visit
                        for special_visit in special_visits_for_same_anchor_list
                        if special_visit.visit_type_name
                        == settings.study_visit_type_early_discontinuation_visit
                    ]
                else:
                    special_visits_of_same_type = [
                        special_visit
                        for special_visit in special_visits_for_same_anchor_list
                        if special_visit.visit_type_name
                        != settings.study_visit_type_early_discontinuation_visit
                    ]

                # Special visit number should be derived for special visits pointed to the same anchor visit
                # but of the same special visit type, e.g. early discontinuation visits should get their own counter
                # and other speciail visits should get the other counter
                visit.special_visit_number = (
                    special_visits_of_same_type.index(visit) + 1
                )
                visit.subvisit_number = subvisit_index + 1


def strtobool(value: str | None) -> int:
    """Convert a string representation of truth to integer 1 (true) or 0 (false).

    Returns 1 for True values: 'y', 'yes', 't', 'true', 'on', '1'.
    Returns 0 for False values: 'n', 'no', 'f', 'false', 'off', '0'.
    Otherwise raises ValueError.

    Reimplemented because of deprecation https://peps.python.org/pep-0632/#migration-advice

    Returns int to remain compatible with Python 3.7 distutils.util.strtobool().
    """

    if value is None:
        return 0

    val = value.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return 1
    if val in ("n", "no", "f", "false", "off", "0"):
        return 0
    raise ValueError(f"invalid truth value: {value:s}")


def booltostr(value: bool | str | int | None, true_format: str = "Yes") -> str:
    """
    Converts a boolean value to a string representation.
    True values are 'y', 'Y', 'Yes', 'yes', 't', 'true', 'on', and '1';
    False values are 'n', 'N', 'No', 'no', 'f', 'false', 'off', and '0'.

    Args:
        value (bool | str | int): The boolean value to convert. If a string is passed, it will be converted to a boolean.
        true_format (str, optional): The string representation of the True value. Defaults to "Yes".

    Returns:
        str: The string representation of the boolean value.

    Raises:
        ValueError: If the true_format argument is invalid.
    """
    if isinstance(value, str):
        value = bool(strtobool(value))
    elif value is None:
        value = False

    mapping = {
        "y": "n",
        "Y": "N",
        "Yes": "No",
        "yes": "no",
        "t": "f",
        "true": "false",
        "on": "off",
        "1": "0",
    }

    if true_format in mapping:
        if value:
            return true_format
        return mapping[true_format]
    raise ValueError(f"Invalid true format {true_format}")


@overload
def convert_to_datetime(value: neo4j.time.DateTime) -> datetime: ...
@overload
def convert_to_datetime(value: datetime) -> datetime: ...
@overload
def convert_to_datetime(value: None) -> None: ...
def convert_to_datetime(
    value: neo4j.time.DateTime | datetime | None,
) -> datetime | None:
    """
    Converts a neo4j.time.DateTime object from the database to a Python datetime object.

    Args:
        value (neo4j.time.DateTime | datetime | None): The object to convert or None.

    Returns:
        datetime.datetime: The Python datetime object or None if `value` is None.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, neo4j.time.DateTime):
        raise TypeError(f"Expected neo4j.time.DateTime, got {type(value)}")
    return value.to_native()


def validate_page_number_and_page_size(page_number: int, page_size: int):
    validate_max_skip_clause(page_number=page_number, page_size=page_size)


def validate_max_skip_clause(page_number: int, page_size: int) -> None:
    # Rather check twice to prevent Cypher injection; this function is used by various repositories
    if not isinstance(page_number, int) or not isinstance(page_size, int):
        raise TypeError("Expected page_number and page_size to be integers")

    # neo4j supports `SKIP {val}` values which fall within unsigned 64-bit integer range
    ValidationException.raise_if(
        max(1, page_number) * max(1, page_size) >= settings.max_int_neo4j,
        msg=f"(page_number * page_size) value must be smaller than {settings.max_int_neo4j}",
    )


def load_env(key: str, default: str | None = None):
    value = os.environ.get(key)
    log.info("ENV variable fetched: %s=%s", key, value)
    if value is None and default is None:
        log.error("%s is not set and no default was provided", key)
        raise EnvironmentError(f"Failed because {key} is not set.")
    if value is not None:
        return value
    log.warning("%s is not set, using default value: %s", key, default)
    return default


def get_field_type(tp: Any) -> type[Any]:
    """
    Determines the actual type of a given type hint, handling generic types and nested types.

    Args:
        tp (Any): The type hint to analyze.

    Returns:
        type[Any]: The resolved type. If the type hint is a generic type, it returns the type of the contained elements.
        If the type hint is a dictionary, it returns the type of the values.
        Otherwise, it returns the type itself.
    """
    origin = get_origin(tp)
    if not origin or not hasattr(tp, "__args__"):
        return tp

    args = get_args(tp)

    args = tuple(arg for arg in args if arg is not NoneType)

    if len(args) > 1:
        if origin is dict:
            return args[1]
        return tp

    if isinstance(args[0], GenericAlias):
        return get_field_type(args[0])

    return args[0]


def get_sub_fields(field_info: FieldInfo):
    """
    Extracts sub-fields from the given field information.

    This function examines the annotation of the provided FieldInfo object and
    returns a list of sub-fields if the annotation is a list or a union type
    containing a list. If the annotation is not a list or does not contain a list,
    the function returns None.

    Args:
        field_info (FieldInfo): The field information containing the annotation to be examined.

    Returns:
        list | None: A list of sub-fields if the annotation is a list or a union type containing a list, otherwise None.
    """
    if (
        isinstance(field_info.annotation, GenericAlias)
        and get_origin(field_info.annotation) is list
    ):
        return list(get_args(field_info.annotation))

    if isinstance(field_info.annotation, UnionType):
        fields = tuple(
            field for field in get_args(field_info.annotation) if field is not NoneType
        )
        for field in fields:
            if isinstance(field, GenericAlias) and get_origin(field) is list:
                return list(get_args(field))

    return None


def version_string_to_tuple(version: str) -> tuple[int, ...]:
    """
    Converts a version string to a tuple of integers.

    Args:
        version (str): The version string to convert, e.g., "1.2.3".

    Returns:
        tuple[int, ...]: A tuple of integers representing the version.

    Examples:
        >>> version_string_to_tuple("1.2.3")
        (1, 2, 3)

        >>> version_string_to_tuple("4.5.6.7")
        (4, 5, 6, 7)

        >>> version_string_to_tuple("0.1")
        (0, 1)
    """
    return tuple(map(int, version.split(".")))


def get_edit_input_or_previous_value(
    edit_input: BaseModel,
    existing_vo: object,
    field_name: str,
    field_name_in_vo: str | None = None,
):
    """
    Get the value of a field from the edit input if it was provided,
    or return the value from the existing VO if not.
    The ``field_name_in_vo`` parameter allows specifying a different field name in the VO.
    If not provided, it defaults to the same name as in the edit input.
    """
    if field_name_in_vo is None:
        field_name_in_vo = field_name
    if field_name in edit_input.model_fields_set:
        return getattr(edit_input, field_name)
    return getattr(existing_vo, field_name_in_vo)


def is_larger_than_or_equal(value_a: int | None, value_b: int | None) -> bool:
    if value_a is not None and value_b is not None:
        # If both values are not None, compare them directly
        return value_a >= value_b
    if value_a is not None and value_b is None:
        # If value_b is None, value_a is larger than or equal to it
        return True
    if value_a is None and value_b is not None:
        # If value_a is None, it cannot be larger than or equal to value_b
        return False
    return True  # both are None, so they are equal


def sanitize_for_log(value: Any) -> str:
    """Sanitize a value before writing it to a log entry to prevent log injection (CWE-117).

    Removes carriage return and line feed characters so that user-provided values
    cannot be used to forge additional log lines.
    """
    return str(value).replace("\r\n", "").replace("\r", "").replace("\n", "")


def get_db_result_as_dict(row: list[Any], columns: list[str]) -> dict[str, Any]:
    item = {}
    for key, value in zip(columns, row):
        item[key] = value
    return item


# Filter keys used in ORDER BY and WHERE filter expressions to avoid Cypher injection
filter_sort_valid_keys_re = re.compile(
    r"^_?[A-Za-z][A-Za-z0-9_]*(\[[0-9]+])?(?:\.[A-Za-z_][A-Za-z0-9_]*(\[[0-9]+])?)*$"
)


def insert_space_after_commas(text: str, n: int, space=" ") -> str:
    """Inserts a whitespace after the next comma after every n characters, not counting commas.

    The purpose is to make long comma-separated strings line-breakable by injecting spaces after about every N chars,
    (not counting commas).
    """

    parts = text.split(",")
    result = [parts[0]]
    parts_len = len(parts[0])

    for part in parts[1:]:
        result.append(",")

        if parts_len >= n:
            result.append(space)
            parts_len = len(part)
        else:
            parts_len += len(part)

        result.append(part)

    return "".join(result)


def db_pagination_clause(
    page_size: int, page_number: int, one_element_extra: bool = False
) -> str:
    # Ensure Cypher injection would not be possible even if values weren't integer types
    if not isinstance(page_size, int) or not isinstance(page_number, int):
        raise TypeError("Expected page_size and page_number to be integers")
    pagination_clause = ""
    if page_size > 0:
        pagination_clause = f"SKIP {page_number - 1} * {page_size} LIMIT {page_size + 1 if one_element_extra else page_size}"
    return pagination_clause
