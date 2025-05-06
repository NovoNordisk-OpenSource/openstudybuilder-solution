from datetime import datetime
from typing import Annotated

from pydantic import ConfigDict, Field

from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameWithConflictFlag,
)
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel
from common import config


class StudyVisitCreateInput(PostInputModel):
    study_epoch_uid: Annotated[str, Field(alias="study_epoch_uid")]
    visit_type_uid: Annotated[
        str, Field(json_schema_extra={"source": "has_visit_type.uid"})
    ]
    time_reference_uid: str | None = None
    time_value: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=-config.MAX_INT_NEO4J,
            lt=config.MAX_INT_NEO4J,
        ),
    ] = None
    time_unit_uid: str | None = None
    visit_sublabel_reference: str | None = None
    consecutive_visit_group: str | None = None
    show_visit: Annotated[bool, Field(alias="show_visit")]
    min_visit_window_value: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=-config.MAX_INT_NEO4J,
            lt=config.MAX_INT_NEO4J,
        ),
    ] = -9999
    max_visit_window_value: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=-config.MAX_INT_NEO4J,
            lt=config.MAX_INT_NEO4J,
        ),
    ] = 9999
    visit_window_unit_uid: str | None = None
    description: str | None = None
    start_rule: str | None = None
    end_rule: str | None = None
    visit_contact_mode_uid: str
    epoch_allocation_uid: str | None = None
    visit_class: str
    visit_subclass: str | None = None
    is_global_anchor_visit: bool
    is_soa_milestone: bool = False
    visit_name: str | None = None
    visit_short_name: str | None = None
    visit_number: float | None = None
    unique_visit_number: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=-config.MAX_INT_NEO4J,
            lt=config.MAX_INT_NEO4J,
        ),
    ] = None
    repeating_frequency_uid: Annotated[
        str | None, Field(json_schema_extra={"source": "has_repeating_frequency.uid"})
    ] = None


class StudyVisitEditInput(PatchInputModel):
    uid: Annotated[str, Field(description="Uid of the Visit")]
    study_epoch_uid: Annotated[str, Field(alias="study_epoch_uid")]
    visit_type_uid: Annotated[
        str, Field(json_schema_extra={"source": "has_visit_type.uid"})
    ]
    time_reference_uid: str | None = None
    time_value: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=-config.MAX_INT_NEO4J,
            lt=config.MAX_INT_NEO4J,
        ),
    ]
    time_unit_uid: str | None = None
    visit_sublabel_reference: str | None = None
    consecutive_visit_group: str | None = None
    show_visit: Annotated[bool, Field(alias="show_visit")]
    min_visit_window_value: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=-config.MAX_INT_NEO4J,
            lt=config.MAX_INT_NEO4J,
        ),
    ] = -9999
    max_visit_window_value: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=-config.MAX_INT_NEO4J,
            lt=config.MAX_INT_NEO4J,
        ),
    ] = 9999
    visit_window_unit_uid: str | None = None
    description: str | None = None
    start_rule: str | None = None
    end_rule: str | None = None
    visit_contact_mode_uid: str
    epoch_allocation_uid: str | None = None
    visit_class: str
    visit_subclass: str | None = None
    is_global_anchor_visit: bool
    is_soa_milestone: bool = False
    visit_name: str | None = None
    visit_short_name: str | None = None
    visit_number: float | None = None
    unique_visit_number: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=-config.MAX_INT_NEO4J,
            lt=config.MAX_INT_NEO4J,
        ),
    ] = None
    repeating_frequency_uid: Annotated[
        str | None, Field(json_schema_extra={"source": "has_repeating_frequency.uid"})
    ] = None


class SimpleStudyVisit(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str, Field(description="Uid of the visit", json_schema_extra={"source": "uid"})
    ]
    visit_name: Annotated[
        str,
        Field(
            description="Name of the visit",
            json_schema_extra={"source": "has_visit_name.has_latest_value.name"},
        ),
    ]
    visit_type_name: Annotated[
        str,
        Field(
            description="Name of the visit type",
            json_schema_extra={
                "source": "has_visit_type.has_name_root.has_latest_value.name"
            },
        ),
    ]


class StudyVisit(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    uid: Annotated[str, Field(description="Uid of the Visit")]
    study_epoch_uid: Annotated[str, Field(alias="study_epoch_uid")]
    visit_type_uid: Annotated[
        str, Field(json_schema_extra={"source": "has_visit_type.uid"})
    ]
    visit_sublabel_reference: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    consecutive_visit_group: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    show_visit: Annotated[bool, Field(alias="show_visit")]
    min_visit_window_value: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = -9999
    max_visit_window_value: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = 9999
    visit_window_unit_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    start_rule: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    end_rule: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    study_uid: str
    study_id: Annotated[
        str | None,
        Field(
            description="The study ID like 'CDISC DEV-0'",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    study_version: Annotated[
        str | None,
        Field(
            title="study version or date information",
            description="Study version number, if specified, otherwise None.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    study_epoch: SimpleCTTermNameWithConflictFlag
    # study_epoch_name can be calculated from uid
    epoch_uid: Annotated[str, Field(description="The uid of the study epoch")]

    order: int
    visit_type: SimpleCTTermNameWithConflictFlag
    visit_type_name: str

    time_reference_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    time_reference_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    time_reference: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    time_value: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    time_unit_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    time_unit_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    time_unit: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    visit_contact_mode_uid: str
    visit_contact_mode: SimpleCTTermNameWithConflictFlag
    epoch_allocation_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    epoch_allocation: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    repeating_frequency_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    repeating_frequency: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    duration_time: Annotated[
        float | None, Field(json_schema_extra={"nullable": True})
    ] = None
    duration_time_unit: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    study_day_number: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_duration_days: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_duration_days_label: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_day_label: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_week_number: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_duration_weeks: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_duration_weeks_label: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_week_label: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    week_in_study_label: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    visit_number: Annotated[float, Field(alias="visit_number")]
    visit_subnumber: int

    unique_visit_number: Annotated[int, Field(alias="unique_visit_number")]
    visit_subname: str

    visit_name: str
    visit_short_name: str

    visit_window_unit_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    visit_class: str
    visit_subclass: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    is_global_anchor_visit: bool
    is_soa_milestone: bool
    status: Annotated[str, Field(description="Study Visit status")]
    start_date: Annotated[datetime, Field(description="Study Visit creation date")]
    end_date: Annotated[
        datetime | None,
        Field(
            description="Study Visit last date of version",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    possible_actions: Annotated[
        list[str],
        Field(description="List of actions to perform on item"),
    ]
    study_activity_count: Annotated[
        int | None,
        Field(
            description="Count of Study Activities assigned to Study Visit",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    change_type: Annotated[
        str | None,
        Field(description="Type of Action", json_schema_extra={"nullable": True}),
    ] = None


class StudyVisitVersion(StudyVisit):
    changes: list[str]


class AllowedTimeReferences(BaseModel):
    time_reference_uid: str
    time_reference_name: str


class VisitConsecutiveGroupInput(PostInputModel):
    visits_to_assign: Annotated[
        list[str],
        Field(
            description="List of visits to be assigned to the consecutive_visit_group",
            min_length=2,
        ),
    ]
    overwrite_visit_from_template: Annotated[
        str | None,
        Field(
            description="The uid of the visit from which get properties to overwrite"
        ),
    ] = None
