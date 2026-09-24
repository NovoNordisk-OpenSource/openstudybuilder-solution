import inspect

from neomodel import db

from clinical_mdr_api.domain_repositories.models.clinical_programme import (
    ClinicalProgramme,
)
from clinical_mdr_api.domain_repositories.models.project import Project


def current_function_name() -> str:
    return inspect.stack()[1][3]


def wipe_study_definition_repository() -> None:
    """
    Static method intended only for testing. Marked as protected (leading underscore) to make
    linters warn obout its invocation (which should never be done by the application).

    We put it in this class to maintain or storage related logic in single class.
    """
    # we simply delete all relationship and nodes we use to store StudyDefinition data.
    with db.transaction:
        db.cypher_query("MATCH (:StudyRoot)-[vr]-(:StudyValue) DELETE vr")
        db.cypher_query("MATCH (:StudyValue)-[vr]-(:StudyProjectField) DELETE vr")
        db.cypher_query("MATCH (:StudyValue)-[vr]-(:StudyTextField) DELETE vr")
        db.cypher_query("MATCH (:StudyValue)-[vr]-(:StudyTimeField) DELETE vr")
        db.cypher_query("MATCH (:StudyValue)-[vr]-(:StudyBooleanField) DELETE vr")
        db.cypher_query("MATCH (:StudyValue)-[vr]-(:StudyArrayField) DELETE vr")
        db.cypher_query("MATCH (:StudyProjectField)-[vr]-(:Project) DELETE vr")
        db.cypher_query("MATCH (sr:StudyRoot) DELETE sr")
        db.cypher_query("MATCH (sv:StudyValue) DELETE sv")
        db.cypher_query("MATCH (sf:StudyField) DELETE sf")


def wipe_project_repository() -> None:
    """
    Static method intended only for testing. Marked as protected (leading underscore) to make
    linters warn obout its invocation (which should never be done by the application).

    We put it in this class to maintain or storage related logic in single class.
    """
    # we simply delete all nodes used to store Project.
    projects = Project.nodes.all()
    for node in projects:
        node.delete()


def wipe_clinical_programme_repository() -> None:
    """
    Static method intended only for testing. Marked as protected (leading underscore) to make
    linters warn obout its invocation (which should never be done by the application).

    We put it in this class to maintain or storage related logic in single class.
    """
    # we simply delete all nodes used to store Clinical Programme.
    clinical_programmes = ClinicalProgramme.nodes.all()
    for node in clinical_programmes:
        node.delete()
