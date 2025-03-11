from neomodel import (
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    ZeroOrMore,
    ZeroOrOne,
)

from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import ClinicalMdrRel
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyDesignCell,
    StudySelection,
    StudySoAFootnote,
)


class StudyEpoch(StudySelection):
    study_value = RelationshipFrom(
        StudyValue, "HAS_STUDY_EPOCH", model=ClinicalMdrRel, cardinality=ZeroOrMore
    )
    has_epoch = RelationshipTo(
        CTTermRoot, "HAS_EPOCH", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )
    has_epoch_subtype = RelationshipTo(
        CTTermRoot, "HAS_EPOCH_SUB_TYPE", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )
    has_epoch_type = RelationshipTo(
        CTTermRoot, "HAS_EPOCH_TYPE", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )
    name = StringProperty()
    short_name = StringProperty()
    description = StringProperty()
    start_rule = StringProperty()
    end_rule = StringProperty()
    color_hash = StringProperty()
    status = StringProperty()
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
