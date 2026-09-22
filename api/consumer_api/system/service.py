import os
import urllib.parse
from typing import Annotated

from neomodel import db
from pydantic import BaseModel, Field


class SystemInformation(BaseModel):
    api_version: Annotated[str, Field(description="Version of the API specification")]
    db_version: Annotated[
        str | None,
        Field(
            description="Version information from the Neo4j database the application is using",
        ),
    ] = None
    db_name: Annotated[
        str | None,
        Field(
            description="Name of the database the application is using",
        ),
    ] = None
    build_id: Annotated[
        str,
        Field(
            description="The Build.BuildNumber identifier from the pipeline run",
        ),
    ]
    commit_id: Annotated[
        str | None,
        Field(
            description="The reference to the repository state: the id of the last commit to the branch at build",
        ),
    ] = None
    branch_name: Annotated[
        str | None,
        Field(
            description="Name of the VCS repository branch the app was built from",
        ),
    ] = None


def get_system_information():
    # avoid circular import
    from consumer_api.consumer_api import app

    return SystemInformation(
        api_version=app.version,
        db_version=get_neo4j_version(),
        db_name=get_database_name(),
        build_id=get_build_id(),
        commit_id=os.environ.get("BUILD_COMMIT"),
        branch_name=os.environ.get("BUILD_BRANCH"),
    )


def get_build_id() -> str:
    return os.environ.get("BUILD_NUMBER") or "unknown"


def get_database_name() -> str | None:
    """Returns database name part of neomodel config database URL"""
    if db.url is None:
        return None
    return urllib.parse.urlparse(db.url).path.split("/", 1)[-1]


def get_neo4j_version():
    get_neo4j_version_query = """
        CALL dbms.components()
        YIELD versions
        UNWIND versions as version
        RETURN version
        """
    result, _ = db.cypher_query(query=get_neo4j_version_query)
    return result[0][0]
