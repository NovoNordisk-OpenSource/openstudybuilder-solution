from enum import Enum

ENG_LANGUAGE = "eng"
EN_LANGUAGE = "en"


class RelationType(Enum):
    """
    Enum for type of relationship
    """

    ACTIVITY = "activity"
    ACTIVITY_GROUP = "activity_group"
    ACTIVITY_SUB_GROUP = "activity_subgroup"
    ITEM_GROUP = "item_group"
    ITEM = "item"
    FORM = "form"
    TERM = "term"
    UNIT_DEFINITION = "unit_definition"
    VENDOR_ELEMENT = "vendor_element"
    VENDOR_ATTRIBUTE = "vendor_attribute"
    VENDOR_ELEMENT_ATTRIBUTE = "vendor_element_attribute"


class VendorAttributeCompatibleType(Enum):
    """
    Enum for types (e.g. FormDef, ItemRef) that are compatible with Vendor Attribute
    """

    FORM_DEF = "FormDef"
    ITEM_GROUP_DEF = "ItemGroupDef"
    ITEM_DEF = "ItemDef"
    ITEM_GROUP_REF = "ItemGroupRef"
    ITEM_REF = "ItemRef"


class VendorElementCompatibleType(Enum):
    """
    Enum for types (e.g. FormDef, ItemDef) that are compatible with Vendor Element
    """

    FORM_DEF = "FormDef"
    ITEM_GROUP_DEF = "ItemGroupDef"
    ITEM_DEF = "ItemDef"


class TargetType(Enum):
    """
    Enum for ODM target types
    """

    STUDY_EVENT = "study_event"
    STUDY = "study"
    FORM = "form"
    ITEM_GROUP = "item_group"
    ITEM = "item"


class ExporterType(Enum):
    """
    Enum for systems that export ODM files that can be imported into OSB
    """

    OSB = "osb"
    CLINSPARK = "clinspark"
