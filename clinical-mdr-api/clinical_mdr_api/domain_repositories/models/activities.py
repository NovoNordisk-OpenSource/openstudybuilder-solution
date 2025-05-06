from neomodel import (
    ArrayProperty,
    BooleanProperty,
    FloatProperty,
    One,
    OneOrMore,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    ZeroOrMore,
    ZeroOrOne,
)

from clinical_mdr_api.domain_repositories.models.biomedical_concepts import (
    ActivityInstanceClassRoot,
    ActivityItemClassRoot,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    ConceptRoot,
    ConceptValue,
    UnitDefinitionRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    ClinicalMdrNodeWithUID,
    ClinicalMdrRel,
    VersionRelationship,
)


class ActivityValidGroup(ClinicalMdrNodeWithUID):
    in_group = RelationshipTo(
        "ActivityGroupValue", "IN_GROUP", model=ClinicalMdrRel, cardinality=One
    )
    has_group = RelationshipFrom(
        "ActivitySubGroupValue", "HAS_GROUP", model=ClinicalMdrRel, cardinality=One
    )
    in_subgroup = RelationshipFrom(
        "ActivityGrouping", "IN_SUBGROUP", model=ClinicalMdrRel, cardinality=One
    )


class ActivityGroupValue(ConceptValue):
    has_latest_value = RelationshipFrom(
        "ActivityGroupRoot", "LATEST", model=ClinicalMdrRel
    )
    has_version = RelationshipFrom(
        "ActivityGroupRoot", "HAS_VERSION", model=VersionRelationship
    )
    in_group = RelationshipFrom(
        ActivityValidGroup, "IN_GROUP", model=ClinicalMdrRel, cardinality=ZeroOrMore
    )


class ActivityGroupRoot(ConceptRoot):
    has_version = RelationshipTo(
        ActivityGroupValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        ActivityGroupValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        ActivityGroupValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        ActivityGroupValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        ActivityGroupValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class ActivitySubGroupValue(ConceptValue):
    has_latest_value = RelationshipFrom(
        "ActivitySubGroupRoot", "LATEST", model=ClinicalMdrRel
    )
    has_version = RelationshipFrom(
        "ActivitySubGroupRoot", "HAS_VERSION", model=VersionRelationship
    )
    has_group = RelationshipTo(
        ActivityValidGroup, "HAS_GROUP", model=ClinicalMdrRel, cardinality=OneOrMore
    )


class ActivitySubGroupRoot(ConceptRoot):
    has_version = RelationshipTo(
        ActivitySubGroupValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        ActivitySubGroupValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        ActivitySubGroupValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        ActivitySubGroupValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        ActivitySubGroupValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class ActivityGrouping(ClinicalMdrNodeWithUID):
    in_subgroup = RelationshipTo(
        ActivityValidGroup, "IN_SUBGROUP", model=ClinicalMdrRel, cardinality=OneOrMore
    )
    has_grouping = RelationshipFrom(
        "ActivityValue", "HAS_GROUPING", model=ClinicalMdrRel, cardinality=One
    )
    has_activity = RelationshipFrom(
        "ActivityInstanceValue",
        "HAS_ACTIVITY",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )


class ActivityValue(ConceptValue):
    synonyms = ArrayProperty(StringProperty())
    is_data_collected = BooleanProperty()
    is_multiple_selection_allowed = BooleanProperty(default=True)
    has_latest_value = RelationshipFrom("ActivityRoot", "LATEST", model=ClinicalMdrRel)
    has_version = RelationshipFrom(
        "ActivityRoot", "HAS_VERSION", model=VersionRelationship
    )
    latest_draft = RelationshipFrom(
        "ActivityRoot", "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipFrom(
        "ActivityRoot", "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipFrom(
        "ActivityRoot", "LATEST_RETIRED", model=ClinicalMdrRel
    )
    has_grouping = RelationshipTo(
        ActivityGrouping, "HAS_GROUPING", model=ClinicalMdrRel, cardinality=ZeroOrMore
    )
    replaced_by_activity = RelationshipTo(
        "ActivityRoot",
        "REPLACED_BY_ACTIVITY",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_selected_activity = RelationshipFrom(
        ".study_selections.StudyActivity",
        "HAS_SELECTED_ACTIVITY",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    # Activity Request properties
    request_rationale = StringProperty()
    is_request_final = BooleanProperty(default=False)
    reason_for_rejecting = StringProperty()
    contact_person = StringProperty()
    is_request_rejected = BooleanProperty(default=False)


class ActivityRoot(ConceptRoot):
    has_version = RelationshipTo(
        ActivityValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(ActivityValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(ActivityValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    latest_final = RelationshipTo(ActivityValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        ActivityValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class ActivityItem(ClinicalMdrNode):
    is_adam_param_specific = BooleanProperty(False)
    has_activity_item_class = RelationshipFrom(
        ActivityItemClassRoot,
        "HAS_ACTIVITY_ITEM",
        model=ClinicalMdrRel,
    )
    has_ct_term = RelationshipTo(
        CTTermRoot, "HAS_CT_TERM", model=ClinicalMdrRel, cardinality=ZeroOrMore
    )
    has_unit_definition = RelationshipTo(
        UnitDefinitionRoot,
        "HAS_UNIT_DEFINITION",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )

    from clinical_mdr_api.domain_repositories.models.odm import OdmItemRoot

    has_odm_item = RelationshipTo(
        OdmItemRoot, "HAS_ODM_ITEM", model=ClinicalMdrRel, cardinality=ZeroOrMore
    )


class ActivityInstanceValue(ConceptValue):
    is_research_lab = BooleanProperty()
    molecular_weight = FloatProperty()
    topic_code = StringProperty()
    adam_param_code = StringProperty()
    is_required_for_activity = BooleanProperty()
    is_default_selected_for_activity = BooleanProperty()
    is_data_sharing = BooleanProperty()
    is_legacy_usage = BooleanProperty()
    is_derived = BooleanProperty(default=False)
    legacy_description = StringProperty()

    has_activity = RelationshipTo(
        ActivityGrouping, "HAS_ACTIVITY", model=ClinicalMdrRel, cardinality=OneOrMore
    )
    activity_instance_class = RelationshipTo(
        ActivityInstanceClassRoot,
        "ACTIVITY_INSTANCE_CLASS",
        cardinality=One,
        model=ClinicalMdrRel,
    )
    contains_activity_item = RelationshipTo(
        ActivityItem, "CONTAINS_ACTIVITY_ITEM", model=ClinicalMdrRel
    )
    has_version = RelationshipFrom(
        "ActivityInstanceRoot", "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipFrom(
        "ActivityInstanceRoot", "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipFrom(
        "ActivityInstanceRoot", "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipFrom(
        "ActivityInstanceRoot", "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipFrom(
        "ActivityInstanceRoot", "LATEST_RETIRED", model=ClinicalMdrRel
    )


class ActivityInstanceRoot(ConceptRoot):
    has_version = RelationshipTo(
        ActivityInstanceValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        ActivityInstanceValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        ActivityInstanceValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        ActivityInstanceValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        ActivityInstanceValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
