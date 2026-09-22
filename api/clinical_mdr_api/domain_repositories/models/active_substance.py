from neomodel import RelationshipTo, ZeroOrOne

from clinical_mdr_api.domain_repositories.models.concepts import (
    ConceptRoot,
    ConceptValue,
)
from clinical_mdr_api.domain_repositories.models.dictionary import DictionaryTermRoot
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrRel,
    VersionRelationship,
)
from common.neomodel import StringProperty


class ActiveSubstanceValue(ConceptValue):
    analyte_number = StringProperty()
    short_number = StringProperty()
    long_number = StringProperty()
    inn = StringProperty()

    has_unii_value = RelationshipTo(
        DictionaryTermRoot,
        "HAS_UNII_VALUE",
        cardinality=ZeroOrOne,
        model=ClinicalMdrRel,
    )


class ActiveSubstanceRoot(ConceptRoot):
    has_version = RelationshipTo(
        ActiveSubstanceValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        ActiveSubstanceValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        ActiveSubstanceValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        ActiveSubstanceValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        ActiveSubstanceValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
