"""System models."""

from typing import Annotated

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class SystemInformation(BaseModel):
    api_version: Annotated[
        str,
        Field(title="API version", description="Version of the API specification"),
    ]
    db_version: Annotated[
        str,
        Field(
            title="Database version",
            description="Version information from the Neo4j database the application is using",
        ),
    ]
    db_name: Annotated[
        str,
        Field(
            title="Database name",
            description="Name of the database the application is using",
        ),
    ]
    build_id: Annotated[
        str,
        Field(
            title="Build identifier",
            description="The Build.BuildNumber identifier from the pipeline run",
        ),
    ]
    commit_id: Annotated[
        str | None,
        Field(
            title="VCS commit identifier",
            description="The reference to the repository state: the id of the last commit to the branch at build",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    branch_name: Annotated[
        str | None,
        Field(
            title="Repository branch name",
            description="Name of the VCS repository branch the app was built from",
            json_schema_extra={"nullable": True},
        ),
    ] = None
