from neomodel import RelationshipTo

from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrRel,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from common.neomodel import BooleanProperty, StringProperty


class FeatureFlagValue(VersionValue):
    section = StringProperty()
    feature = StringProperty()
    name = StringProperty(index=True)
    enabled = BooleanProperty()
    description = StringProperty()


class FeatureFlagRoot(VersionRoot):
    has_version = RelationshipTo(
        FeatureFlagValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(FeatureFlagValue, "LATEST", model=ClinicalMdrRel)
    latest_final = RelationshipTo(
        FeatureFlagValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        FeatureFlagValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
