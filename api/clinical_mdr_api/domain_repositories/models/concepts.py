from neomodel import One, RelationshipFrom, RelationshipTo, ZeroOrMore, ZeroOrOne

from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermContext,
)
from clinical_mdr_api.domain_repositories.models.dictionary import UCUMTermRoot
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrRel,
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from common.neomodel import (
    BooleanProperty,
    FloatProperty,
    IntegerProperty,
    StringProperty,
)


class ConceptValue(VersionValue):
    __optional_labels__ = ["TemplateParameterTermValue"]
    nci_concept_id = StringProperty()
    nci_concept_name = StringProperty()
    name = StringProperty()
    name_sentence_case = StringProperty()
    definition = StringProperty()
    abbreviation = StringProperty()
    external_id = StringProperty()


class ConceptRoot(VersionRoot):
    __optional_labels__ = ["TemplateParameterTermRoot"]
    LIBRARY_REL_LABEL = "CONTAINS_CONCEPT"

    has_library = RelationshipFrom(Library, LIBRARY_REL_LABEL, model=ClinicalMdrRel)


class UnitDefinitionValue(ConceptValue):
    legacy_code = StringProperty()
    convertible_unit = BooleanProperty()
    display_unit = BooleanProperty()
    master_unit = BooleanProperty()
    si_unit = BooleanProperty()
    us_conventional_unit = BooleanProperty()
    use_complex_unit_conversion = BooleanProperty()
    use_molecular_weight = BooleanProperty()
    conversion_factor_to_master = FloatProperty()
    order = IntegerProperty()
    comment = StringProperty()

    has_ct_unit = RelationshipTo(
        CTTermContext, "HAS_CT_UNIT", cardinality=ZeroOrMore, model=ClinicalMdrRel
    )
    has_unit_subset = RelationshipTo(
        CTTermContext, "HAS_UNIT_SUBSET", cardinality=ZeroOrMore, model=ClinicalMdrRel
    )
    has_ct_dimension = RelationshipTo(
        CTTermContext, "HAS_CT_DIMENSION", cardinality=ZeroOrOne, model=ClinicalMdrRel
    )
    has_ucum_term = RelationshipTo(
        UCUMTermRoot, "HAS_UCUM_TERM", cardinality=ZeroOrOne, model=ClinicalMdrRel
    )


class UnitDefinitionRoot(ConceptRoot):
    has_version = RelationshipTo(
        UnitDefinitionValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        UnitDefinitionValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        UnitDefinitionValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        UnitDefinitionValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        UnitDefinitionValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class SimpleConceptValue(ConceptValue):
    pass


class SimpleConceptRoot(ConceptRoot):
    pass


class TextValue(SimpleConceptValue):
    pass


class TextValueRoot(SimpleConceptRoot):
    has_version = RelationshipTo(TextValue, "HAS_VERSION", model=VersionRelationship)
    has_latest_value = RelationshipTo(TextValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(TextValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    latest_final = RelationshipTo(TextValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(TextValue, "LATEST_RETIRED", model=ClinicalMdrRel)


class VisitNameValue(SimpleConceptValue):
    pass


class VisitNameRoot(SimpleConceptRoot):
    has_version = RelationshipTo(
        VisitNameValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(VisitNameValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(VisitNameValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    latest_final = RelationshipTo(VisitNameValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        VisitNameValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class NumericValue(SimpleConceptValue):
    name = StringProperty()
    value = FloatProperty()


class NumericValueRoot(SimpleConceptRoot):
    has_version = RelationshipTo(NumericValue, "HAS_VERSION", model=VersionRelationship)
    has_latest_value = RelationshipTo(NumericValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(NumericValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    latest_final = RelationshipTo(NumericValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        NumericValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class StudyDayValue(NumericValue):
    pass


class StudyDayRoot(NumericValueRoot):
    has_version = RelationshipTo(
        StudyDayValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(StudyDayValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(StudyDayValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    latest_final = RelationshipTo(StudyDayValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        StudyDayValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class StudyWeekValue(NumericValue):
    pass


class StudyWeekRoot(NumericValueRoot):
    has_version = RelationshipTo(
        StudyWeekValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(StudyWeekValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(StudyWeekValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    latest_final = RelationshipTo(StudyWeekValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        StudyWeekValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class StudyDurationDaysValue(NumericValue):
    pass


class StudyDurationDaysRoot(NumericValueRoot):
    has_version = RelationshipTo(
        StudyDurationDaysValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        StudyDurationDaysValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        StudyDurationDaysValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        StudyDurationDaysValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        StudyDurationDaysValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class StudyDurationWeeksValue(NumericValue):
    pass


class StudyDurationWeeksRoot(NumericValueRoot):
    has_version = RelationshipTo(
        StudyDurationWeeksValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        StudyDurationWeeksValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        StudyDurationWeeksValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        StudyDurationWeeksValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        StudyDurationWeeksValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class WeekInStudyValue(NumericValue):
    pass


class WeekInStudyRoot(NumericValueRoot):
    has_version = RelationshipTo(
        WeekInStudyValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(WeekInStudyValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(
        WeekInStudyValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        WeekInStudyValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        WeekInStudyValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class TimePointValue(SimpleConceptValue):
    has_value = RelationshipTo(
        NumericValueRoot, "HAS_VALUE", cardinality=One, model=ClinicalMdrRel
    )
    has_unit_definition = RelationshipTo(
        UnitDefinitionRoot, "HAS_UNIT_DEFINITION", cardinality=One, model=ClinicalMdrRel
    )
    has_time_reference = RelationshipTo(
        CTTermContext, "HAS_TIME_REFERENCE", cardinality=One, model=ClinicalMdrRel
    )


class TimePointRoot(SimpleConceptRoot):
    has_version = RelationshipTo(
        TimePointValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(TimePointValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(TimePointValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    latest_final = RelationshipTo(TimePointValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        TimePointValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class NumericValueWithUnitValue(NumericValue):
    has_unit_definition = RelationshipTo(
        UnitDefinitionRoot,
        "HAS_UNIT_DEFINITION",
        cardinality=ZeroOrOne,
        model=ClinicalMdrRel,
    )


class NumericValueWithUnitRoot(NumericValueRoot):
    has_version = RelationshipTo(
        NumericValueWithUnitValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        NumericValueWithUnitValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        NumericValueWithUnitValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        NumericValueWithUnitValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        NumericValueWithUnitValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class LagTimeValue(NumericValue):
    has_unit_definition = RelationshipTo(
        UnitDefinitionRoot, "HAS_UNIT_DEFINITION", cardinality=One, model=ClinicalMdrRel
    )

    has_sdtm_domain = RelationshipTo(
        CTTermContext, "HAS_SDTM_DOMAIN", cardinality=One, model=ClinicalMdrRel
    )


class LagTimeRoot(NumericValueRoot):
    has_version = RelationshipTo(LagTimeValue, "HAS_VERSION", model=VersionRelationship)
    has_latest_value = RelationshipTo(LagTimeValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(LagTimeValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    latest_final = RelationshipTo(LagTimeValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        LagTimeValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
