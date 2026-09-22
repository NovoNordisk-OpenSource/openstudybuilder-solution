from neomodel import RelationshipTo

from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrRel,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from common.neomodel import StringProperty


class StudyTemplateValue(VersionValue):
    study_uid = StringProperty()
    study_value_version = StringProperty()


class StudyTemplateRoot(VersionRoot):
    has_version = RelationshipTo(
        StudyTemplateValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        StudyTemplateValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        StudyTemplateValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        StudyTemplateValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        StudyTemplateValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
