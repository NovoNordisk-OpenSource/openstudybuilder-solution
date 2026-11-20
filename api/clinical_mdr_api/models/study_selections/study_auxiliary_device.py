from datetime import datetime
from typing import Annotated

from pydantic import ConfigDict, Field, field_validator

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_auxiliary_device import (
    StudyAuxiliaryDeviceVO,
)
from clinical_mdr_api.models.utils import BaseModel, PostInputModel
from common.config import settings

DEVICE_TERM = "has_auxiliary_device.has_selected_term"


class StudyAuxiliaryDeviceCreateInput(PostInputModel):
    auxiliary_device_term_uid: Annotated[
        str, Field(description="UID of the auxiliary device CT term")
    ]
    order: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=0,
            lt=settings.max_int_neo4j,
            description="The ordering of the selection",
        ),
    ] = None


class StudyAuxiliaryDeviceOGM(BaseModel, StudyAuxiliaryDeviceVO):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[str, Field(json_schema_extra={"source": "uid"})]
    study_uid: Annotated[
        str, Field(json_schema_extra={"source": "has_after.audit_trail.uid"})
    ]
    order: Annotated[
        int,
        Field(
            description="The ordering of the selection",
            json_schema_extra={"source": "order"},
        ),
    ]
    status: Annotated[
        StudyStatus,
        Field(
            description="Study auxiliary device status",
            json_schema_extra={"source": "status", "nullable": True},
        ),
    ]

    @field_validator("status", mode="before")
    @classmethod
    def instantiate_study_status(cls, value):
        return StudyStatus[value]

    start_date: Annotated[
        datetime,
        Field(
            description="The most recent point in time when the study auxiliary device was edited. "
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
            json_schema_extra={"source": "has_after.date", "nullable": True},
        ),
    ]
    author_id: Annotated[
        str,
        Field(
            description="ID of user that created last modification",
            json_schema_extra={"source": "has_after.author_id", "nullable": True},
        ),
    ]
    author_username: Annotated[
        str | None,
        Field(json_schema_extra={"nullable": True, "remove_from_wildcard": True}),
    ] = None

    auxiliary_device_term_uid: Annotated[
        str, Field(json_schema_extra={"source": f"{DEVICE_TERM}.uid"})
    ]
    auxiliary_device_name: Annotated[
        str | None,
        Field(
            description="Sponsor preferred name of the device term",
            json_schema_extra={
                "source": f"{DEVICE_TERM}.has_name_root.latest_final.name",
                "nullable": True,
            },
        ),
    ] = None
    auxiliary_device_nci_preferred_name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": f"{DEVICE_TERM}.has_attributes_root.latest_final.preferred_term",
                "nullable": True,
            },
        ),
    ] = None
    # the term keeps a CTCodelistTerm for every submission value it ever had, so the
    # repository resolves it; the source only serves filtering, sorting and headers,
    # which can still match old values. Fix with a Cypher listing if that matters.
    auxiliary_device_submission_value: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": f"{DEVICE_TERM}.has_term_root.submission_value",
                "exclude_from_model_validate": True,
                "nullable": True,
            },
        ),
    ] = None
    auxiliary_device_definition: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": f"{DEVICE_TERM}.has_attributes_root.latest_final.definition",
                "nullable": True,
            },
        ),
    ] = None
    auxiliary_device_algorithm: Annotated[
        str | None,
        Field(
            description="SDTM algorithm text read by SAS programs",
            json_schema_extra={
                "source": f"{DEVICE_TERM}.has_attributes_root.latest_final.algorithm",
                "nullable": True,
            },
        ),
    ] = None

    accepted_version: Annotated[bool, Field()] = False


class StudyAuxiliaryDeviceOGMVer(StudyAuxiliaryDeviceOGM):
    change_type: Annotated[
        str,
        Field(json_schema_extra={"source": "has_after.__label__"}),
    ]
    end_date: Annotated[
        datetime | None,
        Field(
            description="The last point in time when the study auxiliary device was modified."
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
            json_schema_extra={"source": "has_before.date", "nullable": True},
        ),
    ] = None


class StudyAuxiliaryDevice(StudyAuxiliaryDeviceCreateInput):
    uid: Annotated[str, Field()]
    study_uid: Annotated[str, Field()]
    study_version: Annotated[
        str | None,
        Field(
            description="Study version number, if specified, otherwise None.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    auxiliary_device_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    auxiliary_device_nci_preferred_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    auxiliary_device_submission_value: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    auxiliary_device_definition: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    auxiliary_device_algorithm: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    start_date: Annotated[
        datetime, Field(description="Study auxiliary device last modification date")
    ]
    end_date: Annotated[
        datetime | None,
        Field(
            description="Study auxiliary device last modification date",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    status: Annotated[str, Field(description="Study auxiliary device status")]
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    change_type: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )


class StudyAuxiliaryDeviceVersion(StudyAuxiliaryDevice):
    changes: Annotated[list[str], Field()]


class StudyAuxiliaryDeviceNewOrder(BaseModel):
    new_order: Annotated[
        int,
        Field(
            description="New order of the selected auxiliary device",
            gt=0,
            lt=settings.max_int_neo4j,
        ),
    ]
