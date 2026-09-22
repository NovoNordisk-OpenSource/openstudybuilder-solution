from neomodel import (
    One,
    OneOrMore,
    RelationshipFrom,
    RelationshipTo,
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
    CTCodelistRoot,
    CTTermContext,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    ClinicalMdrNodeWithUID,
    ClinicalMdrRel,
    VersionRelationship,
)
from common.neomodel import (
    ArrayProperty,
    BooleanProperty,
    FloatProperty,
    StringProperty,
)


class ActivityGroupValue(ConceptValue):
    has_latest_value = RelationshipFrom(
        "ActivityGroupRoot", "LATEST", model=ClinicalMdrRel
    )
    has_version = RelationshipFrom(
        "ActivityGroupRoot", "HAS_VERSION", model=VersionRelationship
    )
    has_selected_group = RelationshipFrom(
        "ActivityGrouping",
        "HAS_SELECTED_GROUP",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
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
    has_selected_subgroup = RelationshipFrom(
        "ActivityGrouping",
        "HAS_SELECTED_SUBGROUP",
        model=ClinicalMdrRel,
        cardinality=OneOrMore,
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
    has_selected_group = RelationshipTo(
        ActivityGroupValue, "HAS_SELECTED_GROUP", model=ClinicalMdrRel, cardinality=One
    )
    has_selected_subgroup = RelationshipTo(
        ActivitySubGroupValue,
        "HAS_SELECTED_SUBGROUP",
        model=ClinicalMdrRel,
        cardinality=One,
    )
    has_grouping = RelationshipFrom(
        "ActivityValue", "HAS_GROUPING", model=ClinicalMdrRel, cardinality=One
    )
    has_activity = RelationshipFrom(
        "ActivityInstanceGroupingValue",
        "HAS_ACTIVITY",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )


class ActivityValue(ConceptValue):
    synonyms = ArrayProperty(StringProperty())  # type: ignore
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
    is_activity_instance_id_specific = BooleanProperty()
    text_value = StringProperty()
    has_activity_item_class = RelationshipFrom(
        ActivityItemClassRoot,
        "HAS_ACTIVITY_ITEM",
        model=ClinicalMdrRel,
    )
    has_codelist = RelationshipTo(
        CTCodelistRoot, "HAS_CODELIST", model=ClinicalMdrRel, cardinality=ZeroOrMore
    )
    has_ct_term = RelationshipTo(
        CTTermContext, "HAS_CT_TERM", model=ClinicalMdrRel, cardinality=ZeroOrMore
    )
    has_unit_definition = RelationshipTo(
        UnitDefinitionRoot,
        "HAS_UNIT_DEFINITION",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
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


class ActivityInstanceGroupingRoot(ClinicalMdrNode):
    has_version = RelationshipTo(
        "ActivityInstanceGroupingValue", "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        "ActivityInstanceGroupingValue", "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        "ActivityInstanceGroupingValue", "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        "ActivityInstanceGroupingValue", "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        "ActivityInstanceGroupingValue", "LATEST_RETIRED", model=ClinicalMdrRel
    )
    has_grouping_root = RelationshipFrom(
        "ActivityInstanceRoot",
        "HAS_GROUPING_ROOT",
        model=ClinicalMdrRel,
        cardinality=One,
    )

    def get_value_for_version(self, version: str | None):
        matching_values = self.has_version.match(version=version)
        if len(matching_values) > 0:
            return matching_values[0]
        return None

    def get_relation_for_version(self, version: str):
        value = self.get_value_for_version(version)
        relationships = self.has_version.all_relationships(value)
        all_matching = [rel for rel in relationships if rel.version == version]
        all_without_end = [rel for rel in all_matching if rel.end_date is None]
        if len(all_without_end) == 1:
            # There is only one relationship without end date
            return all_without_end[0]
        if len(all_without_end) > 1:
            # There are several relationships without end date, return the latest one based on start date
            return max(all_without_end, key=lambda d: d.start_date)
        # There are no relationships without end date, return the latest one based on end date
        return max(all_matching, key=lambda d: d.end_date)


class ActivityInstanceGroupingValue(ClinicalMdrNode):
    has_latest_value = RelationshipFrom(
        ActivityInstanceGroupingRoot, "LATEST", model=ClinicalMdrRel
    )
    has_version = RelationshipFrom(
        ActivityInstanceGroupingRoot, "HAS_VERSION", model=VersionRelationship
    )
    latest_draft = RelationshipFrom(
        ActivityInstanceGroupingRoot, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipFrom(
        ActivityInstanceGroupingRoot, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipFrom(
        ActivityInstanceGroupingRoot, "LATEST_RETIRED", model=ClinicalMdrRel
    )

    has_activity = RelationshipTo(
        ActivityGrouping, "HAS_ACTIVITY", model=ClinicalMdrRel, cardinality=OneOrMore
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

    has_grouping_root = RelationshipTo(
        ActivityInstanceGroupingRoot,
        "HAS_GROUPING_ROOT",
        model=ClinicalMdrRel,
        cardinality=One,
    )
