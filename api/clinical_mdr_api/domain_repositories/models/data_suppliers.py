from neomodel import RelationshipTo, ZeroOrOne

from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermContext,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrRel,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from common.neomodel import IntegerProperty, StringProperty


class DataSupplierValue(VersionValue):
    name = StringProperty()
    description = StringProperty()
    order = IntegerProperty()
    api_base_url = StringProperty()
    ui_base_url = StringProperty()
    has_data_supplier_type = RelationshipTo(
        CTTermContext,
        "HAS_DATA_SUPPLIER_TYPE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_origin_source = RelationshipTo(
        CTTermContext, "HAS_ORIGIN_SOURCE", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )
    has_origin_type = RelationshipTo(
        CTTermContext, "HAS_ORIGIN_TYPE", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )


class DataSupplierRoot(VersionRoot):
    has_version = RelationshipTo(
        DataSupplierValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(DataSupplierValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(
        DataSupplierValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        DataSupplierValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        DataSupplierValue, "LATEST_RETIRED", model=VersionRelationship
    )
