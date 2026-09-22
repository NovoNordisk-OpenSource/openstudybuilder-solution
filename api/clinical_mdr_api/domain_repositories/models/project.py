from neomodel import RelationshipFrom

from clinical_mdr_api.domain_repositories.models.clinical_programme import (
    ClinicalProgramme,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNodeWithUID,
    ClinicalMdrRel,
)
from common.neomodel import StringProperty


class Project(ClinicalMdrNodeWithUID):
    project_number = StringProperty()
    name = StringProperty()
    description = StringProperty()
    holds_project = RelationshipFrom(
        ClinicalProgramme, "HOLDS_PROJECT", model=ClinicalMdrRel
    )
