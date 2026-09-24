from neomodel import RelationshipFrom, RelationshipTo, ZeroOrMore, ZeroOrOne

from clinical_mdr_api.domain_repositories.models.concepts import UnitDefinitionRoot
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermContext,
)
from clinical_mdr_api.domain_repositories.models.generic import ClinicalMdrRel
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyDesignCell,
    StudySelection,
    StudySoAFootnote,
)
from common.neomodel import IntegerProperty, StringProperty


class StudyEpoch(StudySelection):
    study_value = RelationshipFrom(
        StudyValue, "HAS_STUDY_EPOCH", model=ClinicalMdrRel, cardinality=ZeroOrMore
    )
    has_epoch = RelationshipTo(
        CTTermContext, "HAS_EPOCH", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )
    has_epoch_subtype = RelationshipTo(
        CTTermContext, "HAS_EPOCH_SUB_TYPE", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )
    has_epoch_type = RelationshipTo(
        CTTermContext, "HAS_EPOCH_TYPE", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )
    name = StringProperty()
    short_name = StringProperty()
    description = StringProperty()
    start_rule = StringProperty()
    end_rule = StringProperty()
    color_hash = StringProperty()
    status = StringProperty()

    # Lag time is only intended to support studies migrated from MMA.
    # The three event types mirror the ones MMA recorded.
    ae_lag_time = IntegerProperty()
    hypo_lag_time = IntegerProperty()
    ce_lag_time = IntegerProperty()

    has_ae_lag_time_unit = RelationshipTo(
        UnitDefinitionRoot,
        "HAS_AE_LAG_TIME_UNIT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_hypo_lag_time_unit = RelationshipTo(
        UnitDefinitionRoot,
        "HAS_HYPO_LAG_TIME_UNIT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_ce_lag_time_unit = RelationshipTo(
        UnitDefinitionRoot,
        "HAS_CE_LAG_TIME_UNIT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_design_cell = RelationshipTo(
        StudyDesignCell,
        "STUDY_EPOCH_HAS_DESIGN_CELL",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    has_study_visit = RelationshipTo(
        ".study_visit.StudyVisit",
        "STUDY_EPOCH_HAS_STUDY_VISIT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    study_soa_footnote_references_study_epoch = RelationshipFrom(
        StudySoAFootnote,
        "REFERENCES_STUDY_EPOCH",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )
