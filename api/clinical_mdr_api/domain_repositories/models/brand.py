from clinical_mdr_api.domain_repositories.models.generic import ClinicalMdrNodeWithUID
from common.neomodel import BooleanProperty, StringProperty


class Brand(ClinicalMdrNodeWithUID):
    name = StringProperty()
    is_deleted = BooleanProperty(default=False)
