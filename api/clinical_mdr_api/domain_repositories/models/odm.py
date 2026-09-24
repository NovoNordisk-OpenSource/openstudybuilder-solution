from neomodel import (
    DateProperty,
    JSONProperty,
    RelationshipFrom,
    RelationshipTo,
    ZeroOrMore,
    ZeroOrOne,
)

from clinical_mdr_api.domain_repositories.models.activities import ActivityItem
from clinical_mdr_api.domain_repositories.models.concepts import UnitDefinitionRoot
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCodelistRoot,
    CTTermContext,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    ClinicalMdrRel,
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from common.neomodel import BooleanProperty, IntegerProperty, StringProperty


class Odm(ClinicalMdrNode): ...


class OdmValue(Odm, VersionValue):
    name = StringProperty()


class OdmRoot(Odm, VersionRoot):
    LIBRARY_REL_LABEL = "CONTAINS_ODM"

    has_library = RelationshipFrom(
        Library, "CONTAINS_ODM", cardinality=ZeroOrMore, model=ClinicalMdrRel
    )


class OdmAlias(Odm):
    name = StringProperty()
    context = StringProperty()

    has_condition = RelationshipFrom(
        "OdmConditionValue", "HAS_ALIAS", model=ClinicalMdrRel
    )
    has_method = RelationshipFrom("OdmMethodValue", "HAS_ALIAS", model=ClinicalMdrRel)
    has_form = RelationshipFrom("OdmFormValue", "HAS_ALIAS", model=ClinicalMdrRel)
    has_item_group = RelationshipFrom(
        "OdmItemGroupValue", "HAS_ALIAS", model=ClinicalMdrRel
    )
    has_item = RelationshipFrom("OdmItemValue", "HAS_ALIAS", model=ClinicalMdrRel)


class OdmTranslatedText(Odm):
    text_type = StringProperty()
    language = StringProperty()
    text = StringProperty()

    has_form = RelationshipFrom(
        "OdmFormValue", "HAS_TRANSLATED_TEXT", model=ClinicalMdrRel
    )
    has_item_group = RelationshipFrom(
        "OdmItemGroupValue", "HAS_TRANSLATED_TEXT", model=ClinicalMdrRel
    )
    has_item = RelationshipFrom(
        "OdmItemValue", "HAS_TRANSLATED_TEXT", model=ClinicalMdrRel
    )
    has_condition = RelationshipFrom(
        "OdmConditionValue", "HAS_TRANSLATED_TEXT", model=ClinicalMdrRel
    )
    has_method = RelationshipFrom(
        "OdmMethodValue", "HAS_TRANSLATED_TEXT", model=ClinicalMdrRel
    )


class OdmFormalExpression(Odm):
    context = StringProperty()
    expression = StringProperty()

    has_condition = RelationshipFrom(
        "OdmConditionValue", "HAS_FORMAL_EXPRESSION", model=ClinicalMdrRel
    )
    has_method = RelationshipFrom(
        "OdmMethodValue", "HAS_FORMAL_EXPRESSION", model=ClinicalMdrRel
    )


class OdmConditionValue(OdmValue):
    oid = StringProperty()
    has_translated_text = RelationshipTo(
        OdmTranslatedText, "HAS_TRANSLATED_TEXT", model=ClinicalMdrRel
    )
    has_alias = RelationshipTo(OdmAlias, "HAS_ALIAS", model=ClinicalMdrRel)
    has_formal_expression = RelationshipTo(
        "OdmFormalExpression", "HAS_FORMAL_EXPRESSION", model=ClinicalMdrRel
    )

    has_root = RelationshipFrom(
        "OdmConditionRoot", "HAS_VERSION", model=VersionRelationship
    )


