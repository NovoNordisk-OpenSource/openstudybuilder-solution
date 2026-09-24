from neomodel import One, RelationshipFrom, RelationshipTo, ZeroOrMore

from clinical_mdr_api.domain_repositories.models.controlled_terminology import CTPackage
from clinical_mdr_api.domain_repositories.models.generic import ClinicalMdrRel
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_selections import StudySelection
from common.neomodel import BooleanProperty, StringProperty


class StudyStandardVersion(StudySelection):
    study_value = RelationshipFrom(
        StudyValue, "HAS_STUDY_STANDARD_VERSION", cardinality=ZeroOrMore
    )
    status = StringProperty()
    description = StringProperty()
    automatically_created = BooleanProperty()
    has_ct_package = RelationshipTo(
        CTPackage,
        "HAS_CT_PACKAGE",
        model=ClinicalMdrRel,
        cardinality=One,
    )
