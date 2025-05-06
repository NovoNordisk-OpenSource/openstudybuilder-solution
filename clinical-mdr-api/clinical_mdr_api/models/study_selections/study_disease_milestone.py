from datetime import datetime
from typing import Annotated

from pydantic import ConfigDict, Field, field_validator

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_disease_milestone import (
    StudyDiseaseMilestoneVO,
)
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel
from common import config


class StudyDiseaseMilestoneEditInput(PatchInputModel):
    disease_milestone_type: Annotated[
        str | None, Field(description="Study Disease Milestone Type uid")
    ] = None
    repetition_indicator: bool | None = None


class StudyDiseaseMilestoneCreateInput(PostInputModel):
    disease_milestone_type: Annotated[
        str, Field(description="Study Disease Milestone Type uid")
    ]
    repetition_indicator: bool
    order: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=0,
            lt=config.MAX_INT_NEO4J,
            description="The ordering of the selection",
        ),
    ] = None
    study_uid: str


class StudyDiseaseMilestoneOGM(BaseModel, StudyDiseaseMilestoneVO):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[str, Field(json_schema_extra={"source": "uid"})]
    study_uid: Annotated[
        str, Field(json_schema_extra={"source": "has_after.audit_trail.uid"})
    ]

    order: Annotated[
        int | None,
        Field(
            description="The ordering of the selection",
            json_schema_extra={"source": "order", "nullable": True},
        ),
    ] = None
    status: Annotated[
        StudyStatus,
        Field(
            description="Study disease milestone status",
            json_schema_extra={"source": "status", "nullable": True},
        ),
    ]

    @field_validator("status", mode="before")
    @classmethod
    def instantiate_study_status(cls, value):
        return StudyStatus[value]

    start_date: Annotated[
        datetime | None,
        Field(
            description="The most recent point in time when the study disease_milestone was edited."
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
            json_schema_extra={"source": "has_after.date", "nullable": True},
        ),
    ]
    author_id: Annotated[
        str | None,
        Field(
            description="ID of user that created last modification",
            json_schema_extra={"source": "has_after.author_id", "nullable": True},
        ),
    ]
    author_username: Annotated[str | None, Field(json_schema_extra={"nullable": True})]

    disease_milestone_type: Annotated[
        str,
        Field(
            description="Name of the disease_milestone type based on CT term",
            json_schema_extra={"source": "has_disease_milestone_type.uid"},
        ),
    ]

    disease_milestone_type_definition: Annotated[
        str,
        Field(
            description="Name of the disease_milestone type based on CT term",
            json_schema_extra={
                "source": "has_disease_milestone_type.has_attributes_root.latest_final.definition"
            },
        ),
    ]

    disease_milestone_type_name: Annotated[
        str,
        Field(
            description="Name of the disease_milestone type based on CT term",
            json_schema_extra={
                "source": "has_disease_milestone_type.has_name_root.latest_final.name"
            },
        ),
    ]

    repetition_indicator: Annotated[
        bool, Field(json_schema_extra={"source": "repetition_indicator"})
    ]


class StudyDiseaseMilestoneOGMVer(StudyDiseaseMilestoneOGM):
    study_uid: Annotated[
        str,
        Field(json_schema_extra={"source": "has_after.audit_trail.uid"}),
    ]
    change_type: Annotated[
        str,
        Field(json_schema_extra={"source": "has_after.__label__"}),
    ]
    end_date: Annotated[
        datetime | None,
        Field(
            description="The last point in time when the study disease milestone was modified."
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
            json_schema_extra={"source": "has_before.date", "nullable": True},
        ),
    ] = None


class StudyDiseaseMilestone(StudyDiseaseMilestoneCreateInput):
    uid: Annotated[str, Field()]
    study_uid: Annotated[str, Field()]
    study_version: Annotated[
        str | None,
        Field(
            title="study version or date information",
            description="Study version number, if specified, otherwise None.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    disease_milestone_type: str
    disease_milestone_type_name: str
    disease_milestone_type_definition: str
    start_date: Annotated[
        datetime, Field(description="Study DiseaseMilestone last modification date")
    ]
    end_date: Annotated[
        datetime | None,
        Field(
            description="Study DiseaseMilestone last modification date",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    status: Annotated[str, Field(description="Study DiseaseMilestone status")]
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    change_type: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )


class StudyDiseaseMilestoneVersion(StudyDiseaseMilestone):
    changes: list[str]


class StudySelectionDiseaseMilestoneNewOrder(BaseModel):
    new_order: Annotated[
        int,
        Field(
            description="new order of the selected disease milestones",
            gt=-config.MAX_INT_NEO4J,
            lt=config.MAX_INT_NEO4J,
        ),
    ]
