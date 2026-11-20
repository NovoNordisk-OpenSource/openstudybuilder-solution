from neomodel import RelationshipFrom, RelationshipTo, ZeroOrMore, ZeroOrOne

from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermContext,
)
from clinical_mdr_api.domain_repositories.models.generic import ClinicalMdrRel
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_selections import StudySelection
from common.neomodel import StringProperty


class StudyAuxiliaryDevice(StudySelection):
    study_value = RelationshipFrom(
        StudyValue, "HAS_STUDY_AUXILIARY_DEVICE", cardinality=ZeroOrMore
    )
    status = StringProperty()
    has_auxiliary_device = RelationshipTo(
        CTTermContext,
        "HAS_AUXILIARY_DEVICE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
