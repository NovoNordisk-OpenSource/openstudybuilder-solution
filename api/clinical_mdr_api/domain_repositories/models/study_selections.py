from neomodel import (
    One,
    OneOrMore,
    RelationshipFrom,
    RelationshipTo,
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
    CTTermContext,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNodeWithUID,
    ClinicalMdrRel,
    Conjunction,
    ConjunctionRelation,
    ZonedDateTimeProperty,
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
from common.neomodel import BooleanProperty, IntegerProperty, StringProperty

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


class StudyDataSupplier(StudySelection):
    blinded = BooleanProperty()
    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_DATA_SUPPLIER",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_study_data_supplier_type = RelationshipTo(
        CTTermContext,
        "HAS_STUDY_DATA_SUPPLIER_TYPE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    study_activity_instance_has_study_data_supplier = RelationshipFrom(
        "StudyActivityInstance",
        "HAS_STUDY_DATA_SUPPLIER",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )


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
        CTTermContext,
        "HAS_OBJECTIVE_LEVEL",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
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
        CTTermContext,
        "HAS_ENDPOINT_LEVEL",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_endpoint_sublevel = RelationshipTo(
        CTTermContext,
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
        CTTermContext,
        "HAS_TYPE_OF_TREATMENT",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
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
    has_delivery_device = RelationshipTo(
        CTTermContext,
        "HAS_DELIVERY_DEVICE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_dispenser = RelationshipTo(
        CTTermContext, "HAS_DISPENSED_IN", model=ClinicalMdrRel, cardinality=One
    )
    has_reason_for_missing = RelationshipTo(
        CTTermContext,
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
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_SOA_GROUP",
        cardinality=ZeroOrMore,
    )
    has_flowchart_group = RelationshipTo(
        CTTermContext,
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
        STUDY_VALUE_CLASS_NAME,
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
        STUDY_VALUE_CLASS_NAME,
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
    keep_old_version = BooleanProperty(default=False)
    keep_old_version_date = ZonedDateTimeProperty()
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
    replaced_by = RelationshipTo(
        "StudyActivity",
        "REPLACED_BY",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )


class StudyActivityInstance(StudySelection):
    keep_old_version = BooleanProperty(default=False)
    keep_old_version_date = ZonedDateTimeProperty()
    show_activity_instance_in_protocol_flowchart = BooleanProperty(default=False)
    is_important = BooleanProperty(default=False)
    has_study_activity_instance = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
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
    is_reviewed = BooleanProperty(default=False)
    has_baseline = RelationshipTo(
        ".study_visit.StudyVisit",
        "HAS_BASELINE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    has_study_data_supplier = RelationshipTo(
        StudyDataSupplier,
        "HAS_STUDY_DATA_SUPPLIER",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_origin_type = RelationshipTo(
        CTTermContext,
        "HAS_ORIGIN_TYPE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_origin_source = RelationshipTo(
        CTTermContext,
        "HAS_ORIGIN_SOURCE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )


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
    label = StringProperty()
    arm_code = StringProperty()
    description = StringProperty()
    randomization_group = StringProperty()
    merge_branch_for_this_arm_for_sdtm_adam = BooleanProperty(default=False)
    number_of_subjects = IntegerProperty()

    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_ARM",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )

    arm_type = RelationshipTo(
        CTTermContext,
        "HAS_ARM_TYPE",
        model=ClinicalMdrRel,
        cardinality=One,
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
        CTTermContext,
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
    randomization_group = StringProperty()
    number_of_subjects = IntegerProperty()

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
    composition = StringProperty()
    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_COMPOUND_DOSING",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    has_dose_frequency = RelationshipTo(
        CTTermContext, "HAS_DOSE_FREQUENCY", cardinality=ZeroOrOne
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


class StudyDesignClass(StudySelection):
    value = StringProperty()
    has_study_design_class = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_DESIGN_CLASS",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )


class StudySourceVariable(StudySelection):
    source_variable = StringProperty()
    source_variable_description = StringProperty()
    has_study_source_variable = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME,
        "HAS_STUDY_SOURCE_VARIABLE",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )


class StudyVersion(StudySelection):
    other_reason_for_locking = StringProperty()
    other_reason_for_unlocking = StringProperty()

    has_reason_for_lock = RelationshipTo(
        CTTermContext,
        "HAS_REASON_FOR_LOCK",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_reason_for_unlock = RelationshipTo(
        CTTermContext,
        "HAS_REASON_FOR_UNLOCK",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME, "HAS_STUDY_VERSION", model=ClinicalMdrRel
    )


class StudyDefinitionDocument(StudySelection):
    protocol_header_major_version = IntegerProperty()
    protocol_header_minor_version = IntegerProperty()

    study_value = RelationshipFrom(
        STUDY_VALUE_CLASS_NAME, "HAS_STUDY_DEFINITION_DOCUMENT", model=ClinicalMdrRel
    )


# All domain classes that inherit StudySelection (excluding the abstract base).
STUDY_SELECTION_CONCRETE_LABELS: frozenset[str] = frozenset(
    {
        "StudyDataSupplier",
        "StudyObjective",
        "StudyEndpoint",
        "StudyCompound",
        "StudyCriteria",
        "StudySoAGroup",
        "StudyActivitySubGroup",
        "StudyActivityGroup",
        "StudyActivity",
        "StudyActivityInstance",
        "StudyActivitySchedule",
        "StudyDesignCell",
        "StudyArm",
        "StudyElement",
        "StudyActivityInstruction",
        "StudyBranchArm",
        "StudyCohort",
        "StudyCompoundDosing",
        "StudySoAFootnote",
        "StudyDesignClass",
        "StudySourceVariable",
        "StudyVersion",
        "StudyDefinitionDocument",
        "StudyEpoch",
        "StudyVisit",
        "StudyDiseaseMilestone",
        "StudyStandardVersion",
    }
)

# Omitted from clone/source-vs-target containment checks: footnote rows depend on
# which selection subgraph was copied, so counts are not comparable to the source.
STUDY_SELECTION_LABELS_EXCLUDED_FROM_CONTAINMENT: frozenset[str] = frozenset(
    {
        "StudySoAFootnote",
    }
)
