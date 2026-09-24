from neomodel import One, OneOrMore, RelationshipFrom, RelationshipTo, ZeroOrOne

from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCodelistRoot,
    CTTermContext,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrRel,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    DatasetClass,
    VariableClass,
)
from common.neomodel import BooleanProperty, IntegerProperty, StringProperty


class ActivityItemClassRel(ClinicalMdrRel):
    mandatory = BooleanProperty()
    is_adam_param_specific_enabled = BooleanProperty()
    is_additional_optional = BooleanProperty()
    is_default_linked = BooleanProperty()


class ActivityInstanceClassValue(VersionValue):
    order = IntegerProperty()
    definition = StringProperty()
    is_domain_specific = BooleanProperty()
    level = IntegerProperty()
    nci_concept_id = StringProperty()
    nci_concept_name = StringProperty()
    has_latest_value = RelationshipFrom(
        "ActivityInstanceClassRoot", "LATEST", model=ClinicalMdrRel
    )


class ActivityInstanceClassRoot(VersionRoot):
    LIBRARY_REL_LABEL = "CONTAINS_ACTIVITY_INSTANCE_CLASS"

    has_version = RelationshipTo(
        ActivityInstanceClassValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        ActivityInstanceClassValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        ActivityInstanceClassValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        ActivityInstanceClassValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        ActivityInstanceClassValue, "LATEST_RETIRED", model=VersionRelationship
    )
    parent_class = RelationshipTo(
        "ActivityInstanceClassRoot", "PARENT_CLASS", model=ClinicalMdrRel
    )
    maps_dataset_class = RelationshipTo(
        DatasetClass, "MAPS_DATASET_CLASS", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )
    has_activity_item_class = RelationshipTo(
        "ActivityItemClassRoot", "HAS_ITEM_CLASS", model=ActivityItemClassRel
    )


class ActivityItemClassValue(VersionValue):
    definition = StringProperty()
    nci_concept_id = StringProperty()
    nci_concept_name = StringProperty()
    order = IntegerProperty()
    display_name = StringProperty()
    has_latest_value = RelationshipFrom(
        "ActivityItemClassRoot", "LATEST", model=ClinicalMdrRel
    )
    has_version = RelationshipFrom(
        "ActivityItemClassRoot",
        "HAS_VERSION",
        model=ClinicalMdrRel,
        cardinality=OneOrMore,
    )
    has_data_type = RelationshipTo(
        CTTermContext, "HAS_DATA_TYPE", model=ClinicalMdrRel, cardinality=One
    )
    has_role = RelationshipTo(
        CTTermContext, "HAS_ROLE", model=ClinicalMdrRel, cardinality=One
    )


class NonStandardVariableValue(ActivityItemClassValue):
    code = StringProperty()
    is_multiple = BooleanProperty()
    length = IntegerProperty()
    algorithm = StringProperty()
    is_cdisc_defined = BooleanProperty()
    derivation_rule = StringProperty()
    origin_type = RelationshipTo(
        CTTermContext,
        "DEFAULT_ORIGIN_TYPE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    origin_source = RelationshipTo(
        CTTermContext,
        "DEFAULT_ORIGIN_SOURCE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )


class ActivityItemClassRoot(VersionRoot):
    LIBRARY_REL_LABEL = "CONTAINS"

    has_version = RelationshipTo(
        ActivityItemClassValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        ActivityItemClassValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        ActivityItemClassValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        ActivityItemClassValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        ActivityItemClassValue, "LATEST_RETIRED", model=VersionRelationship
    )
    has_activity_instance_class = RelationshipFrom(
        "ActivityInstanceClassRoot",
        "HAS_ITEM_CLASS",
        model=ActivityItemClassRel,
        cardinality=OneOrMore,
    )
    maps_variable_class = RelationshipTo(
        VariableClass,
        "MAPS_VARIABLE_CLASS",
        model=ClinicalMdrRel,
    )
    has_valid_codelist_for_items = RelationshipTo(
        CTCodelistRoot,
        "HAS_VALID_CODELIST_FOR_ITEMS",
        model=ClinicalMdrRel,
    )
