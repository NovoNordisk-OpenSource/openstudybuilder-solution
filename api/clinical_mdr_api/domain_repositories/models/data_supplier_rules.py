from neomodel import RelationshipTo, ZeroOrMore, ZeroOrOne

from clinical_mdr_api.domain_repositories.models.activities import ActivityGrouping
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermContext,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrRel,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from common.neomodel import StringProperty


class DataSupplierRuleValue(VersionValue):
    name = StringProperty()
    description = StringProperty()
    has_activity_grouping = RelationshipTo(
        ActivityGrouping,
        "HAS_ACTIVITY_GROUPING",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    has_data_supplier_type = RelationshipTo(
        CTTermContext,
        "HAS_DATA_SUPPLIER_TYPE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )


class DataSupplierRuleRoot(VersionRoot):
    has_version = RelationshipTo(
        DataSupplierRuleValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        DataSupplierRuleValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        DataSupplierRuleValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        DataSupplierRuleValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        DataSupplierRuleValue, "LATEST_RETIRED", model=VersionRelationship
    )
