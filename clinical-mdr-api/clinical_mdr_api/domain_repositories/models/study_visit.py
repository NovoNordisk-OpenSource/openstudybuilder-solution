from neomodel import (
    BooleanProperty,
    FloatProperty,
    IntegerProperty,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    ZeroOrMore,
    ZeroOrOne,
)

from clinical_mdr_api.domain_repositories.models.concepts import (
    StudyDayRoot,
    StudyDurationDaysRoot,
    StudyDurationWeeksRoot,
    StudyWeekRoot,
    TimePointRoot,
    UnitDefinitionRoot,
    VisitNameRoot,
    WeekInStudyRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import ClinicalMdrRel
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_epoch import StudyEpoch
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivitySchedule,
    StudySelection,
    StudySoAFootnote,
)


class StudyVisit(StudySelection):
    has_study_visit = RelationshipFrom(
        StudyValue,
        "HAS_STUDY_VISIT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    study_epoch_has_study_visit = RelationshipFrom(
        StudyEpoch,
        "STUDY_EPOCH_HAS_STUDY_VISIT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )

    visit_number = FloatProperty()

    has_visit_type = RelationshipTo(
        CTTermRoot,
        "HAS_VISIT_TYPE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )

    # uid of the anchor StudyVisit given Subvisit refers to
    visit_sublabel_reference = StringProperty()

    visit_name_label = StringProperty()
    short_visit_label = StringProperty()
    unique_visit_number = StringProperty()
    consecutive_visit_group = StringProperty()
    show_visit = BooleanProperty()

    visit_window_min = IntegerProperty()
    visit_window_max = IntegerProperty()

    has_window_unit = RelationshipTo(
        UnitDefinitionRoot,
        "HAS_WINDOW_UNIT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )

    description = StringProperty()
    start_rule = StringProperty()
    end_rule = StringProperty()
    has_visit_contact_mode = RelationshipTo(
        CTTermRoot,
        "HAS_VISIT_CONTACT_MODE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_epoch_allocation = RelationshipTo(
        CTTermRoot,
        "HAS_EPOCH_ALLOCATION",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    is_global_anchor_visit = BooleanProperty()
    status = StringProperty()
    visit_class = StringProperty()
    visit_subclass = StringProperty()
    is_soa_milestone = BooleanProperty(default=False)

    has_repeating_frequency = RelationshipTo(
        CTTermRoot,
        "HAS_REPEATING_FREQUENCY",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_timepoint = RelationshipTo(
        TimePointRoot,
        "HAS_TIMEPOINT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_study_day = RelationshipTo(
        StudyDayRoot,
        "HAS_STUDY_DAY",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_study_duration_days = RelationshipTo(
        StudyDurationDaysRoot,
        "HAS_STUDY_DURATION_DAYS",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_study_week = RelationshipTo(
        StudyWeekRoot,
        "HAS_STUDY_WEEK",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    has_study_duration_weeks = RelationshipTo(
        StudyDurationWeeksRoot,
        "HAS_STUDY_DURATION_WEEKS",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_week_in_study = RelationshipTo(
        WeekInStudyRoot,
        "HAS_WEEK_IN_STUDY",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_visit_name = RelationshipTo(
        VisitNameRoot,
        "HAS_VISIT_NAME",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )

    has_study_activity_schedule = RelationshipTo(
        StudyActivitySchedule,
        "STUDY_VISIT_HAS_SCHEDULE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    study_soa_footnote_references_study_visit = RelationshipFrom(
        StudySoAFootnote,
        "REFERENCES_STUDY_VISIT",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )
