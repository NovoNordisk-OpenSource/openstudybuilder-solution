from datetime import datetime

from neomodel import One, RelationshipFrom, RelationshipTo, ZeroOrMore, ZeroOrOne

from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    ClinicalMdrNodeWithUID,
    ClinicalMdrRel,
    Library,
    VersionRelationship,
    ZonedDateTimeProperty,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    DEFAULT_CODELIST_TYPE,
)
from common.neomodel import (
    ArrayProperty,
    BooleanProperty,
    DateProperty,
    FloatProperty,
    IntegerProperty,
    StringProperty,
)


class CTPackage(ClinicalMdrNodeWithUID):
    name = StringProperty()
    label = StringProperty()
    description = StringProperty()
    href = StringProperty()
    registration_status = StringProperty()
    source = StringProperty()
    import_date = ZonedDateTimeProperty()
    effective_date = DateProperty()
    author_id = StringProperty()
    contains_package = RelationshipFrom(
        "CTCatalogue", "CONTAINS_PACKAGE", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )
    extends_package = RelationshipTo(
        "CTPackage", "EXTENDS_PACKAGE", model=ClinicalMdrRel, cardinality=ZeroOrOne
    )


# abstract class created to easily detect nodes as
# Controlled Terminology items in generic implementation
class ControlledTerminology(ClinicalMdrNode):
    __abstract_node__ = True


class ControlledTerminologyWithUID(ClinicalMdrNodeWithUID):
    __abstract_node__ = True


class CTCodelistAttributesValue(ControlledTerminology):
    name = StringProperty()
    submission_value = StringProperty()
    preferred_term = StringProperty()
    definition = StringProperty()
    extensible = BooleanProperty()
    synonyms = ArrayProperty()


