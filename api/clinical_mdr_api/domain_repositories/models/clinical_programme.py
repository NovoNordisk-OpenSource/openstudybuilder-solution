from clinical_mdr_api.domain_repositories.models.generic import ClinicalMdrNodeWithUID
from common.neomodel import StringProperty


class ClinicalProgramme(ClinicalMdrNodeWithUID):
    name = StringProperty()
