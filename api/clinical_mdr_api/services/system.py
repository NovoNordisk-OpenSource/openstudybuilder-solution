import os

from neomodel import config as neomodel_config

from clinical_mdr_api.models.system import SystemInformation
from clinical_mdr_api.repositories import system as repository


def get_system_information():
    # avoid circular import
    from clinical_mdr_api.main import app

    return SystemInformation(
        api_version=app.version,
        db_version=repository.get_neo4j_version(),
        db_name=get_database_name(),
        build_id=get_build_id(),
        commit_id=os.environ.get("BUILD_COMMIT"),
        branch_name=os.environ.get("BUILD_BRANCH"),
    )


def get_build_id() -> str:
    return os.environ.get("BUILD_NUMBER") or "unknown"


def get_database_name() -> str:
    """Returns database name part of neomodel config database URL"""
    return neomodel_config.DATABASE_NAME
