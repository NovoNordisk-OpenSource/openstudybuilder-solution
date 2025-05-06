from neomodel import (
    BooleanProperty,
    IntegerProperty,
    One,
    OneOrMore,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    ZeroOrMore,
    ZeroOrOne,
)

from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGroupValue,
    ActivityInstanceValue,
    ActivitySubGroupValue,
    ActivityValue,
)
from clinical_mdr_api.domain_repositories.models.compounds import CompoundAliasValue
from clinical_mdr_api.domain_repositories.models.concepts import (
    NumericValueWithUnitRoot,
    UnitDefinitionRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNodeWithUID,
    ClinicalMdrRel,
    Conjunction,
    ConjunctionRelation,
)
from clinical_mdr_api.domain_repositories.models.medicinal_product import (
    MedicinalProductValue,
)
from clinical_mdr_api.domain_repositories.models.pharmaceutical_product import (
    PharmaceuticalProductValue,
)
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Delete,
    StudyAction,
)
from clinical_mdr_api.domain_repositories.models.syntax import (
    ActivityInstructionValue,
    CriteriaTemplateValue,
    CriteriaValue,
    EndpointTemplateValue,
    EndpointValue,
    FootnoteTemplateValue,
    FootnoteValue,
    ObjectiveTemplateValue,
    ObjectiveValue,
    TimeframeValue,
)

STUDY_VALUE_CLASS_NAME = ".study.StudyValue"
STUDY_SOA_FOOTNOTE_CLASS_NAME = ".study.StudySoAFootnote"
STUDY_ARM_CLASS_NAME = ".study_selections.StudyArm"
STUDY_BRANCH_ARM_CLASS_NAME = ".study_selections.StudyBranchArm"
STUDY_COHORT_CLASS_NAME = ".study_selections.StudyCohort"
STUDY_EPOCH_CLASS_NAME = ".study_epoch.StudyEpoch"
STUDY_ELEMENT_CLASS_NAME = ".study_selections.StudyElement"


class AuditTrailMixin:
    """Mixin class to provide audit trail required relations."""

    has_before = RelationshipFrom(
        StudyAction, "BEFORE", model=ConjunctionRelation, cardinality=ZeroOrOne
    )
    has_after = RelationshipFrom(
        StudyAction, "AFTER", model=ConjunctionRelation, cardinality=One
    )


class HasProtocolSoACellRel(ClinicalMdrRel):
    row = IntegerProperty()
    column = IntegerProperty()
    span = IntegerProperty()
    is_propagated = BooleanProperty()
    order = IntegerProperty()


class HasProtocolSoAFootnoteRel(ClinicalMdrRel):
    order = IntegerProperty()
    symbol = StringProperty()


class StudySelection(ClinicalMdrNodeWithUID, AuditTrailMixin):
    order = IntegerProperty()
    accepted_version = BooleanProperty()


class StudyObjective(StudySelection):
    has_selected_objective = RelationshipTo(
        ObjectiveValue,
        "HAS_SELECTED_OBJECTIVE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_selected_objective_template = RelationshipTo(
        ObjectiveTemplateValue,
        "HAS_SELECTED_OBJECTIVE_TEMPLATE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_objective_level = RelationshipTo(
        CTTermRoot, "HAS_OBJECTIVE_LEVEL", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )
    study_endpoint_has_study_objective = RelationshipFrom(
        "StudyEndpoint", "STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE", model=ClinicalMdrRel
    )
    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_OBJECTIVE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )


# pylint: disable=abstract-method
class StudyEndpointUnitRel(ClinicalMdrRel):
    index = IntegerProperty()