class OdmConditionRoot(OdmRoot):
    has_version = RelationshipTo(
        OdmConditionValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(OdmConditionValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(
        OdmConditionValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        OdmConditionValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        OdmConditionValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmMethodValue(OdmValue):
    oid = StringProperty()
    method_type = StringProperty()
    has_translated_text = RelationshipTo(
        OdmTranslatedText, "HAS_TRANSLATED_TEXT", model=ClinicalMdrRel
    )
    has_alias = RelationshipTo(OdmAlias, "HAS_ALIAS", model=ClinicalMdrRel)
    has_formal_expression = RelationshipTo(
        "OdmFormalExpression", "HAS_FORMAL_EXPRESSION", model=ClinicalMdrRel
    )

    has_root = RelationshipFrom(
        "OdmMethodRoot", "HAS_VERSION", model=VersionRelationship
    )


class OdmMethodRoot(OdmRoot):
    has_version = RelationshipTo(
        OdmMethodValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(OdmMethodValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(OdmMethodValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    latest_final = RelationshipTo(OdmMethodValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        OdmMethodValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmItemGroupRefRelation(ClinicalMdrRel):
    order_number = IntegerProperty()
    mandatory = BooleanProperty()
    collection_exception_condition_oid = StringProperty()
    vendor = JSONProperty()


class OdmVendorNamespaceRelation(ClinicalMdrRel):
    value = StringProperty()


class OdmFormRefRelation(ClinicalMdrRel):
    order_number = IntegerProperty()
    mandatory = BooleanProperty()
    locked = BooleanProperty()
    collection_exception_condition_oid = StringProperty()


class OdmFormValue(OdmValue):
    oid = StringProperty()
    repeating = BooleanProperty()
    sdtm_version = StringProperty()

    has_translated_text = RelationshipTo(
        OdmTranslatedText, "HAS_TRANSLATED_TEXT", model=ClinicalMdrRel
    )
    has_alias = RelationshipTo(OdmAlias, "HAS_ALIAS", model=ClinicalMdrRel)

    has_root = RelationshipFrom("OdmFormRoot", "HAS_VERSION", model=VersionRelationship)

    form_ref = RelationshipFrom(
        "OdmStudyEventValue", "FORM_REF", model=OdmFormRefRelation
    )
    item_group_ref = RelationshipTo(
        "OdmItemGroupValue", "ITEM_GROUP_REF", model=OdmItemGroupRefRelation
    )
    has_vendor_element = RelationshipTo(
        "OdmVendorElementValue", "HAS_VENDOR_ELEMENT", model=OdmVendorNamespaceRelation
    )
    has_vendor_attribute = RelationshipTo(
        "OdmVendorAttributeValue",
        "HAS_VENDOR_ATTRIBUTE",
        model=OdmVendorNamespaceRelation,
    )
    has_vendor_element_attribute = RelationshipTo(
        "OdmVendorAttributeValue",
        "HAS_VENDOR_ELEMENT_ATTRIBUTE",
        model=OdmVendorNamespaceRelation,
    )


class OdmFormRoot(OdmRoot):
    has_version = RelationshipTo(OdmFormValue, "HAS_VERSION", model=VersionRelationship)
    has_latest_value = RelationshipTo(OdmFormValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(OdmFormValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    latest_final = RelationshipTo(OdmFormValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        OdmFormValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmItemRefRelation(ClinicalMdrRel):
    order_number = IntegerProperty()
    mandatory = BooleanProperty()
    key_sequence = StringProperty()
    method_oid = StringProperty()
    imputation_method_oid = StringProperty()
    role = StringProperty()
    role_codelist_oid = StringProperty()
    collection_exception_condition_oid = StringProperty()
    vendor = JSONProperty()


class OdmItemGroupValue(OdmValue):
    oid = StringProperty()
    repeating = BooleanProperty()
    is_reference_data = BooleanProperty()
    sas_dataset_name = StringProperty()
    origin = StringProperty()
    purpose = StringProperty()
    comment = StringProperty()

    has_translated_text = RelationshipTo(
        OdmTranslatedText, "HAS_TRANSLATED_TEXT", model=ClinicalMdrRel
    )
    has_alias = RelationshipTo(OdmAlias, "HAS_ALIAS", model=ClinicalMdrRel)

    has_root = RelationshipFrom(
        "OdmItemGroupRoot", "HAS_VERSION", model=VersionRelationship
    )

    has_sdtm_domain = RelationshipTo(
        CTTermContext, "HAS_SDTM_DOMAIN", cardinality=ZeroOrMore, model=ClinicalMdrRel
    )
    item_group_ref = RelationshipFrom(
        OdmFormValue, "ITEM_GROUP_REF", model=OdmItemGroupRefRelation
    )
    item_ref = RelationshipTo("OdmItemValue", "ITEM_REF", model=OdmItemRefRelation)
    has_vendor_element = RelationshipTo(
        "OdmVendorElementValue", "HAS_VENDOR_ELEMENT", model=OdmVendorNamespaceRelation
    )
    has_vendor_attribute = RelationshipTo(
        "OdmVendorAttributeValue",
        "HAS_VENDOR_ATTRIBUTE",
        model=OdmVendorNamespaceRelation,
    )
    has_vendor_element_attribute = RelationshipTo(
        "OdmVendorAttributeValue",
        "HAS_VENDOR_ELEMENT_ATTRIBUTE",
        model=OdmVendorNamespaceRelation,
    )


class OdmItemGroupRoot(OdmRoot):
    has_version = RelationshipTo(
        OdmItemGroupValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(OdmItemGroupValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(
        OdmItemGroupValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        OdmItemGroupValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        OdmItemGroupValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmItemTermRelationship(ClinicalMdrRel):
    mandatory = BooleanProperty()
    order = IntegerProperty()
    display_text = StringProperty()


class OdmItemUnitDefinitionRelationship(ClinicalMdrRel):
    mandatory = BooleanProperty()
    order = IntegerProperty()


class ActivityItemRel(ClinicalMdrRel):
    order = IntegerProperty()
    primary = BooleanProperty()
    preset_response_value = StringProperty()
    value_condition = StringProperty()
    value_dependent_map = StringProperty()


class OdmItemCodelistRelationship(ClinicalMdrRel):
    allows_multi_choice = BooleanProperty()


class OdmItemValue(OdmValue):
    oid = StringProperty()
    prompt = StringProperty()
    length = IntegerProperty()
    significant_digits = IntegerProperty()
    sas_field_name = StringProperty()
    sds_var_name = StringProperty()
    origin = StringProperty()
    comment = StringProperty()

    links_to_activity_item = RelationshipTo(
        ActivityItem, "LINKS_TO_ACTIVITY_ITEM", model=ActivityItemRel
    )

    has_translated_text = RelationshipTo(
        OdmTranslatedText, "HAS_TRANSLATED_TEXT", model=ClinicalMdrRel
    )
    has_alias = RelationshipTo(OdmAlias, "HAS_ALIAS", model=ClinicalMdrRel)

    has_root = RelationshipFrom("OdmItemRoot", "HAS_VERSION", model=VersionRelationship)

    has_data_type = RelationshipTo(
        CTTermContext, "HAS_DATA_TYPE", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )
    has_unit_definition = RelationshipTo(
        UnitDefinitionRoot,
        "HAS_UNIT_DEFINITION",
        model=OdmItemUnitDefinitionRelationship,
    )
    has_external_question = RelationshipTo(
        CTTermContext,
        "HAS_EXTERNAL_QUESTION",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_codelist = RelationshipTo(
        CTCodelistRoot, "HAS_CODELIST", model=OdmItemCodelistRelationship
    )
    has_codelist_term = RelationshipTo(
        CTTermContext,
        "HAS_CODELIST_TERM",
        cardinality=ZeroOrMore,
        model=OdmItemTermRelationship,
    )
    item_ref = RelationshipFrom(OdmItemGroupValue, "ITEM_REF", model=OdmItemRefRelation)
    has_vendor_element = RelationshipTo(
        "OdmVendorElementValue", "HAS_VENDOR_ELEMENT", model=OdmVendorNamespaceRelation
    )
    has_vendor_attribute = RelationshipTo(
        "OdmVendorAttributeValue",
        "HAS_VENDOR_ATTRIBUTE",
        model=OdmVendorNamespaceRelation,
    )
    has_vendor_element_attribute = RelationshipTo(
        "OdmVendorAttributeValue",
        "HAS_VENDOR_ELEMENT_ATTRIBUTE",
        model=OdmVendorNamespaceRelation,
    )


class OdmItemRoot(OdmRoot):
    has_version = RelationshipTo(OdmItemValue, "HAS_VERSION", model=VersionRelationship)
    has_latest_value = RelationshipTo(OdmItemValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(OdmItemValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    latest_final = RelationshipTo(OdmItemValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        OdmItemValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmStudyEventValue(OdmValue):
    oid = StringProperty()
    effective_date = DateProperty()
    retired_date = DateProperty()
    description = StringProperty()
    display_in_tree = BooleanProperty()

    has_root = RelationshipFrom(
        "OdmStudyEventRoot", "HAS_VERSION", model=VersionRelationship
    )

    form_ref = RelationshipTo(OdmFormValue, "FORM_REF", model=OdmFormRefRelation)


class OdmStudyEventRoot(OdmRoot):
    has_version = RelationshipTo(
        OdmStudyEventValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        OdmStudyEventValue, "LATEST", model=ClinicalMdrRel
    )

    latest_draft = RelationshipTo(
        OdmStudyEventValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        OdmStudyEventValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        OdmStudyEventValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmVendorNamespaceValue(OdmValue):
    prefix = StringProperty()
    url = StringProperty()

    has_root = RelationshipFrom(
        "OdmVendorNamespaceRoot", "HAS_VERSION", model=VersionRelationship
    )

    has_vendor_element = RelationshipTo(
        "OdmVendorElementValue", "HAS_VENDOR_ELEMENT", model=ClinicalMdrRel
    )
    has_vendor_attribute = RelationshipTo(
        "OdmVendorAttributeValue", "HAS_VENDOR_ATTRIBUTE", model=ClinicalMdrRel
    )


class OdmVendorNamespaceRoot(OdmRoot):
    has_version = RelationshipTo(
        OdmVendorNamespaceValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        OdmVendorNamespaceValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        OdmVendorNamespaceValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        OdmVendorNamespaceValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        OdmVendorNamespaceValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmVendorAttributeValue(OdmValue):
    compatible_types = JSONProperty()
    data_type = StringProperty()
    value_regex = StringProperty()

    has_root = RelationshipFrom(
        "OdmVendorAttributeRoot", "HAS_VERSION", model=VersionRelationship
    )

    belongs_to_vendor_namespace = RelationshipFrom(
        "OdmVendorNamespaceValue", "HAS_VENDOR_ATTRIBUTE", model=ClinicalMdrRel
    )
    belongs_to_vendor_element = RelationshipFrom(
        "OdmVendorElementValue", "HAS_VENDOR_ATTRIBUTE", model=ClinicalMdrRel
    )
    belongs_to_form = RelationshipFrom(
        "OdmFormValue", "HAS_VENDOR_ATTRIBUTE", model=OdmVendorNamespaceRelation
    )
    belongs_to_item_group = RelationshipFrom(
        "OdmItemGroupValue", "HAS_VENDOR_ATTRIBUTE", model=OdmVendorNamespaceRelation
    )
    belongs_to_item = RelationshipFrom(
        "OdmItemValue", "HAS_VENDOR_ATTRIBUTE", model=OdmVendorNamespaceRelation
    )
    belongs_to_element_form = RelationshipFrom(
        "OdmFormValue", "HAS_VENDOR_ELEMENT_ATTRIBUTE", model=OdmVendorNamespaceRelation
    )
    belongs_to_element_item_group = RelationshipFrom(
        "OdmItemGroupValue",
        "HAS_VENDOR_ELEMENT_ATTRIBUTE",
        model=OdmVendorNamespaceRelation,
    )
    belongs_to_element_item = RelationshipFrom(
        "OdmItemValue", "HAS_VENDOR_ELEMENT_ATTRIBUTE", model=OdmVendorNamespaceRelation
    )


class OdmVendorAttributeRoot(OdmRoot):
    has_version = RelationshipTo(
        OdmVendorAttributeValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        OdmVendorAttributeValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        OdmVendorAttributeValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        OdmVendorAttributeValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        OdmVendorAttributeValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmVendorElementValue(OdmValue):
    compatible_types = JSONProperty()

    has_root = RelationshipFrom(
        "OdmVendorElementRoot", "HAS_VERSION", model=VersionRelationship
    )

    belongs_to_vendor_namespace = RelationshipFrom(
        "OdmVendorNamespaceValue", "HAS_VENDOR_ELEMENT", model=ClinicalMdrRel
    )
    belongs_to_form = RelationshipFrom(
        "OdmFormValue", "HAS_VENDOR_ELEMENT", model=OdmVendorNamespaceRelation
    )
    belongs_to_item_group = RelationshipFrom(
        "OdmItemGroupValue", "HAS_VENDOR_ELEMENT", model=OdmVendorNamespaceRelation
    )
    belongs_to_item = RelationshipFrom(
        "OdmItemValue", "HAS_VENDOR_ELEMENT", model=OdmVendorNamespaceRelation
    )
    has_vendor_attribute = RelationshipTo(
        "OdmVendorAttributeValue", "HAS_VENDOR_ATTRIBUTE", model=ClinicalMdrRel
    )


class OdmVendorElementRoot(OdmRoot):
    has_version = RelationshipTo(
        OdmVendorElementValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        OdmVendorElementValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        OdmVendorElementValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        OdmVendorElementValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        OdmVendorElementValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