class CTCodelistAttributesRoot(ControlledTerminology):
    has_version = RelationshipTo(
        CTCodelistAttributesValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        CTCodelistAttributesValue, "LATEST", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        CTCodelistAttributesValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        CTCodelistAttributesValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        CTCodelistAttributesValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    has_root = RelationshipFrom(
        "CTCodelistRoot", "HAS_ATTRIBUTES_ROOT", model=ClinicalMdrRel
    )


class CTCodelistNameValue(ControlledTerminology):
    __optional_labels__ = ["TemplateParameter"]
    name = StringProperty()
    is_ordinal = BooleanProperty(default=False)
    codelist_type = StringProperty(default=DEFAULT_CODELIST_TYPE)  # type: ignore[call-arg]


class CTCodelistNameRoot(ControlledTerminology):
    has_version = RelationshipTo(
        CTCodelistNameValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        CTCodelistNameValue, "LATEST", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        CTCodelistNameValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        CTCodelistNameValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        CTCodelistNameValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    has_root = RelationshipFrom("CTCodelistRoot", "HAS_NAME_ROOT", model=ClinicalMdrRel)


class CTTermAttributesValue(ControlledTerminology):
    concept_id = StringProperty()
    preferred_term = StringProperty()
    definition = StringProperty()
    synonyms = ArrayProperty()


class CTTermAttributesRoot(ControlledTerminology):
    has_version = RelationshipTo(
        CTTermAttributesValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        CTTermAttributesValue, "LATEST", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        CTTermAttributesValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        CTTermAttributesValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        CTTermAttributesValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    has_root = RelationshipFrom(
        "CTTermRoot", "HAS_ATTRIBUTES_ROOT", model=ClinicalMdrRel
    )


class CTTermNameValue(ControlledTerminology):
    __optional_labels__ = ["TemplateParameterTermValue"]
    name = StringProperty()
    name_sentence_case = StringProperty()

    # Trial Summary Parameter metadata (populated for CT terms in TS codelists C66738/C67152)
    required_level = (
        StringProperty()
    )  # Required | Conditionally Required | If Applicable
    reference = (
        StringProperty()
    )  # Derived enumeration (based on library and semantic data type)
    cardinality = StringProperty()  # One | Many
    notes = StringProperty()

    # Which MetaStudyField this TS parameter corresponds to
    related_study_field_selection = RelationshipTo(
        "MetaStudyField",
        "RELATED_STUDY_FIELD_SELECTION",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    # Which CT codelist provides the allowed response values (for CT term response type)
    response_codelist = RelationshipTo(
        "CTCodelistRoot",
        "RESPONSE_CODELIST",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    # Which dictionary codelist provides response values (for dictionary term response type)
    response_dictionary = RelationshipTo(
        "clinical_mdr_api.domain_repositories.models.dictionary.DictionaryCodelistRoot",
        "RESPONSE_DICTIONARY",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    # Which null flavors are valid for this parameter
    valid_null_flavor = RelationshipTo(
        "CTTermContext",
        "VALID_NULL_FLAVOR",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )


class CTTermNameRoot(ControlledTerminology):
    __optional_labels__ = ["TemplateParameterTermRoot"]
    has_version = RelationshipTo(
        CTTermNameValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(CTTermNameValue, "LATEST", model=ClinicalMdrRel)
    latest_final = RelationshipTo(CTTermNameValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        CTTermNameValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(CTTermNameValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    has_root = RelationshipFrom("CTTermRoot", "HAS_NAME_ROOT", model=ClinicalMdrRel)


# pylint: disable=abstract-method
class CodelistTermRelationship(ClinicalMdrRel):
    """
    A `CodelistTermRelationship` represents a relationship between a `CTCodelistRoot` and a `CTCodelistTerm` node.
    In the graph, these are persisted as `HAS_TERM`.
    """

    start_date: datetime = ZonedDateTimeProperty()
    end_date: datetime | None = ZonedDateTimeProperty()
    author_id = StringProperty()
    order: int | None = IntegerProperty()  # type: ignore[assignment]
    ordinal: float | None = FloatProperty()  # type: ignore[assignment]


class CTCodelistRoot(ControlledTerminologyWithUID):
    LIBRARY_REL_TYPE = "CONTAINS_CODELIST"
    has_child_codelist = RelationshipFrom(
        "CTCodelistRoot", "HAS_PARENT_CODELIST", model=ClinicalMdrRel
    )
    has_parent_codelist = RelationshipTo(
        "CTCodelistRoot", "HAS_PARENT_CODELIST", model=ClinicalMdrRel
    )
    has_name_root = RelationshipTo(
        CTCodelistNameRoot, "HAS_NAME_ROOT", model=ClinicalMdrRel
    )
    has_attributes_root = RelationshipTo(
        CTCodelistAttributesRoot, "HAS_ATTRIBUTES_ROOT", model=ClinicalMdrRel
    )
    has_codelist = RelationshipFrom("CTCatalogue", "HAS_CODELIST", model=ClinicalMdrRel)
    has_library = RelationshipFrom(Library, LIBRARY_REL_TYPE, model=ClinicalMdrRel)
    has_term = RelationshipTo(
        "clinical_mdr_api.domain_repositories.models.controlled_terminology.CTCodelistTerm",
        "HAS_TERM",
        model=CodelistTermRelationship,
    )
    has_paired_code_codelist = RelationshipTo(
        "CTCodelistRoot",
        "PAIRED_CODE_CODELIST",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    has_paired_name_codelist = RelationshipFrom(
        "CTCodelistRoot",
        "PAIRED_CODE_CODELIST",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )


class CTTermRoot(ControlledTerminologyWithUID):
    LIBRARY_REL_TYPE = "CONTAINS_TERM"
    has_name_root = RelationshipTo(
        CTTermNameRoot, "HAS_NAME_ROOT", model=ClinicalMdrRel
    )
    has_attributes_root = RelationshipTo(
        CTTermAttributesRoot, "HAS_ATTRIBUTES_ROOT", model=ClinicalMdrRel
    )
    has_library = RelationshipFrom(Library, LIBRARY_REL_TYPE)
    has_term_root = RelationshipFrom(
        "clinical_mdr_api.domain_repositories.models.controlled_terminology.CTCodelistTerm",
        "HAS_TERM_ROOT",
        model=ClinicalMdrRel,
    )
    has_parent_type = RelationshipTo(
        "CTTermRoot", "HAS_PARENT_TYPE", model=ClinicalMdrRel
    )
    parent_type_for = RelationshipFrom(
        "CTTermRoot", "HAS_PARENT_TYPE", model=ClinicalMdrRel
    )
    has_parent_subtype = RelationshipTo(
        "CTTermRoot", "HAS_PARENT_SUB_TYPE", model=ClinicalMdrRel
    )
    parent_subtype_for = RelationshipFrom(
        "CTTermRoot", "HAS_PARENT_SUB_TYPE", model=ClinicalMdrRel
    )
    is_specialization_of = RelationshipTo(
        "CTTermRoot", "IS_SPECIALIZATION_OF", model=ClinicalMdrRel
    )
    has_specialization = RelationshipFrom(
        "CTTermRoot", "IS_SPECIALIZATION_OF", model=ClinicalMdrRel
    )
    has_predecessor = RelationshipTo(
        "CTTermRoot", "HAS_PREDECESSOR", model=ClinicalMdrRel
    )
    predecessor_for = RelationshipFrom(
        "CTTermRoot", "HAS_PREDECESSOR", model=ClinicalMdrRel
    )


class CTCodelistTerm(ControlledTerminology):
    submission_value = StringProperty()
    has_term_root = RelationshipTo("CTTermRoot", "HAS_TERM_ROOT", model=ClinicalMdrRel)
    has_term = RelationshipFrom(
        "CTCodelistRoot", "HAS_TERM", model=CodelistTermRelationship
    )


class CTCatalogue(ClinicalMdrNode):
    name = StringProperty()
    contains_package = RelationshipTo(
        CTPackage, "CONTAINS_PACKAGE", model=ClinicalMdrRel
    )
    has_codelist = RelationshipTo(CTCodelistRoot, "HAS_CODELIST", model=ClinicalMdrRel)
    contains_catalogue = RelationshipFrom(
        Library, "CONTAINS_CATALOGUE", model=ClinicalMdrRel
    )


class CTTermContext(ClinicalMdrNode):
    has_selected_term = RelationshipTo(
        "CTTermRoot", "HAS_SELECTED_TERM", model=ClinicalMdrRel, cardinality=One
    )

    has_selected_codelist = RelationshipTo(
        "CTCodelistRoot",
        "HAS_SELECTED_CODELIST",
        model=ClinicalMdrRel,
        cardinality=One,
    )


class MetaStudyField(ClinicalMdrNode):
    """Defines a master metadata record for a study field / study selection type.

    Provides a single place to describe each trial summary parameter's
    response value type, the page it appears on, and its data type.
    Referenced by CTTermNameValue via RELATED_STUDY_FIELD_SELECTION
    and by StudyField nodes via HAS_META_STUDY_FIELD.
    """

    osb_field_name = StringProperty()
    study_field_selection_type = (
        StringProperty()
    )  # e.g. 'StudyCTTermField', 'StudyTextField', etc.
    osb_page_reference = StringProperty()

    has_semantic_data_type = RelationshipTo(
        CTTermContext,
        "HAS_SEMANTIC_DATA_TYPE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
