from neomodel import One, RelationshipFrom, RelationshipTo

from clinical_mdr_api.domain_repositories.models.concepts import (
    ConceptRoot,
    ConceptValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrRel,
    VersionRelationship,
)
from common.neomodel import BooleanProperty


class CompoundValue(ConceptValue):
    pass


class CompoundRoot(ConceptRoot):
    has_version = RelationshipTo(
        CompoundValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(CompoundValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(CompoundValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    latest_final = RelationshipTo(CompoundValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        CompoundValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class CompoundAliasValue(ConceptValue):
    is_preferred_synonym = BooleanProperty()

    is_compound = RelationshipTo(
        CompoundRoot, "IS_COMPOUND", cardinality=One, model=ClinicalMdrRel
    )

    compound_alias_root = RelationshipFrom(
        "CompoundAliasRoot", "HAS_VERSION", model=VersionRelationship
    )


class CompoundAliasRoot(ConceptRoot):
    has_version = RelationshipTo(
        CompoundAliasValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        CompoundAliasValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        CompoundAliasValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        CompoundAliasValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        CompoundAliasValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