class StudyEndpoint(StudySelection):
    __optional_labels__ = ["TemplateParameterTermRoot"]
    text = StringProperty()
    study_endpoint_has_study_objective = RelationshipTo(
        StudyObjective,
        "STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_selected_endpoint = RelationshipTo(
        EndpointValue,
        "HAS_SELECTED_ENDPOINT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_selected_endpoint_template = RelationshipTo(
        EndpointTemplateValue,
        "HAS_SELECTED_ENDPOINT_TEMPLATE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_selected_timeframe = RelationshipTo(
        TimeframeValue, "HAS_SELECTED_TIMEFRAME", model=ClinicalMdrRel
    )
    has_endpoint_level = RelationshipTo(
        CTTermRoot,
        "HAS_ENDPOINT_LEVEL",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_endpoint_sublevel = RelationshipTo(
        CTTermRoot,
        "HAS_ENDPOINT_SUB_LEVEL",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_unit = RelationshipTo(
        UnitDefinitionRoot,
        "HAS_UNIT",
        model=StudyEndpointUnitRel,
        cardinality=ZeroOrMore,
    )
    has_conjunction = RelationshipTo(
        Conjunction,
        "HAS_CONJUNCTION",
        model=ConjunctionRelation,
        cardinality=ZeroOrMore,
    )
    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_ENDPOINT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )


class StudyCompound(StudySelection):
    other_information = StringProperty()
    has_selected_compound = RelationshipTo(
        CompoundAliasValue,
        "HAS_SELECTED_COMPOUND",
        model=ClinicalMdrRel,
        cardinality=One,
    )
    has_type_of_treatment = RelationshipTo(
        CTTermRoot, "HAS_TYPE_OF_TREATMENT", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )
    has_medicinal_product = RelationshipTo(
        MedicinalProductValue,
        "HAS_MEDICINAL_PRODUCT",
        model=ClinicalMdrRel,
        cardinality=One,
    )
    has_pharmaceutical_product = RelationshipTo(
        PharmaceuticalProductValue,
        "HAS_PHARMACEUTICAL_PRODUCT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    has_dose_frequency = RelationshipTo(
        CTTermRoot, "HAS_DOSE_FREQUENCY", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )
    has_delivery_device = RelationshipTo(
        CTTermRoot, "HAS_DELIVERY_DEVICE", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )
    has_dose_value = RelationshipTo(
        NumericValueWithUnitRoot,
        "HAS_DOSE_VALUE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_dispenser = RelationshipTo(
        CTTermRoot, "HAS_DISPENSED_IN", model=ClinicalMdrRel, cardinality=One
    )
    has_reason_for_missing = RelationshipTo(
        CTTermRoot,
        "HAS_REASON_FOR_NULL_VALUE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_compound_dosing = RelationshipTo(
        "StudyCompoundDosing",
        "STUDY_COMPOUND_HAS_COMPOUND_DOSING",
        cardinality=OneOrMore,
        model=ClinicalMdrRel,
    )
    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_COMPOUND",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )


class StudyCriteria(StudySelection):
    has_selected_criteria = RelationshipTo(
        CriteriaValue,
        "HAS_SELECTED_CRITERIA",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_selected_criteria_template = RelationshipTo(
        CriteriaTemplateValue,
        "HAS_SELECTED_CRITERIA_TEMPLATE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    key_criteria = BooleanProperty(default=False)
    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_CRITERIA",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )


class StudySoAGroup(StudySelection):
    show_soa_group_in_protocol_flowchart = BooleanProperty(default=False)
    has_study_soa_group = RelationshipFrom(
        ".study.StudyValue",
        "HAS_STUDY_SOA_GROUP",
        cardinality=ZeroOrMore,
    )
    has_flowchart_group = RelationshipTo(
        CTTermRoot,
        "HAS_FLOWCHART_GROUP",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    has_soa_group_selection = RelationshipFrom(
        "StudyActivity",
        "STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    study_soa_footnote_references_study_soa_group = RelationshipFrom(
        STUDY_SOA_FOOTNOTE_CLASS_NAME,
        "REFERENCES_STUDY_SOA_GROUP",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )


class StudyActivitySubGroup(StudySelection):
    show_activity_subgroup_in_protocol_flowchart = BooleanProperty(default=True)
    has_study_activity_sub_group = RelationshipFrom(
        ".study.StudyValue",
        "HAS_STUDY_ACTIVITY_SUBGROUP",
        cardinality=ZeroOrMore,
    )
    study_activity_has_study_activity_subgroup = RelationshipFrom(
        "StudyActivity", "STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP"
    )
    has_selected_activity_subgroup = RelationshipTo(
        ActivitySubGroupValue, "HAS_SELECTED_ACTIVITY_SUBGROUP", model=ClinicalMdrRel
    )
    study_soa_footnote_references_study_activity_subgroup = RelationshipFrom(
        STUDY_SOA_FOOTNOTE_CLASS_NAME,
        "REFERENCES_STUDY_ACTIVITY_SUBGROUP",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )


class StudyActivityGroup(StudySelection):
    show_activity_group_in_protocol_flowchart = BooleanProperty(default=True)
    has_study_activity_group = RelationshipFrom(
        ".study.StudyValue",
        "HAS_STUDY_ACTIVITY_GROUP",
        cardinality=ZeroOrMore,
    )
    study_activity_has_study_activity_group = RelationshipFrom(
        "StudyActivity", "STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP"
    )
    has_selected_activity_group = RelationshipTo(
        ActivityGroupValue, "HAS_SELECTED_ACTIVITY_GROUP", model=ClinicalMdrRel
    )
    study_soa_footnote_references_study_activity_group = RelationshipFrom(
        STUDY_SOA_FOOTNOTE_CLASS_NAME,
        "REFERENCES_STUDY_ACTIVITY_GROUP",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )


class StudyActivity(StudySelection):
    show_activity_in_protocol_flowchart = BooleanProperty(default=False)
    has_study_activity = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_ACTIVITY",
        cardinality=ZeroOrMore,
    )
    has_selected_activity = RelationshipTo(
        ActivityValue,
        "HAS_SELECTED_ACTIVITY",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    has_soa_group_selection = RelationshipTo(
        StudySoAGroup,
        "STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP",
        model=ClinicalMdrRel,
        cardinality=OneOrMore,
    )
    study_activity_has_study_activity_subgroup = RelationshipTo(
        StudyActivitySubGroup,
        "STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    study_activity_has_study_activity_group = RelationshipTo(
        StudyActivityGroup,
        "STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    study_activity_has_study_activity_instance = RelationshipTo(
        "StudyActivityInstance",
        "STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    study_activity_schedule = RelationshipTo(
        "StudyActivitySchedule",
        "STUDY_ACTIVITY_HAS_SCHEDULE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    has_study_activity_instruction = RelationshipTo(
        "StudyActivityInstruction",
        "STUDY_ACTIVITY_HAS_INSTRUCTION",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    study_soa_footnote_references_study_activity = RelationshipFrom(
        STUDY_SOA_FOOTNOTE_CLASS_NAME,
        "REFERENCES_STUDY_ACTIVITY",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )


class StudyActivityInstance(StudySelection):
    has_study_activity_instance = RelationshipFrom(
        ".study.StudyValue",
        "HAS_STUDY_ACTIVITY_INSTANCE",
        cardinality=ZeroOrMore,
    )
    has_selected_activity_instance = RelationshipTo(
        ActivityInstanceValue,
        "HAS_SELECTED_ACTIVITY_INSTANCE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    study_activity_has_study_activity_instance = RelationshipFrom(
        StudyActivity,
        "STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE",
        model=ClinicalMdrRel,
        cardinality=One,
    )
    show_activity_instance_in_protocol_flowchart = BooleanProperty(default=False)


class StudyActivitySchedule(StudySelection):
    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_ACTIVITY_SCHEDULE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    study_activity = RelationshipFrom(
        StudyActivity,
        "STUDY_ACTIVITY_HAS_SCHEDULE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    study_visit = RelationshipFrom(
        ".study_visit.StudyVisit",
        "STUDY_VISIT_HAS_SCHEDULE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    study_soa_footnote_references_study_activity_schedule = RelationshipFrom(
        STUDY_SOA_FOOTNOTE_CLASS_NAME,
        "REFERENCES_STUDY_ACTIVITY_SCHEDULE",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )


class StudyDesignCell(StudySelection):
    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_DESIGN_CELL",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    study_arm = RelationshipFrom(
        STUDY_ARM_CLASS_NAME,
        "STUDY_ARM_HAS_DESIGN_CELL",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    study_branch_arm = RelationshipFrom(
        STUDY_BRANCH_ARM_CLASS_NAME,
        "STUDY_BRANCH_ARM_HAS_DESIGN_CELL",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    study_epoch = RelationshipFrom(
        STUDY_EPOCH_CLASS_NAME,
        "STUDY_EPOCH_HAS_DESIGN_CELL",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    study_element = RelationshipFrom(
        STUDY_ELEMENT_CLASS_NAME,
        "STUDY_ELEMENT_HAS_DESIGN_CELL",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )

    transition_rule = StringProperty()


class StudyArm(StudySelection):
    name = StringProperty()
    short_name = StringProperty()
    arm_code = StringProperty()
    description = StringProperty()
    arm_colour = StringProperty()
    randomization_group = StringProperty()
    number_of_subjects = IntegerProperty()

    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_ARM",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )

    arm_type = RelationshipTo(
        CTTermRoot,
        "HAS_ARM_TYPE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_design_cell = RelationshipTo(
        StudyDesignCell,
        "STUDY_ARM_HAS_DESIGN_CELL",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    has_branch_arm = RelationshipTo(
        STUDY_BRANCH_ARM_CLASS_NAME,
        "STUDY_ARM_HAS_BRANCH_ARM",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    has_cohort = RelationshipTo(
        STUDY_COHORT_CLASS_NAME,
        "STUDY_ARM_HAS_COHORT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )


class StudyElement(StudySelection):
    name = StringProperty()
    short_name = StringProperty()
    element_code = StringProperty()
    description = StringProperty()
    planned_duration = StringProperty()
    start_rule = StringProperty()
    end_rule = StringProperty()
    element_colour = StringProperty()
    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_ELEMENT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    element_subtype = RelationshipTo(
        CTTermRoot,
        "HAS_ELEMENT_SUBTYPE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_design_cell = RelationshipTo(
        StudyDesignCell,
        "STUDY_ELEMENT_HAS_DESIGN_CELL",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    has_compound_dosing = RelationshipTo(
        "StudyCompoundDosing",
        "STUDY_ELEMENT_HAS_COMPOUND_DOSING",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )


class StudyActivityInstruction(StudySelection):
    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_ACTIVITY_INSTRUCTION",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    study_activity = RelationshipFrom(
        StudyActivity,
        "STUDY_ACTIVITY_HAS_INSTRUCTION",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    activity_instruction_value = RelationshipTo(
        ActivityInstructionValue,
        "HAS_SELECTED_ACTIVITY_INSTRUCTION",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )


class StudyBranchArm(StudySelection):
    name = StringProperty()
    short_name = StringProperty()
    branch_arm_code = StringProperty()
    description = StringProperty()
    colour_code = StringProperty()
    randomization_group = StringProperty()
    number_of_subjects = IntegerProperty()
    order = StringProperty()

    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_BRANCH_ARM",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    has_design_cell = RelationshipTo(
        StudyDesignCell,
        "STUDY_BRANCH_ARM_HAS_DESIGN_CELL",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    has_cohort = RelationshipTo(
        STUDY_COHORT_CLASS_NAME,
        "STUDY_BRANCH_ARM_HAS_COHORT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    arm_root = RelationshipFrom(
        StudyArm,
        "STUDY_ARM_HAS_BRANCH_ARM",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )


class StudyCohort(StudySelection):
    name = StringProperty()
    short_name = StringProperty()
    cohort_code = StringProperty()
    description = StringProperty()
    colour_code = StringProperty()
    number_of_subjects = IntegerProperty()

    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_COHORT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    arm_root = RelationshipFrom(
        StudyArm,
        "STUDY_ARM_HAS_COHORT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    branch_arm_root = RelationshipFrom(
        StudyBranchArm,
        "STUDY_BRANCH_ARM_HAS_COHORT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )


class StudyCompoundDosing(StudySelection):
    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_COMPOUND_DOSING",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )

    has_dose_frequency = RelationshipTo(
        CTTermRoot, "HAS_DOSE_FREQUENCY", cardinality=ZeroOrOne
    )
    has_dose_value = RelationshipTo(
        NumericValueWithUnitRoot, "HAS_DOSE_VALUE", cardinality=ZeroOrOne
    )
    study_compound = RelationshipFrom(
        StudyCompound,
        "STUDY_COMPOUND_HAS_COMPOUND_DOSING",
        cardinality=ZeroOrOne,
        model=ClinicalMdrRel,
    )
    study_element = RelationshipFrom(
        StudyElement,
        "STUDY_ELEMENT_HAS_COMPOUND_DOSING",
        cardinality=ZeroOrOne,
        model=ClinicalMdrRel,
    )


class StudySoAFootnote(StudySelection):
    footnote_number = IntegerProperty()
    references_study_activity = RelationshipTo(
        StudyActivity,
        "REFERENCES_STUDY_ACTIVITY",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )
    references_study_activity_subgroup = RelationshipTo(
        StudyActivitySubGroup,
        "REFERENCES_STUDY_ACTIVITY_SUBGROUP",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )
    references_study_activity_group = RelationshipTo(
        StudyActivityGroup,
        "REFERENCES_STUDY_ACTIVITY_GROUP",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )
    references_study_soa_group = RelationshipTo(
        StudySoAGroup,
        "REFERENCES_STUDY_SOA_GROUP",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )
    references_study_activity_schedule = RelationshipTo(
        StudyActivitySchedule,
        "REFERENCES_STUDY_ACTIVITY_SCHEDULE",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )
    references_study_visit = RelationshipTo(
        ".study_visit.StudyVisit",
        "REFERENCES_STUDY_VISIT",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )
    references_study_epoch = RelationshipTo(
        ".study_epoch.StudyEpoch",
        "REFERENCES_STUDY_EPOCH",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )
    has_footnote = RelationshipTo(
        FootnoteValue,
        "HAS_SELECTED_FOOTNOTE",
        cardinality=ZeroOrOne,
        model=ClinicalMdrRel,
    )
    has_footnote_template = RelationshipTo(
        FootnoteTemplateValue,
        "HAS_SELECTED_FOOTNOTE_TEMPLATE",
        cardinality=ZeroOrOne,
        model=ClinicalMdrRel,
    )
    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_FOOTNOTE",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )
    has_deleted = RelationshipFrom(
        Delete, "AFTER", model=ConjunctionRelation, cardinality=ZeroOrOne
    )
