from datetime import datetime
from typing import Annotated, Callable, Self

from pydantic import ConfigDict, Field, field_validator

from clinical_mdr_api.domains.controlled_terminologies.ct_package import CTPackageAR
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_selection_standard_version import (
    StudyStandardVersionVO,
)
from clinical_mdr_api.models.controlled_terminologies.ct_package import CTPackage
from clinical_mdr_api.models.utils import (
    BaseModel,
    PatchInputModel,
    PostInputModel,
    get_latest_on_datetime_str,
)
from clinical_mdr_api.services.user_info import UserInfoService


class StudyStandardVersionInput(PostInputModel):
    ct_package_uid: Annotated[
        str, Field(description="CTPackage uid to select for the study")
    ]
    description: Annotated[
        str | None, Field(description="Description of the study standard version")
    ] = None


class StudyStandardVersionEditInput(PatchInputModel):
    ct_package_uid: Annotated[
        str | None,
        Field(
            description="Updated CTPackage uid to select for the study",
        ),
    ] = None
    description: Annotated[
        str | None,
        Field(
            description="Updated description of the study standard version",
        ),
    ] = None


class StudyStandardVersionOGM(BaseModel, StudyStandardVersionVO):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str,
        Field(
            description="Uid of the StandardVersion",
            json_schema_extra={"source": "uid"},
        ),
    ]
    study_uid: Annotated[
        str,
        Field(
            description="Uid of the study",
            json_schema_extra={"source": "has_after.audit_trail.uid"},
        ),
    ]

    study_status: Annotated[StudyStatus, Field(json_schema_extra={"source": "status"})]

    @field_validator("study_status", mode="before")
    @classmethod
    def instantiate_study_status(cls, value):
        return StudyStatus[value]

    start_date: Annotated[
        datetime | None,
        Field(
            description="The most recent point in time when the study standard_version was edited."
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
            json_schema_extra={"source": "has_after.date"},
        ),
    ]
    author_id: Annotated[
        str | None,
        Field(
            description="ID of user that created last modification",
            json_schema_extra={"source": "has_after.author_id", "nullable": True},
        ),
    ]

    ct_package_uid: Annotated[
        str,
        Field(
            description="CTPackage Uid selected for the study",
            json_schema_extra={"source": "has_ct_package.uid"},
        ),
    ]
    description: Annotated[
        str | None,
        Field(
            description="Description of the study standard version",
            json_schema_extra={"source": "description", "nullable": True},
        ),
    ] = None
    automatically_created: Annotated[
        bool,
        Field(
            description="Boolean to register the way the StudyStandardVersion was created, if true means that was automatically created when locking, so should be deleted when unlocking",
            json_schema_extra={"source": "automatically_created"},
        ),
    ] = False


class StudyStandardVersionOGMVer(StudyStandardVersionOGM):
    study_uid: Annotated[
        str,
        Field(
            description="Uid of the study",
            json_schema_extra={"source": "has_after.audit_trail.uid"},
        ),
    ]
    change_type: Annotated[
        str,
        Field(
            description="type of action",
            json_schema_extra={"source": "has_after.__label__"},
        ),
    ]
    end_date: Annotated[
        datetime | None,
        Field(
            description="The last point in time when the study standard version was modified."
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
            json_schema_extra={"source": "has_before.date", "nullable": True},
        ),
    ] = None


class StudyStandardVersion(BaseModel):
    uid: Annotated[str, Field(description="Uid of the StandardVersion")]
    study_uid: Annotated[str, Field(description="Uid of the StandardVersion Study")]
    study_version: Annotated[
        str | None,
        Field(
            title="study version or date information",
            description="Study version number, if specified, otherwise None.",
            json_schema_extra={"nullable": True},
        ),
    ]
    ct_package: Annotated[
        CTPackage | None,
        Field(description="CtPackage", json_schema_extra={"nullable": True}),
    ]
    description: Annotated[
        str | None,
        Field(
            description="Description of the study standard version",
            json_schema_extra={"nullable": True},
        ),
    ]
    automatically_created: Annotated[
        bool,
        Field(
            description="Boolean to register the way the StudyStandardVersion was created, if true means that was automatically created when locking, so should be deleted when unlocking",
        ),
    ] = False
    start_date: Annotated[
        datetime,
        Field(
            description="Study StandardVersion last modification date",
        ),
    ]
    end_date: Annotated[
        datetime | None,
        Field(
            description="Study StandardVersion last modification date",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    study_status: Annotated[str, Field(description="Study StandardVersion status")]
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    change_type: Annotated[
        str | None,
        Field(description="Type of Action", json_schema_extra={"nullable": True}),
    ] = None

    @classmethod
    def from_study_standard_version_vo(
        cls,
        study_standard_version_vo: StudyStandardVersionVO,
        find_ct_package_by_uid: Callable[[str], CTPackageAR | None],
        study_value_version: str | None = None,
    ) -> Self:
        ct_package = None
        ct_package = find_ct_package_by_uid(study_standard_version_vo.ct_package_uid)
        return cls(
            uid=study_standard_version_vo.uid,
            study_uid=study_standard_version_vo.study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            ct_package=ct_package,
            description=study_standard_version_vo.description,
            author_username=UserInfoService.get_author_username_from_id(
                study_standard_version_vo.author_id
            ),
            start_date=study_standard_version_vo.start_date,
            end_date=study_standard_version_vo.end_date,
            study_status=study_standard_version_vo.study_status.name,
            automatically_created=study_standard_version_vo.automatically_created,
        )


class StudyStandardVersionVersion(StudyStandardVersion):
    changes: list[str]
