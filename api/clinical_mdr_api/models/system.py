"""System models."""

from typing import Annotated

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class StudyNumberRegex(BaseModel):
    regex: Annotated[
        str,
        Field(description="Python regular expression a study number must fully match"),
    ]
    message: Annotated[
        str,
        Field(description="Error message shown when a study number does not match"),
    ]


class SystemSettings(BaseModel):
    studies_study_number_regex: Annotated[
        StudyNumberRegex,
        Field(
            description="The regular expression pattern used to validate study numbers in the system"
        ),
    ]


class SystemInformation(BaseModel):
    api_version: Annotated[str, Field(description="Version of the API specification")]
    db_version: Annotated[
        str,
        Field(
            description="Version information from the Neo4j database the application is using"
        ),
    ]
    db_name: Annotated[
        str, Field(description="Name of the database the application is using")
    ]
    build_id: Annotated[
        str, Field(description="The Build.BuildNumber identifier from the pipeline run")
    ]
    commit_id: Annotated[
        str | None,
        Field(
            description="The reference to the repository state: the id of the last commit to the branch at build",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    branch_name: Annotated[
        str | None,
        Field(
            description="Name of the VCS repository branch the app was built from",
            json_schema_extra={"nullable": True},
        ),
    ] = None
