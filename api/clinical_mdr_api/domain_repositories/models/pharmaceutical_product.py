from neomodel import One, RelationshipTo, ZeroOrMore, ZeroOrOne

from clinical_mdr_api.domain_repositories.models.active_substance import (
    ActiveSubstanceRoot,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    ConceptRoot,
    ConceptValue,
    LagTimeRoot,
    NumericValueWithUnitRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermContext,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    ClinicalMdrRel,
    VersionRelationship,
)
from common.neomodel import StringProperty


class Ingredient(ClinicalMdrNode):
    external_id = StringProperty()
    formulation_name = StringProperty()

    has_substance = RelationshipTo(
        ActiveSubstanceRoot, "HAS_SUBSTANCE", cardinality=One, model=ClinicalMdrRel
    )
    has_strength_value = RelationshipTo(
        NumericValueWithUnitRoot,
        "HAS_STRENGTH_VALUE",
        cardinality=ZeroOrOne,
        model=ClinicalMdrRel,
    )
    has_half_life = RelationshipTo(
        NumericValueWithUnitRoot,
        "HAS_HALF_LIFE",
        cardinality=ZeroOrOne,
        model=ClinicalMdrRel,
    )
    has_lag_time = RelationshipTo(
        LagTimeRoot, "HAS_LAG_TIME", cardinality=ZeroOrMore, model=ClinicalMdrRel
    )


class IngredientFormulation(ClinicalMdrNode):
    external_id = StringProperty()

    has_ingredient = RelationshipTo(
        Ingredient, "HAS_INGREDIENT", cardinality=ZeroOrMore, model=ClinicalMdrRel
    )


class PharmaceuticalProductValue(ConceptValue):
    has_formulation = RelationshipTo(
        IngredientFormulation,
        "HAS_FORMULATION",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )
    has_dosage_form = RelationshipTo(
        CTTermContext, "HAS_DOSAGE_FORM", cardinality=ZeroOrMore, model=ClinicalMdrRel
    )
    has_route_of_administration = RelationshipTo(
        CTTermContext,
        "HAS_ROUTE_OF_ADMINISTRATION",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )


class PharmaceuticalProductRoot(ConceptRoot):
    has_version = RelationshipTo(
        PharmaceuticalProductValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        PharmaceuticalProductValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        PharmaceuticalProductValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        PharmaceuticalProductValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        PharmaceuticalProductValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
